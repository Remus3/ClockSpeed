#!/usr/bin/env python3
"""CS-703 - the interpreter ladder, proven ENFORCED by real git.

WHY EVERY ARM DRIVES REAL GIT INSTEAD OF CALLING A SHELL FUNCTION, which is the
whole reason this module is shaped the way it is. The defect it exists to pin is
that a hook can be correctly wired, syntactically valid, and still do nothing,
because it resolved an interpreter that never ran the check it invoked. A unit
test of ``cs_probe`` is BYTE-IDENTICAL GREEN whether the gate fires or not, so it
could prove only that this file and the hook agree about a shell function - never
that a commit is actually stopped. CLAUDE.md section 2.2 says a hook's presence is
never proof it fires and the only valid test is end to end. Every arm below
therefore drives a real ``git commit`` or a real ``git push`` in a throwaway
repository, and asserts on the process exit code AND on whether HEAD moved - or,
for pre-push, on whether the ref reached the bare remote.

THE DEFECT, AS MEASURED BEFORE THE REPAIR. All three hooks carried a
byte-identical ``cs_probe`` that ran the candidate with ``-c`` and judged ONLY the
exit code, so ``true``, ``:`` and ``echo`` all passed it. The heredoc or the gate
invocation was then handed to that program, which ignored it and exited 0, and the
hook reported success. With ``CLOCKSPEED_PYTHON=true``: the staged em dash
COMMITTED, the co-authorship trailer COMMITTED and git read it back as a real
trailer, and the push LANDED with the suite never run. One environment variable
disarmed every tier-0 gate at once, silently.

ONE WIRED HOOK PER SANDBOX, deliberately. Pointing ``core.hooksPath`` at the
repository's own ``.githooks`` would arm all three, and pre-commit runs first and
has its own reasons to reject - a refusal could then not be attributed to the hook
under test, and an arm expecting a block would pass for the wrong reason. Each copy
is asserted byte-identical to the tracked hook, so the isolation costs no fidelity.

THE HARNESS CONTROLS ARE NOT OPTIONAL AND THEY ARE HALF THIS MODULE. An arm that
only ever expects a BLOCK is satisfied by a sandbox where the hook never ran at
all, or where nothing was ever staged. So for each hook there are three companion
arms: the same defective input with the variable UNSET must still block, a CLEAN
input with the variable unset must be ACCEPTED, and a clean input under a REAL
interpreter named explicitly must be ACCEPTED. The accept arms are what prove the
sandbox can say yes, and the unset-blocks arm is what proves it can say no for the
input's own sake rather than because it is inert.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. ``tmp_path`` sits under the real user
profile and its own directory name embeds the account name, and this module also
puts an absolute interpreter path into a child environment. A rendered
``CompletedProcess`` reprs its own argument list, so every result is reduced to a
bool, an int or the hook's own filtered output before it is asserted on; the
sandbox withholds its paths from its repr; and the output filter drops any line
carrying a drive-letter path (CLAUDE.md non-negotiables 3 and 12).
"""

import ast
import fnmatch
import itertools
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final, NamedTuple

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOKS_DIR: Final = REPO_ROOT / ".githooks"
TRACKED_GATE: Final = REPO_ROOT / "tools" / "precommit_gate.py"

PRE_COMMIT: Final = "pre-commit"
COMMIT_MSG: Final = "commit-msg"
PRE_PUSH: Final = "pre-push"
HOOK_NAMES: Final = (PRE_COMMIT, COMMIT_MSG, PRE_PUSH)

GIT_TIMEOUT: Final = 180
ENV_NAME: Final = "CLOCKSPEED_PYTHON"

# The running interpreter, by its own path. Used to prove PART 2 did not turn
# CLOCKSPEED_PYTHON into a permanent block. It is an absolute path under a user
# profile, so it goes into a child environment and NOWHERE else.
REAL_PYTHON: Final = sys.executable

# The programs the old probe accepted. `true` is the argument-ignoring program
# the CS-703 acceptance names; `:` is the shell's own no-op; `echo` prints its
# arguments and was NOT named in the original filing. `env` is deliberately
# absent - it does not pass on this toolchain, because GNU env rejects -c and
# exits 125, and the ledger records that correction.
ARGUMENT_IGNORING_PROGRAMS: Final = ("true", ":", "echo")

# CLOCKSPEED_PYTHON must name ONE EXECUTABLE. This is the shape that trips real
# operators, because BOOTSTRAP.md section 2.5 writes the ladder as prose that
# reads like a command line.
COMMAND_LINE_NOT_EXECUTABLE: Final = "py -3"

SANDBOX_BRANCH: Final = "cs703-sandbox"
FIXTURE_NAME: Final = "CS-703 Fixture"
FIXTURE_EMAIL: Final = "cs703@example.invalid"
PAYLOAD_STEM: Final = "payload"
MESSAGE_NAME: Final = "commit-message.txt"
SHIM_NAME: Final = "chatty-candidate.sh"
NO_HEAD: Final = "(no commit yet)"

LEGITIMATE: Final = "CS-703: an ordinary subject that says what changed\n"
CLEAN_CONTENT: Final = b"an ordinary line of 7-bit ascii\n"

# U+2014, built at run time and never typed. This file is authored content and
# non-negotiable 4 admits no exception for a fixture: a literal em dash here
# would be caught by the repository's own character-set gate, so the arm proving
# the gate works would be the thing that trips it.
EM_DASH: Final = chr(0x2014)
EM_DASH_CONTENT: Final = ("a line carrying an em " + EM_DASH + " dash\n").encode("utf-8")

TRAILER_MESSAGE: Final = (
    "CS-703: a message carrying the trailer\n"
    "\n"
    "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n"
)

# The PART 2 refusal's own words, so an arm can pin WHICH rule refused rather
# than merely that something did.
PROBE_REFUSAL: Final = "did not answer the probe"
ONE_EXECUTABLE: Final = "ONE EXECUTABLE"
OBSERVED_OUTPUT: Final = "Observed probe output"
ITEM_ID: Final = "CS-703"

# The cap the hook renders the observed output through, and the slack allowed on
# top of it for the two-space indent and the label around it.
OBSERVED_CAP: Final = 200
OBSERVED_SLACK: Final = 80

# A candidate that ignores its arguments and floods stdout, so the truncation has
# something to truncate. 40 characters, 40 times, with no trailing newline.
CHATTY_MARKER: Final = "CHATTY0123456789CHATTY0123456789CHATTY01"
CHATTY_REPEATS: Final = 40
CHATTY_SHIM: Final = (
    "#!/bin/sh\n"
    "# CS-703 fixture: ignores its arguments and floods stdout.\n"
    "i=0\n"
    'while [ "$i" -lt ' + str(CHATTY_REPEATS) + " ]; do\n"
    "    printf '" + CHATTY_MARKER + "'\n"
    "    i=$((i + 1))\n"
    "done\n"
)

# A drive-letter path in any form. Used to drop a line from a report rather than
# to parse it.
DRIVE_PATH: Final = re.compile(r"[A-Za-z]:[\\/]")

# The top of 7-bit ASCII, which is what the hooks are held to.
MAX_ASCII_BYTE: Final = 0x7E

_PAYLOADS: Final = itertools.count(1)


ENVIRONMENT_REPR: Final = "<CS-703 child environment, contents withheld>"

# The shortest environment value the leak probe bothers to look for. Below
# this, a "value" is things like "1" or "C:" and would match by coincidence.
INTERESTING_VALUE_LENGTH: Final = 12


class Environment(NamedTuple):
    """The child environment for a sandbox, wrapped so no report can render it.

    THIS TYPE EXISTS FOR ONE REASON AND IT IS NOT TIDINESS. pytest renders every
    test function's arguments at the top of a failure traceback, by default, with
    no flag required. A test that takes the raw ``dict`` therefore prints the
    WHOLE inherited environment into the report the moment anything in that test
    fails - and a developer machine's environment routinely carries API
    credentials. MEASURED before this type existed, on one forced failure of one
    arm of this module: the report rendered ``isolated = {`` followed by an
    API-key-shaped value in full, plus five other long opaque tokens.

    ``tests/conftest.py`` redacts home paths and account names and carries NO
    secret or token rule at all, so nothing downstream catches it either.

    THE MODULE THIS ONE WAS BUILT FROM DOES NOT HAVE THE HOLE, which is the part
    worth keeping. ``tests/test_commit_msg_gate.py`` takes the environment
    directly on exactly one arm and routes everything else through its
    repr-guarded ``sandbox`` fixture, whose docstring says in terms that ``env``
    carries the whole inherited environment. This module copied the guard onto
    ``Sandbox`` and then reached the same data by a second, unguarded route -
    which is the general shape of a control being defeated by its own copy.
    """

    variables: dict[str, str]

    def __repr__(self) -> str:
        """Render without any of the environment's contents."""
        return ENVIRONMENT_REPR


class Sandbox(NamedTuple):
    """A throwaway git repository whose only wired hook is ``hook``.

    THE REPR WITHHOLDS EVERY PATH, and that is not decoration. pytest renders
    the fixture values it can reach at the top of a failure report, and ``work``,
    ``hooks`` and ``remote`` all carry absolute paths under the real user profile
    while ``env`` carries the whole inherited environment, account name included.
    """

    work: Path
    hooks: Path
    remote: Path
    env: dict[str, str]
    hook: str

    @property
    def prefix(self) -> str:
        """The banner this hook writes, so a refusal can be attributed to it."""
        return "clockspeed " + self.hook

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return f"<CS-703 sandbox for {self.hook}, paths withheld>"


class Attempt(NamedTuple):
    """The measured outcome of one real ``git commit``."""

    returncode: int
    head_before: str
    head_after: str
    hook_output: tuple[str, ...]

    @property
    def head_moved(self) -> bool:
        """Whether the commit actually landed."""
        return self.head_before != self.head_after

    @property
    def blocked(self) -> bool:
        """Whether git refused AND nothing was committed."""
        return self.returncode != 0 and not self.head_moved

    @property
    def accepted(self) -> bool:
        """Whether git succeeded AND a commit landed."""
        return self.returncode == 0 and self.head_moved

    @property
    def blocked_by_the_interpreter_check(self) -> bool:
        """Whether the PART 2 interpreter refusal fired, not merely that something did.

        ``blocked`` alone is satisfied by ANY refusal - nothing staged, a bad
        identity, a different rule inside the same hook - so an arm asserting only
        ``blocked`` could go green while the rule under test did nothing at all.
        That is precisely the false green this item was filed under.
        """
        return self.blocked and any(PROBE_REFUSAL in line for line in self.hook_output)

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.hook_output) if self.hook_output else "(no hook output)"
        return f"exit={self.returncode} head_moved={self.head_moved}\n{shown}"


class Push(NamedTuple):
    """The measured outcome of one real ``git push``."""

    returncode: int
    landed_before: bool
    landed_after: bool
    hook_output: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        """Whether git refused AND the ref never reached the remote."""
        return self.returncode != 0 and not self.landed_after

    @property
    def accepted(self) -> bool:
        """Whether git succeeded AND the ref reached the remote."""
        return self.returncode == 0 and self.landed_after

    @property
    def blocked_by_the_interpreter_check(self) -> bool:
        """Whether the PART 2 interpreter refusal fired. See ``Attempt``."""
        return self.blocked and any(PROBE_REFUSAL in line for line in self.hook_output)

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.hook_output) if self.hook_output else "(no hook output)"
        return (
            f"exit={self.returncode} landed_before={self.landed_before} "
            f"landed_after={self.landed_after}\n{shown}"
        )


