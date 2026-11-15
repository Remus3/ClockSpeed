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

EVERY WORLD HOLDS EVERY MACHINE UNLESS IT SAYS OTHERWISE, and every machine has its build
recipe, so a world's locks are the ones its arm names. The arms under "A recipe is held only
with a machine to run it" take each of those away. THE MINER STANDS APART, on a parameter of its
own, so a world holding no machine can still be supplied Ore, and the arms under "A raw item is
supplied only with a machine to extract it" take that away.

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
    IN_REDESIGN_BUILT,
    IN_REDESIGN_HELD,
    IN_REDESIGN_LOCKED,
    IN_REDESIGN_PLAN,
    IN_REDESIGN_REQUIRES,
    IN_REDESIGN_STATUS,
    IN_REDESIGN_TARGET_NAMES,
    IN_REDESIGN_UNLOCKS,
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
    BUILDING_DESCRIPTOR_GROUP,
    DOCS_TEXT,
    ITEM_GROUP,
    MACHINE_BUILD_ENTRIES,
    MACHINE_DESCRIPTOR_ENTRIES,
    MINER_BUILD_PATH,
    RECIPE_GROUP,
    RESOURCE_GROUP,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_BUILDINGS,
    SOLVE_MINER_BUILDING,
    SOLVE_ORE_ITEM,
    SOLVE_ORPHAN_ITEM,
    SOLVE_PLATE_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_REFINERY_BUILDING,
    SOLVE_RELIC_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_SMELTER_BUILDING,
    SOLVE_TWIN_ITEM,
    building_path,
    document_from_groups,
    extractor_descriptor,
    extractor_entry,
    extractor_group,
    machine_build_entry,
    machine_build_path,
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
    " from the raw items a held extractor supplies, under the stated byproduct policy"
)
MALFORMED_REASON: Final = "the stated request cannot be asked as a question"

#: The words of the reason each status a listing explains reads, spelled so a rewording reddens.
NO_ROUTE_REASON: Final = (
    "the count found no route to the target from the raw items, over every"
    " automated recipe with an unlock path to check, which does not prove no plan exists"
)
ROUTE_REFUSED_REASON: Final = (
    "pillar 1 refused the derived route, solved once under the stated byproduct policy,"
    " which does not prove no plan exists"
)

#: The instant every resolution here reads. Injected, never a clock.
NOW: Final = 1000

#: The display names ``tests/solve/synthetic.py`` gives its Relic and its Rod, spelled here so
#: a change there reddens here.
RELIC_NAME: Final = "Solve Relic"
ROD_NAME: Final = "Solve Rod"

#: A second display name for the Relic, so two registries can differ in that alone.
RENAMED_RELIC: Final = "Renamed Relic"

#: How tiers 1 and 2 read each name: in double quotes (CS-1379), spelled so a change reddens.
RELIC_LABEL: Final = '"Solve Relic"'
ROD_LABEL: Final = '"Solve Rod"'
RENAMED_LABEL: Final = '"Renamed Relic"'

#: The one step a target with no usable display name records, spelled so a rewording reddens.
NAME_ALTERNATIVE: Final = "name every target by its display name"
NAME_REASON: Final = "a target has no usable display name, so its ClassName names it"

#: The step the firing path records whatever the names say.
COMPARE_STEP: Final = (
    "settle the route's card on what is built",
    "a route is derived for a stated target,"
    " so its card going away says nothing about what is built",
)

#: The opening and the clauses of tier 2, spelled here so a rewording reddens.
ROUTE_RUNS: Final = f"This route to {RELIC_LABEL} runs"
MUST_UNLOCK: Final = (
    "; the locked recipes or the machines that run them must unlock first on this route"
)


def _capped_no_unlock(dropped: int) -> str:
    """The no-unlock clause beside a bound that dropped this many recipes (CS-1382).

    The cap and the count, facts only: it says neither that the cap caused the miss nor that
    it did not.
    """
    return (
        f"; this route needs no unlock and the search, which dropped {dropped} held recipe(s) to"
        " fit its cap, found no route within it from the raw items a held extractor supplies"
    )


#: That clause beside the one recipe each world past the cap here drops.
NO_UNLOCK: Final = _capped_no_unlock(1)
#: The same clause where the bound dropped nothing, so it names no cap (CS-1382 F1).
UNCAPPED_NO_UNLOCK: Final = (
    "; this route needs no unlock and the search, which dropped no recipe to fit its cap,"
    " did not find it from the raw items a held extractor supplies"
)


def _not_chosen(stages: int) -> str:
    """The direction clause of tier 2 with a machines model read and no recipe tagged (CS-1375).

    The comparison ran and read unmeasured, so tier 2 says that and states the counts: no stage
    reads more, no recipe reads replace, and every stage with a machine count reads unmeasured.
    """
    return (
        "; the stated direction did not choose this route"
        "; the comparison read unmeasured, as no machine names a recipe"
        "; against what is built 0 stage(s) read more, 0 recipe(s) read replace"
        f" and {stages} stage(s) read unmeasured"
    )


ONE_UNCHECKED: Final = (
    "; 1 automated recipe(s) carry no unlock path to check and were never planned"
)

#: The unlock key of each machine's build recipe, which a held recipe's requires name.
ASSEMBLER_KEY: Final = f"recipe:{machine_build_path(SOLVE_ASSEMBLER_BUILDING)}"
SMELTER_KEY: Final = f"recipe:{machine_build_path(SOLVE_SMELTER_BUILDING)}"

#: The unlock key of the miner's build recipe, which a plan eating Ore requires.
MINER_KEY: Final = f"recipe:{MINER_BUILD_PATH}"

#: The input naming the route's locked extractors, spelled so a rename reddens.
LOCKED_EXTRACTORS: Final = "plan.redesign.locked_extractors"

#: The input naming the raw items no extractor joins, for the same reason.
RAW_UNKNOWN: Final = "plan.raw_unknown"

#: A second extractor, restricted to Rare, for a world with two raw items apart.
DRILL_BUILDING: Final = "Build_SolveDrill_C"
DRILL_KEY: Final = f"recipe:{machine_build_path(DRILL_BUILDING)}"

#: What tier 2 says of a route needing an extractor, spelled so a rewording reddens.
NEEDS_ONE: Final = " and needs 1 locked extractor(s)"
MUST_EXTRACT: Final = "; the locked extractors must unlock first on this route"
ONE_RAW_UNKNOWN: Final = "; 1 raw item(s) have no known extractor and were never supplied"

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
    builds: Iterable[Mapping[str, str]] = MACHINE_BUILD_ENTRIES,
    extractors: Iterable[Mapping[str, str]] = (extractor_entry(SOLVE_MINER_BUILDING),),
    extractor_builds: Iterable[Mapping[str, str]] = (machine_build_entry(SOLVE_MINER_BUILDING),),
) -> Registry:
    """A verified registry holding exactly these recipes, and each machine's build recipe.

    Args:
        entries: The recipe entries, replacing the corpus's own.
        items: Invented items to give descriptors.
        resources: The items the resource group declares. None keeps the corpus's Ore. Empty
            leaves the group empty.
        builds: The machines' build recipes, declared after ``entries``. Every machine has
            one unless told otherwise, because a recipe no machine of which joins a build
            recipe is flagged and never planned.
        extractors: The extractors' entries. The miner, unless told otherwise, so Ore has a
            machine the docs say extracts it.
        extractor_builds: Their build recipes, declared after ``builds``, kept apart so an
            arm can take either kind of build recipe away without the other.

    Returns:
        The registry, stamped as built from the pinned docs bytes.
    """
    extractor_entries = list(extractors)
    groups = json.loads(DOCS_TEXT)
    for group in groups:
        native_class = group[KEY_NATIVE_CLASS]
        if native_class.endswith(f".{ITEM_GROUP}'"):
            group[KEY_CLASSES].extend(_descriptor(item) for item in items)
        elif native_class.endswith(f".{BUILDING_DESCRIPTOR_GROUP}'"):
            group[KEY_CLASSES].extend(MACHINE_DESCRIPTOR_ENTRIES)
            group[KEY_CLASSES].extend(
                extractor_descriptor(entry[KEY_CLASS_NAME]) for entry in extractor_entries
            )
        elif native_class.endswith(f".{RECIPE_GROUP}'"):
            group[KEY_CLASSES] = [*entries, *builds, *extractor_builds]
        elif native_class.endswith(f".{RESOURCE_GROUP}'") and resources is not None:
            group[KEY_CLASSES] = [_descriptor(item) for item in resources]
    if extractor_entries:
        groups.append(extractor_group(*extractor_entries))
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


def _chain_entries(
    *, buildings: tuple[str, ...] = (SOLVE_ASSEMBLER_BUILDING,)
) -> tuple[list[dict[str, str]], list[str]]:
    """A chain one recipe past the cap, one producer per item, every member required."""
    made = [_stage_item(stage) for stage in range(1, CHAIN_STAGES)]
    eaten = [SOLVE_ORE_ITEM, *made]
    outputs = [*made, SOLVE_RELIC_ITEM]
    entries = [
        _recipe(_stage_name(stage), [eaten[stage - 1]], [outputs[stage - 1]], buildings=buildings)
        for stage in range(1, CHAIN_STAGES + 1)
    ]
    return entries, made


def _chain_registry(
    *extra: dict[str, str], buildings: tuple[str, ...] = (SOLVE_ASSEMBLER_BUILDING,)
) -> Registry:
    """The chain, each stage on these machines, and any extra recipes declared after it."""
    entries, made = _chain_entries(buildings=buildings)
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


def _unlocks(
    held: Iterable[str],
    *,
    machines: Iterable[str] = SOLVE_BUILDINGS,
    extractors: Iterable[str] = (SOLVE_MINER_BUILDING,),
) -> UnlockState:
    """An unlock state holding these recipes and these machines' build recipes, by asset path.

    Every machine and the miner are held unless told otherwise, so a world's locks are the ones
    it names. An extractor is on its own parameter, so ``machines=()`` still means no machine
    runs a recipe here and says nothing of what supplies the Ore.
    """
    return dataclasses.replace(
        EMPTY_UNLOCK_STATE,
        recipes=frozenset(
            (
                *(_path(name) for name in held),
                *(machine_build_path(name) for name in machines),
                *(machine_build_path(name) for name in extractors),
            )
        ),
    )


def _model(
    held: Iterable[str],
    *,
    machines: Iterable[str] = SOLVE_BUILDINGS,
    extractors: Iterable[str] = (SOLVE_MINER_BUILDING,),
) -> WorldModel:
    """A synthetic world of the pinned build, none placed, unlocking these recipes and machines."""
    return dataclasses.replace(
        synthetic_world(game_pin()),
        unlocks=_unlocks(held, machines=machines, extractors=extractors),
    )


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


def _route_trace(
    held: Iterable[str],
    registry: Registry,
    request: PlanRequest,
    *,
    extractors: Iterable[str] = (SOLVE_MINER_BUILDING,),
) -> Trace:
    """The plan.redesign trace of one world."""
    return run_rule(REDESIGN_RULE, _inputs(_model(held, extractors=extractors), registry, request))


def _route_card(
    held: Iterable[str],
    registry: Registry,
    request: PlanRequest,
    *,
    extractors: Iterable[str] = (SOLVE_MINER_BUILDING,),
) -> Card:
    """The plan.redesign card of one world, which must fire."""
    card = card_for(_route_trace(held, registry, request, extractors=extractors))
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
            **plan_rules.redesign_inputs(
                plan,
                held=(),
                locked=(),
                locked_extractors=(),
                requires=(),
                target_names=MappingProxyType({SOLVE_RELIC_ITEM: RELIC_NAME}),
            ),
            IN_UNCHECKED: InputValue((), "synthetic.unchecked"),
            RAW_UNKNOWN: InputValue((), "synthetic.raw_unknown"),
        },
        unlocks=frozenset(),
    )


# ---------------------------------------------------------------------------
# CS-1379: tier 1 reads the display name, and the identity stays the ClassName
# ---------------------------------------------------------------------------


