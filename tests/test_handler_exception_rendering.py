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
REWRITTEN_ASSERT, and they behave oppositely on this tree. No handler anywhere
reads its binding inside an ``assert`` - that population is EMPTY and is
asserted empty with a detector proven able to find a planted one, because an
empty population satisfies every zero and this item's own history is the proof:
the CS-851 census read ZERO named handlers for many sessions while the tree held
more than a hundred, because nothing in it could match ``ast.Try``. The
FRAME_ARGUMENT population is NOT empty, and it is the finding that keeps this
module from grading nothing.

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

THE MARKERS ARE INVENTED ASCII TOKENS. Nothing forced by this module plants a
real path, account id or world name, and every fixture binds its marker at
MODULE scope so that the source echo prints the identifier rather than the
value - the channel CS-850 measured while building its own forced arms.
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
    """

    source: str
    renders: bool
    mechanism: str
    binds: bool
    twin: str | None = None


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
        ),
        "nothing-carried-through-the-binding": Arm(
            source=_module(
                "def test_it() -> None:\n"
                "    try:\n"
                '        raise ValueError("inert")\n'
                "    except ValueError as exc:\n"
                "        count = len(MARK)\n"
                "        assert count == 0\n"
            ),
            renders=False,
            mechanism=NOTHING,
            binds=True,
            twin="binding-read-in-an-assert",
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


def _attribute_one(lines: list[str], token: str) -> str:
    """Which mechanism carried one arm's marker into the report.

    ATTRIBUTED FROM THE RENDERED SHAPE, not from the fixture. A label nothing
    compares against a measurement is prose in a field, and this module shipped
    exactly that until a mutation of the label survived a full green run.

    Args:
        lines: The report, split into lines.
        token: The arm's marker.

    Returns:
        One of the mechanism labels, or :data:`NOTHING` when the marker never
        reached the report.
    """
    hit = next((index for index, line in enumerate(lines) if token in line), None)
    if hit is None:
        return NOTHING
    line = lines[hit].strip()
    if FRAME_ARGUMENT_LINE.match(line):
        return FRAME_ARGUMENT
    if not line.startswith("E "):
        return "unattributed"
    return REWRITTEN_ASSERT if "assert" in line else _chained_kind(lines[hit + 1 :])


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


def _attributed(report: str) -> dict[str, str]:
    """Every arm's rendering, attributed to the mechanism that carried it.

    Args:
        report: pytest's combined output over the arm sandbox.

    Returns:
        Arm key to mechanism label.
    """
    lines = report.splitlines()
    return {key: _attribute_one(lines, arm_token(key)) for key in ARMS}


@dataclass(frozen=True)
class RunResult:
    """One forced sandbox run, reduced to what the arms need.

    THE REPORT TEXT IS NOT A FIELD. It carries the sandbox root, which sits
    under a home directory, so reducing it here keeps it out of every consuming
    frame - the CS-850 remedy applied to this module itself.

    Attributes:
        exit_code: pytest's own exit code from the sandbox.
        rendered: Arm key to whether its marker reached the report.
        attributed: Arm key to the mechanism that carried it.
        failed: How many arms pytest reported as failing.
    """

    exit_code: int
    rendered: Mapping[str, bool]
    attributed: Mapping[str, str]
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
        sorted(key for key, arm in ARMS.items() if default_run.attributed[key] != arm.mechanism)
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

    Both arms raise an exception whose ``args`` are the literal "inert", so the
    chained block prints nothing of interest and the producer side is clean.
    """
    measured = default_run.rendered
    for key in ("binding-read-in-an-assert", "binding-handed-to-a-failing-call"):
        assert '"inert"' in ARMS[key].source
        assert measured[key]


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
    """The verdict, as a live measurement rather than a sentence.

    Each channel leaks with the other's ingredient removed, so neither item
    subsumes the other and both are needed.
    """
    measured = default_run.rendered
    binding_without_message = measured["binding-handed-to-a-failing-call"]
    message_without_binding = measured["no-handler-anywhere"]
    assert binding_without_message
    assert message_without_binding


# ---------------------------------------------------------------------------
# The population, DERIVED from the shipped AST rather than listed.
# ---------------------------------------------------------------------------

#: Scopes a handler body does not execute in line. A statement inside a nested
#: function runs in ITS frame, not the handler's, so it is not this handler's
#: exposure.
NESTED_SCOPES: Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

#: The three constructs whose escape from a handler body was MEASURED above -
#: ``escape-from-a-call``, ``bare-reraise`` and ``chain-with-a-binding``. The
#: set is grounded in those arms rather than in an argument about what can
#: raise, which would sweep in every attribute access in the tree.
ESCAPING_NODES: Final = (ast.Call, ast.Raise, ast.Assert)

