"""CS-891 - the two class-closing walks, run over every module in the family.

WHY THIS MODULE EXISTS. ``tests/test_docs_citations.py`` closes two classes by
walking its OWN globals: every compiled pattern it judges by must be a member of
its carrier boundary, and every module-scope container it holds must either
ratchet as a forgiveness or be recorded as forgiving nothing. Both walks read
``globals()``, so both see exactly one file.

THAT WAS SOUND WHILE THE FAMILY WAS ONE FILE AND STOPPED BEING SOUND THE MOMENT
IT WAS TWO. ``tests/bare_path_guard.py`` now holds the shape and the ladder, and
a pattern or a forgiveness table declared there and not imported back is
invisible to both walks - the table forgives, the ladder consults it, and the
contract written to make an unregistered table impossible reports a confident
zero. RELOCATION IS THE SAME EVASION AS NAMING. The container walk already
refuted "spell it in lower case" and then reproduced the fault one shape along
with a prefix rule; "spell it in the other file" is the third door onto the same
room, and it is the one a file split opens by itself.

WHAT CLOSES IT, IN TWO HALVES. An IMPORTED name is in ``globals()``, so anything
imported back into the module that judges it is walked exactly as before - which
is why the split cost no test identifier and changed no verdict. And what is NOT
imported back is reached here, over a population DERIVED FROM THE IMPORT GRAPH:
:func:`namespace_closure` starts at this module and follows every tests-package
import transitively, so a table relocated one hop or two is still walked and a
third module arriving is walked without anybody remembering to add it.

THE ROOT IS THIS MODULE'S OWN NAME AND NOTHING IS HAND-LISTED. A list of the
modules to walk is the identical fault to a list of the tables to bound: right
the day it is written, silently short the day it is not. ``__name__`` is what the
interpreter already knows, and everything else is reachability.

WHY REACHABILITY IS THE RIGHT BOUNDARY. A table only forgives if the code reading
it RUNS, and it only runs if something imported it. A module nothing imports is
inert - it holds no live escape hatch and appears in no verdict. So the set of
modules that could hide one is exactly the set reachable from the arms.

AND A MODULE IN THAT SET THAT IS NOT PART OF THIS FAMILY IS RECORDED RATHER THAN
FILTERED OUT, for the reason ``tests/test_docs_citations.py`` records the docs it
leaves unguarded: a filter is a boundary nobody re-derives, and the next module
that happens to match it joins the unwalked set in silence. There is one such
module, it is a separate guard with its own contracts, and its row is pinned in
both directions and budgeted.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pytest

from tests import bare_path_guard, test_docs_citations
from tests.bare_path_guard import (
    REGISTRY_NAMES,
    floor_problems,
    graded_floor_names,
    module_patterns,
    namespace_closure,
    registry_problems,
    sibling_imports,
)

#: The one module the walk starts from. DERIVED FROM THE INTERPRETER rather than
#: spelled, so the root cannot drift from the file it names, and a single root
#: rather than a list because everything else is reachability - this module
#: imports the module that judges, which imports the module that derives.
WALK_ROOT: Final = __name__

#: How many modules the closure must reach before the walks below are measuring
#: the family they describe rather than whatever the import graph happened to
#: return. A FLOOR rather than a pin: a fourth derivation module should not spend
#: an adjudication, and losing one must redden.
_WALKED_MODULE_FLOOR: Final = 4

#: Every module the closure reaches that is NOT part of this family, and why.
#: RECORDED RATHER THAN FILTERED, for the reason the unguarded-doc record exists:
#: a rule like "anything in a subpackage" is the open-ended prefix boundary this
#: family has already shipped twice and had to repair twice.
#:
#: PINNED IN BOTH DIRECTIONS AND BUDGETED. The contract below derives which
#: modules declare no registry pair and requires that set to EQUAL this one, so a
#: row added for a module that does declare the pair is stale and reddens, and a
#: module that declares nothing and is unrecorded reddens too. The pin catches a
#: row added ALONE; it cannot catch a row added TOGETHER WITH the module it
#: excuses, and that pair is the whole purchase - which is why the ceiling counts
#: the rows as well.
NOT_A_CITATION_GUARD: Final[Mapping[str, str]] = {
    "tests.save.test_oracle_citations": (
        "a separate guard with its own item and its own contracts, imported here"
        " for one resolver rather than for anything it forgives"
    ),
}

#: The recorded budget for the table above. An integer somebody typed, so
#: excusing a second module is a number in the diff rather than a row.
_SEPARATE_GUARD_CEILING: Final = 1

#: EVERY FORGIVENESS TABLE THIS MODULE HOLDS. Empty, and checked rather than
#: claimed: the contract below walks this module too.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {}

#: The other half of this module's own registry pair, for the reason every walked
#: module declares one - this module is in its own population, which is the
#: property that makes the arms below apply to the file that hosts them.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "NOT_A_CITATION_GUARD": "records what is out of the family; it forgives no citation",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
    "REGISTRY_NAMES": "the two names a module declares the pair under, imported to pin it",
}


@pytest.fixture(scope="module")
def closure() -> dict[str, Mapping[str, object]]:
    """The live population, derived once so every arm reads the same one."""
    return namespace_closure([WALK_ROOT])


def family(
    closure: Mapping[str, Mapping[str, object]],
) -> list[tuple[str, Mapping[str, object]]]:
    """The walked closure less the modules recorded as separate guards.

    ONE PLACE, because both walks must exclude the SAME modules. Two arms each
    writing their own filter is two boundaries to drift, and the one that drifted
    wider would be the one still reporting a clean zero.
    """
    return sorted(
        (dotted, namespace)
        for dotted, namespace in closure.items()
        if dotted not in NOT_A_CITATION_GUARD
    )


def test_the_walked_population_is_derived_and_reaches_every_module_in_the_family(
    closure: Mapping[str, Mapping[str, object]],
) -> None:
    """THE POPULATION, ASSERTED BEFORE ANYTHING IS ASSERTED ABOUT IT.

    Every walk below is an ``assert not problems``, which reads identically
    whether the property holds or whether the closure arrived empty - and this
    one is assembled by parsing source and resolving names, two places it could
    silently shrink to the root alone.

    THE MEMBERS ARE NAMED BY THEIR MODULE OBJECTS, never spelled, so the check
    cannot pass because one string happened to match another.
    """
    short = floor_problems("modules in the walked closure", len(closure), _WALKED_MODULE_FLOOR)

    assert not short, "\n".join(short) + (
        " The closure has stopped following the import graph, so the walks below are"
        " reading a population smaller than the family they describe."
    )
    for module in (test_docs_citations, bare_path_guard):
        assert module.__name__ in closure, (
            f"{module.__name__} is not in the walked closure, so a pattern or a"
            " forgiveness table declared in it is judged by nothing"
        )
    assert WALK_ROOT in closure, "the walk does not reach the module that hosts it"


def test_the_import_walk_reads_both_spellings_of_a_module_import_and_no_function() -> None:
    """The derivation's OWN boundary, on a source built for the purpose.

    THE CONTRACT ABOVE CANNOT PROVE THIS: it asks whether the closure reached
    three named modules, and "yes" reads the same whether the walk understands
    every import spelling or merely found them by the one spelling it does read.

    FOUR DIRECTIONS. A ``from package import module`` names the module in the
    ``names`` list and must be read there; a ``from package.module import name``
    names it in ``module`` and must be read there; a name that is a FUNCTION
    rather than a module must not become one; and an import from outside the
    tests package must not join the closure at all.
    """
    package, leaf = WALK_ROOT.split(".", 1)
    source = "\n".join(
        (
            f"from {package} import {leaf}",
            f"from {bare_path_guard.__name__} import namespace_closure",
            f"from {bare_path_guard.__name__} import a_name_that_is_not_a_module",
            "import re",
            "from pathlib import Path",
        )
    )

    found = sibling_imports(source)

    assert found == {WALK_ROOT, bare_path_guard.__name__}, (
        f"the import walk read {sorted(found)}. Both module spellings must be seen -"
        " a walk that reads only one returns a short closure and a confident zero -"
        " while an imported function and a module outside the package must not be."
    )
    assert sibling_imports("x = 1") == frozenset(), (
        "a source importing nothing yielded a sibling, so the walk invents members"
    )


def test_every_pattern_in_every_walked_module_is_a_judged_shape(
    closure: Mapping[str, Mapping[str, object]],
) -> None:
    """THE FIRST WALK, GENERALISED - and the generalisation is the whole point.

    The single-module form reads ``globals()`` and is blind to every other file
    by construction, so the fifth shape's own pattern could have been moved into
    the module that derives with it and left the boundary contract green.

    THE POPULATION IS DERIVED TWICE OVER: which modules to walk comes from the
    import graph, and which names are patterns comes from each namespace. Neither
    is a list somebody has to remember to extend.
    """
    compiled = {
        f"{dotted}.{name}": pattern
        for dotted, namespace in family(closure)
        for name, pattern in sorted(module_patterns(namespace).items())
    }

    assert compiled, (
        "no module in the closure compiles a pattern this family judges by, so the"
        " derivation below reads an empty set and would pass whatever it ignored"
    )
    judged = test_docs_citations.JUDGED_SHAPES
    missing = sorted(name for name, pattern in compiled.items() if pattern not in judged)
    assert not missing, (
        "patterns this family judges by that the carrier boundary does not read:\n"
        + "\n".join(f"  {name}" for name in missing)
        + "\nAdd it to the judged shapes, or stop judging by it."
    )


def test_a_pattern_declared_one_module_over_is_reported_rather_than_unseen() -> None:
    """The control the live walk cannot be: a pattern the boundary has never read.

    THE GREEN ANSWER ABOVE MEANS NOTHING WITHOUT THIS. A tree in which every
    pattern happens to be registered and a walk that cannot see an unregistered
    one produce the same output, and only one of the two is a guard.
    """
    planted = re.compile("a-shape-the-boundary-has-never-been-told-about")
    space: dict[str, object] = {"RELOCATED_RE": planted, "NOT_A_PATTERN_RE": "a string"}

    found = module_patterns(space)

    assert sorted(found) == ["RELOCATED_RE"], (
        f"the pattern walk returned {sorted(found)}. A compiled pattern must be seen"
        " wherever it is declared, and a string named like one must not be."
    )
    assert planted not in test_docs_citations.JUDGED_SHAPES, (
        "the planted pattern is already a judged shape, so the arm above would forgive"
        " it and this control would prove nothing"
    )


def test_every_container_in_every_walked_module_is_answered_by_its_own_registries(
    closure: Mapping[str, Mapping[str, object]],
) -> None:
    """THE SECOND WALK, GENERALISED, and the one a file split reopens by itself.

    A forgiveness table declared in the module that derives and never imported
    back is invisible to the single-module walk. It still forgives: the ladder
    consults it, sites disappear from the reported rung, and the contract whose
    entire purpose is to make an unregistered table impossible sees nothing.

    A MODULE ANSWERS FOR WHAT IT HOLDS. The registries are read out of each
    walked namespace rather than pooled, because a pooled registry would have to
    name modules as well as tables and the module nobody added would be the one
    nobody noticed - this family's founding finding, one level up again.
    """
    problems = [
        f"{dotted}: {problem}"
        for dotted, namespace in family(closure)
        for problem in registry_problems(namespace)
    ]

    assert not problems, (
        "module-scope containers in this family that nothing counts:\n"
        + "\n".join(f"  {problem}" for problem in problems)
        + "\nBound it in that module's forgiveness registry, or record there why it"
        " forgives nothing."
    )


def test_a_table_relocated_into_another_module_without_a_record_is_reported() -> None:
    """THE PLANT, and it is the finding this whole module exists to make.

    Relocation is the evasion a split opens: declare the table one file over,
    import nothing back, and the walk reading ``globals()`` reports zero. The
    namespace here is BUILT rather than borrowed, which is the only way to pose
    the question about a table this family happens not to hold.

    SIX DIRECTIONS, one per leg, because a registry pair can be green while being
    empty, absent, contradictory, stale, or pointing at nothing.
    """

    def contract() -> None:
        """A callable standing in for a bound table's contract."""

    registries = {
        "FORGIVENESS_TABLES": "the registry itself",
        "NOT_A_FORGIVENESS": "the registry itself",
    }
    bound = {"RELOCATED_FORGIVENESS": "test_a_bounding_contract"}

    def space(bounded: Mapping[str, str], nothing: Mapping[str, str]) -> dict[str, object]:
        return {
            "RELOCATED_FORGIVENESS": {("a", "b", "c"): 1},
            "FORGIVENESS_TABLES": dict(bounded),
            "NOT_A_FORGIVENESS": dict(nothing),
            "test_a_bounding_contract": contract,
        }

    assert registry_problems(space(bound, registries)) == [], (
        "a namespace whose registries answer every container it holds was reported,"
        " so the arm above cannot be green for the right reason"
    )

    relocated = registry_problems(space({}, registries))

    assert len(relocated) == 1, f"a relocated forgiveness table was absorbed: {relocated}"
    assert "RELOCATED_FORGIVENESS" in relocated[0], (
        f"the one finding does not name the relocated table: {relocated}"
    )

    silent = space(bound, registries)
    del silent["NOT_A_FORGIVENESS"]

    assert len(registry_problems(silent)) == 1, (
        "a module declaring no registry pair was accepted, so relocating a table into"
        " a module that simply declines to answer buys silence for free"
    )

    both = registry_problems(space(bound, {**registries, "RELOCATED_FORGIVENESS": "claimed twice"}))

    assert any("both" in problem for problem in both), (
        f"a table registered as both a forgiveness and not one was accepted: {both}"
    )

    stale = registry_problems(
        space(bound, {**registries, "A_NAME_THIS_NAMESPACE_DOES_NOT_HOLD": "gone"})
    )

    assert any("no longer holds" in problem for problem in stale), (
        f"a registry row for a container the module no longer holds was accepted: {stale}"
    )

    dangling = registry_problems(
        space({"RELOCATED_FORGIVENESS": "test_a_contract_nothing_defines"}, registries)
    )

    assert any("does not define" in problem for problem in dangling), (
        f"a bounded table naming a contract that does not exist was accepted: {dangling}"
    )