def _with_item_name(registry: Registry, item: str, name: str) -> Registry:
    """The same registry with one item's display name replaced, and nothing else.

    Args:
        registry: The registry.
        item: The item's ClassName.
        name: Its new display name, verbatim.

    Returns:
        The registry, every other field the same.
    """
    entry = dataclasses.replace(registry.items[item], display_name=name)
    return dataclasses.replace(registry, items=MappingProxyType({**registry.items, item: entry}))


def _without_item(registry: Registry, item: str) -> Registry:
    """The same registry holding no descriptor for one item, and nothing else changed."""
    kept = {key: entry for key, entry in registry.items.items() if key != item}
    return dataclasses.replace(registry, items=MappingProxyType(kept))


def _undecided(card: Card) -> list[tuple[str, str]]:
    """Every indeterminate step of a card's trace, as subject and reason, in order."""
    return [
        (step.subject, step.reason)
        for step in card.trace.steps
        if step.kind is StepKind.VERDICT_INDETERMINATE
    ]


def _split_derivation(derivation: str) -> tuple[str, str]:
    """A derivation's headers, whose Advice and Because quote tiers 1 and 2, and its steps."""
    headers, marker, steps = derivation.partition("\nSteps:\n")
    assert marker != ""
    return headers, steps


def _two_target_route() -> Card:
    """10 Relic and 20 Rod a minute, stated Rod first, over two recipes neither of them held."""
    registry = _registry(
        [
            _recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_Rod", [SOLVE_ORE_ITEM], [SOLVE_ROD_ITEM]),
        ]
    )
    request = dataclasses.replace(
        _request(registry),
        targets=MappingProxyType({SOLVE_ROD_ITEM: Fraction(20), SOLVE_RELIC_ITEM: Fraction(10)}),
    )
    return _route_card((), registry, request)


def test_redesign_tiers_read_the_display_name_with_the_id_unchanged(tmp_path: Path) -> None:
    """A name moves tiers 1 and 2 alike, and neither the subject nor the id."""
    model = _model([HELD_STAGE])
    registry = _three_locked_registry()
    other = _with_item_name(registry, SOLVE_RELIC_ITEM, RENAMED_RELIC)

    (card,) = _cards(_advise(tmp_path / "named", model, registry, _request(registry)), REDESIGN_ID)
    (renamed,) = _cards(_advise(tmp_path / "renamed", model, other, _request(other)), REDESIGN_ID)

    assert card.tier1 == f"Plan toward {RELIC_LABEL}"
    assert renamed.tier1 == f"Plan toward {RENAMED_LABEL}"
    assert card.tier2 == (
        f"This route to {RELIC_LABEL} runs 3 locked and 1 held recipe(s)"
        f"{MUST_UNLOCK}{_not_chosen(4)}"
    )
    assert renamed.tier2 == (
        f"This route to {RENAMED_LABEL} runs 3 locked and 1 held recipe(s)"
        f"{MUST_UNLOCK}{_not_chosen(4)}"
    )
    # Two registries differing only in the name: one identity, and it is the ClassName's.
    assert card.subject_key == "plan:Desc_SolveRelic_C"
    assert renamed.subject_key == card.subject_key
    assert card.id == card_id(REDESIGN_ID, "plan:Desc_SolveRelic_C", None)
    assert renamed.id == card.id
    # A name that reads is no fallback: the firing path's own step stands alone.
    assert _undecided(card) == [COMPARE_STEP]


@pytest.mark.parametrize("absent", [False, True], ids=["empty-name", "item-absent"])
def test_redesign_no_display_name_reads_the_classname(absent: bool) -> None:
    registry = _three_locked_registry()
    named = _route_card([HELD_STAGE], registry, _request(registry))
    nameless = (
        _without_item(registry, SOLVE_RELIC_ITEM)
        if absent
        else _with_item_name(registry, SOLVE_RELIC_ITEM, "")
    )

    card = _route_card([HELD_STAGE], nameless, _request(registry))

    assert card.tier1 == "Plan toward Desc_SolveRelic_C"
    assert card.tier2.startswith("This route to Desc_SolveRelic_C runs 3 locked and 1 held")
    assert _card_read(card, IN_REDESIGN_TARGET_NAMES) == {SOLVE_RELIC_ITEM: None}
    assert card.id == named.id
    assert card.subject_key == named.subject_key
    # One fixed step says so, and it is no rejection: only a rejection settles the rule.
    assert _undecided(card) == [COMPARE_STEP, (NAME_ALTERNATIVE, NAME_REASON)]
    rejected = any(step.kind is StepKind.ALTERNATIVE_REJECTED for step in card.trace.steps)
    assert not rejected
    settled = REDESIGN_ID in settled_rules((card.trace,))
    assert not settled


def test_redesign_tier3_steps_keep_the_classname() -> None:
    """The headers quote tiers 1 and 2, so only the steps can carry either ClassName."""
    card = _two_target_route()

    headers, steps = _split_derivation(card.tier3)

    # The control: both headers are there and read the names, so the split is what grades this.
    assert f"Advice: {card.tier1}" in headers
    assert f"Because: {card.tier2}" in headers
    assert card.tier1 == f"Plan toward {RELIC_LABEL}, {ROD_LABEL}"
    assert card.tier2.startswith(f"This route to {RELIC_LABEL}, {ROD_LABEL} runs 2 locked")
    named_in_headers = [item for item in (SOLVE_RELIC_ITEM, SOLVE_ROD_ITEM) if item in headers]
    assert named_in_headers == []
    # Each ClassName in the plan's own read and on the fired line, not just as a name's key.
    production = next(line for line in steps.splitlines() if "Read plan.redesign.plan = " in line)
    assert f'targets={{"{SOLVE_RELIC_ITEM}": 10.00, "{SOLVE_ROD_ITEM}": 20.00}}' in production
    assert f"Rule plan.redesign fired for plan:{SOLVE_RELIC_ITEM}+{SOLVE_ROD_ITEM}" in steps
    assert (
        f'Read plan.redesign.target_names = {{"{SOLVE_RELIC_ITEM}": "{RELIC_NAME}",'
        f' "{SOLVE_ROD_ITEM}": "{ROD_NAME}"}} from registry.items.display_name'
    ) in steps


def test_a_rejected_route_reads_its_names_and_records_no_fallback() -> None:
    """A fallback step would unsettle the one path that settles, so it waits for a card."""
    world = _with_value(
        _rejected_world(), IN_REDESIGN_TARGET_NAMES, MappingProxyType({SOLVE_RELIC_ITEM: None})
    )

    trace = run_rule(REDESIGN_RULE, world)

    assert card_for(trace) is None
    assert _indeterminate_count(trace) == 0
    assert _read(trace, IN_REDESIGN_TARGET_NAMES) == {SOLVE_RELIC_ITEM: None}
    assert settled_rules((trace,)) == frozenset({REDESIGN_ID})


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
    assert card.tier1 == f"Plan toward {RELIC_LABEL}"
    assert card.tier2 == f"{ROUTE_RUNS} 3 locked and 1 held recipe(s){MUST_UNLOCK}{_not_chosen(4)}"
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
    assert requires == (f"recipe:{_path(HELD_STAGE)}", ASSEMBLER_KEY, MINER_KEY)
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
    assert card.tier2 == f"{ROUTE_RUNS} 0 locked and 13 held recipe(s){NO_UNLOCK}{_not_chosen(13)}"
    unlocks = sorted(_requires(card))
    assert unlocks == sorted(
        (ASSEMBLER_KEY, MINER_KEY, *(f"recipe:{_path(name)}" for name in names))
    )
    assert _machines(card) == [(name, Fraction(1)) for name in names]


def test_one_locked_stage_on_the_same_chain_reads_the_must_unlock_wording() -> None:
    """The control for the wording: it turns on the locked count and nothing else."""
    registry = _chain_registry()
    names = _chain_names()
    card = _route_card(names[:-1], registry, _request(registry))
    assert (
        card.tier2 == f"{ROUTE_RUNS} 1 locked and 12 held recipe(s){MUST_UNLOCK}{_not_chosen(13)}"
    )
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
    assert card.tier2 == f"{ROUTE_RUNS} 1 locked and 0 held recipe(s){MUST_UNLOCK}{_not_chosen(1)}"


def test_a_pathless_recipe_stays_off_the_route_and_is_counted_in_tier_2() -> None:
    registry = _ascent_registry(direct_pathless=True)
    card = _route_card((), registry, _request(registry))
    assert [stage for stage, _machine_count in _machines(card)] == ["R_Two", "R_One"]
    assert _card_read(card, IN_UNCHECKED) == ("R_Direct",)
    assert card.tier2 == (
        f"{ROUTE_RUNS} 2 locked and 0 held recipe(s){MUST_UNLOCK}{_not_chosen(2)}{ONE_UNCHECKED}"
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
# A recipe is held only with a machine to run it (BOOTSTRAP.md section 5.4)
# ---------------------------------------------------------------------------


def _one_recipe_registry(*, buildings: tuple[str, ...] = (SOLVE_ASSEMBLER_BUILDING,)) -> Registry:
    """R_Direct, Ore to Relic, on these machines: one machine at 10 Relic a minute."""
    return _registry(
        [_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM], buildings=buildings)]
    )


def test_a_recipe_held_with_no_machine_held_reads_no_adopt_card_and_counts_locked(
    tmp_path: Path,
) -> None:
    """The real-world defect, on one recipe: told to build a chain its machine cannot run."""
    registry = _one_recipe_registry()
    locked = _model(["R_Direct"], machines=())

    advice = _advise(tmp_path, locked, registry, _request(registry))

    assert _cards(advice, ADOPT_ID) == []
    (card,) = _cards(advice, REDESIGN_ID)
    assert card.tier2 == f"{ROUTE_RUNS} 1 locked and 0 held recipe(s){MUST_UNLOCK}{_not_chosen(1)}"
    no_unlock_named = NO_UNLOCK in card.tier2
    assert not no_unlock_named
    assert _card_read(card, IN_STATUS) == NO_PLAN
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Direct",)
    assert _card_read(card, IN_REDESIGN_HELD) == ()
    # The miner alone: this world holds the one machine that digs what the route consumes.
    assert _requires(card) == (MINER_KEY,)

    # The control: the same recipe with its machine held ranks, and reaches no route.
    held = _advise(
        tmp_path,
        _model(["R_Direct"], machines=[SOLVE_ASSEMBLER_BUILDING]),
        registry,
        _request(registry),
    )
    assert _cards(held, REDESIGN_ID) == []
    (adopt,) = _cards(held, ADOPT_ID)
    assert _requires(adopt) == (f"recipe:{_path('R_Direct')}", ASSEMBLER_KEY, MINER_KEY)


def test_a_held_machine_alone_does_not_hold_its_recipe() -> None:
    """The other half of the join: every machine held, and the recipe's own path is not."""
    registry = _one_recipe_registry()
    card = _route_card((), registry, _request(registry))
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Direct",)
    assert _requires(card) == (MINER_KEY,)
    # The control: the recipe's own path lifts it, every machine held as before.
    world = _inputs(_model(["R_Direct"]), registry, _request(registry))
    assert _offered(world, IN_STATUS) == RANKED


