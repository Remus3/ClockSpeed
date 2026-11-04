"""CS-1371: a marked route when no plan is ranked, and what a refused trace says.

Graded here, against CS-1371's acceptance in ``docs/item_notes/phase5.md``, arms 2, 3 and 5
as far as the advisor owns them. The wire, the panel and the three routes are the surface's,
and ``tests/surface/test_advice_golden.py`` holds the no-target body.

EVERY WORLD IS A HAND-BUILT SYNTHETIC REGISTRY, AND EVERY FIGURE IS WORKED BY HAND. Every cycle
is six seconds, ten a minute, and every amount is one, so 10 of an item a minute is one machine
at each stage it passes through. Nothing here reads a save, a docs file or an install. The
request is built through :func:`clockspeed.advisor.plans.plan_request_from`, the published door,
so raw items only ever come from the fixture's resource group.

A FIXTURE SHOWS NO TIER. The clause grades "several tiers out" by a count of locked stages,
because a synthetic world has no progression to read.

THE SHAPE OF A NEGATIVE. Every arm that says something did not fire or did not run carries a
control where it does, on the same fixture, so an empty fixture or a blind oracle cannot pass it.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.advisor import plans as plans_module
from clockspeed.advisor.advise import (
    Advice,
    advise_and_record,
    advise_world,
    inputs_of,
    settled_rules,
)
from clockspeed.advisor.cards import Card, card_for, card_id
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.plans import (
    PlanParameters,
    PlanRequest,
    plan_offer,
    plan_parameters,
    plan_request_from,
)
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.advisor.rules.plan import (
    IN_PLAN,
    IN_REDESIGN_HELD,
    IN_REDESIGN_LOCKED,
    IN_REDESIGN_PLAN,
    IN_REDESIGN_REQUIRES,
    IN_REDESIGN_STATUS,
    IN_REDESIGN_UNMADE,
    IN_STATUS,
    IN_UNCHECKED,
    PLAN_INPUTS,
    REDESIGN_INPUTS,
    REDESIGN_RULE,
    PlanOutcome,
    plan_outcome_of,
)
from clockspeed.advisor.trace import InputValue, StepKind, Trace, WorldInputs, run_rule, run_rules
from clockspeed.data.registry import Registry, build_registry
from clockspeed.save.world import EMPTY_UNLOCK_STATE, UnlockState, WorldModel
from clockspeed.solve.bound import derived_route
from clockspeed.solve.exact import InexactValueError, UndefinedRateError, audit_exact
from clockspeed.solve.optimize import (
    MAX_EXHAUSTIVE_CANDIDATES,
    OptimizeError,
    OptimizeRequest,
    PowerNotComparableError,
    weighted_objective,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    ByproductPolicyRequired,
    InfeasibleChain,
    PlanStep,
    ProductionPlan,
    RatioError,
    RatioRequest,
    UnderdeterminedChain,
    UnsolvableChain,
)
from tests.advisor.build_fixtures import (
    docs_pin,
    game_pin,
    off_pin_build_inputs,
    pinned_build_inputs,
    pinned_source,
    synthetic_world,
)
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_CLASSES,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_FORM,
    KEY_FULL_NAME,
    KEY_INGREDIENTS,
    KEY_NATIVE_CLASS,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)
from tests.solve.synthetic import (
    DOCS_TEXT,
    ITEM_GROUP,
    RECIPE_GROUP,
    RESOURCE_GROUP,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_ORE_ITEM,
    SOLVE_ORPHAN_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RELIC_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_SMELTER_BUILDING,
    building_path,
    document_from_groups,
)

#: The rule this file grades, spelled rather than imported so a rename reddens here.
REDESIGN_ID: Final = "plan.redesign"
ADOPT_ID: Final = "plan.adopt"

#: The status vocabularies, spelled for the same reason.
NOT_REACHED: Final = "not-reached"
ROUTED: Final = "routed"
NO_ROUTE: Final = "no-route"
ROUTE_REFUSED: Final = "route-refused"
RANKED: Final = "ranked"
NO_TARGET: Final = "no-target"
MALFORMED: Final = "request-malformed"
NO_PLAN: Final = "no-plan"
SOLVE_REFUSED: Final = "solve-refused"
NOT_COMPARABLE: Final = "power-not-comparable"

#: The direction and policy spellings a request states.
RAW: Final = "raw"
POWER: Final = "power"
BALANCED: Final = "balanced"
SINKABLE: Final = "sinkable"

#: The words of the reason a no-plan reads, scoped to the kept set.
NO_PLAN_REASON: Final = (
    "the search found no plan over the unlocked automated recipes it kept,"
    " under the stated byproduct policy"
)
MALFORMED_REASON: Final = "the stated request cannot be asked as a question"

#: The instant every resolution here reads. Injected, never a clock.
NOW: Final = 1000

#: The tier 2 clauses, spelled here so a rewording reddens.
MUST_UNLOCK: Final = "; the locked recipes must unlock first on this route"
NO_UNLOCK: Final = "; this route needs no unlock and the capped search did not find it"
NOT_CHOSEN: Final = (
    "; the stated direction did not choose this route and it was never compared with what is built"
)
ONE_UNCHECKED: Final = "; 1 automated recipe(s) carry no asset path and were never planned"

#: The stage count of the world longer than the cap, each stage required.
CHAIN_STAGES: Final = MAX_EXHAUSTIVE_CANDIDATES + 1

#: An unlock path the registry holds no recipe for: a stand-in for a save's own path.
SAVE_ONLY_PATH: Final = "/Game/Cs1371SaveOnly/Never_Echoed.Never_Echoed_C"

#: A planted string a refusal holds, which may never reach anything a reader sees.
MARK: Final = "cs1371plantedrefusaltext"

#: What each child of the determinism arm prints.
CHILD_SOURCE: Final = """
from tests.advisor.test_plan_redesign import rendered_route_derivation

print(rendered_route_derivation())
"""

#: The two hash seeds the determinism arm compares.
HASH_SEEDS: Final = ("0", "1")

#: Child process bound. Generous: each child builds a registry and runs a search.
CHILD_TIMEOUT_SECONDS: Final = 300

#: The repository root, each child's working directory.
REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: Every door out of ``plans.py`` that runs a solve or a route, stood in for by the spies.
SOLVE_DOORS: Final = (
    "optimize_within_bound",
    "optimize_plan",
    "rank_plans",
    "derived_route",
    "solve_for_targets",
)

# ---------------------------------------------------------------------------
# Fixtures, each worked by hand
# ---------------------------------------------------------------------------


def _path(name: str) -> str:
    """One recipe's invented asset path, which does not hold its ClassName."""
    stem = name.removeprefix("R_")
    return f"/Game/FactoryGame/Synthetic/Redesign/Asset_{stem}.Asset_{stem}_C"


def _item(name: str) -> str:
    """An invented item's ClassName."""
    return f"Desc_Redesign{name}_C"


def _recipe(
    name: str,
    eats: Iterable[str],
    makes: Iterable[str],
    *,
    pathless: bool = False,
    buildings: tuple[str, ...] = (SOLVE_ASSEMBLER_BUILDING,),
    duration: str = "6.000000",
) -> dict[str, str]:
    """One recipe entry as docs text, six seconds a cycle unless told, every amount one."""
    entry = {
        KEY_CLASS_NAME: name,
        KEY_DISPLAY_NAME: name.removeprefix("R_"),
        KEY_DURATION: duration,
        KEY_INGREDIENTS: amount_blob([(item, 1) for item in eats]),
        KEY_PRODUCT: amount_blob([(item, 1) for item in makes]),
        KEY_PRODUCED_IN: class_path_blob([building_path(name) for name in buildings]),
    }
    if not pathless:
        entry[KEY_FULL_NAME] = f"BlueprintGeneratedClass {_path(name)}"
    return entry


