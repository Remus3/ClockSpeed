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

THE -n 2 -vvv CHILD IS COLOURED BY THE ENVIRONMENT, NOT BY A FLAG. Left to
detect colour for itself, pytest colours only when the terminal it runs in
allows it. The adjudicator's ``-n 2 -vvv`` run was coloured with no flag
because the terminal it ran in allowed it. The ubuntu CI runner's did not, and
there the child printed 0 escape codes (CI run 36130961603). A ``TERM=dumb``
parent reproduces that zero on Windows too. So every child runs under
``TERM=dumb``, which means no child can be coloured just because of where the
suite happens to run. The ``-n 2 -vvv`` child is told to colour through
``PY_COLORS`` and ``FORCE_COLOR``, which xdist workers inherit. The
colour-steering route this suite covers is then the environment, not the flag,
and that child is graded as coloured below on every platform.

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

#: One terminal escape sequence of any kind: a control sequence with any final
#: byte, an operating-system command ended by BEL or by the string terminator,
#: and a lone ESC. TYPED HERE, never read from `tests/conftest.py`, whose rules
#: are what is being graded. Removing every match leaves the VISIBLE text.
ESCAPE_ORACLE = re.compile(
    "\x1b\\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]|\x1b\\][^\x07\x1b]*(?:\x07|\x1b\\\\)|\x1b"
)

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

#: Colour asked for through the environment, per child. ``PY_COLORS`` is the
#: variable pytest consults first; ``FORCE_COLOR`` is the fallback it also
#: honours. Neither is inherited from this process - `_STEERING` strips both.
COLOUR_BY_ENVIRONMENT: dict[tuple[bool, tuple[str, ...]], dict[str, str]] = {
    XDIST_VVV: {"PY_COLORS": "1", "FORCE_COLOR": "1"},
}


class Counts(NamedTuple):
    """What one child rendered - counts only, never a value."""

    renderings: int
    raw: int
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
    raw_lines = output.replace("\r", "").split("\n")
    lines = [ESCAPE_ORACLE.sub("", line) for line in raw_lines]
    end = lines.index("") if "" in lines else len(lines)
    body = "\n".join(lines[end:])
    return Counts(
        renderings=_renderings(body),
        raw=_renderings("\n".join(raw_lines[end:])),
        markers=body.count(RENDERED_DIFF_MARKER),
        escapes=len(ESCAPE_ORACLE.findall(output)),
        header_found="test session starts" in lines[0] if lines else False,
    )


def _child_environment(colour: dict[str, str] | None = None) -> dict[str, str]:
    """This process's environment, minus pytest's and the colour-steering variables.

    ``TERM`` is pinned to ``dumb``, so the parent's terminal can colour no
    child, and ``colour`` then adds back only the steering asked for.
    """
    steering = {name.upper() for name in _STEERING}
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.upper().startswith("PYTEST_") and name.upper() not in steering
    }
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["TERM"] = "dumb"
    environment.update(colour or {})
    return environment


def _run(
    root: Path,
    *,
    redacted: bool,
    flags: tuple[str, ...],
    colour: dict[str, str] | None = None,
) -> Counts:
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
        env=_child_environment(colour),
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
        _label(child): _run(
            tmp_path_factory.mktemp("cs1191"),
            redacted=child[0],
            flags=child[1],
            colour=COLOUR_BY_ENVIRONMENT.get(child),
        )
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
    raw = counts[child].raw
    assert renderings == 0, "account-name renderings beyond the header: %d" % renderings
    assert raw == 0, "account-name renderings in the raw bytes beyond the header: %d" % raw


#: THE ADVERSARY'S REGRESSION PAIR against the first repair. A failing test
#: prints the name followed by erase-line and by a hyperlink's terminator, and
#: ``-rA`` renders the captured output. The unrepaired rules caught both, and
#: the first repair printed both whole, because it refused ESC as a boundary.
CHILD_PRINTED = """
import getpass

MARKER = "AAAA-zz-cs1191-" + "rendered-diff-zz"
NAME = getpass.getuser()


def test_a_printed_name_is_followed_by_a_non_colour_escape():
    print(MARKER)
    print("erase:", NAME + "\\x1b[K")
    print("link:", NAME + "\\x1b]8;;\\x1b\\\\")
    raise AssertionError("forced, so the captured section is rendered")
"""


@pytest.fixture(scope="module")
def printed(tmp_path_factory: pytest.TempPathFactory) -> Counts:
    """The regression-pair child under ``-rA --color=no``. Counts only."""
    root = tmp_path_factory.mktemp("cs1191_printed")
    target = root / "test_cs1191_printed.py"
    target.write_text(CHILD_PRINTED, encoding="ascii")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(target),
            "-p",
            "tests.conftest",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(root),
            "-rA",
            "--color=no",
        ],
        capture_output=True,
        check=False,
        cwd=str(root),
        env=_child_environment(),
        timeout=SUBPROCESS_TIMEOUT,
    )
    return _count((completed.stdout + completed.stderr).decode("utf-8", errors="replace"))


