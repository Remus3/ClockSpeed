#!/usr/bin/env python3
"""CS-871 - the arms over :mod:`tests.sphinx_role_guard`.

THE LIVE ARM AND ITS CONTROLS ARE THE POINT. A walk that reports no unresolved
role and a walk that read nothing print the same number, so every arm here
either asserts a real finding or asserts that the walk can still produce one.
The planted-role arm runs against a REAL module's text rather than a toy
string, because an oracle that can only see a fixture it built itself says
nothing about the frames the live arm enters.

THIS MODULE IS INSIDE THE POPULATION IT GRADES, which decides how its fixtures
are written. A role spelled out here - especially one naming a deliberately
dead symbol - is a role in a tracked tests module and the live arm would report
it. :func:`role` assembles the text at run time, so the walk still reads exactly
the bytes it would have read while this module's own source carries none of
them.
"""

from __future__ import annotations

from typing import Final

import pytest

from tests.sphinx_role_guard import (
    GRADED,
    ROLE_DISPOSITIONS,
    dotted_target_resolves,
    graded_roles,
    graded_site_count,
    graded_sources,
    role_sites,
    role_spellings,
    unresolved_roles,
)
from tests.test_docs_citations import tracked_files

#: The smallest number of graded role sites this corpus may contain before the
#: live arm is presumed to have stopped reading. BELOW the measured count on
#: purpose - a floor that tracked the corpus would need editing on every commit
#: that writes a docstring, and a floor nobody dares edit gets deleted.
#:
#: IT IS NOT THE CONTROL AGAINST A SPELLING BEING DROPPED, and a first draft of
#: this module treated it as one. A refutation pass measured that un-grading
#: ``data`` or ``class`` leaves the count above any floor loose enough to be
#: stable. :data:`GRADED_SPELLING_COUNT` is what answers that, because the
#: defect is a change of SET rather than a change of size.
GRADED_SITE_FLOOR: Final = 1500

#: How many spellings the resolver grades. PINNED because every other arm in
#: this module reads the graded set from the table and would follow it down: a
#: spelling moved from GRADED to a reason string keeps the vocabulary equality
#: green, keeps the reason arm green, and silently removes its sites from the
#: per-spelling plant. CS-1075 raises this to the whole vocabulary; nothing else
#: may change it downward.
GRADED_SPELLING_COUNT: Final = 3

#: The module the planted-role arms mutate in memory. Chosen because it is the
#: subject of this file, so an arm that stopped reading it would be visible
#: here rather than in a module nobody opens.
PLANTED_SUBJECT: Final = "tests/sphinx_role_guard.py"

#: A symbol no module in this repository binds. Spelled to be unmistakable in a
#: grep, so a plant that escaped into the tree could be found by reading.
PLANTED_DEAD_NAME: Final = "_cs871_no_module_binds_this_name"

#: The character a Sphinx role wraps its target in, held apart so this module
#: can build role text without spelling any.
BACKTICK: Final = "`"


def role(kind: str, target: str) -> str:
    """Assemble role text at run time rather than spelling it in this module.

    Args:
        kind: The role name, without its colons.
        target: The symbol the role names.

    Returns:
        The role exactly as it would appear in prose.
    """
    return f":{kind}:{BACKTICK}{target}{BACKTICK}"


@pytest.fixture(scope="module")
def sources() -> dict[str, str]:
    return graded_sources(tracked_files())


def test_no_tests_module_names_an_unresolvable_symbol(sources: dict[str, str]) -> None:
    """Every graded role in a tests module resolves against a real namespace.

    THE ITEM'S ACCEPTANCE CLAUSE. A role naming a symbol the citing module does
    not bind is repaired by QUALIFYING it with the module that does, not by
    deleting it - the reference is prose somebody wrote for a reader.
    """
    dead = unresolved_roles(sources)
    count = len(dead)
    listed = "\n".join(
        f"  {path}:{line} {role(kind, target)}" for path, line, kind, target in dead[:40]
    )
    assert count == 0, (
        f"{count} Sphinx roles in tests modules name a symbol nothing resolves.\n"
        f"{listed}\n"
        "Qualify the role with the module that defines the symbol, or fix the name."
    )


def test_the_graded_population_is_not_empty(sources: dict[str, str]) -> None:
    """The live arm judged a real corpus rather than an empty one.

    A clean corpus and a walk that read nothing both report zero findings. This
    arm is the only thing that separates them.
    """
    judged = graded_site_count(sources)
    assert judged >= GRADED_SITE_FLOOR, (
        f"{judged} graded role sites were read, below the floor of {GRADED_SITE_FLOOR}. "
        "The walk has stopped reading the corpus it is supposed to grade."
    )


def test_every_role_spelling_in_the_corpus_is_declared(sources: dict[str, str]) -> None:
    """The role vocabulary is an allowlist asserted as an equality.

    A SEVENTH SPELLING REDDENS THIS ARM rather than passing unread. The item
    that filed this guard rules that learning one role and stopping buys one
    spelling of the property, and a declared table is how that ruling is kept
    mechanically rather than remembered.
    """
    found = role_spellings(sources)
    declared = frozenset(ROLE_DISPOSITIONS)
    mismatch = {
        "undeclared": sorted(found - declared),
        "declared but absent from the corpus": sorted(declared - found),
    }
    offending = {label: names for label, names in mismatch.items() if names}
    assert not offending, (
        f"the corpus and ROLE_DISPOSITIONS disagree: {offending}\n"
        "Grade the spelling in ROLE_DISPOSITIONS, or record why it is not graded."
    )


