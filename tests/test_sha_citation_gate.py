"""CS-1222 - a doc carrying an unpublished or unresolvable commit sha turns a guard red.

WHAT THIS GRADES. ``tools/sha_citation_gate.py`` resolves every sha-shaped
citation its published inclusion rule admits with ``git rev-parse --verify -q
<sha>^{commit}`` and counts it only when the commit is reachable from a
PUBLISHED ref (``refs/remotes/origin/main`` or a tag). The arms here:

* THE PLANT ARMS run in a throwaway repository holding a byte-copy of a guarded
  doc, tracked there too so the gate's own discovery finds it, with its one
  commit published as ``refs/remotes/origin/main``. One plants a sha the
  throwaway store provably lacks and demands the refusal BY NAME; one plants a
  commit that exists only on a local branch, and one only on a remote SIDE
  branch, and demands ``unpublished`` for both; one
  plants the published commit, short and full, and demands a pass - so the gate
  is not merely refusing every hex run.
* THE ANTI-ESCAPE ARMS: a token an exclusion rule swallows that IS a published
  commit reddens the gate (overreach); ``path at <sha>`` in a copy of
  ``docs/LEDGER.md`` is refused rather than read as a foreign pin; a ``hash``
  label on the PREVIOUS line exempts nothing.
* THE EMPTY ARMS: a sweep that admits nothing, and a repository with no
  published ref, exit "could not judge", never 0.
* THE CLASS ARMS: each stated exclusion rule is fed a line shaped like the
  measured population it exists for, and the SAME token on a bare line is the
  control that must be admitted.
* THE REPORT ARMS: the inclusion rule (with what it does not admit), every
  exclusion class with its count, and the filter-repo discriminator's
  availability are printed on every run.
* THE SHALLOW ARM: a shallow clone cannot judge, so it says so and exits 2.
* THE LIVE ARM runs the gate over this tree and FAILS - never skips - when the
  tree is shallow or has no published ref. CI runs this module only in the
  full-history save shard of ``.github/workflows/tier1.yml``.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
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


# --- the plant arms -----------------------------------------------------------


def test_an_unresolvable_sha_in_a_guarded_doc_is_refused_by_name(repo: Repo) -> None:
    """A planted sha the object store lacks makes the gate exit 1 and name it."""
    assert repo.lacks(ABSENT_SHA), "control: the planted sha must be absent from the store"
    plant(repo, f"Landed as commit `{ABSENT_SHA}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"unresolved {GUARDED_DOC}:" in done.stdout
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


@pytest.mark.parametrize("ref", ["refs/heads/local-only", "refs/remotes/origin/side"])
def test_an_unpublished_commit_is_refused(repo: Repo, ref: str) -> None:
    """A commit on a local branch or a remote SIDE branch resolves here and is refused."""
    tree = repo.git("write-tree")
    side = repo.git("commit-tree", tree, "-p", "HEAD", "-m", "not on main")
    repo.git("update-ref", ref, side)
    plant(repo, f"Landed as commit `{side[:9]}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{side[:9]} unpublished" in done.stdout


def test_a_tagged_commit_is_published(repo: Repo) -> None:
    """A commit reachable only from a tag counts as published."""
    tree = repo.git("write-tree")
    tagged = repo.git("commit-tree", tree, "-p", "HEAD", "-m", "tagged")
    repo.git("tag", "v-synthetic", tagged)
    plant(repo, f"Landed as commit `{tagged[:9]}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr


@pytest.mark.parametrize("width", [7, FULL_SHA_WIDTH])
def test_a_published_sha_in_a_guarded_doc_passes(repo: Repo, width: int) -> None:
    """The throwaway's published commit, short and full, is admitted and passes."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"Landed as commit `{head[:width]}` on the merge.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert "admitted 1 " in done.stdout
    assert "unresolved 0; overreach 0" in done.stdout


