"""CS-1237 - the fixed-order constraint-relaxation ladder over pillar 2.

Every case is built from the synthetic solve corpus and reaches the optimizer
only through ``optimize_plan``, the same door every other caller uses. Each
infeasible case first PROVES it is infeasible as stated, through that door, so a
test cannot pass because the ladder solved a request that never needed it.

The cases, and which constraint each one is built to need:

- C3 with ``R_Recover`` locked under ``balanced``: the residue has no consumer,
  so the Gadget is forced to zero. Venting the residue OR unlocking the recovery
  recipe would each fix it on its own - which is exactly what makes it the order
  test: the ladder must report the byproduct rung, because that rung comes first.
- C5 with ``Std_Gadget`` locked: the only feasible recipe is locked, and no
  byproduct policy helps, so only admitting it does.
- C3 minus ``R_Recover`` with ``R_Plate`` locked under ``balanced``: needs BOTH
  rungs at once, so it separates a cumulative ladder from a single-rung one.
- C7: no rung can supply an item nothing produces, so the ladder is exhausted.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType

import pytest

from clockspeed.data.registry import Registry
from clockspeed.solve.backends import BACKEND_EXHAUSTIVE, BACKEND_GREEDY
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.optimize import (
    NoFeasibleSelectionError,
    OptimizeRequest,
    SolveConfig,
    optimize_plan,
    registry_order,
    weighted_objective,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    BYPRODUCT_SINKABLE,
    ByproductPolicyRequired,
)
from clockspeed.solve.relax import (
    RELAXATION_LADDER,
    RUNG_ADMIT_LOCKED,
    RUNG_BYPRODUCT_SINKABLE,
    LadderExhaustedError,
    RelaxationStep,
    RelaxedResult,
    optimize_with_relaxation,
)
from tests.solve.synthetic import (
    ALT_GADGET_RECIPE,
    C3_GADGET_TARGET,
    C5_TRINKET_TARGET,
    FLUID_RECIPE,
    GADGET_RECIPE,
    ORPHAN_RECIPE,
    PLATE_RECIPE,
    RECOVER_RECIPE,
    SOLVE_GADGET_ITEM,
    SOLVE_ORE_ITEM,
    SOLVE_RELIC_ITEM,
    SOLVE_RESIDUE_ITEM,
    SOLVE_TRINKET_ITEM,
    STD_GADGET_RECIPE,
    solve_registry,
)

UNIT: Fraction = Fraction(1)
BOTH_BACKENDS: tuple[str, ...] = (BACKEND_EXHAUSTIVE, BACKEND_GREEDY)

#: The ladder as this test pins it. Reordering ``RELAXATION_LADDER`` reddens
#: :func:`test_the_ladder_order_is_one_pinned_table`; it also reddens
#: :func:`test_the_first_relaxed_constraint_is_the_first_rung_that_applies`,
#: whose request either rung alone would make feasible.
EXPECTED_LADDER: tuple[tuple[str, str], ...] = (
    (RUNG_BYPRODUCT_SINKABLE, "byproduct_policy"),
    (RUNG_ADMIT_LOCKED, "unlocked"),
)

C3_LOOP: tuple[str, ...] = (GADGET_RECIPE, RECOVER_RECIPE, FLUID_RECIPE, PLATE_RECIPE)
C3_WITHOUT_RECOVER: tuple[str, ...] = (GADGET_RECIPE, FLUID_RECIPE, PLATE_RECIPE)
C5_PAIR: tuple[str, ...] = (ALT_GADGET_RECIPE, STD_GADGET_RECIPE)

BYPRODUCT_STEP: RelaxationStep = RelaxationStep(
    rung=RUNG_BYPRODUCT_SINKABLE,
    field="byproduct_policy",
    removed=(BYPRODUCT_BALANCED,),
    added=(BYPRODUCT_SINKABLE,),
)


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Build the synthetic solve registry once for the module.

    Returns:
        The registry.
    """
    return solve_registry()


def _c3(backend: str, *, candidates: tuple[str, ...], unlocked: tuple[str, ...]) -> OptimizeRequest:
    """Build a C3-shaped request for 20 Gadget/min under ``balanced``.

    Args:
        backend: The backend name for the config.
        candidates: The candidate recipe keys.
        unlocked: The recipe keys declared unlocked.

    Returns:
        The request.
    """
    return OptimizeRequest(
        targets=MappingProxyType({SOLVE_GADGET_ITEM: C3_GADGET_TARGET}),
        candidates=candidates,
        unlocked=unlocked,
        raw_items=(SOLVE_ORE_ITEM,),
        byproduct_policy=BYPRODUCT_BALANCED,
        objective=weighted_objective(raw=UNIT, buildings=UNIT),
        config=SolveConfig(backend=backend),
    )


