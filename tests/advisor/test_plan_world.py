"""CS-1351: advise_world ranks a plan for a stated target, and plan.adopt fires on it.

Graded here, against CS-1351's acceptance in ``docs/item_notes/phase5.md``:

- :func:`clockspeed.advisor.advise.advise_world` ranks a plan for a synthetic
  fixture world and ``plan.adopt`` fires on it, its
  :class:`clockspeed.solve.strategy.StrategyBadge` reaching the tier-3 derivation
  of a real card that call returned;
- the unlock keys the plan's recipes need are filled by the recipe-to-unlock
  join, never supplied by hand;
- the plan family is registered in ``clockspeed/advisor/rules/__init__.py::_FAMILIES``.

THE FIXTURE IS THE ASCENT SHAPE OF ``tests/solve/test_bound.py``, defined here
from ``tests/solve/synthetic.py``, each entry carrying a FullName whose path half
does NOT derive from its ClassName, so a join rebuilt from a name cannot pass.
Every assembler cycle is six seconds, ten cycles a minute, 15 MW a machine. Worked
by hand at 10 Relic a minute:

- two stages, R_B1Relic (1 Rare to 1 Relic) and R_B3Rare (1 Ore to 1 Rare): one
  machine each, so 10 Ore a minute, 2 machines, 30 MW;
- one stage, R_B2Direct (6 Ore to 1 Relic): one machine, so 60 Ore a minute,
  1 machine, 15 MW.

So under raw the top plan is the two stages, and each rung's own optimum is 10
Ore, 1 machine and 15 MW: the badge clears within-raw and nothing else. Those
figures are literals below. They are never read back from ``optimize_plan``,
because the plan and its references share that door.

THE COMMON-MODE RISK, STATED. Every synthetic arm builds a FullName and an unlock
path from one string, so it would pass even if real paths never matched. Only
:func:`test_the_join_holds_on_a_library_world` grades that, on a real save and the
installed docs, and it skips where either is absent. It prints and asserts counts
only: nothing from a save reaches its assertion, and its helpers hand back ints.

Every other world here is synthetic, hand-built from invented paths. No save or
install is read by any other arm.

THE REPAIR'S WORLDS, EACH WORKED BY HAND IN ITS OWN DOCSTRING: a route longer than the
cap, which the cap cuts short (:func:`test_a_capped_no_plan_names_what_the_bound_dropped`),
a world where greedy's raw walk dead-ends (:func:`_dead_end_registry`), and one where the
buildings and power optima are different plans (:func:`_crossed_optima_registry`).
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, NamedTuple

import pytest

from clockspeed.advisor import plans as plans_module
from clockspeed.advisor import rules as rules_module
from clockspeed.advisor.advise import (
    Advice,
    advise_and_record,
    advise_world,
    inputs_of,
    settled_rules,
)
from clockspeed.advisor.cards import Card, card_for, render_value
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.plans import PlanRequest, plan_offer
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.advisor.rules import registered_rules
from clockspeed.advisor.trace import (
    InputValue,
    StepKind,
    Trace,
    WorldInputs,
    run_rule,
    unlock_keys,
)
from clockspeed.data import locate, version
from clockspeed.data.registry import (
    WARN_UNRESOLVED_PRODUCED_IN,
    Registry,
    automated_recipes,
    build_cost,
    build_registry,
    build_registry_from_bytes,
)
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    UnlockState,
    WorldModel,
    load_world_from_bytes,
)
from clockspeed.solve.backends import BACKEND_EXHAUSTIVE, BACKEND_GREEDY
from clockspeed.solve.bound import (
    TRIM_ROUTE_FIRST,
    BoundedResult,
    BoundExhaustedError,
    TrimRecord,
    TrimStep,
)
from clockspeed.solve.exact import InexactValueError, UndefinedRateError
from clockspeed.solve.optimize import (
    BACKEND_ENV_VAR,
    MAX_EXHAUSTIVE_CANDIDATES,
    OBJECTIVE_BUILDINGS,
    OBJECTIVE_POWER,
    OBJECTIVE_RAW,
    NoFeasibleSelectionError,
    ObjectiveUndefinedError,
    OptimizeRequest,
    PowerNotComparableError,
    SearchSpaceTooLargeError,
    UnknownBackendError,
    optimize_plan,
    weighted_objective,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    BYPRODUCT_SINKABLE,
    RatioRequest,
    solve_for_targets,
)
from clockspeed.solve.strategy import (
    NOT_CLEARED_OVER_BOUND,
    NOT_CLEARED_UNPRICEABLE,
    RUNG_WITHIN_BUILDINGS,
    RUNG_WITHIN_POWER,
    RUNG_WITHIN_RAW,
    STRATEGY_LADDER,
    StrategyBadge,
    rank_plans,
)
from clockspeed.surface import providers
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, routes
from tests.advisor.build_fixtures import (
    docs_pin,
    game_pin,
    off_pin_build_inputs,
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
    MACHINE_BUILD_PATHS,
    MACHINE_DESCRIPTOR_ENTRIES,
    RECIPE_GROUP,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_ORE_ITEM,
    SOLVE_RARE_ITEM,
    SOLVE_RECIPES,
    SOLVE_RELIC_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_SMELTER_BUILDING,
    building_path,
    document_from_groups,
    machine_build_path,
    registry_with,
)
from tests.surface import test_map as map_fixtures

#: The one rule this file grades, by its stable id.
ADOPT_ID: Final = "plan.adopt"

#: The rule a no-plan offers its route to, which ``tests/advisor/test_plan_redesign.py`` grades.
REDESIGN_ID: Final = "plan.redesign"

#: The closed status vocabulary, spelled here rather than imported from the module
#: under test, so a rename there is red here rather than carried along.
STATUS_RANKED: Final = "ranked"
STATUS_NO_TARGET: Final = "no-target"
STATUS_REQUEST_MALFORMED: Final = "request-malformed"
STATUS_NO_PLAN: Final = "no-plan"
STATUS_SOLVE_REFUSED: Final = "solve-refused"
STATUS_POWER_NOT_COMPARABLE: Final = "power-not-comparable"

#: The instant every resolution here reads. Injected, never a clock.
NOW: Final = 1000

#: Relic a minute, for every target here.
RELIC_RATE: Final = Fraction(10)

#: The hand-worked figures of the module docstring, as literals.
TWO_STAGE_ORE: Final = Fraction(10)
TWO_STAGE_MACHINES: Final = Fraction(2)
TWO_STAGE_MEGAWATTS: Final = Fraction(30)
ONE_STAGE_ORE: Final = Fraction(60)
ONE_STAGE_MACHINES: Final = Fraction(1)
ONE_STAGE_MEGAWATTS: Final = Fraction(15)

#: The two-stage route's Relic recipe, declared first of the three.
RELIC_FROM_RARE: Final = "R_B1Relic"

#: The one-stage route.
RELIC_DIRECT: Final = "R_B2Direct"

#: The two-stage route's first stage, which produces no target.
RARE_FROM_ORE: Final = "R_B3Rare"

#: A second target's only recipe, for the arm whose target moves.
ROD_FROM_ORE: Final = "R_B4Rod"

#: A recipe no building can run: 1 Ore to 2 Relic, cheaper than either route.
NO_PRODUCER: Final = "R_NoProducerRelic"

#: What a raw search pays for 10 Relic when it may use :data:`NO_PRODUCER`.
NO_PRODUCER_ORE: Final = Fraction(5)

#: A recipe whose second product nothing consumes.
BYPRODUCT_RECIPE: Final = "R_By"

#: A direct Relic producer naming two buildings, so it has no exact draw.
UNPRICEABLE_RECIPE: Final = "R_Odd"

#: The three recipes of the world where greedy's raw walk dead-ends.
DEAD_END_A: Final = "R_A"
DEAD_END_B: Final = "R_B"
DEAD_END_C: Final = "R_C"

#: The three recipes of the world whose buildings and power optima differ.
CROSSED_X: Final = "R_X"
CROSSED_Y1: Final = "R_Y1"
CROSSED_Y2: Final = "R_Y2"

#: Each recipe's invented asset path. NONE derives from its ClassName, so a join
#: that rebuilt a path from a name, or matched a trailing token, joins nothing.
PATHS: Final[Mapping[str, str]] = MappingProxyType(
    {
        RELIC_FROM_RARE: "/Game/FactoryGame/Synthetic/Alpha/Stage_Two.Stage_Two_C",
        RELIC_DIRECT: "/Game/FactoryGame/Synthetic/Beta/One_Stage.One_Stage_C",
        RARE_FROM_ORE: "/Game/FactoryGame/Synthetic/Gamma/Stage_One.Stage_One_C",
        ROD_FROM_ORE: "/Game/FactoryGame/Synthetic/Delta/Rod_Maker.Rod_Maker_C",
        NO_PRODUCER: "/Game/FactoryGame/Synthetic/Epsilon/By_Hand.By_Hand_C",
    }
)

#: The unlock key of the one machine every recipe here runs on, which a plan's requires name
#: beside its first recipe. Spelled through the fixture's path, never read back from a plan.
ASSEMBLER_KEY: Final = "recipe:" + machine_build_path(SOLVE_ASSEMBLER_BUILDING)

#: The three recipes of the ascent shape, in registry order.
ASCENT: Final = (RELIC_FROM_RARE, RELIC_DIRECT, RARE_FROM_ORE)

#: The unlock paths that unlock all three.
ASCENT_PATHS: Final = tuple(PATHS[name] for name in ASCENT)

#: The filler recipe names of the trim fixture.
PADDING_PREFIX: Final = "R_Pad"

#: A planted string that may never reach anything a reader sees.
MARK: Final = "cs1351plantedrefusaltext"

#: An unlock path the registry holds no recipe for: a stand-in for a save's own
#: path, which may be counted and may never be echoed.
SAVE_ONLY_PATH: Final = "/Game/Cs1351SaveOnly/Never_Echoed.Never_Echoed_C"

#: What each child of the determinism arm prints. ``-c``, so the working directory
#: is on ``sys.path`` and no argv carries a path; ``tests/solve/test_bound.py``
#: records why ``-I`` and ``-E`` are unusable here.
CHILD_SOURCE: Final = """
from tests.advisor.test_plan_world import rendered_derivation

print(rendered_derivation())
"""

#: The two hash seeds the determinism arm compares.
HASH_SEEDS: Final = ("0", "1")

#: Child process bound. Generous: each child builds a registry and runs a search.
CHILD_TIMEOUT_SECONDS: Final = 300

#: The repository root, each child's working directory.
REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: Reaches the installed docs and the save library, name to what it does. Every
#: one contains what it reaches and hands back counts or a model it never
#: renders; see the module docstring.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_library_registry": "resolves the install and reads the docs file",
        "_library_saves": "resolves the save root and the account directory, and globs",
        "_library_save_unlocks": "reads one save and hands back its unlock state",
        "_library_unlocks": "walks the saves, newest first, until the reader accepts one",
        "_library_join": "composes the three above and hands back counts only",
    }
)


def _entry(
    class_name: str,
    ingredients: list[tuple[str, int]],
    products: list[tuple[str, int]],
    *,
    path: str | None,
    buildings: tuple[str, ...] = (SOLVE_ASSEMBLER_BUILDING,),
) -> dict[str, str]:
    """One recipe entry as docs text, six seconds a cycle.

    Args:
        class_name: The entry's ClassName.
        ingredients: ``(item, verbatim amount)`` pairs.
        products: The product side.
        path: The path half of its FullName, or None to carry no FullName at all.
        buildings: The buildings it names; empty is a recipe no machine runs.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    entry = {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: class_name.removeprefix("R_"),
        KEY_DURATION: "6.000000",
        KEY_INGREDIENTS: amount_blob(ingredients),
        KEY_PRODUCT: amount_blob(products),
        KEY_PRODUCED_IN: class_path_blob([building_path(name) for name in buildings]),
    }
    if path is not None:
        entry[KEY_FULL_NAME] = f"BlueprintGeneratedClass {path}"
    return entry


