"""CS-955 - the pre-commit gate must grade exactly the index git commits.

THE DEFECT. ``.githooks/pre-commit`` ran ``tools/precommit_gate.py --staged``
against the LIVE index, and git builds the commit from the index it RE-READS
after the hook returns. A stage that lands while the gate is running is
therefore committed without ever being graded - CS-954's shape one level down.

THE FIRST REPAIR WAS REFUTED. It listed the live index before and after the
gate and refused on a difference. An entry REMOVED while the gate read the
index and RESTORED before the second listing (an A-B-A excursion) left both
listings equal, so the gate graded an index without that entry and git then
committed it ungraded.

THE ROUTE TAKEN, under the G-955 addendum recorded in ``docs/LEDGER.md``: the
hook copies the index git handed it into a snapshot inside the git dir, runs
the gate against the SNAPSHOT, and after the gate-ran proof refuses unless the
snapshot listing before the gate, the snapshot listing after it and the live
listing are identical. What git commits is then exactly what the gate graded,
or the commit is refused.

HOW THE MID-HOOK EVENTS ARE MADE DETERMINISTIC. The sandbox's
``tools/precommit_gate.py`` is a STAND-IN this module writes. The hook runs it
exactly where it runs the real gate, so it executes strictly between the
listings, with no sleep and no timer. Under the snapshot design the index the
stand-in INHERITS is the snapshot, so the LIVE index path comes from the TEST
(``CS955_LIVE``), never from the hook: plain commit the git dir's ``index``,
``commit -a`` its ``index.lock``, a pathspec commit its single
``next-index-*.lock``. A separate arm measures that model against git itself
with a trivial hook, because every other arm rests on it.

THE MATRIX. Plain, ``commit -a`` and pathspec commits for every arm, with a
committing control per shape. Every commit, whatever its outcome, is followed
by a check that no snapshot survived in the git dir.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. ``tmp_path`` sits under the user
profile, so the stand-in's report is reduced to bools, ints and repo-relative
listings before anything is asserted on.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.git_env import scrub

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOK_PATH: Final = REPO_ROOT / ".githooks" / "pre-commit"
TRACKED_GATE: Final = REPO_ROOT / "tools" / "precommit_gate.py"
PRE_COMMIT: Final = "pre-commit"

GIT_TIMEOUT: Final = 180
SANDBOX_BRANCH: Final = "cs955-sandbox"
FIXTURE_NAME: Final = "CS-955 Fixture"
FIXTURE_EMAIL: Final = "cs955@example.invalid"

HOOK_BANNER: Final = "clockspeed pre-commit"
ENVIRONMENT_REPR: Final = "<environment withheld>"

#: The words each refusal carries, so an arm pins WHICH rule refused.
INDEX_MOVED: Final = "the index MOVED while the gate ran"
SNAPSHOT_MOVED: Final = "the SNAPSHOT the gate graded changed while the gate ran"
GATE_BLOCKED: Final = "BLOCKED (gate exit"
GATE_DID_NOT_RUN: Final = "the gate DID NOT RUN"
REDUCTION_FAILED: Final = "could not be reduced"

#: The snapshot's name prefix, which the grant fixes.
SNAPSHOT_PREFIX: Final = "cs-precommit-index."

#: The sandbox files. ``tracked.txt`` is the change every shape commits;
#: ``keep.txt`` is a tracked bystander the mode and removal advances act on;
#: ``advance.txt`` is untracked until an advance stages it.
TRACKED: Final = "tracked.txt"
KEEP: Final = "keep.txt"
ADVANCE: Final = "advance.txt"
REPORT_NAME: Final = "stand-in-report.json"

ORIGINAL: Final = b"the seeded line\n"
CHANGED: Final = b"the line the commit is meant to carry\n"

ADVANCE_ENV: Final = "CS955_ADVANCE"
REPORT_ENV: Final = "CS955_REPORT"
LIVE_ENV: Final = "CS955_LIVE"
GLOB_PREFIX: Final = "glob:"
NEXT_INDEX_GLOB: Final = "next-index-*.lock"

#: The stand-in the hook runs in place of the gate. It records what it
#: inherited, acts on the index it is told to, and then prints the real gate's
#: success banner as its last stdout line - except for the kinds whose point is
#: a gate that refuses or a gate that never proves it ran.
STAND_IN: Final = r'''"""CS-955 sandbox stand-in for the gate. Written by the test."""

import glob
import json
import os
import signal
import subprocess
import sys

KIND = os.environ.get("CS955_ADVANCE", "")
SPEC = os.environ["CS955_LIVE"]
if SPEC.startswith("glob:"):
    FOUND = sorted(glob.glob(SPEC[len("glob:"):]))
    LIVE = FOUND[0] if len(FOUND) == 1 else ""
    LIVE_COUNT = len(FOUND)
else:
    LIVE = SPEC
    LIVE_COUNT = 1 if os.path.exists(SPEC) else 0
INHERITED = os.environ.get("GIT_INDEX_FILE", "")


def git(*args, index=None, drop=False):
    env = dict(os.environ)
    if drop:
        env = {k: v for k, v in env.items() if k.upper() != "GIT_INDEX_FILE"}
    elif index is not None:
        env["GIT_INDEX_FILE"] = index
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, timeout=120, check=False, env=env
    )


def listing(index):
    return git("ls-files", "-s", index=index).stdout


def hook_shell_pid():
    """The pid of the shell running the hook, walked up from this process."""
    if os.name == "nt":
        table = subprocess.run(["ps"], capture_output=True, text=True, timeout=60).stdout
        rows = {}
        for line in table.splitlines()[1:]:
            parts = line.split()
            if parts and not parts[0].isdigit():
                parts = parts[1:]
            if len(parts) >= 4 and all(part.isdigit() for part in parts[:4]):
                rows[int(parts[0])] = (int(parts[1]), int(parts[3]))
        mine = [pid for pid, (_, win) in rows.items() if win in (os.getpid(), os.getppid())]
        top = mine[0]
        while rows[top][0] in rows:
            top = rows[top][0]
        return top

    def parent(pid):
        with open("/proc/%d/status" % pid, encoding="ascii", errors="replace") as handle:
            for line in handle:
                if line.startswith("PPid:"):
                    return int(line.split()[1])
        return 0

    def is_hook(pid):
        try:
            with open("/proc/%d/cmdline" % pid, "rb") as handle:
                return b"pre-commit" in handle.read()
        except OSError:
            return False

    top = os.getppid()
    while is_hook(parent(top)):
        top = parent(top)
    return top


report = {
    "ran": 1,
    "inherited": INHERITED,
    "inherited_exists": bool(INHERITED) and os.path.exists(INHERITED),
    "live_count": LIVE_COUNT,
    "graded_equals_live_at_start": bool(LIVE) and listing(INHERITED) == listing(LIVE),
}
live_before = listing(LIVE)
rc = 0
if KIND == "add":
    rc = git("add", "--", "advance.txt", index=LIVE).returncode
elif KIND == "restage":
    with open("tracked.txt", "wb") as handle:
        handle.write(b"a line the gate never graded\n")
    rc = git("add", "--", "tracked.txt", index=LIVE).returncode
elif KIND == "chmod":
    rc = git("update-index", "--chmod=+x", "--", "keep.txt", index=LIVE).returncode
elif KIND == "remove":
    rc = git("rm", "--cached", "-q", "--", "keep.txt", index=LIVE).returncode
elif KIND == "aba":
    rc = git("rm", "--cached", "-q", "--", "tracked.txt", index=LIVE).returncode
    report["graded"] = listing(INHERITED)
    rc |= git("add", "--", "tracked.txt", index=LIVE).returncode
elif KIND == "snapshot":
    rc = git("add", "--", "advance.txt").returncode
elif KIND == "refresh":
    os.utime("keep.txt", ns=(1, 1))
    rc = git("update-index", "-q", "--refresh", index=LIVE).returncode
elif KIND == "ita":
    rc = git("add", "-f", "--", "intent.txt", index=LIVE).returncode
elif KIND == "outsider":
    rc = git("add", "--", "advance.txt", drop=True).returncode
elif KIND == "sigterm":
    pid = hook_shell_pid()
    if os.name == "nt":
        rc = subprocess.run(["kill", "-TERM", str(pid)], timeout=60, check=False).returncode
    else:
        os.kill(pid, signal.SIGTERM)
report["advance_rc"] = rc
report["live_moved"] = listing(LIVE) != live_before
report.setdefault("graded", listing(INHERITED))

with open(os.environ["CS955_REPORT"], "w", encoding="ascii") as handle:
    json.dump(report, handle)

if KIND == "refuse":
    sys.exit(1)
if KIND != "silent":
    sys.stdout.write("precommit_gate: PASS - 1 checked, 0 skipped, 0 blocking\n")
'''

SHAPES: Final = ("plain", "all", "pathspec")
ADVANCES: Final = ("add", "restage", "chmod", "remove")


class Environment(NamedTuple):
    """The child environment, wrapped so no failure report can render it."""

    variables: dict[str, str]

    def __repr__(self) -> str:
        """Render without any of the environment's contents."""
        return ENVIRONMENT_REPR