def test_the_separate_guard_record_is_pinned_in_both_directions_and_budgeted(
    closure: Mapping[str, Mapping[str, object]],
) -> None:
    """The exemption, DERIVED against the closure rather than trusted.

    A module recorded as outside this family must actually be outside it, and a
    module outside it must actually be recorded. Both directions, because a
    record for a module that has since grown a registry pair has stopped
    describing anything, and a maintainer reading it would be told a false thing
    about a live file.

    AND IT IS BUDGETED, because the pin catches a row added ALONE and never one
    added together with the module it excuses - which is the entire purchase.
    """
    silent = {
        dotted
        for dotted, namespace in closure.items()
        if not all(isinstance(namespace.get(name), Mapping) for name in REGISTRY_NAMES)
    }

    assert silent == set(NOT_A_CITATION_GUARD), (
        f"the modules declaring no registry pair are {sorted(silent)} and the record"
        f" names {sorted(NOT_A_CITATION_GUARD)}. A module missing from the record is"
        " one nothing walks; a record naming a module that now declares the pair has"
        " stopped describing anything."
    )
    assert len(NOT_A_CITATION_GUARD) <= _SEPARATE_GUARD_CEILING, (
        f"{len(NOT_A_CITATION_GUARD)} modules are excused against a ceiling of"
        f" {_SEPARATE_GUARD_CEILING}. Excusing another is a number in the diff."
    )
    assert len(NOT_A_CITATION_GUARD) == _SEPARATE_GUARD_CEILING, (
        f"the ceiling is {_SEPARATE_GUARD_CEILING} and {len(NOT_A_CITATION_GUARD)}"
        " rows are spent, so it is slack after a repair. Lower it."
    )
    for dotted, why in sorted(NOT_A_CITATION_GUARD.items()):
        assert why.strip(), f"{dotted} is excused and states no reason"


