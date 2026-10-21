"""CS-1043 S2 - the milestone model: required rates over a named budget.

Every arm builds a small SYNTHETIC ``FGSchematic`` document in this file, loads
it through the real docs_extract seam and normalizes it through
:func:`clockspeed.data.schematics.normalize_schematics`, then hands the catalog,
a synthetic two-item registry and a synthetic
:class:`clockspeed.save.world.UnlockState` to the module under test. No game
install and no save file is needed, and no slice of real game data is checked
in (CLAUDE.md section 7). Every class name and amount below is authored here.

THE ORACLE IS INDEPENDENT OF THE MODULE. The expected rates are written as
``Fraction(amount, TWO_HOURS_IN_MINUTES)`` with the two-hour figure spelled in
THIS file, never read back off the module's constant - an expectation computed
from the constant under test moves with it and could never redden when the
budget moves, which is the CS-1039 vacuity shape by name.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.data.docs_extract import DocsDocument
from clockspeed.data.registry import FORM_SOLID, Item, Registry
from clockspeed.data.schematics import (
    CostLine,
    Schematic,
    SchematicCatalog,
    normalize_schematics,
)
from clockspeed.progress import milestones
from clockspeed.save.world import UnlockState
from clockspeed.solve.exact import InexactValueError, audit_exact
from tests.data import synthetic
from tests.solve.test_phase3_gate import inexact_violations

# ---------------------------------------------------------------------------
# The synthetic corpus, authored here
# ---------------------------------------------------------------------------

KEY_COST: Final = "mCost"
KEY_TECH_TIER: Final = "mTechTier"
KEY_TYPE: Final = "mType"
KEY_DEPENDENCIES: Final = "mSchematicDependencies"
KEY_DISPLAY_NAME: Final = "mDisplayName"

#: Two hours in minutes, spelled here as the oracle rather than imported.
TWO_HOURS_IN_MINUTES: Final = 120
#: A moved budget, one hour in minutes, planted by the budget-moved arm.
MOVED_BUDGET_MINUTES: Final = 60

NEAR_MILESTONE: Final = "Schematic_SynthTierOne_C"
FAR_MILESTONE: Final = "Schematic_SynthTierSix_C"
#: The far milestone's tier, as the document writes it.
FAR_TIER: Final = 6
FREE_MILESTONE: Final = "Schematic_SynthFree_C"
FLAGGED_MILESTONE: Final = "Schematic_SynthAmountless_C"
GHOST_MILESTONE: Final = "Schematic_SynthGhostCost_C"
ABSENT_MILESTONE: Final = "Schematic_SynthNeverDeclared_C"

PLATE_ITEM: Final = "Desc_SynthPlate_C"
ROTOR_ITEM: Final = "Desc_SynthRotor_C"
#: A cost item the synthetic registry deliberately does not declare.
GHOST_ITEM: Final = "Desc_SynthGhost_C"
PLATE_AMOUNT: Final = 50
ROTOR_AMOUNT: Final = 7
GHOST_AMOUNT: Final = 3
#: How many cost lines the ghost milestone spends on the ghost item.
GHOST_LINES: Final = 2

TYPE_MILESTONE: Final = "EST_Milestone"

MODULE_SOURCE: Final = Path(milestones.__file__)


def schematic_entry(class_name: str, **fields: Any) -> dict[str, Any]:
    """Build one schematic entry with the modelled fields defaulted to a valid reading.

    Args:
        class_name: The entry's ClassName.
        **fields: Field overrides, keyed by the document's own field name.

    Returns:
        The entry mapping.
    """
    entry: dict[str, Any] = {
        synthetic.KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: "Synthetic Milestone",
        KEY_COST: "",
        KEY_TECH_TIER: "1",
        KEY_TYPE: TYPE_MILESTONE,
        KEY_DEPENDENCIES: [],
    }
    entry.update(fields)
    return entry


def schematic_document(entries: Sequence[Mapping[str, Any]]) -> DocsDocument:
    """Load schematic entries through the real docs_extract seam.

    Args:
        entries: The FGSchematic Classes entries.

    Returns:
        The loaded document.
    """
    group = {
        synthetic.KEY_NATIVE_CLASS: (
            f"/Script/CoreUObject.Class'/Script/FactoryGame.{synthetic.SCHEMATIC_GROUP}'"
        ),
        synthetic.KEY_CLASSES: list(entries),
    }
    return synthetic.document_from([group])


def near_entry(*, reverse_cost: bool = False) -> dict[str, Any]:
    """Build the tier-1 milestone costing plates and rotors.

    Args:
        reverse_cost: List the two cost lines in the opposite order.

    Returns:
        The entry.
    """
    pairs = [(PLATE_ITEM, PLATE_AMOUNT), (ROTOR_ITEM, ROTOR_AMOUNT)]
    if reverse_cost:
        pairs.reverse()
    return schematic_entry(
        NEAR_MILESTONE, **{KEY_COST: synthetic.amount_blob(pairs), KEY_TECH_TIER: "1"}
    )


def far_entry() -> dict[str, Any]:
    """Build the tier-6 milestone costing rotors alone.

    Returns:
        The entry.
    """
    return schematic_entry(
        FAR_MILESTONE,
        **{
            KEY_COST: synthetic.amount_blob([(ROTOR_ITEM, ROTOR_AMOUNT)]),
            KEY_TECH_TIER: str(FAR_TIER),
        },
    )


def milestone_catalog() -> SchematicCatalog:
    """Build the two-milestone synthetic catalog most arms read.

    Returns:
        The normalized catalog.
    """
    return normalize_schematics(schematic_document([near_entry(), far_entry()]))


def synthetic_registry() -> Registry:
    """Build a registry declaring the plate and the rotor, and NOT the ghost.

    Returns:
        The registry.
    """
    items = {
        key: Item(
            key=key,
            display_name=key,
            form=FORM_SOLID,
            energy_value=None,
            sink_points=None,
            is_fluid=False,
        )
        for key in (PLATE_ITEM, ROTOR_ITEM)
    }
    return Registry(
        items=MappingProxyType(items),
        recipes=MappingProxyType({}),
        buildings=MappingProxyType({}),
        warnings=(),
        unknown_groups=(),
    )


def unlock_state(trading_post_level: int | None = None) -> UnlockState:
    """Build a synthetic unlock state that has purchased nothing.

    Args:
        trading_post_level: The HUB tier to plant, or None - which is what
            every real load publishes today.

    Returns:
        The unlock state.
    """
    return UnlockState(
        purchased_schematics=frozenset(),
        recipes=frozenset(),
        current_game_phase=None,
        feature_flags=MappingProxyType({}),
        scanned_resources=frozenset(),
        trading_post_level=trading_post_level,
    )


def near_requirement() -> milestones.MilestoneRequirement:
    """Build the near milestone's requirement over the shared fixtures.

    Returns:
        The requirement.
    """
    return milestones.milestone_requirement(
        milestone_catalog(), synthetic_registry(), unlock_state(), NEAR_MILESTONE
    )


# ---------------------------------------------------------------------------
# A1 and A2 - each required rate is exactly cost over the NAMED budget
# ---------------------------------------------------------------------------


def test_a_required_rate_is_cost_over_the_named_budget() -> None:
    """Each cost line's required rate is its amount over two hours, exactly.

    The expected values are computed from :data:`TWO_HOURS_IN_MINUTES`, spelled
    in this file, so the arm reddens when the module's budget moves.
    """
    plan = near_requirement()
    assert plan.reason is None
    assert plan.rates is not None
    expected = {
        PLATE_ITEM: Fraction(PLATE_AMOUNT, TWO_HOURS_IN_MINUTES),
        ROTOR_ITEM: Fraction(ROTOR_AMOUNT, TWO_HOURS_IN_MINUTES),
    }
    assert dict(plan.rates) == expected
    rate_types = sorted({type(rate).__name__ for rate in plan.rates.values()})
    assert rate_types == ["Fraction"]
    assert plan.budget_minutes == Fraction(TWO_HOURS_IN_MINUTES)
    assert type(plan.budget_minutes) is Fraction


def test_a_required_rate_follows_the_budget_when_it_moves(monkeypatch: pytest.MonkeyPatch) -> None:
    """Moving the NAMED budget moves every rate, so no literal sits at the site.

    The module's constant is replaced with one hour; a division that read a
    literal instead of the constant would still answer over two hours and this
    arm would redden.

    Args:
        monkeypatch: Replaces the module's budget for this arm only.
    """
    monkeypatch.setattr(milestones, "COMPLETION_BUDGET_MINUTES", Fraction(MOVED_BUDGET_MINUTES))
    plan = near_requirement()
    assert plan.rates is not None
    expected = {
        PLATE_ITEM: Fraction(PLATE_AMOUNT, MOVED_BUDGET_MINUTES),
        ROTOR_ITEM: Fraction(ROTOR_AMOUNT, MOVED_BUDGET_MINUTES),
    }
    assert dict(plan.rates) == expected
    assert plan.budget_minutes == Fraction(MOVED_BUDGET_MINUTES)


# ---------------------------------------------------------------------------
# The HUB tier is unavailable, never zero
# ---------------------------------------------------------------------------


def test_the_hub_tier_is_unavailable_when_unread_and_never_zero() -> None:
    """An unread HUB tier is None with its reason; a read zero stays zero.

    Zero is a real onboarding tier, so the two halves are asserted together:
    a defaulted zero would pass a test that only checked the read case.
    """
    unread = milestones.hub_tier(unlock_state(None))
    assert unread.tier is None
    assert unread.reason == milestones.REASON_HUB_TIER_UNREAD
    onboarding = milestones.hub_tier(unlock_state(0))
    assert onboarding.tier == 0
    assert type(onboarding.tier) is int
    assert onboarding.reason is None
    carried = near_requirement().hub_tier
    assert carried.tier is None
    assert carried.reason == milestones.REASON_HUB_TIER_UNREAD


# ---------------------------------------------------------------------------
# Flagged and unknown content publishes null with a reason, never zero
# ---------------------------------------------------------------------------


def test_a_flagged_milestone_cost_is_null_with_a_reason_never_zero() -> None:
    """A cost the catalog flagged is None, and differs from a free milestone.

    The amount-less blob is the measured shape the catalog publishes as None.
    A free milestone costs the EMPTY mapping, which is a fact, not a flag.
    """
    amountless = f'((ItemClass="{synthetic.item_path(PLATE_ITEM)}"))'
    catalog = normalize_schematics(
        schematic_document(
            [
                schematic_entry(FLAGGED_MILESTONE, **{KEY_COST: amountless}),
                schematic_entry(FREE_MILESTONE),
            ]
        )
    )
    registry, unlocks = synthetic_registry(), unlock_state()
    flagged = milestones.milestone_requirement(catalog, registry, unlocks, FLAGGED_MILESTONE)
    assert flagged.cost is None
    assert flagged.rates is None
    assert flagged.reason == milestones.REASON_COST_UNREADABLE
    assert flagged.unresolved_lines is None
    free = milestones.milestone_requirement(catalog, registry, unlocks, FREE_MILESTONE)
    assert free.cost is not None
    assert free.rates is not None
    assert (len(free.cost), len(free.rates)) == (0, 0)
    assert free.reason is None
    assert free.unresolved_lines == 0


def test_an_unknown_target_is_null_with_a_reason_and_does_not_raise() -> None:
    """A target the catalog does not declare is None under its named reason."""
    plan = milestones.milestone_requirement(
        milestone_catalog(), synthetic_registry(), unlock_state(), ABSENT_MILESTONE
    )
    assert plan.cost is None
    assert plan.rates is None
    assert plan.tech_tier is None
    assert plan.reason == milestones.REASON_UNKNOWN_SCHEMATIC


def test_a_cost_item_the_registry_does_not_resolve_is_flagged_never_dropped() -> None:
    """An unresolved cost item is warned, counted, and nulls the rates.

    The ghost item spends two cost lines and is absent from the registry. A
    rate list that silently dropped it would read as the whole requirement,
    and a zero rate for it would be a free item reported with confidence.
    """
    pairs = [(PLATE_ITEM, PLATE_AMOUNT)] + [(GHOST_ITEM, GHOST_AMOUNT)] * GHOST_LINES
    catalog = normalize_schematics(
        schematic_document(
            [schematic_entry(GHOST_MILESTONE, **{KEY_COST: synthetic.amount_blob(pairs)})]
        )
    )
    plan = milestones.milestone_requirement(
        catalog, synthetic_registry(), unlock_state(), GHOST_MILESTONE
    )
    assert plan.rates is None
    assert plan.reason == milestones.REASON_UNRESOLVED_COST_ITEM
    assert plan.unresolved_lines == GHOST_LINES
    flagged = [(w.code, w.subject, w.count) for w in plan.warnings]
    assert flagged == [(milestones.WARN_UNRESOLVED_COST_ITEM, GHOST_ITEM, GHOST_LINES)]
    assert plan.cost is not None
    assert dict(plan.cost) == {
        GHOST_ITEM: Fraction(GHOST_AMOUNT * GHOST_LINES),
        PLATE_ITEM: Fraction(PLATE_AMOUNT),
    }
    resolved = near_requirement()
    assert resolved.unresolved_lines == 0
    assert resolved.warnings == ()


# ---------------------------------------------------------------------------
# The milestone target is a free selector
# ---------------------------------------------------------------------------


def test_any_target_may_be_selected_not_only_the_next_one() -> None:
    """A tier-6 milestone is answered directly for a world that bought nothing.

    The world has purchased nothing, so a next-milestone pointer would answer
    tier 1. The far milestone's own cost is what comes back.
    """
    plan = milestones.milestone_requirement(
        milestone_catalog(), synthetic_registry(), unlock_state(), FAR_MILESTONE
    )
    assert plan.target == FAR_MILESTONE
    assert plan.tech_tier == FAR_TIER
    assert plan.rates is not None
    assert dict(plan.rates) == {ROTOR_ITEM: Fraction(ROTOR_AMOUNT, TWO_HOURS_IN_MINUTES)}
    selected = milestones.milestone_requirements(
        milestone_catalog(), synthetic_registry(), unlock_state(), [FAR_MILESTONE]
    )
    assert [requirement.target for requirement in selected] == [FAR_MILESTONE]


# ---------------------------------------------------------------------------
# No float anywhere
# ---------------------------------------------------------------------------


def test_no_float_reaches_a_rate_or_the_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """The output audits exact, a float budget is refused, and the source scans clean.

    Three halves. The runtime audit walks the whole published model. A float
    budget must RAISE rather than divide - ``Fraction(50) / 120.0`` is a float
    with the right value, which equality alone would pass. And the module's
    source passes the phase 3 gate's AST scan, with a planted float in a copy
    of the same source as the control that the scan can see one.

    Args:
        monkeypatch: Plants the float budget for the second half only.
    """
    audit_exact(near_requirement(), path="requirement")
    monkeypatch.setattr(milestones, "COMPLETION_BUDGET_MINUTES", float(TWO_HOURS_IN_MINUTES))
    with pytest.raises(InexactValueError):
        milestones.required_rates([CostLine(PLATE_ITEM, Fraction(PLATE_AMOUNT))])
    source = MODULE_SOURCE.read_text(encoding="utf-8")
    assert inexact_violations(source) == []
    planted = inexact_violations(source + "\nPLANTED_BUDGET = 120.0\n")
    assert len(planted) == 1


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_the_same_inputs_publish_the_same_output_in_the_same_order() -> None:
    """Permuted entries, cost lines and targets publish a byte-identical result.

    Tier order then ClassName order decides the sequence, and sorted ClassName
    order decides every mapping, so nothing published takes its order from the
    document or the caller.
    """
    registry, unlocks = synthetic_registry(), unlock_state()
    forward = normalize_schematics(schematic_document([near_entry(), far_entry()]))
    backward = normalize_schematics(
        schematic_document([far_entry(), near_entry(reverse_cost=True)])
    )
    first = milestones.milestone_requirements(
        forward, registry, unlocks, [NEAR_MILESTONE, FAR_MILESTONE]
    )
    second = milestones.milestone_requirements(
        backward, registry, unlocks, [FAR_MILESTONE, NEAR_MILESTONE, FAR_MILESTONE]
    )
    assert [requirement.target for requirement in first] == [NEAR_MILESTONE, FAR_MILESTONE]
    assert repr(first) == repr(second)
    near_rates = first[0].rates
    assert near_rates is not None
    assert list(near_rates) == [PLATE_ITEM, ROTOR_ITEM]


# ---------------------------------------------------------------------------
# Repair arms - each written against a mutant that survived the first suite
# ---------------------------------------------------------------------------

#: The amount basis as published, spelled here so a relabel reddens.
AMOUNT_BASIS_SPELLING: Final = "as-written"
ZERO_MILESTONE: Final = "Schematic_SynthZeroCost_C"


def test_requirements_are_ordered_by_tier_whatever_order_the_caller_gives() -> None:
    """A caller order that is the exact reverse of the answer is still sorted.

    The targets arrive unknown first, then tier 6, then tier 1, and the answer
    is tier 1, tier 6, unknown last. The order a caller gives is fixed and
    adversarial, so an implementation that echoed it reddens under every hash
    seed rather than on a coin flip.
    """
    published = milestones.milestone_requirements(
        milestone_catalog(),
        synthetic_registry(),
        unlock_state(),
        [ABSENT_MILESTONE, FAR_MILESTONE, NEAR_MILESTONE, FAR_MILESTONE],
    )
    order = [requirement.target for requirement in published]
    assert order == [NEAR_MILESTONE, FAR_MILESTONE, ABSENT_MILESTONE]


@pytest.mark.parametrize("amount", [0, -5])
def test_a_non_positive_milestone_cost_is_null_never_a_zero_rate(amount: int) -> None:
    """A zero or negative amount publishes None with a reason, as a phase does.

    Through the document, the catalog flags the amount and the cost arrives as
    None. Through a hand-built catalog that skips that flag, this model's own
    guard still refuses to publish a zero or negative rate.

    Args:
        amount: The non-positive amount planted on the plate line.
    """
    flagged_doc = schematic_document(
        [
            schematic_entry(
                ZERO_MILESTONE, **{KEY_COST: synthetic.amount_blob([(PLATE_ITEM, amount)])}
            )
        ]
    )
    registry, unlocks = synthetic_registry(), unlock_state()
    through_doc = milestones.milestone_requirement(
        normalize_schematics(flagged_doc), registry, unlocks, ZERO_MILESTONE
    )
    assert through_doc.rates is None
    assert through_doc.reason == milestones.REASON_COST_UNREADABLE
    unflagged = Schematic(
        class_name=ZERO_MILESTONE,
        tech_tier=1,
        type_token=TYPE_MILESTONE,
        cost=(CostLine(PLATE_ITEM, Fraction(amount)), CostLine(ROTOR_ITEM, Fraction(ROTOR_AMOUNT))),
        purchase_dependencies=(),
        phase_dependency=None,
        dependencies_complete=True,
    )
    catalog = SchematicCatalog(
        schematics=MappingProxyType({ZERO_MILESTONE: unflagged}),
        warnings=(),
        entries_offered=1,
        entries_skipped=0,
        costs_parsed=1,
        costs_flagged=0,
    )
    guarded = milestones.milestone_requirement(catalog, registry, unlocks, ZERO_MILESTONE)
    assert guarded.rates is None
    assert guarded.cost is None
    assert guarded.reason == milestones.REASON_NONPOSITIVE_COST


def test_the_amount_basis_is_pinned_by_its_exact_spelling() -> None:
    """The published unit basis is a fixed spelling, not whatever the constant holds."""
    assert near_requirement().amount_basis == AMOUNT_BASIS_SPELLING


def test_every_milestone_reason_code_is_distinct() -> None:
    """No two REASON_* constants share a spelling, so a reason names one cause."""
    codes = [getattr(milestones, name) for name in milestones.__all__ if name.startswith("REASON_")]
    assert len(codes) == len(set(codes))
    assert len(codes) > 1


# ---------------------------------------------------------------------------
# CS-1339 - the non-positive guard reads every cost line, not only the first
# ---------------------------------------------------------------------------

#: Two hand-built costs whose non-positive line comes SECOND. The first is
#: second in source order only - the plate sorts before the rotor, so it is
#: first in the guard's sorted totals. The second is second in source order
#: AND in sorted ClassName order. The arm above always plants the bad line
#: first, so a guard that read only the first line, in either order, passed it.
LATER_NONPOSITIVE_COSTS: Final = (
    (CostLine(ROTOR_ITEM, Fraction(ROTOR_AMOUNT)), CostLine(PLATE_ITEM, Fraction(0))),
    (CostLine(PLATE_ITEM, Fraction(PLATE_AMOUNT)), CostLine(ROTOR_ITEM, Fraction(0))),
)


@pytest.mark.parametrize(
    "cost",
    LATER_NONPOSITIVE_COSTS,
    ids=["second-in-source-order", "second-in-source-and-sorted-order"],
)
def test_a_non_positive_amount_on_a_later_cost_line_is_flagged_and_published_null(
    cost: tuple[CostLine, ...],
) -> None:
    """A zero on the second cost line nulls the requirement, as one on the first does.

    The catalog is hand-built, as in the arm above, so the catalog's own amount
    flag is skipped and this model's guard alone stands between the zero and a
    published zero rate.

    Args:
        cost: The two cost lines, the non-positive one second.
    """
    assert PLATE_ITEM < ROTOR_ITEM
    first_amount, second_amount = cost[0].amount, cost[1].amount
    assert first_amount > 0
    assert second_amount == 0
    unflagged = Schematic(
        class_name=ZERO_MILESTONE,
        tech_tier=1,
        type_token=TYPE_MILESTONE,
        cost=cost,
        purchase_dependencies=(),
        phase_dependency=None,
        dependencies_complete=True,
    )
    catalog = SchematicCatalog(
        schematics=MappingProxyType({ZERO_MILESTONE: unflagged}),
        warnings=(),
        entries_offered=1,
        entries_skipped=0,
        costs_parsed=1,
        costs_flagged=0,
    )
    plan = milestones.milestone_requirement(
        catalog, synthetic_registry(), unlock_state(), ZERO_MILESTONE
    )
    reason = plan.reason
    assert reason == milestones.REASON_NONPOSITIVE_COST
    rates_withheld = plan.rates is None
    assert rates_withheld
    cost_withheld = plan.cost is None
    assert cost_withheld
    unresolved_lines = plan.unresolved_lines
    assert unresolved_lines is None