class Sandbox(NamedTuple):
    """A throwaway repository wired to the tracked pre-commit hook."""

    work: Path
    git_dir: Path
    report: Path
    env: dict[str, str]

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return "<CS-955 sandbox, paths withheld>"


class Outcome(NamedTuple):
    """The measured result of one real ``git commit``, reduced to path-free values."""

    returncode: int
    head_moved: bool
    hook_said: tuple[str, ...]
    stand_in: dict[str, object]
    graded_on_snapshot: bool
    committed: tuple[str, ...]
    snapshots_left: int

    def refused_by(self, words: str) -> bool:
        """Git refused, nothing landed, and the named rule is what refused."""
        refused = self.returncode != 0 and not self.head_moved
        return refused and any(words in line for line in self.hook_said)

    @property
    def accepted(self) -> bool:
        """Git succeeded and a commit landed."""
        return self.returncode == 0 and self.head_moved

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.hook_said) if self.hook_said else "(no hook output)"
        return (
            f"exit={self.returncode} head_moved={self.head_moved} "
            f"on_snapshot={self.graded_on_snapshot} snapshots_left={self.snapshots_left} "
            f"stand_in={self.stand_in} committed_tree={self.committed}\n{shown}"
        )


def hook_output(stderr: str) -> tuple[str, ...]:
    """Keep only the hook's own lines, so no git-rendered path reaches a report."""
    return tuple(
        line
        for line in stderr.split("\n")
        if line.startswith((HOOK_BANNER, "  ")) and line.strip() and ":\\" not in line
    )


