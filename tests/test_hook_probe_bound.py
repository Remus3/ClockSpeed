#!/usr/bin/env python3
"""CS-816 - a hook whose interpreter probe does not answer in bounded time REFUSES.

THE DEFECT. Every tier-0 hook resolves its interpreter through ``cs_probe``, and
before this item the probe ran each candidate with no time limit at all. Three
hang shapes were MEASURED on this toolchain (docs/item_notes/phase7.md, CS-816):

  1. ``PYTHONINSPECT=1``. The candidate runs the program and then goes
     interactive. Under MSYS ``/dev/null`` is the Windows ``NUL`` CHARACTER
     DEVICE, so ``isatty()`` is true and the REPL never returns - WITH stdin
     already redirected.
  2. A candidate that leaves a background process holding stdout. Command
     substitution waits for EOF on the pipe, not for the child to exit.
  3. A wrapper of the form ``exec python "$@" < /dev/null``. It answers a ``-c``
     program exactly, then spins forever on any program handed to it on stdin -
     which is how commit-msg delivers its whole checking program.

A hung hook looks like frozen git rather than a refusal, and a probe that timed
out and then PROCEEDED would be the CS-703 no-op wearing a clock. So the answer
is a BOUND, enforced by a bounding binary whose behaviour is checked before use,
and a timed-out probe REFUSES the hook at whatever rung it happened on.

WHY REAL COMMITS. CLAUDE.md section 2.2: a hook's presence is never proof that it
fires. Every hang arm drives a real ``git commit`` (or ``git push``) in a
throwaway repository and asserts a non-zero exit INSIDE the bound with HEAD - or
the remote ref - unmoved. The harness itself sits inside an outer timeout and
kills the whole process tree if the hook ever hangs, so a failed bound fails an
arm instead of hanging the suite.

WHY EVERY SHAPE HAS A CONTROL. An arm that only ever expects a refusal is
satisfied by a sandbox that refuses everything. Each shape is paired with the same
harness driving a well-behaved interpreter, which must COMMIT.

PLATFORM. Shapes 1 and 3 hang only where ``/dev/null`` is a character device that
reports a tty. Each of those arms MEASURES that precondition first and skips with
the measured reason where it does not hold, so a POSIX runner reports them as NOT
RUN rather than passing them vacuously. Shape 2 and the plain sleeper hang
everywhere and run everywhere.

WHY A CALL LOG AND A WINDOW FROM THE HANG (CS-1201). A window measured from
before ``git`` starts charges every process creation ahead of the hang - git, the
hook, the timeout self-check, each probe half that ANSWERED - to the bound, so a
loaded box reddened a correct refusal at 32.5s. Each test shim therefore appends
one line per invocation to a call log under ``tmp_path`` (``start``, and ``done``
where it returns), holding only a fixed shim label, the probe MODE and a wall
clock stamp - never a path, never an environment value. Two claims are graded
from it. NO FALL-THROUGH is a COUNT: exactly one call never answered, it is the
last call, and it is the expected half - load cannot change an invocation count.
INSIDE THE BOUND is a window that starts at the hanging call's own logged start,
so only the post-expiry tail rides on the slack. The honest-wrapper control
grades each probe half, never the whole commit, against the bound.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. ``tmp_path`` sits under the user
profile, and the wrapper scripts carry the running interpreter's absolute path.
Every outcome is reduced to ints, bools and the hook's own filtered lines before
it is asserted on (CLAUDE.md non-negotiables 3 and 12).
"""

import contextlib
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.git_env import scrub
from tests.pre_push_floor import wired_hook_bytes

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOKS_DIR: Final = REPO_ROOT / ".githooks"
TRACKED_GATE: Final = REPO_ROOT / "tools" / "precommit_gate.py"

PRE_COMMIT: Final = "pre-commit"
COMMIT_MSG: Final = "commit-msg"
PRE_PUSH: Final = "pre-push"
HOOK_NAMES: Final = (PRE_COMMIT, COMMIT_MSG, PRE_PUSH)
COMMIT_HOOKS: Final = (PRE_COMMIT, COMMIT_MSG)

ENV_NAME: Final = "CLOCKSPEED_PYTHON"
INSPECT_NAME: Final = "PYTHONINSPECT"

# The bound is READ from the hooks, never restated here. It is one literal line.
BOUND_LINE: Final = re.compile(rb"^CS_PROBE_BOUND=([0-9]+)$", re.MULTILINE)
BOUND_NAME: Final = b"CS_PROBE_BOUND"

# Used ONLY to size the harness when a hook declares no bound - the pre-repair
# tree - so the arms can still fail cleanly there instead of erroring.
FALLBACK_BOUND: Final = 10

# How long a REFUSAL may take beyond the bound: git's own startup, the hook's,
# the bounding binary's kill grace. KEPT BELOW THE BOUND ON PURPOSE - a refusal
# that fell through to a second rung would have to wait a second bound, and a
# slack smaller than one bound makes that impossible to hide inside the window.
EXIT_SLACK: Final = 8

# CS-1201: how far BELOW the bound a refusal may land, measured from the last
# stamp that must precede the hanging call's bounding binary. The edge compares
# two wall-clock reads, and its unloaded margin MEASURED only 68ms, so a quiet
# fast box or a clock step could redden a correct refusal. One second absorbs
# that and still refuses the early-expiry mutant it exists for: a half bounded
# at 5s expired about 4s inside this tolerance.
LOWER_EDGE_TOLERANCE: Final = 1

# The outer harness limit beyond the bound. A hook still running at bound plus
# this is HUNG, and the harness kills its whole process tree.
HARNESS_SLACK: Final = 40

# Plain git calls that set a sandbox up. Generous, bounded.
GIT_TIMEOUT: Final = 120

# How long a precondition probe waits before calling a shape a hang.
PRECONDITION_WAIT: Final = 5

# The refusal's own words, so an arm pins WHICH rule refused.
TIMEOUT_REFUSAL: Final = "did not answer within"
BINARY_REFUSAL: Final = "cannot be bounded"

SANDBOX_BRANCH: Final = "cs816-sandbox"
FIXTURE_NAME: Final = "CS-816 Fixture"
FIXTURE_EMAIL: Final = "cs816@example.invalid"
MESSAGE: Final = "CS-816: an ordinary subject that says what changed\n"
CLEAN_CONTENT: Final = b"an ordinary line of 7-bit ascii\n"
NO_HEAD: Final = "(no commit yet)"

REAL_PYTHON_POSIX: Final = Path(sys.executable).as_posix()

DRIVE_PATH: Final = re.compile(r"[A-Za-z]:[\\/]")
ENVIRONMENT_REPR: Final = "<CS-816 child environment, contents withheld>"


# --- the call log (CS-1201) ---------------------------------------------------

# The one file every test shim appends to, under the arm's own tmp_path.
CALL_LOG: Final = "calls.log"

