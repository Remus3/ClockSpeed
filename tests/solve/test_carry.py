"""CS-1360 - the carrier, the utilisation and the bottleneck of a plan's edges.

Every arm builds its edges and transports by hand, with rates that do not terminate where the
arithmetic matters, so nothing here re-solves and an answer equal to a float's is told apart.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data import registry as registry_module
from clockspeed.solve import carry
from clockspeed.solve.exact import InexactValueError, audit_exact
from clockspeed.solve.ratio import UNIT_ITEM, UNIT_M3, UNIT_UNKNOWN, PlanEdge

BELT1: Final = "Build_Belt1_C"
BELT2: Final = "Build_Belt2_C"
PIPE1: Final = "Build_Pipe1_C"
PIPE2: Final = "Build_Pipe2_C"


def _transport(
    key: str, per_minute: Fraction | None, *, unit: str = UNIT_ITEM
) -> registry_module.Transport:
    kind = "belt" if unit == UNIT_ITEM else "pipe"
    return registry_module.Transport(
        key=key,
        group="FGBuildableConveyorBelt" if kind == "belt" else "FGBuildablePipeline",
        kind=kind,
        unit=unit,
        numeric=per_minute,
        stated=per_minute,
        per_minute=per_minute,
    )


def _carriers(*members: registry_module.Transport) -> dict[str, registry_module.Transport]:
    return {member.key: member for member in members}


def _edge(
    item: str,
    rate: Fraction,
    *,
    unit: str = UNIT_ITEM,
    producer: str | None = None,
    consumer: str | None = None,
) -> PlanEdge:
    return PlanEdge(producer, item, consumer, rate, unit, None)


FLEET: Final = _carriers(
    _transport(BELT1, Fraction(600)),
    _transport(BELT2, Fraction(1200)),
    _transport(PIPE1, Fraction(300), unit=UNIT_M3),
    _transport(PIPE2, Fraction(600), unit=UNIT_M3),
)


def test_an_edge_reads_the_smallest_holding_carrier_and_its_share_of_the_best() -> None:
    report = carry.carry_of([_edge("Desc_Ore_C", Fraction(900))], FLEET)
    (row,) = report.rows
    assert row.carrier == BELT2
    assert row.carrier_per_minute == Fraction(1200)
    assert row.best_carrier == BELT2
    assert row.best == Fraction(1200)
    assert row.utilisation == Fraction(3, 4)
    assert row.saturated is False
    assert report.bottleneck == 0


def test_a_rate_a_smaller_carrier_holds_names_that_carrier_not_the_best() -> None:
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(600))], FLEET).rows
    assert row.carrier == BELT1  # exactly equal to the rate: it holds it
    assert row.best_carrier == BELT2
    assert row.utilisation == Fraction(1, 2)


def test_a_rate_above_every_carrier_has_no_carrier_and_a_utilisation_above_one() -> None:
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(3601, 3))], FLEET).rows
    assert row.carrier is None
    assert row.carrier_per_minute is None
    assert row.utilisation == Fraction(3601, 3600)
    assert row.saturated is True


def test_a_rate_equal_to_the_best_carrier_is_saturated() -> None:
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(1200))], FLEET).rows
    assert (row.utilisation, row.saturated, row.carrier) == (Fraction(1), True, BELT2)


def test_the_bottleneck_is_the_highest_utilisation_not_the_highest_rate() -> None:
    solid = _edge("Desc_Ore_C", Fraction(600))  # 1/2 of the best belt
    fluid = _edge("Desc_Water_C", Fraction(540), unit=UNIT_M3)  # 9/10 of the best pipe
    report = carry.carry_of([solid, fluid], FLEET)
    assert report.bottleneck == 1
    assert report.rows[1].item == "Desc_Water_C"
    assert report.rows[1].utilisation == Fraction(9, 10)
    assert report.rows[0].utilisation == Fraction(1, 2)


def test_a_tie_goes_to_the_first_edge_in_plan_order() -> None:
    first = _edge("Desc_A_C", Fraction(600))  # 1/2 of the best belt
    second = _edge("Desc_B_C", Fraction(300), unit=UNIT_M3)  # also 1/2 of the best pipe
    assert carry.carry_of([first, second], FLEET).bottleneck == 0
    assert carry.carry_of([second, first], FLEET).bottleneck == 0
    rows = carry.carry_of([second, first], FLEET).rows
    assert [row.item for row in rows] == ["Desc_B_C", "Desc_A_C"]


def test_an_unknown_unit_and_an_unrated_unit_are_ineligible() -> None:
    unknown = _edge("Desc_Odd_C", Fraction(10**6), unit=UNIT_UNKNOWN)
    only_belts = _carriers(_transport(BELT1, Fraction(600)))
    fluid = _edge("Desc_Water_C", Fraction(1), unit=UNIT_M3)
    solid = _edge("Desc_Ore_C", Fraction(6))
    report = carry.carry_of([unknown, fluid, solid], only_belts)
    assert [row.item for row in report.rows] == ["Desc_Ore_C"]
    assert report.bottleneck == 0
    # An unknown-unit carrier is not a way to rate an unknown-unit edge.
    odd = _carriers(_transport("Build_Odd_C", Fraction(5), unit=UNIT_UNKNOWN))
    assert carry.carry_of([unknown], odd) == carry.CarryReport(rows=(), bottleneck=None)


def test_a_carrier_with_no_published_rate_carries_nothing() -> None:
    withdrawn = _carriers(_transport(BELT1, None), _transport(BELT2, Fraction(0)))
    assert carry.carry_of([_edge("Desc_Ore_C", Fraction(1))], withdrawn) == carry.CarryReport(
        rows=(), bottleneck=None
    )
    # THE CONTROL: with one real carrier beside them the same edge does answer.
    rated = {**withdrawn, **_carriers(_transport("Build_Real_C", Fraction(10)))}
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(1))], rated).rows
    assert row.carrier == "Build_Real_C"


def test_no_edge_and_no_transport_report_no_bottleneck() -> None:
    assert carry.carry_of([], FLEET) == carry.CarryReport(rows=(), bottleneck=None)
    assert carry.carry_of([_edge("Desc_Ore_C", Fraction(1))], {}) == carry.CarryReport(
        rows=(), bottleneck=None
    )


def test_equal_classes_resolve_to_the_first_class_name() -> None:
    twins = _carriers(
        _transport("Build_Z_C", Fraction(100)), _transport("Build_A_C", Fraction(100))
    )
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(10))], twins).rows
    assert row.carrier == "Build_A_C"
    assert row.best_carrier == "Build_A_C"


def test_the_fastest_class_is_the_first_by_name_among_the_fastest_equals() -> None:
    fleet = _carriers(
        _transport("Build_Z_C", Fraction(200)),
        _transport("Build_M_C", Fraction(200)),
        _transport("Build_A_C", Fraction(50)),
    )
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(100))], fleet).rows
    assert row.best_carrier == "Build_M_C"
    assert row.carrier == "Build_M_C"


def test_the_rows_keep_each_edges_identity_and_plan_order() -> None:
    edges = [
        _edge("Desc_Ore_C", Fraction(100), consumer="Recipe_A_C"),
        _edge("Desc_Plate_C", Fraction(50), producer="Recipe_A_C", consumer="Recipe_B_C"),
        PlanEdge("Recipe_B_C", "Desc_Ingot_C", None, Fraction(25), UNIT_ITEM, "target"),
    ]
    rows = carry.carry_of(edges, FLEET).rows
    assert [(r.producer, r.item, r.consumer, r.sink) for r in rows] == [
        (None, "Desc_Ore_C", "Recipe_A_C", None),
        ("Recipe_A_C", "Desc_Plate_C", "Recipe_B_C", None),
        ("Recipe_B_C", "Desc_Ingot_C", None, "target"),
    ]


def test_every_number_is_an_exact_fraction_and_an_inexact_one_is_refused() -> None:
    report = carry.carry_of(
        [_edge("Desc_Ore_C", Fraction(7, 3)), _edge("Desc_Water_C", Fraction(1, 7), unit=UNIT_M3)],
        FLEET,
    )
    for row in report.rows:
        assert type(row.best) is Fraction
        assert type(row.utilisation) is Fraction
    # THE CONTROL: the audit really does refuse a float planted where a Fraction belongs.
    forged = carry.CarryReport(
        rows=(
            carry.EdgeCarry(
                producer=None,
                item="Desc_Ore_C",
                consumer=None,
                sink=None,
                unit=UNIT_ITEM,
                carrier=None,
                carrier_per_minute=None,
                carrier_name=None,
                best_carrier=BELT1,
                best_name="Belt1",
                best=Fraction(1),
                utilisation=0.5,  # type: ignore[arg-type]
                percent=50,
                saturated=False,
            ),
        ),
        bottleneck=0,
    )
    with pytest.raises(InexactValueError):
        audit_exact(forged)


def test_the_module_source_has_no_float_literal_round_or_float_call() -> None:
    source = Path(carry.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    floats = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is float]
    names = {
        n.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Name) and n.id in {"float", "round", "divmod", "pow"}
    }
    assert floats == []
    assert names == set()
    # THE CONTROL: the same walk does see a planted float literal.
    planted = ast.parse("x = 0.5")
    seen = next(n for n in ast.walk(planted) if isinstance(n, ast.Constant))
    assert type(seen.value) is float


@pytest.mark.parametrize(
    ("rate", "expected"),
    [
        (Fraction(3, 2) * 1200, 150),  # above one: the figure shows it, nothing caps it
        (Fraction(1200), 100),
        (Fraction(1199), 100),  # 99.9166..: rounds up
        (Fraction(1194), 100),  # 99.5 exactly: half rounds UP
        (Fraction(1193), 99),  # 99.4166..: rounds down
        (Fraction(600), 50),
        (Fraction(400), 33),  # 33.33..
        (Fraction(1, 2), 0),  # 0.0416..%
        (Fraction(6), 1),  # 0.5 exactly: half rounds UP
        (Fraction(5), 0),  # 0.4166..%
    ],
)
def test_the_display_percent_is_the_utilisation_rounded_half_up_exactly(
    rate: Fraction, expected: int
) -> None:
    (row,) = carry.carry_of([_edge("Desc_Ore_C", rate)], FLEET).rows
    assert type(row.percent) is int
    assert row.percent == expected, (rate, row.utilisation)
    # The percent is a presentation of the utilisation, which stays exact beside it.
    assert row.utilisation == rate / Fraction(1200)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("Build_ConveyorBeltMk1_C", "ConveyorBeltMk1"),
        ("Build_PipelineMK2_C", "PipelineMK2"),
        ("Plain", "Plain"),
        ("Build_", "Build_"),  # nothing left once the prefix goes: the key stands
        ("Build_X", "X"),
        ("X_C", "X"),
    ],
)
def test_a_carrier_short_name_drops_the_build_prefix_and_class_suffix(
    key: str, expected: str
) -> None:
    fleet = _carriers(_transport(key, Fraction(100)))
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(10))], fleet).rows
    assert row.carrier_name == expected
    assert row.best_name == expected


def test_a_row_names_the_smallest_and_the_fastest_carrier_in_short_form() -> None:
    fleet = _carriers(
        _transport("Build_ConveyorBeltMk1_C", Fraction(600)),
        _transport("Build_ConveyorBeltMk2_C", Fraction(1200)),
    )
    (row,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(100))], fleet).rows
    assert (row.carrier_name, row.best_name) == ("ConveyorBeltMk1", "ConveyorBeltMk2")
    (over,) = carry.carry_of([_edge("Desc_Ore_C", Fraction(5000))], fleet).rows
    assert (over.carrier, over.carrier_name, over.best_name) == (None, None, "ConveyorBeltMk2")