def run_git(
    box: Sandbox, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run git inside the sandbox with the operator's own configuration excluded."""
    return subprocess.run(
        ["git", *args],
        cwd=str(box.work),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=box.env if env is None else env,
        check=False,
    )


def head_of(box: Sandbox) -> str:
    """The current HEAD commit id."""
    return run_git(box, "rev-parse", "HEAD").stdout.strip()


def tree_of_head(box: Sandbox) -> tuple[str, ...]:
    """Mode, object id and path of every entry HEAD's tree carries."""
    listed = run_git(box, "ls-tree", "-r", "HEAD").stdout
    return tuple(line for line in listed.split("\n") if line)


def as_tree(listing: str) -> tuple[str, ...]:
    """An ``ls-files -s`` listing rendered as ``ls-tree -r`` would render it."""
    rows = []
    for line in listing.split("\n"):
        if not line:
            continue
        meta, path = line.split("\t", 1)
        mode, oid, _stage = meta.split(" ")
        rows.append(f"{mode} blob {oid}\t{path}")
    return tuple(rows)


def blob_id(box: Sandbox, content: bytes) -> str:
    """The object id git gives ``content``, computed without writing it."""
    proc = subprocess.run(
        ["git", "hash-object", "--stdin"],
        cwd=str(box.work),
        input=content,
        capture_output=True,
        timeout=GIT_TIMEOUT,
        env=box.env,
        check=False,
    )
    return proc.stdout.decode("ascii").strip()


def snapshots_left(box: Sandbox) -> int:
    """How many snapshot files remain in the git dir."""
    return len(list(box.git_dir.glob(SNAPSHOT_PREFIX + "*")))


def read_report(box: Sandbox) -> tuple[dict[str, object], bool]:
    """What the stand-in wrote, with its inherited path reduced to one bool.

    The bool is whether the stand-in was graded against a snapshot: a file
    whose name carries the fixed prefix, directly inside the git dir, that
    existed while the stand-in ran.
    """
    if not box.report.exists():
        return {}, False
    try:
        raw = json.loads(box.report.read_text("ascii"))
    except json.JSONDecodeError:
        # The recording hook of the model arm writes a bare path, not JSON.
        return {}, False
    inherited = str(raw.pop("inherited", ""))
    located = False
    if inherited:
        path = Path(inherited)
        if not path.is_absolute():
            path = box.work / path
        located = path.parent.resolve() == box.git_dir.resolve()
        located = located and path.name.startswith(SNAPSHOT_PREFIX)
    return raw, located and bool(raw.get("inherited_exists"))


def live_spec(box: Sandbox, shape: str) -> str:
    """The LIVE index git hands the hook for ``shape``, as the test knows it."""
    if shape == "plain":
        return str(box.git_dir / "index")
    if shape == "all":
        return str(box.git_dir / "index.lock")
    return GLOB_PREFIX + (box.git_dir / NEXT_INDEX_GLOB).as_posix()


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment with the operator's own git configuration excluded."""
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    env.pop("CLOCKSPEED_PYTHON", None)
    env.pop(ADVANCE_ENV, None)
    env[REPORT_ENV] = str(tmp_path / REPORT_NAME)
    return Environment(env)


def make_sandbox(
    tmp_path: Path, isolated: Environment, *, hook: bytes | None = None, real_gate: bool = False
) -> Sandbox:
    """A real repository with a hook wired and the gate stand-in in place.

    The seed commit is made with ``--no-verify`` on purpose: the hook under test
    is not what the seed is for, and a hook refusal there would read as a
    sandbox that cannot commit.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    installed = hooks / PRE_COMMIT
    installed.write_bytes(HOOK_PATH.read_bytes() if hook is None else hook)
    installed.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()
    box = Sandbox(
        work=work, git_dir=work / ".git", report=tmp_path / REPORT_NAME, env=isolated.variables
    )

    started = run_git(box, "init", "-q", "-b", SANDBOX_BRANCH)
    assert started.returncode == 0, "the throwaway repository could not be initialised"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(hooks)),
    ):
        written = run_git(box, "config", key, value)
        assert written.returncode == 0, f"{key} could not be written in the sandbox"
    readback = run_git(box, "config", "--get", "core.hooksPath")
    took = readback.returncode == 0 and readback.stdout.strip() == str(hooks)
    assert took, "core.hooksPath did not take in the sandbox"

    (work / TRACKED).write_bytes(ORIGINAL)
    (work / KEEP).write_bytes(b"a bystander\n")
    staged = run_git(box, "add", "--", TRACKED, KEEP)
    assert staged.returncode == 0, "the sandbox seed could not be staged"
    seeded = run_git(box, "commit", "-q", "--no-verify", "-m", "CS-955 sandbox seed")
    assert seeded.returncode == 0, "the sandbox could not make its first commit"

    # UNTRACKED ON PURPOSE. The hook loads the gate from the working tree, and
    # neither `commit -a` nor a pathspec commit picks up an untracked file.
    (work / "tools").mkdir()
    gate = work / "tools" / "precommit_gate.py"
    if real_gate:
        shutil.copy2(TRACKED_GATE, gate)
    else:
        gate.write_bytes(STAND_IN.encode("ascii"))
    (work / ADVANCE).write_bytes(b"a path nobody staged before the hook ran\n")
    return box


def commit_env(box: Sandbox, shape: str, advance: str) -> dict[str, str]:
    """The sandbox environment telling the stand-in what to do and where.

    A function rather than a local, so no frame that asserts ever holds the
    environment the sandbox withholds from its repr.
    """
    env = dict(box.env)
    env[ADVANCE_ENV] = advance
    env[LIVE_ENV] = live_spec(box, shape)
    return env


def commit_in_shape(box: Sandbox, shape: str, advance: str, content: bytes = CHANGED) -> Outcome:
    """Change ``tracked.txt``, then drive one real commit of ``shape``."""
    (box.work / TRACKED).write_bytes(content)
    if box.report.exists():
        box.report.unlink()
    message = ["-m", "CS-955: an ordinary subject"]
    if shape == "plain":
        staged = run_git(box, "add", "--", TRACKED).returncode == 0
        assert staged, "the change could not be staged"
        args = ["commit", *message]
    elif shape == "all":
        args = ["commit", "-a", *message]
    else:
        args = ["commit", *message, "--", TRACKED]

    before = head_of(box)
    proc = run_git(box, *args, env=commit_env(box, shape, advance))
    after = head_of(box)
    stand_in, on_snapshot = read_report(box)
    return Outcome(
        returncode=proc.returncode,
        head_moved=before != after,
        hook_said=hook_output(proc.stderr),
        stand_in=stand_in,
        graded_on_snapshot=on_snapshot,
        committed=tree_of_head(box),
        snapshots_left=snapshots_left(box),
    )


# --- the model every arm rests on, measured against git itself ----------------


#: A hook that records which index git hands it and does nothing else.
RECORDING_HOOK: Final = b'#!/bin/sh\nprintf \'%s\' "$GIT_INDEX_FILE" > "$CS955_REPORT"\nexit 0\n'


@pytest.mark.parametrize("shape", SHAPES)
def test_git_hands_the_hook_the_index_file_the_stand_in_is_told_about(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """Plain: the real index. ``-a``: ``index.lock``. Pathspec: one next-index lock."""
    box = make_sandbox(tmp_path, isolated, hook=RECORDING_HOOK)
    outcome = commit_in_shape(box, shape, "")
    in_git_dir, name = handed_index(box)
    if shape == "pathspec":
        named = re.fullmatch(r"next-index-[0-9]+\.lock", name) is not None
    else:
        named = name == Path(live_spec(box, shape)).name
    assert outcome.accepted, outcome.report
    assert in_git_dir, "git handed the hook an index outside the git dir"
    assert named, "git handed the hook an index file of another name: " + name


def handed_index(box: Sandbox) -> tuple[bool, str]:
    """Whether the recorded index sits in the git dir, and its bare file name."""
    handed = box.report.read_text("ascii").strip()
    path = Path(handed) if Path(handed).is_absolute() else box.work / handed
    return path.parent.resolve() == box.git_dir.resolve(), path.name


# --- the refusals -------------------------------------------------------------


@pytest.mark.parametrize("shape", SHAPES)
def test_an_entry_removed_and_restored_mid_gate_commits_only_as_graded(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """The refuted A-B-A race: the gate must have graded the restored entry.

    Red on the compare-only candidate: the gate read the live index while the
    entry was gone, both listings matched afterwards, and git committed the
    entry ungraded.
    """
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, "aba")

    assert outcome.stand_in.get("ran") == 1, outcome.report
    assert outcome.stand_in.get("advance_rc") == 0, outcome.report
    graded = as_tree(str(outcome.stand_in.get("graded", "")))
    carried = f"100644 blob {blob_id(box, CHANGED)}\t{TRACKED}"
    in_graded_view = carried in graded
    assert in_graded_view, outcome.report
    as_graded = outcome.accepted and outcome.committed == graded
    assert as_graded or outcome.refused_by(INDEX_MOVED), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


@pytest.mark.parametrize("advance", ADVANCES)
@pytest.mark.parametrize("shape", SHAPES)
def test_an_index_advanced_mid_hook_is_blocked_rather_than_committed(
    tmp_path: Path, isolated: Environment, shape: str, advance: str
) -> None:
    """A live index that moves and stays moved is REFUSED, HEAD unmoved."""
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, advance)

    # PRESENCE IS NOT FIRING. The stand-in ran and its advance really moved
    # the live index - otherwise a block proves nothing.
    assert outcome.stand_in.get("ran") == 1, outcome.report
    assert outcome.stand_in.get("live_count") == 1, outcome.report
    assert outcome.stand_in.get("advance_rc") == 0, outcome.report
    assert outcome.stand_in.get("live_moved") is True, outcome.report

    assert outcome.refused_by(INDEX_MOVED), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


@pytest.mark.parametrize("shape", SHAPES)
def test_a_write_into_the_graded_snapshot_is_refused(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """The gate's own index changing under it is refused, not graded twice."""
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, "snapshot")

    assert outcome.stand_in.get("advance_rc") == 0, outcome.report
    assert outcome.refused_by(SNAPSHOT_MOVED), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


