#!/usr/bin/env python3
"""CS-855 - what renders a CAUGHT exception into a failure report under DEFAULT flags.

THE CHANNEL, NAMED PRECISELY, because the inherited name for it was wrong. This
is the CONSUMER side: given an exception that already holds something, which
constructs put it in a pytest report when no ``-l`` is passed. It is not the
locals channel - every arm below measures identically with and without ``-l``,
which is exactly what distinguishes it from CS-851 - and it is not the
producer's question of what reached ``BaseException.args`` at the raise site.

THREE MECHANISMS FIRE, MEASURED RATHER THAN REASONED, and they have different
remedies, which is the whole reason for separating them:

  CHAINED_CONTEXT   An exception escaping a handler body makes the CAUGHT
                    exception the new one's ``__context__``, and the report
                    prints the caught one's own traceback ending in
                    ``E   ValueError: <its args>``, then "During handling of the
                    above exception, another exception occurred:".
  CHAINED_CAUSE     The same block under ``raise X from exc``, introduced by
                    "The above exception was the direct cause of the following
                    exception:".
  FRAME_ARGUMENT    A handler that hands its binding to a function renders that
                    object as an ARGUMENT of the callee's frame - ``problem =
                    Boom('...')`` printed above the callee's source - with no
                    ``-l`` and with the chain suppressed. Frame arguments render
                    by default on this project; ``tests/save/test_synthetic.py``
                    carries that measurement for its own population.
  REWRITTEN_ASSERT  pytest's rewriter reprs the sub-expressions of an asserted
                    expression, so a read of the binding inside an ``assert``
                    renders whatever that read returns.

THE BINDING IS NOT WHAT RENDERS THE CHAINED BLOCK, AND THAT REFUTES THE
ATTRIBUTION THIS ITEM INHERITED. ``locals_rendering_guard.EXCEPT_TARGET``
records the form as "LEAKS ON A DIFFERENT CHANNEL", measured through a fixture
whose handler binds ``as exc``. Running that shipped fixture verbatim, and then
again with the binding deleted, renders the marker BOTH TIMES - so the fixture
never isolated the binding, and ``renders_by_default=True`` is a true statement
about the fixture and a false one about the FORM. ``test_the_binding_is_not_what
_renders_the_chained_context`` runs both halves on every run so the distinction
cannot rot back into "the except-target form leaks".

THE TWO MECHANISMS THAT REALLY ARE NAME-KEYED are FRAME_ARGUMENT and
REWRITTEN_ASSERT, and they behave oppositely on this tree. The
FRAME_ARGUMENT population is NOT empty, and it is the finding that keeps this
module from grading nothing. The REWRITTEN_ASSERT population measures ZERO, and
WHAT THAT ZERO MEANS IS NARROWER THAN ITS NAME - read the boundary below before
quoting it. An empty population satisfies every zero, and this item's own
history is the proof: the CS-851 census read ZERO named handlers for many
sessions while the tree held more than a hundred, because nothing in it could
match ``ast.Try``.

WHAT THE REWRITTEN_ASSERT ZERO IS, EXACTLY. It is a SYNTACTIC result over the
shipped AST: no ``except`` clause in the tree has an ``assert`` in its enclosing
scope reading the bound name or a local aliased from it. It is NOT the claim
that no assert can render a caught exception. Four constructs were measured to
render while defeating an earlier, narrower version of this detector - an alias
before the assert, a ``*[exc]`` unpack, an alias then a hand-off, and a call
through a module-level name that shadows a builtin - and each is followed or
counted now. There is no argument that the list is complete. A construct nobody
has thought of renders and goes uncounted, and the zero would look identical.

THE ALIAS IS FOLLOWED BECAUSE THE TREE SHIPS IT. ``last = exc`` inside a retry
handler, with the object used after the loop, occurs in ``clockspeed/data/
version.py`` and ``clockspeed/save/workdir.py``. A detector keyed on the bound
name alone reported a clean sheet over a construct in live code, which is why
``carriers`` is a measured field rather than the handler's name.

THE SANCTIONED CS-205 REMEDY CREATES THE FRAME_ARGUMENT EXPOSURE, which is the
cross-item result worth carrying. ``tests/test_exception_rendering.py`` asks
that a handler not render the exception OBJECT into a message, and the fix it
sanctions is to hand the object to a redaction helper - ``helper(NAME)``, named
there as "the FIX". That hand-off is precisely the construct measured here to
put the unredacted object into a rendered frame. It is an EXPOSURE and not a
demonstrated disclosure: the frame renders only if the helper itself raises, and
these helpers are small. The shape is named rather than the sites, which drift.

POSITION RELATIVE TO THE HANDLER IS A PROXY, NOT THE RULE, and the inherited
note states the proxy as the cause. It says Python deletes the handler's name on
the way out, so an assert AFTER the handler renders nothing. The deletion is
real, the conclusion does not follow, and the counter-example is
``object-kept-past-the-handler``: keep the OBJECT under a second name and an
assert after the handler renders it in full. What decides is whether the object
reaches a rendered expression, or whether an exception escapes while the caught
one is still being handled. Both happen to be true inside a handler and false
after one, which is why the proxy looked like a rule.

WHAT THIS MODULE DOES NOT GRADE, stated as a boundary rather than implied away.

  WHETHER ANY PARTICULAR EXCEPTION CARRIES SAVE-DERIVED CONTENT. What renders
  through the chained block is ``str()`` of the caught exception, and its args
  come from the RAISE SITE. That is the producer side and it belongs to the
  CS-852 gap-1 work; re-deriving it here from the same tree would be two agents
  agreeing rather than two measurements, which CLAUDE.md section 5 says is not
  evidence. This module measures only whether the CONTENT REACHES A REPORT.

  WHETHER A CALL IN AN EXPOSED HANDLER EVER ACTUALLY RAISES. The population
  derived below is an UPPER BOUND on FRAME_ARGUMENT: it counts a handler that
  hands its binding to a non-builtin call, whether or not that callee can fail.
  Builtin callees are excluded because a builtin gets no Python frame, so
  ``type(exc)`` and ``str(exc)`` cannot render an argument - and ``str(exc)`` is
  already CS-205's subject on a different channel.

  THE LOCALS CHANNEL. CS-851 owns it, and the ``-l`` arm here exists only to
  show that this channel is not it.

  WHETHER PERSONAL DATA SPECIFICALLY REACHES A REPORT. THIS IS THE LIMITATION
  THAT MATTERS MOST AND IT IS STATED RATHER THAN IMPLIED AWAY. Every arm runs
  in a sandbox with ``--rootdir`` and ``cwd`` set to a temporary directory
  OUTSIDE the repo, so neither ``pyproject.toml`` nor ``tests/conftest.py``
  loads - a sandbox header carries no ``configfile:`` line where an in-repo run
  carries one. The real pipeline has a redactor in front of it:
  ``tests/conftest.py``'s CS-428 ``pytest_runtest_makereport`` wrapper, whose
  own docstring names frame arguments as a channel ``longrepr`` carries, and
  which rewrites home paths and the account name. So what these arms prove is
  that AN ARBITRARY STRING REACHES THE REPORT. They do NOT prove that personal
  data does, and a green run here is not a privacy result. Measuring through
  the configured pipeline is unfinished work, recorded rather than claimed:
  doing it needs the fixtures to sit inside the repo, where every tree-wide
  guard would enumerate them - ``tracked_python_files`` lists untracked files
  too - so the sandbox would perturb the very census this module derives.

THE MARKERS ARE INVENTED ASCII TOKENS. Nothing forced by this module plants a
real path, account id or world name, and every fixture binds its marker at
MODULE scope so that the source echo prints the identifier rather than the
value - the channel CS-850 measured while building its own forced arms.

WHAT IS RECORDED AS STILL UNSOUND, so it is not rediscovered as a surprise.
:func:`_hands_over` skips the builtin filter whenever the callee is an
ATTRIBUTE, so a C-implemented method call is counted although it gets no Python
frame. That over-reports, which is the safe direction, and every one of the
callees it counts on this tree today is a Python function.
"""

