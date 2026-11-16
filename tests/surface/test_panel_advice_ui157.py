"""CS-1400 - the panel half of the UI-157 audit's five majors: S1, S2 (the label), H2 and Y1.

The UI-157 browser audit of the dashboard advice panel read five majors. This file grades
the four whose fix lives in ``clockspeed/surface/web/panel_advice.js``; the stylesheet half
(H1, and S2's bounded width) is graded in ``test_panel_advice_layout.py``.

Each arm runs the SHIPPED module under the advice bench's own node driver, imported from
``tests/surface/test_panel_advice.py`` as ``tests/surface/test_flow_view.py`` imports it.
That driver is deliberately not a browser, so nothing here claims anything about pixels:
the arms read the node tree the panel builds, which is what a browser would lay out, and
the one focus fact they read (``document.activeElement``) is the fact the driver models.

EVERY ARM CARRIES ITS OWN CONTROL, because a panel that built nothing and a panel that built
the right thing both fail an arm that never checked its subject existed. The control is
named where it stands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract
from tests.surface import test_panel_advice as panel

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

#: The words a saturation or capacity claim would need. The legend names the star by what
#: it measures, the highest rate, and no layer in this tree publishes a limit.
CAPACITY_WORDS: Final = ("capacity", "limit", "saturat", "full", "maximum", "max ")

#: The ids this slice publishes, built as the panel builds every card's.
FLOW_ID: Final = "advice-flow-{}"
FLOW_LABEL_ID: Final = "advice-flow-label-{}"
FLOW_LEGEND_ID: Final = "advice-flow-legend-{}"
SNOOZE_LABEL_ID: Final = "advice-snooze-label-{}"
SNOOZE_GROUP_CLASS: Final = "advice-snooze"


def _edge(item: str, num: int, den: int, *, marked: bool) -> dict[str, Any]:
    """One served flow edge, keyed as the flow view keys it."""
    return {
        "item": item,
        "role": "raw-input",
        "direction": "in",
        "transport": "belt",
        "width": {"num": num, "den": den},
        "marked": marked,
    }


def _flow(*edges: Mapping[str, Any]) -> dict[str, Any]:
    """One served flow object."""
    return {"rule_id": "x", "nodes": [], "marked_edge": None, "edges": list(edges)}


def _flow_read_steps(flow: object, *, position: int = 0) -> list[dict[str, Any]]:
    """The steps that press Read derivation on the held card and let a body with this flow land."""
    held = panel.card("Held", "held reason")
    body = {"id": held["id"], "rule_id": held["rule_id"], "derivation": "text", "flow": flow}
    return [
        {"click": panel.read_id(position)},
        {"settle": {"call": 0, "outcome": panel.answered(body)}},
    ]


def _held_flow_report(tmp_path: Path, flow: object) -> Mapping[str, Any]:
    """A held card whose derivation read answered with this flow."""
    held = panel.card("Held", "held reason")
    return panel.drive(tmp_path, panel.payload(held), steps=_flow_read_steps(flow))


def _row(report: Mapping[str, Any], node_id: str) -> Mapping[str, Any]:
    return panel.row_of(report["nodes"], node_id)


# ---------------------------------------------------------------------------
# S1 - the flow block carries a visible label and a legend for its star
# ---------------------------------------------------------------------------


def test_s1_a_shown_flow_carries_its_own_label_and_a_legend_for_the_star(tmp_path: Path) -> None:
    """The audit read a bare ``*`` under the derivation: no heading, no key to the mark."""
    flow = _flow(_edge("Desc_Ore_C", 25, 3, marked=True), _edge("Desc_Half_C", 25, 6, marked=False))
    report = _held_flow_report(tmp_path, flow)
    pre = _row(report, FLOW_ID.format(0))
    # THE CONTROL: the flow itself is shown, so the label and legend are graded beside a real one.
    assert pre["tag"] == "PRE"
    assert pre["hidden"] is False
    assert str(pre["text"]).startswith("* Desc_Ore_C"), pre["text"]

    label = _row(report, FLOW_LABEL_ID.format(0))
    legend = _row(report, FLOW_LEGEND_ID.format(0))
    assert label["hidden"] is False
    assert legend["hidden"] is False
    assert str(label["text"]).strip() != ""
    assert pre["attributes"].get("aria-labelledby") == label["id"], pre["attributes"]
    # Same card, in reading order: the label leads the flow and the legend follows it.
    assert label["parent"] == pre["parent"] == legend["parent"]
    assert label["index"] < pre["index"] < legend["index"]

    key = str(legend["text"]).lower()
    assert "*" in str(legend["text"])
    assert "highest rate" in key, key
    leaked = tuple(word for word in CAPACITY_WORDS if word in key)
    assert leaked == (), leaked


def test_s1_the_flow_block_has_a_role_that_accepts_the_name_the_label_gives_it(
    tmp_path: Path,
) -> None:
    """A role-less ``pre`` ignores ``aria-labelledby``: the re-audit read the flow unnamed."""
    report = _held_flow_report(tmp_path, _flow(_edge("Desc_Ore_C", 25, 3, marked=True)))
    pre = _row(report, FLOW_ID.format(0))
    # THE CONTROL: the block is shown and still carries the name's source.
    assert pre["hidden"] is False
    assert pre["attributes"].get("aria-labelledby") == FLOW_LABEL_ID.format(0)
    assert pre["attributes"].get("role") == "group", pre["attributes"]


def test_s1_the_label_and_legend_sit_under_the_derivation_not_above_it(tmp_path: Path) -> None:
    report = _held_flow_report(tmp_path, _flow(_edge("Desc_Ore_C", 1, 1, marked=True)))
    derivation = _row(report, panel.derivation_id(0))
    label = _row(report, FLOW_LABEL_ID.format(0))
    assert derivation["index"] < label["index"]


def test_s1_the_label_and_legend_are_hidden_until_a_flow_is_shown(tmp_path: Path) -> None:
    held = panel.card("Held", "held reason")
    report = panel.drive(tmp_path, panel.payload(held))
    for stem in (FLOW_LABEL_ID, FLOW_LEGEND_ID):
        row = _row(report, stem.format(0))
        assert row["hidden"] is True, row["id"]


@pytest.mark.parametrize("absent", [None, {"edges": []}], ids=["null", "no-edge"])
def test_s1_a_body_with_no_flow_hides_the_label_and_the_legend_with_the_block(
    absent: object, tmp_path: Path
) -> None:
    report = _held_flow_report(tmp_path, absent)
    # THE CONTROL: the derivation is shown, so the body landed and the flow's absence is its own.
    assert _row(report, panel.derivation_id(0))["hidden"] is False
    assert _row(report, FLOW_ID.format(0))["hidden"] is True
    for stem in (FLOW_LABEL_ID, FLOW_LEGEND_ID):
        assert _row(report, stem.format(0))["hidden"] is True, stem


def test_s1_a_flow_with_no_starred_edge_shows_its_label_and_no_legend_for_a_star(
    tmp_path: Path,
) -> None:
    """A key to a mark nothing carries would describe an absence."""
    flow = _flow(_edge("Desc_Ore_C", 25, 3, marked=False))
    report = _held_flow_report(tmp_path, flow)
    pre = _row(report, FLOW_ID.format(0))
    assert pre["hidden"] is False
    assert "*" not in str(pre["text"])
    assert _row(report, FLOW_LABEL_ID.format(0))["hidden"] is False
    assert _row(report, FLOW_LEGEND_ID.format(0))["hidden"] is True


def test_s1_a_refused_re_read_hides_the_label_and_the_legend_with_the_block(
    tmp_path: Path,
) -> None:
    held = panel.card("Held", "held reason")
    shown = _flow_read_steps(_flow(_edge("Desc_Ore_C", 25, 3, marked=True)))
    refusal = panel.delivered(
        contract.bad_request(advice_endpoint.DERIVATION_ENDPOINT, contract.REASON_INVALID_PARAMETER)
    )
    report = panel.drive(
        tmp_path,
        panel.payload(held),
        steps=[*shown, {"click": panel.read_id(0)}, {"settle": {"call": 1, "outcome": refusal}}],
    )
    # THE CONTROL: the step before the refusal showed all three.
    before = report["steps"][-3]["nodes"]
    for stem in (FLOW_ID, FLOW_LABEL_ID, FLOW_LEGEND_ID):
        assert panel.row_of(before, stem.format(0))["hidden"] is False, stem
    for stem in (FLOW_ID, FLOW_LABEL_ID, FLOW_LEGEND_ID):
        assert _row(report, stem.format(0))["hidden"] is True, stem


# ---------------------------------------------------------------------------
# S2 - the snooze select has a visible bound label and sits beside its button
# ---------------------------------------------------------------------------


def _children(rows: Sequence[Mapping[str, Any]], parent: int) -> list[Mapping[str, Any]]:
    return [row for row in rows if row["parent"] == parent]


def test_s2_the_snooze_select_has_a_visible_label_bound_to_it_beside_its_button(
    tmp_path: Path,
) -> None:
    """The audit read an unlabelled, page-wide select that fell onto its own row."""
    answer_card = card_of("Answer shown")
    report = panel.drive(tmp_path, panel.payload(), steps=panel.stated_steps(answer_card))
    select = _row(report, panel.control_id(panel.SNOOZE_FOR_STEM, 0))
    button = _row(report, panel.control_id(panel.SNOOZE_STEM, 0))
    label = _row(report, SNOOZE_LABEL_ID.format(0))
    # THE CONTROL: the select and the button are the real ones, so the label is graded against them.
    assert select["tag"] == "SELECT"
    assert button["tag"] == "BUTTON"

    assert label["tag"] == "LABEL"
    assert label["hidden"] is False
    assert str(label["text"]).strip() != ""
    assert label["attributes"].get("for") == select["id"], label["attributes"]

    group = next(row for row in report["nodes"] if row["index"] == select["parent"])
    assert SNOOZE_GROUP_CLASS in str(group["class"]).split(), group["class"]
    order = [child["id"] for child in _children(report["nodes"], group["index"])]
    assert order == [label["id"], select["id"], button["id"]], order


def test_s2_the_other_three_controls_stand_outside_the_snooze_group(tmp_path: Path) -> None:
    report = panel.drive(
        tmp_path, panel.payload(), steps=panel.stated_steps(card_of("Answer shown"))
    )
    select = _row(report, panel.control_id(panel.SNOOZE_FOR_STEM, 0))
    for stem in panel.PLAIN_CONTROLS:
        plain = _row(report, panel.control_id(stem, 0))
        assert plain["parent"] != select["parent"], stem
        # They share the controls row, which is the group's parent.
        group = next(row for row in report["nodes"] if row["index"] == select["parent"])
        assert plain["parent"] == group["parent"], stem


def test_s2_each_card_binds_its_own_label_to_its_own_select(tmp_path: Path) -> None:
    first, second = card_of("First"), card_of("Second")
    report = panel.drive(tmp_path, panel.payload(), steps=panel.stated_steps(first, second))
    for index in (0, 1):
        label = _row(report, SNOOZE_LABEL_ID.format(index))
        assert label["attributes"].get("for") == panel.control_id(panel.SNOOZE_FOR_STEM, index)


def test_s2_the_snooze_press_still_posts_the_picked_token(tmp_path: Path) -> None:
    """Regrouping the controls moved no behaviour: the same id still carries the same door call."""
    answer_card = card_of("Answer shown")
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=[
            *panel.stated_steps(answer_card),
            {
                "fill": {
                    "id": panel.control_id(panel.SNOOZE_FOR_STEM, 0),
                    "value": panel.PICKED_TOKEN,
                }
            },
            {"click": panel.control_id(panel.SNOOZE_STEM, 0)},
        ],
    )
    calls = panel.door_calls(report, "state")
    count = len(calls)
    assert count == 1, calls
    assert calls[0]["params"][advice_endpoint.DURATION_PARAMETER] == panel.PICKED_TOKEN


def card_of(headline: str) -> dict[str, Any]:
    """One visible card with a reason of its own."""
    return panel.card(headline, f"{headline} reason")


# ---------------------------------------------------------------------------
# H2 - a successful state press keeps focus and keeps the read derivation
# ---------------------------------------------------------------------------

#: The stated path's call numbers: act 0, then derivation 1 (when read), state, re-read.
READ_CALL: Final = 1


def _press_steps(
    cards: Sequence[Mapping[str, Any]],
    *,
    stem: str,
    pressed: int,
    kind: str,
    reread: Mapping[str, Any],
    read_first: int | None = 0,
) -> list[dict[str, Any]]:
    """State the request, read one derivation with a flow, focus and press, settle both calls."""
    steps = panel.stated_steps(*cards)
    state_call = READ_CALL
    if read_first is not None:
        state_call += 1
        held = cards[read_first]
        body = {
            "id": held["id"],
            "rule_id": held["rule_id"],
            "derivation": "the derivation text",
            "flow": _flow(_edge("Desc_Ore_C", 25, 3, marked=True)),
        }
        steps += [
            {"click": panel.read_id(read_first)},
            {"settle": {"call": READ_CALL, "outcome": panel.answered(body)}},
        ]
    control = panel.control_id(stem, pressed)
    steps += [
        {"focus": control},
        {"click": control},
        {"settle": {"call": state_call, "outcome": panel.recorded(kind)}},
        {"settle": {"call": state_call + 1, "outcome": panel.answered(reread)}},
    ]
    return steps


@pytest.mark.parametrize(
    ("stem", "kind"),
    [("accept", "accepted"), ("pin", "pinned"), ("dismiss", "dismissed")],
)
def test_h2_a_successful_state_press_keeps_focus_and_the_read_derivation(
    stem: str, kind: str, tmp_path: Path
) -> None:
    """The audit read focus dropped to Ask and the derivation and flow hidden after Accept."""
    answer_card = card_of("Answer shown")
    reread = panel.listing({**answer_card, "state": kind}, plan_outcome={"status": "ranked"})
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps([answer_card], stem=stem, pressed=0, kind=kind, reread=reread),
    )
    control = panel.control_id(stem, 0)
    # THE CONTROL: focus really was on the pressed control until the re-read landed.
    assert report["steps"][-2]["active"] == control
    assert report["steps"][-1]["active"] == control

    derivation = _row(report, panel.derivation_id(0))
    flow = _row(report, FLOW_ID.format(0))
    assert derivation["hidden"] is False
    assert derivation["text"] == "the derivation text"
    assert flow["hidden"] is False
    assert str(flow["text"]).startswith("* Desc_Ore_C"), flow["text"]
    assert _row(report, FLOW_LABEL_ID.format(0))["hidden"] is False
    assert _row(report, FLOW_LEGEND_ID.format(0))["hidden"] is False
    assert f"state: {kind}" in panel.text_of(report, panel.ANSWER_ID)


def test_h2_the_answering_note_and_the_plan_outcome_stand_through_the_re_read(
    tmp_path: Path,
) -> None:
    answer_card = card_of("Answer shown")
    reread = panel.listing({**answer_card, "state": "accepted"}, plan_outcome={"status": "ranked"})
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps([answer_card], stem="accept", pressed=0, kind="accepted", reread=reread),
    )
    text = panel.text_of(report, panel.ANSWER_ID)
    assert "answering:" in text, text
    assert "plan status: ranked" in text, text
    # One re-read, and the door was asked nothing else.
    asked = panel.door_calls(report, "advice")
    count = len(asked)
    assert count == 1, asked


def test_h2_the_state_line_stops_saying_the_listing_is_being_read(tmp_path: Path) -> None:
    """The line the press wrote was true while the re-read ran, and is stale once it lands."""
    answer_card = card_of("Answer shown")
    reread = panel.listing({**answer_card, "state": "accepted"}, plan_outcome={"status": "ranked"})
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps([answer_card], stem="accept", pressed=0, kind="accepted", reread=reread),
    )
    line = panel.text_of(report, panel.state_status_id(0))
    assert "reading the listing again" not in line, line
    assert "recorded" in line, line


def test_h2_a_pressed_card_the_reread_hides_leaves_and_focus_lands_on_ask(
    tmp_path: Path,
) -> None:
    kept, dropped = card_of("Kept card"), card_of("Dropped card")
    reread = panel.listing(
        {**kept, "state": "new"},
        {**dropped, "state": "dismissed", "visible": False},
        plan_outcome={"status": "ranked"},
    )
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps(
            [kept, dropped],
            stem="dismiss",
            pressed=1,
            kind="dismissed",
            reread=reread,
            read_first=None,
        ),
    )
    # THE CONTROL: focus was on the card that then left.
    assert report["steps"][-2]["active"] == panel.control_id("dismiss", 1)
    assert report["steps"][-1]["active"] == panel.ASK_ID
    text = panel.text_of(report, panel.ANSWER_ID)
    assert "Kept card" in text, text
    assert "Dropped card" not in text, text


def test_h2_a_card_the_reread_hides_leaves_and_the_card_beside_it_keeps_its_derivation(
    tmp_path: Path,
) -> None:
    kept, dropped = card_of("Kept card"), card_of("Dropped card")
    reread = panel.listing(
        {**kept, "state": "new"},
        {**dropped, "state": "dismissed", "visible": False},
        plan_outcome={"status": "ranked"},
    )
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps(
            [kept, dropped], stem="dismiss", pressed=1, kind="dismissed", reread=reread
        ),
    )
    assert "Dropped card" not in panel.text_of(report, panel.ANSWER_ID)
    derivation = _row(report, panel.derivation_id(0))
    assert derivation["hidden"] is False
    assert derivation["text"] == "the derivation text"
    ids = {row["id"] for row in report["nodes"]}
    assert panel.read_id(1) not in ids, "the dropped card's own nodes stayed on the page"


def test_h2_a_reread_that_adds_a_card_falls_back_to_a_whole_answer(tmp_path: Path) -> None:
    """Labelled regression fence: an id the page does not hold cannot be reconciled in place."""
    first, fresh = card_of("First"), card_of("Fresh")
    reread = panel.listing({**first, "state": "accepted"}, fresh, plan_outcome={"status": "ranked"})
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps([first], stem="accept", pressed=0, kind="accepted", reread=reread),
    )
    text = panel.text_of(report, panel.ANSWER_ID)
    assert "Fresh" in text, text
    assert report["steps"][-1]["active"] == panel.ASK_ID
    # Whole answer: the earlier reading is gone with the cards that carried it.
    assert _row(report, panel.derivation_id(0))["hidden"] is True


def test_h2_a_reread_that_reorders_cards_falls_back_to_a_whole_answer(tmp_path: Path) -> None:
    first, second = card_of("First"), card_of("Second")
    reread = panel.listing(
        {**second, "state": "new"},
        {**first, "state": "accepted"},
        plan_outcome={"status": "ranked"},
    )
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps(
            [first, second], stem="accept", pressed=0, kind="accepted", reread=reread
        ),
    )
    text = panel.text_of(report, panel.ANSWER_ID)
    assert text.index("Second") < text.index("First"), text
    assert _row(report, panel.derivation_id(0))["hidden"] is True


def test_h2_a_reread_that_hides_every_card_falls_back_and_says_none_is_visible(
    tmp_path: Path,
) -> None:
    only = card_of("Only card")
    reread = panel.listing(
        {**only, "state": "dismissed", "visible": False}, plan_outcome={"status": "ranked"}
    )
    report = panel.drive(
        tmp_path,
        panel.payload(),
        steps=_press_steps([only], stem="dismiss", pressed=0, kind="dismissed", reread=reread),
    )
    text = panel.text_of(report, panel.ANSWER_ID)
    assert "Only card" not in text, text
    assert NO_CARD_STATED in text, text


def test_h2_a_refused_reread_is_drawn_whole_as_it_was(tmp_path: Path) -> None:
    answer_card = card_of("Answer shown")
    refusal = panel.delivered(
        contract.bad_request(advice_endpoint.ENDPOINT, contract.REASON_INVALID_PARAMETER)
    )
    steps = _press_steps(
        [answer_card],
        stem="accept",
        pressed=0,
        kind="accepted",
        reread=panel.listing(),
    )
    steps[-1] = {"settle": {"call": READ_CALL + 2, "outcome": refusal}}
    report = panel.drive(tmp_path, panel.payload(), steps=steps)
    text = panel.text_of(report, panel.ANSWER_ID)
    assert "Answer shown" not in text, text
    assert report["steps"][-1]["active"] == panel.ASK_ID


# ---------------------------------------------------------------------------
# Y1 - the inert both-chosen line clears an earlier answer or refusal
# ---------------------------------------------------------------------------

BOTH_LINE_WORDS: Final = "not both"

#: The line the panel writes under a stated answer that lists no visible card.
NO_CARD_STATED: Final = "no visible card answered this request."


def _both_steps(first_outcome: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Press an item statement, let it settle, then choose a schematic beside it and press."""
    return [
        *panel.schematic_fills({**panel.STATED}),
        panel.press_ask(),
        {"settle": {"call": 0, "outcome": first_outcome}},
        *panel.schematic_fills({panel.SCHEMATIC_NAME: "Schematic_Alpha_C"}),
        panel.press_ask(),
    ]


