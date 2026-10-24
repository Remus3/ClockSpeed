"""CS-814 and CS-1200 - the probe refusal withholds output; a kill is a working bound.

The interpreter probe's refusal renders none of the candidate's output, and its
bounding self-check reads a kill after the grace as a working bound.

THE AUTHORITY is the frozen-file grant recorded in docs/LEDGER.md under
2026-09-25 for CS-814, with the CS-1200 grant beneath it. This module is the
permanent proof its conditions 2 and 3 require. The rule it grades is owned by
CLAUDE.md non-negotiable 13 and is not restated here.

CONDITION 2 - CS-814. Before the re-pin the ``CLOCKSPEED_PYTHON`` refusal carried
up to 200 characters of what the candidate printed. A candidate that ignores its
arguments and prints its environment therefore had the start of that
environment rendered by the hook. The arms below point ``CLOCKSPEED_PYTHON`` at
exactly such a program, plant synthetic credential-shaped canaries in the child
environment, and drive every carrier the way it really runs: a real ``git
commit`` through pre-commit and through commit-msg, a real ``git push`` to a
local bare remote through pre-push, and ``tools/claude_hook.sh`` on both of its
legs. Each run must still REFUSE, and no canary may appear in its output.

THE FIRST CANARY SORTS FIRST. The candidate prints its environment sorted by
name, and the canary names begin ``AAAA``, so the first marker lands inside the
old 200-character window. That is MEASURED by a control rather than assumed:
the candidate is run directly and the marker's offset in its flattened output
is compared with the old window. A second control installs a copy of pre-commit
whose refusal re-renders the raw output and shows the SAME harness finding the
canary - so a harness that never planted it, or never captured the hook's
streams, cannot read as clean.

CONDITION 3 - CS-1200. The bounding self-check runs ``timeout -k 1 0.05 sleep 5``.
A ``sleep`` that ignores TERM outlives the bound and is killed after the
one-second grace, so the check returns 137 rather than 124 - the shape a loaded
box produced in 2 of 12 runs. The arms put such a ``sleep`` first on PATH,
MEASURE that the check really returns 137 under it, and show every carrier's
probe proceeding. The controls put a ``timeout`` that is no bound at all first
on PATH and show every carrier still refusing.

CS-1326 - THE STUBBORN CHILD IS TERM-IMMUNE FROM ITS FIRST INSTRUCTION. A
``sleep`` that ignores TERM only once its trap has run loses the race with the
0.05 s bound whenever it starts slowly, and the check then returns 124 - a
loaded runner did exactly that. So beside it on PATH goes a ``timeout`` that
runs the real one with TERM BLOCKED. The child inherits that mask across its
exec, so the bound's TERM stays pending from the child's first instruction and
only the kill ends it. THE BLOCK IS WHAT CARRIES THE 137: with the trap line
deleted every arm still passes (an adversary's mutant, session 141). The trap
stays as a second barrier - it discards the pending TERM and keeps the child
literally ignoring it, the shape CS-1200 names - but it is not the mechanism.
That ``timeout`` records every self-check's status, and each arm reads the
record to show the carrier's own check ended by the kill, because a carrier
proceeds on 124 as well and an arm that read only that could pass on the
wrong path.

NOTHING ASSERTED HERE RENDERS AN ENVIRONMENT VALUE OR A PATH. Every run is
reduced to an exit status, counts and bools before an assertion sees it (the
CS-1199 rule in ``tests/test_assertion_rendering.py``). The canary values are
markers made fresh from ``secrets`` at import time; no real credential is read,
compared or printed.
"""

from __future__ import annotations

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

from tests.fleet_hook_kit import (
    OPERATOR_IDENT_KEY,
    commit_margin_env,
    install_hook_kit,
    suite_dir_env,
)
from tests.git_env import scrub
from tests.test_pretooluse_gate import envelope, require_posix_shell

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOKS_DIR: Final = REPO_ROOT / ".githooks"
WRAPPER: Final = REPO_ROOT / "tools" / "claude_hook.sh"
GATE: Final = REPO_ROOT / "tools" / "precommit_gate.py"
PRETOOL: Final = REPO_ROOT / "tools" / "pretooluse_gate.py"
LINT: Final = REPO_ROOT / "tools" / "edit_lint_check.py"