@pytest.mark.parametrize("shape", SHAPES)
def test_an_unadvanced_commit_of_each_shape_lands_graded_on_a_snapshot(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """The control, and the location arm: the gate read a snapshot in the git dir.

    The snapshot also listed exactly what the live index git handed the hook
    listed when the gate started, which is what ties the test's live path to
    the index the hook copied.
    """
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, "")

    assert outcome.stand_in.get("ran") == 1, outcome.report
    assert outcome.graded_on_snapshot, outcome.report
    assert outcome.stand_in.get("live_count") == 1, outcome.report
    assert outcome.stand_in.get("graded_equals_live_at_start") is True, outcome.report
    assert outcome.accepted, outcome.report
    carried = f"100644 blob {blob_id(box, CHANGED)}\t{TRACKED}"
    assert carried in outcome.committed, outcome.report
    assert not any(line.endswith("\t" + ADVANCE) for line in outcome.committed), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


@pytest.mark.parametrize("shape", SHAPES)
def test_a_benign_refresh_of_the_live_index_mid_gate_does_not_refuse(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """Stat data is not what git commits, so a refresh rewriting it must not refuse.

    The stand-in makes a tracked file stat-dirty and refreshes the live index,
    which rewrites that entry's stat fields and nothing else. The listing keeps
    the flags and drops the stat fields; one that kept them would refuse here.
    """
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, "refresh")

    assert outcome.stand_in.get("advance_rc") == 0, outcome.report
    assert outcome.stand_in.get("live_moved") is False, outcome.report
    assert outcome.accepted, outcome.report
    assert outcome.snapshots_left == 0, outcome.report


