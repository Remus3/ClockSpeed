"""CS-814 - no shipped hook path echoes the environment, proven by driving every one.

THE RULE this module grades is owned by CLAUDE.md non-negotiable 13 and is not
restated here. This module is the PROBE half of CS-814's acceptance.

WHAT THIS MODULE GRADES, in one place. (1) DRIVEN: every refusal class of every
hook program, reached through the real hooks, renders no canary - the gate's
short and generic account-name skips included, which render no name either.
(2) STATIC SHELL: no line of a shell carrier renders the environment. (3) STATIC
PYTHON: in every program the hooks run, the environment AND every value the
operating system derives from the person at the keyboard - account and machine
names, home, profile, temp and interpreter paths - are reached only at a
PERMITTED site: an allowlisted import, an allowlisted member of a surface
module or path method (personal ones in the one function that needs them), a
read whose key resolves to an allowlisted name. The whole environment may only
become a child's ``env=``; aliases, dynamic code and locals-capturing calls are
refused; and a child command is literal words naming git or python that neither
dump nor expand the environment. Everything not permitted is a finding, and
every permission no shipped program uses is red. OUT OF SCOPE, stated rather
than implied: ``__file__`` and ``__spec__.origin`` (a module's own path is a
CS-1208 value-flow source, not an environment read), what an ``os.scandir``
listing names, how many levels a ``relpath`` climbs, ``time.tzname``, and a
``/proc`` path built at run time rather than written as a literal (CS-1208).

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
        CLOCKSPEED_CRASH_TRACEBACK opt-in engaged; the short and the generic
        account-name skips of current_account_names
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
asserts every canary IS found. The account-name skip arm has its own: a
SANDBOX copy of the gate whose skip line renders the value, which the same
oracle must see, lower- and upper-cased.

TWO STATIC ARMS. The shell scan reads the four shell carriers for constructs that
render the environment. The PYTHON arm is an ALLOWLIST, AST-level, over every
repository program the hooks run - discovered from the hooks and
``.claude/settings.json`` and followed through their repository imports - plus
every inline program the shell carriers embed, and every repository python
program they launch as a literal child. A blocklist of rendering shapes was
REFUTED: three mutants leaked a canary through real hooks while it stayed green.
And a list of the READERS it knew was refuted too (CS-1207): an unlisted reader
such as ``os.path.expandvars`` rendered a marker through the real gate. So the
arm lists what is PERMITTED - imports, surface-module members, path methods,
keys and child programs - and refuses the rest unnamed, personal values only
inside the one function that needs them. The rules and the tables sit at the
arm itself. It is proven against each refuted mutant planted into the shipped
source, and by a synthetic control per shape that names the rule refusing it.

THE STATIC BOUNDARY, stated rather than implied. The tests tree is OUT of the
static scope, although pre-push runs it: assertion rendering there is graded by
CS-1199 in ``tests/test_assertion_rendering.py``, and a non-assert echo in a test
is CS-1206. The driven pre-push arms still run the shipped conftest. The key
resolver follows literals, constants, loops, locals, and a parameter's call
sites across every scanned module and through ``map`` and ``partial``. DECLARED
RESIDUALS: deliberate obfuscation - a key or a command assembled at run time
beyond what the resolver follows, or indirection through another process; an
``env=`` handed to a program that is not python or not a literal, whose own
handling of the environment this arm cannot read; an untyped receiver exposing
a personal lookup under a name that is not a public ``pathlib.Path`` name; and
where a permitted value GOES once read, which is CS-1208.

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

from tests.fleet_hook_kit import OPERATOR_IDENT_KEY, install_hook_kit, suite_dir_env
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
    "tests/xdist_quiet.py",
    "clockspeed/__init__.py",
    "clockspeed/data/__init__.py",
    "clockspeed/data/locate.py",
    "clockspeed/save/__init__.py",
    "clockspeed/save/workdir.py",
    # CS-1290: tests/conftest.py installs the kit's test guard from this path.
    "ops/fleet_kit/fleet_test_guard.py",
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
# CS-1290: the kit's identity line (grant C.1) runs BEFORE the ladder, on plain
# `python`, so a stand-in that failed it too would refuse the push there and the
# ladder's own refusal - the path these arms name - would never be reached. The
# stand-in answers that one call as passed and fails every other, ladder probes
# included; the identity refusal itself is graded in test_pre_push_suite_floor.py.
FAILING_RUNG: Final = b'#!/bin/sh\ncase "$1" in *fleet_identity.py) exit 0 ;; esac\nexit 1\n'
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
    env.update(suite_dir_env(root))
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


def make_repo(
    root: Path, hooks: dict[str, bytes], suite: bytes | None = None, gate: bytes | None = None
) -> Path:
    """A throwaway repository wired to hook copies, with the real gate in place.

    With a ``suite`` it also carries the shipped pytest configuration and
    conftest, and a bare remote seeded through ``--no-verify`` so a refused push
    can be told apart from one that never reached the hook. With ``gate`` the
    SANDBOX copy of the gate is those bytes instead - a control's one planted
    edit; the tracked gate is never written.
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
        (OPERATOR_IDENT_KEY, FIXTURE_EMAIL),
    ):
        assert git_ok(work, root, "config", key, value), "a sandbox config key did not write"
    # CS-1290: the kit files the wired identity and suite-gate lines run,
    # UNTRACKED like the gate below - the hooks run them from the working tree.
    install_hook_kit(work)
    # UNTRACKED ON PURPOSE: the hook loads the gate from the working tree.
    (work / "tools").mkdir()
    if gate is None:
        shutil.copy2(GATE, work / "tools" / "precommit_gate.py")
    else:
        (work / "tools" / "precommit_gate.py").write_bytes(gate)
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
    gate: bytes | None = None,
) -> Run:
    """Stage one file and commit it through the hooks."""
    work = make_repo(root, hooks, gate=gate)
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


# --- the account-name skip branches of the gate, driven -----------------------------
#
# precommit_gate.current_account_names reads USERNAME and USER, and a value too
# short or too generic to match safely is dropped with a skip line that the
# pre-commit invocation renders. The canaries above put a long marker in
# USERNAME, so the name is appended and neither skip branch is ever reached;
# these arms set the two names themselves. Short values are two letters outside
# [a-f0-9], so no hex marker or object name in the output can collide with one.

#: Each skip branch: the names it sets, and the text that proves it was reached.
ACCOUNT_SKIP_ARMS: Final = {
    "short-account-names": (
        {"USERNAME": "qz", "USER": "jx"},
        (b"USERNAME=<2 chars> is too short", b"USER=<2 chars> is too short"),
    ),
    "generic-account-names": (
        {"USERNAME": "admin", "USER": "root"},
        (b"USERNAME is a generic account name", b"USER is a generic account name"),
    ),
}

#: The skip line's format in the tracked gate, and each control's one planted edit
#: to the SANDBOX copy - a skip line that renders the value itself.
SHORT_SKIP_SITE: Final = b'"%s=<%d chars> is too short to match safely" % (key, len(value))'
SHORT_SKIP_PLANTS: Final = {
    "renders-the-value": b'"%s=<%s chars> is too short to match safely" % (key, value)',
    "renders-the-value-upper-cased": (
        b'"%s=<%s chars> is too short to match safely" % (key, value.upper())'
    ),
}


#: Per skip branch, a second set of names the gate drops by the SAME branch whose
#: values share no token with the arm's own. A run with these plants nothing the
#: oracle counts, so every occurrence it finds is prose the branch always carries
#: - CS-1221. The short pair is two letters outside [a-f0-9], like the arm's own.
ACCOUNT_SKIP_BASELINES: Final = {
    "short-account-names": {"USERNAME": "wv", "USER": "kp"},
    "generic-account-names": {"USERNAME": "guest", "USER": "owner"},
}

#: The generic-name skip line in the tracked gate, and - one per site measured in
#: it - prose a CORRECT gate prints that carries a generic account name as a
#: BOUNDED token, because a hyphen and a space are both non-alphanumeric. The
#: real sites are the save-root subdirectory skip, the save-root entry cap, and
#: the two absolute-home-path findings; each is reachable only on a machine whose
#: save root or staged file supplies it, so this arm plants the carriage instead.
GENERIC_SKIP_HEAD: Final = b'f"{key} is a generic account name'
GENERIC_SKIP_SITE: Final = GENERIC_SKIP_HEAD + b'; whole-word match would flag ordinary prose"'
CARRIED_PROSE_SITES: Final = {
    "posix-home-path-finding": ("home", b"; absolute POSIX home path, auto-detect it"),
    "save-root-entry-cap": ("root", b"; save root holds more than that many entries"),
    "save-root-subdirectory-skip": ("root", b"; save-root subdirectory is not an account id"),
    "windows-home-path-finding": ("home", b"; absolute Windows home path, auto-detect it"),
}
#: Both account-name keys reach the generic branch, so prose planted in its skip
#: line is printed once per key. The arm asserts the carriage is at least this
#: present in both of its runs, so it cannot pass by observing nothing.
CARRIED_PROSE_PRINTS: Final = 2


class SkipVerdict(NamedTuple):
    """One skip branch reduced to scalars: counts and bools, never a value."""

    reached: bool
    base_reached: bool
    hits: int
    shown: int
    carried: int
    rendered: int


def bounded_hits(output: bytes, value: str) -> int:
    """How often ``value`` occurs as a whole token, case-insensitively."""
    token = re.escape(value.encode("ascii"))
    pattern = re.compile(rb"(?<![A-Za-z0-9])" + token + rb"(?![A-Za-z0-9])", re.IGNORECASE)
    return len(pattern.findall(output))


def account_skip_run(
    root: Path,
    planted: dict[str, str],
    counted: tuple[str, ...],
    said: tuple[bytes, ...],
    gate: bytes | None,
) -> tuple[bool, int, int]:
    """One commit with ``planted`` set: reached, canary hits, counted-token hits.

    ``counted`` is deliberately NOT tied to ``planted``. A baseline run plants
    values that cannot add to the count, so what it finds is the fixed prose
    every run of that branch carries rather than anything the hook rendered.
    """
    root.mkdir(parents=True, exist_ok=True)
    run = commit_through(root, both_commit_hooks(), extra=dict(planted), gate=gate)
    reached = run.code == 0 and run.landed and all(words in run.out for words in said)
    hits, _found = marker_hits(run.out)
    shown = sum(bounded_hits(run.out, value) for value in counted)
    return reached, hits, shown


def account_skip_verdict(
    root: Path,
    planted: dict[str, str],
    baseline: dict[str, str],
    counted: tuple[str, ...],
    said: tuple[bytes, ...],
    gate: bytes | None = None,
) -> SkipVerdict:
    """Grade one skip branch AGAINST a baseline run of that same branch - CS-1221.

    The two runs differ in the planted VALUES alone and reach the same branch,
    so every line of fixed prose is identical between them. What the baseline
    finds is therefore carried by that prose rather than rendered from a value,
    and only the EXCESS is a leak. That is what lets a correct gate print a
    compound such as a save-root path - whose own hyphen leaves the generic word
    `root` bounded - without the oracle reading it as a rendered account name.
    """
    reached, hits, shown = account_skip_run(root / "planted", planted, counted, said, gate)
    base_reached, _base_hits, carried = account_skip_run(
        root / "baseline", baseline, counted, said, gate
    )
    return SkipVerdict(reached, base_reached, hits, shown, carried, shown - carried)


@pytest.mark.parametrize("arm", sorted(ACCOUNT_SKIP_ARMS))
def test_no_account_name_skip_renders_the_name(tmp_path: Path, arm: str) -> None:
    """Each skip branch of current_account_names, reached, renders no name and no canary."""
    names, said = ACCOUNT_SKIP_ARMS[arm]
    verdict = account_skip_verdict(
        tmp_path, names, ACCOUNT_SKIP_BASELINES[arm], tuple(names.values()), said
    )
    assert verdict.reached, f"{arm}: the commit did not reach the skip branch it names"
    assert verdict.base_reached, f"{arm}: the baseline did not reach the same skip branch"
    hits = verdict.hits
    assert hits == 0, f"{arm}: {hits} canary occurrence(s) in the hook output"
    rendered = verdict.rendered
    assert rendered <= 0, (
        f"{arm}: an account name occurred {rendered} time(s) beyond what the hook's "
        "own fixed prose carries"
    )


