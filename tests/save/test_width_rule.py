"""CS-422 - the width shipping rule, graded where there is no game and no save.

WHAT THIS MODULE GRADES
-------------------------
``clockspeed/save/objects.py`` states one rule for when a width may ship, names
the criteria that rule admits, names the reasons it does NOT admit, records the
value readings it declines against one of those reasons, and derives its
exception set from those declines. This module asserts that those structures
agree with one another and with the rule's own text.

WHY IT READS SHIPPED DATA AND ITS OWN SOURCE, AND NOTHING ELSE
----------------------------------------------------------------
CS-422's earlier grading rested on sweeps of the operator's save library. The
tier-1 lane runs with no game installed and no saves present, so on that lane
the rule was graded by nothing at all. This module imports the standard
library, pytest, and ``clockspeed.save.objects`` - an import chain that opens
no file and locates no install - so it runs on a clone.

WHAT IS DERIVED RATHER THAN LISTED
------------------------------------
The population of type words that ship a tag-extra width while their value
reading is unmeasured is COMPUTED from the shipped tables here, never written
down. A list of those words in this file would be a second hand-authored scope
free to disagree with the first, and a scope that was hand-authored and
incomplete is what got the item refuted.

THE SEAM SYMBOLS ARE READ INSIDE THE TEST BODIES, DELIBERATELY
----------------------------------------------------------------
Not bound at module scope. ADR 0008's REVISIT clause turns on a shipped
constant staying monkeypatchable in process: a name read into a module-level
local at import time freezes the value a mutation sweep needs to move. Reading
``objects.<NAME>`` inside the body keeps every constant below mutable by
``monkeypatch.setattr(objects, ...)``.

WHAT IS NOT GRADED HERE
-------------------------
Whether a declined reading is declined CORRECTLY, and whether a shipped width
is the right number. Both are measurements against real payloads and live with
the oracles rather than here. What is graded here is that the rule has one
stated form, that the bookkeeping around it is complete against the shipped
tables, and that neither can be edited into agreement by hand.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

from clockspeed.save import objects

# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------

#: A decline is a reason code beside its prose.
_DECLINE_FIELDS: Final = 2

#: Statements that end a function's straight-line body.
_TERMINATORS: Final = (ast.Return, ast.Raise, ast.Continue, ast.Break)

#: The function node kinds a module can define.
_ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)


def _module_tests(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Collect the test functions a module defines at module or class scope.

    Args:
        tree: The parsed module.

    Returns:
        The test functions, keyed by name - a method as ``Class.method``, so it
        cannot collide with a module-scope function of the same bare name.
    """
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, _ANY_FUNCTION) and node.name.startswith("test_"):
            found[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, _ANY_FUNCTION) and member.name.startswith("test_"):
                    found[f"{node.name}.{member.name}"] = member
    return found


def _is_inert(statement: ast.stmt) -> bool:
    """Report whether a statement neither asserts nor computes anything.

    ``pass`` is one shape. A bare constant expression is the other, and it is
    the shape that matters: a docstring IS a bare string constant, so a test
    body cut down to its docstring is a body of inert statements, and so is one
    cut down to ``...``.

    Args:
        statement: One statement from a function body.

    Returns:
        True if the statement does nothing at runtime.
    """
    if isinstance(statement, ast.Pass):
        return True
    return isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)


def _hollow_tests(tree: ast.Module) -> list[str]:
    """Find the tests in a module whose body cannot assert anything.

    TWO SHAPES, and the first is the one this guard exists for.

    1. AN INERT BODY - every statement is ``pass``, ``...``, or a bare string.
       That covers a test emptied to its docstring, which leaves no unreachable
       statement behind and therefore no signal for a type checker to raise.
    2. AN EARLY TERMINATOR - a ``return``, ``raise``, ``continue`` or ``break``
       with statements after it, so the assertions are in the file and dead.

    THE SHAPE IT DOES NOT COVER is a body whose assertions are rewritten to
    something trivially true, such as ``assert True`` or a comparison of a
    literal with itself. Those execute, so nothing structural separates them
    from a real assertion, and a guard read as covering them would be a
    false guarantee.

    Args:
        tree: The parsed module.

    Returns:
        ``name at line N: reason`` for each hollow test, empty if none.
    """
    found: list[str] = []
    for name, node in _module_tests(tree).items():
        if all(_is_inert(statement) for statement in node.body):
            found.append(f"{name} at line {node.lineno}: the body does nothing")
            continue
        for index, statement in enumerate(node.body[:-1]):
            if isinstance(statement, _TERMINATORS):
                found.append(
                    f"{name} at line {node.body[index + 1].lineno}: "
                    f"dead statements after a terminator"
                )
                break
    return found