# --- an intent-to-add entry made real under the gate ---------------------------

#: An empty file registered with ``git add -N``. Its ``ls-files -s`` line is
#: byte-identical to a real empty-file entry; only the index flags differ.
INTENT: Final = "intent.txt"


def register_intent(box: Sandbox) -> bool:
    """Register an empty file as intent-to-add in the real index."""
    (box.work / INTENT).write_bytes(b"")
    return run_git(box, "add", "-N", "-f", "--", INTENT).returncode == 0


def test_an_intent_to_add_entry_made_real_mid_gate_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """The intent-to-add swap: the flags differ, so the listings must.

    PLAIN COMMIT ONLY, by construction: `commit -a` stages an intent-to-add
    entry for real before the hook runs, and a pathspec commit builds its index
    from HEAD, so neither hands the hook an intent-to-add entry to swap. Red on
    the stat-free `ls-files -s` listing: the gate never graded the entry, whose
    line did not change, and git committed it.
    """
    box = make_sandbox(tmp_path, isolated)
    registered = register_intent(box)
    assert registered, "the intent-to-add entry could not be registered"
    outcome = commit_in_shape(box, "plain", "ita")

    assert outcome.stand_in.get("advance_rc") == 0, outcome.report
    assert outcome.refused_by(INDEX_MOVED), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