from __future__ import annotations

import ast
import builtins
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from tests.assertion_rendering_guard import REPO_ROOT, tracked_python_files
from tests.locals_rendering_guard import EXCEPT_TARGET, shipped_binding_forms

SUBPROCESS_TIMEOUT: Final = 300

#: The placeholder every arm's source carries, replaced per arm so one grep of
#: the combined report attributes each rendering to the arm that planted it.
PLACEHOLDER: Final = "__CS855_MARKER__"

# The mechanism labels. A rendering is attributed to exactly one, and the label
# is what a remedy would have to key on.
CHAINED_CONTEXT: Final = "chained-context"
CHAINED_CAUSE: Final = "chained-cause"
FRAME_ARGUMENT: Final = "frame-argument"
REWRITTEN_ASSERT: Final = "rewritten-assert"
UNCAUGHT: Final = "uncaught"
NOTHING: Final = "nothing"

#: How many DISTINCT mechanisms the arms must separate. Below this the arms have
#: measured one thing several ways, and the attribution above is decoration - a
#: result this module would report as three findings when it holds one.
DISTINCT_MECHANISMS_MEASURED: Final = 3


@dataclass(frozen=True)
class Arm:
    """One forced fixture, and what a real run was MEASURED to do with it.

    Attributes:
        source: The fixture module, carrying :data:`PLACEHOLDER` exactly once as a
            module-scope binding.
        renders: Whether the marker reaches the report under the flags this
            project ships. Graded against a real run rather than declared.
        mechanism: Which measured mechanism carries it, or :data:`NOTHING`.
        binds: Whether the fixture's handler binds a name at all. The arms that
            differ ONLY in this field are what refute the inherited attribution.
        twin: For a quiet arm, the key of the rendering arm it differs from by
            one construct. A quiet arm with no twin proves nothing - absence is
            satisfied by a fixture that never planted anything.
        discriminator: The construct that differs, as text. IT IS NOT
            DECORATION: repointing ``twin`` at an unrelated rendering arm
            survived two mutation passes, because nothing checked the
            "by one construct" half of the claim - the exact "prose wearing a
            type" defect this module says it closed. The string must appear in
            the twin's source and be absent from this one, so a repointed twin
            fails the containment rather than passing quietly. A line-count
            threshold cannot do this job: the closest NON-twin pair in this set
            also differs by a single line.
    """

    source: str
    renders: bool
    mechanism: str
    binds: bool
    twin: str | None = None
    discriminator: tuple[str, str] | None = None


def _module(body: str) -> str:
    """Wrap a fixture body with its module-scope marker binding.

    Args:
        body: The fixture's own statements.

    Returns:
        A complete module source.
    """
    return f'MARK = "{PLACEHOLDER}"\n\n{body}'


_INERT_HELPER: Final = 'def helper(problem):\n    raise RuntimeError("inert") from None\n\n'
_RAISING_HELPER: Final = 'def helper():\n    raise RuntimeError("inert")\n\n'
_CARRIER: Final = "class Boom(Exception):\n    pass\n\n"
_ATTRIBUTE_CARRIER: Final = (
    "class Boom(Exception):\n"
    "    def __init__(self, secret):\n"
    '        super().__init__("inert")\n'
    "        self.secret = secret\n\n"
)