@pytest.mark.parametrize("site", sorted(CARRIED_PROSE_SITES))
def test_the_skip_arm_separates_a_carried_token_from_a_rendered_one(
    tmp_path: Path, site: str
) -> None:
    """A generic name the gate's own fixed prose CARRIES is not a rendered name.

    The real collisions are machine-dependent - the save-root lines need a save
    root, the home-path lines need a staged home path - so this arm plants the
    carriage into a SANDBOX gate copy and holds on any machine. The planted name
    IS the carried token, so an oracle with no baseline must read the gate's own
    prose as a leak; one with a baseline must not.
    """
    token, prose = CARRIED_PROSE_SITES[site]
    pristine = GATE.read_bytes()
    sites = pristine.count(GENERIC_SKIP_SITE)
    assert sites == 1, f"the generic skip format occurs {sites} time(s) in the tracked gate"
    carrying = pristine.replace(GENERIC_SKIP_SITE, GENERIC_SKIP_HEAD + prose + b'"', 1)
    moved = carrying != pristine
    assert moved, f"{site}: the carried-prose plant was not applied"
    _names, said = ACCOUNT_SKIP_ARMS["generic-account-names"]
    verdict = account_skip_verdict(
        tmp_path,
        {"USERNAME": token, "USER": token},
        ACCOUNT_SKIP_BASELINES["generic-account-names"],
        (token,),
        said,
        carrying,
    )
    assert verdict.reached, f"{site}: the commit did not reach the generic skip branch"
    assert verdict.base_reached, f"{site}: the baseline did not reach the same skip branch"
    hits = verdict.hits
    assert hits == 0, f"{site}: {hits} canary occurrence(s) in the hook output"
    shown = verdict.shown
    assert shown >= CARRIED_PROSE_PRINTS, (
        f"{site}: the token occurs {shown} time(s) in the output, so the carriage "
        "this arm exists to separate is not even present"
    )
    rendered = verdict.rendered
    assert rendered <= 0, f"{site}: carried prose read as {rendered} rendered name(s)"
    carried = verdict.carried
    assert carried >= CARRIED_PROSE_PRINTS, (
        f"{site}: the baseline measured the carriage {carried} time(s)"
    )


@pytest.mark.parametrize("plant", sorted(SHORT_SKIP_PLANTS))
def test_a_gate_copy_whose_skip_renders_the_name_is_caught(tmp_path: Path, plant: str) -> None:
    """THE CONTROL for the skip arm: the same oracle DOES see a rendered short name."""
    pristine = GATE.read_bytes()
    sites = pristine.count(SHORT_SKIP_SITE)
    assert sites == 1, f"the skip format occurs {sites} time(s) in the tracked gate"
    planted_gate = pristine.replace(SHORT_SKIP_SITE, SHORT_SKIP_PLANTS[plant], 1)
    moved = planted_gate != pristine
    assert moved, "the control plant was not applied"
    names, _said = ACCOUNT_SKIP_ARMS["short-account-names"]
    run = commit_through(tmp_path, both_commit_hooks(), extra=dict(names), gate=planted_gate)
    reached = run.landed and b"is too short to match safely" in run.out
    assert reached, f"{plant}: the control commit did not reach the skip branch"
    shown = bounded_hits(run.out, names["USERNAME"])
    assert shown >= 1, f"{plant}: the oracle saw no rendered name - the skip arm proves nothing"


# --- the shell static arm -----------------------------------------------------------

#: Where a shell command word can start: line start, a separator, a substitution,
#: or a keyword that introduces a command.
_CMD: Final = r"(?:^|[;&|({`!=]|\$\(|\bthen\b|\bdo\b|\belse\b|\bexec\b)\s*"
#: What may follow a command that takes no operand: end, a separator or a redirect.
_END: Final = r"\s*(?:$|[;&|)`>'\"]|[0-9]>)"

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
    ("PowerShell Env: drive", re.compile(r"(?<![\w$\{])env:", re.IGNORECASE)),
    ("PowerShell dollar-env read", re.compile(r"\$\{?env:", re.IGNORECASE)),
    (".NET environment API", re.compile(r"\[(?:System\.)?Environment\]::", re.IGNORECASE)),
    ("process.env", re.compile(r"\bprocess\.env\b")),
    ("pytest showlocals", re.compile(r"\bpytest\b.*\s(?:--showlocals|-l)(?=\s|$)")),
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
    ("Get-ChildItem Env:", "PowerShell Env: drive"),
    ("pwsh -c 'gci env:/'", "PowerShell Env: drive"),
    ("Get-Item Env:USERNAME", "PowerShell Env: drive"),
    ("dir env:", "PowerShell Env: drive"),
    ('powershell -Command "Write-Output $Env:GITHUB_TOKEN"', "PowerShell dollar-env read"),
    ("echo ${env:USERNAME}", "PowerShell dollar-env read"),
    ("[Environment]::GetEnvironmentVariables()", ".NET environment API"),
    ("[System.Environment]::UserName", ".NET environment API"),
    ('node -e "console.log(process.env)"', "process.env"),
    ("node -p process.env.X", "process.env"),
    ("python -m pytest -q -l", "pytest showlocals"),
    ("python -m pytest --showlocals tests", "pytest showlocals"),
    ("git -c 'alias.x=!env' x", "env with no command"),
    ('git -c "core.pager=env" -p log', "env with no command"),
    ("alias.x=!env", "env with no command"),
    ("core.pager=env", "env with no command"),
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
    "the environment and its envelope",
    "# Get-ChildItem Env: in a comment",
    "python -m pytest -q -p no:cacheprovider",
    "ls -l hooks",
    "node --version",
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
# way to print a value. So the arm grades what the programs are ALLOWED to reach -
# the environment, and the values the operating system derives from the person at
# the keyboard: the account and machine names, and the home, profile, temp and
# interpreter paths that carry them - and everything else is a finding. CLAUDE.md
# non-negotiable 13 covers ANY environment value, account and machine names
# included. Every rule below REFUSES BY DEFAULT: an unlisted import, member, path
# method, key or program is a finding without anyone having had to name it.
#
#   IMPORT   every imported module is on PURE_MODULES or SURFACE_MODULES, or a
#            repository module of the scanned population. Members of BOTH kinds
#            are graded by MEMBER - a pure module re-exports os, sys and inspect.
#            getpass, socket, platform, pwd, cgitb and every other module are refused
#            without being listed.
#   MEMBER   every member reached on an imported module - ``ns.member``, ``from m
#            import member``, ``getattr(ns, literal)`` - must be on GLOBAL_MEMBERS,
#            or on SITE_SCOPED_MEMBERS for the one function it sits in. A method
#            or attribute whose name is a public ``pathlib.Path`` name
#            (PATH_METHODS), on a receiver the scanner cannot type, is graded the
#            same way as ``Path.NAME`` against PATH_METHODS_GLOBAL. ``os.environ``
#            and the key functions are ROUTED to READS and WHOLE instead. A surface
#            module handed anywhere whole is a finding.
#   READS    every read by name - ``os.environ[k]``, ``.get(k)``, ``.pop(k)``,
#            ``.setdefault(k)``, ``k in os.environ``, ``os.getenv(k)``,
#            ``os.putenv(k)``, ``os.unsetenv(k)``, and each of those readers handed
#            to ``map`` or ``partial`` - must resolve to string keys, each on
#            ALLOWED_ENV_KEYS or on SITE_SCOPED_KEYS for the function the read sits
#            in. Keys resolve through literals, module constants, loop variables
#            over constant sequences that the loop body never rebinds, locals bound
#            by a plain, annotated or walrus assignment, and a parameter's call
#            sites in EVERY scanned module - by name, import alias or attribute,
#            and through ``map`` and ``partial``. Any other binding of the name, or
#            the function handed anywhere else as a value, leaves it unresolved.
#   WHOLE    an expression that is the whole environment - ``os.environ``,
#            ``environ`` imported bare, ``sys.modules[...].environ``,
#            ``vars(os)``, ``os.__dict__``, ``dict(...)``, ``.copy()``,
#            ``.items()``, ``.keys()``, ``.values()``, ``{**...}`` of one - may
#            only be the ``env=`` of a subprocess call, or a COPY assigned to a
#            local whose every later use is such an ``env=`` or an allowlisted
#            read, pop, set or delete. A bare alias is a finding.
#            A private or dunder member is never globally permitted, and a dunder
#            or frame attribute on any object must be on DUNDER_ATTRIBUTES.
#   ALIAS    ``os.getenv`` and its siblings referenced without being called, other
#            than as the reader ``map`` or ``partial`` is handed; ``getattr``
#            reaching ``environ`` or ``getenv`` by a literal; and ANY ``getattr`` on
#            a surface module with a computed name.
#   DYNAMIC  ``exec``, ``eval``, ``compile``, ``__import__``, ``importlib``,
#            ``globals()``, ``locals()``, ``vars()`` with no argument,
#            ``breakpoint()``, any ``__builtins__`` or ``__globals__`` reach, a
#            call whose ``capture_locals``, ``show_locals`` or ``showlocals``
#            keyword is anything but the constant False, a literal path under
#            ``/proc``, and ``getattr``, ``setattr``, ``hasattr`` or ``delattr``
#            by a computed name, or any of them or ``vars`` used as a value.
#   COMMAND  a subprocess or ``os`` command must resolve to literal words whose
#            PROGRAM is git or a python interpreter - whose ``-c`` program is
#            graded by this same allowlist, whose flags are on
#            PYTHON_CHILD_FLAGS and whose ``-m`` module is on PYTHON_CHILD_MODULES.
#            A git child's ``-c`` keys are on GIT_CONFIG_KEYS, and ``--config-env``,
#            ``--exec-path``, ``ext::`` remotes and program-naming options are
#            refused. A child's ``env=`` must be an ENV_SCRUB_HELPERS result. A
#            word that would dump the environment
#            (the shell constructs above), or that expands ``$NAME``, ``${NAME}``
#            or ``%NAME%`` off the allowlist, is a finding as well.
#
# Every finding the shipped programs need is on REVIEWED, pinned to the file, the
# function, the kind AND the exact detail, with its reason. REVIEWED is graded in
# BOTH directions: an unreviewed finding is red, and an entry that no longer
# matches a finding is red, so an allowance cannot outlive its site or cover a
# different finding at the same site. Every permission table is graded the same
# two ways: an unlisted use is a finding, and a listed permission no shipped
# program uses is red.

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

#: Modules whose members are NOT graded: none reads the environment or an
#: OS-derived personal value, so importing one grants nothing.
PURE_MODULES: Final = {
    "__future__": "compiler directives",
    "argparse": "argument parsing over the argv it is handed",
    "contextlib": "context-manager helpers",
    "dataclasses": "class decoration",
    "functools": "higher-order helpers; partial is resolved by READS",
    "hashlib": "digests of the bytes it is handed",
    "heapq": "heap algorithms",
    "json": "serialization of the values it is handed",
    "re": "regular expressions",
    "struct": "binary packing",
    "time": "clocks and sleep",
    "types": "type objects",
    "unicodedata": "the Unicode database",
    "xml.etree.ElementTree": "parsing of the text it is handed",
}

#: Modules whose members ARE graded: some member reads the environment or an
#: OS-derived personal value, so every member reached is on a permission table.
SURFACE_MODULES: Final = {
    "os": "the environment, the account and the working directory",
    "os.path": "home expansion, environment expansion and absolute paths",
    "sys": "the interpreter path and the import path",
    "pathlib": "home, working-directory and owner lookups",
    "tempfile": "the temp directory, which carries the account name",
    "shutil": "PATH lookup",
    "subprocess": "child processes, graded by COMMAND",
    "site": "the per-user site directory",
    "sysconfig": "installation paths",
    "ctypes": "any native call, the account-bearing short-path API among them",
    "ctypes.wintypes": "native types for the calls above",
    "winreg": "the registry, per-user hive included",
    "traceback": "frame and locals capture",
    "ruff": "the location of the ruff binary",
    "pytest": "the location of the installed package",
    "typing": "a string annotation evaluates through ForwardRef and get_type_hints",
    "yaml": "an unsafe loader constructs any python object, a call among them",
}

