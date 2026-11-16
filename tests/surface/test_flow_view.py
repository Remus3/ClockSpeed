"""CS-1360 - the boundary flow view a derivation carries.

The view is a projection of the ProductionPlan the trace already holds, so every arm
here builds a plan by hand with Fractions that do not terminate and reads it back off
a trace. Nothing re-solves: an edge width that equalled a re-solve would agree with the
solver by construction and could never catch a view that dropped the trace's own number.

WHAT THE VIEW IS. The boundary edges (raw inputs, targets, byproducts) and the chain's
internal links, each carrying the exact rate as its width. The BOTTLENECK mark, the carrier of
each edge, its utilisation and whether it saturates are not computed here: the advisor records
them as one input of the plan rule (``plan.carry``), and the view transcribes that record from
the trace. The arms that build a carry build it with the real ``solve.carry.carry_of`` and
record it as the rule would, so a view that computed its own would be told apart by an arm
whose recorded bottleneck disagrees with the rates.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.advisor.advise import Advice, AdvisedCard
from clockspeed.advisor.cards import Card
from clockspeed.advisor.ledger import CardState
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.advisor.trace import Recommendation, StepKind, Trace, TraceStep
from clockspeed.data import registry as registry_module
from clockspeed.solve import carry as carry_module
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
REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PERCENT_7_5: Final = 8
PERCENT_3_75: Final = 4
PERCENT_OVER_FULL: Final = 100


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


ORE: Final = "Desc_Ore_C"
PLATE: Final = "Desc_Plate_C"
INGOT: Final = "Desc_Ingot_C"
WATER: Final = "Desc_Water_C"
ACID: Final = "Desc_Acid_C"
MAKE_PLATE: Final = "Recipe_Plate_C"
MAKE_INGOT: Final = "Recipe_Ingot_C"
MAKE_ACID: Final = "Recipe_Acid_C"
CHAIN_FORMS: Final = {ORE: SOLID, PLATE: SOLID, INGOT: SOLID, WATER: LIQUID, ACID: LIQUID}


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


MK1 = _transport("Build_Belt1_C", Fraction(600))
MK2 = _transport("Build_Belt2_C", Fraction(1200))
PIPE1 = _transport("Build_Pipe1_C", Fraction(300), kind="pipe", unit="m3")
PIPE2 = _transport("Build_Pipe2_C", Fraction(600), kind="pipe", unit="m3")
FLEET: Final = _carriers(MK1, MK2, PIPE1, PIPE2)


def _plan_of_edges(
    *edges: PlanEdge,
    raw_inputs: Mapping[str, Fraction] | None = None,
    targets: Mapping[str, Fraction] | None = None,
    byproducts: Mapping[str, Fraction] | None = None,
) -> ProductionPlan:
    """A plan whose boundary totals are the ones given and whose edges are exactly these."""
    return ProductionPlan(
        steps=(PlanStep(MAKE_PLATE, Fraction(3)), PlanStep(MAKE_INGOT, Fraction(2))),
        targets={} if targets is None else targets,
        raw_inputs={} if raw_inputs is None else raw_inputs,
        byproducts={} if byproducts is None else byproducts,
        excluded=(),
        byproduct_policy="sinkable",
        edges=edges,
    )


def _with_carry(plan: ProductionPlan, transports: Mapping[str, object] | None) -> Trace:
    """The trace the rule would record: the plan, then the carry the advisor computed for it."""
    base = _trace(plan)
    if transports is None:
        return base
    report = carry_module.carry_of(plan.edges, transports)  # type: ignore[arg-type]
    return Trace(
        rule_id=base.rule_id,
        domain=base.domain,
        steps=(
            *base.steps[:-1],
            TraceStep(
                kind=StepKind.INPUT_READ,
                subject="plan.carry",
                source="solve.carry.carry_of",
                value=report,
            ),
            *base.steps[-1:],
        ),
        recommendation=base.recommendation,
    )


def _carried_view(
    plan: ProductionPlan,
    transports: Mapping[str, object] | None = None,
    forms: Mapping[str, str] | None = CHAIN_FORMS,
) -> dict:
    view = flow_view.view_of(_with_carry(plan, transports), forms=forms)
    assert view is not None
    return view


def _by_item(rows: list[dict]) -> dict[str, dict]:
    return {row["item"]: row for row in rows}


def _every_marked(view: Mapping[str, object]) -> list[tuple[str, str]]:
    """Every row of the view flagged marked, as (kind, item), edges before links."""
    found: list[tuple[str, str]] = []
    for kind in ("edges", "links"):
        rows = view[kind]
        assert isinstance(rows, list)
        found.extend((kind, row["item"]) for row in rows if row["marked"] is True)
    return found


def test_the_mark_is_the_highest_utilisation_not_the_highest_rate() -> None:
    # A solid at 600 a minute is 1/2 of the best belt (1200); a fluid at 540 is 9/10 of the
    # best pipe (600). The solid has the greater rate and the fluid the greater utilisation.
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(600), "item", None),
        PlanEdge(MAKE_ACID, ACID, None, Fraction(540), "m3", "target"),
        raw_inputs={ORE: Fraction(600)},
        targets={ACID: Fraction(540)},
    )
    view = _carried_view(plan, FLEET)
    assert _every_marked(view) == [("edges", ACID)]
    assert view["marked_edge"] == {
        "producer": MAKE_ACID,
        "item": ACID,
        "consumer": None,
        "role": "target",
        "unit": "m3",
        "utilisation": {"num": 9, "den": 10},
        "percent": 90,
        "reason": "bottleneck",
    }
    assert flow_view.MARK_BOTTLENECK == "bottleneck"


def test_an_internal_link_can_be_the_bottleneck() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(300), "item", None),
        PlanEdge(MAKE_PLATE, PLATE, MAKE_INGOT, Fraction(1140), "item", None),
        PlanEdge(MAKE_INGOT, INGOT, None, Fraction(30), "item", "target"),
        raw_inputs={ORE: Fraction(300)},
        targets={INGOT: Fraction(30)},
    )
    view = _carried_view(plan, FLEET)
    assert _every_marked(view) == [("links", PLATE)]
    assert view["marked_edge"]["item"] == PLATE
    assert view["marked_edge"]["role"] == "internal"
    assert view["marked_edge"]["utilisation"] == {"num": 19, "den": 20}
    # THE CONTROL: no boundary edge is flagged, so the link is the only mark.
    assert not any(edge["marked"] for edge in view["edges"])


def test_a_row_with_a_carry_row_takes_its_unit_from_it_not_from_the_forms() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(900), "item", None),
        PlanEdge(MAKE_PLATE, ACID, None, Fraction(30), "m3", "target"),
        raw_inputs={ORE: Fraction(900)},
        targets={ACID: Fraction(30)},
    )
    for forms in (None, {}, {ORE: LIQUID, ACID: SOLID}):  # none, absent, or contradicting
        view = _carried_view(plan, FLEET, forms=forms)
        assert view["marked_edge"]["unit"] == "item"
        by_item = _by_item(view["edges"])
        assert by_item[ORE]["unit"] == "item"
        assert by_item[ORE]["marked"] is True
        assert by_item[ACID]["unit"] == "m3"
    # THE CONTROL: an edge with no carry row (no capacity) still reads its unit from the forms.
    bare = _carried_view(plan, None, forms={ORE: SOLID, ACID: LIQUID})
    assert [e["unit"] for e in bare["edges"]] == ["item", "m3"]
    assert bare["marked_edge"] is None


def test_a_byproduct_edge_can_be_the_bottleneck_and_reads_as_a_byproduct() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(60), "item", None),
        PlanEdge(MAKE_PLATE, INGOT, None, Fraction(30), "item", "target"),
        PlanEdge(MAKE_PLATE, PLATE, None, Fraction(1080), "item", "byproduct"),
        raw_inputs={ORE: Fraction(60)},
        targets={INGOT: Fraction(30)},
        byproducts={PLATE: Fraction(1080)},
    )
    view = _carried_view(plan, FLEET)
    assert _every_marked(view) == [("edges", PLATE)]
    assert view["marked_edge"]["role"] == "byproduct"
    assert view["marked_edge"]["utilisation"] == {"num": 9, "den": 10}
    by_role = {(e["role"], e["item"]): e["marked"] for e in view["edges"]}
    assert by_role == {
        ("raw-input", ORE): False,
        ("target", INGOT): False,
        ("byproduct", PLATE): True,
    }


def test_no_known_capacity_marks_nothing() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(600), "item", None),
        PlanEdge(MAKE_PLATE, INGOT, None, Fraction(30), "item", "target"),
        raw_inputs={ORE: Fraction(600)},
        targets={INGOT: Fraction(30)},
    )
    for transports in (None, {}, _carriers(_transport("Build_Belt9_C", None))):
        view = _carried_view(plan, transports)
        assert view["edges"]  # THE CONTROL: there is a flow to mark and nothing marks it
        assert view["marked_edge"] is None
        assert _every_marked(view) == []


def test_the_view_transcribes_the_recorded_bottleneck() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(900), "item", None),
        PlanEdge(MAKE_PLATE, INGOT, None, Fraction(60), "item", "target"),
        raw_inputs={ORE: Fraction(900)},
        targets={INGOT: Fraction(60)},
    )
    honest = carry_module.carry_of(plan.edges, FLEET)
    assert honest.bottleneck == 0  # the rates favour the ore edge
    named = dataclasses.replace(honest, bottleneck=1)  # the trace names the ingot edge
    base = _trace(plan)
    trace = Trace(
        rule_id=base.rule_id,
        domain=base.domain,
        steps=(
            *base.steps[:-1],
            TraceStep(kind=StepKind.INPUT_READ, subject="plan.carry", value=named),
            *base.steps[-1:],
        ),
        recommendation=base.recommendation,
    )
    view = flow_view.view_of(trace, forms=CHAIN_FORMS)
    assert view is not None
    assert _every_marked(view) == [("edges", INGOT)]
    assert view["marked_edge"]["utilisation"] == contract.rational(Fraction(60, 1200))
    # The view computes no carrier of its own: it takes no transports.
    assert "transports" not in inspect.signature(flow_view.view_of).parameters


def test_the_view_does_no_capacity_arithmetic_of_its_own() -> None:
    source = Path(flow_view.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned = {"_capacity_of", "_rated_carriers", "_marked_position", "MARK_HIGHEST_RATE"}
    named = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in banned}
    defined = {
        n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in banned
    }
    divisions = [
        n for n in ast.walk(tree) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
    ]
    assert named == set()
    assert defined == set()
    assert divisions == []
    # THE CONTROL: the same walk does see a planted division and a planted definition.
    planted = ast.parse("def _capacity_of(a, b):\n    return a / b\n")
    assert [n for n in ast.walk(planted) if isinstance(n, ast.BinOp)]
    assert [n for n in ast.walk(planted) if isinstance(n, ast.FunctionDef)]


def test_a_recorded_report_with_no_bottleneck_marks_nothing() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(600), "item", None),
        raw_inputs={ORE: Fraction(600)},
    )
    base = _trace(plan)
    empty = carry_module.CarryReport(rows=(), bottleneck=None)
    trace = Trace(
        rule_id=base.rule_id,
        domain=base.domain,
        steps=(
            *base.steps[:-1],
            TraceStep(kind=StepKind.INPUT_READ, subject="plan.carry", value=empty),
            *base.steps[-1:],
        ),
        recommendation=base.recommendation,
    )
    view = flow_view.view_of(trace, forms=CHAIN_FORMS)
    assert view is not None
    assert view["marked_edge"] is None
    assert _every_marked(view) == []


def test_a_carry_step_of_another_kind_is_not_read() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, Fraction(600), "item", None),
        raw_inputs={ORE: Fraction(600)},
    )
    report = carry_module.carry_of(plan.edges, FLEET)
    base = _trace(plan)
    trace = Trace(
        rule_id=base.rule_id,
        domain=base.domain,
        steps=(
            *base.steps[:-1],
            TraceStep(kind=StepKind.RULE_FIRED, subject="plan.carry", value=report),
            *base.steps[-1:],
        ),
        recommendation=base.recommendation,
    )
    view = flow_view.view_of(trace, forms=CHAIN_FORMS)
    assert view is not None
    assert view["marked_edge"] is None
    # THE CONTROL: the same report as an input-read step does mark.
    assert _carried_view(plan, FLEET)["marked_edge"] is not None


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
    view = _carried_view(_chain(), FLEET)
    assert frozenset(view) == {"rule_id", "nodes", "edges", "links", "marked_edge"}
    edge_keys = {
        "item",
        "role",
        "direction",
        "transport",
        "unit",
        "width",
        "marked",
        "capacity",
        "fastest",
        "utilisation",
        "percent",
        "saturated",
    }
    assert all(frozenset(edge) == edge_keys for edge in view["edges"])
    assert all(
        frozenset(link) == (edge_keys - {"role", "direction"}) | {"producer", "consumer"}
        for link in view["links"]
    )
    assert frozenset(view["marked_edge"]) == {
        "producer",
        "item",
        "consumer",
        "role",
        "unit",
        "utilisation",
        "percent",
        "reason",
    }
    assert contract.encode({"flow": view}).isascii()


# ---------------------------------------------------------------------------
# the derivation endpoint
# ---------------------------------------------------------------------------


def _plan_card_advice(
    plan: ProductionPlan | None, transports: Mapping[str, object] | None = None
) -> tuple[Advice, str]:
    card = Card(_trace(plan) if plan is None else _with_carry(plan, transports))
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
# internal links and the carriers the trace recorded
# ---------------------------------------------------------------------------


def _chain(*, ore: Fraction = Fraction(90)) -> ProductionPlan:
    """Ore into plates into ingots: one raw input, one internal link, one target."""
    return _plan_of_edges(
        PlanEdge(None, ORE, MAKE_PLATE, ore, "item", None),
        PlanEdge(MAKE_PLATE, PLATE, MAKE_INGOT, Fraction(45), "item", None),
        PlanEdge(MAKE_INGOT, INGOT, None, Fraction(30), "item", "target"),
        raw_inputs={ORE: ore},
        targets={INGOT: Fraction(30)},
    )


def test_the_internal_links_are_the_plan_edges_that_have_both_ends() -> None:
    view = _carried_view(_chain())
    assert view["links"] == [
        {
            "producer": MAKE_PLATE,
            "consumer": MAKE_INGOT,
            "item": PLATE,
            "transport": "belt",
            "unit": "item",
            "width": contract.rational(Fraction(45)),
            "marked": False,
            "capacity": None,
            "fastest": None,
            "utilisation": None,
            "percent": None,
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
    rates = {
        ("P1", "C1"): Fraction(1, 3),
        ("P1", "C2"): Fraction(2, 3),
        ("P2", "C1"): Fraction(5, 7),
        ("P2", "C2"): Fraction(10, 7),
    }
    plan = _plan_of_edges(
        *(
            PlanEdge(producer, PLATE, consumer, rate, "item", None)
            for (producer, consumer), rate in rates.items()
        )
    )
    links = _carried_view(plan)["links"]
    assert [(link["producer"], link["consumer"]) for link in links] == list(rates)
    assert [link["width"] for link in links] == [contract.rational(r) for r in rates.values()]


def test_a_link_reads_its_unit_from_the_plan_edge_and_its_transport_from_the_form() -> None:
    plan = _plan_of_edges(PlanEdge("P", WATER, "C", Fraction(7, 3), "m3", None))
    (link,) = _carried_view(plan)["links"]
    assert (link["unit"], link["transport"]) == ("m3", "pipe")
    (unformed,) = _carried_view(plan, forms=None)["links"]
    assert (unformed["unit"], unformed["transport"]) == ("m3", "unknown")


def test_each_row_carries_the_recorded_carrier_utilisation_and_saturation() -> None:
    view = _carried_view(_chain(), FLEET)
    ore = _by_item(view["edges"])[ORE]
    assert ore["capacity"] == {
        "carrier": MK1.key,
        "name": "Belt1",
        "per_minute": contract.rational(Fraction(600)),
    }
    assert ore["fastest"] == {
        "carrier": MK2.key,
        "name": "Belt2",
        "per_minute": contract.rational(Fraction(1200)),
    }
    assert ore["utilisation"] == contract.rational(Fraction(90, 1200))
    assert ore["percent"] == PERCENT_7_5  # 7.5 exactly: half rounds up; the view only transcribes
    assert ore["saturated"] is False
    (link,) = view["links"]
    assert link["capacity"]["carrier"] == MK1.key
    assert link["utilisation"] == contract.rational(Fraction(45, 1200))
    assert link["percent"] == PERCENT_3_75  # 3.75
    assert link["saturated"] is False


def test_a_saturated_row_with_no_single_carrier_names_none() -> None:
    plan = _chain(ore=Fraction(1201))
    ore = _by_item(_carried_view(plan, FLEET)["edges"])[ORE]
    assert ore["saturated"] is True
    assert ore["capacity"] is None
    assert ore["fastest"]["name"] == "Belt2"  # the share is of this one, whatever fits
    assert ore["utilisation"] == contract.rational(Fraction(1201, 1200))
    assert ore["percent"] == PERCENT_OVER_FULL


def test_a_boundary_item_split_across_consumers_carries_no_single_row() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, ORE, "C1", Fraction(300), "item", None),
        PlanEdge(None, ORE, "C2", Fraction(900), "item", None),
        raw_inputs={ORE: Fraction(1200)},
    )
    view = _carried_view(plan, FLEET)
    (edge,) = view["edges"]
    # The aggregated edge is the sum; the piece that is the bottleneck marks it, and its own
    # figures are not the sum's, so none are shown against it.
    assert edge["marked"] is True
    assert (edge["capacity"], edge["utilisation"], edge["saturated"]) == (None, None, None)
    assert view["marked_edge"]["consumer"] == "C2"
    assert view["marked_edge"]["utilisation"] == contract.rational(Fraction(3, 4))


def test_an_unknown_unit_edge_has_no_row_and_no_mark() -> None:
    plan = _plan_of_edges(
        PlanEdge(None, "Desc_Mystery_C", MAKE_PLATE, Fraction(10**6), "unknown", None),
        PlanEdge(MAKE_PLATE, INGOT, None, Fraction(30), "item", "target"),
        raw_inputs={"Desc_Mystery_C": Fraction(10**6)},
        targets={INGOT: Fraction(30)},
    )
    view = _carried_view(plan, FLEET, forms={INGOT: SOLID})
    assert _every_marked(view) == [("edges", INGOT)]
    mystery = _by_item(view["edges"])["Desc_Mystery_C"]
    assert (mystery["capacity"], mystery["utilisation"], mystery["saturated"]) == (None, None, None)


def test_supplying_capacity_moves_no_width() -> None:
    plan = _chain()
    bare = _carried_view(plan)
    rated = _carried_view(plan, FLEET)
    assert [(e["item"], e["width"]) for e in rated["edges"]] == [
        (e["item"], e["width"]) for e in bare["edges"]
    ]
    assert contract.encode({"flow": rated}).isascii()
    assert [leaf for leaf in _walk(rated) if isinstance(leaf, float)] == []


def test_the_carry_spellings_are_bound_to_their_owners() -> None:
    assert flow_view.CARRY_SUBJECT == plan_rules.IN_CARRY == "plan.carry"
    assert registry_module.TRANSPORT_UNIT_ITEM == flow_view.UNIT_ITEM
    assert registry_module.TRANSPORT_UNIT_CUBIC_METRE == flow_view.UNIT_VOLUME
    assert registry_module.TRANSPORT_KIND_BELT == flow_view.TRANSPORT_BELT
    assert registry_module.TRANSPORT_KIND_PIPE == flow_view.TRANSPORT_PIPE
    assert plan_rules.PLAN_INPUTS[-1] == plan_rules.IN_CARRY


def test_the_endpoint_serves_the_view_of_the_recorded_trace_and_takes_no_transports() -> None:
    registry = solve_synthetic.solve_registry()
    plan = _chain()
    found, card_id = _plan_card_advice(plan, FLEET)
    log: list[str] = []
    response = _derivation(advice_fixtures._Source(found, log=log), log, card_id)  # noqa: SLF001
    assert response.http_status == contract.HTTP_OK
    data = response.payload["data"]
    assert isinstance(data, dict)
    forms = {key: item.form for key, item in registry.items.items()}
    assert data["flow"] == flow_view.view_of(_with_carry(plan, FLEET), forms=forms)
    # THE CONTROL: the served flow carries a mark, so equality is not two Nones.
    assert data["flow"]["marked_edge"] is not None
    assert not hasattr(advice_endpoint._SeenRegistry, "transports")  # noqa: SLF001
    assert log.count("registry") == 1


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


def _with_utilisation(
    edge: dict, num: int, den: int, percent: int, *, carrier: str | None = "Build_Belt1_C"
) -> dict:
    edge["utilisation"] = {"num": num, "den": den}
    edge["percent"] = percent
    edge["saturated"] = num >= den
    edge["capacity"] = (
        None
        if carrier is None
        else {
            "carrier": carrier,
            "name": carrier.removeprefix("Build_").removesuffix("_C"),
            "per_minute": {"num": 120, "den": 1},
        }
    )
    edge["fastest"] = {
        "carrier": "Build_Belt2_C",
        "name": "Belt2",
        "per_minute": {"num": 1200, "den": 1},
    }
    return edge


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


def _panel_flow_lines(tmp_path: object, flow: object) -> list[str]:
    text, hidden = _panel_flow_text(tmp_path, flow)
    assert hidden is False
    return text.split(chr(10))


def _flow(*edges: dict, links: list[dict] | None = None) -> dict:
    return {"rule_id": "x", "nodes": [], "marked_edge": None, "edges": list(edges), "links": links}


def test_the_panel_writes_one_line_per_edge_starred_and_barred_by_utilisation(
    tmp_path: object,
) -> None:
    flow = _flow(
        _with_utilisation(_flow_edge("Desc_Ore_C", "raw-input", 25, 3, marked=True), 9, 10, 90),
        _with_utilisation(_flow_edge("Desc_Half_C", "target", 25, 6, marked=False), 1, 2, 50),
        _with_utilisation(
            _flow_edge("<b>Desc_Tiny_C</b>", "byproduct", 1, 1000, marked=False), 1, 100, 1
        ),
    )
    lines = _panel_flow_lines(tmp_path, flow)
    assert lines == [
        "* Desc_Ore_C raw-input 25/3 item per min on belt "
        + "#" * 18
        + " fits Belt1; 90% of Belt2",
        "  Desc_Half_C target 25/6 item per min on belt " + "#" * 10 + " fits Belt1; 50% of Belt2",
        "  <b>Desc_Tiny_C</b> byproduct 1/1000 item per min on belt # fits Belt1; 1% of Belt2",
    ]


def test_a_utilisation_above_one_is_capped_and_a_row_with_none_has_no_bar(
    tmp_path: object,
) -> None:
    over = _with_utilisation(
        _flow_edge("Desc_Big_C", "target", 5, 1, marked=True), 3, 2, 150, carrier=None
    )
    plain = _flow_edge("Desc_Plain_C", "target", 1, 1, marked=False)
    lines = _panel_flow_lines(tmp_path, _flow(over, plain))
    assert lines[0] == (
        "* Desc_Big_C target 5 item per min on belt "
        + "#" * 20
        + " fits none; 150% of Belt2 saturated"
    )
    assert lines[1] == "  Desc_Plain_C target 1 item per min on belt "


def test_a_whole_rate_renders_bare_and_a_zero_denominator_renders_dash(tmp_path: object) -> None:
    # The unmodified rateText, driven in node: den 1 reads as the bare numerator, den 0
    # (never a rate) as a dash, and an ordinary ratio as num/den.
    flow = _flow(
        _flow_edge("Desc_Whole_C", "target", 3, 1, marked=False),
        _flow_edge("Desc_Zero_C", "target", 3, 0, marked=False),
        _flow_edge("Desc_Ratio_C", "target", 3, 2, marked=False),
    )
    assert _panel_flow_lines(tmp_path, flow) == [
        "  Desc_Whole_C target 3 item per min on belt ",
        "  Desc_Zero_C target - item per min on belt ",
        "  Desc_Ratio_C target 3/2 item per min on belt ",
    ]


def test_the_panel_shows_no_flow_region_when_the_body_carries_none(tmp_path: object) -> None:
    absents: tuple[object, ...] = (None, {"edges": []})
    for absent in absents:
        text, hidden = _panel_flow_text(tmp_path, absent)
        assert (text, hidden) == ("", True)


def test_a_starred_line_names_its_unit_and_a_fluid_is_not_an_item(tmp_path: object) -> None:
    fluid = _flow_edge("Desc_Water_C", "raw-input", 9, 2, marked=True)
    fluid["transport"] = "pipe"
    fluid["unit"] = "m3"
    _with_utilisation(fluid, 3, 4, 75)
    assert _panel_flow_lines(tmp_path, _flow(fluid)) == [
        "* Desc_Water_C raw-input 9/2 m3 per min on pipe " + "#" * 15 + " fits Belt1; 75% of Belt2"
    ]


def test_an_edge_with_no_unit_reads_unknown_on_the_panel(tmp_path: object) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 5, 1, marked=False)
    del edge["unit"]
    assert _panel_flow_lines(tmp_path, _flow(edge)) == [
        "  Desc_Ore_C raw-input 5 unknown per min on belt "
    ]


def test_the_panel_transcribes_the_carrier_and_the_saturated_flag(tmp_path: object) -> None:
    carried = _with_utilisation(
        _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=True), 3, 4, 75, carrier="Build_Belt2_C"
    )
    full = _with_utilisation(
        _flow_edge("Desc_Big_C", "target", 500, 1, marked=False), 5, 4, 125, carrier=None
    )
    unknown = _flow_edge("Desc_Odd_C", "target", 1, 1, marked=False)
    lines = _panel_flow_lines(tmp_path, _flow(carried, full, unknown))
    assert lines[0].startswith("* Desc_Ore_C raw-input 90 item per min on belt ")
    assert lines[0].endswith(" fits Belt2; 75% of Belt2")
    assert "saturated" not in lines[0]
    assert lines[1].endswith(" fits none; 125% of Belt2 saturated")
    assert lines[2] == "  Desc_Odd_C target 1 item per min on belt "


def _link(
    *,
    marked: bool,
    percent: int = 75,
    num: int = 3,
    den: int = 4,
    carrier: str | None = "Build_Belt1_C",
) -> dict:
    link = {
        "producer": "Recipe_Plate_C",
        "consumer": "Recipe_Ingot_C",
        "item": "Desc_Plate_C",
        "transport": "belt",
        "unit": "item",
        "width": {"num": 45, "den": 1},
        "marked": marked,
    }
    return _with_utilisation(link, num, den, percent, carrier=carrier)


CHAIN_LABEL_ID: Final = "advice-flow-chain-label-{}"
CHAIN_ID: Final = "advice-flow-links-{}"


def _panel_report(tmp_path: object, flow: object) -> Mapping[str, Any]:
    held = panel.card("Held", "held reason")
    body = {"id": held["id"], "rule_id": held["rule_id"], "derivation": "text", "flow": flow}
    return panel.drive(
        tmp_path,  # type: ignore[arg-type]
        panel.payload(held),
        steps=[
            {"click": panel.read_id(0)},
            {"settle": {"call": 0, "outcome": panel.answered(body)}},
        ],
    )


def test_a_chain_link_line_shows_its_utilisation_bar_and_percent(tmp_path: object) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=False)
    report = _panel_report(tmp_path, _flow(edge, links=[_link(marked=True)]))
    links = panel.row_of(report["nodes"], CHAIN_ID.format(0))
    assert links["tag"] == "PRE"
    assert links["hidden"] is False
    assert links["text"] == (
        "* Recipe_Plate_C -> Recipe_Ingot_C Desc_Plate_C 45 item per min on belt "
        + "#" * 15
        + " fits Belt1; 75% of Belt2"
    )


def test_a_link_over_one_hundred_percent_prints_the_number_whatever_its_bar(
    tmp_path: object,
) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=False)
    over = _link(marked=False, percent=150, num=3, den=2, carrier=None)
    report = _panel_report(tmp_path, _flow(edge, links=[over]))
    text = panel.row_of(report["nodes"], CHAIN_ID.format(0))["text"]
    assert "#" * 20 + " fits none; 150% of Belt2" in text
    assert "#" * 21 not in text


def test_the_chain_heading_is_its_own_element_over_its_own_block(tmp_path: object) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=False)
    report = _panel_report(tmp_path, _flow(edge, links=[_link(marked=False)]))
    heading = panel.row_of(report["nodes"], CHAIN_LABEL_ID.format(0))
    links = panel.row_of(report["nodes"], CHAIN_ID.format(0))
    boundary = panel.row_of(report["nodes"], "advice-flow-0")
    assert heading["hidden"] is False
    assert heading["text"] == "chain, allocated not routed"
    assert links["attributes"].get("aria-labelledby") == heading["id"], links["attributes"]
    assert links["attributes"].get("role") == "group"
    assert heading["parent"] == links["parent"] == boundary["parent"]
    assert boundary["index"] < heading["index"] < links["index"]
    # The heading is not a line inside either block.
    assert "chain" not in str(boundary["text"])
    assert "chain" not in str(links["text"])


def test_the_chain_heading_and_block_are_hidden_when_there_is_no_link(tmp_path: object) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=False)
    no_links: tuple[list[dict] | None, ...] = (None, [])
    for links in no_links:
        report = _panel_report(tmp_path, _flow(edge, links=links))
        # THE CONTROL: the boundary block itself is shown.
        assert panel.row_of(report["nodes"], "advice-flow-0")["hidden"] is False
        for stem in (CHAIN_LABEL_ID, CHAIN_ID):
            assert panel.row_of(report["nodes"], stem.format(0))["hidden"] is True, stem


def test_a_star_on_a_link_line_is_keyed_by_the_legend(tmp_path: object) -> None:
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=False)
    report = _panel_report(tmp_path, _flow(edge, links=[_link(marked=True)]))
    legend = panel.row_of(report["nodes"], "advice-flow-legend-0")
    assert legend["hidden"] is False
    assert str(legend["text"]).startswith("* marks the bottleneck")


def test_the_panel_has_no_highest_rate_wording_left() -> None:
    text = (REPO_ROOT / "clockspeed/surface/web/panel_advice.js").read_text(encoding="utf-8")
    assert "highest rate" not in text.lower()
    assert "highest-rate" not in text.lower()


def test_every_line_names_the_fastest_carrier_beside_its_percent(tmp_path: object) -> None:
    """A fitting carrier beside a percent of another would read as that carrier's share."""
    edge = _with_utilisation(
        _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=True), 3, 40, 8, carrier="Build_Belt1_C"
    )
    report = _panel_report(tmp_path, _flow(edge, links=[_link(marked=False)]))
    boundary = panel.row_of(report["nodes"], "advice-flow-0")["text"]
    chain = panel.row_of(report["nodes"], CHAIN_ID.format(0))["text"]
    assert "fits Belt1; 8% of Belt2" in boundary
    assert "fits Belt1; 75% of Belt2" in chain
    for text in (boundary, chain):
        assert "carrier " not in text


def test_an_unmarked_chain_line_has_no_leading_indent_and_a_marked_one_has_the_star(
    tmp_path: object,
) -> None:
    """A two-space lead wraps to a blank-looking first line at narrow widths."""
    edge = _flow_edge("Desc_Ore_C", "raw-input", 90, 1, marked=False)
    report = _panel_report(tmp_path, _flow(edge, links=[_link(marked=False), _link(marked=True)]))
    first, second = panel.row_of(report["nodes"], CHAIN_ID.format(0))["text"].split(chr(10))
    assert first.startswith("Recipe_Plate_C ->"), first
    assert second.startswith("* Recipe_Plate_C ->"), second