def _c5(backend: str, *, unlocked: tuple[str, ...], policy: str) -> OptimizeRequest:
    """Build a C5-shaped request for 30 Trinket/min.

    Args:
        backend: The backend name for the config.
        unlocked: The recipe keys declared unlocked.
        policy: The byproduct policy.

    Returns:
        The request.
    """
    return OptimizeRequest(
        targets=MappingProxyType({SOLVE_TRINKET_ITEM: C5_TRINKET_TARGET}),
        candidates=C5_PAIR,
        unlocked=unlocked,
        raw_items=(SOLVE_ORE_ITEM,),
        byproduct_policy=policy,
        objective=weighted_objective(raw=UNIT, buildings=UNIT),
        config=SolveConfig(backend=backend),
    )


def _orphan(*, unlocked: tuple[str, ...], policy: str) -> OptimizeRequest:
    """Build the C7 request: a Relic nothing upstream can ever supply.

    Args:
        unlocked: The recipe keys declared unlocked.
        policy: The byproduct policy.

    Returns:
        The request, with ``R_Plate`` as a second candidate so a locked one
        exists for the admit rung to admit.
    """
    return OptimizeRequest(
        targets=MappingProxyType({SOLVE_RELIC_ITEM: UNIT}),
        candidates=(ORPHAN_RECIPE, PLATE_RECIPE),
        unlocked=unlocked,
        raw_items=(SOLVE_ORE_ITEM,),
        byproduct_policy=policy,
        objective=weighted_objective(raw=UNIT),
        config=SolveConfig(backend=BACKEND_EXHAUSTIVE),
    )


def _assert_infeasible_as_stated(registry: Registry, request: OptimizeRequest) -> None:
    """Prove through the ordinary door that the request needs relaxing at all.

    Args:
        registry: The built registry.
        request: The request.
    """
    with pytest.raises(NoFeasibleSelectionError):
        optimize_plan(registry, request)


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------


def test_the_ladder_order_is_one_pinned_table() -> None:
    """The rung names and the field each loosens, in order, are exactly the pin."""
    assert tuple((rung.name, rung.field) for rung in RELAXATION_LADDER) == EXPECTED_LADDER


def test_every_rung_names_a_real_request_field_and_says_what_it_loosens() -> None:
    """A rung's field is one OptimizeRequest carries, and its prose is not empty."""
    fields = set(OptimizeRequest.__dataclass_fields__)
    for rung in RELAXATION_LADDER:
        assert rung.field in fields
        assert rung.loosens.strip()


# ---------------------------------------------------------------------------
# Feasible as stated: no record
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_a_feasible_request_produces_no_relaxation_record(registry: Registry, backend: str) -> None:
    """The full C3 loop solves as stated, so nothing is relaxed and nothing reported."""
    request = _c3(backend, candidates=C3_LOOP, unlocked=C3_LOOP)

    relaxed = optimize_with_relaxation(registry, request)

    assert relaxed.record is None
    assert relaxed.result == optimize_plan(registry, request)


# ---------------------------------------------------------------------------
# Infeasible as stated: a plan plus a record naming the first relaxed constraint
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_the_first_relaxed_constraint_is_the_first_rung_that_applies(
    registry: Registry, backend: str
) -> None:
    """C3 with the recovery locked: venting the residue is the rung reported.

    Admitting ``R_Recover`` would ALSO make this feasible, so a ladder that tried
    the admit rung first would report it instead - the behavioural half of the
    order pin.
    """
    request = _c3(backend, candidates=C3_LOOP, unlocked=C3_WITHOUT_RECOVER)
    _assert_infeasible_as_stated(registry, request)

    relaxed = optimize_with_relaxation(registry, request)

    assert relaxed.record is not None
    assert relaxed.record.steps == (BYPRODUCT_STEP,)
    assert relaxed.record.first == BYPRODUCT_STEP
    assert relaxed.result.selection == registry_order(registry, C3_WITHOUT_RECOVER)
    assert SOLVE_RESIDUE_ITEM in relaxed.result.plan.byproducts
    assert relaxed.result == optimize_plan(
        registry, replace(request, byproduct_policy=BYPRODUCT_SINKABLE)
    )


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_admitting_locked_candidates_names_exactly_the_admitted_recipes(
    registry: Registry, backend: str
) -> None:
    """C5 with Std_Gadget locked: the admit rung reports the one recipe it admitted.

    The policy is already ``sinkable``, so the byproduct rung would change
    nothing; it is skipped and NOT reported.
    """
    request = _c5(backend, unlocked=(ALT_GADGET_RECIPE,), policy=BYPRODUCT_SINKABLE)
    _assert_infeasible_as_stated(registry, request)

    relaxed = optimize_with_relaxation(registry, request)

    assert relaxed.record is not None
    assert relaxed.record.steps == (
        RelaxationStep(
            rung=RUNG_ADMIT_LOCKED,
            field="unlocked",
            removed=(),
            added=(STD_GADGET_RECIPE,),
        ),
    )
    assert relaxed.result.selection == (STD_GADGET_RECIPE,)
    assert relaxed.result.excluded == ()