#: Members the rules above route elsewhere rather than permit: READS and WHOLE grade
#: every use of them. They are grading routes, not permissions.
ROUTED_MEMBERS: Final = {
    "os": frozenset({"environ", "getenv", "putenv", "unsetenv"}),
    "functools": frozenset({"partial"}),
}

#: Why a pure module's measured members are permitted.
PURE_MEMBER: Final = "a pure module's member; it computes over what it is handed"

#: Members of an imported module any program may reach, and why none of them is an
#: environment value or an OS-derived personal value. Never a private name.
GLOBAL_MEMBERS: Final = {
    "__future__": (frozenset({"annotations"}), PURE_MEMBER),
    "argparse": (frozenset({"ArgumentParser"}), PURE_MEMBER),
    "contextlib": (frozenset({"suppress"}), PURE_MEMBER),
    "dataclasses": (frozenset({"dataclass", "field", "fields"}), PURE_MEMBER),
    "functools": (frozenset({"lru_cache"}), PURE_MEMBER),
    "hashlib": (frozenset({"sha256"}), PURE_MEMBER),
    "heapq": (frozenset({"heappush", "heapreplace"}), PURE_MEMBER),
    "json": (frozenset({"loads"}), PURE_MEMBER),
    "re": (
        frozenset({"IGNORECASE", "Pattern", "compile", "escape", "finditer", "sub"}),
        PURE_MEMBER,
    ),
    "struct": (frozenset({"pack", "unpack_from"}), PURE_MEMBER),
    "time": (frozenset({"monotonic"}), PURE_MEMBER),
    "types": (frozenset({"ModuleType"}), PURE_MEMBER),
    "unicodedata": (frozenset({"name"}), PURE_MEMBER),
    "xml.etree.ElementTree": (frozenset({"parse"}), PURE_MEMBER),
    "os": (
        frozenset({"name", "scandir", "DirEntry"}),
        "the platform name, and a listing of a directory the caller names",
    ),
    "os.path": (
        frozenset(
            {"commonpath", "dirname", "isabs", "isfile", "join", "normcase", "normpath", "relpath"}
        ),
        "path algebra and a file test over the paths handed in",
    ),
    "sys": (
        frozenset({"argv", "exit", "platform", "stderr", "stdin", "stdout", "flags"}),
        "the hook's own arguments, exit, the platform switch, the standard streams and "
        "the interpreter flags",
    ),
    "pathlib": (
        frozenset({"Path", "PurePosixPath"}),
        "the path classes; their personal lookups are graded as path methods",
    ),
    "subprocess": (
        frozenset(
            {"run", "CalledProcessError", "SubprocessError", "TimeoutExpired", "CREATE_NO_WINDOW"}
        ),
        "the runner COMMAND grades, its exception classes and a creation flag",
    ),
    "typing": (
        frozenset({"Final", "TextIO"}),
        "annotation markers; neither evaluates a string",
    ),
    "yaml": (
        frozenset({"safe_load", "YAMLError"}),
        "the safe loader, which constructs plain data only, and its exception class",
    ),
}

#: The yaml loaders that construct plain data only. ``yaml.load`` and
#: ``yaml.load_all`` are permitted exactly when their Loader is one of these.
YAML_SAFE_LOADERS: Final = frozenset({"SafeLoader", "CSafeLoader"})
YAML_LOADS: Final = frozenset({"load", "load_all"})

#: EVERY public name of ``pathlib.Path``, pinned as a literal so the graded set is
#: the same on every platform and interpreter; a guard arm reddens when the running
#: interpreter grows a name this list lacks.
PATH_METHODS: Final = frozenset(
    {
        "absolute", "anchor", "as_posix", "as_uri", "chmod", "copy", "copy_into", "cwd",
        "drive", "exists", "expanduser", "from_uri", "full_match", "glob", "group",
        "hardlink_to", "home", "info", "is_absolute", "is_block_device", "is_char_device",
        "is_dir", "is_fifo", "is_file", "is_junction", "is_mount", "is_relative_to",
        "is_reserved", "is_socket", "is_symlink", "iterdir", "joinpath", "lchmod", "lstat",
        "match", "mkdir", "move", "move_into", "name", "open", "owner", "parent", "parents",
        "parser", "parts", "read_bytes", "read_text", "readlink", "relative_to", "rename",
        "replace", "resolve", "rglob", "rmdir", "root", "samefile", "stat", "stem",
        "suffix", "suffixes", "symlink_to", "touch", "unlink", "walk", "with_name",
        "with_segments", "with_stem", "with_suffix", "write_bytes", "write_text",
    }
)  # fmt: skip

#: Path names any program may use on an untyped receiver, and why.
PATH_METHODS_GLOBAL: Final = (
    frozenset(
        {
            "exists", "is_absolute", "is_dir", "is_file", "iterdir", "joinpath", "match",
            "mkdir", "name", "open", "parent", "parents", "parts", "read_bytes", "read_text",
            "replace", "stat", "suffix", "write_bytes",
        }
    ),
    "path algebra, file tests and file I/O on a path the program was handed - and the "
    "same names on strings and matches; none reads the home, the working directory "
    "or an owner",
)  # fmt: skip

#: Members that yield an OS-derived personal value - a value that can carry the
#: account name, the profile path or the machine name - reachable ONLY in the one
#: function that needs them, and why. ``Path.NAME`` is a path method.
SITE_SCOPED_MEMBERS: Final = {
    ("clockspeed/data/locate.py", "_redaction_pairs"): (
        frozenset({"Path.home"}),
        "the REDACTOR: the home directory is paired with the placeholder that replaces it",
    ),
    ("clockspeed/data/locate.py", "resolve_save_root"): (
        frozenset({"Path.home"}),
        "the per-user root the save directory sits under; joined into a path",
    ),
    ("clockspeed/data/locate.py", "_win_path_form"): (
        frozenset(
            {
                "ctypes.windll",
                "ctypes.create_unicode_buffer",
                "ctypes.wintypes.DWORD",
                "ctypes.wintypes.LPCWSTR",
                "ctypes.wintypes.LPWSTR",
            }
        ),
        "GetShortPathNameW, so the REDACTOR also strips the 8.3 form of the account name",
    ),
    ("clockspeed/data/locate.py", "_registry_steam_roots"): (
        frozenset(
            {
                "winreg.OpenKey",
                "winreg.QueryValueEx",
                "winreg.HKEY_CURRENT_USER",
                "winreg.HKEY_LOCAL_MACHINE",
            }
        ),
        "the Steam install root, read from the registry to locate the game install",
    ),
    ("clockspeed/data/locate.py", "_repo_root"): (
        frozenset({"Path.resolve"}),
        "the repository root, from this module's own absolute path",
    ),
    ("clockspeed/data/locate.py", "_steam_library_paths"): (
        frozenset({"Path.group"}),
        "re.Match.group: the scanner cannot tell it from PosixPath.group, which returns "
        "the owning group name - so it is permitted only where a match is grouped",
    ),
    ("tools/precommit_gate.py", "_world_names_from_saves"): (
        frozenset({"Path.group"}),
        "re.Match.group: the scanner cannot tell it from PosixPath.group, which returns "
        "the owning group name - so it is permitted only where a match is grouped",
    ),
    ("tools/precommit_gate.py", "check_secrets"): (
        frozenset({"Path.group"}),
        "re.Match.group: the scanner cannot tell it from PosixPath.group, which returns "
        "the owning group name - so it is permitted only where a match is grouped",
    ),
    ("tools/precommit_gate.py", "_repo_root"): (
        frozenset({"Path.resolve"}),
        "the repository root, from this module's own absolute path",
    ),
    ("tools/precommit_gate.py", "normalized_key"): (
        frozenset({"Path.resolve"}),
        "a comparison key for a path; compared, never rendered",
    ),
    ("tools/precommit_gate.py", "label_for"): (
        frozenset({"Path.absolute"}),
        "the absolute form of a path, only to relativise it to a repository label",
    ),
    ("tools/precommit_gate.py", "stage_for_lint"): (
        frozenset({"Path.absolute", "Path.resolve"}),
        "maps each staged copy to the temp directory and back to its repository label",
    ),
    ("tools/precommit_gate.py", "run_ruff"): (
        frozenset({"tempfile.TemporaryDirectory"}),
        "the staging directory ruff lints; findings are mapped back to repository labels",
    ),
    ("tools/precommit_gate.py", "ruff_command"): (
        frozenset({"sys.executable"}),
        "the interpreter ruff runs under when no ruff is on PATH",
    ),
    ("tools/precommit_gate.py", "<module>"): (
        frozenset({"shutil.which", "traceback.print_exc"}),
        "which is imported for ruff_command to locate ruff on PATH; print_exc renders "
        "absolute frame paths, reached only under the CLOCKSPEED_CRASH_TRACEBACK opt-in",
    ),
    ("tools/precommit_gate.py", "_load_header_reader"): (
        frozenset({"sys.path"}),
        "puts the repository root on the import path for the save reader, then removes it",
    ),
    ("tools/precommit_gate.py", "_load_token_scanner"): (
        frozenset({"sys.path"}),
        "puts the repository root on the import path for the scanner, then removes it",
    ),
    ("tools/edit_lint_check.py", "<module>"): (
        frozenset({"Path.resolve", "sys.path", "traceback.print_exc"}),
        "puts this directory on the import path so the gate imports; print_exc renders "
        "absolute frame paths, reached only under the CLOCKSPEED_CRASH_TRACEBACK opt-in",
    ),
    ("tools/pretooluse_gate.py", "load_gate"): (
        frozenset({"Path.resolve", "sys.path"}),
        "puts this directory on the import path so the gate imports",
    ),
    ("claude_hook.sh#1", "<module>"): (
        frozenset({"sys.executable"}),
        "names the pythonw beside the winning interpreter; the shell captures it to "
        "exec it, and it is never shown",
    ),
    ("pre-push#1", "<module>"): (
        frozenset(
            {
                "site.getsitepackages",
                "site.getusersitepackages",
                "sysconfig.get_path",
                "os.path.realpath",
                "pytest.__file__",
            }
        ),
        "the shadow check: pytest must resolve inside the interpreter's own site "
        "directories; paths are compared, never printed",
    ),
}

#: The finding details that recur, spelled once.
UNRESOLVED_KEY: Final = "a key that does not resolve to a literal"
NONLITERAL_COMMAND: Final = "a command that does not resolve to a literal"
DUMPING_COMMAND: Final = "a command that dumps the environment"
CAPTURED_LOCALS: Final = "a call that captures locals"

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

ENV_ATTRS: Final = frozenset({"environ"})
READ_METHODS: Final = frozenset({"get", "pop", "setdefault", "__getitem__", "__contains__"})
WHOLE_METHODS: Final = frozenset({"copy", "items", "keys", "values"})
KEY_FUNCTIONS: Final = frozenset({"getenv", "putenv", "unsetenv"})
#: What a ``getattr`` by a literal must never reach, whatever its receiver.
ALIAS_REACH: Final = frozenset({"environ", "environb", "getenv", "getenvb", "putenv", "unsetenv"})
DYNAMIC_BUILTINS: Final = frozenset(
    {"exec", "eval", "compile", "__import__", "globals", "locals", "breakpoint"}
)
#: Names that hand out a whole namespace, the builtins or a function's module globals.
NAMESPACE_DUNDERS: Final = frozenset({"__builtins__", "__globals__"})
#: A literal path into the process filesystem, which serves the environment itself.
PROC_PATH: Final = re.compile(r"/proc(?:/|$)")
#: git ``-c`` keys a hook-run program may set. Measured: no shipped program sets
#: one as a literal, so the list is empty and every ``-c`` key is a finding.
GIT_CONFIG_KEYS: Final[frozenset[str]] = frozenset()
#: git options whose value is a program git runs, refused wherever they sit.
GIT_PROGRAM_OPTIONS: Final = ("--upload-pack", "--receive-pack", "--exec=")
#: git top-level options that consume the next word.
GIT_OPTIONS_WITH_A_VALUE: Final = frozenset({"-c", "-C"})
#: Helpers whose result a child may be handed as its ``env=``. Measured: no
#: shipped program hands a child an ``env=``, so the list is empty.
ENV_SCRUB_HELPERS: Final[frozenset[str]] = frozenset()
SCRUBBED_ENV_ONLY: Final = "a child env= that is not a scrub helper's"
#: Builtins that reach an attribute by a name: the name must be a literal, and
#: none of them may be handed on as a value.
ATTRIBUTE_BUILTINS: Final = frozenset({"getattr", "setattr", "hasattr", "delattr"})
VALUE_REFUSED_BUILTINS: Final = ATTRIBUTE_BUILTINS | {"vars"}
#: Frame, code and generator attributes, which reach a frame's globals or builtins.
FRAME_ATTRIBUTES: Final = frozenset(
    {
        "gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame", "ag_code", "f_back",
        "f_builtins", "f_globals", "f_locals", "f_code", "tb_frame", "tb_next",
        "co_code", "co_consts", "co_names",
    }
)  # fmt: skip
#: Dunder attributes a program may read on an object, and why each reaches no
#: namespace, frame or code object.
DUNDER_ATTRIBUTES: Final = {
    "__name__": "the name of a class or function, rendered in place of its value",
    "__init__": "a base-class constructor reached through super()",
}
DUNDER_OR_FRAME: Final = "a dunder or frame attribute "
#: Modules a python child may be launched on with ``-m``. Measured: no shipped
#: program launches a literal ``python -m`` child, so the list is empty.
PYTHON_CHILD_MODULES: Final[frozenset[str]] = frozenset()
#: Interpreter flags a python child may carry; each changes no output.
PYTHON_CHILD_FLAGS: Final = frozenset({"-B", "-E", "-I", "-s", "-S", "-u", "-q", "-P"})
#: The keywords that make a traceback or a logger render the locals of each frame.
CAPTURE_KEYWORDS: Final = frozenset({"capture_locals", "show_locals", "showlocals"})
#: The calls that hand a function on to be called later, with its arguments.
HANDING_FUNCTIONS: Final = frozenset({"map", "partial"})
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
#: The one other program a hook-run program may launch by literal name.
GIT_PROGRAM: Final = re.compile(r"git(?:\.exe)?", re.IGNORECASE)
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