#: Names that resolve to a builtin. A builtin callee gets no Python frame, so
#: ``type(exc)`` cannot render an argument. ``str(exc)`` is a real leak on
#: CS-205's channel and is graded there, not here.
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
        reads_binding_in_an_assert: Whether the bound name is read inside an
            ``assert`` in the body, which opens REWRITTEN_ASSERT.
        hands_binding_to_a_call: Whether the bound name is passed as an argument
            to a non-builtin call, which opens FRAME_ARGUMENT.
    """

    module: str
    lineno: int
    binds: bool
    escape_capable: bool
    reads_binding_in_an_assert: bool
    hands_binding_to_a_call: bool


def _body_nodes(handler: ast.ExceptHandler) -> list[ast.AST]:
    """Every node in a handler body, NOT descending into a nested scope.

    Args:
        handler: The clause.

    Returns:
        The nodes that run in the handler's own frame.
    """
    found: list[ast.AST] = []
    stack: list[ast.AST] = list(handler.body)
    while stack:
        node = stack.pop()
        found.append(node)
        stack += [
            child for child in ast.iter_child_nodes(node) if not isinstance(child, NESTED_SCOPES)
        ]
    return found


def _reads_name(node: ast.AST | None, name: str) -> bool:
    """Whether an expression reads a bare name.

    Args:
        node: The expression, or None.
        name: The name to look for.

    Returns:
        True when the name is read anywhere inside.
    """
    if node is None:
        return False
    return any(isinstance(inner, ast.Name) and inner.id == name for inner in ast.walk(node))


def _hands_over(nodes: list[ast.AST], name: str) -> bool:
    """Whether the bound name is passed to a non-builtin call.

    Args:
        nodes: The handler body's nodes.
        name: The bound name.

    Returns:
        True when at least one such call exists.
    """
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in BUILTIN_NAMES:
            continue
        passed = [*node.args, *(keyword.value for keyword in node.keywords)]
        if any(isinstance(arg, ast.Name) and arg.id == name for arg in passed):
            return True
    return False


def sites_in_source(module: str, source: str) -> list[HandlerSite]:
    """Classify every ``except`` clause in one source.

    THE CONTROL PATH TOO. The same function runs over synthetic sources with a
    planted shape, so a detector that finds nothing in the tree is told apart
    from a detector that looks for nothing.

    Args:
        module: A label for the sites.
        source: Python source.

    Returns:
        One record per clause.
    """
    sites: list[HandlerSite] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ExceptHandler):
            continue
        nodes = _body_nodes(node)
        name = node.name
        sites.append(
            HandlerSite(
                module=module,
                lineno=node.lineno,
                binds=name is not None,
                escape_capable=any(isinstance(item, ESCAPING_NODES) for item in nodes),
                reads_binding_in_an_assert=name is not None
                and any(
                    isinstance(item, ast.Assert)
                    and (_reads_name(item.test, name) or _reads_name(item.msg, name))
                    for item in nodes
                ),
                hands_binding_to_a_call=name is not None and _hands_over(nodes, name),
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
    """
    mine = sum(1 for site in tree_sites() if site.binds)
    theirs = shipped_binding_forms()[EXCEPT_TARGET]
    assert mine == theirs


def test_the_graded_population_is_not_empty():
    """An empty population satisfies every zero. This module must grade something."""
    named = sum(1 for site in tree_sites() if site.binds)
    exposed = sum(1 for site in tree_sites() if site.escape_capable)
    assert named > 0
    assert exposed > 0


def test_no_named_handler_in_the_tree_reads_its_binding_in_an_assert():
    """The REWRITTEN_ASSERT population, asserted empty - with a detector proven able.

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
    """The positive control for the zero above."""
    planted = sites_in_source(
        "<planted>",
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except ValueError as exc:\n"
        "        assert exc.args == ()\n",
    )
    outside = sites_in_source(
        "<outside>",
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except ValueError as exc:\n"
        "        kept = exc\n"
        "    assert kept.args == ()\n",
    )
    assert sum(1 for site in planted if site.reads_binding_in_an_assert) == 1
    assert sum(1 for site in outside if site.reads_binding_in_an_assert) == 0


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
    """The positive control, and the boundary that keeps it from over-reporting."""
    handed = sites_in_source(
        "<handed>",
        "def f():\n    try:\n        g()\n    except ValueError as exc:\n        helper(exc)\n",
    )
    builtin_only = sites_in_source(
        "<builtin>",
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except ValueError as exc:\n"
        "        name = type(exc).__name__\n",
    )
    assert sum(1 for site in handed if site.hands_binding_to_a_call) == 1
    assert sum(1 for site in builtin_only if site.hands_binding_to_a_call) == 0


def test_the_chained_population_is_not_confined_to_named_handlers():
    """CHAINED_CONTEXT reads no binding, so grading only named clauses under-reports.

    Mechanised from the arms above: ``chain-without-a-binding`` renders. If this
    exposure were name-keyed, no unnamed clause could carry it.
    """
    unnamed_exposed = sum(1 for site in tree_sites() if site.escape_capable and not site.binds)
    assert unnamed_exposed > 0
