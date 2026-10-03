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
* THE LIVE ARM runs the gate over this tree and FAILS - never skips - when the
  tree is shallow or has no origin/main and no tag, and fails on an unused
  table row.
  CI runs this module only in the full-history save shard of
  ``.github/workflows/tier1.yml``.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
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


# --- the live arm -------------------------------------------------------------


def test_this_tree_cites_only_published_commits() -> None:
    """The gate passes on this tree - and a tree it cannot judge FAILS here, never skips.

    CI runs this module only in the full-history save shard, so a shallow
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
    admitted = len(report.admitted)
    assert admitted > 0
    assert report.verdict() == gate.EXIT_CLEAN
