"""CS-814 - no shipped hook path echoes the environment, proven by driving every one.

THE RULE this module grades is owned by CLAUDE.md non-negotiable 13 and is not
restated here. This module is the PROBE half of CS-814's acceptance.

HOW THE PROOF WORKS. Every child this module spawns inherits the real
environment PLUS several synthetic credential-shaped canaries - named like the
kinds that actually sit in a developer's environment, valued with markers made
fresh from ``secrets`` at import time. Nothing here reads, prints or compares a
real credential: the only thing ever counted is how often a MARKER appears in a
child's combined stdout and stderr. Each arm reduces a run to scalars - an exit
status, a marker count and a bool saying the run reached the path it names -
before anything is asserted, so no assertion here can render an environment
value (the CS-1199 rule in ``tests/test_assertion_rendering.py``).

WHAT IS DRIVEN. The git hooks run under REAL ``git`` in a throwaway repository
whose ``core.hooksPath`` points at copies of the tracked hooks, with the
operator's own git configuration cut off. ``tools/claude_hook.sh`` is driven the
way the harness drives it: a shell runs it with the tool and its arguments and a
JSON envelope arrives on stdin. One arm per hook program per refusal CLASS:

    pre-commit and tools/precommit_gate.py
        pass; charset refusal; secret refusal; syntax refusal; the probe failing;
        PYTHONINSPECT; no usable python; the gate crashing with its
        CLOCKSPEED_CRASH_TRACEBACK opt-in engaged
    commit-msg
        accept; placeholder, non-ASCII and over-long subjects; the probe
        failing; no usable python
    pre-push and the pytest it runs
        pass; a FAILING test that holds every canary in a local; the floor;
        zero collected; no importable pytest; the probe failing; no usable python
    claude_hook.sh with tools/pretooluse_gate.py and tools/edit_lint_check.py
        allow; em dash deny; secret deny; lint pass; lint refusal; lint crash
        with the traceback opt-in; the probe failing; no usable python

PYTHONINSPECT is driven on pre-commit alone. The probe and ladder it exercises
are byte-identical across the four carriers, pinned by the carriage arms of
``tests/test_claude_hook.py``, and on Windows each run waits out the ten second
probe bound - one arm buys the class, four would buy the same class four times.

THE PRE-PUSH SANDBOX CARRIES THE REAL ``pyproject.toml`` AND ``tests/conftest.py``
(with the ``tests/git_env.py`` it imports), so the shipped pytest configuration
and the shipped report redaction are what the pushed suite runs under. The
inherited ``PYTEST_*`` variables are left as they are, as the hook leaves them,
with one exception: ``PYTEST_ADDOPTS`` is unset, because what an inherited
addopts can make the nested run render is CS-1205 and out of this item's scope.

THE CRASH ARMS reach each crash handler from OUTSIDE, without a test hook in a
frozen file: a ``sitecustomize`` first on PYTHONPATH replaces
``argparse.ArgumentParser`` with a function that raises, and both tools build
their parser inside ``main``.

THE ANTI-VACUITY CONTROLS. A probe that finds nothing proves nothing unless the
SAME harness is measured finding something. Each control installs a copy of a
tracked hook differing from it by exactly one inserted ``env >&2`` line and
asserts every canary IS found.

TWO STATIC ARMS. The shell scan reads the four shell carriers for constructs that
render the environment. The PYTHON arm is an ALLOWLIST, AST-level, over every
repository program the hooks run - discovered from the hooks and
``.claude/settings.json`` and followed through their repository imports - plus
every inline program the shell carriers embed, and every repository python
program they launch as a literal child. A blocklist of rendering shapes was
REFUTED: three mutants leaked a canary through real hooks while it stayed green.
So every read by name must resolve to an allowlisted key - personal values only
inside the one function that needs them - the whole environment may only become
a subprocess ``env=``, aliases and dynamic code are refused, and a child command
must be literal words that neither dump nor expand the environment. The rules
and the review table sit at the arm itself. It is proven against each refuted
mutant planted into the shipped source, and by a synthetic control per shape.

THE STATIC BOUNDARY, stated rather than implied. The tests tree is OUT of the
static scope, although pre-push runs it: assertion rendering there is graded by
CS-1199 in ``tests/test_assertion_rendering.py``, and a non-assert echo in a test
is CS-1206. The driven pre-push arms still run the shipped conftest. DECLARED
RESIDUALS: deliberate obfuscation - a key or a command assembled at run time
beyond what the resolver follows, or indirection through another process - and
an ``env=`` handed to a program that is not python or not a literal, whose own
handling of the environment this arm cannot read.

The CLOCKSPEED_PYTHON refusal's rendering of candidate output is graded by the
``test_probe_refusal_output`` module beside this one.
"""

from __future__ import annotations

import ast
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.git_env import scrub
from tests.pre_push_floor import with_test_floor
from tests.test_pretooluse_gate import EM_DASH, PEM_HEADER, envelope, require_posix_shell

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOKS_DIR: Final = REPO_ROOT / ".githooks"
WRAPPER: Final = REPO_ROOT / "tools" / "claude_hook.sh"
SETTINGS: Final = REPO_ROOT / ".claude" / "settings.json"
GATE: Final = REPO_ROOT / "tools" / "precommit_gate.py"
PRETOOL: Final = REPO_ROOT / "tools" / "pretooluse_gate.py"
LINT: Final = REPO_ROOT / "tools" / "edit_lint_check.py"

PRE_COMMIT: Final = "pre-commit"
COMMIT_MSG: Final = "commit-msg"
PRE_PUSH: Final = "pre-push"
SHIPPED_GIT_HOOKS: Final = (PRE_COMMIT, COMMIT_MSG, PRE_PUSH)

#: The shipped files a pre-push sandbox carries, so the real configuration and
#: the real report redaction are what its pytest runs under.
SUITE_SUPPORT: Final = (
    "pyproject.toml",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/git_env.py",
    "clockspeed/__init__.py",
    "clockspeed/data/__init__.py",
    "clockspeed/data/locate.py",
    "clockspeed/save/__init__.py",
    "clockspeed/save/workdir.py",
)

PRE: Final = "pretooluse"
POST: Final = "posttooluse"
DENY: Final = 2

CALL_TIMEOUT: Final = 300
BRANCH: Final = "cs814-sandbox"
FIXTURE_NAME: Final = "CS-814 Fixture"
FIXTURE_EMAIL: Final = "cs814@example.invalid"
GOOD_SUBJECT: Final = b"CS-814 - an ordinary subject that says what changed\n"
PLACEHOLDER_SUBJECT: Final = b"wip\n"
LONG_SUBJECT: Final = b"CS-814 - " + b"a subject far too long to be stored " * 3 + b"\n"
NON_ASCII_SUBJECT: Final = ("CS-814 - a subject with an em " + EM_DASH + " dash\n").encode()

#: Names shaped like the credential kinds a developer environment carries: a
#: forge token under both spellings, a model vendor key, a generic vendor key
#: and a messaging token - and the personal values non-negotiable 13 covers as
#: well, the account name, the profile path and the machine name. Their VALUES
#: are markers made below, never real ones.
CANARY_NAMES: Final = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "ANTHROPIC_API_KEY",
    "CS814_VENDOR_API_KEY",
    "SLACK_BOT_TOKEN",
    "USERNAME",
    "USERPROFILE",
    "COMPUTERNAME",
)

#: One unique marker per canary, fresh each run, so no hook text can carry one
#: by coincidence and no marker ever sits in this file's source.
MARKERS: Final = tuple(f"cs814canary{secrets.token_hex(12)}" for _ in CANARY_NAMES)

#: Variables the probe pins for itself. An inherited copy would steer the ladder
#: or the crash opt-in from outside the arm; PYTEST_ADDOPTS is CS-1205.
PINNED_BY_THE_PROBE: Final = frozenset(
    {
        "CLOCKSPEED_PYTHON",
        "PYTHONPATH",
        "CLOCKSPEED_CRASH_TRACEBACK",
        "PYTHONINSPECT",
        "PYTEST_ADDOPTS",
    }
)

CHATTY_CANDIDATE: Final = b"#!/bin/sh\nprintf 'an argument-ignoring candidate\\n'\nexit 0\n"
FAILING_RUNG: Final = b"#!/bin/sh\nexit 1\n"
LADDER_RUNGS: Final = ("python", "python3", "py")

CRASHING_SITECUSTOMIZE: Final = (
    b"import argparse\n"
    b"\n"
    b"\n"
    b"def _cs814_crash(*args, **kwargs):\n"
    b'    raise RuntimeError("CS-814 synthetic crash")\n'
    b"\n"
    b"\n"
    b"argparse.ArgumentParser = _cs814_crash\n"
)

SHADOW_PYTEST: Final = b'raise ImportError("CS-814 shadow pytest")\n'

PASSING_SUITE: Final = b"def test_passes() -> None:\n    assert True\n"
EMPTY_SUITE: Final = b'"""CS-814 - a module that collects nothing."""\n'
#: A failing test that holds every canary VALUE in a local, so any channel that
#: renders locals has something to render. It fails on an unrelated comparison.
FAILING_SUITE: Final = (
    b"import os\n"
    b"\n"
    b"NAMES = " + repr(CANARY_NAMES).encode("ascii") + b"\n"
    b"\n"
    b"\n"
    b"def test_fails() -> None:\n"
    b'    held = {name: os.environ.get(name, "") for name in NAMES}\n'
    b"    assert 1 == 2\n"
)

CLEAN_FILE: Final = b"an ordinary line of 7-bit ascii\n"
NON_ASCII_FILE: Final = ("a line carrying an em " + EM_DASH + " dash\n").encode("utf-8")
SECRET_FILE: Final = (PEM_HEADER + "\n").encode("ascii")
SYNTAX_ERROR_MODULE: Final = b"def f(:\n    pass\n"
NUL_FILE: Final = b"# Notes\n\na line with a NUL \x00 byte inside it\n"
CLEAN_MODULE: Final = b'"""A clean module."""\n'
NON_ASCII_MODULE: Final = ('"""A module carrying an em ' + EM_DASH + ' dash."""\n').encode("utf-8")

#: The one line the anti-vacuity controls insert, and the line it goes after.
DUMP_LINE: Final = b"env >&2"
ANCHOR_LINE: Final = b"set -u"