def test_two_recipes_on_one_held_machine_name_its_key_once() -> None:
    """Deduped in first-seen order: each recipe's own key, its machine's beside the first."""
    registry = _registry(
        [
            _recipe("R_Two", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_One", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),
        ]
    )
    world = _inputs(_model(("R_Two", "R_One")), registry, _request(registry))
    assert _offered(world, IN_PLAN) is not None
    assert _offered(world, "plan.requires") == (
        f"recipe:{_path('R_Two')}",
        ASSEMBLER_KEY,
        f"recipe:{_path('R_One')}",
        MINER_KEY,
    )

    # The control: two recipes on two machines name both, each beside its first recipe.
    two_machines = _registry(
        [
            _recipe("R_Two", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe(
                "R_One", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM], buildings=(SOLVE_SMELTER_BUILDING,)
            ),
        ]
    )
    both = _inputs(_model(("R_Two", "R_One")), two_machines, _request(two_machines))
    assert _offered(both, "plan.requires") == (
        f"recipe:{_path('R_Two')}",
        ASSEMBLER_KEY,
        f"recipe:{_path('R_One')}",
        SMELTER_KEY,
        MINER_KEY,
    )


def test_every_stage_of_a_route_on_one_held_machine_names_its_key_once() -> None:
    registry = _chain_registry()
    names = _chain_names()
    card = _route_card(names, registry, _request(registry))
    named = _requires(card).count(ASSEMBLER_KEY)
    assert named == 1
    # First-seen order: the first stage of the plan, then its machine, then the rest.
    assert _requires(card)[:2] == (f"recipe:{_path(names[0])}", ASSEMBLER_KEY)
    # Every stage's own, the one machine's, and the miner's, read last.
    assert len(_requires(card)) == len(names) + 2
    assert _requires(card)[-1] == MINER_KEY


@pytest.mark.parametrize(
    ("buildings", "machines", "first"),
    [
        (
            (SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
            (SOLVE_SMELTER_BUILDING,),
            SMELTER_KEY,
        ),
        (
            (SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
            (SOLVE_ASSEMBLER_BUILDING,),
            ASSEMBLER_KEY,
        ),
        (
            (SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
            (SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
            ASSEMBLER_KEY,
        ),
        (
            (SOLVE_SMELTER_BUILDING, SOLVE_ASSEMBLER_BUILDING),
            (SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
            SMELTER_KEY,
        ),
    ],
    ids=["second-held", "first-held", "both-held", "both-held-declared-the-other-way"],
)
def test_of_two_machines_a_recipe_names_the_first_the_world_holds_and_that_one_alone(
    buildings: tuple[str, ...], machines: tuple[str, ...], first: str
) -> None:
    """The recipe's own produced_in decides which is first, never the world or a sort."""
    ranked = _one_recipe_registry(buildings=buildings)
    world = _inputs(_model(["R_Direct"], machines=machines), ranked, _request(ranked))
    assert _offered(world, "plan.requires") == (f"recipe:{_path('R_Direct')}", first, MINER_KEY)

    # The same on the route, over a chain the cap cuts, so no ranked plan reads it.
    chain = _chain_registry(buildings=buildings)
    names = _chain_names()
    routed = _inputs(_model(names, machines=machines), chain, _request(chain))
    card = card_for(run_rule(REDESIGN_RULE, routed))
    assert card is not None
    machine_keys = [key for key in _requires(card) if key in (ASSEMBLER_KEY, SMELTER_KEY)]
    assert machine_keys == [first]


#: The two shapes a machine with no unlock to check takes, each graded below.
_SMELTER_BUILD_SHAPES: Final[Mapping[str, tuple[Mapping[str, str], ...]]] = MappingProxyType(
    {
        "no-build-recipe": (),
        "pathless-build-recipe": (machine_build_entry(SOLVE_SMELTER_BUILDING, pathless=True),),
    }
)


def _smelter_builds(shape: str) -> tuple[Mapping[str, str], ...]:
    """Every machine's build recipe, with the Smelter's in one of those shapes."""
    return (
        machine_build_entry(SOLVE_ASSEMBLER_BUILDING),
        machine_build_entry(SOLVE_REFINERY_BUILDING),
        *_SMELTER_BUILD_SHAPES[shape],
    )


def _smelter_registry(builds: Iterable[Mapping[str, str]], *, two_stages: bool = True) -> Registry:
    """R_Direct runs on the Smelter; R_Two and R_One on the Assembler.

    Under the power direction R_Direct would win, at 4 MW against 30, so a search that kept it
    could not hide. Off the search and off the route the two stages are all there is.
    """
    direct = _recipe(
        "R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM], buildings=(SOLVE_SMELTER_BUILDING,)
    )
    stages = [
        _recipe("R_Two", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
        _recipe("R_One", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),
    ]
    return _registry([direct, *stages] if two_stages else [direct], builds=builds)


@pytest.mark.parametrize("shape", sorted(_SMELTER_BUILD_SHAPES))
def test_a_recipe_no_machine_of_which_joins_a_build_recipe_is_flagged_and_off_the_route(
    shape: str,
) -> None:
    registry = _smelter_registry(_smelter_builds(shape))
    request = _request(registry, direction=POWER)

    # The world holds its own path and every machine, and still it is held nowhere.
    card = _route_card(("R_Direct",), registry, request)

    assert [stage for stage, _machine_count in _machines(card)] == ["R_Two", "R_One"]
    assert _card_read(card, IN_UNCHECKED) == ("R_Direct",)
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Two", "R_One")
    assert _card_read(card, IN_REDESIGN_HELD) == ()
    assert card.tier2 == (
        f"{ROUTE_RUNS} 2 locked and 0 held recipe(s){MUST_UNLOCK}{_not_chosen(2)}{ONE_UNCHECKED}"
    )

    # Off the search too: with the two stages held they rank under power, and it stays flagged.
    ranked = _inputs(_model(("R_Direct", "R_Two", "R_One")), registry, request)
    plan = _plan_of(_offered(ranked, IN_PLAN))
    assert [step.recipe_key for step in plan.steps] == ["R_Two", "R_One"]
    assert _offered(ranked, IN_UNCHECKED) == ("R_Direct",)
    adopt = card_for(run_rule(plan_rules.ADOPT_RULE, ranked))
    assert adopt is not None
    stated = adopt.tier2.endswith(ONE_UNCHECKED)
    assert stated
    assert _offered(ranked, "plan.requires") == (
        f"recipe:{_path('R_Two')}",
        ASSEMBLER_KEY,
        f"recipe:{_path('R_One')}",
        MINER_KEY,
    )

    # The control: with a build recipe carrying a path it wins that search, at 4 MW.
    control = _smelter_registry(MACHINE_BUILD_ENTRIES)
    won = _inputs(
        _model(("R_Direct", "R_Two", "R_One")), control, _request(control, direction=POWER)
    )
    assert [step.recipe_key for step in _plan_of(_offered(won, IN_PLAN)).steps] == ["R_Direct"]
    assert _offered(won, IN_UNCHECKED) == ()


@pytest.mark.parametrize("shape", sorted(_SMELTER_BUILD_SHAPES))
def test_a_target_whose_only_recipe_has_no_machine_to_check_is_no_route_never_fatal(
    shape: str,
) -> None:
    """Flagged and skipped: no lock nothing could lift, no silent hold, and nothing raises."""
    registry = _smelter_registry(_smelter_builds(shape), two_stages=False)
    world = _inputs(_model(("R_Direct",)), registry, _request(registry))

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, IN_REDESIGN_STATUS) == NO_ROUTE
    assert _offered(world, IN_REDESIGN_UNMADE) == (SOLVE_RELIC_ITEM,)
    assert _offered(world, IN_UNCHECKED) == ("R_Direct",)
    trace = run_rule(REDESIGN_RULE, world)
    assert card_for(trace) is None
    assert _errors(trace) == []

    # The control: a Smelter that can be shown unlocked makes the same recipe a route.
    built = _smelter_registry(MACHINE_BUILD_ENTRIES, two_stages=False)
    assert _route_card((), built, _request(built)).tier1 == f"Plan toward {RELIC_LABEL}"


@pytest.mark.parametrize(
    ("machines", "fires_with"),
    [((SOLVE_ASSEMBLER_BUILDING,), ASSEMBLER_KEY), ((), None)],
    ids=["other-machine-held", "no-machine-held"],
)
def test_one_machine_with_no_build_recipe_leaves_the_recipe_checkable_through_the_other(
    machines: tuple[str, ...], fires_with: str | None
) -> None:
    """At least one is enough: this recipe joins, so it is held or locked and never flagged."""
    registry = _registry(
        [
            _recipe(
                "R_Direct",
                [SOLVE_ORE_ITEM],
                [SOLVE_RELIC_ITEM],
                buildings=(SOLVE_SMELTER_BUILDING, SOLVE_ASSEMBLER_BUILDING),
            )
        ],
        builds=(machine_build_entry(SOLVE_ASSEMBLER_BUILDING),),
    )
    world = _inputs(_model(["R_Direct"], machines=machines), registry, _request(registry))

    assert _offered(world, IN_UNCHECKED) == ()
    if fires_with is None:
        assert _offered(world, IN_STATUS) == NO_PLAN
        assert _offered(world, IN_REDESIGN_LOCKED) == ("R_Direct",)
    else:
        assert _offered(world, IN_STATUS) == RANKED
        assert _offered(world, "plan.requires") == (
            f"recipe:{_path('R_Direct')}",
            fires_with,
            MINER_KEY,
        )


# ---------------------------------------------------------------------------
# A raw item is supplied only with a machine to extract it (CS-1382)
# ---------------------------------------------------------------------------


def test_an_unsupplied_raw_reads_no_adopt_card_and_counts_its_machine_locked(
    tmp_path: Path,
) -> None:
    """The clause's constructed set: recipe and machine held, and nothing that digs the Ore."""
    registry = _one_recipe_registry()
    unsupplied = _model(["R_Direct"], extractors=())

    advice = _advise(tmp_path / "unsupplied", unsupplied, registry, _request(registry))

    assert _cards(advice, ADOPT_ID) == []
    (card,) = _cards(advice, REDESIGN_ID)
    assert _card_read(card, IN_STATUS) == NO_PLAN
    assert _card_read(card, IN_REDESIGN_HELD) == ("R_Direct",)
    assert _card_read(card, IN_REDESIGN_LOCKED) == ()
    assert _card_read(card, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING,)

    # The control: the same world holding the miner ranks, so the miner alone decided above.
    supplied = _advise(tmp_path / "supplied", _model(["R_Direct"]), registry, _request(registry))
    assert _cards(supplied, REDESIGN_ID) == []
    (adopt,) = _cards(supplied, ADOPT_ID)
    assert _requires(adopt) == (f"recipe:{_path('R_Direct')}", ASSEMBLER_KEY, MINER_KEY)


def _two_raw_registry(
    entries: list[dict[str, str]],
    *,
    items: Iterable[str] = (),
    resources: tuple[str, ...] = (SOLVE_ORE_ITEM, SOLVE_RARE_ITEM),
    drill_first: bool = False,
) -> Registry:
    """These recipes, Ore dug only by the miner and Rare only by the drill.

    Args:
        entries: The recipes.
        items: Invented items to give descriptors.
        resources: The items the resource group declares, in that order.
        drill_first: Declare the drill ahead of the miner, so an order that followed the
            document rather than the plan's raw items would show.

    Returns:
        The registry.
    """
    miner = extractor_entry(SOLVE_MINER_BUILDING, only=(SOLVE_ORE_ITEM,))
    drill = extractor_entry(DRILL_BUILDING, only=(SOLVE_RARE_ITEM,))
    return _registry(
        entries,
        items=items,
        resources=resources,
        extractors=(drill, miner) if drill_first else (miner, drill),
        extractor_builds=(
            machine_build_entry(SOLVE_MINER_BUILDING),
            machine_build_entry(DRILL_BUILDING),
        ),
    )


def _both_raw_registry(*, drill_first: bool = False) -> Registry:
    """R_Both eats Rare and Ore and makes Relic: one machine at 10 Relic a minute."""
    return _two_raw_registry(
        [_recipe("R_Both", [SOLVE_RARE_ITEM, SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],
        drill_first=drill_first,
    )


def test_no_unlock_never_reads_beside_an_unsupplied_raw() -> None:
    """Every stage held, past the cap, so only the miner parts the two sentences."""
    registry = _chain_registry()
    names = _chain_names()

    card = _route_card(names, registry, _request(registry), extractors=())

    assert card.tier2 == (
        f"{ROUTE_RUNS} 0 locked and 13 held recipe(s){NEEDS_ONE}{MUST_EXTRACT}{_not_chosen(13)}"
    )
    no_unlock_named = NO_UNLOCK in card.tier2
    assert not no_unlock_named
    assert _card_read(card, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING,)

    # The control, and the byte-same half of the ruling: the miner held reads the sentence as
    # it read before raw supply was asked about, and names the miner on what the engine checks.
    held = _route_card(names, registry, _request(registry))
    assert held.tier2 == f"{ROUTE_RUNS} 0 locked and 13 held recipe(s){NO_UNLOCK}{_not_chosen(13)}"
    assert _card_read(held, LOCKED_EXTRACTORS) == ()
    named = _requires(held).count(MINER_KEY)
    assert named == 1


def test_a_locked_stage_and_a_locked_extractor_each_say_so() -> None:
    """Both clauses, stages first, and no third sentence between them."""
    registry = _chain_registry()
    names = _chain_names()

    card = _route_card(names[:-1], registry, _request(registry), extractors=())

    assert card.tier2 == (
        f"{ROUTE_RUNS} 1 locked and 12 held recipe(s){NEEDS_ONE}"
        f"{MUST_UNLOCK}{MUST_EXTRACT}{_not_chosen(13)}"
    )


def test_locked_stages_and_locked_machines_never_reach_requires() -> None:
    registry = _one_recipe_registry()

    card = _route_card((), registry, _request(registry), extractors=())

    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Direct",)
    assert _card_read(card, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING,)
    assert _requires(card) == ()
    assert card.tier2 == (
        f"{ROUTE_RUNS} 1 locked and 0 held recipe(s){NEEDS_ONE}"
        f"{MUST_UNLOCK}{MUST_EXTRACT}{_not_chosen(1)}"
    )
    # Tier 3 names the machine through the read, and tier 1 and tier 2 do not.
    named = (
        f'Read plan.redesign.locked_extractors = ("{SOLVE_MINER_BUILDING}") from'
        " advisor.plans.redesign.locked_extractors"
    ) in card.tier3
    assert named
    in_tiers = SOLVE_MINER_BUILDING in card.tier1 + card.tier2
    assert not in_tiers


def test_a_held_converter_still_ranks() -> None:
    """The Rare is declared raw and nothing digs it, and a held recipe makes it from Ore.

    By hand: R_Two eats Rare, R_One eats Ore and makes Rare, one machine each at 10 Relic a
    minute, 10 Ore a minute. The narrowed search takes the Rare as an ordinary item.
    """
    registry = _two_raw_registry(
        [
            _recipe("R_Two", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM]),
            _recipe("R_One", [SOLVE_ORE_ITEM], [SOLVE_RARE_ITEM]),
        ]
    )

    world = _inputs(_model(("R_Two", "R_One")), registry, _request(registry))

    assert _offered(world, IN_STATUS) == RANKED
    plan = _plan_of(_offered(world, IN_PLAN))
    assert [(step.recipe_key, step.machines) for step in plan.steps] == [
        ("R_Two", Fraction(1)),
        ("R_One", Fraction(1)),
    ]
    assert plan.raw_inputs == {SOLVE_ORE_ITEM: Fraction(10)}
    assert _offered(world, "plan.requires") == (
        f"recipe:{_path('R_Two')}",
        ASSEMBLER_KEY,
        f"recipe:{_path('R_One')}",
        MINER_KEY,
    )
    assert run_rule(plan_rules.ADOPT_RULE, world).recommendation is not None


def test_a_target_declared_raw_and_unsupplied_stays_malformed() -> None:
    """Pillar 1 refuses the question, so no narrowing can turn it into a false no-plan."""
    registry = _one_recipe_registry()
    request = dataclasses.replace(
        _request(registry), targets=MappingProxyType({SOLVE_ORE_ITEM: Fraction(10)})
    )

    unsupplied = plan_offer(_unlocks(["R_Direct"], extractors=()), registry, request)

    assert unsupplied[IN_STATUS].value == MALFORMED
    assert unsupplied[IN_REDESIGN_STATUS].value == NOT_REACHED
    # The control: the same request with the miner held reads the same, so supply decides nothing.
    supplied = plan_offer(_unlocks(["R_Direct"]), registry, request)
    assert supplied[IN_STATUS].value == MALFORMED

    # A target no extractor joins is the same question, from the other side of the join.
    relic = dataclasses.replace(_request(registry), raw_items=(SOLVE_ORE_ITEM, SOLVE_RELIC_ITEM))
    declared = plan_offer(_unlocks(["R_Direct"]), registry, relic)
    assert declared[IN_STATUS].value == MALFORMED
    assert declared[RAW_UNKNOWN].value == (SOLVE_RELIC_ITEM,)


def test_a_net_zero_raw_needs_no_extractor() -> None:
    """R_Up eats Ore and R_Down gives it back, so the plan's net Ore is zero.

    By hand at 10 Relic a minute: R_Down makes 10 Relic and 10 Ore on one machine, and R_Up turns
    that Ore into the 10 Feed R_Down eats on one machine.
    """
    feed = _item("Feed")
    registry = _registry(
        [
            _recipe("R_Down", [feed], [SOLVE_ORE_ITEM, SOLVE_RELIC_ITEM]),
            _recipe("R_Up", [SOLVE_ORE_ITEM], [feed]),
        ],
        items=[feed],
    )

    world = _inputs(_model(("R_Down", "R_Up")), registry, _request(registry))

    assert _offered(world, IN_STATUS) == RANKED
    plan = _plan_of(_offered(world, IN_PLAN))
    assert plan.raw_inputs == {SOLVE_ORE_ITEM: Fraction(0)}
    assert _offered(world, "plan.requires") == (
        f"recipe:{_path('R_Down')}",
        ASSEMBLER_KEY,
        f"recipe:{_path('R_Up')}",
    )

    # The control: a plan that does eat Ore names the miner, so its absence above is the rate's.
    direct = _one_recipe_registry()
    eats = _inputs(_model(["R_Direct"]), direct, _request(direct))
    assert _offered(eats, "plan.requires") == (
        f"recipe:{_path('R_Direct')}",
        ASSEMBLER_KEY,
        MINER_KEY,
    )


@pytest.mark.parametrize("extractors", [(SOLVE_MINER_BUILDING,), ()], ids=["held", "not-held"])
def test_a_route_stage_at_no_machine_needs_no_extractor(extractors: tuple[str, ...]) -> None:
    """The route's half of the same rate: the feeder runs at zero, and eats no Ore."""
    registry = _free_loop_registry()

    card = _route_card((), registry, _request(registry), extractors=extractors)

    plan = _plan_of(_card_read(card, IN_REDESIGN_PLAN))
    assert plan.raw_inputs == {SOLVE_ORE_ITEM: Fraction(0)}
    assert _card_read(card, LOCKED_EXTRACTORS) == ()
    assert _requires(card) == ()


#: The three ways a registry can name no extractor a world could be shown to hold.
_NO_EXTRACTOR_SHAPES: Final[Mapping[str, Mapping[str, Any]]] = MappingProxyType(
    {
        "no-extractor-at-all": {"extractors": (), "extractor_builds": ()},
        "no-build-recipe": {"extractor_builds": ()},
        "pathless-build-recipe": {
            "extractor_builds": (machine_build_entry(SOLVE_MINER_BUILDING, pathless=True),)
        },
    }
)


@pytest.mark.parametrize("shape", sorted(_NO_EXTRACTOR_SHAPES))
def test_a_registry_with_no_extractor_flags_every_raw(shape: str, tmp_path: Path) -> None:
    """Flagged, skipped and never fatal: no-plan, then no-route, and it says which items."""
    registry = _registry(
        [_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])], **_NO_EXTRACTOR_SHAPES[shape]
    )
    model = _model(["R_Direct"], extractors=())

    world = _inputs(model, registry, _request(registry))

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, IN_REDESIGN_STATUS) == NO_ROUTE
    assert _offered(world, IN_REDESIGN_UNMADE) == (SOLVE_ORE_ITEM,)
    assert _offered(world, RAW_UNKNOWN) == (SOLVE_ORE_ITEM,)
    for rule in plan_rules.RULES:
        trace = run_rule(rule, world)
        assert card_for(trace) is None
        assert _errors(trace) == []
    advice = _advise(tmp_path, model, registry, _request(registry))
    assert _outcome_of(advice) == PlanOutcome(
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=NO_ROUTE,
        redesign_reason=NO_ROUTE_REASON,
        trimmed=(),
        unmade=(SOLVE_ORE_ITEM,),
        raw_unknown=(SOLVE_ORE_ITEM,),
    )


def test_a_raw_item_no_extractor_joins_reads_in_tier_2_and_tier_3() -> None:
    """The Rare is declared and nothing can dig it: a count beside the plan, the name in tier 3."""
    registry = _registry(
        [_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],
        resources=(SOLVE_ORE_ITEM, SOLVE_RARE_ITEM),
        extractors=(extractor_entry(SOLVE_MINER_BUILDING, only=(SOLVE_ORE_ITEM,)),),
    )

    world = _inputs(_model(["R_Direct"]), registry, _request(registry))

    assert _offered(world, IN_STATUS) == RANKED
    assert _offered(world, RAW_UNKNOWN) == (SOLVE_RARE_ITEM,)
    assert _source_of(world, RAW_UNKNOWN) == "advisor.plans.raw_unknown"
    adopt = card_for(run_rule(plan_rules.ADOPT_RULE, world))
    assert adopt is not None
    assert adopt.tier2 == (
        f"It makes 10.00 per minute of {RELIC_LABEL} with 1.00 machine equivalents{ONE_RAW_UNKNOWN}"
    )
    read = (
        f'Read plan.raw_unknown = ("{SOLVE_RARE_ITEM}") from advisor.plans.raw_unknown'
    ) in adopt.tier3
    assert read

    # The route reads the same input on its own path, the clause after the unchecked one.
    route = _route_card((), registry, _request(registry))
    assert route.tier2 == (
        f"{ROUTE_RUNS} 1 locked and 0 held recipe(s){MUST_UNLOCK}{_not_chosen(1)}{ONE_RAW_UNKNOWN}"
    )
    assert _card_read(route, RAW_UNKNOWN) == (SOLVE_RARE_ITEM,)

    # The control: with an extractor joined, nothing is flagged and nothing is said.
    control = _one_recipe_registry()
    clean = _inputs(_model(["R_Direct"]), control, _request(control))
    assert _offered(clean, RAW_UNKNOWN) == ()
    plain = card_for(run_rule(plan_rules.ADOPT_RULE, clean))
    assert plain is not None
    flagged = ONE_RAW_UNKNOWN in plain.tier2
    assert not flagged


def test_a_raw_item_no_extractor_joins_is_never_treated_as_supplied() -> None:
    """R_Rare eats the Rare and nothing can dig it: no search, and no route either."""
    registry = _registry(
        [_recipe("R_Rare", [SOLVE_RARE_ITEM], [SOLVE_RELIC_ITEM])],
        resources=(SOLVE_ORE_ITEM, SOLVE_RARE_ITEM),
        extractors=(extractor_entry(SOLVE_MINER_BUILDING, only=(SOLVE_ORE_ITEM,)),),
    )

    world = _inputs(_model(["R_Rare"]), registry, _request(registry))

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, IN_REDESIGN_STATUS) == NO_ROUTE
    assert _offered(world, IN_REDESIGN_UNMADE) == (SOLVE_RARE_ITEM,)
    assert _offered(world, RAW_UNKNOWN) == (SOLVE_RARE_ITEM,)


def test_the_engine_drops_a_card_whose_extractor_is_not_held() -> None:
    """The second gate does not trust the first: the same offer, a world lacking the miner."""
    registry = _one_recipe_registry()
    world = _inputs(_model(["R_Direct"]), registry, _request(registry))
    # The control: the offer as built fires, over the world it was built for.
    assert run_rule(plan_rules.ADOPT_RULE, world).recommendation is not None

    bare = WorldInputs(values=world.values, unlocks=world.unlocks - {MINER_KEY})
    trace = run_rule(plan_rules.ADOPT_RULE, bare)

    assert trace.recommendation is None
    assert card_for(trace) is None
    assert trace.unmet == (MINER_KEY,)
    last = trace.steps[-1].kind
    assert last is StepKind.PRECONDITION_UNMET

    # The route's half: its no-unlock sentence rests on the same check.
    chain = _chain_registry()
    routed = _inputs(_model(_chain_names()), chain, _request(chain))
    assert run_rule(REDESIGN_RULE, routed).recommendation is not None
    gated = run_rule(
        REDESIGN_RULE, WorldInputs(values=routed.values, unlocks=routed.unlocks - {MINER_KEY})
    )
    assert card_for(gated) is None
    assert gated.unmet == (MINER_KEY,)


def test_a_world_holding_no_extractor_reads_no_plan_and_a_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Narrowed to no raw items at all, and only the stated tuple can read malformed."""
    calls = _count_calls(monkeypatch)
    registry = _one_recipe_registry()
    request = _request(registry)
    assert request.raw_items == (SOLVE_ORE_ITEM,)

    offered = plan_offer(_unlocks(["R_Direct"], extractors=()), registry, request)

    assert offered[IN_STATUS].value == NO_PLAN
    assert offered[IN_REDESIGN_STATUS].value == ROUTED
    assert offered[LOCKED_EXTRACTORS].value == (SOLVE_MINER_BUILDING,)
    (bound_args,) = calls["optimize_within_bound"]
    assert bound_args[1].raw_items == ()
    # The route is not narrowed: it starts from the one raw item, whose machine it names.
    (route_args,) = calls["derived_route"]
    assert route_args[1].raw_items == (SOLVE_ORE_ITEM,)
    (ratio_args,) = calls["solve_for_targets"]
    assert ratio_args[1].raw_items == (SOLVE_ORE_ITEM,)

    # The control: an empty tuple as STATED is what reads malformed, and reaches no search.
    stated = dataclasses.replace(request, raw_items=())
    assert plan_offer(_unlocks(["R_Direct"]), registry, stated)[IN_STATUS].value == MALFORMED


#: An invented item a free recipe makes: the chain's middle stage, or the byproduct.
_SPARE: Final = _item("Spare")

#: Worlds no raw item can feed, each its recipes and the ones it holds. The loop is
#: :func:`_free_loop_registry`'s, holding R_Main alone.
_FREE_WORLDS: Final = {
    "direct": ([_recipe("R_Free", [], [SOLVE_RELIC_ITEM])], ["R_Free"]),
    "chain": (
        [_recipe("R_Seed", [], [_SPARE]), _recipe("R_Up", [_SPARE], [SOLVE_RELIC_ITEM])],
        ["R_Seed", "R_Up"],
    ),
    "byproduct": ([_recipe("R_FreeBy", [], [SOLVE_RELIC_ITEM, _SPARE])], ["R_FreeBy"]),
}


@pytest.mark.parametrize(
    ("shape", "policy", "status"),
    [
        ("direct", BALANCED, RANKED),
        ("chain", BALANCED, RANKED),
        ("loop", BALANCED, RANKED),
        ("byproduct", BALANCED, NO_PLAN),
        ("byproduct", SINKABLE, RANKED),
    ],
)
def test_a_world_supplying_none_ranks_only_a_plan_eating_no_raw_item(
    shape: str, policy: str, status: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The module docstring's sentence on a world supplying none, measured (CS-1382, LOW).

    No miner is held, so the search starts from no raw item. A plan ranks fed by a held recipe
    eating nothing, making the target or a stage below it, or by a loop giving back what it
    eats, and a free recipe's byproduct still meets the stated policy: balanced reads no-plan
    where sinkable ranks the same world. The sentence this corrects read no-plan for the chain
    and the loop, and a rank for the byproduct under balanced.
    """
    calls = _count_calls(monkeypatch)
    if shape == "loop":
        registry, held = _free_loop_registry(), ["R_Main"]
    else:
        entries, held = _FREE_WORLDS[shape]
        registry = _registry(entries, items=[_SPARE])
    request = _request(registry, policy=policy)
    assert request.raw_items == (SOLVE_ORE_ITEM,)

    offered = plan_offer(_unlocks(held, extractors=()), registry, request)

    assert offered[IN_STATUS].value == status
    bound_raw = [args[1].raw_items for args in calls["optimize_within_bound"]]
    assert bound_raw == [()]
    if status == RANKED:
        assert _plan_of(offered[IN_PLAN].value).raw_inputs == {}


def test_the_search_keeps_the_stated_order_of_the_supplied_raw_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The group's own order, not the docs' extractor order, and no set decides it."""
    calls = _count_calls(monkeypatch)
    registry = _two_raw_registry(
        [_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],
        resources=(SOLVE_RARE_ITEM, SOLVE_ORE_ITEM),
    )

    plan_offer(
        _unlocks(["R_Direct"], extractors=(SOLVE_MINER_BUILDING, DRILL_BUILDING)),
        registry,
        _request(registry),
    )

    (bound_args,) = calls["optimize_within_bound"]
    assert bound_args[1].raw_items == (SOLVE_RARE_ITEM, SOLVE_ORE_ITEM)

    # The narrowing's half: with the drill not held the Rare is off the list and the Ore stays.
    plan_offer(_unlocks(["R_Direct"]), registry, _request(registry))
    (_both, narrowed) = calls["optimize_within_bound"]
    assert narrowed[1].raw_items == (SOLVE_ORE_ITEM,)


def test_one_machine_is_named_once_for_two_raw_items_it_extracts() -> None:
    registry = _registry(
        [_recipe("R_Both", [SOLVE_RARE_ITEM, SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],
        resources=(SOLVE_ORE_ITEM, SOLVE_RARE_ITEM),
    )

    card = _route_card((), registry, _request(registry), extractors=())

    assert _card_read(card, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING,)
    stated = NEEDS_ONE in card.tier2
    assert stated


@pytest.mark.parametrize("drill_first", [False, True], ids=["miner-first", "drill-first"])
def test_locked_extractors_read_in_the_plans_raw_order(drill_first: bool) -> None:
    """Sorted by raw item, as pillar 1 publishes them, whichever the document declares first."""
    registry = _both_raw_registry(drill_first=drill_first)

    card = _route_card((), registry, _request(registry), extractors=())

    assert _card_read(card, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING, DRILL_BUILDING)
    stated = " and needs 2 locked extractor(s)" in card.tier2
    assert stated


def test_a_held_extractor_joins_requires_beside_a_locked_one() -> None:
    registry = _both_raw_registry()

    card = _route_card((), registry, _request(registry), extractors=(DRILL_BUILDING,))

    assert _card_read(card, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING,)
    assert _requires(card) == (DRILL_KEY,)


def test_a_ranked_plan_names_each_raw_items_machine_sorted_by_raw_item() -> None:
    registry = _both_raw_registry(drill_first=True)

    world = _inputs(
        _model(["R_Both"], extractors=(SOLVE_MINER_BUILDING, DRILL_BUILDING)),
        registry,
        _request(registry),
    )

    assert _offered(world, "plan.requires") == (
        f"recipe:{_path('R_Both')}",
        ASSEMBLER_KEY,
        MINER_KEY,
        DRILL_KEY,
    )


#: Two unrestricted miners, for the arms over which of them a raw item names.
_SECOND_MINER: Final = "Build_SolveMinerTwo_C"
_SECOND_MINER_KEY: Final = f"recipe:{machine_build_path(_SECOND_MINER)}"


def _two_miner_registry(*, first_builds: bool = True, reversed_order: bool = False) -> Registry:
    """R_Direct on Ore, and two miners that can each dig it.

    Args:
        first_builds: Give the first miner a build recipe.
        reversed_order: Declare the second miner first.

    Returns:
        The registry.
    """
    entries = (extractor_entry(SOLVE_MINER_BUILDING), extractor_entry(_SECOND_MINER))
    builds = (machine_build_entry(SOLVE_MINER_BUILDING), machine_build_entry(_SECOND_MINER))
    return _registry(
        [_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],
        extractors=entries[::-1] if reversed_order else entries,
        extractor_builds=builds if first_builds else builds[1:],
    )


@pytest.mark.parametrize(
    ("held", "reversed_order", "key"),
    [
        ((SOLVE_MINER_BUILDING,), False, MINER_KEY),
        ((_SECOND_MINER,), False, _SECOND_MINER_KEY),
        ((SOLVE_MINER_BUILDING, _SECOND_MINER), False, MINER_KEY),
        ((SOLVE_MINER_BUILDING, _SECOND_MINER), True, _SECOND_MINER_KEY),
    ],
    ids=["first-held", "second-held", "both-held", "both-held-declared-the-other-way"],
)
def test_of_two_extractors_a_plan_names_the_first_the_world_holds_and_that_one_alone(
    held: tuple[str, ...], reversed_order: bool, key: str
) -> None:
    registry = _two_miner_registry(reversed_order=reversed_order)

    world = _inputs(_model(["R_Direct"], extractors=held), registry, _request(registry))

    assert _offered(world, "plan.requires") == (f"recipe:{_path('R_Direct')}", ASSEMBLER_KEY, key)


def test_a_locked_machine_named_is_the_first_that_can_be_shown_held() -> None:
    """A first miner with no build recipe would state a lock nothing could ever lift."""
    registry = _two_miner_registry(first_builds=False)
    card = _route_card((), registry, _request(registry), extractors=())
    assert _card_read(card, LOCKED_EXTRACTORS) == (_SECOND_MINER,)

    # The control: with its build recipe the first miner is the one named.
    built = _two_miner_registry()
    named = _route_card((), built, _request(built), extractors=())
    assert _card_read(named, LOCKED_EXTRACTORS) == (SOLVE_MINER_BUILDING,)


def test_an_extractor_held_by_a_trailing_token_alone_supplies_nothing() -> None:
    """A path sharing only the trailing token is another asset, and digs no Ore (CS-1343)."""
    real = MINER_BUILD_PATH
    elsewhere = real.replace("/Placed/", "/Elsewhere/")
    assert elsewhere != real
    assert elsewhere.rpartition(".")[2] == real.rpartition(".")[2]
    registry = _one_recipe_registry()
    held = _unlocks(["R_Direct"], extractors=())

    near = dataclasses.replace(held, recipes=held.recipes | {elsewhere})
    assert plan_offer(near, registry, _request(registry))[IN_STATUS].value == NO_PLAN

    # The control: the whole string supplies it.
    whole = dataclasses.replace(held, recipes=held.recipes | {real})
    assert plan_offer(whole, registry, _request(registry))[IN_STATUS].value == RANKED


def test_an_unsupplied_raw_byproduct_meets_the_stated_policy() -> None:
    """Accepted and filed, no case added to pillar 1: R_By makes Relic and leaves Rare over.

    With the drill held the Rare is raw, so nothing balances it. Unheld it is an ordinary item
    with a row, which balanced refuses and sinkable reports.
    """
    registry = _two_raw_registry(
        [_recipe("R_By", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM])]
    )
    both = (SOLVE_MINER_BUILDING, DRILL_BUILDING)

    balanced = _inputs(_model(["R_By"]), registry, _request(registry))
    assert _offered(balanced, IN_STATUS) == NO_PLAN
    # The route takes the Rare as raw, at a rate below zero, so nothing it consumes is locked and
    # it reads the no-unlock sentence. The bound dropped nothing, so it never says capped.
    route = card_for(run_rule(REDESIGN_RULE, balanced))
    assert route is not None
    assert route.tier2 == (
        f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){UNCAPPED_NO_UNLOCK}{_not_chosen(1)}"
    )
    assert _card_read(route, LOCKED_EXTRACTORS) == ()

    sinkable = _inputs(_model(["R_By"]), registry, _request(registry, policy=SINKABLE))
    assert _offered(sinkable, IN_STATUS) == RANKED
    assert _plan_of(_offered(sinkable, IN_PLAN)).byproducts == {SOLVE_RARE_ITEM: Fraction(10)}

    # The control: the drill held makes it raw, so balanced ranks, the Rare at a negative rate.
    supplied = _inputs(_model(["R_By"], extractors=both), registry, _request(registry))
    assert _offered(supplied, IN_STATUS) == RANKED
    assert _plan_of(_offered(supplied, IN_PLAN)).raw_inputs == {
        SOLVE_ORE_ITEM: Fraction(10),
        SOLVE_RARE_ITEM: Fraction(-10),
    }
    assert _offered(supplied, "plan.requires") == (
        f"recipe:{_path('R_By')}",
        ASSEMBLER_KEY,
        MINER_KEY,
    )


def test_a_route_no_cap_cut_never_says_the_capped_search_missed_it() -> None:
    """CS-1382 F1: Ore dug, Rare not, R_By makes Relic and Rare, all held, balanced, Relic.

    The search reads no-plan with nothing dropped, so the no-unlock clause may not name a cap,
    and the trace reads the word the clause rests on. The controls plant what a cap dropped
    beside the same route: the route's own stage, or two held recipes it never runs, and the clause
    names the cap and the count either way.
    """
    registry = _two_raw_registry(
        [_recipe("R_By", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM])]
    )
    world = _inputs(_model(["R_By"]), registry, _request(registry))
    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, "plan.trimmed") == ()

    route = card_for(run_rule(REDESIGN_RULE, world))

    assert route is not None
    capped = "held recipe(s) to fit its cap" in route.tier2
    assert not capped
    assert route.tier2 == (
        f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){UNCAPPED_NO_UNLOCK}{_not_chosen(1)}"
    )
    assert _card_read(route, "plan.trimmed") == ()

    planted = _with_value(world, "plan.trimmed", ("R_By",))
    control = card_for(run_rule(REDESIGN_RULE, planted))
    assert control is not None
    assert control.tier2 == f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){NO_UNLOCK}{_not_chosen(1)}"

    # F1's world holding two more recipes beside R_By, so the planted trim names recipes it holds.
    beside_registry, beside_held = _by_world_beside(2)
    beside_model = _model(beside_held)
    beside = _inputs(beside_model, beside_registry, _request(beside_registry))
    assert _offered(beside, IN_STATUS) == NO_PLAN
    assert _offered(beside, "plan.trimmed") == ()
    dropped = beside_held[1:]
    held_all = all(_path(name) in beside_model.unlocks.recipes for name in dropped)
    assert held_all
    two = _with_value(beside, "plan.trimmed", dropped)
    elsewhere = card_for(run_rule(REDESIGN_RULE, two))
    assert elsewhere is not None
    assert elsewhere.tier2 == (
        f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){_capped_no_unlock(2)}{_not_chosen(1)}"
    )


#: What ties the miss to a cause: a causal word ("because", "caused"), or the search named by
#: its cap, which makes the cap the reason it missed. Neither shipped no-unlock clause holds one.
_CAUSAL_PHRASES: Final = ("cause", "due to", "owing to", "capped search")
#: The no-unlock clause before the CS-1382 F1 repair, on every route with nothing locked.
OLD_CAUSAL_NO_UNLOCK: Final = "; this route needs no unlock and the capped search did not find it"


def _claims_a_cause(tier2: str) -> bool:
    """Whether a tier 2 gives a cause for the miss, which the no-unlock clause never may.

    It reads the link, never the miss alone: both shipped clauses say the search found no route
    within its cap or did not find it, and read False, while the old wording "the capped search
    did not find it" names the search by its cap and reads True.
    """
    return any(phrase in tier2 for phrase in _CAUSAL_PHRASES)


def test_the_cause_reader_reads_the_link_not_the_miss() -> None:
    """CS-1382: the reader the cap-cut arms lean on, on both shipped clauses and the old one.

    False on the capped clause at either count and on the uncapped one, each in its full tier 2,
    and True on the old causal clause, so an arm calling it goes red on a clause blaming the cap.
    """
    old = f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){OLD_CAUSAL_NO_UNLOCK}{_not_chosen(1)}"
    old_blames = _claims_a_cause(old)
    assert old_blames
    for clause in (NO_UNLOCK, _capped_no_unlock(2), UNCAPPED_NO_UNLOCK):
        tier2 = f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){clause}{_not_chosen(1)}"
        blames = _claims_a_cause(tier2)
        assert not blames


def _by_world_beside(extra: int) -> tuple[Registry, tuple[str, ...]]:
    """F1's world and this many more held recipes, each eating Ore into an item nothing eats.

    Args:
        extra: How many recipes stand beside R_By.

    Returns:
        The registry, and every recipe held, R_By first and then registry order. None but R_By
        is a stage of the route to Relic.
    """
    made = [_item(f"X{index:02d}") for index in range(extra)]
    beside = [f"R_X{index:02d}" for index in range(extra)]
    entries = [_recipe("R_By", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM])]
    entries += [
        _recipe(name, [SOLVE_ORE_ITEM], [item]) for name, item in zip(beside, made, strict=True)
    ]
    return _two_raw_registry(entries, items=made), ("R_By", *beside)


def test_a_cap_cut_beside_the_route_reads_the_cap_as_a_fact() -> None:
    """CS-1382, the first adversary's world: F1's world beside 12 unrelated recipes, 13 held.

    The bound keeps R_By, the route's one stage, and drops the last unrelated recipe. The clause
    names the cap and how many it dropped, 1, which is true, and claims no cause: the control
    holds the drill, and the same world ranks under the same trim, so the cap was not the cause
    here and a clause blaming it would be false.
    """
    registry, held = _by_world_beside(MAX_EXHAUSTIVE_CANDIDATES)
    count = len(held)
    assert count == MAX_EXHAUSTIVE_CANDIDATES + 1
    world = _inputs(_model(held), registry, _request(registry))
    assert _offered(world, IN_STATUS) == NO_PLAN
    dropped = held[-1]
    assert _offered(world, "plan.trimmed") == (dropped,)
    assert _offered(world, IN_REDESIGN_HELD) == ("R_By",)

    route = card_for(run_rule(REDESIGN_RULE, world))

    assert route is not None
    assert route.tier2 == f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){NO_UNLOCK}{_not_chosen(1)}"
    blames = _claims_a_cause(route.tier2)
    assert not blames
    assert _card_read(route, "plan.trimmed") == (dropped,)
    read = f'Read plan.trimmed = ("{dropped}") from solve.bound.trim_record.removed'
    shown = read in route.tier3
    assert shown

    both = (SOLVE_MINER_BUILDING, DRILL_BUILDING)
    supplied = _inputs(_model(held, extractors=both), registry, _request(registry))
    assert _offered(supplied, IN_STATUS) == RANKED
    assert _offered(supplied, "plan.trimmed") == (dropped,)


def _world_k(by_count: int) -> tuple[Registry, tuple[str, ...]]:
    """This many recipes making Relic with a Rare over, then R_Alt making Relic alone, last.

    Args:
        by_count: How many byproduct recipes come first.

    Returns:
        The registry, and every recipe, in registry order.
    """
    names = [f"R_By{index:02d}" for index in range(by_count)]
    entries = [
        _recipe(name, [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM]) for name in names
    ]
    entries.append(_recipe("R_Alt", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]))
    return _two_raw_registry(entries), (*names, "R_Alt")


def test_a_cap_cut_off_the_plan_reads_the_same_fact() -> None:
    """CS-1382, the second adversary's world K: 12 byproduct recipes, then R_Alt, 13 held.

    The bound drops R_Alt, the one recipe that ranks under balanced, and keeps R_By00, the
    route's one stage. The clause names the cap and how many it dropped, 1, as beside the
    first adversary's world, and claims no cause: the controls rank with 12 held and with R_Alt
    alone, so the cap was the cause here and a clause denying it would be false.
    """
    registry, held = _world_k(MAX_EXHAUSTIVE_CANDIDATES)
    count = len(held)
    assert count == MAX_EXHAUSTIVE_CANDIDATES + 1
    world = _inputs(_model(held), registry, _request(registry))
    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, "plan.trimmed") == ("R_Alt",)
    assert _offered(world, IN_REDESIGN_HELD) == ("R_By00",)

    route = card_for(run_rule(REDESIGN_RULE, world))

    assert route is not None
    assert route.tier2 == f"{ROUTE_RUNS} 0 locked and 1 held recipe(s){NO_UNLOCK}{_not_chosen(1)}"
    blames = _claims_a_cause(route.tier2)
    assert not blames
    assert _card_read(route, "plan.trimmed") == ("R_Alt",)

    fewer_registry, fewer = _world_k(MAX_EXHAUSTIVE_CANDIDATES - 1)
    within = _inputs(_model(fewer), fewer_registry, _request(fewer_registry))
    assert _offered(within, IN_STATUS) == RANKED
    assert _offered(within, "plan.trimmed") == ()
    alone = _inputs(_model(["R_Alt"]), registry, _request(registry))
    assert _offered(alone, IN_STATUS) == RANKED


def test_a_cap_cut_into_the_route_reads_the_same_fact() -> None:
    """The chain one past the cap, all held, from the planner and no plant.

    The bound drops a stage the route runs, read off the trim and the route's held list the
    planner offers, and the clause says what it says beside the two worlds above: the cap and
    the count, and no cause.
    """
    registry = _chain_registry()
    world = _inputs(_model(_chain_names()), registry, _request(registry))
    assert _offered(world, IN_STATUS) == NO_PLAN
    trimmed = _offered(world, "plan.trimmed")
    held = _offered(world, IN_REDESIGN_HELD)
    assert isinstance(trimmed, tuple)
    assert isinstance(held, tuple)
    cut = sum(1 for name in trimmed if name in held)
    assert cut == 1

    route = card_for(run_rule(REDESIGN_RULE, world))

    assert route is not None
    assert route.tier2 == (
        f"{ROUTE_RUNS} 0 locked and {CHAIN_STAGES} held recipe(s)"
        f"{NO_UNLOCK}{_not_chosen(CHAIN_STAGES)}"
    )
    blames = _claims_a_cause(route.tier2)
    assert not blames


def test_the_no_plan_reason_says_what_the_search_started_from() -> None:
    """The exact sentence, spelled here and read off the offer the rule reads it from."""
    registry = _one_recipe_registry()
    world = _inputs(_model(["R_Direct"], extractors=()), registry, _request(registry))

    trace = run_rule(plan_rules.ADOPT_RULE, world)

    recorded = [step.reason for step in trace.steps if step.kind is StepKind.VERDICT_INDETERMINATE]
    assert recorded == [
        "the search found no plan over the unlocked automated recipes it kept,"
        " from the raw items a held extractor supplies, under the stated byproduct policy"
    ]


#: A path the engine's text test refuses, spelled in escapes so this file stays ASCII.
_ACCENTED_PATH: Final = "/Game/FactoryGame/Synthetic/Placed/Gun_\u00e9.Gun_\u00e9_C"


def _accented(entry: Mapping[str, str]) -> dict[str, str]:
    """The same recipe entry at :data:`_ACCENTED_PATH`."""
    return {**entry, KEY_FULL_NAME: f"BlueprintGeneratedClass {_ACCENTED_PATH}"}


def _holding_the_accented_path(held: Iterable[str]) -> WorldModel:
    """A world holding these recipes, every machine, the miner and the accented path too."""
    model = _model(held)
    state = dataclasses.replace(model.unlocks, recipes=model.unlocks.recipes | {_ACCENTED_PATH})
    return dataclasses.replace(model, unlocks=state)


def _no_rule_errors(world: WorldInputs) -> list[str]:
    """Every rule error either plan rule records over a world, and no card may hide one."""
    return [error for rule in plan_rules.RULES for error in _errors(run_rule(rule, world))]


def test_a_non_ascii_extractor_path_reads_raw_unknown_with_no_rule_error() -> None:
    """No requires key can carry the path, so the machine joins nothing and the item is flagged."""
    registry = _registry(
        [_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])],
        extractor_builds=(_accented(machine_build_entry(SOLVE_MINER_BUILDING)),),
    )

    world = _inputs(_holding_the_accented_path(["R_Direct"]), registry, _request(registry))

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, RAW_UNKNOWN) == (SOLVE_ORE_ITEM,)
    assert _offered(world, IN_REDESIGN_STATUS) == NO_ROUTE
    assert _no_rule_errors(world) == []


def test_a_non_ascii_machine_path_reads_unchecked_with_no_rule_error() -> None:
    """The same path on the machine a recipe runs on: no key, so that recipe cannot be checked."""
    builds = tuple(
        _accented(machine_build_entry(name)) if name == SOLVE_ASSEMBLER_BUILDING else entry
        for name, entry in zip(SOLVE_BUILDINGS, MACHINE_BUILD_ENTRIES, strict=True)
    )
    registry = _registry([_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])], builds=builds)

    world = _inputs(_holding_the_accented_path(["R_Direct"]), registry, _request(registry))

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, IN_UNCHECKED) == ("R_Direct",)
    assert _offered(world, IN_REDESIGN_STATUS) == NO_ROUTE
    assert _no_rule_errors(world) == []


def test_a_non_ascii_recipe_path_reads_unchecked_with_no_rule_error() -> None:
    """A recipe's own path fails the same test, and reads the same way."""
    registry = _registry([_accented(_recipe("R_Direct", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM]))])

    world = _inputs(_holding_the_accented_path(()), registry, _request(registry))

    assert _offered(world, IN_STATUS) == NO_PLAN
    assert _offered(world, IN_UNCHECKED) == ("R_Direct",)
    assert _no_rule_errors(world) == []


def test_the_engine_sees_the_machine_key_on_plan_adopt() -> None:
    """The second gate does not trust the first: the same offer, a world lacking the machine."""
    registry = _one_recipe_registry()
    world = _inputs(_model(["R_Direct"]), registry, _request(registry))
    # The control: the offer as built fires, over the world it was built for.
    assert run_rule(plan_rules.ADOPT_RULE, world).recommendation is not None

    bare = WorldInputs(values=world.values, unlocks=world.unlocks - {ASSEMBLER_KEY})
    trace = run_rule(plan_rules.ADOPT_RULE, bare)

    assert trace.recommendation is None
    assert card_for(trace) is None
    assert trace.unmet == (ASSEMBLER_KEY,)
    last = trace.steps[-1].kind
    assert last is StepKind.PRECONDITION_UNMET


def test_the_engine_sees_the_machine_key_on_plan_redesign() -> None:
    registry = _chain_registry()
    world = _inputs(_model(_chain_names()), registry, _request(registry))
    # The control: the offer as built fires, over the world it was built for.
    assert run_rule(REDESIGN_RULE, world).recommendation is not None

    bare = WorldInputs(values=world.values, unlocks=world.unlocks - {ASSEMBLER_KEY})
    trace = run_rule(REDESIGN_RULE, bare)

    assert trace.recommendation is None
    assert card_for(trace) is None
    assert trace.unmet == (ASSEMBLER_KEY,)
    last = trace.steps[-1].kind
    assert last is StepKind.PRECONDITION_UNMET


def test_a_machine_locked_recipe_cannot_tie_a_route_that_runs_now() -> None:
    """By hand: R_Short counts (1, 1), machine locked, and the held chain (0, 13) beats it.

    Held by its recipe path alone, R_Short would count (0, 1) and take the route: the player
    would read a route needing an unlock where one that runs now exists.
    """
    short = _recipe(
        "R_Short", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM], buildings=(SOLVE_SMELTER_BUILDING,)
    )
    registry = _chain_registry(short)
    names = _chain_names()
    world = _inputs(
        _model((*names, "R_Short"), machines=[SOLVE_ASSEMBLER_BUILDING]),
        registry,
        _request(registry),
    )
    assert _offered(world, IN_STATUS) == NO_PLAN

    card = card_for(run_rule(REDESIGN_RULE, world))

    assert card is not None
    assert [stage for stage, _machine_count in _machines(card)] == list(names)
    assert _card_read(card, IN_REDESIGN_LOCKED) == ()
    assert card.tier2 == f"{ROUTE_RUNS} 0 locked and 13 held recipe(s){NO_UNLOCK}{_not_chosen(13)}"
    uncovered = len(set(_requires(card)) - world.unlocks)
    assert uncovered == 0

    # The control: with its machine held R_Short ranks, so the machine alone decided above.
    ranked = _inputs(
        _model((*names, "R_Short"), machines=SOLVE_BUILDINGS), registry, _request(registry)
    )
    assert _offered(ranked, IN_STATUS) == RANKED
    plan = _plan_of(_offered(ranked, IN_PLAN))
    assert [step.recipe_key for step in plan.steps] == ["R_Short"]


def test_the_machine_join_is_the_whole_path_never_its_trailing_token() -> None:
    """A path sharing only the trailing token is another asset, and holds no machine (CS-1343)."""
    real = machine_build_path(SOLVE_ASSEMBLER_BUILDING)
    elsewhere = real.replace("/Placed/", "/Elsewhere/")
    assert elsewhere != real
    assert elsewhere.rpartition(".")[2] == real.rpartition(".")[2]
    registry = _one_recipe_registry()
    held = dataclasses.replace(
        EMPTY_UNLOCK_STATE, recipes=frozenset({_path("R_Direct"), elsewhere, MINER_BUILD_PATH})
    )

    offered = plan_offer(held, registry, _request(registry))

    assert offered[IN_STATUS].value == NO_PLAN
    assert offered[IN_REDESIGN_LOCKED].value == ("R_Direct",)
    assert offered["plan.unmatched_unlocks"].value == 1

    # The control: the whole string joins, and a machine's path is no unmatched path.
    whole = dataclasses.replace(
        EMPTY_UNLOCK_STATE, recipes=frozenset({_path("R_Direct"), real, MINER_BUILD_PATH})
    )
    joined = plan_offer(whole, registry, _request(registry))
    assert joined[IN_STATUS].value == RANKED
    assert joined["plan.unmatched_unlocks"].value == 0


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
    # What the route was asked over: every automated recipe the join could check, by hand, in
    # registry order, so no machine's build recipe, which the registry also holds.
    every_stage = ("R_B4", "R_B3", "R_B2", "R_B1", "R_A1", "R_A2", "R_A3", "R_A4")
    (args,) = calls["derived_route"]
    asked = args[1]
    assert asked.candidates == every_stage
    assert asked.unlocked == every_stage
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
        status=RANKED,
        reason=None,
        redesign=NOT_REACHED,
        redesign_reason=None,
        trimmed=(),
        unmade=None,
        raw_unknown=(),
    )