ARMS: Final[Mapping[str, Arm]] = MappingProxyType(
    {
        # ---- CHAINED_CONTEXT: the caught exception printed above the separator.
        "chain-without-a-binding": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError:\n"
                "        count = 0\n"
                "        assert count == 1\n"
            ),
            renders=True,
            mechanism=CHAINED_CONTEXT,
            binds=False,
        ),
        "chain-with-a-binding": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                "        count = 0\n"
                "        assert count == 1\n"
            ),
            renders=True,
            mechanism=CHAINED_CONTEXT,
            binds=True,
        ),
        # NO ASSERT ANYWHERE. The tree holds zero asserts in handler bodies and
        # 115 handlers holding a call, so this is the shape the population has.
        "escape-from-a-call": Arm(
            source=_module(
                _RAISING_HELPER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                "        helper()\n"
            ),
            renders=True,
            mechanism=CHAINED_CONTEXT,
            binds=True,
        ),
        "bare-reraise": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                '        raise RuntimeError("inert")\n'
            ),
            renders=True,
            mechanism=CHAINED_CONTEXT,
            binds=True,
        ),
        # THE NARROW SUPPRESSION IS NARROW ON PURPOSE. A call that escapes
        # BEFORE the suppressing raise is reached renders anyway, so reading
        # "has a from None somewhere" as an exemption would be wrong.
        "call-escapes-before-a-from-none": Arm(
            source=_module(
                _RAISING_HELPER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                "        helper()\n"
                '        raise RuntimeError("inert") from None\n'
            ),
            renders=True,
            mechanism=CHAINED_CONTEXT,
            binds=True,
        ),
        # ---- CHAINED_CAUSE: the explicit `from exc` wording.
        "reraise-from-the-binding": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                '        raise RuntimeError("inert") from exc\n'
            ),
            renders=True,
            mechanism=CHAINED_CAUSE,
            binds=True,
        ),
        # ---- FRAME_ARGUMENT: name-keyed, and NOT closed by suppressing the chain.
        "binding-handed-to-a-failing-call": Arm(
            source=_module(
                _CARRIER + _INERT_HELPER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise Boom(MARK)\n"
                "    except Boom as exc:\n"
                "        helper(exc)\n"
            ),
            renders=True,
            mechanism=FRAME_ARGUMENT,
            binds=True,
        ),
        # ---- REWRITTEN_ASSERT: reached through the binding, message inert.
        "binding-read-in-an-assert": Arm(
            source=_module(
                _ATTRIBUTE_CARRIER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise Boom(MARK)\n"
                "    except Boom as exc:\n"
                '        assert exc.secret == ""\n'
            ),
            renders=True,
            mechanism=REWRITTEN_ASSERT,
            binds=True,
        ),
        # THE COUNTER-EXAMPLE TO THE NAME-DELETION STORY. The handler name IS
        # deleted here and the object renders anyway, from after the handler.
        "object-kept-past-the-handler": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                "        kept = exc\n"
                "    assert kept.args == ()\n"
            ),
            renders=True,
            mechanism=REWRITTEN_ASSERT,
            binds=True,
        ),
        # ---- The producer side alone, for the CS-852 gap-1 relation.
        "no-handler-anywhere": Arm(
            source=_module("def test_it() -> None:\n    raise ValueError(MARK)\n"),
            renders=True,
            mechanism=UNCAUGHT,
            binds=False,
        ),
        # ---- The quiet arms. EVERY ONE NAMES A TWIN.
        "reraise-from-none": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                '        raise RuntimeError("inert") from None\n'
            ),
            renders=False,
            mechanism=NOTHING,
            binds=True,
            twin="bare-reraise",
            discriminator=(" from None", ""),
        ),
        "binding-not-handed-over": Arm(
            source=_module(
                _CARRIER + _INERT_HELPER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise Boom(MARK)\n"
                "    except Boom as exc:\n"
                '        helper("inert")\n'
            ),
            renders=False,
            mechanism=NOTHING,
            binds=True,
            twin="binding-handed-to-a-failing-call",
            discriminator=('helper("inert")', "helper(exc)"),
        ),
        "assert-after-the-handler": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                "        seen = 1\n"
                "    count = 0\n"
                "    assert count == 1\n"
            ),
            renders=False,
            mechanism=NOTHING,
            binds=True,
            twin="chain-with-a-binding",
            discriminator=(
                "        seen = 1\n    count = 0\n    assert count == 1\n",
                "        count = 0\n        assert count == 1\n",
            ),
        ),
        "binding-reduced-inside-the-handler": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                "        raise ValueError(MARK)\n"
                "    except ValueError as exc:\n"
                "        count = len(exc.args)\n"
                "    assert count == 0\n"
            ),
            renders=False,
            mechanism=NOTHING,
            binds=True,
            twin="object-kept-past-the-handler",
            discriminator=(
                "        count = len(exc.args)\n    assert count == 0\n",
                "        kept = exc\n    assert kept.args == ()\n",
            ),
        ),
        # A REDUCTION INSIDE THE ASSERTED EXPRESSION DOES NOT HIDE ANYTHING, and
        # this arm exists because the author assumed it did. pytest's rewriter
        # reprs a call's ARGUMENTS as well as its result, so the comparison line
        # reads "assert 15 == 0" while the explanation beneath it prints
        # "where 15 = len('<the marker>')". Measured, not reasoned - it was
        # declared quiet and the module reddened.
        "reduction-inside-the-asserted-expression": Arm(
            source=_module(
                _ATTRIBUTE_CARRIER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise Boom(MARK)\n"
                "    except Boom as exc:\n"
                "        assert len(exc.secret) == 0\n"
            ),
            renders=True,
            mechanism=REWRITTEN_ASSERT,
            binds=True,
        ),
        # REDUCED BEFORE THE ASSERT - CS-850's own remedy, and the only form
        # measured to close this channel. One construct away from its twin.
        "binding-reduced-before-the-assert": Arm(
            source=_module(
                _ATTRIBUTE_CARRIER + "def test_it() -> None:\n"
                "    try:\n"
                "        raise Boom(MARK)\n"
                "    except Boom as exc:\n"
                "        count = len(exc.secret)\n"
                "        assert count == 0\n"
            ),
            renders=False,
            mechanism=NOTHING,
            binds=True,
            twin="reduction-inside-the-asserted-expression",
            discriminator=(
                "        count = len(exc.secret)\n        assert count == 0\n",
                "        assert len(exc.secret) == 0\n",
            ),
        ),
    }
)


def arm_token(key: str) -> str:
    """The marker planted in one arm's fixture.

    Args:
        key: The arm's key.

    Returns:
        An invented ASCII token unique to that arm.
    """
    return f"cs855mark{sorted(ARMS).index(key):02d}zz"


def _sandbox(root: Path, *, showlocals: bool) -> tuple[int, str]:
    """Write every arm and run real pytest over the lot, once.

    ONE SUBPROCESS FOR ALL OF THEM, one file each so their identically named
    tests cannot collide. ``-ra`` matches this project's own ``addopts``, so
    "default flags" means the flags the suite really runs under.

    Args:
        root: A directory to write into.
        showlocals: Whether to add ``-l``, which this module expects to change
            nothing.

    Returns:
        pytest's own exit code, and its combined output.
    """
    root.mkdir(parents=True, exist_ok=True)
    for key in sorted(ARMS):
        source = ARMS[key].source.replace(PLACEHOLDER, arm_token(key))
        (root / f"test_arm_{sorted(ARMS).index(key):02d}.py").write_bytes(source.encode("ascii"))
    argv = [
        sys.executable,
        "-m",
        "pytest",
        str(root),
        "-ra",
        "-p",
        "no:cacheprovider",
        "--rootdir",
        str(root),
    ]
    if showlocals:
        argv.append("-l")
    done = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=str(root),
        timeout=SUBPROCESS_TIMEOUT,
    )
    return (done.returncode, (done.stdout + done.stderr).decode("utf-8", errors="replace"))


def _measured(report: str) -> dict[str, bool]:
    """Which arms had their marker printed in one rendered report.

    Args:
        report: pytest's combined output over the arm sandbox.

    Returns:
        Arm key to whether its marker reached the report.
    """
    return {key: arm_token(key) in report for key in ARMS}


#: A rendered frame ARGUMENT line - ``problem = Boom('...')`` - printed above
#: the callee's source with no ``-l``. The anchor is the whole point: it is what
#: tells FRAME_ARGUMENT apart from an ``E`` line, and the two have different
#: remedies.
FRAME_ARGUMENT_LINE: Final = re.compile(r"^[A-Za-z_][A-Za-z_0-9]* = ")

#: Where one failure block ends and the next begins.
BLOCK_BREAK: Final = re.compile(r"^(_{5,}|={5,}|-{5,})")

#: The two sentences pytest prints between a chained pair.
CONTEXT_SENTENCE: Final = "During handling of the above exception"
CAUSE_SENTENCE: Final = "The above exception was the direct cause"

#: The crash line that opens a rendered exception - ``E   ValueError: ...``, a
#: dotted type included. The colon must follow the name immediately, so an
#: explanation line such as ``E   Left contains one more item: '...'`` does NOT
#: match and is read as a continuation of the assertion above it.
EXCEPTION_HEADER: Final = re.compile(r"^E\s+([A-Za-z_][A-Za-z_0-9.]*):\s")