TRACEBACK: Final = b"Traceback (most recent call last)"
PRE_COMMIT_BLOCKED: Final = b"clockspeed pre-commit: BLOCKED"
NO_PYTHON: Final = b"no usable python interpreter found"
#: Bound to a name so a type checker on either platform sees both arms as live.
INSPECT_PROBE_HANGS: Final = sys.platform == "win32"
REFUSED_WRAPPER: Final = b"REFUSED (CS-815)"


class Outcome(NamedTuple):
    """One driven run, reduced to scalars before anything is asserted."""

    returncode: int
    hits: int
    found: int
    reached: bool


class Run(NamedTuple):
    """One commit or push attempt: its status, its output, and whether it landed."""

    code: int
    out: bytes
    landed: bool


def marker_hits(output: bytes) -> tuple[int, int]:
    """Total marker occurrences, and how many distinct markers occur at all."""
    counts = [output.count(marker.encode("ascii")) for marker in MARKERS]
    return sum(counts), sum(1 for count in counts if count)


def outcome(run: Run, reached: bool) -> Outcome:
    """Reduce one run to scalars."""
    hits, found = marker_hits(run.out)
    return Outcome(run.code, hits, found, reached)


def child_env(
    root: Path, extra: dict[str, str] | None = None, path_first: Path | None = None
) -> dict[str, str]:
    """The inherited environment, cut loose from git config, plus every canary."""
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(root / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(root / "absent" / "gitconfig-system")
    for name in [key for key in env if key.upper() in PINNED_BY_THE_PROBE]:
        env.pop(name)
    env.update(zip(CANARY_NAMES, MARKERS, strict=True))
    env.update(extra or {})
    if path_first is not None:
        env["PATH"] = str(path_first) + os.pathsep + env.get("PATH", "")
    return env


def run_git(work: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[bytes]:
    """One git child in the sandbox, bounded and captured."""
    return subprocess.run(
        ["git", *args],
        cwd=str(work),
        capture_output=True,
        env=env,
        timeout=CALL_TIMEOUT,
        check=False,
    )


def git_ok(work: Path, root: Path, *args: str) -> bool:
    """Whether one setup git call succeeded; its output is never kept."""
    return run_git(work, child_env(root), *args).returncode == 0


def rev(work: Path, root: Path, *args: str) -> str:
    """A resolved object name, or the empty string."""
    proc = run_git(work, child_env(root), *args)
    return proc.stdout.decode("ascii", "replace").strip() if proc.returncode == 0 else ""


def tracked_hook(name: str) -> bytes:
    """The tracked bytes of one shipped git hook."""
    return (HOOKS_DIR / name).read_bytes()


def with_dump(raw: bytes) -> bytes:
    """``raw`` with ONE ``env >&2`` line inserted after its first ``set -u`` line."""
    lines = raw.split(b"\n")
    at = lines.index(ANCHOR_LINE) + 1
    return b"\n".join([*lines[:at], DUMP_LINE, *lines[at:]])


def differs_by_the_dump_line_only(copy: bytes, tracked: bytes) -> bool:
    """Whether ``copy`` is ``tracked`` with exactly the one dump line inserted."""
    left = copy.split(b"\n")
    right = tracked.split(b"\n")
    if len(left) != len(right) + 1 or left.count(DUMP_LINE) != right.count(DUMP_LINE) + 1:
        return False
    at = next((i for i, (a, b) in enumerate(zip(left, right, strict=False)) if a != b), None)
    return at is not None and left[at] == DUMP_LINE and left[:at] + left[at + 1 :] == right


def write_executable(path: Path, raw: bytes) -> Path:
    """Materialise one executable file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o755)
    return path


def chatty_candidate(root: Path) -> dict[str, str]:
    """CLOCKSPEED_PYTHON at a candidate that ignores its arguments and prints a line."""
    shim = write_executable(root / "shims" / "chatty.sh", CHATTY_CANDIDATE)
    return {"CLOCKSPEED_PYTHON": shim.as_posix()}


def failing_rungs(root: Path) -> Path:
    """A directory whose every ladder rung exits 1, to be put first on PATH."""
    shadow = root / "failing-rungs"
    for rung in LADDER_RUNGS:
        write_executable(shadow / rung, FAILING_RUNG)
    return shadow


def crash_env(root: Path) -> dict[str, str]:
    """A ``sitecustomize`` that makes every argparse parser raise, plus the opt-in."""
    site = root / "crash-site"
    site.mkdir(exist_ok=True)
    (site / "sitecustomize.py").write_bytes(CRASHING_SITECUSTOMIZE)
    return {"PYTHONPATH": str(site), "CLOCKSPEED_CRASH_TRACEBACK": "1"}


def shadow_pytest_env(root: Path) -> dict[str, str]:
    """A ``pytest`` first on PYTHONPATH that cannot be imported."""
    shadow = root / "shadow-pytest"
    shadow.mkdir(exist_ok=True)
    (shadow / "pytest.py").write_bytes(SHADOW_PYTEST)
    return {"PYTHONPATH": str(shadow)}


def make_repo(root: Path, hooks: dict[str, bytes], suite: bytes | None = None) -> Path:
    """A throwaway repository wired to hook copies, with the real gate in place.

    With a ``suite`` it also carries the shipped pytest configuration and
    conftest, and a bare remote seeded through ``--no-verify`` so a refused push
    can be told apart from one that never reached the hook.
    """
    hooks_dir = root / "hooks"
    hooks_dir.mkdir()
    for name, raw in hooks.items():
        write_executable(hooks_dir / name, raw)
    work = root / "work"
    work.mkdir()
    assert git_ok(work, root, "init", "-q", "-b", BRANCH), "the sandbox could not init"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(hooks_dir)),
    ):
        assert git_ok(work, root, "config", key, value), "a sandbox config key did not write"
    # UNTRACKED ON PURPOSE: the hook loads the gate from the working tree.
    (work / "tools").mkdir()
    shutil.copy2(GATE, work / "tools" / "precommit_gate.py")
    if suite is not None:
        (work / "tests").mkdir()
        for relative in SUITE_SUPPORT:
            (work / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / relative, work / relative)
        (work / "tests" / "test_sandbox.py").write_bytes(suite)
        remote = root / "remote.git"
        assert git_ok(work, root, "init", "-q", "--bare", str(remote)), "no bare remote"
        assert git_ok(work, root, "remote", "add", "origin", str(remote)), "no origin"
        staged = git_ok(work, root, "add", "--", "tests", "clockspeed", "pyproject.toml")
        assert staged, "the seed did not stage"
        seeded = git_ok(work, root, "commit", "-q", "--no-verify", "-m", "CS-814 seed")
        assert seeded, "the seed commit failed"
        pushed = git_ok(work, root, "push", "-q", "--no-verify", "origin", BRANCH)
        assert pushed, "the seed did not reach the remote"
    return work


def commit_through(
    root: Path,
    hooks: dict[str, bytes],
    *,
    message: bytes = GOOD_SUBJECT,
    staged: tuple[str, bytes] = ("staged.txt", CLEAN_FILE),
    extra: dict[str, str] | None = None,
    path_first: Path | None = None,
) -> Run:
    """Stage one file and commit it through the hooks."""
    work = make_repo(root, hooks)
    name, content = staged
    (work / name).write_bytes(content)
    (root / "message.txt").write_bytes(message)
    assert git_ok(work, root, "add", "--", name), "the file did not stage"
    env = child_env(root, extra, path_first)
    proc = run_git(work, env, "commit", "-q", "-F", str(root / "message.txt"))
    moved = bool(rev(work, root, "rev-parse", "--verify", "--quiet", "HEAD"))
    return Run(proc.returncode, proc.stdout + proc.stderr, moved)


def push_through(
    root: Path,
    hook: bytes,
    *,
    suite: bytes = PASSING_SUITE,
    extra: dict[str, str] | None = None,
    path_first: Path | None = None,
) -> Run:
    """Offer one new commit through pre-push; ``landed`` reads the remote itself."""
    work = make_repo(root, {PRE_PUSH: hook}, suite)
    made = git_ok(work, root, "commit", "-q", "--no-verify", "--allow-empty", "-m", "CS-814 offer")
    assert made, "the offered commit failed"
    proc = run_git(work, child_env(root, extra, path_first), "push", "origin", BRANCH)
    local = rev(work, root, "rev-parse", "refs/heads/" + BRANCH)
    listed = rev(work, root, "ls-remote", "origin", "refs/heads/" + BRANCH)
    remote = listed.split()[0] if listed else ""
    return Run(proc.returncode, proc.stdout + proc.stderr, bool(local) and remote == local)


def run_wrapper(
    root: Path,
    wrapper: Path,
    leg: str,
    tool: list[str],
    stdin: bytes,
    extra: dict[str, str] | None = None,
    path_first: Path | None = None,
) -> Run:
    """The harness shape: a shell runs the wrapper, the envelope arrives on stdin."""
    shell = require_posix_shell()
    env = child_env(root, extra)
    env["PATH"] = str(Path(shell).parent) + os.pathsep + env.get("PATH", "")
    if path_first is not None:
        env["PATH"] = str(path_first) + os.pathsep + env["PATH"]
    proc = subprocess.run(
        [shell, str(wrapper), leg, *tool],
        input=stdin,
        capture_output=True,
        env=env,
        cwd=str(root),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    return Run(proc.returncode, proc.stdout + proc.stderr, proc.returncode == 0)


def refused(run: Run, *said: bytes) -> bool:
    """A refusal that landed nothing and names every expected cause."""
    return run.code != 0 and not run.landed and all(words in run.out for words in said)


# --- the git hooks, driven through real git ---------------------------------------


def both_commit_hooks() -> dict[str, bytes]:
    """pre-commit and commit-msg, byte-identical to the tracked hooks."""
    return {name: tracked_hook(name) for name in (PRE_COMMIT, COMMIT_MSG)}


def commit_msg_only() -> dict[str, bytes]:
    """commit-msg alone, so its own bootstrap refusals are reachable."""
    return {COMMIT_MSG: tracked_hook(COMMIT_MSG)}


#: Each gate content refusal: the staged file, its bytes, and the gate's label.
CONTENT_REFUSALS: Final = {
    "pre-commit-blocks-a-non-ascii-file": ("staged.txt", NON_ASCII_FILE, b"CHARSET"),
    "pre-commit-blocks-a-secret": ("staged.txt", SECRET_FILE, b"SECRET"),
    "pre-commit-blocks-a-nul-byte": ("notes.md", NUL_FILE, b"BINARY"),
    "pre-commit-blocks-a-syntax-error": ("broken.py", SYNTAX_ERROR_MODULE, b"SYNTAX"),
}


def drive_pre_commit(arm: str, root: Path) -> Outcome:
    """One pre-commit arm, by name: a gate verdict, or the interpreter bootstrap."""
    hooks = both_commit_hooks()
    if arm in BOOTSTRAP_ARMS:
        return drive_pre_commit_bootstrap(arm, root, hooks)
    if arm == "pre-commit-pass-and-commit-msg-accept":
        run = commit_through(root, hooks)
        return outcome(run, run.code == 0 and run.landed)
    if arm in CONTENT_REFUSALS:
        name, content, label = CONTENT_REFUSALS[arm]
        run = commit_through(root, hooks, staged=(name, content))
        return outcome(run, refused(run, PRE_COMMIT_BLOCKED, label))
    if arm == "pre-commit-gate-crash-with-traceback":
        run = commit_through(root, hooks, extra=crash_env(root))
        return outcome(run, refused(run, b"crashed with RuntimeError", TRACEBACK))
    raise AssertionError("unknown pre-commit arm")


#: The pre-commit arms that exercise the interpreter bootstrap rather than the gate.
BOOTSTRAP_ARMS: Final = frozenset(
    {
        "pre-commit-refuses-a-failed-probe",
        "pre-commit-under-pythoninspect",
        "pre-commit-refuses-with-no-usable-python",
    }
)


def drive_pre_commit_bootstrap(arm: str, root: Path, hooks: dict[str, bytes]) -> Outcome:
    """One pre-commit bootstrap arm: the probe and the ladder, before the gate."""
    if arm == "pre-commit-refuses-a-failed-probe":
        run = commit_through(root, hooks, extra=chatty_candidate(root))
        return outcome(run, refused(run, b"clockspeed pre-commit: CLOCKSPEED_PYTHON is set"))
    if arm == "pre-commit-under-pythoninspect":
        # MEASURED, one named path per platform, never a disjunction (CS-1209).
        # Windows under MSYS: the probe hangs and the bound refuses. ubuntu, CI
        # run 36241835384: the probe returns, but the flag reports a SystemExit
        # and exits 1 for sys.exit(0) and sys.exit(1) alike, and the commit was
        # refused with no usable python - so no rung's probe answered 97 there.
        # Neither measured platform lands.
        run = commit_through(root, hooks, extra={"PYTHONINSPECT": "1"})
        if INSPECT_PROBE_HANGS:
            return outcome(run, refused(run, b"the interpreter probe did not answer within"))
        return outcome(run, refused(run, NO_PYTHON))
    if arm == "pre-commit-refuses-with-no-usable-python":
        run = commit_through(root, hooks, path_first=failing_rungs(root))
        return outcome(run, refused(run, NO_PYTHON))
    raise AssertionError("unknown pre-commit bootstrap arm")


def drive_commit_msg(arm: str, root: Path) -> Outcome:
    """One commit-msg arm, by name."""
    rejected = b"clockspeed commit-msg: REJECTED - "
    if arm == "commit-msg-refuses-a-placeholder":
        run = commit_through(root, both_commit_hooks(), message=PLACEHOLDER_SUBJECT)
        return outcome(run, refused(run, rejected + b"subject 'wip' is a bare placeholder"))
    if arm == "commit-msg-refuses-a-non-ascii-message":
        run = commit_through(root, both_commit_hooks(), message=NON_ASCII_SUBJECT)
        return outcome(run, refused(run, rejected + b"non-ASCII character"))
    if arm == "commit-msg-refuses-a-long-subject":
        run = commit_through(root, both_commit_hooks(), message=LONG_SUBJECT)
        return outcome(run, refused(run, rejected + b"subject line is"))
    if arm == "commit-msg-refuses-a-failed-probe":
        run = commit_through(root, commit_msg_only(), extra=chatty_candidate(root))
        return outcome(run, refused(run, b"clockspeed commit-msg: CLOCKSPEED_PYTHON is set"))
    if arm == "commit-msg-refuses-with-no-usable-python":
        run = commit_through(root, commit_msg_only(), path_first=failing_rungs(root))
        return outcome(run, refused(run, NO_PYTHON))
    raise AssertionError("unknown commit-msg arm")


PRE_COMMIT_ARMS: Final = (
    "pre-commit-pass-and-commit-msg-accept",
    "pre-commit-blocks-a-non-ascii-file",
    "pre-commit-blocks-a-secret",
    "pre-commit-blocks-a-nul-byte",
    "pre-commit-blocks-a-syntax-error",
    "pre-commit-refuses-a-failed-probe",
    "pre-commit-under-pythoninspect",
    "pre-commit-refuses-with-no-usable-python",
    "pre-commit-gate-crash-with-traceback",
)

COMMIT_MSG_ARMS: Final = (
    "commit-msg-refuses-a-placeholder",
    "commit-msg-refuses-a-non-ascii-message",
    "commit-msg-refuses-a-long-subject",
    "commit-msg-refuses-a-failed-probe",
    "commit-msg-refuses-with-no-usable-python",
)


@pytest.mark.parametrize("arm", PRE_COMMIT_ARMS)
def test_no_pre_commit_path_echoes_a_canary(tmp_path: Path, arm: str) -> None:
    """Each pre-commit and gate path, reached, renders no canary."""
    result = drive_pre_commit(arm, tmp_path)
    assert result.reached, f"{arm}: the run did not reach the path it names"
    assert result.hits == 0, f"{arm}: {result.hits} canary occurrence(s) in the hook output"


@pytest.mark.parametrize("arm", COMMIT_MSG_ARMS)
def test_no_commit_msg_path_echoes_a_canary(tmp_path: Path, arm: str) -> None:
    """Each commit-msg refusal, reached, renders no canary."""
    result = drive_commit_msg(arm, tmp_path)
    assert result.reached, f"{arm}: the run did not reach the path it names"
    assert result.hits == 0, f"{arm}: {result.hits} canary occurrence(s) in the hook output"


def drive_push(arm: str, root: Path) -> Outcome:
    """One pre-push arm, by name."""
    tracked = tracked_hook(PRE_PUSH)
    blocked = b"clockspeed pre-push: "
    if arm == "pre-push-pass":
        run = push_through(root, with_test_floor(tracked))
        return outcome(run, run.code == 0 and run.landed)
    if arm == "pre-push-blocks-a-failing-test":
        run = push_through(root, tracked, suite=FAILING_SUITE)
        return outcome(run, refused(run, blocked + b"BLOCKED (pytest exit", b"assert 1 == 2"))
    if arm == "pre-push-blocks-below-the-floor":
        run = push_through(root, tracked)
        return outcome(run, refused(run, b"below the floor"))
    if arm == "pre-push-blocks-zero-collected":
        run = push_through(root, tracked, suite=EMPTY_SUITE)
        return outcome(run, refused(run, blocked + b"pytest collected zero tests"))
    if arm == "pre-push-blocks-without-pytest":
        run = push_through(root, tracked, extra=shadow_pytest_env(root))
        return outcome(run, refused(run, blocked + b"pytest is not available"))
    return drive_push_bootstrap(arm, root, tracked)


def drive_push_bootstrap(arm: str, root: Path, tracked: bytes) -> Outcome:
    """One pre-push bootstrap arm: the probe and the ladder, before the suite."""
    blocked = b"clockspeed pre-push: "
    if arm == "pre-push-refuses-a-failed-probe":
        run = push_through(root, tracked, extra=chatty_candidate(root))
        return outcome(run, refused(run, blocked + b"CLOCKSPEED_PYTHON is set"))
    if arm == "pre-push-refuses-with-no-usable-python":
        run = push_through(root, tracked, path_first=failing_rungs(root))
        return outcome(run, refused(run, NO_PYTHON))
    raise AssertionError("unknown push arm")


PUSH_ARMS: Final = (
    "pre-push-pass",
    "pre-push-blocks-a-failing-test",
    "pre-push-blocks-below-the-floor",
    "pre-push-blocks-zero-collected",
    "pre-push-blocks-without-pytest",
    "pre-push-refuses-a-failed-probe",
    "pre-push-refuses-with-no-usable-python",
)


@pytest.mark.parametrize("arm", PUSH_ARMS)
def test_no_push_hook_path_echoes_a_canary(tmp_path: Path, arm: str) -> None:
    """Each pre-push path, reached, renders no canary - the failing-test arm above all."""
    result = drive_push(arm, tmp_path)
    assert result.reached, f"{arm}: the run did not reach the path it names"
    assert result.hits == 0, f"{arm}: {result.hits} canary occurrence(s) in the hook output"


# --- tools/claude_hook.sh, driven the way the harness drives it -------------------


def drive_wrapper(arm: str, root: Path, wrapper: Path = WRAPPER) -> Outcome:
    """One claude_hook.sh arm, by name."""
    if arm.startswith(PRE):
        return drive_pretooluse(arm, root, wrapper)
    return drive_posttooluse(arm, root, wrapper)


def drive_pretooluse(arm: str, root: Path, wrapper: Path) -> Outcome:
    """One PreToolUse leg arm: ``tools/pretooluse_gate.py`` behind the wrapper."""
    allow = json.dumps(envelope("git status")).encode("utf-8")
    tool = [str(PRETOOL)]
    if arm == "pretooluse-allows":
        run = run_wrapper(root, wrapper, PRE, tool, allow)
        return outcome(run, run.code == 0)
    if arm == "pretooluse-denies-an-em-dash":
        deny = json.dumps(envelope("echo " + EM_DASH)).encode("utf-8")
        run = run_wrapper(root, wrapper, PRE, tool, deny)
        return outcome(run, run.code == DENY and b"CHARSET" in run.out)
    if arm == "pretooluse-denies-a-secret":
        deny = json.dumps(envelope("echo '" + PEM_HEADER + "' > id_rsa")).encode("utf-8")
        run = run_wrapper(root, wrapper, PRE, tool, deny)
        return outcome(run, run.code == DENY and b"SECRET" in run.out)
    if arm == "pretooluse-refuses-a-failed-probe":
        run = run_wrapper(root, wrapper, PRE, tool, allow, chatty_candidate(root))
        return outcome(run, run.code not in (0, DENY) and REFUSED_WRAPPER in run.out)
    if arm == "pretooluse-refuses-with-no-usable-python":
        run = run_wrapper(root, wrapper, PRE, tool, allow, path_first=failing_rungs(root))
        return outcome(run, run.code not in (0, DENY) and REFUSED_WRAPPER in run.out)
    raise AssertionError("unknown pretooluse arm")


def drive_posttooluse(arm: str, root: Path, wrapper: Path) -> Outcome:
    """One PostToolUse leg arm: ``tools/edit_lint_check.py`` behind the wrapper."""
    edited = root / "cs814_edited.py"
    edited.write_bytes(NON_ASCII_MODULE if arm.endswith("non-ascii-file") else CLEAN_MODULE)
    lint = [str(LINT), "--files", str(edited)]
    if arm == "posttooluse-passes":
        run = run_wrapper(root, wrapper, POST, lint, b"{}")
        return outcome(run, run.code == 0)
    if arm == "posttooluse-refuses-a-non-ascii-file":
        run = run_wrapper(root, wrapper, POST, lint, b"{}")
        return outcome(run, run.code != 0 and b"left a problem on disk" in run.out)
    if arm == "posttooluse-crash-with-traceback":
        run = run_wrapper(root, wrapper, POST, lint, b"{}", crash_env(root))
        said = b"guard raised RuntimeError" in run.out and TRACEBACK in run.out
        return outcome(run, run.code != 0 and said)
    if arm == "posttooluse-refuses-a-failed-probe":
        run = run_wrapper(root, wrapper, POST, lint, b"{}", chatty_candidate(root))
        return outcome(run, run.code not in (0, DENY) and REFUSED_WRAPPER in run.out)
    raise AssertionError("unknown posttooluse arm")


WRAPPER_ARMS: Final = (
    "pretooluse-allows",
    "pretooluse-denies-an-em-dash",
    "pretooluse-denies-a-secret",
    "pretooluse-refuses-a-failed-probe",
    "pretooluse-refuses-with-no-usable-python",
    "posttooluse-passes",
    "posttooluse-refuses-a-non-ascii-file",
    "posttooluse-crash-with-traceback",
    "posttooluse-refuses-a-failed-probe",
)


@pytest.mark.parametrize("arm", WRAPPER_ARMS)
def test_no_claude_hook_path_echoes_a_canary(tmp_path: Path, arm: str) -> None:
    """Each leg of the wrapper and the tool it runs, reached, renders no canary."""
    result = drive_wrapper(arm, tmp_path)
    assert result.reached, f"{arm}: the run did not reach the path it names"
    assert result.hits == 0, f"{arm}: {result.hits} canary occurrence(s) in the hook output"


# --- the anti-vacuity controls: the same harness, a hook that DOES dump --------


def test_the_control_hook_copy_differs_by_the_dump_line_alone() -> None:
    """Each control copy is its tracked hook plus exactly the one dump line."""
    for raw in (tracked_hook(PRE_COMMIT), WRAPPER.read_bytes()):
        exact = differs_by_the_dump_line_only(with_dump(raw), raw)
        vacuous = differs_by_the_dump_line_only(raw, raw)
        assert exact, "the control copy moved another byte"
        assert not vacuous, "an unmodified copy passed as a control"


def test_a_pre_commit_copy_that_dumps_the_environment_is_caught(tmp_path: Path) -> None:
    """THE CONTROL for the git harness: every canary IS found, through real git."""
    hooks = {PRE_COMMIT: with_dump(tracked_hook(PRE_COMMIT)), COMMIT_MSG: tracked_hook(COMMIT_MSG)}
    found = outcome(commit_through(tmp_path, hooks), True).found
    total = len(MARKERS)
    assert found == total, (
        f"the git harness found {found} of {total} canaries in a hook that dumps "
        "the environment - the probe arms above prove nothing"
    )


def test_a_wrapper_copy_that_dumps_the_environment_is_caught(tmp_path: Path) -> None:
    """THE CONTROL for the wrapper harness: every canary IS found."""
    dumped = write_executable(
        tmp_path / "dumping" / "claude_hook.sh", with_dump(WRAPPER.read_bytes())
    )
    found = drive_wrapper("pretooluse-allows", tmp_path, dumped).found
    total = len(MARKERS)
    assert found == total, (
        f"the wrapper harness found {found} of {total} canaries in a wrapper that "
        "dumps the environment - the probe arms above prove nothing"
    )


# --- the shell static arm -----------------------------------------------------------

#: Where a shell command word can start: line start, a separator, a substitution,
#: or a keyword that introduces a command.
_CMD: Final = r"(?:^|[;&|({`]|\$\(|\bthen\b|\bdo\b|\belse\b|\bexec\b)\s*"
#: What may follow a command that takes no operand: end, a separator or a redirect.
_END: Final = r"\s*(?:$|[;&|)`>]|[0-9]>)"

#: Each construct that renders the environment, with the label a finding carries.
RENDERING_CONSTRUCTS: Final = (
    ("env with no command", re.compile(_CMD + r"env(?:\s+-[-\w]+)*" + _END)),
    ("printenv", re.compile(r"(?:^|[^\w-])printenv\b")),
    ("export listing", re.compile(_CMD + r"export(?:\s+-p)?" + _END)),
    ("declare or typeset -p", re.compile(r"\b(?:declare|typeset)\s+-[a-zA-Z]*p")),
    ("declare or typeset -x listing", re.compile(r"\b(?:declare|typeset)\s+-[a-zA-Z]*x" + _END)),
    ("bare set", re.compile(_CMD + r"set" + _END)),
    ("set -x", re.compile(r"\bset\s+-[a-zA-Z]*x")),
    ("set -o xtrace", re.compile(r"\bset\s+-o\s+xtrace\b")),
    ("compgen -e", re.compile(r"\bcompgen\s+-[a-zA-Z]*e")),
    ("shell -x", re.compile(r"\b(?:ba|da|z|k)?sh\s+-[a-zA-Z]*x")),
    ("os.environ used whole", re.compile(r"\bos\.environb?\b(?!\s*(?:\.get\s*\(|\[))")),
    ("environ imported bare", re.compile(r"\bfrom\s+os\s+import\b[^#\n]*\benviron")),
)

#: A shebang that switches tracing on for the whole script.
TRACING_SHEBANG: Final = re.compile(r"^#!.*\s-[a-zA-Z]*x")


def rendering_findings(text: str) -> list[tuple[int, str]]:
    """Every (line number, construct) that renders the environment in ``text``.

    Whole-line comments are skipped, except a shebang, which is read for its flags.
    """
    findings: list[tuple[int, str]] = []
    for number, line in enumerate(text.split("\n"), 1):
        if number == 1 and TRACING_SHEBANG.search(line):
            findings.append((number, "tracing shebang"))
        if line.lstrip().startswith("#"):
            continue
        findings.extend(
            (number, label) for label, pattern in RENDERING_CONSTRUCTS if pattern.search(line)
        )
    return findings


def shell_carriers() -> list[Path]:
    """Every file under .githooks, plus the Claude hook wrapper."""
    return [*sorted(p for p in HOOKS_DIR.iterdir() if p.is_file()), WRAPPER]


def test_no_shipped_hook_source_carries_an_environment_rendering_construct() -> None:
    """The four shell hook sources, scanned line by line."""
    sources = shell_carriers()
    names = {p.name for p in sources}
    assert set(SHIPPED_GIT_HOOKS) <= names, "a shipped git hook was not in the scanned population"
    for path in sources:
        text = path.read_text(encoding="ascii")
        lines = text.count("\n")
        assert lines > 0, f"{path.name}: nothing was scanned"
        found = rendering_findings(text)
        assert not found, f"{path.name}: environment-rendering construct(s) at {found}"


#: Each synthetic line, with the construct the scanner must name for it.
MUST_FLAG: Final = (
    ("env >&2", "env with no command"),
    ("env", "env with no command"),
    ("    env | sort", "env with no command"),
    ("x=$(env)", "env with no command"),
    ("env -0 >&2", "env with no command"),
    ("printenv", "printenv"),
    ("printenv GITHUB_TOKEN >&2", "printenv"),
    ("export -p", "export listing"),
    ("export", "export listing"),
    ("declare -p", "declare or typeset -p"),
    ("typeset -p NAME", "declare or typeset -p"),
    ("declare -x", "declare or typeset -x listing"),
    ("set", "bare set"),
    ("set > listing.txt", "bare set"),
    ("if true; then set; fi", "bare set"),
    ("set -x", "set -x"),
    ("set -eux", "set -x"),
    ("set -o xtrace", "set -o xtrace"),
    ("compgen -e", "compgen -e"),
    ("sh -x hook", "shell -x"),
    ("bash -x hook", "shell -x"),
    ("print(os.environ)", "os.environ used whole"),
    ("sys.stderr.write(repr(os.environ))", "os.environ used whole"),
    ("json.dumps(dict(os.environ))", "os.environ used whole"),
    ("'%s' % (os.environb,)", "os.environ used whole"),
    ("f'{os.environ}'", "os.environ used whole"),
    ("from os import environ", "environ imported bare"),
)

#: Ordinary shapes the hooks do use, which the scanner must pass.
MUST_PASS: Final = (
    "set -u",
    "set -f",
    "set -- a b",
    "env FOO=1 cmd",
    "setting = os.environ.get('NAME')",
    "value = os.environ['NAME']",
    "# env >&2 in a comment",
    "printf 'the environment is never echoed'",
    "timeout -k 1 10 sh -c 'exit 42'",
    "CS_PROBE_BOUND=10",
    "cs_msg_leaders=$(timeout -k 1 10 git config --get-regexp x)",
    '    "Unset PYTHONINSPECT, or point it at a plain python." \\',
)


@pytest.mark.parametrize(("line", "label"), MUST_FLAG)
def test_the_scanner_names_each_rendering_construct(line: str, label: str) -> None:
    """The mutation control for the shell arm: every construct is caught by name."""
    labels = [found for _number, found in rendering_findings(line)]
    assert label in labels, f"the scanner missed a {label!r} construct: saw {labels}"


def test_the_scanner_catches_a_tracing_shebang() -> None:
    """The one comment-shaped line the scanner still reads."""
    labels = [label for _number, label in rendering_findings("#!/bin/sh -x\ntrue\n")]
    assert labels == ["tracing shebang"], f"saw {labels}"


def test_the_scanner_passes_the_shapes_the_hooks_use() -> None:
    """The other half of the control: a scanner that flags everything proves nothing."""
    flagged = [line for line in MUST_PASS if rendering_findings(line)]
    assert not flagged, f"the scanner flagged ordinary line(s): {flagged}"


def test_the_scanner_flags_the_control_copies() -> None:
    """The static arm and the driven controls agree about the same inserted line."""
    for raw in (tracked_hook(PRE_COMMIT), WRAPPER.read_bytes()):
        labels = [label for _n, label in rendering_findings(with_dump(raw).decode("ascii"))]
        assert labels == ["env with no command"], f"saw {labels}"


# --- the python static arm: an ALLOWLIST over every program the hooks run ----------
#
# A blocklist of rendering shapes loses by construction - there is always one more
# way to print a value. So the arm grades what the programs are ALLOWED to do with
# the environment, and everything else is a finding. CLAUDE.md non-negotiable 13
# covers ANY environment value, account and machine names included.
#
#   READS    every read by name - ``os.environ[k]``, ``.get(k)``, ``.pop(k)``,
#            ``.setdefault(k)``, ``k in os.environ``, ``os.getenv(k)``,
#            ``os.putenv(k)``, ``os.unsetenv(k)`` - must resolve to string keys,
#            each on ALLOWED_ENV_KEYS or on SITE_SCOPED_KEYS for the function the
#            read sits in. Keys resolve through literals, module constants, loop
#            variables over constant sequences that the loop body never rebinds,
#            and a parameter's call sites in the same module.
#   WHOLE    an expression that is the whole environment - ``os.environ``,
#            ``environ`` imported bare, ``sys.modules[...].environ``,
#            ``vars(os)``, ``os.__dict__``, ``dict(...)``, ``.copy()``,
#            ``.items()``, ``.keys()``, ``.values()``, ``{**...}`` of one - may
#            only be the ``env=`` of a subprocess call, or a COPY assigned to a
#            local whose every later use is such an ``env=`` or an allowlisted
#            read, pop, set or delete. A bare alias is a finding.
#   ALIAS    ``os.getenv`` and its siblings referenced without being called,
#            ``getattr`` reaching ``environ`` or ``getenv`` by a literal, and ANY
#            ``getattr`` on ``os`` with a computed name.
#   DYNAMIC  ``exec``, ``eval``, ``compile``, ``__import__`` and ``importlib``.
#   COMMAND  a subprocess or ``os`` command must resolve to literal words. A word
#            that would dump the environment (the shell constructs above), that
#            expands ``$NAME``, ``${NAME}`` or ``%NAME%`` off the allowlist, or a
#            ``python -c`` program that fails this same allowlist, is a finding.
#
# Every finding the shipped programs need is on REVIEWED, pinned to the file, the
# function, the kind AND the exact detail, with its reason. REVIEWED is graded in
# BOTH directions: an unreviewed finding is red, and an entry that no longer
# matches a finding is red, so an allowance cannot outlive its site or cover a
# different finding at the same site.

#: Operator configuration any hook-run program may read, and why it is not a
#: credential or a personal value.
ALLOWED_ENV_KEYS: Final = {
    "CLOCKSPEED_SAVE_ROOT": "operator override of the save root directory",
    "CLOCKSPEED_ACCOUNT_DIR": "operator override of the save account directory",
    "CLOCKSPEED_LOCAL_CONFIG": "path of the gitignored local configuration file",
    "CLOCKSPEED_WORLD_NAMES": "operator-declared world names the PII scan blocks",
    "CLOCKSPEED_WORLD_TOKENS": "operator-declared world tokens the PII scan blocks",
    "CLOCKSPEED_WORLD_NAME_EXCLUSIONS": "world names the PII scan must not block",
    "CLOCKSPEED_CRASH_TRACEBACK": "the opt-in flag that prints a crash traceback",
    "CLOCKSPEED_COMMIT_MSG_LEADERS": "comment leaders commit-msg hands its checker",
    "CLOCKSPEED_GAME_DIR": "operator override of the game install directory",
}

#: Personal values - account names and profile paths - readable ONLY in the one
#: function that needs them, and why.
SITE_SCOPED_KEYS: Final = {
    ("tools/precommit_gate.py", "save_root"): (
        frozenset({"LOCALAPPDATA", "XDG_DATA_HOME"}),
        "the per-user data roots the save directory sits under; joined into a path",
    ),
    ("tools/precommit_gate.py", "current_account_names"): (
        frozenset({"USERNAME", "USER"}),
        "the account names the PII scan blocks; a skip renders only a name and a length",
    ),
    ("clockspeed/data/locate.py", "_redaction_pairs"): (
        frozenset({"USERPROFILE", "LOCALAPPDATA", "APPDATA", "USERNAME", "COMPUTERNAME"}),
        "the REDACTOR: each value is paired with a placeholder that replaces it wherever "
        "the save reader the gate calls renders a path",
    ),
    ("clockspeed/data/locate.py", "resolve_save_root"): (
        frozenset({"LOCALAPPDATA"}),
        "the per-user data root the save directory sits under; joined into a path",
    ),
}

#: The finding details that recur, spelled once.
UNRESOLVED_KEY: Final = "a key that does not resolve to a literal"
NONLITERAL_COMMAND: Final = "a command that does not resolve to a literal"
DUMPING_COMMAND: Final = "a command that dumps the environment"

#: Every finding the shipped programs need, pinned to (file, function, kind,
#: detail), and why it is safe.
REVIEWED: Final = {
    ("tools/precommit_gate.py", "run_ruff_format", "command", NONLITERAL_COMMAND): (
        "ruff, located by ruff_command() on PATH, run with format arguments only"
    ),
    ("tools/precommit_gate.py", "run_ruff", "command", NONLITERAL_COMMAND): (
        "ruff, located by ruff_command() on PATH, run with check arguments only"
    ),
    ("tools/precommit_gate.py", "check_python_syntax", "dynamic", "compile"): (
        "compiles STAGED source only to find a syntax error; the code is never executed"
    ),
}

ENV_ATTRS: Final = frozenset({"environ", "environb"})
READ_METHODS: Final = frozenset({"get", "pop", "setdefault", "__getitem__", "__contains__"})
WHOLE_METHODS: Final = frozenset({"copy", "items", "keys", "values"})
KEY_FUNCTIONS: Final = frozenset({"getenv", "getenvb", "putenv", "unsetenv"})
DYNAMIC_BUILTINS: Final = frozenset({"exec", "eval", "compile", "__import__"})
SUBPROCESS_FUNCTIONS: Final = frozenset(
    {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
)
OS_COMMAND_PREFIXES: Final = ("system", "popen", "exec", "spawn", "posix_spawn", "startfile")
#: A later argument that is not a literal, as the command words render it.
NONLITERAL_WORD: Final = "<non-literal>"
#: A shell or command-interpreter expansion of an environment variable.
EXPANSION: Final = re.compile(r"\$\{?([A-Za-z_]\w*)|%([A-Za-z_]\w*)%")
#: A program name that is a python interpreter.
PYTHON_PROGRAM: Final = re.compile(r"(?:python(?:\d+(?:\.\d+)?)?w?|py)(?:\.exe)?", re.IGNORECASE)
#: How far key and command resolution follows names before giving up.
MAX_RESOLUTION_DEPTH: Final = 6
#: What a loop variable the loop body rebinds resolves through: nothing.
REBOUND: Final = ast.Constant(value=None)


class Finding(NamedTuple):
    """One refused use: where, what kind, and a NAME - never a value."""

    label: str
    function: str
    kind: str
    detail: str
    line: int


def module_constants(trees: dict[str, ast.Module]) -> dict[str, list[ast.expr]]:
    """Every top-level single-name assignment in the population, by name."""
    constants: dict[str, list[ast.expr]] = {}
    for tree in trees.values():
        for node in tree.body:
            target: ast.expr | None = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                target, value = node.target, node.value
            if isinstance(target, ast.Name):
                constants.setdefault(target.id, []).append(value)
    return constants


def callee(call: ast.Call) -> str:
    """The called name, from a bare name or the last attribute."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def context_of(node: ast.AST | None) -> str:
    """A short name for where a whole-environment expression was used."""
    if isinstance(node, ast.Call):
        return "handed to " + (callee(node) or "a call")
    if isinstance(node, ast.keyword):
        return "handed as " + (node.arg or "**") + "="
    return "used in " + type(node).__name__ if node is not None else "at module level"


class Allowlist:
    """One program's environment uses, graded against the allowlist."""

    def __init__(self, label: str, tree: ast.Module, constants: dict[str, list[ast.expr]]) -> None:
        """Index parents and the names ``os`` and its members are imported as."""
        self.label = label
        self.tree = tree
        self.constants = constants
        self.parent: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parent[child] = node
        self.bare_environ: set[str] = set()
        self.bare_key_functions: set[str] = set()
        self.bare_commands: set[str] = set()
        self.os_names = {"os"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.os_names |= {a.asname or a.name for a in node.names if a.name == "os"}
            if isinstance(node, ast.ImportFrom) and node.module in {"os", "subprocess"}:
                for alias in node.names:
                    self.bind_import(alias.name, alias.asname or alias.name)
        self.findings: list[Finding] = []
        self.read_keys: set[str] = set()
        self.children: list[list[str]] = []

    def bind_import(self, name: str, bound: str) -> None:
        """Remember what a ``from os`` or ``from subprocess`` import binds."""
        if name in ENV_ATTRS:
            self.bare_environ.add(bound)
        elif name in KEY_FUNCTIONS:
            self.bare_key_functions.add(bound)
        elif name in SUBPROCESS_FUNCTIONS or name.startswith(OS_COMMAND_PREFIXES):
            self.bare_commands.add(bound)

    # -- where a node sits -----------------------------------------------------

    def function_of(self, node: ast.AST) -> ast.AST:
        """The nearest enclosing function, or the module."""
        current = node
        while not isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef | ast.Module):
            current = self.parent[current]
        return current

    def name_of(self, node: ast.AST) -> str:
        """The enclosing function's name, or ``<module>``."""
        scope = self.function_of(node)
        return (
            scope.name if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef) else "<module>"
        )

    def find(self, node: ast.AST, kind: str, detail: str) -> None:
        """Record one refused use."""
        line = getattr(node, "lineno", 0)
        self.findings.append(Finding(self.label, self.name_of(node), kind, detail, line))

    def allowed_at(self, node: ast.AST) -> set[str]:
        """The keys a read at ``node`` may name: the global list plus its site's scope."""
        scoped, _reason = SITE_SCOPED_KEYS.get((self.label, self.name_of(node)), (frozenset(), ""))
        return set(ALLOWED_ENV_KEYS) | scoped

    # -- key resolution ----------------------------------------------------------

    def keys(self, expr: ast.AST | None, depth: int = 0) -> set[str] | None:
        """The string keys ``expr`` can evaluate to, or None when it cannot be resolved."""
        if expr is None or depth > MAX_RESOLUTION_DEPTH:
            return None
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return {expr.value}
        if isinstance(expr, ast.Attribute):
            return self.constant_keys(expr.attr, depth)
        if isinstance(expr, ast.Name):
            return self.name_keys(expr, depth)
        return None

    def constant_keys(self, name: str, depth: int) -> set[str] | None:
        """The keys a population constant holds."""
        return self.union(self.constants.get(name) or [], depth)

    def sequence_keys(self, expr: ast.AST, depth: int) -> set[str] | None:
        """The keys a literal or constant sequence holds, every member resolved."""
        if isinstance(expr, ast.Name | ast.Attribute):
            name = expr.id if isinstance(expr, ast.Name) else expr.attr
            values = self.constants.get(name) or []
            if len(values) != 1:
                return None
            return self.sequence_keys(values[0], depth + 1)
        if not isinstance(expr, ast.Tuple | ast.List | ast.Set):
            return None
        return self.union(list(expr.elts), depth)

    def name_keys(self, name: ast.Name, depth: int) -> set[str] | None:
        """A name: a loop variable, a parameter, a local, or a constant."""
        scope = self.function_of(name)
        loop = self.binding_loop(name)
        if loop is not None:
            return self.sequence_keys(loop, depth + 1)
        if isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
            params = [a.arg for a in (*scope.args.posonlyargs, *scope.args.args)]
            if name.id in params:
                return self.parameter_keys(scope, params.index(name.id), name.id, depth)
            local = self.local_values(name)
            if local:
                return self.union(local, depth)
        return self.constant_keys(name.id, depth)

    def binding_loop(self, name: ast.Name) -> ast.expr | None:
        """The iterable of the NEAREST loop binding ``name``; REBOUND if its body rebinds it."""
        current: ast.AST = name
        while not isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef | ast.Module):
            current = self.parent[current]
            generators: list[ast.comprehension | ast.For] = []
            if isinstance(current, ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp):
                generators = list(current.generators)
            elif isinstance(current, ast.For):
                generators = [current]
            for generator in generators:
                target = generator.target
                if isinstance(target, ast.Name) and target.id == name.id:
                    if isinstance(generator, ast.For) and self.rebinds(generator, name.id):
                        return REBOUND
                    return generator.iter
        return None

    @staticmethod
    def rebinds(loop: ast.For, name: str) -> bool:
        """Whether a loop's body assigns the loop variable again."""
        return any(
            isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Store)
            for statement in loop.body
            for node in ast.walk(statement)
        )

    def parameter_keys(
        self, function: ast.FunctionDef | ast.AsyncFunctionDef, index: int, arg: str, depth: int
    ) -> set[str] | None:
        """A parameter resolves through every call site of its function in this module."""
        handed: list[ast.expr] = []
        for call in ast.walk(self.tree):
            if not isinstance(call, ast.Call) or callee(call) != function.name:
                continue
            by_name = [k.value for k in call.keywords if k.arg == arg]
            if by_name:
                handed.append(by_name[0])
            elif index < len(call.args):
                handed.append(call.args[index])
            else:
                return None
        return self.union(handed, depth) if handed else None

    def union(self, exprs: list[ast.expr], depth: int) -> set[str] | None:
        """Every expression resolved, or None if any one is not (or there are none)."""
        if not exprs:
            return None
        found: set[str] = set()
        for expr in exprs:
            got = self.keys(expr, depth + 1)
            if got is None:
                return None
            found |= got
        return found

    def local_values(self, name: ast.Name) -> list[ast.expr]:
        """Every value assigned to ``name`` in the function it is used in."""
        return [
            node.value
            for node in ast.walk(self.function_of(name))
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name.id for t in node.targets)
        ]

    def check_key(self, site: ast.AST, key: ast.AST | None) -> None:
        """A read's key must resolve, and every value it can take must be allowed here."""
        resolved = self.keys(key)
        if resolved is None:
            self.find(site, "read", UNRESOLVED_KEY)
            return
        self.read_keys |= resolved
        for name in sorted(resolved - self.allowed_at(site)):
            self.find(site, "read", name)

    # -- the whole environment ---------------------------------------------------

    def is_whole_root(self, node: ast.AST) -> bool:
        """``os.environ``, ``environ`` bare, ``vars(os)`` or ``os.__dict__``."""
        if isinstance(node, ast.Attribute) and node.attr in ENV_ATTRS:
            return True
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            return node.id in self.bare_environ
        if isinstance(node, ast.Call) and callee(node) == "vars" and node.args:
            return self.is_os(node.args[0])
        return (
            isinstance(node, ast.Attribute) and node.attr == "__dict__" and self.is_os(node.value)
        )

    def is_os(self, node: ast.AST) -> bool:
        """The ``os`` module by name or through ``sys.modules``."""
        if isinstance(node, ast.Name):
            return node.id in self.os_names
        return isinstance(node, ast.Subscript) and self.keys(node.slice) == {"os"}

    def widen(self, node: ast.AST) -> ast.AST:
        """The largest expression around ``node`` that is still the whole environment."""
        while True:
            up = self.parent.get(node)
            if isinstance(up, ast.keyword) and up.arg is None:
                up = self.parent[up]
                if not (isinstance(up, ast.Call) and callee(up) == "dict"):
                    return node
            if isinstance(up, ast.Call) and callee(up) == "dict":
                node = up
                continue
            if isinstance(up, ast.Attribute) and up.attr in WHOLE_METHODS:
                method = self.parent.get(up)
                if isinstance(method, ast.Call) and method.func is up:
                    node = method
                    continue
            if isinstance(up, ast.Dict) and any(
                k is None and v is node for k, v in zip(up.keys, up.values, strict=True)
            ):
                node = up
                continue
            return node

    def is_command_call(self, call: ast.AST) -> bool:
        """A subprocess or ``os`` command call."""
        if not isinstance(call, ast.Call):
            return False
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in self.bare_commands
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "subprocess":
                return func.attr in SUBPROCESS_FUNCTIONS
            if func.value.id in self.os_names:
                return func.attr.startswith(OS_COMMAND_PREFIXES)
        return False

    def whole_use(self, node: ast.AST, *, local: bool = False) -> None:
        """Grade one use of the whole environment by the context it sits in."""
        up = self.parent.get(node)
        if isinstance(up, ast.Attribute) and up.value is node and up.attr in READ_METHODS:
            call = self.parent.get(up)
            if isinstance(call, ast.Call) and call.func is up:
                self.check_key(call, call.args[0] if call.args else None)
                return
        if isinstance(up, ast.Subscript) and up.value is node:
            self.check_key(up, up.slice)
            return
        if (
            isinstance(up, ast.Compare)
            and node in up.comparators
            and all(isinstance(op, ast.In | ast.NotIn) for op in up.ops)
        ):
            self.check_key(up, up.left)
            return
        if (
            isinstance(up, ast.keyword)
            and up.arg == "env"
            and self.is_command_call(self.parent[up])
        ):
            return
        # Narrowed with isinstance, not assert: an assert here makes this a grader
        # in tests/test_liveness.py's census, and every return above an exit.
        if (
            self.is_local_copy(node, up, local=local)
            and isinstance(up, ast.Assign)
            and isinstance(up.targets[0], ast.Name)
        ):
            self.local_uses(up.targets[0])
            return
        self.find(node, "whole", "the whole environment " + context_of(up))

    def is_local_copy(self, node: ast.AST, up: ast.AST | None, *, local: bool) -> bool:
        """A COPY of the environment assigned to one plain local; a bare alias is not one."""
        return (
            not local
            and not self.is_whole_root(node)
            and isinstance(up, ast.Assign)
            and len(up.targets) == 1
            and isinstance(up.targets[0], ast.Name)
        )

    def local_uses(self, target: ast.Name) -> None:
        """Every later use of a local holding the environment, graded as the whole."""
        scope = self.function_of(target)
        for node in ast.walk(scope):
            if (
                isinstance(node, ast.Name)
                and node.id == target.id
                and isinstance(node.ctx, ast.Load)
                and self.function_of(node) is scope
            ):
                self.whole_use(node, local=True)

    # -- aliases and dynamic code ------------------------------------------------------

    def check_alias(self, node: ast.AST) -> None:
        """A key function referenced uncalled, and ``getattr`` reaching the environment."""
        up = self.parent.get(node)
        called = isinstance(up, ast.Call) and up.func is node
        if isinstance(node, ast.Attribute) and node.attr in KEY_FUNCTIONS and not called:
            self.find(node, "alias", node.attr + " referenced without a call")
        if (
            isinstance(node, ast.Name)
            and node.id in self.bare_key_functions
            and isinstance(node.ctx, ast.Load)
            and not called
        ):
            self.find(node, "alias", node.id + " referenced without a call")
        if isinstance(node, ast.Call) and callee(node) == "getattr" and len(node.args) >= 2:  # noqa: PLR2004
            reached = self.keys(node.args[1])
            if reached is not None and reached & (ENV_ATTRS | KEY_FUNCTIONS):
                self.find(node, "alias", "getattr reaching " + ", ".join(sorted(reached)))
            elif reached is None and self.is_os(node.args[0]):
                self.find(node, "alias", "a getattr on os with a computed name")

    def check_dynamic(self, node: ast.AST) -> None:
        """``exec``, ``eval``, ``compile``, ``__import__``, and any use of ``importlib``."""
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else ""
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                name = func.attr if func.value.id == "builtins" else ""
            if name in DYNAMIC_BUILTINS:
                self.find(node, "dynamic", name)
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "importlib" for a in node.names
        ):
            self.find(node, "dynamic", "importlib")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "importlib":
            self.find(node, "dynamic", "importlib")

    # -- commands ------------------------------------------------------------------

    def command_words(self, expr: ast.AST | None, depth: int = 0) -> list[str] | None:
        """A command as its words, with non-literal later arguments as NONLITERAL_WORD."""
        if expr is None or depth > MAX_RESOLUTION_DEPTH:
            return None
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return [expr.value]
        if isinstance(expr, ast.List | ast.Tuple) and expr.elts:
            return self.sequence_words(expr, depth)
        if isinstance(expr, ast.Name):
            local = self.local_values(expr)
            return self.command_words(local[0], depth + 1) if len(local) == 1 else None
        return None

    def sequence_words(self, expr: ast.List | ast.Tuple, depth: int) -> list[str] | None:
        """An argument vector: its program must resolve, later arguments may not."""
        head = expr.elts[0]
        if isinstance(head, ast.Starred):
            values = self.constants.get(getattr(head.value, "id", ""), [])
            first = self.command_words(values[0], depth + 1) if len(values) == 1 else None
        else:
            first = self.command_words(head, depth + 1)
        if first is None:
            return None
        rest = [
            " ".join(self.command_words(e, depth + 1) or [NONLITERAL_WORD]) for e in expr.elts[1:]
        ]
        return [*first, *rest]

    def check_command(self, call: ast.Call) -> None:
        """A command must be literal words that neither dump nor expand the environment."""
        command = call.args[0] if call.args else None
        if command is None:
            command = next((k.value for k in call.keywords if k.arg == "args"), None)
        words = self.command_words(command)
        if words is None:
            self.find(call, "command", NONLITERAL_COMMAND)
            return
        # The whole line, and each later word on its own - a `sh -c` payload.
        if any(rendering_findings(text) for text in (" ".join(words), *words[1:])):
            self.find(call, "command", DUMPING_COMMAND)
        allowed = self.allowed_at(call)
        for word in words:
            for match in EXPANSION.finditer(word):
                name = match.group(1) or match.group(2)
                if name not in allowed:
                    self.find(call, "command", "a child command expanding " + name)
        self.check_child_python(call, words)

    def check_child_python(self, call: ast.Call, words: list[str]) -> None:
        """A python child: its ``-c`` program is graded here, its script is discovered."""
        program = Path(words[0].split()[0]).name if words[0].split() else ""
        if not PYTHON_PROGRAM.fullmatch(program):
            return
        self.children.append(words)
        if "-c" not in words[1:-1]:
            return
        text = words[words.index("-c", 1) + 1]
        if text == NONLITERAL_WORD:
            self.find(call, "command", "a python -c program that is not a literal")
            return
        try:
            tree = ast.parse(text)
        except SyntaxError:
            self.find(call, "command", "a python -c program that does not parse")
            return
        inner = Allowlist(f"{self.label}:{self.name_of(call)}:-c", tree, self.constants)
        self.findings.extend(inner.run())

    # -- the pass ----------------------------------------------------------------------

    def run(self) -> list[Finding]:
        """Grade every read, whole use, alias, dynamic use and command."""
        for node in ast.walk(self.tree):
            if self.is_whole_root(node) and not self.inside_whole(node):
                self.whole_use(self.widen(node))
            elif isinstance(node, ast.Call) and self.is_key_call(node):
                self.check_key(node, node.args[0] if node.args else None)
            self.check_alias(node)
            self.check_dynamic(node)
            if self.is_command_call(node) and isinstance(node, ast.Call):
                self.check_command(node)
        return self.findings

    def inside_whole(self, node: ast.AST) -> bool:
        """``os.environ`` inside ``vars(os).environ`` and similar is graded once."""
        up = self.parent.get(node)
        return isinstance(node, ast.Attribute) and up is not None and self.is_whole_root(up)

    def is_key_call(self, call: ast.Call) -> bool:
        """``os.getenv(k)`` and its siblings, by module attribute or bare import."""
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in self.bare_key_functions
        return isinstance(func, ast.Attribute) and func.attr in KEY_FUNCTIONS