def test_an_ungraded_spelling_carries_a_reason() -> None:
    """Every spelling that is not graded says why, and names the row that owns it."""
    silent = sorted(
        name
        for name, disposition in ROLE_DISPOSITIONS.items()
        if disposition != GRADED and not disposition.startswith("CS-")
    )
    assert not silent, f"ungraded role spellings with no item id behind them: {silent}"


def test_a_planted_dead_role_reddens(sources: dict[str, str]) -> None:
    """A dead role planted into a real module is reported.

    THE MUTATION THE LIVE ARM IS GRADED BY. The subject is the real text of a
    real module, so a resolver that had stopped entering that frame could not
    pass this.
    """
    planted = sources[PLANTED_SUBJECT] + f'\n\n"""{role("func", PLANTED_DEAD_NAME)}."""\n'
    dead = unresolved_roles({PLANTED_SUBJECT: planted})
    targets = [target for _path, _line, _kind, target in dead]
    assert targets == [PLANTED_DEAD_NAME], (
        f"the planted dead role was not the single finding; got {targets}"
    )


def test_the_planted_subject_is_clean_without_the_plant(sources: dict[str, str]) -> None:
    """The control for the arm above - the unplanted module reports nothing.

    Without this, a plant arm passes on a module that was already red, and the
    mutation would have proved nothing about the plant.
    """
    dead = unresolved_roles({PLANTED_SUBJECT: sources[PLANTED_SUBJECT]})
    assert dead == [], f"the planted subject is not clean before the plant: {dead}"


def test_a_planted_dead_role_reddens_in_every_graded_spelling(sources: dict[str, str]) -> None:
    """The plant is not a property of one role spelling.

    An arm that only ever plants one role proves the walk reads that role. Each
    graded spelling gets the same plant, so a resolver that silently dropped a
    spelling from its filter cannot pass.
    """
    survived = []
    for kind in sorted(graded_roles()):
        planted = sources[PLANTED_SUBJECT] + f'\n\n"""{role(kind, PLANTED_DEAD_NAME)}."""\n'
        if not unresolved_roles({PLANTED_SUBJECT: planted}):
            survived.append(kind)
    assert not survived, f"a planted dead role went unreported for spellings: {survived}"


def test_a_role_naming_an_imported_name_resolves() -> None:
    """An imported name is part of the citing module's namespace."""
    source = f"from tests.bare_path_guard import module_file\n\n'{role('func', 'module_file')}'\n"
    assert unresolved_roles({"tests/x.py": source}) == []


def test_a_role_naming_a_method_of_a_class_in_the_module_resolves() -> None:
    """A role in a class docstring may name that class's own method."""
    source = (
        f"class C:\n    '''{role('func', 'helper')}'''\n\n"
        "    def helper(self) -> None:\n        ...\n"
    )
    assert unresolved_roles({"tests/x.py": source}) == []


def test_a_qualified_cross_module_role_resolves() -> None:
    """A dotted target is resolved against the module it names, not the citer."""
    assert dotted_target_resolves("tests.bare_path_guard.module_file")


def test_a_qualified_role_naming_an_absent_symbol_does_not_resolve() -> None:
    """The dotted resolver is not a rubber stamp for anything with a dot in it."""
    assert not dotted_target_resolves(f"tests.bare_path_guard.{PLANTED_DEAD_NAME}")


def test_a_dotted_target_whose_prefix_is_no_module_does_not_resolve() -> None:
    """A dotted name pointing at no file on disk is an unresolved symbol."""
    assert not dotted_target_resolves("no.such.module.at_all")


def test_the_longest_module_prefix_is_the_one_asked() -> None:
    """Resolution runs downward, so the deepest module answers.

    ``tests.sphinx_role_guard.GRADED`` must be read as ``GRADED`` inside
    ``tests/sphinx_role_guard.py``. A search that ran upward would ask the
    ``tests`` package for a symbol named ``sphinx_role_guard`` and answer the
    wrong question.
    """
    assert dotted_target_resolves("tests.sphinx_role_guard.GRADED")
    assert not dotted_target_resolves("tests.sphinx_role_guard.bare_path_guard")


def test_a_tilde_prefixed_target_is_read_without_its_tilde() -> None:
    """Sphinx's abbreviating tilde is presentation, not part of the symbol."""
    sites = role_sites(role("func", "~tests.bare_path_guard.module_file"))
    assert [target for _line, _kind, target in sites] == ["tests.bare_path_guard.module_file"]


def test_the_graded_set_is_exactly_the_table_entries_marked_graded() -> None:
    """The resolver's role set is derived from the table, never transcribed."""
    assert graded_roles() == frozenset(
        name for name, disposition in ROLE_DISPOSITIONS.items() if disposition == GRADED
    )


def test_the_number_of_graded_spellings_is_pinned() -> None:
    """A spelling cannot leave the graded set in silence.

    THE ONE ARM IN THIS MODULE THAT DOES NOT READ THE TABLE FOR ITS EXPECTATION.
    Every other arm derives from :data:`ROLE_DISPOSITIONS`, so a spelling
    demoted to a reason string takes them all with it - the vocabulary equality
    still holds, the reason arm still holds, and the plant simply stops being
    run for that spelling. A refutation pass measured exactly that.
    """
    graded = sorted(graded_roles())
    assert len(graded) == GRADED_SPELLING_COUNT, (
        f"{len(graded)} spellings are graded ({graded}), pinned at {GRADED_SPELLING_COUNT}. "
        "Raising it is CS-1075's job; lowering it removes sites from every arm here."
    )
