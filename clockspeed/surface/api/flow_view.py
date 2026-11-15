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

WHY THE WORDS "saturated" AND "bottleneck" ARE ABSENT FROM THE PAYLOAD. No layer in this
tree publishes a belt or pipeline capacity (``clockspeed/audit/flow.py`` knows nothing
about belts, and the registry's only throughput is the extractor's), and the plan
publishes no internal edge: ``PlanStep`` carries a recipe and a machine count only. A
saturation claim needs a capacity to compare a rate against, so it cannot be computed,
and naming one would be a confident wrong answer (non-negotiable 7). The one mark this
view makes is therefore named for what it measures - :data:`MARK_HIGHEST_RATE`, the edge
with the greatest width - and says nothing about a limit. A successor that lands a
capacity owns the claim.

A form this layer cannot classify is :data:`TRANSPORT_UNKNOWN`, never a belt: ``RF_INVALID``
is a third case in the registry and not a synonym for a solid, an empty form is a missing
one, and a key the caller did not supply is a fact nobody stated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping
    from fractions import Fraction

    from clockspeed.advisor.trace import Trace

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


def view_of(trace: Trace, *, forms: Mapping[str, str] | None = None) -> dict | None:
    """Project the trace's plan into nodes, edges and the one marked edge.

    Args:
        trace: The rule's trace.
        forms: Item key to its verbatim ``mForm``, or None when the caller has none.

    Returns:
        ``{"rule_id", "nodes", "edges", "marked_edge"}``, or None when the trace holds
        no plan - flagged and skipped, never an empty view that would read as "this
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
    # Selected on the exact rates, first wins a tie; the serialised dicts are never compared.
    marked = 0
    for position in range(1, len(exact)):
        if exact[position][2] > exact[marked][2]:
            marked = position
    edges = [
        {
            "item": key,
            "role": role,
            "direction": "in" if role == ROLE_RAW_INPUT else "out",
            "transport": _transport_of(key, forms),
            "width": contract.rational(rate),
            "marked": position == marked,
        }
        for position, (key, role, rate) in enumerate(exact)
    ]
    marked_edge = (
        {"item": exact[marked][0], "role": exact[marked][1], "reason": MARK_HIGHEST_RATE}
        if exact
        else None
    )
    return {
        "rule_id": trace.rule_id,
        "nodes": nodes,
        "edges": edges,
        "marked_edge": marked_edge,
    }