def environment_scan(sources: dict[str, str]) -> list[Allowlist]:
    """One graded pass per source, constants shared between them."""
    trees = {label: ast.parse(text) for label, text in sources.items()}
    constants = module_constants(trees)
    flows = [Allowlist(label, tree, constants) for label, tree in trees.items()]
    for flow in flows:
        flow.run()
    return flows


def environment_findings(sources: dict[str, str]) -> list[Finding]:
    """Every refused environment use across ``sources``."""
    return [finding for flow in environment_scan(sources) for finding in flow.findings]


def unreviewed(findings: list[Finding]) -> list[Finding]:
    """The findings no review entry covers EXACTLY."""
    return [f for f in findings if (f.label, f.function, f.kind, f.detail) not in REVIEWED]


def keys_read(sources: dict[str, str]) -> set[str]:
    """Every key the programs read that resolved, allowed or not."""
    return {key for flow in environment_scan(sources) for key in flow.read_keys}


#: Where a shell carrier or the settings file names a repository tool.
TOOL_REFERENCE: Final = re.compile(r"tools/(\w+)\.py")
#: A heredoc body, and a single-quoted multi-line shell assignment.
HEREDOC: Final = re.compile(r"<<'(\w+)'\n(.*?)\n\1\n", re.DOTALL)
QUOTED_PROGRAM: Final = re.compile(r"^\w+='([^']*\bimport\b[^']*)'$", re.MULTILINE)
#: The tests tree is out of this arm's static scope - see the module docstring.
TESTS_TREE: Final = REPO_ROOT / "tests"