def test_a_no_plan_outcome_reads_its_reason_scoped_to_the_kept_set_and_the_trim() -> None:
    registry = _chain_registry()
    outcome = _outcome(_chain_names(), registry, _request(registry))
    assert outcome == PlanOutcome(
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=ROUTED,
        redesign_reason=None,
        trimmed=(_stage_name(1),),
        unmade=None,
        raw_unknown=(),
    )


def test_a_no_route_outcome_names_the_item_nothing_makes() -> None:
    registry = _orphan_registry()
    outcome = _outcome((), registry, _request(registry))
    assert outcome == PlanOutcome(
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=NO_ROUTE,
        redesign_reason=NO_ROUTE_REASON,
        trimmed=(),
        unmade=(SOLVE_ORPHAN_ITEM,),
        raw_unknown=(),
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
        redesign_reason=ROUTE_REFUSED_REASON,
        trimmed=(),
        unmade=None,
        raw_unknown=(),
    )
    assert card_for(_route_trace((), registry, _request(registry, policy=BALANCED))) is None

    # The same request under the other policy fires.
    card = _route_card((), registry, _request(registry, policy=SINKABLE))
    assert card.tier1 == f"Plan toward {RELIC_LABEL}"
    plan = _plan_of(_card_read(card, IN_REDESIGN_PLAN))
    assert plan.byproducts == {SOLVE_RARE_ITEM: Fraction(10)}