#: Where pytest stops rendering failures and starts repeating them. The ``-ra``
#: summary reprints a crash line, so counting it as a second rendering would
#: report one mechanism twice.
SUMMARY_HEADING: Final = "short test summary info"


def _body_lines(report: str) -> list[str]:
    """The failure bodies, with the repeated short summary cut off.

    Args:
        report: pytest's combined output.

    Returns:
        The lines up to the summary heading.
    """
    lines = report.splitlines()
    end = next((index for index, line in enumerate(lines) if SUMMARY_HEADING in line), len(lines))
    return lines[:end]


def _attribute_all(lines: list[str], token: str) -> frozenset[str]:
    """EVERY mechanism that carried one arm's marker into the report.

    ATTRIBUTED FROM THE RENDERED SHAPE, not from the fixture. A label nothing
    compares against a measurement is prose in a field, and this module shipped
    exactly that until a mutation of the label survived a full green run.

    A SET RATHER THAN THE FIRST HIT. Reading only the first line holding the
    token recorded one mechanism for a handler that fired two, and silently: the
    second rendering had no way to redden anything. No shipped arm fires two
    today, which is a measurement this returns rather than an assumption it
    builds in.

    Args:
        lines: The report bodies, split into lines.
        token: The arm's marker.

    Returns:
        The mechanism labels, or ``{NOTHING}`` when the marker never reached the
        report.
    """
    found = {_attribute_line(lines, index) for index, line in enumerate(lines) if token in line}
    return frozenset(found) if found else frozenset({NOTHING})


def _attribute_line(lines: list[str], index: int) -> str:
    """Which mechanism one token-bearing line represents.

    Args:
        lines: The report bodies.
        index: The line holding the token.

    Returns:
        A mechanism label.
    """
    line = lines[index].strip()
    if FRAME_ARGUMENT_LINE.match(line):
        return FRAME_ARGUMENT
    if not line.startswith("E "):
        return "unattributed"
    # KEYED ON THE EXCEPTION HEADER, NOT ON A KEYWORD, because an assertion
    # rendering spans several lines and only its FIRST says "assert". pytest
    # prints "assert 15 == 0" and then "+ where 15 = len('<marker>')", or
    # "Left contains one more item: '<marker>'", beneath it - and the line that
    # actually carries the value names neither a keyword nor an exception type.
    # Matching on words filed those continuations as UNCAUGHT: a rewriter
    # rendering attributed to the chaining mechanism, which is the wrong remedy.
    # Both misattributions were caught by the module reddening, not by review.
    header = EXCEPTION_HEADER.match(line)
    if header is None or header.group(1) == "AssertionError":
        return REWRITTEN_ASSERT
    return _chained_kind(lines[index + 1 :])


def _chained_kind(following: list[str]) -> str:
    """Whether the block after a rendered exception line names a chain, and which.

    Args:
        following: The report lines after the one that carried the marker.

    Returns:
        The chaining label, or :data:`UNCAUGHT` when the block names neither -
        the shape of an exception that reached the report without being caught.
    """
    for line in following:
        if BLOCK_BREAK.match(line.strip()):
            break
        if CONTEXT_SENTENCE in line:
            return CHAINED_CONTEXT
        if CAUSE_SENTENCE in line:
            return CHAINED_CAUSE
    return UNCAUGHT


def _attributed(report: str) -> dict[str, frozenset[str]]:
    """Every arm's rendering, attributed to the mechanisms that carried it.

    Args:
        report: pytest's combined output over the arm sandbox.

    Returns:
        Arm key to the set of mechanism labels measured for it.
    """
    lines = _body_lines(report)
    return {key: _attribute_all(lines, arm_token(key)) for key in ARMS}


@dataclass(frozen=True)
class RunResult:
    """One forced sandbox run, reduced to what the arms need.

    THE REPORT TEXT IS NOT A FIELD. It carries the sandbox root, which sits
    under a home directory, so reducing it here keeps it out of every consuming
    frame - the CS-850 remedy applied to this module itself.

    Attributes:
        exit_code: pytest's own exit code from the sandbox.
        rendered: Arm key to whether its marker reached the report.
        attributed: Arm key to the SET of mechanisms measured for it. A set,
            because a handler can fire two at once and recording only the first
            hides the second with nothing able to redden.
        failed: How many arms pytest reported as failing.
    """

    exit_code: int
    rendered: Mapping[str, bool]
    attributed: Mapping[str, frozenset[str]]
    failed: int


@pytest.fixture(scope="module")
def default_run(tmp_path_factory: pytest.TempPathFactory) -> RunResult:
    """Every arm under the flags this project ships.

    Args:
        tmp_path_factory: pytest's factory.

    Returns:
        The run, reduced.
    """
    code, report = _sandbox(tmp_path_factory.mktemp("cs855_d"), showlocals=False)
    failed = sum(1 for line in report.splitlines() if line.startswith("FAILED "))
    return RunResult(code, _measured(report), _attributed(report), failed)


@pytest.fixture(scope="module")
def showlocals_run(tmp_path_factory: pytest.TempPathFactory) -> dict[str, bool]:
    """Every arm under ``-l``, to show this channel is not the locals channel.

    Args:
        tmp_path_factory: pytest's factory.

    Returns:
        The per-arm rendering.
    """
    _, report = _sandbox(tmp_path_factory.mktemp("cs855_l"), showlocals=True)
    return _measured(report)


# ---------------------------------------------------------------------------
# The controls. Every absence arm below is worthless without these.
# ---------------------------------------------------------------------------


def test_every_arm_planted_its_marker():
    """`assert MARKER not in rendered` PASSES when the marker was never planted."""
    unplanted = tuple(sorted(key for key in ARMS if PLACEHOLDER not in ARMS[key].source))
    assert unplanted == ()


def test_the_forced_arms_actually_ran_and_failed(
    default_run: RunResult,
):
    """A clean report proves nothing if nothing ran. Every arm must FAIL."""
    assert default_run.exit_code != 0
    assert default_run.failed == len(ARMS)


def test_every_quiet_arm_names_a_rendering_twin():
    """A quiet arm with no twin measures the fixture, not the construct."""
    orphaned = tuple(
        sorted(key for key, arm in ARMS.items() if not arm.renders and arm.twin is None)
    )
    assert orphaned == ()
    unknown = tuple(
        sorted(
            key
            for key, arm in ARMS.items()
            if arm.twin is not None and (arm.twin not in ARMS or not ARMS[arm.twin].renders)
        )
    )
    assert unknown == ()