def handing_call(node: ast.AST, up: ast.AST | None) -> ast.Call | None:
    """The ``map`` or ``partial`` call ``node`` is the handed function of, if any."""
    if isinstance(up, ast.Call) and callee(up) in HANDING_FUNCTIONS and up.args:
        return up if up.args[0] is node else None
    return None


class Population(NamedTuple):
    """Every scanned tree, indexed once: parents, constants, calls and value uses.

    ``calls`` and ``handed`` are keyed by every name a callee can mean - its own
    and what an ``import ... as`` alias binds - so a parameter is resolved from
    its call sites in every module, not only its own. ``valued`` holds every name
    loaded as a value anywhere else, which leaves a function's keys unresolved.
    """

    labels: frozenset[str]
    constants: dict[str, list[ast.expr]]
    parent: dict[ast.AST, ast.AST]
    calls: dict[str, list[ast.Call]]
    handed: dict[str, list[ast.Call]]
    valued: frozenset[str]


def reference_names(node: ast.AST, aliases: dict[str, set[str]]) -> set[str]:
    """The function names a reference can mean: its own, and what an alias binds."""
    name = ""
    if isinstance(node, ast.Name):
        name = node.id
    elif isinstance(node, ast.Attribute):
        name = node.attr
    return {name, *aliases.get(name, set())} if name else set()


def index_population(
    trees: dict[str, ast.Module],
    constants: dict[str, list[ast.expr]],
    labels: frozenset[str] | None = None,
) -> Population:
    """Index every tree once, for key resolution across modules."""
    parent: dict[ast.AST, ast.AST] = {}
    aliases: dict[str, set[str]] = {}
    for tree in trees.values():
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent[child] = node
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.asname:
                        aliases.setdefault(alias.asname, set()).add(alias.name)
    calls: dict[str, list[ast.Call]] = {}
    handed: dict[str, list[ast.Call]] = {}
    valued: set[str] = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            index_reference(node, parent, aliases, (calls, handed, valued))
    return Population(
        frozenset(trees) if labels is None else labels,
        constants,
        parent,
        calls,
        handed,
        frozenset(valued),
    )


def index_reference(
    node: ast.AST,
    parent: dict[ast.AST, ast.AST],
    aliases: dict[str, set[str]],
    into: tuple[dict[str, list[ast.Call]], dict[str, list[ast.Call]], set[str]],
) -> None:
    """File one node: a call under its callee's names, a handed or valued reference."""
    calls, handed, valued = into
    if isinstance(node, ast.Call):
        for name in reference_names(node.func, aliases):
            calls.setdefault(name, []).append(node)
    if not (isinstance(node, ast.Name | ast.Attribute) and isinstance(node.ctx, ast.Load)):
        return
    up = parent.get(node)
    if isinstance(up, ast.Call) and up.func is node:
        return
    handing = handing_call(node, up)
    for name in reference_names(node, aliases):
        if handing is not None:
            handed.setdefault(name, []).append(handing)
        else:
            valued.add(name)


def listed_module(module: str) -> bool:
    """Whether a module is on the import allowlist, pure or surface."""
    return module in PURE_MODULES or module in SURFACE_MODULES


def package_of_listed(module: str) -> bool:
    """Whether a module is a listed module or a package a listed module sits in."""
    return listed_module(module) or any(
        m.startswith(module + ".") for m in (*PURE_MODULES, *SURFACE_MODULES)
    )


def repository_module(module: str, labels: frozenset[str]) -> bool:
    """Whether an imported module is one of the scanned population's own sources."""
    path = module.replace(".", "/") + ".py"
    return any(label in {module, path} or label.endswith("/" + path) for label in labels)