PRE_COMMIT: Final = "pre-commit"
COMMIT_MSG: Final = "commit-msg"
PRE_PUSH: Final = "pre-push"
GIT_HOOKS: Final = (PRE_COMMIT, COMMIT_MSG, PRE_PUSH)
COMMIT_HOOKS: Final = (PRE_COMMIT, COMMIT_MSG)
WRAPPER_NAME: Final = "claude_hook.sh"
CARRIERS: Final = (*GIT_HOOKS, WRAPPER_NAME)

PRE: Final = "pretooluse"
POST: Final = "posttooluse"
LEGS: Final = (PRE, POST)
DENY: Final = 2

CALL_TIMEOUT: Final = 300
BRANCH: Final = "cs814-refusal"
FIXTURE_NAME: Final = "CS-814 Fixture"
FIXTURE_EMAIL: Final = "cs814@example.invalid"
SUBJECT: Final = "CS-814 - an ordinary subject that says what changed"
CLEAN_FILE: Final = b"an ordinary line of 7-bit ascii\n"
CLEAN_MODULE: Final = b'"""A clean module."""\n'
PASSING_SUITE: Final = b"def test_passes() -> None:\n    assert True\n"

ENV_NAME: Final = "CLOCKSPEED_PYTHON"
PINNED_HERE: Final = frozenset({ENV_NAME, "PYTHONPATH", "PYTHONINSPECT"})

#: Names shaped like credential kinds a developer environment carries. The
#: ``AAAA`` prefix sorts the first one ahead of every ordinary variable, so its
#: marker falls inside the old preview window; the control measures that.
CANARY_NAMES: Final = (
    "AAAA_CS814_FORGE_TOKEN",
    "AAAB_CS814_VENDOR_API_KEY",
    "CS814_MESSAGING_TOKEN",
)

#: One marker per canary, fresh each run, never present in this file's source.
MARKERS: Final = tuple(f"cs814canary{secrets.token_hex(12)}" for _ in CANARY_NAMES)

#: The window the removed preview rendered, in characters.
OLD_WINDOW: Final = 200

REAL_PYTHON_POSIX: Final = Path(sys.executable).as_posix()

#: Ignores its arguments and prints its whole environment, sorted by name.
ENV_PRINTER_PROGRAM: Final = (
    "import os, sys; "
    'sys.stdout.write("".join(k + "=" + os.environ[k] + "\\n" for k in sorted(os.environ)))'
)
ENV_PRINTER: Final = (
    "#!/bin/sh\n"
    "# CS-814 fixture: ignores its arguments and prints its environment.\n"
    'exec "' + REAL_PYTHON_POSIX + "\" -c '" + ENV_PRINTER_PROGRAM + "'\n"
)

#: The headline each git hook's pinned-interpreter refusal opens with.
PINNED_HEADLINE: Final = "CLOCKSPEED_PYTHON is set but did not answer the probe."
#: The wrapper's one-line report for the same refusal.
WRAPPER_REFUSED: Final = b"REFUSED (CS-815)"
#: The byte count the re-pinned refusal reports in place of the output.
COUNTED: Final = re.compile(rb"Observed probe output: \[([0-9]+)\] bytes")

#: The one line the anti-vacuity mutant adds to the refusal: the raw output.
DUMP_ARGUMENT: Final = b'            "[$cs_probe_out]" \\'
REFUSAL_OPENING: Final = b'        die "' + PINNED_HEADLINE.encode("ascii") + b'" \\'


class Outcome(NamedTuple):
    """One driven run, reduced to scalars before anything is asserted."""

    returncode: int
    hits: int
    reached: bool
    counted: int


def marker_hits(output: bytes) -> int:
    """Total marker occurrences in ``output``, as a count only."""
    return sum(output.count(marker.encode("ascii")) for marker in MARKERS)


def counted_bytes(output: bytes) -> int:
    """The byte count the refusal reports, or -1 when it reports none."""
    found = COUNTED.search(output)
    return int(found.group(1)) if found else -1


def outcome(returncode: int, output: bytes, reached: bool) -> Outcome:
    """Reduce one run to scalars."""
    return Outcome(returncode, marker_hits(output), reached, counted_bytes(output))