def repo_imports(path: Path) -> list[Path]:
    """The repository modules ``path`` imports, beside it or from the repository root."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[Path] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module] + [node.module + "." + alias.name for alias in node.names]
        for parts in (name.split(".") for name in names):
            candidates = [REPO_ROOT.joinpath(*parts).with_suffix(".py")]
            if len(parts) == 1:
                candidates.append(path.parent / (parts[0] + ".py"))
            found.extend(candidate for candidate in candidates if candidate.is_file())
    return found


def launched_programs(words_seen: list[list[str]]) -> list[Path]:
    """The repository scripts and modules a python child command line names."""
    found: list[Path] = []
    for words in words_seen:
        rest = words[1:]
        if "-m" in rest[:-1]:
            module = rest[rest.index("-m") + 1].split(".")
            candidates = [
                REPO_ROOT.joinpath(*module).with_suffix(".py"),
                REPO_ROOT.joinpath(*module, "__main__.py"),
            ]
        else:
            candidates = [REPO_ROOT / word for word in rest if word.endswith(".py")]
        found.extend(candidate for candidate in candidates if candidate.is_file())
    return found


def child_programs(path: Path) -> list[Path]:
    """The repository python programs ``path`` launches as child processes."""
    flow = Allowlist(path.name, ast.parse(path.read_text(encoding="utf-8")), {})
    flow.run()
    return launched_programs(flow.children)


def hook_programs() -> list[Path]:
    """Every repository program the hooks run, followed through imports and child launches."""
    texts = [p.read_text(encoding="ascii") for p in shell_carriers()]
    texts.append(SETTINGS.read_text(encoding="utf-8"))
    roots = {REPO_ROOT / "tools" / (m + ".py") for t in texts for m in TOOL_REFERENCE.findall(t)}
    population: set[Path] = set()
    pending = [p for p in roots if p.is_file()]
    while pending:
        path = pending.pop()
        if path in population or path.is_relative_to(TESTS_TREE):
            continue
        population.add(path)
        pending.extend([*repo_imports(path), *child_programs(path)])
    return sorted(population)


def inline_programs() -> dict[str, str]:
    """Every python program a shell carrier embeds, as heredoc or quoted assignment."""
    programs: dict[str, str] = {}
    for path in shell_carriers():
        text = path.read_text(encoding="ascii")
        bodies = [body for _tag, body in HEREDOC.findall(text)] + QUOTED_PROGRAM.findall(text)
        for index, body in enumerate(bodies):
            programs[f"{path.name}#{index}"] = body
    return programs


def shipped_sources() -> dict[str, str]:
    """The population and the inline programs, by repository label."""
    sources = {p.relative_to(REPO_ROOT).as_posix(): p.read_text("utf-8") for p in hook_programs()}
    sources.update(inline_programs())
    return sources


def test_the_python_population_holds_every_program_the_hooks_run() -> None:
    """Anti-narrowing: the programs the hooks run are all derived, the tests tree is not."""
    names = {p.relative_to(REPO_ROOT).as_posix() for p in hook_programs()}
    wanted = {"tools/precommit_gate.py", "tools/pretooluse_gate.py", "tools/edit_lint_check.py"}
    missing = sorted(wanted - names)
    assert not missing, f"the derived population lacks {missing}"
    inside = sorted(name for name in names if name.startswith("tests/"))
    assert not inside, f"the tests tree leaked into the static population: {inside}"
    inline = inline_programs()
    carriers = {label.split("#")[0] for label in inline}
    assert carriers == {p.name for p in shell_carriers()}, f"inline programs came from {carriers}"
    heredoc = any("CLOCKSPEED_COMMIT_MSG_LEADERS" in body for body in inline.values())
    assert heredoc, "the commit-msg check program was not extracted"


def test_discovery_follows_a_launched_repository_program() -> None:
    """A literal python child - a script or a ``-m`` module - joins the population."""
    program = (
        "import subprocess\n"
        "subprocess.run(['python', 'scripts/verify_env.py'])\n"
        "subprocess.run(['python', '-m', 'tools.drift_guard'])\n"
    )
    flow = Allowlist("synthetic", ast.parse(program), {})
    flow.run()
    found = {p.relative_to(REPO_ROOT).as_posix() for p in launched_programs(flow.children)}
    assert found == {"scripts/verify_env.py", "tools/drift_guard.py"}, f"discovered {found}"


def test_every_environment_use_in_a_hook_run_program_is_allowed() -> None:
    """THE ALLOWLIST ARM over the derived population and every inline program."""
    left = [
        (f.label, f.line, f.kind, f.detail)
        for f in unreviewed(environment_findings(shipped_sources()))
    ]
    assert not left, f"environment uses off the allowlist: {left}"


def test_every_review_entry_still_matches_a_finding() -> None:
    """The other direction: an allowance whose exact finding is gone is stale, and red."""
    findings = {
        (f.label, f.function, f.kind, f.detail) for f in environment_findings(shipped_sources())
    }
    stale = [entry for entry in REVIEWED if entry not in findings]
    assert not stale, f"review entries that match no finding: {stale}"


def test_every_allowed_key_is_read_by_a_shipped_program() -> None:
    """Both key lists are DERIVED: a name no program reads any more is removed, not kept."""
    listed = set(ALLOWED_ENV_KEYS).union(*(keys for keys, _reason in SITE_SCOPED_KEYS.values()))
    unread = sorted(listed - keys_read(shipped_sources()))
    assert not unread, f"allowed keys no shipped program reads: {unread}"


def test_a_review_entry_covers_only_its_exact_detail() -> None:
    """A second finding at a reviewed site is NOT covered by that site's entry."""
    site = ("tools/precommit_gate.py", "run_ruff", "command")
    covered = Finding(*site, NONLITERAL_COMMAND, 1)
    other = Finding(*site, DUMPING_COMMAND, 1)
    assert unreviewed([covered]) == [], "the reviewed finding itself was not covered"
    assert unreviewed([other]) == [other], "a different finding at a reviewed site was covered"