class Allowlist:
    """One program's environment and OS-identity uses, graded against the allowlist."""

    def __init__(
        self,
        label: str,
        tree: ast.Module,
        constants: dict[str, list[ast.expr]],
        population: Population | None = None,
    ) -> None:
        """Index what ``os``, its members and every surface module are imported as."""
        self.label = label
        self.tree = tree
        self.population = population or index_population({label: tree}, constants)
        self.constants = self.population.constants
        self.parent = self.population.parent
        self.bare_environ: set[str] = set()
        self.bare_key_functions: set[str] = set()
        self.bare_commands: set[str] = set()
        self.namespaces: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    module = alias.name if alias.asname else bound
                    if not repository_module(alias.name, self.population.labels):
                        self.namespaces[bound] = module
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                for alias in node.names:
                    full = node.module + "." + alias.name
                    if package_of_listed(full):
                        self.namespaces[alias.asname or alias.name] = full
                    if node.module in {"os", "subprocess"}:
                        self.bind_import(alias.name, alias.asname or alias.name)
        self.os_names = {"os"} | {b for b, m in self.namespaces.items() if m == "os"}
        self.subprocess_names = {"subprocess"} | {
            b for b, m in self.namespaces.items() if m == "subprocess"
        }
        self.findings: list[Finding] = []
        self.read_keys: set[str] = set()
        self.children: list[list[str]] = []
        #: Every permission a use matched, so a listed permission nothing uses is red.
        self.used: set[tuple[str, ...]] = set()

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
        """A loop variable, a parameter or local of an enclosing function, or a constant."""
        loop = self.binding_loop(name)
        if loop is not None:
            return self.sequence_keys(loop, depth + 1)
        if self.lambda_bound(name):
            return None
        scope = self.function_of(name)
        while isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
            bound, keys = self.scope_binding(scope, name.id, depth)
            if bound:
                return keys
            scope = self.function_of(self.parent[scope])
        return self.constant_keys(name.id, depth)

    def scope_binding(
        self, scope: ast.FunctionDef | ast.AsyncFunctionDef, name: str, depth: int
    ) -> tuple[bool, set[str] | None]:
        """Whether ``scope`` binds ``name``, and the keys it can hold there."""
        args = scope.args
        positional = [a.arg for a in (*args.posonlyargs, *args.args)]
        if name in positional:
            return True, self.parameter_keys(scope, positional.index(name), name, depth)
        if name in [a.arg for a in args.kwonlyargs]:
            return True, self.parameter_keys(scope, -1, name, depth)
        if any(a is not None and a.arg == name for a in (args.vararg, args.kwarg)):
            return True, None
        local = self.local_values(scope, name)
        if local is None:
            return True, None
        return bool(local), self.union(local, depth)

    def lambda_bound(self, name: ast.Name) -> bool:
        """Whether a lambda between ``name`` and its function binds it as a parameter."""
        current: ast.AST = name
        while not isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef | ast.Module):
            current = self.parent[current]
            if isinstance(current, ast.Lambda) and name.id in {
                a.arg for a in ast.walk(current.args) if isinstance(a, ast.arg)
            }:
                return True
        return False

    def binding_loop(self, name: ast.Name) -> ast.expr | None:
        """The iterable of the NEAREST loop binding ``name``; REBOUND if it cannot resolve.

        REBOUND when the loop body binds the name again, or when the name is one
        part of an unpacked target.
        """
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
                if any(isinstance(n, ast.Name) and n.id == name.id for n in ast.walk(target)):
                    return REBOUND
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
        """A parameter resolves through every call site of its function in the POPULATION.

        ``index`` is -1 for a keyword-only parameter. Call sites are matched by name,
        by import alias and by attribute; ``map`` hands each sequence's members to
        the parameter at its position and ``partial`` hands what it binds. A
        function loaded anywhere else as a value, a site that does not bind the
        parameter, or a starred argument, leaves it unresolved.
        """
        if function.name in self.population.valued:
            return None
        sites = self.parameter_sites(function.name, index, arg, depth)
        if sites is None or not (sites[0] or sites[1]):
            return None
        handed, found = sites
        resolved = self.union(handed, depth) if handed else set()
        return None if resolved is None else resolved | found

    def parameter_sites(
        self, name: str, index: int, arg: str, depth: int
    ) -> tuple[list[ast.expr], set[str]] | None:
        """What every call, ``map`` and ``partial`` site hands the parameter, or None."""
        handed: list[ast.expr] = []
        found: set[str] = set()
        for call in self.population.calls.get(name, []):
            value = self.bound_argument(call, call.args, index, arg)
            if value is None:
                return None
            handed.append(value)
        for call in self.population.handed.get(name, []):
            if callee(call) == "map":
                members = self.map_members(call, index, depth)
                if members is None:
                    return None
                found |= members
                continue
            value = self.bound_argument(call, call.args[1:], index, arg)
            if value is None:
                return None
            handed.append(value)
        return handed, found

    def map_members(self, call: ast.Call, index: int, depth: int) -> set[str] | None:
        """The keys ``map`` hands the parameter at ``index``: its sequence's members."""
        sequences = call.args[1:]
        if index < 0 or index >= len(sequences):
            return None
        return self.sequence_keys(sequences[index], depth + 1)

    @staticmethod
    def bound_argument(
        call: ast.Call, positional: list[ast.expr], index: int, arg: str
    ) -> ast.expr | None:
        """What one call site binds to a parameter, or None when it cannot be told."""
        by_name = [k.value for k in call.keywords if k.arg == arg]
        if by_name:
            return by_name[0]
        if any(k.arg is None for k in call.keywords):
            return None
        if index < 0 or index >= len(positional):
            return None
        if any(isinstance(a, ast.Starred) for a in positional[: index + 1]):
            return None
        return positional[index]

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

    def local_values(self, scope: ast.AST, name: str) -> list[ast.expr] | None:
        """Every value bound to ``name`` in ``scope``; None if any binding has no one value.

        A plain, annotated or walrus assignment contributes its value. Any other
        binding - augmented, unpacked, a ``for`` or ``with`` target, an ``except``
        or ``import`` name - makes the local unresolved rather than letting a
        module constant of the same name stand in for it.
        """
        values: list[ast.expr] = []
        for node in ast.walk(scope):
            if isinstance(node, ast.ExceptHandler) and node.name == name:
                return None
            if isinstance(node, ast.Import | ast.ImportFrom) and any(
                (a.asname or a.name.split(".")[0]) == name for a in node.names
            ):
                return None
            if not (isinstance(node, ast.Name) and node.id == name):
                continue
            if not isinstance(node.ctx, ast.Store):
                continue
            up = self.parent.get(node)
            if isinstance(up, ast.comprehension) and up.target is node:
                continue
            if isinstance(up, ast.Assign) and node in up.targets:
                values.append(up.value)
            elif isinstance(up, ast.AnnAssign | ast.NamedExpr) and up.target is node:
                if up.value is not None:
                    values.append(up.value)
            else:
                return None
        return values

    def check_key(self, site: ast.AST, key: ast.AST | None) -> None:
        """A read's key must resolve, and every value it can take must be allowed here."""
        self.check_resolved(site, self.keys(key))

    def check_resolved(self, site: ast.AST, resolved: set[str] | None) -> None:
        """Every resolved key must be allowed here; an unresolved read is a finding."""
        if resolved is None:
            self.find(site, "read", UNRESOLVED_KEY)
            return
        self.read_keys |= resolved
        for name in sorted(resolved - self.allowed_at(site)):
            self.find(site, "read", name)

    def check_handed(self, call: ast.Call) -> None:
        """A reader handed to ``map`` or ``partial``: the keys it will be called with."""
        if callee(call) == "map":
            keys = self.sequence_keys(call.args[1], 0) if len(call.args) > 1 else None
            self.check_resolved(call, keys)
            return
        key = call.args[1] if len(call.args) > 1 else None
        if key is None:
            key = next((k.value for k in call.keywords if k.arg == "key"), None)
        self.check_key(call, key)

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
            if func.value.id in self.subprocess_names:
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
            handing = handing_call(up, call)
            if handing is not None:
                self.check_handed(handing)
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

    # -- imports, surface members and path methods --------------------------------

    def namespace_of(self, node: ast.AST) -> str | None:
        """The module ``node`` IS - a bound name, a submodule, ``sys.modules[m]``."""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            return self.namespaces.get(node.id)
        if isinstance(node, ast.Attribute):
            base = self.namespace_of(node.value)
            full = f"{base}.{node.attr}"
            return full if base is not None and package_of_listed(full) else None
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "modules"
            and self.namespace_of(node.value.value) == "sys"
        ):
            named = self.keys(node.slice)
            module = next(iter(named)) if named is not None and len(named) == 1 else ""
            return module if package_of_listed(module) else None
        return None

    def grade_member(self, node: ast.AST, module: str, member: str) -> None:
        """One member of an imported module - or one path method - must be permitted here.

        A private or dunder member is never globally permitted: only a site entry
        can grant one.
        """
        if member in ROUTED_MEMBERS.get(module, frozenset()):
            return
        if module == "yaml" and (
            member in YAML_SAFE_LOADERS or (member in YAML_LOADS and self.safe_yaml_load(node))
        ):
            return
        qualified = f"{module}.{member}"
        listed, _reason = (
            PATH_METHODS_GLOBAL
            if module == "Path"
            else GLOBAL_MEMBERS.get(module, (frozenset(), ""))
        )
        if member in listed and not member.startswith("_"):
            self.used.add(("global", module, member))
            return
        site = (self.label, self.name_of(node))
        scoped, _why = SITE_SCOPED_MEMBERS.get(site, (frozenset(), ""))
        if qualified in scoped:
            self.used.add(("site", *site, qualified))
            return
        self.find(node, "member", "an unlisted reader " + qualified)

    def safe_yaml_load(self, node: ast.AST) -> bool:
        """``yaml.load(text, Loader=yaml.SafeLoader)`` and its CSafeLoader sibling."""
        call = self.parent.get(node)
        if not (isinstance(call, ast.Call) and call.func is node):
            return False
        loader = next((k.value for k in call.keywords if k.arg == "Loader"), None)
        if loader is None and len(call.args) > 1:
            loader = call.args[1]
        return (
            isinstance(loader, ast.Attribute)
            and loader.attr in YAML_SAFE_LOADERS
            and self.namespace_of(loader.value) == "yaml"
        )

    def check_import(self, node: ast.AST) -> None:
        """Every imported module is listed or the population's own.

        Every name imported from a listed module is a listed member.
        """
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.grade_module(node, alias.name)
        if isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            self.grade_module(node, module)
            if not listed_module(module):
                return
            for alias in node.names:
                if not package_of_listed(f"{module}.{alias.name}"):
                    self.grade_member(node, module, alias.name)

    def grade_module(self, node: ast.AST, module: str) -> None:
        """One imported module against the import allowlist."""
        if module in PURE_MODULES or module in SURFACE_MODULES:
            self.used.add(("module", module))
        elif not repository_module(module, self.population.labels):
            self.find(node, "import", "an unlisted import " + module)

    def check_member(self, node: ast.AST) -> None:
        """A member reached on a module; a path method or dunder on anything else."""
        if not isinstance(node, ast.Attribute):
            return
        namespace = self.namespace_of(node.value)
        if namespace is not None:
            if listed_module(namespace):
                self.used.add(("module", namespace))
            if self.namespace_of(node) is None:
                self.grade_member(node, namespace, node.attr)
            return
        self.grade_dunder(node, node.attr)
        if node.attr in PATH_METHODS and not self.is_whole_root(node.value):
            self.grade_member(node, "Path", node.attr)

    def grade_dunder(self, node: ast.AST, name: str) -> None:
        """A dunder or frame attribute on an object must be on DUNDER_ATTRIBUTES."""
        dunder = name.startswith("__") and name.endswith("__")
        if not (dunder or name in FRAME_ATTRIBUTES):
            return
        if name in DUNDER_ATTRIBUTES:
            self.used.add(("dunder", name))
            return
        self.find(node, "dynamic", DUNDER_OR_FRAME + name)

    def check_module_whole(self, node: ast.AST) -> None:
        """A module may be reached through, never handed on whole."""
        namespace = self.namespace_of(node)
        if namespace is None:
            return
        up = self.parent.get(node)
        if isinstance(up, ast.Attribute) and up.value is node:
            return
        if isinstance(up, ast.Call) and callee(up) == "getattr" and up.args[:1] == [node]:
            return
        self.find(node, "whole", f"the module {namespace} handed whole")

    # -- aliases and dynamic code ------------------------------------------------------

    def check_alias(self, node: ast.AST) -> None:
        """A key function referenced uncalled, and ``getattr`` reaching the environment."""
        up = self.parent.get(node)
        called = isinstance(up, ast.Call) and up.func is node
        if isinstance(node, ast.Attribute) and node.attr in KEY_FUNCTIONS and not called:
            self.reader_reference(node, node.attr, up)
        if (
            isinstance(node, ast.Name)
            and node.id in self.bare_key_functions
            and isinstance(node.ctx, ast.Load)
            and not called
        ):
            self.reader_reference(node, node.id, up)
        if isinstance(node, ast.Call) and callee(node) == "getattr" and len(node.args) >= 2:  # noqa: PLR2004
            self.check_getattr(node)

    def reader_reference(self, node: ast.AST, name: str, up: ast.AST | None) -> None:
        """A key function referenced uncalled: graded where ``map`` or ``partial`` calls it."""
        handing = handing_call(node, up)
        if handing is not None:
            self.check_handed(handing)
            return
        self.find(node, "alias", name + " referenced without a call")

    def check_getattr(self, node: ast.Call) -> None:
        """``getattr`` by a literal is a member reach; on a surface module, never computed."""
        reached = self.keys(node.args[1])
        if reached is not None and reached & ALIAS_REACH:
            self.find(node, "alias", "getattr reaching " + ", ".join(sorted(reached)))
        namespace = self.namespace_of(node.args[0])
        if namespace is None and self.is_os(node.args[0]):
            namespace = "os"
        if namespace is None:
            return
        if reached is None:
            self.find(node, "alias", f"a getattr on {namespace} with a computed name")
            return
        for member in sorted(reached):
            self.grade_member(node, namespace, member)

    def check_dynamic(self, node: ast.AST) -> None:
        """``exec`` and its kin, ``importlib``, and a call that captures frame locals."""
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else ""
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                name = func.attr if func.value.id == "builtins" else ""
            if name in DYNAMIC_BUILTINS:
                self.find(node, "dynamic", name)
            if name == "vars" and not node.args:
                self.find(node, "dynamic", "vars with no argument")
            if name == "vars" and node.args and not self.is_whole_root(node):
                self.find(node, "dynamic", "vars of an object")
            if name in ATTRIBUTE_BUILTINS:
                self.check_attribute_builtin(node, name)
            if any(self.captures_locals(k) for k in node.keywords):
                self.find(node, "dynamic", CAPTURED_LOCALS)
        if (
            isinstance(node, ast.Name)
            and node.id in VALUE_REFUSED_BUILTINS
            and isinstance(node.ctx, ast.Load)
            and not self.is_called(node)
        ):
            self.find(node, "dynamic", node.id + " used as a value")
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "importlib" for a in node.names
        ):
            self.find(node, "dynamic", "importlib")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "importlib":
            self.find(node, "dynamic", "importlib")
        self.check_namespace_dunder(node)
        if isinstance(node, ast.Constant) and isinstance(node.value, str | bytes):
            text = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
            if PROC_PATH.match(text):
                self.find(node, "path", "a literal /proc path")

    def is_called(self, node: ast.AST) -> bool:
        """Whether ``node`` is the function of the call around it."""
        up = self.parent.get(node)
        return isinstance(up, ast.Call) and up.func is node

    def check_attribute_builtin(self, call: ast.Call, name: str) -> None:
        """``getattr`` and its kin: a literal name only, and never a dunder or frame one."""
        named = self.keys(call.args[1]) if len(call.args) > 1 else None
        if named is None:
            self.find(call, "dynamic", f"a {name} with a computed name")
            return
        if self.namespace_of(call.args[0]) is not None:
            return
        for attribute in sorted(named):
            self.grade_dunder(call, attribute)

    def check_namespace_dunder(self, node: ast.AST) -> None:
        """``__builtins__`` and ``__globals__`` by name, attribute or literal subscript."""
        name = ""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, ast.Subscript):
            keys = self.keys(node.slice)
            name = next(iter(keys)) if keys is not None and len(keys) == 1 else ""
        elif isinstance(node, ast.Call) and callee(node) == "getattr" and len(node.args) > 1:
            keys = self.keys(node.args[1])
            name = next(iter(keys)) if keys is not None and len(keys) == 1 else ""
        if name in NAMESPACE_DUNDERS:
            self.find(node, "dynamic", name)

    @staticmethod
    def captures_locals(keyword: ast.keyword) -> bool:
        """A locals-capturing keyword not set to the constant False, or one in ``**{...}``."""
        if keyword.arg is None:
            return isinstance(keyword.value, ast.Dict) and any(
                isinstance(k, ast.Constant) and k.value in CAPTURE_KEYWORDS
                for k in keyword.value.keys
            )
        if keyword.arg not in CAPTURE_KEYWORDS:
            return False
        return not (isinstance(keyword.value, ast.Constant) and keyword.value.value is False)

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
            local = self.local_values(self.function_of(expr), expr.id)
            return self.command_words(local[0], depth + 1) if local and len(local) == 1 else None
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
        """Literal words naming an allowed program, that neither dump nor expand the env."""
        command = call.args[0] if call.args else None
        if command is None:
            command = next((k.value for k in call.keywords if k.arg == "args"), None)
        words = self.command_words(command)
        if words is None:
            self.find(call, "command", NONLITERAL_COMMAND)
            return
        program = Path(words[0].split()[0]).name if words[0].split() else ""
        if not (GIT_PROGRAM.fullmatch(program) or PYTHON_PROGRAM.fullmatch(program)):
            self.find(call, "command", f"a child program {program or '<empty>'} off the allowlist")
        # The whole line, and each later word on its own - a `sh -c` payload.
        if any(rendering_findings(text) for text in (" ".join(words), *words[1:])):
            self.find(call, "command", DUMPING_COMMAND)
        allowed = self.allowed_at(call)
        for word in words:
            for match in EXPANSION.finditer(word):
                name = match.group(1) or match.group(2)
                if name not in allowed:
                    self.find(call, "command", "a child command expanding " + name)
        env = next((k.value for k in call.keywords if k.arg == "env"), None)
        if env is not None and not self.scrubbed(env):
            self.find(call, "command", SCRUBBED_ENV_ONLY)
        if GIT_PROGRAM.fullmatch(program):
            self.check_git_options(call, words)
        self.check_child_python(call, words, program)

    def scrubbed(self, env: ast.AST) -> bool:
        """An ``env=`` that is a scrub helper's result, or a name bound only to one."""
        if isinstance(env, ast.Call):
            return callee(env) in ENV_SCRUB_HELPERS
        if isinstance(env, ast.Name):
            local = self.local_values(self.function_of(env), env.id)
            return local is not None and bool(local) and all(map(self.scrubbed, local))
        return False

    def check_git_options(self, call: ast.Call, words: list[str]) -> None:
        """A git child's ``-c`` keys are on GIT_CONFIG_KEYS; no option names a program."""
        for word in words[1:]:
            if "ext::" in word:
                self.find(call, "command", "a git ext:: remote")
            if word.startswith(GIT_PROGRAM_OPTIONS):
                option = word.split("=", 1)[0]
                self.find(call, "command", "a git option that names a program: " + option)
        for key, value in self.git_top_level_config(call, words):
            if key not in GIT_CONFIG_KEYS or value.lstrip().startswith("!"):
                self.find(call, "command", "a git -c key off the allowlist: " + key)

    def git_top_level_config(self, call: ast.Call, words: list[str]) -> list[tuple[str, str]]:
        """The ``-c`` pairs among git's top-level options; other options are graded here."""
        pairs: list[tuple[str, str]] = []
        index = 1
        while index < len(words) and words[index].startswith("-"):
            word = words[index]
            if word.startswith("--config-env"):
                self.find(call, "command", "a git --config-env option")
            if word.startswith("--exec-path"):
                self.find(call, "command", "a git --exec-path option")
            setting = words[index + 1] if word == "-c" and index + 1 < len(words) else ""
            if word.startswith("-c") and not word.startswith("--") and word != "-c":
                setting = word[2:]
            if setting:
                key, _eq, value = setting.partition("=")
                pairs.append((key.lower(), value))
            index += 2 if word in GIT_OPTIONS_WITH_A_VALUE else 1
        return pairs

    def check_child_python(self, call: ast.Call, words: list[str], program: str) -> None:
        """A python child: its ``-c`` program is graded here, its script is discovered."""
        if not PYTHON_PROGRAM.fullmatch(program):
            return
        self.children.append(words)
        self.check_python_flags(call, words)
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
        label = f"{self.label}:{self.name_of(call)}:-c"
        labels = self.population.labels | {label}
        population = index_population({label: tree}, self.constants, labels)
        inner = Allowlist(label, tree, self.constants, population)
        self.findings.extend(inner.run())
        self.used |= inner.used
        self.read_keys |= inner.read_keys

    def check_python_flags(self, call: ast.Call, words: list[str]) -> None:
        """A python child's flags are on PYTHON_CHILD_FLAGS and its ``-m`` module on the list."""
        for index, word in enumerate(words[1:], 1):
            if word == "-c":
                return
            if word == "-m":
                module = words[index + 1] if index + 1 < len(words) else NONLITERAL_WORD
                if module not in PYTHON_CHILD_MODULES:
                    self.find(call, "command", f"a python -m {module} off the allowlist")
                return
            if not word.startswith("-"):
                return
            if word not in PYTHON_CHILD_FLAGS:
                self.find(call, "command", f"a python flag {word} off the allowlist")

    # -- the pass ----------------------------------------------------------------------

    def run(self) -> list[Finding]:
        """Grade every import, member, read, whole use, alias, dynamic use and command."""
        for node in ast.walk(self.tree):
            if self.is_whole_root(node) and not self.inside_whole(node):
                self.whole_use(self.widen(node))
            elif isinstance(node, ast.Call) and self.is_key_call(node):
                self.check_key(node, node.args[0] if node.args else None)
            self.check_alias(node)
            self.check_dynamic(node)
            self.check_import(node)
            self.check_member(node)
            self.check_module_whole(node)
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
    """One graded pass per source, over one population index shared between them."""
    trees = {label: ast.parse(text) for label, text in sources.items()}
    population = index_population(trees, module_constants(trees))
    flows = [
        Allowlist(label, tree, population.constants, population) for label, tree in trees.items()
    ]
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