def _assert_no_test_is_hollow(module_path: Path) -> None:
    """Assert that no test in a module has a body that cannot assert anything.

    Args:
        module_path: The module to read. Its own source, or a spliced copy.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    named = sorted(_module_tests(tree))
    assert named, f"{module_path.name} defines no test, so this guard grades nothing"

    hollow = _hollow_tests(tree)
    assert not hollow, (
        f"these tests cannot assert anything: {hollow}. A test emptied to its "
        "docstring passes for the same reason an empty one does, and it leaves "
        "the assertions nowhere a reader or a diff can miss them"
    )


def _digits_in(text: str) -> list[str]:
    """List the digit characters in a string, in the order they appear.

    Args:
        text: The prose to scan.

    Returns:
        The digits found, empty if the prose carries none.
    """
    return [character for character in text if character.isdigit()]


# ---------------------------------------------------------------------------
# The rule, and the criteria it admits
# ---------------------------------------------------------------------------


def test_the_rule_prose_names_every_code_it_governs() -> None:
    """CS-422 - the rule's text has to name the codes its own tables use."""
    criteria = objects.WIDTH_CRITERIA
    non_criteria = objects.WIDTH_NON_CRITERIA
    assert criteria, "WIDTH_CRITERIA is empty, so the naming check below grades nothing"
    assert non_criteria, "WIDTH_NON_CRITERIA is empty, so the naming check grades nothing"

    both = criteria & non_criteria
    assert not both, (
        f"a code is filed as both a criterion the rule admits and a reason it "
        f"does not: {sorted(both)}. A code on both sides admits whatever it is "
        f"pointed at"
    )

    rule = objects.WIDTH_SHIPPING_RULE
    unnamed = sorted(code for code in criteria | non_criteria if code not in rule)
    assert not unnamed, (
        f"the rule's own text does not name these codes: {unnamed}. A rule that "
        f"does not name what it admits and what it refuses can be replaced with "
        f"any sentence at all and the tables around it still agree"
    )


def test_every_shipped_width_names_a_criterion_the_rule_admits() -> None:
    """CS-422 - a shipped width carries a criterion, and the right class of one."""
    cursor = objects.CURSOR_WIDTHS
    extent = objects.EXTENT_WIDTHS
    assert cursor, "CURSOR_WIDTHS is empty, so the class check below grades nothing"
    assert extent, "EXTENT_WIDTHS is empty, so the class check below grades nothing"

    overlap = cursor & extent
    assert not overlap, (
        f"a width is filed as both a cursor width and an extent width: "
        f"{sorted(overlap)}. The two classes are graded by different oracles, so "
        f"a width in both has no single answer"
    )

    grounds = objects.WIDTH_SHIPPING_GROUNDS
    shipped = cursor | extent
    assert frozenset(grounds) == shipped, (
        f"the grounds table and the shipped widths disagree. Shipped with no "
        f"ground recorded: {sorted(shipped - frozenset(grounds))}. Ground "
        f"recorded for a width that does not ship: "
        f"{sorted(frozenset(grounds) - shipped)}"
    )

    invented = sorted(word for word, code in grounds.items() if code not in objects.WIDTH_CRITERIA)
    assert not invented, (
        f"these widths name a criterion the rule does not admit: {invented}. "
        f"The admitted set is WIDTH_CRITERIA and it is closed"
    )

    misclassed = sorted(
        word for word in cursor if grounds[word] != objects.CRITERION_CURSOR_REACH
    ) + sorted(word for word in extent if grounds[word] != objects.CRITERION_VALUE_DISAGREEMENT)
    assert not misclassed, (
        f"these widths are graded by the wrong criterion: {misclassed}. A cursor "
        f"width is graded by terminator reach and an extent width by value "
        f"disagreement, and grading either by the other reports it undetectable "
        f"when it is in fact detected"
    )


