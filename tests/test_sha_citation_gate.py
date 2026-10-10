"""CS-1222 - a doc carrying an unpublished or unresolvable commit sha turns a guard red.

WHAT THIS GRADES. ``tools/sha_citation_gate.py`` resolves every sha-shaped
citation as ``<sha>^{commit}`` - one ``git cat-file --batch-check`` for the tree,
the resolution ``git rev-parse --verify -q`` performs - and counts it only
when the commit is reachable from ``HEAD``, ``refs/remotes/origin/main`` or a
tag. Its
exclusions are an ALLOWLIST of exact tokens; no shape excludes anything. Arms:

* THE PLANT ARMS run in a throwaway repository holding a byte-copy of a guarded
  doc, with its one commit published as ``refs/remotes/origin/main``: an absent
  sha is refused by name, a commit on a local or remote SIDE branch that HEAD
  cannot reach is refused as ``unpublished``, and the published commit (short
  and full), a tagged one, or an ancestor of HEAD that origin/main has not
  reached yet - the pre-push case - passes, so the gate is not merely refusing
  every hex run. Every planted
  prefix is CONSTRUCTED to carry a digit and a letter, so no arm depends on the
  luck of a random sha.
* THE ESCAPE ARMS: every shape an adversary walked an unresolvable sha through
  - ``name@``, ``owner/repo at``, ``-dirty``, ``...``, ``origin/main@``,
  ``feature/lane at``, ``<sha>-<sha>``, ``run <8hex>``, a ``blob`` label, a
  blob that really is in the store, ``path at`` - is planted in a copy of
  ``docs/LEDGER.md`` and must be refused.
* THE OVERREACH ARM: an allowlisted token that IS a published commit fails.
* THE TABLE ARMS: the closed class set, one stated reason per row, no
  duplicates, every row sha-shaped, and an exact-token match only.
* THE EMPTY ARMS: a sweep that admits nothing, and a repository with no
  origin/main and no tag, exit "could not judge", never 0.
* THE REPORT ARMS: the inclusion rule, every class with its count, the table
  size, unused rows and the filter-repo discriminator are printed every run.
* THE SHALLOW ARM: a shallow clone cannot judge, so it says so and exits 2.
* THE CS-1224 ARMS: an unpublished commit abbreviation planted in a byte-copy
  of a tracked ``.py`` file is refused, and a 5- or 6-character unpublished
  abbreviation in a guarded doc is refused, each beside a control in which a
  published commit passes; a 6-character run of any shape - digit-only,
  upper-case, joined - is refused in a doc and in code alike, and an upper-case
  7-character code citation is refused; a 4-character run and a run of 41 or
  more are never silently passed - every run states each width class it does
  not judge, with its count and the reason; UTF-16 and UTF-32 files behind a
  BOM are decoded and judged, a doc with a stray Latin-1 byte is still graded,
  a NUL-bearing or undecodable file is counted not-read and makes the run
  COULD NOT JUDGE unless an unpublished finding outranks it, a BOM over 8-bit
  text still yields its ASCII citation through the byte view, and a 5-run
  git calls ambiguous - two commits, or a commit and a tag at it - is counted
  and is red when a candidate is unpublished.
* THE LIVE ARM runs the gate over this tree and FAILS - never skips - when the
  tree is shallow or has no origin/main and no tag, and fails on an unused
  table row.
  CI runs this module in three jobs, each checking out full history: the
  ``tests (save shard)`` job of ``.github/workflows/tier1.yml``, and the
  ``full suite (<os>, save shard)`` and ``clean-checkout probe (<os>, save
  shard)`` legs of ``.github/workflows/tier2.yml`` on both ubuntu-latest and
  windows-latest. ``tests/test_full_history_checkouts.py`` pins that set.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
GATE_SOURCE: Final = REPO_ROOT / "tools" / "sha_citation_gate.py"

#: The guarded doc a throwaway repository carries a byte-copy of. It carries no
#: sha-shaped token of its own - the empty arm asserts that rather than trusting it.
GUARDED_DOC: Final = "CLAUDE.md"

#: A tracked code file a throwaway repository carries a byte-copy of - CS-1224.
CODE_FILE: Final = "tools/toolpath.py"

#: A tracked PowerShell file the decode arm re-encodes as UTF-16 - CS-1224.
UTF16_FILE: Final = "ops/loop/run_lane.ps1"

#: The ledger, whose copy carries the ``path at <sha>`` plant.
LEDGER_DOC: Final = "docs/LEDGER.md"

#: Hex characters in a full sha1 object name.
FULL_SHA_WIDTH: Final = 40

#: Seconds one git call or one CLI run may take in these arms.
TIMEOUT: Final = 120

#: A sha-shaped value no throwaway repository holds - asserted absent by the arm
#: that plants it, never assumed.
ABSENT_SHA: Final = "5ca1ab1e0ddba11"

#: Inherited variables that would point a child git at another repository - the
#: pre-push hook exports GIT_DIR, for one.
_GIT_REDIRECTS: Final = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
)


def _load() -> ModuleType:
    """Import ``tools/sha_citation_gate.py`` by path.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_sha_citation_gate", GATE_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {GATE_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load()


@dataclass
class Repo:
    """A throwaway repository and the environment its git runs under."""

    path: Path
    env: dict[str, str]

    def git(self, *args: str) -> str:
        """Run one git command in the repository and return its stripped stdout."""
        completed = subprocess.run(
            ["git", "-c", "core.autocrlf=false", *args],
            cwd=self.path,
            env=self.env,
            capture_output=True,
            timeout=TIMEOUT,
            check=True,
        )
        return completed.stdout.decode("ascii").strip()

    def lacks(self, sha: str) -> bool:
        """Whether ``sha`` resolves to no object at all here."""
        completed = subprocess.run(
            ["git", "cat-file", "-e", sha],
            cwd=self.path,
            env=self.env,
            capture_output=True,
            timeout=TIMEOUT,
            check=False,
        )
        return completed.returncode != 0


def _env(tmp_path: Path) -> dict[str, str]:
    """A child environment with a synthetic identity and no inherited git config."""
    env = dict(os.environ)
    for name in _GIT_REDIRECTS:
        env.pop(name, None)
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for role in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{role}_NAME"] = "Synthetic"
        env[f"GIT_{role}_EMAIL"] = "synthetic@example.invalid"
    return env


def _make(tmp_path: Path, *docs: str, publish: bool = True) -> Repo:
    """A repository whose one commit tracks byte-copies of ``docs``, optionally published."""
    path = tmp_path / "repo"
    path.mkdir()
    made = Repo(path, _env(tmp_path))
    made.git("init", "-q")
    for doc in docs:
        (path / doc).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / doc, path / doc)
        made.git("add", "--", doc)
    made.git("commit", "-q", "-m", "seed")
    if publish:
        made.git("update-ref", "refs/remotes/origin/main", "HEAD")
    return made


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    """A repository whose one PUBLISHED commit tracks a byte-copy of the guarded doc."""
    return _make(tmp_path, GUARDED_DOC)


@dataclass(frozen=True)
class Run:
    """One CLI run reduced to scalars, so an assertion never renders the argv.

    A failing assertion on a ``CompletedProcess`` attribute renders the whole
    object, interpreter path included; these fields are all an arm reads.
    """

    returncode: int
    stdout: str
    stderr: str