def _ascent_entries(*, pathless: frozenset[str] = frozenset()) -> list[dict[str, str]]:
    """The three asymmetric recipes of the module docstring.

    Args:
        pathless: The recipes that carry no FullName.

    Returns:
        The entries, in registry order.
    """

    def path(name: str) -> str | None:
        return None if name in pathless else PATHS[name]

    return [
        _entry(
            RELIC_FROM_RARE,
            [(SOLVE_RARE_ITEM, 1)],
            [(SOLVE_RELIC_ITEM, 1)],
            path=path(RELIC_FROM_RARE),
        ),
        _entry(
            RELIC_DIRECT, [(SOLVE_ORE_ITEM, 6)], [(SOLVE_RELIC_ITEM, 1)], path=path(RELIC_DIRECT)
        ),
        _entry(
            RARE_FROM_ORE, [(SOLVE_ORE_ITEM, 1)], [(SOLVE_RARE_ITEM, 1)], path=path(RARE_FROM_ORE)
        ),
    ]


def _registry_of(entries: list[dict[str, str]]) -> Registry:
    """A verified registry holding exactly these recipes.

    The corpus's own recipes are dropped because they carry no FullName, and
    would otherwise fill every arm's unchecked list with recipes it is not about.
    Each machine's build recipe is added, so every recipe here has a machine to check.

    Args:
        entries: The recipe entries.

    Returns:
        The registry, stamped as built from the pinned docs bytes.
    """
    return pinned_source(
        registry_with(add=entries, drop=frozenset(SOLVE_RECIPES), machine_builds=True)
    )


def _registry() -> Registry:
    """The ascent fixture's registry."""
    return _registry_of(_ascent_entries())


def _padded_paths() -> tuple[str, ...]:
    """Every unlock path of the trim fixture."""
    return (*ASCENT_PATHS, *(_pad_path(index) for index in range(_padding_count())))


def _padding_count() -> int:
    """How many fillers put exactly one usable recipe past the cap."""
    return MAX_EXHAUSTIVE_CANDIDATES + 1 - len(ASCENT)


def _pad_path(index: int) -> str:
    """One filler's asset path."""
    return f"/Game/FactoryGame/Synthetic/Filler/Filler_{index}.Filler_{index}_C"


def _padded_registry() -> Registry:
    """The ascent fixture plus enough fillers to pass the cap by one.

    The fillers make Rod, which no walk from Relic reads, so the trim ranks them
    behind all three recipes of the ascent fixture and among themselves by registry
    position: the one it drops is the last filler, by the rule and never by a solve.

    Returns:
        The registry.
    """
    fillers = [
        _entry(
            f"{PADDING_PREFIX}{index}",
            [(SOLVE_ORE_ITEM, 1)],
            [(SOLVE_ROD_ITEM, 1)],
            path=_pad_path(index),
        )
        for index in range(_padding_count())
    ]
    return _registry_of([*_ascent_entries(), *fillers])


def _request(*, direction: str = OBJECTIVE_RAW, item: str = SOLVE_RELIC_ITEM) -> PlanRequest:
    """A well-formed request: 10 of one item a minute, Ore raw, balanced byproducts."""
    return PlanRequest(
        targets=MappingProxyType({item: RELIC_RATE}),
        raw_items=(SOLVE_ORE_ITEM,),
        byproduct_policy=BYPRODUCT_BALANCED,
        direction=direction,
    )


def _unlocks(
    unlocked: Iterable[str], *, machines: Iterable[str] = MACHINE_BUILD_PATHS
) -> UnlockState:
    """An unlock state holding these recipe paths and these machines' build recipe paths.

    Every machine unless told otherwise, so an arm's locks are the recipes it names.
    """
    return dataclasses.replace(EMPTY_UNLOCK_STATE, recipes=frozenset((*unlocked, *machines)))


def _model(unlocked: Iterable[str]) -> WorldModel:
    """A synthetic world of the pinned build, placing no machine, with these recipes unlocked."""
    return dataclasses.replace(synthetic_world(game_pin()), unlocks=_unlocks(unlocked))


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


def _plan_trace(advice: Advice) -> Trace:
    """The one plan.adopt trace of a run.

    Reduced inline to a count first, so no local holds the withheld traces when
    the assertion fails (CS-850, CS-851).
    """
    count = sum(1 for trace in advice.traces if trace.rule_id == ADOPT_ID)
    assert count == 1
    return next(trace for trace in advice.traces if trace.rule_id == ADOPT_ID)


def _plan_cards(advice: Advice) -> list[Card]:
    """Every card plan.adopt yielded in a run."""
    return [advised.card for advised in advice.cards if advised.card.rule_id == ADOPT_ID]


def _plan_card(advice: Advice) -> Card:
    """The one card plan.adopt yielded in a run."""
    cards = _plan_cards(advice)
    count = len(cards)
    assert count == 1
    return cards[0]


def _read(trace: Trace, name: str) -> object:
    """What the trace read for one input, which it must have read exactly once."""
    found = [
        step.value
        for step in trace.steps
        if step.kind is StepKind.INPUT_READ and step.subject == name
    ]
    count = len(found)
    assert count == 1, name
    return found[0]


def _card_read(card: Card, name: str) -> object:
    """What a card's own trace read for one input.

    A helper so an assertion over the value never renders the withheld trace.
    """
    return _read(card.trace, name)


def _state_kind(ledger: Ledger, model: WorldModel, card_id: str) -> str:
    """One card's recorded state in this world.

    A helper so an assertion over the state never renders the withheld token.
    """
    return ledger.state(model.token, card_id, now=NOW).kind


def _completed_count(advice: Advice) -> int:
    """How many cards a run recorded completed, reduced so no assertion renders the ids."""
    return len(advice.completed)


def _kinds(trace: Trace) -> list[StepKind]:
    """The step kinds of a trace, in order."""
    return [step.kind for step in trace.steps]


def _rendered(trace: Trace) -> str:
    """Every field of every step, as a reader of the trace could see it."""
    return "\n".join(
        f"{step.kind.value} {step.subject} {step.source} {step.reason} {render_value(step.value)}"
        for step in trace.steps
    )


def _badge_of(offered: Mapping[str, InputValue]) -> StrategyBadge:
    """The badge one offer carries, which must be a badge."""
    badge = offered["plan.badge"].value
    assert type(badge) is StrategyBadge
    return badge


def _measured(badge: StrategyBadge) -> list[tuple[str, bool, object, object, str]]:
    """A badge's verdicts as plain rows, one per rung."""
    return [
        (check.strategy, check.cleared, check.score, check.reference, check.reason)
        for check in badge.checks
    ]


# ---------------------------------------------------------------------------
# The acceptance
# ---------------------------------------------------------------------------


def test_the_plan_family_is_registered() -> None:
    ids = [spec.rule_id for spec in registered_rules()]
    assert ADOPT_ID in ids
    assert REDESIGN_ID in ids
    listed = any(family is plan_rules.RULES for family in rules_module._FAMILIES)  # noqa: SLF001
    assert listed


def test_advise_world_ranks_a_plan_and_fires_plan_adopt(tmp_path: Path) -> None:
    advice = _advise(tmp_path, _model(ASCENT_PATHS), _registry(), _request())

    card = _plan_card(advice)
    shown = [advised.card.id for advised in advice.shown]
    assert card.id in shown
    assert card.tier1 == "Build the planned production chain for Desc_SolveRelic_C"
    assert (
        card.tier2 == "It makes 10.00 per minute of Desc_SolveRelic_C with 2.00 machine equivalents"
    )
    derivation = card.tier3
    assert (
        'Read plan.badge = StrategyBadge(strongest="within-raw", cleared=("within-raw"), checks=('
        'ThresholdCheck(strategy="within-raw", cleared=true, score=10.00, reference=10.00, '
        'bound=1.00, reason=""), '
        'ThresholdCheck(strategy="within-buildings", cleared=false, score=2.00, reference=1.00, '
        'bound=1.00, reason="over-bound"), '
        'ThresholdCheck(strategy="within-power", cleared=false, score=30.00, reference=15.00, '
        'bound=1.00, reason="over-bound"))) from solve.strategy.ranked_plan.badge'
    ) in derivation
    # Tier 1 carries nothing of the badge: no rung name, no rung claim.
    headline = card.tier1.lower()
    leaked = [rung.name for rung in STRATEGY_LADDER if rung.name in headline]
    assert leaked == []


def test_the_badge_is_graded_against_each_rungs_own_optimum() -> None:
    registry = _registry()
    offered = plan_offer(_unlocks(ASCENT_PATHS), registry, _request())

    badge = _badge_of(offered)
    assert badge.cleared == (RUNG_WITHIN_RAW,)
    assert badge.strongest == RUNG_WITHIN_RAW
    assert _measured(badge) == [
        (RUNG_WITHIN_RAW, True, TWO_STAGE_ORE, TWO_STAGE_ORE, ""),
        (
            RUNG_WITHIN_BUILDINGS,
            False,
            TWO_STAGE_MACHINES,
            ONE_STAGE_MACHINES,
            NOT_CLEARED_OVER_BOUND,
        ),
        (
            RUNG_WITHIN_POWER,
            False,
            TWO_STAGE_MEGAWATTS,
            ONE_STAGE_MEGAWATTS,
            NOT_CLEARED_OVER_BOUND,
        ),
    ]
    # The control: this plan graded against its own ranking clears all three,
    # which is the claim the ladder would otherwise have published.
    plan = offered["plan.production"].value
    self_graded = rank_plans(registry, (plan,), objective=weighted_objective(raw=Fraction(1)))  # type: ignore[arg-type]
    assert self_graded[0].badge.cleared == tuple(rung.name for rung in STRATEGY_LADDER)


def test_the_requires_are_the_join_not_a_supplied_tuple() -> None:
    state = _unlocks(ASCENT_PATHS)
    offered = plan_offer(state, _registry(), _request())

    requires = offered["plan.requires"].value
    assert requires == (
        "recipe:/Game/FactoryGame/Synthetic/Alpha/Stage_Two.Stage_Two_C",
        ASSEMBLER_KEY,
        "recipe:/Game/FactoryGame/Synthetic/Gamma/Stage_One.Stage_One_C",
    )
    assert offered["plan.requires"].source == "advisor.plans.recipe_unlock_join"
    # Each key is exactly one the engine's own flattening of the state builds, so
    # the join and unlock_keys share one prefix rather than two literals.
    assert isinstance(requires, tuple)
    missing = sorted(set(requires) - unlock_keys(state))
    assert missing == []