def _descriptor(item: str) -> dict[str, str]:
    """One invented solid item's descriptor."""
    return {KEY_CLASS_NAME: item, KEY_DISPLAY_NAME: item, KEY_FORM: "RF_SOLID"}


def _registry(
    entries: list[dict[str, str]],
    *,
    items: Iterable[str] = (),
    resources: tuple[str, ...] | None = None,
) -> Registry:
    """A verified registry holding exactly these recipes.

    Args:
        entries: The recipe entries, replacing the corpus's own.
        items: Invented items to give descriptors.
        resources: The items the resource group declares. None keeps the corpus's Ore. Empty
            leaves the group empty.

    Returns:
        The registry, stamped as built from the pinned docs bytes.
    """
    groups = json.loads(DOCS_TEXT)
    for group in groups:
        native_class = group[KEY_NATIVE_CLASS]
        if native_class.endswith(f".{ITEM_GROUP}'"):
            group[KEY_CLASSES].extend(_descriptor(item) for item in items)
        elif native_class.endswith(f".{RECIPE_GROUP}'"):
            group[KEY_CLASSES] = entries
        elif native_class.endswith(f".{RESOURCE_GROUP}'") and resources is not None:
            group[KEY_CLASSES] = [_descriptor(item) for item in resources]
    return pinned_source(build_registry(document_from_groups(groups)))


#: Each stage of the world three locked stages out, ahead of the world's one held recipe.
HELD_STAGE: Final = "R_A1"
LOCKED_STAGES: Final = ("R_A2", "R_A3", "R_A4")


def _three_locked_registry() -> Registry:
    """A world whose every route to Relic runs at least three locked stages.

    By hand, Ore raw and R_A1 the one recipe held:

    - R_A1 Ore to Rare, R_A2 Rare to S2, R_A3 S2 to S3, R_A4 S3 to Relic: 3 locked on 4 recipes.
    - R_B1 to R_B4, Ore to T1 to T2 to T3 to Relic: 4 locked on 4 recipes.

    Counting locked first picks the R_A route. At 10 Relic a minute that is one machine a stage.
    """
    return _registry(
        [
            _recipe("R_B4", [_item("T3")], [SOLVE_RELIC_ITEM]),
            _recipe("R_B3", [_item("T2")], [_item("T3")]),
            _recipe("R_B2", [_item("T1")], [_item("T2")]),
            _recipe("R_B1", [SOLVE_ORE_ITEM], [_item("T1")]),
            _recipe(HELD_STAGE, [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),
            _recipe("R_A2", [SOLVE_RARE_ITEM], [_item("S2")]),
            _recipe("R_A3", [_item("S2")], [_item("S3")]),
            _recipe("R_A4", [_item("S3")], [SOLVE_RELIC_ITEM]),
        ],
        items=[_item(name) for name in ("S2", "S3", "T1", "T2", "T3")],
    )


def _ascent_registry(*, direct_pathless: bool = False) -> Registry:
    """R_Two, Rare to Relic, R_One, Ore to Rare, and R_Direct, Ore to Relic."""
    return _registry(
        [
            _recipe("R_Two", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM], pathless=direct_pathless),
            _recipe("R_One", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),
        ]
    )


def _stage_name(stage: int) -> str:
    """One stage of the world longer than the cap, zero-padded."""
    return f"R_Stage{stage:02d}"


def _stage_item(stage: int) -> str:
    """The item one stage makes."""
    return _item(f"Stage{stage:02d}")


def _chain_entries() -> tuple[list[dict[str, str]], list[str]]:
    """A chain one recipe past the cap, one producer per item, every member required."""
    made = [_stage_item(stage) for stage in range(1, CHAIN_STAGES)]
    eaten = [SOLVE_ORE_ITEM, *made]
    outputs = [*made, SOLVE_RELIC_ITEM]
    entries = [
        _recipe(_stage_name(stage), [eaten[stage - 1]], [outputs[stage - 1]])
        for stage in range(1, CHAIN_STAGES + 1)
    ]
    return entries, made


def _chain_registry(*extra: dict[str, str]) -> Registry:
    """The chain, and any extra recipes declared after it."""
    entries, made = _chain_entries()
    return _registry([*entries, *extra], items=made)


def _chain_names() -> tuple[str, ...]:
    """Every stage of the chain, stage 1 first, which is registry order."""
    return tuple(_stage_name(stage) for stage in range(1, CHAIN_STAGES + 1))


def _byproduct_registry() -> Registry:
    """R_By makes Relic and Rare from Ore. Nothing consumes the Rare.

    By hand: balanced leaves a Rare row nothing can cancel, so pillar 1 refuses. Sinkable sinks
    the Rare: 10 Relic a minute is one machine.
    """
    return _registry([_recipe("R_By", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM])])


def _orphan_registry(*, orphan_raw: bool = False) -> Registry:
    """R_Orphan eats Orphan, which nothing makes. The group holds it only when told to."""
    resources = (SOLVE_ORE_ITEM, SOLVE_ORPHAN_ITEM) if orphan_raw else None
    return _registry(
        [_recipe("R_Orphan", [SOLVE_ORPHAN_ITEM], [SOLVE_RELIC_ITEM])], resources=resources
    )


def _free_loop_registry() -> Registry:
    """A catalyst the route must reach and the solve gives no machine.

    R_Main eats 1 Feed and makes 1 Feed and 1 Relic, so its net Feed is zero. R_Feed makes Feed
    from Ore. Relic's only recipe needs Feed on the tree, so the route is both. By hand: the Feed
    row reads 10 y = 0, so R_Feed runs no machine, and the Relic row reads 10 x = 10, one machine.
    """
    feed = _item("Feed")
    return _registry(
        [
            _recipe("R_Main", [feed], [feed, SOLVE_RELIC_ITEM]),
            _recipe("R_Feed", [SOLVE_ORE_ITEM], [feed]),
        ],
        items=[feed],
    )


def _parameters(
    *, rate: str = "10", direction: str = RAW, policy: str = BALANCED
) -> PlanParameters:
    """The stated parameters, through their published door."""
    parameters = plan_parameters(rate=rate, direction=direction, byproduct_policy=policy)
    assert parameters is not None
    return parameters


def _request(
    registry: Registry,
    *,
    target: str = SOLVE_RELIC_ITEM,
    rate: str = "10",
    direction: str = RAW,
    policy: str = BALANCED,
) -> PlanRequest:
    """A stated request, through the published door, so raw items are the group's alone."""
    request = plan_request_from(
        registry, target, _parameters(rate=rate, direction=direction, policy=policy)
    )
    assert request is not None
    return request


def _unlocks(held: Iterable[str]) -> UnlockState:
    """An unlock state holding these recipes by asset path."""
    return dataclasses.replace(EMPTY_UNLOCK_STATE, recipes=frozenset(_path(name) for name in held))


def _model(held: Iterable[str]) -> WorldModel:
    """A synthetic world of the pinned build, holding no machine, with these recipes."""
    return dataclasses.replace(synthetic_world(game_pin()), unlocks=_unlocks(held))


def _inputs(model: WorldModel, registry: Registry, request: PlanRequest | None) -> WorldInputs:
    """The advisor's own inputs for one world, on the pin."""
    return inputs_of(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        plan_request=request,
    )


def _advise(
    directory: Path, model: WorldModel, registry: Registry, request: PlanRequest | None
) -> Advice:
    """The one call a surface makes, over fresh stores."""
    return advise_world(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
        plan_request=request,
    )


def _route_trace(held: Iterable[str], registry: Registry, request: PlanRequest) -> Trace:
    """The plan.redesign trace of one world."""
    return run_rule(REDESIGN_RULE, _inputs(_model(held), registry, request))


def _route_card(held: Iterable[str], registry: Registry, request: PlanRequest) -> Card:
    """The plan.redesign card of one world, which must fire."""
    card = card_for(_route_trace(held, registry, request))
    assert card is not None
    return card