def test_the_ladder_is_cumulative(registry: Registry) -> None:
    """A request needing BOTH rungs is answered, and the record lists both in order.

    C3 without the recovery and with ``R_Plate`` locked: venting alone leaves no
    Plate, and admitting the Plate alone leaves the residue unbalanced - proved
    below through the ordinary door - so only the two together solve.
    """
    request = _c3(
        BACKEND_EXHAUSTIVE, candidates=C3_WITHOUT_RECOVER, unlocked=C3_WITHOUT_RECOVER[:2]
    )
    _assert_infeasible_as_stated(registry, request)
    _assert_infeasible_as_stated(registry, replace(request, byproduct_policy=BYPRODUCT_SINKABLE))
    _assert_infeasible_as_stated(registry, replace(request, unlocked=C3_WITHOUT_RECOVER))

    relaxed = optimize_with_relaxation(registry, request)

    assert relaxed.record is not None
    assert relaxed.record.steps == (
        BYPRODUCT_STEP,
        RelaxationStep(rung=RUNG_ADMIT_LOCKED, field="unlocked", removed=(), added=(PLATE_RECIPE,)),
    )
    assert relaxed.record.first == BYPRODUCT_STEP
    assert relaxed.result == optimize_plan(
        registry,
        replace(request, byproduct_policy=BYPRODUCT_SINKABLE, unlocked=C3_WITHOUT_RECOVER),
    )


# ---------------------------------------------------------------------------
# Every rung failing
# ---------------------------------------------------------------------------


def test_every_rung_failing_refuses_and_names_every_rung_tried(registry: Registry) -> None:
    """C7 cannot be rescued; the refusal names both rungs, in ladder order."""
    request = _orphan(unlocked=(ORPHAN_RECIPE,), policy=BYPRODUCT_BALANCED)

    with pytest.raises(LadderExhaustedError) as caught:
        optimize_with_relaxation(registry, request)

    assert caught.value.tried == (RUNG_BYPRODUCT_SINKABLE, RUNG_ADMIT_LOCKED)
    assert isinstance(caught.value, NoFeasibleSelectionError)
    for name in caught.value.tried:
        assert name in str(caught.value)


def test_a_rung_that_changes_nothing_is_not_tried(registry: Registry) -> None:
    """With nothing locked and the policy already sinkable, no rung applies at all."""
    request = _orphan(unlocked=(ORPHAN_RECIPE, PLATE_RECIPE), policy=BYPRODUCT_SINKABLE)

    with pytest.raises(LadderExhaustedError) as caught:
        optimize_with_relaxation(registry, request)

    assert caught.value.tried == ()


def test_a_refusal_that_is_not_infeasibility_is_not_relaxed(registry: Registry) -> None:
    """An unusable policy is a malformed request, not an infeasible one.

    ``solve_selection`` absorbs every pillar 1 refusal, so through
    ``optimize_plan`` alone a misspelt policy arrives as "no selection solves" -
    and a ladder trusting that would "relax" a typo into a plan. It must be
    refused at the door instead.
    """
    request = _c5(BACKEND_EXHAUSTIVE, unlocked=C5_PAIR, policy="balance")

    with pytest.raises(ByproductPolicyRequired):
        optimize_with_relaxation(registry, request)


# ---------------------------------------------------------------------------
# Determinism and exactness
# ---------------------------------------------------------------------------


def _relaxed_cases(registry: Registry) -> tuple[RelaxedResult, ...]:
    """Run every answerable case once.

    Args:
        registry: The built registry.

    Returns:
        The relaxed results, in a fixed order.
    """
    return (
        optimize_with_relaxation(
            registry, _c3(BACKEND_EXHAUSTIVE, candidates=C3_LOOP, unlocked=C3_LOOP)
        ),
        optimize_with_relaxation(
            registry, _c3(BACKEND_EXHAUSTIVE, candidates=C3_LOOP, unlocked=C3_WITHOUT_RECOVER)
        ),
        optimize_with_relaxation(
            registry,
            _c5(BACKEND_EXHAUSTIVE, unlocked=(ALT_GADGET_RECIPE,), policy=BYPRODUCT_BALANCED),
        ),
        optimize_with_relaxation(
            registry,
            _c3(
                BACKEND_EXHAUSTIVE,
                candidates=C3_WITHOUT_RECOVER,
                unlocked=C3_WITHOUT_RECOVER[:2],
            ),
        ),
    )


def test_two_runs_agree(registry: Registry) -> None:
    """Two runs on the same inputs produce equal results with identical reprs."""
    first = _relaxed_cases(registry)
    second = _relaxed_cases(registry)

    assert first == second
    assert repr(first) == repr(second)


def test_every_numeric_leaf_is_an_exact_fraction(registry: Registry) -> None:
    """``audit_exact`` passes over every relaxed result, record included."""
    for index, relaxed in enumerate(_relaxed_cases(registry)):
        audit_exact(relaxed, path=f"relaxed[{index}]")