def test_the_engine_refuses_the_joined_keys_over_a_world_lacking_them() -> None:
    world = _inputs(_model(ASCENT_PATHS), _registry(), _request())
    held = run_rule(plan_rules.ADOPT_RULE, world)
    assert held.recommendation is not None

    bare = dataclasses.replace(world, unlocks=frozenset())
    trace = run_rule(plan_rules.ADOPT_RULE, bare)

    assert trace.recommendation is None
    assert card_for(trace) is None
    assert trace.unmet == (
        "recipe:/Game/FactoryGame/Synthetic/Alpha/Stage_Two.Stage_Two_C",
        ASSEMBLER_KEY,
        "recipe:/Game/FactoryGame/Synthetic/Gamma/Stage_One.Stage_One_C",
    )


def test_a_locked_recipe_cannot_enter_the_plan(tmp_path: Path) -> None:
    """With the first stage locked the cheap route has no Rare, so 60 Ore it is."""
    unlocked = (PATHS[RELIC_FROM_RARE], PATHS[RELIC_DIRECT])
    advice = _advise(tmp_path, _model(unlocked), _registry(), _request())

    card = _plan_card(advice)
    plan = _card_read(card, "plan.production")
    assert [step.recipe_key for step in plan.steps] == [RELIC_DIRECT]  # type: ignore[attr-defined]
    assert plan.raw_inputs[SOLVE_ORE_ITEM] == ONE_STAGE_ORE  # type: ignore[attr-defined]
    assert _card_read(card, "plan.requires") == ("recipe:" + PATHS[RELIC_DIRECT], ASSEMBLER_KEY)
    locked_named = RARE_FROM_ORE in card.tier3 or PATHS[RARE_FROM_ORE] in card.tier3
    assert not locked_named


def test_the_join_is_the_whole_path_never_its_trailing_token() -> None:
    """A path sharing only the trailing token is another asset, and joins nothing (CS-1343)."""
    elsewhere = PATHS[RARE_FROM_ORE].replace("/Gamma/", "/Elsewhere/")
    assert elsewhere.rpartition(".")[2] == PATHS[RARE_FROM_ORE].rpartition(".")[2]
    unlocked = (PATHS[RELIC_FROM_RARE], PATHS[RELIC_DIRECT], elsewhere)

    offered = plan_offer(_unlocks(unlocked), _registry(), _request())

    assert offered["plan.requires"].value == ("recipe:" + PATHS[RELIC_DIRECT], ASSEMBLER_KEY)
    assert offered["plan.unmatched_unlocks"].value == 1


@pytest.mark.parametrize(
    "unlocked", [(), (PATHS[RARE_FROM_ORE],)], ids=["nothing-unlocked", "only-the-first-stage"]
)
def test_every_producer_locked_is_no_plan_no_adopt_card_and_fires_the_route(
    tmp_path: Path, unlocked: tuple[str, ...]
) -> None:
    """plan.adopt stays silent and unsettled, and the route goes to plan.redesign (CS-1371)."""
    advice = _advise(tmp_path, _model(unlocked), _registry(), _request())

    trace = _plan_trace(advice)
    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _plan_cards(advice) == []
    assert trace.recommendation is None
    assert _kinds(trace).count(StepKind.VERDICT_INDETERMINATE) == 1
    settled = settled_rules(advice.traces)
    assert ADOPT_ID not in settled
    assert REDESIGN_ID not in settled
    fired = [advised.card.rule_id for advised in advice.cards]
    assert fired == [REDESIGN_ID]


def test_a_recipe_with_no_asset_path_is_flagged_and_never_planned(tmp_path: Path) -> None:
    """The one-stage route carries no FullName, so nothing can say whether it is unlocked."""
    registry = _registry_of(_ascent_entries(pathless=frozenset({RELIC_DIRECT})))
    advice = _advise(tmp_path, _model(ASCENT_PATHS), registry, _request(direction=OBJECTIVE_POWER))

    card = _plan_card(advice)
    # Under power the unknown route would have won, at 15 MW against 30.
    assert _card_read(card, "plan.requires") == (
        "recipe:" + PATHS[RELIC_FROM_RARE],
        ASSEMBLER_KEY,
        "recipe:" + PATHS[RARE_FROM_ORE],
    )
    assert _card_read(card, "plan.unchecked") == (RELIC_DIRECT,)
    flagged = (
        "; 1 automated recipe(s) carry no unlock path to check and were never planned" in card.tier2
    )
    assert flagged
    assert 'Read plan.unchecked = ("R_B2Direct") from advisor.plans.unchecked' in card.tier3


def test_a_pathless_only_route_is_no_plan_and_still_flagged(tmp_path: Path) -> None:
    """No silent no-plan: the trace says which recipes were never asked about."""
    pathless = frozenset({RELIC_FROM_RARE, RELIC_DIRECT})
    registry = _registry_of(_ascent_entries(pathless=pathless))
    advice = _advise(tmp_path, _model(ASCENT_PATHS), registry, _request())

    trace = _plan_trace(advice)
    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _read(trace, "plan.unchecked") == (RELIC_FROM_RARE, RELIC_DIRECT)
    assert _plan_cards(advice) == []


def test_a_recipe_with_no_producer_cannot_enter_the_plan() -> None:
    """Unlocked and with a path, and no machine can run it, so no plan may lean on it."""
    free = _entry(
        NO_PRODUCER,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_RELIC_ITEM, 2)],
        path=PATHS[NO_PRODUCER],
        buildings=(),
    )
    registry = _registry_of([*_ascent_entries(), free])
    keys = (*ASCENT, NO_PRODUCER)

    # The control: a raw search that may use it does, so the door is what is graded.
    unfiltered = optimize_plan(
        registry,
        OptimizeRequest(
            targets=MappingProxyType({SOLVE_RELIC_ITEM: RELIC_RATE}),
            candidates=keys,
            unlocked=keys,
            raw_items=(SOLVE_ORE_ITEM,),
            byproduct_policy=BYPRODUCT_BALANCED,
            objective=weighted_objective(raw=Fraction(1)),
        ),
    )
    assert unfiltered.selection == (NO_PRODUCER,)
    assert unfiltered.plan.raw_inputs[SOLVE_ORE_ITEM] == NO_PRODUCER_ORE

    offered = plan_offer(_unlocks((*ASCENT_PATHS, PATHS[NO_PRODUCER])), registry, _request())

    plan = offered["plan.production"].value
    assert [step.recipe_key for step in plan.steps] == [RELIC_FROM_RARE, RARE_FROM_ORE]  # type: ignore[attr-defined]
    assert plan.raw_inputs[SOLVE_ORE_ITEM] == TWO_STAGE_ORE  # type: ignore[attr-defined]
    # It joined, so it is neither unmatched nor unchecked: it is simply not automated.
    assert offered["plan.unmatched_unlocks"].value == 0
    assert offered["plan.unchecked"].value == ()


def test_no_target_records_indeterminate_and_no_missing_input(tmp_path: Path) -> None:
    """Every world runs the rule, so a world with no target must not read as lacking one."""
    advice = _advise(tmp_path, _model(ASCENT_PATHS), _registry(), None)

    trace = _plan_trace(advice)
    assert _read(trace, "plan.status") == STATUS_NO_TARGET
    kinds = _kinds(trace)
    assert kinds.count(StepKind.INPUT_MISSING) == 0
    assert kinds.count(StepKind.RULE_ERROR) == 0
    assert kinds.count(StepKind.VERDICT_INDETERMINATE) == 1
    assert _plan_cards(advice) == []
    settled = ADOPT_ID in settled_rules(advice.traces)
    assert not settled


def _no_rung_world(model: WorldModel, registry: Registry) -> WorldInputs:
    """A world whose ranked plan cleared no rung: the rule rejects it and settles.

    The control the two arms below need, proving the ledger WOULD complete the
    recorded card over a settled rule, so their not completing it grades the
    indeterminate step rather than something else.
    """
    plan = plan_offer(model.unlocks, registry, _request())["plan.production"].value
    assert plan is not None
    ranked = rank_plans(
        registry,
        (plan,),  # type: ignore[arg-type]
        objective=weighted_objective(raw=Fraction(1)),
        references=dict.fromkeys(tuple(rung.name for rung in STRATEGY_LADDER)),
    )
    values = dict(_inputs(model, registry, None).values)
    values.update(
        plan_rules.plan_inputs(
            ranked[0],
            requires=(),
            trimmed=(),
            unchecked=(),
            unmatched_unlocks=0,
            backend=BACKEND_EXHAUSTIVE,
        )
    )
    return WorldInputs(values=values, unlocks=unlock_keys(model.unlocks))


def test_a_recorded_card_is_not_completed_when_the_target_clears(tmp_path: Path) -> None:
    model = _model(ASCENT_PATHS)
    registry = _registry()
    ledger = Ledger(tmp_path)
    mutes = MuteStore(tmp_path)

    first = advise_and_record(
        model.token, _inputs(model, registry, _request()), ledger=ledger, mutes=mutes, now=NOW
    )
    recorded = _plan_card(first).id

    cleared = advise_and_record(
        model.token, _inputs(model, registry, None), ledger=ledger, mutes=mutes, now=NOW
    )
    assert _completed_count(cleared) == 0
    assert _state_kind(ledger, model, recorded) == "new"

    # The control, over the same ledger: a settled rule DOES complete it.
    settled = advise_and_record(
        model.token, _no_rung_world(model, registry), ledger=ledger, mutes=mutes, now=NOW
    )
    completed_it = settled.completed == (recorded,)
    assert completed_it


def test_a_recorded_card_is_not_completed_when_the_target_moves(tmp_path: Path) -> None:
    """The world never moved: the player only asked about something else."""
    rod = _entry(
        ROD_FROM_ORE, [(SOLVE_ORE_ITEM, 1)], [(SOLVE_ROD_ITEM, 1)], path=PATHS[ROD_FROM_ORE]
    )
    registry = _registry_of([*_ascent_entries(), rod])
    model = _model((*ASCENT_PATHS, PATHS[ROD_FROM_ORE]))
    ledger = Ledger(tmp_path)
    mutes = MuteStore(tmp_path)

    first = advise_and_record(
        model.token, _inputs(model, registry, _request()), ledger=ledger, mutes=mutes, now=NOW
    )
    recorded = _plan_card(first).id

    moved = advise_and_record(
        model.token,
        _inputs(model, registry, _request(item=SOLVE_ROD_ITEM)),
        ledger=ledger,
        mutes=mutes,
        now=NOW,
    )

    # The card for the new target fires, which is what makes this the moved case.
    other = _plan_card(moved).id
    assert other != recorded
    assert _completed_count(moved) == 0
    assert _state_kind(ledger, model, recorded) == "new"
    assert _state_kind(ledger, model, other) == "new"