def _cards(advice: Advice, rule_id: str) -> list[Card]:
    """Every card one rule yielded in a run."""
    return [advised.card for advised in advice.cards if advised.card.rule_id == rule_id]


def _read(trace: Trace, name: str) -> object:
    """What a trace read for one input, which it must have read exactly once."""
    found = [
        step.value
        for step in trace.steps
        if step.kind is StepKind.INPUT_READ and step.subject == name
    ]
    count = len(found)
    assert count == 1, name
    return found[0]


def _card_read(card: Card, name: str) -> object:
    """What a card's own trace read for one input."""
    return _read(card.trace, name)


def _requires(card: Card) -> tuple[str, ...]:
    """The unlock keys a card requires, so an assertion never renders the withheld trace."""
    recommendation = card.trace.recommendation
    if recommendation is None:
        raise TypeError("a card with no recommendation")
    return recommendation.requires


def _offered(world: WorldInputs, name: str) -> object:
    """What a world offers for one input, so an assertion never renders the withheld mapping."""
    return world.values[name].value


def _source_of(world: WorldInputs, name: str) -> str:
    """Where a world's input came from, for the same reason."""
    return world.values[name].source


def _with_value(world: WorldInputs, name: str, value: object) -> WorldInputs:
    """The same world with one input's value planted, under its own source."""
    values = dict(world.values)
    values[name] = InputValue(value, values[name].source)
    return WorldInputs(values=values, unlocks=world.unlocks)


def _state_kind(ledger: Ledger, model: WorldModel, card_id: str) -> str:
    """One card's recorded state, so an assertion never renders the withheld token."""
    return ledger.state(model.token, card_id, now=NOW).kind


def _completed_count(advice: Advice) -> int:
    """How many cards a run recorded completed, so no assertion renders the ids."""
    return len(advice.completed)


def _outcome_of(advice: Advice) -> PlanOutcome:
    """What a run's outcome reads, which it must carry."""
    outcome = advice.plan_outcome
    if outcome is None:
        raise TypeError("a run with no plan outcome")
    return outcome


def _plan_of(value: object) -> ProductionPlan:
    """A value read as the plan it must be."""
    assert type(value) is ProductionPlan
    return value


def _machines(card: Card) -> list[tuple[str, Fraction]]:
    """Every stage of the plan a card read, with its machine count."""
    plan = _plan_of(_card_read(card, IN_REDESIGN_PLAN))
    return [(step.recipe_key, step.machines) for step in plan.steps]


def _indeterminate_count(trace: Trace) -> int:
    """How many indeterminate steps a trace recorded."""
    return sum(1 for step in trace.steps if step.kind is StepKind.VERDICT_INDETERMINATE)


def _errors(trace: Trace) -> list[str]:
    """The rule-error subjects a trace recorded."""
    return [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]


def _rendered(trace: Trace) -> str:
    """Every field of every step a reader could see."""
    return "\n".join(
        f"{step.kind.value} {step.subject} {step.source} {step.reason} {step.value!r}"
        for step in trace.steps
    )


class _DoorReachedError(Exception):
    """Raised by a stand-in at a solve door, so reaching it cannot be mistaken."""


def _refuse_every_door(monkeypatch: pytest.MonkeyPatch, doors: Iterable[str] = SOLVE_DOORS) -> None:
    """Make any step through these doors raise an error nothing handles."""

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise _DoorReachedError

    for door in doors:
        monkeypatch.setattr(plans_module, door, refuse)


def _count_calls(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[tuple[Any, ...]]]:
    """Record every call through each door out of ``plans.py``, and pass it through."""
    calls: dict[str, list[tuple[Any, ...]]] = {door: [] for door in SOLVE_DOORS}

    def spy(door: str, real: Callable[..., Any]) -> Callable[..., Any]:
        def recording(*args: Any, **kwargs: Any) -> Any:
            calls[door].append(args)
            return real(*args, **kwargs)

        return recording

    for door in SOLVE_DOORS:
        monkeypatch.setattr(plans_module, door, spy(door, getattr(plans_module, door)))
    return calls


def _rejected_world() -> WorldInputs:
    """A hand-built routed plan with no machine on any step, which no world reaches."""
    plan = ProductionPlan(
        steps=(PlanStep(recipe_key="R_A1", machines=Fraction(0)),),
        targets=MappingProxyType({SOLVE_RELIC_ITEM: Fraction(0)}),
        raw_inputs=MappingProxyType({}),
        byproducts=MappingProxyType({}),
        excluded=(),
        byproduct_policy=BYPRODUCT_BALANCED,
    )
    return WorldInputs(
        values={
            **pinned_build_inputs(game_pin()),
            **plan_rules.status_inputs(NO_PLAN),
            **plan_rules.redesign_inputs(plan, held=(), locked=(), requires=()),
            IN_UNCHECKED: InputValue((), "synthetic.unchecked"),
        },
        unlocks=frozenset(),
    )


# ---------------------------------------------------------------------------
# Three locked stages: the card, rendered from the trace
# ---------------------------------------------------------------------------


def test_a_target_three_locked_stages_out_reads_a_route_card(tmp_path: Path) -> None:
    registry = _three_locked_registry()
    advice = _advise(tmp_path, _model([HELD_STAGE]), registry, _request(registry))

    assert _cards(advice, ADOPT_ID) == []
    (card,) = _cards(advice, REDESIGN_ID)
    shown = [advised.card.id for advised in advice.shown]
    assert card.id in shown
    assert card.tier1 == f"Plan toward {SOLVE_RELIC_ITEM}"
    assert card.tier2 == f"This route runs 3 locked and 1 held recipe(s){MUST_UNLOCK}{NOT_CHOSEN}"
    assert _card_read(card, IN_STATUS) == NO_PLAN


def test_the_route_counts_locked_recipes_first_and_all_recipes_second() -> None:
    """Both routes are four recipes on a tree, so the tie would go to R_B on no held set."""
    registry = _three_locked_registry()
    card = _route_card([HELD_STAGE], registry, _request(registry))
    assert _card_read(card, IN_REDESIGN_LOCKED) == LOCKED_STAGES
    assert _card_read(card, IN_REDESIGN_HELD) == (HELD_STAGE,)

    # The control: the same pool with no held set counts recipes alone.
    search = OptimizeRequest(
        targets=MappingProxyType({SOLVE_RELIC_ITEM: Fraction(10)}),
        candidates=tuple(registry.recipes),
        unlocked=tuple(registry.recipes),
        raw_items=registry.resource_items,
        byproduct_policy=BYPRODUCT_BALANCED,
        objective=weighted_objective(raw=Fraction(1)),
    )
    assert derived_route(registry, search).members == ("R_B4", "R_B3", "R_B2", "R_B1")


def test_tier3_carries_every_stage_and_reads_the_locked_recipes_by_class_name() -> None:
    registry = _three_locked_registry()
    card = _route_card([HELD_STAGE], registry, _request(registry))

    assert _machines(card) == [
        (HELD_STAGE, Fraction(1)),
        ("R_A2", Fraction(1)),
        ("R_A3", Fraction(1)),
        ("R_A4", Fraction(1)),
    ]
    for stage in (HELD_STAGE, *LOCKED_STAGES):
        step = f'PlanStep(recipe_key="{stage}", machines=1.00)'
        carried = step in card.tier3
        assert carried, stage
    locked_line = (
        'Read plan.redesign.locked = ("R_A2", "R_A3", "R_A4") from advisor.plans.redesign.locked'
    )
    named = locked_line in card.tier3
    assert named
    held_line = 'Read plan.redesign.held = ("R_A1") from advisor.plans.redesign.held'
    read_held = held_line in card.tier3
    assert read_held