# ---------------------------------------------------------------------------
# The declines, and the exception set derived from them
# ---------------------------------------------------------------------------


def test_every_unmeasured_word_that_ships_a_tag_extra_width_is_declined() -> None:
    """CS-422 - the declined population is derived from the shipped tables."""
    ships_tag_extra = frozenset(objects._TAG_EXTRA_STRINGS)  # noqa: SLF001
    unmeasured = ships_tag_extra - objects.MEASURED_VALUE_TYPES
    assert unmeasured, (
        "no type word ships a tag-extra width while its value reading is "
        "unmeasured, so this test grades nothing. Either the shipped tables "
        "moved or this derivation no longer describes them"
    )

    undeclined = sorted(unmeasured - frozenset(objects.DECLINED_VALUE_READINGS))
    assert not undeclined, (
        f"these type words ship a tag-extra width and their value reading is "
        f"unmeasured, yet no decline is recorded against the rule for them: "
        f"{undeclined}. Declining one somewhere else, on a criterion the rule "
        f"disclaims, is what made the rule look like it had one exception when "
        f"the file applied more than one standard"
    )


def test_every_decline_carries_a_reason_code_from_the_closed_set() -> None:
    """CS-422 - a decline is a code plus prose, and the code set is closed."""
    declined = objects.DECLINED_VALUE_READINGS
    assert declined, "DECLINED_VALUE_READINGS is empty, so this test grades nothing"

    for word, entry in sorted(declined.items()):
        assert isinstance(entry, tuple), (
            f"the decline for {word} is not a reason code beside its prose. A "
            f"bare sentence records a decision without recording what rule it "
            f"was decided under"
        )
        assert len(entry) == _DECLINE_FIELDS, (
            f"the decline for {word} does not carry exactly a reason code and its prose"
        )
        code, prose = entry
        assert code in objects.WIDTH_NON_CRITERIA, (
            f"the decline for {word} names {code!r}, which is not one of the "
            f"reasons the rule recognises. Inventing a code per entry is "
            f"deciding per entry with extra steps"
        )
        assert prose.strip(), (
            f"the decline for {word} carries a reason code and no prose, so a "
            f"later slice re-opening it learns nothing about what would settle it"
        )


def test_the_exception_set_is_derived_from_the_codes() -> None:
    """CS-422 - the exception set is a union of code classes, never transcribed."""
    declined = objects.DECLINED_VALUE_READINGS
    exceptions = objects.WIDTH_RULE_EXCEPTIONS
    assert declined, "DECLINED_VALUE_READINGS is empty, so this test grades nothing"
    assert exceptions, (
        "WIDTH_RULE_EXCEPTIONS is empty. The rule records its exceptions "
        "against itself, and an empty set says it has none"
    )

    stray = sorted(frozenset(exceptions) - frozenset(declined))
    assert not stray, (
        f"these words are exceptions to the rule without being declines under "
        f"it: {stray}. An exception with no decline behind it was transcribed"
    )

    # Refuse a shape this test cannot read, rather than unpacking it and
    # raising. The closed-set test owns the shape; what this buys is that a
    # malformed decline reddens here with a sentence instead of an unpacking
    # error from the middle of a comprehension.
    unshaped = sorted(
        word
        for word, entry in declined.items()
        if not isinstance(entry, tuple) or len(entry) != _DECLINE_FIELDS
    )
    assert not unshaped, (
        f"these declines are not a reason code beside its prose: {unshaped}, so "
        f"no reason code can be read off them and the derivation below is undefined"
    )

    # Which reason codes mark an exception is the shipping module's decision,
    # so it is READ rather than pinned here. What is asserted is that the set
    # is CLOSED over those codes: every decline sharing a code with an
    # exception is itself an exception. A transcribed set drifts the moment a
    # decline is added and this is what refuses that.
    exception_codes = {code for word, (code, _) in declined.items() if word in exceptions}
    assert exception_codes <= objects.WIDTH_NON_CRITERIA, (
        f"an exception is filed under a code the rule does not list as a "
        f"non-criterion: {sorted(exception_codes - objects.WIDTH_NON_CRITERIA)}"
    )

    recomputed = frozenset(word for word, (code, _) in declined.items() if code in exception_codes)
    assert frozenset(exceptions) == recomputed, (
        f"the exception set is not the set its own reason codes produce. "
        f"Recorded and not derivable: {sorted(frozenset(exceptions) - recomputed)}. "
        f"Derivable and not recorded: {sorted(recomputed - frozenset(exceptions))}"
    )

    measured = frozenset(exceptions) & objects.MEASURED_VALUE_TYPES
    assert not measured, (
        f"these words are exceptions to the width rule and also types whose "
        f"value encoding is measured: {sorted(measured)}. A measured reading "
        f"that is also a declined reading is one of the two claims being wrong"
    )