#: Each refusal the solve layer can raise, and the status it must be recorded as.
#: Each carries :data:`MARK` wherever it holds text, so an echo cannot hide.
REFUSALS: Final[Mapping[str, tuple[Callable[[], Exception], str]]] = MappingProxyType(
    {
        "no-feasible": (lambda: NoFeasibleSelectionError(MARK), STATUS_NO_PLAN),
        "bound-exhausted": (
            lambda: BoundExhaustedError(MAX_EXHAUSTIVE_CANDIDATES, MARK, 1, MARK),
            STATUS_NO_PLAN,
        ),
        "search-too-large": (lambda: SearchSpaceTooLargeError(MARK), STATUS_SOLVE_REFUSED),
        "objective-undefined": (lambda: ObjectiveUndefinedError(MARK), STATUS_REQUEST_MALFORMED),
        "power-not-comparable": (
            lambda: PowerNotComparableError(MARK, MARK),
            STATUS_POWER_NOT_COMPARABLE,
        ),
        "key-error": (lambda: KeyError(MARK), STATUS_SOLVE_REFUSED),
        "value-error": (lambda: ValueError(MARK), STATUS_REQUEST_MALFORMED),
        "inexact-value": (lambda: InexactValueError(MARK), STATUS_REQUEST_MALFORMED),
        "undefined-rate": (lambda: UndefinedRateError(MARK), STATUS_SOLVE_REFUSED),
        "unknown-backend": (lambda: UnknownBackendError(MARK, MARK), STATUS_SOLVE_REFUSED),
    }
)

#: The three doors the ranked path reaches solve through.
SOLVE_DOORS: Final = ("optimize_within_bound", "optimize_plan", "rank_plans")

#: The two doors a no-plan's marked route reaches through, and no other status (CS-1371).
ROUTE_DOORS: Final = ("derived_route", "solve_for_targets")

#: The door a rung search runs through. A no-plan refusal arriving here comes after
#: the bound has solved, so a plan does exist and no-plan would be false.
RUNG_SEARCH_DOOR: Final = "optimize_plan"

#: The refusals that say no-plan at every door but that one.
NO_PLAN_REFUSALS: Final = frozenset({"no-feasible", "bound-exhausted"})


@pytest.mark.parametrize("door", SOLVE_DOORS)
@pytest.mark.parametrize("refusal", sorted(REFUSALS))
def test_each_solve_refusal_is_a_recorded_step_never_a_crash(
    door: str, refusal: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    make, status = REFUSALS[refusal]
    if door == RUNG_SEARCH_DOOR and refusal in NO_PLAN_REFUSALS:
        status = STATUS_SOLVE_REFUSED

    def refusing(*_args: object, **_kwargs: object) -> object:
        raise make()

    monkeypatch.setattr(plans_module, door, refusing)

    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), _request()))

    assert _read(trace, "plan.status") == status
    assert card_for(trace) is None
    kinds = _kinds(trace)
    assert kinds.count(StepKind.RULE_ERROR) == 0
    assert kinds.count(StepKind.VERDICT_INDETERMINATE) == 1
    echoed = MARK in _rendered(trace)
    assert not echoed


def test_a_power_refusal_on_another_rung_loses_that_rung_alone() -> None:
    """A recipe naming two buildings has no single draw, so power cannot be compared."""
    unpriceable = _entry(
        RARE_FROM_ORE,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_RARE_ITEM, 1)],
        path=PATHS[RARE_FROM_ORE],
        buildings=(SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
    )
    registry = _registry_of([*_ascent_entries()[:2], unpriceable])

    offered = plan_offer(_unlocks(ASCENT_PATHS), registry, _request())

    badge = _badge_of(offered)
    assert badge.cleared == (RUNG_WITHIN_RAW,)
    power = badge.checks[-1]
    assert power.strategy == RUNG_WITHIN_POWER
    assert power.reason == NOT_CLEARED_UNPRICEABLE
    assert power.score is None
    assert power.reference is None


def test_a_power_refusal_on_the_asked_rung_is_a_recorded_status() -> None:
    """Asked for by power there is no order to publish, so there is no plan to advise."""
    unpriceable = _entry(
        RARE_FROM_ORE,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_RARE_ITEM, 1)],
        path=PATHS[RARE_FROM_ORE],
        buildings=(SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
    )
    registry = _registry_of([*_ascent_entries()[:2], unpriceable])

    trace = run_rule(
        plan_rules.ADOPT_RULE,
        _inputs(_model(ASCENT_PATHS), registry, _request(direction=OBJECTIVE_POWER)),
    )

    assert _read(trace, "plan.status") == STATUS_POWER_NOT_COMPARABLE
    assert card_for(trace) is None


def test_an_unknown_backend_in_the_environment_is_a_recorded_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real refusal, through the real door, and its name is never echoed.

    Solve-refused and never request-malformed: a bad environment value says nothing
    about the target the caller stated.
    """
    monkeypatch.setenv(BACKEND_ENV_VAR, MARK)

    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), _request()))

    assert _read(trace, "plan.status") == STATUS_SOLVE_REFUSED
    echoed = MARK in _rendered(trace)
    assert not echoed


def _capped_entries() -> list[dict[str, str]]:
    """Fourteen recipes: the two-stage route with twelve fillers between its stages."""
    two_stages = _ascent_entries()
    fillers = [
        _entry(
            f"{PADDING_PREFIX}{index}",
            [(SOLVE_ORE_ITEM, 1)],
            [(SOLVE_ROD_ITEM, 1)],
            path=_pad_path(index),
        )
        for index in range(12)
    ]
    return [two_stages[0], *fillers, two_stages[2]]


def _capped_paths() -> tuple[str, ...]:
    """Every unlock path of :func:`_capped_entries`."""
    return (
        PATHS[RELIC_FROM_RARE],
        *(_pad_path(index) for index in range(12)),
        PATHS[RARE_FROM_ORE],
    )


def _indeterminate_reason(trace: Trace) -> str:
    """The reason on the one indeterminate step a trace must hold."""
    found = [step.reason for step in trace.steps if step.kind is StepKind.VERDICT_INDETERMINATE]
    count = len(found)
    assert count == 1
    return found[0]


#: One recipe past the cap, each one required, so the cap has to cut a route short.
CHAIN_STAGES: Final = 13

#: Ore a minute at 10 Relic a minute: one Ore a cycle, ten cycles a minute at stage 1.
CHAIN_ORE: Final = Fraction(10)

#: The stage the cap drops, by hand. The route walks down from Relic, so the deepest
#: stage ranks last. It is the FIRST in registry order, where the shipped order ranked
#: stage 13 and then registry order, and would have dropped stage 12 instead.
CHAIN_DROPPED_STAGE: Final = 1


def _stage_recipe(stage: int) -> str:
    """One stage's recipe name, zero-padded so registry and name order agree."""
    return f"R_Stage{stage:02d}"


def _stage_item(stage: int) -> str:
    """The item one stage makes, each new to the corpus and given its own descriptor."""
    return f"Desc_SolveStage{stage:02d}_C"


def _stage_path(stage: int) -> str:
    """One stage's invented asset path."""
    return f"/Game/FactoryGame/Synthetic/Chain/Stage_{stage:02d}.Stage_{stage:02d}_C"


def _chain_recipes() -> tuple[str, ...]:
    """The whole chain in registry order, stage 1 first."""
    return tuple(_stage_recipe(stage) for stage in range(1, CHAIN_STAGES + 1))


def _chain_registry() -> Registry:
    """A chain longer than the cap: one producer per item, every member required.

    Stage 1 makes the first stage item from Ore, each next stage eats the item before,
    and the last makes Relic, so no recipe can be left out and no other recipe can stand
    in. Every cycle is six seconds and every amount one, so 10 Relic a minute runs one
    machine a stage and draws 10 Ore. Declared stage 1 first, so registry order runs
    against the walk.

    The corpus holds too few items for this, so each stage item gets its own descriptor
    through the same text seam the corpus uses, and the registry builds with no warning
    but the build gun's: an unknown-item warning would be solving a different factory.

    Returns:
        The registry, stamped as built from the pinned docs bytes.
    """
    made = [_stage_item(stage) for stage in range(1, CHAIN_STAGES)]
    eaten = [SOLVE_ORE_ITEM, *made]
    entries = [
        _entry(
            _stage_recipe(stage),
            [(eaten[stage - 1], 1)],
            [(made[stage - 1] if stage < CHAIN_STAGES else SOLVE_RELIC_ITEM, 1)],
            path=_stage_path(stage),
        )
        for stage in range(1, CHAIN_STAGES + 1)
    ]
    descriptors = [
        {KEY_CLASS_NAME: item, KEY_DISPLAY_NAME: item, KEY_FORM: "RF_SOLID"} for item in made
    ]
    groups = json.loads(DOCS_TEXT)
    for group in groups:
        native_class = group[KEY_NATIVE_CLASS]
        if native_class.endswith(f".{ITEM_GROUP}'"):
            group[KEY_CLASSES].extend(descriptors)
        elif native_class.endswith(f".{BUILDING_DESCRIPTOR_GROUP}'"):
            group[KEY_CLASSES].extend(MACHINE_DESCRIPTOR_ENTRIES)
        elif native_class.endswith(f".{RECIPE_GROUP}'"):
            group[KEY_CLASSES] = [*entries, *MACHINE_BUILD_ENTRIES]
    return pinned_source(build_registry(document_from_groups(groups)))


def _chain_paths() -> tuple[str, ...]:
    """Every unlock path of :func:`_chain_registry`."""
    return tuple(_stage_path(stage) for stage in range(1, CHAIN_STAGES + 1))


def test_a_capped_no_plan_names_what_the_bound_dropped(tmp_path: Path) -> None:
    """A route exists among the unlocked recipes and the cap cut it short.

    Rebuilt under CS-1372, because the two-recipe route this arm used to sit on now
    ranks. By hand: thirteen recipes, one producer per item, so the derived route is
    all thirteen and the walk from Relic reads R_Stage13 down to R_Stage01. The cap of
    twelve keeps R_Stage13 to R_Stage02 and drops R_Stage01, the only way in from Ore.
    So no prefix solves, and the status is a statement about the kept set: the trace
    has to say what the search never asked about.
    """
    registry = _chain_registry()
    assert [warning.code for warning in registry.warnings] == [WARN_UNRESOLVED_PRODUCED_IN]
    assert len(_chain_recipes()) > MAX_EXHAUSTIVE_CANDIDATES

    advice = _advise(tmp_path, _model(_chain_paths()), registry, _request())

    trace = _plan_trace(advice)
    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _read(trace, "plan.trimmed") == (_stage_recipe(CHAIN_DROPPED_STAGE),)
    assert _plan_cards(advice) == []
    assert trace.recommendation is None
    settled = ADOPT_ID in settled_rules(advice.traces)
    assert not settled

    # The control: the whole chain, asked about, does solve. Through pillar 1, because
    # pillar 2's door refuses thirteen candidates, which that refusal shows.
    route = _chain_recipes()
    solved = solve_for_targets(
        registry,
        RatioRequest(
            targets=MappingProxyType({SOLVE_RELIC_ITEM: RELIC_RATE}),
            recipes=route,
            raw_items=(SOLVE_ORE_ITEM,),
            byproduct_policy=BYPRODUCT_BALANCED,
        ),
    )
    assert [step.recipe_key for step in solved.steps] == list(route)
    assert solved.raw_inputs[SOLVE_ORE_ITEM] == CHAIN_ORE

    with pytest.raises(SearchSpaceTooLargeError):
        optimize_plan(
            registry,
            OptimizeRequest(
                targets=MappingProxyType({SOLVE_RELIC_ITEM: RELIC_RATE}),
                candidates=route,
                unlocked=route,
                raw_items=(SOLVE_ORE_ITEM,),
                byproduct_policy=BYPRODUCT_BALANCED,
                objective=weighted_objective(raw=Fraction(1)),
            ),
        )


