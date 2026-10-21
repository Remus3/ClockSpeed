"""CS-1043 S1 - the schematic normalizer in the data layer.

Every arm builds a small SYNTHETIC ``FGSchematic`` group in this file and loads
it through the real docs_extract seam (``tests/data/synthetic.py``
``document_from``), so the suite runs on a machine with no game installed and
no slice of real game data is ever checked in (CLAUDE.md section 7). Every
class name, path and amount below is authored here.

The shapes being stood in for were measured on the shipped document by name
only: mCost is an item-amount blob or empty, and a minority carry entries with
no ``Amount=`` at all; mTechTier is an integer string; mType is an enum token;
mSchematicDependencies is a list of dicts in one of two keysets.

The document field names are spelled out HERE rather than imported from the
module under test, so a key the module misspells reddens an arm instead of
agreeing with itself.
"""

from __future__ import annotations

import ast
import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path
from typing import Any, Final

import pytest

from clockspeed.data import schematics as schematics_module
from clockspeed.data.docs_extract import DocsDocument
from clockspeed.data.schematics import (
    WARN_COST_WITHOUT_AMOUNT,
    WARN_MISSING_FIELD,
    WARN_UNKNOWN_DEPENDENCY,
    WARN_UNKNOWN_FIELD,
    WARN_UNPARSABLE_TIER,
    WARN_UNREADABLE_COST,
    CostLine,
    PhaseDependency,
    PurchaseDependency,
    SchematicCatalog,
    SchematicIntegrityError,
    SchematicWarning,
    class_name_of_path,
    normalize_schematics,
    verify_accounting,
)
from clockspeed.solve.exact import audit_exact
from tests.data import synthetic

# ---------------------------------------------------------------------------
# The synthetic corpus, authored here
# ---------------------------------------------------------------------------

KEY_COST: Final = "mCost"
KEY_TECH_TIER: Final = "mTechTier"
KEY_TYPE: Final = "mType"
KEY_DEPENDENCIES: Final = "mSchematicDependencies"
KEY_UNLOCKS: Final = "mUnlocks"
KEY_DISPLAY_NAME: Final = "mDisplayName"
KEY_DEP_CLASS: Final = "Class"
KEY_DEP_SCHEMATICS: Final = "mSchematics"
KEY_DEP_REQUIRE_ALL: Final = "mRequireAllSchematicsToBePurchased"
KEY_DEP_PHASE: Final = "mGamePhase"
KEY_DEP_ONLY_IN_PHASE: Final = "mOnlyAllowInSelectedPhase"

AMOUNTLESS_SCHEMATIC: Final = "Schematic_SynthAmountless_C"
NORMAL_SCHEMATIC: Final = "Schematic_SynthNormal_C"
FREE_SCHEMATIC: Final = "Schematic_SynthFree_C"
ABSENT_COST_SCHEMATIC: Final = "Schematic_SynthAbsentCost_C"
MALFORMED_SCHEMATIC: Final = "Schematic_SynthMalformed_C"
DEPENDENT_SCHEMATIC: Final = "Schematic_SynthDependent_C"
PREREQ_A: Final = "Schematic_SynthPrereqA_C"
PREREQ_B: Final = "Schematic_SynthPrereqB_C"
NEW_FIELD_SCHEMATIC: Final = "Schematic_SynthNewField_C"

PART_ITEM: Final = "Desc_SynthPart_C"
PLATE_ITEM: Final = "Desc_SynthPlate_C"
PART_AMOUNT: Final = 5
PLATE_AMOUNT: Final = 12

TYPE_MILESTONE: Final = "EST_Milestone"
TYPE_ALTERNATE: Final = "EST_Alternate"
TIER_TEXT: Final = "7"
TIER_VALUE: Final = 7
GAME_PHASE: Final = "EGP_SynthPhase"
NEW_FIELD: Final = "mSynthFieldNoBuildShips"

PURCHASED_CLASS_PATH: Final = (
    "/Game/Synth/Dependency/BP_SchematicPurchasedDependency.BP_SchematicPurchasedDependency_C"
)
PHASE_CLASS_PATH: Final = (
    "/Game/Synth/Dependency/BP_GamePhaseReachedDependency.BP_GamePhaseReachedDependency_C"
)
UNKNOWN_CLASS_PATH: Final = "/Game/Synth/Dependency/BP_SynthNewDependency.BP_SynthNewDependency_C"


