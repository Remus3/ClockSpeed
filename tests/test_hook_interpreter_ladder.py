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
is asserted byte-identical to the tracked hook - pre-push EXCEPT its single CS-824
floor line, rewritten to a test-local value by ``tests/pre_push_floor.py`` - so the
isolation costs no fidelity.

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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.git_env import scrub
from tests.pre_push_floor import differs_only_on_floor_line, wired_hook_bytes

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

# CS-814: the refusal renders NONE of the candidate's output, only its byte count
# in this form. The cap bounds every refusal line, with slack for the indent.
OBSERVED_COUNT: Final = re.compile(re.escape(OBSERVED_OUTPUT) + r": \[([0-9]+)\] bytes")
OBSERVED_CAP: Final = 200
OBSERVED_SLACK: Final = 80

# A candidate that ignores its arguments and floods stdout, so a refusal that
# rendered its output would have something to flood with. 40 characters, 40
# times, with no trailing newline.
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


# CS-818's seam: the resolution ladder between two comment-only markers. The
# only lines inside it allowed to differ per hook are the two closing-voice
# lines, the same per-hook tail refusal_block drops.
MARKED_LADDER_BEGIN: Final = b"# >>> CS-818 LADDER BEGIN"
MARKED_LADDER_END: Final = b"# <<< CS-818 LADDER END\n"
MARKED_LADDER_RUNGS: Final = (
    b'if [ -n "${CLOCKSPEED_PYTHON:-}" ]; then',
    b"elif cs_probe python; then",
    b"elif cs_probe python3; then",
    b"elif cs_probe py -3; then",
)
MARKED_LADDER_VOICE_LINES: Final = 2
MARKED_LADDER_VOICE: Final = re.compile(rb'^\s+"The (commit|push) is BLOCKED: ')


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
    # CS-968: scrubbed FIRST. A push from a worktree exports GIT_DIR, and a
    # sandbox that inherits it builds itself in the real repository.
    env = scrub(dict(os.environ))
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
    # CS-824: pre-push gets the one-line test floor; the other hooks are verbatim.
    installed.write_bytes(wired_hook_bytes(hook, (HOOKS_DIR / hook).read_bytes()))
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
    """Without this, every arm below could be grading a copy that drifted.

    Byte-identical EXCEPT the single CS-824 floor line of pre-push, which the
    ruling rewrites to a test-local value. For pre-push the arm asserts both that
    the copy is exactly the helper's output and that it differs from the tracked
    hook on that one line only, so any other drift is still red.
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    copied = (box.hooks / hook).read_bytes()
    tracked = (HOOKS_DIR / hook).read_bytes()
    assert copied == wired_hook_bytes(hook, tracked), (
        "the sandbox hook is not the tracked hook, so nothing below grades the real file"
    )
    if hook == PRE_PUSH:
        assert differs_only_on_floor_line(copied, tracked), (
            "the sandbox pre-push differs from the tracked hook beyond the CS-824 floor line"
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

    # CS-816 grant condition 5: the MARKED LADDER is pinned too, because CS-818
    # executes it and tools/claude_hook.sh carries it. Each marker must occur
    # exactly once, the region must hold the whole four-rung chain, and exactly
    # the two per-hook closing-voice lines are excluded before comparing.
    ladders: dict[str, bytes] = {}
    for hook in HOOK_NAMES:
        raw = (HOOKS_DIR / hook).read_bytes()
        assert raw.count(MARKED_LADDER_BEGIN) == 1, f"{hook} carries no single ladder BEGIN marker"
        assert raw.count(MARKED_LADDER_END) == 1, f"{hook} carries no single ladder END marker"
        region = raw[
            raw.index(MARKED_LADDER_BEGIN) : raw.index(MARKED_LADDER_END) + len(MARKED_LADDER_END)
        ]
        for rung in MARKED_LADDER_RUNGS:
            assert rung in region, f"{hook}'s marked ladder is missing a rung"
        lines = region.split(b"\n")
        voiced = [line for line in lines if MARKED_LADDER_VOICE.match(line)]
        assert len(voiced) == MARKED_LADDER_VOICE_LINES, (
            f"{hook}'s ladder has {len(voiced)} closing-voice lines, "
            f"not {MARKED_LADDER_VOICE_LINES}"
        )
        ladders[hook] = b"\n".join(line for line in lines if not MARKED_LADDER_VOICE.match(line))
    split = sorted(hook for hook, block in ladders.items() if block != ladders[PRE_COMMIT])
    assert not split, f"the marked ladder is not byte-identical across the hooks: {split}"


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
def test_the_refusal_counts_the_observed_output_and_withholds_it(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """Condition 4's other half, re-pinned by CS-814: the size, never the content.

    ``echo`` re-emits the probe program, so its observed output carries a fragment
    no other part of the message contains. The refusal must report a non-zero byte
    count for it AND must not contain that fragment: a candidate that ignores its
    arguments can print the hook's environment, so its output is never rendered
    (CLAUDE.md non-negotiable 13).
    """
    box = make_sandbox(tmp_path, isolated, hook, suite_passes=True)
    outcome = clean_attempt(box, "echo")
    assert outcome.blocked_by_the_interpreter_check, (
        f"{hook}: expected a refusal:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    counted = OBSERVED_COUNT.search(rendered)
    assert counted is not None, (
        f"{hook}: the refusal does not report the observed byte count:\n{outcome.report}"
    )
    assert int(counted.group(1)) > 0, f"{hook}: the refusal counted no bytes:\n{outcome.report}"
    assert "sys.stdout.write" not in rendered, (
        f"{hook}: the refusal rendered what the candidate printed:\n{outcome.report}"
    )


@pytest.mark.parametrize("hook", HOOK_NAMES)
def test_a_chatty_candidate_cannot_flood_the_terminal(
    tmp_path: Path, isolated: Environment, hook: str
) -> None:
    """No refusal line can be flooded, measured rather than assumed, on every hook.

    A candidate that ignores its arguments is free to print without limit. Before
    CS-814 the refusal quoted it through a 200-character cap; since CS-814 it
    renders none of it, only its byte count. The shim emits 1600 characters on
    one line: no refusal line may carry any of them, and the count must be all
    1600.

    PARAMETRIZED FOR THE SAME REASON AS THE ARM ABOVE. Removing the old cap from
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
    quoting = sum(1 for line in outcome.hook_output if CHATTY_MARKER in line)
    assert quoting == 0, f"{hook}: {quoting} refusal line(s) quote the candidate's output"
    longest = max((len(line) for line in outcome.hook_output), default=0)
    assert longest <= OBSERVED_CAP + OBSERVED_SLACK, (
        f"{hook}: a refusal line is {longest} characters long"
    )
    counted = OBSERVED_COUNT.search("\n".join(outcome.hook_output))
    total = int(counted.group(1)) if counted else -1
    assert total == len(CHATTY_MARKER) * CHATTY_REPEATS, (
        f"{hook}: the refusal counted {total} bytes of the candidate's output"
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
    wrapper. The refusal must report the exit-status half as REACHED - the liar's
    dropped status, 0, rather than "not reached" - which is only possible if the
    stdout half PASSED. Since CS-814 the output itself is never rendered, so the
    byte count standing in for it must equal the token's length.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    liar = write_shim(box.hooks.parent / "shims", "liar.sh", LIAR_SHIM)

    outcome = commit_attempt(box, interpreter=str(liar))
    assert outcome.blocked_by_the_interpreter_check, (
        f"the liar was accepted as an interpreter:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    assert EXIT_STATUS_LABEL + " when asked to fail: [0]" in rendered, (
        "the refusal does not report the exit-status half as reached, so the stdout half "
        f"did not pass and this is not the exit-code refusal:\n{outcome.report}"
    )
    counted = OBSERVED_COUNT.search(rendered)
    total = int(counted.group(1)) if counted else -1
    assert total == len(PROBE_ANSWER), (
        f"the refusal counted {total} bytes, not the answer's {len(PROBE_ANSWER)}"
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
    assert b"$cs_probe_bytes" in block, (
        "the extracted refusal does not render the BYTE COUNT of the observed output"
    )
    assert b"$cs_probe_out" not in block, (
        "the extracted refusal renders the observed output itself (CS-814)"
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
    than to the answer being absent. Since CS-814 the output itself is never
    rendered, so that proof is the byte count: exactly the prefix plus the answer.
    """
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    noisy = write_shim(box.hooks.parent / "shims", "noisy.sh", NOISY_SHIM)
    noise = "sitecustomize noise "
    assert "printf '" + noise + "'" in NOISY_SHIM, "the noise prefix no longer matches the shim"

    outcome = commit_attempt(box, interpreter=str(noisy))
    assert outcome.blocked_by_the_interpreter_check, (
        f"output merely CONTAINING the answer was accepted:\n{outcome.report}"
    )
    rendered = "\n".join(outcome.hook_output)
    counted = OBSERVED_COUNT.search(rendered)
    total = int(counted.group(1)) if counted else -1
    assert total == len(noise) + len(PROBE_ANSWER), (
        f"the refusal counted {total} bytes, not the prefix plus the answer, so this arm is "
        "not measuring exactness at all"
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
# NO ARM HERE CARRIES THE PROOF WITHOUT A SHELL, AND THIS COMMENT USED TO SAY
# OTHERWISE. It claimed `test_a_silent_interpreter_...` below proved the property
# shell-independently and ran everywhere. MEASURED FALSE TWICE, by two adversaries
# that wrote none of this module. A real defect planted in a COPY of the hook - a
# stdout leak before the final exit - left that arm PASSING, because it installs a
# silent stub as the interpreter so the hook's own program never executes and no
# defect inside it is observable. And with a broken `sh` first on PATH that same
# arm FAILED, so it does not run everywhere either.
#
# WHAT IS TRUE: where no shell resolves, these arms DO NOT RUN, and this module
# claims nothing about whether anything else covers what they would have graded.
# Nothing in this harness can check such a claim, which is why the skip reasons
# refuse to make one and why a citation in a skip reason is now refused outright.
# A skip is not a pass (docs/LEDGER.md CS-428) - it is a stated gap, and a stated
# gap is evidence where a false reassurance is worse than silence.

SENTINEL: Final = "clockspeed-commit-msg-ran"
SENTINEL_REFUSAL: Final = "DID NOT RUN"

# The two shells this section can reach for, each named ONCE so a resolution
# and the skip reason that explains its absence cannot drift apart.
DASH_NAME: Final = "dash"
DEFAULT_SHELL_NAME: Final = "sh"

DASH: Final = shutil.which(DASH_NAME)
DEFAULT_SHELL: Final = shutil.which(DEFAULT_SHELL_NAME)

# The phrase every skip in this module opens with, owned here rather than
# retyped, so an arm added later cannot quietly ship a reason that lets a
# reader count a skip as a pass (docs/LEDGER.md CS-428).
NOT_RUN_MARKER: Final = "NOT RUN, NOT PASSED"

# The phrase a shell-dependent skip names its requirement with. The arm at the
# foot of this module asserts every such reason carries it.
SHELL_REQUIREMENT: Final = "requires an executable named"

# The phrase an arm names a BUILD requirement with, for the one skip whose
# requirement is a behaviour of a resolvable executable rather than its presence.
BUILD_REQUIREMENT: Final = "requires a build of"

# WHAT EVERY SKIP REASON SAYS INSTEAD OF NAMING A COVERING ARM. It asserts
# nothing this harness cannot check, in either direction - it does not claim the
# property is covered elsewhere, and it does not claim it is not.
UNCOVERED: Final = (
    "This reason makes NO claim about whether anything else covers the property; "
    "nothing here can check such a claim (CS-839). Read the arm as NOT RUN, never "
    "as covered."
)


def shell_requirement(executable: str) -> str:
    """Render the skip reason for an arm that cannot run without ``executable``.

    IT NAMES WHAT IT REQUIRES AND STOPS THERE. The first version closed by
    saying the property was proven shell-independently by a named arm. That
    sentence was MEASURED FALSE: a stdout leak planted in a COPY of the
    commit-msg hook left the cited arm GREEN while the defect was live, because
    that arm installs a silent stub as the interpreter and so never executes the
    hook's inline program at all. An honest gap is evidence; a false reassurance
    is worse than silence, because it makes a false green read as a considered
    one.
    """
    return (
        f"{NOT_RUN_MARKER}: this arm {SHELL_REQUIREMENT} `{executable}`, resolvable "
        "through shutil.which on the PATH of the interpreter that imported this "
        "module. WHICH SHELL INVOKED PYTEST decides whether that resolution "
        "succeeds, so an absence here is a harness artifact and not a broken "
        f"machine (CS-839). {UNCOVERED}"
    )


DEFAULT_SHELL_SKIP: Final = shell_requirement(DEFAULT_SHELL_NAME)
DASH_ABSENT_SKIP: Final = shell_requirement(DASH_NAME)

# A dash that RESOLVED and then would not answer. This is the third verdict
# class - present but not working - and before it was named the arms below ran
# against it and failed with text about the machine, which is the exact shape
# this item was filed against.
DASH_UNUSABLE_SKIP: Final = (
    f"{NOT_RUN_MARKER}: this arm {SHELL_REQUIREMENT} `{DASH_NAME}` that can actually "
    "RUN. The one on this machine RESOLVED and then did not answer the delivery "
    "probe - it failed to exec, exited non-zero, or could not find the counter the "
    "probe pipes into - so its behaviour above the heredoc threshold is unmeasured "
    f"and no branch here can be selected honestly. {UNCOVERED}"
)


def dash_usability_skip() -> str:
    """Why an arm needing a WORKING dash did not run - absent, or present and mute."""
    if DASH is None:
        return DASH_ABSENT_SKIP
    return DASH_UNUSABLE_SKIP


def dash_truncation_skip() -> str:
    """Why the MSYS2 truncation arm did not run, branch by branch.

    THE REASON IS COMPUTED, NOT WRITTEN ONCE FOR THREE BRANCHES. The single
    reason this replaced described a DELIVERING dash and rendered
    ``DASH_DELIVERED`` into itself, so on a machine with no dash at all it
    reported that this machine's dash delivers an over-threshold heredoc of
    ``None`` bytes - which names nothing the arm requires and states something
    about the machine that is not true. MEASURED under PowerShell before the
    repair; each branch now says only what was actually observed.

    THE THIRD BRANCH NAMES A BUILD, NOT AN EXECUTABLE, and that is the honest
    wording rather than a dodge: on a machine whose dash resolves and answers,
    what this arm still lacks is a build that TRUNCATES.
    """
    if not DASH_USABLE:
        return dash_usability_skip()
    return (
        f"{NOT_RUN_MARKER}: this arm {BUILD_REQUIREMENT} `{DASH_NAME}` that TRUNCATES an "
        f"over-threshold heredoc; the one on this machine DELIVERS ({DASH_DELIVERED} "
        f"bytes), so the MSYS2 truncation cannot be reproduced here. {UNCOVERED}"
    )


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

# PRESENT IS NOT USABLE, and conflating the two was a false-green risk. The
# probe above returns None when dash cannot exec, exits non-zero, or when the
# counter it pipes into is missing - so a fully resolvable dash that merely
# ERRORS made `DASH_TRUNCATES` false and skipped the truncation arm under a
# reason about delivery, while the other dash arm ran anyway and failed. This
# is the one predicate that separates the two.
DASH_USABLE: Final = DASH is not None and DASH_DELIVERED is not None


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


@pytest.mark.skipif(DEFAULT_SHELL is None, reason=DEFAULT_SHELL_SKIP)
def test_the_success_path_leaks_no_stdout_and_still_reports_on_stderr(
    tmp_path: Path, isolated: Environment
) -> None:
    """The sentinel must be CONSUMED, not printed at git.

    Command substitution swallows the program's stdout, so the sentinel never
    reaches the terminal. This asserts both halves: nothing on stdout for a
    legitimate message, and the rejection text still arriving on stderr for a bad
    one - the capture must not have swallowed the diagnostics too.
    """
    assert DEFAULT_SHELL is not None
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


@pytest.mark.skipif(DEFAULT_SHELL is None, reason=DEFAULT_SHELL_SKIP)
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
    assert DEFAULT_SHELL is not None
    code, out, err = run_commit_msg_under(DEFAULT_SHELL, tmp_path, isolated.variables, message)
    assert code != 0, f"{label} was accepted"
    assert out == b"", f"{label} leaked stdout"
    assert reason.encode("ascii") in err, f"{label} did not report its own reason on stderr"
    assert SENTINEL_REFUSAL.encode("ascii") not in err, (
        f"{label} was refused by the sentinel rather than by its own rule, so the "
        "check program did not run"
    )


@pytest.mark.skipif(not DASH_USABLE or not DASH_TRUNCATES, reason=dash_truncation_skip())
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


@pytest.mark.skipif(not DASH_USABLE, reason=dash_usability_skip())
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


# --- CS-839: a shell resolved at IMPORT time must SKIP, never assert ---------
#
# THE DEFECT, MEASURED ON ONE COMMIT UNDER TWO SHELLS. `DASH` and
# `DEFAULT_SHELL` above are resolved from the invoking interpreter's PATH at
# IMPORT time. Git Bash carries both; PowerShell's PATH carries neither. The two
# `sh` arms used to assert `DEFAULT_SHELL is not None` with the message `no
# /bin/sh on this machine`, so the SAME TREE was green under one shell and red
# under the other - and the red named a MISSING SHELL, which reads as a broken
# machine rather than as a harness artifact. An agent or an operator checking
# their work from the wrong shell hunts a regression that is not there; the
# reverse is worse, because a green run then proves less than it appears to.
#
# WHY A DECLARED SKIP AND NOT A WIDER PATH. Putting the missing directory on
# PATH makes the two measurements agree by changing the MACHINE rather than the
# property, and leaves the next machine to rediscover it. This section already
# declared a skip criterion for `dash` for exactly that reason - a skip is not a
# pass (docs/LEDGER.md CS-428) - and the `sh` arms were the two that escaped the
# discipline the rest of the section already followed.
#
# THE HALF THAT IS NOT THE ONE-LINE FIX. Turning two asserts into two skips
# repairs the INSTANCE. The arm below repairs the POPULATION: it DERIVES, from
# this module's own syntax tree, every name that depends on a shell resolved at
# import time - the constants, anything computed from them, and every arm that
# reads either - re-runs exactly the arms among them in a child interpreter that
# cannot resolve those shells, and reddens if any one reports a FAILURE instead
# of a skip, or a skip whose reason does not name what it requires. That
# derivation is what found the two dash arms as well as the two named in the
# item: their skip reason interpolated an unresolved value and told a machine
# with no dash at all that its dash DELIVERS.
#
# THE ARM IS SHELL-INDEPENDENT ITSELF, DELIBERATELY. The child gets no narrowed
# PATH; `shutil.which` is stubbed to refuse the derived names. So it reproduces
# the PowerShell condition while running under Git Bash, under PowerShell and
# under CI alike. A guard that only reddened under the shell that happens to
# have the defect would be the same one-toolchain evidence this item exists to
# end.
#
# WHAT A SKIP REASON MAY NOT SAY, AND THIS WAS MEASURED RATHER THAN REASONED.
# The first version of these reasons closed by naming an arm that "proves the
# property shell-independently". An adversary planted a stdout leak in a COPY of
# the commit-msg hook and measured the cited arm GREEN with the defect live: it
# installs a silent stub as the interpreter, so the hook's inline program never
# executes and no defect inside it is observable. The skip did not reduce
# coverage - before the repair the same arms asserted and died on that shell
# without detecting it either. The SENTENCE did the damage, by making a false
# green readable as a considered one. So a reason may name WHAT IT REQUIRES and
# must stop there, and the arm below refuses any reason that names a test at
# all. It does NOT check coverage and must not grow into something that tries.
#
# THE THIRD VERDICT CLASS, AND ONLY HALF OF IT IS HANDLED - THE OTHER HALF IS
# RECORDED, NOT FIXED. A shell that RESOLVES BUT DOES NOT WORK is neither of the
# two cases above: the arm runs and fails with text about the machine, which is
# the exact shape this item was filed against. For dash it is now handled, and
# for free, because `_dash_heredoc_delivery` already has to RUN dash to answer -
# so a dash that resolves and then cannot exec, exits non-zero, or lacks the
# counter the probe pipes into yields no measurement, `DASH_USABLE` is false,
# and both dash arms skip naming what they require. Demonstrated with a `dash`
# on PATH that exits 1. For `sh` it is NOT handled, and that is a JUDGEMENT
# rather than a measurement: a broken `sh` also breaks every sandbox arm in this
# module, since real git runs hooks through one, so it is a genuinely broken
# machine rather than a harness artifact - and probing it would add an
# import-time subprocess under every shell to cover a case nothing else in this
# module survives either.

PLUGIN_NAME: Final = "cs839_no_shell"
HIDDEN_ENV: Final = "CS839_HIDDEN"
REPORT_ENV: Final = "CS839_REPORT"
CONTROL_MODULE: Final = "test_cs839_control.py"
CHILD_TIMEOUT: Final = 300
WITHHELD_TEXT: Final = "<withheld: the text carried a filesystem path>"

# Ranked so a node id reported across several phases reduces to ONE outcome the
# way pytest's own summary reduces it: a failure anywhere wins, then a skip.
OUTCOME_RANK: Final = {"passed": 0, "skipped": 1, "failed": 2}

# Any test a skip reason names. The arm below refuses ALL of them: a citation in
# a skip reason is a coverage claim, and this harness can check that a name
# EXISTS but never that the arm it names COVERS anything. One such claim shipped
# and was measured false, so the fence is on making the claim, not on its spelling.
CITED_TEST: Final = re.compile(r"\btest_[A-Za-z0-9_]+")

NO_SHELL_PLUGIN: Final = '''"""Hide named executables from shutil.which, and record outcomes.

Loaded with ``-p`` so it is installed BEFORE collection, which is when the
module under test resolves its shells. Generated by, and meaningful only to,
tests/test_hook_interpreter_ladder.py.
"""

import json
import os
import shutil

_REAL_WHICH = shutil.which
_HIDDEN = frozenset(json.loads(os.environ["%(hidden)s"]))
_REPORT = os.environ["%(report)s"]


def _which(cmd, *args, **kwargs):
    """Refuse the hidden names, and defer to the real resolver for everything else."""
    if cmd in _HIDDEN:
        return None
    return _REAL_WHICH(cmd, *args, **kwargs)


shutil.which = _which


def pytest_runtest_logreport(report):
    """Append one JSON record per phase, so the parent reads outcomes not text."""
    longrepr = report.longrepr
    if isinstance(longrepr, tuple):
        reason = str(longrepr[2])
    elif longrepr is None:
        reason = ""
    else:
        reason = str(longrepr)
    record = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
        "reason": reason,
    }
    with open(_REPORT, "a", encoding="ascii", errors="backslashreplace") as handle:
        print(json.dumps(record), file=handle)
'''

CONTROL_HEAD: Final = '''"""The CS-839 defect in miniature - this guard's control arm.

Each arm below reproduces the exact pre-repair shape: a shell resolved at IMPORT
time and a bare assert on it, carrying the message the repaired arms used to
carry. If the stub did not land, every arm here PASSES and the guard reddens for
that instead - which is what stops the guard from being satisfied by a child that
quietly resolved its shells after all.
"""

import shutil
'''

CONTROL_ARM: Final = '''

SHELL_%(index)d = shutil.which(%(executable)r)


def test_the_control_asserts_on_shell_%(index)d():
    """Fail exactly the way the arms under test used to fail."""
    assert SHELL_%(index)d is not None, "no /bin/sh on this machine"
'''


class ChildOutcome(NamedTuple):
    """One test's reduced outcome in a child run, with any path text withheld."""

    nodeid: str
    outcome: str
    reason: str


def module_tree() -> ast.Module:
    """This module's own syntax tree, read as bytes and decoded as ASCII."""
    return ast.parse(Path(__file__).resolve().read_bytes().decode("ascii"))


def module_assignments(tree: ast.Module) -> list[tuple[list[str], ast.expr]]:
    """Every module-level assignment, as its target names and its value."""
    found: list[tuple[list[str], ast.expr]] = []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            found.append(([node.target.id], node.value))
        elif isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if names:
                found.append((names, node.value))
    return found


def module_string_literals(tree: ast.Module) -> dict[str, str]:
    """Every module-level name bound to a plain string, for indirect which() arguments."""
    literals: dict[str, str] = {}
    for names, value in module_assignments(tree):
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            for name in names:
                literals[name] = value.value
    return literals


def names_read_in(node: ast.AST) -> set[str]:
    """Every bare name the sub-tree reads, which is how dependence travels here."""
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def which_arguments(node: ast.AST, literals: dict[str, str]) -> set[str]:
    """The executable names a sub-tree hands to shutil.which, literal or by constant."""
    found: set[str] = set()
    for item in ast.walk(node):
        if not isinstance(item, ast.Call):
            continue
        function = item.func
        if not isinstance(function, ast.Attribute) or function.attr != "which" or not item.args:
            continue
        argument = item.args[0]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            found.add(argument.value)
        elif isinstance(argument, ast.Name) and argument.id in literals:
            found.add(literals[argument.id])
    return found


def shell_dependence(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Derive the required executables and every name that depends on one.

    THE POPULATION IS DERIVED, NEVER LISTED. The roots are every module-level
    name resolved through ``shutil.which`` and every module-level function that
    calls it. The closure then follows ordinary name reads - through the
    functions that read a root and the constants computed from those functions -
    until it stops growing, so a sibling constant resolved the same way and an
    arm that reads either are both caught with nobody maintaining a list.
    """
    literals = module_string_literals(tree)
    required: set[str] = set()
    dependent: set[str] = set()
    for names, value in module_assignments(tree):
        arguments = which_arguments(value, literals)
        if arguments:
            required |= arguments
            dependent |= set(names)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            arguments = which_arguments(node, literals)
            if arguments:
                required |= arguments
                dependent.add(node.name)
    growing = True
    while growing:
        growing = False
        for node in tree.body:
            if (
                isinstance(node, ast.FunctionDef)
                and node.name not in dependent
                and names_read_in(node) & dependent
            ):
                dependent.add(node.name)
                growing = True
        for names, value in module_assignments(tree):
            if names_read_in(value) & dependent and not set(names) <= dependent:
                dependent |= set(names)
                growing = True
    return required, dependent


def withhold(text: str) -> str:
    """Replace any text carrying a filesystem path, which must never be asserted on."""
    return WITHHELD_TEXT if DRIVE_PATH.search(text) else text


def write_child_plugin(directory: Path) -> None:
    """Write the stub-and-record plugin the child loads with ``-p``."""
    source = NO_SHELL_PLUGIN % {"hidden": HIDDEN_ENV, "report": REPORT_ENV}
    (directory / (PLUGIN_NAME + ".py")).write_bytes(source.encode("ascii"))


def write_control_module(directory: Path, executables: tuple[str, ...]) -> None:
    """Write one control arm per executable the derivation says is required."""
    body = CONTROL_HEAD
    for index, executable in enumerate(executables):
        body += CONTROL_ARM % {"index": index, "executable": executable}
    (directory / CONTROL_MODULE).write_bytes(body.encode("ascii"))


def read_child_outcomes(report: Path) -> tuple[ChildOutcome, ...]:
    """Reduce the child's per-phase records to one outcome per node id."""
    if not report.exists():
        return ()
    best: dict[str, tuple[int, str, str]] = {}
    for line in report.read_bytes().decode("ascii", "replace").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        rank = OUTCOME_RANK.get(record["outcome"], max(OUTCOME_RANK.values()))
        current = best.get(record["nodeid"])
        if current is None or rank > current[0]:
            best[record["nodeid"]] = (rank, record["outcome"], withhold(record["reason"]))
    return tuple(ChildOutcome(nodeid, entry[1], entry[2]) for nodeid, entry in sorted(best.items()))


def run_child_pytest(
    plugin_directory: Path,
    report: Path,
    hidden: tuple[str, ...],
    cwd: Path,
    *arguments: str,
) -> tuple[ChildOutcome, ...]:
    """Run pytest in a child that cannot resolve ``hidden``, and read its outcomes.

    THE CHILD'S PATH IS UNTOUCHED, deliberately. Only ``shutil.which`` is
    stubbed, so this reproduces the unresolvable-shell condition under ANY
    invoking shell rather than only under the one that happens to have it.
    """
    # CS-968: a NESTED pytest inherits this environment, and everything it runs
    # inherits it in turn - so an unscrubbed GIT_DIR reaches every git call in
    # the child suite, not just the ones in this module.
    env = scrub(dict(os.environ))
    for name in ("PYTEST_ADDOPTS", "PYTEST_CURRENT_TEST", "PYTEST_DEBUG_TEMPROOT"):
        env.pop(name, None)
    env["PYTHONPATH"] = str(plugin_directory)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env[HIDDEN_ENV] = json.dumps(sorted(hidden))
    env[REPORT_ENV] = str(report)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            PLUGIN_NAME,
            "-p",
            "no:cacheprovider",
            "--tb=no",
            "-q",
            *arguments,
        ],
        cwd=str(cwd),
        capture_output=True,
        timeout=CHILD_TIMEOUT,
        check=False,
        env=env,
    )
    return read_child_outcomes(report)


def test_no_arm_needing_an_import_time_shell_fails_when_it_cannot_be_resolved(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """CS-839's second half - the POPULATION, not the two arms that were caught.

    Converting an assert into a skip repairs one instance. This derives EVERY
    name in this module that depends on a shell resolved at import time, re-runs
    exactly the arms among them in a child that cannot resolve those shells, and
    reddens if any one of them reports a FAILURE instead of a skip, or a skip
    whose reason does not name what it requires.

    THE CONTROL RUNS FIRST AND IS NOT OPTIONAL. A child that quietly resolved
    its shells after all, or a harness that could not see a failure, would make
    every assertion below pass while measuring nothing. The control is the
    pre-repair shape itself, and it must FAIL.
    """
    tree = module_tree()
    required, dependent = shell_dependence(tree)
    population = {name for name in dependent if name.startswith("test_")}

    assert required, "no module-level shutil.which() resolution was derived - the scan is broken"
    assert population, "no arm was derived as depending on a shell resolved at import time"
    assert request.function.__name__ not in population, (
        "this arm derived ITSELF into the population, which would make the child run recurse"
    )

    plugin_directory = tmp_path / "plugin"
    plugin_directory.mkdir()
    write_child_plugin(plugin_directory)
    hidden = tuple(sorted(required))

    control_directory = tmp_path / "control"
    control_directory.mkdir()
    write_control_module(control_directory, hidden)
    control = run_child_pytest(
        plugin_directory, tmp_path / "control.jsonl", hidden, control_directory, CONTROL_MODULE
    )
    assert len(control) == len(hidden), (
        f"the control run reported {len(control)} arms for {len(hidden)} hidden executables, "
        "so this harness did not run what it believes it ran"
    )
    surviving = sorted(item.nodeid for item in control if item.outcome != "failed")
    assert not surviving, (
        "the control did NOT fail, so either the child resolved the executables after all or "
        "this harness cannot see a failure - every assertion below would be vacuous:\n"
        + "\n".join(surviving)
    )

    observed = run_child_pytest(
        plugin_directory,
        tmp_path / "population.jsonl",
        hidden,
        REPO_ROOT,
        Path(__file__).resolve().relative_to(REPO_ROOT).as_posix(),
        "-k",
        " or ".join(sorted(population)),
    )
    reached = {item.nodeid.split("::")[-1].split("[")[0] for item in observed}
    assert reached == population, (
        "the child did not reach every derived arm, so this proves nothing about the ones it "
        f"missed: derived {sorted(population)}, reached {sorted(reached)}"
    )

    failed = sorted(item.nodeid for item in observed if item.outcome == "failed")
    assert not failed, (
        "these arms FAILED instead of SKIPPING when the shell could not be resolved. That is "
        "CS-839 itself: a harness artifact rendered as a broken machine, and it makes this "
        "suite's verdict depend on which shell invoked it:\n" + "\n".join(failed)
    )
    ran = sorted(item.nodeid for item in observed if item.outcome == "passed")
    assert not ran, (
        "these arms PASSED with their shells hidden, so they do not depend on one after all "
        "and the derivation above is over-broad:\n" + "\n".join(ran)
    )

    for item in observed:
        assert NOT_RUN_MARKER in item.reason, (
            f"{item.nodeid} skipped without saying that a skip is not a pass, so a reader "
            f"counting green cannot tell it never ran:\n{item.reason}"
        )
        assert SHELL_REQUIREMENT in item.reason, (
            f"{item.nodeid} skipped without naming what it requires, which is the whole of "
            f"CS-839's second route - a skip that says why is evidence:\n{item.reason}"
        )
        assert "None" not in item.reason, (
            f"{item.nodeid} rendered an unresolved value into its own skip reason, so the "
            f"reason states something about this machine that is not true:\n{item.reason}"
        )
        cited = sorted(set(CITED_TEST.findall(item.reason)))
        assert not cited, (
            f"{item.nodeid} names another test in its skip reason. A citation there is a "
            "COVERAGE CLAIM, and nothing in this harness can check that the cited arm covers "
            "anything - the one such claim that shipped was measured FALSE, and a false "
            f"reassurance is worse than silence: {cited}"
        )


# --- CS-906 conditions EIGHT and TWELVE: the parallel path -------------------
#
# WHAT THESE ARMS ARE FOR. The pre-push hook is gaining a second way to run the
# same suite: when pytest-xdist is importable the run is distributed, and when it
# is not the run degrades to serial with a notice. The suite is NEVER re-run -
# try-parallel-then-retry-serial would double a 24 minute push on the exact day
# it is already failing - so there is no second attempt to hide a broken first
# one, and every property the serial path had must hold on the parallel one by
# construction rather than by luck.
#
# THE THREE ARMS BELOW DO NOT SHARE A RESULT. Condition TWELVE says agreement
# between the two paths is not evidence, so the serial arm reads nothing the
# parallel arm measured and each carries its own control. Two paths that agree
# because both are inert agree perfectly.
#
# EVERY ORACLE IS READ OUT OF THE CHILD, not inferred from the push. A refusing
# hook always exits 1 - ``die`` says so - so the push's own exit code cannot
# distinguish "pytest returned 5" from "pytest was never runnable", and a hook
# that never passed a parallel option is indistinguishable from one that did.
# The sandbox suite therefore carries a conftest that records, from inside the
# pytest process the hook launched, whether the run was distributed, whether
# xdist was importable to it, and what exit status the session actually reached.
#
# EVERYTHING CS-906 ADDS IS APPENDED BELOW THE LAST ARM, AND NOTHING ABOVE MOVES.
# Two documentation pins are anchored at LINE NUMBERS in this module, one of them
# at line 122, and tests/test_docs_citations.py turns red the moment a line
# shifts under either. Measured: one inserted import at the top and an eight-line
# docstring at push_attempt broke both pins at once, in two files no slice here
# may write. That constraint is why the helper below asks whether xdist is
# importable with a builtin rather than a new import, and why the environment
# override arrives through Sandbox._replace rather than a new parameter.

XDIST_MODULE: Final = "xdist"


def xdist_installed() -> bool:
    """Whether pytest-xdist can be imported here.

    ``importlib.util.find_spec`` is the ordinary way to ask and would cost one
    more line at the top of this file. See the note above for why that line is
    not free. ``__import__`` is a builtin, so this asks the same question from
    down here.

    ONLY ``ImportError`` IS CAUGHT. An xdist that is installed but raises
    something else on import is a broken toolchain, and it should surface as a
    collection error rather than as three arms quietly skipping.
    """
    try:
        __import__(XDIST_MODULE)
    except ImportError:
        return False
    return True


XDIST_INSTALLED: Final = xdist_installed()
XDIST_SKIP: Final = (
    "pytest-xdist is not installed here, so the parallel path cannot be driven at all. "
    "A skip is NOT a pass: nothing below ran."
)

# Where the sandbox conftest leaves its records, relative to the sandbox work
# tree. Outside the suite directory on purpose - inside it, every arm would pay
# for pytest scanning a directory that grows one file per worker.
PROBE_DIR_NAME: Final = "xdist-probe"
SHIM_DIR_NAME: Final = "no-xdist"
SANDBOX_TESTS: Final = "tests"
SANDBOX_SUITE: Final = "test_sandbox_arm.py"
SANDBOX_CONFTEST: Final = "conftest.py"

PYTHONPATH_ENV: Final = "PYTHONPATH"
AUTOLOAD_ENV: Final = "PYTEST_DISABLE_PLUGIN_AUTOLOAD"

# Bounded like every other subprocess here. The child is one import.
PROBE_TIMEOUT: Final = 60
# What ``import_xdist_exit`` reports when the interpreter could not be started at
# all. Not 0, because 0 is the answer that would satisfy the known-good half of
# the control and let a broken control read as an established one.
UNRESOLVABLE: Final = 127

# pytest's own "no tests collected". The hook already treats it as a refusal on
# the serial path; condition EIGHT is that it still arrives on the parallel one.
EMPTY_SUITE_EXIT: Final = 5
# The hook's own words on that branch, and the ONLY line it prints there that a
# report can carry. The banner line above it renders $TESTS, which carries a
# drive letter and is dropped by ``hook_output``, so this indented continuation
# is what survives.
EMPTY_SUITE_REFUSAL: Final = "An empty suite is not a green suite"

# THE ONE PIECE OF PROSE THESE ARMS REQUIRE OF THE HOOK, named here so it reads
# as a specification rather than a guess. When xdist is not importable the hook
# must write ONE stderr line that begins with its own banner and carries the
# literal lowercase token below. Beginning with the banner is not decoration:
# ``hook_output`` keeps only banner lines and two-space continuations, pytest
# writes to the same stream, and a bare line carrying that token could be either
# the notice or a stray fragment of a traceback - the assertion could not tell.
SERIAL_NOTICE: Final = "xdist"

# Makes ``import xdist`` fail in a child WITHOUT uninstalling anything. Shadows
# the real package from a PYTHONPATH entry, which precedes site-packages on
# sys.path.
SHIM_SOURCE: Final = (
    '"""CS-906 fixture: hides pytest-xdist from one child interpreter."""\n'
    "\n"
    'raise ImportError("CS-906 fixture: xdist is hidden from this child")\n'
)

# The recorder, written into the SANDBOX suite and never into this repository's
# own tests. It is the only thing that can answer what the hook's child did.
RUN_RECORDER: Final = '''"""CS-906 probe: what the pytest process the pre-push hook launched did.

Records at configure time whether xdist was importable and whether a parallel
option reached this process, and at session end the exit status the session
actually reached. One file per process, named by pid, because under xdist this
conftest runs in the controller AND in every worker - and only the controller's
record answers the questions the arms ask.

Written through a temporary name and renamed into place: the parent reads these
only after the push returns, but a file another process may read is written
atomically here regardless (CLAUDE.md non-negotiable 5).
"""

import json
import os
import pathlib

RECORDS = "@PROBE_DIR@"


def _directory():
    directory = pathlib.Path(__file__).resolve().parent.parent / RECORDS
    directory.mkdir(exist_ok=True)
    return directory


def _write(record, tag):
    directory = _directory()
    name = "{0}-{1}.json".format(tag, os.getpid())
    scratch = directory / (name + ".tmp")
    scratch.write_text(json.dumps(record), encoding="ascii")
    scratch.replace(directory / name)


def _worker(config):
    """Which xdist worker this process is, or None when it is the controller.

    DELIBERATELY NOT ``os.environ["PYTEST_XDIST_WORKER"]``, and that is the whole
    reason this helper exists. THAT VARIABLE IS INHERITED. When the OUTER suite
    runs under ``-n auto`` the process driving the push is itself an xdist worker,
    the variable is already set in its environment, and it travels down the whole
    chain - the environment copy, git, sh, the hook - into this process. The
    controller then reads a worker id it never earned, files itself as a worker,
    and every controller-derived field the arms assert on comes back None while
    the run plainly happened. MEASURED: with the outer suite serial the controller
    recorded worker=None; with the outer suite under ``-n auto`` the same
    controller recorded the OUTER run's worker id, and all three arms below failed
    on ran=False - the two parallel ones beside workers=9, which is a controller
    miscounted among its own eight, and the degraded-serial one beside workers=1,
    which is a lone controller counted as the only worker.

    ``config.workerinput`` is injected by xdist INSIDE the worker process
    (xdist/remote.py sets it before the session configures) and cannot arrive from
    a parent. It is also xdist's own discriminator - ``xdist.is_xdist_worker`` is
    exactly this hasattr. It is read with ``getattr`` rather than through an
    import because the degraded arm hides xdist from this very process.
    """
    workerinput = getattr(config, "workerinput", None)
    if workerinput is None:
        return None
    return workerinput.get("workerid", "unnamed")


def pytest_configure(config):
    try:
        import xdist  # noqa: F401

        importable = True
    except ImportError:
        importable = False
    _write(
        {
            "kind": "configure",
            "worker": _worker(config),
            # CONTROL ONLY, AND NEVER AN IDENTITY. What the environment claimed
            # this process was, recorded so an arm can prove an inherited value
            # reached the child and was overruled rather than merely absent.
            "env_worker": os.environ.get("PYTEST_XDIST_WORKER"),
            "xdist_importable": importable,
            "numprocesses": getattr(config.option, "numprocesses", None),
        },
        "c",
    )


def pytest_sessionfinish(session, exitstatus):
    _write(
        {
            "kind": "finish",
            "worker": _worker(session.config),
            "exitstatus": int(exitstatus),
        },
        "f",
    )
'''.replace("@PROBE_DIR@", PROBE_DIR_NAME)


class SuiteRun(NamedTuple):
    """What the pytest process the pre-push hook launched reported about itself.

    Every field is a bool, an int or None. Nothing here carries a path, so unlike
    ``Sandbox`` and ``Environment`` this type needs no repr guard - and it is safe
    to render into an assertion message, which is the whole reason the records are
    reduced to it before anything asserts on them.

    ``distributed`` is read from the CONTROLLER's ``numprocesses``, measured on
    this toolchain as an int under ``-n auto`` and None without it. The workers
    report None for it and are counted only for the report, never asserted on:
    they are separate processes whose files can still be landing when the
    controller has already exited, and an arm that counted them would be a race.

    ``inherited_worker`` IS A CONTROL AND NEVER AN IDENTITY. It is what
    ``PYTEST_XDIST_WORKER`` said inside the controller, which is a claim the
    environment makes and not a fact about this process - see ``_worker`` in the
    recorder for what reading it as an identity cost. It is carried because
    ``ran=False`` beside a non-zero ``workers`` is otherwise a silent shape: it
    reads as "nothing ran" when what happened is that everything ran and the
    controller was misfiled. An xdist worker id is ``gwN``, so this carries no
    path and is safe to render.
    """

    ran: bool
    distributed: bool
    xdist_importable: bool | None
    exitstatus: int | None
    workers: int
    inherited_worker: str | None

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        return (
            f"suite: ran={self.ran} distributed={self.distributed} "
            f"xdist_importable={self.xdist_importable} "
            f"session_exit={self.exitstatus} worker_processes={self.workers} "
            f"inherited_worker={self.inherited_worker}"
        )


def instrument_sandbox(box: Sandbox) -> None:
    """Put the run recorder into the sandbox suite.

    DELIBERATELY NOT FOLDED INTO ``make_sandbox``. The arms above measure the
    interpreter ladder against exactly the suite they were written for, and adding
    a conftest to every pre-push sandbox would change what those arms collect for
    the sake of three that came later.
    """
    (box.work / SANDBOX_TESTS / SANDBOX_CONFTEST).write_bytes(RUN_RECORDER.encode("ascii"))


def set_sandbox_suite(box: Sandbox, *, passes: bool | None) -> None:
    """Make the sandbox suite pass, fail, or collect NOTHING.

    ``None`` removes the only test file, which is how condition EIGHT's empty
    collection is produced - the recorder conftest stays, is not itself a test,
    and pytest collects zero. Measured on this toolchain: exit 5, serially and
    under ``-n auto`` alike.
    """
    arm = box.work / SANDBOX_TESTS / SANDBOX_SUITE
    if passes is None:
        arm.unlink(missing_ok=True)
        return
    body = "def test_sandbox_arm() -> None:\n    assert %s\n" % passes
    arm.write_bytes(body.encode("ascii"))


def clear_suite_records(box: Sandbox) -> None:
    """Drop every record before driving a push.

    LOAD-BEARING WHEREVER AN ARM PUSHES TWICE. A control push into the same
    sandbox would otherwise read the blocked push's controller record and conclude
    the control ran distributed when it may not have - the stale record and the
    fresh one are the same shape.
    """
    directory = box.work / PROBE_DIR_NAME
    if directory.is_dir():
        shutil.rmtree(directory)


def read_suite_run(box: Sandbox) -> SuiteRun:
    """Reduce the records the sandbox conftest left to the facts an arm asserts on."""
    directory = box.work / PROBE_DIR_NAME
    records: list[dict[str, object]] = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="ascii")))
            except (OSError, ValueError):
                continue
    configured = [item for item in records if item.get("kind") == "configure"]
    finished = [item for item in records if item.get("kind") == "finish"]
    controllers = [item for item in configured if item.get("worker") is None]
    enders = [item for item in finished if item.get("worker") is None]
    head: dict[str, object] = controllers[0] if controllers else {}
    tail: dict[str, object] = enders[0] if enders else {}
    importable = head.get("xdist_importable")
    status = tail.get("exitstatus")
    inherited = head.get("env_worker")
    return SuiteRun(
        ran=bool(controllers),
        distributed=head.get("numprocesses") is not None,
        xdist_importable=importable if isinstance(importable, bool) else None,
        exitstatus=status if isinstance(status, int) else None,
        workers=sum(1 for item in configured if item.get("worker") is not None),
        inherited_worker=inherited if isinstance(inherited, str) else None,
    )