def child_env(root: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """The inherited environment, cut loose from git config, plus every canary."""
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(root / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(root / "absent" / "gitconfig-system")
    for name in [
        key for key in env if key.upper() in PINNED_HERE or key.upper().startswith("PYTEST_")
    ]:
        env.pop(name)
    env.update(zip(CANARY_NAMES, MARKERS, strict=True))
    env.update(suite_dir_env(root))
    # CS-1349: the gate's commit margin is 0 for a sandbox push (grant clause C).
    env.update(commit_margin_env())
    # CS-1297: the nested pytest names its base temp `pytest-of-<account>`, and
    # the account here may be a canary marker - aim TMPDIR (read first by
    # tempfile and by the hook's mktemp) under this arm's own root, outside the
    # work tree, so no marker-named root is ever left at the top of temp.
    scratch = root / "tmpdir"
    scratch.mkdir(parents=True, exist_ok=True)
    env["TMPDIR"] = str(scratch)
    env.update(extra or {})
    return env


def write_executable(path: Path, raw: bytes) -> Path:
    """Materialise one executable file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o755)
    return path


def env_printer(root: Path) -> str:
    """The argument-ignoring, environment-printing candidate, as a POSIX path."""
    shim = write_executable(root / "shims" / "env-printer.sh", ENV_PRINTER.encode("ascii"))
    return shim.as_posix()


def tracked(name: str) -> bytes:
    """The tracked bytes of one carrier."""
    return (WRAPPER if name == WRAPPER_NAME else HOOKS_DIR / name).read_bytes()


# --- real git ---------------------------------------------------------------------


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


def make_repo(root: Path, hooks: dict[str, bytes], *, remote: bool = False) -> Path:
    """A throwaway repository wired to hook copies, seeded through ``--no-verify``."""
    hooks_dir = root / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
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
    (work / "tools").mkdir()
    shutil.copy2(GATE, work / "tools" / "precommit_gate.py")
    (work / "tests").mkdir()
    (work / "tests" / "test_sandbox.py").write_bytes(PASSING_SUITE)
    (work / "pytest.ini").write_bytes(b"[pytest]\n")
    assert git_ok(work, root, "add", "--", "tests", "pytest.ini"), "the seed did not stage"
    seeded = git_ok(work, root, "commit", "-q", "--no-verify", "-m", "CS-814 seed")
    assert seeded, "the seed commit failed"
    if remote:
        bare = root / "remote.git"
        assert git_ok(work, root, "init", "-q", "--bare", str(bare)), "no bare remote"
        assert git_ok(work, root, "remote", "add", "origin", str(bare)), "no origin"
        pushed = git_ok(work, root, "push", "-q", "--no-verify", "origin", BRANCH)
        assert pushed, "the seed did not reach the remote"
    return work


def commit_through(
    root: Path, hooks: dict[str, bytes], extra: dict[str, str]
) -> tuple[int, bytes, bool]:
    """Stage one clean file and commit it through the hooks: status, output, HEAD moved."""
    work = make_repo(root, hooks)
    before = rev(work, root, "rev-parse", "HEAD")
    (work / "staged.txt").write_bytes(CLEAN_FILE)
    assert git_ok(work, root, "add", "--", "staged.txt"), "the file did not stage"
    proc = run_git(work, child_env(root, extra), "commit", "-q", "-m", SUBJECT)
    moved = rev(work, root, "rev-parse", "HEAD") != before
    return proc.returncode, proc.stdout + proc.stderr, moved


def push_through(root: Path, hook: bytes, extra: dict[str, str]) -> tuple[int, bytes, bool]:
    """Offer one new commit through pre-push: status, output, whether it landed."""
    work = make_repo(root, {PRE_PUSH: hook}, remote=True)
    made = git_ok(work, root, "commit", "-q", "--no-verify", "--allow-empty", "-m", "CS-814 offer")
    assert made, "the offered commit failed"
    proc = run_git(work, child_env(root, extra), "push", "-q", "origin", BRANCH)
    local = rev(work, root, "rev-parse", "refs/heads/" + BRANCH)
    listed = rev(work, root, "ls-remote", "origin", "refs/heads/" + BRANCH)
    landed = bool(local) and bool(listed) and listed.split()[0] == local
    return proc.returncode, proc.stdout + proc.stderr, landed


def refused_by_the_pin(hook: str, returncode: int, output: bytes, landed: bool) -> bool:
    """The run refused, nothing landed, and the pinned-interpreter refusal said so."""
    said = ("clockspeed " + hook + ": " + PINNED_HEADLINE).encode("ascii") in output
    return returncode != 0 and not landed and said


def drive_git_hook(hook: str, root: Path, raw: bytes) -> Outcome:
    """Drive one git hook, given as bytes, under the environment-printing candidate."""
    extra = {ENV_NAME: env_printer(root)}
    if hook == PRE_PUSH:
        code, out, landed = push_through(root, raw, extra)
    else:
        code, out, landed = commit_through(root, {hook: raw}, extra)
    return outcome(code, out, refused_by_the_pin(hook, code, out, landed))


# --- the wrapper, driven the way the harness drives it -----------------------------


def shell_first(env: dict[str, str], *first: Path) -> dict[str, str]:
    """``env`` with ``first`` and then the POSIX shell's own directory leading PATH."""
    shell = require_posix_shell()
    leading = [str(path) for path in first] + [str(Path(shell).parent)]
    env["PATH"] = os.pathsep.join([*leading, env.get("PATH", "")])
    return env


def run_wrapper(
    leg: str, root: Path, extra: dict[str, str] | None = None, *first: Path
) -> tuple[int, bytes]:
    """One wrapper call on ``leg`` with a benign tool call behind it.

    The environment is built inside the call expression, so no frame on a
    failure's traceback holds it as a local.
    """
    shell = require_posix_shell()
    if leg == PRE:
        tool = [str(PRETOOL)]
        stdin = json.dumps(envelope("git status")).encode("utf-8")
    else:
        edited = root / "cs814_edited.py"
        edited.write_bytes(CLEAN_MODULE)
        tool = [str(LINT), "--files", str(edited)]
        stdin = b"{}"
    proc = subprocess.run(
        [shell, str(WRAPPER), leg, *tool],
        input=stdin,
        capture_output=True,
        env=shell_first(child_env(root, extra), *first),
        cwd=str(root),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


# --- condition 2: the refusal renders none of the candidate's output ---------------


def test_the_candidate_prints_a_canary_inside_the_old_window(tmp_path: Path) -> None:
    """ANTI-VACUITY. The candidate, run directly, prints every canary.

    The first one lands inside the 200 characters the removed preview rendered.
    """
    proc = subprocess.run(
        [require_posix_shell(), env_printer(tmp_path), "-c", "ignored"],
        capture_output=True,
        env=child_env(tmp_path),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    flat = proc.stdout.replace(b"\r", b" ").replace(b"\n", b" ")
    printed = marker_hits(flat)
    offset = flat.find(MARKERS[0].encode("ascii"))
    inside = offset >= 0 and offset + len(MARKERS[0]) <= OLD_WINDOW
    assert proc.returncode == 0, "the environment-printing candidate did not run"
    assert printed == len(MARKERS), f"the candidate printed {printed} of {len(MARKERS)} canaries"
    assert inside, "the first canary does not fall inside the old preview window"


@pytest.mark.parametrize("hook", GIT_HOOKS)
def test_a_git_hook_refusal_renders_no_canary(tmp_path: Path, hook: str) -> None:
    """Condition 2 through real git: refused, zero canaries, the byte count reported."""
    result = drive_git_hook(hook, tmp_path, tracked(hook))
    assert result.reached, f"{hook}: the run did not refuse through the pinned-variable check"
    assert result.hits == 0, f"{hook}: {result.hits} canary occurrence(s) in the hook output"
    assert result.counted > 0, f"{hook}: the refusal reports no byte count ({result.counted})"


def test_the_harness_sees_a_canary_the_refusal_re_renders(tmp_path: Path) -> None:
    """ANTI-VACUITY. The same harness finds the canary where a refusal renders it.

    The subject is a pre-commit copy whose refusal re-renders the raw output by
    one inserted line.
    """
    lines = tracked(PRE_COMMIT).split(b"\n")
    at = lines.index(REFUSAL_OPENING) + 1
    mutant = b"\n".join([*lines[:at], DUMP_ARGUMENT, *lines[at:]])
    one_line = len(mutant.split(b"\n")) == len(lines) + 1
    result = drive_git_hook(PRE_COMMIT, tmp_path, mutant)
    assert one_line, "the mutant is not the tracked hook plus one line"
    assert result.reached, "the mutant did not refuse through the pinned-variable check"
    assert result.hits > 0, "the harness found no canary even where the refusal renders it"


@pytest.mark.parametrize("leg", LEGS)
def test_a_wrapper_refusal_renders_no_canary(tmp_path: Path, leg: str) -> None:
    """Condition 2 through ``tools/claude_hook.sh``: refused, never a deny, zero canaries."""
    code, out = run_wrapper(leg, tmp_path, {ENV_NAME: env_printer(tmp_path)})
    refused = code not in (0, DENY) and WRAPPER_REFUSED in out
    result = outcome(code, out, refused)
    assert result.reached, f"{leg}: the wrapper did not refuse (exit {result.returncode})"
    assert result.hits == 0, f"{leg}: {result.hits} canary occurrence(s) in the wrapper output"


# --- condition 3: a kill after the grace is a working bound -------------------------

#: A ``sleep`` that outlives TERM, so a bound is enforced only by the KILL.
#: CS-1326: what makes it outlive TERM is the mask it inherits across its exec
#: from the ``timeout`` below - TERM blocked from its first instruction. Its
#: ``trap '' TERM`` is a SECOND barrier: it discards the pending TERM and makes
#: the child ignore it as CS-1200 describes, but with the trap deleted the
#: block alone still yields 137. Its shebang is the resolved bash: bash keeps
#: an inherited blocked TERM blocked through its start and its waits, while
#: dash unblocks it while waiting on a child, so a dash stand-in for a slow
#: start died of TERM even behind the ``timeout`` below (measured, WSL Ubuntu
#: 26.04).
STUBBORN_SLEEP_HEAD: Final = (
    "# CS-1200 and CS-1326 fixture: a sleep started with TERM blocked by its\n"
    "# timeout; the trap below is a second barrier that also ignores TERM.\n"
)
STUBBORN_TRAP: Final = "trap '' TERM\n"
#: CS-1326: how long the slow-start arm's stubborn ``sleep`` runs the real one
#: BEFORE its trap - six times the 0.05 s bound, well inside the 1 s grace.
SLOW_START: Final = "0.3"

#: CS-1326: beside the stubborn ``sleep``, a ``timeout`` that runs the real one
#: with TERM BLOCKED. The real timeout starts its child with the mask it
#: inherited - measured for GNU coreutils and for uutils - so that child is born
#: with TERM blocked, the bound's TERM stays pending, and only the kill can end
#: it, however slowly the child starts. The real timeout does all the bounding.
TERM_BLOCKING_TIMEOUT: Final = (
    "#!/bin/sh\n"
    "# CS-1326 fixture: the real timeout, its child born with TERM blocked.\n"
    '"{env}" --block-signal=TERM "{timeout}" "$@"\n'
    "cs_rc=$?\n"
    'case "$*" in\n'
    '"{args}") printf \'%s\\n\' "$cs_rc" >>"{record}" ;;\n'
    "esac\n"
    'exit "$cs_rc"\n'
)
#: Where that ``timeout`` records each carried self-check's status, one a line.
SELF_CHECK_RECORD: Final = "self-check-status.txt"
#: What the shell resolves for the fixtures, in this order.
RESOLVED_TOOLS: Final = ("bash", "env", "timeout")

#: No bound at all: runs nothing and exits 1, the shape of a foreign ``timeout``.
FOREIGN_TIMEOUT: Final = "#!/bin/sh\nexit 1\n"
#: Answers 137 to everything, so 137 alone is shown not to pass the check.
ALWAYS_KILLED_TIMEOUT: Final = "#!/bin/sh\nexit 137\n"
BROKEN_TIMEOUTS: Final = {"foreign": FOREIGN_TIMEOUT, "always-137": ALWAYS_KILLED_TIMEOUT}

SELF_CHECK: Final = 'timeout -k 1 0.05 sleep 5 </dev/null >/dev/null 2>&1; printf "%s" "$?"'
#: The self-check's arguments as the ``timeout`` in front of it receives them.
SELF_CHECK_ARGS: Final = SELF_CHECK.split(" <", 1)[0].removeprefix("timeout ")
KILLED: Final = "137"

BLOCK_DIE: Final = b"die() { printf 'DIE: %s\\n' \"$1\"; exit 3; }\n"
BLOCK_TAIL: Final = b'\ncs_probe "$1"\nprintf \'RC=%s\\n\' "$?"\n'
BOUND_REFUSAL: Final = "no working GNU timeout"


class BlockRun(NamedTuple):
    """The extracted probe, run directly in a shell, reduced to scalars."""

    died: bool
    bound_refusal: bool
    probe_rc: str


def probe_block(raw: bytes) -> bytes:
    """The ``CS_PROBE_*`` constants and the ``cs_probe`` function from a carrier."""
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


def resolved_in_shell(root: Path) -> dict[str, str]:
    """Each of :data:`RESOLVED_TOOLS` as the POSIX shell resolves it on the arms' PATH.

    The shell's own spelling, so a shebang or a script line can use it as is.
    Nothing resolved here is ever rendered.
    """
    resolve = 'for n do command -v "$n" || exit 1; done'
    proc = subprocess.run(
        [require_posix_shell(), "-c", resolve, "resolve", *RESOLVED_TOOLS],
        capture_output=True,
        env=block_env(root),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    found = proc.stdout.decode("utf-8", "replace").splitlines()
    whole = proc.returncode == 0 and len(found) == len(RESOLVED_TOOLS)
    assert whole, f"the shell resolved {len(found)} of {len(RESOLVED_TOOLS)} fixture tools"
    absolute = all(path.startswith("/") for path in found)
    assert absolute, "a fixture tool resolved to something other than a file path"
    return dict(zip(RESOLVED_TOOLS, found, strict=True))


def stubborn_bin(root: Path, pre_trap_wait: str | None = None) -> Path:
    """A directory whose ``sleep`` outlives TERM and then runs the real one.

    CS-1326: its ``timeout`` runs the real one with TERM blocked, so that
    ``sleep`` inherits the block across its exec and is TERM-immune from its
    first instruction; its trap is a second barrier, not the mechanism. The
    ``timeout`` records every carried self-check's status at
    :data:`SELF_CHECK_RECORD` under ``root``. ``pre_trap_wait`` makes the
    ``sleep`` run the real one for that long BEFORE its trap - a child that
    starts slowly, the shape a loaded box gives it.
    """
    shell = require_posix_shell()
    real = shutil.which("sleep", path=str(Path(shell).parent)) or shutil.which("sleep")
    assert real, "no real sleep resolved beside the shell or on PATH"
    tools = resolved_in_shell(root)
    one_word = len(tools["bash"].split()) == 1
    assert one_word, "the resolved bash holds whitespace, so no shebang line can carry it"
    sleep = '"' + Path(real).as_posix() + '"'
    delay = "" if pre_trap_wait is None else sleep + " " + pre_trap_wait + "\n"
    shebang = "#!" + tools["bash"] + "\n"
    body = shebang + STUBBORN_SLEEP_HEAD + delay + STUBBORN_TRAP + "exec " + sleep + ' "$@"\n'
    write_executable(root / "stubborn" / "sleep", body.encode("utf-8"))
    shim = TERM_BLOCKING_TIMEOUT.format(
        env=tools["env"],
        timeout=tools["timeout"],
        args=SELF_CHECK_ARGS,
        record=(root / SELF_CHECK_RECORD).as_posix(),
    )
    write_executable(root / "stubborn" / "timeout", shim.encode("utf-8"))
    # The precondition, asserted and never skipped: env takes --block-signal
    # and the timeout behind it answers --version, so BusyBox and coreutils
    # before 8.31 refuse here. Any implementation is accepted - GNU and uutils
    # both measured to keep the block in the child - because the slow-start arm
    # below is the behavioural guard that the block reaches the child.
    proc = subprocess.run(
        [shell, str(root / "stubborn" / "timeout"), "--version"],
        capture_output=True,
        env=block_env(root),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    code = proc.returncode
    assert code == 0, f"the TERM-blocking timeout is unusable: --version exited {code}"
    return root / "stubborn"


def self_check_record(root: Path) -> list[str]:
    """Every status the carried self-check returned through :func:`stubborn_bin`'s ``timeout``."""
    record = root / SELF_CHECK_RECORD
    return record.read_text(encoding="ascii").split() if record.is_file() else []


def ended_by_the_kill(statuses: list[str]) -> bool:
    """At least one self-check ran, and every one of them ended by the kill."""
    return bool(statuses) and all(status == KILLED for status in statuses)


def broken_bin(root: Path, kind: str) -> Path:
    """A directory whose ``timeout`` is no bound at all."""
    write_executable(root / kind / "timeout", BROKEN_TIMEOUTS[kind].encode("ascii"))
    return root / kind


def block_env(root: Path, *first: Path) -> dict[str, str]:
    """A direct-shell environment with ``first`` leading PATH, the probe variables cut."""
    return shell_first(child_env(root), *first)


def self_check_status(root: Path, *first: Path) -> str:
    """The bounding self-check's exit status under ``first`` on PATH, measured."""
    proc = subprocess.run(
        [require_posix_shell(), "-c", SELF_CHECK],
        capture_output=True,
        env=block_env(root, *first),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    return proc.stdout.decode("ascii", "replace").strip()


def run_block(root: Path, carrier: str, *first: Path) -> BlockRun:
    """Run one carrier's own probe bytes against the real interpreter."""
    script = root / f"block-{carrier}.sh"
    script.write_bytes(BLOCK_DIE + probe_block(tracked(carrier)) + BLOCK_TAIL)
    proc = subprocess.run(
        [require_posix_shell(), str(script), REAL_PYTHON_POSIX],
        capture_output=True,
        text=True,
        env=block_env(root, *first),
        timeout=CALL_TIMEOUT,
        check=False,
    )
    rc_lines = [line[3:] for line in proc.stdout.splitlines() if line.startswith("RC=")]
    return BlockRun(
        "DIE: " in proc.stdout,
        BOUND_REFUSAL in proc.stdout,
        rc_lines[0] if rc_lines else "",
    )


def test_the_stubborn_sleep_makes_the_self_check_return_137(tmp_path: Path) -> None:
    """ANTI-VACUITY. The stubborn fixture really makes the check end by the kill.

    With the real sleep the same check ends by the bound - 124, or 137 when a
    loaded box delays the child past the grace (CS-1200 measured 2 of 12) - and
    never by the child finishing. The stubborn half alone carries the proof.
    CS-1326: what makes that half end by the kill is the TERM mask its child
    inherits across exec from the fixture's ``timeout``, not the child's trap -
    with the trap alone it read 124 on a loaded runner, whose child had not
    reached the trap by the bound, and with the trap deleted it still reads 137.
    """
    stubborn = self_check_status(tmp_path, stubborn_bin(tmp_path))
    plain = self_check_status(tmp_path)
    assert stubborn == KILLED, f"the stubborn sleep did not end by the kill: [{stubborn}]"
    assert plain in {"124", KILLED}, f"the real sleep did not end by the bound: [{plain}]"


def test_a_slow_starting_stubborn_sleep_still_ends_by_the_kill(tmp_path: Path) -> None:
    """CS-1326. The kill must not depend on how fast the stubborn child starts.

    Its trap runs only after the 0.05 s bound has expired - the shape of the
    loaded runner on which tier2 38537859291 read 124 for the arm above - so
    only the inherited block can carry it to the kill: without the block it
    reads 124. This is the behavioural guard that the block reaches the child,
    whichever coreutils supplies ``env`` and ``timeout``. The record the arms
    below read is shown here to hold exactly what the shell saw.
    """
    status = self_check_status(tmp_path, stubborn_bin(tmp_path, SLOW_START))
    recorded = self_check_record(tmp_path)
    assert status == KILLED, f"a slow-starting stubborn sleep did not end by the kill: [{status}]"
    assert recorded == [status], f"the self-check record {recorded} is not the status the shell saw"


@pytest.mark.parametrize("carrier", CARRIERS)
def test_a_kill_after_the_grace_is_a_working_bound(tmp_path: Path, carrier: str) -> None:
    """Condition 3: with the self-check ending by the kill, the probe proceeds.

    CS-1326: the record shows the carrier's own check ended by the kill - a 124
    proceeds too, so without it this arm could pass on the path it is not about.
    """
    run = run_block(tmp_path, carrier, stubborn_bin(tmp_path))
    statuses = self_check_record(tmp_path)
    assert not run.died, f"{carrier} refused (bound refusal: {run.bound_refusal})"
    assert run.probe_rc == "0", f"{carrier}'s probe returned [{run.probe_rc}] for a real python"
    assert ended_by_the_kill(statuses), f"{carrier}'s self-check statuses: {statuses}"


@pytest.mark.parametrize("kind", sorted(BROKEN_TIMEOUTS))
@pytest.mark.parametrize("carrier", CARRIERS)
def test_no_working_timeout_still_refuses(tmp_path: Path, carrier: str, kind: str) -> None:
    """Condition 3's control: a ``timeout`` that is no bound still refuses by behaviour."""
    run = run_block(tmp_path, carrier, broken_bin(tmp_path, kind))
    assert run.died, f"{carrier} ran its probe under a {kind} timeout"
    assert run.bound_refusal, f"{carrier} refused under a {kind} timeout, but not for the bound"


@pytest.mark.parametrize("leg", LEGS)
def test_the_wrapper_proceeds_when_the_self_check_ends_by_the_kill(
    tmp_path: Path, leg: str
) -> None:
    """Condition 3 through the whole wrapper: the tool runs and its verdict passes through.

    CS-1326: and every self-check the wrapper ran ended by the kill, read from
    the record rather than inferred from the wrapper proceeding.
    """
    code, out = run_wrapper(leg, tmp_path, None, stubborn_bin(tmp_path))
    refused = WRAPPER_REFUSED in out
    statuses = self_check_record(tmp_path)
    assert code == 0, f"{leg}: the wrapper exited {code} (refused: {refused})"
    assert not refused, f"{leg}: the wrapper refused"
    assert ended_by_the_kill(statuses), f"{leg}: the wrapper's self-check statuses: {statuses}"


@pytest.mark.parametrize("leg", LEGS)
def test_the_wrapper_still_refuses_with_no_working_timeout(tmp_path: Path, leg: str) -> None:
    """Condition 3's control through the whole wrapper.

    The wrapper bounds its own resolve child with the same ``timeout``, so a
    foreign one stops the call before the carried self-check is reached; the
    report line then names the missing verdict rather than the bound. What this
    control pins is that the call is REFUSED, loudly and never as a deny - the
    block arms above pin that the carried check itself refuses for the bound.
    """
    code, out = run_wrapper(leg, tmp_path, None, broken_bin(tmp_path, "foreign"))
    refused = WRAPPER_REFUSED in out
    assert code not in (0, DENY), f"{leg}: the wrapper exited {code}"
    assert refused, f"{leg}: the wrapper did not report a refusal"


def stubborn_first(root: Path, stubborn: Path) -> dict[str, str]:
    """The canary environment with the stubborn ``sleep`` leading PATH."""
    env = child_env(root)
    env["PATH"] = str(stubborn) + os.pathsep + env.get("PATH", "")
    return env


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "NOT RUN, NOT PASSED: git for Windows prepends its own usr/bin to a hook's PATH "
        "(measured for tests/test_hook_probe_bound.py), so a PATH-prefixed sleep cannot "
        "reach a real commit here. The block and wrapper arms above cover the check."
    ),
)
def test_a_real_commit_proceeds_when_the_self_check_ends_by_the_kill(tmp_path: Path) -> None:
    """Condition 3 through real git, where PATH order can be controlled.

    CS-1326: the record shows the hook's own self-check ended by the kill.
    """
    stubborn = stubborn_bin(tmp_path)
    work = make_repo(tmp_path, {PRE_COMMIT: tracked(PRE_COMMIT)})
    before = rev(work, tmp_path, "rev-parse", "HEAD")
    (work / "staged.txt").write_bytes(CLEAN_FILE)
    assert git_ok(work, tmp_path, "add", "--", "staged.txt"), "the file did not stage"
    proc = run_git(work, stubborn_first(tmp_path, stubborn), "commit", "-q", "-m", SUBJECT)
    moved = rev(work, tmp_path, "rev-parse", "HEAD") != before
    statuses = self_check_record(tmp_path)
    assert proc.returncode == 0, f"the commit exited {proc.returncode}"
    assert moved, "the commit did not land"
    assert ended_by_the_kill(statuses), f"the hook's self-check statuses: {statuses}"
