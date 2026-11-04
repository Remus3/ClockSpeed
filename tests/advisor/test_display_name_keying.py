"""CS-1240 and CS-1379: a display-name change moves names and wording, and no identity.

THE CLAIM (CS-1240 acceptance 2). Every join the advisor makes - the audit
models it composes, the rule inputs it offers, the card ids it keys the ledger
by - is keyed on the stable class identifier, never on a display name. So the
same world advised against two registries that differ ONLY in display names
gives identical inputs and identical card ids. The inputs that ARE display
names - ``fuel_rules.IN_CLASS_NAMES`` and ``fuel_rules.IN_FUEL_NAMES``, and
``plan_rules.IN_TARGET_NAMES`` and ``plan_rules.IN_REDESIGN_TARGET_NAMES``, each
offered verbatim for a card's wording - are the one place the rename may and
must show, and arms below prove it reaches them, so the identity half is not
satisfied by a rename that never arrived.

THE STATED WORLDS (CS-1379). No world of ``worlds.WORLDS`` states a target, so none
reaches a plan rule with a plan. :data:`STATED_WORLDS` does, once for each rule,
through the fixtures ``tests/advisor/test_plan_world.py`` and
``tests/advisor/test_plan_redesign.py`` grade, and a rename there moves tier 1,
tier 2 where it names a target, and the one name input, and never a card id.

The worlds and registries are the advisor suite's own synthetic fixtures; every
store lives in ``tmp_path`` and every instant is injected.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import advise_world, inputs_of
from clockspeed.advisor.cards import card_for
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.rules import fuel as fuel_rules
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.advisor.trace import StepKind, run_rule
from tests.advisor import test_plan_redesign as route_worlds
from tests.advisor import test_plan_world as plan_worlds
from tests.advisor import test_world_advice as worlds
from tests.advisor.build_fixtures import docs_pin, game_pin

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from clockspeed.advisor.advise import Advice
    from clockspeed.advisor.cards import Card
    from clockspeed.advisor.plans import PlanRequest
    from clockspeed.advisor.trace import RuleSpec, Trace, WorldInputs
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

#: The inputs the fuel rules read a display name from, offered on every fuel world.
FUEL_NAME_INPUTS: Final = frozenset({fuel_rules.IN_CLASS_NAMES, fuel_rules.IN_FUEL_NAMES})

#: The inputs the plan rules read a display name from, offered with a value on a stated plan.
PLAN_NAME_INPUTS: Final = frozenset(
    {plan_rules.IN_TARGET_NAMES, plan_rules.IN_REDESIGN_TARGET_NAMES}
)

#: Every input that carries a display name verbatim, for wording only.
DISPLAY_NAME_INPUTS: Final = FUEL_NAME_INPUTS | PLAN_NAME_INPUTS

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
    assert moved == len(FUEL_NAME_INPUTS)


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


# ---------------------------------------------------------------------------
# CS-1379: the stated worlds, where a rename reaches a plan rule
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Stated:
    """One world whose stated target reaches one plan rule.

    Attributes:
        rule: The rule that fires on it.
        names_input: The name input it reads, and the only input a rename may move.
        tier2_names_the_target: Whether its tier 2 says the target at all.
    """

    rule: RuleSpec
    names_input: str
    tier2_names_the_target: bool

    def parts(self) -> tuple[WorldModel, Registry, PlanRequest]:
        """The world, the registry and the request, built fresh for this rule."""
        if self.rule is plan_rules.ADOPT_RULE:
            return (
                plan_worlds._model(plan_worlds.ASCENT_PATHS),  # noqa: SLF001
                plan_worlds._registry(),  # noqa: SLF001
                plan_worlds._request(),  # noqa: SLF001
            )
        registry = route_worlds._three_locked_registry()  # noqa: SLF001
        return (
            route_worlds._model([route_worlds.HELD_STAGE]),  # noqa: SLF001
            registry,
            route_worlds._request(registry),  # noqa: SLF001
        )


#: One stated world for each rule of the plan family.
STATED_WORLDS: Final = MappingProxyType(
    {
        "adopt": _Stated(plan_rules.ADOPT_RULE, plan_rules.IN_TARGET_NAMES, True),
        "redesign": _Stated(plan_rules.REDESIGN_RULE, plan_rules.IN_REDESIGN_TARGET_NAMES, False),
    }
)

#: Names the engine's text test refuses, each a plain ``str`` the registry could hold.
UNPRINTABLE_NAMES: Final = MappingProxyType(
    {
        "not-ascii": "Solve Relic \u00e9",
        "a-tab": "Solve\tRelic",
        "a-newline": "Solve\nRelic",
        "a-nul": "Solve\x00Relic",
        "a-del": "Solve\x7fRelic",
        "only-spaces": "   ",
    }
)


def _stated_inputs(stated: _Stated, *, rename: bool) -> WorldInputs:
    """The advisor's inputs for one stated world, against one registry.

    Args:
        stated: The world.
        rename: Whether to rename every display name first.

    Returns:
        The inputs.
    """
    model, registry, request = stated.parts()
    return inputs_of(
        model,
        renamed(registry) if rename else registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        plan_request=request,
    )


def _stated_card(stated: _Stated, directory: Path, *, rename: bool) -> tuple[Card, Advice]:
    """The one card a stated world yields through advise_world, and the advice it came in.

    Args:
        stated: The world.
        directory: Where this run's two stores live.
        rename: Whether to rename every display name first.

    Returns:
        The card and the whole advice.
    """
    model, registry, request = stated.parts()
    advice = advise_world(
        model,
        renamed(registry) if rename else registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=worlds.NOW,
        plan_request=request,
    )
    (card,) = [
        advised.card for advised in advice.cards if advised.card.rule_id == stated.rule.rule_id
    ]
    return card, advice


def _fallback_steps(trace: Trace) -> list[tuple[str, str]]:
    """The steps a trace records for a name it could not use, as subject and reason."""
    return [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.VERDICT_INDETERMINATE
        and step.subject == plan_worlds.NAME_ALTERNATIVE
    ]


@pytest.mark.parametrize("world_name", sorted(STATED_WORLDS))
def test_a_rename_on_a_stated_world_moves_its_name_input_alone(world_name: str) -> None:
    stated = STATED_WORLDS[world_name]
    before = _stated_inputs(stated, rename=False)
    after = _stated_inputs(stated, rename=True)

    differing = _differing(before, after, display=False)
    assert differing == 0
    moved = _differing(before, after, display=True)
    assert moved == 1
    # The one that moved is this rule's own, and the rename is what it holds now.
    target = plan_worlds.SOLVE_RELIC_ITEM
    assert before.values[stated.names_input].value == {target: plan_worlds.RELIC_NAME}
    assert after.values[stated.names_input].value == {
        target: RENAME_PREFIX + plan_worlds.RELIC_NAME
    }


@pytest.mark.parametrize("world_name", sorted(STATED_WORLDS))
def test_a_rename_on_a_stated_world_moves_the_wording_and_never_the_id(
    world_name: str, tmp_path: Path
) -> None:
    stated = STATED_WORLDS[world_name]
    before, before_advice = _stated_card(stated, tmp_path / "before", rename=False)
    after, after_advice = _stated_card(stated, tmp_path / "after", rename=True)

    assert plan_worlds.RELIC_NAME in before.tier1
    named = RENAME_PREFIX + plan_worlds.RELIC_NAME
    assert named in after.tier1
    assert (named in after.tier2) is stated.tier2_names_the_target
    assert (before.tier2 != after.tier2) is stated.tier2_names_the_target
    assert after.id == before.id
    assert after.subject_key == before.subject_key
    assert _card_ids(after_advice) == _card_ids(before_advice)


@pytest.mark.parametrize("name", UNPRINTABLE_NAMES.values(), ids=UNPRINTABLE_NAMES.keys())
@pytest.mark.parametrize("world_name", sorted(STATED_WORLDS))
def test_a_non_printable_name_falls_back_and_the_card_survives(world_name: str, name: str) -> None:
    """The engine drops a card whose wording it refuses, so the label must not offer that."""
    stated = STATED_WORLDS[world_name]
    model, registry, request = stated.parts()
    target = plan_worlds.SOLVE_RELIC_ITEM

    def trace_for(display_name: str) -> Trace:
        changed = plan_worlds._with_item_name(registry, target, display_name)  # noqa: SLF001
        return run_rule(
            stated.rule,
            inputs_of(
                model,
                changed,
                pinned_changelist=game_pin(),
                pinned_docs_sha256=docs_pin(),
                plan_request=request,
            ),
        )

    # The control: a printable name reads, with no fallback step, on the same world.
    control = card_for(trace_for(plan_worlds.RENAMED_RELIC))
    assert control is not None
    assert plan_worlds.RENAMED_RELIC in control.tier1
    assert _fallback_steps(control.trace) == []

    trace = trace_for(name)

    card = card_for(trace)
    assert card is not None
    assert target in card.tier1
    assert card.id == control.id
    errors = [step for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == []
    assert _fallback_steps(trace) == [(plan_worlds.NAME_ALTERNATIVE, plan_worlds.NAME_REASON)]
    rejected = any(step.kind is StepKind.ALTERNATIVE_REJECTED for step in trace.steps)
    assert not rejected
    # The input keeps the name verbatim, and tier 3 renders it escaped, so every tier stays ASCII.
    (read,) = [step.value for step in trace.steps if step.subject == stated.names_input]
    assert read == {target: name}
    printable = card.tier1.isascii() and card.tier2.isascii() and card.tier3.isascii()
    assert printable