# A done line whose status is at or above this ended on a SIGNAL - the bound's
# TERM or KILL - so the call did not answer, whatever else the line says.
KILLED_BY_SIGNAL: Final = 128

# The probe's three halves, in the order every hook's cs_probe runs them.
PROBE_HALVES: Final = ("-c", "-c", "-")

# Fixed shim labels. A label is test vocabulary, never a path.
HONEST: Final = "honest"
NUL_STDIN: Final = "nul-stdin"
BACKGROUND: Final = "background"
SLEEPER: Final = "sleeper"
LADDER_RUNGS: Final = ("python", "python3", "py")

# Fields on a start line (start, label, mode, stamp) and a done line (plus status).
START_FIELDS: Final = 4
DONE_FIELDS: Final = 5


def log_start(log: Path, label: str) -> str:
    """Shell lines that append ``start <label> <mode> <stamp>`` to ``log``.

    The mode is the first argument ONLY when it is one of the probe's own
    flags; anything else - a script path included - is written as ``other``.
    The stamp is the system wall clock, the same clock ``time.time`` reads.
    """
    return (
        'case "$1" in -c|-|-3) cs_m="$1" ;; *) cs_m=other ;; esac\n'
        "printf 'start "
        + label
        + ' %s %s\\n\' "$cs_m" "$(date +%s.%N)" >>"'
        + log.as_posix()
        + '"\n'
    )


def log_done(log: Path, label: str) -> str:
    """Shell lines that append ``done <label> <mode> <stamp> <status>`` and exit with it."""
    return (
        "cs_r=$?\n"
        "printf 'done "
        + label
        + ' %s %s %s\\n\' "$cs_m" "$(date +%s.%N)" "$cs_r" >>"'
        + log.as_posix()
        + '"\n'
        'exit "$cs_r"\n'
    )


def honest_shim(log: Path) -> str:
    """A well-behaved wrapper: the real interpreter, arguments and streams intact.

    NOT an exec, so it can log the call's return and pass the status through.
    """
    return (
        "#!/bin/sh\n"
        + log_start(log, HONEST)
        + '"'
        + REAL_PYTHON_POSIX
        + '" "$@"\n'
        + log_done(log, HONEST)
    )


def nul_stdin_shim(log: Path) -> str:
    """Shape 3: the real interpreter with stdin replaced by /dev/null."""
    return (
        "#!/bin/sh\n"
        + log_start(log, NUL_STDIN)
        + '"'
        + REAL_PYTHON_POSIX
        + '" "$@" </dev/null\n'
        + log_done(log, NUL_STDIN)
    )


def background_shim(pid_file: Path, log: Path) -> str:
    """Shape 2: leaves a background process holding stdout, then runs python."""
    return (
        "#!/bin/sh\n" + log_start(log, BACKGROUND) + "sleep 600 &\n"
        'printf \'%s\' "$!" >"' + pid_file.as_posix() + '"\n'
        'exec "' + REAL_PYTHON_POSIX + '" "$@"\n'
    )


def sleeper_shim(pid_file: Path, log: Path) -> str:
    """The plainest hang: a candidate that never answers anything."""
    return (
        "#!/bin/sh\n"
        + log_start(log, SLEEPER)
        + 'printf \'%s\' "$$" >"'
        + pid_file.as_posix()
        + '"\nexec sleep 600\n'
    )


def ladder_shim(log: Path, rung: str) -> str:
    """A PATH-first stand-in for one ladder rung: log, then exec the real interpreter.

    The ``py`` rung is asked with ``-3`` first, which the real interpreter would
    reject, so that one flag is dropped before the exec.
    """
    drop = 'if [ "$1" = "-3" ]; then shift; fi\n' if rung == "py" else ""
    return "#!/bin/sh\n" + log_start(log, rung) + drop + 'exec "' + REAL_PYTHON_POSIX + '" "$@"\n'


class Call(NamedTuple):
    """One logged shim invocation: which shim, which probe mode, and when."""

    shim: str
    mode: str
    start: float
    done: float | None = None
    status: int | None = None

    @property
    def answered(self) -> bool:
        """It returned on its own: a done line, and not ended by a signal."""
        return self.done is not None and self.status is not None and self.status < KILLED_BY_SIGNAL

    @property
    def duration(self) -> float | None:
        """Seconds from its start to its return, or None when it never answered."""
        return self.done - self.start if self.answered and self.done is not None else None


def parse_calls(text: str) -> tuple[Call, ...]:
    """The calls a call log records, in order. A malformed log fails loudly.

    Calls are sequential, so a done line closes the call opened by the line
    before it. No line's content is rendered on failure, only its number.
    """
    calls: list[Call] = []
    for number, line in enumerate(text.splitlines(), start=1):
        fields = line.split(" ")
        if fields[0] == "start" and len(fields) == START_FIELDS:
            calls.append(Call(fields[1], fields[2], float(fields[3])))
            continue
        if fields[0] == "done" and len(fields) == DONE_FIELDS:
            open_call = calls[-1] if calls else None
            closes = (
                open_call is not None
                and open_call.done is None
                and (open_call.shim, open_call.mode) == (fields[1], fields[2])
            )
            if not closes or open_call is None:
                raise AssertionError(f"call log line {number} closes no open call")
            calls[-1] = open_call._replace(done=float(fields[3]), status=int(fields[4]))
            continue
        raise AssertionError(f"call log line {number} is malformed")
    return tuple(calls)


def read_calls(log: Path) -> tuple[Call, ...]:
    """The calls ``log`` records; none when no shim ever ran."""
    return parse_calls(log.read_text(encoding="ascii")) if log.is_file() else ()


# --- the bound, read from the hooks ------------------------------------------


def declared_bounds(hook: str) -> list[int]:
    """Every literal ``CS_PROBE_BOUND=<digits>`` line in ``hook``."""
    raw = (HOOKS_DIR / hook).read_bytes()
    return [int(match) for match in BOUND_LINE.findall(raw)]


def harness_bound() -> int:
    """The bound the arms size themselves by: the declared one, else the fallback."""
    found = declared_bounds(PRE_COMMIT)
    return found[0] if len(found) == 1 else FALLBACK_BOUND


# --- process-tree handling ----------------------------------------------------


class Run(NamedTuple):
    """One bounded child run, reduced to what an arm may assert on."""

    returncode: int
    killed: bool
    elapsed: float
    stderr: str
    # Wall clock, so a shim's logged stamp can be compared with them (CS-1201).
    started_at: float = 0.0
    returned_at: float = 0.0


def kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill ``proc`` AND every descendant. A killed parent skips nothing for them.

    On Windows the hook's shell, the bounding binary and the interpreter are all
    real Windows processes under git, so ``taskkill /T`` walks them. Elsewhere the
    child was started in its own session and the whole group is killed.
    """
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)


def run_bounded(argv: list[str], cwd: Path, env: dict[str, str], limit: float) -> Run:
    """Run ``argv`` with a hard outer limit, reaping the whole tree on expiry."""
    extra: dict[str, object] = {}
    if sys.platform == "win32":
        extra["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        extra["start_new_session"] = True
    started_at = time.time()
    started = time.monotonic()
    proc = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **extra,  # type: ignore[call-overload]
    )
    killed = False
    try:
        _, err = proc.communicate(timeout=limit)
    except subprocess.TimeoutExpired:
        killed = True
        kill_tree(proc)
        try:
            _, err = proc.communicate(timeout=GIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=GIT_TIMEOUT)
            err = b""
    elapsed = time.monotonic() - started
    returned_at = time.time()
    stderr = err.decode("utf-8", "replace")
    return Run(proc.returncode, killed, elapsed, stderr, started_at, returned_at)


# --- the sandbox --------------------------------------------------------------


class Environment(NamedTuple):
    """The child environment, wrapped so no failure report can render it."""

    variables: dict[str, str]

    def __repr__(self) -> str:
        """Render without any of the environment's contents."""
        return ENVIRONMENT_REPR


class Sandbox(NamedTuple):
    """A throwaway repository with exactly one tracked hook wired."""

    work: Path
    hooks: Path
    remote: Path
    env: dict[str, str]
    hook: str
    # CS-1201: how long the seed commit - an ACCEPTED commit through the same
    # hook on the same box - measured. Zero until the seed has run.
    seed_elapsed: float = 0.0

    @property
    def prefix(self) -> str:
        """The banner the hook writes, so a refusal can be attributed to it."""
        return "clockspeed " + self.hook

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return f"<CS-816 sandbox for {self.hook}, paths withheld>"


class Attempt(NamedTuple):
    """The measured outcome of one real commit or push."""

    returncode: int
    killed: bool
    elapsed: float
    moved: bool
    hook_output: tuple[str, ...]
    # Wall clock around the git command, for the window from the hang (CS-1201).
    started_at: float = 0.0
    returned_at: float = 0.0

    @property
    def blocked(self) -> bool:
        """Git refused, the harness did not have to kill it, and nothing landed."""
        return self.returncode != 0 and not self.killed and not self.moved

    @property
    def accepted(self) -> bool:
        """Git succeeded and the change landed."""
        return self.returncode == 0 and not self.killed and self.moved

    def refusals(self, words: str) -> int:
        """How many hook lines carry ``words``."""
        return sum(1 for line in self.hook_output if words in line)

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.hook_output) if self.hook_output else "(no hook output)"
        return (
            f"exit={self.returncode} killed={self.killed} moved={self.moved} "
            f"elapsed={self.elapsed:.1f}s expiry={self.refusals(TIMEOUT_REFUSAL)}\n{shown}"
        )


def hook_output(stderr: str, prefix: str) -> tuple[str, ...]:
    """Keep only the hook's own lines, and drop any line carrying a drive path."""
    return tuple(
        line
        for line in stderr.split("\n")
        if line.startswith((prefix, "  ")) and line.strip() and not DRIVE_PATH.search(line)
    )


def run_git(box: Sandbox, *args: str, env: dict[str, str] | None = None) -> int:
    """Run one set-up git command in the sandbox and return its exit code."""
    return subprocess.run(
        ["git", *args],
        cwd=str(box.work),
        capture_output=True,
        timeout=GIT_TIMEOUT,
        env=box.env if env is None else env,
        check=False,
    ).returncode