def test_every_twin_is_one_stated_edit_away_from_its_quiet_arm():
    """The "differs by one construct" half of the twin claim, made checkable.

    REPOINTING ``twin`` AT AN UNRELATED RENDERING ARM SURVIVED TWO MUTATION
    PASSES while every arm stayed green, because the twin was only checked to
    exist and to render. An EXACT TRANSFORM is what closes that: applying the
    stated edit to the quiet source must reproduce the twin's source byte for
    byte, so a repointed twin cannot match. A line-count threshold was measured
    and rejected - the closest NON-twin pair in this set also differs by one
    line, so no threshold separates them.
    """
    missing = tuple(
        sorted(key for key, arm in ARMS.items() if arm.twin is not None and not arm.discriminator)
    )
    assert missing == ()
    unproven: list[str] = []
    for key, arm in ARMS.items():
        if arm.twin is None or arm.discriminator is None:
            continue
        old, new = arm.discriminator
        if arm.source.replace(old, new) != ARMS[arm.twin].source:
            unproven.append(key)
    assert tuple(sorted(unproven)) == ()


# ---------------------------------------------------------------------------
# The mechanism, measured under the flags this project actually ships.
# ---------------------------------------------------------------------------


def test_every_arm_renders_exactly_as_it_declares(
    default_run: RunResult,
):
    """The whole channel, pinned behaviourally rather than in prose."""
    measured = default_run.rendered
    disagreed = tuple(sorted(key for key, arm in ARMS.items() if measured[key] != arm.renders))
    assert disagreed == ()


def test_every_rendering_is_attributed_to_the_mechanism_it_declares(
    default_run: RunResult,
):
    """The mechanism label, graded against the SHAPE of the line that carried it.

    THIS ARM EXISTS BECAUSE ITS ABSENCE SURVIVED A GREEN RUN. Flipping a
    declared field on one arm changed nothing while all twenty tests passed, so
    every field on :class:`Arm` that no arm compares against a measurement is
    prose wearing a type. Which mechanism fires decides the remedy - suppressing
    a chain, not handing the binding over, or reducing before asserting are
    three different fixes - so an unverified label is the one thing here that
    must not rot.
    """
    disagreed = tuple(
        sorted(
            key
            for key, arm in ARMS.items()
            if default_run.attributed[key] != frozenset({arm.mechanism})
        )
    )
    assert disagreed == ()


def test_every_arm_binds_exactly_as_it_declares():
    """The ``binds`` field, derived from the fixture source rather than trusted."""
    disagreed = tuple(
        sorted(key for key, arm in ARMS.items() if (" as exc:" in arm.source) != arm.binds)
    )
    assert disagreed == ()


def test_the_mechanisms_measured_are_more_than_one():
    """A single-mechanism result would mean the arms never separated anything."""
    fired = {arm.mechanism for arm in ARMS.values() if arm.renders}
    assert len(fired) >= DISTINCT_MECHANISMS_MEASURED


def test_the_channel_renders_without_showlocals(
    default_run: RunResult,
):
    """The item's headline: this leaks with no debugging flag at all."""
    measured = default_run.rendered
    rendering = tuple(sorted(key for key, shown in measured.items() if shown))
    assert len(rendering) > 0


def test_the_showlocals_flag_changes_nothing_on_this_channel(
    default_run: RunResult,
    showlocals_run: dict[str, bool],
):
    """What separates this channel from CS-851's, asserted rather than asserted-of."""
    measured = default_run.rendered
    moved = tuple(sorted(key for key in ARMS if measured[key] != showlocals_run[key]))
    assert moved == ()


def test_the_binding_is_not_what_renders_the_chained_context(
    default_run: RunResult,
):
    """Two arms differing ONLY in the handler clause render identically.

    This is the refutation of the attribution this item inherited. If the
    ``except ... as NAME`` binding were what leaked, deleting it would go quiet.
    """
    measured = default_run.rendered
    bound = ARMS["chain-with-a-binding"]
    unbound = ARMS["chain-without-a-binding"]
    assert bound.binds
    assert not unbound.binds
    assert bound.source.replace("except ValueError as exc:", "except ValueError:") == unbound.source
    assert measured["chain-without-a-binding"]
    assert measured["chain-with-a-binding"]


def test_position_relative_to_the_handler_is_not_the_rule(
    default_run: RunResult,
):
    """Name deletion is real; it is not why an assert after the handler is quiet."""
    measured = default_run.rendered
    assert not measured["assert-after-the-handler"]
    assert measured["object-kept-past-the-handler"]


def test_the_chain_is_suppressed_only_where_nothing_escapes_first(
    default_run: RunResult,
):
    """`from None` closes the chained block, and only at the raise it guards."""
    measured = default_run.rendered
    assert not measured["reraise-from-none"]
    assert measured["bare-reraise"]
    assert measured["call-escapes-before-a-from-none"]


def test_the_frame_argument_channel_survives_chain_suppression(
    default_run: RunResult,
):
    """The name-keyed mechanism with a live population, isolated from chaining.

    Both arms suppress the chain inside the callee, so the only difference is
    whether the binding was handed over.
    """
    measured = default_run.rendered
    assert measured["binding-handed-to-a-failing-call"]
    assert not measured["binding-not-handed-over"]


# ---------------------------------------------------------------------------
# The relation to CS-852 gap 1: two channels, or one?
# ---------------------------------------------------------------------------


def test_the_binding_channel_leaks_with_an_inert_message(
    default_run: RunResult,
):
    """Q1: can this channel leak when the exception's MESSAGE carries nothing?

    ONLY THE ARMS BUILT ON THE ATTRIBUTE CARRIER ANSWER THIS, and an earlier
    version of this arm got it wrong in a way worth recording.
    ``binding-handed-to-a-failing-call`` raises ``Boom(MARK)`` on a bare
    ``Exception`` subclass, so the marker IS its ``args`` - and the guard that
    was supposed to catch that searched the source for the substring
    ``"inert"``, which the unrelated helper text satisfies. A substring of the
    fixture is not a property of the exception.

    The carrier below is checked structurally instead, by
    ``test_the_attribute_carrier_keeps_the_marker_out_of_args``: it hands
    ``super().__init__`` a literal and nothing else, so no argument can reach
    ``args`` whatever is passed in.
    """
    measured = default_run.rendered
    qualifying = tuple(
        sorted(key for key, arm in ARMS.items() if _ATTRIBUTE_CARRIER in arm.source and arm.renders)
    )
    assert len(qualifying) > 0
    for key in qualifying:
        assert measured[key]
        assert default_run.attributed[key] == frozenset({REWRITTEN_ASSERT})


def test_the_attribute_carrier_keeps_the_marker_out_of_args():
    """The carrier the Q1 arms rest on cannot put its argument into ``args``."""
    tree = ast.parse(_ATTRIBUTE_CARRIER)
    supers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "__init__"
    ]
    assert len(supers) == 1
    assert supers[0].args
    assert all(isinstance(argument, ast.Constant) for argument in supers[0].args)
    assert not supers[0].keywords