#: The two lines the check_nul plants go after, and the reviewed call in run_ruff.
NUL_SITE: Final = '    line = data.count(b"\\n", 0, index) + 1\n'
RUFF_SITE: Final = "        run_ruff_format(command, paths, mapping, report, root, cwd)\n"
JSON_SITE: Final = (
    "    except ValueError as exc:\n"
    '        detail = getattr(exc, "msg", None) or type(exc).__name__\n'
)
SCRUBBED_SITE: Final = '    """\n    return scrub(dict(os.environ))\n'

#: The refuted mutants, each planted into a source in memory: (label, the site,
#: its replacement, a helper appended to the module). The last one sits in the
#: tests tree, outside the static scope, and is scanned only to show it is refused.
MUTANTS: Final = {
    "gate-check-nul-prints-a-token-and-runs-env": (
        "tools/precommit_gate.py",
        NUL_SITE,
        NUL_SITE + '    print(os.environ.get("GITHUB_TOKEN"), file=sys.stderr)\n'
        '    subprocess.run(["env"])\n',
        "",
    ),
    "gate-check-nul-prints-the-account-and-profile": (
        "tools/precommit_gate.py",
        NUL_SITE,
        NUL_SITE + '    print("user:", os.environ.get("USERNAME"), os.environ.get("USERPROFILE"),'
        " file=sys.stderr)\n",
        "",
    ),
    "gate-run-ruff-runs-env-at-a-reviewed-site": (
        "tools/precommit_gate.py",
        RUFF_SITE,
        RUFF_SITE + '        subprocess.run(["env"])\n',
        "",
    ),
    "pretooluse-fail-open-hands-environ-to-a-helper": (
        "tools/pretooluse_gate.py",
        '        ALLOW_EXIT_CODE, always.\n    """\n',
        '        ALLOW_EXIT_CODE, always.\n    """\n    import os\n\n    _cs814_dump(os.environ)\n',
        "\n\ndef _cs814_dump(m):\n    sys.stderr.write(repr(m))\n",
    ),
    "lint-check-json-pprints-the-environment": (
        "tools/edit_lint_check.py",
        JSON_SITE,
        JSON_SITE + "        from pprint import pprint\n\n        pprint(dict(os.environ))\n",
        "",
    ),
    "git-env-scrubbed-env-prints-the-environment": (
        "tests/git_env.py",
        SCRUBBED_SITE,
        '    """\n    print(os.environ)\n    return scrub(dict(os.environ))\n',
        "",
    ),
}


