"""CS-1191 - the account name must not survive a coloured or an xdist-verbose report.

THE DEFECT, MEASURED BY THE CS-820 CLOSING ADJUDICATOR. Under ``--color=yes -vv``,
and under ``-n 2`` with ``-vv`` or ``-vvv``, pytest renders an assertion diff
through its syntax highlighter, which wraps every token of a string repr in a
terminal escape code. A repr's escape sequences are tokens of their own, so a
doubled home path renders as its separate components, and the account name is
left standing between an escape code that ENDS in a letter and one that begins
with ESC. The account-name rule in `tests/conftest.py::redact_personal_data`
needs a non-word character on its left and the letter the escape code ends in
is a word character, so the name printed whole, once per token, with the
redaction loaded.

WHY -n 2 COLOURS WITHOUT --color=yes. A worker renders the highlighted diff
when the controller was told nothing about colour and its output is a pipe, so
the xdist report path is a coloured path. The ``-n 2 -vvv`` child passes no
colour flag and is graded as coloured below.

EVERY ARM RUNS A REAL CHILD PYTEST, for the reason
tests/test_credential_redaction.py gives: the render path is the subject, and
only a child that loads `tests.conftest` as a plugin reaches it. Nothing the
child prints is returned from the helpers - they reduce it to COUNTS, because
on the unrepaired tree the output carries the very name being counted.

THE SESSION HEADER IS EXCLUDED, AND ONLY IT. CS-447 owns the header: pytest's
platform and rootdir lines print the interpreter and the checkout paths on every
run, and no report hook can reach them. The header ends at the first blank line
of the output, and every line after it is counted.

THE CONTROLS, each of which turns a zero into a statement about something:

- the diff was RENDERED - a marker the child assembles at run time is counted
  in the output;
- the coloured children were COLOURED - escape codes are counted in them, and
  the plain control carries none;
- the oracle SEES the name - the same child with the redaction removed renders
  it at least once;
- the repair is EQUIVALENT on plain text - the same child under ``--color=no``
  renders the name nowhere beyond the header either.
"""

from __future__ import annotations

import contextlib
import getpass
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

from tests.conftest import REDACTED_HOME, REDACTED_USER, redact_personal_data

REPO_ROOT = Path(__file__).resolve().parent.parent

SUBPROCESS_TIMEOUT = 180

#: One Select Graphic Rendition escape, the only kind pytest's highlighter
#: emits. TYPED HERE, never read from `tests/conftest.py`, whose rules are what
#: is being graded.
SGR_ORACLE = re.compile("\x1b\\[[0-9;]*m")

#: The marker the child assembles. Its presence proves the diff was rendered.
RENDERED_DIFF_MARKER = "AAAA-zz-cs1191-rendered-diff-zz"

#: The child. The name and the home are read AT RUN TIME in the child, never
#: written down, and the marker is assembled from two fragments so the failing
#: function's own source, which pytest prints, cannot supply it.
#:
#: THREE VALUES, THREE TOKEN SHAPES. The name alone is a string token of its
#: own; a name behind an escaped backslash follows the escape's own token; and a
#: home path with a doubled separator is the shape the adjudicator measured,
#: split into its components on Windows.
CHILD = """
import getpass
from pathlib import Path

MARKER = "AAAA-zz-cs1191-" + "rendered-diff-zz"
NAME = getpass.getuser()
HOME = str(Path.home())


def test_a_highlighted_diff_renders_the_mapping():
    mapping = {
        MARKER: "1",
        "AAAB_name": NAME,
        "AAAC_escaped": "\\\\" + NAME,
        "AAAD_home": HOME + "\\\\" + "sub",
    }
    assert mapping == {}
"""

#: Variables that steer the child's colour. Every ``PYTEST_`` variable goes as
#: well: a parent under xdist exports ``PYTEST_XDIST_WORKER``, and a child that
#: inherited it would believe itself a worker.
_STEERING = ("NO_COLOR", "PY_COLORS", "FORCE_COLOR", "PYTEST_THEME", "PYTEST_THEME_MODE")