def amountless_blob(class_names: Sequence[str]) -> str:
    """Build the measured mCost shape whose entries carry NO ``Amount=``.

    Args:
        class_names: Item class names, in source order.

    Returns:
        ``((ItemClass="<path>"),...)`` - the shape the item-amount parser
        refuses.
    """
    entries = ",".join(f'(ItemClass="{synthetic.item_path(name)}")' for name in class_names)
    return f"({entries})"


def purchase_dependency(names: Sequence[str], require_all: str = "True") -> dict[str, str]:
    """Build one purchased-schematics dependency in its measured keyset.

    Args:
        names: The prerequisite schematics' ClassNames.
        require_all: The verbatim flag spelling.

    Returns:
        The dependency mapping.
    """
    return {
        KEY_DEP_CLASS: PURCHASED_CLASS_PATH,
        KEY_DEP_SCHEMATICS: synthetic.class_path_blob([synthetic.item_path(n) for n in names]),
        KEY_DEP_REQUIRE_ALL: require_all,
    }


def phase_dependency(phase: str = GAME_PHASE, only: str = "False") -> dict[str, str]:
    """Build one game-phase dependency in its measured keyset.

    Args:
        phase: The verbatim phase token.
        only: The verbatim mOnlyAllowInSelectedPhase spelling.

    Returns:
        The dependency mapping.
    """
    return {KEY_DEP_CLASS: PHASE_CLASS_PATH, KEY_DEP_PHASE: phase, KEY_DEP_ONLY_IN_PHASE: only}


def schematic_entry(class_name: str, **fields: Any) -> dict[str, Any]:
    """Build one schematic entry with the modelled fields defaulted to a valid reading.

    Args:
        class_name: The entry's ClassName.
        **fields: Field overrides, keyed by the document's own field name. A
            value of None removes the field.

    Returns:
        The entry mapping.
    """
    entry: dict[str, Any] = {
        synthetic.KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: "Synthetic Schematic",
        KEY_COST: "",
        KEY_TECH_TIER: "0",
        KEY_TYPE: TYPE_MILESTONE,
        KEY_DEPENDENCIES: [],
        KEY_UNLOCKS: [],
    }
    for key, value in fields.items():
        if value is None:
            entry.pop(key, None)
        else:
            entry[key] = value
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


def warnings_of(catalog: SchematicCatalog, code: str, subject: str) -> list[SchematicWarning]:
    """Select the warnings one code raised about one subject.

    Args:
        catalog: The catalog.
        code: A WARN_* constant.
        subject: The subject.

    Returns:
        The matching warnings.
    """
    return [w for w in catalog.warnings if w.code == code and w.subject == subject]


def mixed_document() -> DocsDocument:
    """Build a document carrying every cost shape plus an unkeyable and a repeated entry.

    Returns:
        Seven offered entries: two parsed costs, three flagged, two skipped.
    """
    return schematic_document(
        [
            schematic_entry(
                NORMAL_SCHEMATIC,
                mCost=synthetic.amount_blob([(PART_ITEM, PART_AMOUNT), (PLATE_ITEM, PLATE_AMOUNT)]),
            ),
            schematic_entry(FREE_SCHEMATIC, mCost=""),
            schematic_entry(AMOUNTLESS_SCHEMATIC, mCost=amountless_blob([PART_ITEM, PLATE_ITEM])),
            schematic_entry(ABSENT_COST_SCHEMATIC, mCost=None),
            schematic_entry(MALFORMED_SCHEMATIC, mCost="((ItemClass=,Amount=))"),
            schematic_entry(FREE_SCHEMATIC, mCost=synthetic.amount_blob([(PART_ITEM, 1)])),
            {KEY_COST: ""},
        ]
    )


MIXED_OFFERED: Final = 7
MIXED_PARSED: Final = 2
MIXED_FLAGGED: Final = 3
MIXED_SKIPPED: Final = 2


# ---------------------------------------------------------------------------
# The amount-less cost: flagged and published null, never defaulted
# ---------------------------------------------------------------------------