def test_tier1_tier2_and_requires_name_no_locked_recipe() -> None:
    registry = _three_locked_registry()
    card = _route_card([HELD_STAGE], registry, _request(registry))
    requires = _requires(card)

    for stage in LOCKED_STAGES:
        named = [
            where
            for where, text in (
                ("tier1", card.tier1),
                ("tier2", card.tier2),
                ("requires", " ".join(requires)),
            )
            if stage in text or _path(stage) in text
        ]
        assert named == [], stage
    # The control: tier 3 does name each, so the words above were not simply absent everywhere.
    in_tier3 = [stage for stage in LOCKED_STAGES if stage in card.tier3]
    assert in_tier3 == list(LOCKED_STAGES)


def test_requires_holds_only_held_recipes_by_the_whole_path_join() -> None:
    registry = _three_locked_registry()
    model = _model([HELD_STAGE])
    world = _inputs(model, registry, _request(registry))
    card = card_for(run_rule(REDESIGN_RULE, world))
    assert card is not None

    requires = _requires(card)
    assert requires == (f"recipe:{_path(HELD_STAGE)}",)
    # The world's own held keys cover it, as the engine's check needs.
    uncovered = len(set(requires) - world.unlocks)
    assert uncovered == 0
    assert _source_of(world, IN_REDESIGN_REQUIRES) == "advisor.plans.redesign.recipe_unlock_join"


def test_the_route_card_carries_no_badge() -> None:
    registry = _three_locked_registry()
    card = _route_card([HELD_STAGE], registry, _request(registry))
    words = [word for word in ("StrategyBadge", "plan.badge", "within-") if word in card.tier3]
    assert words == []
    # The control: the same reader sees a badge where a card carries one.
    ascent = _ascent_registry()
    ranked = run_rule(
        plan_rules.ADOPT_RULE,
        _inputs(_model(("R_Two", "R_Direct", "R_One")), ascent, _request(ascent)),
    )
    adopt = card_for(ranked)
    assert adopt is not None
    has_badge = "StrategyBadge" in adopt.tier3
    assert has_badge


@pytest.mark.parametrize(
    ("rate", "direction", "policy", "held"),
    [
        ("20", RAW, BALANCED, (HELD_STAGE,)),
        ("10", POWER, BALANCED, (HELD_STAGE,)),
        ("10", RAW, SINKABLE, (HELD_STAGE,)),
        ("10", RAW, BALANCED, ()),
    ],
    ids=["rate", "direction", "policy", "count"],
)
def test_the_card_id_moves_with_no_count_rate_policy_or_direction(
    rate: str, direction: str, policy: str, held: tuple[str, ...]
) -> None:
    registry = _three_locked_registry()
    first = _route_card([HELD_STAGE], registry, _request(registry))
    second = _route_card(
        held, registry, _request(registry, rate=rate, direction=direction, policy=policy)
    )
    assert second.id == first.id
    assert first.subject_key == f"plan:{SOLVE_RELIC_ITEM}"
    assert first.id == card_id(REDESIGN_ID, f"plan:{SOLVE_RELIC_ITEM}", None)
    # The control: another rule over the same subject is another card.
    assert first.id != card_id(ADOPT_ID, f"plan:{SOLVE_RELIC_ITEM}", None)