def test_an_intent_to_add_entry_left_alone_does_not_refuse(
    tmp_path: Path, isolated: Environment
) -> None:
    """The control: an untouched intent-to-add entry lists the same every time."""
    box = make_sandbox(tmp_path, isolated)
    registered = register_intent(box)
    assert registered, "the intent-to-add entry could not be registered"
    outcome = commit_in_shape(box, "plain", "")

    assert outcome.accepted, outcome.report
    assert not any(line.endswith("\t" + INTENT) for line in outcome.committed), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


# --- the reduction fails closed -----------------------------------------------

REDUCTION_HEAD: Final = "cs_index_view() {"

#: Stubs for the reduction: print nothing, and return failure or success. The
#: second is the sharper one - only the empty-view check can catch it.
REDUCTION_STUBS: Final = {
    "fails": "    return 1",
    "prints-nothing": "    return 0",
}


def stubbed_hook(stub: str) -> bytes:
    """The tracked hook with the reduction's body replaced by ``stub``.

    Asserts the copy differs from the tracked hook ONLY inside the function, so
    a refusal cannot come from anything else.
    """
    lines = HOOK_PATH.read_text("ascii").split("\n")
    start = lines.index(REDUCTION_HEAD)
    end = lines.index("}", start)
    patched = [*lines[: start + 1], stub, *lines[end:]]
    untouched = patched[: start + 1] == lines[: start + 1] and patched[start + 2 :] == lines[end:]
    assert untouched, "the stub touched more than the reduction's body"
    assert patched != lines, "the stub changed nothing"
    return "\n".join(patched).encode("ascii")