# ---------------------------------------------------------------------------
# CS-1378: a balanced route pillar 1 refuses gets one consumer per leftover byproduct
# ---------------------------------------------------------------------------

#: 20 Relic a minute: R_By and one consumer share it, one machine each, by the hand work below.
CONSUMER_RATE: Final = "20"

#: The consumer step's own door out of ``plans.py``.
CONSUMER_DOOR: Final = "route_with_consumers"


def _by_entry() -> dict[str, str]:
    """R_By makes Relic and, beside it, a Rare nothing on the route eats."""
    return _recipe("R_By", [SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM, SOLVE_RARE_ITEM])


def _eats_rare(
    name: str, *, also: str = SOLVE_ORE_ITEM, makes: str = SOLVE_RELIC_ITEM, pathless: bool = False
) -> dict[str, str]:
    """A recipe eating one Rare and one more item, and making one of an item."""
    return _recipe(name, [SOLVE_RARE_ITEM, also], [makes], pathless=pathless)


def _consumer_request(registry: Registry, *, policy: str = BALANCED) -> PlanRequest:
    """The request every arm below asks, at :data:`CONSUMER_RATE`."""
    return _request(registry, rate=CONSUMER_RATE, policy=policy)


def _consumer_outcome(held: Iterable[str], registry: Registry) -> PlanOutcome:
    """The projection of one world's offer under the balanced policy."""
    return _outcome(held, registry, _consumer_request(registry))


