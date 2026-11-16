"""CS-1360 - the boundary flow view a derivation carries.

The view is a projection of the ProductionPlan the trace already holds, so every arm
here builds a plan by hand with Fractions that do not terminate and reads it back off
a trace. Nothing re-solves: an edge width that equalled a re-solve would agree with the
solver by construction and could never catch a view that dropped the trace's own number.

WHAT THE VIEW IS. The boundary edges (raw inputs, targets, byproducts) and the chain's
internal links, each carrying the exact rate as its width and, when the caller hands over the
registry's transports, the smallest belt or pipe class that carries it. The plan names no
belt tier, so SATURATED means the rate reaches the best carrier the registry knows, and it is
unknown, never false, whenever no capacity was supplied. The mark stays named for what it
measures, the highest rate.
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import Advice, AdvisedCard
from clockspeed.advisor.cards import Card
from clockspeed.advisor.ledger import CardState
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.advisor.trace import Recommendation, StepKind, Trace, TraceStep
from clockspeed.data import registry as registry_module
from clockspeed.solve.ratio import PlanEdge, PlanStep, ProductionPlan
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, flow_view
from tests.solve import synthetic as solve_synthetic
from tests.surface import test_advice as advice_fixtures
from tests.surface import test_panel_advice as panel

if TYPE_CHECKING:
    from collections.abc import Mapping

#: The measured form spellings (clockspeed/data/registry.py FORM_* constants), spelled
#: here as the documents spell them so a constant renamed there cannot move these arms.
SOLID: Final = "RF_SOLID"
LIQUID: Final = "RF_LIQUID"
GAS: Final = "RF_GAS"
INVALID: Final = "RF_INVALID"

THIRD: Final = Fraction(10, 3)


def _plan(
    *,
    targets: Mapping[str, Fraction] | None = None,
    raw_inputs: Mapping[str, Fraction] | None = None,
    byproducts: Mapping[str, Fraction] | None = None,
) -> ProductionPlan:
    """A hand-built plan with rates that do not terminate, one zero-machine step."""
    return ProductionPlan(
        steps=(
            PlanStep("Recipe_B_C", Fraction(7, 3)),
            PlanStep("Recipe_A_C", Fraction(0)),
            PlanStep("Recipe_C_C", Fraction(1, 6)),
        ),
        targets={"Desc_Zeta_C": THIRD, "Desc_Alpha_C": Fraction(1, 7)}
        if targets is None
        else targets,
        raw_inputs={"Desc_Ore_C": Fraction(25, 3), "Desc_Water_C": Fraction(2, 9)}
        if raw_inputs is None
        else raw_inputs,
        byproducts={"Desc_Slag_C": Fraction(5, 6)} if byproducts is None else byproducts,
        excluded=(),
        byproduct_policy="sinkable",
    )


def _trace(plan: ProductionPlan | None, *, subject: str = flow_view.PLAN_SUBJECT) -> Trace:
    """A trace holding the plan as an input-read step, ending in its one rule-fired step."""
    steps = [TraceStep(kind=StepKind.INPUT_READ, subject="plan.status", value="ranked")]
    if plan is not None:
        steps.append(
            TraceStep(
                kind=StepKind.INPUT_READ,
                subject=subject,
                source="solve.strategy.ranked_plan.plan",
                value=plan,
            )
        )
    steps.append(TraceStep(kind=StepKind.RULE_FIRED, subject="synthetic-plan"))
    return Trace(
        rule_id="synthetic.plan",
        domain="plan",
        steps=tuple(steps),
        recommendation=Recommendation(
            subject_key="synthetic-plan", action="Build it", reason="why"
        ),
    )


def _view(plan: ProductionPlan, forms: Mapping[str, str] | None = None) -> dict:
    view = flow_view.view_of(_trace(plan), forms=forms)
    assert view is not None
    return view


def _widths(view: Mapping[str, object]) -> dict[tuple[str, str], object]:
    edges = view["edges"]
    assert isinstance(edges, list)
    return {(edge["item"], edge["role"]): edge["width"] for edge in edges}


def test_every_edge_width_is_the_rational_the_trace_step_carries() -> None:
    plan = _plan()
    view = flow_view.view_of(_trace(plan))
    assert view is not None
    expected = {
        (key, role): contract.rational(rate)
        for role, mapping in (
            (flow_view.ROLE_RAW_INPUT, plan.raw_inputs),
            (flow_view.ROLE_TARGET, plan.targets),
            (flow_view.ROLE_BYPRODUCT, plan.byproducts),
        )
        for key, rate in mapping.items()
    }
    assert _widths(view) == expected
    # The control: a repeating rate really is in the plan, so the equality is not trivial.
    assert contract.rational(THIRD) == {"num": 10, "den": 3}
    assert view["rule_id"] == "synthetic.plan"


def test_edges_follow_the_role_order_then_the_item_key() -> None:
    view = _view(_plan())
    order = [(edge["role"], edge["item"]) for edge in view["edges"]]
    assert order == [
        ("raw-input", "Desc_Ore_C"),
        ("raw-input", "Desc_Water_C"),
        ("target", "Desc_Alpha_C"),
        ("target", "Desc_Zeta_C"),
        ("byproduct", "Desc_Slag_C"),
    ]
    assert flow_view.ROLES == ("raw-input", "target", "byproduct")
    directions = {edge["role"]: edge["direction"] for edge in view["edges"]}
    assert directions == {"raw-input": "in", "target": "out", "byproduct": "out"}


def test_nodes_are_the_plan_steps_in_plan_order_zero_machine_step_included() -> None:
    plan = _plan()
    view = _view(plan)
    assert view["nodes"] == [
        {"recipe": step.recipe_key, "machines": contract.rational(step.machines)}
        for step in plan.steps
    ]
    machines = [node["machines"] for node in view["nodes"]]
    assert {"num": 0, "den": 1} in machines
    assert [node["recipe"] for node in view["nodes"]] == ["Recipe_B_C", "Recipe_A_C", "Recipe_C_C"]


def test_a_trace_with_no_plan_step_is_none_never_an_empty_view() -> None:
    assert flow_view.view_of(_trace(None)) is None
    # The same plan under another subject is not the plan: the subject is what is matched.
    assert flow_view.view_of(_trace(_plan(), subject="plan.badge")) is None


def test_the_first_plan_step_is_the_one_read() -> None:
    first = _plan(raw_inputs={"Desc_First_C": Fraction(1, 3)}, targets={}, byproducts={})
    second = _plan(raw_inputs={"Desc_Second_C": Fraction(2, 3)}, targets={}, byproducts={})
    base = _trace(first)
    twice = Trace(
        rule_id=base.rule_id,
        domain=base.domain,
        steps=(
            *base.steps[:-1],
            TraceStep(kind=StepKind.INPUT_READ, subject=flow_view.PLAN_SUBJECT, value=second),
            *base.steps[-1:],
        ),
        recommendation=base.recommendation,
    )
    view = flow_view.view_of(twice)
    assert view is not None
    assert [edge["item"] for edge in view["edges"]] == ["Desc_First_C"]


def test_the_marked_edge_is_the_maximum_rate_compared_exactly() -> None:
    # 25/3 is the greatest; 8333/1000 is a float-close neighbour that a float or a
    # serialised comparison could tie with or swap, and an exact one cannot.
    plan = _plan(raw_inputs={"Desc_Ore_C": Fraction(25, 3), "Desc_Near_C": Fraction(8333, 1000)})
    view = _view(plan, {"Desc_Ore_C": SOLID, "Desc_Near_C": SOLID, "Desc_Zeta_C": SOLID})
    marked = [edge for edge in view["edges"] if edge["marked"]]
    assert [(e["item"], e["role"]) for e in marked] == [("Desc_Ore_C", "raw-input")]
    assert view["marked_edge"] == {
        "item": "Desc_Ore_C",
        "role": "raw-input",
        "unit": flow_view.UNIT_ITEM,
        "reason": flow_view.MARK_HIGHEST_RATE,
    }
    assert flow_view.MARK_HIGHEST_RATE == "highest-rate"


def test_a_tie_marks_the_first_edge_in_published_order_and_only_one() -> None:
    plan = _plan(
        raw_inputs={"Desc_B_C": Fraction(4, 3)},
        targets={"Desc_A_C": Fraction(4, 3)},
        byproducts={"Desc_C_C": Fraction(4, 3)},
    )
    view = _view(plan, {"Desc_A_C": SOLID, "Desc_B_C": SOLID, "Desc_C_C": SOLID})
    marked = [(e["role"], e["item"]) for e in view["edges"] if e["marked"] is True]
    assert marked == [("raw-input", "Desc_B_C")]
    assert view["marked_edge"] == {
        "item": "Desc_B_C",
        "role": "raw-input",
        "unit": flow_view.UNIT_ITEM,
        "reason": flow_view.MARK_HIGHEST_RATE,
    }


# ---------------------------------------------------------------------------
# the mark is taken within one unit (CS-1360 gap 1, ruling Q6)
# ---------------------------------------------------------------------------


def _marked(view: Mapping[str, object]) -> list[tuple[str, str]]:
    edges = view["edges"]
    assert isinstance(edges, list)
    return [(e["role"], e["item"]) for e in edges if e["marked"] is True]


def test_a_fluid_edge_never_outranks_a_solid_edge_across_units() -> None:
    # A fluid byproduct is 5 cubic metres a minute, a solid target 1/3 of an item a
    # minute: 5 > 1/3 numerically, and the two are not the same unit.
    plan = _plan(
        raw_inputs={},
        targets={"Desc_Plate_C": Fraction(1, 3)},
        byproducts={"Desc_Water_C": Fraction(5)},
    )
    view = _view(plan, {"Desc_Plate_C": SOLID, "Desc_Water_C": LIQUID})
    assert _marked(view) == [("target", "Desc_Plate_C")]
    assert view["marked_edge"] == {
        "item": "Desc_Plate_C",
        "role": "target",
        "unit": "item",
        "reason": flow_view.MARK_HIGHEST_RATE,
    }


def test_a_solid_larger_than_every_fluid_is_marked() -> None:
    plan = _plan(
        raw_inputs={"Desc_Ore_C": Fraction(25, 3)},
        targets={"Desc_Plate_C": Fraction(1, 3)},
        byproducts={"Desc_Water_C": Fraction(2, 3)},
    )
    view = _view(plan, {"Desc_Ore_C": SOLID, "Desc_Plate_C": SOLID, "Desc_Water_C": GAS})
    assert _marked(view) == [("raw-input", "Desc_Ore_C")]


def test_a_plan_of_fluids_only_marks_the_largest_fluid_in_cubic_metres() -> None:
    plan = _plan(
        raw_inputs={"Desc_Water_C": Fraction(2, 3)},
        targets={"Desc_Acid_C": Fraction(10, 3)},
        byproducts={"Desc_Gas_C": Fraction(5, 2)},
    )
    forms = {"Desc_Water_C": LIQUID, "Desc_Acid_C": LIQUID, "Desc_Gas_C": GAS}
    view = _view(plan, forms)
    assert _marked(view) == [("target", "Desc_Acid_C")]
    assert view["marked_edge"] == {
        "item": "Desc_Acid_C",
        "role": "target",
        "unit": flow_view.UNIT_VOLUME,
        "reason": flow_view.MARK_HIGHEST_RATE,
    }
    assert flow_view.UNIT_VOLUME == "m3"


def test_a_plan_of_solids_only_marks_the_largest_solid_in_items() -> None:
    plan = _plan(
        raw_inputs={"Desc_Ore_C": Fraction(2, 3)},
        targets={"Desc_Plate_C": Fraction(10, 3)},
        byproducts={"Desc_Slag_C": Fraction(5, 2)},
    )
    forms = {"Desc_Ore_C": SOLID, "Desc_Plate_C": SOLID, "Desc_Slag_C": SOLID}
    view = _view(plan, forms)
    assert _marked(view) == [("target", "Desc_Plate_C")]
    assert {e["unit"] for e in view["edges"]} == {"item"}


def test_an_unknown_unit_edge_is_never_marked_however_large() -> None:
    plan = _plan(
        raw_inputs={"Desc_Mystery_C": Fraction(900)},
        targets={"Desc_Plate_C": Fraction(1, 3)},
        byproducts={"Desc_Blank_C": Fraction(800), "Desc_Water_C": Fraction(700)},
    )
    forms = {"Desc_Plate_C": SOLID, "Desc_Blank_C": "", "Desc_Water_C": LIQUID}
    view = _view(plan, forms)
    assert _marked(view) == [("target", "Desc_Plate_C")]
    # With no solid at all the largest KNOWN-unit edge, a fluid, is the one marked.
    fluid_only = _view(plan, {"Desc_Water_C": LIQUID, "Desc_Blank_C": INVALID})
    assert _marked(fluid_only) == [("byproduct", "Desc_Water_C")]
    assert fluid_only["marked_edge"]["unit"] == "m3"


def test_a_plan_whose_every_unit_is_unknown_marks_nothing() -> None:
    for forms in (None, {"Desc_Ore_C": INVALID, "Desc_Zeta_C": "RF_PLASMA"}):
        view = _view(_plan(), forms)
        assert view["edges"]
        assert [e["unit"] for e in view["edges"]] == ["unknown"] * len(view["edges"])
        assert _marked(view) == []
        assert view["marked_edge"] is None


def test_a_tie_within_a_unit_marks_the_first_and_never_ties_across_units() -> None:
    plan = _plan(
        raw_inputs={"Desc_Water_C": Fraction(4, 3)},
        targets={"Desc_Plate_C": Fraction(4, 3), "Desc_Rod_C": Fraction(4, 3)},
        byproducts={},
    )
    view = _view(plan, {"Desc_Water_C": LIQUID, "Desc_Plate_C": SOLID, "Desc_Rod_C": SOLID})
    # The fluid is published first and ties the solids numerically; the solid unit wins
    # and, within it, the first in published order.
    assert _marked(view) == [("target", "Desc_Plate_C")]
    assert [e["marked"] for e in view["edges"]].count(True) == 1


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        (SOLID, "item"),
        (LIQUID, "m3"),
        (GAS, "m3"),
        (INVALID, "unknown"),
        ("", "unknown"),
        ("rf_solid", "unknown"),
    ],
)
def test_every_edge_carries_the_unit_of_its_verbatim_form(form: str, expected: str) -> None:
    plan = _plan(raw_inputs={"Desc_Ore_C": Fraction(1, 3)}, targets={}, byproducts={})
    view = _view(plan, {"Desc_Ore_C": form})
    assert [edge["unit"] for edge in view["edges"]] == [expected]
    assert (flow_view.UNIT_ITEM, flow_view.UNIT_VOLUME, flow_view.UNIT_UNKNOWN) == (
        "item",
        "m3",
        "unknown",
    )


def test_a_step_of_another_kind_with_the_plan_subject_is_not_read() -> None:
    plan = _plan()
    only_a_rule = Trace(
        rule_id="synthetic.plan",
        domain="plan",
        steps=(
            TraceStep(kind=StepKind.RULE_FIRED, subject=flow_view.PLAN_SUBJECT, value=plan),
            TraceStep(kind=StepKind.INPUT_READ, subject="plan.status", value="ranked"),
        ),
        recommendation=Recommendation(subject_key="s", action="Build it", reason="why"),
    )
    assert flow_view.view_of(only_a_rule) is None
    # The control: the same plan as an input-read step is read.
    assert flow_view.view_of(_trace(plan)) is not None


def test_a_plan_with_no_edge_marks_none() -> None:
    view = _view(_plan(targets={}, raw_inputs={}, byproducts={}))
    assert view["edges"] == []
    assert view["marked_edge"] is None
    assert len(view["nodes"]) == len(_plan().steps)


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        (SOLID, flow_view.TRANSPORT_BELT),
        (LIQUID, flow_view.TRANSPORT_PIPE),
        (GAS, flow_view.TRANSPORT_PIPE),
        (INVALID, flow_view.TRANSPORT_UNKNOWN),
        ("", flow_view.TRANSPORT_UNKNOWN),
        ("(RF_SOLID)", flow_view.TRANSPORT_UNKNOWN),
        ("rf_solid", flow_view.TRANSPORT_UNKNOWN),
        ("RF_PLASMA", flow_view.TRANSPORT_UNKNOWN),
    ],
)
def test_transport_is_read_from_the_verbatim_form(form: str, expected: str) -> None:
    plan = _plan(raw_inputs={"Desc_Ore_C": Fraction(1, 3)}, targets={}, byproducts={})
    view = _view(plan, {"Desc_Ore_C": form})
    assert [edge["transport"] for edge in view["edges"]] == [expected]


def test_an_absent_key_and_no_forms_at_all_read_unknown() -> None:
    plan = _plan(raw_inputs={"Desc_Ore_C": Fraction(1, 3)}, targets={}, byproducts={})
    absent = _view(plan, {"Desc_Other_C": SOLID})
    none_at_all = _view(plan, None)
    for view in (absent, none_at_all):
        assert [edge["transport"] for edge in view["edges"]] == ["unknown"]
    assert (flow_view.TRANSPORT_BELT, flow_view.TRANSPORT_PIPE, flow_view.TRANSPORT_UNKNOWN) == (
        "belt",
        "pipe",
        "unknown",
    )


def _walk(node: object) -> list[object]:
    """Every leaf and every key under a payload, recursively."""
    if isinstance(node, dict):
        out: list[object] = []
        for key, value in node.items():
            out.append(key)
            out.extend(_walk(value))
        return out
    if isinstance(node, list | tuple):
        return [leaf for item in node for leaf in _walk(item)]
    return [node]


def test_no_value_is_a_float_and_none_names_saturation() -> None:
    forms = {"Desc_Ore_C": SOLID, "Desc_Water_C": LIQUID}
    view = _view(_plan(), forms)
    leaves = _walk(view)
    assert leaves  # the walk reached something
    floats = [leaf for leaf in leaves if isinstance(leaf, float)]
    assert floats == []
    # A claim is a VALUE: no string leaf names one, and with no capacity supplied every
    # saturated field is unknown, never false. The keys are the schema, not a claim.
    words = [
        leaf
        for leaf in leaves
        if isinstance(leaf, str) and ("saturated" in leaf.lower() or "bottleneck" in leaf.lower())
    ]
    assert words == ["saturated" for _edge in view["edges"]], (
        "only the schema key, once per edge, may spell the word"
    )
    assert [edge["saturated"] for edge in view["edges"]] == [None] * len(view["edges"])
    assert [edge["capacity"] for edge in view["edges"]] == [None] * len(view["edges"])
    # The control: the walker does see a planted word and a planted float.
    assert _walk({"k": ["bottleneck", 1.5]}) == ["k", "bottleneck", 1.5]
    # And the wire accepts the whole thing, which refuses a float.
    assert contract.encode({"flow": view})


def test_the_view_is_ascii_and_its_keys_are_closed() -> None:
    view = _view(_plan(), {"Desc_Ore_C": SOLID})
    assert frozenset(view) == {"rule_id", "nodes", "edges", "links", "marked_edge"}
    assert all(
        frozenset(edge)
        == {
            "item",
            "role",
            "direction",
            "transport",
            "unit",
            "width",
            "marked",
            "capacity",
            "saturated",
        }
        for edge in view["edges"]
    )
    assert frozenset(view["marked_edge"]) == {"item", "role", "unit", "reason"}
    assert contract.encode({"flow": view}).isascii()


# ---------------------------------------------------------------------------
# the derivation endpoint
# ---------------------------------------------------------------------------


def _plan_card_advice(plan: ProductionPlan | None) -> tuple[Advice, str]:
    card = Card(_trace(plan))
    advice = Advice(
        traces=(),
        cards=(AdvisedCard(card=card, state=CardState("new"), muted=False),),
        new_world=True,
    )
    return advice, card.id


def _derivation(source: advice_fixtures._Source, log: list[str], wanted: str) -> contract.Response:
    providers = advice_fixtures._LoggedProviders(log)  # noqa: SLF001 - the shared stub
    published = advice_endpoint.routes(providers, providers, source)
    handler = {r.template: r.handler for r in published}[advice_endpoint.DERIVATION_ENDPOINT]
    return handler({advice_endpoint.ID_PARAMETER: wanted})


def test_the_derivation_key_set_carries_flow() -> None:
    assert "flow" in advice_endpoint.DERIVATION_KEYS
    assert {"id", "rule_id", "derivation", "flow"} == advice_endpoint.DERIVATION_KEYS


def test_the_derivation_endpoint_serves_the_flow_of_a_plan_card_over_one_registry_read() -> None:
    registry = solve_synthetic.solve_registry()
    ore, fluid = solve_synthetic.SOLVE_ORE_ITEM, solve_synthetic.SOLVE_FLUID_ITEM
    plan = _plan(
        raw_inputs={ore: Fraction(25, 3)},
        targets={fluid: Fraction(10, 3), "Desc_Unlisted_C": Fraction(1, 3)},
        byproducts={},
    )
    found, card_id = _plan_card_advice(plan)
    log: list[str] = []
    response = _derivation(advice_fixtures._Source(found, log=log), log, card_id)  # noqa: SLF001
    assert response.http_status == contract.HTTP_OK
    problems = contract.contract_problems(response)
    assert len(problems) == 0, problems
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert frozenset(data) == advice_endpoint.DERIVATION_KEYS
    forms = {key: item.form for key, item in registry.items.items()}
    assert data["flow"] == flow_view.view_of(_trace(plan), forms=forms)
    transport = {e["item"]: e["transport"] for e in data["flow"]["edges"]}
    assert transport == {ore: "belt", fluid: "pipe", "Desc_Unlisted_C": "unknown"}
    units = {e["item"]: e["unit"] for e in data["flow"]["edges"]}
    assert units == {ore: "item", fluid: "m3", "Desc_Unlisted_C": "unknown"}
    assert log.count("registry") == 1


def test_a_card_that_holds_no_plan_serves_flow_as_null() -> None:
    found, card_id = _plan_card_advice(None)
    log: list[str] = []
    response = _derivation(advice_fixtures._Source(found, log=log), log, card_id)  # noqa: SLF001
    assert response.http_status == contract.HTTP_OK
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert "flow" in data
    assert data["flow"] is None


def test_the_closed_spellings_are_bound_to_their_owners() -> None:
    assert flow_view.PLAN_SUBJECT == plan_rules.IN_PLAN
    assert StepKind.INPUT_READ.value == "input-read"
    assert registry_module.FORM_SOLID == SOLID
    assert registry_module.FORM_LIQUID == LIQUID
    assert registry_module.FORM_GAS == GAS
    assert registry_module.FORM_INVALID == INVALID


# ---------------------------------------------------------------------------
# the panel
# ---------------------------------------------------------------------------


def _flow_edge(item: str, role: str, num: int, den: int, *, marked: bool) -> dict:
    return {
        "item": item,
        "role": role,
        "direction": "in" if role == "raw-input" else "out",
        "transport": "belt",
        "unit": "item",
        "width": {"num": num, "den": den},
        "marked": marked,
    }


def _panel_flow_text(tmp_path: object, flow: object) -> tuple[str, bool]:
    held = panel.card("Held", "held reason")
    body = {"id": held["id"], "rule_id": held["rule_id"], "derivation": "text", "flow": flow}
    report = panel.drive(
        tmp_path,  # type: ignore[arg-type]
        panel.payload(held),
        steps=[
            {"click": panel.read_id(0)},
            {"settle": {"call": 0, "outcome": panel.answered(body)}},
        ],
    )
    region = panel.row_of(report["nodes"], "advice-flow-0")
    assert region["tag"] == "PRE"
    return region["text"], region["hidden"]


def test_the_panel_writes_one_line_per_edge_starred_and_barred(tmp_path: object) -> None:
    flow = {
        "rule_id": "x",
        "nodes": [],
        "marked_edge": None,
        "edges": [
            _flow_edge("Desc_Ore_C", "raw-input", 25, 3, marked=True),
            _flow_edge("Desc_Half_C", "target", 25, 6, marked=False),
            _flow_edge("<b>Desc_Tiny_C</b>", "byproduct", 1, 1000, marked=False),
        ],
    }
    text, hidden = _panel_flow_text(tmp_path, flow)
    assert hidden is False
    lines = text.split(chr(10))
    assert lines == [
        "* Desc_Ore_C raw-input 25/3 item per min on belt " + "#" * 20,
        "  Desc_Half_C target 25/6 item per min on belt " + "#" * 10,
        "  <b>Desc_Tiny_C</b> byproduct 1/1000 item per min on belt #",
    ]


def test_the_panel_shows_no_flow_region_when_the_body_carries_none(tmp_path: object) -> None:
    absents: tuple[object, ...] = (None, {"edges": []})
    for absent in absents:
        text, hidden = _panel_flow_text(tmp_path, absent)
        assert (text, hidden) == ("", True)


def test_a_whole_rate_renders_bare_and_a_zero_denominator_renders_dash(tmp_path: object) -> None:
    # The unmodified rateText, driven in node: den 1 reads as the bare numerator, den 0
    # (never a rate) as a dash, and an ordinary ratio as num/den. Each differs from the
    # next, so a `den === 1` slipped to `den === 0` or `den < 1` slipped to `den < 0` fails.
    flow = {
        "rule_id": "x",
        "nodes": [],
        "marked_edge": None,
        "edges": [
            _flow_edge("Desc_Whole_C", "target", 3, 1, marked=False),
            _flow_edge("Desc_Zero_C", "target", 3, 0, marked=False),
            _flow_edge("Desc_Ratio_C", "target", 3, 2, marked=False),
        ],
    }
    text, hidden = _panel_flow_text(tmp_path, flow)
    assert hidden is False
    assert text.split(chr(10)) == [
        "  Desc_Whole_C target 3 item per min on belt ",
        "  Desc_Zero_C target - item per min on belt ",
        "  Desc_Ratio_C target 3/2 item per min on belt ",
    ]


# ---------------------------------------------------------------------------
# CS-1360 closure - internal links, capacity and saturation
# ---------------------------------------------------------------------------

ORE: Final = "Desc_Ore_C"
PLATE: Final = "Desc_Plate_C"
INGOT: Final = "Desc_Ingot_C"
WATER: Final = "Desc_Water_C"
MAKE_PLATE: Final = "Recipe_Plate_C"
MAKE_INGOT: Final = "Recipe_Ingot_C"
CHAIN_FORMS: Final = {ORE: SOLID, PLATE: SOLID, INGOT: SOLID, WATER: LIQUID}


def _transport(
    key: str, per_minute: Fraction | None, *, kind: str = "belt", unit: str = "item"
) -> registry_module.Transport:
    """One synthetic transport class, built the way the registry builds it."""
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


MK1 = _transport("Build_Belt1_C", Fraction(60))
MK2 = _transport("Build_Belt2_C", Fraction(120))
PIPE1 = _transport("Build_Pipe1_C", Fraction(300), kind="pipe", unit="m3")


def _chain(*, ore: Fraction = Fraction(90)) -> ProductionPlan:
    """Ore into plates into ingots: one raw input, one internal link, one target."""
    return ProductionPlan(
        steps=(PlanStep(MAKE_PLATE, Fraction(3)), PlanStep(MAKE_INGOT, Fraction(2))),
        targets={INGOT: Fraction(30)},
        raw_inputs={ORE: ore},
        byproducts={},
        excluded=(),
        byproduct_policy="sinkable",
        edges=(
            PlanEdge(None, ORE, MAKE_PLATE, ore, "item", None),
            PlanEdge(MAKE_PLATE, PLATE, MAKE_INGOT, Fraction(45), "item", None),
            PlanEdge(MAKE_INGOT, INGOT, None, Fraction(30), "item", "target"),
        ),
    )


def _capacity_view(
    plan: ProductionPlan, *members: registry_module.Transport, forms: Mapping[str, str] | None
) -> dict:
    view = flow_view.view_of(_trace(plan), forms=forms, transports=_carriers(*members))
    assert view is not None
    return view


def _by_item(rows: list[dict]) -> dict[str, dict]:
    return {row["item"]: row for row in rows}


def _empty_plan(
    edges: tuple[PlanEdge, ...] = (), raw_inputs: Mapping[str, Fraction] | None = None
) -> ProductionPlan:
    return ProductionPlan(
        steps=(),
        targets={},
        raw_inputs={} if raw_inputs is None else raw_inputs,
        byproducts={},
        excluded=(),
        byproduct_policy="sinkable",
        edges=edges,
    )


def test_the_internal_links_are_the_plan_edges_that_have_both_ends() -> None:
    view = _view(_chain(), CHAIN_FORMS)
    assert view["links"] == [
        {
            "producer": MAKE_PLATE,
            "consumer": MAKE_INGOT,
            "item": PLATE,
            "transport": "belt",
            "unit": "item",
            "width": contract.rational(Fraction(45)),
            "capacity": None,
            "saturated": None,
        }
    ]
    # THE CONTROL: the boundary edges are still the boundary, once each, and not links.
    assert [(edge["item"], edge["role"]) for edge in view["edges"]] == [
        (ORE, "raw-input"),
        (INGOT, "target"),
    ]


def test_a_plan_with_no_published_edges_serves_no_links() -> None:
    assert _view(_plan())["links"] == []


def test_every_allocated_link_of_a_shared_item_is_served_in_the_plan_edge_order() -> None:
    # Two producers and two consumers of one item: four allocations, none merged.
    rates = {
        ("P1", "C1"): Fraction(1, 3),
        ("P1", "C2"): Fraction(2, 3),
        ("P2", "C1"): Fraction(5, 7),
        ("P2", "C2"): Fraction(10, 7),
    }
    plan = _empty_plan(
        tuple(
            PlanEdge(producer, PLATE, consumer, rate, "item", None)
            for (producer, consumer), rate in rates.items()
        )
    )
    links = _view(plan, CHAIN_FORMS)["links"]
    assert [(link["producer"], link["consumer"]) for link in links] == list(rates)
    assert [link["width"] for link in links] == [contract.rational(r) for r in rates.values()]


def test_a_link_reads_its_unit_from_the_plan_edge_and_its_transport_from_the_form() -> None:
    plan = _empty_plan((PlanEdge("P", WATER, "C", Fraction(7, 3), "m3", None),))
    (link,) = _view(plan, CHAIN_FORMS)["links"]
    assert (link["unit"], link["transport"]) == ("m3", "pipe")
    (unformed,) = _view(plan, None)["links"]
    assert (unformed["unit"], unformed["transport"]) == ("m3", "unknown")


def test_each_edge_names_the_smallest_carrier_that_holds_its_rate() -> None:
    view = _capacity_view(_chain(), MK1, MK2, forms=CHAIN_FORMS)
    ore = _by_item(view["edges"])[ORE]
    assert ore["capacity"] == {"carrier": MK2.key, "per_minute": contract.rational(Fraction(120))}
    assert ore["saturated"] is False
    ingot = _by_item(view["edges"])[INGOT]
    assert ingot["capacity"]["carrier"] == MK1.key
    (link,) = view["links"]
    assert link["capacity"]["carrier"] == MK1.key
    assert link["saturated"] is False


def test_a_rate_at_or_above_the_best_known_carrier_is_saturated() -> None:
    def edges_at(ore: Fraction) -> dict[str, dict]:
        return _by_item(_capacity_view(_chain(ore=ore), MK1, MK2, forms=CHAIN_FORMS)["edges"])

    at_best = edges_at(Fraction(120))
    assert at_best[ORE]["saturated"] is True
    assert at_best[ORE]["capacity"]["carrier"] == MK2.key
    above = edges_at(Fraction(361, 3))
    assert above[ORE]["saturated"] is True
    assert above[ORE]["capacity"] is None  # no single carrier holds it
    # THE CONTROL: just under the best is not saturated, so the boundary is exact.
    assert edges_at(Fraction(359, 3))[ORE]["saturated"] is False


def test_a_link_can_be_saturated_while_the_boundary_is_not() -> None:
    plan = _chain()
    internal = PlanEdge(MAKE_PLATE, PLATE, MAKE_INGOT, Fraction(500), "item", None)
    plan = dataclasses.replace(plan, edges=(plan.edges[0], internal, plan.edges[2]))
    view = _capacity_view(plan, MK1, MK2, forms=CHAIN_FORMS)
    assert _by_item(view["edges"])[ORE]["saturated"] is False
    (link,) = view["links"]
    assert (link["saturated"], link["capacity"]) == (True, None)


def test_a_fluid_edge_is_carried_by_a_pipe_never_a_belt() -> None:
    plan = _empty_plan(raw_inputs={WATER: Fraction(250)})
    water = _by_item(_capacity_view(plan, MK1, MK2, PIPE1, forms=CHAIN_FORMS)["edges"])[WATER]
    assert water["capacity"]["carrier"] == PIPE1.key
    assert water["saturated"] is False
    # Only belts supplied: nothing carries a fluid, which is UNKNOWN, never a free pass.
    only_belts = _by_item(_capacity_view(plan, MK1, MK2, forms=CHAIN_FORMS)["edges"])[WATER]
    assert (only_belts["capacity"], only_belts["saturated"]) == (None, None)


def test_an_unknown_unit_and_an_unpublished_rate_read_unknown_never_saturated() -> None:
    plan = _chain()
    unformed = _by_item(_capacity_view(plan, MK1, MK2, forms=None)["edges"])
    assert {row["saturated"] for row in unformed.values()} == {None}
    withdrawn = _transport("Build_Belt9_C", None)
    unrated = _by_item(_capacity_view(plan, withdrawn, forms=CHAIN_FORMS)["edges"])
    assert {(row["capacity"], row["saturated"]) for row in unrated.values()} == {(None, None)}
    # THE CONTROL: with a real carrier the same plan does answer.
    rated = _by_item(_capacity_view(plan, withdrawn, MK2, forms=CHAIN_FORMS)["edges"])
    assert rated[ORE]["capacity"]["carrier"] == MK2.key


def test_equal_capacity_classes_resolve_to_the_first_key() -> None:
    twin_b = _transport("Build_Z_C", Fraction(120))
    twin_a = _transport("Build_A_C", Fraction(120))
    ore = _by_item(_capacity_view(_chain(), twin_b, twin_a, forms=CHAIN_FORMS)["edges"])[ORE]
    assert ore["capacity"]["carrier"] == "Build_A_C"


def test_supplying_capacity_moves_no_width_and_no_mark() -> None:
    plan = _chain()
    bare = _view(plan, CHAIN_FORMS)
    rated = _capacity_view(plan, MK1, MK2, PIPE1, forms=CHAIN_FORMS)
    assert [(e["item"], e["width"], e["marked"]) for e in rated["edges"]] == [
        (e["item"], e["width"], e["marked"]) for e in bare["edges"]
    ]
    assert rated["marked_edge"] == bare["marked_edge"]
    assert contract.encode({"flow": rated}).isascii()
    assert [leaf for leaf in _walk(rated) if isinstance(leaf, float)] == []


def test_the_transport_spellings_are_bound_to_their_owners() -> None:
    assert registry_module.TRANSPORT_UNIT_ITEM == flow_view.UNIT_ITEM
    assert registry_module.TRANSPORT_UNIT_CUBIC_METRE == flow_view.UNIT_VOLUME
    assert registry_module.TRANSPORT_KIND_BELT == flow_view.TRANSPORT_BELT
    assert registry_module.TRANSPORT_KIND_PIPE == flow_view.TRANSPORT_PIPE


def test_the_derivation_endpoint_hands_the_registrys_transports_to_the_view() -> None:
    ore_rate = Fraction(90)
    registry = solve_synthetic.solve_registry()
    rated = dataclasses.replace(registry, transports=_carriers(MK1, MK2, PIPE1))
    # The registry knows the synthetic ore, so the boundary edge reads its form as a solid.
    ore = solve_synthetic.SOLVE_ORE_ITEM
    chain = _chain(ore=ore_rate)
    plan = dataclasses.replace(
        chain,
        raw_inputs={ore: ore_rate},
        edges=(PlanEdge(None, ore, MAKE_PLATE, ore_rate, "item", None), *chain.edges[1:]),
    )
    found, card_id = _plan_card_advice(plan)
    log: list[str] = []
    providers = advice_fixtures._LoggedProviders(log)  # noqa: SLF001 - the shared stub
    providers._registry = rated  # noqa: SLF001 - a registry that carries transports
    source = advice_fixtures._Source(found, log=log)  # noqa: SLF001
    published = advice_endpoint.routes(providers, providers, source)
    handler = {r.template: r.handler for r in published}[advice_endpoint.DERIVATION_ENDPOINT]
    response = handler({advice_endpoint.ID_PARAMETER: card_id})
    assert response.http_status == contract.HTTP_OK
    forms = {key: item.form for key, item in rated.items.items()}
    expected = flow_view.view_of(_trace(plan), forms=forms, transports=rated.transports)
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert data["flow"] == expected
    # THE CONTROL: the expectation itself carries a carrier, so equality is not two Nones.
    assert expected is not None
    assert _by_item(expected["edges"])[ore]["capacity"]["carrier"] == MK2.key
    assert expected["links"][0]["capacity"]["carrier"] == MK1.key
    assert log.count("registry") == 1


def test_the_endpoint_serves_no_capacity_when_the_registry_publishes_no_transport() -> None:
    plan = _chain()
    found, card_id = _plan_card_advice(plan)
    log: list[str] = []
    response = _derivation(advice_fixtures._Source(found, log=log), log, card_id)  # noqa: SLF001
    data = response.payload["data"]
    assert isinstance(data, dict)
    assert {edge["saturated"] for edge in data["flow"]["edges"]} == {None}


# ---------------------------------------------------------------------------
# the panel, closure
# ---------------------------------------------------------------------------


def _panel_flow_lines(tmp_path: object, flow: object) -> list[str]:
    text, hidden = _panel_flow_text(tmp_path, flow)
    assert hidden is False
    return text.split(chr(10))


def test_a_starred_line_names_its_unit_and_a_fluid_is_not_an_item(tmp_path: object) -> None:
    fluid = _flow_edge("Desc_Water_C", "raw-input", 9, 2, marked=True)
    fluid["transport"] = "pipe"
    fluid["unit"] = "m3"
    lines = _panel_flow_lines(
        tmp_path, {"rule_id": "x", "nodes": [], "marked_edge": None, "edges": [fluid]}
    )
    assert lines == ["* Desc_Water_C raw-input 9/2 m3 per min on pipe " + "#" * 20]


def test_an_edge_with_no_unit_reads_unknown_on_the_panel(tmp_path: object) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 5, 1, marked=False)
    del edge["unit"]
    lines = _panel_flow_lines(
        tmp_path, {"rule_id": "x", "nodes": [], "marked_edge": None, "edges": [edge]}
    )
    assert lines == ["  Desc_Ore_C raw-input 5 unknown per min on belt "]


def test_the_panel_transcribes_the_carrier_and_the_saturated_flag(tmp_path: object) -> None:
    carried = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=True)
    carried["capacity"] = {"carrier": "Build_Belt2_C", "per_minute": {"num": 120, "den": 1}}
    carried["saturated"] = False
    full = _flow_edge("Desc_Big_C", "target", 500, 1, marked=False)
    full["capacity"] = None
    full["saturated"] = True
    unknown = _flow_edge("Desc_Odd_C", "target", 1, 1, marked=False)
    unknown["capacity"] = None
    unknown["saturated"] = None
    lines = _panel_flow_lines(
        tmp_path,
        {"rule_id": "x", "nodes": [], "marked_edge": None, "edges": [carried, full, unknown]},
    )
    assert lines[0].startswith("* Desc_Ore_C raw-input 90 item per min on belt ")
    assert lines[0].endswith(" carrier Build_Belt2_C 120 per min")
    assert "saturated" not in lines[0]
    assert lines[1].endswith(" saturated")
    assert "carrier" not in lines[1]
    assert lines[2] == "  Desc_Odd_C target 1 item per min on belt #"


def test_the_panel_lists_the_chain_links_under_one_allocation_heading(tmp_path: object) -> None:
    link = {
        "producer": "Recipe_Plate_C",
        "consumer": "Recipe_Ingot_C",
        "item": "Desc_Plate_C",
        "transport": "belt",
        "unit": "item",
        "width": {"num": 45, "den": 1},
        "capacity": {"carrier": "Build_Belt1_C", "per_minute": {"num": 60, "den": 1}},
        "saturated": False,
    }
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=True)
    lines = _panel_flow_lines(
        tmp_path,
        {"rule_id": "x", "nodes": [], "marked_edge": None, "edges": [edge], "links": [link]},
    )
    assert lines[0].startswith("* Desc_Ore_C")
    assert lines[1:] == [
        "chain, allocated not routed:",
        "  Recipe_Plate_C -> Recipe_Ingot_C Desc_Plate_C 45 item per min on belt"
        " carrier Build_Belt1_C 60 per min",
    ]
    # No links, no heading: the boundary reads as before.
    assert len(_panel_flow_lines(tmp_path, {"edges": [edge], "links": []})) == 1