@pytest.mark.parametrize("stub", sorted(REDUCTION_STUBS))
@pytest.mark.parametrize("shape", SHAPES)
def test_a_failed_reduction_refuses_rather_than_comparing_empty_views(
    tmp_path: Path, isolated: Environment, shape: str, stub: str
) -> None:
    """Fault injection: a reduction that yields nothing must refuse, not pass.

    Red on the here-document candidate: three empty views compared equal and
    the commit landed with nothing compared at all.
    """
    box = make_sandbox(tmp_path, isolated, hook=stubbed_hook(REDUCTION_STUBS[stub]))
    outcome = commit_in_shape(box, shape, "")

    assert outcome.refused_by(REDUCTION_FAILED), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


# --- the snapshot never survives a run ----------------------------------------

#: Kinds whose run ends on a path other than a pass or an index mismatch.
EXIT_PATHS: Final = {
    "refuse": GATE_BLOCKED,
    "silent": GATE_DID_NOT_RUN,
}


@pytest.mark.parametrize("kind", sorted(EXIT_PATHS))
@pytest.mark.parametrize("shape", SHAPES)
def test_no_snapshot_survives_a_gate_refusal_or_a_die(
    tmp_path: Path, isolated: Environment, shape: str, kind: str
) -> None:
    """The gate's own refusal and the gate-ran proof's die both clean up."""
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, kind)

    assert outcome.stand_in.get("ran") == 1, outcome.report
    assert outcome.refused_by(EXIT_PATHS[kind]), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


@pytest.mark.parametrize("shape", SHAPES)
def test_a_hook_sent_sigterm_mid_gate_blocks_and_leaves_no_snapshot(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """The signal trap: a TERM to the hook's shell while the gate runs.

    The stand-in signals the shell running the hook and then finishes
    normally. The hook must not commit, and its traps must remove the snapshot.
    """
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, "sigterm")

    assert outcome.stand_in.get("advance_rc") == 0, outcome.report
    refused = outcome.returncode != 0 and not outcome.head_moved
    assert refused, outcome.report
    assert outcome.snapshots_left == 0, outcome.report


# --- the real gate grades what -a and a pathspec commit carry ----------------


WORKTREE_SHAPES: Final = ["all", "pathspec"]