def test_no_family_decline_restates_a_count_the_region_table_owns() -> None:
    """CS-422 - a decline points at the region table for a count, never copies one."""
    declined = objects.DECLINED_VALUE_READINGS
    regions = objects.UNMEASURED_PAYLOAD_REGIONS
    shared = sorted(frozenset(declined) & frozenset(regions))
    assert shared, (
        "no declined word has an entry in UNMEASURED_PAYLOAD_REGIONS, so this "
        "test grades nothing. Either the tables moved apart or the overlap this "
        "guards has gone"
    )

    # The shape is asserted here as well as in the closed-set test, and not
    # because it is that test's job twice. Indexing field one of a BARE STRING
    # yields its second character, which carries no digit and would report this
    # test green while the prose it exists to scan went unread. A vacuous pass
    # is the failure mode this whole module was rewritten to remove.
    unshaped = sorted(
        word
        for word in shared
        if not isinstance(declined[word], tuple) or len(declined[word]) != _DECLINE_FIELDS
    )
    assert not unshaped, (
        f"these declines are not a reason code beside its prose: {unshaped}. "
        f"The scan below would read one character of each instead of the prose"
    )

    restated = {word: _digits_in(declined[word][1]) for word in shared}
    offenders = sorted(word for word, digits in restated.items() if digits)
    assert not offenders, (
        f"these declines write a figure that UNMEASURED_PAYLOAD_REGIONS owns: "
        f"{offenders}. CLAUDE.md section 4 gives a measured number exactly one "
        f"owner file, and the same number in two entries is the drift that rule "
        f"exists to stop - point at the region table instead of copying it"
    )


# ---------------------------------------------------------------------------
# The guard against this module being emptied
# ---------------------------------------------------------------------------


def test_no_test_in_this_module_is_emptied_to_a_docstring_or_a_pass() -> None:
    """CS-422 - the guard against grading the rule with a file of empty bodies."""
    _assert_no_test_is_hollow(Path(__file__))


def test_the_gutting_guard_here_catches_a_spliced_empty_body(tmp_path: Path) -> None:
    """CS-422 - the guard's power, forced against a copy rather than asserted about.

    A guard that returned an empty list on every module would pass on this one
    and read exactly like a working guard. The splices below are the three
    empty shapes themselves, appended to a COPY of this module in ``tmp_path``,
    with the unspliced source run afterwards as the positive control.
    """
    spliced = tmp_path / "hollowed.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef test_spliced_docstring_only():\n"
        '    """A test emptied to its docstring."""\n'
        "\n\ndef test_spliced_pass_only():\n"
        "    pass\n"
        "\n\ndef test_spliced_docstring_and_pass():\n"
        '    """A test emptied to its docstring and a pass."""\n'
        "    pass\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        _assert_no_test_is_hollow(spliced)
    reported = str(caught.value)
    for name in (
        "test_spliced_docstring_only",
        "test_spliced_pass_only",
        "test_spliced_docstring_and_pass",
    ):
        assert name in reported, f"the guard missed the {name} shape"

    # The positive control: the unspliced source passes, so the red above is
    # the splice rather than a guard that rejects every module it is handed.
    _assert_no_test_is_hollow(Path(__file__))