def test_an_amountless_cost_is_flagged_and_published_null() -> None:
    document = schematic_document(
        [schematic_entry(AMOUNTLESS_SCHEMATIC, mCost=amountless_blob([PART_ITEM]))]
    )
    catalog = normalize_schematics(document)

    schematic = catalog.schematics[AMOUNTLESS_SCHEMATIC]
    # None, never () and never a defaulted amount: the document named an item
    # and did not say how many, which is a different fact from "free".
    assert schematic.cost is None
    named = warnings_of(catalog, WARN_COST_WITHOUT_AMOUNT, AMOUNTLESS_SCHEMATIC)
    assert len(named) == 1
    assert catalog.costs_flagged == 1
    assert catalog.costs_parsed == 0
    # The detail names the field, never the value: the blob's path is not echoed.
    path = synthetic.item_path(PART_ITEM)
    echoed = sum(1 for warning in catalog.warnings if path in warning.detail)
    assert echoed == 0


def test_a_malformed_cost_that_is_not_amountless_has_its_own_code() -> None:
    catalog = normalize_schematics(
        schematic_document([schematic_entry(MALFORMED_SCHEMATIC, mCost="((ItemClass=,Amount=))")])
    )
    assert catalog.schematics[MALFORMED_SCHEMATIC].cost is None
    assert len(warnings_of(catalog, WARN_UNREADABLE_COST, MALFORMED_SCHEMATIC)) == 1
    assert not warnings_of(catalog, WARN_COST_WITHOUT_AMOUNT, MALFORMED_SCHEMATIC)


# ---------------------------------------------------------------------------
# Readable costs: exact Fractions, and the empty cost is not the absent one
# ---------------------------------------------------------------------------


def test_a_normal_cost_parses_to_exact_fractions() -> None:
    blob = synthetic.amount_blob([(PART_ITEM, PART_AMOUNT), (PLATE_ITEM, PLATE_AMOUNT)])
    catalog = normalize_schematics(
        schematic_document([schematic_entry(NORMAL_SCHEMATIC, mCost=blob)])
    )
    cost = catalog.schematics[NORMAL_SCHEMATIC].cost
    assert cost == (
        CostLine(PART_ITEM, Fraction(PART_AMOUNT)),
        CostLine(PLATE_ITEM, Fraction(PLATE_AMOUNT)),
    )
    assert cost is not None
    kinds = sorted({type(line.amount).__name__ for line in cost})
    assert kinds == ["Fraction"]
    # A line IS the (item class, amount) pair.
    assert tuple(cost[0]) == (PART_ITEM, Fraction(PART_AMOUNT))
    assert catalog.costs_parsed == 1
    assert catalog.costs_flagged == 0
    assert catalog.warnings == ()


def test_the_item_join_key_is_the_class_name_after_the_final_dot() -> None:
    # The same key the registry's items are keyed by, for both a wrapped asset
    # path and a bare one, and a dotless token comes back whole.
    assert class_name_of_path(synthetic.item_path(PART_ITEM)) == PART_ITEM
    assert class_name_of_path(PURCHASED_CLASS_PATH) == "BP_SchematicPurchasedDependency_C"
    assert class_name_of_path(PART_ITEM) == PART_ITEM


def test_an_empty_cost_is_the_empty_tuple_not_none() -> None:
    catalog = normalize_schematics(schematic_document([schematic_entry(FREE_SCHEMATIC, mCost="")]))
    cost = catalog.schematics[FREE_SCHEMATIC].cost
    assert cost is not None
    assert cost == ()
    assert catalog.costs_parsed == 1
    assert catalog.costs_flagged == 0
    assert catalog.warnings == ()


def test_an_absent_cost_is_flagged_and_published_null() -> None:
    catalog = normalize_schematics(
        schematic_document([schematic_entry(ABSENT_COST_SCHEMATIC, mCost=None)])
    )
    assert catalog.schematics[ABSENT_COST_SCHEMATIC].cost is None
    assert len(warnings_of(catalog, WARN_MISSING_FIELD, ABSENT_COST_SCHEMATIC)) == 1


# ---------------------------------------------------------------------------
# Tier and type
# ---------------------------------------------------------------------------