def permissions_used(sources: dict[str, str]) -> set[tuple[str, ...]]:
    """Every module, member and site permission a use in ``sources`` matched."""
    return {entry for flow in environment_scan(sources) for entry in flow.used}


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


def listed_permissions() -> set[tuple[str, ...]]:
    """Every permission the tables grant, in the shape a matched use records."""
    listed: set[tuple[str, ...]] = {
        ("module", module) for module in (*PURE_MODULES, *SURFACE_MODULES)
    }
    for module, (members, _reason) in GLOBAL_MEMBERS.items():
        listed |= {("global", module, member) for member in members}
    listed |= {("global", "Path", member) for member in PATH_METHODS_GLOBAL[0]}
    listed |= {("dunder", name) for name in DUNDER_ATTRIBUTES}
    for (label, function), (members, _why) in SITE_SCOPED_MEMBERS.items():
        listed |= {("site", label, function, member) for member in members}
    return listed


def test_every_listed_permission_is_used_by_a_shipped_program() -> None:
    """The permission tables are DERIVED: a module, member or site nothing uses is red."""
    unused = sorted(listed_permissions() - permissions_used(shipped_sources()))
    assert not unused, f"permissions no shipped program uses: {unused}"


def test_an_unused_permission_is_caught_as_stale() -> None:
    """THE CONTROL for the stale arm: one extra permission IS reported unused."""
    extra = ("global", "os.path", "cs1207_never_used")
    unused = extra in (listed_permissions() | {extra}) - permissions_used(shipped_sources())
    assert unused, "an extra permission was not reported unused"


def test_the_path_method_list_holds_every_public_path_name() -> None:
    """PATH_METHODS is pinned; the running pathlib.Path must not have grown past it."""
    running = {name for name in dir(Path) if not name.startswith("_")}
    missing = sorted(running - PATH_METHODS)
    assert not missing, f"public pathlib.Path names PATH_METHODS lacks: {missing}"
    stray = sorted(PATH_METHODS_GLOBAL[0] - PATH_METHODS)
    assert not stray, f"PATH_METHODS_GLOBAL names that are not path names: {stray}"


def test_every_permission_table_names_a_listed_surface_module() -> None:
    """A member permission for a module the import rule does not list grants nothing."""
    modules = set(GLOBAL_MEMBERS) | {
        member.rsplit(".", 1)[0]
        for members, _why in SITE_SCOPED_MEMBERS.values()
        for member in members
    }
    unknown = sorted(modules - set(SURFACE_MODULES) - set(PURE_MODULES) - {"Path"})
    assert not unknown, f"permissions for modules the import rule does not list: {unknown}"
    private = sorted(
        f"{module}.{member}"
        for module, (members, _reason) in GLOBAL_MEMBERS.items()
        for member in members
        if member.startswith("_")
    )
    assert not private, f"private members granted globally: {private}"
    both = sorted(set(PURE_MODULES) & set(SURFACE_MODULES))
    assert not both, f"modules listed both pure and surface: {both}"
    paths = {
        m.split(".", 1)[1]
        for ms, _why in SITE_SCOPED_MEMBERS.values()
        for m in ms
        if m.startswith("Path.")
    }
    stray = sorted(paths - PATH_METHODS)
    assert not stray, f"site-scoped path names that are not path names: {stray}"


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
#: The short-name skip line in current_account_names, and the first line of redact().
ACCOUNT_SKIP_SITE: Final = (
    '                    "%s=<%d chars> is too short to match safely" % (key, len(value)),\n'
)
REDACT_SITE: Final = '    out = str(text).replace("\\\\", "/")\n'

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
    "gate-account-skip-renders-through-expandvars": (
        "tools/precommit_gate.py",
        ACCOUNT_SKIP_SITE,
        '                    os.path.expandvars("%s=$%s" % (key, key)),\n',
        "",
    ),
    "locate-redact-reads-the-home-directory": (
        "clockspeed/data/locate.py",
        REDACT_SITE,
        REDACT_SITE + "    out = out.replace(str(Path.home()), '~')\n",
        "",
    ),
    "gate-check-nul-prints-the-temp-dir": (
        "tools/precommit_gate.py",
        NUL_SITE,
        NUL_SITE + "    print(tempfile.gettempdir(), file=sys.stderr)\n",
        "",
    ),
    "gate-check-nul-prints-the-account-through-getpass": (
        "tools/precommit_gate.py",
        NUL_SITE,
        NUL_SITE + "    import getpass\n\n    print(getpass.getuser(), file=sys.stderr)\n",
        "",
    ),
    "lint-check-json-captures-locals": (
        "tools/edit_lint_check.py",
        JSON_SITE,
        JSON_SITE
        + "        traceback.TracebackException.from_exception(exc, capture_locals=True)\n",
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


#: A helper that reads the key it is handed, with one allowed call site of its own.
KEY_HELPER: Final = (
    "import functools\nimport os\n\n\ndef read(k):\n    return os.environ.get(k)\n\n\n"
    "read('CLOCKSPEED_SAVE_ROOT')\n"
)

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
    # Retired from PY_MUST_PASS by the CS-1207 ruling: a child program off the
    # program allowlist is a finding whatever it is handed, and the second one
    # echoes a personal value.
    "import subprocess\nsubprocess.run(['env', 'A=1', 'git', 'status'])\n",
    "import subprocess\nsubprocess.run(['sh', '-c', 'echo $CLOCKSPEED_SAVE_ROOT'])\n",
    # Retired from PY_MUST_PASS by the CS-1207 round-2 ruling: a child env= must be a
    # scrub helper's, and a git -c key must be on the measured key allowlist.
    "import os, subprocess\nsubprocess.run(['git', 'status'], env=dict(os.environ))\n",
    "import os, subprocess\nsubprocess.run(['git', 'status'], env=os.environ)\n",
    "import os, subprocess\nenv = os.environ.copy()\nenv['CLOCKSPEED_SAVE_ROOT'] = 'x'\n"
    "env.pop('CLOCKSPEED_LOCAL_CONFIG', None)\nsubprocess.run(['git'], env=env)\n",
    "import subprocess\nsubprocess.run(['git', '-c', 'core.quotepath=off', 'status'])\n",
)