def sandbox_without_xdist(box: Sandbox, shim: Path) -> Sandbox:
    """The same sandbox, with ``import xdist`` broken for every child it starts.

    THE OVERRIDE ARRIVES THROUGH ``_replace`` RATHER THAN A NEW PARAMETER ON
    ``push_attempt``, and that is not a stylistic choice. ``Sandbox`` already owns
    the child environment, ``push_attempt`` already builds from it through
    ``env_naming``, and widening that signature would have cost eight lines at the
    top of the file - which two line-anchored documentation pins do not survive.
    The replaced sandbox keeps the same work tree, the same remote and the same
    repr guard, so every helper here takes it unchanged.

    XDIST IS NOT UNINSTALLED, and it is not switched off with ``-p no:xdist``
    either. A hook that asks whether the plugin is IMPORTABLE must be answered by
    the import system, and ``-p no:xdist`` leaves the import working - that would
    simulate a disabled plugin, which is not the case under test.

    THE AUTOLOAD SWITCH IS NOT PADDING, AND IT WAS MEASURED RATHER THAN ASSUMED.
    With the shim alone, pytest's entry-point autoload does ``import xdist.plugin``,
    hits the shim, and dies with an ImportError traceback before collecting
    anything: the suite never runs, and every arm below would then block for a
    reason with nothing to do with the hook. Disabling autoload is what a machine
    with no pytest-xdist installed actually looks like from pytest's side - no
    importable module AND no entry point - and it leaves both plausible shapes of
    the hook's check reading "unavailable": ``python -c "import xdist"``, and a
    probe of pytest's own option surface.

    WINDOWS FOLDS ENVIRONMENT KEYS AND ``dict(os.environ)`` HANDS BACK UPPER-CASE
    ONES, so any existing spelling is removed before the canonical name is
    written. Writing ``env["PYTHONPATH"]`` over a dict that already carries
    ``PythonPath`` leaves both in the block, and which one the child sees is not
    defined - a simulation that silently did not take, reported as clean.

    NOTHING IS SET IN THIS PROCESS, for the reason ``env_naming`` gives about
    PATH: an arm that hid xdist from the whole pytest run would change what every
    other arm resolves, invisibly from here.
    """
    env = env_naming(box, None)
    inherited = [key for key in env if key.upper() == PYTHONPATH_ENV]
    carried = os.pathsep.join(value for value in (env.pop(key) for key in inherited) if value)
    env[PYTHONPATH_ENV] = str(shim) + (os.pathsep + carried if carried else "")
    for key in [key for key in env if key.upper() == AUTOLOAD_ENV]:
        env.pop(key)
    env[AUTOLOAD_ENV] = "1"
    return box._replace(env=env)