def planted(label: str, site: str, replacement: str, helper: str) -> tuple[int, str]:
    """The source with one plant applied: how many sites matched, and the text."""
    pristine = (REPO_ROOT / label).read_text(encoding="utf-8")
    return pristine.count(site), pristine.replace(site, replacement, 1) + helper


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_each_refuted_mutant_is_refused_and_the_pristine_source_is_not(mutant: str) -> None:
    """THE MUTATION PROOF on shipped code: the plant applied, pristine clean, planted red."""
    label, site, lines, helper = MUTANTS[mutant]
    sites, mutated = planted(label, site, lines, helper)
    assert sites == 1, f"{mutant}: the plant site occurs {sites} times"
    sources = shipped_sources()
    if label in sources:
        before = len(unreviewed(environment_findings(sources)))
        assert before == 0, f"{mutant}: the pristine population reads as {before} finding(s)"
    sources[label] = mutated
    after = len(unreviewed(environment_findings(sources)))
    assert after >= 1, f"{mutant}: the plant was not refused"


#: One synthetic program per refused shape.
PY_MUST_FLAG: Final = (
    "import os\nx = os.environ.get('GITHUB_TOKEN')\n",
    "import os\nx = os.environ['GITHUB_TOKEN']\n",
    "import os\nx = 'GITHUB_TOKEN' in os.environ\n",
    "import os\nx = os.environ.pop('SLACK_BOT_TOKEN')\n",
    "import os\nx = os.getenv('ANTHROPIC_API_KEY')\n",
    "from os import getenv\nx = getenv('GH_TOKEN')\n",
    "import os\nx = os.environ.get('USERNAME')\n",
    "import os\nx = os.getenv('USERPROFILE')\n",
    "import os\nx = os.environ.get('LOCALAPPDATA')\n",
    "import os\n\n\ndef f(name):\n    return os.getenv(name)\n",
    "import os\nx = os.environ.get(input())\n",
    "import os\nfor key in ('CLOCKSPEED_SAVE_ROOT',):\n    key = input()\n"
    "    os.environ.get(key)\n",
    "import os\nprint(os.environ)\n",
    "import os\nprint(os.environ.keys())\n",
    "import os\nd = {}\nd.update(os.environ)\n",
    "import os\nx = {**os.environ}\nprint(x)\n",
    "import sys\nprint(sys.modules['os'].environ)\n",
    "import os\nprint(vars(os))\n",
    "import os\nprint(os.__dict__)\n",
    "import os\n\n\ndef f():\n    return os.environ\n",
    "import os\n\n\nclass C:\n    def __init__(self):\n        self.env = dict(os.environ)\n",
    "import os\nenv = os.environ.copy()\nenv.update({'A': 'B'})\n",
    "import os\nenv = dict(os.environ)\nprint(env)\n",
    "import os\ne = os.environ\n",
    "import os\ng = os.getenv\n",
    "from os import getenv\ng = getenv\n",
    "import os\nx = getattr(os, 'environ')\n",
    "import os\nx = getattr(os, 'get' + 'env')\n",
    "import os\nfor k, v in os.environ.items():\n    pass\n",
    "from os import environ\nhelper(environ)\n",
    "import os\nhelper(os.environ)\n",
    "exec('print(1)')\n",
    "x = eval('1')\n",
    "x = __import__('os')\n",
    "import importlib\n",
    "from importlib import import_module\n",
    "import os\nos.system('set')\n",
    "import os\nos.popen('env')\n",
    "import subprocess\nsubprocess.run(['env'])\n",
    "import subprocess\nsubprocess.run('printenv', shell=True)\n",
    "import subprocess\nsubprocess.run(['sh', '-c', 'export -p'])\n",
    "import subprocess\nsubprocess.run('declare -x', shell=True)\n",
    "import subprocess\nsubprocess.run('compgen -e', shell=True)\n",
    "import subprocess\nsubprocess.run(command)\n",
    "import subprocess\nsubprocess.run(['sh', '-c', 'echo $GITHUB_TOKEN >&2'])\n",
    "import subprocess\nsubprocess.run('echo ${GH_TOKEN}', shell=True)\n",
    "import subprocess\nsubprocess.run(['cmd', '/c', 'echo %USERNAME%'])\n",
    "import subprocess\n"
    "subprocess.run(['python', '-c', \"import os; print(os.environ.get('GITHUB_TOKEN'))\"])\n",
    "import os, subprocess\n"
    "subprocess.run(['python', '-c', \"import os;print(getattr(os,'environ'))\"],"
    " env=os.environ)\n",
    "import subprocess\nsubprocess.run(['python', '-c', program])\n",
)