def test_a_capped_no_plan_reason_speaks_only_for_the_kept_set() -> None:
    """The same chain, for the sentence: it claims nothing of what the cap dropped.

    A reason claiming that no selection of the unlocked recipes reaches the target would
    be false here, by the control in the arm above.
    """
    trace = run_rule(
        plan_rules.ADOPT_RULE, _inputs(_model(_chain_paths()), _chain_registry(), _request())
    )

    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _indeterminate_reason(trace) == (
        "the search found no plan over the unlocked automated recipes it kept,"
        " under the stated byproduct policy"
    )
    assert card_for(trace) is None


def test_an_uncapped_no_plan_is_the_same_status_and_names_nothing_dropped() -> None:
    """One status for both: only what the bound dropped tells them apart."""
    trace = run_rule(
        plan_rules.ADOPT_RULE,
        _inputs(_model((PATHS[RARE_FROM_ORE],)), _registry(), _request()),
    )

    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _read(trace, "plan.trimmed") == ()
    assert card_for(trace) is None


def test_a_refusal_reads_what_the_refusal_itself_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal's record is what no-plan names, and the world here trims nothing."""
    record = TrimRecord(
        steps=(
            TrimStep(
                rule=TRIM_ROUTE_FIRST,
                cap=MAX_EXHAUSTIVE_CANDIDATES,
                kept=(RELIC_FROM_RARE,),
                removed=(RELIC_DIRECT, RARE_FROM_ORE),
            ),
        )
    )

    def refusing(*_args: object, **_kwargs: object) -> object:
        raise BoundExhaustedError(MAX_EXHAUSTIVE_CANDIDATES, MARK, 1, MARK, record=record)

    monkeypatch.setattr(plans_module, "optimize_within_bound", refusing)

    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), _request())

    assert offered["plan.status"].value == STATUS_NO_PLAN
    assert offered["plan.trimmed"].value == (RELIC_DIRECT, RARE_FROM_ORE)


def test_a_target_declared_raw_is_malformed_after_the_join_and_reads_the_status_alone() -> None:
    """Pillar 1 refuses it at the empty prefix, so the join ran and its report stays unread."""
    request = _request(item=SOLVE_ORE_ITEM)

    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), request)
    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), request))

    assert offered["plan.status"].value == STATUS_REQUEST_MALFORMED
    assert offered["plan.trimmed"].value == ()
    reads = [
        step.subject
        for step in trace.steps
        if step.kind is StepKind.INPUT_READ and step.subject.startswith("plan.")
    ]
    assert reads == ["plan.status"]


def test_a_byproduct_refusal_reads_as_the_stated_policy() -> None:
    """One recipe does reach the target, refused only for its byproduct.

    By hand: R_By makes 1 Relic and 1 Rare from 1 Ore. Balanced byproducts leave a
    Rare row nothing consumes, so no plan; sinkable sinks the Rare, at 10 Ore a minute.
    """
    entries = [
        _entry(
            BYPRODUCT_RECIPE,
            [(SOLVE_ORE_ITEM, 1)],
            [(SOLVE_RELIC_ITEM, 1), (SOLVE_RARE_ITEM, 1)],
            path=PATHS[RELIC_DIRECT],
        )
    ]
    registry = _registry_of(entries)
    model = _model((PATHS[RELIC_DIRECT],))

    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(model, registry, _request()))

    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _read(trace, "plan.trimmed") == ()
    assert "under the stated byproduct policy" in _indeterminate_reason(trace)

    # The control: the same recipe under the other policy is a plan.
    sinkable = dataclasses.replace(_request(), byproduct_policy=BYPRODUCT_SINKABLE)
    offered = plan_offer(model.unlocks, registry, sinkable)
    assert offered["plan.status"].value == STATUS_RANKED
    plan = offered["plan.production"].value
    assert plan.raw_inputs[SOLVE_ORE_ITEM] == TWO_STAGE_ORE  # type: ignore[attr-defined]


def test_a_refusal_the_bound_never_answered_still_names_the_trim() -> None:
    """The cap's drop is a rule, so it stays true when the ascent itself refuses.

    By hand: R_Odd names two buildings, so it has no exact draw, and it is the one
    direct Relic producer. Asked by power, the prefix holding it refuses inside the
    ascent, with no BoundedResult and no BoundExhaustedError to read a record from.
    R_Odd eats only Ore, so it is the whole route and the whole closure, and every
    other recipe ranks behind it by registry position: the cap keeps R_Odd and R_Pad0
    to R_Pad10, and drops R_Pad11 and R_B3Rare. An empty ``plan.trimmed`` here would
    say nothing was dropped.
    """
    fillers = _capped_entries()[1:-1]
    odd = _entry(
        UNPRICEABLE_RECIPE,
        [(SOLVE_ORE_ITEM, 5)],
        [(SOLVE_RELIC_ITEM, 1)],
        path=PATHS[RELIC_FROM_RARE],
        buildings=(SOLVE_ASSEMBLER_BUILDING, SOLVE_SMELTER_BUILDING),
    )
    registry = _registry_of([odd, *fillers, _ascent_entries()[2]])

    trace = run_rule(
        plan_rules.ADOPT_RULE,
        _inputs(_model(_capped_paths()), registry, _request(direction=OBJECTIVE_POWER)),
    )

    assert _read(trace, "plan.status") == STATUS_POWER_NOT_COMPARABLE
    assert _read(trace, "plan.trimmed") == (f"{PADDING_PREFIX}11", RARE_FROM_ORE)


def _dead_end_registry() -> Registry:
    """A world where greedy's raw walk dead-ends and a plan does exist.

    Every cycle is six seconds, ten a minute, 15 MW a machine. By hand at 10 Relic a
    minute, balanced:

    - R_A alone, 6 Ore to 1 Relic: 60 Ore, 1 machine, 15 MW. The only plan, because
    - R_B, 1 Rare to 1 Relic, needs R_C, 1 Ore to 1 Rare and 1 Rod, and nothing
      consumes the Rod.

    Greedy's raw walk probes R_B at a relaxed raw total of 10 against R_A's 60, commits
    to it, adds R_C, and has nothing left to add, and no selection it reached solved. Its
    buildings and power walks tie R_A against R_B and take R_A, first in registry order.

    Returns:
        The registry, in the order above.
    """
    return _registry_of(
        [
            _entry(
                DEAD_END_A, [(SOLVE_ORE_ITEM, 6)], [(SOLVE_RELIC_ITEM, 1)], path=PATHS[ROD_FROM_ORE]
            ),
            _entry(
                DEAD_END_B,
                [(SOLVE_RARE_ITEM, 1)],
                [(SOLVE_RELIC_ITEM, 1)],
                path=PATHS[RELIC_DIRECT],
            ),
            _entry(
                DEAD_END_C,
                [(SOLVE_ORE_ITEM, 1)],
                [(SOLVE_RARE_ITEM, 1), (SOLVE_ROD_ITEM, 1)],
                path=PATHS[RARE_FROM_ORE],
            ),
        ]
    )


#: Every unlock path of :func:`_dead_end_registry`.
DEAD_END_PATHS: Final = (PATHS[ROD_FROM_ORE], PATHS[RELIC_DIRECT], PATHS[RARE_FROM_ORE])


@pytest.mark.parametrize("direction", [OBJECTIVE_RAW, OBJECTIVE_BUILDINGS, OBJECTIVE_POWER])
def test_any_rung_search_that_dead_ends_is_solve_refused(
    direction: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Greedy's raw walk dead-ends whichever direction was asked, and a plan exists.

    No-plan would be false, because the bound has just solved. Not comparable would
    be false too: that plan's raw score is exactly 60, and a None reference says a rung
    has no exact figure to compare. So the search refused, and no card is built on it.
    """
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_GREEDY)

    trace = run_rule(
        plan_rules.ADOPT_RULE,
        _inputs(_model(DEAD_END_PATHS), _dead_end_registry(), _request(direction=direction)),
    )

    assert _read(trace, "plan.status") == STATUS_SOLVE_REFUSED
    assert _indeterminate_reason(trace) == "the search refused, which says nothing about the target"
    assert card_for(trace) is None


def test_a_power_rung_that_dead_ends_is_refused_though_every_recipe_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every recipe here has an exact draw, so an unpriceable power rung would be false.

    By hand at 10 Relic a minute, balanced: R_A in an assembler, 6 Ore to 1 Relic, is the
    only plan, at 60 Ore, 1 machine, 15 MW. R_B in a smelter, 7 Rare to 1 Relic, needs
    R_C in a smelter, 1 Ore to 1 Rare and 1 Rod, and nothing consumes the Rod. Greedy's
    raw walk probes R_A at 60 against R_B's relaxed 70, and its buildings walk ties them
    and takes R_A first, so both solve. Its power walk probes R_B at 4 MW against R_A's
    15, commits to it, adds R_C, and no selection it reached solved.
    """
    smelter = (SOLVE_SMELTER_BUILDING,)
    registry = _registry_of(
        [
            _entry(
                DEAD_END_A, [(SOLVE_ORE_ITEM, 6)], [(SOLVE_RELIC_ITEM, 1)], path=PATHS[ROD_FROM_ORE]
            ),
            _entry(
                DEAD_END_B,
                [(SOLVE_RARE_ITEM, 7)],
                [(SOLVE_RELIC_ITEM, 1)],
                path=PATHS[RELIC_DIRECT],
                buildings=smelter,
            ),
            _entry(
                DEAD_END_C,
                [(SOLVE_ORE_ITEM, 1)],
                [(SOLVE_RARE_ITEM, 1), (SOLVE_ROD_ITEM, 1)],
                path=PATHS[RARE_FROM_ORE],
                buildings=smelter,
            ),
        ]
    )
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_GREEDY)

    offered = plan_offer(_unlocks(DEAD_END_PATHS), registry, _request())

    assert offered["plan.status"].value == STATUS_SOLVE_REFUSED

    # The control: a complete search prices the one plan on all three rungs.
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_EXHAUSTIVE)
    complete = plan_offer(_unlocks(DEAD_END_PATHS), registry, _request())
    assert _measured(_badge_of(complete)) == [
        (RUNG_WITHIN_RAW, True, ONE_STAGE_ORE, ONE_STAGE_ORE, ""),
        (RUNG_WITHIN_BUILDINGS, True, ONE_STAGE_MACHINES, ONE_STAGE_MACHINES, ""),
        (RUNG_WITHIN_POWER, True, ONE_STAGE_MEGAWATTS, ONE_STAGE_MEGAWATTS, ""),
    ]