@pytest.mark.parametrize(
    ("what", "floor"),
    [("modules in the walked closure", _WALKED_MODULE_FLOOR)],
)
def test_every_non_vacuity_floor_rejects_a_population_that_measured_nothing(
    what: str, floor: int
) -> None:
    """THE FLOOR, GRADED - because it could be set to zero with the suite green.

    THREE DIRECTIONS: nothing measured is rejected, one short is rejected, and
    the floor itself is accepted, so this is about the boundary rather than about
    the floor being large.
    """
    assert floor_problems(what, 0, floor), (
        f"the floor under {what} is {floor}, which ACCEPTS a population of nothing -"
        " the defect it exists to prevent, restored"
    )
    assert floor_problems(what, floor - 1, floor), f"the floor under {what} is off by one"
    assert floor_problems(what, floor, floor) == [], (
        f"the floor under {what} rejects a population that exactly meets it"
    )


def test_every_floor_this_module_uses_is_one_this_arm_grades() -> None:
    """CLOSING THE CLASS, so a SECOND floor cannot arrive ungraded.

    The parametrization above is checked against what this module's SOURCE passes
    as a floor, rather than against a list somebody keeps in step by hand.
    """
    used = graded_floor_names(Path(__file__).read_text(encoding="ascii"))

    assert used, "this module passes no named floor to the floor check at all"
    graded = {"_WALKED_MODULE_FLOOR"}
    ungraded = sorted(used - graded)

    assert not ungraded, (
        f"floors used but not graded: {ungraded}. Add each to the parametrization"
        " above, so a floor that could be zeroed is one something asks about."
    )
    stale = sorted(graded - used)

    assert not stale, f"graded floors this module no longer uses as floors: {stale}"


def test_every_module_this_split_created_is_seven_bit_ascii() -> None:
    """Non-negotiable 4, on both halves of the split rather than assumed of them."""
    guard = Path(bare_path_guard.__file__)

    assert guard.is_file(), "the module this one is paired with is not on disk"
    for path in (Path(__file__), guard):
        raw = path.read_bytes()

        assert not [byte for byte in raw if byte > test_docs_citations.HIGHEST_ASCII], (
            f"{path.name} carries a byte above the 7-bit range"
        )