def hook_output(stderr: str, prefix: str) -> tuple[str, ...]:
    """Keep only the hook's own lines, so no git-rendered path can reach a report.

    Each hook writes a banner beginning with its own tool name and indents every
    continuation by two spaces. Anything else on stderr is git's, may name the
    sandbox path, and is dropped.

    THE DRIVE-LETTER FILTER IS A DELIBERATE TRADE. It can in principle drop the
    very line an assertion is looking for, turning a real failure into a confusing
    one. No line any of the three hooks writes carries a drive letter, so the cost
    is hypothetical while the leak it prevents is not.
    """
    return tuple(
        line
        for line in stderr.split("\n")
        if line.startswith((prefix, "  ")) and line.strip() and not DRIVE_PATH.search(line)
    )


def probe_block(raw: bytes) -> bytes:
    """Extract the ``cs_probe`` definition and its constants from a hook's bytes.

    Anchored on the function, which exists both before and after the repair, plus
    any ``CS_PROBE_*`` assignment the repair introduces. The comment above the
    probe is deliberately NOT part of the extracted block: it is prose, and the
    property under test is that the EXECUTABLE text cannot diverge between the
    three copies.
    """
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


def refusal_block(raw: bytes) -> bytes:
    """The PART 2 refusal message, MINUS its final per-hook line.

    WHY THIS EXISTS. ``probe_block`` covers only the constants and the ``cs_probe``
    body, so the entire refusal was invisible to the byte-identity arm. Two
    mutants survived on exactly that gap: deleting the "ONE EXECUTABLE" line from
    two hooks of three, and removing the flood cap from two hooks of three. Both
    left the suite green.

    THE LAST LINE IS EXCLUDED BECAUSE IT IS SUPPOSED TO DIFFER - each hook closes
    in its own voice, "an unrunnable gate is not a passed gate" against "an
    unrunnable suite is not a passing suite". Every die argument except the last
    ends in a backslash continuation, which is what locates the tail.
    """
    collected: list[bytes] = []
    inside = False
    for line in raw.split(b"\n"):
        if line.lstrip().startswith(b'die "CLOCKSPEED_PYTHON is set'):
            inside = True
        if inside:
            collected.append(line)
            if not line.rstrip().endswith(b"\\"):
                break
    return b"\n".join(collected[:-1])


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


def env_naming(
    box: Sandbox, interpreter: str | None, path_prefix: Path | None = None
) -> dict[str, str]:
    """The sandbox environment with CLOCKSPEED_PYTHON set, and optionally PATH shadowed.

    PATH IS MANIPULATED IN THIS DICT, NEVER IN THE PROCESS. An arm that shadowed
    ``python`` for the whole pytest run would change which interpreter every other
    arm resolves, and the damage would not be visible in the arm that caused it.
    """
    env = dict(box.env)
    env.pop(ENV_NAME, None)
    if interpreter is not None:
        env[ENV_NAME] = interpreter
    if path_prefix is not None:
        env["PATH"] = str(path_prefix) + os.pathsep + env["PATH"]
    return env


def head_of(box: Sandbox, env: dict[str, str]) -> str:
    """The current HEAD commit id, or a sentinel when there is no commit yet."""
    proc = run_git(box, "rev-parse", "HEAD", env=env)
    return proc.stdout.strip() if proc.returncode == 0 else NO_HEAD


def ref_on_remote(box: Sandbox, env: dict[str, str]) -> bool:
    """Whether the sandbox branch exists on the bare remote. The push oracle."""
    proc = run_git(box, "ls-remote", "origin", "refs/heads/" + SANDBOX_BRANCH, env=env)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def commit_attempt(
    box: Sandbox,
    *,
    message: str = LEGITIMATE,
    content: bytes = CLEAN_CONTENT,
    interpreter: str | None = None,
    path_prefix: Path | None = None,
) -> Attempt:
    """Stage a real change and drive a real ``git commit``.

    EVERY ATTEMPT STAGES A NEW FILE, and the counter that guarantees it is
    load-bearing rather than tidy. Re-staging identical bytes stages nothing, and
    git then refuses the commit for having nothing to commit - a non-zero exit
    with HEAD unchanged, which is indistinguishable from a hook block. Every arm
    expecting a block would pass, and pass for the wrong reason.
    """
    payload = box.work / f"{PAYLOAD_STEM}-{next(_PAYLOADS)}.txt"
    payload.write_bytes(content)
    env = env_naming(box, interpreter, path_prefix)

    staged = run_git(box, "add", payload.name, env=env)
    assert staged.returncode == 0, "the sandbox change could not be staged"

    message_file = box.hooks.parent / MESSAGE_NAME
    message_file.write_bytes(message.encode("utf-8"))

    before = head_of(box, env)
    proc = run_git(box, "commit", "-F", str(message_file), env=env)
    after = head_of(box, env)
    return Attempt(proc.returncode, before, after, hook_output(proc.stderr, box.prefix))


def push_attempt(box: Sandbox, *, interpreter: str | None = None) -> Push:
    """Drive a real ``git push`` at the sandbox's own bare remote."""
    env = env_naming(box, interpreter)
    before = ref_on_remote(box, env)
    # MEASURED AND ASSERTED, not merely rendered. If the branch were already on
    # the remote, `git push` short-circuits with "Everything up-to-date" and exit
    # 0 WITHOUT running the hook at all - and `accepted` would then be True for a
    # push that proved nothing. The commit path guards its analogue by asserting
    # the change staged; this is that guard.
    assert not before, (
        "the sandbox branch was already on the remote; the push would not run the hook"
    )
    proc = run_git(box, "push", "origin", SANDBOX_BRANCH, env=env)
    after = ref_on_remote(box, env)
    return Push(proc.returncode, before, after, hook_output(proc.stderr, box.prefix))


def clean_attempt(box: Sandbox, interpreter: str) -> Attempt | Push:
    """Drive this sandbox's hook on a CLEAN input under ``interpreter``.

    THE INPUT IS CLEAN ON PURPOSE. Nothing about the commit or the push is
    objectionable, so the only thing that can refuse it is the interpreter check -
    which is what lets an arm below attribute a refusal to that check and then
    make assertions about its wording.
    """
    if box.hook == PRE_PUSH:
        return push_attempt(box, interpreter=interpreter)
    return commit_attempt(box, interpreter=interpreter)


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment with the operator's own git configuration excluded.

    Both files are aimed at paths that do not exist, so a machine carrying
    core.hooksPath, commit.gpgsign or commit.template globally cannot answer for
    git here. CLOCKSPEED_PYTHON is removed at the root, so an arm that means
    "unset" gets unset even if the operator exported one.

    RETURNS THE CARRIER RATHER THAN THE BARE DICT. Every arm in this module takes
    this fixture as a direct argument, and pytest renders a failing test's
    arguments by default - see ``Environment`` for what that printed before this
    was wrapped.
    """
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    env.pop(ENV_NAME, None)
    return Environment(env)


def make_sandbox(
    tmp_path: Path,
    isolated: Environment,
    hook: str,
    *,
    suite_passes: bool = False,
) -> Sandbox:
    """A real repository with exactly one tracked hook wired, and one commit in it.

    The identity is synthetic. Letting git fall back to the machine's real
    user.name would write the Windows account name into a commit object inside the
    test (CLAUDE.md non-negotiable 3).
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir(exist_ok=True)
    installed = hooks / hook
    installed.write_bytes((HOOKS_DIR / hook).read_bytes())
    installed.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()
    remote = tmp_path / "remote.git"

    box = Sandbox(work=work, hooks=hooks, remote=remote, env=isolated.variables, hook=hook)

    started = run_git(box, "init", "-q", "-b", SANDBOX_BRANCH)
    assert started.returncode == 0, "the throwaway repository could not be initialised"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("core.hooksPath", str(hooks)),
    ):
        written = run_git(box, "config", key, value)
        assert written.returncode == 0, f"{key} could not be written in the sandbox"

    # Setting a value is not evidence the value took - scripts/install_hooks.py
    # reads its own write back for exactly this reason.
    readback = run_git(box, "config", "--get", "core.hooksPath")
    took = readback.returncode == 0 and readback.stdout.strip() == str(hooks)
    assert took, "core.hooksPath did not take in the sandbox"

    if hook == PRE_COMMIT:
        # The hook resolves the gate at $ROOT/tools/precommit_gate.py and refuses
        # to run without it, so the sandbox carries the real tracked gate rather
        # than a stub. A stub would make every pre-commit arm a test of the stub.
        (work / "tools").mkdir()
        shutil.copy2(TRACKED_GATE, work / "tools" / "precommit_gate.py")

    if hook == PRE_PUSH:
        # A TINY SUITE, DELIBERATELY. The hook runs pytest against $ROOT/tests, and
        # pointing that at this repository's own suite would put roughly 250
        # seconds into every pre-push arm.
        tests = work / "tests"
        tests.mkdir()
        body = "def test_sandbox_arm() -> None:\n    assert %s\n" % suite_passes
        (tests / "test_sandbox_arm.py").write_bytes(body.encode("ascii"))
        # PINS PYTEST'S ROOTDIR AT THE SANDBOX, and this line is worth its comment.
        # Without an ini file pytest walks upward looking for one, reaches the
        # system temp directory, and spends about 33 seconds enumerating it before
        # dying with a collection error on a stale sibling that vanished mid-scan -
        # exit 2, which is neither of the outcomes any arm here means to measure.
        (work / "pytest.ini").write_bytes(b"[pytest]\n")

        initialised = run_git(box, "init", "-q", "--bare", str(remote))
        assert initialised.returncode == 0, "the bare remote could not be initialised"
        added = run_git(box, "remote", "add", "origin", str(remote))
        assert added.returncode == 0, "the bare remote could not be added"

    seed = commit_attempt(box)
    assert seed.accepted, f"the sandbox could not make its first commit:\n{seed.report}"
    return box


