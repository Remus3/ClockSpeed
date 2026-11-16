"""CS-1360 - the flow view of a solved chain, a projection of one rule trace.

A derivation for a plan card carries the ProductionPlan the rule read, as the value of
its ``plan.production`` input-read step, and the CarryReport the advisor set against the
registry's transports, as the value of its ``plan.carry`` input-read step. This module turns
the two into a small read-only picture: the recipe nodes with their exact machine counts, the
edges that cross the plan's BOUNDARY - what it eats (raw inputs), what it makes (targets) and
what falls out (byproducts) - the chain's INTERNAL links, and the one edge the trace names as
the BOTTLENECK. Every width is the plan's own exact per-minute rate.

THIS IS A PROJECTION AND NOTHING ELSE. It opens no file, imports nothing from
``clockspeed/data``, ``clockspeed/solve`` or ``clockspeed/advisor`` at run time (the
types are named under TYPE_CHECKING only), reads the registry not at all - the caller
hands over a ``forms`` mapping - and COMPUTES NOTHING: it selects and transcribes what the
trace recorded. Fractions cross the wire through :func:`contract.rational`. A number that
first existed here would be a number with no trace behind it, so the carrier of each edge, its
utilisation, whether it saturates and which edge is the bottleneck are all decided by
``clockspeed/solve/carry.py``, offered to the rule by ``clockspeed/advisor/plans.py`` and
recorded by ``plan.adopt``; this module reads the record.

THE CHAIN, NOT ONLY ITS BOUNDARY (CS-1395). ``ProductionPlan.edges`` publishes one exact
flow per (producer recipe, item, consumer recipe), and the edges with both ends are the
chain's INTERNAL links: they are served as ``links``, in the plan's own order, each
width the plan's own Fraction. A link is an ALLOCATION and never a route - where several
recipes make an item and several use it, nothing says which machine feeds which - and
the panel says so.

THE MARK IS THE BOTTLENECK (CS-1394). The recorded bottleneck is the edge using the
largest share of the fastest known belt or pipe for its unit, over every edge of the plan,
boundary and internal. ``marked_edge`` names it and the one row it is flagged ``marked``.
When the trace records no carry, or a carry with no bottleneck, nothing is marked: no
capacity was known, and the view does not fall back to a rate.

A row with a recorded carry row reads its unit from that row, which is the unit the carry was
computed in; only an edge nothing was recorded for reads it from ``forms``, so a caller with
no forms still shows the marked edge's real unit.

A boundary edge here is one (item, role) total, and the plan may split one item's boundary
flow across several consumers. Such a total carries no carrier or utilisation of its own, since
the figures belong to its pieces, but it is flagged ``marked`` when one of its pieces is the
bottleneck, and ``marked_edge`` names the piece.

A form this layer cannot classify is :data:`TRANSPORT_UNKNOWN`, never a belt: ``RF_INVALID``
is a third case in the registry and not a synonym for a solid, an empty form is a missing
one, and a key the caller did not supply is a fact nobody stated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from clockspeed.advisor.trace import Trace
    from clockspeed.solve.carry import CarryReport, EdgeCarry
    from clockspeed.solve.ratio import PlanEdge

__all__ = [
    "CARRY_SUBJECT",
    "MARK_BOTTLENECK",
    "PLAN_SUBJECT",
    "ROLES",
    "ROLE_BYPRODUCT",
    "ROLE_INTERNAL",
    "ROLE_RAW_INPUT",
    "ROLE_TARGET",
    "TRANSPORT_BELT",
    "TRANSPORT_PIPE",
    "TRANSPORT_UNKNOWN",
    "UNIT_ITEM",
    "UNIT_UNKNOWN",
    "UNIT_VOLUME",
    "view_of",
]

#: The trace step subject that carries the ProductionPlan.
#: ``clockspeed/advisor/rules/plan.py``, ``IN_PLAN``. A test binds the two.
PLAN_SUBJECT: Final = "plan.production"

#: The trace step subject that carries the CarryReport, ``IN_CARRY`` there. A test binds them.
CARRY_SUBJECT: Final = "plan.carry"

ROLE_RAW_INPUT: Final = "raw-input"
ROLE_TARGET: Final = "target"
ROLE_BYPRODUCT: Final = "byproduct"

#: The role of an edge with a producer recipe and a consumer recipe: a chain link.
ROLE_INTERNAL: Final = "internal"

#: The published edge order: a role, then the item key within it.
ROLES: Final = (ROLE_RAW_INPUT, ROLE_TARGET, ROLE_BYPRODUCT)

TRANSPORT_BELT: Final = "belt"
TRANSPORT_PIPE: Final = "pipe"
TRANSPORT_UNKNOWN: Final = "unknown"

#: The unit an edge's rate is counted in: a solid in items a minute, a liquid or a gas in
#: cubic metres a minute.
UNIT_ITEM: Final = "item"
UNIT_VOLUME: Final = "m3"
UNIT_UNKNOWN: Final = "unknown"

#: What the one mark means: the bottleneck the trace records.
MARK_BOTTLENECK: Final = "bottleneck"

#: The verbatim ``mForm`` spellings, from ``clockspeed/data/registry.py`` ``FORM_SOLID``,
#: ``FORM_LIQUID`` and ``FORM_GAS``. A test binds each to its constant. Only these three
#: classify: ``RF_INVALID`` and anything else are not named here, so they read unknown.
_BELT_FORMS: Final = frozenset({"RF_SOLID"})
_PIPE_FORMS: Final = frozenset({"RF_LIQUID", "RF_GAS"})

#: The plan's attribute for each role, in published order.
_ROLE_FIELDS: Final = (
    (ROLE_RAW_INPUT, "raw_inputs"),
    (ROLE_TARGET, "targets"),
    (ROLE_BYPRODUCT, "byproducts"),
)


def _input_of(trace: Trace, subject: str) -> object | None:
    """The value of the first input-read step with this subject, or None.

    Args:
        trace: The rule's trace.
        subject: The input's name.

    Returns:
        The value, or None when no such step exists.
    """
    for step in trace.steps:
        if step.kind.value == "input-read" and step.subject == subject:
            return step.value
    return None


def _transport_of(item_key: str, forms: Mapping[str, str] | None) -> str:
    """Classify one item's transport from its verbatim form.

    Args:
        item_key: The item's ClassName.
        forms: Item key to verbatim ``mForm``, or None when none was supplied.

    Returns:
        Belt for a solid, pipe for a liquid or a gas, otherwise unknown.
    """
    if forms is None:
        return TRANSPORT_UNKNOWN
    form = forms.get(item_key, "")
    if form in _BELT_FORMS:
        return TRANSPORT_BELT
    if form in _PIPE_FORMS:
        return TRANSPORT_PIPE
    return TRANSPORT_UNKNOWN


def _unit_of(item_key: str, forms: Mapping[str, str] | None) -> str:
    """Classify the unit one item's rate is counted in, from the same verbatim form.

    Args:
        item_key: The item's ClassName.
        forms: Item key to verbatim ``mForm``, or None when none was supplied.

    Returns:
        Items for a solid, cubic metres for a liquid or a gas, otherwise unknown.
    """
    transport = _transport_of(item_key, forms)
    if transport == TRANSPORT_BELT:
        return UNIT_ITEM
    if transport == TRANSPORT_PIPE:
        return UNIT_VOLUME
    return UNIT_UNKNOWN


def _role_of(row: EdgeCarry) -> str:
    """The role one recorded row plays: where it enters or leaves the plan, or inside it.

    Args:
        row: One row of the recorded carry.

    Returns:
        Raw input for a row with no producer, byproduct or target for a row with no
        consumer by its sink, otherwise internal.
    """
    if row.producer is None:
        return ROLE_RAW_INPUT
    if row.consumer is None:
        return ROLE_BYPRODUCT if row.sink == ROLE_BYPRODUCT else ROLE_TARGET
    return ROLE_INTERNAL


def _figures(row: EdgeCarry | None) -> dict:
    """The recorded carrier, utilisation and saturation of one row, or all three None.

    Args:
        row: The row, or None when nothing was recorded for the edge.

    Returns:
        ``{"capacity", "utilisation", "saturated"}``, each transcribed from the row.
    """
    if row is None:
        return {"capacity": None, "utilisation": None, "saturated": None}
    capacity = (
        None
        if row.carrier is None or row.carrier_per_minute is None
        else {
            "carrier": row.carrier,
            "per_minute": contract.rational(row.carrier_per_minute),
        }
    )
    return {
        "capacity": capacity,
        "utilisation": contract.rational(row.utilisation),
        "saturated": row.saturated,
    }


def _links_of(
    plan: object,
    forms: Mapping[str, str] | None,
    rows: tuple[EdgeCarry, ...],
    bottleneck: EdgeCarry | None,
) -> list[dict]:
    """The plan's internal flows, one entry per edge that has both a producer and a consumer.

    Args:
        plan: The ProductionPlan the trace held.
        forms: Item key to its verbatim ``mForm``, or None.
        rows: The recorded carry's rows.
        bottleneck: The recorded bottleneck row, or None.

    Returns:
        The links in the plan's own edge order. A plan that published no edges has none.
    """
    by_triple = {(row.producer, row.item, row.consumer): row for row in rows}
    plan_edges: Iterable[PlanEdge] = getattr(plan, "edges", ())
    links: list[dict] = []
    for edge in plan_edges:
        if edge.producer is None or edge.consumer is None:
            continue
        row = by_triple.get((edge.producer, edge.item, edge.consumer))
        links.append(
            {
                "producer": edge.producer,
                "consumer": edge.consumer,
                "item": edge.item,
                "transport": _transport_of(edge.item, forms),
                "unit": edge.unit,
                "width": contract.rational(edge.rate),
                "marked": row is not None and row == bottleneck,
                **_figures(row),
            }
        )
    return links


def _recorded(trace: Trace) -> tuple[tuple[EdgeCarry, ...], EdgeCarry | None]:
    """The carry rows the trace recorded and the one it names the bottleneck.

    Args:
        trace: The rule's trace.

    Returns:
        ``(rows, bottleneck)``. Without a recorded carry, or one with no bottleneck, the rows
        are what was recorded and the bottleneck is None.
    """
    report = _input_of(trace, CARRY_SUBJECT)
    if report is None:
        return (), None
    carry: CarryReport = report  # type: ignore[assignment]
    rows = tuple(carry.rows)
    index = carry.bottleneck
    if index is None or not 0 <= index < len(rows):
        return rows, None
    return rows, rows[index]


def view_of(trace: Trace, *, forms: Mapping[str, str] | None = None) -> dict | None:
    """Project the trace's plan and recorded carry into nodes, edges, links and the mark.

    Args:
        trace: The rule's trace.
        forms: Item key to its verbatim ``mForm``, or None when the caller has none.

    Returns:
        ``{"rule_id", "nodes", "edges", "links", "marked_edge"}``, or None when the trace
        holds no plan - flagged and skipped, never an empty view that would read as "this
        chain has no flow". Every number is a ``{"num", "den"}`` object.
    """
    plan = _input_of(trace, PLAN_SUBJECT)
    if plan is None:
        return None
    rows, bottleneck = _recorded(trace)
    nodes = [
        {"recipe": step.recipe_key, "machines": contract.rational(step.machines)}
        for step in plan.steps  # type: ignore[attr-defined]
    ]
    edges: list[dict] = []
    for role, attribute in _ROLE_FIELDS:
        rates: Mapping[str, object] = getattr(plan, attribute)
        for key in sorted(rates):
            pieces = [row for row in rows if _role_of(row) == role and row.item == key]
            edges.append(
                {
                    "item": key,
                    "role": role,
                    "direction": "in" if role == ROLE_RAW_INPUT else "out",
                    "transport": _transport_of(key, forms),
                    "unit": pieces[0].unit if pieces else _unit_of(key, forms),
                    "width": contract.rational(rates[key]),  # type: ignore[arg-type]
                    "marked": bottleneck is not None and bottleneck in pieces,
                    **_figures(pieces[0] if len(pieces) == 1 else None),
                }
            )
    marked_edge = (
        None
        if bottleneck is None
        else {
            "producer": bottleneck.producer,
            "item": bottleneck.item,
            "consumer": bottleneck.consumer,
            "role": _role_of(bottleneck),
            "unit": bottleneck.unit,
            "utilisation": contract.rational(bottleneck.utilisation),
            "reason": MARK_BOTTLENECK,
        }
    )
    return {
        "rule_id": trace.rule_id,
        "nodes": nodes,
        "edges": edges,
        "links": _links_of(plan, forms, rows, bottleneck),
        "marked_edge": marked_edge,
    }
