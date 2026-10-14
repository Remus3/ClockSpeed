"""CS-977 slice D - the Map panel: the world as geometry, and what geometry cannot say.

WHAT THE OPERATOR ASKED FOR. "I would like to be in-game and understand what
resources I have, interactive map tab perhaps for the world, and the throughput
of the resources." Three questions, and the honest answers have three different
shapes.

WHERE IS IT - EXACT AND FREE. ``ObjectRecord`` carries a ``Transform`` and a
node carries one too, so every placement on this map is the number the save
holds. The payload ships each coordinate as a DECIMAL STRING, so the panel is
handed the shortest round-trip spelling of the stored float and never an IEEE
double that JSON re-parsed. This module's
:func:`test_no_coordinate_reaches_the_page_in_a_spelling_the_payload_did_not_carry`
is what keeps the panel from improving on that: a coordinate it prints must be
a substring of the coordinate it was given, so there is no rounding to disclose.

WHAT IS IT - NOT IN THE FILE AT ALL. ``docs/adr/0003-s4-node-actors-in-save.md``
measured ``mPurity``, ``mResourceNodeType`` and ``mResourceClass`` at zero
occurrences across three worlds and four builds: a save stores deltas from level
defaults and a node's type never changes from the level asset. So this map
cannot say "iron", and a map that let a reader infer it would be worse than one
that says nothing. The panel says it, and
:func:`test_the_panel_refuses_to_label_a_node_by_resource` grades that it does.

HOW FAST - ONE DERIVED RATE AND ONE DECLARED ASSUMPTION, RENDERED AS TWO
DIFFERENT KINDS OF STATEMENT. Extraction rate depends on node purity, and purity
is the field that is not there. This file's first draft graded three equal
figures per row; the endpoint measured that only ONE of them is derivable - the
normal-purity rate, exact from the shipped items-per-cycle and cycle time - and
that no purity multiplier exists in the shipped docs or in a save at all. So the
wire carries ``per_minute_normal`` plus a ``purity_scaling`` it marks
``purity_scaling_measured`` false, and the panel is required to say which half
is measured. Printing an assumption in the same voice as a derivation is the
fault these arms grade. An empty ``throughput`` is the other half of the same
rule: printing an empty box would read as "you have no extractors", which is a
confident wrong answer of exactly the kind non-negotiable 7 forbids in the data
path. The warning is what the panel prints instead.

WHY THE BUTTONS ARE THE GRADED PATH AND NOT A FALLBACK
======================================================

``memory`` records, measured in this project: a browser automation pane silently
fakes wheel, resize, focus and default key scrolling - three false findings in
one session came out of trusting it. A panel whose only zoom was a wheel handler
would therefore be a panel no instrument here can verify, and a panel a keyboard
reader cannot use. So every capability is reachable from a real ``<button>``,
the harness drives those buttons, and the wheel and drag handlers are the extra
affordance rather than the mechanism.

AND THE ONE MECHANISM THE STAND-IN CAN EXPRESS IS ``setAttribute`` ON THE
``viewBox``. ``tests/surface/panel_harness.py`` documents a deliberately narrow
DOM: no ``classList``, no ``dataset``, no ``children``, no ``focus()``. Pan and
zoom are therefore a viewBox rewrite, which is both the simplest correct SVG
answer and the only one this suite could grade at all.

THE ONE THING THIS MODULE CANNOT SAY
====================================

No browser runs here. The arms below read the tree a panel built against a
stand-in, so they grade structure, text and attribute values. Whether the SVG
paints, whether the legend swatch is distinguishable, and whether a 44px button
is 44px after the cascade are measurements for ``tests/surface/audit_harness.py``
under a real Chromium, which is a different control and is named as one.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.save.world import NODE_CLASS_NAMES
from clockspeed.surface.api import map as map_endpoint
from tests.advisor.build_fixtures import OFF_PIN_OFFSETS, game_pin
from tests.surface import panel_harness
from tests.surface.audit_harness import _assert_build_state_matches, _assert_rows_match

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: The module under grade.
MODULE: Final = "panel_map.js"

#: The seam module. Read when an arm pins what ``app.js`` must hand this panel.
SEAM: Final = "app.js"

#: The route the panel is fed from, and the payload key the seam publishes it
#: under. The key is the domain word out of the path, which is the rule
#: ``panelData`` states for every other key it carries.
MAP_ENDPOINT: Final = "/api/map"
MAP_KEY: Final = "map"

#: The element ids the panel puts on the regions an arm needs to find.
SVG_ID: Final = "map-svg"
LEGEND_ID: Final = "map-legend"
#: The one list that is both the legend and the map-as-text. IT WAS TWO IDS
#: until a browser pass showed the same eleven lines rendered twice, each
#: list green on its own arm. One id now, and an arm below grades that there
#: is no second copy.
ALT_ID: Final = "map-legend"
INVENTORY_ID: Final = "map-inventory"
THROUGHPUT_ID: Final = "map-throughput"
NOTE_ID: Final = "map-note"
#: CS-1316. The note that says which build the rates belong to, or that the
#: registry is unverified. Absent when there is nothing to say: on the pin, over
#: a verified registry.
BUILD_ID: Final = "map-build"

#: CS-1316. The marking a rate row carries when the save is off the pin and the
#: registry is the pinned build's. Matched lower-cased, so the arm grades the
#: claim rather than its capitalisation.
PINNED_MARK: Final = "pinned build's rate"

#: CS-1316. The audit codes the build source serves, spelled here for the
#: reason :data:`MAX_ASCII_BYTE` gives: a test that imports what it asserts
#: grades nothing.
SOURCE_BUILD: Final = "build"
BUILD_MISMATCH: Final = "build-mismatch"
BUILD_UNCOMPARED: Final = "build-uncompared"

#: CS-1316. The off-pin arm serves one rated row and one unrated row.
TWO_RATE_ROWS: Final = 2

#: CS-1316. The registry states the marking must never reach: the name, the
#: served ``registry_verified`` and the registry code served beside it.
UNVERIFIED_STATES: Final = (
    ("no-byte-source", False, "registry-unverified"),
    ("other-docs-bytes", False, "registry-mismatch"),
    ("no-registry", None, None),
)

#: The class the panel puts on a plotted resource node and on a plotted built
#: actor. Two shapes as well as two colours, because colour alone is not a
#: distinction for every reader.
NODE_CLASS: Final = "map-node"
BUILT_CLASS: Final = "map-built"

#: The seven controls, by the label each carries. THE LABELS ARE THE HANDLE the
#: harness clicks by, so they are spelled here rather than read off the panel -
#: an arm that took the label from the thing it grades would assert nothing.
ZOOM_IN: Final = "Zoom in"
ZOOM_OUT: Final = "Zoom out"
RESET: Final = "Reset view"
PAN_LEFT: Final = "Pan west"
PAN_RIGHT: Final = "Pan east"
PAN_UP: Final = "Pan north"
PAN_DOWN: Final = "Pan south"

#: Every control label, in the order the panel builds them.
CONTROL_LABELS: Final = (
    ZOOM_IN,
    ZOOM_OUT,
    RESET,
    PAN_LEFT,
    PAN_RIGHT,
    PAN_UP,
    PAN_DOWN,
)

#: The pointer and wheel affordances the SVG carries in a real browser, on top
#: of the buttons. Graded as PRESENCE only: the stand-in records a listener and
#: dispatches nothing but a click, so what a wheel handler DOES is out of reach
#: here and is named as such rather than asserted.
POINTER_EVENTS: Final = ("wheel", "pointerdown", "pointermove", "pointerup")

#: The highest byte the project character-set rule admits. Spelled rather than
#: imported: a test that imports a constant to assert the constant grades
#: nothing, which is the reason tests/surface/test_web_assets.py gives for its
#: own copy.
MAX_ASCII_BYTE: Final = 0x7E

#: How many numbers an SVG viewBox carries.
VIEW_BOX_PARTS: Final = 4

#: Every way a browser script reaches the network, spelled as it is USED so a
#: comment explaining the absence does not read as a use.
NETWORK_SINKS: Final = (
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "EventSource",
    "WebSocket",
    "import(",
)

#: A JavaScript comment of either kind. An arm about what the panel RENDERS has
#: to be given code; an arm about what it SAYS in prose is given the comments.
_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/|//[^\n]*")

#: Two node classes out of the closed five, and one built class. Small on
#: purpose: a fixture large enough to be realistic is a fixture whose arms stop
#: naming the thing they measure.
NODE_A: Final = "BP_ResourceNode_C"
NODE_B: Final = "BP_ResourceNodeGeyser_C"
BUILT_A: Final = "Build_MinerMk1_C"

#: A coordinate spelled to more digits than a renderer would choose, so an arm
#: can tell a verbatim string from a reformatted one.
AWKWARD_X: Final = "-12345.5678901"

#: A placement's rotation as the wire carries it - an (x, y, z, w) quaternion of
#: decimal strings. Both are UNIT quaternions, as every real one is: no rotation,
#: and a real quarter turn about the vertical axis, whose two non-zero members
#: are the shortest float32 spelling of the square root of one half.
IDENTITY_TURN: Final = ("0.0", "0.0", "0.0", "1.0")
QUARTER_TURN: Final = ("0.0", "0.0", "0.70710677", "0.70710677")

#: A placement's scale as the wire carries it - three decimal strings.
UNIT_SCALE: Final = ("1.0", "1.0", "1.0")


def _code(name: str) -> str:
    """One shipped asset with every comment stripped.

    Args:
        name: A filename inside the web directory.

    Returns:
        The asset's code, decoded strictly as ASCII.
    """
    text = (panel_harness.WEB_DIR / name).read_bytes().decode("ascii")
    return _COMMENT.sub(" ", text)


def _payload(**overrides: Any) -> dict[str, Any]:
    """The seam's payload with every key null, then the given keys replaced.

    NOT :func:`panel_harness.null_payload`, AND THE REASON IS A SEAM FACT
    RATHER THAN A PREFERENCE. That helper refuses a key outside the six it
    pins, and ``tests/surface/panel_harness.py`` is owned by CS-962 and is not
    on this slice's write-list. So the six are read OFF it - a key added there
    lands here without an edit - and the map key is added beside them.

    Args:
        **overrides: Payload keys to set, among the seam's six plus
            :data:`MAP_KEY`.

    Returns:
        A fresh dict carrying the seam's keys and the map key.

    Raises:
        ValueError: If an override names a key the seam does not publish.
    """
    keys = (*panel_harness.PAYLOAD_KEYS, MAP_KEY)
    unknown = sorted(set(overrides) - set(keys))
    if unknown:
        raise ValueError(
            f"the panel seam publishes no payload key {unknown}; it hands {list(keys)}"
        )
    payload: dict[str, Any] = dict.fromkeys(keys)
    payload.update(overrides)
    return payload


def _map_body(**overrides: Any) -> dict[str, Any]:
    """A synthetic ``/api/map`` data object, keyed as the endpoint keys it.

    That is ENFORCED rather than claimed: :func:`_assert_body_matches` checks
    the default body at import against the endpoint's own key tuples, top level
    and every row, so a key the endpoint adds or drops fails collection here.

    Every coordinate and every rate is a STRING here, because that is what the
    wire carries: a JSON number would be an IEEE double the reader cannot
    reconstruct the stored float from.

    Args:
        **overrides: Members to replace on the default body.

    Returns:
        The body a mount is handed as ``data.map``.
    """
    body: dict[str, Any] = {
        "schema": 1,
        "masked_token": "cs1-abcdef",
        "coordinate_units": "centimetres",
        "node_semantics_available": False,
        "node_orientation_available": True,
        "bounds": {
            "min_x": "-20000.0",
            "max_x": "20000.0",
            "min_y": "-10000.0",
            "max_y": "10000.0",
            "min_z": "-500.0",
            "max_z": "1500.0",
        },
        "nodes": [
            {
                "class_name": NODE_A,
                "x": AWKWARD_X,
                "y": "6789.25",
                "z": "-100.0",
                "rotation": list(IDENTITY_TURN),
                "scale": list(UNIT_SCALE),
            },
            {
                "class_name": NODE_B,
                "x": "900.5",
                "y": "-1200.75",
                "z": "12.0",
                "rotation": list(QUARTER_TURN),
                "scale": list(UNIT_SCALE),
            },
        ],
        "node_counts": {NODE_A: 1, NODE_B: 1},
        "built": [
            {
                "class_name": BUILT_A,
                "x": "1.0",
                "y": "2.0",
                "z": "3.0",
                "rotation": list(QUARTER_TURN),
                "scale": list(UNIT_SCALE),
            }
        ],
        "built_counts": {BUILT_A: 1},
        "inventory": [{"item_key": "Desc_OreIron_C", "display_name": "Iron Ore", "count": 4200}],
        "throughput": [
            {
                "class_name": BUILT_A,
                "display_name": "Miner Mk.1",
                "built": 1,
                "purity_known": False,
                "per_minute_normal": "60",
                "per_minute_unit": "items-or-litres-per-minute",
                "allowed_forms": ["RF_SOLID"],
                "purity_scaling": {"impure": "1/2", "normal": "1", "pure": "2"},
                "purity_scaling_measured": False,
            }
        ],
        # CS-1316. On the pin, over a verified registry: the state that carries
        # no build marking, so every arm above grades the panel it always did.
        "build_state": _build_state(game_pin(), game_pin(), matches=True, verified=True),
        "warnings": [{"source": "map", "code": "node-semantics-unavailable", "count": 1}],
    }
    body.update(overrides)
    return body


def _build_state(
    save: int, pinned: int | None, *, matches: bool, verified: bool | None
) -> dict[str, Any]:
    """A synthetic ``build_state``, keyed as the endpoint keys it.

    Args:
        save: The save's build - the pin or the pin plus an offset.
        pinned: The pin, or None for a pin that did not parse.
        matches: ``save_build_matches``.
        verified: ``registry_verified``, None for no registry.

    Returns:
        The state.
    """
    return {
        "save_changelist": save,
        "pinned_changelist": pinned,
        "save_build_matches": matches,
        "registry_verified": verified,
    }


def _build_warning(code: str) -> dict[str, Any]:
    """One audit build code as the endpoint serves it.

    Args:
        code: The code.

    Returns:
        The warning row, count one.
    """
    return {"source": SOURCE_BUILD, "code": code, "count": 1}


def _side(offset: int) -> str:
    """Name an off-pin offset by the side of the pin it sits on.

    Args:
        offset: One of ``OFF_PIN_OFFSETS``.

    Returns:
        ``after`` or ``before``.
    """
    return "after" if offset > 0 else "before"


def _assert_body_matches(body: dict[str, Any]) -> None:
    """Bind a canned map body to the endpoint's own key tuples, in both directions.

    CS-1022. The docstring above claimed this fixture was "shaped exactly as the
    contract froze it" while its rows carried four keys and the endpoint's
    ``PLACEMENT_KEYS`` six, and nothing checked either claim. The top level is
    checked here against ``map_endpoint.DATA_KEYS``; every row is checked by
    ``tests/surface/audit_harness.py::_assert_rows_match``, IMPORTED rather than
    copied, so the two canned map bodies in this suite answer to one row guard.

    Args:
        body: A canned ``/api/map`` data object.

    Raises:
        AssertionError: When a top-level key is missing or surplus, or - raised
            by ``_assert_rows_match`` - when a row's key set differs from the
            endpoint's tuple for its section.
    """
    missing = tuple(key for key in map_endpoint.DATA_KEYS if key not in body)
    surplus = tuple(key for key in body if key not in map_endpoint.DATA_KEYS)
    if missing or surplus:
        message = f"canned map body does not match the endpoint: {missing} {surplus}"
        raise AssertionError(message)
    _assert_rows_match(body)
    _assert_build_state_matches(body)


# THE GUARD RUNS AT IMPORT, SO A DRIFTED FIXTURE FAILS COLLECTION. An arm that
# ran it would be one arm among many going red; a module that cannot be
# collected cannot report any arm green on a body the endpoint does not serve.
_assert_body_matches(_map_body())


def _mount(tmp_path: Path, **overrides: Any) -> Mapping[str, Any]:
    """Mount the panel against a map body built from ``overrides``.

    Args:
        tmp_path: A directory the harness may write scratch files into.
        **overrides: Members to replace on :func:`_map_body`.

    Returns:
        The harness report.
    """
    report = panel_harness.mount(tmp_path, MODULE, _payload(map=_map_body(**overrides)))
    assert report["load_threw"] is None, report["load_threw"]
    assert report["state"] == panel_harness.STATE_MOUNTED, report["threw"]
    return report


def _one(report: Mapping[str, Any], node_id: str) -> Mapping[str, Any]:
    """The single row carrying ``node_id``, failing loudly on any other count.

    Args:
        report: A report from the harness.
        node_id: The element id to find.

    Returns:
        That row of the dump.
    """
    rows = panel_harness.nodes_matching(report, {"id": node_id})
    if len(rows) != 1:
        pytest.fail(
            f"{MODULE} built {len(rows)} nodes with id {node_id!r}; expected exactly one. "
            f"The tree held: {[row['tag'] + '#' + row['id'] for row in report['nodes']]}"
        )
    return rows[0]


def _text(report: Mapping[str, Any], node_id: str) -> str:
    """The joined text of the one node carrying ``node_id``.

    Args:
        report: A report from the harness.
        node_id: The element id to find.

    Returns:
        That node's ``textContent``.
    """
    return str(_one(report, node_id)["text"])


def _entries(report: Mapping[str, Any], node_id: str) -> tuple[str, ...]:
    """The text of each direct child of the element carrying ``node_id``.

    Args:
        report: A report from the harness.
        node_id: The element id to find.

    Returns:
        One string per child row, in document order.
    """
    parent = _one(report, node_id)["index"]
    return tuple(str(row["text"]) for row in report["nodes"] if row["parent"] == parent)


def _svg_class(report: Mapping[str, Any], wanted: str) -> tuple[Mapping[str, Any], ...]:
    """Every row whose ``class`` ATTRIBUTE is exactly ``wanted``.

    WHY THE ATTRIBUTE AND NOT ``className``. An SVG element's ``className`` is
    an ``SVGAnimatedString`` in a real browser and assigning a string to it
    does nothing, so the panel sets ``class`` with ``setAttribute`` on every
    node inside the SVG. The stand-in stores that in ``attributes`` and leaves
    ``className`` empty, which is exactly the real behaviour and is why an arm
    reading the harness ``class`` column would find nothing.

    Args:
        report: A report from the harness.
        wanted: The class attribute value to match.

    Returns:
        The matching rows, in document order.
    """
    return tuple(row for row in report["nodes"] if row["attributes"].get("class") == wanted)


def _view_box(report: Mapping[str, Any]) -> tuple[float, float, float, float]:
    """The SVG ``viewBox`` as four numbers.

    Args:
        report: A report from the harness.

    Returns:
        ``(min_x, min_y, width, height)``.

    Raises:
        AssertionError: If the SVG carries no four-part viewBox.
    """
    declared = _one(report, SVG_ID)["attributes"].get("viewBox")
    assert declared, f"{MODULE} put no viewBox on #{SVG_ID}"
    parts = tuple(float(part) for part in declared.split())
    assert len(parts) == VIEW_BOX_PARTS, f"a viewBox takes four numbers, not {declared!r}"
    return parts


# ---------------------------------------------------------------------------
# a. The seam feeds the panel, and the panel asks for nothing itself
# ---------------------------------------------------------------------------


def test_the_seam_probes_the_map_route_and_publishes_its_payload() -> None:
    """``app.js`` carries the ``/api/map`` probe row and the ``map`` payload key.

    A PANEL NEVER FETCHES (``app.js`` ``registerPanel``'s preamble), so this is
    the whole of the panel's supply line and it is graded in the file that owns
    it. Both halves read CODE: the probe table row and the ``panelData`` member
    are both real syntax, and a comment naming the route would satisfy neither.
    """
    code = _code(SEAM)
    row = re.search(
        r'\{\s*template:\s*"' + re.escape(MAP_ENDPOINT) + r'"\s*,'
        r'\s*method:\s*"GET"\s*,\s*probe:\s*"' + re.escape(MAP_ENDPOINT) + r'"\s*\}',
        code,
    )
    assert row is not None, f"{SEAM} carries no GET probe row for {MAP_ENDPOINT}"

    published = re.search(
        MAP_KEY + r':\s*bodyData\(probes\["' + re.escape(MAP_ENDPOINT) + r'"\]\)',
        code,
    )
    assert published is not None, f"{SEAM} hands no {MAP_KEY!r} payload to a mount"


def test_the_panel_issues_no_request_and_names_no_remote_host() -> None:
    """The panel reaches the network by no primitive and names nothing off the box.

    ``tests/surface/test_panel_seam.py`` grades this over every panel module the
    SERVER publishes. It is repeated here because this module is graded before
    that table names it, and an arm that arrives only with the route it depends
    on is an arm that grades nothing on the commit that needed it.
    """
    code = _code(MODULE)
    sinks = tuple(sink for sink in NETWORK_SINKS if sink in code)
    assert not sinks, f"{MODULE} reaches the network: {sinks}"

    raw = (panel_harness.WEB_DIR / MODULE).read_bytes()
    assert raw == raw.replace(b"\r", b""), f"{MODULE} holds a carriage return"
    assert max(raw) <= MAX_ASCII_BYTE, f"{MODULE} holds a byte above {MAX_ASCII_BYTE:#x}"
    assert b"http" not in raw.replace(b"http://www.w3.org/2000/svg", b""), (
        f"{MODULE} names a scheme that is not the SVG namespace"
    )


# ---------------------------------------------------------------------------
# b. Nothing is drawn before the fetch lands, and a refusal is named
# ---------------------------------------------------------------------------


def test_the_panel_mounts_on_an_all_null_payload_and_names_the_refusal(
    tmp_path: Path,
) -> None:
    """With ``data.map`` null the panel names the refusal and plots nothing.

    ``/api/map`` ANSWERING 503 IS THE NORMAL STATE ON A MACHINE WITH NO SAVE,
    and a blank map would read as an empty world. The seam reduces a refusal to
    a null body before a mount sees it, so the panel cannot print the reason
    code - it prints that the route did not answer with a body, and names the
    save-absent case as the ordinary cause without claiming to have read it.
    """
    report = panel_harness.mount(tmp_path, MODULE, _payload())
    assert report["load_threw"] is None, report["load_threw"]
    assert report["state"] == panel_harness.STATE_MOUNTED, report["threw"]

    note = _text(report, NOTE_ID)
    assert MAP_ENDPOINT in note, f"the note names no route: {note!r}"
    assert "did not answer" in note, f"the note does not name the refusal: {note!r}"

    assert not _svg_class(report, NODE_CLASS), "a node was plotted with no payload"
    assert not _svg_class(report, BUILT_CLASS), "a built actor was plotted with no payload"


def test_an_empty_world_says_so_rather_than_drawing_an_empty_map(tmp_path: Path) -> None:
    """A body carrying no node and nothing built says which population is empty.

    An empty SVG and an unanswered route look identical on screen. They are
    different facts, so they read differently.
    """
    report = _mount(tmp_path, nodes=[], node_counts={}, built=[], built_counts={})
    text = report["nodes"][0]["text"]
    assert "no resource node" in text, f"an empty node population is unstated: {text!r}"
    assert "nothing built" in text, f"an empty built population is unstated: {text!r}"


# ---------------------------------------------------------------------------
# c. Both populations are plotted, distinguished, and named in a legend
# ---------------------------------------------------------------------------


def test_every_node_and_built_actor_in_the_payload_is_plotted(tmp_path: Path) -> None:
    """One mark per member of each population, and the two shapes differ.

    COUNTED AGAINST THE FIXTURE RATHER THAN AGAINST A TYPED NUMBER, so a
    fixture that grows is still fully graded.
    """
    body = _map_body()
    report = _mount(tmp_path)

    plotted = _svg_class(report, NODE_CLASS)
    assert len(plotted) == len(body["nodes"]), (
        f"{len(body['nodes'])} nodes in the payload, {len(plotted)} plotted"
    )
    built = _svg_class(report, BUILT_CLASS)
    assert len(built) == len(body["built"]), (
        f"{len(body['built'])} built actors in the payload, {len(built)} plotted"
    )

    node_tags = {str(row["tag"]) for row in plotted}
    built_tags = {str(row["tag"]) for row in built}
    assert node_tags, "no tag on a plotted node"
    assert not node_tags & built_tags, (
        f"the two populations share a shape, so they read as one: {node_tags}"
    )


def test_the_legend_names_every_class_present_and_no_class_that_is_absent(
    tmp_path: Path,
) -> None:
    """The legend is derived from the payload, so it names what is on the map.

    A LEGEND TYPED INTO THE PANEL WOULD NAME THE FIVE-CLASS VOCABULARY whether
    or not this world holds one of each, which is a page telling a reader about
    marks that are not there. ``NODE_CLASS_NAMES`` is read here only to pin the
    absent member: a class in the closed vocabulary and not in this payload must
    not appear in the legend.
    """
    legend = _text(_mount(tmp_path), LEGEND_ID)
    for present in (NODE_A, NODE_B, BUILT_A):
        assert present in legend, f"the legend never names {present}: {legend!r}"

    absent = tuple(name for name in NODE_CLASS_NAMES if name not in (NODE_A, NODE_B))
    assert absent, "the fixture uses the whole node vocabulary; this arm is vacuous"
    named = tuple(name for name in absent if name in legend)
    assert not named, f"the legend names classes this world does not hold: {named}"


def test_the_panel_refuses_to_label_a_node_by_resource(tmp_path: Path) -> None:
    """The page says a node's resource cannot be known, and names where from.

    ``docs/adr/0003-s4-node-actors-in-save.md`` measured the three fields at
    zero occurrences. The wire says the same in one boolean; a reader needs the
    sentence, because the alternative is inferring iron from a dot.
    """
    text = _mount(tmp_path)["nodes"][0]["text"]
    assert "purity" in text, f"the page never mentions purity: {text!r}"
    for phrase in ("resource", "save"):
        assert phrase in text, f"the page does not say the {phrase} fact is absent"
    assert "node_semantics_available" not in text, (
        "the page prints a wire field name at the reader instead of a sentence"
    )


def test_the_svg_carries_an_accessible_name_and_a_text_alternative(tmp_path: Path) -> None:
    """The map has a name, and everything it shows is also available as text.

    A READER WHO CANNOT SEE THE SVG STILL GETS THE ANSWER. The alternative
    names each class and its count off ``node_counts`` and ``built_counts``, so
    it is the same figures the marks are drawn from rather than a second tally.
    """
    report = _mount(tmp_path)
    svg = _one(report, SVG_ID)
    assert svg["attributes"].get("role") == "img", f"the SVG declares no role: {svg['attributes']}"
    name = svg["attributes"].get("aria-label", "")
    assert name.strip(), "the SVG carries no aria-label, so focus on it announces nothing"

    described = svg["attributes"].get("aria-describedby", "")
    assert described == ALT_ID, (
        f"the SVG points at {described!r} for its description, not the list that "
        f"carries it ({ALT_ID!r})"
    )

    alternative = _text(report, ALT_ID)
    for class_name in (NODE_A, NODE_B, BUILT_A):
        assert class_name in alternative, f"the text alternative omits {class_name}"
    assert "1" in alternative, "the text alternative carries no count"


def test_the_map_is_not_listed_as_text_twice(tmp_path: Path) -> None:
    """The legend and the text alternative are ONE list, not two identical ones.

    MEASURED IN A BROWSER, NOT REASONED. The panel rendered a LEGEND and, lower
    down, a second list built from the same two count maps by the same
    function: the same lines twice, read twice by a screen reader, and green on
    every arm because each list was graded on its own. This arm grades the pair.
    """
    report = _mount(tmp_path)
    lines = [entry for entry in _entries(report, ALT_ID) if entry.strip()]
    seen = sorted(lines)
    duplicated = tuple(line for line in set(lines) if lines.count(line) > 1)
    assert not duplicated, f"the legend repeats {len(duplicated)} line(s): {duplicated}"

    # COUNTED OVER LIST ITEMS, NOT OVER EVERY NODE'S TEXT. An ancestor's text
    # contains its descendants', so a whole-panel substring count reports three
    # hits for one line and would be satisfied by no arrangement of the DOM at
    # all - an oracle that can never pass is as useless as one that always does.
    items = [
        str(row.get("text", "")).strip()
        for row in panel_harness.nodes_matching(report, {"tag": "li"})
    ]
    for line in seen:
        occurrences = items.count(line)
        assert occurrences == 1, f"{line!r} is a list item {occurrences} times on the panel"


def test_an_empty_inventory_does_not_read_as_an_empty_world(tmp_path: Path) -> None:
    """An empty item total is served with its reason, and the panel prints it.

    THE PINNED DEVELOPMENT WORLD MAKES THIS THE NORMAL CASE, NOT AN EDGE ONE.
    Its record payloads do not decode at all, so the aggregate is empty for a
    reason that has nothing to do with what the player is holding. "No item was
    served" alone reads as "you have nothing", which is a confident wrong
    answer of exactly the kind non-negotiable 7 forbids.
    """
    code = "inventory-total-empty"
    report = _mount(
        tmp_path,
        inventory=[],
        warnings=[{"source": "inventory", "code": code, "count": 1}],
    )
    printed = _text(report, INVENTORY_ID)
    assert code in printed, f"the empty inventory names no reason: {printed!r}"
    assert "not a claim" in printed, f"the empty inventory is not disclaimed: {printed!r}"


def test_no_coordinate_reaches_the_page_in_a_spelling_the_payload_did_not_carry(
    tmp_path: Path,
) -> None:
    """Any coordinate the panel PRINTS is the string it was handed, verbatim.

    THIS IS HOW "NEVER PRINT A ROUNDED COORDINATE WITHOUT SAYING SO" IS
    ENFORCED WITHOUT TRUSTING A SENTENCE: the panel prints no rounded
    coordinate at all. The fixture's x carries more digits than any renderer
    would choose, so a panel that reformatted would fail this rather than pass
    it quietly. Geometry is a different question - the SVG attributes ARE
    derived from the parsed numbers, which is why this arm reads TEXT only.
    """
    report = _mount(tmp_path)
    text = report["nodes"][0]["text"]
    assert AWKWARD_X in text, (
        f"the page prints no coordinate at all, so this arm grades nothing: {text!r}"
    )

    handed = {AWKWARD_X, "6789.25", "900.5", "-1200.75", "-20000.0", "20000.0"}
    truncations = tuple(
        candidate
        for original in handed
        for candidate in (original[:-2],)
        if candidate not in handed and candidate in text and original not in text
    )
    assert not truncations, f"a coordinate reached the page shortened: {truncations}"


# ---------------------------------------------------------------------------
# d. The controls are real buttons, and they move the viewBox
# ---------------------------------------------------------------------------


def test_every_control_is_a_real_button_carrying_a_click_listener(tmp_path: Path) -> None:
    """Seven labelled buttons, each with a click handler attached.

    A CONTROL THAT IS NOT A BUTTON IS NOT KEYBOARD-REACHABLE, and a button with
    no listener is a control that does nothing. Both halves are read off the
    tree the panel built rather than off its source text.
    """
    report = _mount(tmp_path)
    buttons = {
        str(row["text"]): row for row in report["nodes"] if str(row["tag"]).upper() == "BUTTON"
    }
    missing = tuple(label for label in CONTROL_LABELS if label not in buttons)
    assert not missing, f"{MODULE} built no button for {missing}; it built {sorted(buttons)}"

    deaf = tuple(label for label in CONTROL_LABELS if "click" not in buttons[label]["listens"])
    assert not deaf, f"these buttons carry no click listener: {deaf}"

    unnamed = tuple(
        label for label in CONTROL_LABELS if not buttons[label]["attributes"].get("type")
    )
    assert not unnamed, f"these buttons declare no type, so a form could submit them: {unnamed}"


def test_zooming_in_narrows_the_view_box_and_reset_restores_it(tmp_path: Path) -> None:
    """Zoom in shrinks the viewBox extent; Reset puts it back exactly.

    ``setAttribute`` ON THE ``viewBox`` IS THE WHOLE MECHANISM, which is both
    the simplest correct SVG answer and the only one the narrow stand-in can
    express. Reset is graded as an EQUALITY against the first view rather than
    as "something changed", because a reset that lands near the start is the
    bug this catches.
    """
    start = _view_box(_mount(tmp_path))

    zoomed = _view_box(
        panel_harness.run(tmp_path, MODULE, _payload(map=_map_body()), clicks=[{"text": ZOOM_IN}])
    )
    assert zoomed[2] < start[2], f"zoom in did not narrow the width: {start} -> {zoomed}"
    assert zoomed[3] < start[3], f"zoom in did not narrow the height: {start} -> {zoomed}"

    restored = _view_box(
        panel_harness.run(
            tmp_path,
            MODULE,
            _payload(map=_map_body()),
            clicks=[{"text": ZOOM_IN}, {"text": ZOOM_IN}, {"text": RESET}],
        )
    )
    assert restored == start, f"Reset view did not restore the first view: {start} -> {restored}"


def test_zooming_out_widens_the_view_box(tmp_path: Path) -> None:
    """Zoom out is the inverse of zoom in, and is reachable on its own."""
    start = _view_box(_mount(tmp_path))
    widened = _view_box(
        panel_harness.run(tmp_path, MODULE, _payload(map=_map_body()), clicks=[{"text": ZOOM_OUT}])
    )
    assert widened[2] > start[2], f"zoom out did not widen the width: {start} -> {widened}"
    assert widened[3] > start[3], f"zoom out did not widen the height: {start} -> {widened}"


@pytest.mark.parametrize(
    ("label", "axis", "direction"),
    [
        (PAN_RIGHT, 0, 1),
        (PAN_LEFT, 0, -1),
        (PAN_DOWN, 1, 1),
        (PAN_UP, 1, -1),
    ],
)
def test_each_pan_button_moves_the_view_on_its_own_axis_and_sense(
    tmp_path: Path, label: str, axis: int, direction: int
) -> None:
    """One press moves the view origin on one axis, in the named sense.

    ALL FOUR DIRECTIONS ARE GRADED, not one of them, because the shape this
    catches is a copied handler that pans the same way twice - and a panel that
    pans east on the west button is a panel a reader cannot navigate.

    THE SENSE IS SCREEN SENSE AND THE PANEL'S OWN AXES SAY SO. Panning east
    raises ``min_x``, which moves the view rightwards over the world; panning
    south raises ``min_y``, which is downwards on screen because the SVG y axis
    grows downwards. The panel documents the flip at the point it applies it.

    Args:
        tmp_path: Provided by pytest.
        label: The button to press.
        axis: 0 for the x origin, 1 for the y origin.
        direction: 1 when the origin must rise, -1 when it must fall.
    """
    start = _view_box(_mount(tmp_path))
    moved = _view_box(
        panel_harness.run(tmp_path, MODULE, _payload(map=_map_body()), clicks=[{"text": label}])
    )
    assert (moved[axis] - start[axis]) * direction > 0, (
        f"{label} moved the origin the wrong way on axis {axis}: {start} -> {moved}"
    )
    other = 1 - axis
    assert moved[other] == start[other], f"{label} also moved axis {other}: {start} -> {moved}"
    assert moved[2:] == start[2:], f"{label} changed the extent as well as the origin: {moved}"


def test_the_svg_also_carries_the_pointer_and_wheel_affordances(tmp_path: Path) -> None:
    """Drag and wheel are attached too, as the extra path and not the only one.

    PRESENCE IS ALL THIS ARM CLAIMS. The stand-in dispatches a click and
    nothing else, and this project has measured a browser automation pane
    faking wheel outright, so what these handlers DO is graded by neither
    instrument available here and is stated as unmeasured rather than implied.
    """
    listens = set(_one(_mount(tmp_path), SVG_ID)["listens"])
    missing = tuple(name for name in POINTER_EVENTS if name not in listens)
    assert not missing, f"the SVG carries no {missing} handler; it carries {sorted(listens)}"


# ---------------------------------------------------------------------------
# e. Per-class filters
# ---------------------------------------------------------------------------


def test_a_filter_toggle_hides_one_population_and_a_second_press_restores_it(
    tmp_path: Path,
) -> None:
    """Pressing a class filter removes that class's marks and leaves the others.

    THE OTHER POPULATION IS CHECKED ON THE SAME PRESS, because a filter that
    clears the whole map would satisfy a one-sided arm. The toggle also reports
    its own state, so a reader knows a class is hidden rather than absent.
    """
    body = _map_body()
    first = panel_harness.run(
        tmp_path, MODULE, _payload(map=body), clicks=[{"text": "Hide " + NODE_A}]
    )
    assert first["steps"][-1]["threw"] is None, first["steps"][-1]["threw"]

    remaining = _svg_class(first, NODE_CLASS)
    assert len(remaining) == 1, f"hiding one of two node classes left {len(remaining)} marks"
    assert len(_svg_class(first, BUILT_CLASS)) == len(body["built"]), (
        "hiding a node class also cleared the built population"
    )

    again = panel_harness.run(
        tmp_path,
        MODULE,
        _payload(map=body),
        clicks=[{"text": "Hide " + NODE_A}, {"text": "Show " + NODE_A}],
    )
    assert len(_svg_class(again, NODE_CLASS)) == len(body["nodes"]), (
        "a second press did not restore the hidden class"
    )


# ---------------------------------------------------------------------------
# f. What I have, and how fast
# ---------------------------------------------------------------------------


def test_the_inventory_names_each_item_by_display_name_and_count(tmp_path: Path) -> None:
    """What I have: the item's display name and its count, one row each.

    THE DISPLAY NAME AND NOT THE KEY. ``Desc_OreIron_C`` is an identifier the
    operator never sees in game; the answer to "what resources do I have" is
    the words on the tooltip. The key is not printed at all, so there is no
    second spelling of the same thing for a reader to reconcile.
    """
    report = _mount(tmp_path)
    rows = _entries(report, INVENTORY_ID)
    assert len(rows) == 1, f"one inventory item in the payload, {len(rows)} rendered: {rows}"
    assert "Iron Ore" in rows[0], rows[0]
    assert "4200" in rows[0], rows[0]
    assert "Desc_OreIron_C" not in rows[0], f"the page prints the item key at the reader: {rows[0]}"


def test_an_empty_inventory_says_so(tmp_path: Path) -> None:
    """No inventory is a sentence, never an empty list."""
    report = _mount(tmp_path, inventory=[])
    text = report["nodes"][0]["text"]
    assert "no item" in text, f"an empty inventory is unstated: {text!r}"


def test_the_throughput_separates_the_derived_rate_from_the_assumed_scaling(
    tmp_path: Path,
) -> None:
    """The row carries the class, the built count, the exact rate and the caveat.

    THE SENTENCE IS THE POINT, AND WHICH HALF IT ATTACHES TO IS THE WHOLE
    FINDING. The normal-purity figure is derived exactly from the game's own
    shipped numbers. The impure and pure multipliers are not in any file on this
    machine, and the wire says so with ``purity_scaling_measured`` false. A row
    that printed all three in one voice would present an assumption as a
    measurement, which is the fault this arm exists to catch.
    """
    report = _mount(tmp_path)
    rows = _entries(report, THROUGHPUT_ID)
    assert len(rows) == 1, f"one throughput row in the payload, {len(rows)} rendered: {rows}"

    row = rows[0]
    for token in ("Miner Mk.1", "60", "NORMAL", "impure", "pure", "1/2", "ASSUMED"):
        assert token in row, f"the throughput row omits {token!r}: {row!r}"

    text = report["nodes"][0]["text"]
    assert "not measured" in text, f"the assumed scaling is not disclaimed: {text!r}"


def test_a_machine_with_no_published_rate_says_so_rather_than_printing_a_zero(
    tmp_path: Path,
) -> None:
    """A null rate is rendered as absent, never as zero.

    The registry refuses to default an absent extraction rate to a number the
    game did not ship, for the reason its own model gives: a confident zero is
    exactly what a plan cannot detect as wrong. That refusal is worth nothing if
    the page rounds it back to a figure.
    """
    report = _mount(
        tmp_path,
        throughput=[
            {
                "class_name": "Build_UnratedThing_C",
                "display_name": "Unrated Thing",
                "built": 2,
                "purity_known": False,
                "per_minute_normal": None,
                "per_minute_unit": "items-or-litres-per-minute",
                "allowed_forms": [],
                "purity_scaling": {"impure": "1/2", "normal": "1", "pure": "2"},
                "purity_scaling_measured": False,
            }
        ],
    )
    row = _entries(report, THROUGHPUT_ID)[0]
    assert "0" not in row.split("built")[1], f"a zero rate was rendered: {row!r}"
    assert "no rate is published" in row, f"an absent rate is not named: {row!r}"


def test_an_empty_throughput_prints_the_warning_reason_rather_than_an_empty_box(
    tmp_path: Path,
) -> None:
    """With no throughput the panel prints the warning code that says why.

    AN EMPTY SECTION WOULD READ AS "YOU HAVE NO EXTRACTORS", which is a
    confident wrong answer of the kind non-negotiable 7 forbids. The reason is
    read off the warnings array rather than typed, so the day the code changes
    the page says the new one.
    """
    code = "extraction-rate-unavailable"
    report = _mount(
        tmp_path,
        throughput=[],
        warnings=[{"source": "map", "code": code, "count": 1}],
    )
    printed = _text(report, THROUGHPUT_ID)
    assert code in printed, f"the empty throughput names no reason: {printed!r}"
    assert printed.strip(), "the throughput section is empty and says nothing"


def test_a_warning_from_a_layer_below_the_endpoint_still_reaches_the_reader(
    tmp_path: Path,
) -> None:
    """The explainer reads every warning source, not just the endpoint's own.

    THE ENDPOINT DOES NOT REMAP A WARNING'S SOURCE AND THAT IS DELIBERATE: the
    field names the layer that flagged it, so ``placement`` and ``inventory``
    reach the wire spelled as themselves. This panel filtered on the endpoint's
    own source for one revision, which dropped precisely the warnings that
    explain an empty answer - the emptiness and its reason arriving from
    different layers is the normal case, not the exotic one.
    """
    code = "inventory-total-empty"
    report = _mount(
        tmp_path,
        throughput=[],
        warnings=[{"source": "inventory", "code": code, "count": 1}],
    )
    printed = _text(report, THROUGHPUT_ID)
    assert code in printed, f"a warning from a lower layer never reached the page: {printed!r}"


def test_an_empty_throughput_with_no_warning_still_refuses_to_imply_zero(
    tmp_path: Path,
) -> None:
    """A missing reason is reported as missing, never rendered as an empty box.

    The wire is required to carry the warning. A panel that trusted it would
    print nothing on the one body where the server got it wrong, and nothing is
    the reading this whole section exists to prevent.
    """
    report = _mount(tmp_path, throughput=[], warnings=[])
    printed = _text(report, THROUGHPUT_ID)
    assert printed.strip(), "an unexplained empty throughput rendered as an empty box"
    assert "no reason" in printed, f"the absent warning is not named: {printed!r}"


# ---------------------------------------------------------------------------
# g. Which build the rate belongs to - CS-1316
# ---------------------------------------------------------------------------


def _page(report: Mapping[str, Any]) -> str:
    """The whole mounted panel's text, lower-cased for a claim sweep.

    Args:
        report: A report from the harness.

    Returns:
        The root's ``textContent``, lower-cased.
    """
    return str(report["nodes"][0]["text"]).lower()


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_an_off_pin_world_marks_the_rate_as_the_pinned_builds(tmp_path: Path, offset: int) -> None:
    """Off the pin, over a verified registry, each served rate says whose it is.

    The marking attaches to the RATE: a row with no rate has nothing to mark
    and carries none. The note states both builds as the wire spelled them
    and the audit code verbatim, so the reader sees the evidence, not only
    the conclusion.
    """
    pin = game_pin()
    save = pin + offset
    rated = dict(_map_body()["throughput"][0])
    unrated = dict(rated, class_name="Build_UnratedThing_C", per_minute_normal=None)
    report = _mount(
        tmp_path,
        build_state=_build_state(save, pin, matches=False, verified=True),
        throughput=[rated, unrated],
        warnings=[_build_warning(BUILD_MISMATCH)],
    )

    rows = _entries(report, THROUGHPUT_ID)
    assert len(rows) == TWO_RATE_ROWS, f"two throughput rows served, {len(rows)} rendered: {rows}"
    assert "60" in rows[0], rows[0]
    assert PINNED_MARK in rows[0].lower(), f"an off-pin rate is not marked: {rows[0]!r}"
    assert PINNED_MARK not in rows[1].lower(), f"a row with no rate was marked: {rows[1]!r}"

    note = _text(report, BUILD_ID)
    assert str(save) in note, f"the note names no save build: {note!r}"
    assert str(pin) in note, f"the note names no pinned build: {note!r}"
    assert BUILD_MISMATCH in note, f"the note drops the served code: {note!r}"


def test_an_on_pin_world_carries_no_build_marking(tmp_path: Path) -> None:
    """On the pin, over a verified registry, there is nothing to say and nothing is said."""
    report = _mount(tmp_path)
    rows = _entries(report, THROUGHPUT_ID)
    assert "60" in rows[0], f"the rate never rendered, so this arm grades nothing: {rows!r}"
    page = _page(report)
    assert PINNED_MARK not in page, "an on-pin rate was marked as the pinned build's"
    assert "unverified" not in page, "a verified registry was called unverified"
    built = panel_harness.nodes_matching(report, {"id": BUILD_ID})
    assert not built, f"an on-pin world rendered a build note: {built!r}"


@pytest.mark.parametrize("state", UNVERIFIED_STATES, ids=lambda state: state[0])
@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_an_unverified_registry_is_never_marked_as_the_pinned_builds(
    tmp_path: Path, offset: int, state: tuple[str, bool | None, str | None]
) -> None:
    """Off the pin, a registry not shown to be the pin's makes no pinned-build claim.

    The rate row is the default one, so a rate IS rendered and the absence of
    the marking is not the absence of a row. The note says the registry is
    unverified and carries every served build code verbatim.
    """
    _name, verified, registry_code = state
    pin = game_pin()
    codes = [BUILD_MISMATCH] if registry_code is None else [BUILD_MISMATCH, registry_code]
    report = _mount(
        tmp_path,
        build_state=_build_state(pin + offset, pin, matches=False, verified=verified),
        warnings=[_build_warning(code) for code in codes],
    )

    rows = _entries(report, THROUGHPUT_ID)
    assert "60" in rows[0], f"the rate never rendered, so this arm grades nothing: {rows!r}"
    page = _page(report)
    assert PINNED_MARK not in page, "a rate from an unverified registry was marked as the pin's"

    note = _text(report, BUILD_ID)
    assert "unverified" in note, f"the note does not say the registry is unverified: {note!r}"
    missing = [code for code in codes if code not in note]
    assert not missing, f"the note drops served codes {missing}: {note!r}"


def test_an_on_pin_world_over_an_unverified_registry_still_says_so(tmp_path: Path) -> None:
    """The registry half stands alone: a matching save does not verify the registry."""
    pin = game_pin()
    report = _mount(
        tmp_path,
        build_state=_build_state(pin, pin, matches=True, verified=False),
        warnings=[_build_warning("registry-unverified")],
    )
    assert PINNED_MARK not in _page(report), "an unverified rate was marked as the pin's"
    note = _text(report, BUILD_ID)
    assert "unverified" in note, f"the note does not say the registry is unverified: {note!r}"


def test_an_unparsed_pin_still_marks_a_verified_rate_as_the_pinned_builds(
    tmp_path: Path,
) -> None:
    """An uncompared build is never a match, so a verified rate is still the pin's.

    The note must not print a null as a changelist: it says the pin did not
    parse, and the served code says the builds were never compared.
    """
    pin = game_pin()
    report = _mount(
        tmp_path,
        build_state=_build_state(pin, None, matches=False, verified=True),
        warnings=[_build_warning(BUILD_UNCOMPARED)],
    )
    rows = _entries(report, THROUGHPUT_ID)
    assert PINNED_MARK in rows[0].lower(), f"a verified uncompared rate is unmarked: {rows[0]!r}"
    note = _text(report, BUILD_ID)
    assert BUILD_UNCOMPARED in note, f"the note drops the served code: {note!r}"
    assert "did not parse" in note, f"the note does not say the pin did not parse: {note!r}"
    assert "null" not in note.lower(), f"the note printed a null as a build: {note!r}"


def test_a_body_without_a_build_state_makes_no_build_claim(tmp_path: Path) -> None:
    """A body carrying no build state is reported as carrying none, never read as on-pin."""
    report = _mount(tmp_path, build_state=None)
    assert PINNED_MARK not in _page(report), "a rate was marked with no build state served"
    note = _text(report, BUILD_ID)
    assert "no build state" in note, f"the absent build state is not named: {note!r}"