def test_the_card_id_moves_with_the_target() -> None:
    """The control for the arm above: an id that never moved would pass it too."""
    registry = _registry(
        [
            _recipe("R_Relic", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_Rod", [SOLVE_ORE_ITEM], [SOLVE_ROD_ITEM]),
        ]
    )
    relic = _route_card((), registry, _request(registry))
    rod = _route_card((), registry, _request(registry, target=SOLVE_ROD_ITEM))
    assert rod.id != relic.id


# ---------------------------------------------------------------------------
# It settles nothing, on every path a world reaches
# ---------------------------------------------------------------------------


def _worlds_per_status() -> dict[str, WorldInputs]:
    """One real world reaching each plan.redesign status, by status."""
    ascent = _ascent_registry()
    three = _three_locked_registry()
    orphan = _orphan_registry()
    byproduct = _byproduct_registry()
    return {
        NOT_REACHED: _inputs(_model(("R_Two", "R_Direct", "R_One")), ascent, _request(ascent)),
        ROUTED: _inputs(_model([HELD_STAGE]), three, _request(three)),
        NO_ROUTE: _inputs(_model(()), orphan, _request(orphan)),
        ROUTE_REFUSED: _inputs(_model(()), byproduct, _request(byproduct)),
    }


@pytest.mark.parametrize("status", [NOT_REACHED, ROUTED, NO_ROUTE, ROUTE_REFUSED])
def test_every_path_a_world_reaches_records_one_indeterminate_step(status: str) -> None:
    world = _worlds_per_status()[status]
    assert _offered(world, IN_REDESIGN_STATUS) == status

    trace = run_rule(REDESIGN_RULE, world)

    assert _indeterminate_count(trace) == 1
    settled = REDESIGN_ID in settled_rules((trace,))
    assert not settled
    assert _errors(trace) == []
    fired = trace.recommendation is not None
    assert fired == (status == ROUTED)


def test_no_target_records_one_indeterminate_step_and_no_missing_input() -> None:
    """Ruling G6: no registered rule runs on a world lacking its inputs."""
    registry = _three_locked_registry()
    world = _inputs(_model(()), registry, None)
    traces = run_rules((REDESIGN_RULE,), world)
    (trace,) = traces
    assert _read(trace, IN_REDESIGN_STATUS) == NOT_REACHED
    assert _indeterminate_count(trace) == 1
    missing = [step.subject for step in trace.steps if step.kind is StepKind.INPUT_MISSING]
    assert missing == []
    assert card_for(trace) is None


def test_a_recorded_route_card_is_not_completed_when_the_target_clears_or_moves(
    tmp_path: Path,
) -> None:
    """Through the real ledger: a route is never compared with the world, so it settles nothing."""
    registry = _registry(
        [
            _recipe("R_Relic", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_Rod", [SOLVE_ORE_ITEM], [SOLVE_ROD_ITEM]),
        ]
    )
    model = _model(())
    ledger = Ledger(tmp_path)
    mutes = MuteStore(tmp_path)

    def run(world: WorldInputs) -> Advice:
        return advise_and_record(
            model.token, world, ledger=ledger, mutes=mutes, now=NOW, rules=(REDESIGN_RULE,)
        )

    first = run(_inputs(model, registry, _request(registry)))
    (recorded,) = _cards(first, REDESIGN_ID)
    assert _state_kind(ledger, model, recorded.id) == "new"

    cleared = run(_inputs(model, registry, None))
    assert _completed_count(cleared) == 0
    assert _state_kind(ledger, model, recorded.id) == "new"

    moved = run(_inputs(model, registry, _request(registry, target=SOLVE_ROD_ITEM)))
    (other,) = _cards(moved, REDESIGN_ID)
    assert other.id != recorded.id
    assert _completed_count(moved) == 0
    assert _state_kind(ledger, model, recorded.id) == "new"

    # The control, over the same ledger: a settling trace DOES complete it, so the ledger read
    # above could have shown otherwise.
    completed_it = recorded.id in run(_rejected_world()).completed
    assert completed_it


def test_the_reject_path_is_a_plan_with_no_machine_and_it_settles() -> None:
    """Unreachable from a world because a stated rate is above zero; the census needs one."""
    trace = run_rule(REDESIGN_RULE, _rejected_world())
    assert card_for(trace) is None
    rejected = sum(1 for step in trace.steps if step.kind is StepKind.ALTERNATIVE_REJECTED)
    assert rejected == 1
    assert _indeterminate_count(trace) == 0
    settled = REDESIGN_ID in settled_rules((trace,))
    assert settled


# ---------------------------------------------------------------------------
# The separate arms of clause 2
# ---------------------------------------------------------------------------


def test_a_locked_key_in_a_hand_built_offer_is_precondition_unmet_and_no_card() -> None:
    registry = _three_locked_registry()
    world = _inputs(_model([HELD_STAGE]), registry, _request(registry))
    # The control: the offer as built fires.
    held = run_rule(REDESIGN_RULE, world)
    assert held.recommendation is not None

    locked_key = f"recipe:{_path(LOCKED_STAGES[0])}"
    trace = run_rule(REDESIGN_RULE, _with_value(world, IN_REDESIGN_REQUIRES, (locked_key,)))

    assert trace.recommendation is None
    assert card_for(trace) is None
    assert trace.unmet == (locked_key,)
    last = trace.steps[-1].kind
    assert last is StepKind.PRECONDITION_UNMET


def test_a_ranked_target_reaches_no_route_solve_and_gets_no_route_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _ascent_registry()
    held = ("R_Two", "R_Direct", "R_One")
    _refuse_every_door(monkeypatch, ("derived_route", "solve_for_targets"))

    advice = _advise(tmp_path, _model(held), registry, _request(registry))

    assert _cards(advice, REDESIGN_ID) == []
    assert len(_cards(advice, ADOPT_ID)) == 1
    outcome = _outcome_of(advice)
    assert outcome.status == RANKED
    assert outcome.redesign == NOT_REACHED

    # The control: the same stand-ins do fire on the no-plan the same request reads locked.
    with pytest.raises(_DoorReachedError):
        _advise(tmp_path, _model(()), registry, _request(registry))


def test_a_route_longer_than_the_cap_fires_wholly_held_with_the_no_unlock_wording() -> None:
    """By hand: thirteen required stages. The cap keeps twelve, so the search reads no-plan."""
    registry = _chain_registry()
    names = _chain_names()
    assert len(names) > MAX_EXHAUSTIVE_CANDIDATES
    request = _request(registry)
    world = _inputs(_model(names), registry, request)
    assert _offered(world, IN_STATUS) == NO_PLAN

    card = card_for(run_rule(REDESIGN_RULE, world))

    assert card is not None
    assert card.tier2 == f"This route runs 0 locked and 13 held recipe(s){NO_UNLOCK}{NOT_CHOSEN}"
    unlocks = sorted(_requires(card))
    assert unlocks == sorted(f"recipe:{_path(name)}" for name in names)
    assert _machines(card) == [(name, Fraction(1)) for name in names]


def test_one_locked_stage_on_the_same_chain_reads_the_must_unlock_wording() -> None:
    """The control for the wording: it turns on the locked count and nothing else."""
    registry = _chain_registry()
    names = _chain_names()
    card = _route_card(names[:-1], registry, _request(registry))
    assert card.tier2 == f"This route runs 1 locked and 12 held recipe(s){MUST_UNLOCK}{NOT_CHOSEN}"
    assert _card_read(card, IN_REDESIGN_LOCKED) == (names[-1],)


def test_a_longer_held_route_beats_a_shorter_locked_one() -> None:
    """By hand: thirteen held recipes count (0, 13) and the one locked recipe (1, 1)."""
    registry = _chain_registry(_recipe("R_Short", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]))
    names = _chain_names()
    card = _route_card(names, registry, _request(registry))
    assert [stage for stage, _machine_count in _machines(card)] == list(names)
    assert _card_read(card, IN_REDESIGN_LOCKED) == ()

    # The control: with no held set the short recipe wins, so the count did the choosing.
    search = OptimizeRequest(
        targets=MappingProxyType({SOLVE_RELIC_ITEM: Fraction(10)}),
        candidates=(*names, "R_Short"),
        unlocked=(*names, "R_Short"),
        raw_items=registry.resource_items,
        byproduct_policy=BYPRODUCT_BALANCED,
        objective=weighted_objective(raw=Fraction(1)),
    )
    assert derived_route(registry, search).members == ("R_Short",)


@pytest.mark.parametrize("held", [("R_Feed",), ()], ids=["feeder-held", "feeder-locked"])
def test_a_stage_the_solve_gives_no_machine_is_neither_held_nor_locked(
    held: tuple[str, ...],
) -> None:
    registry = _free_loop_registry()
    card = _route_card(held, registry, _request(registry))

    # Worked by hand in the fixture's docstring, and the zero really is on the route.
    assert _machines(card) == [("R_Main", Fraction(1)), ("R_Feed", Fraction(0))]
    assert _card_read(card, IN_REDESIGN_HELD) == ()
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Main",)
    assert _requires(card) == ()
    assert card.tier2 == f"This route runs 1 locked and 0 held recipe(s){MUST_UNLOCK}{NOT_CHOSEN}"


def test_a_pathless_recipe_stays_off_the_route_and_is_counted_in_tier_2() -> None:
    registry = _ascent_registry(direct_pathless=True)
    card = _route_card((), registry, _request(registry))
    assert [stage for stage, _machine_count in _machines(card)] == ["R_Two", "R_One"]
    assert _card_read(card, IN_UNCHECKED) == ("R_Direct",)
    assert card.tier2 == (
        f"This route runs 2 locked and 0 held recipe(s){MUST_UNLOCK}{NOT_CHOSEN}{ONE_UNCHECKED}"
    )
    # The control: carrying a path, that recipe is the whole route and nothing is unchecked.
    pathed = _ascent_registry()
    control = _route_card((), pathed, _request(pathed))
    assert [stage for stage, _machine_count in _machines(control)] == ["R_Direct"]
    assert ONE_UNCHECKED not in control.tier2


@pytest.mark.parametrize(
    "shortcut",
    [
        _recipe("R_ByHand", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM], buildings=()),
        _recipe("R_Instant", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM], duration="0.000000"),
    ],
    ids=["no-machine-runs-it", "zero-duration"],
)
def test_a_recipe_the_route_may_not_use_stays_off_it(shortcut: dict[str, str]) -> None:
    """One stage, with a path, and it never counts: the pool is the usable automated recipes."""
    registry = _registry(
        [
            shortcut,
            _recipe("R_Two", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_One", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),
        ]
    )
    card = _route_card((), registry, _request(registry))
    assert [stage for stage, _machine_count in _machines(card)] == ["R_Two", "R_One"]
    # The control: the same recipe at a machine and a duration wins, at one stage.
    control = _ascent_registry()
    assert [stage for stage, _count in _machines(_route_card((), control, _request(control)))] == [
        "R_Direct"
    ]


def test_off_the_pin_the_build_caveat_is_last_and_nothing_settles() -> None:
    registry = _ascent_registry(direct_pathless=True)
    pin = game_pin()
    world = _inputs(_model(()), registry, _request(registry))
    off = WorldInputs(
        values={**world.values, **off_pin_build_inputs(pin, 1)}, unlocks=world.unlocks
    )

    trace = run_rule(REDESIGN_RULE, off)
    card = card_for(trace)

    assert card is not None
    caveat = f"; build-mismatch: priced at the pinned build {pin}, not the save build {pin + 1}"
    assert card.tier2.endswith(f"{ONE_UNCHECKED}{caveat}")
    settled = REDESIGN_ID in settled_rules((trace,))
    assert not settled


# ---------------------------------------------------------------------------
# One bound, no rung search, one solve
# ---------------------------------------------------------------------------


def test_the_route_path_makes_one_bound_call_no_rung_call_and_one_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _count_calls(monkeypatch)
    registry = _three_locked_registry()

    offered = plan_offer(_unlocks([HELD_STAGE]), registry, _request(registry))

    assert offered[IN_REDESIGN_STATUS].value == ROUTED
    counts = {door: len(made) for door, made in calls.items()}
    assert counts == {
        "optimize_within_bound": 1,
        "optimize_plan": 0,
        "rank_plans": 0,
        "derived_route": 1,
        "solve_for_targets": 1,
    }
    # What the route was asked over: every automated recipe carrying a path, in registry order.
    (args,) = calls["derived_route"]
    asked = args[1]
    assert asked.candidates == tuple(registry.recipes)
    assert asked.unlocked == tuple(registry.recipes)
    # What the solve was handed: the route, the stated policy, the group, and no float.
    (solve_args,) = calls["solve_for_targets"]
    ratio = solve_args[1]
    assert type(ratio) is RatioRequest
    assert ratio.recipes == ("R_A4", "R_A3", "R_A2", "R_A1")
    assert ratio.byproduct_policy == BALANCED
    assert ratio.raw_items == (SOLVE_ORE_ITEM,)
    audit_exact(ratio, path="ratio")
    rates = [type(rate) for rate in ratio.targets.values()]
    assert rates == [Fraction]


def test_a_ranked_target_makes_no_route_call_and_every_rung_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The control for the arm above: its zero rung calls are not a spy that sees nothing."""
    calls = _count_calls(monkeypatch)
    registry = _ascent_registry()

    plan_offer(_unlocks(("R_Two", "R_Direct", "R_One")), registry, _request(registry))

    counts = {door: len(made) for door, made in calls.items()}
    assert counts == {
        "optimize_within_bound": 1,
        "optimize_plan": 3,
        "rank_plans": 1,
        "derived_route": 0,
        "solve_for_targets": 0,
    }


# ---------------------------------------------------------------------------
# Arm 3: what a refused trace says, through the projection
# ---------------------------------------------------------------------------


def _outcome(unlocked: Iterable[str], registry: Registry, request: PlanRequest) -> PlanOutcome:
    """The projection of one offer."""
    return plan_outcome_of(plan_offer(_unlocks(unlocked), registry, request))


def test_a_ranked_outcome_has_no_reason_and_reads_not_reached() -> None:
    registry = _ascent_registry()
    outcome = _outcome(("R_Two", "R_Direct", "R_One"), registry, _request(registry))
    assert outcome == PlanOutcome(
        status=RANKED, reason=None, redesign=NOT_REACHED, trimmed=(), unmade=None
    )


def test_a_no_plan_outcome_reads_its_reason_scoped_to_the_kept_set_and_the_trim() -> None:
    registry = _chain_registry()
    outcome = _outcome(_chain_names(), registry, _request(registry))
    assert outcome == PlanOutcome(
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=ROUTED,
        trimmed=(_stage_name(1),),
        unmade=None,
    )


def test_a_no_route_outcome_names_the_item_nothing_makes() -> None:
    registry = _orphan_registry()
    outcome = _outcome((), registry, _request(registry))
    assert outcome == PlanOutcome(
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=NO_ROUTE,
        trimmed=(),
        unmade=(SOLVE_ORPHAN_ITEM,),
    )


def test_an_item_nothing_makes_is_never_treated_as_raw_unless_the_group_holds_it() -> None:
    """The control for the no-route arm: only the group's word makes that same item raw."""
    registry = _orphan_registry(orphan_raw=True)
    assert SOLVE_ORPHAN_ITEM in registry.resource_items
    outcome = _outcome((), registry, _request(registry))
    assert outcome.redesign == ROUTED
    assert outcome.unmade is None


def test_a_loop_no_raw_item_enters_reads_no_route_and_names_nothing() -> None:
    """A cycle with no way in: the count finds no route and no item is missing from the world."""
    registry = _registry(
        [
            _recipe("R_Left", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_Right", [SOLVE_RELIC_ITEM], [SOLVE_RARE_ITEM]),
        ]
    )
    outcome = _outcome((), registry, _request(registry))
    assert outcome.status == NO_PLAN
    assert outcome.redesign == NO_ROUTE
    assert outcome.unmade == ()


def test_a_route_refused_outcome_fires_under_the_other_policy() -> None:
    registry = _byproduct_registry()
    refused = _outcome((), registry, _request(registry, policy=BALANCED))
    assert refused == PlanOutcome(
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=ROUTE_REFUSED,
        trimmed=(),
        unmade=None,
    )
    assert card_for(_route_trace((), registry, _request(registry, policy=BALANCED))) is None

    # The same request under the other policy fires.
    card = _route_card((), registry, _request(registry, policy=SINKABLE))
    assert card.tier1 == f"Plan toward {SOLVE_RELIC_ITEM}"
    plan = _plan_of(_card_read(card, IN_REDESIGN_PLAN))
    assert plan.byproducts == {SOLVE_RARE_ITEM: Fraction(10)}


@pytest.mark.parametrize(
    ("refusal", "status"),
    [
        (lambda: PowerNotComparableError("R_Odd", "synthetic"), NOT_COMPARABLE),
        (lambda: OptimizeError("synthetic"), SOLVE_REFUSED),
    ],
    ids=[NOT_COMPARABLE, SOLVE_REFUSED],
)
def test_a_refusal_other_than_no_plan_is_not_reached_and_runs_no_route(
    monkeypatch: pytest.MonkeyPatch, refusal: Callable[[], Exception], status: str
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> object:
        raise refusal()

    monkeypatch.setattr(plans_module, "optimize_within_bound", refuse)
    _refuse_every_door(monkeypatch, ("derived_route", "solve_for_targets"))
    registry = _ascent_registry()

    outcome = _outcome((), registry, _request(registry))

    assert outcome.status == status
    assert outcome.redesign == NOT_REACHED
    assert outcome.reason is not None
    assert outcome.trimmed == ()


#: Each refusal the route's two calls can raise. Each holds :data:`MARK` wherever it holds
#: text, so an echo cannot hide. ``solve_for_targets`` documents the first five and the
#: value error. The rest are what ``plan_offer`` also reads as a refusal.
ROUTE_REFUSALS: Final[Mapping[str, Callable[[], Exception]]] = MappingProxyType(
    {
        "unsolvable": lambda: UnsolvableChain(MARK, MARK),
        "underdetermined": lambda: UnderdeterminedChain((MARK,), MARK),
        "infeasible": lambda: InfeasibleChain(MARK, Fraction(-1), MARK),
        "policy": lambda: ByproductPolicyRequired(MARK, MARK),
        "ratio": lambda: RatioError(MARK),
        "optimize": lambda: OptimizeError(MARK),
        "value-error": lambda: ValueError(MARK),
        "key-error": lambda: KeyError(MARK),
        "inexact-value": lambda: InexactValueError(MARK),
        "undefined-rate": lambda: UndefinedRateError(MARK),
    }
)

#: The route path's two doors.
ROUTE_DOORS: Final = ("derived_route", "solve_for_targets")


@pytest.mark.parametrize("door", ROUTE_DOORS)
@pytest.mark.parametrize("refusal", sorted(ROUTE_REFUSALS))
def test_each_refusal_on_the_route_path_reads_route_refused_and_echoes_nothing(
    monkeypatch: pytest.MonkeyPatch, door: str, refusal: str
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> object:
        raise ROUTE_REFUSALS[refusal]()

    monkeypatch.setattr(plans_module, door, refuse)
    registry = _ascent_registry()
    world = _inputs(_model(()), registry, _request(registry))

    trace = run_rule(REDESIGN_RULE, world)

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, IN_REDESIGN_STATUS) == ROUTE_REFUSED
    assert card_for(trace) is None
    assert _indeterminate_count(trace) == 1
    assert _errors(trace) == []
    echoed = MARK in _rendered(trace)
    assert not echoed


@pytest.mark.parametrize("door", ROUTE_DOORS)
def test_a_type_error_from_the_route_raises_out_of_the_offer(
    monkeypatch: pytest.MonkeyPatch, door: str
) -> None:
    """Only a type outside the catches raises, as on the ranked path, so a bug stays loud."""

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise TypeError(MARK)

    monkeypatch.setattr(plans_module, door, refuse)
    registry = _ascent_registry()
    with pytest.raises(TypeError):
        plan_offer(_unlocks(()), registry, _request(registry))


def test_no_target_projects_the_status_alone_and_runs_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _refuse_every_door(monkeypatch)
    registry = _ascent_registry()
    offered = plan_offer(_unlocks(()), registry, None)
    assert plan_outcome_of(offered).status == NO_TARGET
    assert plan_outcome_of(offered).redesign == NOT_REACHED
    assert plan_outcome_of(offered).trimmed is None
    assert plan_outcome_of(offered).unmade is None


def test_an_empty_group_reads_request_malformed_and_reaches_no_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = _registry([_recipe("R_Relic", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])], resources=())
    assert registry.resource_items == ()
    flagged = [warning.code for warning in registry.warnings if warning.code == "no-resource-group"]
    assert flagged == ["no-resource-group"]
    request = _request(registry)
    assert request.raw_items == ()

    _refuse_every_door(monkeypatch)
    outcome = _outcome((), registry, request)

    assert outcome == PlanOutcome(
        status=MALFORMED, reason=MALFORMED_REASON, redesign=NOT_REACHED, trimmed=None, unmade=None
    )
    # The control: the same request with the group's one item stands the door open.
    with_group = dataclasses.replace(request, raw_items=(SOLVE_ORE_ITEM,))
    with pytest.raises(_DoorReachedError):
        plan_offer(_unlocks(()), registry, with_group)


@pytest.mark.parametrize(
    "name", [IN_STATUS, IN_REDESIGN_STATUS], ids=["plan-status", "redesign-status"]
)
def test_a_status_outside_the_vocabulary_is_refused_with_no_value_named(name: str) -> None:
    planted = "cs1371plantedstatus"
    values = {
        IN_STATUS: InputValue(NO_TARGET, "synthetic.status"),
        IN_REDESIGN_STATUS: InputValue(NOT_REACHED, "synthetic.redesign"),
        IN_REDESIGN_UNMADE: InputValue(None, "synthetic.unmade"),
    }
    # The control: the words as stated project.
    assert plan_outcome_of(values).status == NO_TARGET
    values[name] = InputValue(planted, "synthetic.planted")
    with pytest.raises(ValueError, match="closed vocabulary") as refused:
        plan_outcome_of(values)
    echoed = planted in str(refused.value)
    assert not echoed


def test_advice_carries_the_outcome_only_when_a_target_is_stated(tmp_path: Path) -> None:
    registry = _three_locked_registry()
    model = _model([HELD_STAGE])

    stated = _advise(tmp_path, model, registry, _request(registry))
    silent = _advise(tmp_path, model, registry, None)

    assert _outcome_of(stated) == PlanOutcome(
        status=NO_PLAN, reason=NO_PLAN_REASON, redesign=ROUTED, trimmed=(), unmade=None
    )
    no_outcome = silent.plan_outcome is None
    assert no_outcome
    # The repr stays counts only, whatever the outcome holds.
    rendered = repr(stated)
    assert rendered.startswith("Advice(traces=")
    leaked = NO_PLAN_REASON in rendered or "plan_outcome" in rendered
    assert not leaked


@pytest.mark.parametrize("status", [NOT_REACHED, ROUTED, NO_ROUTE, ROUTE_REFUSED])
def test_every_status_offers_every_redesign_input(status: str) -> None:
    world = _worlds_per_status()[status]
    absent = len(set(REDESIGN_INPUTS) - set(world.values))
    assert absent == 0


def test_the_redesign_inputs_stay_out_of_the_plan_inputs() -> None:
    shared = sorted(set(REDESIGN_INPUTS) & set(PLAN_INPUTS))
    assert shared == []
    assert REDESIGN_INPUTS == (
        "plan.redesign.status",
        "plan.redesign.plan",
        "plan.redesign.held",
        "plan.redesign.locked",
        "plan.redesign.requires",
        "plan.redesign.unmade",
    )


def test_each_redesign_input_names_the_field_it_came_from() -> None:
    world = _worlds_per_status()[ROUTED]
    sources = {name: _source_of(world, name) for name in REDESIGN_INPUTS}
    assert sources == {
        IN_REDESIGN_STATUS: "advisor.plans.redesign.status",
        IN_REDESIGN_PLAN: "solve.ratio.solve_for_targets",
        IN_REDESIGN_HELD: "advisor.plans.redesign.held",
        IN_REDESIGN_LOCKED: "advisor.plans.redesign.locked",
        IN_REDESIGN_REQUIRES: "advisor.plans.redesign.recipe_unlock_join",
        IN_REDESIGN_UNMADE: "solve.bound.derived_route.unmade",
    }


def test_a_ranked_plan_and_a_route_plan_share_no_input() -> None:
    """The route and the ranked plan never share an input: one world never offers both."""
    routed = _worlds_per_status()[ROUTED]
    ranked_on_the_route = IN_PLAN in routed.values
    assert not ranked_on_the_route
    ranked = _worlds_per_status()[NOT_REACHED]
    assert _offered(ranked, IN_REDESIGN_PLAN) is None
    assert type(_offered(ranked, IN_PLAN)) is ProductionPlan


# ---------------------------------------------------------------------------
# The rule refuses what disagrees with itself
# ---------------------------------------------------------------------------


def _forged(change: Mapping[str, object]) -> Trace:
    """The routed world with these values planted, each under its own source."""
    world = _worlds_per_status()[ROUTED]
    for name, value in change.items():
        world = _with_value(world, name, value)
    return run_rule(REDESIGN_RULE, world)


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({IN_REDESIGN_STATUS: "synthetic-status"}, "ValueError"),
        ({IN_REDESIGN_STATUS: Fraction(1)}, "TypeError"),
        ({IN_REDESIGN_PLAN: "not a plan"}, "TypeError"),
        ({IN_REDESIGN_PLAN: None}, "TypeError"),
        ({IN_REDESIGN_HELD: "R_A1"}, "TypeError"),
        ({IN_REDESIGN_LOCKED: None}, "TypeError"),
        ({IN_REDESIGN_REQUIRES: None}, "TypeError"),
        ({IN_REDESIGN_UNMADE: ()}, "TypeError"),
        ({IN_UNCHECKED: None}, "TypeError"),
        # Beside a status that says a plan was ranked, no route can have been reached.
        ({IN_STATUS: RANKED}, "ValueError"),
        # A list that disagrees with the plan's own machines.
        ({IN_REDESIGN_HELD: ()}, "ValueError"),
        ({IN_REDESIGN_LOCKED: ("R_A2", "R_A3")}, "ValueError"),
        ({IN_REDESIGN_HELD: ("R_A1", "R_A2")}, "ValueError"),
        # A status with no plan cannot carry the route it did not solve.
        ({IN_REDESIGN_STATUS: NO_ROUTE}, "TypeError"),
        ({IN_REDESIGN_STATUS: ROUTE_REFUSED}, "TypeError"),
        ({IN_REDESIGN_STATUS: NOT_REACHED}, "ValueError"),
    ],
    ids=[
        "status-unknown",
        "status-not-text",
        "plan-not-a-plan",
        "plan-none",
        "held-not-a-tuple",
        "locked-none",
        "requires-none",
        "unmade-on-routed",
        "unchecked-none",
        "routed-beside-ranked",
        "held-short",
        "locked-short",
        "held-overlaps",
        "no-route-carrying-a-plan",
        "refused-carrying-a-plan",
        "not-reached-beside-no-plan",
    ],
)
def test_a_redesign_offer_that_disagrees_with_itself_is_a_rule_error(
    change: Mapping[str, object], error: str
) -> None:
    # The control: the world as built fires, so each error below is the change's own.
    control = _forged({})
    assert control.recommendation is not None

    trace = _forged(change)

    assert card_for(trace) is None
    assert _errors(trace) == [error]