def _consumer_card(held: Iterable[str], registry: Registry, *, policy: str = BALANCED) -> Card:
    """The plan.redesign card of one world, which must fire."""
    return _route_card(held, registry, _consumer_request(registry, policy=policy))


def _stage_machines(card: Card) -> dict[str, Fraction]:
    """Each stage of a card's plan with its machine count, read by recipe."""
    return dict(_machines(card))


def test_a_byproduct_a_recipe_off_the_route_eats_reads_a_route_card_with_its_count() -> None:
    """A byproduct a recipe off the route eats reads a route card with its count.

    By hand: R_By makes 10 Relic and 10 Rare per machine, R_Use eats 10 Rare and 10 Ore and
    makes 10 Relic. Rare: 10 x = 10 y, Relic: 10 x + 10 y = 20, so x = y = 1.

    R_Use is held and R_By is not, so no ranked plan exists and the route path runs. At
    CS-1371 the Rare left a row nothing cancelled and the route read route-refused.
    """
    registry = _registry([_by_entry(), _eats_rare("R_Use")])

    outcome = _consumer_outcome(("R_Use",), registry)
    card = _consumer_card(("R_Use",), registry)

    assert outcome.status == NO_PLAN
    assert outcome.redesign == ROUTED
    assert _stage_machines(card) == {"R_By": Fraction(1), "R_Use": Fraction(1)}
    assert 'PlanStep(recipe_key="R_Use", machines=1.00)' in card.tier3
    assert _card_read(card, IN_REDESIGN_HELD) == ("R_Use",)
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_By",)


