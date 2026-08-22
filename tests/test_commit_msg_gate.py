#!/usr/bin/env python3
"""CS-702 - the no-co-authorship-trailer rule, proven ENFORCED by a real commit.

WHY THIS MODULE DRIVES GIT INSTEAD OF CALLING A FUNCTION, which is the whole
reason it is shaped the way it is. The hook's invocation path is
``core.hooksPath``, machine-local git configuration that is never cloned. A
unit test of a matcher function is BYTE-IDENTICAL GREEN whether the gate fires
or not, so a matcher test can prove only that this file and the hook agree
about a regex - never that a commit is actually stopped. CLAUDE.md section 2.2
says a hook's presence is never proof it fires and the only valid test is end
to end. Every arm below therefore stages a real change, runs a real
``git commit``, and asserts on the process exit code AND on whether HEAD moved.

HEAD IS CHECKED SEPARATELY FROM THE EXIT CODE, and both are required. A
non-zero exit with HEAD advanced would mean the commit landed and the hook
merely complained afterwards, which is the failure this item exists to
prevent. ``Attempt.blocked`` demands both halves; ``Attempt.accepted`` demands
both of the opposite.

ONLY commit-msg IS WIRED INTO THE SANDBOX, deliberately. Pointing
``core.hooksPath`` at the repository's own ``.githooks`` would also arm
pre-commit, which runs FIRST and has its own reasons to reject. A rejection
could then not be attributed to the hook under test, and an arm expecting a
block would pass for the wrong reason. The copy is asserted byte-identical to
the tracked hook so the isolation costs no fidelity.

THE NON-REGRESSION ARMS ARE ALSO THE HARNESS CONTROL. A sandbox where the hook
never ran would allow every message, so the empty, non-ASCII, over-long and
placeholder arms would all fail. They are the reason a green trailer arm means
the gate fired rather than that the harness is inert. One arm goes further and
asserts the rejection text carries this hook's own banner, so the block cannot
be credited to git.

THE PREDICATE UNDER TEST IS NAME-FREE, AND IT MODELS GIT'S OWN TRAILER PARSER
RATHER THAN A STRING PREFIX. It judges a body line only at column zero, and
compares the text before the first colon - trailing whitespace trimmed - against
the token, case-folded. NAME-FREE, because a list of agent names fails open on
the next harness or model rename, the exact continuous pressure CS-702 was filed
against.

GIT-SHAPED, because the first cut of this gate matched a line whose STRIPPED
form started with `co-authored-by:`, and that was wrong in BOTH directions at
once. Too NARROW: git finds the separator first and trims the token after, so
`Co-authored-by : x` is a real trailer to git, and the first cut let it commit -
exit zero, HEAD moved, key populated. Too WIDE: git refuses whitespace before a
token has begun, so an INDENTED line is not a trailer to git anywhere in any
message, yet the first cut blocked it - which meant this repository could not
quote the shape it forbids, and the commit landing the item was rejected by the
gate it was landing. The shape table further down carries both columns and
measures each of them, so neither error can return quietly.

A FENCE IS NOT A SHIELD, which is why no arm here teaches the gate about one.
Measured on git 2.53: a triple-backtick block carrying a co-authorship line
alone is not a trailer block, but the same block carrying a GIT-GENERATED
trailer beside it - a sign-off, a cherry-pick line - is parsed whole and the
co-authorship line inside it becomes a real trailer. The arm holding that
message is the reason the flush-inside fenced example stays blocked.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. tmp_path sits under the real user
profile and its own directory name embeds the account name, so a rendered
CompletedProcess - which reprs its own argument list - would put a home path
and an account name into a failure report (CLAUDE.md non-negotiables 3 and 12).
Every result is reduced to a bool, an int or the hook's own output before it is
asserted on, and the sandbox withholds its paths from its repr.
"""

import os
import subprocess
from pathlib import Path
from typing import Final, NamedTuple

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOK_PATH: Final = REPO_ROOT / ".githooks" / "commit-msg"