@pytest.mark.parametrize("direction", [OBJECTIVE_RAW, OBJECTIVE_BUILDINGS, OBJECTIVE_POWER])
def test_the_dead_end_world_under_exhaustive_clears_every_rung(
    direction: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control: a complete search finds the one plan on every rung, so no rung dead-ends."""
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_EXHAUSTIVE)

    offered = plan_offer(
        _unlocks(DEAD_END_PATHS), _dead_end_registry(), _request(direction=direction)
    )

    assert offered["plan.status"].value == STATUS_RANKED
    assert _measured(_badge_of(offered)) == [
        (RUNG_WITHIN_RAW, True, ONE_STAGE_ORE, ONE_STAGE_ORE, ""),
        (RUNG_WITHIN_BUILDINGS, True, ONE_STAGE_MACHINES, ONE_STAGE_MACHINES, ""),
        (RUNG_WITHIN_POWER, True, ONE_STAGE_MEGAWATTS, ONE_STAGE_MEGAWATTS, ""),
    ]


@pytest.mark.parametrize(
    ("environment", "backend"),
    [
        pytest.param(None, BACKEND_EXHAUSTIVE, id="nothing-stated"),
        pytest.param(BACKEND_EXHAUSTIVE, BACKEND_EXHAUSTIVE, id="exhaustive"),
        pytest.param(BACKEND_GREEDY, BACKEND_GREEDY, id="greedy"),
    ],
)
def test_tier3_names_the_backend_that_ran(
    environment: str | None, backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tier 3 differs by backend, so it cannot be reproduced from what it shows without this."""
    if environment is None:
        monkeypatch.delenv(BACKEND_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(BACKEND_ENV_VAR, environment)

    card = card_for(
        run_rule(plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), _request()))
    )

    assert card is not None
    named = f'Read plan.backend = "{backend}" from solve.optimize.optimize_result.backend'
    assert named in card.tier3


def test_the_backend_moves_tier3_and_never_tier1_or_the_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both backends top out on the two stages, and only tier 3 tells them apart.

    By hand: greedy's buildings and power walks tie R_B1Relic against R_B2Direct and
    take R_B1Relic, first in registry order, so their references are the two stages
    and the badge clears all three rungs where exhaustive's clears within-raw alone.
    That claim is the reason tier 3 has to name the backend, and it is the one other
    line that moves.
    """
    cards = []
    for backend in (BACKEND_EXHAUSTIVE, BACKEND_GREEDY):
        monkeypatch.setenv(BACKEND_ENV_VAR, backend)
        cards.append(
            card_for(
                run_rule(
                    plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), _request())
                )
            )
        )
    first, second = cards
    assert first is not None
    assert second is not None
    same_headline = first.tier1 == second.tier1
    assert same_headline
    same_id = first.id == second.id
    assert same_id
    moved = [
        new
        for old, new in zip(first.tier3.splitlines(), second.tier3.splitlines(), strict=True)
        if old != new
    ]
    badge_line, backend_line = moved
    assert "Read plan.badge = " in badge_line
    assert 'cleared=("within-raw", "within-buildings", "within-power")' in badge_line
    assert 'Read plan.backend = "greedy" from' in backend_line


def test_a_different_backend_can_rank_a_different_plan_which_moves_tier2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Across backends the name is not all that moves, so tier 2 can differ on one card id.

    By hand at 10 Relic a minute: R_D alone, 2 Ore to 1 Relic, is 1 machine at 20 Ore,
    the raw optimum exhaustive finds. Greedy's raw walk probes R_B, 1 Rare to 1 Relic, at
    a relaxed raw total of 10 against R_D's 20, commits to it, and adds R_C, 5 Ore to 1
    Rare: 2 machines at 50 Ore. Its other walks tie and take R_A, 6 Ore to 1 Relic, at
    60 Ore, so the top of its ranking under raw is the 50 Ore plan.
    """
    registry = _registry_of(
        [
            _entry("R_A", [(SOLVE_ORE_ITEM, 6)], [(SOLVE_RELIC_ITEM, 1)], path=PATHS[ROD_FROM_ORE]),
            _entry(
                "R_B", [(SOLVE_RARE_ITEM, 1)], [(SOLVE_RELIC_ITEM, 1)], path=PATHS[RELIC_DIRECT]
            ),
            _entry("R_C", [(SOLVE_ORE_ITEM, 5)], [(SOLVE_RARE_ITEM, 1)], path=PATHS[RARE_FROM_ORE]),
            _entry("R_D", [(SOLVE_ORE_ITEM, 2)], [(SOLVE_RELIC_ITEM, 1)], path=PATHS[NO_PRODUCER]),
        ]
    )
    model = _model((*DEAD_END_PATHS, PATHS[NO_PRODUCER]))
    cards = []
    for backend in (BACKEND_EXHAUSTIVE, BACKEND_GREEDY):
        monkeypatch.setenv(BACKEND_ENV_VAR, backend)
        cards.append(
            card_for(run_rule(plan_rules.ADOPT_RULE, _inputs(model, registry, _request())))
        )
    first, second = cards
    assert first is not None
    assert second is not None
    same_id = first.id == second.id
    assert same_id
    assert (
        first.tier2
        == "It makes 10.00 per minute of Desc_SolveRelic_C with 1.00 machine equivalents"
    )
    assert second.tier2 == (
        "It makes 10.00 per minute of Desc_SolveRelic_C with 2.00 machine equivalents"
    )


def test_the_backend_is_the_results_field_never_the_environment_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The environment says one name and the result another, and the result is what ran."""
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_EXHAUSTIVE)
    real = plans_module.optimize_within_bound

    def relabelled(*args: Any, **kwargs: Any) -> BoundedResult:
        bounded = real(*args, **kwargs)
        result = dataclasses.replace(bounded.result, backend=BACKEND_GREEDY)
        return dataclasses.replace(bounded, result=result)

    monkeypatch.setattr(plans_module, "optimize_within_bound", relabelled)

    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), _request())

    assert offered["plan.backend"].value == BACKEND_GREEDY
    assert offered["plan.backend"].source == "solve.optimize.optimize_result.backend"


class _ItemsTuple(tuple[str, ...]):
    """A tuple by inheritance and not exactly one, as a request's raw items may not be."""

    __slots__ = ()


class _ItemKey(str):
    """A str by inheritance and not exactly one, as an item key may not be."""

    __slots__ = ()


@pytest.mark.parametrize(
    "raw_items",
    [
        pytest.param(SOLVE_ORE_ITEM, id="a-str"),
        pytest.param(None, id="none"),
        pytest.param([SOLVE_ORE_ITEM], id="a-list"),
        pytest.param((SOLVE_ORE_ITEM, 1), id="a-non-str-member"),
        pytest.param(_ItemsTuple((SOLVE_ORE_ITEM,)), id="a-tuple-subclass"),
        pytest.param((_ItemKey(SOLVE_ORE_ITEM),), id="a-str-subclass-member"),
    ],
)
def test_raw_items_that_are_not_a_tuple_of_str_are_malformed(
    raw_items: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A str read as no raw item at all, a false no-plan, and None raised out of the offer.

    Refused before any solve, for the reason the targets arm below gives.
    """
    _refuse_every_door(monkeypatch)
    request = dataclasses.replace(_request(), raw_items=raw_items)

    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), request)

    assert offered["plan.status"].value == STATUS_REQUEST_MALFORMED


@pytest.mark.parametrize(
    "targets",
    [
        pytest.param(None, id="none"),
        pytest.param([SOLVE_RELIC_ITEM], id="a-list"),
        pytest.param({1: RELIC_RATE}, id="a-non-str-key"),
        pytest.param({_ItemKey(SOLVE_RELIC_ITEM): RELIC_RATE}, id="a-str-subclass-key"),
    ],
)
def test_targets_that_are_not_a_mapping_keyed_by_str_are_malformed(
    targets: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A status and never a crash, because inputs_of does not catch what plan_offer raises.

    Refused before any solve: a str subclass does read malformed from the exact audit's
    own refusal further down, so only the door standing closed shows this check answered.
    """
    _refuse_every_door(monkeypatch)
    request = dataclasses.replace(_request(), targets=targets)

    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), request)

    assert offered["plan.status"].value == STATUS_REQUEST_MALFORMED


def test_no_raw_items_at_all_is_request_malformed(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty tuple is a tuple of str, and names nothing to start from (CS-1371).

    A search over no raw items would read no-plan and speak for the kept set about a question
    nobody can answer, so it never runs: every door stands closed, and none is reached.
    """
    _refuse_every_door(monkeypatch)
    request = dataclasses.replace(_request(), raw_items=())

    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), request)

    assert offered["plan.status"].value == STATUS_REQUEST_MALFORMED
    assert offered["plan.redesign.status"].value == "not-reached"
    # The control: one raw item, and the same closed door is reached.
    with pytest.raises(_DoorReachedError):
        plan_offer(_unlocks(ASCENT_PATHS), _registry(), _request())


def _crossed_optima_registry() -> Registry:
    """A world where the buildings and power optima are different plans.

    Every cycle is six seconds, ten a minute. An assembler draws 15 MW and a smelter 4.
    By hand at 10 Relic a minute:

    - R_X in an assembler, 6 Ore to 1 Relic: 1 machine, 15 MW, 60 Ore;
    - R_Y1 and R_Y2 in smelters, 1 Rare to 1 Relic and 1 Ore to 1 Rare: 2 machines,
      8 MW, 10 Ore.

    Returns:
        The registry.
    """
    smelter = (SOLVE_SMELTER_BUILDING,)
    return _registry_of(
        [
            _entry(
                CROSSED_X, [(SOLVE_ORE_ITEM, 6)], [(SOLVE_RELIC_ITEM, 1)], path=PATHS[RELIC_DIRECT]
            ),
            _entry(
                CROSSED_Y1,
                [(SOLVE_RARE_ITEM, 1)],
                [(SOLVE_RELIC_ITEM, 1)],
                path=PATHS[RELIC_FROM_RARE],
                buildings=smelter,
            ),
            _entry(
                CROSSED_Y2,
                [(SOLVE_ORE_ITEM, 1)],
                [(SOLVE_RARE_ITEM, 1)],
                path=PATHS[RARE_FROM_ORE],
                buildings=smelter,
            ),
        ]
    )


@pytest.mark.parametrize(
    ("direction", "steps", "rows"),
    [
        pytest.param(
            OBJECTIVE_BUILDINGS,
            [CROSSED_X],
            [
                (RUNG_WITHIN_RAW, False, Fraction(60), Fraction(10), NOT_CLEARED_OVER_BOUND),
                (RUNG_WITHIN_BUILDINGS, True, Fraction(1), Fraction(1), ""),
                (RUNG_WITHIN_POWER, False, Fraction(15), Fraction(8), NOT_CLEARED_OVER_BOUND),
            ],
            id=OBJECTIVE_BUILDINGS,
        ),
        pytest.param(
            OBJECTIVE_POWER,
            [CROSSED_Y1, CROSSED_Y2],
            [
                (RUNG_WITHIN_RAW, True, Fraction(10), Fraction(10), ""),
                (RUNG_WITHIN_BUILDINGS, False, Fraction(2), Fraction(1), NOT_CLEARED_OVER_BOUND),
                (RUNG_WITHIN_POWER, True, Fraction(8), Fraction(8), ""),
            ],
            id=OBJECTIVE_POWER,
        ),
    ],
)
def test_the_buildings_and_power_rungs_are_graded_apart(
    direction: str, steps: list[str], rows: list[tuple[str, bool, Fraction, Fraction, str]]
) -> None:
    """Each rung against its own optimum: a world where crossing the two cannot pass."""
    offered = plan_offer(
        _unlocks(ASCENT_PATHS), _crossed_optima_registry(), _request(direction=direction)
    )

    plan = offered["plan.production"].value
    assert [step.recipe_key for step in plan.steps] == steps  # type: ignore[attr-defined]
    assert _measured(_badge_of(offered)) == rows


@pytest.mark.parametrize("door", SOLVE_DOORS)
def test_a_type_error_from_the_search_raises_out_of_the_offer(
    door: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A type outside the catches is no refusal, so it never reads as a status."""

    def faulting(*_args: object, **_kwargs: object) -> object:
        raise TypeError(MARK)

    monkeypatch.setattr(plans_module, door, faulting)

    with pytest.raises(TypeError):
        plan_offer(_unlocks(ASCENT_PATHS), _registry(), _request())


def test_the_unmatched_count_is_read_on_a_refused_path() -> None:
    """The unlock path the docs do not know is counted on a no-plan as well."""
    model = _model((PATHS[RARE_FROM_ORE], SAVE_ONLY_PATH))

    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(model, _registry(), _request()))

    assert _read(trace, "plan.status") == STATUS_NO_PLAN
    assert _read(trace, "plan.unmatched_unlocks") == 1


