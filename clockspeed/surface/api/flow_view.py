"""CS-1360 - the boundary flow view of a solved chain, a projection of one rule trace.

A derivation for a plan card carries the ProductionPlan the rule read, as the value of
its ``plan.production`` input-read step. This module turns that plan into a small
read-only picture: the recipe nodes with their exact machine counts, and the edges that
cross the plan's BOUNDARY - what it eats (raw inputs), what it makes (targets) and what
falls out (byproducts) - each with its exact per-minute rate as the edge width.

THIS IS A PROJECTION AND NOTHING ELSE. It opens no file, imports nothing from
``clockspeed/data``, ``clockspeed/solve`` or ``clockspeed/advisor`` at run time (the
types are named under TYPE_CHECKING only), reads the registry not at all - the caller
hands over a ``forms`` mapping - and computes nothing beyond selecting a maximum and
transcribing. Fractions cross the wire through :func:`contract.rational`.

THE CHAIN, NOT ONLY ITS BOUNDARY (CS-1395). ``ProductionPlan.edges`` publishes one exact
flow per (producer recipe, item, consumer recipe), and the edges with both ends are the
chain's INTERNAL links: they are served as ``links``, in the plan's own order, each
width the plan's own Fraction. A link is an ALLOCATION and never a route - where several
recipes make an item and several use it, nothing says which machine feeds which - and
the panel says so.

CAPACITY AND SATURATION (CS-1394). The caller may hand over the registry's transports,
each a belt, lift or pipeline class with its published per-minute rate and unit. Every
edge and link then names the SMALLEST carrier whose rate holds its width, and says
whether it is SATURATED. The plan chooses no belt tier, so saturated means one thing
only: the width reaches the best carrier of its unit the registry knows, so no single
carrier has room to spare. Choosing the carrier is a comparison of exact Fractions and
no arithmetic is added. A claim needs a capacity to compare against, so both fields
read None - never False, never a free pass - when no transports were supplied, when the
edge's unit is unknown, or when no carrier of its unit publishes a rate (non-negotiable
7).

THE MARK IS STILL THE HIGHEST RATE. The one mark this view makes is named for what it
measures, :data:`MARK_HIGHEST_RATE`, the boundary edge with the greatest width within
one unit, and capacity moves neither it nor any width.

THE MARK IS TAKEN WITHIN ONE UNIT. A solid's rate is items a minute and a fluid's is
cubic metres a minute, so the two are never compared: the mark goes to the greatest
solid edge when one exists, else the greatest fluid edge, and an edge of unknown unit
is never marked. Selecting that maximum is the existing seam - this module already
chose the one maximum - and no arithmetic is added to it.

A form this layer cannot classify is :data:`TRANSPORT_UNKNOWN`, never a belt: ``RF_INVALID``
is a third case in the registry and not a synonym for a solid, an empty form is a missing
one, and a key the caller did not supply is a fact nobody stated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from fractions import Fraction

    from clockspeed.advisor.trace import Trace
    from clockspeed.data.registry import Transport
    from clockspeed.solve.ratio import PlanEdge

__all__ = [
    "MARK_HIGHEST_RATE",
    "PLAN_SUBJECT",
    "ROLES",
    "ROLE_BYPRODUCT",
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

ROLE_RAW_INPUT: Final = "raw-input"
ROLE_TARGET: Final = "target"
ROLE_BYPRODUCT: Final = "byproduct"

#: The published edge order: a role, then the item key within it.
ROLES: Final = (ROLE_RAW_INPUT, ROLE_TARGET, ROLE_BYPRODUCT)

TRANSPORT_BELT: Final = "belt"
TRANSPORT_PIPE: Final = "pipe"
TRANSPORT_UNKNOWN: Final = "unknown"

#: The unit an edge's rate is counted in: a solid in items a minute, a liquid or a gas in
#: cubic metres a minute. The two are never compared; unknown is never marked.
UNIT_ITEM: Final = "item"
UNIT_VOLUME: Final = "m3"
UNIT_UNKNOWN: Final = "unknown"

#: The one mark this view makes, and what it measures.
MARK_HIGHEST_RATE: Final = "highest-rate"

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


def _plan_of(trace: Trace) -> object | None:
    """The value of the first input-read step whose subject is the plan's, or None.

    Args:
        trace: The rule's trace.

    Returns:
        The value, or None when no such step exists.
    """
    for step in trace.steps:
        if step.kind.value == "input-read" and step.subject == PLAN_SUBJECT:
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


def _marked_position(exact: list[tuple[str, str, Fraction]], units: list[str]) -> int | None:
    """The position of the highest-rate edge within one known unit, or None.

    Args:
        exact: The edges as (item, role, exact rate), in published order.
        units: The unit of each edge, in the same order.

    Returns:
        The first greatest rate among the solid edges when any exists, else among the
        fluid edges, else None. Unknown-unit edges never compete.
    """
    for unit in (UNIT_ITEM, UNIT_VOLUME):
        marked: int | None = None
        for position, (_key, _role, rate) in enumerate(exact):
            if units[position] != unit:
                continue
            if marked is None or rate > exact[marked][2]:
                marked = position
        if marked is not None:
            return marked
    return None


def _rated_carriers(
    transports: Mapping[str, Transport] | None,
) -> dict[str, list[tuple[Fraction, str]]]:
    """The carriers that publish a rate, by unit, each list in ascending rate then key.

    Args:
        transports: Class key to transport, or None when the caller has none.

    Returns:
        Unit to ``(per_minute, key)`` pairs. A class whose rate is unpublished is left
        out: it carries nothing as far as this layer can say.
    """
    by_unit: dict[str, list[tuple[Fraction, str]]] = {}
    for key, transport in (transports or {}).items():
        if transport.per_minute is not None:
            by_unit.setdefault(transport.unit, []).append((transport.per_minute, key))
    for carriers in by_unit.values():
        carriers.sort()
    return by_unit


def _capacity_of(
    rate: Fraction, unit: str, carriers: Mapping[str, list[tuple[Fraction, str]]]
) -> tuple[dict | None, bool | None]:
    """The smallest carrier that holds this rate, and whether the rate saturates the best.

    Args:
        rate: The edge's exact width.
        unit: The edge's unit.
        carriers: :func:`_rated_carriers`.

    Returns:
        ``(carrier, saturated)``. Both None when the unit is unknown or no carrier of the
        unit publishes a rate. Otherwise ``saturated`` is whether ``rate`` reaches the
        best carrier, and ``carrier`` is None when no single carrier holds the rate.
    """
    known = carriers.get(unit)
    if not known:
        return None, None
    saturated = rate >= known[-1][0]
    for per_minute, key in known:
        if per_minute >= rate:
            return {"carrier": key, "per_minute": contract.rational(per_minute)}, saturated
    return None, saturated


def _links_of(
    plan: object,
    forms: Mapping[str, str] | None,
    carriers: Mapping[str, list[tuple[Fraction, str]]],
) -> list[dict]:
    """The plan's internal flows, one entry per edge that has both a producer and a consumer.

    Args:
        plan: The ProductionPlan the trace held.
        forms: Item key to its verbatim ``mForm``, or None.
        carriers: :func:`_rated_carriers`.

    Returns:
        The links in the plan's own edge order. A plan that published no edges has none.
    """
    plan_edges: Iterable[PlanEdge] = getattr(plan, "edges", ())
    links: list[dict] = []
    for edge in plan_edges:
        if edge.producer is None or edge.consumer is None:
            continue
        capacity, saturated = _capacity_of(edge.rate, edge.unit, carriers)
        links.append(
            {
                "producer": edge.producer,
                "consumer": edge.consumer,
                "item": edge.item,
                "transport": _transport_of(edge.item, forms),
                "unit": edge.unit,
                "width": contract.rational(edge.rate),
                "capacity": capacity,
                "saturated": saturated,
            }
        )
    return links


def view_of(
    trace: Trace,
    *,
    forms: Mapping[str, str] | None = None,
    transports: Mapping[str, Transport] | None = None,
) -> dict | None:
    """Project the trace's plan into nodes, edges, links and the one marked edge.

    Args:
        trace: The rule's trace.
        forms: Item key to its verbatim ``mForm``, or None when the caller has none.
        transports: The registry's transport classes by key, or None when the caller has
            none, in which case no edge names a carrier or a saturation.

    Returns:
        ``{"rule_id", "nodes", "edges", "links", "marked_edge"}``, or None when the trace
        holds no plan - flagged and skipped, never an empty view that would read as "this
        chain has no flow". Every number is a ``{"num", "den"}`` object.
    """
    plan = _plan_of(trace)
    if plan is None:
        return None
    nodes = [
        {"recipe": step.recipe_key, "machines": contract.rational(step.machines)}
        for step in plan.steps  # type: ignore[attr-defined]
    ]
    exact: list[tuple[str, str, Fraction]] = []
    for role, attribute in _ROLE_FIELDS:
        rates: Mapping[str, Fraction] = getattr(plan, attribute)
        exact.extend((key, role, rates[key]) for key in sorted(rates))
    units = [_unit_of(key, forms) for key, _role, _rate in exact]
    carriers = _rated_carriers(transports)
    capacities = [
        _capacity_of(rate, units[position], carriers)
        for position, (_key, _role, rate) in enumerate(exact)
    ]
    # Selected on the exact rates, first wins a tie; the serialised dicts are never compared.
    # Only edges of ONE unit compete: items when any solid edge exists, else cubic metres.
    # An edge of unknown unit never competes, so a plan with none known marks nothing.
    marked = _marked_position(exact, units)
    edges = [
        {
            "item": key,
            "role": role,
            "direction": "in" if role == ROLE_RAW_INPUT else "out",
            "transport": _transport_of(key, forms),
            "unit": units[position],
            "width": contract.rational(rate),
            "marked": position == marked,
            "capacity": capacities[position][0],
            "saturated": capacities[position][1],
        }
        for position, (key, role, rate) in enumerate(exact)
    ]
    marked_edge = (
        {
            "item": exact[marked][0],
            "role": exact[marked][1],
            "unit": units[marked],
            "reason": MARK_HIGHEST_RATE,
        }
        if marked is not None
        else None
    )
    return {
        "rule_id": trace.rule_id,
        "nodes": nodes,
        "edges": edges,
        "links": _links_of(plan, forms, carriers),
        "marked_edge": marked_edge,
    }