def head_of(box: Sandbox, env: dict[str, str]) -> str:
    """HEAD's commit id, or a sentinel before the first commit."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(box.work),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=env,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else NO_HEAD


def remote_ref(box: Sandbox, env: dict[str, str]) -> str:
    """The sandbox branch's id on the bare remote, or empty when absent."""
    proc = subprocess.run(
        ["git", "ls-remote", "origin", "refs/heads/" + SANDBOX_BRANCH],
        cwd=str(box.work),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=env,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def child_env(
    box: Sandbox, *, interpreter: str | None = None, extra: dict[str, str] | None = None
) -> dict[str, str]:
    """The sandbox environment with CLOCKSPEED_PYTHON and extras set for ONE attempt."""
    env = dict(box.env)
    env.pop(ENV_NAME, None)
    if interpreter is not None:
        env[ENV_NAME] = interpreter
    env.update(extra or {})
    return env


def harness_limit(box: Sandbox) -> float:
    """The outer kill ceiling for one attempt in ``box``.

    CS-1201: the bound plus the harness slack PLUS what the seed commit - an
    accepted commit through the same hook on the same box - measured, so a
    loaded box widens the ceiling by its own measured overhead rather than an
    assumed one. A real hang is ``sleep 600`` or an endless REPL, so this costs
    time only on a genuine regression.
    """
    return harness_bound() + HARNESS_SLACK + box.seed_elapsed


_PAYLOADS: list[int] = [0]


def commit_attempt(box: Sandbox, env: dict[str, str], content: bytes = CLEAN_CONTENT) -> Attempt:
    """Stage a NEW file and drive a real, outer-bounded ``git commit``."""
    _PAYLOADS[0] += 1
    name = f"payload-{_PAYLOADS[0]}.txt"
    (box.work / name).write_bytes(content)
    staged = run_git(box, "add", name, env=env)
    assert staged == 0, "the sandbox change did not stage"
    message = box.hooks.parent / "message.txt"
    message.write_bytes(MESSAGE.encode("ascii"))
    before = head_of(box, env)
    run = run_bounded(
        ["git", "commit", "-q", "-F", str(message)],
        box.work,
        env,
        harness_limit(box),
    )
    moved = head_of(box, env) != before
    lines = hook_output(run.stderr, box.prefix)
    return Attempt(
        run.returncode, run.killed, run.elapsed, moved, lines, run.started_at, run.returned_at
    )


def push_attempt(box: Sandbox, env: dict[str, str]) -> Attempt:
    """Drive a real, outer-bounded ``git push`` at the sandbox's own bare remote."""
    before = remote_ref(box, env)
    assert not before, "the branch is already on the remote; the push would not run the hook"
    run = run_bounded(
        ["git", "push", "-q", "origin", SANDBOX_BRANCH],
        box.work,
        env,
        harness_limit(box) + GIT_TIMEOUT,
    )
    moved = bool(remote_ref(box, env))
    lines = hook_output(run.stderr, box.prefix)
    return Attempt(
        run.returncode, run.killed, run.elapsed, moved, lines, run.started_at, run.returned_at
    )


def attempt(box: Sandbox, env: dict[str, str]) -> Attempt:
    """A commit for a commit hook, a push for pre-push."""
    return push_attempt(box, env) if box.hook == PRE_PUSH else commit_attempt(box, env)


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment with the operator's git configuration and hang triggers removed."""
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for name in (ENV_NAME, INSPECT_NAME):
        env.pop(name, None)
    return Environment(env)


def make_sandbox(tmp_path: Path, isolated: Environment, hook: str) -> Sandbox:
    """A real repository with exactly one tracked hook wired and one commit in it.

    A pre-push copy differs from the tracked hook on its CS-824 floor line only.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    installed = hooks / hook
    # CS-824: pre-push gets the one-line test floor; the other hooks are verbatim.
    installed.write_bytes(wired_hook_bytes(hook, (HOOKS_DIR / hook).read_bytes()))
    installed.chmod(0o755)
    work = tmp_path / "work"
    work.mkdir()
    remote = tmp_path / "remote.git"
    box = Sandbox(work, hooks, remote, isolated.variables, hook)

    assert run_git(box, "init", "-q", "-b", SANDBOX_BRANCH) == 0, "git init failed"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("core.hooksPath", str(hooks)),
    ):
        assert run_git(box, "config", key, value) == 0, f"{key} could not be written"

    if hook == PRE_COMMIT:
        (work / "tools").mkdir()
        shutil.copy2(TRACKED_GATE, work / "tools" / "precommit_gate.py")
    if hook == PRE_PUSH:
        tests = work / "tests"
        tests.mkdir()
        (tests / "test_sandbox_arm.py").write_bytes(
            b"def test_sandbox_arm() -> None:\n    assert True\n"
        )
        (work / "pytest.ini").write_bytes(b"[pytest]\n")
        assert run_git(box, "init", "-q", "--bare", str(remote)) == 0, "no bare remote"
        assert run_git(box, "remote", "add", "origin", str(remote)) == 0, "remote not added"

    seed = commit_attempt(box, child_env(box))
    assert seed.accepted, f"the sandbox could not make its first commit:\n{seed.report}"
    return box._replace(seed_elapsed=seed.elapsed)


def write_shim(tmp_path: Path, name: str, body: str) -> str:
    """Write an executable wrapper and return its POSIX-form path."""
    shim = tmp_path / name
    shim.write_bytes(body.encode("ascii"))
    shim.chmod(0o755)
    return shim.as_posix()


# --- a POSIX shell for reap checks and block-level arms -----------------------


def posix_shell() -> str | None:
    """A shell that can run a POSIX script, resolved without assuming the caller's PATH.

    ``sh`` on PATH wins. Where the test runner was started from a shell that
    does not carry Git's own ``usr/bin`` on PATH (PowerShell on Windows), the
    shell git itself uses is found beside git's exec path.
    """
    found = shutil.which("sh")
    if found:
        return found
    proc = subprocess.run(
        ["git", "--exec-path"], capture_output=True, text=True, timeout=GIT_TIMEOUT, check=False
    )
    if proc.returncode != 0:
        return None
    for parent in Path(proc.stdout.strip()).parents:
        for candidate in (parent / "usr" / "bin" / "sh.exe", parent / "bin" / "sh.exe"):
            if candidate.is_file():
                return str(candidate)
    return None


SHELL: Final = posix_shell()
SHELL_SKIP: Final = (
    "NOT RUN, NOT PASSED: this arm requires a POSIX `sh`, and none resolved on PATH or "
    "beside git's exec path. It makes no claim about whether anything else covers it."
)


def shell_env() -> dict[str, str]:
    """The environment for a direct shell call: this process's, repository-scrubbed."""
    return scrub(dict(os.environ))


def process_alive(pid: str) -> bool:
    """Whether a POSIX-layer process id is still alive, asked of the shell layer."""
    assert SHELL is not None, "process_alive needs a POSIX shell"
    proc = subprocess.run(
        [SHELL, "-c", 'kill -0 "$1" 2>/dev/null', "cs816", pid],
        capture_output=True,
        timeout=GIT_TIMEOUT,
        env=shell_env(),
        check=False,
    )
    return proc.returncode == 0


def reap(pid_file: Path) -> bool:
    """Kill a recorded background process if it survived; return whether it had."""
    if not pid_file.is_file() or SHELL is None:
        return False
    pid = pid_file.read_text(encoding="ascii").strip()
    if not pid.isdigit():
        return False
    alive = process_alive(pid)
    if alive:
        subprocess.run(
            [SHELL, "-c", 'kill -9 "$1" 2>/dev/null', "cs816", pid],
            capture_output=True,
            timeout=GIT_TIMEOUT,
            env=shell_env(),
            check=False,
        )
    return alive


# --- measured preconditions ---------------------------------------------------


def hangs(argv: list[str], extra_env: dict[str, str]) -> bool:
    """Whether ``argv`` with stdin from the null device fails to return in time."""
    env = scrub(dict(os.environ))
    env.update(extra_env)
    try:
        subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=PRECONDITION_WAIT,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return True
    return False


INSPECT_HANGS: Final = hangs([sys.executable, "-c", "pass"], {INSPECT_NAME: "1"})
NUL_STDIN_HANGS: Final = hangs([sys.executable, "-"], {})

INSPECT_SKIP: Final = (
    "NOT RUN, NOT PASSED: MEASURED that PYTHONINSPECT=1 with stdin from the null device "
    "returns on this platform (the device is not a tty here), so the shape does not hang "
    "and there is nothing for the bound to stop. The sleeper and background-child arms "
    "prove the bound here instead."
)
NUL_SKIP: Final = (
    "NOT RUN, NOT PASSED: MEASURED that `python -` with stdin from the null device returns "
    "on this platform (an empty program, not a REPL), so the /dev/null wrapper does not "
    "hang here and there is nothing for the bound to stop."
)


# --- the bound is ONE literal constant, byte-identical ------------------------


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_each_hook_declares_exactly_one_literal_bound(hook: str) -> None:
    """Grant condition 4: one literal, the same in every hook, never overridable.

    A literal line matched end to end cannot read an environment variable or a
    config file. The name is also never ASSIGNED anywhere else in the hook, so no
    later line can replace the literal.
    """
    found = declared_bounds(hook)
    assert len(found) == 1, f"{hook} declares {len(found)} literal bounds, expected exactly one"
    assert found[0] > EXIT_SLACK, "the bound must exceed the refusal slack the arms allow"
    raw = (HOOKS_DIR / hook).read_bytes()
    assignments = raw.count(BOUND_NAME + b"=")
    assert assignments == 1, f"{hook} assigns the bound {assignments} times, expected once"
    assert found == declared_bounds(PRE_COMMIT), f"{hook} declares a different bound"


# --- the three measured shapes, and the plain sleeper, by real commits --------


def assert_refused_inside_the_bound(
    outcome: Attempt, calls: tuple[Call, ...], hung: tuple[str, str]
) -> None:
    """The acceptance, stated once: non-zero, unmoved, attributable, inside the bound.

    CS-1201 splits "inside the bound" into its two real claims, so neither is
    graded against process creation that a loaded box stretches:

    - NO FALL-THROUGH is a COUNT from the call log: exactly one call never
      answered, nothing ran after it, and it is the ``hung`` shim and mode. A
      second rung writes a second call whatever the clock says.
    - THE EXPIRY is timed from the hang itself. The upper edge runs from the
      hanging call's own logged start, so only the post-expiry tail rides on
      EXIT_SLACK, which stays below one bound. The lower edge runs from the last
      stamp that must precede the hang's bounding binary - the answering call
      before it, else git's own start - so it is load-immune: an expiry cannot
      arrive early. It allows LOWER_EDGE_TOLERANCE for the two clock reads.
    """
    bound = harness_bound()
    assert not outcome.killed, f"the hook HUNG - the harness had to kill it:\n{outcome.report}"
    assert outcome.blocked, f"the hook did not refuse:\n{outcome.report}"
    assert outcome.refusals(TIMEOUT_REFUSAL) == 1, (
        f"refused, but NOT by the timed-out probe:\n{outcome.report}"
    )
    assert calls, f"no shim call was logged, so this arm measured nothing:\n{outcome.report}"
    unanswered = sum(1 for call in calls if not call.answered)
    assert unanswered == 1, (
        f"{unanswered} of {len(calls)} calls never answered, expected exactly one - a "
        f"second is a fall-through to another rung:\n{outcome.report}"
    )
    hang = calls[-1]
    assert not hang.answered, f"a call ran after the one that hung:\n{outcome.report}"
    assert (hang.shim, hang.mode) == hung, (
        f"the call that hung was [{hang.shim} {hang.mode}], not the expected "
        f"[{hung[0]} {hung[1]}]:\n{outcome.report}"
    )
    before = calls[-2].done if len(calls) > 1 else None
    anchor = outcome.started_at if before is None else before
    floor = outcome.returned_at - anchor
    assert floor >= bound - LOWER_EDGE_TOLERANCE, (
        f"refused {floor:.2f}s after the hanging call could first have started, "
        f"before the bound of {bound}s could expire:\n{outcome.report}"
    )
    window = outcome.returned_at - hang.start
    assert window < bound + EXIT_SLACK, (
        f"refused {window:.2f}s after the hanging call started, not inside the bound "
        f"of {bound}s plus {EXIT_SLACK}s:\n{outcome.report}"
    )


def assert_honest_wrapper_committed(outcome: Attempt, calls: tuple[Call, ...]) -> None:
    """The control's acceptance: the commit landed and no probe half met the bound.

    CS-1201: the whole commit - git, the hook, three probe halves and the hook's
    own program - was once graded against the PROBE bound, which no probe half
    need approach for the sum to exceed. Each probe half is graded instead: it
    ANSWERED (a start with no done, or a done by signal, is a half the bound cut
    off) and its own duration stayed under the bound. Only the probe halves run
    under the bound, so only they are timed against it.
    """
    bound = harness_bound()
    assert outcome.accepted, f"an honest wrapper was refused:\n{outcome.report}"
    modes = tuple(call.mode for call in calls[: len(PROBE_HALVES)])
    assert modes == PROBE_HALVES, (
        f"the log does not open with the probe's halves, so the shim was not the "
        f"interpreter - modes {modes}:\n{outcome.report}"
    )
    assert len(calls) > len(PROBE_HALVES), (
        f"only {len(calls)} calls: the hook's own program never reached the shim after "
        f"the probe:\n{outcome.report}"
    )
    unanswered = sum(1 for call in calls if not call.answered)
    assert unanswered == 0, (
        f"{unanswered} of {len(calls)} calls never answered - a probe half that timed "
        f"out and proceeded:\n{outcome.report}"
    )
    halves = [call.duration for call in calls[: len(PROBE_HALVES)]]
    slowest = max((took for took in halves if took is not None), default=0.0)
    assert slowest < bound, (
        f"a probe half took {slowest:.2f}s, which reached the bound of {bound}s:\n{outcome.report}"
    )


def ladder_bin(tmp_path: Path, log: Path) -> Path:
    """A directory of PATH-first logging stand-ins, one per ladder rung."""
    directory = tmp_path / "ladder-bin"
    directory.mkdir()
    for rung in LADDER_RUNGS:
        shim = directory / rung
        shim.write_bytes(ladder_shim(log, rung).encode("ascii"))
        shim.chmod(0o755)
    return directory


@pytest.mark.skipif(not INSPECT_HANGS, reason=INSPECT_SKIP)
@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_pythoninspect_is_refused_inside_the_bound(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """Shape 1, the acceptance's own named proof. RED before the repair: HUNG.

    No CLOCKSPEED_PYTHON: the ladder starts at its first rung, which hangs, and
    the hook must refuse THERE rather than fall through. Every rung is a
    PATH-first logging stand-in for the real interpreter, so a fall-through to
    ``python3`` or ``py -3`` writes a second call and the count goes red.
    """
    box = make_sandbox(tmp_path, isolated, hook)
    log = tmp_path / CALL_LOG
    env = child_env(box, extra={INSPECT_NAME: "1"})
    env["PATH"] = str(ladder_bin(tmp_path, log)) + os.pathsep + env["PATH"]
    outcome = attempt(box, env)
    assert_refused_inside_the_bound(outcome, read_calls(log), (LADDER_RUNGS[0], "-c"))


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_pythoninspect_control_the_same_harness_accepts_without_it(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """The control for shape 1: the same sandbox and harness, the variable unset."""
    box = make_sandbox(tmp_path, isolated, hook)
    outcome = attempt(box, child_env(box))
    assert outcome.accepted, f"the control was refused:\n{outcome.report}"


@pytest.mark.skipif(not NUL_STDIN_HANGS, reason=NUL_SKIP)
@pytest.mark.parametrize("hook", COMMIT_HOOKS)
def test_a_dev_null_stdin_wrapper_is_refused_inside_the_bound(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """Shape 3. RED before the repair: the probe passed, then commit-msg HUNG.

    The wrapper answers every ``-c`` program exactly, so a probe that asked only
    ``-c`` questions passed it; the hang arrived afterwards, outside any probe,
    on the heredoc. The probe now also hands the candidate a program on STDIN
    under the bound, which is the delivery shape commit-msg really uses.
    """
    box = make_sandbox(tmp_path, isolated, hook)
    log = tmp_path / CALL_LOG
    shim = write_shim(tmp_path, "nul-stdin.sh", nul_stdin_shim(log))
    outcome = commit_attempt(box, child_env(box, interpreter=shim))
    assert_refused_inside_the_bound(outcome, read_calls(log), (NUL_STDIN, "-"))


@pytest.mark.skipif(SHELL is None, reason=SHELL_SKIP)
@pytest.mark.parametrize("hook", COMMIT_HOOKS)
def test_a_background_child_holding_stdout_is_refused_and_reaped(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """Shape 2. RED before the repair: the capture waited on the child's pipe.

    The interpreter itself answers at once; the process it leaves behind is what
    holds the probe's stdout open. The capture therefore runs INSIDE the bounded
    process, so the bound covers the pipe and not merely the direct child - and
    expiry kills the group, which is what reaps the background process.
    """
    box = make_sandbox(tmp_path, isolated, hook)
    pid_file = tmp_path / "background.pid"
    log = tmp_path / CALL_LOG
    shim = write_shim(tmp_path, "background.sh", background_shim(pid_file, log))
    try:
        outcome = commit_attempt(box, child_env(box, interpreter=shim))
        survived = reap(pid_file)
    finally:
        reap(pid_file)
    assert_refused_inside_the_bound(outcome, read_calls(log), (BACKGROUND, "-c"))
    assert pid_file.is_file(), "the wrapper never ran, so this arm measured nothing"
    assert not survived, "the background process outlived the refusal - it was not reaped"


@pytest.mark.skipif(SHELL is None, reason=SHELL_SKIP)
@pytest.mark.parametrize("hook", COMMIT_HOOKS)
def test_a_candidate_that_never_answers_is_refused_and_reaped(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """The platform-independent proof of the bound: the candidate just sleeps."""
    box = make_sandbox(tmp_path, isolated, hook)
    pid_file = tmp_path / "sleeper.pid"
    log = tmp_path / CALL_LOG
    shim = write_shim(tmp_path, "sleeper.sh", sleeper_shim(pid_file, log))
    try:
        outcome = commit_attempt(box, child_env(box, interpreter=shim))
        survived = reap(pid_file)
    finally:
        reap(pid_file)
    assert_refused_inside_the_bound(outcome, read_calls(log), (SLEEPER, "-c"))
    assert pid_file.is_file(), "the sleeper never ran, so this arm measured nothing"
    assert not survived, "the sleeping candidate outlived the refusal - it was not reaped"


@pytest.mark.parametrize("hook", COMMIT_HOOKS)
def test_wrapper_control_an_honest_wrapper_commits(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """The control for shapes 2 and 3 and the sleeper: the same harness, a clean wrapper."""
    box = make_sandbox(tmp_path, isolated, hook)
    log = tmp_path / CALL_LOG
    shim = write_shim(tmp_path, "honest.sh", honest_shim(log))
    outcome = commit_attempt(box, child_env(box, interpreter=shim))
    assert_honest_wrapper_committed(outcome, read_calls(log))


@pytest.mark.skipif(SHELL is None, reason=SHELL_SKIP)
def test_the_refusal_echoes_no_interpreter_path(tmp_path: Path, isolated: Environment) -> None:
    """Grant condition 6: the timed-out refusal names no path and no variable value."""
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    pid_file = tmp_path / "sleeper.pid"
    shim = write_shim(tmp_path, "sleeper.sh", sleeper_shim(pid_file, tmp_path / CALL_LOG))
    try:
        run = run_bounded(
            ["git", "commit", "-q", "--allow-empty", "-m", MESSAGE.strip()],
            box.work,
            child_env(box, interpreter=shim),
            harness_limit(box),
        )
    finally:
        reap(pid_file)
    leaked = shim in run.stderr or str(Path(shim)) in run.stderr
    named = TIMEOUT_REFUSAL in run.stderr
    assert named, "the timed-out refusal did not fire, so this arm measured nothing"
    assert not leaked, "the refusal echoed the interpreter's path"


# --- the graders, on synthetic timing records (CS-1201) -----------------------
#
# No commit, no bound waited: each arm hands a grader evidence SHAPED like one
# measured run. The first two are the shapes a loaded box produced - a correct
# refusal and a correct control that the absolute windows reddened. The rest are
# plants each grader must still refuse, and each asserts its plant was built.

SYNTHETIC_T0: Final = 1_000_000.0


def synthetic(returned_after: float, *, accepted: bool = False) -> Attempt:
    """An attempt that started at SYNTHETIC_T0 and returned ``returned_after`` later."""
    words = f"clockspeed {PRE_COMMIT}: the interpreter probe {TIMEOUT_REFUSAL} n seconds."
    return Attempt(
        0 if accepted else 1,
        False,
        returned_after,
        accepted,
        () if accepted else (words,),
        SYNTHETIC_T0,
        SYNTHETIC_T0 + returned_after,
    )


def call_log(*entries: tuple[str, str, float, float | None, int | None]) -> tuple[Call, ...]:
    """Calls parsed from log TEXT, so the parser is on the path of every grader arm."""
    lines = []
    for shim, mode, start, done, status in entries:
        lines.append(f"start {shim} {mode} {SYNTHETIC_T0 + start:.9f}")
        if done is not None:
            lines.append(f"done {shim} {mode} {SYNTHETIC_T0 + done:.9f} {status}")
    return parse_calls("\n".join(lines) + "\n")


def loaded_refusal() -> tuple[Attempt, tuple[Call, ...]]:
    """The measured red: two answering halves ate most of the window, the third hung."""
    bound = harness_bound()
    calls = call_log(
        (NUL_STDIN, "-c", 6.0, 11.0, 0),
        (NUL_STDIN, "-c", 15.0, 20.0, 97),
        (NUL_STDIN, "-", 22.3, None, None),
    )
    return synthetic(22.3 + bound + 0.2), calls


def test_grader_charges_the_bound_only_from_the_hanging_call() -> None:
    """A correct refusal on a loaded box: the hang started late, the expiry was on time."""
    outcome, calls = loaded_refusal()
    assert outcome.elapsed >= harness_bound() + EXIT_SLACK, "the plant is not the loaded shape"
    assert_refused_inside_the_bound(outcome, calls, (NUL_STDIN, "-"))


def test_grader_control_grades_each_probe_half_not_the_commit() -> None:
    """A correct control on a loaded box: every call answered well inside the bound."""
    step = harness_bound() * 0.3
    calls = call_log(
        (HONEST, "-c", 0.1, 0.1 + step, 0),
        (HONEST, "-c", 0.2 + step, 0.2 + 2 * step, 97),
        (HONEST, "-", 0.3 + 2 * step, 0.3 + 3 * step, 0),
        (HONEST, "other", 0.4 + 3 * step, 0.4 + 4 * step, 0),
    )
    outcome = synthetic(0.5 + 4 * step, accepted=True)
    assert outcome.elapsed >= harness_bound(), "the plant is not the loaded shape"
    assert_honest_wrapper_committed(outcome, calls)


def test_grader_refuses_a_second_hanging_call() -> None:
    """Condition 1: a fall-through to a second rung is red whatever the clock says."""
    bound = harness_bound()
    calls = call_log(
        (SLEEPER, "-c", 1.0, None, None),
        (SLEEPER, "-c", 1.5 + bound, None, None),
    )
    assert not any(call.answered for call in calls), "the plant did not apply"
    with pytest.raises(AssertionError, match="never answered"):
        assert_refused_inside_the_bound(synthetic(2.0 + 2 * bound), calls, (SLEEPER, "-c"))


def test_grader_refuses_a_call_after_the_hang() -> None:
    """Condition 1: nothing may run after the call that hung."""
    calls = call_log(
        (NUL_STDIN, "-", 1.0, None, None),
        (NUL_STDIN, "-c", 12.0, 12.5, 0),
    )
    assert calls[-1].answered, "the plant did not apply"
    with pytest.raises(AssertionError, match="ran after"):
        assert_refused_inside_the_bound(synthetic(13.0), calls, (NUL_STDIN, "-"))


def test_grader_refuses_the_wrong_half_hanging() -> None:
    """The arm names which half must hang; a different one is a different defect."""
    calls = call_log((NUL_STDIN, "-c", 1.0, None, None))
    with pytest.raises(AssertionError, match="not the expected"):
        assert_refused_inside_the_bound(synthetic(1.2 + harness_bound()), calls, (NUL_STDIN, "-"))


def test_grader_refuses_a_tail_past_the_slack() -> None:
    """Condition 8: the window from the hang is still graded, one slack wide."""
    over = harness_bound() + EXIT_SLACK + 0.5
    calls = call_log((SLEEPER, "-c", 1.0, None, None))
    outcome = synthetic(1.0 + over)
    assert outcome.returned_at - calls[-1].start >= harness_bound() + EXIT_SLACK, "no plant"
    with pytest.raises(AssertionError, match="not inside the bound"):
        assert_refused_inside_the_bound(outcome, calls, (SLEEPER, "-c"))


def test_grader_refuses_a_refusal_before_the_bound() -> None:
    """An expiry cannot arrive early: a refusal sooner than the bound was not one."""
    calls = call_log(
        (NUL_STDIN, "-c", 1.0, 1.5, 0),
        (NUL_STDIN, "-c", 2.0, 2.5, 97),
        (NUL_STDIN, "-", 3.0, None, None),
    )
    # The measured early-expiry mutant: the stdin half bounded at half the bound.
    outcome = synthetic(2.5 + harness_bound() / 2)
    early = outcome.returned_at - SYNTHETIC_T0 - 2.5
    assert early < harness_bound() - LOWER_EDGE_TOLERANCE, "the plant did not apply"
    with pytest.raises(AssertionError, match="before the bound"):
        assert_refused_inside_the_bound(outcome, calls, (NUL_STDIN, "-"))


def test_grader_lower_edge_tolerance_sits_between_its_two_plants() -> None:
    """A clock step or a quiet fast box inside the tolerance passes; one past it fails."""
    bound = harness_bound()
    calls = call_log(
        (NUL_STDIN, "-c", 1.0, 1.5, 0),
        (NUL_STDIN, "-c", 2.0, 2.5, 97),
        (NUL_STDIN, "-", 3.0, None, None),
    )
    inside = synthetic(2.5 + bound - 0.5)
    past = synthetic(2.5 + bound - 1.5)
    assert_refused_inside_the_bound(inside, calls, (NUL_STDIN, "-"))
    with pytest.raises(AssertionError, match="before the bound"):
        assert_refused_inside_the_bound(past, calls, (NUL_STDIN, "-"))


def test_grader_refuses_an_empty_call_log() -> None:
    """A refusal with no logged call measured no shim at all."""
    with pytest.raises(AssertionError, match="measured nothing"):
        assert_refused_inside_the_bound(synthetic(1.0 + harness_bound()), (), (SLEEPER, "-c"))


def test_control_refuses_an_unmatched_start() -> None:
    """A probe half that timed out and PROCEEDED leaves a start with no done."""
    calls = call_log(
        (HONEST, "-c", 0.1, 0.2, 0),
        (HONEST, "-c", 0.3, 0.4, 97),
        (HONEST, "-", 0.5, None, None),
        (HONEST, "other", 0.8, 0.9, 0),
    )
    assert not calls[2].answered, "the plant did not apply"
    with pytest.raises(AssertionError, match="never answered"):
        assert_honest_wrapper_committed(synthetic(1.0, accepted=True), calls)


def test_control_refuses_a_call_ended_by_a_signal() -> None:
    """A done line carrying the bound's TERM status is not an answer."""
    calls = call_log(
        (HONEST, "-c", 0.1, 0.2, 0),
        (HONEST, "-c", 0.3, 0.4, 97),
        (HONEST, "-", 0.5, 0.6, KILLED_BY_SIGNAL + 15),
        (HONEST, "other", 0.8, 0.9, 0),
    )
    assert calls[2].done is not None, "the plant did not apply"
    with pytest.raises(AssertionError, match="never answered"):
        assert_honest_wrapper_committed(synthetic(1.0, accepted=True), calls)


def test_control_refuses_a_probe_half_at_the_bound() -> None:
    """A probe half that took the whole bound is a near-miss, and red."""
    bound = harness_bound()
    calls = call_log(
        (HONEST, "-c", 0.1, 0.1 + bound, 0),
        (HONEST, "-c", 0.2 + bound, 0.3 + bound, 97),
        (HONEST, "-", 0.4 + bound, 0.5 + bound, 0),
        (HONEST, "other", 0.6 + bound, 0.7 + bound, 0),
    )
    took = calls[0].duration
    assert took is not None, "the plant did not apply"
    assert took >= bound, "the plant did not apply"
    with pytest.raises(AssertionError, match="reached the bound"):
        assert_honest_wrapper_committed(synthetic(0.8 + bound, accepted=True), calls)


def test_control_refuses_a_log_that_skipped_the_probe() -> None:
    """The shim must have BEEN the interpreter: the probe's halves come first."""
    calls = call_log((HONEST, "other", 0.1, 0.2, 0))
    with pytest.raises(AssertionError, match="probe"):
        assert_honest_wrapper_committed(synthetic(0.3, accepted=True), calls)


def test_call_log_refuses_a_malformed_line() -> None:
    """A log the parser cannot read fails loudly, never as an empty log."""
    with pytest.raises(AssertionError, match="malformed"):
        parse_calls("start honest -c\n")
    with pytest.raises(AssertionError, match="closes no open call"):
        parse_calls("done honest -c 1.0 0\n")


def test_the_outer_ceiling_carries_the_seed_commits_measured_time() -> None:
    """A2: the kill ceiling grows by what an accepted commit measured on this box."""
    box = Sandbox(Path(), Path(), Path(), {}, PRE_COMMIT, seed_elapsed=7.5)
    assert harness_limit(box) == harness_bound() + HARNESS_SLACK + 7.5


# --- the bounding binary is checked by BEHAVIOUR, block level -----------------


def probe_block(raw: bytes) -> bytes:
    """The ``cs_probe`` definition plus every ``CS_PROBE_*`` line, as executable text."""
    lines = raw.split(b"\n")
    kept = [line for line in lines if line.startswith(b"CS_PROBE_")]
    inside = False
    for line in lines:
        if line.startswith(b"cs_probe() {"):
            inside = True
        if inside:
            kept.append(line)
            if line == b"}":
                inside = False
    return b"\n".join(kept)


FAKE_ABSENT: Final = "#!/bin/sh\nexit 127\n"
# The Windows pause command's answer to GNU syntax: an error and exit 1.
FAKE_FOREIGN: Final = "#!/bin/sh\necho 'ERROR: Invalid syntax.' >&2\nexit 1\n"
# Parses the options, then runs the command UNBOUNDED - passes an ordinary exit
# status through perfectly, and never expires.
FAKE_UNBOUNDING: Final = (
    "#!/bin/sh\n"
    'while [ "$#" -gt 0 ]; do\n'
    '    case "$1" in\n'
    "        -k) shift 2 ;;\n"
    "        -*) shift ;;\n"
    "        *) break ;;\n"
    "    esac\n"
    "done\n"
    "shift\n"
    'exec "$@"\n'
)
FAKES: Final = {"absent": FAKE_ABSENT, "foreign": FAKE_FOREIGN, "unbounding": FAKE_UNBOUNDING}

BLOCK_DIE: Final = b"die() { printf 'DIE: %s\\n' \"$1\"; exit 3; }\n"
BLOCK_TAIL: Final = b'\ncs_probe "$1"\nprintf \'RC=%s\\n\' "$?"\n'


class BlockRun(NamedTuple):
    """The outcome of the extracted probe run directly in a shell."""

    returncode: int
    died: bool
    binary_refusal: bool
    probe_rc: str


def run_block(tmp_path: Path, hook: str, path_value: str) -> BlockRun:
    """Run ``hook``'s own probe bytes against the real interpreter under ``path_value``."""
    assert SHELL is not None, "run_block needs a POSIX shell"
    script = tmp_path / f"block-{hook}.sh"
    script.write_bytes(BLOCK_DIE + probe_block((HOOKS_DIR / hook).read_bytes()) + BLOCK_TAIL)
    env = shell_env()
    env["PATH"] = path_value
    env.pop(ENV_NAME, None)
    env.pop(INSPECT_NAME, None)
    proc = subprocess.run(
        [SHELL, str(script), REAL_PYTHON_POSIX],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=env,
        check=False,
    )
    rc_lines = [line[3:] for line in proc.stdout.splitlines() if line.startswith("RC=")]
    return BlockRun(
        proc.returncode,
        "DIE: " in proc.stdout,
        BINARY_REFUSAL in proc.stdout,
        rc_lines[0] if rc_lines else "",
    )


def shell_bin_dir() -> str:
    """The directory holding the POSIX shell, so ``sleep`` and ``sh`` still resolve."""
    assert SHELL is not None, "shell_bin_dir needs a POSIX shell"
    return str(Path(SHELL).parent)


@pytest.mark.skipif(SHELL is None, reason=SHELL_SKIP)
@pytest.mark.parametrize("fake", sorted(FAKES))
@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_a_timeout_that_fails_the_behaviour_check_refuses(
    tmp_path: Path, hook: str, fake: str
) -> None:
    """Grant condition 3. RED before the repair: the probe never consulted timeout.

    Each fake is FIRST on PATH, so a check by NAME (``command -v timeout``) would
    pass every one of them. Only a check by BEHAVIOUR - an ordinary status passed
    through AND 124 on expiry - refuses all three.
    """
    fakes = tmp_path / "fakes"
    fakes.mkdir()
    (fakes / "timeout").write_bytes(FAKES[fake].encode("ascii"))
    (fakes / "timeout").chmod(0o755)
    path_value = str(fakes) + os.pathsep + shell_bin_dir() + os.pathsep + os.environ["PATH"]
    run = run_block(tmp_path, hook, path_value)
    assert run.died, f"{hook} ran its probe under a {fake} timeout instead of refusing"
    assert run.binary_refusal, f"{hook} refused under a {fake} timeout, but not by name"


WINDOWS_ONLY: Final = "NOT RUN, NOT PASSED: the foreign timeout.exe exists on Windows only"


@pytest.mark.skipif(SHELL is None, reason=SHELL_SKIP)
@pytest.mark.skipif(sys.platform != "win32", reason=WINDOWS_ONLY)
@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_the_windows_pause_command_named_timeout_refuses(tmp_path: Path, hook: str) -> None:
    """The measured hazard itself: System32's timeout.exe FIRST on PATH."""
    system_root = os.environ.get("SYSTEMROOT", "")
    system32 = Path(system_root) / "System32"
    present = (system32 / "timeout.exe").is_file()
    assert present, "System32 carries no timeout.exe, so this arm measured nothing"
    path_value = str(system32) + os.pathsep + shell_bin_dir()
    run = run_block(tmp_path, hook, path_value)
    assert run.binary_refusal, f"{hook} accepted the Windows pause command as its bound"


@pytest.mark.skipif(SHELL is None, reason=SHELL_SKIP)
@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_block_control_the_real_timeout_passes_a_real_interpreter(
    tmp_path: Path, hook: str
) -> None:
    """The control for the block-level arms: the same harness, the real binary."""
    path_value = shell_bin_dir() + os.pathsep + os.environ["PATH"]
    run = run_block(tmp_path, hook, path_value)
    assert not run.died, f"{hook} refused a real interpreter under the real timeout"
    assert run.probe_rc == "0", f"{hook}'s probe returned [{run.probe_rc}] for a real python"


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "NOT RUN, NOT PASSED: MEASURED 2026-09-25 that git for Windows prepends its own "
        "usr/bin to a hook's PATH, so a PATH-prefixed fake cannot shadow the real timeout "
        "inside a real commit. The block-level arms above cover the check on this platform."
    ),
)
def test_a_foreign_timeout_first_on_path_refuses_a_real_commit(
    tmp_path: Path, isolated: Environment
) -> None:
    """The binary check inside a real commit, where PATH order can be controlled."""
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    fakes = tmp_path / "fakes"
    fakes.mkdir()
    (fakes / "timeout").write_bytes(FAKE_FOREIGN.encode("ascii"))
    (fakes / "timeout").chmod(0o755)
    env = child_env(box)
    env["PATH"] = str(fakes) + os.pathsep + env["PATH"]
    outcome = commit_attempt(box, env)
    assert outcome.blocked, f"a foreign timeout did not refuse the commit:\n{outcome.report}"
    assert outcome.refusals(BINARY_REFUSAL) == 1, f"refused, but not by name:\n{outcome.report}"
