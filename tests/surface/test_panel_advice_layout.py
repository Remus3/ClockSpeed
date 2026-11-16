"""CS-1400 slice A - the Advice card's control row and snooze group, graded in the sheet.

THE CRITERION. ``docs/item_notes/phase5.md``, ``## CS-1400``, ``### Acceptance``: the
card's Accept, Dismiss and Pin stand apart by a non-zero gap (H1), and the snooze length
select has a bounded width and sits beside its Snooze button as one row (the stylesheet
half of S2).

HOW IT IS GRADED. No browser runs in this suite, so the layout is graded by PARSING the
served stylesheet: the shipped ``app.css`` is read as the server would send it, comments
are removed, every rule (a rule inside an at-rule included) becomes a selector list and a
declaration map, and a property's value is the last declaration any rule naming the
selector makes. A real render is the ui-auditor's, not this file's.

THE NAMES ARE THE CONTRACT WITH ``panel_advice.js``. The row carries ``advice-controls``
and the group wrapping the snooze label, select and button carries ``advice-snooze``.
The row class is asserted in the shipped script here. The group class is emitted by the
sibling slice and asserted there (``test_panel_advice_ui157.py``), so this file stays green
whichever of the two lands first.

Test-quality discipline (``CONVENTIONS.md`` section 7.2). Every negative has a control,
and the parser is run against a planted rule before an absence is believed.
"""

from __future__ import annotations

import re
from typing import Final

import pytest

from tests.surface import panel_harness

STYLESHEET: Final = "app.css"
SCRIPT: Final = "panel_advice.js"

#: A block comment in the sheet, out before a rule is looked for.
CSS_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/")

#: One CSS length: a number and its unit, or a bare zero.
LENGTH: Final = re.compile(r"^(-?\d*\.?\d+)([a-z%]*)$")

#: The units a bounded width may be written in. Relative to type, so it scales with it.
BOUNDED_UNITS: Final = ("rem", "ch", "em")


def served(name: str) -> str:
    """One shipped web asset, as ASCII text.

    Args:
        name: The asset's filename.

    Returns:
        The whole file.
    """
    return (panel_harness.WEB_DIR / name).read_bytes().decode("ascii")


def parse_rules(sheet: str) -> list[tuple[tuple[str, ...], dict[str, str]]]:
    """Every rule in a sheet, flattened out of any at-rule around it.

    Args:
        sheet: The stylesheet text.

    Returns:
        ``(selectors, declarations)`` per rule, in sheet order. A property declared twice in
        one rule keeps the later value.
    """
    text = CSS_COMMENT.sub(" ", sheet)
    rules: list[tuple[tuple[str, ...], dict[str, str]]] = []
    stack: list[str] = []
    buf = ""
    for char in text:
        if char == "{":
            stack.append(buf.strip())
            buf = ""
        elif char == "}":
            opener = stack.pop() if stack else ""
            if buf.strip() and not opener.startswith("@"):
                selectors = tuple(" ".join(part.split()) for part in opener.split(","))
                rules.append((selectors, declarations_of(buf)))
            buf = ""
        else:
            buf += char
    return rules


def declarations_of(body: str) -> dict[str, str]:
    """The ``property: value`` pairs of one rule body.

    Args:
        body: The text between a rule's braces.

    Returns:
        Property to value, whitespace folded, a later declaration replacing an earlier.
    """
    found: dict[str, str] = {}
    for declaration in body.split(";"):
        name, colon, value = declaration.partition(":")
        if colon:
            found[name.strip().lower()] = " ".join(value.split())
    return found


def value_of(sheet: str, selector: str, prop: str) -> str | None:
    """The last value any rule naming this exact selector gives a property.

    Args:
        sheet: The stylesheet text.
        selector: One selector, as the sheet spells it.
        prop: The property name.

    Returns:
        The value, or None when no rule naming the selector declares it.
    """
    value: str | None = None
    for selectors, declared in parse_rules(sheet):
        if selector in selectors and prop in declared:
            value = declared[prop]
    return value


def style(selector: str, prop: str) -> str | None:
    """The shipped sheet's value for a selector and property.

    Bound here so a failed assertion renders the two names and the value, never the sheet.

    Args:
        selector: One selector, as the sheet spells it.
        prop: The property name.

    Returns:
        The value, or None when the shipped sheet gives none.
    """
    return value_of(served(STYLESHEET), selector, prop)