def cli(repo: Repo, *args: str) -> Run:
    """Run the gate CLI in a fresh interpreter against ``repo``."""
    done = subprocess.run(
        [sys.executable, "-B", str(GATE_SOURCE), "--repo", str(repo.path), *args],
        env=repo.env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    return Run(done.returncode, done.stdout, done.stderr)


def plant(repo: Repo, line: str, doc: str = GUARDED_DOC) -> int:
    """Append ``line`` to the working copy of ``doc``; return its one-based line number."""
    target = repo.path / doc
    body = target.read_bytes() + b"\n" + line.encode("ascii") + b"\n"
    target.write_bytes(body)
    return body.count(b"\n") - line.count("\n")


def mixed(sha: str, width: int = 7) -> str:
    """The shortest prefix of ``sha`` at least ``width`` long that carries a digit and a letter."""
    for end in range(width, len(sha) + 1):
        head = sha[:end]
        if any(c.isdigit() for c in head) and any(c.isalpha() for c in head):
            return head
    message = "a full sha always carries both"
    raise AssertionError(message)


# --- the plant arms -----------------------------------------------------------


def test_an_unresolvable_sha_in_a_guarded_doc_is_refused_by_name(repo: Repo) -> None:
    """A planted sha the object store lacks makes the gate exit 1 and name it."""
    absent = repo.lacks(ABSENT_SHA)
    assert absent, "control: the planted sha must be absent from the store"
    plant(repo, f"Landed as commit `{ABSENT_SHA}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unresolved {GUARDED_DOC}:" in done.stdout
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


@pytest.mark.parametrize("ref", ["refs/heads/local-only", "refs/remotes/origin/side"])
def test_an_unpublished_commit_is_refused(repo: Repo, ref: str) -> None:
    """A side-branch commit HEAD cannot reach resolves here and is still refused."""
    tree = repo.git("write-tree")
    side = repo.git("commit-tree", tree, "-p", "HEAD", "-m", "not on main")
    repo.git("update-ref", ref, side)
    token = mixed(side, 9)
    plant(repo, f"Landed as commit `{token}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{token} unpublished" in done.stdout


def test_an_ancestor_of_head_not_yet_on_origin_main_passes(repo: Repo) -> None:
    """The pre-push case: a commit of the batch being pushed is published by that push."""
    repo.git("commit", "-q", "--allow-empty", "-m", "earlier in the batch")
    batch = repo.git("rev-parse", "HEAD")
    origin = repo.git("rev-parse", "refs/remotes/origin/main")
    assert batch != origin
    repo.git("commit", "-q", "--allow-empty", "-m", "the tip being judged")
    plant(repo, f"Landed as commit `{mixed(batch, 9)}` earlier in this batch.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr


def side_commit(repo: Repo, wanted: str = "") -> str:
    """A commit on a side ref HEAD cannot reach; ``wanted`` digit-only makes its 7-prefix digits."""
    tree = repo.git("write-tree")
    for attempt in range(4000):
        sha = repo.git("commit-tree", tree, "-p", "HEAD", "-m", f"side {attempt}")
        if wanted != "digits" or sha[:7].isdigit():
            repo.git("update-ref", "refs/heads/side", sha)
            return sha
    message = "no digit-only prefix in 4000 commits"
    raise AssertionError(message)


NOT_ADMITTED_SHAPES: Final = [
    ("digits", "Landed as commit `{tok}` on the merge.", lambda sha: sha[:7]),
    ("", "Landed as commit `{tok}` on the merge.", lambda sha: mixed(sha, 9).upper()),
    ("", "built as v1.0-3-g{tok} on the runner", lambda sha: mixed(sha, 9)),
    ("", "the address 0x{tok} was hit", lambda sha: mixed(sha, 9)),
    ("", "the symbol sha_{tok} was kept", lambda sha: mixed(sha, 9)),
    ("", "the branch {tok}_fix was merged", lambda sha: mixed(sha, 9)),
]


@pytest.mark.parametrize(("wanted", "shape", "make"), NOT_ADMITTED_SHAPES)
def test_a_not_admitted_run_naming_an_unpublished_commit_fails(
    repo: Repo, wanted: str, shape: str, make: Callable[[str], str]
) -> None:
    """Digit-only, upper-case, describe, 0x and underscore-joined runs are resolved too."""
    side = side_commit(repo, wanted)
    token = make(side)
    head = repo.git("rev-parse", "HEAD")
    plant(repo, shape.format(tok=token))
    plant(repo, f"Landed as `{head}`.")
    done = cli(repo)
    assert f"unpublished-not-admitted {GUARDED_DOC}:" in done.stdout, done.stdout
    assert done.returncode == gate.EXIT_UNRESOLVED


def test_a_not_admitted_run_naming_nothing_or_a_published_commit_is_silent(repo: Repo) -> None:
    """The noise rule: a decimal, a word, or a run naming a PUBLISHED commit stays silent."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"run 36192391765 read 1234567 and DEFACED at v1-g{mixed(head, 9)}.")
    plant(repo, f"Landed as `{head}`.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr


def test_a_tagged_commit_is_published(repo: Repo) -> None:
    """A commit reachable only from a tag counts as published."""
    tree = repo.git("write-tree")
    tagged = repo.git("commit-tree", tree, "-p", "HEAD", "-m", "tagged")
    repo.git("tag", "v-synthetic", tagged)
    plant(repo, f"Landed as commit `{mixed(tagged, 9)}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr


@pytest.mark.parametrize("width", [7, FULL_SHA_WIDTH])
def test_a_published_sha_in_a_guarded_doc_passes(repo: Repo, width: int) -> None:
    """The throwaway's published commit, short and full, is admitted and passes."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"Landed as commit `{mixed(head, width)}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert "admitted 1 " in done.stdout
    assert "unresolved 0; overreach 0" in done.stdout


def test_the_prefix_constructor_never_yields_an_unadmitted_token() -> None:
    """An all-digit head is lengthened until it carries a letter, so it is admitted."""
    head = mixed("1234567890abcdef" + "0" * 24)
    assert head == "1234567890a"
    assert [entry.token for entry in gate.scan_text(f"`{head}`", allowlist={})] == [head]


def test_the_batch_resolver_agrees_with_rev_parse_verify(repo: Repo) -> None:
    """The batch answers every token exactly as ``rev-parse --verify -q`` does, one by one."""
    head = repo.git("rev-parse", "HEAD")
    blob = repo.git("hash-object", "--", GUARDED_DOC)
    tokens = [head, mixed(head, 7), mixed(head, 12).upper(), blob, mixed(blob, 9), ABSENT_SHA]
    batch = gate.resolve_many(repo.path, tokens)
    single = {token: gate.commit_of(repo.path, token.lower()) for token in tokens}
    assert batch == single
    assert batch[head] == head
    assert batch[blob] is None
    assert batch[ABSENT_SHA] is None


def test_sweep_api_matches_the_cli_on_a_plant(repo: Repo) -> None:
    """The in-process sweep reports the same unresolved citation the CLI does."""
    plant(repo, f"See `{ABSENT_SHA}`.")
    report = gate.sweep(repo.path)
    assert [(entry.token, state) for entry, state in report.unresolved] == [
        (ABSENT_SHA, "never-resolved")
    ]
    assert report.verdict() == gate.EXIT_UNRESOLVED


# --- the escape arms: no shape excludes anything ----------------------------------

ESCAPES: Final = [
    "Gate run at main@{sha}: MIT, two holders",
    "**PIN.** Moonbeam/Clockspeed at {sha}, retrieved",
    "built from `{sha}-dirty` on the runner",
    "and none carries `{sha}...`. The carriers",
    "fast-forwarded to origin/main@{sha} cleanly",
    "branch feature/lane at {sha} was merged",
    "the range `{sha}-{sha2}` was squashed",
    "the pre-push run {run} refused",
    "byte-identical, blob `{sha}`, verified by hash",
    "the gate `tools/precommit_gate.py` at {sha} was identical",
    "measured digest `{sha}` against the pin",
    "worktree-agent-{sha} is halted",
]


def test_every_escape_shape_is_refused_in_a_ledger_copy(tmp_path: Path) -> None:
    """Each shape the adversary used carries an unresolvable sha to a refusal, by line."""
    made = _make(tmp_path, LEDGER_DOC)
    planted: set[tuple[int, str]] = set()
    for index, shape in enumerate(ESCAPES):
        sha = f"{index:x}f9a2c1d"
        sha2 = f"{index:x}e8b3d2c"
        run = f"{index:x}d7c4e3b"[:8]
        for value in (sha, sha2, run):
            absent = made.lacks(value)
            assert absent, "control: every planted value is absent from the store"
        token = run if "{run}" in shape else sha
        line = plant(made, shape.format(sha=sha, sha2=sha2, run=run), LEDGER_DOC)
        planted.add((line, token))
    done = cli(made)
    assert done.returncode == gate.EXIT_UNRESOLVED
    refused = {
        (int(fields[1].rsplit(":", 1)[1]), fields[2])
        for fields in (line.split() for line in done.stdout.splitlines())
        if fields and fields[0] == "unresolved" and fields[1].startswith(f"{LEDGER_DOC}:")
    }
    escaped = sorted(planted - refused)
    assert escaped == []


def test_a_real_blob_in_the_store_is_still_refused(repo: Repo) -> None:
    """A blob that exists is not a commit; with no table row it fails like any other."""
    blob = mixed(repo.git("hash-object", "--", GUARDED_DOC), 10)
    plant(repo, f"The hook blob `{blob}` is unchanged.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{blob} never-resolved (hint: looks like a blob" in done.stdout


def test_a_hash_label_on_the_previous_line_exempts_nothing(repo: Repo) -> None:
    """A keyword one line up reaches nothing: the citation is refused."""
    plant(repo, f"assert `git hash-object x` is\n`{ABSENT_SHA}` before measuring.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


# --- the overreach arm --------------------------------------------------------


def test_an_allowlisted_token_that_is_a_published_commit_reddens_the_gate(repo: Repo) -> None:
    """A table row that names a real published commit is overreach, and overreach fails."""
    head = repo.git("rev-parse", "HEAD")
    row = mixed(head, 10)
    plant(repo, f"Run `{row}` first; landed as `{head}`.")
    report = gate.sweep(repo.path, {row: "lane-run-id"})
    assert [(entry.rule, entry.token) for entry in report.overreach] == [("lane-run-id", row)]
    assert report.verdict() == gate.EXIT_UNRESOLVED


# --- the table arms -----------------------------------------------------------


def test_the_class_set_is_closed() -> None:
    """The classes are the acceptance's measured set plus guid, and nothing else."""
    assert set(gate.CLASSES) == {
        "agent-id",
        "sha256-prefix",
        "foreign-pin",
        "git-blob",
        "lane-run-id",
        "fixture-vector",
        "guid",
    }


def test_every_row_is_classed_reasoned_shaped_and_unique() -> None:
    """The table loads; a bad class, blank reason, bad shape or duplicate is refused."""
    assert len(gate.allowlist_map()) == len(gate.ALLOWLIST)
    row = gate.AllowRow
    for bad in (
        [row("5ca1ab1e0d", "commit", "x")],
        [row("5ca1ab1e0d", "guid", " ")],
        [row("ABCDEF1234", "guid", "x")],
        [row("5ca1ab1e0d", "guid", "x"), row("5ca1ab1e0d", "guid", "y")],
    ):
        with pytest.raises(ValueError, match="allowlist row"):
            gate.allowlist_map(bad)


def test_the_match_is_exact_token_only() -> None:
    """A prefix, an extension or a neighbour of an allowlisted token is admitted."""
    listed = gate.ALLOWLIST[0].token
    for near in (listed[:-1], listed + "0", "0" + listed[1:]):
        found = [(e.token, e.rule) for e in gate.scan_text(f"See `{near}`.")]
        assert found == [(near, None)], near
    assert [e.rule for e in gate.scan_text(f"See `{listed}`.")] == [gate.ALLOWLIST[0].klass]


@pytest.mark.parametrize(
    "token",
    ["7656119", "1234567890", "defaced", "ABCDEF1234", "x1a2b3c4d5", "a" * 41 + "1"],
)
def test_the_inclusion_rule_admits_only_its_published_shape(token: str) -> None:
    """Decimal runs, all-letter words, upper case, embedded and over-long runs are not shas."""
    assert gate.scan_text(f"See {token} here.") == []


def test_the_inclusion_rule_states_what_it_does_not_admit() -> None:
    """The published rule names its non-admissions and the reason for each."""
    rule = gate.INCLUSION_RULE
    for phrase in ("NOT ADMITTED", "all-digit", "upper-case", "lower case", "decimal"):
        assert phrase in rule, phrase


# --- the empty arms -----------------------------------------------------------


def test_an_empty_sweep_is_never_a_pass(repo: Repo) -> None:
    """The unplanted copy admits nothing, and that is reported as could-not-judge."""
    done = cli(repo)
    assert "admitted 0 " in done.stdout, done.stdout
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE


def test_no_published_ref_cannot_judge(tmp_path: Path) -> None:
    """With no origin/main and no tag the gate refuses to judge, HEAD notwithstanding."""
    made = _make(tmp_path, GUARDED_DOC, publish=False)
    plant(made, f"Landed as `{made.git('rev-parse', 'HEAD')}`.")
    done = cli(made)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert "resolver NO-PUBLISHED-REF" in done.stdout


# --- the report arms ----------------------------------------------------------


def test_every_run_publishes_its_rule_its_exclusions_and_its_discriminator(repo: Repo) -> None:
    """Inclusion rule, table size, every class with its count, resolver and discriminator."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"Landed as `{head}`; worktree-agent-ace624231ac7fd814 built it.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert gate.INCLUSION_RULE in done.stdout
    assert f"allowlist rows {len(gate.ALLOWLIST)}; " in done.stdout
    for name in gate.CLASSES:
        assert f"excluded-count {name} " in done.stdout, name
    assert "excluded-count agent-id 1" in done.stdout
    assert f"excluded agent-id {GUARDED_DOC}:" in done.stdout
    assert "resolver full" in done.stdout
    assert "discriminator filter-repo commit-map: ABSENT" in done.stdout


def test_a_present_commit_map_labels_a_rewritten_sha(repo: Repo) -> None:
    """With filter-repo's commit-map present, a mapped unresolved sha is named rewritten."""
    old = "0dd" + "5ca1ab1e" * 4 + "1234e"
    assert len(old) == FULL_SHA_WIDTH
    common = Path(repo.git("rev-parse", "--path-format=absolute", "--git-common-dir"))
    (common / "filter-repo").mkdir()
    (common / "filter-repo" / "commit-map").write_bytes(
        b"old                                      new\n"
        + old.encode("ascii")
        + b" "
        + repo.git("rev-parse", "HEAD").encode("ascii")
        + b"\n"
    )
    plant(repo, f"Landed as `{old[:12]}` and `{ABSENT_SHA}`.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert "discriminator filter-repo commit-map: AVAILABLE" in done.stdout
    assert f"{old[:12]} rewritten-away" in done.stdout
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


def test_a_shallow_clone_cannot_judge(repo: Repo, tmp_path: Path) -> None:
    """A shallow clone holds no history to resolve against; it says so and exits 2."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"Landed as `{head}`.")
    repo.git("commit", "-q", "-am", "plant")
    shallow = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", repo.path.as_uri(), str(shallow)],
        env=repo.env,
        capture_output=True,
        timeout=TIMEOUT,
        check=True,
    )
    done = cli(Repo(shallow, repo.env))
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert "resolver SHALLOW" in done.stdout


# --- the CS-1224 arms: code files, short and over-long widths -------------------


def commit_where(repo: Repo, ok: Callable[[str], bool], ref: str) -> str:
    """A commit off HEAD whose sha satisfies ``ok``, pointed at by ``ref``."""
    tree = repo.git("write-tree")
    for attempt in range(4000):
        sha = repo.git("commit-tree", tree, "-p", "HEAD", "-m", f"cs1224 {attempt}")
        if ok(sha):
            repo.git("update-ref", ref, sha)
            return sha
    message = "no commit satisfied the predicate in 4000 attempts"
    raise AssertionError(message)


def _carries_both(text: str) -> bool:
    return any(c.isdigit() for c in text) and any(c.isalpha() for c in text)


@pytest.fixture
def code_repo(tmp_path: Path) -> Repo:
    """A published repository tracking the guarded doc and a byte-copy of a tracked .py."""
    made = _make(tmp_path, GUARDED_DOC, CODE_FILE)
    plant(made, f"Landed as `{made.git('rev-parse', 'HEAD')}`.")
    return made


def _not_judged(stdout: str, name: str) -> int:
    """The count a run printed for the not-judged width class ``name``."""
    for line in stdout.splitlines():
        fields = line.split()
        if fields[:2] == ["not-judged", name]:
            return int(fields[2])
    message = f"no not-judged line for {name}"
    raise AssertionError(message)


def test_an_unpublished_commit_cited_in_a_tracked_py_file_is_refused(code_repo: Repo) -> None:
    """A side-branch abbreviation in a .py copy turns the gate red and is named by line."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    line = plant(code_repo, f"# RED at {side[:7]}: the push landed.", CODE_FILE)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {CODE_FILE}:{line} {side[:7]} " in done.stdout


def test_a_published_commit_cited_in_a_tracked_py_file_passes(code_repo: Repo) -> None:
    """Control: the published commit, cited the same way in the same .py copy, passes."""
    head = code_repo.git("rev-parse", "HEAD")
    plant(code_repo, f"# RED at {mixed(head, 7)}: the push landed.", CODE_FILE)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert "code files 1;" in done.stdout


@pytest.mark.parametrize("width", [5, 6])
def test_a_short_unpublished_abbreviation_in_a_guarded_doc_is_refused(
    code_repo: Repo, width: int
) -> None:
    """A 5- or 6-character abbreviation of an unpublished commit is refused."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:width]), "refs/heads/side")
    token = side[:width]
    line = plant(code_repo, f"Landed as commit `{token}` on the merge.")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {GUARDED_DOC}:{line} {token} " in done.stdout


@pytest.mark.parametrize("width", [5, 6])
def test_a_short_published_abbreviation_in_a_guarded_doc_passes(
    code_repo: Repo, width: int
) -> None:
    """Control: a 5- or 6-character abbreviation of a TAGGED commit passes."""
    tagged = commit_where(code_repo, lambda sha: _carries_both(sha[:width]), "refs/tags/v-short")
    plant(code_repo, f"Landed as commit `{tagged[:width]}` on the merge.")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr


SHORT_SHAPES: Final = [
    ("digit-only-doc", GUARDED_DOC, "Landed as commit `{tok}` on the merge.", "digits", False),
    ("upper-doc", GUARDED_DOC, "Landed as commit `{tok}` on the merge.", "both", True),
    ("lower-code", CODE_FILE, "# RED at {tok}: the push landed.", "both", False),
    ("joined-code", CODE_FILE, "ADDRESS = 0x{tok}", "both", False),
]


@pytest.mark.parametrize(
    ("label", "target", "shape", "kind", "upper"), SHORT_SHAPES, ids=[s[0] for s in SHORT_SHAPES]
)
def test_a_six_character_unpublished_run_of_any_shape_in_any_file_is_refused(
    code_repo: Repo, label: str, target: str, shape: str, kind: str, upper: bool
) -> None:
    """A 6-run naming an unpublished commit is refused in a doc and in a .py copy alike."""
    if kind == "digits":
        side = commit_where(code_repo, lambda sha: sha[:6].isdigit(), "refs/heads/side")
    else:
        side = commit_where(code_repo, lambda sha: _carries_both(sha[:6]), "refs/heads/side")
    token = side[:6].upper() if upper else side[:6]
    line = plant(code_repo, shape.format(tok=token), target)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, label + done.stdout + done.stderr
    assert f"unpublished-not-admitted {target}:{line} {token} " in done.stdout, label


def test_an_upper_case_unpublished_citation_in_a_tracked_py_file_is_refused(
    code_repo: Repo,
) -> None:
    """Code runs are read in either case: an UPPER-case 7-char citation in .py is refused."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    token = side[:7].upper()
    line = plant(code_repo, f"# RED at {token}: the push landed.", CODE_FILE)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {CODE_FILE}:{line} {token} " in done.stdout


def _not_read(stdout: str) -> int:
    """The not-read count a run printed."""
    for line in stdout.splitlines():
        fields = line.split()
        if fields[:1] == ["not-read"]:
            return int(fields[1])
    message = "no not-read line"
    raise AssertionError(message)


def test_a_utf16_file_with_a_bom_is_decoded_and_judged(tmp_path: Path) -> None:
    """A UTF-16 .ps1 carrying an unpublished citation is decoded, so it is refused."""
    made = _make(tmp_path, GUARDED_DOC, UTF16_FILE)
    plant(made, f"Landed as `{made.git('rev-parse', 'HEAD')}`.")
    side = commit_where(made, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    text = (REPO_ROOT / UTF16_FILE).read_bytes().decode("utf-8")
    text += f"\n# RED at {side[:7]}: the push landed.\n"
    (made.path / UTF16_FILE).write_bytes(text.encode("utf-16"))
    done = cli(made)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {UTF16_FILE}:" in done.stdout
    assert _not_read(done.stdout) == 0


@pytest.mark.parametrize(
    "body",
    [b"\x00\x01binary\xff\xfe\x00", b"# valid UTF-8 text\n\x00# with a NUL inside\n"],
    ids=["undecodable", "nul-in-valid-utf8"],
)
def test_a_not_read_tracked_file_makes_the_run_could_not_judge(
    code_repo: Repo, body: bytes
) -> None:
    """A file the reader cannot judge is counted, named, and is never a PASS - exit 2."""
    before = _not_read(cli(code_repo).stdout)
    assert before == 0
    (code_repo.path / CODE_FILE).write_bytes(body)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert _not_read(done.stdout) == 1
    assert f"not-read-file {CODE_FILE}" in done.stdout
    assert "COULD NOT JUDGE - 1 tracked file not read" in done.stdout


#: CS-1292 - the README's images are this tree's first tracked binaries.
KNOWN_PNG: Final = "docs/assets/known.png"

#: The eight bytes every PNG opens with.
PNG_MAGIC: Final = b"\x89PNG\r\n\x1a\n"


def _png() -> bytes:
    """A real one-pixel PNG, built here, never read from the tree."""

    def chunk(kind: bytes, body: bytes) -> bytes:
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00\x00\x00\x00")
    return PNG_MAGIC + chunk(b"IHDR", header) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")


def _track(repo: Repo, name: str, body: bytes) -> None:
    """Write ``body`` at ``name`` and stage it, so the sweep's ``ls-files`` lists it."""
    target = repo.path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    repo.git("add", "--", name)


def _pin_binaries(repo: Repo, rows: dict[str, bytes]) -> None:
    """Track a hash-pin file naming each path with the SHA-256 of ``rows[path]``."""
    pins = {name: hashlib.sha256(body).hexdigest() for name, body in rows.items()}
    _track(repo, gate.KNOWN_BINARY_FILE, (json.dumps(pins, indent=2) + "\n").encode("ascii"))


def _smuggle(token: str) -> bytes:
    """PNG magic, a NUL, then plain text citing ``token`` - binary to the decoder."""
    return PNG_MAGIC + b"\x00" + f"\n# RED at {token}: the push landed.\n".encode("ascii")


def _known_binary(stdout: str) -> int:
    """The known-binary count a run printed."""
    for line in stdout.splitlines():
        fields = line.split()
        if fields[:1] == ["known-binary"]:
            return int(fields[1])
    message = "no known-binary line"
    raise AssertionError(message)


def test_a_pinned_png_is_counted_known_binary_and_never_left_unread(code_repo: Repo) -> None:
    """A binary whose path AND SHA-256 match a pin is counted and named, never not-read."""
    body = _png()
    assert b"\0" in body, "control: these bytes must be binary to the reader"
    _track(code_repo, KNOWN_PNG, body)
    _pin_binaries(code_repo, {KNOWN_PNG: body})
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert _not_read(done.stdout) == 0
    assert f"not-read-file {KNOWN_PNG}" not in done.stdout
    assert _known_binary(done.stdout) == 1
    assert f"known-binary-file {KNOWN_PNG}" in done.stdout


@pytest.mark.parametrize(
    ("name", "body", "pinned"),
    [
        (KNOWN_PNG, _png(), b""),
        ("docs/assets/unlisted.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF\x00", b""),
        (KNOWN_PNG, _png(), _png() + b"\x00"),
    ],
    ids=["png-with-no-pin", "unlisted-image-format", "pinned-path-other-bytes"],
)
def test_an_unpinned_binary_is_still_not_read(
    code_repo: Repo, name: str, body: bytes, pinned: bytes
) -> None:
    """The pin fails closed: a binary off the list, or off its pinned hash, stays not-read."""
    _track(code_repo, name, body)
    if pinned:
        _pin_binaries(code_repo, {name: pinned})
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert _not_read(done.stdout) == 1
    assert f"not-read-file {name}" in done.stdout
    assert _known_binary(done.stdout) == 0


@pytest.mark.parametrize("pinned", [False, True], ids=["unpinned", "pinned-to-itself"])
def test_a_citation_smuggled_behind_png_magic_fails_the_run(code_repo: Repo, pinned: bool) -> None:
    """PNG magic, a NUL, then an unpublished citation: its raw bytes are graded - exit 1.

    A pin admits a file to known-binary; it never stops its bytes being graded, so
    pinning the smuggle file's own hash still fails the run.
    """
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    name = "docs/assets/smuggle.png"
    body = _smuggle(side[:7])
    _track(code_repo, name, body)
    if pinned:
        _pin_binaries(code_repo, {name: body})
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:" in done.stdout
    assert f" {side[:7]} " in done.stdout


@pytest.mark.parametrize(
    "body",
    [
        b"not json\n",
        b'{"docs/assets/known.png": "beef"}\n',
        b'{"../outside.png": "' + b"a" * 64 + b'"}\n',
    ],
    ids=["not-json", "short-digest", "path-outside-the-tree"],
)
def test_a_malformed_pin_file_could_not_judge(code_repo: Repo, body: bytes) -> None:
    """A pin file the gate cannot trust is refused, exit 2 - never read as an empty list."""
    _track(code_repo, gate.KNOWN_BINARY_FILE, body)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert "COULD NOT JUDGE" in done.stderr


def test_a_png_named_text_file_is_still_read_and_judged(code_repo: Repo) -> None:
    """The pin never hides text: a decodable .png is scanned like any code file."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    name = "docs/assets/text.png"
    _track(code_repo, name, f"# RED at {side[:7]}: the push landed.\n".encode("ascii"))
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:1 {side[:7]} " in done.stdout
    assert _known_binary(done.stdout) == 0
    assert _not_read(done.stdout) == 0


# --- CS-1292: the bytes git would publish, not only the work tree's ------------


def _stage_blob(repo: Repo, scratch: Path, name: str, body: bytes, mode: str = "100644") -> None:
    """Put ``body`` in the index at ``name`` and leave the work tree untouched."""
    source = scratch / "blob.bin"
    source.write_bytes(body)
    blob = repo.git("hash-object", "-w", "--no-filters", str(source))
    repo.git("update-index", "--add", "--cacheinfo", f"{mode},{blob},{name}")


def _unpublished(repo: Repo) -> str:
    """A 7-character abbreviation of a side-branch commit HEAD cannot reach."""
    return commit_where(repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")[:7]


def test_a_smuggle_staged_behind_a_clean_pinned_work_tree_fails_the_run(
    code_repo: Repo, tmp_path: Path
) -> None:
    """The index blob is judged: a clean pinned file on disk hides no staged smuggle."""
    token = _unpublished(code_repo)
    clean = _png()
    _track(code_repo, KNOWN_PNG, clean)
    _pin_binaries(code_repo, {KNOWN_PNG: clean})
    _stage_blob(code_repo, tmp_path, KNOWN_PNG, clean + _smuggle(token))
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {KNOWN_PNG}:" in done.stdout
    assert f" {token} " in done.stdout
    assert f"not-read-file {KNOWN_PNG}" in done.stdout


def test_a_smuggle_committed_at_head_behind_a_clean_index_fails_the_run(code_repo: Repo) -> None:
    """HEAD's blob is judged: restoring the index and the work tree hides no commit."""
    token = _unpublished(code_repo)
    clean = _png()
    _track(code_repo, KNOWN_PNG, clean + _smuggle(token))
    _pin_binaries(code_repo, {KNOWN_PNG: clean})
    code_repo.git("commit", "-q", "-m", "smuggle")
    _track(code_repo, KNOWN_PNG, clean)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {KNOWN_PNG}:" in done.stdout
    assert f" {token} " in done.stdout


def test_a_case_variant_pin_never_admits_a_smuggled_blob(code_repo: Repo, tmp_path: Path) -> None:
    """A case-variant path opens the clean file on a case-insensitive disk; its blob is judged.

    The variant is pinned with the clean file's reviewed hash, as the leak adversary
    did, so only the blob's own bytes can tell the two apart.
    """
    code_repo.git("config", "core.ignorecase", "false")
    token = _unpublished(code_repo)
    clean = _png()
    variant = "docs/assets/Known.png"
    _track(code_repo, KNOWN_PNG, clean)
    _stage_blob(code_repo, tmp_path, variant, clean + _smuggle(token))
    _pin_binaries(code_repo, {KNOWN_PNG: clean, variant: clean})
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {variant}:" in done.stdout
    assert f" {token} " in done.stdout
    assert f"not-read-file {variant}" in done.stdout


def test_an_index_only_case_variant_of_a_doc_is_judged_by_its_blob(
    code_repo: Repo, tmp_path: Path
) -> None:
    """``CLAUDE.MD`` staged beside ``CLAUDE.md``: the variant's own blob is read and judged."""
    code_repo.git("config", "core.ignorecase", "false")
    token = _unpublished(code_repo)
    variant = GUARDED_DOC.upper()
    assert variant != GUARDED_DOC, "control: the variant must differ in case"
    _stage_blob(code_repo, tmp_path, variant, f"Landed as `{token}`.\n".encode("ascii"))
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {variant}:1 {token} " in done.stdout


def test_a_symlink_entry_is_judged_by_its_blob(code_repo: Repo, tmp_path: Path) -> None:
    """A mode-120000 entry's blob is its link text; a citation in it fails the run."""
    token = _unpublished(code_repo)
    clean = _png()
    _track(code_repo, KNOWN_PNG, clean)
    _pin_binaries(code_repo, {KNOWN_PNG: clean})
    _stage_blob(code_repo, tmp_path, KNOWN_PNG, f"../{token}/target".encode("ascii"), "120000")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {KNOWN_PNG}:1 {token} " in done.stdout


# --- CS-1292 round 3: HEAD's tree is judged whatever the index says ------------

#: A code path and a doc path, each committed carrying a citation and then dropped
#: from the index - the rename source of a ``git mv`` is the same dropped path.
DROPPED: Final = ("tools/smuggle.py", "docs/smuggle.md")


def _commit_citing(repo: Repo, name: str, token: str) -> None:
    """Commit ``name`` citing ``token``, so HEAD's tree carries the citation."""
    _track(repo, name, f"# RED at {token}: the push landed.\n".encode("ascii"))
    repo.git("commit", "-q", "-m", "carry")


@pytest.mark.parametrize("name", DROPPED)
@pytest.mark.parametrize("cached", [False, True], ids=["rm", "rm-cached"])
def test_a_citation_committed_at_head_then_removed_from_the_index_fails_the_run(
    code_repo: Repo, name: str, cached: bool
) -> None:
    """``git rm`` empties the index, not HEAD: the committed blob is still judged - exit 1."""
    token = _unpublished(code_repo)
    _commit_citing(code_repo, name, token)
    code_repo.git("rm", "-q", *(["--cached"] if cached else []), "--", name)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f" {name}:1 {token} " in done.stdout


@pytest.mark.parametrize("name", DROPPED)
def test_a_citation_committed_at_head_then_renamed_and_cleaned_fails_the_run(
    code_repo: Repo, name: str
) -> None:
    """``git mv`` then a clean rewrite: the rename SOURCE in HEAD is still judged - exit 1."""
    token = _unpublished(code_repo)
    _commit_citing(code_repo, name, token)
    moved = name.replace("smuggle", "renamed")
    code_repo.git("mv", "--", name, moved)
    _track(code_repo, moved, b"# clean\n")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f" {name}:1 {token} " in done.stdout


@pytest.mark.parametrize("name", DROPPED)
def test_a_clean_file_removed_from_the_index_is_judged_and_never_not_read(
    code_repo: Repo, name: str
) -> None:
    """Control: a staged deletion of a clean file passes - its absence is never NOT READ."""
    _track(code_repo, name, b"# clean\n")
    code_repo.git("commit", "-q", "-m", "carry")
    code_repo.git("rm", "-q", "--", name)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert _not_read(done.stdout) == 0


def _stage_gitlink(repo: Repo, name: str, commit: str) -> None:
    """Put a gitlink (mode 160000) naming ``commit`` in the index at ``name``."""
    repo.git("update-index", "--add", "--cacheinfo", f"160000,{commit},{name}")


def _gitlink_where(repo: Repo, name: str, commit: str, where: str) -> None:
    """A gitlink at ``name``: staged, committed, or committed then dropped from the index."""
    _stage_gitlink(repo, name, commit)
    if where != "staged":
        repo.git("commit", "-q", "-m", "gitlink")
    if where == "head-only":
        repo.git("rm", "-q", "--cached", "--", name)


GITLINK_STATES: Final = ("staged", "committed", "head-only")


@pytest.mark.parametrize("where", GITLINK_STATES)
def test_a_gitlink_path_holding_a_plain_file_is_scanned_as_one(code_repo: Repo, where: str) -> None:
    """A gitlink's path holding a plain file on disk is read as that file - exit 1."""
    token = _unpublished(code_repo)
    name = "tools/linked.py"
    _gitlink_where(code_repo, name, code_repo.git("rev-parse", "HEAD"), where)
    (code_repo.path / name).write_bytes(f"# RED at {token}: the push landed.\n".encode("ascii"))
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:1 {token} " in done.stdout


@pytest.mark.parametrize("where", GITLINK_STATES)
def test_a_gitlink_naming_an_unpublished_commit_fails_the_run(code_repo: Repo, where: str) -> None:
    """A gitlink's own commit is graded like a code run: an unpublished one is red - exit 1.

    Line 0 names the tree entry itself, never a line of its bytes.
    """
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    name = "vendor/linked"
    _gitlink_where(code_repo, name, side, where)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:0 {side} " in done.stdout


@pytest.mark.parametrize("where", GITLINK_STATES)
def test_a_gitlink_with_no_file_on_disk_is_judged_by_its_commit_and_never_not_read(
    code_repo: Repo, where: str
) -> None:
    """Control: a gitlink naming a published commit, nothing on disk, passes - exit 0.

    Its content is the commit it names, which is judged; an empty or absent
    submodule folder is a gitlink's normal state, never a file dropping out.
    """
    _gitlink_where(code_repo, "vendor/linked", code_repo.git("rev-parse", "HEAD"), where)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert _not_read(done.stdout) == 0


@pytest.mark.parametrize("where", ["staged", "head-only"])
def test_a_citation_in_a_tracked_file_name_fails_the_run(code_repo: Repo, where: str) -> None:
    """A path is graded like a code run too, in the index and in HEAD's tree - exit 1."""
    token = _unpublished(code_repo)
    name = f"docs/notes-{token}.md"
    _track(code_repo, name, b"clean\n")
    if where == "head-only":
        code_repo.git("commit", "-q", "-m", "carry")
        code_repo.git("rm", "-q", "--", name)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:0 {token} " in done.stdout


# --- CS-1292 round 4: git's local views of history are never honoured ----------

#: The objects a replace ref can stand a clean one in for, so the cited bytes are
#: never read: the cited blob, HEAD's tree, or HEAD itself.
REPLACED: Final = ("blob", "tree", "commit")

#: The two local views that give a commit parents a push never sends: a replace
#: ref written by ``git replace --graft`` and the deprecated ``info/grafts`` file.
GRAFTS: Final = ("replace-graft", "grafts-file")


def _replace_clean(repo: Repo, scratch: Path, name: str, target: str) -> None:
    """Stand a clean object in for the one carrying ``name``'s citation - a local view only."""
    if target == "blob":
        clean = scratch / "clean.txt"
        clean.write_bytes(b"# clean\n")
        blob = repo.git("hash-object", "-w", "--no-filters", str(clean))
        cited = repo.git("rev-parse", f"HEAD:{name}")
        repo.git("replace", cited, blob)
        # Bound first: rendered inline, the call would repr ``repo`` and its env.
        shown = repo.git("cat-file", "blob", cited)
        assert "RED at" not in shown, "control: the view is live"
        return
    suffix = "^{tree}" if target == "tree" else ""
    old, new = (repo.git("rev-parse", f"{rev}{suffix}") for rev in ("HEAD", "HEAD~1"))
    repo.git("replace", old, new)
    listed = repo.git("ls-tree", "-r", "--name-only", "HEAD").split("\n")
    assert name not in listed, "control: the view must hide the cited path"


def _graft(repo: Repo, how: str, parent: str) -> None:
    """Give HEAD ``parent`` as a second parent in git's local view only.

    ``how`` names the view (:data:`GRAFTS`). A push sends HEAD's own parents, so
    ``parent`` stays unpublished whatever the view says.
    """
    head, first = repo.git("rev-parse", "HEAD"), repo.git("rev-parse", "HEAD~1")
    if how == "replace-graft":
        repo.git("replace", "--graft", head, first, parent)
    else:
        grafts = repo.path / repo.git("rev-parse", "--git-path", "info/grafts")
        grafts.parent.mkdir(parents=True, exist_ok=True)
        grafts.write_bytes(f"{head} {first} {parent}\n".encode("ascii"))
    reach = repo.git("rev-list", "HEAD").split()
    assert parent in reach, "control: the view must make the parent look reachable"


@pytest.mark.parametrize("target", REPLACED)
def test_a_citation_hidden_by_a_replace_ref_fails_the_run(
    code_repo: Repo, tmp_path: Path, target: str
) -> None:
    """A replace ref swaps what git READS for an object, never what a push SENDS - exit 1.

    The citation is committed and ``git rm``'d, then the blob, HEAD's tree or HEAD
    itself is replaced by a clean one, so only the published object carries it.
    """
    token = _unpublished(code_repo)
    name = DROPPED[0]
    _commit_citing(code_repo, name, token)
    code_repo.git("rm", "-q", "--", name)
    _replace_clean(code_repo, tmp_path, name, target)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f" {name}:1 {token} " in done.stdout


@pytest.mark.parametrize("how", GRAFTS)
def test_a_gitlink_to_a_commit_grafted_under_head_fails_the_run(code_repo: Repo, how: str) -> None:
    """A graft makes an unpublished gitlink commit LOOK reachable; a push never sends it."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    name = "vendor/linked"
    _gitlink_where(code_repo, name, side, "committed")
    _graft(code_repo, how, side)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:0 {side} " in done.stdout


@pytest.mark.parametrize("how", GRAFTS)
def test_a_file_name_citing_a_commit_grafted_under_head_fails_the_run(
    code_repo: Repo, how: str
) -> None:
    """The same graft behind a citation in a committed file name - exit 1."""
    token = _unpublished(code_repo)
    name = f"docs/notes-{token}.md"
    _track(code_repo, name, b"clean\n")
    code_repo.git("commit", "-q", "-m", "carry")
    _graft(code_repo, how, code_repo.git("rev-parse", "refs/heads/side"))
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {name}:0 {token} " in done.stdout


def _nul_hidden(text: str, shape: str) -> bytes:
    """``text`` in a shape whose raw bytes carry no plain hex run - NULs between its pieces."""
    if shape == "utf16le-no-bom":
        return text.encode("utf-16-le")
    if shape == "utf16be-no-bom":
        return text.encode("utf-16-be")
    return b"\x00".join(text[i : i + 4].encode("ascii") for i in range(0, len(text), 4))


@pytest.mark.parametrize("shape", ["utf16le-no-bom", "utf16be-no-bom", "nul-split"])
def test_a_citation_hidden_by_nuls_in_a_pinned_binary_fails_the_run(
    code_repo: Repo, shape: str
) -> None:
    """A not-read file's bytes are also graded with every NUL removed - exit 1, pinned or not."""
    token = _unpublished(code_repo)
    hidden = _nul_hidden(f"\n# RED at {token}: the push landed.\n", shape)
    assert token.encode("ascii") not in hidden, "control: no plain hex run in the raw bytes"
    body = _png() + hidden
    _track(code_repo, KNOWN_PNG, body)
    _pin_binaries(code_repo, {KNOWN_PNG: body})
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {KNOWN_PNG}:" in done.stdout
    assert f" {token} " in done.stdout


def test_every_run_states_what_the_byte_grade_cannot_see() -> None:
    """A compressed citation is invisible to the byte grade; the run says so, every run."""
    reason = gate.KNOWN_BINARY_REASON
    assert "NUL removed" in reason
    assert "compressed" in reason
    assert "pin" in reason
    assert "index and HEAD" in gate.NOT_READ_REASON


def test_a_utf32_file_with_a_bom_is_decoded_and_judged(code_repo: Repo) -> None:
    """A UTF-32 BOM opens with the UTF-16 one; it is told apart, decoded and judged."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    text = (REPO_ROOT / CODE_FILE).read_bytes().decode("utf-8")
    text += f"\n# RED at {side[:7]}: the push landed.\n"
    (code_repo.path / CODE_FILE).write_bytes(text.encode("utf-32"))
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {CODE_FILE}:" in done.stdout
    assert _not_read(done.stdout) == 0


def test_a_doc_with_one_latin1_byte_is_still_graded(code_repo: Repo) -> None:
    """A stray non-UTF-8 byte without a NUL degrades to replacement, never to not-read."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    target = code_repo.path / GUARDED_DOC
    target.write_bytes(
        target.read_bytes() + b"\nCaf\xe9 landed as commit `" + side[:7].encode() + b"`.\n"
    )
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{side[:7]} unpublished" in done.stdout
    assert _not_read(done.stdout) == 0


def colliding_commits(repo: Repo, width: int = 5) -> tuple[str, str]:
    """Two commits written into ``repo`` whose ``width``-prefixes are equal and sha-shaped."""
    tree = repo.git("write-tree")
    parent = repo.git("rev-parse", "HEAD")
    who = "Synthetic <synthetic@example.invalid> 1700000000 +0000"
    seen: dict[str, bytes] = {}
    for attempt in range(1 << 20):
        body = (
            f"tree {tree}\nparent {parent}\nauthor {who}\ncommitter {who}\n\n"
            f"cs1224 collide {attempt}\n"
        ).encode("ascii")
        sha = hashlib.sha1(b"commit %d\x00" % len(body) + body, usedforsecurity=False)
        prefix = sha.hexdigest()[:width]
        if prefix in seen and _carries_both(prefix):
            return _write_commit(repo, seen[prefix]), _write_commit(repo, body)
        seen[prefix] = body
    message = "no prefix collision found"
    raise AssertionError(message)


def _write_commit(repo: Repo, body: bytes) -> str:
    done = subprocess.run(
        ["git", "hash-object", "-t", "commit", "-w", "--stdin"],
        cwd=repo.path,
        env=repo.env,
        input=body,
        capture_output=True,
        timeout=TIMEOUT,
        check=True,
    )
    return done.stdout.decode("ascii").strip()


def _ambiguous(stdout: str) -> int:
    """The ambiguous-run count a run printed."""
    for line in stdout.splitlines():
        fields = line.split()
        if fields[:1] == ["ambiguous"]:
            return int(fields[1])
    message = "no ambiguous line"
    raise AssertionError(message)


def test_an_ambiguous_short_run_with_an_unpublished_candidate_is_refused(
    code_repo: Repo,
) -> None:
    """A 5-run two commits answer is no citation; with an unpublished candidate it is red."""
    first, second = colliding_commits(code_repo)
    assert first[:5] == second[:5]
    assert first != second
    code_repo.git("tag", "v-first", first)
    code_repo.git("update-ref", "refs/heads/side", second)
    line = plant(code_repo, f"Landed as commit `{first[:5]}` on the merge.")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert _ambiguous(done.stdout) == 1
    assert f"ambiguous-unpublished {GUARDED_DOC}:{line} {first[:5]} " in done.stdout


def test_an_ambiguous_short_run_of_published_commits_is_counted(code_repo: Repo) -> None:
    """Control: when every candidate is published the run is counted ambiguous, not red."""
    first, second = colliding_commits(code_repo)
    code_repo.git("tag", "v-first", first)
    code_repo.git("tag", "v-second", second)
    plant(code_repo, f"Landed as commit `{first[:5]}` on the merge.")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert _ambiguous(done.stdout) == 1


def colliding_tag(repo: Repo, commit: str, width: int = 5) -> str:
    """A tag object pointing at ``commit`` whose ``width``-prefix equals the commit's."""
    for attempt in range(1 << 26):
        body = (
            f"object {commit}\ntype commit\ntag cs1224-{attempt}\n"
            "tagger Synthetic <synthetic@example.invalid> 1700000000 +0000\n\nx\n"
        ).encode("ascii")
        sha = hashlib.sha1(b"tag %d\x00" % len(body) + body, usedforsecurity=False)
        if sha.hexdigest()[:width] == commit[:width]:
            done = subprocess.run(
                ["git", "hash-object", "-t", "tag", "-w", "--stdin"],
                cwd=repo.path,
                env=repo.env,
                input=body,
                capture_output=True,
                timeout=TIMEOUT,
                check=True,
            )
            written = done.stdout.decode("ascii").strip()
            assert written == sha.hexdigest()
            return written
    message = "no colliding tag found"
    raise AssertionError(message)


def test_an_ambiguous_run_peeling_to_one_unpublished_commit_is_refused(code_repo: Repo) -> None:
    """A commit and a dangling tag at it share a 5-prefix: ONE peeled commit, still red."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:5]), "refs/heads/side")
    colliding_tag(code_repo, side)
    line = plant(code_repo, f"Landed as commit `{side[:5]}` on the merge.")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert _ambiguous(done.stdout) == 1
    assert f"ambiguous-unpublished {GUARDED_DOC}:{line} {side[:5]} " in done.stdout


def _even(data: bytes) -> bytes:
    """``data`` padded with one space, when needed, so it decodes cleanly as UTF-16."""
    return data if len(data) % 2 == 0 else data + b" "


@pytest.mark.parametrize("shape", ["bom-8bit-doc", "bom-8bit-code", "utf16-plus-ascii"])
def test_a_bom_file_whose_bytes_carry_an_ascii_citation_is_judged(
    tmp_path: Path, shape: str
) -> None:
    """A UTF-16 BOM over 8-bit text decodes as CJK; the byte view still finds the citation."""
    made = _make(tmp_path, GUARDED_DOC, CODE_FILE, UTF16_FILE)
    head = made.git("rev-parse", "HEAD")
    side = commit_where(made, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    cite = f"\n# Landed as commit `{side[:7]}` on the merge.\n".encode("ascii")
    if shape == "utf16-plus-ascii":
        target = UTF16_FILE
        text = (REPO_ROOT / UTF16_FILE).read_bytes().decode("utf-8")
        body = _even(text.encode("utf-16") + cite)
        plant(made, f"Landed as `{head}`.")
    else:
        target = GUARDED_DOC if shape == "bom-8bit-doc" else CODE_FILE
        original = (made.path / target).read_bytes()
        if target == GUARDED_DOC:
            original += f"\nLanded as `{head}`.\n".encode("ascii")
        else:
            plant(made, f"Landed as `{head}`.")
        body = _even(b"\xff\xfe" + original + cite)
    (made.path / target).write_bytes(body)
    assert body.decode("utf-16", errors="replace").count(side[:7]) == 0
    done = cli(made)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert side[:7] in done.stdout
    assert _not_read(done.stdout) == 0


@pytest.mark.parametrize(
    ("lead", "mark"),
    [("\0", b"\xff\xfe\x00\x00"), ("x\0", b"\xff\xfex\x00")],
    ids=["u0000-first", "u0000-second"],
)
def test_a_utf16_file_carrying_u0000_is_never_a_pass(
    code_repo: Repo, lead: str, mark: bytes
) -> None:
    """U+0000 first opens UTF-16LE with the UTF-32LE mark; later, it is a NUL: exit 1 both.

    Either way the file is not read, and its citation - joined once its NULs are
    removed (CS-1292) - fails the run, never a pass.
    """
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    text = (REPO_ROOT / CODE_FILE).read_bytes().decode("utf-8")
    body = (lead + text + f"\n# RED at {side[:7]}: the push landed.\n").encode("utf-16")
    assert body.startswith(mark)
    (code_repo.path / CODE_FILE).write_bytes(body)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f" {side[:7]} " in done.stdout
    assert _not_read(done.stdout) == 1
    assert f"not-read-file {CODE_FILE}" in done.stdout


@pytest.mark.parametrize("cited", [True, False], ids=["cited", "uncited"])
def test_a_bom_file_that_fails_a_strict_decode_is_not_read_but_its_bytes_are_graded(
    code_repo: Repo, cited: bool
) -> None:
    """Odd-length 8-bit text behind a UTF-16 mark: not read, yet an ASCII citation is red."""
    original = (code_repo.path / CODE_FILE).read_bytes()
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    tail = f"\n# RED at {side[:7]}: the push landed.\n".encode("ascii") if cited else b"\n"
    body = b"\xff\xfe" + original + tail
    if len(body) % 2 == 0:
        body += b"#"
    (code_repo.path / CODE_FILE).write_bytes(body)
    done = cli(code_repo)
    assert _not_read(done.stdout) == 1
    if cited:
        assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
        assert f"unpublished-not-admitted {CODE_FILE}:" in done.stdout
        assert "ALSO COULD NOT JUDGE - 1 tracked file not read" in done.stdout
    else:
        assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr


def test_a_bom_file_decoding_to_a_nul_still_grades_its_bytes(code_repo: Repo) -> None:
    """Strict UTF-16 succeeds but yields a NUL: not read, yet the byte view's citation is red."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    head = _even(b"\xff\xfe" + (code_repo.path / CODE_FILE).read_bytes())
    body = _even(head + b"\x00\x00" + f"\n# RED at {side[:7]}: landed.\n".encode("ascii"))
    assert "\0" in body.decode("utf-16")
    (code_repo.path / CODE_FILE).write_bytes(body)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unpublished-not-admitted {CODE_FILE}:" in done.stdout
    assert _not_read(done.stdout) == 1


def test_an_unpublished_run_beside_a_not_read_file_reports_both_and_exits_one(
    code_repo: Repo,
) -> None:
    """Precedence: the unpublished finding is exit 1, and the not-read file is still printed."""
    side = commit_where(code_repo, lambda sha: _carries_both(sha[:7]), "refs/heads/side")
    plant(code_repo, f"Landed as commit `{side[:7]}` on the merge.")
    (code_repo.path / CODE_FILE).write_bytes(b"\x00binary\x00")
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{side[:7]} unpublished" in done.stdout
    assert _not_read(done.stdout) == 1
    assert "ALSO COULD NOT JUDGE - 1 tracked file not read" in done.stdout


def test_the_inclusion_rule_states_the_not_read_precedence() -> None:
    """The published rule says an unpublished finding outranks a not-read file."""
    assert "an unpublished finding outranks it" in gate.INCLUSION_RULE


def test_a_run_over_forty_holding_an_unpublished_sha_is_stated_not_judged(
    code_repo: Repo,
) -> None:
    """A 41-character run is no sha1 name git resolves: counted as NOT JUDGED, never passed."""
    before = _not_judged(cli(code_repo).stdout, "w41+")
    side = commit_where(code_repo, lambda _sha: True, "refs/heads/side")
    plant(code_repo, f"digest {side}0 recorded", CODE_FILE)
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert _not_judged(done.stdout, "w41+") == before + 1


def test_every_run_states_each_width_class_it_does_not_judge(code_repo: Repo) -> None:
    """Each not-judged width class is printed with its count and reason, even at zero."""
    done = cli(code_repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert set(gate.NOT_JUDGED) == {"w4", "w41+"}
    for name, reason in gate.NOT_JUDGED.items():
        assert f" - {reason}" in done.stdout, name
        assert _not_judged(done.stdout, name) >= 0


def test_the_inclusion_rule_states_the_code_and_short_width_rules() -> None:
    """The published rule names the code sweep and the short and over-long widths."""
    rule = gate.INCLUSION_RULE
    for phrase in ("every other tracked file", "5 or 6", "41 or more", "NOT JUDGED"):
        assert phrase in rule, phrase


# --- the live arm -------------------------------------------------------------


def test_this_tree_cites_only_published_commits() -> None:
    """The gate passes on this tree - and a tree it cannot judge FAILS here, never skips.

    CI runs this module only in full-history save shards, so a shallow
    checkout or a checkout with no origin/main and no tag there is a broken premise,
    reported as red rather than as a skip that reads like a pass.
    """
    report = gate.sweep(REPO_ROOT)
    assert not report.shallow, "CS-1222 live arm needs full history: this clone is shallow"
    published = report.published_refs
    assert published > 0, "CS-1222 live arm needs a published ref: no origin/main or tag"
    unresolved = [f"{e.path}:{e.line} {e.token} {state}" for e, state in report.unresolved]
    assert unresolved == []
    overreach = [f"{e.rule} {e.path}:{e.line} {e.token}" for e in report.overreach]
    assert overreach == []
    assert report.unused == []
    runs = [f"{e.path}:{e.line} {e.token}" for e in report.not_admitted_unpublished]
    assert runs == []
    admitted = len(report.admitted)
    assert admitted > 0
    code_files = report.code_files
    assert code_files > 0
    not_read = list(report.not_read)
    assert not_read == []
    verdict = report.verdict()
    assert verdict == gate.EXIT_CLEAN


# --- CS-700 S7a survival: the state-witnessed historical set ------------------
#
# A throwaway repository is REWRITTEN the way S7a rewrites this one: the same
# trees are replayed under a new author with ``git commit-tree``, ``main`` and
# ``origin/main`` move to the replay, and the old commits are expired out of
# the TEMP store. A doc citing an old commit must then pass when its token is
# on the generated historical set, and only then.
#
# The gate PINS its set: the set's SHA-256 and the witness pair are constants
# in the gate's own source. So each throwaway repository tracks its OWN copy of
# the gate under test, with the witness pair of that repository written in,
# and every arm runs that copy - never this tree's gate, whose pins name this
# tree's set.

#: The synthetic identity the replay commits under - never a real one.
_REPLAY_ROLE: Final = "Replayed"

#: A fixed date, so every commit of the arms is reproducible.
_FIXED_DATE: Final = "2026-01-01T00:00:00+0000"

#: The same date as git writes it into a commit object: epoch seconds and offset.
_FIXED_STAMP: Final = "1767225600 +0000"

#: Where a throwaway repository tracks its copy of the gate, and of its resolver.
_OWN_GATE: Final = "tools/sha_citation_gate.py"
_OWN_TOOLPATH: Final = "tools/toolpath.py"

#: The adversary's laundering plant: a typo-shaped sha no store holds.
_SMUGGLED: Final = "badc0de"


def _commit_env(repo: Repo, name: str) -> dict[str, str]:
    env = dict(repo.env)
    for role in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{role}_NAME"] = name
        env[f"GIT_{role}_EMAIL"] = f"{name.lower()}@example.invalid"
        env[f"GIT_{role}_DATE"] = _FIXED_DATE
    return env


def _replay(repo: Repo, old: str, parents: list[str]) -> str:
    """``old``'s tree and message, re-committed under the replay identity onto ``parents``."""
    tree = repo.git("rev-parse", f"{old}^{{tree}}")
    message = repo.git("log", "-1", "--format=%B", old)
    args = ["git", "commit-tree", tree, "-m", message]
    for parent in parents:
        args += ["-p", parent]
    done = subprocess.run(
        args,
        cwd=repo.path,
        env=_commit_env(repo, _REPLAY_ROLE),
        capture_output=True,
        timeout=TIMEOUT,
        check=True,
    )
    return done.stdout.decode("ascii").strip()


def _replay_name(repo: Repo, old: str) -> str:
    """The name ``_replay(repo, old, [])`` WILL produce, computed without storing it.

    A held but unpublished witness image would itself be an unpublished commit
    the gate copy cites; the real tree's store does not hold the image either.
    """
    tree = repo.git("rev-parse", f"{old}^{{tree}}")
    message = repo.git("log", "-1", "--format=%B", old)
    ident = f"{_REPLAY_ROLE} <{_REPLAY_ROLE.lower()}@example.invalid> {_FIXED_STAMP}"
    body = f"tree {tree}\nauthor {ident}\ncommitter {ident}\n\n{message}\n"
    done = subprocess.run(
        ["git", "hash-object", "-t", "commit", "--stdin"],
        cwd=repo.path,
        env=repo.env,
        input=body.encode("ascii"),
        capture_output=True,
        timeout=TIMEOUT,
        check=True,
    )
    return done.stdout.decode("ascii").strip()


def _commit_all(repo: Repo, message: str) -> str:
    subprocess.run(
        ["git", "-c", "core.autocrlf=false", "commit", "-q", "-m", message],
        cwd=repo.path,
        env=_commit_env(repo, "Synthetic"),
        capture_output=True,
        timeout=TIMEOUT,
        check=True,
    )
    return repo.git("rev-parse", "HEAD")


def _write_historical(repo: Repo, pre: str, post: str, tokens: list[str]) -> None:
    body = (
        "{\n"
        '  "schema": 1,\n'
        f'  "witness": {{"pre": "{pre}", "post": "{post}"}},\n'
        '  "tokens": [' + ", ".join(f'"{token}"' for token in tokens) + "]\n"
        "}\n"
    )
    target = repo.path / gate.HISTORICAL_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body.encode("ascii"))


def _witness_block(pre: str, post: str) -> str:
    return f'WITNESS: Final = (\n    "{pre}",\n    "{post}",\n)\n'


def _own_gate(repo: Repo, pre: str, post: str) -> None:
    """Track a copy of the gate under test whose WITNESS pin is ``(pre, post)``."""
    source = GATE_SOURCE.read_bytes().decode("ascii")
    block = _witness_block(*gate.WITNESS)
    assert source.count(block) == 1, "control: the gate must carry one WITNESS block"
    target = repo.path / _OWN_GATE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.replace(block, _witness_block(pre, post)).encode("ascii"))
    shutil.copyfile(GATE_SOURCE.parent / "toolpath.py", repo.path / _OWN_TOOLPATH)


def _pin(repo: Repo) -> None:
    """Re-pin the repository's gate copy to its set's CURRENT bytes - a deliberate re-pin."""
    target = repo.path / _OWN_GATE
    digest = hashlib.sha256((repo.path / gate.HISTORICAL_FILE).read_bytes()).hexdigest()
    source = target.read_bytes().decode("ascii")
    pinned = gate.repin_source(source, digest)
    target.write_bytes(pinned.encode("ascii"))


def own(repo: Repo, *args: str) -> Run:
    """Run the repository's OWN gate copy against it, in a fresh interpreter."""
    done = subprocess.run(
        [sys.executable, "-B", str(repo.path / _OWN_GATE), "--repo", str(repo.path), *args],
        env=repo.env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    return Run(done.returncode, done.stdout, done.stderr)


def _own_module(repo: Repo) -> ModuleType:
    """Import the repository's own gate copy, for the in-process arms."""
    name = f"clockspeed_own_gate_{hashlib.sha256(str(repo.path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, repo.path / _OWN_GATE)
    if spec is None or spec.loader is None:
        message = "could not load the gate copy"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _listed(repo: Repo) -> list[str]:
    loaded = gate.load_historical(repo.path)
    assert loaded is not None, "control: the historical set must be present"
    return sorted(loaded.tokens)


@dataclass
class Rewrite:
    """A repository in the PRE state, and the commits the S7a replay will touch."""

    repo: Repo
    old_a: str
    new_a: str
    old_b: str
    cited: str


def _pre_state(tmp_path: Path) -> Rewrite:
    """A PRE-state repository: ``A`` published, its replay ``A'`` not even held.

    ``A`` is the witness ``pre``, ``A'`` the witness ``post``, both pinned in
    the repository's own gate copy; a doc in ``B`` cites ``A``, and the copy's
    ``--emit-historical`` has listed that citation and pinned the set's digest.
    """
    path = tmp_path / "rewrite"
    path.mkdir()
    repo = Repo(path, _env(tmp_path))
    repo.git("init", "-q")
    (path / "README.md").write_bytes(b"A seed doc that cites nothing.\n")
    repo.git("add", "--", "README.md")
    old_a = _commit_all(repo, "seed")
    new_a = _replay_name(repo, old_a)
    held = repo.lacks(new_a)
    assert held, "control: the witness image must not be held in the PRE store"
    cited = mixed(old_a)
    (path / "docs").mkdir()
    (path / "docs" / "notes.md").write_bytes(f"Landed as commit `{cited}`.\n".encode("ascii"))
    _own_gate(repo, old_a, new_a)
    repo.git("add", "--", "docs/notes.md", _OWN_GATE, _OWN_TOOLPATH)
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    emitted = own(repo, "--emit-historical")
    assert emitted.returncode == gate.EXIT_CLEAN, emitted.stdout + emitted.stderr
    repo.git("add", "--", gate.HISTORICAL_FILE, _OWN_GATE)
    old_b = _commit_all(repo, "cite A")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    return Rewrite(repo, old_a, new_a, old_b, cited)


def _rewrite(state: Rewrite) -> str:
    """Replay ``A`` and ``B``, move main and origin/main, expire every old commit."""
    repo = state.repo
    new_a = _replay(repo, state.old_a, [])
    reproduced = new_a == state.new_a
    assert reproduced, "control: the replay must reproduce the pinned image"
    new_b = _replay(repo, state.old_b, [new_a])
    branch = repo.git("symbolic-ref", "HEAD")
    repo.git("update-ref", branch, new_b)
    repo.git("update-ref", "refs/remotes/origin/main", new_b)
    repo.git("reflog", "expire", "--expire=now", "--all")
    repo.git("gc", "--prune=now", "-q")
    gone = repo.lacks(state.old_a) and repo.lacks(state.old_b)
    assert gone, "control: the expired old commits must be absent from the temp store"
    return new_b


@pytest.fixture
def pre(tmp_path: Path) -> Rewrite:
    """A repository in the PRE state, its historical set emitted, pinned and committed."""
    return _pre_state(tmp_path)


def test_emit_lists_the_published_citation_and_pins_its_digest(pre: Rewrite) -> None:
    """The emitted set holds the cited token and the witness, ASCII and LF, and is pinned."""
    listed = _listed(pre.repo)
    assert listed == sorted([pre.cited, pre.old_a])
    raw = (pre.repo.path / gate.HISTORICAL_FILE).read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"}\n")
    pinned = _own_module(pre.repo).HISTORICAL_SHA256
    assert pinned == hashlib.sha256(raw).hexdigest()


def test_the_pre_state_passes(pre: Rewrite) -> None:
    """Before the rewrite, every listed token is a published commit: exit 0."""
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert "historical PRE" in done.stdout


def test_a_rewritten_citation_on_the_set_survives_the_rewrite(pre: Rewrite) -> None:
    """THE S7a ARM: after the replay and the expiry, the old citation passes as historical."""
    _rewrite(pre)
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert "historical POST" in done.stdout


def test_an_old_sha_not_on_the_set_stays_red_after_the_rewrite(pre: Rewrite) -> None:
    """A citation of an expired commit the set does not list is refused by name."""
    _rewrite(pre)
    old = mixed(pre.old_b)
    plant(pre.repo, f"Also landed as `{old}`.", "docs/notes.md")
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{old} never-resolved" in done.stdout


def test_a_new_absent_citation_outside_the_set_is_red_after_the_rewrite(pre: Rewrite) -> None:
    """A citation of a sha no store holds, outside the set, is red in the POST state."""
    _rewrite(pre)
    plant(pre.repo, f"Landed as commit `{ABSENT_SHA}`.", "docs/notes.md")
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


def test_a_token_smuggled_into_the_set_by_hand_is_refused(pre: Rewrite) -> None:
    """F1 - POST laundering: a hand-added token breaks the pinned digest, named by file.

    Control: the same set DELIBERATELY re-pinned in the gate passes, so the
    digest - and nothing else - is what refused the smuggled token.
    """
    _rewrite(pre)
    absent = pre.repo.lacks(_SMUGGLED)
    assert absent, "control: the smuggled sha must be absent from the store"
    plant(pre.repo, f"Landed as commit `{_SMUGGLED}`.", "docs/notes.md")
    _write_historical(pre.repo, pre.old_a, pre.new_a, sorted([pre.cited, pre.old_a, _SMUGGLED]))
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"historical-digest-mismatch {gate.HISTORICAL_FILE}" in done.stdout
    _pin(pre.repo)
    repinned = own(pre.repo)
    assert repinned.returncode == gate.EXIT_CLEAN, repinned.stdout + repinned.stderr


def test_a_witness_pair_differing_from_the_gate_is_refused(pre: Rewrite) -> None:
    """F2 - a swapped witness, even re-pinned, would read PRE as POST; the gate refuses it."""
    _write_historical(pre.repo, pre.new_a, pre.old_a, [])
    _pin(pre.repo)
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"historical-witness-mismatch {gate.HISTORICAL_FILE}" in done.stdout


def test_a_listed_token_resolving_to_a_published_commit_after_the_rewrite_is_red(
    pre: Rewrite,
) -> None:
    """POST: a listed token naming a published commit is a collision, never history."""
    new_b = _rewrite(pre)
    collide = mixed(new_b)
    _write_historical(pre.repo, pre.old_a, pre.new_a, sorted([pre.cited, pre.old_a, collide]))
    _pin(pre.repo)
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"historical-collision {collide}" in done.stdout


def test_a_listed_token_not_resolving_before_the_rewrite_is_red(pre: Rewrite) -> None:
    """PRE: every listed token must name a published commit - and listing exempts nothing.

    The stale token is also CITED, so the arm sees the PRE state exempt no
    citation as history: it is still reported unresolved beside the stale line.
    """
    absent = pre.repo.lacks(ABSENT_SHA)
    assert absent, "control: the listed sha must be absent from the store"
    _write_historical(pre.repo, pre.old_a, pre.new_a, sorted([pre.cited, pre.old_a, ABSENT_SHA]))
    _pin(pre.repo)
    plant(pre.repo, f"Landed as commit `{ABSENT_SHA}`.", "docs/notes.md")
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"historical-stale {ABSENT_SHA}" in done.stdout
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


def test_both_witnesses_published_cannot_judge(pre: Rewrite) -> None:
    """Both witnesses published reads as neither state: exit 2."""
    image = _replay(pre.repo, pre.old_a, [])
    pre.repo.git("tag", "both", image)
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert "historical BOTH" in done.stdout


def test_neither_witness_published_cannot_judge(pre: Rewrite) -> None:
    """Neither witness published - a gate and set from another history - exits 2."""
    first, second = "1" * FULL_SHA_WIDTH, "2" * FULL_SHA_WIDTH
    _own_gate(pre.repo, first, second)
    _write_historical(pre.repo, first, second, [pre.cited])
    _pin(pre.repo)
    done = own(pre.repo)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert "historical NEITHER" in done.stdout


def test_emit_refuses_outside_the_pre_state(pre: Rewrite) -> None:
    """Regenerating after the rewrite would empty the set, so emit exits 2 and writes nothing."""
    _rewrite(pre)
    before = (pre.repo.path / gate.HISTORICAL_FILE).read_bytes()
    pin_before = (pre.repo.path / _OWN_GATE).read_bytes()
    done = own(pre.repo, "--emit-historical")
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    after = (pre.repo.path / gate.HISTORICAL_FILE).read_bytes()
    assert after == before
    pin_after = (pre.repo.path / _OWN_GATE).read_bytes()
    assert pin_after == pin_before


def test_emit_refuses_a_tree_that_is_not_its_own(pre: Rewrite, tmp_path: Path) -> None:
    """A gate pins only the set beside it: emit against ANOTHER tree exits 2, writing nothing.

    The foreign gate is a byte-copy of the tree's own - the same WITNESS, so the
    tree reads PRE to it - kept OUTSIDE the tree: only the own-file check refuses it.
    """
    foreign = tmp_path / "foreign" / _OWN_GATE
    foreign.parent.mkdir(parents=True)
    shutil.copyfile(pre.repo.path / _OWN_GATE, foreign)
    shutil.copyfile(pre.repo.path / _OWN_TOOLPATH, foreign.parent / "toolpath.py")
    before = (pre.repo.path / gate.HISTORICAL_FILE).read_bytes()
    foreign_before = foreign.read_bytes()
    done = subprocess.run(
        [sys.executable, "-B", str(foreign), "--repo", str(pre.repo.path), "--emit-historical"],
        env=pre.repo.env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    code = done.returncode
    assert code == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    after = (pre.repo.path / gate.HISTORICAL_FILE).read_bytes()
    assert after == before
    foreign_after = foreign.read_bytes()
    assert foreign_after == foreign_before


def test_flip_readiness_passes_only_with_no_citation_outside_the_set(pre: Rewrite) -> None:
    """Readiness is 0 on the emitted set, and 1 once a published citation sits outside it."""
    ready = own(pre.repo, "--flip-readiness")
    assert ready.returncode == gate.EXIT_CLEAN, ready.stdout + ready.stderr
    longer = mixed(pre.old_a, 12)
    line = plant(pre.repo, f"The longer name is `{longer}`.", "docs/notes.md")
    outside = own(pre.repo, "--flip-readiness")
    assert outside.returncode == gate.EXIT_UNRESOLVED, outside.stdout + outside.stderr
    assert f"flip-outside docs/notes.md:{line} {longer}" in outside.stdout


def test_flip_readiness_refuses_outside_the_pre_state(pre: Rewrite) -> None:
    """Readiness after the rewrite has nothing to measure: exit 2."""
    _rewrite(pre)
    done = own(pre.repo, "--flip-readiness")
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr


def test_the_witness_image_on_the_allowlist_is_not_overreach_after_the_rewrite(
    pre: Rewrite,
) -> None:
    """POST: the allowlisted witness image is published by design; any OTHER row still reddens."""
    new_b = _rewrite(pre)
    image = mixed(pre.new_a)
    other = mixed(new_b)
    plant(pre.repo, f"Image `{image}` and tip `{other}`.", "docs/notes.md")
    allow = {image: "foreign-pin", other: "foreign-pin"}
    report = _own_module(pre.repo).sweep(pre.repo.path, allowlist=allow)
    flagged = sorted(entry.token for entry in report.overreach)
    assert flagged == [other]
    verdict = report.verdict()
    assert verdict == gate.EXIT_UNRESOLVED


def test_the_witness_image_on_the_allowlist_is_overreach_without_the_set(
    pre: Rewrite,
) -> None:
    """Control: with no historical set, the same published image row IS overreach, as today."""
    _rewrite(pre)
    image = mixed(pre.new_a)
    plant(pre.repo, f"Image `{image}`.", "docs/notes.md")
    (pre.repo.path / gate.HISTORICAL_FILE).unlink()
    report = _own_module(pre.repo).sweep(pre.repo.path, allowlist={image: "foreign-pin"})
    flagged = [entry.token for entry in report.overreach]
    assert flagged == [image]


def test_this_tree_ships_its_historical_set() -> None:
    """The tracked set exists, parses, names this tree's witness and matches the pinned digest."""
    listed = gate.load_historical(REPO_ROOT)
    assert listed is not None
    witness = listed.witness
    assert witness == gate.WITNESS
    count = len(listed.tokens)
    assert count > 0
    digest = hashlib.sha256((REPO_ROOT / gate.HISTORICAL_FILE).read_bytes()).hexdigest()
    pinned = gate.HISTORICAL_SHA256
    assert digest == pinned