def test_a_no_route_offer_must_carry_its_items() -> None:
    world = _with_value(_worlds_per_status()[NO_ROUTE], IN_REDESIGN_UNMADE, None)
    assert _errors(run_rule(REDESIGN_RULE, world)) == ["TypeError"]


# ---------------------------------------------------------------------------
# Arm 5, the advisor's half: the stated parameters, refused by None alone
# ---------------------------------------------------------------------------


class _Text(str):
    """A str subclass, which an exact parameter refuses."""

    __slots__ = ()


@pytest.mark.parametrize(
    "rate",
    [
        "0",
        "0.0",
        "00",
        "0/5",
        "-1",
        "-0.5",
        "-1/2",
        "1/0",
        "0/0",
        "1e3",
        "1E3",
        "1.5e3",
        "+1",
        " 1",
        "1 ",
        "1\n",
        "",
        ".",
        ".5",
        "5.",
        "1/",
        "/2",
        "1/2/3",
        "1.5/2",
        "1_000",
        "0x10",
        "nan",
        "inf",
        "Infinity",
        chr(0x0661),
        "1" + chr(0x0660),
        "1" * 65,
        1,
        1.5,
        Fraction(1),
        None,
        b"1",
        True,
        _Text("1"),
    ],
)
def test_a_rate_at_or_below_zero_or_malformed_is_refused_by_none(
    monkeypatch: pytest.MonkeyPatch, rate: Any
) -> None:
    _refuse_every_door(monkeypatch)
    refused = plan_parameters(rate=rate, direction=RAW, byproduct_policy=BALANCED)
    assert refused is None


