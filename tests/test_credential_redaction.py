"""CS-1156 - a credential must not survive a rendered failure report.

THE DEFECT, MEASURED RATHER THAN REASONED ABOUT. On 2026-09-19 a suite run
failed on an unrelated `FileNotFoundError` inside `tests/test_pre_push_ref_race.py`,
and pytest rendered the frame it crashed in. That frame was a
``subprocess.run(..., env=...)`` call, so the rendered arguments were the WHOLE
environment dict - and this machine's environment carries an `sk-ant-` prefixed
admin key. The key printed in full, beside a home path the shipped redactor DID
replace, which is what makes the surviving credential look deliberate rather
than missed.

`tests/conftest.py::redact_personal_data` says plainly what it covers - a home
path and the account name - and a credential is not personal data, so this is
not a bug in that function. It is a class of secret nothing owned. Every test
log, every CI artifact and every pasted failure is an echo path; CLAUDE.md
non-negotiable 12 states exactly this rule for save-header bytes and nothing
stated it for credentials.

WHY EVERY ARM HERE RUNS A REAL PYTEST SUBPROCESS. A unit call of the redactor
grades the function; it does not grade the RENDER PATH, and the render path is
where the leak happened. The report hook has to be reached for the measurement
to mean anything, so the arms drive a child pytest with `tests.conftest` loaded
as a plugin - which is what makes its hooks fire on a target outside this
rootdir - and read the child's combined output.

THE CHILD'S ENVIRONMENT IS STRIPPED OF REAL CREDENTIALS BEFORE IT STARTS, and
that is a correctness property rather than hygiene. An adversary measured the
first build's placeholder arm passing under a MUTANT, because a real key in the
inherited environment supplied the placeholder the arm was looking for. With the
environment stripped, the only credential in the child's report is the one the
arm planted, so every assertion is about that plant and the arms behave the same
here as on a CI runner that holds no key at all.

THE CONTROL THAT MAKES A GREEN MEAN SOMETHING. A child that never rendered the
frame would show no secret for a reason that has nothing to do with redaction,
and would pass. So every arm first asserts that the frame it grades actually
reached the report.

THE CONTROL IS NOT THE HOME PLACEHOLDER, AND THE REASON IS MEASURED. The first
build asserted `REDACTED_HOME` was present, on the reasoning that it proves the
report hook ran. It does not, and it is not even stable: when the child's
rootdir sits deep under the home directory - which is exactly where a
`tmp_path_factory` directory sits, and NOT where a `tempfile.mkdtemp` one sits -
pytest renders stdlib frames as RELATIVE paths, so no absolute home path is
emitted and there is nothing for the home rule to rewrite. The same child
command was measured green from a plain parent and red from a pytest parent for
that reason alone. A control that reports on how deep a temporary directory
happens to be is a control about nothing.
"""

from __future__ import annotations

import getpass
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