#: Shapes the allowlist permits: configuration reads, resolved keys, literal children.
PY_MUST_PASS: Final = (
    "import os\nx = os.environ.get('CLOCKSPEED_SAVE_ROOT')\n",
    "import os\nx = os.getenv('CLOCKSPEED_LOCAL_CONFIG')\n",
    "import os\nx = 'CLOCKSPEED_CRASH_TRACEBACK' in os.environ\n",
    "import os\nKEY = 'CLOCKSPEED_LOCAL_CONFIG'\nx = os.environ.get(KEY)\n",
    "import os\nfor key in ('CLOCKSPEED_WORLD_NAMES', 'CLOCKSPEED_WORLD_TOKENS'):\n"
    "    x = os.environ.get(key)\n",
    "import os\n\n\ndef f(name):\n    return os.environ.get(name)\n\n\n"
    "f('CLOCKSPEED_ACCOUNT_DIR')\n",
    "import subprocess\nGIT = ('git',)\nsubprocess.run([*GIT, 'status'])\n",
    "import subprocess\nsubprocess.run(['python', '-c', 'import sys; sys.exit(0)'])\n",
    "import re\nx = re.compile('a')\n",
    "import os\nx = list(map(os.getenv, ('CLOCKSPEED_SAVE_ROOT',)))\n",
    "import os\n"
    "x = list(map(os.environ.get, ('CLOCKSPEED_WORLD_NAMES', 'CLOCKSPEED_WORLD_TOKENS')))\n",
    "import functools\nimport os\nx = functools.partial(os.getenv, 'CLOCKSPEED_LOCAL_CONFIG')\n",
    "from functools import partial\nimport os\n"
    "x = partial(os.environ.get, 'CLOCKSPEED_GAME_DIR')()\n",
    KEY_HELPER + "x = list(map(read, ['CLOCKSPEED_ACCOUNT_DIR']))\n",
    KEY_HELPER + "x = functools.partial(read, 'CLOCKSPEED_ACCOUNT_DIR')()\n",
    KEY_HELPER + "x = functools.partial(read, k='CLOCKSPEED_ACCOUNT_DIR')()\n",
    "def f(e):\n    return helper(e, capture_locals=False)\n",
    "import os\nx = os.path.join('a', 'b')\n",
    "from pathlib import Path\nx = Path('a').parent.name\n",
    "import yaml\nx = yaml.safe_load(s)\n",
    "import yaml\nx = yaml.load(s, Loader=yaml.SafeLoader)\n",
    "from typing import Final\nX: Final = 1\n",
    "x = open('/tmp/proc/a')\n",
    "import json\nx = json.loads('1')\n",
    "def f(e):\n    return type(e).__name__\n",
    "def f(e):\n    return getattr(e, 'msg', None)\n",
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


#: One synthetic program per reader, route or shape the inverted rules must NAME:
#: (program, the finding's kind, its detail) - so each arm proves WHICH rule
#: refused it, not merely that something did.
PY_MUST_NAME: Final = {
    "expandvars-by-attribute": (
        "import os\nx = os.path.expandvars('$GITHUB_TOKEN')\n",
        "member",
        "an unlisted reader os.path.expandvars",
    ),
    "expandvars-imported-bare": (
        "from os.path import expandvars\nx = expandvars('$GITHUB_TOKEN')\n",
        "member",
        "an unlisted reader os.path.expandvars",
    ),
    "expandvars-by-a-literal-getattr": (
        "import os\nx = getattr(os.path, 'expandvars')\n",
        "member",
        "an unlisted reader os.path.expandvars",
    ),
    "getpass": ("import getpass\nx = getpass.getuser()\n", "import", "an unlisted import getpass"),
    "os-getlogin": ("import os\nx = os.getlogin()\n", "member", "an unlisted reader os.getlogin"),
    "os-uname": ("import os\nx = os.uname()\n", "member", "an unlisted reader os.uname"),
    "os-getuid": ("import os\nx = os.getuid()\n", "member", "an unlisted reader os.getuid"),
    "path-home": (
        "from pathlib import Path\nx = Path.home()\n",
        "member",
        "an unlisted reader Path.home",
    ),
    "path-home-through-the-module": (
        "import pathlib\nx = pathlib.Path.home()\n",
        "member",
        "an unlisted reader Path.home",
    ),
    "path-expanduser": (
        "from pathlib import Path\nx = Path('~').expanduser()\n",
        "member",
        "an unlisted reader Path.expanduser",
    ),
    "os-path-expanduser": (
        "import os\nx = os.path.expanduser('~')\n",
        "member",
        "an unlisted reader os.path.expanduser",
    ),
    "platform-node": (
        "import platform\nx = platform.node()\n",
        "import",
        "an unlisted import platform",
    ),
    "platform-uname": (
        "from platform import uname\nx = uname()\n",
        "import",
        "an unlisted import platform",
    ),
    "socket-gethostname": (
        "import socket\nx = socket.gethostname()\n",
        "import",
        "an unlisted import socket",
    ),
    "tempfile-gettempdir": (
        "import tempfile\nx = tempfile.gettempdir()\n",
        "member",
        "an unlisted reader tempfile.gettempdir",
    ),
    "pwd-getpwuid": (
        "import os\nimport pwd\nx = pwd.getpwuid(os.getuid()).pw_name\n",
        "import",
        "an unlisted import pwd",
    ),
    "cgitb": ("import cgitb\ncgitb.enable()\n", "import", "an unlisted import cgitb"),
    "os-environb-read": (
        "import os\nx = os.environb.get(b'CLOCKSPEED_SAVE_ROOT')\n",
        "member",
        "an unlisted reader os.environb",
    ),
    "os-environb-whole": (
        "import os\nprint(os.environb)\n",
        "member",
        "an unlisted reader os.environb",
    ),
    "os-getenvb": (
        "import os\nx = os.getenvb(b'CLOCKSPEED_SAVE_ROOT')\n",
        "member",
        "an unlisted reader os.getenvb",
    ),
    "environb-imported-bare": (
        "from os import environb\nx = environb\n",
        "member",
        "an unlisted reader os.environb",
    ),
    "rich-traceback-show-locals": (
        "from rich.traceback import install\ninstall(show_locals=True)\n",
        "dynamic",
        "a call that captures locals",
    ),
    "traceback-capture-locals": (
        "import traceback\n\n\ndef f(e):\n"
        "    return traceback.TracebackException.from_exception(e, capture_locals=True)\n",
        "dynamic",
        "a call that captures locals",
    ),
    "capture-locals-by-a-flag": (
        "def f(e, flag):\n    return helper(e, capture_locals=flag)\n",
        "dynamic",
        "a call that captures locals",
    ),
    "show-locals-by-a-number": (
        "helper(show_locals=1)\n",
        "dynamic",
        "a call that captures locals",
    ),
    "showlocals": ("helper(showlocals=True)\n", "dynamic", "a call that captures locals"),
    "getattr-on-sys-computed": (
        "import sys\n\n\ndef f(name):\n    return getattr(sys, name)\n",
        "alias",
        "a getattr on sys with a computed name",
    ),
    "os-path-handed-whole": (
        "import os\nm = os.path\n",
        "whole",
        "the module os.path handed whole",
    ),
    "os-handed-whole": ("import os\nhelper(os)\n", "whole", "the module os handed whole"),
    "annotated-local-shadows-an-allowed-constant": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\n\n\ndef f():\n"
        "    k: str = 'GITHUB_TOKEN'\n    return os.environ.get(k)\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "walrus-local-shadows-an-allowed-constant": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\n\n\ndef f():\n"
        "    if k := 'GITHUB_TOKEN':\n        return os.environ.get(k)\n    return None\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "augmented-local-is-unresolved": (
        "import os\n\n\ndef f(suffix):\n    k = 'CLOCKSPEED_SAVE_ROOT'\n    k += suffix\n"
        "    return os.environ.get(k)\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "with-bound-local-is-unresolved": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\n\n\ndef f():\n"
        "    with open('n') as k:\n        return os.environ.get(k)\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "keyword-only-parameter-shadows-an-allowed-constant": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\n\n\ndef f(*, k):\n    return os.environ.get(k)\n"
        "\n\nf(k='GITHUB_TOKEN')\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "map-of-getenv": (
        "import os\nx = list(map(os.getenv, ('GITHUB_TOKEN',)))\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "map-of-environ-get": (
        "import os\nx = list(map(os.environ.get, ['USERNAME']))\n",
        "read",
        "USERNAME",
    ),
    "partial-of-environ-get": (
        "from functools import partial\nimport os\nx = partial(os.environ.get, 'GH_TOKEN')\n",
        "read",
        "GH_TOKEN",
    ),
    "partial-of-getenv-with-no-key": (
        "import functools\nimport os\ng = functools.partial(os.getenv)\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "map-of-a-helper": (
        KEY_HELPER + "x = list(map(read, ['GITHUB_TOKEN']))\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "partial-of-a-helper": (
        KEY_HELPER + "x = functools.partial(read, 'GITHUB_TOKEN')()\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "partial-of-a-helper-by-keyword": (
        KEY_HELPER + "x = functools.partial(read, k='GITHUB_TOKEN')()\n",
        "read",
        "GITHUB_TOKEN",
    ),
    "a-helper-handed-as-a-value": (
        KEY_HELPER + "x = sorted(['GITHUB_TOKEN'], key=read)\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "lambda-parameter-shadows-an-allowed-constant": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\nf = lambda k: os.environ.get(k)\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "unpacked-loop-target-shadows-an-allowed-constant": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\nfor k, v in [('GITHUB_TOKEN', 1)]:\n"
        "    os.environ.get(k)\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "except-name-shadows-an-allowed-constant": (
        "import os\nk = 'CLOCKSPEED_SAVE_ROOT'\n\n\ndef f():\n    try:\n        pass\n"
        "    except OSError as k:\n        return os.environ.get(k)\n    return None\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "a-starred-call-site-is-unresolved": (
        KEY_HELPER + "read(*['GITHUB_TOKEN'])\n",
        "read",
        UNRESOLVED_KEY,
    ),
    "subprocess-imported-under-an-alias": (
        "import subprocess as sp\nsp.run(['env'])\n",
        "command",
        "a child program env off the allowlist",
    ),
    "os-reached-through-sys-modules": (
        "import sys\nx = sys.modules['os'].getlogin()\n",
        "member",
        "an unlisted reader os.getlogin",
    ),
    "globals-builtins-import": (
        "x = globals()['__builtins__'].__import__('os')\nprint(x.path.expandvars('$A'))\n",
        "dynamic",
        "globals",
    ),
    "globals-os-getlogin": (
        "import os\nprint(globals()['os'].getlogin())\n",
        "dynamic",
        "globals",
    ),
    "vars-with-no-argument": (
        "import os\nprint(vars()['os'].path.expandvars('$A'))\n",
        "dynamic",
        "vars with no argument",
    ),
    "locals-call": (
        "def f():\n    return locals()\n",
        "dynamic",
        "locals",
    ),
    "builtins-by-name": (
        "x = __builtins__\n",
        "dynamic",
        "__builtins__",
    ),
    "builtins-by-subscript": (
        "def f():\n    pass\n\n\nx = f.__globals__['__builtins__']\n",
        "dynamic",
        "__builtins__",
    ),
    "function-globals": (
        "def f():\n    pass\n\n\nx = f.__globals__['os'].getlogin()\n",
        "dynamic",
        "__globals__",
    ),
    "breakpoint": (
        "breakpoint()\n",
        "dynamic",
        "breakpoint",
    ),
    "yaml-unsafe-load": (
        "import yaml\nx = yaml.unsafe_load(s)\n",
        "member",
        "an unlisted reader yaml.unsafe_load",
    ),
    "yaml-full-load": (
        "import yaml\nx = yaml.full_load(s)\n",
        "member",
        "an unlisted reader yaml.full_load",
    ),
    "yaml-load-with-no-loader": (
        "import yaml\nx = yaml.load(s)\n",
        "member",
        "an unlisted reader yaml.load",
    ),
    "yaml-load-unsafe-loader": (
        "import yaml\nx = yaml.load(s, Loader=yaml.UnsafeLoader)\n",
        "member",
        "an unlisted reader yaml.load",
    ),
    "yaml-load-imported-bare": (
        "from yaml import load\nx = load(s)\n",
        "member",
        "an unlisted reader yaml.load",
    ),
    "typing-get-type-hints": (
        "import typing\n\n\ndef f(x: 'int'):\n    pass\n\n\nprint(typing.get_type_hints(f))\n",
        "member",
        "an unlisted reader typing.get_type_hints",
    ),
    "typing-forward-ref": (
        "import typing\nr = typing.ForwardRef('int')\n",
        "member",
        "an unlisted reader typing.ForwardRef",
    ),
    "typing-forward-ref-imported-bare": (
        "from typing import ForwardRef\n",
        "member",
        "an unlisted reader typing.ForwardRef",
    ),
    "typing-eval-type": (
        "import typing\nx = typing._eval_type\n",
        "member",
        "an unlisted reader typing._eval_type",
    ),
    "git-alias-runs-a-program": (
        "import subprocess\nsubprocess.run(['git', '-c', 'alias.x=!env', 'x'])\n",
        "command",
        "a git -c key off the allowlist: alias.x",
    ),
    "git-pager-runs-a-program": (
        "import subprocess\nsubprocess.run(['git', '-c', 'core.pager=env', '-p', 'log'])\n",
        "command",
        "a git -c key off the allowlist: core.pager",
    ),
    "git-editor-runs-a-program": (
        "import subprocess\nsubprocess.run(['git', '-c', 'core.editor=true', 'commit'])\n",
        "command",
        "a git -c key off the allowlist: core.editor",
    ),
    "git-ssh-command": (
        "import subprocess\nsubprocess.run(['git', '-c', 'core.sshCommand=ssh', 'fetch'])\n",
        "command",
        "a git -c key off the allowlist: core.sshcommand",
    ),
    "git-credential-helper": (
        "import subprocess\nsubprocess.run(['git', '-c', 'credential.helper=store', 'fetch'])\n",
        "command",
        "a git -c key off the allowlist: credential.helper",
    ),
    "git-bang-value": (
        "import subprocess\nsubprocess.run(['git', '-c', 'x.y=!true', 'status'])\n",
        "command",
        "a git -c key off the allowlist: x.y",
    ),
    "git-config-env": (
        "import subprocess\nsubprocess.run(['git', '--config-env=core.pager=A', 'log'])\n",
        "command",
        "a git --config-env option",
    ),
    "python-m-site": (
        "import subprocess\nsubprocess.run(['python', '-m', 'site'])\n",
        "command",
        "a python -m site off the allowlist",
    ),
    "python-m-sysconfig": (
        "import subprocess\nsubprocess.run(['python', '-m', 'sysconfig'])\n",
        "command",
        "a python -m sysconfig off the allowlist",
    ),
    "python-verbose-flag": (
        "import subprocess\nsubprocess.run(['python', '-v', '-c', 'pass'])\n",
        "command",
        "a python flag -v off the allowlist",
    ),
    "python-x-flag": (
        "import subprocess\nsubprocess.run(['python', '-X', 'importtime', '-c', 'pass'])\n",
        "command",
        "a python flag -X off the allowlist",
    ),
    "open-proc-environ": (
        "print(open('/proc/self/environ').read())\n",
        "path",
        "a literal /proc path",
    ),
    "path-proc-read-text": (
        "from pathlib import Path\nprint(Path('/proc/self/environ').read_text())\n",
        "path",
        "a literal /proc path",
    ),
    "os-open-proc": (
        "import os\nfd = os.open('/proc/self/environ', 0)\n",
        "path",
        "a literal /proc path",
    ),
    "traceback-print-exc-unscoped": (
        "import traceback\ntraceback.print_exc()\n",
        "member",
        "an unlisted reader traceback.print_exc",
    ),
    "traceback-format-exc-unscoped": (
        "import traceback\nx = traceback.format_exc()\n",
        "member",
        "an unlisted reader traceback.format_exc",
    ),
    "traceback-print-exception-unscoped": (
        "import traceback\ntraceback.print_exception(e)\n",
        "member",
        "an unlisted reader traceback.print_exception",
    ),
    "pure-module-reexports-os": (
        "import contextlib\nprint(contextlib.os.path.expandvars('$A'))\n",
        "member",
        "an unlisted reader contextlib.os",
    ),
    "pure-module-reexport-imported-bare": (
        "from contextlib import os as o\nprint(o.getlogin())\n",
        "member",
        "an unlisted reader contextlib.os",
    ),
    "pure-module-private-member": (
        "import argparse\nprint(argparse._os.getcwd())\n",
        "member",
        "an unlisted reader argparse._os",
    ),
    "pure-module-reexports-inspect": (
        "import dataclasses\nx = dataclasses.inspect.stack()\n",
        "member",
        "an unlisted reader dataclasses.inspect",
    ),
    "pure-submodule-reexports-contextlib": (
        "import xml.etree.ElementTree as ET\nprint(ET.contextlib.os.getlogin())\n",
        "member",
        "an unlisted reader xml.etree.ElementTree.contextlib",
    ),
    "pure-module-reader-stored-in-a-dict": (
        "import contextlib\nd = {'f': contextlib.os.path.expandvars}\nprint(d['f']('$A'))\n",
        "member",
        "an unlisted reader contextlib.os",
    ),
    "dotted-import-reaches-a-reexport": (
        "import xml.etree.ElementTree\nx = xml.etree.ElementTree.contextlib.os\n",
        "member",
        "an unlisted reader xml.etree.ElementTree.contextlib",
    ),
    "json-reexports-codecs": (
        "import json\nx = json.codecs\n",
        "member",
        "an unlisted reader json.codecs",
    ),
    "getattr-computed-on-any-receiver": (
        "import contextlib\nprint(dict(getattr(contextlib.os, 'envi' + 'ron')))\n",
        "dynamic",
        "a getattr with a computed name",
    ),
    "hasattr-computed": (
        "def f(o, n):\n    return hasattr(o, n)\n",
        "dynamic",
        "a hasattr with a computed name",
    ),
    "setattr-computed": (
        "def f(o, n):\n    setattr(o, n, 1)\n",
        "dynamic",
        "a setattr with a computed name",
    ),
    "getattr-handed-to-reduce": (
        "import contextlib\nimport functools\n"
        "x = functools.reduce(getattr, ['os', 'path'], contextlib)\n",
        "dynamic",
        "getattr used as a value",
    ),
    "getattr-stored-in-a-list": (
        "fs = [getattr]\n",
        "dynamic",
        "getattr used as a value",
    ),
    "vars-of-an-object": (
        "import contextlib\nprint(vars(contextlib.os)['environ'])\n",
        "dynamic",
        "vars of an object",
    ),
    "generator-frame-builtins": (
        "imp = (x for x in ()).gi_frame.f_builtins['__import__']\n",
        "dynamic",
        "a dunder or frame attribute gi_frame",
    ),
    "traceback-frame-globals": (
        "try:\n    raise ValueError\nexcept ValueError as e:\n"
        "    g = e.__traceback__.tb_frame.f_globals\n",
        "dynamic",
        "a dunder or frame attribute tb_frame",
    ),
    "subclasses-walk": (
        "c = ().__class__.__base__.__subclasses__()\n",
        "dynamic",
        "a dunder or frame attribute __subclasses__",
    ),
    "code-object-replace": (
        "def f():\n    return 0\n\n\nf.__code__ = f.__code__.replace(co_names=('x',))\n",
        "dynamic",
        "a dunder or frame attribute __code__",
    ),
    "closure-cells": (
        "def f():\n    return 0\n\n\nx = f.__closure__\n",
        "dynamic",
        "a dunder or frame attribute __closure__",
    ),
    "instance-dict": (
        "class C:\n    pass\n\n\nx = C().__dict__\n",
        "dynamic",
        "a dunder or frame attribute __dict__",
    ),
    "dunder-by-a-literal-getattr": (
        "def f():\n    return 0\n\n\nx = getattr(f, '__globals__')\n",
        "dynamic",
        "a dunder or frame attribute __globals__",
    ),
    "env-spreads-the-environment": (
        "import os\nimport subprocess\n"
        "subprocess.run(['git', 'x'], env={**os.environ, 'GIT_CONFIG_PARAMETERS': 'a'})\n",
        "command",
        "a child env= that is not a scrub helper's",
    ),
    "env-sets-a-pager": (
        "import os\nimport subprocess\n"
        "subprocess.run(['git', 'log'], env={**os.environ, 'GIT_PAGER': 'env'})\n",
        "command",
        "a child env= that is not a scrub helper's",
    ),
    "env-sets-python-verbose": (
        "import os\nimport subprocess\n"
        "subprocess.run(['python', '-c', 'pass'], env={**os.environ, 'PYTHONVERBOSE': '1'})\n",
        "command",
        "a child env= that is not a scrub helper's",
    ),
    "env-is-the-environment": (
        "import os\nimport subprocess\nsubprocess.run(['git', 'status'], env=os.environ)\n",
        "command",
        "a child env= that is not a scrub helper's",
    ),
    "git-c-joined-with-its-key": (
        "import subprocess\nsubprocess.run(['git', '-calias.x=!env', 'x'])\n",
        "command",
        "a git -c key off the allowlist: alias.x",
    ),
    "git-c-include-path": (
        "import subprocess\nsubprocess.run(['git', '-c', 'include.path=/tmp/x', 'log'])\n",
        "command",
        "a git -c key off the allowlist: include.path",
    ),
    "git-c-protocol-allow": (
        "import subprocess\nsubprocess.run(['git', '-c', 'protocol.ext.allow=always', 'log'])\n",
        "command",
        "a git -c key off the allowlist: protocol.ext.allow",
    ),
    "git-c-difftool-cmd": (
        "import subprocess\nsubprocess.run(['git', '-c', 'difftool.x.cmd=env', 'difftool'])\n",
        "command",
        "a git -c key off the allowlist: difftool.x.cmd",
    ),
    "git-c-ordinary-key": (
        "import subprocess\nsubprocess.run(['git', '-c', 'core.quotepath=true', 'status'])\n",
        "command",
        "a git -c key off the allowlist: core.quotepath",
    ),
    "git-exec-path": (
        "import subprocess\nsubprocess.run(['git', '--exec-path'])\n",
        "command",
        "a git --exec-path option",
    ),
    "git-ext-remote": (
        "import subprocess\nsubprocess.run(['git', 'ls-remote', 'ext::sh -c env'])\n",
        "command",
        "a git ext:: remote",
    ),
    "git-upload-pack": (
        "import subprocess\nsubprocess.run(['git', 'ls-remote', '--upload-pack=env', 'x'])\n",
        "command",
        "a git option that names a program: --upload-pack",
    ),
    "node-prints-process-env": (
        "import subprocess\nsubprocess.run(['node', '-e', 'console.log(process.env)'])\n",
        "command",
        DUMPING_COMMAND,
    ),
    "pwsh-lists-the-env-drive": (
        "import subprocess\nsubprocess.run(['pwsh', '-c', 'gci env:'])\n",
        "command",
        DUMPING_COMMAND,
    ),
    "pytest-showlocals": (
        "import subprocess\nsubprocess.run(['python', '-m', 'pytest', '--showlocals'])\n",
        "command",
        DUMPING_COMMAND,
    ),
    "a-program-off-the-allowlist": (
        "import subprocess\nsubprocess.run(['node', '-e', 'process.exit(0)'])\n",
        "command",
        "a child program node off the allowlist",
    ),
    "env-as-the-program": (
        "import subprocess\nsubprocess.run(['env', 'A=1', 'git', 'status'])\n",
        "command",
        "a child program env off the allowlist",
    ),
}