def lengths(value: str) -> list[float]:
    """The numeric part of each length in a value.

    Args:
        value: A declaration value such as ``0.5rem 1rem``.

    Returns:
        One number per space-separated token.

    Raises:
        AssertionError: A token is not a length.
    """
    numbers: list[float] = []
    for token in value.split():
        match = LENGTH.match(token)
        assert match is not None, f"not a length: {token!r} in {value!r}"
        numbers.append(float(match.group(1)))
    return numbers


# ---------------------------------------------------------------------------
# The parser, before an absence is believed
# ---------------------------------------------------------------------------

PLANTED: Final = """
/* .advice-controls { gap: 9rem; } */
.a, .b { gap: 0.5rem; display: flex }
@media (max-width: 40rem) {
  .a { gap: 1rem 2rem; }
}
.c { gap: 0; gap: 3rem; }
"""


def test_the_parser_reads_a_selector_list_an_at_rule_and_a_comment() -> None:
    assert value_of(PLANTED, ".b", "gap") == "0.5rem"
    assert value_of(PLANTED, ".b", "display") == "flex"
    # The later rule, inside the at-rule, wins for .a.
    assert value_of(PLANTED, ".a", "gap") == "1rem 2rem"
    # A commented-out rule is no rule, and a repeat in one rule keeps the later.
    assert value_of(PLANTED, ".advice-controls", "gap") is None
    assert value_of(PLANTED, ".c", "gap") == "3rem"
    # Absence is real: a name the sheet never states answers None.
    assert value_of(PLANTED, ".never", "gap") is None


# ---------------------------------------------------------------------------
# The contract with the script
# ---------------------------------------------------------------------------


def test_the_script_emits_the_control_row_class_the_sheet_styles() -> None:
    script = served(SCRIPT)
    assert 'row.className = "advice-read advice-controls"' in script


def test_the_sheet_names_the_two_classes_it_styles() -> None:
    assert style(".advice-controls", "display") is not None
    assert style(".advice-snooze", "display") is not None


# ---------------------------------------------------------------------------
# H1 - Accept, Dismiss and Pin stand apart
# ---------------------------------------------------------------------------


def test_h1_the_card_controls_stand_apart_by_a_non_zero_gap() -> None:
    assert style(".advice-controls", "display") == "flex"
    assert style(".advice-controls", "flex-wrap") == "wrap"
    gap = style(".advice-controls", "gap")
    assert gap is not None, "no gap on .advice-controls"
    # Both axes: the row gap when it wraps and the column gap between buttons.
    assert all(number > 0 for number in lengths(gap)), gap


# ---------------------------------------------------------------------------
# S2 (stylesheet half) - the snooze select is bounded and one row with its button
# ---------------------------------------------------------------------------


def test_s2_the_snooze_select_width_is_bounded_and_its_group_is_one_row() -> None:
    group = ".advice-snooze"
    assert style(group, "display") == "flex"
    assert style(group, "flex-wrap") == "nowrap"
    assert style(group, "align-items") == "center"
    gap = style(group, "gap")
    assert gap is not None, "no gap on .advice-snooze"
    assert all(number > 0 for number in lengths(gap)), gap

    # The select no longer takes the bench's full width, and may shrink to fit a narrow card.
    select = ".advice-snooze .bench-input"
    assert style(select, "width") == "auto"
    ceiling = style(select, "max-width")
    assert ceiling is not None, "no max-width on the snooze select"
    match = LENGTH.match(ceiling)
    assert match is not None, ceiling
    assert match.group(2) in BOUNDED_UNITS, ceiling
    assert float(match.group(1)) > 0, ceiling


def test_s2_the_bench_input_the_group_overrides_is_the_full_width_one() -> None:
    # Control: the rule the group has to beat really is full width, so the override above
    # is a change and not a restatement.
    assert style(".bench-input", "width") == "100%"


@pytest.mark.parametrize("selector", [".advice-controls", ".advice-snooze"])
def test_the_new_rules_carry_no_float_or_fixed_height_that_would_reflow(selector: str) -> None:
    # hud_doctrine section 2: no reflow. A float or a pinned height is how a row jumps.
    assert style(selector, "float") is None
    assert style(selector, "height") is None
    # Control: the selector is really declared, so the two Nones above are about the rule.
    assert style(selector, "display") is not None