from tests.conftest import (
    _CREDENTIAL_MIN_LITERAL,
    _CREDENTIAL_VARIABLES,
    REDACTED_CREDENTIAL,
    UNCOVERED_SECRETS,
    redact_credentials,
    redact_report,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Synthetic and never real. The prefix is the vendor-assigned one the shape
#: rule anchors on; everything after it is a literal this file authored, so a
#: grep of the repository for a real key cannot match it.
PLANTED_KEY = "sk-ant-admin01-" + "Z" * 40

#: A second shape, so a green is not a statement about one prefix.
PLANTED_GH_TOKEN = "ghp_" + "Q" * 36

#: A credential with NO vendor prefix at all. Only a LITERAL rule can reach
#: this, which is what makes it the arm that grades the literal half - see
#: :func:`test_a_prefixless_secret_in_a_listed_variable_does_not_survive`.
PLANTED_BARE_TOKEN = "7f3a" * 10

#: The variable the shape arms plant under. Deliberately NOT one of the names
#: `tests/conftest.py` lists: an arm that planted a listed name would be graded
#: by the literal rule as well and would say nothing about the shape rule.
UNLISTED_VARIABLE = "CS1156_UNLISTED_PROBE"

#: The variable the literal arm plants under. Deliberately one that IS listed,
#: because a literal rule is only built for a listed name.
LISTED_VARIABLE = "CODSPEED_TOKEN"

#: The child's own program name, which pytest renders in the traceback body on
#: every run. Its presence proves the body was rendered at all.
RENDERED_BODY_MARKER = "zz-cs1156-no-such-program-zz"

#: The name of the frame local the runtime child binds the secret to. Under
#: ``--showlocals`` pytest renders ``leaked = '...'``, so this marker's
#: presence proves the CHANNEL THE SECRET TRAVELS THROUGH reached the report,
#: which is what a control has to prove.
#:
#: IT IS NOT AN ENVIRONMENT VARIABLE NAME, AND THAT IS THE REPAIR. The first
#: build used ALLUSERSPROFILE, which every Windows environment carries and NO
#: ubuntu runner does, so the control could not hold in CI and tier 1 went red
#: on a suite that was green on Windows. A control naming a platform-specific
#: value grades the platform rather than the mechanism.
RENDERED_LOCAL_MARKER = "leaked"

SUBPROCESS_TIMEOUT = 180

#: The leak as it was filed: a failure DURING A TEST.
#:
#: WHY THE SECRET IS BOUND TO A LOCAL AND NOT LEFT IN THE ENV DICT ALONE. The
#: first build planted it in the environment and relied on the rendered
#: ``env={...}`` argument to carry it. pytest TRUNCATES a long dict repr, and a
#: variable added last falls outside the shown portion - so the arm measured
#: nothing and passed. The local is rendered in full under ``--showlocals``, and
#: the env dict is still passed, because it is what the filed leak rendered.
CHILD_AT_RUNTIME = """
import os
import subprocess


def test_the_env_frame_renders():
    leaked = os.environ["{variable}"]
    subprocess.run(["zz-cs1156-no-such-program-zz"], env=dict(os.environ), check=False)
"""

#: The same secret raised at MODULE level, so it fails during COLLECTION. An
#: adversary reproduced the original leak here after the first build shipped,
#: because a collection failure is rendered from a CollectReport that no hook
#: touched. There are no frame locals at module level, so the value travels in
#: the exception message - which is the ``longrepr`` and ``reprcrash`` channel
#: :func:`tests.conftest._redact_report` reads.
CHILD_AT_COLLECTION = """
import os

raise RuntimeError(
    "zz-cs1156-no-such-program-zz " + os.environ["{variable}"]
)


def test_never_reached():
    pass
"""

#: The secret through CAPTURED OUTPUT rather than through a frame or a message.
#: This is the ``report.sections`` channel, a render site no arm covered before.
CHILD_AT_STDOUT = """
import os


def test_the_captured_output_renders():
    print("zz-cs1156-no-such-program-zz", os.environ["{variable}"])
    raise AssertionError("forced, so the captured section is rendered")
"""

#: CS-820 - the secret through a test PARAMETER, the door the item names:
#: pytest renders a failing test's ARGUMENTS at the top of its frame, so a test
#: taking an environment mapping prints the mapping. Two parameter kinds, a
#: fixture and a parametrize argument, each a whole environment mapping.
#:
#: THE PLANTS ARE NAMED TO SORT FIRST, AND THAT IS MEASURED, NOT STYLE. pytest
#: renders an argument through a repr that SORTS a dict's keys and shows only
#: the first four, at every verbosity. A plant under a name sorting after the
#: fourth key never reaches the report and the arm would measure nothing - the
#: first build of this arm counted zero markers for exactly that reason. The
#: filed leak was the same mechanism in the other direction: `ANTHROPIC_` keys
#: sort near the front of a real environment.
#:
#: NO VALUE IN THIS SOURCE IS ONE THE PARENT COUNTS. The marker is assembled
#: from two fragments and the plants are read from the environment, because
#: pytest prints the SOURCE of the failing function - decorators included - and
#: a marker spelled whole there would be counted whether or not the arguments
#: were rendered.
#:
#: THE REST OF THE CHILD IS THE ADVERSARY'S REFUTATION OF THE FIRST BUILD, each
#: door measured leaking on the frozen candidate:
#:
#: - A CUT. At default verbosity pytest cuts a long argument repr in the MIDDLE
#:   and joins the halves with ``...``. A cut inside a token leaves a prefix and
#:   a few characters - under a length floor - on one side, and a bare tail on
#:   the other; a cut inside a home path leaves the account name's last letters.
#:   The sweeps move the cut across every offset of both, from the head side
#:   and from the tail side.
#: - A TEST ID. A parametrize id is printed in the section header and on the
#:   FAILED line, and the report hooks never saw a node id: an id derived from
#:   the mapping's items, from an ``ids=`` callable and from an ``ids=`` list.
#: - AN ASSERTION DIFF, which renders the mapping through the same cut.
#: - A SHORTENED TOKEN with no cut marker beside it - a prefix and ten
#:   characters, under the length floor the first build's shapes carried.
CHILD_AT_PARAMETER = """
import os
from pathlib import Path

import pytest

MARKER = "AAAA-zz-cs820-" + "rendered-arg-zz"
VARIABLES = {variables!r}
KEY = os.environ[VARIABLES[0]]
TOKEN = os.environ[VARIABLES[1]]
BARE = os.environ[{bare!r}]
HOME = str(Path.home())
PLANTED = {{"AAAA_KEY": KEY, "AAAA_TOKEN": TOKEN}}


def mapping():
    planted = {{name: os.environ[name] for name in VARIABLES}}
    return {{MARKER: "1", **planted, **os.environ}}


@pytest.fixture
def environment():
    return mapping()


@pytest.mark.parametrize("parameter", [mapping()])
def test_a_parameter_holds_an_environment_mapping(parameter, environment):
    raise RuntimeError("zz-cs1156-no-such-program-zz")


@pytest.mark.parametrize(
    "parameter",
    [
        {{
            "AAAA_pad": "p" * width,
            "AAAA_tok": TOKEN,
            "AAAB_key": KEY,
            "AAAC_bare": BARE,
            "ZZZZ": "q" * 300,
        }}
        for width in range(40, 125)
    ],
)
def test_a_cut_lands_inside_a_token(parameter):
    raise RuntimeError("forced")


@pytest.mark.parametrize(
    "parameter",
    [
        {{"AAAA_pad": "p" * 300, "ZZZA_bare": BARE, "ZZZZ": "q" * width}}
        for width in range(0, 125)
    ],
)
def test_a_cut_leaves_only_a_token_tail(parameter):
    raise RuntimeError("forced")


@pytest.mark.parametrize(
    "parameter",
    ["p" * width + HOME + "q" * 300 for width in range(60, 125)]
    + ["p" * 300 + HOME + "q" * width for width in range(60, 125)],
)
def test_a_cut_lands_inside_a_home_path(parameter):
    raise RuntimeError("forced")


@pytest.mark.parametrize("name,value", sorted(PLANTED.items()))
def test_an_id_from_the_items(name, value):
    raise RuntimeError("forced")


@pytest.mark.parametrize("parameter", [PLANTED], ids=lambda planted: planted["AAAA_KEY"])
def test_an_id_from_a_callable(parameter):
    raise RuntimeError("forced")


@pytest.mark.parametrize("parameter", [PLANTED], ids=[TOKEN])
def test_an_id_from_a_list(parameter):
    raise RuntimeError("forced")


def test_an_assertion_diff_renders_the_mapping():
    parameter = {{"AAAA_pad": "p" * 3, **PLANTED}}
    assert parameter == {{}}


def test_a_token_the_test_itself_shortened():
    raise RuntimeError("shown as " + TOKEN[:14] + " only")
"""

#: The marker CHILD_AT_PARAMETER assembles. Each rendered parameter carries it
#: once, so two parameters rendered is a count of at least two.
RENDERED_ARGUMENT_MARKER = "AAAA-zz-cs820-rendered-arg-zz"

#: The unlisted variables CS-820 plants under - two, so two shapes ride in one
#: mapping and a green is not a statement about one prefix. Both sort after
#: the marker and before every real variable, for the reason stated beside
#: CHILD_AT_PARAMETER.
SORTED_FIRST_VARIABLES = ("AAAA_CS820_KEY_PROBE", "AAAA_CS820_TOKEN_PROBE")

#: Two parameters are rendered - the fixture and the parametrize argument - so
#: a report that rendered both carries the marker at least this many times.
RENDERED_PARAMETERS = 2

#: The independent oracle's prefixes: the vendor-assigned ones, typed here and
#: NOT read from `tests/conftest.py`, whose rules are what is being graded.
ORACLE_PREFIXES = ("sk-ant-", "ghp_", "gho_", "ghs_", "ghu_", "github_pat_")

#: A credential SHAPE, for counting. The run after the prefix is 8 - half the
#: shortest floor the redactor's own shapes used when this arm was built - so
#: residue a narrowed rule leaves standing beside its placeholder still counts.
CREDENTIAL_SHAPE_ORACLE = re.compile(
    "(?:" + "|".join(re.escape(prefix) for prefix in ORACLE_PREFIXES) + r")[A-Za-z0-9_\-]{8,}"
)

#: The TAIL half of a cut token carries no prefix, so no shape can see it. This
#: oracle counts any eight consecutive characters of a PLANT instead - built
#: from the plants the parent authored, never from the redactor's rules.
FRAGMENT_WIDTH = 8

#: Account-name letters on either side of pytest's ``...`` cut marker, counted
#: when at least this many letters of the name survive. It is the floor the
#: cut layer in tests/conftest.py states for itself: a shorter piece is too
#: likely to be a piece of an ordinary word too, and removing those is what the
#: second adversary refuted. Pieces below it stand, by declaration.
ACCOUNT_FRAGMENT_WIDTH = 4

#: The four children: redacted or bare, at default verbosity or at ``-vvv``.
#: The default is the one the adversary measured leaking; ``-vvv`` is the one
#: that renders the most of every argument.
VERBOSITIES: tuple[tuple[str, ...], ...] = ((), ("-vvv",))


class ParameterCounts(NamedTuple):
    """What one CS-820 child rendered - counts only, never a value."""

    shapes: int
    fragments: int
    account_fragments: int
    id_shapes: int
    markers: int


def _child_environment(plant: dict[str, str]) -> dict[str, str]:
    """This process's environment, stripped of real secrets, plus the plant.

    Two removals, for two different reasons.

    ``PYTEST_ADDOPTS`` reaches the child and can carry a ``--tb`` setting that
    suppresses the very frame an arm exists to render; ``PYTEST_CURRENT_TEST``
    travels the same way and names the parent's test in the child's output.

    Every name in :data:`_CREDENTIAL_VARIABLES` goes because a real value left
    in place would build a real literal rule in the child AND could supply the
    placeholder an arm asserts on - which is how the first build's placeholder
    arm passed under a mutant that had broken the thing it was grading.

    Args:
        plant: Variables to set in the child, after the removals.

    Returns:
        The child's environment.
    """
    listed = {name.upper() for name in _CREDENTIAL_VARIABLES}
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.upper().startswith("PYTEST_") and name.upper() not in listed
    }
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(plant)
    return environment