def test_y1_both_chosen_after_an_answer_leaves_no_answer_standing(tmp_path: Path) -> None:
    """The audit read 'nothing was sent' beside the answer it was not about."""
    held = card_of("Held card")
    answer = panel.answered(
        panel.listing(card_of("Answer shown"), plan_outcome={"status": "ranked"})
    )
    report = panel.drive(tmp_path, panel.schematic_payload(held), steps=_both_steps(answer))
    # THE CONTROL: the first press reached the door once and the answer landed under it.
    acted = panel.door_calls(report, "act")
    count = len(acted)
    assert count == 1, report["door_calls"]
    assert "Answer shown" in panel.text_of({"nodes": report["steps"][-3]["nodes"]}, panel.ANSWER_ID)

    # THE CLAUSE: the second press is inert, says so, and no answer stands beside the line.
    assert BOTH_LINE_WORDS in panel.text_of(report, panel.STATUS_ID)
    text = panel.text_of(report, panel.ANSWER_ID)
    assert "Answer shown" not in text, text
    assert "answering:" not in text, text
    assert "plan status" not in text, text
    # Restored to the mount listing, with no door call.
    assert "Held card" in text, text
    assert len(report["door_calls"]) == 1, report["door_calls"]


def test_y1_both_chosen_after_a_refusal_leaves_no_refusal_standing(tmp_path: Path) -> None:
    refusal_response = contract.bad_request(
        advice_endpoint.ENDPOINT, contract.REASON_INVALID_PARAMETER
    )
    detail = str(refusal_response.payload["detail"])
    report = panel.drive(
        tmp_path,
        panel.schematic_payload(card_of("Held card")),
        steps=_both_steps(panel.delivered(refusal_response)),
    )
    count = len(report["door_calls"])
    assert count == 1, report["door_calls"]
    # THE CONTROL: the refusal really was standing before the second press.
    assert detail in panel.text_of({"nodes": report["steps"][-3]["nodes"]}, panel.ANSWER_ID)

    assert BOTH_LINE_WORDS in panel.text_of(report, panel.STATUS_ID)
    text = panel.text_of(report, panel.ANSWER_ID)
    assert detail not in text, text
    assert "Held card" in text, text