@pytest.mark.parametrize(
    ("rate", "exact"),
    [
        ("10", Fraction(10)),
        ("007", Fraction(7)),
        ("2.5", Fraction(5, 2)),
        ("0.1", Fraction(1, 10)),
        ("10/3", Fraction(10, 3)),
        ("1" * 64, Fraction("1" * 64)),
    ],
)
def test_a_rate_in_every_spelling_is_exact_and_never_through_a_float(
    rate: str, exact: Fraction
) -> None:
    parameters = plan_parameters(rate=rate, direction=POWER, byproduct_policy=SINKABLE)
    assert parameters == PlanParameters(rate=exact, direction=POWER, byproduct_policy=SINKABLE)
    assert parameters is not None
    kind = type(parameters.rate)
    assert kind is Fraction


@pytest.mark.parametrize(
    "value", ["", "speed", "RAW", " raw", "balanced", None, 1, ["raw"], _Text(RAW)]
)
def test_a_direction_outside_its_vocabulary_is_refused_by_none(value: Any) -> None:
    assert plan_parameters(rate="10", direction=value, byproduct_policy=BALANCED) is None
    # The control: each other parameter is good, so only the direction refused.
    assert plan_parameters(rate="10", direction=RAW, byproduct_policy=BALANCED) is not None