def test_tier_and_type_parse() -> None:
    catalog = normalize_schematics(
        schematic_document(
            [schematic_entry(NORMAL_SCHEMATIC, mTechTier=TIER_TEXT, mType=TYPE_ALTERNATE)]
        )
    )
    schematic = catalog.schematics[NORMAL_SCHEMATIC]
    assert schematic.tech_tier == TIER_VALUE
    assert type(schematic.tech_tier) is int
    assert schematic.type_token == TYPE_ALTERNATE
    assert schematic.class_name == NORMAL_SCHEMATIC
    assert catalog.warnings == ()


@pytest.mark.parametrize("text", [" 3", "-1", "3.0", "", "three", "1_0"])
def test_an_unparsable_tier_is_flagged_and_never_zero(text: str) -> None:
    catalog = normalize_schematics(
        schematic_document([schematic_entry(NORMAL_SCHEMATIC, mTechTier=text)])
    )
    assert catalog.schematics[NORMAL_SCHEMATIC].tech_tier is None
    assert len(warnings_of(catalog, WARN_UNPARSABLE_TIER, NORMAL_SCHEMATIC)) == 1


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def test_both_dependency_forms_are_read() -> None:
    catalog = normalize_schematics(
        schematic_document(
            [
                schematic_entry(
                    DEPENDENT_SCHEMATIC,
                    mSchematicDependencies=[
                        purchase_dependency([PREREQ_A, PREREQ_B], require_all="False"),
                        phase_dependency(),
                    ],
                )
            ]
        )
    )
    schematic = catalog.schematics[DEPENDENT_SCHEMATIC]
    assert schematic.purchase_dependencies == (
        PurchaseDependency(schematics=(PREREQ_A, PREREQ_B), require_all=False),
    )
    assert schematic.dependency_schematics == (PREREQ_A, PREREQ_B)
    assert schematic.phase_dependency == PhaseDependency(
        phase=GAME_PHASE, only_in_selected_phase=False
    )
    assert schematic.game_phase == GAME_PHASE
    assert schematic.dependencies_complete is True
    assert catalog.warnings == ()


def test_no_dependency_means_no_phase_and_a_complete_empty_list() -> None:
    catalog = normalize_schematics(schematic_document([schematic_entry(NORMAL_SCHEMATIC)]))
    schematic = catalog.schematics[NORMAL_SCHEMATIC]
    assert schematic.purchase_dependencies == ()
    assert schematic.game_phase is None
    assert schematic.dependencies_complete is True


_UNKNOWN_SHAPES: Final[dict[str, object]] = {
    "extra-key": {**purchase_dependency([PREREQ_B]), "mSynthExtra": "True"},
    "unknown-class-token": {**purchase_dependency([PREREQ_B]), KEY_DEP_CLASS: UNKNOWN_CLASS_PATH},
    "phase-keys-on-purchase-class": {**phase_dependency(), KEY_DEP_CLASS: PURCHASED_CLASS_PATH},
    "no-class": {KEY_DEP_SCHEMATICS: "", KEY_DEP_REQUIRE_ALL: "True"},
    "not-a-mapping": "BP_SynthLooseString_C",
}


@pytest.mark.parametrize("shape", sorted(_UNKNOWN_SHAPES))
def test_an_unknown_dependency_shape_is_flagged(shape: str) -> None:
    catalog = normalize_schematics(
        schematic_document(
            [
                schematic_entry(
                    DEPENDENT_SCHEMATIC,
                    mSchematicDependencies=[
                        purchase_dependency([PREREQ_A]),
                        _UNKNOWN_SHAPES[shape],
                    ],
                )
            ]
        )
    )
    schematic = catalog.schematics[DEPENDENT_SCHEMATIC]
    assert len(warnings_of(catalog, WARN_UNKNOWN_DEPENDENCY, DEPENDENT_SCHEMATIC)) == 1
    # The readable remainder is kept, and is marked as only a remainder.
    assert schematic.dependencies_complete is False
    assert schematic.dependency_schematics == (PREREQ_A,)
    assert schematic.game_phase is None


# ---------------------------------------------------------------------------
# Accounting: parsed + flagged == total
# ---------------------------------------------------------------------------