@pytest.mark.parametrize("arm", sorted(PY_MUST_NAME))
def test_the_allowlist_names_each_reader_it_refuses(arm: str) -> None:
    """Each refused reader is refused BY the rule that owns it, and named."""
    program, kind, detail = PY_MUST_NAME[arm]
    seen = {(f.kind, f.detail) for f in environment_findings({"synthetic": program})}
    named = (kind, detail) in seen
    others = len(seen)
    assert named, f"{arm}: no {kind} finding {detail!r} ({others} other finding(s))"


#: A helper module that reads the key it is handed, and callers in another module.
CROSS_MODULE_HELPER: Final = (
    "import os\n\n\ndef read(k):\n    return os.environ.get(k)\n\n\nread('CLOCKSPEED_SAVE_ROOT')\n"
)
CROSS_MODULE_CALLERS: Final = {
    "from-import": "from helper import read\n\nread('{key}')\n",
    "from-import-as": "from helper import read as fetch\n\nfetch('{key}')\n",
    "module-attribute": "import helper\n\nhelper.read('{key}')\n",
    "map-across-modules": "from helper import read\n\nx = list(map(read, ['{key}']))\n",
    "partial-across-modules": (
        "import functools\n\nfrom helper import read\n\nx = functools.partial(read, '{key}')()\n"
    ),
}


@pytest.mark.parametrize("caller", sorted(CROSS_MODULE_CALLERS))
def test_a_key_handed_across_modules_is_resolved(caller: str) -> None:
    """A key handed to a reader's helper from ANOTHER module is resolved and graded."""
    sources = {
        "helper": CROSS_MODULE_HELPER,
        "caller": CROSS_MODULE_CALLERS[caller].format(key="GITHUB_TOKEN"),
    }
    named = any(
        f.kind == "read" and f.detail == "GITHUB_TOKEN" for f in environment_findings(sources)
    )
    assert named, f"{caller}: a disallowed key handed across modules was not refused"


@pytest.mark.parametrize("caller", sorted(CROSS_MODULE_CALLERS))
def test_an_allowed_key_handed_across_modules_passes(caller: str) -> None:
    """The other half: an allowed key on both sides is resolved, not merely refused."""
    sources = {
        "helper": CROSS_MODULE_HELPER,
        "caller": CROSS_MODULE_CALLERS[caller].format(key="CLOCKSPEED_ACCOUNT_DIR"),
    }
    found = len(environment_findings(sources))
    assert found == 0, f"{caller}: an allowed key across modules read as {found} finding(s)"


#: A personal member read in a named function of a real label.
HOME_IN: Final = "from pathlib import Path\n\n\ndef {name}():\n    return Path.home()\n"
LOCATE_LABEL: Final = "clockspeed/data/locate.py"


def test_a_personal_member_is_permitted_only_in_its_own_function() -> None:
    """A site-scoped member is keyed by label AND function: one file is not a licence."""
    inside = len(environment_findings({LOCATE_LABEL: HOME_IN.format(name="_redaction_pairs")}))
    outside = {
        (f.kind, f.detail)
        for f in environment_findings({LOCATE_LABEL: HOME_IN.format(name="elsewhere")})
    }
    refused = ("member", "an unlisted reader Path.home") in outside
    assert inside == 0, f"Path.home in its scoped function read as {inside} finding(s)"
    assert refused, "Path.home in an unscoped function of the same file was not refused"
