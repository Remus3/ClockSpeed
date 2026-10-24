"""CS-1240: a display-name change in the registry changes no advisor output but the names.

THE CLAIM (CS-1240 acceptance 2). Every join the advisor makes - the audit
models it composes, the rule inputs it offers, the card ids it keys the ledger
by - is keyed on the stable class identifier, never on a display name. So the
same world advised against two registries that differ ONLY in display names
gives identical inputs and identical card ids. The two inputs that ARE display
names - ``fuel_rules.IN_CLASS_NAMES`` and ``fuel_rules.IN_FUEL_NAMES``, offered
verbatim for a card's wording (G4) - are the one place the rename may and must
show, and an arm below proves it reaches them, so the identity half is not
satisfied by a rename that never arrived.

The worlds and registries are the advisor suite's own synthetic fixtures; every
store lives in ``tmp_path`` and every instant is injected.
"""

from __future__ import annotations

from dataclasses import fields, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import advise_world, inputs_of
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.rules import fuel as fuel_rules
from tests.advisor import test_world_advice as worlds
from tests.advisor.build_fixtures import docs_pin, game_pin

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from clockspeed.advisor.advise import Advice
    from clockspeed.advisor.trace import WorldInputs
    from clockspeed.data.registry import Registry

#: The two inputs that carry a display name verbatim, for wording only.
DISPLAY_NAME_INPUTS: Final = frozenset({fuel_rules.IN_CLASS_NAMES, fuel_rules.IN_FUEL_NAMES})

#: What every non-empty display name is renamed to: a prefix, so the new name
#: is printable ASCII and differs from the old one.
RENAME_PREFIX: Final = "Renamed "


def _renamed_entries(entries: Mapping[str, object]) -> Mapping[str, object]:
    """Every entry with a non-empty display name renamed; nothing else touched.

    Args:
        entries: One registry namespace.

    Returns:
        A read-only copy, each display name prefixed.
    """
    out: dict[str, object] = {}
    for key, entry in entries.items():
        names = {field.name for field in fields(entry)}  # type: ignore[arg-type]
        current = getattr(entry, "display_name", "") if "display_name" in names else ""
        if current:
            out[key] = replace(entry, display_name=RENAME_PREFIX + current)  # type: ignore[type-var]
        else:
            out[key] = entry
    return MappingProxyType(out)


def renamed(registry: Registry) -> Registry:
    """The same registry with every non-empty display name changed.

    Args:
        registry: The registry.

    Returns:
        The renamed registry. Keys, figures, warnings and provenance unchanged.
    """
    return replace(
        registry,
        items=_renamed_entries(registry.items),  # type: ignore[arg-type]
        recipes=_renamed_entries(registry.recipes),  # type: ignore[arg-type]
        buildings=_renamed_entries(registry.buildings),  # type: ignore[arg-type]
        extractors=_renamed_entries(registry.extractors),  # type: ignore[arg-type]
        generators=_renamed_entries(registry.generators),  # type: ignore[arg-type]
    )


def _renamed_count(registry: Registry) -> int:
    """How many entries the rename actually changed - the control's count.

    Args:
        registry: The original registry.

    Returns:
        The number of entries carrying a non-empty display name.
    """
    namespaces = (
        registry.items,
        registry.recipes,
        registry.buildings,
        registry.extractors,
        registry.generators,
    )
    return sum(
        1
        for namespace in namespaces
        for entry in namespace.values()
        if getattr(entry, "display_name", "")
    )


def _differing(left: WorldInputs, right: WorldInputs, *, display: bool) -> int:
    """How many inputs differ between two runs, on one side of the name split.

    Args:
        left: One run's inputs.
        right: The other run's.
        display: True to count only the display-name inputs, False to count
            every other input.

    Returns:
        The number of input names whose offered values differ, or that one
        run offers and the other does not.
    """
    names = set(left.values) | set(right.values)
    chosen = {name for name in names if (name in DISPLAY_NAME_INPUTS) is display}
    return sum(1 for name in chosen if left.values.get(name) != right.values.get(name))


def _inputs(world_name: str, *, rename: bool) -> WorldInputs:
    """The advisor's inputs for one fixture world, against one registry.

    Args:
        world_name: A key of ``worlds.WORLDS``.
        rename: Whether to rename every display name first.

    Returns:
        The inputs.
    """
    make_world, make_registry = worlds.WORLDS[world_name]
    registry = make_registry()
    return inputs_of(
        make_world(),
        renamed(registry) if rename else registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
    )


def _advice(world_name: str, directory: Path, *, rename: bool) -> Advice:
    """The advice for one fixture world, against one registry and fresh stores.

    Args:
        world_name: A key of ``worlds.WORLDS``.
        directory: Where this run's two stores live.
        rename: Whether to rename every display name first.

    Returns:
        The advice.
    """
    make_world, make_registry = worlds.WORLDS[world_name]
    registry = make_registry()
    return advise_world(
        make_world(),
        renamed(registry) if rename else registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=worlds.NOW,
    )


def _card_ids(advice: Advice) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Every card id, and the shown ones, in the order the advice lists them.

    Args:
        advice: The advice.

    Returns:
        (all ids, shown ids).
    """
    every = tuple(advised.card.id for advised in advice.cards)
    shown = tuple(advised.card.id for advised in advice.shown)
    return every, shown


def _headlines(advice: Advice) -> tuple[str, ...]:
    """Every card's tier-1 headline, in card order.

    Args:
        advice: The advice.

    Returns:
        The headlines.
    """
    return tuple(advised.card.tier1 for advised in advice.cards)


@pytest.mark.parametrize("world_name", sorted(worlds.WORLDS))
def test_a_rename_changes_no_input_but_the_display_names(world_name: str) -> None:
    """Every input that is not a display name is offered unchanged."""
    _make_world, make_registry = worlds.WORLDS[world_name]
    changed = _renamed_count(make_registry())
    assert changed > 0, "the fixture registry carries no display name to rename"
    before = _inputs(world_name, rename=False)
    after = _inputs(world_name, rename=True)
    differing = _differing(before, after, display=False)
    assert differing == 0


def test_the_rename_really_reaches_the_display_name_inputs() -> None:
    """The control: the fuel world offers display names, and they moved."""
    before = _inputs("fuel", rename=False)
    after = _inputs("fuel", rename=True)
    moved = _differing(before, after, display=True)
    assert moved == len(DISPLAY_NAME_INPUTS)


@pytest.mark.parametrize("world_name", sorted(worlds.WORLDS))
def test_a_rename_changes_no_card_id_and_no_card_shown(world_name: str, tmp_path: Path) -> None:
    """The ledger keys by card id; a rename must not orphan a recorded card."""
    before = _card_ids(_advice(world_name, tmp_path / "before", rename=False))
    after = _card_ids(_advice(world_name, tmp_path / "after", rename=True))
    fired = len(before[0])
    assert fired > 0, "the fixture world fires no card, so the id half grades nothing"
    assert after == before


def test_the_rename_really_reaches_a_card_headline(tmp_path: Path) -> None:
    """The control: the fuel world's wording names a renamed class or fuel."""
    before = _headlines(_advice("fuel", tmp_path / "before", rename=False))
    after = _headlines(_advice("fuel", tmp_path / "after", rename=True))
    renamed_lines = sum(1 for line in after if RENAME_PREFIX in line)
    assert before != after
    assert renamed_lines > 0