def _render(
    root: Path,
    source: str,
    plant: dict[str, str],
    *,
    redacted: bool = True,
    flags: tuple[str, ...] = ("--showlocals",),
    select: tuple[str, ...] | None = None,
) -> str:
    """Run a child pytest that fails, and return its combined output.

    Args:
        root: A directory of this arm's own, so two arms cannot overwrite each
            other's module.
        source: The child module's text.
        plant: Environment variables to set in the child.
        redacted: False runs the child WITHOUT `tests.conftest` as a plugin, so
            no report hook redacts anything. Only a hygiene-removed control
            asks for that - CS-820.
        flags: Rendering flags for the child. The default binds the secret to a
            FRAME LOCAL rendered by ``--showlocals``, for the reason stated
            beside CHILD_AT_RUNTIME: a long env dict repr is truncated and a
            variable added last falls outside it. The CS-820 arms pass ``-vvv``
            instead: below that verbosity pytest also cuts a rendered
            ARGUMENT's repr to a fixed length, and at it only the four-item
            limit stated beside CHILD_AT_PARAMETER remains.
        select: Node ids, relative to `root`, run IN PLACE of the module path -
            how an arm reruns ids copied from an earlier report.

    Returns:
        The child's combined output, exactly as a log or a CI artifact would
        hold it. NOTHING is scrubbed here - scrubbing on this side would grade
        this file instead of the render path.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_cs1156_child.py"
    target.write_text(source, encoding="ascii")
    plugin = ["-p", "tests.conftest"] if redacted else []
    # `select` replaces the module path with node ids relative to `root`, so a
    # run can name exactly the ids a reader copied from an earlier report.
    targets = [str(target)] if select is None else list(select)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *targets,
            *plugin,
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(root),
            # EXPLICIT, never inherited: the frame carrying the environment dict
            # is the subject, so the arm states the traceback style it grades
            # rather than taking whatever the parent run happened to set.
            "--tb=long",
            *flags,
        ],
        capture_output=True,
        check=False,
        cwd=str(root),
        env=_child_environment(plant),
        timeout=SUBPROCESS_TIMEOUT,
    )
    return (completed.stdout + completed.stderr).decode("utf-8", errors="replace")


def _tail(rendered: str) -> str:
    """The last of a child report, for a failure message a reader can act on."""
    return rendered[-1200:]


def _assert_the_frame_was_rendered(rendered: str, *, local: bool = False) -> None:
    """THE CONTROL. Without it every assertion below passes on a child that rendered nothing.

    Args:
        rendered: The child's combined output.
        local: True for the children that carry the secret in a FRAME LOCAL, so
            the arm also proves the locals section was rendered. The collection
            child and the captured-output child carry it in the exception
            message and in the printed line, and for those the body marker sits
            in the SAME STRING as the secret - so its presence already proves
            that channel reached the report.
    """
    assert RENDERED_BODY_MARKER in rendered, _tail(rendered)
    if local:
        assert RENDERED_LOCAL_MARKER in rendered, _tail(rendered)


@pytest.fixture(scope="module")
def rendered_key(tmp_path_factory: pytest.TempPathFactory) -> str:
    """One child run, shared by the arms that read it."""
    return _render(
        tmp_path_factory.mktemp("cs1156_key"),
        CHILD_AT_RUNTIME.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_KEY},
    )


def test_the_env_frame_reached_the_report(rendered_key: str) -> None:
    """THE CONTROL, as an arm of its own so it fails by name when the harness drifts."""
    _assert_the_frame_was_rendered(rendered_key, local=True)


def test_a_planted_key_does_not_survive_a_rendered_env_frame(rendered_key: str) -> None:
    """CS-1156: the exact shape that leaked on 2026-09-19, through the real render path."""
    _assert_the_frame_was_rendered(rendered_key, local=True)
    assert PLANTED_KEY not in rendered_key, _tail(rendered_key)


def test_the_placeholder_is_what_replaced_it(rendered_key: str) -> None:
    """Absence alone passes for a collapsed report. The placeholder pins the substitution.

    This arm is only worth anything because the child's environment was
    stripped: with a real key left in place it passed under a mutant that had
    narrowed the rule so far it no longer matched the planted key at all.
    """
    _assert_the_frame_was_rendered(rendered_key, local=True)
    assert REDACTED_CREDENTIAL in rendered_key, _tail(rendered_key)


def test_a_second_vendor_shape_does_not_survive_either(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """One prefix covered is a statement about one prefix."""
    rendered = _render(
        tmp_path_factory.mktemp("cs1156_gh"),
        CHILD_AT_RUNTIME.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_GH_TOKEN},
    )
    _assert_the_frame_was_rendered(rendered, local=True)
    assert PLANTED_GH_TOKEN not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_a_prefixless_secret_in_a_listed_variable_does_not_survive(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """THE LITERAL HALF, and nothing else in this file grades it.

    An adversary emptied :data:`_CREDENTIAL_VARIABLES` to ``()`` - deleting the
    entire literal rule kind - and every arm stayed green, because every arm
    planted under an UNLISTED name and every planted value carried a vendor
    prefix a shape rule could reach. The value here carries no prefix any shape
    matches, so only a literal built from the listed variable can catch it.
    """
    assert len(PLANTED_BARE_TOKEN) >= _CREDENTIAL_MIN_LITERAL, PLANTED_BARE_TOKEN
    assert LISTED_VARIABLE in _CREDENTIAL_VARIABLES, LISTED_VARIABLE

    rendered = _render(
        tmp_path_factory.mktemp("cs1156_bare"),
        CHILD_AT_RUNTIME.format(variable=LISTED_VARIABLE),
        {LISTED_VARIABLE: PLANTED_BARE_TOKEN},
    )
    _assert_the_frame_was_rendered(rendered, local=True)
    assert PLANTED_BARE_TOKEN not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_a_credential_does_not_survive_a_collection_failure(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The gap an adversary found AFTER the first build shipped.

    The same leaking frame at module level fails during collection, which pytest
    renders from a CollectReport. Measured on the first build: the planted key
    printed three times and the placeholder zero.
    """
    rendered = _render(
        tmp_path_factory.mktemp("cs1156_collect"),
        CHILD_AT_COLLECTION.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_KEY},
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_KEY not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def test_a_credential_does_not_survive_captured_output(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The ``report.sections`` render site, which no arm covered before.

    A secret printed by a failing test reaches the terminal through the captured
    stdout section rather than through a frame argument, so it exercises a
    different one of the seven sites the render path redacts at.
    """
    rendered = _render(
        tmp_path_factory.mktemp("cs1156_stdout"),
        CHILD_AT_STDOUT.format(variable=UNLISTED_VARIABLE),
        {UNLISTED_VARIABLE: PLANTED_KEY},
    )
    _assert_the_frame_was_rendered(rendered)
    assert PLANTED_KEY not in rendered, _tail(rendered)
    assert REDACTED_CREDENTIAL in rendered, _tail(rendered)


def _fragment_oracle() -> re.Pattern[str]:
    """Every run of :data:`FRAGMENT_WIDTH` consecutive characters of the LISTED plant.

    Only the listed plant: a cut piece is removed only when it is a piece of a
    KNOWN value, and the unlisted plants' prefix-less tails are declared
    uncovered in ``UNCOVERED_SECRETS`` and probed there rather than counted here.
    """
    windows = {
        PLANTED_BARE_TOKEN[start : start + FRAGMENT_WIDTH]
        for start in range(len(PLANTED_BARE_TOKEN) - FRAGMENT_WIDTH + 1)
    }
    return re.compile("|".join(re.escape(window) for window in sorted(windows)))


def _account_fragments(rendered: str) -> int:
    """Account-name letters standing against a ``...`` cut, on either side.

    The name is read here, at run time, and never written down: a count of
    runs that touch the cut marker and are a piece of it.
    """
    try:
        account = getpass.getuser().lower()
    except (KeyError, OSError):
        return 0
    width = min(ACCOUNT_FRAGMENT_WIDTH, len(account))
    return sum(
        1
        for run in re.findall(r"([A-Za-z0-9_\-]+)\.\.\.|\.\.\.([A-Za-z0-9_\-]+)", rendered)
        for piece in run
        if len(piece) >= width and piece.lower() in account
    )


def _parameter_counts(rendered: str) -> ParameterCounts:
    """Every CS-820 count in one child's output.

    COUNTS, NEVER VALUES, and the output is held only by this frame's
    argument: the item's own finding is that this class of output leaks, so
    the check for it must not leak in turn. ``id_shapes`` counts shapes on the
    two lines a node id is printed on - a section header and a FAILED line - so
    the id door is graded apart from the argument door.
    """
    id_lines = "\n".join(
        line for line in rendered.splitlines() if line.startswith(("FAILED ", "_"))
    )
    return ParameterCounts(
        shapes=len(CREDENTIAL_SHAPE_ORACLE.findall(rendered)),
        fragments=len(_fragment_oracle().findall(rendered)),
        account_fragments=_account_fragments(rendered),
        id_shapes=len(CREDENTIAL_SHAPE_ORACLE.findall(id_lines)),
        markers=rendered.count(RENDERED_ARGUMENT_MARKER),
    )


@pytest.fixture(scope="module")
def parameter_counts(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[tuple[bool, str], ParameterCounts]:
    """CS-820: every count, for the redacted and the bare child at each verbosity.

    The bare child runs WITHOUT `tests.conftest`, so nothing redacts - the
    hygiene-removed control. Every child is forced red by the same raises and
    plants two vendor shapes under unlisted names, so only the SHAPE rules can
    reach them.

    SCALARS ONLY LEAVE THIS FIXTURE. A fixture value is a test ARGUMENT, and a
    failing arm renders its arguments - the very door CS-820 names - so a
    fixture handing back the child's output would print what it counts.

    Returns:
        Counts keyed by ``(redacted, verbosity flags joined)``.
    """
    source = CHILD_AT_PARAMETER.format(variables=SORTED_FIRST_VARIABLES, bare=LISTED_VARIABLE)
    plant = dict(zip(SORTED_FIRST_VARIABLES, (PLANTED_KEY, PLANTED_GH_TOKEN), strict=True))
    plant[LISTED_VARIABLE] = PLANTED_BARE_TOKEN
    return {
        (redacted, " ".join(flags)): _parameter_counts(
            _render(tmp_path_factory.mktemp("cs820"), source, plant, redacted=redacted, flags=flags)
        )
        for redacted in (True, False)
        for flags in VERBOSITIES
    }


@pytest.mark.parametrize("verbosity", [" ".join(flags) for flags in VERBOSITIES])
def test_both_parameter_kinds_reached_the_report(
    parameter_counts: dict[tuple[bool, str], ParameterCounts], verbosity: str
) -> None:
    """CS-820's RENDERED-FRAME CONTROL: the fixture and the parametrize argument both rendered.

    Without it a zero below passes on a child whose arguments never reached
    the report - the same vacuity this file's CS-1156 controls exist to stop.
    """
    markers = parameter_counts[True, verbosity].markers
    bare_markers = parameter_counts[False, verbosity].markers
    assert markers >= RENDERED_PARAMETERS, "rendered parameters, redacted child: %d" % markers
    assert bare_markers >= RENDERED_PARAMETERS, "rendered parameters, bare child: %d" % bare_markers


@pytest.mark.parametrize("verbosity", [" ".join(flags) for flags in VERBOSITIES])
def test_a_credential_in_a_test_parameter_renders_no_credential_shape(
    parameter_counts: dict[tuple[bool, str], ParameterCounts], verbosity: str
) -> None:
    """CS-820: a forced failure of a test holding such a mapping, counted by shape.

    The acceptance asks for COUNTS rather than values, and the counts are taken
    by oracles typed in this file and not read from the rules they grade: a
    vendor shape, a run of a plant's characters that survives a cut, and an
    account-name fragment beside a cut. Each is bound to a scalar before the
    assertion, so a failure renders a number and nothing else.
    """
    counts = parameter_counts[True, verbosity]
    markers = counts.markers
    shapes = counts.shapes
    fragments = counts.fragments
    account = counts.account_fragments
    assert markers >= RENDERED_PARAMETERS, "rendered parameters: %d" % markers
    assert shapes == 0, "credential shapes rendered: %d" % shapes
    assert fragments == 0, "plant fragments rendered: %d" % fragments
    assert account == 0, "account-name fragments beside a cut: %d" % account


@pytest.mark.parametrize("verbosity", [" ".join(flags) for flags in VERBOSITIES])
def test_the_counts_see_every_door_when_redaction_is_removed(
    parameter_counts: dict[tuple[bool, str], ParameterCounts], verbosity: str
) -> None:
    """CS-820's HYGIENE-REMOVED CONTROL: the same child, no redaction, counts on every oracle.

    A zero from an oracle that cannot see the plant is a zero about nothing,
    so each oracle - and the node-id door on its own - must count at least one
    here. The account-fragment oracle is graded at default verbosity only,
    because ``-vvv`` renders an argument uncut and no cut is made there.
    """
    counts = parameter_counts[False, verbosity]
    shapes = counts.shapes
    fragments = counts.fragments
    id_shapes = counts.id_shapes
    account = counts.account_fragments
    assert shapes >= 1, "shapes the oracle saw with redaction removed: %d" % shapes
    assert fragments >= 1, "plant fragments seen with redaction removed: %d" % fragments
    assert id_shapes >= 1, "shapes in node ids with redaction removed: %d" % id_shapes
    if not verbosity:
        assert account >= 1, "account fragments seen with redaction removed: %d" % account


#: CS-820, the second adversary's refutation of the first repair. That repair
#: REWROTE node ids to redact them, and selection by the original id broke:
#: ``-k`` matched nothing, ``--deselect`` removed nothing, and an id copied from
#: the output reran nothing. Its cut rule also ate a message pytest never cut.
#: The ids here are the adversary's: a shape-like one, one carrying ``...``, and
#: a plain one; the message is the one that lost both its words.
CHILD_SELECTION = """
import pytest


@pytest.mark.parametrize("value", ["ghp_note", "wait...then", "plain"])
def test_sel(value):
    raise RuntimeError("retrying connection...giving_up")
"""

#: How many tests the selection child holds - one per parametrize id.
SELECTION_TESTS = 3

#: The message the child raises, which must render exactly as written.
UNCUT_MESSAGE = "retrying connection...giving_up"

#: Ids that carry no shape and must render, and rerun, exactly as pytest built them.
ORDINARY_IDS = ("test_sel[wait...then]", "test_sel[plain]")

#: A prefix followed by ANY run, the widest shape, for the selection child.
ANY_SHAPE = re.compile(
    "(?:" + "|".join(re.escape(prefix) for prefix in ORACLE_PREFIXES) + r")[A-Za-z0-9_\-]"
)


class SelectionCounts(NamedTuple):
    """What the selection child showed - counts only."""

    failed: int
    shapes: int
    uncut_messages: int
    ordinary_ids: int
    keyword_failed: int
    keyword_deselected: int
    shape_deselect_failed: int
    cut_deselect_failed: int
    copied: int
    reran: int


def _summary(rendered: str, word: str) -> int:
    """The count pytest's final summary line gives for `word`, or 0."""
    found = re.search(r"(\d+) " + word, rendered)
    return int(found.group(1)) if found else 0


def _copied_ids(rendered: str) -> list[str]:
    """Every id on a FAILED line that carries no placeholder - what a reader would copy."""
    return [
        found.group(1)
        for found in re.finditer(r"^FAILED (\S+::\S+)", rendered, re.MULTILINE)
        if "<redacted" not in found.group(1)
    ]


@pytest.fixture(scope="module")
def selection_counts(tmp_path_factory: pytest.TempPathFactory) -> SelectionCounts:
    """Run the selection child every way the adversary did; scalars only leave."""
    root = tmp_path_factory.mktemp("cs820_selection")
    child = "test_cs1156_child.py"

    def run(*flags: str) -> str:
        return _render(root, CHILD_SELECTION, {}, flags=flags)

    full = run("-v")
    copied = _copied_ids(full)
    reran = sum(
        1
        for nodeid in copied
        if _summary(_render(root, CHILD_SELECTION, {}, flags=(), select=(nodeid,)), "failed") == 1
    )
    keyword = run("-k", "ghp_note")
    return SelectionCounts(
        failed=_summary(full, "failed"),
        shapes=len(ANY_SHAPE.findall(full)),
        uncut_messages=full.count(UNCUT_MESSAGE),
        ordinary_ids=sum(1 for nodeid in ORDINARY_IDS if nodeid in full),
        keyword_failed=_summary(keyword, "failed"),
        keyword_deselected=_summary(keyword, "deselected"),
        shape_deselect_failed=_summary(run("--deselect", child + "::test_sel[ghp_note]"), "failed"),
        cut_deselect_failed=_summary(
            run("--deselect", child + "::test_sel[wait...then]"), "failed"
        ),
        copied=len(copied),
        reran=reran,
    )


def test_selection_by_the_original_id_still_works(selection_counts: SelectionCounts) -> None:
    """``-k`` and ``--deselect`` by the id pytest built select and deselect exactly one.

    The first repair rewrote ids and both matched nothing. Ids are now redacted
    only where they are RENDERED, so the id a user types is the id pytest holds.
    """
    counts = selection_counts
    failed = counts.failed
    keyword_failed = counts.keyword_failed
    keyword_deselected = counts.keyword_deselected
    shape_deselect = counts.shape_deselect_failed
    cut_deselect = counts.cut_deselect_failed
    assert failed == SELECTION_TESTS, "the child's failures: %d" % failed
    assert keyword_failed == 1, "-k by the original id ran %d" % keyword_failed
    assert keyword_deselected == SELECTION_TESTS - 1, (
        "-k by the original id deselected %d" % keyword_deselected
    )
    assert shape_deselect == SELECTION_TESTS - 1, (
        "--deselect of the shape-like id left %d" % shape_deselect
    )
    assert cut_deselect == SELECTION_TESTS - 1, (
        "--deselect of the id carrying ... left %d" % cut_deselect
    )


def test_an_id_copied_from_the_output_reruns(selection_counts: SelectionCounts) -> None:
    """Every id on a FAILED line that carries no placeholder reruns exactly one test."""
    copied = selection_counts.copied
    reran = selection_counts.reran
    assert copied == len(ORDINARY_IDS), "ids a reader could copy: %d" % copied
    assert reran == copied, "copied ids that reran: %d of %d" % (reran, copied)


def test_ordinary_text_renders_exactly_as_written(selection_counts: SelectionCounts) -> None:
    """No shape renders, and an id or a message carrying no known value is untouched.

    The first repair's cut rule ate a message pytest never cut; the rule now
    removes only a piece of a KNOWN value beside a ``...``. The message renders
    on its error line and on its summary line for each of three failures.
    """
    shapes = selection_counts.shapes
    uncut = selection_counts.uncut_messages
    ordinary = selection_counts.ordinary_ids
    assert shapes == 0, "shapes rendered: %d" % shapes
    assert uncut >= SELECTION_TESTS, "the uncut message rendered as written %d times" % uncut
    assert ordinary == len(ORDINARY_IDS), "ordinary ids rendered as built: %d" % ordinary


def test_a_message_touching_no_known_value_passes_the_render_path_unchanged() -> None:
    """The cut layer's claim, pinned as a unit: text with ``...`` and no known piece is kept."""
    for text in (UNCUT_MESSAGE, "wait...then", "...Full output truncated"):
        kept = redact_report(text) == text
        assert kept, "the render path rewrote an ordinary text"


def test_the_live_environment_holds_no_credential_the_redactor_leaves_standing() -> None:
    """The LIVE arm. The other arms plant; this one reads what this machine carries.

    A fixture that is correct does not make a live arm - the value that leaked
    was a real one, so the measurement has to be taken against real ones.

    IT ASSERTS WHOLE-VALUE REPLACEMENT, NOT MERELY THAT SOMETHING CHANGED. The
    first build asked only whether redaction moved the string, and an adversary
    measured that passing on a PARTIAL redaction: a key whose prefix matched and
    whose tail did not came back as the placeholder followed by real bytes, and
    the arm scored it clean. Residue beside a placeholder is worse than no
    redaction, because it reads as handled.
    """
    standing = sorted(
        name
        for name, value in os.environ.items()
        if _looks_like_a_credential(value)
        and redact_credentials(value.strip()) != REDACTED_CREDENTIAL
    )
    assert standing == [], standing


def test_every_uncovered_secret_is_declared_and_still_uncovered() -> None:
    """A stated exemption that quietly starts working is drift too.

    The mirror of ``tests/test_report_redaction_classes.py``'s arm over
    ``UNCOVERED_CLASSES``: each declaration carries a reason, and the one that
    can be probed is probed rather than believed.
    """
    assert set(UNCOVERED_SECRETS) == {
        "unlisted-and-unprefixed",
        "not-in-the-environment",
        "cut-tail-of-an-unlisted-key",
        "node-ids-outside-the-reporter",
        "internal-errors",
    }, sorted(UNCOVERED_SECRETS)
    assert all(reason.strip() for reason in UNCOVERED_SECRETS.values()), sorted(UNCOVERED_SECRETS)

    # The probe for "unlisted-and-unprefixed": a secret-shaped value carrying no
    # vendor prefix, held in no listed variable, passes through UNCHANGED. If
    # this ever starts being redacted, the declaration is stale and must move.
    unreachable = "9c2e" * 12
    assert redact_credentials(unreachable) == unreachable, unreachable

    # The probe for "cut-tail-of-an-unlisted-key": a prefix-less tail beside a
    # cut marker, of no known value, survives the whole render path.
    tail = "x..." + "Q" * 12
    assert redact_report(tail) == tail, tail


def _looks_like_a_credential(value: str) -> bool:
    """An INDEPENDENT oracle, derived from the vendor prefixes and not from the rules.

    Deliberately NOT ``tests/conftest.py``'s own patterns: an oracle built from
    the thing it grades agrees with it by construction and can observe nothing.
    """
    lowered = value.strip().lower()
    return any(lowered.startswith(prefix) for prefix in ORACLE_PREFIXES)