def import_xdist_exit(box: Sandbox) -> int:
    """Exit code of ``python -c "import xdist"`` in this sandbox's environment.

    RUN BY THE BARE NAME, which is the hook's own first ladder rung, so this
    measures what the hook will resolve rather than what this process happens to
    be running.

    ONLY THE INTEGER COMES BACK. The shim raises an ImportError that renders its
    own absolute path under the user profile, and nothing here may reach an
    assertion message (CLAUDE.md non-negotiable 3).
    """
    try:
        proc = subprocess.run(
            ["python", "-c", "import " + XDIST_MODULE],
            cwd=str(box.work),
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT,
            env=box.env,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return UNRESOLVABLE
    return proc.returncode


@pytest.mark.skipif(not XDIST_INSTALLED, reason=XDIST_SKIP)
def test_the_empty_suite_guard_still_returns_five_under_the_parallel_path(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-906 condition EIGHT. RED at c298ecf: the run was never distributed.

    A MEASUREMENT IS NOT A GUARD, which is the condition's own wording. Exit 5 is
    produced by the pytest process, not by the hook, and xdist changes how an
    empty collection is reported - so the property is asserted UNDER the parallel
    path rather than inherited from a serial measurement taken once. Measured on
    xdist 3.8.0 at the time of writing: still 5, controller and workers alike.
    That measurement is the reason to write the guard, not a substitute for it.

    THE ORACLE IS THE SESSION'S OWN EXIT STATUS plus the one hook line only the
    exit-5 branch can print. Neither alone is enough: the status alone would not
    show the hook ACTED on it, and the line alone could be printed by a hook that
    never distributed anything.

    THE PUSH'S OWN EXIT CODE CANNOT CARRY IT. ``die`` exits 1, so from outside
    every refusal this hook makes looks identical.
    """
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=True)
    instrument_sandbox(box)
    set_sandbox_suite(box, passes=None)

    clear_suite_records(box)
    outcome = push_attempt(box)
    run = read_suite_run(box)

    assert run.distributed, (
        "the pre-push suite did not run distributed, so this arm measured the SERIAL "
        "path under a parallel name. The hook must pass a parallel option to pytest "
        f"when xdist is importable:\n{run.report}\n{outcome.report}"
    )
    assert run.exitstatus == EMPTY_SUITE_EXIT, (
        f"an empty suite did not reach exit {EMPTY_SUITE_EXIT} under the parallel path. "
        "The hook reads that status to refuse an empty collection, and a path that "
        f"reports it differently disarms the guard silently:\n{run.report}\n{outcome.report}"
    )
    assert outcome.blocked, f"an empty suite reached the remote:\n{run.report}\n{outcome.report}"
    assert any(EMPTY_SUITE_REFUSAL in line for line in outcome.hook_output), (
        "blocked, but NOT by the empty-suite guard, so the block cannot be attributed to "
        f"it. The hook must still treat exit {EMPTY_SUITE_EXIT} as its own refusal on the "
        f"parallel path:\n{run.report}\n{outcome.report}"
    )

    # THE CONTROL, ON THE SAME PATH AND IN THE SAME SANDBOX. Everything above is
    # satisfied by a parallel path that refuses every push. The ref did not land,
    # so the branch is still absent and a second push really does run the hook.
    set_sandbox_suite(box, passes=True)
    clear_suite_records(box)
    control = push_attempt(box)
    control_run = read_suite_run(box)

    assert control.accepted, (
        "the control push of a NON-empty passing suite was blocked, so the refusal above "
        "cannot be attributed to the empty collection - this sandbox cannot say yes on "
        f"the parallel path at all:\n{control_run.report}\n{control.report}"
    )
    assert control_run.distributed, (
        "the control push did not run distributed, so it is a control for the serial path "
        f"and not for the one under test:\n{control_run.report}"
    )


@pytest.mark.skipif(not XDIST_INSTALLED, reason=XDIST_SKIP)
def test_a_failing_suite_blocks_a_real_push_on_the_parallel_path(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-906 condition TWELVE, parallel arm. RED at c298ecf: never distributed.

    THE REF IS ASSERTED SEPARATELY FROM THE EXIT CODE, and that separation is the
    entire reason to drive a real push. A hook that exits non-zero AFTER the ref
    has already reached the remote is the failure mode that matters, and an
    exit-code-only arm cannot see it: the push would be reported as blocked while
    the branch sits on the remote.

    ITS OWN ARM AND ITS OWN CONTROL. The grant says agreement between the two
    paths is not evidence, so nothing here reads what the serial arm measured.

    ON THIS TOOLCHAIN THE TWO PATHS DO NOT EVEN AGREE ON THE CODE: a failing suite
    under ``-x`` exits 1 serially and 2 distributed, because xdist raises
    Interrupted. Nothing below asserts a particular code for exactly that reason -
    only that it is not 0, which is what the hook's own ``-ne 0`` branch reads.
    """
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=False)
    instrument_sandbox(box)

    clear_suite_records(box)
    outcome = push_attempt(box)
    run = read_suite_run(box)

    assert run.distributed, (
        "the pre-push suite did not run distributed, so this arm measured the SERIAL "
        "path under a parallel name. The hook must pass a parallel option to pytest "
        f"when xdist is importable:\n{run.report}\n{outcome.report}"
    )
    assert outcome.returncode != 0, (
        "git push reported SUCCESS with a failing suite on the parallel path:\n"
        f"{run.report}\n{outcome.report}"
    )
    assert not outcome.landed_after, (
        "the ref REACHED THE REMOTE even though the suite failed. A non-zero exit after "
        "the ref has landed is not a block - it is a push that happened and then "
        f"complained:\n{run.report}\n{outcome.report}"
    )

    # THE CONTROL. Without it, a push that failed for an unrelated reason - an
    # unreachable remote, a sandbox that never wired the hook - satisfies every
    # assertion above and proves nothing about the failing test.
    set_sandbox_suite(box, passes=True)
    clear_suite_records(box)
    control = push_attempt(box)
    control_run = read_suite_run(box)

    assert control.returncode == 0, (
        "the control push of a PASSING suite was refused, so the block above cannot be "
        f"attributed to the failing test:\n{control_run.report}\n{control.report}"
    )
    assert control.landed_after, (
        "the control push reported success but the ref never reached the remote, so this "
        f"sandbox cannot demonstrate a landing at all:\n{control.report}"
    )
    assert control_run.distributed, (
        "the control push did not run distributed, so it is a control for the serial path "
        f"and not for the one under test:\n{control_run.report}"
    )


@pytest.mark.skipif(not XDIST_INSTALLED, reason=XDIST_SKIP)
def test_a_failing_suite_blocks_a_real_push_on_the_degraded_serial_path(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-906 condition TWELVE, serial arm. RED at c298ecf: no degradation notice.

    THE SIMULATION IS FRONTED BY A TWO-SIDED CONTROL, and the second side is the
    one that matters. A probe reporting "xdist is not importable" proves nothing
    unless the same probe reports "it is" without the shim: on Windows a key that
    was never really removed reads exactly like a key that was, and the negative
    measurement comes back clean either way.

    THE HOOK MUST SAY SO OUT LOUD, and this arm is the specification for that
    line. When xdist is not importable the hook writes ONE stderr line beginning
    with its own banner and containing the literal lowercase token ``xdist``.
    Beginning with the banner is load-bearing, not cosmetic: ``hook_output`` keeps
    banner lines and two-space continuations, pytest writes to the same stream,
    and a bare line carrying that token could be either the notice or a stray
    fragment of a traceback - the assertion could not tell them apart.

    WHAT THIS ARM DELIBERATELY DOES NOT FORBID: the same token appearing on the
    parallel path. A hook that announces itself on both paths still has to
    actually degrade to satisfy the three assertions below, so the announcement is
    the only thing it could be lying about, and forbidding a friendly
    parallel-path line would constrain wording this arm has no business
    constraining.
    """
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=False)
    instrument_sandbox(box)
    shim = tmp_path / SHIM_DIR_NAME
    shim.mkdir()
    (shim / (XDIST_MODULE + ".py")).write_bytes(SHIM_SOURCE.encode("ascii"))
    hidden = sandbox_without_xdist(box, shim)

    assert import_xdist_exit(box) == 0, (
        "THE KNOWN-GOOD HALF OF THE CONTROL FAILED: a child could not import xdist even "
        "without the shim, so every refusal below would be evidence about this machine "
        "rather than about the shim, and the negative measurement would mean nothing"
    )
    assert import_xdist_exit(hidden) != 0, (
        "THE SHIM DID NOT TAKE: a child still imported xdist under the shimmed "
        "environment, so this arm would drive the PARALLEL path under a serial name and "
        "pass by measuring nothing"
    )

    clear_suite_records(hidden)
    outcome = push_attempt(hidden)
    run = read_suite_run(hidden)

    assert run.ran, (
        "no pytest process recorded itself, so the suite the hook is supposed to run "
        f"never started and nothing below is about a suite result:\n{run.report}\n"
        f"{outcome.report}"
    )
    assert run.xdist_importable is False, (
        "the child the hook launched could still import xdist, so the shim did not reach "
        f"the process actually under test:\n{run.report}\n{outcome.report}"
    )
    assert not run.distributed, (
        "the hook ran the suite distributed with xdist NOT importable. It must degrade to "
        f"serial rather than pass an option the plugin cannot honour:\n{run.report}\n"
        f"{outcome.report}"
    )
    assert any(
        line.startswith(hidden.prefix) and SERIAL_NOTICE in line for line in outcome.hook_output
    ), (
        "the hook degraded to serial SILENTLY. It must write ONE stderr line that begins "
        f"'{hidden.prefix}:' and carries the token '{SERIAL_NOTICE}', or an operator reads "
        "a slow push as a normal one and never learns the parallel path is unavailable:\n"
        f"{run.report}\n{outcome.report}"
    )
    assert outcome.returncode != 0, (
        "git push reported SUCCESS with a failing suite on the degraded serial path:\n"
        f"{run.report}\n{outcome.report}"
    )
    assert not outcome.landed_after, (
        "the ref REACHED THE REMOTE even though the suite failed. A non-zero exit after "
        "the ref has landed is not a block - it is a push that happened and then "
        f"complained:\n{run.report}\n{outcome.report}"
    )

    # THE CONTROL, on the degraded path and in the same sandbox.
    set_sandbox_suite(hidden, passes=True)
    clear_suite_records(hidden)
    control = push_attempt(hidden)
    control_run = read_suite_run(hidden)

    assert control.returncode == 0, (
        "the control push of a PASSING suite was refused on the degraded path, so the "
        "block above cannot be attributed to the failing test - degrading may simply have "
        f"broken the hook:\n{control_run.report}\n{control.report}"
    )
    assert control.landed_after, (
        "the control push reported success but the ref never reached the remote, so this "
        f"sandbox cannot demonstrate a landing at all:\n{control.report}"
    )
    assert control_run.ran, (
        "no pytest process recorded itself on the control push, so it is not a control "
        f"for anything the suite did:\n{control_run.report}"
    )
    assert not control_run.distributed, (
        "the control push did not run serially, so it is a control for the parallel path "
        f"and not for the one under test:\n{control_run.report}"
    )


# --- CS-906: the recorder's own identity, which all three arms above assume ---
#
# THE THREE ARMS ABOVE ARE GRADED BY read_suite_run, AND READ NOTHING THAT GRADES
# read_suite_run ITSELF. Every one of them asserts on a field taken from the
# CONTROLLER's record, so a recorder that cannot tell its controller from a worker
# makes all three report an all-None SuiteRun - which reads as "the suite never
# ran" and is indistinguishable from a hook that never launched pytest.
#
# THAT IS NOT HYPOTHETICAL AND IT DOES NOT REPRODUCE SERIALLY, which is the whole
# reason this arm exists rather than a note. The recorder identified itself from
# PYTEST_XDIST_WORKER, xdist sets that variable in every worker, and the pre-push
# lane now runs this module under -n auto - so the process driving the push was a
# worker, the variable came down the chain into the child, and the child's
# controller filed itself as a worker. The three arms above were green serially
# and red under an outer -n auto: all three on ran=False, the two parallel ones
# beside workers=9 and the degraded-serial one beside workers=1.
#
# THE ARM BELOW PLANTS THE VARIABLE BY HAND so the serial lane can see the same
# defect. It needs no xdist and takes no skip: a lane that cannot fail is exactly
# how this got as far as it did.

WORKER_ENV: Final = "PYTEST_XDIST_WORKER"

# What the guard plants. DELIBERATELY NOT A WELL-FORMED WORKER ID - xdist writes
# `gwN` - so a failure rendering `gw3` here says a REAL inherited value won and
# the plant did not take, which a plausible-looking plant could not distinguish.
# Nothing in pytest 9.0.3 or xdist 3.8.0 reads this variable; xdist/remote.py only
# WRITES it. Measured by grepping both installed packages, not assumed.
PLANTED_WORKER: Final = "gw-cs906"


def plant_outer_worker(box: Sandbox) -> dict[str, str]:
    """The sandbox environment as an OUTER distributed run would hand it down.

    WINDOWS FOLDS ENVIRONMENT KEYS AND ``dict(os.environ)`` HANDS BACK UPPER-CASE
    ONES, so any existing spelling is removed before the canonical name is
    written - the same reason ``sandbox_without_xdist`` does it. Writing over a
    dict that already carries another casing leaves both in the block, and which
    one the child sees is undefined: a plant that silently did not take, read as
    one that did.
    """
    env = env_naming(box, None)
    for key in [key for key in env if key.upper() == WORKER_ENV]:
        env.pop(key)
    env[WORKER_ENV] = PLANTED_WORKER
    return env


def run_sandbox_suite(box: Sandbox, env: dict[str, str]) -> int:
    """Run the sandbox suite directly under ``env``. ONLY THE INTEGER COMES BACK.

    NO HOOK AND NO PUSH. The arms above drive the hook; this one is about what the
    recorder writes, and going through git would put the interpreter ladder, the
    remote and the hook's own branches between the plant and the thing measured.

    RUN UNDER ``sys.executable``, NOT THE BARE NAME. ``import_xdist_exit`` uses the
    bare name because it must measure what the HOOK will resolve; nothing here
    depends on the ladder, and pinning the interpreter removes a way for this arm
    to fail for a reason that is not the recorder.

    The child renders sandbox paths on both streams and nothing here may reach an
    assertion message (CLAUDE.md non-negotiable 3), so its output is captured and
    dropped. The oracle is the record the recorder left, never this number.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(box.work / SANDBOX_TESTS), "-q"],
            cwd=str(box.work),
            capture_output=True,
            text=True,
            timeout=CHILD_TIMEOUT,
            env=env,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return UNRESOLVABLE
    return proc.returncode


def test_the_run_recorder_tells_controller_from_worker_without_reading_the_environment(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-906. RED before the recorder read ``config.workerinput``.

    THE CHILD IS RUN SERIALLY AND IS STILL HANDED A WORKER ID. That pairing is the
    point: no xdist process exists anywhere below this line, so the ONLY thing that
    could call the child's single process a worker is the environment. Under the
    old recorder that one record was filed as a worker and the reduction came back
    ran=False, workers=1 - the exact shape the degraded-serial arm reported under
    an outer ``-n auto``, reproduced here without needing one.

    BOTH RECORDER HOOKS ARE GRADED, not just the first. ``pytest_configure`` is
    what ``ran`` and ``workers`` come from; ``exitstatus`` can only arrive if
    ``pytest_sessionfinish`` identified the controller too, and it read the same
    variable. An arm that checked only the first would leave the second free to
    rot until the next distributed lane found it.

    WHAT THIS DOES NOT COVER, stated rather than implied: the hook, the push, and
    the genuinely distributed shape. Those are the three arms above - which now
    exercise inheritance for real, because the pre-push lane runs them under
    ``-n auto``. This arm is what lets the SERIAL lane fail too.
    """
    box = make_sandbox(tmp_path, isolated, PRE_PUSH, suite_passes=True)
    instrument_sandbox(box)
    clear_suite_records(box)

    status = run_sandbox_suite(box, plant_outer_worker(box))
    run = read_suite_run(box)

    assert run.ran, (
        "the recorder did not identify the CONTROLLER of a child that ran. With a "
        "worker id planted in its environment and no xdist process anywhere, this is "
        "the outer -n auto shape exactly: a controller reads an INHERITED id, files "
        "itself as a worker, and every field the three arms above assert on comes back "
        f"None while the run plainly happened:\nchild_exit={status}\n{run.report}"
    )
    assert run.inherited_worker == PLANTED_WORKER, (
        "THE PLANT DID NOT REACH THE CHILD, so this arm graded an ORDINARY child and "
        "measured nothing about inheritance. Windows folds environment keys and "
        f"dict(os.environ) hands back upper-case ones:\nchild_exit={status}\n{run.report}"
    )
    assert not run.distributed, (
        "the child ran DISTRIBUTED, so it carries real workers and the count below "
        "would no longer be evidence about the controller. Something outside this arm "
        f"is passing a parallel option - PYTEST_ADDOPTS is the usual one:\n{run.report}"
    )
    assert run.workers == 0, (
        "a serial child reported worker processes. The only process that ran was the "
        "controller, so it was counted as BOTH - which is what reading the identity "
        f"out of the environment does:\nchild_exit={status}\n{run.report}"
    )
    assert run.exitstatus == 0, (
        "no session-end record was attributed to the controller, so pytest_sessionfinish "
        "is still reading the identity out of the environment even if pytest_configure "
        f"is not. Without it the empty-suite arm has no exit status to read:\n"
        f"child_exit={status}\n{run.report}"
    )