#: Shapes the allowlist permits: configuration reads, resolved keys, child envs.
PY_MUST_PASS: Final = (
    "import os\nx = os.environ.get('CLOCKSPEED_SAVE_ROOT')\n",
    "import os\nx = os.getenv('CLOCKSPEED_LOCAL_CONFIG')\n",
    "import os\nx = 'CLOCKSPEED_CRASH_TRACEBACK' in os.environ\n",
    "import os\nKEY = 'CLOCKSPEED_LOCAL_CONFIG'\nx = os.environ.get(KEY)\n",
    "import os\nfor key in ('CLOCKSPEED_WORLD_NAMES', 'CLOCKSPEED_WORLD_TOKENS'):\n"
    "    x = os.environ.get(key)\n",
    "import os\n\n\ndef f(name):\n    return os.environ.get(name)\n\n\n"
    "f('CLOCKSPEED_ACCOUNT_DIR')\n",
    "import os, subprocess\nsubprocess.run(['git', 'status'], env=dict(os.environ))\n",
    "import os, subprocess\nsubprocess.run(['git', 'status'], env=os.environ)\n",
    "import os, subprocess\nenv = os.environ.copy()\nenv['CLOCKSPEED_SAVE_ROOT'] = 'x'\n"
    "env.pop('CLOCKSPEED_LOCAL_CONFIG', None)\nsubprocess.run(['git'], env=env)\n",
    "import subprocess\nsubprocess.run(['env', 'A=1', 'git', 'status'])\n",
    "import subprocess\nGIT = ('git',)\nsubprocess.run([*GIT, 'status'])\n",
    "import subprocess\nsubprocess.run(['sh', '-c', 'echo $CLOCKSPEED_SAVE_ROOT'])\n",
    "import subprocess\nsubprocess.run(['python', '-c', 'import sys; sys.exit(0)'])\n",
    "import re\nx = re.compile('a')\n",
)


@pytest.mark.parametrize("program", PY_MUST_FLAG)
def test_the_allowlist_refuses_each_shape(program: str) -> None:
    """The synthetic control per refused shape."""
    found = len(environment_findings({"synthetic": program}))
    assert found >= 1, "an environment use off the allowlist was not refused"


@pytest.mark.parametrize("program", PY_MUST_PASS)
def test_the_allowlist_permits_configuration_reads_and_child_envs(program: str) -> None:
    """The other half: an allowlist that refuses everything proves nothing."""
    found = len(environment_findings({"synthetic": program}))
    assert found == 0, f"a permitted environment use read as {found} finding(s)"