@pytest.mark.parametrize(
    "declared",
    [
        pytest.param((SOLVE_ROD_ITEM, SOLVE_RELIC_ITEM), id="rod-first"),
        pytest.param((SOLVE_RELIC_ITEM, SOLVE_ROD_ITEM), id="relic-first"),
    ],
)
def test_a_two_target_plan_names_both_sorted_however_they_were_stated(
    declared: tuple[str, str],
) -> None:
    """By hand: 10 Relic over two stages is 2 machines, and 20 Rod is 2 more."""
    rates = {SOLVE_RELIC_ITEM: RELIC_RATE, SOLVE_ROD_ITEM: Fraction(20)}
    rod = _entry(
        ROD_FROM_ORE, [(SOLVE_ORE_ITEM, 1)], [(SOLVE_ROD_ITEM, 1)], path=PATHS[ROD_FROM_ORE]
    )
    registry = _registry_of([*_ascent_entries(), rod])
    model = _model((*ASCENT_PATHS, PATHS[ROD_FROM_ORE]))
    request = dataclasses.replace(
        _request(), targets=MappingProxyType({item: rates[item] for item in declared})
    )

    card = card_for(run_rule(plan_rules.ADOPT_RULE, _inputs(model, registry, request)))

    assert card is not None
    assert card.subject_key == "plan:Desc_SolveRelic_C+Desc_SolveRod_C"
    assert card.tier1 == (
        "Build the planned production chain for Desc_SolveRelic_C, Desc_SolveRod_C"
    )
    assert card.tier2 == (
        "It makes 10.00 per minute of Desc_SolveRelic_C, 20.00 per minute of Desc_SolveRod_C"
        " with 4.00 machine equivalents"
    )


