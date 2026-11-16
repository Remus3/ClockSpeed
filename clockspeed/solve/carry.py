"""CS-1360 - which belt or pipe a plan's flows need, and which flow is the bottleneck.

A solved plan publishes one exact rate per edge (``ProductionPlan.edges``, CS-1395) and the
registry publishes each conveyor and pipeline class's per-minute rate (``Registry.transports``,
CS-1394). This module sets the one against the other and nothing else: for every edge whose
unit has a published carrier it names the SMALLEST carrier that holds the rate, the utilisation of
the FASTEST known carrier of that unit the rate uses, and whether that utilisation reaches one. The
edge using the largest utilisation is the plan's BOTTLENECK.

THE DENOMINATOR IS THE BEST KNOWN CARRIER, AND THAT IS A CHOICE. A plan chooses no belt tier,
so the only defensible single capacity for a unit is the greatest per-minute rate the registry
publishes for it. It is registry-wide, not the tiers a world has unlocked, and a utilisation above
one is meaningful: no single carrier of that unit holds the rate.

UTILISATION IS UNITLESS. A fluid edge in cubic metres a minute over the fastest pipe in cubic
metres a minute, and a solid edge in items a minute over the fastest belt in items a minute,
are both plain ratios, so the two compare with each other; a rate compared with a rate of
another unit never is.

An edge whose unit is unknown, or whose unit no carrier publishes a rate for, is INELIGIBLE:
it is left out, never read as a utilisation of zero or as unsaturated. A report with no
eligible edge has no bottleneck.

Pure and exact: Fractions in, Fractions out, no float, no rounding. Ties go to the first edge
in the plan's own edge order, which CS-1395 pins as deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from clockspeed.solve.exact import audit_exact
from clockspeed.solve.ratio import UNIT_UNKNOWN

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from fractions import Fraction

    from clockspeed.data.registry import Transport
    from clockspeed.solve.ratio import PlanEdge

__all__ = ["CARRY_SOURCE", "CarryReport", "EdgeCarry", "carry_of"]

#: Where a :class:`CarryReport` offered to a rule says it came from.
CARRY_SOURCE: Final = "solve.carry.carry_of"


@dataclass(frozen=True, slots=True)
class EdgeCarry:
    """One eligible plan edge set against the carriers of its unit.

    Frozen with slots on purpose: the advice trace admits a frozen slotted dataclass without
    an allowlist entry.

    Attributes:
        producer: The producing recipe's ClassName, or None for a raw supply.
        item: The item's ClassName.
        consumer: The consuming recipe's ClassName, or None for a sink.
        sink: ``PlanEdge.sink``: ``target`` or ``byproduct`` for a boundary delivery, else None.
        unit: The edge's unit, as ``PlanEdge.unit`` spells it.
        carrier: The ClassName of the smallest carrier whose rate holds the edge's rate, the
            first by ClassName among equals, or None when no single carrier holds it.
        carrier_per_minute: That carrier's published per-minute rate, or None with it.
        carrier_name: ``carrier`` in short form (see :func:`_short_name`), or None with it.
        best_carrier: The ClassName of the fastest carrier of the unit, the first by
            ClassName among equals.
        best_name: ``best_carrier`` in short form. ``utilisation`` and ``percent`` are shares
            of THIS carrier, not of ``carrier``, so a surface names it beside the figure.
        best: That carrier's published per-minute rate, an exact Fraction above zero.
        utilisation: The edge's rate over ``best``, an exact unitless Fraction; above one when no
            single carrier holds the rate.
        percent: ``utilisation`` times one hundred rounded to a whole number, HALF UP, on
            the exact Fraction: the integer ``(2 * 100 * numerator + denominator) // (2 *
            denominator)``. It exists so a surface can print the figure without computing it,
            and it is NOT capped: above one hundred means no single carrier holds the rate.
        saturated: Whether ``utilisation`` is at least one.
    """

    producer: str | None
    item: str
    consumer: str | None
    sink: str | None
    unit: str
    carrier: str | None
    carrier_per_minute: Fraction | None
    carrier_name: str | None
    best_carrier: str
    best_name: str
    best: Fraction
    utilisation: Fraction
    percent: int
    saturated: bool


@dataclass(frozen=True, slots=True)
class CarryReport:
    """Every eligible edge's carrier and utilisation, and which one is the bottleneck.

    Attributes:
        rows: One :class:`EdgeCarry` per eligible edge, in the plan's edge order.
        bottleneck: The index into ``rows`` of the row with the greatest utilisation, the first
            among equals, or None when no edge is eligible.
    """

    rows: tuple[EdgeCarry, ...]
    bottleneck: int | None


def _short_name(key: str) -> str:
    """A carrier's ClassName without its ``Build_`` prefix and ``_C`` suffix.

    Args:
        key: The ClassName, e.g. ``Build_ConveyorBeltMk1_C``.

    Returns:
        ``ConveyorBeltMk1``. A part is dropped only when something remains, so a key that is
        nothing but the affix stands as it is.
    """
    name = key
    if name.startswith("Build_") and len(name) > len("Build_"):
        name = name[len("Build_") :]
    if name.endswith("_C") and len(name) > len("_C"):
        name = name[: -len("_C")]
    return name


def _percent(utilisation: Fraction) -> int:
    """A utilisation as a whole percent, rounded half up on the exact Fraction.

    Args:
        utilisation: An exact non-negative Fraction.

    Returns:
        ``floor(utilisation * 100 + 1/2)`` by integer arithmetic alone.
    """
    scaled = utilisation.numerator * 100
    return (2 * scaled + utilisation.denominator) // (2 * utilisation.denominator)


def _rated(transports: Mapping[str, Transport]) -> dict[str, list[tuple[Fraction, str]]]:
    """The carriers that publish a rate, by unit, each list ascending by rate then ClassName.

    Args:
        transports: Class key to transport.

    Returns:
        Unit to ``(per_minute, key)`` pairs. A class whose rate is unpublished is left out.
    """
    by_unit: dict[str, list[tuple[Fraction, str]]] = {}
    for key, transport in transports.items():
        if transport.per_minute is not None and transport.per_minute > 0:
            by_unit.setdefault(transport.unit, []).append((transport.per_minute, key))
    for carriers in by_unit.values():
        carriers.sort()
    return by_unit


def carry_of(edges: Iterable[PlanEdge], transports: Mapping[str, Transport]) -> CarryReport:
    """Set every plan edge against the carriers of its unit and pick the bottleneck.

    Args:
        edges: The plan's edges, in the plan's own order.
        transports: The registry's transports by ClassName.

    Returns:
        The report. An edge of unknown unit, or of a unit no carrier publishes a rate for,
        has no row; with no row at all the bottleneck is None.

    Raises:
        InexactValueError: A non-exact number is reachable from the result.
    """
    carriers = _rated(transports)
    rows: list[EdgeCarry] = []
    bottleneck: int | None = None
    for edge in edges:
        known = carriers.get(edge.unit) if edge.unit != UNIT_UNKNOWN else None
        if not known:
            continue
        best, best_key = known[-1]
        # The fastest class, first by ClassName among equals: the list is ascending, so walk
        # back over every class that ties the greatest rate.
        for per_minute, key in known:
            if per_minute == best:
                best_key = key
                break
        holds = next(
            ((per_minute, key) for per_minute, key in known if per_minute >= edge.rate), None
        )
        utilisation = edge.rate / best
        if bottleneck is None or utilisation > rows[bottleneck].utilisation:
            bottleneck = len(rows)
        rows.append(
            EdgeCarry(
                producer=edge.producer,
                item=edge.item,
                consumer=edge.consumer,
                sink=edge.sink,
                unit=edge.unit,
                carrier=None if holds is None else holds[1],
                carrier_per_minute=None if holds is None else holds[0],
                carrier_name=None if holds is None else _short_name(holds[1]),
                best_carrier=best_key,
                best_name=_short_name(best_key),
                best=best,
                utilisation=utilisation,
                percent=_percent(utilisation),
                saturated=utilisation >= 1,
            )
        )
    report = CarryReport(rows=tuple(rows), bottleneck=bottleneck)
    audit_exact(report, path="carry")
    return report