def test_y1_both_chosen_with_nothing_earlier_changes_nothing_in_the_region(
    tmp_path: Path,
) -> None:
    """Idempotent: a press that finds only the mount listing leaves it exactly as it was."""
    held = card_of("Held card")
    fills = [
        *panel.schematic_fills({**panel.STATED}),
        *panel.schematic_fills({panel.SCHEMATIC_NAME: "Schematic_Alpha_C"}),
    ]
    report = panel.drive(
        tmp_path,
        panel.schematic_payload(held),
        steps=[*fills, panel.press_ask()],
    )
    assert report["door_calls"] == []
    assert BOTH_LINE_WORDS in panel.text_of(report, panel.STATUS_ID)
    before = report["steps"][-2]["nodes"]
    after = report["nodes"]
    shown = {row["id"]: row["hidden"] for row in after if row["id"].startswith("advice-")}
    held_before = {row["id"]: row["hidden"] for row in before if row["id"].startswith("advice-")}
    assert shown == held_before


def test_y1_a_derivation_read_on_the_mount_listing_survives_an_inert_press(
    tmp_path: Path,
) -> None:
    """Nothing request-produced stands, so nothing is cleared: the reading is the reader's own."""
    held = panel.card("Held", "held reason")
    body = {
        "id": held["id"],
        "rule_id": held["rule_id"],
        "derivation": "text",
        "flow": None,
    }
    report = panel.drive(
        tmp_path,
        panel.schematic_payload(held),
        steps=[
            {"click": panel.read_id(0)},
            {"settle": {"call": 0, "outcome": panel.answered(body)}},
            *panel.schematic_fills({**panel.STATED}),
            *panel.schematic_fills({panel.SCHEMATIC_NAME: "Schematic_Alpha_C"}),
            panel.press_ask(),
        ],
    )
    assert _row(report, panel.derivation_id(0))["hidden"] is False