def test_a_trimmed_search_names_what_it_dropped(tmp_path: Path) -> None:
    advice = _advise(tmp_path, _model(_padded_paths()), _padded_registry(), _request())

    card = _plan_card(advice)
    dropped = f"{PADDING_PREFIX}{_padding_count() - 1}"
    assert _card_read(card, "plan.trimmed") == (dropped,)
    named = "; the search dropped 1 recipe(s) to fit its cap" in card.tier2
    assert named
    assert f'Read plan.trimmed = ("{dropped}") from solve.bound.trim_record.removed' in card.tier3
    # Trimmed, the plan is still the two stages the kept set holds.
    plan = _card_read(card, "plan.production")
    assert plan.raw_inputs[SOLVE_ORE_ITEM] == TWO_STAGE_ORE  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "targets",
    [
        pytest.param({SOLVE_RELIC_ITEM: Fraction(0)}, id="zero"),
        pytest.param({SOLVE_RELIC_ITEM: Fraction(-1)}, id="negative"),
        pytest.param({SOLVE_RELIC_ITEM: 0.5}, id="float"),
        pytest.param({SOLVE_RELIC_ITEM: 10}, id="int"),
        pytest.param({SOLVE_RELIC_ITEM: RELIC_RATE, SOLVE_ROD_ITEM: Fraction(0)}, id="one-of-two"),
        pytest.param({}, id="no-target"),
    ],
)
def test_non_positive_targets_are_refused(
    targets: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A zero-rate Build card is absurd, and an inexact rate never reaches solve."""
    _refuse_every_door(monkeypatch)
    request = dataclasses.replace(_request(), targets=MappingProxyType(targets))

    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), request))

    assert _read(trace, "plan.status") == STATUS_REQUEST_MALFORMED
    assert card_for(trace) is None


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"direction": "fastest"}, id="direction"),
        pytest.param({"byproduct_policy": "whatever"}, id="byproduct-policy"),
    ],
)
def test_an_unknown_direction_or_policy_is_refused_before_any_solve(
    overrides: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unknown policy reaches solve as no selection at all: a false no-plan."""
    _refuse_every_door(monkeypatch)
    request = dataclasses.replace(_request(), **overrides)

    trace = run_rule(plan_rules.ADOPT_RULE, _inputs(_model(ASCENT_PATHS), _registry(), request))

    assert _read(trace, "plan.status") == STATUS_REQUEST_MALFORMED


@pytest.mark.parametrize(
    ("direction", "rung", "cleared", "machines"),
    [
        (OBJECTIVE_RAW, RUNG_WITHIN_RAW, (RUNG_WITHIN_RAW,), TWO_STAGE_MACHINES),
        (
            OBJECTIVE_BUILDINGS,
            RUNG_WITHIN_BUILDINGS,
            (RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER),
            ONE_STAGE_MACHINES,
        ),
        (
            OBJECTIVE_POWER,
            RUNG_WITHIN_POWER,
            (RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER),
            ONE_STAGE_MACHINES,
        ),
    ],
    ids=[OBJECTIVE_RAW, OBJECTIVE_BUILDINGS, OBJECTIVE_POWER],
)
def test_the_asked_direction_always_clears_its_own_rung(
    direction: str, rung: str, cleared: tuple[str, ...], machines: Fraction
) -> None:
    """The top plan IS that rung's optimum, so the reject path is unreachable from a world."""
    offered = plan_offer(_unlocks(ASCENT_PATHS), _registry(), _request(direction=direction))

    badge = _badge_of(offered)
    assert rung in badge.cleared
    assert badge.cleared == cleared
    checks = {check.strategy: check for check in badge.checks}
    assert checks[RUNG_WITHIN_BUILDINGS].score == machines
    assert offered["plan.status"].value == STATUS_RANKED


class _DoorReachedError(Exception):
    """Raised by a stand-in at a solve door, so reaching it cannot be mistaken."""


def _refuse_every_door(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any step through a solve door raise an error nothing handles."""

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise _DoorReachedError

    for door in (*SOLVE_DOORS, *ROUTE_DOORS):
        monkeypatch.setattr(plans_module, door, refuse)


def test_no_request_runs_no_solve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _refuse_every_door(monkeypatch)
    model = _model(ASCENT_PATHS)
    registry = _registry()

    advice = _advise(tmp_path, model, registry, None)

    assert _read(_plan_trace(advice), "plan.status") == STATUS_NO_TARGET
    # The control: the same stand-ins do fire once a target is stated.
    with pytest.raises(_DoorReachedError):
        _advise(tmp_path, model, registry, _request())


def rendered_derivation() -> str:
    """One card's tier 3, over a world where any order could come from a set.

    Public because :data:`CHILD_SOURCE` imports it, so the two children build the
    SAME world this process describes rather than a copy of it.

    Returns:
        The derivation. A trace with no recommendation refuses to build a card, so
        a child that fired nothing exits non-zero and the arm says so.
    """
    unlocked = (*_padded_paths(), SAVE_ONLY_PATH, SAVE_ONLY_PATH + "A", SAVE_ONLY_PATH + "B")
    trace = run_rule(
        plan_rules.ADOPT_RULE, _inputs(_model(unlocked), _padded_registry(), _request())
    )
    return Card(trace).tier3


def test_two_processes_under_different_hash_seeds_render_one_derivation() -> None:
    """A set deciding an order is stable within a process, so this takes two."""
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
        assert exit_code == 0, f"the child under PYTHONHASHSEED={seed} failed:\n{child.stderr}"
        printed.append(child.stdout.strip())

    assert printed[0].startswith("Derivation of rule plan.adopt")
    assert printed[0] == printed[1]


def test_the_surface_passes_no_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no target stated the surface asks for no plan; stated, it asks for that one.

    Both halves through the real route table, so the spy sees what the routes hand over.

    THE DECISION THIS PINS (CS-1371 arm 4). The source hands ``plan_request`` on every time,
    and with no target stated its value is None, which is the one spelling of no request:
    one call path, and no branch deciding which keyword an advisor call carries. So the no
    target half reads the keyword and finds None, and the stated half reads a request built
    by the advisor's own door.
    """
    seen: list[Mapping[str, object]] = []
    real = providers.advise_world

    def spy(*args: Any, **kwargs: Any) -> Advice:
        seen.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(providers, "advise_world", spy)
    source = providers.StoreAdviceSource(tmp_path, clock=lambda: NOW)
    model = _model(ASCENT_PATHS)
    registry = _registry()
    built = routes.build_routes(
        map_fixtures._Worlds(model),  # noqa: SLF001
        map_fixtures._Registries(registry),  # noqa: SLF001
        source,
    )
    listing = next(route.handler for route in built if route.template == advice_endpoint.ENDPOINT)

    # No target: the rule runs and fires nothing, and the spy sees no request.
    silent = listing({})

    assert silent.http_status == contract.HTTP_OK
    calls = len(seen)
    assert calls == 1
    no_request = seen[0]["plan_request"] is None
    assert no_request
    assert inspect.signature(advise_world).parameters["plan_request"].default is None
    silent_body = contract.encode(silent.payload)
    assert ADOPT_ID.encode("ascii") not in silent_body
    assert b"plan_outcome" not in silent_body

    found = source.advice(model, registry)

    assert found is not None
    no_request_either = seen[1]["plan_request"] is None
    assert no_request_either
    assert _read(_plan_trace(found), "plan.status") == STATUS_NO_TARGET
    assert _plan_cards(found) == []

    # Stated: the same route, the same spy, and the rule fires on what the spy saw.
    before = len(seen)
    stated = listing(
        {
            advice_endpoint.TARGET_PARAMETER: SOLVE_RELIC_ITEM,
            advice_endpoint.RATE_PARAMETER: str(RELIC_RATE),
            advice_endpoint.DIRECTION_PARAMETER: OBJECTIVE_RAW,
            advice_endpoint.BYPRODUCT_POLICY_PARAMETER: BYPRODUCT_BALANCED,
        }
    )

    assert stated.http_status == contract.HTTP_OK
    calls = len(seen) - before
    assert calls == 1
    request = seen[-1]["plan_request"]
    assert type(request) is PlanRequest
    assert dict(request.targets) == {SOLVE_RELIC_ITEM: RELIC_RATE}
    assert request.raw_items == registry.resource_items
    assert request.direction == OBJECTIVE_RAW
    assert request.byproduct_policy == BYPRODUCT_BALANCED
    stated_body = contract.encode(stated.payload)
    assert ADOPT_ID.encode("ascii") in stated_body
    assert b"plan_outcome" in stated_body


# ---------------------------------------------------------------------------
# What may never leak, and what plans.py may never reach
# ---------------------------------------------------------------------------


def test_an_unmatched_unlock_path_is_counted_and_never_echoed(tmp_path: Path) -> None:
    """A save's path may cross this seam as a count, on no surface as itself."""
    model = _model((*ASCENT_PATHS, SAVE_ONLY_PATH))
    registry = _registry()

    offered = plan_offer(model.unlocks, registry, _request())
    advice = _advise(tmp_path, model, registry, _request())
    card = _plan_card(advice)

    assert offered["plan.unmatched_unlocks"].value == 1
    assert "Read plan.unmatched_unlocks = 1 from advisor.plans.unmatched_unlocks" in card.tier3
    surfaces = (
        card.tier1,
        card.tier2,
        card.tier3,
        _rendered(card.trace),
        repr(advice),
        repr(card),
        repr(offered),
        repr(_inputs(model, registry, _request())),
    )
    echoed = sum(1 for surface in surfaces if "Never_Echoed" in surface)
    assert echoed == 0


class _SavePath(str):
    """A path read out of a save: it may be hashed and compared, and never become text."""

    __slots__ = ()

    def _refuse(self, *_args: object, **_kwargs: object) -> str:
        raise _SavePathRenderedError

    __str__ = _refuse
    __repr__ = _refuse
    __format__ = _refuse
    __add__ = _refuse


class _SavePathRenderedError(Exception):
    """A save's path was turned into text, which is the echo path."""


def test_the_requires_come_from_the_registry_never_from_the_save() -> None:
    """Equal strings cannot be told apart by value, so the save's side refuses to render.

    A key built from the member the join compared equal to would format it and
    raise here. Built from the registry's own string, nothing touches it.
    """
    state = _unlocks(
        (_SavePath(path) for path in (*ASCENT_PATHS, SAVE_ONLY_PATH)),
        machines=tuple(_SavePath(path) for path in MACHINE_BUILD_PATHS),
    )
    # The control: the plant does fire when a path is rendered.
    with pytest.raises(_SavePathRenderedError):
        f"{next(iter(state.recipes))}"

    offered = plan_offer(state, _registry(), _request())

    assert offered["plan.requires"].value == (
        "recipe:" + PATHS[RELIC_FROM_RARE],
        ASSEMBLER_KEY,
        "recipe:" + PATHS[RARE_FROM_ORE],
    )
    assert offered["plan.unmatched_unlocks"].value == 1


def _file_or_clock_reach(source: str) -> list[str]:
    """Every module or call in a source that could reach a file or a clock, sorted."""
    tree = ast.parse(source)
    imported = {
        name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for name in (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
        )
    }
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    return sorted(
        (imported & {"datetime", "io", "os", "pathlib", "time"})
        | (called & {"open", "read_bytes", "read_text"})
    )


def test_the_offer_takes_no_world_and_reaches_no_file_or_clock() -> None:
    """The world token cannot enter a function that is never handed the world."""
    assert tuple(inspect.signature(plan_offer).parameters) == ("unlocks", "registry", "request")
    source = Path(inspect.getfile(plans_module)).read_bytes().decode("ascii")
    assert _file_or_clock_reach(source) == []
    # The control: the same reader sees each kind of reach when it is there.
    planted = "import time\nfrom pathlib import Path\nopen('x')\nPath('y').read_bytes()\n"
    assert _file_or_clock_reach(planted) == ["open", "pathlib", "read_bytes", "time"]


def test_off_the_pin_the_plan_card_names_both_builds_and_never_settles() -> None:
    """The join does not change what every other card owes an off-pin world."""
    pin = game_pin()
    world = _inputs(_model(ASCENT_PATHS), _registry(), _request())
    off = WorldInputs(
        values={**world.values, **off_pin_build_inputs(pin, 1)}, unlocks=world.unlocks
    )

    trace = run_rule(plan_rules.ADOPT_RULE, off)
    card = card_for(trace)

    assert card is not None
    assert card.tier2.endswith(
        f"; build-mismatch: priced at the pinned build {pin}, not the save build {pin + 1}"
    )
    settled = ADOPT_ID in settled_rules((trace,))
    assert not settled


# ---------------------------------------------------------------------------
# The common-mode risk: real paths, real docs
# ---------------------------------------------------------------------------


class _JoinCounts(NamedTuple):
    """What the library arm is allowed to see: counts and closed vocabulary, nothing else.

    Attributes:
        unlocked: Recipe paths the world holds.
        joined: Of those, how many equal a registry recipe's whole path.
        automated: Automated recipes the join admits.
        status: The offer's status over one recipe made of raw items, or empty
            when the world holds no such recipe.
        requires: The keys that offer requires.
        unmet: Of those, how many the world's own unlock keys lack.
        failure: The type name of anything unexpected, or empty.
    """

    unlocked: int
    joined: int
    automated: int
    status: str
    requires: int
    unmet: int
    failure: str


def _library_registry() -> Registry | None:
    """The registry of the installed docs, or None when this machine has none.

    Returns:
        The registry, or None. Held broadly: a failure must not unwind through a
        frame holding an install path.
    """
    try:
        install, _label = locate.resolve_game_dir()
        if install is None:
            return None
        return build_registry_from_bytes(
            install.joinpath(*version.DOCS_RELATIVE_PARTS).read_bytes()
        )
    except (Exception, SystemExit):
        return None


def _library_saves() -> tuple[Path, ...]:
    """Every save on this machine, newest first, or an empty tuple.

    Returns:
        The paths. Held broadly: the account directory's NAME is personal data
        and may not unwind through a failure report.
    """
    try:
        root = locate.resolve_save_root()
        account = locate.resolve_account_dir(root) if root is not None else None
        if account is None:
            return ()
        return tuple(
            sorted(account.glob("*.sav"), key=lambda path: path.stat().st_mtime, reverse=True)
        )
    except (Exception, SystemExit):
        return ()


def _library_save_unlocks(path: Path) -> UnlockState | None:
    """One save's unlock state, or None when the reader refuses it.

    Args:
        path: The save.

    Returns:
        The state, whose repr renders counts only. Held broadly: a narrower catch
        lets an unexpected type escape carrying the save's bytes.
    """
    try:
        return load_world_from_bytes(path.read_bytes()).unlocks
    except (Exception, SystemExit):
        return None


def _library_unlocks(saves: tuple[Path, ...]) -> UnlockState | None:
    """The unlock state of the newest save the reader accepts, or None.

    Args:
        saves: The candidates, newest first.

    Returns:
        The state.
    """
    for path in saves:
        unlocks = _library_save_unlocks(path)
        if unlocks is not None:
            return unlocks
    return None


def _a_machine_is_held(
    registry: Registry, buildings: tuple[str, ...], unlocks: UnlockState
) -> bool:
    """Whether the world holds the build recipe of any of these machines, by whole path.

    Args:
        registry: The installed docs' registry.
        buildings: A recipe's machines.
        unlocks: The world's unlock state.

    Returns:
        A bool, so nothing from the save leaves this helper.
    """
    costs = (build_cost(registry, building) for building in buildings)
    return any(
        cost is not None and registry.recipes[cost.recipe_key].asset_path in unlocks.recipes
        for cost in costs
    )


def _join_counts(registry: Registry, unlocks: UnlockState) -> _JoinCounts:
    """Count the join over one real world, and offer one real plan.

    The target is the first joined recipe made wholly of raw items - no automated
    recipe produces them - that a machine the world holds runs, so a plan exists and
    no chain has to survive the trim. A world can hold such a recipe with no machine.

    Args:
        registry: The installed docs' registry.
        unlocks: The world's unlock state.

    Returns:
        The counts.
    """
    paths = {recipe.asset_path for recipe in registry.recipes.values()}
    automated_all = automated_recipes(registry)
    automated = [recipe for recipe in automated_all if recipe.asset_path in unlocks.recipes]
    produced = {output.item_key for recipe in automated_all for output in recipe.outputs}
    raw = sorted(item for item in registry.items if item not in produced)
    simple = [
        recipe
        for recipe in automated
        if recipe.inputs
        and all(entry.item_key in raw for entry in recipe.inputs)
        and _a_machine_is_held(registry, recipe.produced_in, unlocks)
    ]
    status = ""
    requires = unmet = 0
    if simple:
        offered = plan_offer(
            unlocks,
            registry,
            PlanRequest(
                targets=MappingProxyType({simple[0].outputs[0].item_key: Fraction(1)}),
                raw_items=tuple(raw),
                byproduct_policy=BYPRODUCT_SINKABLE,
                direction=OBJECTIVE_RAW,
            ),
        )
        read = offered["plan.status"].value
        status = read if type(read) is str else ""
        keys = offered["plan.requires"].value if "plan.requires" in offered else ()
        assert isinstance(keys, tuple)
        requires = len(keys)
        unmet = len(set(keys) - unlock_keys(unlocks))
    return _JoinCounts(
        unlocked=len(unlocks.recipes),
        joined=sum(1 for path in unlocks.recipes if path in paths),
        automated=len(automated),
        status=status,
        requires=requires,
        unmet=unmet,
        failure="",
    )


def _library_join() -> _JoinCounts | None:
    """Join the installed docs against the newest readable save, counts only.

    Returns:
        The counts, or None when this machine has no docs or no readable save.
    """
    registry = _library_registry()
    saves = _library_saves()
    if registry is None or not saves:
        return None
    unlocks = _library_unlocks(saves)
    if unlocks is None:
        return None
    try:
        return _join_counts(registry, unlocks)
    except (Exception, SystemExit) as exc:
        return _JoinCounts(0, 0, 0, "", 0, 0, type(exc).__name__)


def test_the_join_holds_on_a_library_world() -> None:
    """Real recipe paths match real docs paths, which no synthetic arm can show."""
    counts = _library_join()
    if counts is None:
        pytest.skip("no installed docs or no readable save on this machine")
    assert counts.failure == ""
    print(  # noqa: T201 - counts only, the arm's stated report
        f"unlocked {counts.unlocked} joined {counts.joined} automated {counts.automated} "
        f"status {counts.status} requires {counts.requires} unmet {counts.unmet}"
    )
    if counts.unlocked == 0:
        pytest.skip("the newest readable world has unlocked no recipe")
    assert counts.joined > 0
    assert counts.automated > 0
    if counts.status == "":
        pytest.skip("the newest readable world unlocked no recipe made of raw items")
    assert counts.status == STATUS_RANKED
    assert counts.requires > 0
    assert counts.unmet == 0