def test_parsed_plus_flagged_equals_total() -> None:
    catalog = normalize_schematics(mixed_document())
    published = len(catalog.schematics)
    assert catalog.entries_offered == MIXED_OFFERED
    assert catalog.entries_skipped == MIXED_SKIPPED
    assert published + catalog.entries_skipped == catalog.entries_offered
    assert catalog.costs_parsed == MIXED_PARSED
    assert catalog.costs_flagged == MIXED_FLAGGED
    assert catalog.costs_parsed + catalog.costs_flagged == published
    nulls = sorted(name for name, s in catalog.schematics.items() if s.cost is None)
    assert nulls == sorted([AMOUNTLESS_SCHEMATIC, ABSENT_COST_SCHEMATIC, MALFORMED_SCHEMATIC])
    # The repeated ClassName keeps the FIRST entry, whose cost was empty.
    assert catalog.schematics[FREE_SCHEMATIC].cost == ()


_ACCOUNTING_SKEWS: Final[dict[str, dict[str, int]]] = {
    "one-more-parsed": {"costs_parsed": 1},
    "one-more-flagged": {"costs_flagged": 1},
    "one-more-skipped": {"entries_skipped": 1},
    # The sum still closes; only the recount from the model can see this one.
    "one-flagged-counted-as-parsed": {"costs_parsed": 1, "costs_flagged": -1},
}


@pytest.mark.parametrize("skew", sorted(_ACCOUNTING_SKEWS))
def test_an_accounting_that_does_not_close_raises(skew: str) -> None:
    catalog = normalize_schematics(mixed_document())
    verify_accounting(catalog)
    deltas = _ACCOUNTING_SKEWS[skew]
    broken = dataclasses.replace(
        catalog, **{field: getattr(catalog, field) + delta for field, delta in deltas.items()}
    )
    with pytest.raises(SchematicIntegrityError):
        verify_accounting(broken)
    # The integrity error is not a ValueError, so a BlobParseError handler
    # cannot swallow it.
    assert not issubclass(SchematicIntegrityError, ValueError)


# ---------------------------------------------------------------------------
# No float anywhere
# ---------------------------------------------------------------------------


def test_no_float_reaches_the_catalog() -> None:
    catalog = normalize_schematics(mixed_document())
    audit_exact(catalog, path="catalog")
    amounts = [
        line.amount for s in catalog.schematics.values() if s.cost is not None for line in s.cost
    ]
    assert len(amounts) == MIXED_PARSED
    kinds = sorted({type(amount).__name__ for amount in amounts})
    assert kinds == ["Fraction"]


def test_the_module_source_names_no_float() -> None:
    source = Path(schematics_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    float_literals = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is float
    ]
    float_names = [
        node.lineno for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == "float"
    ]
    assert float_literals == []
    assert float_names == []


# ---------------------------------------------------------------------------
# Unknown fields, and the model's immutability
# ---------------------------------------------------------------------------


def test_an_unknown_field_is_flagged_by_field_name() -> None:
    catalog = normalize_schematics(
        schematic_document(
            [
                schematic_entry(NEW_FIELD_SCHEMATIC, **{NEW_FIELD: "1"}),
                schematic_entry(NORMAL_SCHEMATIC, **{NEW_FIELD: "2"}),
            ]
        )
    )
    rows = warnings_of(catalog, WARN_UNKNOWN_FIELD, NEW_FIELD)
    # One row, aggregated across both schematics, and still never fatal.
    assert [row.count for row in rows] == [2]
    assert set(catalog.schematics) == {NEW_FIELD_SCHEMATIC, NORMAL_SCHEMATIC}
    # A known field this model does not read is not flagged.
    assert not [w for w in catalog.warnings if w.subject == KEY_DISPLAY_NAME]


def test_the_model_is_frozen() -> None:
    catalog = normalize_schematics(schematic_document([schematic_entry(NORMAL_SCHEMATIC)]))
    schematic = catalog.schematics[NORMAL_SCHEMATIC]
    with pytest.raises(FrozenInstanceError):
        schematic.tech_tier = 1  # type: ignore[misc]
    with pytest.raises(TypeError):
        catalog.schematics[NORMAL_SCHEMATIC] = schematic  # type: ignore[index]