@pytest.mark.parametrize(
    "value", ["", "vent", "BALANCED", " balanced", "raw", None, 1, ["balanced"], _Text(BALANCED)]
)
def test_a_policy_outside_its_vocabulary_is_refused_by_none(value: Any) -> None:
    assert plan_parameters(rate="10", direction=RAW, byproduct_policy=value) is None
    assert plan_parameters(rate="10", direction=RAW, byproduct_policy=BALANCED) is not None


@pytest.mark.parametrize(
    "target",
    [
        SOLVE_ORE_ITEM,
        SOLVE_ORPHAN_ITEM,
        "Desc_NeverDeclared_C",
        "",
        None,
        1,
        _Text(SOLVE_RELIC_ITEM),
    ],
    ids=[
        "group-member",
        "nothing-makes-it",
        "unknown",
        "empty",
        "none",
        "not-text",
        "str-subclass",
    ],
)
def test_a_target_off_the_list_is_refused_by_none_and_reaches_no_solve(
    monkeypatch: pytest.MonkeyPatch, target: Any
) -> None:
    _refuse_every_door(monkeypatch)
    registry = _ascent_registry()
    assert plan_request_from(registry, target, _parameters()) is None
    # The control: the listed target is admitted, through the same stand-ins, by reading only
    # the registry, so a refused target above was the membership test's own.
    assert plan_request_from(registry, SOLVE_RELIC_ITEM, _parameters()) is not None


def test_a_request_takes_its_raw_items_from_the_published_group_alone() -> None:
    registry = _orphan_registry(orphan_raw=True)
    request = _request(registry, rate="10/3", direction=POWER, policy=SINKABLE)
    assert request == PlanRequest(
        targets=MappingProxyType({SOLVE_RELIC_ITEM: Fraction(10, 3)}),
        raw_items=(SOLVE_ORE_ITEM, SOLVE_ORPHAN_ITEM),
        byproduct_policy=SINKABLE,
        direction=POWER,
    )
    assert request.raw_items is registry.resource_items


def test_the_parameters_take_no_registry_so_no_provider_is_read_first() -> None:
    named = tuple(inspect.signature(plan_parameters).parameters)
    assert named == ("rate", "direction", "byproduct_policy")


# ---------------------------------------------------------------------------
# What may never leak, and what no two runs may disagree on
# ---------------------------------------------------------------------------


def test_a_save_path_reaches_no_input_on_the_route_path() -> None:
    registry = _three_locked_registry()
    state = dataclasses.replace(
        EMPTY_UNLOCK_STATE, recipes=frozenset({_path(HELD_STAGE), SAVE_ONLY_PATH})
    )
    model = dataclasses.replace(synthetic_world(game_pin()), unlocks=state)
    world = _inputs(model, registry, _request(registry))

    trace = run_rule(REDESIGN_RULE, world)
    card = card_for(trace)
    assert card is not None
    # The control: the join counted it, so the path did reach the offer.
    assert _offered(world, "plan.unmatched_unlocks") == 1
    leaked = [
        where
        for where, text in (
            ("trace", _rendered(trace)),
            ("tier1", card.tier1),
            ("tier2", card.tier2),
            ("tier3", card.tier3),
            ("outcome", repr(plan_outcome_of(world.values))),
        )
        if SAVE_ONLY_PATH in text
    ]
    assert leaked == []


def rendered_route_derivation() -> str:
    """One route card's tier 3, over a world where any order could come from a set.

    Public because :data:`CHILD_SOURCE` imports it, so the children build this very world.

    Returns:
        The derivation. A trace with no recommendation refuses to build a card, so a child
        that fired nothing exits non-zero and the arm says so.
    """
    registry = _three_locked_registry()
    trace = _route_trace((HELD_STAGE, "R_B1", "R_B2"), registry, _request(registry))
    return Card(trace).tier3


def test_two_processes_under_different_hash_seeds_render_one_route_derivation() -> None:
    """A held set deciding an order is stable within a process, so this takes two."""
    printed: list[str] = []
    for seed in HASH_SEEDS:
        child = subprocess.run(
            [sys.executable, "-s", "-B", "-c", CHILD_SOURCE],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHILD_TIMEOUT_SECONDS,
            env={"PYTHONHASHSEED": seed, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        # Bound to a plain int first: pytest would otherwise render the whole
        # CompletedProcess, whose argv[0] is the absolute interpreter path.
        exit_code = child.returncode
        assert exit_code == 0, f"the child under PYTHONHASHSEED={seed} failed"
        printed.append(child.stdout.strip())

    opened = printed[0].startswith("Derivation of rule plan.redesign")
    assert opened
    agreed = printed[0] == printed[1]
    assert agreed


def test_the_hash_seed_world_holds_several_recipes_a_set_could_order() -> None:
    """The control for the arm above: holding R_B1 and R_B2 moves the route to R_B, by hand."""
    registry = _three_locked_registry()
    card = _route_card((HELD_STAGE, "R_B1", "R_B2"), registry, _request(registry))
    assert _card_read(card, IN_REDESIGN_HELD) == ("R_B2", "R_B1")
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_B4", "R_B3")


def test_a_recipe_with_no_exact_draw_can_still_be_routed() -> None:
    """A recipe naming two buildings has no exact draw, and a route does not read the draw."""
    registry = _registry(
        [
            _recipe(
                "R_Odd",
                [SOLVE_ORE_ITEM],
                [SOLVE_RELIC_ITEM],
                buildings=(SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
            )
        ]
    )
    card = _route_card((), registry, _request(registry, direction=POWER))
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Odd",)