def test_the_message_channel_leaks_with_no_named_handler(
    default_run: RunResult,
):
    """Q2: can the message leak with no bound handler name anywhere?"""
    measured = default_run.rendered
    for key in ("no-handler-anywhere", "chain-without-a-binding"):
        assert not ARMS[key].binds
        assert measured[key]
    assert "except" not in ARMS["no-handler-anywhere"].source


def test_the_two_channels_are_measured_independent(
    default_run: RunResult,
):
    """The verdict, narrower than the one this module first reported.

    THE HONEST SHAPE OF IT. Q2 is unqualified: the producer leaks with no
    handler bound anywhere, and that has live instances. Q1 holds ONLY through
    REWRITTEN_ASSERT reading a NON-ARGS attribute. FRAME_ARGUMENT does not
    answer it, because a frame argument renders ``repr(exc)`` and a standard
    exception's repr IS its args - the very content the chained line prints via
    ``str()``. So the two channels are separable, and the separating construct
    has ZERO live instances on this tree: every measured leak that a real
    handler here could produce carries producer content.

    That is weaker than "independent channels, both items needed" and it is
    what was measured. The consumer-side item earns its keep by naming WHICH
    construct renders and what closes it, not by carrying content the producer
    side does not already own.
    """
    measured = default_run.rendered
    producer_independent = tuple(
        sorted(
            key
            for key, arm in ARMS.items()
            if _ATTRIBUTE_CARRIER in arm.source
            and arm.renders
            and default_run.attributed[key] == frozenset({REWRITTEN_ASSERT})
        )
    )
    assert len(producer_independent) > 0
    assert measured["no-handler-anywhere"]
    # The frame-argument arm is NOT evidence for Q1: its marker is in args.
    assert FRAME_ARGUMENT not in {
        mechanism for key in producer_independent for mechanism in default_run.attributed[key]
    }
    live_producer_independent = sum(1 for site in tree_sites() if site.reads_binding_in_an_assert)
    assert live_producer_independent == 0


# ---------------------------------------------------------------------------
# The population, DERIVED from the shipped AST rather than listed.
# ---------------------------------------------------------------------------

#: Scopes a handler body does not execute in line. A statement inside a nested
#: function runs in ITS frame, not the handler's, so it is not this handler's
#: exposure. THE SEED IS FILTERED TOO: an adversary measured that seeding the
#: walk with ``list(handler.body)`` unfiltered descended into a ``def`` written
#: directly in a handler body while skipping the same ``def`` one level deeper,
#: so the rule depended on nesting depth rather than on scope.
NESTED_SCOPES: Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

#: The three constructs whose escape from a handler body was MEASURED above -
#: ``escape-from-a-call``, ``bare-reraise`` and ``chain-with-a-binding``. The
#: set is grounded in those arms rather than in an argument about what can
#: raise, which would sweep in every attribute access in the tree.
#:
#: GRADED MEMBER BY MEMBER, not by a population floor.
#: ``test_each_escaping_construct_is_classified_on_its_own`` plants one source
#: per member, because a threshold over the pooled population is met by its
#: strongest member: reducing this tuple to ``(ast.Raise,)`` collapsed the
#: population by 77 per cent and left every arm green.
ESCAPING_NODES: Final = (ast.Call, ast.Raise, ast.Assert)

#: Names that resolve to a builtin. A builtin callee gets no Python frame, so
#: ``type(exc)`` cannot render an argument. ``str(exc)`` is a real leak on
#: CS-205's channel and is graded there, not here.
#:
#: A MODULE THAT BINDS ONE OF THESE NAMES ITSELF DEFEATS THAT REASONING, and
#: the failure direction is the dangerous one - a project ``def format(...)``
#: reads as a builtin and its hand-off goes uncounted. :func:`_shadowed` is
#: subtracted per module for that reason.
BUILTIN_NAMES: Final = frozenset(dir(builtins))


@dataclass(frozen=True)
class HandlerSite:
    """One ``except`` clause, classified by what could carry it into a report.

    Attributes:
        module: Repo-relative path, forward-slashed by git.
        lineno: The handler's own line.
        binds: Whether the clause binds a name.
        escape_capable: Whether the body holds a construct measured to escape,
            which is what opens CHAINED_CONTEXT. True for unnamed clauses too -
            the mechanism does not read the binding.
        reads_binding_in_an_assert: Whether the binding, OR a local aliased from
            it, is read inside an ``assert`` anywhere in the enclosing scope.
            This opens REWRITTEN_ASSERT.
        hands_binding_to_a_call: Whether the binding or an alias is passed to a
            non-builtin call, which opens FRAME_ARGUMENT.
        carriers: Every local measured to hold the caught exception. Always
            contains the bound name itself when the clause binds one.
    """

    module: str
    lineno: int
    binds: bool
    escape_capable: bool
    reads_binding_in_an_assert: bool
    hands_binding_to_a_call: bool
    carriers: frozenset[str]


def _own_nodes(roots: list[ast.stmt]) -> list[ast.AST]:
    """Every node under these statements that runs in the SAME frame.

    Args:
        roots: The statements to walk.

    Returns:
        The nodes, nested scopes pruned - the roots themselves included in the
        pruning, so depth cannot change the answer.
    """
    found: list[ast.AST] = []
    stack: list[ast.AST] = [node for node in roots if not isinstance(node, NESTED_SCOPES)]
    while stack:
        node = stack.pop()
        found.append(node)
        stack += [
            child for child in ast.iter_child_nodes(node) if not isinstance(child, NESTED_SCOPES)
        ]
    return found


def _reads_any(node: ast.AST | None, names: frozenset[str]) -> bool:
    """Whether an expression reads any of these bare names.

    Args:
        node: The expression, or None.
        names: The names to look for.

    Returns:
        True when one is read anywhere inside.
    """
    if node is None:
        return False
    return any(isinstance(inner, ast.Name) and inner.id in names for inner in ast.walk(node))


def _carriers(handler: ast.ExceptHandler) -> frozenset[str]:
    """Every local that holds the caught exception, following aliases.

    THE ALIAS IDIOM IS LIVE IN SHIPPED CODE - ``last = exc`` inside the handler
    with the object used after it - so a detector keyed on the bound name alone
    reports a clean sheet over a construct the tree really ships. Followed
    transitively to a fixed point, because ``a = exc`` then ``b = a`` is one
    statement further out and the same defect.

    Args:
        handler: The clause.

    Returns:
        The bound name plus every alias, or an empty set for an unnamed clause.
    """
    if handler.name is None:
        return frozenset()
    carriers = {handler.name}
    for _ in range(len(handler.body) + 1):
        grown = set(carriers)
        for node in _own_nodes(list(handler.body)):
            value: ast.expr | None = None
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                value, targets = node.value, list(node.targets)
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
                value, targets = node.value, [node.target]
            if not (isinstance(value, ast.Name) and value.id in carriers):
                continue
            grown |= {target.id for target in targets if isinstance(target, ast.Name)}
        if grown == carriers:
            break
        carriers = grown
    return frozenset(carriers)