GIT_TIMEOUT: Final = 120
TOOL_PREFIX: Final = "clockspeed commit-msg"
REJECTED: Final = "REJECTED"

# The trailer check's own words, so an arm can pin WHICH rule refused rather
# than merely that something did.
TRAILER_REASON: Final = "co-authorship trailer"

# The trailer key, WITHOUT the colon, because the colon is a separator rather
# than part of the token. git's own parser locates the separator first and then
# trims the token, which is why `Co-authored-by : x` is a trailer to git.
TRAILER_KEY: Final = "co-authored-by"

SANDBOX_BRANCH: Final = "cs702-sandbox"
FIXTURE_NAME: Final = "CS-702 Fixture"
FIXTURE_EMAIL: Final = "cs702@example.invalid"
TRACKED_NAME: Final = "tracked.txt"
MESSAGE_NAME: Final = "commit-message.txt"
NO_HEAD: Final = "(no commit yet)"

# Mirrors the hook's own LIMIT. Pinned here so a change to either side shows up
# as a failure rather than as two files quietly disagreeing.
SUBJECT_LIMIT: Final = 72

# The top of 7-bit ASCII, which is what the hook and this file are both held to.
MAX_ASCII_BYTE: Final = 0x7E

# git's own scissors line, as emitted into the editor buffer by `commit
# --verbose`. Measured from git 2.53 rather than typed from memory: 24 dashes,
# the marker, 24 dashes.
SCISSORS: Final = "# ------------------------ >8 ------------------------"

LEGITIMATE: Final = "CS-702: prove the commit-msg gate accepts an ordinary message\n"

# U+2014, written as an escape so this file stays 7-bit ASCII on disk. See the
# note on the arm that uses it.
EM_DASH: Final = chr(0x2014)


class Sandbox(NamedTuple):
    """A throwaway git repository whose only wired hook is commit-msg.

    THE REPR WITHHOLDS EVERY PATH, and that is not decoration. pytest renders
    the fixture values it can reach at the top of a failure report, and both
    ``work`` and ``env`` carry absolute paths under the real user profile -
    ``env`` carries the whole inherited environment, account name included.
    """

    work: Path
    hooks: Path
    env: dict[str, str]

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return "<CS-702 sandbox repository, paths withheld>"


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
    def blocked_by_the_trailer_check(self) -> bool:
        """Whether the TRAILER check refused, not merely that something did.

        ``blocked`` alone is satisfied by ANY refusal - nothing staged, a bad
        identity, a different rule inside the same hook - so a trailer arm
        asserting only ``blocked`` could go green while the gate under test did
        nothing at all. That is precisely the false green this item was filed
        under, so every trailer arm asserts this stronger property instead.
        """
        return self.blocked and any(TRAILER_REASON in line for line in self.hook_output)

    @property
    def accepted(self) -> bool:
        """Whether git succeeded AND a commit landed."""
        return self.returncode == 0 and self.head_moved

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.hook_output) if self.hook_output else "(no hook output)"
        return f"exit={self.returncode} head_moved={self.head_moved}\n{shown}"


def hook_output(stderr: str) -> tuple[str, ...]:
    """Keep only the hook's own lines, so no git-rendered path can reach a report.

    The hook writes a banner line beginning with its tool name and indents
    every continuation by two spaces. Anything else on stderr is git's, may
    name the sandbox path, and is dropped.
    """
    return tuple(
        line for line in stderr.split("\n") if line.startswith((TOOL_PREFIX, "  ")) and line.strip()
    )