def test_a_name_before_a_non_colour_escape_is_redacted_as_at_base(printed: Counts) -> None:
    """No regression against the unrepaired rules: both printed names are replaced."""
    markers = printed.markers
    escapes = printed.escapes
    renderings = printed.renderings
    raw = printed.raw
    assert markers >= 1, "rendered captured-output markers: %d" % markers
    assert escapes >= BOTH_SIDES, "escape sequences the child printed: %d" % escapes
    assert renderings == 0, "account-name renderings, visible: %d" % renderings
    assert raw == 0, "account-name renderings, raw bytes: %d" % raw


#: Every escape form the redaction must see through, as a report can carry it.
ESCAPE_FORMS: dict[str, str] = {
    "sgr": "\x1b[33m",
    "colon-sgr": "\x1b[38:5:208m",
    "erase-line": "\x1b[K",
    "cursor-right": "\x1b[1C",
    "reset-then-erase": "\x1b[0m\x1b[K",
    "osc8-st": "\x1b]8;;\x1b\\",
    "osc8-bel": "\x1b]8;;http://example.invalid/\x07",
    "lone-esc": "\x1b",
}

#: Where the escape sits relative to the name.
POSITIONS = ("after", "before", "split")

#: Escapes on each side of a name in the keep arm, and the printed pair.
BOTH_SIDES = 2

#: The control-sequence forms: each ends in a word character, which is the
#: shape where judging the boundary on raw bytes and on visible text disagree.
CSI_FORMS = ("sgr", "colon-sgr", "erase-line", "cursor-right", "reset-then-erase")


def _placed(name: str, escape: str, position: str) -> str:
    """``name`` in quotes with ``escape`` after it, before it, or splitting it."""
    if position == "after":
        return "'" + name + escape + "'"
    if position == "before":
        return "'" + escape + name + "'"
    half = max(1, len(name) // 2)
    return "'" + name[:half] + escape + name[half:] + "'"


@pytest.mark.parametrize("form", sorted(ESCAPE_FORMS))
@pytest.mark.parametrize("position", POSITIONS)
def test_an_escape_beside_or_inside_the_name_does_not_let_it_through(
    form: str, position: str
) -> None:
    """Judged on the visible text; the placeholder lands in the original."""
    for name in _names():
        rendered = redact_personal_data(_placed(name, ESCAPE_FORMS[form], position))
        visible = _renderings(ESCAPE_ORACLE.sub("", rendered))
        raw = _renderings(rendered)
        placed = REDACTED_USER in rendered
        assert visible == 0, "account-name renderings, visible: %d" % visible
        assert raw == 0, "account-name renderings, raw: %d" % raw
        assert placed, "no account-name placeholder was rendered"


@pytest.mark.parametrize("form", CSI_FORMS)
def test_the_escapes_around_a_redacted_name_are_kept(form: str) -> None:
    """Only the name's characters go: an escape before it and one after it stay."""
    escape = ESCAPE_FORMS[form]
    for name in _names():
        rendered = redact_personal_data("'" + escape + name + escape + "'")
        kept = rendered.count(escape)
        assert kept == BOTH_SIDES, "escapes kept around a redacted name: %d" % kept


def test_a_name_inside_a_hyperlink_target_is_redacted_as_at_base() -> None:
    """The first pass over the text as written still runs, so an invisible name goes too."""
    for name in _names():
        link = "\x1b]8;;file:///x/" + name + "\x1b\\" + "link" + "\x1b]8;;\x1b\\"
        raw = _renderings(redact_personal_data(link))
        assert raw == 0, "account-name renderings inside a hyperlink target: %d" % raw


def test_a_home_path_split_by_escape_codes_is_replaced_whole() -> None:
    """The sibling: the doubled home spelling, each component its own token."""
    doubled = str(Path.home()).replace("\\", "\\\\")
    pieces = re.split(r"(\\\\|/)", doubled)
    rendered = redact_personal_data(
        "".join("\x1b[33m" + piece + "\x1b[39;49;00m" for piece in pieces if piece) + "sub"
    )
    placed = REDACTED_HOME in rendered
    left = _renderings(ESCAPE_ORACLE.sub("", rendered))
    assert placed, "no home placeholder was rendered for a split home path"
    assert left == 0, "account-name renderings left: %d" % left


@pytest.mark.parametrize("form", CSI_FORMS)
@pytest.mark.parametrize("shape", ["x{name}", "9{name}", "_{name}"])
def test_a_name_glued_to_a_word_is_left_alone_through_an_escape(form: str, shape: str) -> None:
    """The boundary is judged on VISIBLE text: an escape is not a separator.

    A name glued to a word character is not replaced in plain text - the
    blast-radius limit `tests/conftest.py` states - and a control sequence
    between the two must not turn it into one.
    """
    for name in _names():
        head = shape.partition("{name}")[0]
        plain = head + name
        escaped = head + ESCAPE_FORMS[form] + name
        plain_moved = redact_personal_data(plain) != plain
        escaped_moved = redact_personal_data(escaped) != escaped
        assert plain_moved == escaped_moved, (
            "an escape changed the verdict: plain moved %s, escaped moved %s"
            % (plain_moved, escaped_moved)
        )