def _shadowed(tree: ast.Module) -> frozenset[str]:
    """Builtin names this module binds itself, so they are not builtins here.

    Args:
        tree: The parsed module.

    Returns:
        The shadowing names.
    """
    bound: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Assign):
            bound |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            bound |= {alias.asname or alias.name.split(".")[0] for alias in node.names}
    return frozenset(bound & BUILTIN_NAMES)


def _call_arguments(node: ast.Call) -> list[ast.expr]:
    """Every expression handed to a call, unpacking included.

    ``f(*[exc])`` AND ``f(**{"k": exc})`` REACH THE CALLEE'S FRAME exactly as
    ``f(exc)`` does - both measured to render - and reading only ``node.args``
    and ``keyword.value`` misses them, because the starred form arrives as
    ``ast.Starred`` and the double-star as a keyword whose ``arg`` is None.

    WHAT IS DELIBERATELY NOT UNWRAPPED, because widening here silently merges
    two channels. Only an expression that IS the object counts. ``f(str(exc))``
    hands the callee a STRING, so the frame renders a message and not the
    exception - that is CS-205's channel, graded in
    ``tests/test_exception_rendering.py``. Walking every argument subtree for
    the name instead took this population from 42 to 92 by absorbing exactly
    those message-shaped calls.

    Args:
        node: The call.

    Returns:
        The expressions that ARE the handed-over object, one container level
        unwrapped for the two unpacking forms.
    """
    passed: list[ast.expr] = []
    for argument in node.args:
        passed += _unwrapped(argument.value) if isinstance(argument, ast.Starred) else [argument]
    for keyword in node.keywords:
        passed += _unwrapped(keyword.value) if keyword.arg is None else [keyword.value]
    return passed


def _unwrapped(node: ast.expr) -> list[ast.expr]:
    """One container level of an unpacked argument.

    Args:
        node: The expression after ``*`` or ``**``.

    Returns:
        Its elements when it is a literal container, else the expression itself.
    """
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return list(node.elts)
    if isinstance(node, ast.Dict):
        return [value for value in node.values if value is not None]
    return [node]


def _hands_over(nodes: list[ast.AST], carriers: frozenset[str], shadowed: frozenset[str]) -> bool:
    """Whether a carrier is passed to a call that gets a Python frame.

    Args:
        nodes: The handler body's nodes.
        carriers: The bound name and its aliases.
        shadowed: Builtin names this module rebinds.

    Returns:
        True when at least one such call exists.
    """
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in BUILTIN_NAMES and func.id not in shadowed:
            continue
        if any(
            isinstance(argument, ast.Name) and argument.id in carriers
            for argument in _call_arguments(node)
        ):
            return True
    return False