@pytest.mark.parametrize("shape", WORKTREE_SHAPES)
def test_a_violation_only_in_the_worktree_is_blocked_by_the_real_gate(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """Nothing staged beforehand: only the index git builds carries the violation.

    A snapshot copied from the git dir's plain ``index`` would hold the seeded
    clean bytes and pass; one copied from the index git handed the hook holds
    the violation and is blocked.
    """
    box = make_sandbox(tmp_path, isolated, real_gate=True)
    violation = ("a line with an e acute " + chr(0xE9) + "\n").encode("utf-8")
    outcome = commit_in_shape(box, shape, "", content=violation)

    assert outcome.refused_by(GATE_BLOCKED), outcome.report
    assert outcome.snapshots_left == 0, outcome.report


# --- the declared window, measured -------------------------------------------

#: Per shape, whether an ordinary concurrent `git add` - one that does NOT
#: inherit GIT_INDEX_FILE - reaches the index git will commit. MEASURED: a plain
#: commit hands the hook the real index with its lock already released, so an
#: outsider reaches it; `commit -a` and a pathspec commit hold `index.lock` for
#: the whole hook, so the outsider is refused by the lock.
OUTSIDER_REACHES: Final = {"plain": True, "all": False, "pathspec": False}


@pytest.mark.parametrize("shape", SHAPES)
def test_an_ordinary_concurrent_stage_reaches_the_index_only_on_a_plain_commit(
    tmp_path: Path, isolated: Environment, shape: str
) -> None:
    """The measurement behind the declared post-hook window.

    Where the outsider reaches the live index mid-hook, the hook refuses. The
    same outsider landing AFTER the hook's last listing and before git re-reads
    the index is the window the grant says to declare, not claim. Where the
    lock refuses the outsider, the commit lands without its change.
    """
    box = make_sandbox(tmp_path, isolated)
    outcome = commit_in_shape(box, shape, "outsider")

    assert outcome.stand_in.get("ran") == 1, outcome.report
    reached = outcome.stand_in.get("advance_rc") == 0
    assert reached is OUTSIDER_REACHES[shape], outcome.report
    if reached:
        assert outcome.stand_in.get("live_moved") is True, outcome.report
        assert outcome.refused_by(INDEX_MOVED), outcome.report
    else:
        assert outcome.stand_in.get("live_moved") is False, outcome.report
        assert outcome.accepted, outcome.report
        assert not any(line.endswith("\t" + ADVANCE) for line in outcome.committed)
    assert outcome.snapshots_left == 0, outcome.report


# --- the listings, read from the hook ------------------------------------------

LISTING_LINE: Final = re.compile(r"^(CS_INDEX_[A-Z]+)=\$\((.*)\)$")
SNAPSHOT_LISTING: Final = 'GIT_INDEX_FILE="$CS_INDEX_SNAP" git ls-files -s --debug'
LIVE_LISTING: Final = "git ls-files -s --debug"
REDUCTION: Final = 'cs_index_view "$CS_INDEX_RAW"'

#: Commands that write an index. The grant forbids every one of them in the hook.
INDEX_WRITERS: Final = ("write-tree", "update-index", "read-tree")


def listing_commands() -> list[tuple[str, str]]:
    """Every index listing and reduction the hook takes, in file order."""
    found: list[tuple[str, str]] = []
    for line in HOOK_PATH.read_text("ascii").split("\n"):
        matched = LISTING_LINE.match(line)
        if matched and matched.group(1) != "CS_INDEX_SNAP":
            found.append((matched.group(1), matched.group(2)))
    return found


def test_the_hook_lists_the_snapshot_twice_and_the_live_index_once() -> None:
    """Each raw listing is ``ls-files -s --debug``, each reduced before comparing."""
    assert listing_commands() == [
        ("CS_INDEX_RAW", SNAPSHOT_LISTING),
        ("CS_INDEX_BEFORE", REDUCTION),
        ("CS_INDEX_RAW", SNAPSHOT_LISTING),
        ("CS_INDEX_AFTER", REDUCTION),
        ("CS_INDEX_RAW", LIVE_LISTING),
        ("CS_INDEX_LIVE", REDUCTION),
    ]


def test_no_line_of_the_hook_runs_an_index_writing_command() -> None:
    """The snapshot is written by ``cp`` only, and the live index never."""
    code = [
        line
        for line in HOOK_PATH.read_text("ascii").split("\n")
        if line.strip() and not line.lstrip().startswith("#")
    ]
    writers = [line for line in code if any(word in line for word in INDEX_WRITERS)]
    assert writers == []


def test_the_live_listing_the_hook_takes_does_not_rewrite_the_index(
    tmp_path: Path, isolated: Environment
) -> None:
    """The grant forbids a listing that rewrites the index git handed the hook.

    The index is made stat-dirty first, which is exactly the state in which a
    refreshing command would rewrite it. The hook's own live-listing command is
    then run and the index bytes compared. THE CONTROL runs a refreshing
    command in the same state and requires the bytes to CHANGE, so the arm
    cannot pass on an index nothing would have rewritten.
    """
    box = make_sandbox(tmp_path, isolated)
    os.utime(box.work / KEEP, ns=(1, 1))
    before = index_bytes(box)
    command = next(
        cmd for name, cmd in listing_commands() if name == "CS_INDEX_RAW" and "SNAP" not in cmd
    )
    proc = subprocess.run(
        ["sh", "-c", command],
        cwd=str(box.work),
        capture_output=True,
        timeout=GIT_TIMEOUT,
        env=box.env,
        check=False,
    )
    listed = proc.returncode == 0 and bool(proc.stdout)
    assert listed, "the listing failed or printed nothing, so it measured nothing"
    untouched = index_bytes(box) == before
    assert untouched, "the hook's index listing rewrote the index"

    refreshed = run_git(box, "update-index", "-q", "--refresh").returncode
    rewritten = index_bytes(box) != before
    assert rewritten, f"control: a refresh (exit {refreshed}) left the index as it was"


def index_bytes(box: Sandbox) -> bytes:
    """The sandbox's real index file, byte for byte."""
    return (box.git_dir / "index").read_bytes()


def test_the_stand_in_compiles() -> None:
    """The stand-in is plain ASCII Python, so a sandbox failure is never a typo."""
    compile(STAND_IN, "stand-in", "exec")