# --- preconditions ----------------------------------------------------------


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_the_wired_hook_is_a_byte_identical_copy_of_the_tracked_hook(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """Without this, every arm below could be grading a copy that drifted."""
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    copied = (box.hooks / hook).read_bytes()
    assert copied == (HOOKS_DIR / hook).read_bytes(), (
        "the sandbox hook is not the tracked hook, so nothing below grades the real file"
    )


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_the_tracked_hook_is_lf_only_ascii_and_carries_no_bom(hook: str) -> None:
    """Asserted after every edit, on all three hooks, never assumed.

    The harness edit path converts a tracked file to CRLF while git normalises the
    blob, so ``git status`` still reports clean and the breakage is invisible
    there. msys bash runs a CRLF hook correctly on this toolchain; it surfaces on
    a stricter shell, which is the worst place to find it.
    """
    raw = (HOOKS_DIR / hook).read_bytes()
    assert raw.count(b"\r") == 0, "the hook carries CR bytes; .gitattributes pins it to LF"
    assert not raw.startswith(b"\xef\xbb\xbf"), "the hook carries a UTF-8 BOM"
    assert max(raw) <= MAX_ASCII_BYTE, "the hook carries a byte above 0x7E"


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_the_probe_extractor_finds_a_probe_in_each_hook(hook: str) -> None:
    """The non-vacuity control for the arm below.

    An extractor that silently returned nothing would make three empty blocks
    compare equal, and the common-mode arm would be green while proving nothing.
    """
    block = probe_block((HOOKS_DIR / hook).read_bytes())
    assert b"cs_probe() {" in block, "no cs_probe definition was extracted"
    assert block.rstrip().endswith(b"}"), "the extracted probe block is not closed"


def test_the_three_hooks_carry_a_byte_identical_probe() -> None:
    """The common-mode control the CS-703 grant names by name.

    The defect was one probe copied three times. A repair applied to two of the
    three is green in exactly the way the defect was green - the two repaired
    hooks pass their own arms and the third silently keeps the hole. Comparing the
    executable text of all three is what makes that impossible to miss.
    """
    blocks = {hook: probe_block((HOOKS_DIR / hook).read_bytes()) for hook in HOOK_NAMES}
    distinct = set(blocks.values())
    diverging = sorted(hook for hook, block in blocks.items() if block != blocks[PRE_COMMIT])
    assert len(distinct) == 1, f"the probe is not byte-identical across the hooks: {diverging}"


# --- the defect, one arm per hook -------------------------------------------


def test_pre_commit_blocks_a_staged_em_dash_under_a_substituted_interpreter(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-703 acceptance, pre-commit. RED before the repair: exit 0, HEAD MOVED.

    ``true`` is the argument-ignoring program the acceptance names. It passed the
    old probe on its exit code alone, was handed the gate invocation, ignored it,
    and exited 0 - so the em dash committed and the character-set gate never ran.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    outcome = commit_attempt(box, content=EM_DASH_CONTENT, interpreter="true")
    assert outcome.blocked, (
        f"a substituted interpreter waved a staged em dash through:\n{outcome.report}"
    )
    assert outcome.blocked_by_the_interpreter_check, (
        "blocked, but NOT by the interpreter check. `blocked` alone is satisfied by "
        "the ladder falling through to a real python and refusing the em dash, which "
        f"is why a full PART 2 revert left this arm green:\n{outcome.report}"
    )


def test_commit_msg_blocks_a_co_authorship_trailer_under_a_substituted_interpreter(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-703 acceptance, commit-msg. RED before the repair: exit 0, HEAD MOVED.

    The heredoc carrying the whole check was handed to ``true``, which ignored it.
    Measured on the unrepaired hook: the commit landed and
    ``git log -1 --format='%(trailers:key=Co-authored-by)'`` read the trailer back
    as a REAL trailer, so CS-702 was disarmed by an environment variable.
    """
    box = make_sandbox(tmp_path, isolated, COMMIT_MSG)
    outcome = commit_attempt(box, message=TRAILER_MESSAGE, interpreter="true")
    assert outcome.blocked, (
        f"a substituted interpreter waved a co-authorship trailer through:\n{outcome.report}"
    )
    assert outcome.blocked_by_the_interpreter_check, (
        "blocked, but NOT by the interpreter check - see the pre-commit twin for why "
        f"that distinction is what a PART 2 revert turns on:\n{outcome.report}"
    )


def test_pre_push_blocks_a_failing_suite_under_a_substituted_interpreter(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-703 acceptance, pre-push. RED before the repair: exit 0, the ref LANDED.

    Both the ``import pytest`` check and the suite invocation went to ``true``, so
    the push reported a green suite that never ran.
    """
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=False)
    outcome = push_attempt(box, interpreter="true")
    assert outcome.blocked, (
        f"a substituted interpreter pushed a failing suite to the remote:\n{outcome.report}"
    )
    assert outcome.blocked_by_the_interpreter_check, (
        "blocked, but NOT by the interpreter check - see the pre-commit twin for why "
        f"that distinction is what a PART 2 revert turns on:\n{outcome.report}"
    )


# --- the harness controls, without which the three arms above prove nothing --


def test_pre_commit_still_blocks_a_staged_em_dash_with_the_variable_unset(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sandbox can say no for the input's own sake. Green before AND after."""
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    outcome = commit_attempt(box, content=EM_DASH_CONTENT)
    assert outcome.blocked, f"the character-set gate did not fire at all:\n{outcome.report}"


def test_commit_msg_still_blocks_a_co_authorship_trailer_with_the_variable_unset(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sandbox can say no for the input's own sake. Green before AND after."""
    box = make_sandbox(tmp_path, isolated, COMMIT_MSG)
    outcome = commit_attempt(box, message=TRAILER_MESSAGE)
    assert outcome.blocked, f"the trailer check did not fire at all:\n{outcome.report}"


def test_pre_push_still_blocks_a_failing_suite_with_the_variable_unset(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sandbox can say no for the input's own sake. Green before AND after."""
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=False)
    outcome = push_attempt(box)
    assert outcome.blocked, f"the suite did not gate the push at all:\n{outcome.report}"


def test_pre_commit_accepts_a_clean_file_with_the_variable_unset(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sandbox can say yes. An arm that only ever blocks proves nothing."""
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    outcome = commit_attempt(box)
    assert outcome.accepted, f"an ordinary commit was blocked:\n{outcome.report}"


def test_commit_msg_accepts_an_ordinary_message_with_the_variable_unset(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sandbox can say yes. An arm that only ever blocks proves nothing."""
    box = make_sandbox(tmp_path, isolated, COMMIT_MSG)
    outcome = commit_attempt(box)
    assert outcome.accepted, f"an ordinary message was blocked:\n{outcome.report}"


def test_pre_push_accepts_a_passing_suite_with_the_variable_unset(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sandbox can say yes, and the ref really reaches the remote."""
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=True)
    outcome = push_attempt(box)
    assert outcome.accepted, f"a passing suite did not reach the remote:\n{outcome.report}"


# --- PART 2 did not turn the variable into a permanent block -----------------


def test_pre_commit_accepts_a_real_interpreter_named_in_the_variable(
    tmp_path: Path, isolated: Environment
) -> None:
    """A REAL interpreter in CLOCKSPEED_PYTHON is still honoured.

    Named by the running interpreter's own path, so this arm cannot be satisfied
    by the ladder falling through to ``python`` - the value under test is a real,
    working, explicitly chosen executable. The path goes into the child
    environment and into no assertion message.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    outcome = commit_attempt(box, interpreter=REAL_PYTHON)
    assert outcome.accepted, (
        f"a real interpreter named in {ENV_NAME} was refused:\n{outcome.report}"
    )


def test_commit_msg_accepts_a_real_interpreter_named_in_the_variable(
    tmp_path: Path, isolated: Environment
) -> None:
    """See the pre-commit twin. PART 2 must refuse a FAILING value, not every value."""
    box = make_sandbox(tmp_path, isolated, COMMIT_MSG)
    outcome = commit_attempt(box, interpreter=REAL_PYTHON)
    assert outcome.accepted, (
        f"a real interpreter named in {ENV_NAME} was refused:\n{outcome.report}"
    )


def test_pre_push_accepts_a_real_interpreter_named_in_the_variable(
    tmp_path: Path, isolated: Environment
) -> None:
    """See the pre-commit twin. The suite really runs under the named interpreter."""
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=True)
    outcome = push_attempt(box, interpreter=REAL_PYTHON)
    assert outcome.accepted, (
        f"a real interpreter named in {ENV_NAME} was refused:\n{outcome.report}"
    )


# --- the probe judges OUTPUT, not the exit code -----------------------------


@pytest.mark.parametrize("program", ARGUMENT_IGNORING_PROGRAMS)
def test_a_program_that_ignores_its_arguments_is_refused(
    tmp_path: Path, isolated: Environment, program: str
) -> None:
    """The heart of PART 1, driven through the tracked hook rather than a copy.

    THE INPUT IS CLEAN, which is what makes this arm sharp. Nothing about the
    commit is objectionable, so the ONLY thing that can refuse it is the
    interpreter check. Before the repair all three of these passed the probe on
    their exit code and the commit landed, exit 0.

    ``echo`` is the interesting one: it exits 0 like the others but PRINTS, so it
    is the candidate that separates "judges the exit code" from "judges the
    output". It was not named in the original filing and was measured later.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    outcome = commit_attempt(box, interpreter=program)
    assert outcome.blocked_by_the_interpreter_check, (
        f"{program!r} was accepted as an interpreter:\n{outcome.report}"
    )


def test_the_interpreter_attribution_can_tell_the_hooks_refusals_apart(
    tmp_path: Path, isolated: Environment
) -> None:
    """The control for ``blocked_by_the_interpreter_check``, without which it proves nothing.

    A property that were merely an alias for ``blocked`` would make every arm above
    pass on ANY refusal, and nothing would say so. This arm forces a refusal from a
    DIFFERENT rule - the character-set gate, with a real interpreter resolved - and
    asserts the property reports False.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    outcome = commit_attempt(box, content=EM_DASH_CONTENT)
    assert outcome.blocked, f"the character-set gate did not refuse at all:\n{outcome.report}"
    assert not outcome.blocked_by_the_interpreter_check, (
        "a character-set refusal was credited to the interpreter check, so the "
        f"attribution used by every arm above is worthless:\n{outcome.report}"
    )


# --- PART 2: a set-but-failing value is a hard failure, and it says why ------


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_a_set_but_failing_value_is_refused_by_every_hook(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """PART 2, on all three hooks. Agreement between byte-identical copies is not evidence.

    The old ladder fell through to ``python`` when the named interpreter failed the
    probe, so a value the operator deliberately set was silently overruled and the
    commit landed anyway - the CS-806 shape in a quieter form. A loud refusal is
    the chosen cost.
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    if hook == PRE_PUSH:
        result: Attempt | Push = push_attempt(box, interpreter="true")
    else:
        result = commit_attempt(box, interpreter="true")
    assert result.blocked_by_the_interpreter_check, (
        f"{hook} did not refuse a set-but-failing value:\n{result.report}"
    )


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_a_command_line_in_the_variable_is_refused_and_the_message_says_why(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """THE MOST LIKELY REAL-WORLD TRIP, and the reason condition 4 is worded as it is.

    BOOTSTRAP.md section 2.5 writes the resolution order as prose that reads like a
    command line, so ``CLOCKSPEED_PYTHON='py -3'`` is the natural thing to type. It
    is two tokens, it cannot be exec'd as one executable name, and it fails the
    probe. Before PART 2 that failure was silent - the ladder fell through to
    ``python`` and the commit landed. After PART 2 it blocks EVERY commit, so the
    message has to name the cause outright rather than leave it to be guessed.

    PARAMETRIZED OVER ALL THREE HOOKS, because it was not. Deleting the ONE
    EXECUTABLE line from commit-msg and pre-push while leaving pre-commit intact
    was a MEASURED SURVIVOR: the suite stayed green at 41 passed. Condition 4 was
    pinned on one hook of three.
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    outcome = clean_attempt(box, COMMAND_LINE_NOT_EXECUTABLE)
    assert outcome.blocked_by_the_interpreter_check, (
        f"{hook}: a command line was accepted as an interpreter:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert ONE_EXECUTABLE in rendered, (
        f"{hook}: the refusal does not say the value must name one executable:\n{outcome.report}"
    )
    assert ITEM_ID in rendered, f"{hook}: the refusal does not cite the item:\n{outcome.report}"


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_the_refusal_prints_the_observed_probe_output(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """Condition 4's other half: the message shows what the candidate actually said.

    ``echo`` re-emits the probe program, so its observed output carries a fragment
    no other part of the message contains. Finding that fragment in the refusal is
    what proves the OBSERVED output is rendered rather than a fixed description of
    it.
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    outcome = clean_attempt(box, "echo")
    assert outcome.blocked_by_the_interpreter_check, (
        f"{hook}: expected a refusal:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert OBSERVED_OUTPUT in rendered, (
        f"{hook}: the refusal does not label the observed output:\n{outcome.report}"
    )
    assert "sys.stdout.write" in rendered, (
        f"{hook}: the refusal omits what the candidate printed:\n{outcome.report}"
    )


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_a_chatty_candidate_cannot_flood_the_terminal(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """The truncation, measured rather than assumed, on every hook.

    A candidate that ignores its arguments is free to print without limit, and the
    refusal quotes what it printed. Without a cap, one misconfigured value turns
    every commit into a wall of that program's output. The shim emits 1600
    characters on one line.

    PARAMETRIZED FOR THE SAME REASON AS THE ARM ABOVE. Removing the cap from
    commit-msg and pre-push was a MEASURED SURVIVOR at 41 passed; the longest
    banner line went from 204 characters to 1564 and nothing failed.
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    shim = box.hooks.parent / SHIM_NAME
    shim.write_bytes(CHATTY_SHIM.encode("ascii"))
    shim.chmod(0o755)

    outcome = clean_attempt(box, str(shim))
    assert outcome.blocked_by_the_interpreter_check, (
        f"{hook}: the chatty candidate was accepted as an interpreter:\n{outcome.report}"
    )
    quoting = [line for line in outcome.hook_output if CHATTY_MARKER in line]
    assert quoting, f"{hook}: the refusal did not quote the candidate's output at all"
    assert len(quoting) == 1, f"{hook}: the output was rendered across several lines"
    assert len(quoting[0]) <= OBSERVED_CAP + OBSERVED_SLACK, (
        f"{hook}: the observed output was not truncated: {len(quoting[0])} characters"
    )


# --- the repair round: the probe must prove the candidate can REPORT FAILURE --
#
# THE ESCAPE THIS SECTION CLOSES, and it refuted the first build of this item.
# The stdout half of the probe proves a candidate RUNS the program it is handed.
# It says nothing about whether the candidate can REPORT a failure - and every
# gate decision in all three hooks is taken from ``$?``, a channel the stdout
# half never consults. A wrapper that forwards stdout faithfully and drops the
# exit status therefore answers the probe with the exact token and turns all
# three tier-0 gates into no-ops.
#
# NEITHER SHAPE IS PURPOSE-BUILT AND NEITHER KNOWS THE TOKEN. A POSIX wrapper
# ending in ``| cat`` reports the pipeline's status, which is the LAST command's.
# A Windows .cmd shim wrapping its body in ``setlocal`` / ``endlocal`` has its
# ERRORLEVEL reset by ``endlocal``. Both are ordinary ways to wrap an
# interpreter, and a person who writes either is not attacking anything.
#
# THE ESCAPE IS REACHABLE WITH NO ENVIRONMENT VARIABLE AT ALL, through the
# ``python`` rung of the ladder. That is why "unset CLOCKSPEED_PYTHON" is not a
# mitigation, and why the PATH arms below are the ones that decide the item.
#
# WHY EVERY ARM ABOVE MISSED IT, which is the transferable part: ``true``, ``:``
# and ``echo`` all fail at the STDOUT comparison and never reach the exit-code
# question. The suite therefore established "a candidate that cannot print the
# token is refused" - true, and far narrower than what CS-703 needs. An oracle
# built from the same three programs has the same blind spot.

REAL_PYTHON_POSIX: Final = Path(REAL_PYTHON).as_posix()

# Forwards stdout AND the exit status. The non-vacuity control: without it, the
# liar arms are satisfied by a probe that refuses every wrapper on sight, which
# would be a different and much cruder rule than the one under test.
HONEST_SHIM: Final = '#!/bin/sh\nexec "' + REAL_PYTHON_POSIX + '" "$@"\n'

# Forwards stdout faithfully and throws the exit status away, because a
# pipeline's status is its LAST command's.
LIAR_SHIM: Final = '#!/bin/sh\n"' + REAL_PYTHON_POSIX + '" "$@" | cat\n'

# The rungs the ladder tries by name. Shadowing all of them is what stops a liar
# on one rung from being masked by a real interpreter on the next.
LADDER_RUNGS: Final = ("python", "python3", "py")

PROBE_ANSWER: Final = "clockspeed-python-ok"
EXIT_STATUS_LABEL: Final = "Observed exit status"
LADDER_EXHAUSTED: Final = "no usable python interpreter found"


def write_shim(directory: Path, name: str, body: str) -> Path:
    """Materialise one shim as an executable file and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(body.encode("ascii"))
    path.chmod(0o755)
    return path


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_every_hook_refuses_an_interpreter_that_cannot_report_failure(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """The escape, on all three hooks. RED before the repair: the violation LANDED.

    Measured against the stdout-only probe: the pre-commit em dash committed, the
    commit-msg trailer committed and git read it back as a real trailer, and the
    push put a red suite on the remote. All three exited 0.
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=False)
    liar = write_shim(box.hooks.parent / "shims", "liar.sh", LIAR_SHIM)

    if hook == PRE_PUSH:
        result: Attempt | Push = push_attempt(box, interpreter=str(liar))
    elif hook == COMMIT_MSG:
        result = commit_attempt(box, message=TRAILER_MESSAGE, interpreter=str(liar))
    else:
        result = commit_attempt(box, content=EM_DASH_CONTENT, interpreter=str(liar))

    assert result.blocked, (
        f"{hook} accepted an interpreter that cannot report failure:\n{result.report}"
    )


def test_a_liar_on_the_path_is_refused_with_no_environment_variable_set(
    tmp_path: Path, isolated: Environment
) -> None:
    """THE ARM THAT DECIDES THE ITEM. No CLOCKSPEED_PYTHON anywhere.

    The wrapper is installed as ``python`` and found through PATH, which is the
    ladder's second rung and the one a real machine actually uses. Before the
    repair this committed a staged em dash with exit 0 - so the defect never
    needed an environment variable, and telling someone to unset one fixed
    nothing.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    shadow = box.hooks.parent / "onpath"
    write_shim(shadow, "python", LIAR_SHIM)

    outcome = commit_attempt(box, content=EM_DASH_CONTENT, path_prefix=shadow)
    assert outcome.blocked, (
        f"a liar installed as `python` waved a staged em dash through:\n{outcome.report}"
    )


def test_a_liar_on_every_ladder_rung_exhausts_the_ladder_rather_than_passing(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sharper PATH arm: no real interpreter is reachable by name at all.

    The arm above can in principle be satisfied by the ladder falling through to a
    genuine ``python3`` - which is correct behaviour, but it means that arm does
    not prove the PROBE rejected anything. Shadowing every rung removes the
    fall-through, so the only way to block is to refuse each liar in turn and run
    out of rungs.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    shadow = box.hooks.parent / "allrungs"
    for rung in LADDER_RUNGS:
        write_shim(shadow, rung, LIAR_SHIM)

    outcome = commit_attempt(box, content=EM_DASH_CONTENT, path_prefix=shadow)
    assert outcome.blocked, (
        f"a liar on every ladder rung was accepted as an interpreter:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert LADDER_EXHAUSTED in rendered, (
        f"the ladder did not report itself exhausted, so something resolved:\n{outcome.report}"
    )


def test_an_honest_wrapper_is_still_accepted(tmp_path: Path, isolated: Environment) -> None:
    """THE NON-VACUITY CONTROL for every liar arm above.

    ``exec "$real" "$@"`` forwards both channels, so it is a perfectly good
    interpreter and must be honoured. Without this arm, the liar arms are equally
    satisfied by a probe that refuses anything that is not a bare executable -
    a cruder rule that would break real setups (a venv shim, a pyenv shim, a
    wrapper that sets an environment variable) for no gain.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    honest = write_shim(box.hooks.parent / "shims", "honest.sh", HONEST_SHIM)

    outcome = commit_attempt(box, interpreter=str(honest))
    assert outcome.accepted, f"an honest wrapper was refused:\n{outcome.report}"


def test_an_honest_wrapper_still_carries_a_real_refusal_through(
    tmp_path: Path, isolated: Environment
) -> None:
    """The other half of the control: the honest wrapper is FUNCTIONAL, not merely tolerated.

    Accepting a wrapper proves only that the probe let it past. This arm proves
    the gate then ran through it and its refusal survived the wrapper, which is
    the property the liar destroys.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    honest = write_shim(box.hooks.parent / "shims", "honest.sh", HONEST_SHIM)

    outcome = commit_attempt(box, content=EM_DASH_CONTENT, interpreter=str(honest))
    assert outcome.blocked, f"a real violation did not survive an honest wrapper:\n{outcome.report}"
    assert not outcome.blocked_by_the_interpreter_check, (
        f"the honest wrapper was refused as an interpreter rather than used:\n{outcome.report}"
    )


def test_the_liar_is_refused_by_the_exit_code_half_and_not_the_stdout_half(
    tmp_path: Path, isolated: Environment
) -> None:
    """WHICH HALF REFUSED, asserted rather than assumed.

    The liar's stdout is CORRECT - it forwards the real interpreter's, token and
    all - so a refusal that came from the stdout comparison would mean the probe
    is rejecting it for the wrong reason and would also reject every honest
    wrapper. The refusal must quote the token as the observed output, which is
    only possible if the stdout half PASSED, and must then report the exit status
    it got back.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    liar = write_shim(box.hooks.parent / "shims", "liar.sh", LIAR_SHIM)

    outcome = commit_attempt(box, interpreter=str(liar))
    assert outcome.blocked_by_the_interpreter_check, (
        f"the liar was accepted as an interpreter:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert PROBE_ANSWER in rendered, (
        "the refusal does not quote the expected answer as the observed output, so the stdout "
        f"half did not pass and this is not the exit-code refusal:\n{outcome.report}"
    )
    assert EXIT_STATUS_LABEL in rendered, (
        f"the refusal does not report the observed exit status:\n{outcome.report}"
    )


def test_the_environment_carrier_withholds_its_contents(isolated: Environment) -> None:
    """The credential control, pinned so the carrier cannot be quietly unwrapped.

    Every other arm in this module takes ``isolated`` as a direct argument, so the
    single thing standing between a routine assertion failure and a rendered API
    key is this repr. A future edit that returns the bare dict again, or that adds
    a field whose default repr leaks, fails here.

    THE ASSERTION MESSAGE NAMES VARIABLES, NEVER VALUES. A control that printed
    the secret it found in order to prove the secret was printed would be the
    defect wearing a different hat.
    """
    rendered = repr(isolated)
    assert rendered == ENVIRONMENT_REPR, "the environment carrier no longer withholds its contents"
    leaked = sorted(
        name
        for name, value in isolated.variables.items()
        if len(value) >= INTERESTING_VALUE_LENGTH and value in rendered
    )
    assert not leaked, f"the carrier's repr rendered the values of: {leaked}"


# --- the refusal block is common-mode too, and that is how two mutants lived --

# Each hook signs off in its own voice, which is why the identity arm compares
# the refusal MINUS its last line. Pinned here so the tails cannot quietly
# converge - if they ever did, excluding the last line would start hiding a real
# divergence instead of an intended one.
CLOSING_VOICES: Final = {
    PRE_COMMIT: "an unrunnable gate is not a passed gate",
    COMMIT_MSG: "an unrunnable check is not a passed check",
    PRE_PUSH: "an unrunnable suite is not a passing suite",
}

# Prints a banner and THEN delegates, so its stdout CONTAINS the expected answer
# behind a prefix. This is the shape the comment in the hook calls a knowingly
# accepted false refusal - a sitecustomize that prints, a .cmd shim without
# `@echo off`.
NOISY_SHIM: Final = (
    "#!/bin/sh\nprintf 'sitecustomize noise '\nexec \"" + REAL_PYTHON_POSIX + '" "$@"\n'
)


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_the_refusal_extractor_finds_a_refusal_in_each_hook(hook: str) -> None:
    """The non-vacuity control for the identity arm below.

    An extractor that silently returned nothing would make three empty blocks
    compare equal, and the arm would be green while proving nothing - which is
    precisely how the probe-only identity arm let two mutants through.
    """
    block = refusal_block((HOOKS_DIR / hook).read_bytes())
    assert block, "no refusal block was extracted"
    assert ONE_EXECUTABLE.encode("ascii") in block, (
        "the extracted refusal does not carry the ONE EXECUTABLE line"
    )
    assert b"$cs_probe_shown" in block, (
        "the extracted refusal does not render the TRUNCATED observed output"
    )


def test_the_three_hooks_carry_a_byte_identical_refusal() -> None:
    """The second common-mode control, added after two mutants survived the first.

    ``probe_block`` covers the constants and the ``cs_probe`` body and nothing
    else, so the whole refusal message was outside the identity check. MEASURED:
    deleting the ONE EXECUTABLE line from commit-msg and pre-push, and separately
    removing the flood cap from the same two, each left the suite green at 41
    passed. Both mutants change this block and cannot survive it.
    """
    blocks = {hook: refusal_block((HOOKS_DIR / hook).read_bytes()) for hook in HOOK_NAMES}
    diverging = sorted(hook for hook, block in blocks.items() if block != blocks[PRE_COMMIT])
    assert len(set(blocks.values())) == 1, (
        f"the refusal is not byte-identical across the hooks: {diverging}"
    )


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_each_hook_signs_the_refusal_in_its_own_voice(hook: str) -> None:
    """The justification for excluding the last line, asserted rather than assumed."""
    raw = (HOOKS_DIR / hook).read_bytes().decode("ascii")
    assert CLOSING_VOICES[hook] in raw, f"{hook} lost its own closing line"
    for other, voice in CLOSING_VOICES.items():
        if other != hook:
            assert voice not in raw, f"{hook} also carries {other}'s closing line"


def test_output_that_merely_contains_the_answer_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """EXACT EQUALITY, pinned so it cannot be softened to containment by one edit.

    The hook's comment records exact equality as a deliberate trade, and names the
    three false refusals it buys - a sitecustomize that prints, a .cmd shim
    without ``@echo off``, PYTHONIOENCODING=utf-8-sig. A decision with no arm
    behind it is one edit from being undone, and containment WAS a surviving
    mutant, so this arm is the fence.

    The shim below is otherwise a perfectly good interpreter: it forwards
    arguments, stdout and exit status. The ONLY thing wrong with it is a prefix on
    stdout. Under exact equality it is refused; under containment it would pass.
    The second assertion is what makes the arm sharp - it proves the answer really
    was present in the output, so the refusal is attributable to exactness rather
    than to the answer being absent.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    noisy = write_shim(box.hooks.parent / "shims", "noisy.sh", NOISY_SHIM)

    outcome = commit_attempt(box, interpreter=str(noisy))
    assert outcome.blocked_by_the_interpreter_check, (
        f"output merely CONTAINING the answer was accepted:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert PROBE_ANSWER in rendered, (
        "the observed output does not contain the expected answer, so this arm is "
        f"not measuring exactness at all:\n{outcome.report}"
    )


# --- CS-819: the check program must prove it RAN ----------------------------
#
# THE DEFECT. `.githooks/commit-msg` delivers its whole checking program to the
# interpreter as a heredoc. Under the MSYS2 build of dash a heredoc above 4096
# DELIVERED bytes arrives as ZERO bytes, so `python -` reads an EMPTY program -
# valid Python - does nothing and exits 0, and the old `exit $?` propagated that
# 0 faithfully. MEASURED on the tracked hook before the repair: the trailer, the
# em dash, the over-long subject, the placeholder and the empty message ALL
# exited 0 with COMPLETELY EMPTY STDERR under that dash, while all five refused
# correctly under bash. Zero bytes rather than truncation is what makes it fail
# OPEN - a truncated program would raise a SyntaxError and fail loudly.
#
# THE SEVERITY IS NARROWER THAN IT LOOKS AND THESE ARMS DO NOT OVERSTATE IT. The
# affected dash links msys-2.0.dll and the zero-byte delivery is a property of
# MSYS2 fork emulation rather than of dash generally. On Ubuntu CI `/bin/sh` IS
# dash, and `tests/test_commit_msg_gate.py` - driving REAL commits through this
# hook, with no skip or xfail markers - passes every violation class there.
# CS-702 IS ENFORCED ON UBUNTU CI. On this machine `/bin/sh` is bash, so git
# never invokes the affected dash here either. The defect is LATENT.
#
# THE ARM THAT CARRIES THE PROOF NEEDS NO DASH. `test_a_silent_interpreter_...`
# below drives REAL git through the sandbox with an interpreter that consumes the
# program and prints nothing - which is what the hook observes under the defect -
# and it runs everywhere. The dash arms are ADDITIONAL platform confirmation. A
# skip is not a pass (docs/LEDGER.md CS-428), so the property is never left to a
# shell that may be absent.

SENTINEL: Final = "clockspeed-commit-msg-ran"
SENTINEL_REFUSAL: Final = "DID NOT RUN"

DASH: Final = shutil.which("dash")
DEFAULT_SHELL: Final = shutil.which("sh")


def _dash_heredoc_delivery() -> int | None:
    """How many bytes does THIS dash deliver for an OVER-THRESHOLD heredoc?

    THE TRUNCATION IS A PROPERTY OF THE BUILD, NOT OF DASH, and the arms below
    branch on this rather than on whether dash exists. The MSYS2 build delivers
    ZERO above 4096 because MSYS fork emulation breaks dash's ``openhere()``
    writer path. GLIBC dash delivers the whole body - measured at 4535 bytes on
    ubuntu-latest by tier1 run 32609343989, which is the run that refuted the
    first version of these arms and turned an INFERRED residual in the CS-819
    grant into a measurement.

    Returns the delivered byte count, or None when there is no dash to ask.
    """
    if DASH is None:
        return None
    body = "\n".join(f"# pad {index:04d}" for index in range(500))
    if len(body) <= DASH_HEREDOC_THRESHOLD:
        return None
    script = "consume() { wc -c; }\nconsume <<'CS_END'\n" + body + "\nCS_END\n"
    with tempfile.TemporaryDirectory(prefix="cs819-delivery-") as box:
        path = Path(box) / "probe.sh"
        path.write_text(script, encoding="ascii", newline="\n")
        try:
            proc = subprocess.run(
                [DASH, str(path)],
                capture_output=True,
                text=True,
                timeout=GIT_TIMEOUT,
                stdin=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            return None
    if proc.returncode != 0:
        return None
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return None


# The delivery cliff, and what this machine's dash actually does with it.
DASH_HEREDOC_THRESHOLD: Final = 4096
DASH_DELIVERED: Final = _dash_heredoc_delivery()
DASH_TRUNCATES: Final = DASH_DELIVERED == 0


# Delegates -c so the probe still passes, and swallows the program otherwise.
# This is exactly what the hook observes under the CS-819 defect: no stdout,
# exit 0 - and it reproduces that without needing an affected shell.
SILENT_STUB: Final = (
    "#!/bin/sh\n"
    'if [ "$1" = "-c" ]; then\n'
    '    exec "' + REAL_PYTHON_POSIX + '" "$@"\n'
    "fi\n"
    "cat > /dev/null\n"
    "exit 0\n"
)

# The same shape, but it captures what was delivered so an arm can assert the
# program genuinely did NOT arrive rather than assuming it.
CAPTURE_STUB: Final = (
    "#!/bin/sh\n"
    'if [ "$1" = "-c" ]; then\n'
    '    exec "' + REAL_PYTHON_POSIX + '" "$@"\n'
    "fi\n"
    'cat > "$CS819_CAPTURE"\n'
    "exit 0\n"
)

# Delegates everything, so the real program runs and writes the real sentinel.
HONEST_STUB: Final = '#!/bin/sh\nexec "' + REAL_PYTHON_POSIX + '" "$@"\n'

# Each violation class, with the reason the hook's own program gives for it.
MESSAGE_CLASSES: Final = (
    ("trailer", TRAILER_MESSAGE, "co-authorship trailer"),
    ("non-ascii", "CS-819: an em " + EM_DASH + " dash\n", "non-ASCII character"),
    ("over-long subject", "C" * 90 + "\n", "subject line is"),
    ("placeholder", "wip\n", "bare placeholder"),
    ("empty", "\n\n   \n", "empty or whitespace only"),
)


def run_commit_msg_under(
    shell: str,
    tmp_path: Path,
    base: dict[str, str],
    message: str,
    interpreter: str | None = None,
    capture: Path | None = None,
) -> tuple[int, bytes, bytes]:
    """Invoke the tracked commit-msg hook directly under ``shell``.

    A DIRECT INVOCATION IS A SIMULATION and is labelled as one. git's real path
    is the sandbox suite above and `tests/test_commit_msg_gate.py`; this exists
    to reach a shell git does not use on this machine, which no sandbox can do.
    """
    message_file = tmp_path / "cs819-message.txt"
    message_file.write_bytes(message.encode("utf-8"))
    env = dict(base)
    env.pop(ENV_NAME, None)
    if interpreter is not None:
        env[ENV_NAME] = interpreter
    if capture is not None:
        env["CS819_CAPTURE"] = capture.as_posix()
    proc = subprocess.run(
        [shell, str(HOOKS_DIR / COMMIT_MSG), str(message_file)],
        capture_output=True,
        timeout=GIT_TIMEOUT,
        check=False,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_a_silent_interpreter_is_refused_through_real_git(
    tmp_path: Path, isolated: Environment
) -> None:
    """THE ARM THAT CARRIES CS-819, and it needs no particular shell.

    The interpreter consumes the program and prints nothing, which is precisely
    what the hook observes when the heredoc arrives empty. The message is
    LEGITIMATE, so nothing else in the hook has any reason to refuse it - the
    only thing that can is the completion sentinel.

    RED before the repair: the commit LANDED, exit 0, because `exit $?` faithfully
    propagated the 0 that an interpreter which did nothing returned.
    """
    box = make_sandbox(tmp_path, isolated, COMMIT_MSG)
    stub = write_shim(box.hooks.parent / "shims", "silent.sh", SILENT_STUB)

    outcome = commit_attempt(box, interpreter=stub.as_posix())
    assert outcome.blocked, (
        f"an interpreter that ran no checks was waved through:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert SENTINEL_REFUSAL in rendered, (
        f"the refusal does not say the check DID NOT RUN:\n{outcome.report}"
    )


def test_an_honest_interpreter_still_runs_the_checks_through_real_git(
    tmp_path: Path, isolated: Environment
) -> None:
    """THE NON-VACUITY CONTROL for the arm above, and it has two halves.

    Without it, the sentinel arm is equally satisfied by a hook that refuses
    every commit - which would pass the acceptance and break the repository. The
    first half proves a legitimate commit still LANDS through a delegating
    interpreter; the second proves a real violation is still refused BY ITS OWN
    RULE rather than by the sentinel, so the program really did run.
    """
    box = make_sandbox(tmp_path, isolated, COMMIT_MSG)
    stub = write_shim(box.hooks.parent / "shims", "honest-stub.sh", HONEST_STUB)

    landed = commit_attempt(box, interpreter=stub.as_posix())
    assert landed.accepted, f"a legitimate commit was refused:\n{landed.report}"

    refused = commit_attempt(box, message=TRAILER_MESSAGE, interpreter=stub.as_posix())
    assert refused.blocked, f"a trailer was not refused:\n{refused.report}"
    rendered = "\n".join(refused.hook_output)
    assert SENTINEL_REFUSAL not in rendered, (
        "the trailer was refused by the SENTINEL rather than by the trailer check, "
        f"so the check program did not actually run:\n{refused.report}"
    )


def test_the_shell_and_the_program_agree_on_the_sentinel() -> None:
    """One string, written in two languages in one file. Pinned so they cannot drift.

    The python program writes it and the shell compares against it. If an edit
    changed one and not the other, every commit would be refused with a message
    saying the check did not run - loudly, but for an invented reason.
    """
    raw = (HOOKS_DIR / COMMIT_MSG).read_bytes().decode("ascii")
    written = 'sys.stdout.write("' + SENTINEL + '")'
    compared = '"$cs_msg_out" != "' + SENTINEL + '"'
    assert raw.count(written) == 1, "the program does not write the sentinel exactly once"
    assert raw.count(compared) == 1, "the shell does not compare against that same sentinel"


def test_the_capture_is_a_plain_assignment_with_no_status_masking_prefix() -> None:
    """The single most dangerous way to get this wrong, pinned as a fence.

    `export`, `local` and `readonly` in front of the capture each MASK `$?` to 0
    in both bash and dash, which would silently restore the exact fail-open the
    sentinel exists to close - the status check would simply never fire. A future
    edit that adds one of them fails here.
    """
    raw = (HOOKS_DIR / COMMIT_MSG).read_bytes().decode("ascii")
    assert "\ncs_msg_out=$(" in raw, "the capture is not a bare assignment at column zero"
    for prefix in ("export cs_msg_out", "local cs_msg_out", "readonly cs_msg_out"):
        assert prefix not in raw, f"`{prefix}` masks $? to 0 and reopens CS-819"


def test_the_success_path_leaks_no_stdout_and_still_reports_on_stderr(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sentinel must be CONSUMED, not printed at git.

    Command substitution swallows the program's stdout, so the sentinel never
    reaches the terminal. This asserts both halves: nothing on stdout for a
    legitimate message, and the rejection text still arriving on stderr for a bad
    one - the capture must not have swallowed the diagnostics too.
    """
    assert DEFAULT_SHELL is not None, "no /bin/sh on this machine"
    code, out, err = run_commit_msg_under(DEFAULT_SHELL, tmp_path, isolated.variables, LEGITIMATE)
    assert code == 0, "a legitimate message was refused"
    assert out == b"", "the hook leaked stdout on the success path"
    assert SENTINEL.encode("ascii") not in out, "the sentinel reached the terminal"

    code, out, err = run_commit_msg_under(
        DEFAULT_SHELL, tmp_path, isolated.variables, TRAILER_MESSAGE
    )
    assert code != 0, "a trailer was accepted"
    assert out == b"", "the hook leaked stdout on the rejection path"
    assert b"co-authorship trailer" in err, "the rejection did not reach stderr"


@pytest.mark.parametrize(
    ("label", "message", "reason"), MESSAGE_CLASSES, ids=lambda value: str(value)[:20]
)
def test_every_message_class_still_reports_its_own_reason_on_stderr(
    tmp_path: Path, isolated: Environment, label: str, message: str, reason: str
) -> None:
    """The regression control for the CS-819 edit, over all five violation classes.

    MEASURED at the time of the edit, against the hook as it stood immediately
    before it: stderr was BYTE-IDENTICAL for all five classes plus the legitimate
    one, and every exit code was unchanged. That comparison needed the pre-edit
    file and cannot be reproduced from the tree afterwards, so what is pinned here
    is the observable it was protecting - each class still refused, by its own
    rule, with its reason on stderr and nothing on stdout.
    """
    assert DEFAULT_SHELL is not None, "no /bin/sh on this machine"
    code, out, err = run_commit_msg_under(DEFAULT_SHELL, tmp_path, isolated.variables, message)
    assert code != 0, f"{label} was accepted"
    assert out == b"", f"{label} leaked stdout"
    assert reason.encode("ascii") in err, f"{label} did not report its own reason on stderr"
    assert SENTINEL_REFUSAL.encode("ascii") not in err, (
        f"{label} was refused by the sentinel rather than by its own rule, so the "
        "check program did not run"
    )


@pytest.mark.skipif(
    DASH is None or not DASH_TRUNCATES,
    reason=(
        "NOT RUN, NOT PASSED: this machine's dash DELIVERS an over-threshold "
        f"heredoc ({DASH_DELIVERED} bytes), so the MSYS2 truncation cannot be "
        "reproduced here and this arm has nothing to measure. It is NOT a silent "
        "pass: the DELIVERING case is asserted by "
        "test_no_violation_class_slips_through_under_dash, which takes its other "
        "branch, and the property itself is proven shell-independently by "
        "test_a_silent_interpreter_is_refused_through_real_git."
    ),
)
def test_the_msys2_dash_truncation_reproduces_and_is_now_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """The platform arm, with the positive control that keeps it from going tautological.

    THE DELIVERED-BYTES ASSERTION IS THE CONTROL. Without it this arm would still
    pass on a dash that delivered the whole body, because the capturing stub prints
    no sentinel either way - it would be asserting nothing about the defect. So the
    premise is measured: the program must genuinely have failed to arrive. If a
    future dash delivers it, this FAILS rather than passing quietly, and the
    finding needs re-measuring (CONVENTIONS.md section 16).

    THE PATH MUST BE POSIX-FORM. Measured: dash cannot exec a backslash Windows
    path, and the interpreter check refuses it before the heredoc is ever reached -
    a refusal for the wrong reason, which would have made this arm meaningless.
    """
    assert DASH is not None
    stub = write_shim(tmp_path / "shims", "capture.sh", CAPTURE_STUB)
    capture = tmp_path / "delivered.txt"

    code, out, err = run_commit_msg_under(
        DASH,
        tmp_path,
        isolated.variables,
        TRAILER_MESSAGE,
        interpreter=stub.as_posix(),
        capture=capture,
    )
    delivered = capture.stat().st_size if capture.exists() else -1
    assert delivered == 0, (
        f"the heredoc delivered {delivered} bytes under dash, so the MSYS2 "
        "truncation no longer reproduces here and this arm's premise needs re-measuring"
    )
    assert code != 0, "the hook exited 0 after receiving no program at all"
    assert SENTINEL_REFUSAL.encode("ascii") in err, "the refusal does not name the cause"
    assert out == b"", "the hook leaked stdout"


@pytest.mark.skipif(
    DASH is None,
    reason=(
        "NOT RUN, NOT PASSED: no dash on this machine. See the arm above; the "
        "property is proven shell-independently elsewhere in this module."
    ),
)
@pytest.mark.parametrize(
    ("label", "message", "reason"), MESSAGE_CLASSES, ids=lambda value: str(value)[:20]
)
def test_no_violation_class_slips_through_under_dash(
    tmp_path: Path, isolated: Environment, label: str, message: str, reason: str
) -> None:
    """End to end on the affected shell, with the real interpreter.

    Before the repair every one of these exited 0 with COMPLETELY EMPTY STDERR.
    They are refused now - by the sentinel rather than by their own rules, because
    on this shell the rules never get delivered. That is the accepted cost the
    grant records: on an affected shell the hook is SAFE, not USABLE, and a
    legitimate commit is refused there too.
    """
    assert DASH is not None
    code, out, err = run_commit_msg_under(DASH, tmp_path, isolated.variables, message)
    assert code != 0, f"{label} exited 0 under dash"
    assert err != b"", f"{label} was refused with completely empty stderr"
    assert out == b"", f"{label} leaked stdout"
    if DASH_TRUNCATES:
        # THE RULE'S OWN REASON MUST BE ABSENT on a TRUNCATING build, and that is
        # the point rather than an oversight. The program never arrives, so no rule
        # can have judged anything, and the sentinel is the only thing that can
        # refuse. This is CS-819's accepted cost: SAFE on such a shell, not USABLE.
        assert reason.encode("ascii") not in err, (
            f"{label} reported its own rule's reason on a build measured to deliver "
            f"{DASH_DELIVERED} bytes, which contradicts the branch selector"
        )
        assert SENTINEL_REFUSAL.encode("ascii") in err, (
            f"{label} was refused, but not by the sentinel that CS-819 added"
        )
    else:
        # A DELIVERING build gets the STRONGER assertion, and on CI this is the
        # branch that runs. The program arrives, so each class must be refused BY
        # ITS OWN RULE - which proves the hook behaves identically under dash and
        # bash, and that CS-819's sentinel costs a delivering shell nothing.
        assert reason.encode("ascii") in err, (
            f"{label} did not report its own reason on a build measured to deliver "
            f"{DASH_DELIVERED} bytes, where the program does arrive"
        )
        assert SENTINEL_REFUSAL.encode("ascii") not in err, (
            f"{label} was refused by the sentinel on a DELIVERING build, which means "
            "the program did not arrive after all and the branch selector is wrong"
        )


# --- CS-823: the gate must PROVE it ran -------------------------------------
#
# THE DEFECT, IN TWO SHAPES. `.githooks/pre-commit` tested that the gate FILE
# existed and then ran it, taking the whole decision from `$?`. Nothing proved
# the gate EXECUTED.
#
# SHAPE ONE, A TRUNCATED GATE. `tools/precommit_gate.py` ends in an
# `if __name__ ...` main guard, so a copy truncated anywhere before that guard
# defines everything and executes NOTHING - python exits 0, and the hook read
# that 0 as a pass. MEASURED before the repair, with real commits staging an em
# dash and the gate truncated in the WORKING TREE only: truncated to 2368 lines,
# truncated to 1 line and emptied ALL exited 0, MOVED HEAD and wrote ZERO BYTES
# of stderr, against an intact control that refused with exit 1 and 576 bytes.
#
# SHAPE TWO, AND IT IS NOT WHAT THE ITEM WAS FILED ABOUT. The CS-703 probe asks
# a candidate to run a `-c` program; the gate is invoked as a FILE. A wrapper
# that delegates `-c` faithfully answers BOTH probe halves - the computed token
# and the returned 97 - while ignoring the gate entirely. MEASURED on the
# tracked hook: such a wrapper COMMITTED a staged em dash with exit 0, HEAD
# moved and ZERO bytes of stderr. It knows no token and is not built against the
# probe. `FILE_BLIND_SHIM` below is that wrapper.
#
# THE INDEX IS NO PROTECTION, and the sandbox reproduces that faithfully rather
# than by accident. The hook loads the gate from the WORKING TREE while the gate
# reads the files under test from the INDEX, and ``make_sandbox`` copies the gate
# in WITHOUT staging it - so truncating the working-tree copy leaves the index
# untouched, which is exactly the exposure.
#
# THE COMPILE ASSERTION IS A PREMISE FENCE, AND THIS PARAGRAPH USED TO OVERSTATE
# IT. It said the control was "why these arms mean anything"; an adversary then
# MEASURED that deleting both `gate_compiles` assertions leaves this module
# GREEN, so today they are inert. They are kept for what they will catch LATER -
# a truncation that stopped compiling would make python exit 1, and the hook
# would refuse for a reason that is not this defect - and the premise they guard
# is separately fenced by the main-guard arm below. What actually makes the
# truncation arms mean something is that each one COMMITTED before the repair.
#
# EVERY REFUSAL ARM ASSERTS NON-EMPTY OUTPUT AS WELL AS A NON-ZERO EXIT, because
# the defect's signature is exit 0 WITH ZERO BYTES OF STDERR. An arm reading only
# the exit code cannot tell the repair from the defect.
#
# WHY BOTH A DIRTY AND A CLEAN ARM. The dirty arm proves a forbidden byte cannot
# get through an unrun gate. The clean arm proves the guard refuses on the GATE'S
# state rather than on the CONTENT - an unrun gate is not a passed gate even when
# there was nothing to find. Without the clean arm the guard could be satisfied
# by a hook that merely re-checked the staged bytes itself in shell.

GATE_REFUSAL: Final = "DID NOT RUN"

# The gate's own main guard. Any truncation BEFORE this line that compiles
# defines everything and executes nothing, which is the whole defect.
GATE_MAIN_GUARD: Final = 'if __name__ == "__main__":'


def gate_main_guard_line() -> int:
    """The 1-based line the gate's main guard sits on, LOCATED rather than restated.

    The same locate-rather-than-restate rule ``gate_success_format`` applies to
    the PASS banner, applied to the one line number the truncation arms depend
    on. What comes back is the gate's own structure, so a change there moves
    the arms with it instead of leaving them pointed at a stale constant.
    """
    lines = TRACKED_GATE.read_bytes().decode("ascii").split("\n")
    hits = [number for number, line in enumerate(lines, 1) if line.startswith(GATE_MAIN_GUARD)]
    assert len(hits) == 1, f"the gate carries {len(hits)} main guards, expected exactly one"
    return hits[0]


# The truncation points the arms drive: one line before the main guard, one at
# the very top, and the empty file. ``None`` means empty.
#
# DERIVED, NEVER RESTATED, and this cost a real failure before it was. The first
# element was the literal 2368, which was correct only for the gate as it stood
# on the day it was written: MEASURED across insertion sizes 0 to 60 above the
# guard, 24 of 61 leave the 2368-line prefix no longer COMPILING, and a prefix
# that does not compile makes python exit 1 - so the arm would refuse for a
# reason that is not this defect and would pass while proving nothing. CS-838
# then inserted 117 lines above the guard and 2368 stopped compiling exactly as
# predicted. "One line before the main guard" is invariant under any insertion
# above it, which is the whole point.
TRUNCATIONS: Final = (gate_main_guard_line() - 1, 1, None)

# Answers the `-c` probe by delegating to the real interpreter, and does nothing
# at all with a FILE. This is the shape that makes the interpreter ladder
# insufficient on its own: it passes both probe halves honestly.
FILE_BLIND_SHIM: Final = (
    '#!/bin/sh\nif [ "$1" = "-c" ]; then\n    exec "' + REAL_PYTHON_POSIX + '" "$@"\nfi\nexit 0\n'
)


def gate_success_format() -> str:
    """The gate's success format string, LOCATED in its source rather than restated.

    ONE SIDE OF THE CONTRACT. The locator is the fragment ``: PASS - ``, which is
    narrow enough to find exactly one line and wide enough that it does not
    restate the format it is looking for. What comes back is the gate's own
    declaration, so a change there surfaces as a DISAGREEMENT with the hook
    rather than as two files quietly agreeing with a stale constant in a test.
    """
    gate = TRACKED_GATE.read_bytes().decode("ascii")
    hits = [line.strip() for line in gate.split("\n") if ": PASS - " in line]
    assert len(hits) == 1, f"expected one PASS format line in the gate, found {len(hits)}"
    literal = hits[0]
    stale = "the gate's PASS line is no longer a bare string literal, so this locator is stale"
    assert literal.startswith('"'), stale
    assert literal.endswith('"'), stale
    return literal[1:-1].replace("\\n", "")


def gate_name() -> str:
    """The gate's own tool name, read from its source."""
    gate = TRACKED_GATE.read_bytes().decode("ascii")
    marker = 'GATE_NAME = "'
    assert gate.count(marker) == 1, "the gate's name declaration moved"
    start = gate.index(marker) + len(marker)
    return gate[start : gate.index('"', start)]


def gate_success_line(checked: int, skipped: int) -> str:
    """What the gate actually writes as its last stdout line on a zero exit."""
    return gate_success_format() % (gate_name(), checked, skipped)


# Derived, never restated. Used only to search raw output for the banner's head.
GATE_SUCCESS_HEAD: Final = "%s: PASS - " % gate_name()


def hook_head_and_pattern() -> tuple[str, str]:
    """What the HOOK declares it requires: the banner head, and its case pattern.

    THE OTHER SIDE OF THE CONTRACT, also extracted rather than restated. The
    shell ``case`` pattern is translated into the glob ``fnmatch`` understands by
    dropping the shell quoting - the two share the same ``*`` and ``[...]``
    vocabulary for everything this pattern uses.
    """
    raw = (HOOKS_DIR / PRE_COMMIT).read_bytes().decode("ascii")
    marker = "CS_GATE_PASS='"
    assert raw.count(marker) == 1, "the hook does not declare the banner head exactly once"
    start = raw.index(marker) + len(marker)
    head = raw[start : raw.index("'", start)]

    lines = [line.strip() for line in raw.split("\n") if line.strip().startswith('"$CS_GATE_PASS"')]
    assert len(lines) == 1, f"expected one case pattern in the hook, found {len(lines)}"
    pattern = lines[0].rstrip(")").replace('"$CS_GATE_PASS"', head).replace('"', "")
    return head, pattern


def gate_prefix(lines: int | None) -> bytes:
    """The first ``lines`` lines of the tracked gate, or empty bytes for ``None``."""
    if lines is None:
        return b""
    body = TRACKED_GATE.read_bytes().split(b"\n")[:lines]
    return b"\n".join(body) + b"\n"


def gate_compiles(lines: int | None) -> bool:
    """Whether that prefix is syntactically valid python.

    An empty file compiles, which is precisely why the empty case fails OPEN
    rather than loudly: python accepts it, does nothing, and exits 0.
    """
    try:
        compile(gate_prefix(lines), "gate-under-test", "exec")
    except SyntaxError:
        return False
    return True


def truncate_gate(box: Sandbox, lines: int | None) -> None:
    """Rewrite the sandbox's WORKING-TREE gate. The index is deliberately untouched."""
    (box.work / "tools" / "precommit_gate.py").write_bytes(gate_prefix(lines))


def refused_as_unrun(attempt: Attempt) -> bool:
    """Whether the CS-823 guard fired, not merely that something refused.

    ``blocked`` alone is satisfied by any refusal at all - the gate's own
    verdict, a bad identity, nothing staged - so an arm asserting only
    ``blocked`` could go green while this guard did nothing. Same reasoning as
    ``Attempt.blocked_by_the_interpreter_check``.
    """
    return attempt.blocked and any(GATE_REFUSAL in line for line in attempt.hook_output)


def commit_and_scan(box: Sandbox, *, content: bytes, literal: str) -> tuple[Attempt, bool]:
    """A real commit, plus whether the RAW output carried one fixed literal.

    ``hook_output`` keeps only lines that begin with the hook's own banner or two
    spaces, and the gate's success banner is neither - so it is filtered out by
    design and an arm cannot see it through an ``Attempt``. This asks about ONE
    FIXED LITERAL instead of widening that filter: the raw text may name the
    sandbox path, so it is searched and then dropped, never returned and never
    rendered into an assertion message (CLAUDE.md non-negotiables 3 and 12).
    """
    payload = box.work / f"{PAYLOAD_STEM}-{next(_PAYLOADS)}.txt"
    payload.write_bytes(content)
    env = env_naming(box, None)

    staged = run_git(box, "add", payload.name, env=env)
    assert staged.returncode == 0, "the sandbox change could not be staged"

    message_file = box.hooks.parent / MESSAGE_NAME
    message_file.write_bytes(LEGITIMATE.encode("utf-8"))

    before = head_of(box, env)
    proc = run_git(box, "commit", "-F", str(message_file), env=env)
    after = head_of(box, env)
    attempt = Attempt(proc.returncode, before, after, hook_output(proc.stderr, box.prefix))
    return attempt, literal in (proc.stdout + proc.stderr)


def test_the_main_guard_sits_where_the_truncation_arms_assume() -> None:
    """The premise the arms rest on, measured rather than asserted in prose.

    THIS TEST WAS REWRITTEN WHEN TRUNCATIONS BECAME DERIVED, and the reason is
    worth stating so it is not read as a weakening. It used to assert that the
    guard sat AFTER the largest truncation point, which was a real check while
    that point was the literal 2368. Against a point derived as
    ``gate_main_guard_line() - 1`` the same comparison reduces to
    ``guard > guard - 1`` - an identity that can never fail and therefore
    detects nothing. Leaving it would have been a coverage reduction wearing
    the shape of a passing test.

    WHAT IS ASSERTED INSTEAD IS THE PROPERTY THAT ACTUALLY BREAKS. Every arm
    below rests on the truncated prefix being SYNTACTICALLY VALID: a prefix
    that does not compile makes python exit 1, the hook refuses for a reason
    that is not this defect, and the arm goes green having tested nothing.
    That is not hypothetical - CS-838 inserted 117 lines above the guard and
    the old hardcoded 2368 stopped compiling. Ordering is still checked, but
    against the FILE rather than against the derived value, so it remains
    capable of failing.
    """
    lines = TRACKED_GATE.read_bytes().decode("ascii").split("\n")
    hits = [number for number, line in enumerate(lines, 1) if line.startswith(GATE_MAIN_GUARD)]
    # UNREACHABLE BY CONSTRUCTION, and kept deliberately rather than deleted:
    # gate_main_guard_line asserts this same property at MODULE scope, so a
    # second guard fails COLLECTION and this line never runs. It stays because
    # it is the property the arms below depend on, and it starts firing again
    # the day that locator stops asserting.
    assert len(hits) == 1, f"the gate carries {len(hits)} main guards, expected exactly one"
    assert hits[0] < len(lines), "the main guard is the last line, so it defines no arm"

    # WITHOUT THIS THE LOOP BELOW IS VACUOUS on an all-None tuple: it would pass
    # having asserted nothing, where the pre-derivation form raised from max().
    # Green where the old code was LOUD is a coverage reduction, so it is pinned
    # rather than left to whoever next simplifies the tuple by hand.
    assert any(point is not None for point in TRUNCATIONS), (
        "every truncation point is None, so the arms below assert nothing at all"
    )

    for point in TRUNCATIONS:
        if point is None:
            continue
        assert point < hits[0], (
            f"truncation point {point} sits AT OR AFTER the main guard, so it would "
            "raise rather than exit 0 and the arm would refuse for the wrong reason"
        )
        assert gate_compiles(point), (
            f"the {point}-line prefix does not compile, so python would exit 1 and "
            "the arm would pass for a reason that is not the defect"
        )


@pytest.mark.parametrize("lines", TRUNCATIONS, ids=lambda value: f"lines={value}")
def test_a_truncated_gate_cannot_wave_a_forbidden_byte_through(
    tmp_path: Path, isolated: Environment, lines: int | None
) -> None:
    """The item, end to end: a gate that never ran must not pass a staged em dash.

    Every one of these COMMITTED before the repair, with exit 0 and completely
    empty stderr.
    """
    assert gate_compiles(lines), (
        f"the {lines}-line prefix does not compile, so python would exit 1 and "
        "this arm would pass for a reason that is not the defect"
    )
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    truncate_gate(box, lines)

    attempt = commit_attempt(box, content=EM_DASH_CONTENT)
    assert attempt.hook_output, (
        f"a gate truncated to {lines} lines was answered with NO hook output at "
        "all, which is the defect's own signature"
    )
    assert refused_as_unrun(attempt), (
        f"a gate truncated to {lines} lines did not refuse as unrun:\n{attempt.report}"
    )


@pytest.mark.parametrize("lines", TRUNCATIONS, ids=lambda value: f"lines={value}")
def test_a_truncated_gate_refuses_a_clean_commit_too(
    tmp_path: Path, isolated: Environment, lines: int | None
) -> None:
    """An unrun gate is not a passed gate, whatever was staged.

    THE ACCEPTED COST, stated rather than discovered later. While the gate is
    broken every commit is refused, including legitimate ones - the hook is SAFE,
    not USABLE, in that state. That is the same trade CS-819 records, and it is
    correct here for the same reason: the alternative is committing bytes nothing
    ever checked.
    """
    assert gate_compiles(lines), f"the {lines}-line prefix does not compile"
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    truncate_gate(box, lines)

    attempt = commit_attempt(box, content=CLEAN_CONTENT)
    assert refused_as_unrun(attempt), (
        f"a clean commit passed a gate truncated to {lines} lines, so the guard "
        f"is judging the CONTENT rather than whether the gate ran:\n{attempt.report}"
    )


def test_an_interpreter_that_cannot_run_a_file_is_refused_by_the_gate_guard(
    tmp_path: Path, isolated: Environment
) -> None:
    """SHAPE TWO: the probe passes honestly and the gate still never runs.

    THE PROBE CANNOT CATCH THIS AND IS NOT SUPPOSED TO. It validates the ``-c``
    invocation shape; the gate is invoked as a FILE. This wrapper delegates
    ``-c`` faithfully - so it prints the computed token AND returns 97 - and
    exits 0 on everything else. MEASURED on the tracked hook before this guard:
    the staged em dash COMMITTED, exit 0, HEAD moved, zero bytes of stderr.

    THE ATTRIBUTION MATTERS. The refusal must come from the GATE guard, not from
    the interpreter probe, because the probe is satisfied. An arm asserting only
    ``blocked`` would not be able to tell those apart.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    shim = write_shim(box.hooks.parent / "shims", "file-blind.sh", FILE_BLIND_SHIM)

    attempt = commit_attempt(box, content=EM_DASH_CONTENT, interpreter=shim.as_posix())
    assert attempt.hook_output, (
        "the file-blind interpreter was answered with NO hook output at all, "
        "which is the defect's own signature"
    )
    assert refused_as_unrun(attempt), (
        f"a file-blind interpreter was not refused by the gate guard:\n{attempt.report}"
    )
    assert not attempt.blocked_by_the_interpreter_check, (
        f"the PROBE refused this, so the arm is not measuring the gate guard and "
        f"the shim no longer answers the probe honestly:\n{attempt.report}"
    )


def test_an_intact_gate_still_blocks_by_its_own_rule(tmp_path: Path, isolated: Environment) -> None:
    """The regression control. The gate's own verdict must not be replaced by this guard.

    A guard that refused everything would pass every arm above and would have
    broken the hook completely. This pins that an intact gate still refuses an em
    dash BY ITS OWN RULE and NOT as unrun.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    attempt = commit_attempt(box, content=EM_DASH_CONTENT)
    assert attempt.blocked, f"an intact gate did not block an em dash:\n{attempt.report}"
    assert not refused_as_unrun(attempt), (
        f"an INTACT gate was reported as unrun, so the guard fires on a gate that "
        f"did run and the hook is broken:\n{attempt.report}"
    )


def test_an_intact_gate_still_accepts_a_clean_commit(tmp_path: Path, isolated: Environment) -> None:
    """The arm that proves the sandbox can say YES, and the LIVE half of the contract.

    THIS IS THE EXECUTABLE CONTRACT TEST. The hook demands the gate's success
    banner, so if the gate's banner text ever changed, this arm goes RED - a
    clean commit would be refused as unrun. The text arm below pins the same
    coupling statically; this one pins it against what the gate actually emits.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    attempt = commit_attempt(box, content=CLEAN_CONTENT)
    assert attempt.accepted, (
        f"a clean commit through an intact gate was refused, so the hook and the "
        f"gate no longer agree on the success banner:\n{attempt.report}"
    )


def test_the_gate_output_still_reaches_the_terminal(tmp_path: Path, isolated: Environment) -> None:
    """The capture must not SWALLOW what the operator used to see.

    CS-819 consumes its sentinel on purpose - it is noise. This is the opposite
    case: the gate's stdout carries the CS-209 coverage-skip lines, which exist
    to say a check's detection was REDUCED. Swallowing them would silence the one
    channel that reports a gap. Measured when the guard shipped: the accept path
    is SEQUENCE IDENTICAL to the pre-capture hook and the blocked path is
    identical as a MULTISET, with the skip lines moving after the gate's stderr.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    attempt, carried = commit_and_scan(box, content=CLEAN_CONTENT, literal=GATE_SUCCESS_HEAD)
    assert attempt.accepted, f"the clean commit was refused:\n{attempt.report}"
    assert carried, (
        "the gate's success banner never reached the terminal, so the capture "
        "swallowed the report the operator relies on"
    )


def test_the_hook_and_the_gate_agree_on_the_success_banner() -> None:
    """TWO SIDES, NEITHER RESTATED HERE. The static half of the contract.

    The gate declares what it WRITES and the hook declares what it REQUIRES.
    Both are extracted from their own files and matched against each other, so
    this arm cannot go green because a constant in a test agrees with neither.
    If an edit moved one side, EVERY commit would be refused with a message
    saying the gate did not run - loudly, but for an invented reason.
    """
    head, pattern = hook_head_and_pattern()
    rendered = gate_success_line(3, 1)

    assert rendered.startswith(head), (
        "the gate's rendered banner no longer begins with the head the hook declares"
    )
    assert fnmatch.fnmatchcase(rendered, pattern), (
        "the gate's rendered banner does not match the pattern the hook requires"
    )

    # THE NEGATIVE CONTROL. Without it this arm would pass against a pattern that
    # matched anything at all - an empty head, or a bare `*`, either of which
    # would silently reopen the fail-open.
    for mangled in (
        rendered + " and then some",
        "note: " + rendered,
        rendered.replace("0 blocking", "9 blocking"),
        rendered.replace("3 checked", "x checked"),
    ):
        assert not fnmatch.fnmatchcase(mangled, pattern), (
            f"the hook's pattern accepts a mangled banner, so it is not anchored: {mangled!r}"
        )


def test_the_gate_capture_is_a_plain_assignment_with_no_status_masking_prefix() -> None:
    """The single most dangerous way to get this wrong, pinned as a fence.

    ``export``, ``local`` and ``readonly`` in front of the capture each MASK
    ``$?`` to 0 in both bash and dash, which would make STATUS always 0 and
    silently restore the fail-open. A future edit that adds one fails here. Same
    fence as the commit-msg capture carries for CS-819, which had no pre-commit
    equivalent until this item.
    """
    raw = (HOOKS_DIR / PRE_COMMIT).read_bytes().decode("ascii")
    assert "\nCS_GATE_OUT=$(" in raw, "the capture is not a bare assignment at column zero"
    for prefix in ("export CS_GATE_OUT", "local CS_GATE_OUT", "readonly CS_GATE_OUT"):
        assert prefix not in raw, f"`{prefix}` masks $? to 0 and reopens CS-823"
    assert "\nSTATUS=$?\n" in raw, "the status is not captured immediately after the assignment"


def test_the_gate_spawns_no_child_that_could_inherit_the_captured_stdout() -> None:
    """The only thing standing between the capture and a HANG, pinned from this side.

    Command substitution waits for EOF ON THE PIPE rather than for the child to
    exit, so a gate that spawned a process holding stdout open would hang the
    hook instead of failing it - and a hung hook reads as a hung credential
    dialog rather than as a defect. Every ``subprocess.run`` in the gate passes
    ``capture_output`` today, so each child gets its own pipes. The gate is
    FROZEN and this arm changes nothing in it; it just refuses to let that
    property lapse silently.
    """
    tree = ast.parse(TRACKED_GATE.read_bytes())
    spawns = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("run", "Popen", "call", "check_output")
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    ]
    assert spawns, "no subprocess call found in the gate, so this locator is stale"
    for call in spawns:
        named = {keyword.arg for keyword in call.keywords}
        assert "capture_output" in named or "stdout" in named, (
            f"a subprocess call at gate line {call.lineno} does not redirect its "
            "child's stdout, so the child would inherit the hook's captured pipe "
            "and could hang the commit instead of failing it"
        )


def replace_gate(box: Sandbox, source: str) -> None:
    """Put a tiny synthetic gate in the sandbox's WORKING TREE. Index untouched.

    A hand-authored stub rather than a slice of the real gate, which is the rule
    for fixtures here. What each stub varies is ONE property of the gate's
    stdout, so an arm names the property it is measuring instead of measuring a
    truncation and hoping.
    """
    (box.work / "tools" / "precommit_gate.py").write_bytes(source.encode("ascii"))


def test_a_gate_that_talks_but_never_banners_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """NON-EMPTY stdout is not proof of execution. Exit 0, output, no banner.

    ADDED AFTER AN ADVERSARY REFUTED THE FIRST SUITE, and it is worth recording
    what got through rather than only that something did. THREE wrong hooks
    passed every other arm in this section: accept when the last line is
    non-empty, accept when the capture has a non-zero byte count, and accept
    when the last line merely starts with the gate's NAME. All three commit a
    staged em dash through a gate that checked nothing. This stub is what
    separates them from the shipped hook - it says something, it says it on
    stdout, it even opens with the gate's own name, and it never banners.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    replace_gate(box, 'print("precommit_gate: BLOCKED - 1 finding")\n')

    attempt = commit_attempt(box, content=EM_DASH_CONTENT)
    assert attempt.hook_output, (
        "a talking-but-bannerless gate was answered with NO hook output at all"
    )
    assert refused_as_unrun(attempt), (
        f"a gate that printed a non-banner line and exited 0 was accepted, so the "
        f"hook is judging that stdout is NON-EMPTY rather than what it says:\n{attempt.report}"
    )


def test_a_banner_that_is_not_the_last_line_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """LAST LINE, not anywhere. The arm the hook's own comment needs and lacked.

    THE COMMENT CLAIMED THIS AND NOTHING TESTED IT. `.githooks/pre-commit` says
    the check "is stronger than a plain search: a banner anywhere but the final
    line is refused". An adversary measured that sentence unbacked: a mutant
    that kept the declared pattern BYTE-IDENTICAL and only changed which line it
    was applied to - `grep -F "$CS_GATE_PASS" | tail -n 1` - passed every arm in
    this section, and so did a plain containment test. Neither has dead code and
    the first is what an ordinary "make it less brittle" edit looks like.

    The stub writes a WELL-FORMED banner and then one more line. A containment
    test finds the banner and accepts; a last-line test sees the trailing line
    and refuses. `gate_success_line` renders the banner from the gate's own
    format string, so this arm restates nothing.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    replace_gate(
        box,
        "print(%r)\n" % gate_success_line(1, 0)
        + 'print("precommit_gate: note - 3 units were skipped")\n',
    )

    attempt = commit_attempt(box, content=EM_DASH_CONTENT)
    assert attempt.hook_output, "a banner-then-trailer gate was answered with NO hook output"
    assert refused_as_unrun(attempt), (
        f"a banner that was NOT the last line was accepted, so the check is a "
        f"search rather than a last-line test:\n{attempt.report}"
    )