def test_of_two_qualifying_consumers_the_lower_count_wins_though_later_in_registry_order() -> None:
    """By hand: R_Dear also eats Rod, made by R_MakeRod, so it counts 2 against R_Cheap's 1.

    R_Dear is declared first, so plain registry order would take it and run R_MakeRod too.
    """
    registry = _registry(
        [
            _by_entry(),
            _eats_rare("R_Dear", also=SOLVE_ROD_ITEM),
            _recipe("R_MakeRod", [SOLVE_ORE_ITEM], [SOLVE_ROD_ITEM]),
            _eats_rare("R_Cheap"),
        ]
    )

    card = _consumer_card(("R_By",), registry)

    assert _stage_machines(card) == {"R_By": Fraction(1), "R_Cheap": Fraction(1)}


@pytest.mark.parametrize(
    ("declared", "chosen"),
    [
        pytest.param(("R_TieA", "R_TieB"), "R_TieA", id="name-order"),
        pytest.param(("R_TieB", "R_TieA"), "R_TieB", id="against-name-order"),
    ],
)
def test_a_count_tie_between_consumers_goes_to_the_earlier_in_the_registry(
    declared: tuple[str, str], chosen: str
) -> None:
    """Both count 1, so only registry position decides, and the two params swap it."""
    registry = _registry([_by_entry(), *(_eats_rare(name) for name in declared)])

    card = _consumer_card(("R_By",), registry)

    assert _stage_machines(card) == {"R_By": Fraction(1), chosen: Fraction(1)}


def test_a_locked_consumer_is_admitted_and_offered_locked() -> None:
    """A locked consumer is admitted and offered locked.

    The pool is the join's checked recipes, held or not, so a consumer the world has not
    unlocked is offered as a locked stage beside the held producer.
    """
    registry = _registry([_by_entry(), _eats_rare("R_Use")])

    card = _consumer_card(("R_By",), registry)

    assert _card_read(card, IN_REDESIGN_HELD) == ("R_By",)
    assert _card_read(card, IN_REDESIGN_LOCKED) == ("R_Use",)
    assert _stage_machines(card) == {"R_By": Fraction(1), "R_Use": Fraction(1)}