def run_git(sandbox: Sandbox, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git inside the sandbox with the operator's own configuration excluded."""
    return subprocess.run(
        ["git", *args],
        cwd=str(sandbox.work),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=sandbox.env,
        check=False,
    )


def head_of(sandbox: Sandbox) -> str:
    """The current HEAD commit id, or a sentinel when there is no commit yet."""
    proc = run_git(sandbox, "rev-parse", "HEAD")
    return proc.stdout.strip() if proc.returncode == 0 else NO_HEAD


def attempt(sandbox: Sandbox, message: str, *flags: str) -> Attempt:
    """Stage a real change and drive a real ``git commit`` carrying ``message``.

    The message is written as BYTES from UTF-8, so a non-ASCII arm delivers the
    same bytes git would hand the hook rather than something a text-mode write
    re-encoded.
    """
    tracked = sandbox.work / TRACKED_NAME
    with tracked.open("a", encoding="ascii") as handle:
        handle.write("one more line\n")
    staged = run_git(sandbox, "add", TRACKED_NAME)
    assert staged.returncode == 0, "the sandbox change could not be staged"

    message_file = sandbox.hooks.parent / MESSAGE_NAME
    message_file.write_bytes(message.encode("utf-8"))

    before = head_of(sandbox)
    proc = run_git(sandbox, "commit", "-F", str(message_file), *flags)
    after = head_of(sandbox)
    return Attempt(proc.returncode, before, after, hook_output(proc.stderr))


@pytest.fixture
def isolated(tmp_path: Path) -> dict[str, str]:
    """An environment with the operator's own git configuration excluded.

    Both files are aimed at paths that do not exist, so a machine carrying
    core.hooksPath, commit.gpgsign, commit.template or a custom trailer.* setting
    globally cannot answer for git here. Shared by the sandbox fixture and by the
    oracle arms, so the gate and the oracle are read under the same git.
    """
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    return env


@pytest.fixture
def sandbox(tmp_path: Path, isolated: dict[str, str]) -> Sandbox:
    """A real repository with the tracked commit-msg hook wired, and one commit in it.

    The operator's own git configuration is excluded by the ``isolated``
    fixture; without that, a machine with core.hooksPath, commit.gpgsign or
    commit.template set globally would be grading its own configuration rather
    than this hook.

    The identity is synthetic. Letting git fall back to the machine's real
    user.name would write the Windows account name into a commit object inside
    the test (CLAUDE.md non-negotiable 3).
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    source = HOOK_PATH.read_bytes()
    installed = hooks / "commit-msg"
    installed.write_bytes(source)
    installed.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()

    box = Sandbox(work=work, hooks=hooks, env=isolated)

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

    first = attempt(box, LEGITIMATE)
    assert first.accepted, f"the sandbox could not make its first commit:\n{first.report}"
    return box


# --- preconditions ----------------------------------------------------------


def test_the_wired_hook_is_a_byte_identical_copy_of_the_tracked_hook(sandbox: Sandbox) -> None:
    copied = (sandbox.hooks / "commit-msg").read_bytes()
    assert copied == HOOK_PATH.read_bytes(), (
        "the sandbox hook is not the tracked hook, so nothing below grades the real file"
    )


def test_the_tracked_hook_is_lf_only_ascii_and_carries_no_bom() -> None:
    """CS-702 narrowing 4 - asserted after every edit, never assumed.

    The harness edit path converts a tracked file to CRLF while git normalises
    the blob, so ``git status`` still reports clean and the breakage is
    invisible here. msys bash runs a CRLF hook correctly on this toolchain; it
    surfaces on another shell, which is the worst place to find it.
    """
    raw = HOOK_PATH.read_bytes()
    assert raw.count(b"\r") == 0, "the hook carries CR bytes; .gitattributes pins it to LF"
    assert not raw.startswith(b"\xef\xbb\xbf"), "the hook carries a UTF-8 BOM"
    assert max(raw) <= MAX_ASCII_BYTE, "the hook carries a byte above 0x7E"


# --- the gate ---------------------------------------------------------------


def test_a_co_authorship_trailer_is_blocked_and_head_is_unchanged(sandbox: Sandbox) -> None:
    """The acceptance criterion of CS-702, stated as the item states it."""
    outcome = attempt(
        sandbox,
        "CS-702: a message carrying the trailer\n"
        "\n"
        "A body that is otherwise entirely ordinary.\n"
        "\n"
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n",
    )
    assert outcome.blocked_by_the_trailer_check, (
        f"the trailer was NOT blocked end to end:\n{outcome.report}"
    )


def test_the_rejection_is_issued_by_this_hook_and_not_by_git(sandbox: Sandbox) -> None:
    """Attribution, against the common-mode risk this item was filed under."""
    outcome = attempt(
        sandbox,
        "CS-702: attribution arm\n\nCo-authored-by: Someone <someone@example.invalid>\n",
    )
    banner = [line for line in outcome.hook_output if line.startswith(TOOL_PREFIX)]
    assert outcome.blocked_by_the_trailer_check, f"expected a block:\n{outcome.report}"
    assert banner, f"the block carries no hook banner, so it may be git's:\n{outcome.report}"
    assert REJECTED in banner[0], f"the banner does not report a rejection:\n{outcome.report}"


def test_the_attribution_property_can_tell_the_hooks_rules_apart(sandbox: Sandbox) -> None:
    """The control for ``blocked_by_the_trailer_check``, without which it proves nothing.

    A property that were merely an alias for ``blocked`` would make every
    trailer arm above pass on ANY refusal, and nothing would say so. This arm
    forces a refusal from a DIFFERENT rule in the same hook and asserts the
    property reports False - so the arms that assert it True are known to be
    reading the trailer check specifically.
    """
    outcome = attempt(sandbox, "wip\n")
    assert outcome.blocked, f"the placeholder rule did not refuse at all:\n{outcome.report}"
    assert not outcome.blocked_by_the_trailer_check, (
        "a placeholder refusal was credited to the trailer check, so the "
        f"attribution used by every arm above is worthless:\n{outcome.report}"
    )


@pytest.mark.parametrize(
    "spelling",
    [
        "Co-Authored-By:",
        "Co-authored-by:",
        "co-authored-by:",
        "CO-AUTHORED-BY:",
        "cO-aUtHoReD-bY:",
    ],
)
def test_the_trailer_gate_is_case_insensitive(sandbox: Sandbox, spelling: str) -> None:
    outcome = attempt(
        sandbox,
        f"CS-702: case arm\n\n{spelling} Someone <someone@example.invalid>\n",
    )
    assert outcome.blocked_by_the_trailer_check, (
        f"spelling {spelling!r} slipped through:\n{outcome.report}"
    )


@pytest.mark.parametrize("indent", [" ", "    ", "\t", " \t "])
def test_an_indented_line_is_accepted_because_git_reads_no_trailer_there(
    sandbox: Sandbox, indent: str
) -> None:
    """Leading whitespace is git's OWN disqualifier, so it is this gate's too.

    THIS ARM ASSERTED THE OPPOSITE UNTIL CS-702 WAS REPAIRED, and the reversal
    is the finding rather than a relaxation. git's separator scan refuses a
    leading space or tab outright - it tolerates whitespace inside a token only
    once at least one token character has been consumed - so an indented line
    is not a trailer to git at any position in any message. Measured on git
    2.53 for all four indents below: `interpret-trailers --parse` returns
    nothing, and `%(trailers:key=Co-authored-by)` is empty on a commit that
    carries one.

    Blocking it cost this repository the ability to QUOTE THE SHAPE IT FORBIDS.
    The ledger entry, the GATED section and the commit message that land this
    item all have to show an example, and under the old predicate every one of
    them was rejected by the gate they were describing. It bought nothing in
    exchange: a gate that blocks what git ignores closes no hole.
    """
    outcome = attempt(
        sandbox,
        f"CS-702: indent arm\n\n{indent}Co-authored-by: Someone <someone@example.invalid>\n",
    )
    assert outcome.accepted, f"an indented line was blocked:\n{outcome.report}"


@pytest.mark.parametrize("gap", [" ", "\t", "  ", " \t "])
def test_whitespace_before_the_colon_is_still_a_trailer_and_is_blocked(
    sandbox: Sandbox, gap: str
) -> None:
    """The fail-OPEN defect that refuted the first cut of this slice.

    git locates the separator and THEN trims the token, so `Co-authored-by : x`
    is a trailer by git's own reading - measured: the commit lands and
    `%(trailers:key=Co-authored-by,valueonly)` returns the value. The predicate
    this replaced required the colon to sit adjacent to the token, so every
    spelling below walked straight through a gate whose entire purpose is to
    stop them.
    """
    outcome = attempt(
        sandbox,
        f"CS-702: gap arm\n\nCo-authored-by{gap}: Someone <someone@example.invalid>\n",
    )
    assert outcome.blocked_by_the_trailer_check, (
        f"whitespace before the colon slipped through:\n{outcome.report}"
    )


@pytest.mark.parametrize(
    "co_author",
    [
        "Claude Opus 5 <noreply@anthropic.com>",
        "Some Future Model <noreply@example.invalid>",
        "A Harness Nobody Has Named Yet <bot@example.invalid>",
        "A Human Being <person@example.invalid>",
    ],
)
def test_the_trailer_gate_is_name_free(sandbox: Sandbox, co_author: str) -> None:
    """No name list, so a rename cannot open the gate.

    THE HUMAN CASE IS DELIBERATE AND IS THE INTENDED FAILURE DIRECTION. The
    grant recorded in docs/LEDGER.md chose a name-free predicate on the
    fail-closed criterion, measured cost zero at the time, and recorded that a
    genuine human co-author is blocked. The route out is a new item and a
    recorded allowlist entry, never a shortened matcher - so this arm pins the
    wider polarity rather than leaving it to be discovered by surprise.
    """
    outcome = attempt(sandbox, f"CS-702: name-free arm\n\nCo-authored-by: {co_author}\n")
    assert outcome.blocked_by_the_trailer_check, (
        f"a trailer naming {co_author!r} slipped through:\n{outcome.report}"
    )


def test_a_trailer_anywhere_in_the_body_is_blocked_not_only_the_last_line(
    sandbox: Sandbox,
) -> None:
    outcome = attempt(
        sandbox,
        "CS-702: position arm\n"
        "\n"
        "Co-authored-by: Someone <someone@example.invalid>\n"
        "\n"
        "Body text after the trailer, so the trailer is not the final line.\n",
    )
    assert outcome.blocked_by_the_trailer_check, (
        f"a mid-body trailer slipped through:\n{outcome.report}"
    )


# --- git is the oracle ------------------------------------------------------
#
# THE RULE THIS GATE IMPLEMENTS IS "BLOCK WHAT GIT WOULD READ AS A CO-AUTHORSHIP
# TRAILER". So the shapes below are not judged against a description of git,
# which is how the first cut of this slice went wrong twice - once too narrow
# and once too wide. Each shape carries TWO measured columns: what git does with
# it, and what this gate must do with it. Both are asserted by running the real
# thing, so a stale row fails rather than misleads.

FENCE: Final = "```"
CO_AUTHOR: Final = "A Co Author <co@example.invalid>"
SIGNOFF: Final = "Signed-off-by: A Signer <signer@example.invalid>"


class Shape(NamedTuple):
    """One message shape, what GIT reads in it, and what this gate must do."""

    label: str
    message: str
    git_reads_it: bool
    gate_blocks_it: bool


def shaped(tail: str) -> str:
    """A whole commit message ending in ``tail``, so git sees a real last block."""
    return "CS-702: shape arm\n\nAn ordinary body paragraph.\n\n" + tail + "\n"


SHAPES: Final = (
    # --- git reads a trailer here, so the gate MUST block ------------------
    Shape("canonical", shaped("Co-Authored-By: " + CO_AUTHOR), True, True),
    Shape("lower case", shaped("co-authored-by: " + CO_AUTHOR), True, True),
    Shape("no space after the colon", shaped("Co-authored-by:" + CO_AUTHOR), True, True),
    Shape("one space before the colon", shaped("Co-authored-by : " + CO_AUTHOR), True, True),
    Shape("a tab before the colon", shaped("Co-authored-by\t: " + CO_AUTHOR), True, True),
    Shape("two spaces before the colon", shaped("Co-authored-by  : " + CO_AUTHOR), True, True),
    # THE ARM THAT FORBIDS EVER TEACHING THIS GATE ABOUT FENCES. A fence is not
    # a shield: measured on git 2.53, a fenced block that also carries a
    # GIT-GENERATED trailer is parsed whole, fence lines and all, and the
    # co-authorship line inside it becomes a real trailer. Any future "skip
    # fenced blocks" refinement would fail OPEN on exactly this message.
    Shape(
        "a fenced block beside a sign-off",
        shaped(FENCE + "\nCo-authored-by: " + CO_AUTHOR + "\n" + SIGNOFF + "\n" + FENCE),
        True,
        True,
    ),
    # --- git reads nothing here, so the gate must NOT block ----------------
    Shape("indented one space", shaped(" Co-authored-by: " + CO_AUTHOR), False, False),
    Shape("indented four spaces", shaped("    Co-authored-by: " + CO_AUTHOR), False, False),
    Shape("indented one tab", shaped("\tCo-authored-by: " + CO_AUTHOR), False, False),
    Shape("a bullet list item", shaped("* Co-authored-by: " + CO_AUTHOR), False, False),
    Shape("a quoted line", shaped("> Co-authored-by: " + CO_AUTHOR), False, False),
    Shape("underscores, not hyphens", shaped("Co_authored_by: " + CO_AUTHOR), False, False),
    Shape("the token then more words", shaped("Co-authored-by et al: " + CO_AUTHOR), False, False),
    Shape("the token mid-sentence", shaped("It forbids a Co-authored-by: line."), False, False),
    Shape(
        "a fenced example, indented inside",
        shaped(FENCE + "\n    Co-authored-by: " + CO_AUTHOR + "\n" + FENCE),
        False,
        False,
    ),
    # --- the two places this gate is deliberately WIDER than git -----------
    Shape(
        "a fenced example, flush inside",
        shaped(FENCE + "\nCo-authored-by: " + CO_AUTHOR + "\n" + FENCE),
        False,
        True,
    ),
    Shape(
        "a trailer with prose after it",
        shaped("Co-authored-by: " + CO_AUTHOR + "\n\nProse, so the trailer is not last."),
        False,
        True,
    ),
)

# Named so a NEW divergence has to be declared here rather than appearing
# quietly in a table nobody re-reads. Both are fail-CLOSED: the gate refuses
# something git would ignore. Neither can be closed by teaching the gate about
# fences or about last-block position - see the sign-off arm above for why the
# first is unsafe, and the mid-body arm for why the second is deliberate.
KNOWN_DIVERGENCES: Final = frozenset(
    {"a fenced example, flush inside", "a trailer with prose after it"}
)


def git_reads_a_co_authorship_trailer(env: dict[str, str], cwd: Path, message: str) -> bool:
    """Ask GIT whether this message carries the trailer. The oracle, not this file.

    ``interpret-trailers --parse`` re-emits what it found in a NORMALISED form -
    token, colon, single space, value - with no leading whitespace and no gap
    before the colon, whatever the input spelling was. Measured on git 2.53: an
    input line reading ``Co-authored-by <tab> : value`` comes back as
    ``Co-authored-by: value``. That normalisation is what lets this reader be a
    plain prefix test instead of borrowing the predicate under test, which would
    make the whole comparison circular and prove nothing.
    """
    proc = subprocess.run(
        ["git", "interpret-trailers", "--parse"],
        cwd=str(cwd),
        input=message,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=env,
        check=False,
    )
    return any(line.lower().startswith(TRAILER_KEY + ":") for line in proc.stdout.split("\n"))


@pytest.mark.parametrize("shape", SHAPES, ids=lambda shape: shape.label)
def test_git_reads_each_shape_exactly_as_the_table_claims(
    isolated: dict[str, str], tmp_path: Path, shape: Shape
) -> None:
    """The git column is MEASURED. A stale row fails here, not silently downstream."""
    reads = git_reads_a_co_authorship_trailer(isolated, tmp_path, shape.message)
    claimed = "reads a trailer in" if shape.git_reads_it else "reads no trailer in"
    assert reads == shape.git_reads_it, (
        f"the table claims git {claimed} {shape.label!r}, and git disagrees. "
        "git is the oracle here, so the table is what is wrong."
    )


@pytest.mark.parametrize("shape", SHAPES, ids=lambda shape: shape.label)
def test_the_gate_treats_each_shape_exactly_as_the_table_claims(
    sandbox: Sandbox, shape: Shape
) -> None:
    """The gate column, measured end to end against a real commit."""
    outcome = attempt(sandbox, shape.message)
    if shape.gate_blocks_it:
        assert outcome.blocked_by_the_trailer_check, (
            f"{shape.label!r} was NOT blocked:\n{outcome.report}"
        )
    else:
        assert outcome.accepted, f"{shape.label!r} was blocked:\n{outcome.report}"


def test_the_gate_is_never_narrower_than_git() -> None:
    """The fail-OPEN guard, and the property the repair exists to restore.

    Stated over the table rather than by re-running the shapes, because the two
    arms above already measure both columns; this one asserts the RELATION
    between them. A row that lets git read a trailer the gate waves through is
    the defect that refuted the first cut, and it can never be acceptable.
    """
    narrower = sorted(s.label for s in SHAPES if s.git_reads_it and not s.gate_blocks_it)
    assert not narrower, f"the gate would fail OPEN on: {narrower}"


def test_the_only_divergences_from_git_are_the_two_recorded_ones() -> None:
    """A new divergence has to be declared, not discovered by someone later."""
    diverging = {s.label for s in SHAPES if s.git_reads_it != s.gate_blocks_it}
    assert diverging == set(KNOWN_DIVERGENCES), (
        f"undeclared divergence from git: {sorted(diverging ^ set(KNOWN_DIVERGENCES))}"
    )


# --- narrowing 2: the comment-stripped body, never the raw bytes ------------


def test_a_commented_out_trailer_does_not_block_the_commit(sandbox: Sandbox) -> None:
    """The hook reads git's comment-stripped body, so a '#' line is out of scope.

    A commented line is not a co-authorship attribution: its stripped form
    starts with '#', git's own trailer parser does not read it as a trailer,
    and blocking it would reject the commit template itself.
    """
    outcome = attempt(
        sandbox,
        "CS-702: commented arm\n\n# Co-authored-by: Someone <someone@example.invalid>\n",
    )
    assert outcome.accepted, f"a commented-out trailer was blocked:\n{outcome.report}"


def test_a_trailer_below_a_scissors_marker_does_not_block_the_commit(sandbox: Sandbox) -> None:
    """Everything past the scissors marker is out of scope, per narrowing 2.

    THIS ARM PINS A DELIBERATE HOLE, and naming it here is the point. It exists
    so that `git commit --verbose` does not reject on its own diff: the verbose
    buffer carries the full patch below this marker, and a CONTEXT line in that
    patch is rendered with a single leading space - so a diff of any file
    quoting a trailer would strip to a line starting with the token and reject
    a commit that carries no trailer at all. This module is such a file.

    THE COST IS A REAL FAIL-OPEN AND THIS DOCSTRING USED TO UNDERSTATE IT.
    `--cleanup=scissors` truncates only when the message is to be EDITED, so
    under `-F` the section survives into the stored commit - and git READS THE
    SURVIVING LINE AS A TRAILER. Two independent agents measured that:
    `git log -1 --format='%(trailers:key=Co-authored-by,valueonly)'` returns the
    value on a commit this arm asserts is accepted. So this arm pins a
    DISCLOSED HOLE, not a harmless one. It is filed as CS-813 and recorded in
    `docs/GATED.md`; a rewrite of the pre-filter that closed it was built,
    refuted for other reasons, and not shipped. Deliberate evasion has easier
    routes - `--no-verify` bypasses every hook - and that class is CS-704.
    """
    outcome = attempt(
        sandbox,
        f"CS-702: scissors arm\n\n{SCISSORS}\nCo-authored-by: Someone <someone@example.invalid>\n",
    )
    assert outcome.accepted, f"a trailer below the scissors marker was blocked:\n{outcome.report}"


# --- the accept path --------------------------------------------------------


def test_a_legitimate_message_is_accepted(sandbox: Sandbox) -> None:
    outcome = attempt(
        sandbox,
        "CS-702: an ordinary subject that says what changed\n"
        "\n"
        "An ordinary body paragraph explaining why the change was made.\n",
    )
    assert outcome.accepted, f"an ordinary message was blocked:\n{outcome.report}"


@pytest.mark.parametrize(
    "prose",
    [
        "The rule forbids a Co-authored-by: trailer on any commit.",
        "Nothing enforced the co-authored-by rule before this item.",
        "Every commit carrying Co-Authored-By: lines predates the gate.",
        "Search for co-authored to find the prose about this rule.",
    ],
)
def test_prose_discussing_the_rule_mid_line_is_accepted(sandbox: Sandbox, prose: str) -> None:
    """A gate that cannot tell a sentence from a trailer blocks its own documentation.

    git reads none of these as a trailer: once a token has been broken by a word
    rather than by the separator, its scan stops. Measured over this repository's
    history on 2026-08-22, a plain substring search for the COLON-LESS token
    returns nineteen commits where the trailer-shaped match returns eighteen, and
    the nineteenth is a commit message ABOUT this rule. Searching for the token
    WITH its colon returns eighteen too - so that particular gap is the colon's
    doing, not the anchor's, and the number is quoted here with its matcher named
    because a count whose matcher is unstated cannot be re-derived.
    """
    outcome = attempt(sandbox, f"CS-702: prose arm\n\n{prose}\n")
    assert outcome.accepted, f"prose about the rule was blocked:\n{outcome.report}"


# --- non-regressions, which are also the harness control --------------------


def test_an_empty_message_is_still_blocked(sandbox: Sandbox) -> None:
    outcome = attempt(sandbox, "\n\n   \n")
    assert outcome.blocked, f"an empty message was accepted:\n{outcome.report}"


def test_a_non_ascii_message_is_still_blocked(sandbox: Sandbox) -> None:
    """An em dash, the character that made the ASCII rule permanent.

    THE CHARACTER IS BUILT FROM AN ESCAPE, NEVER TYPED. This file is itself
    authored content, and non-negotiable 4 admits no exception for a test
    fixture: a literal em dash here would be caught by the repository's own
    character-set gate, so the arm proving the gate works would be the thing
    that trips it. The escape is 7-bit ASCII on disk and the character exists
    only at run time, which is the only way to have both.
    """
    outcome = attempt(sandbox, f"CS-702: an em {EM_DASH} dash in the subject\n")
    assert outcome.blocked, f"a non-ASCII message was accepted:\n{outcome.report}"


def test_an_over_long_subject_is_still_blocked(sandbox: Sandbox) -> None:
    outcome = attempt(sandbox, "C" * (SUBJECT_LIMIT + 1) + "\n")
    assert outcome.blocked, f"an over-long subject was accepted:\n{outcome.report}"


def test_a_subject_at_the_limit_is_still_accepted(sandbox: Sandbox) -> None:
    """The boundary, so the cap cannot drift to an off-by-one without a failure."""
    outcome = attempt(sandbox, "C" * SUBJECT_LIMIT + "\n")
    assert outcome.accepted, f"a subject at the limit was blocked:\n{outcome.report}"


@pytest.mark.parametrize("placeholder", ["wip", "fix", "update", "temp", "asdf", "test"])
def test_a_placeholder_subject_is_still_blocked(sandbox: Sandbox, placeholder: str) -> None:
    outcome = attempt(sandbox, placeholder + "\n")
    assert outcome.blocked, f"placeholder {placeholder!r} was accepted:\n{outcome.report}"