def _scopes(tree: ast.Module) -> list[ast.AST]:
    """Every scope that can hold an assert able to read a handler's alias.

    Args:
        tree: The parsed module.

    Returns:
        The module and every function definition in it.
    """
    return [tree] + [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def sites_in_source(module: str, source: str) -> list[HandlerSite]:
    """Classify every ``except`` clause in one source.

    THE CONTROL PATH TOO. The same function runs over synthetic sources with a
    planted shape, so a detector that finds nothing in the tree is told apart
    from a detector that looks for nothing.

    THE ASSERT SEARCH SPANS THE ENCLOSING SCOPE, not the handler body. An alias
    OUTLIVES the handler - Python deletes the bound name and not what was
    copied out of it - so ``kept = exc`` inside and ``assert kept.secret == ""``
    after is a rendering this module measures as one. Searching the whole scope
    over-approximates, since an assert BEFORE the try cannot read the alias, and
    over-reporting is the direction that does not hide a disclosure.

    Args:
        module: A label for the sites.
        source: Python source.

    Returns:
        One record per clause.
    """
    tree = ast.parse(source)
    shadowed = _shadowed(tree)
    asserts: dict[int, list[ast.AST]] = {}
    owner: dict[int, int] = {}
    for scope in _scopes(tree):
        body = list(getattr(scope, "body", []))
        own = _own_nodes(body)
        asserts[id(scope)] = [node for node in own if isinstance(node, ast.Assert)]
        for node in own:
            if isinstance(node, ast.ExceptHandler):
                owner[id(node)] = id(scope)

    sites: list[HandlerSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        nodes = _own_nodes(list(node.body))
        carriers = _carriers(node)
        reachable = asserts.get(owner.get(id(node), id(tree)), [])
        sites.append(
            HandlerSite(
                module=module,
                lineno=node.lineno,
                binds=node.name is not None,
                escape_capable=any(isinstance(item, ESCAPING_NODES) for item in nodes),
                reads_binding_in_an_assert=bool(carriers)
                and any(
                    isinstance(item, ast.Assert)
                    and (_reads_any(item.test, carriers) or _reads_any(item.msg, carriers))
                    for item in reachable
                ),
                hands_binding_to_a_call=bool(carriers) and _hands_over(nodes, carriers, shadowed),
                carriers=carriers,
            )
        )
    return sites


@cache
def tree_sites() -> tuple[HandlerSite, ...]:
    """Every ``except`` clause in the tree, classified.

    Returns:
        The records, derived on every run. Nothing here is listed.
    """
    found: list[HandlerSite] = []
    for relative in tracked_python_files():
        source = (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        found += sites_in_source(relative, source)
    return tuple(found)


def test_the_derived_population_agrees_with_the_shipped_census():
    """Two independent derivations of the same population, compared.

    A blind spot in EITHER reddens, which is the fault that let this form read
    as absent for many sessions - the CS-851 census could not match ``ast.Try``
    at all, so it counted zero while the tree held more than a hundred. No
    number is written down here: both sides are measured on every run.

    THE NUMBER IN THE ITEM NOTE WENT STALE; IT WAS NOT WRONG. Counting named
    handlers out of git objects at the commit that closed the ``ast.Try`` hole
    gives exactly the figure ``docs/LEDGER.md`` records, over fewer files than
    the tree now holds, and the escape-capable subset was a DIFFERENT number
    then - so the two were never the same measurement wearing one name. The
    disposition is "derive it, do not quote it", which is what this arm does.
    """
    mine = sum(1 for site in tree_sites() if site.binds)
    theirs = shipped_binding_forms()[EXCEPT_TARGET]
    assert mine == theirs


def test_each_escaping_construct_is_classified_on_its_own():
    """Every member of :data:`ESCAPING_NODES`, planted alone.

    A POPULATION FLOOR IS MET BY ITS STRONGEST MEMBER - see
    ``memory/a-guard-can-be-green-by-accident.md``. Reducing that tuple to
    ``(ast.Raise,)`` collapsed the escape-capable population by 77 per cent and
    left every arm in this module green, because the only checks over it were
    "greater than zero". One planted source per member reddens on exactly the
    member that was dropped, and the two negatives redden if the classifier is
    forced true.
    """
    planted = {
        "call": ("        g()\n", True),
        "raise": ("        raise RuntimeError\n", True),
        "assert": ("        assert seen == 0\n", True),
        "assignment": ("        seen = 1\n", False),
        "pass": ("        pass\n", False),
    }
    wrong = []
    for label, (body, expected) in sorted(planted.items()):
        source = "def f():\n    seen = 0\n    try:\n        h()\n    except ValueError as exc:\n"
        sites = [site for site in sites_in_source(label, source + body) if site.binds]
        if len(sites) != 1 or sites[0].escape_capable != expected:
            wrong.append(label)
    assert tuple(wrong) == ()


def test_the_graded_population_is_not_empty():
    """An empty population satisfies every zero. This module must grade something."""
    named = sum(1 for site in tree_sites() if site.binds)
    exposed = sum(1 for site in tree_sites() if site.escape_capable)
    assert named > 0
    assert exposed > 0


def test_no_named_handler_in_the_tree_reads_its_binding_in_an_assert():
    """The REWRITTEN_ASSERT population, asserted empty - with a detector proven able.

    THE ZERO IS SYNTACTIC AND ITS NAME OVERSTATES IT. What is measured: no
    ``except`` clause has an ``assert`` in its enclosing scope reading the bound
    name or a local aliased from it. What is NOT measured: that no assert can
    render a caught exception. Five constructs defeated a narrower version of
    this detector while rendering, and nothing proves the repaired list is
    complete.

    An arrival reddens this. A departure cannot, because the set is already
    empty, and saying so is worth more than a both-directions claim that is
    vacuous in one of them.
    """
    offenders = tuple(
        sorted(
            f"{site.module}:{site.lineno}"
            for site in tree_sites()
            if site.reads_binding_in_an_assert
        )
    )
    assert offenders == ()


def test_the_detector_finds_a_planted_binding_read_in_an_assert():
    """The positive control for the zero above, and the negative that bounds it.

    THE ALIASED ARM USED TO BE PINNED AS A NON-FINDING HERE, and that was this
    module contradicting itself in one file: the same source is
    ``ARMS["object-kept-past-the-handler"]``, declared ``renders=True``. A
    detector keyed on the bare bound name reported it clean while the arm beside
    it measured the marker in the report. The alias is followed now, so the two
    halves agree, and the negative below is a shape that really does read
    nothing of the exception rather than one that merely renamed it.
    """
    planted = sites_in_source(
        "<planted>",
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except ValueError as exc:\n"
        "        assert exc.args == ()\n",
    )
    aliased = sites_in_source(
        "<aliased>",
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except ValueError as exc:\n"
        "        kept = exc\n"
        "    assert kept.args == ()\n",
    )
    unrelated = sites_in_source(
        "<unrelated>",
        "def f():\n"
        "    seen = 0\n"
        "    try:\n"
        "        g()\n"
        "    except ValueError as exc:\n"
        "        seen = 1\n"
        "    assert seen == 0\n",
    )
    assert sum(1 for site in planted if site.reads_binding_in_an_assert) == 1
    assert sum(1 for site in aliased if site.reads_binding_in_an_assert) == 1
    assert sum(1 for site in unrelated if site.reads_binding_in_an_assert) == 0


def test_the_detector_follows_the_alias_idiom_the_tree_actually_ships():
    """`last = exc` inside the handler, the object used after it - a live shape.

    Verified in shipped code at ``clockspeed/data/version.py`` and
    ``clockspeed/save/workdir.py``, each a retry loop that keeps the last
    failure. Keyed on the SHAPE rather than on those two line numbers, which
    drift; the arm asserts only that the tree still contains the idiom and that
    the detector resolves more than the bound name at those sites.
    """
    aliasing = tuple(site for site in tree_sites() if len(site.carriers) > 1)
    assert len(aliasing) > 0
    assert all(site.binds for site in aliasing)


def test_the_frame_argument_population_is_not_empty():
    """The name-keyed exposure that DOES have live instances.

    Keying this item on "an assert inside a handler body" would grade zero and
    report green. This is the arm that stops that, and it is why the module
    does not close on the empty set above.
    """
    exposed = sum(1 for site in tree_sites() if site.hands_binding_to_a_call)
    reads = sum(1 for site in tree_sites() if site.reads_binding_in_an_assert)
    assert exposed > reads


def test_the_detector_finds_a_planted_hand_off_and_ignores_a_builtin_one():
    """Every hand-off shape this detector claims to see, planted one at a time.

    EACH SHAPE HERE WAS MEASURED TO RENDER AND TO DEFEAT AN EARLIER VERSION OF
    THIS DETECTOR. None of them has a live instance in the tree, so the tree
    cannot grade them and only a planted source can: disabling the starred
    unwrap, or the shadowed-builtin subtraction, left every other arm in this
    module green. A repair with no control proving it is a claim, not a fix.

    The two negatives bound it. ``type(exc)`` is a real builtin and gets no
    Python frame; ``helper(str(exc))`` hands over a STRING, which is CS-205's
    channel and not this one.
    """
    positives = {
        "bare": "        helper(exc)\n",
        "starred": "        helper(*[exc])\n",
        "doublestar": '        helper(**{"problem": exc})\n',
        "aliased": "        kept = exc\n        helper(kept)\n",
    }
    negatives = {
        "builtin": "        name = type(exc).__name__\n",
        "message-only": "        helper(str(exc))\n",
    }
    prologue = "def f():\n    try:\n        g()\n    except ValueError as exc:\n"
    wrong = []
    for label, body in sorted(positives.items()):
        sites = sites_in_source(label, prologue + body)
        if sum(1 for site in sites if site.hands_binding_to_a_call) != 1:
            wrong.append(f"positive:{label}")
    for label, body in sorted(negatives.items()):
        sites = sites_in_source(label, prologue + body)
        if sum(1 for site in sites if site.hands_binding_to_a_call) != 0:
            wrong.append(f"negative:{label}")
    # A module-level def SHADOWING a builtin name is not a builtin. Measured to
    # render, and read as a builtin - hence uncounted - before this subtraction.
    shadowing = sites_in_source(
        "<shadowed>",
        'def format(problem):\n    raise RuntimeError("inert") from None\n\n'
        + prologue
        + "        format(exc)\n",
    )
    if sum(1 for site in shadowing if site.hands_binding_to_a_call) != 1:
        wrong.append("positive:shadowed-builtin")
    assert tuple(wrong) == ()


def test_the_chained_population_is_not_confined_to_named_handlers():
    """CHAINED_CONTEXT reads no binding, so grading only named clauses under-reports.

    Mechanised from the arms above: ``chain-without-a-binding`` renders. If this
    exposure were name-keyed, no unnamed clause could carry it.
    """
    unnamed_exposed = sum(1 for site in tree_sites() if site.escape_capable and not site.binds)
    assert unnamed_exposed > 0