#: The children: whether the redaction is loaded, and the flags.
ACCEPTANCE = (True, ("--color=yes", "-n", "2", "-vv"))
COLOURED = (True, ("--color=yes", "-vv"))
XDIST_VVV = (True, ("-n", "2", "-vvv"))
PLAIN = (True, ("--color=no", "-vv"))
BARE = (False, ("--color=yes", "-n", "2", "-vv"))
CHILDREN = (ACCEPTANCE, COLOURED, XDIST_VVV, PLAIN, BARE)

#: The redacted children the zero is asserted over, the acceptance one first.
REDACTED_CHILDREN = (ACCEPTANCE, COLOURED, XDIST_VVV, PLAIN)


class Counts(NamedTuple):
    """What one child rendered - counts only, never a value."""

    renderings: int
    markers: int
    escapes: int
    header_found: bool


def _names() -> tuple[str, ...]:
    """Every account-name spelling the oracle counts, read at run time.

    The login name and the profile directory's own name, which can differ on a
    renamed account. Built here and not from `tests/conftest.py`.
    """
    names = {Path.home().name}
    with contextlib.suppress(KeyError, OSError):
        names.add(getpass.getuser())
    return tuple(sorted(name for name in names if name.strip()))


def _renderings(text: str) -> int:
    """How many times an account-name spelling stands as a word in ``text``."""
    return sum(
        len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", text, re.IGNORECASE))
        for name in _names()
    )


def _count(output: str) -> Counts:
    """Reduce one child's output to counts. The output never leaves this frame."""
    visible = SGR_ORACLE.sub("", output).replace("\r", "")
    lines = visible.split("\n")
    end = lines.index("") if "" in lines else len(lines)
    body = "\n".join(lines[end:])
    return Counts(
        renderings=_renderings(body),
        markers=body.count(RENDERED_DIFF_MARKER),
        escapes=len(SGR_ORACLE.findall(output)),
        header_found="test session starts" in lines[0] if lines else False,
    )


def _child_environment() -> dict[str, str]:
    """This process's environment, minus pytest's and the colour-steering variables."""
    steering = {name.upper() for name in _STEERING}
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.upper().startswith("PYTEST_") and name.upper() not in steering
    }
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(root: Path, *, redacted: bool, flags: tuple[str, ...]) -> Counts:
    """Run the failing child once and return its counts."""
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_cs1191_child.py"
    target.write_text(CHILD, encoding="ascii")
    plugin = ["-p", "tests.conftest"] if redacted else []
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(target),
            *plugin,
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(root),
            "--tb=long",
            *flags,
        ],
        capture_output=True,
        check=False,
        cwd=str(root),
        env=_child_environment(),
        timeout=SUBPROCESS_TIMEOUT,
    )
    return _count((completed.stdout + completed.stderr).decode("utf-8", errors="replace"))


def _label(child: tuple[bool, tuple[str, ...]]) -> str:
    """A readable id for one child."""
    redacted, flags = child
    return ("redacted " if redacted else "bare ") + " ".join(flags)


@pytest.fixture(scope="module")
def counts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Counts]:
    """Every child once, reduced to counts. SCALARS ONLY LEAVE THIS FIXTURE."""
    return {
        _label(child): _run(tmp_path_factory.mktemp("cs1191"), redacted=child[0], flags=child[1])
        for child in CHILDREN
    }


@pytest.mark.parametrize("child", [_label(child) for child in CHILDREN])
def test_the_diff_reached_the_report(counts: dict[str, Counts], child: str) -> None:
    """THE RENDERED-DIFF CONTROL, and the header the exclusion depends on."""
    markers = counts[child].markers
    header = counts[child].header_found
    assert markers >= 1, "rendered diff markers: %d" % markers
    assert header, "the output did not open with the session header"


@pytest.mark.parametrize(
    "child", [_label(child) for child in (ACCEPTANCE, COLOURED, XDIST_VVV, BARE)]
)
def test_the_coloured_children_were_coloured(counts: dict[str, Counts], child: str) -> None:
    """A zero from a child that emitted no colour says nothing about the coloured path."""
    escapes = counts[child].escapes
    assert escapes >= 1, "escape codes in a coloured child: %d" % escapes