def test_a_byproduct_nothing_eats_still_reads_route_refused_beside_a_recipe_that_could_not() -> (
    None
):
    """The fence: R_Decoy eats Plate, never Rare, so no recipe consumes the leftover.

    The control is the same world with a real consumer, which routes.
    """
    decoy = _recipe("R_Decoy", [SOLVE_PLATE_ITEM, SOLVE_ORE_ITEM], [SOLVE_RELIC_ITEM])
    refused = _registry([_by_entry(), decoy])
    routed = _registry([_by_entry(), decoy, _eats_rare("R_Use")])

    assert _consumer_outcome(("R_By",), refused).redesign == ROUTE_REFUSED
    assert _consumer_outcome(("R_By",), routed).redesign == ROUTED


def test_a_consumer_whose_output_only_a_second_recipe_eats_still_reads_route_refused() -> None:
    """A consumer's own leftover is never chased.

    The fence, one hop: R_Turn makes Twin from Rare, and only R_Chase eats Twin. The Twin is
    the consumer's own leftover and is never chased, so the second solve is refused as the
    first was.
    """
    registry = _registry(
        [
            _by_entry(),
            _eats_rare("R_Turn", makes=SOLVE_TWIN_ITEM),
            _recipe("R_Chase", [SOLVE_TWIN_ITEM], [SOLVE_RELIC_ITEM]),
        ]
    )

    assert _consumer_outcome(("R_By",), registry).redesign == ROUTE_REFUSED


def test_an_unchecked_consumer_is_never_picked() -> None:
    """An unchecked consumer is never picked.

    The fence: the pool is the join's checked recipes. R_Use has no path, so nothing could
    show it held, and it is named unchecked and kept off the route. The control gives it one.
    """
    registry = _registry([_by_entry(), _eats_rare("R_Use", pathless=True)])
    checked = _registry([_by_entry(), _eats_rare("R_Use")])

    refused = _consumer_outcome(("R_By",), registry)

    assert refused.redesign == ROUTE_REFUSED
    assert _consumer_outcome(("R_By",), checked).redesign == ROUTED


def test_under_sinkable_the_byproduct_sinks_and_no_consumer_runs() -> None:
    """The fence: the policy sinks the Rare, so the first solve stands and R_Use stays off."""
    registry = _registry([_by_entry(), _eats_rare("R_Use")])

    card = _consumer_card((), registry, policy=SINKABLE)

    assert _stage_machines(card) == {"R_By": Fraction(2)}
    assert _plan_of(_card_read(card, IN_REDESIGN_PLAN)).byproducts == {
        SOLVE_RARE_ITEM: Fraction(20)
    }


def _spy_on_the_consumer_step(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Any, ...]]:
    """Record each call into the consumer step and pass it through."""
    calls: list[tuple[Any, ...]] = []
    real = plans_module.route_with_consumers

    def recording(*args: Any, **kwargs: Any) -> Any:
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(plans_module, CONSUMER_DOOR, recording)
    return calls


def test_a_route_solved_first_try_never_reaches_the_consumer_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three first-try worlds, then the control on which the spy does see a call."""
    calls = _spy_on_the_consumer_step(monkeypatch)
    consumer = _registry([_by_entry(), _eats_rare("R_Use")])
    three = _three_locked_registry()

    plan_offer(_unlocks(()), consumer, _consumer_request(consumer, policy=SINKABLE))
    plan_offer(_unlocks([HELD_STAGE]), three, _request(three))
    plan_offer(
        _unlocks(("R_Two", "R_Direct", "R_One")), _ascent_registry(), _request(_ascent_registry())
    )
    assert calls == []

    plan_offer(_unlocks(("R_By",)), consumer, _consumer_request(consumer))
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("policy", "reached"), [(SINKABLE, 0), (BALANCED, 1)], ids=[SINKABLE, BALANCED]
)
def test_a_refusal_reaches_the_consumer_step_under_the_balanced_policy_alone(
    monkeypatch: pytest.MonkeyPatch, policy: str, reached: int
) -> None:
    """The step is for a balanced refusal, so the same refusal under sinkable stops there.

    A solve stood in for with a refusal, so the policy is the one thing that differs. Both
    read route-refused, and only the balanced one runs the step.
    """
    calls = _spy_on_the_consumer_step(monkeypatch)

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise RatioError(MARK)

    monkeypatch.setattr(plans_module, "solve_for_targets", refuse)
    registry = _registry([_by_entry(), _eats_rare("R_Use")])

    outcome = plan_outcome_of(
        plan_offer(_unlocks(()), registry, _consumer_request(registry, policy=policy))
    )

    assert outcome.redesign == ROUTE_REFUSED
    assert len(calls) == reached


def test_a_refusal_from_the_consumer_step_reads_route_refused_and_echoes_nothing() -> None:
    """The consumer step's own refusal reads route-refused and echoes nothing.

    The step's own refusal, raised for real: nothing eats the Rare. Neither the status the
    rule reads nor anything the trace renders holds an item or a recipe key.
    """
    registry = _registry([_by_entry(), _recipe("R_Decoy", [SOLVE_PLATE_ITEM], [SOLVE_RELIC_ITEM])])
    world = _inputs(_model(("R_By",)), registry, _consumer_request(registry))

    trace = run_rule(REDESIGN_RULE, world)

    assert _offered(world, IN_REDESIGN_STATUS) == ROUTE_REFUSED
    assert card_for(trace) is None
    assert _indeterminate_count(trace) == 1
    assert _errors(trace) == []
    rendered = _rendered(trace)
    named = [
        key for key in ("R_By", "R_Decoy", SOLVE_RARE_ITEM, SOLVE_PLATE_ITEM) if key in rendered
    ]
    assert named == []


@pytest.mark.parametrize(
    ("status", "sentence"),
    [(NO_ROUTE, NO_ROUTE_REASON), (ROUTE_REFUSED, ROUTE_REFUSED_REASON)],
    ids=[NO_ROUTE, ROUTE_REFUSED],
)
def test_the_outcome_reads_the_one_sentence_the_trace_records(status: str, sentence: str) -> None:
    """A surface reads the sentence the rule records, so the wire and the trace cannot differ."""
    world = _worlds_per_status()[status]
    assert _offered(world, IN_REDESIGN_STATUS) == status

    trace = run_rule(REDESIGN_RULE, world)

    recorded = [step.reason for step in trace.steps if step.kind is StepKind.VERDICT_INDETERMINATE]
    assert recorded == [sentence]
    assert plan_outcome_of(world.values).redesign_reason == sentence


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

#: The route path's doors. The last is reached only once pillar 1 refuses the route under the
#: balanced policy, so its arms take the fixture that does.
ROUTE_DOORS: Final = ("derived_route", "solve_for_targets", "route_with_consumers")


def _door_registry(door: str) -> Registry:
    """The world whose route path reaches this door: the routable one, or one pillar 1 refuses."""
    return _byproduct_registry() if door == "route_with_consumers" else _ascent_registry()


@pytest.mark.parametrize("door", ROUTE_DOORS)
@pytest.mark.parametrize("refusal", sorted(ROUTE_REFUSALS))
def test_each_refusal_on_the_route_path_reads_route_refused_and_echoes_nothing(
    monkeypatch: pytest.MonkeyPatch, door: str, refusal: str
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> object:
        raise ROUTE_REFUSALS[refusal]()

    monkeypatch.setattr(plans_module, door, refuse)
    registry = _door_registry(door)
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
    registry = _door_registry(door)
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
    assert plan_outcome_of(offered).redesign_reason is None
    assert plan_outcome_of(offered).trimmed is None
    assert plan_outcome_of(offered).unmade is None
    assert plan_outcome_of(offered).raw_unknown is None


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
        status=MALFORMED,
        reason=MALFORMED_REASON,
        redesign=NOT_REACHED,
        redesign_reason=None,
        trimmed=None,
        unmade=None,
        raw_unknown=None,
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
        status=NO_PLAN,
        reason=NO_PLAN_REASON,
        redesign=ROUTED,
        redesign_reason=None,
        trimmed=(),
        unmade=None,
        raw_unknown=(),
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
        "plan.redesign.locked_extractors",
        "plan.redesign.requires",
        "plan.redesign.unmade",
        "plan.redesign.target_names",
        "plan.redesign.unlocks",
        "plan.redesign.built",
    )


def test_each_redesign_input_names_the_field_it_came_from() -> None:
    world = _worlds_per_status()[ROUTED]
    sources = {name: _source_of(world, name) for name in REDESIGN_INPUTS}
    assert sources == {
        IN_REDESIGN_STATUS: "advisor.plans.redesign.status",
        IN_REDESIGN_PLAN: "solve.ratio.solve_for_targets",
        IN_REDESIGN_HELD: "advisor.plans.redesign.held",
        IN_REDESIGN_LOCKED: "advisor.plans.redesign.locked",
        LOCKED_EXTRACTORS: "advisor.plans.redesign.locked_extractors",
        IN_REDESIGN_REQUIRES: "advisor.plans.redesign.recipe_unlock_join",
        IN_REDESIGN_UNMADE: "solve.bound.derived_route.unmade",
        IN_REDESIGN_TARGET_NAMES: "registry.items.display_name",
        IN_REDESIGN_UNLOCKS: "advisor.plans.redesign.schematic_unlock_join",
        IN_REDESIGN_BUILT: "advisor.plans.redesign.built_comparison",
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
        ({LOCKED_EXTRACTORS: None}, "TypeError"),
        ({LOCKED_EXTRACTORS: SOLVE_MINER_BUILDING}, "TypeError"),
        ({IN_REDESIGN_REQUIRES: None}, "TypeError"),
        ({IN_REDESIGN_UNMADE: ()}, "TypeError"),
        ({IN_UNCHECKED: None}, "TypeError"),
        ({RAW_UNKNOWN: None}, "TypeError"),
        ({IN_REDESIGN_TARGET_NAMES: None}, "TypeError"),
        ({IN_REDESIGN_TARGET_NAMES: (RELIC_NAME,)}, "TypeError"),
        ({IN_REDESIGN_TARGET_NAMES: MappingProxyType({})}, "ValueError"),
        (
            {
                IN_REDESIGN_TARGET_NAMES: MappingProxyType(
                    {SOLVE_RELIC_ITEM: RELIC_NAME, SOLVE_ROD_ITEM: ROD_NAME}
                )
            },
            "ValueError",
        ),
        ({IN_REDESIGN_TARGET_NAMES: MappingProxyType({SOLVE_ROD_ITEM: ROD_NAME})}, "ValueError"),
        (
            {IN_REDESIGN_TARGET_NAMES: MappingProxyType({SOLVE_RELIC_ITEM: Fraction(1)})},
            "TypeError",
        ),
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
        "locked-extractors-none",
        "locked-extractors-not-a-tuple",
        "requires-none",
        "unmade-on-routed",
        "unchecked-none",
        "raw-unknown-none",
        "names-none",
        "names-not-a-mapping",
        "names-lack-the-target",
        "names-hold-another-target",
        "names-hold-another-target-alone",
        "name-not-text",
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


@pytest.mark.parametrize("status", [NOT_REACHED, NO_ROUTE, ROUTE_REFUSED])
def test_a_status_with_no_route_offers_no_names_and_refuses_any(status: str) -> None:
    world = _worlds_per_status()[status]
    assert _offered(world, IN_REDESIGN_TARGET_NAMES) is None
    assert _errors(run_rule(REDESIGN_RULE, world)) == []

    named = MappingProxyType({SOLVE_RELIC_ITEM: RELIC_NAME})
    trace = run_rule(REDESIGN_RULE, _with_value(world, IN_REDESIGN_TARGET_NAMES, named))

    assert _errors(trace) == ["TypeError"]


@pytest.mark.parametrize("status", [NOT_REACHED, NO_ROUTE, ROUTE_REFUSED])
def test_a_status_with_no_route_offers_no_locked_extractors_and_refuses_any(status: str) -> None:
    world = _worlds_per_status()[status]
    assert _offered(world, LOCKED_EXTRACTORS) is None
    assert _errors(run_rule(REDESIGN_RULE, world)) == []

    planted = (SOLVE_MINER_BUILDING,)
    trace = run_rule(REDESIGN_RULE, _with_value(world, LOCKED_EXTRACTORS, planted))

    assert _errors(trace) == ["TypeError"]


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
    held = _unlocks([HELD_STAGE])
    state = dataclasses.replace(held, recipes=held.recipes | {SAVE_ONLY_PATH})
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