def test_sweep_api_matches_the_cli_on_a_plant(repo: Repo) -> None:
    """The in-process sweep reports the same unresolved citation the CLI does."""
    plant(repo, f"See `{ABSENT_SHA}`.")
    report = gate.sweep(repo.path)
    assert [(entry.token, state) for entry, state in report.unresolved] == [
        (ABSENT_SHA, "never-resolved")
    ]
    assert report.verdict() == gate.EXIT_UNRESOLVED


# --- the anti-escape arms -------------------------------------------------------


def test_an_excluded_token_that_is_a_published_commit_reddens_the_gate(repo: Repo) -> None:
    """A rule that swallows a real published commit is overreach, and overreach fails."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"the measured digest `{head[:10]}` first.")
    plant(repo, f"Landed as `{head}` on the merge.")
    done = cli(repo)
    assert "excluded-count content-digest 1" in done.stdout, done.stdout
    assert f"overreach content-digest {GUARDED_DOC}:" in done.stdout
    assert done.returncode == gate.EXIT_UNRESOLVED


def test_path_at_an_unresolvable_sha_in_a_ledger_copy_is_refused(tmp_path: Path) -> None:
    """``path at <sha>`` is a citation, not a foreign pin - in a copy of the ledger."""
    made = _make(tmp_path, LEDGER_DOC)
    (made.path / "docs" / "adr").mkdir()
    assert made.lacks(ABSENT_SHA)
    planted = {
        plant(made, f"`tools/precommit_gate.py` at {ABSENT_SHA} was byte-identical.", LEDGER_DOC),
        plant(made, f"Measured docs/adr at {ABSENT_SHA}, clean.", LEDGER_DOC),
        plant(made, f"fast-forwarded to origin/main at {ABSENT_SHA}.", LEDGER_DOC),
    }
    done = cli(made)
    assert done.returncode == gate.EXIT_UNRESOLVED
    refused = {
        int(line.split()[1].rsplit(":", 1)[1])
        for line in done.stdout.splitlines()
        if line.startswith(f"unresolved {LEDGER_DOC}:") and f" {ABSENT_SHA} " in line
    }
    assert refused == planted


def test_a_hash_label_on_the_previous_line_exempts_nothing(repo: Repo) -> None:
    """A keyword one line up no longer reaches the token: the citation is refused."""
    plant(repo, f"assert `git hash-object x` is\n`{ABSENT_SHA}` before measuring.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_UNRESOLVED, done.stdout + done.stderr
    assert f"{ABSENT_SHA} never-resolved" in done.stdout


def test_a_blob_in_the_store_is_excluded_as_a_git_object(repo: Repo) -> None:
    """A token naming a blob in this store is the verified half of the git-blob rule."""
    blob = repo.git("hash-object", "--", GUARDED_DOC)
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"The hook file `{blob[:10]}` is unchanged; landed as `{head}`.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert f"excluded git-blob {GUARDED_DOC}:" in done.stdout


# --- the empty arms -----------------------------------------------------------


def test_an_empty_sweep_is_never_a_pass(repo: Repo) -> None:
    """The unplanted copy admits nothing, and that is reported as could-not-judge."""
    done = cli(repo)
    assert "admitted 0 " in done.stdout, done.stdout
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE


def test_no_published_ref_cannot_judge(tmp_path: Path) -> None:
    """With nothing under refs/remotes or refs/tags, nothing counts as published."""
    made = _make(tmp_path, GUARDED_DOC, publish=False)
    plant(made, f"Landed as `{made.git('rev-parse', 'HEAD')}`.")
    done = cli(made)
    assert done.returncode == gate.EXIT_COULD_NOT_JUDGE, done.stdout + done.stderr
    assert "resolver NO-PUBLISHED-REF" in done.stdout


# --- the class arms: each stated rule against its measured shape -----------------


CLASS_CASES: Final = [
    ("agent-id", "branch worktree-agent-ace624231ac7fd814 is halted", "ace624231ac7fd814"),
    ("guid", "`3f2504e0-4f89-11d3-9a0c-0305e82c3301` braceless GUID", "3f2504e0"),
    ("compound-name", "note `2026-09-19-from-CS-e085b4a92ab2-sweep.md` merged", "e085b4a92ab2"),
    ("foreign-pin", "Gate run at archify@72c750bb: MIT, two holders", "72c750bb"),
    ("foreign-pin", "**PIN.** someone/somerepo at 5bca2948959a7fb5, retrieved", "5bca2948959a7fb5"),
    ("git-blob", "byte-identical, blob `d90c7876`, verified by hash", "d90c7876"),
    ("content-digest", "reported measured digest `fc22e86e` against", "fc22e86e"),
    ("content-digest", "sha256 `899f6eb9...05f4c6b` re-hashed from this disk", "05f4c6b"),
    ("truncation", "and none carries `f1b4b011...`. The carriers", "f1b4b011"),
    ("run-id", 'cycle 1, "run_id": "e085d9aa", "outcome"', "e085d9aa"),
    ("run-id", "lane run `62f29b90` on the night started late", "62f29b90"),
    ("run-id", "Exactly ONE: run id `5ff0ddfd`, 13:02:03", "5ff0ddfd"),
    ("fixture-vector", "| `a1b2c3d4e5f60718` | Epic-shaped hex | redacted |", "a1b2c3d4e5f60718"),
]


@pytest.mark.parametrize(("rule", "text", "token"), CLASS_CASES)
def test_each_stated_rule_excludes_its_measured_shape(rule: str, text: str, token: str) -> None:
    """The rule names the class on its shape, and the bare token is admitted."""
    assert rule in gate.EXCLUSION_RULES, f"{rule} is not a published rule"
    found = {entry.token: entry.rule for entry in gate.scan_text(text)}
    assert found.get(token, "absent") == rule
    control = {entry.token: entry.rule for entry in gate.scan_text(f"Merged as `{token}`.")}
    if rule == "fixture-vector":
        # The vector rule is a property of the token itself, so the bare control
        # still excludes it; the control here is that it is the SAME rule.
        assert control.get(token, "absent") == rule
    else:
        assert control.get(token, "absent") is None, f"{token} is excluded on a bare line"


@pytest.mark.parametrize(
    "text",
    [
        "fast-forwarded to origin/main at 0dbf309 with an empty status",
        "the gate `tools/precommit_gate.py` at 0dbf309 was identical",
        "the tree clockspeed/save/x at 0dbf309 held it",
        "the digest arm reported measured `0dbf309` against",
        "assert `git hash-object x` is\n`0dbf309` first",
        "`0dbf309` is the row this document is named after",
    ],
)
def test_near_miss_shapes_are_admitted(text: str) -> None:
    """A remote ref, a path, a non-adjacent label and an unlabelled site are all admitted."""
    rules = [entry.rule for entry in gate.scan_text(text, root=REPO_ROOT)]
    assert rules == [None]


def test_a_label_in_one_place_does_not_carry_to_another_site() -> None:
    """No file-wide label propagation: the bare second site is admitted."""
    text = "Exactly ONE: run id `5ff0ddfd`, 13:02:03.\n\n`5ff0ddfd` is the row named here.\n"
    assert [entry.rule for entry in gate.scan_text(text)] == ["run-id", None]


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


# --- the report arms ----------------------------------------------------------


def test_every_run_publishes_its_rule_its_exclusions_and_its_discriminator(repo: Repo) -> None:
    """Inclusion rule, every class with its count, resolver and discriminator lines."""
    head = repo.git("rev-parse", "HEAD")
    plant(repo, f"Landed as `{head}`; worktree-agent-ace624231ac7fd814 built it.")
    done = cli(repo)
    assert done.returncode == gate.EXIT_CLEAN, done.stdout + done.stderr
    assert gate.INCLUSION_RULE in done.stdout
    for rule in gate.EXCLUSION_RULES:
        assert f"excluded-count {rule} " in done.stdout, rule
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
    checkout or a checkout with no published ref there is a broken premise,
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
    admitted = len(report.admitted)
    assert admitted > 0
    assert report.verdict() == gate.EXIT_CLEAN