def test_the_plain_control_carries_no_escape_code(counts: dict[str, Counts]) -> None:
    """The equivalence control is a plain run, or it controls nothing."""
    escapes = counts[_label(PLAIN)].escapes
    assert escapes == 0, "escape codes in the plain control: %d" % escapes


def test_the_oracle_sees_the_name_when_redaction_is_removed(counts: dict[str, Counts]) -> None:
    """THE HYGIENE-REMOVED CONTROL: without it every zero below is a zero about nothing."""
    renderings = counts[_label(BARE)].renderings
    assert renderings >= 1, "account-name renderings with redaction removed: %d" % renderings


@pytest.mark.parametrize("child", [_label(child) for child in REDACTED_CHILDREN])
def test_no_account_name_renders_beyond_the_session_header(
    counts: dict[str, Counts], child: str
) -> None:
    """CS-1191's acceptance: zero account-name renderings beyond the CS-447 header.

    The first id is the acceptance's own child, ``--color=yes -n 2 -vv``; the
    others are the single-process coloured path, the xdist ``-vvv`` path the
    adjudicator also measured, and the plain control.
    """
    renderings = counts[child].renderings
    assert renderings == 0, "account-name renderings beyond the header: %d" % renderings


#: One escape code as the highlighter emits it around a string token, and the
#: reset it closes the token with.
_OPEN = "\x1b[33m"
_CLOSE = "\x1b[39;49;00m"


def _highlighted(value: str) -> str:
    """``value`` as a string token between highlighter escape codes."""
    return _OPEN + "'" + _CLOSE + _OPEN + value + _CLOSE + _OPEN + "'" + _CLOSE


def test_a_highlighted_name_is_replaced_and_the_colour_kept() -> None:
    """The unit shape of the leak, graded without a child.

    The placeholder must appear, the name must not, and the escape codes that do
    not sit between the name and its visible neighbours must survive - the
    repair tolerates colour rather than stripping it.
    """
    for name in _names():
        rendered = redact_personal_data(_highlighted(name))
        left = _renderings(SGR_ORACLE.sub("", rendered))
        placed = REDACTED_USER in rendered
        coloured = rendered.startswith(_OPEN + "'")
        assert left == 0, "account-name renderings left: %d" % left
        assert placed, "no account-name placeholder was rendered"
        assert coloured, "the colour of the token before the name was lost"


def test_a_home_path_split_by_escape_codes_is_replaced_whole() -> None:
    """The sibling: the doubled home spelling, each component its own token."""
    doubled = str(Path.home()).replace("\\", "\\\\")
    pieces = re.split(r"(\\\\|/)", doubled)
    rendered = redact_personal_data(
        "".join(_OPEN + piece + _CLOSE for piece in pieces if piece) + _OPEN + "sub" + _CLOSE
    )
    placed = REDACTED_HOME in rendered
    left = _renderings(SGR_ORACLE.sub("", rendered))
    assert placed, "no home placeholder was rendered for a split home path"
    assert left == 0, "account-name renderings left: %d" % left


@pytest.mark.parametrize(
    "shape",
    ["x{name}", "{name}x", "9{name}", "{name}_", "_{name}"],
)
def test_a_name_inside_a_word_is_left_alone_with_or_without_colour(shape: str) -> None:
    """The boundary is judged on VISIBLE text, so colour moves nothing a plain run keeps.

    A name glued to a word character is not replaced in plain text - the
    blast-radius limit `tests/conftest.py` states - and an escape code between
    the two must not change that verdict in either direction.
    """
    for name in _names():
        plain = shape.format(name=name)
        head, _, tail = shape.partition("{name}")
        coloured = _OPEN + head + _CLOSE + _OPEN + name + _CLOSE + _OPEN + tail + _CLOSE
        plain_moved = redact_personal_data(plain) != plain
        coloured_moved = redact_personal_data(coloured) != coloured
        assert plain_moved == coloured_moved, (
            "colour changed the verdict: plain moved %s, coloured moved %s"
            % (plain_moved, coloured_moved)
        )
