"""CS-962 slice S3 - the Registry panel, graded by mounting it.

WHAT THIS MODULE GRADES. ``clockspeed/surface/web/panel_registry.js`` is mounted
under ``tests/surface/panel_harness.py`` against SYNTHETIC payloads authored
here, and the DOM it builds is read back. Nothing here reads a real registry, so
the arms run on a machine with no game installed - which is the rule
``CLAUDE.md`` section 7 states for fixtures.

WHY THE PANEL EXISTS AT ALL. Before it, ``/api/registry`` was probed on every
repaint and only its HTTP STATUS reached the page: not one item, recipe or
building name was ever displayed. The solve bench's vocabulary is exactly the
identifiers that route carries, so a caller had to invent one. Every arm below
asserts that some piece of registry CONTENT reached the DOM.

THE THREE RENDERING RULES THE ARMS ENFORCE, each of which is a project rule
rather than a taste:

  1. A RATE IS RENDERED FROM THE PAIR THE WIRE CARRIES. ``duration`` and
     ``energy_value`` arrive as ``{"num": int, "den": int}``
     (``clockspeed/surface/api/registry.py:177-203``). The pair is the truth and
     is shown as the pair; a decimal may sit beside it ONLY labelled as an
     approximation. Non-negotiable 6 does not stop at the browser.
  2. ABSENT IS NOT ZERO. ``energy_value`` and ``sink_points`` are both nullable
     (``clockspeed/data/registry.py:453`` and
     ``clockspeed/surface/api/registry.py:190-202``), and the data layer states
     that None and zero are different facts. A confident zero over an absent
     measurement is the one unacceptable rendering.
  3. A NULL PAYLOAD RENDERS WITHOUT THROWING AND WITHOUT INVENTING NUMBERS.
     Under the seam grader's canned probes ``data.registry`` is null, and a
     throw would redden an arm this slice does not own.

THE BASELINE PIN, AND WHY IT LIVES HERE.
``tests/surface/test_panel_seam.py:518-528`` takes ``PANEL_MODULES[0]`` as the
CLEAN BASELINE for the network detector that grades all four panels, and sorted,
that is this slice's module. The ordering is alphabetical and no arm in that
file declares it. If a module sorting before ``panel_registry.js`` is ever
added, the baseline moves silently to a file nobody checked. Worse, the baseline
is a CONCATENATION PREFIX: a sink in the baseline makes the fire-check compute
an empty set and PASS while grading nothing - a gate that skips its checks
reporting PASS, one layer down. The pin below makes that move visible.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Final

from tests.surface import panel_harness
from tests.surface.test_panel_seam import PANEL_MODULES

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: The module under grade.
MODULE: Final = "panel_registry.js"

#: The id it registers with the seam.
PANEL_ID: Final = "registry"

#: The roster cap the panel declares. Pinned here rather than parsed out of the
#: asset, so raising it is a deliberate two-file edit and not a silent one.
ROSTER_CAP: Final = 25

#: How many rows the truncation arm builds, so the cap is genuinely exceeded.
OVERSIZED: Final = 30

#: The two item keys every content arm looks for.
IRON_ROD: Final = "Desc_IronRod_C"
WATER: Final = "Desc_Water_C"
RECIPE_KEY: Final = "Recipe_IronRod_C"
BUILDING_KEY: Final = "Build_ConstructorMk1_C"
WARNING_CODE: Final = "item_missing_name"
WARNING_SUBJECT: Final = "Desc_Mystery_C"
UNKNOWN_GROUP: Final = "FGBuildableWeirdThing"

#: What the panel must say when it is handed no registry at all.
ROUTE: Final = "/api/registry"

#: The word that marks a decimal as not the truth beside it.
APPROX: Final = "approx."

#: What an absent measurement renders as. Never a zero.
ABSENT: Final = "not declared"


def _item(
    key: str,
    display_name: str,
    form: str,
    *,
    is_fluid: bool,
    energy_value: Mapping[str, int] | None,
    sink_points: int | None,
) -> dict[str, Any]:
    """One item, keyed exactly as ``registry.ITEM_KEYS`` spells it."""
    return {
        "key": key,
        "display_name": display_name,
        "form": form,
        "is_fluid": is_fluid,
        "energy_value": energy_value,
        "sink_points": sink_points,
    }


def _registry(**overrides: Any) -> dict[str, Any]:
    """A synthetic ``/api/registry`` body: 2 items, 1 recipe, 1 building, 1 warning.

    The shape is read off the endpoint's own builder
    (``clockspeed/surface/api/registry.py:180-320``), not off prose. The first
    item declares no energy value and the second declares no sink points, so one
    fixture carries both halves of the absent-is-not-zero rule.
    """
    body: dict[str, Any] = {
        "items": [
            _item(
                IRON_ROD,
                "Iron Rod",
                "RF_SOLID",
                is_fluid=False,
                energy_value=None,
                sink_points=4,
            ),
            _item(
                WATER,
                "Water",
                "RF_LIQUID",
                is_fluid=True,
                energy_value={"num": 0, "den": 1},
                sink_points=None,
            ),
        ],
        "recipes": [
            {
                "key": RECIPE_KEY,
                "display_name": "Iron Rod",
                "duration": {"num": 10, "den": 3},
                "inputs": [{"item_key": "Desc_IronIngot_C", "amount": {"num": 1, "den": 1}}],
                "outputs": [{"item_key": IRON_ROD, "amount": {"num": 1, "den": 1}}],
                "produced_in": [BUILDING_KEY],
            }
        ],
        "buildings": [{"key": BUILDING_KEY, "display_name": "Constructor"}],
        "counts": {
            "items": 2,
            "recipes": 1,
            "buildings": 1,
            "warnings": 1,
            "unknown_groups": 1,
        },
        "warnings": [
            {
                "code": WARNING_CODE,
                "subject": WARNING_SUBJECT,
                "detail": "the entry declared no display name",
                "count": 2,
            }
        ],
        "unknown_groups": [UNKNOWN_GROUP],
    }
    body.update(overrides)
    return body


def _panel_text(report: Mapping[str, Any]) -> str:
    """Everything the panel put on screen, as one string.

    Row 0 of the dump is the panel's own section
    (``tests/surface/panel_harness.py:567-604``), so its ``textContent`` is the
    whole rendered panel.
    """
    return str(report["nodes"][0]["text"])


def _cell_texts(report: Mapping[str, Any]) -> tuple[str, ...]:
    """The text of every table cell the panel built."""
    return tuple(str(row["text"]) for row in panel_harness.nodes_matching(report, {"tag": "td"}))


def _field_texts(report: Mapping[str, Any], field: str) -> tuple[str, ...]:
    """The text of every cell the panel tagged with ``data-field=<field>``.

    A cell is selected by the field it renders rather than by its class, because
    the class carries presentation and one cell may need both - and because
    ``nodes_matching`` compares a class string for EQUALITY, so a two-token
    class would make the match silently select nothing, which reads exactly like
    a panel that never built the cell.
    """
    return tuple(
        str(row["text"])
        for row in panel_harness.nodes_matching(report, {"tag": "td"})
        if row["attributes"].get("data-field") == field
    )


def _mount(tmp_path: Path, registry: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Mount the shipped module against one registry payload."""
    return panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(registry=registry))


# ---------------------------------------------------------------------------
# a. The baseline pin - see the module docstring
# ---------------------------------------------------------------------------


def test_this_module_is_the_network_detectors_clean_baseline() -> None:
    """``PANEL_MODULES[0]`` is this slice's file, and nothing else declares that.

    ``test_panel_seam.py:522`` reads ``PANEL_MODULES[0]`` as the text the network
    detector must find clean, and line 526 concatenates each sink onto it to
    prove the detector fires. Both claims are claims about THIS file. The
    ordering that makes it so is ``sorted()`` over the server's asset names and
    is stated nowhere - so this is the one arm that would go red the day a new
    panel module sorts ahead of it, instead of the baseline moving in silence.
    """
    assert PANEL_MODULES, "no panel module is published, so the baseline names nothing"
    assert PANEL_MODULES[0] == MODULE, (
        f"the network detector's clean baseline moved from {MODULE} to "
        f"{PANEL_MODULES[0]}; the arm at test_panel_seam.py:522 now grades a "
        "file this pin was never checked against"
    )


def test_the_baseline_module_carries_no_line_comment() -> None:
    """A ``//`` comment survives into the baseline and can carry a sink word.

    ``code_only`` in the seam grader strips BLOCK comments only
    (``test_panel_seam.py:_BLOCK_COMMENT``), so prose in a line comment is
    indistinguishable from code to the detector. This file therefore documents
    itself in block comments exclusively.
    """
    source = (panel_harness.WEB_DIR / MODULE).read_text(encoding="ascii")
    offenders = tuple(
        line.strip() for line in source.splitlines() if re.search(r"(?<![:/])//", line)
    )
    assert not offenders, f"{MODULE} holds line comment(s) that reach the detector: {offenders}"


# ---------------------------------------------------------------------------
# b. It registers, and it survives the payload the seam grader actually hands it
# ---------------------------------------------------------------------------


def test_the_module_registers_the_registry_panel(tmp_path: Path) -> None:
    report = _mount(tmp_path, _registry())
    assert report["registered"] is True
    assert report["panel_id"] == PANEL_ID
    assert report["load_threw"] is None


def test_an_entirely_null_payload_mounts_without_throwing(tmp_path: Path) -> None:
    """The seam grader's canned probes leave every payload key null."""
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    assert report["threw"] is None
    assert report["state"] == "mounted"


# ---------------------------------------------------------------------------
# c. Acceptance 1 - registry CONTENT reaches the DOM
# ---------------------------------------------------------------------------


def test_the_panel_names_every_item_the_registry_carries(tmp_path: Path) -> None:
    """The defect CS-962 exists to fix: not one identifier used to be displayed."""
    text = _panel_text(_mount(tmp_path, _registry()))
    missing = tuple(key for key in (IRON_ROD, WATER) if key not in text)
    assert not missing, f"the panel displayed no row for {missing}"


def test_the_panel_names_the_recipe_and_the_building(tmp_path: Path) -> None:
    text = _panel_text(_mount(tmp_path, _registry()))
    missing = tuple(key for key in (RECIPE_KEY, BUILDING_KEY) if key not in text)
    assert not missing, f"the panel displayed no row for {missing}"


def test_the_panel_renders_display_names_beside_the_keys(tmp_path: Path) -> None:
    """A key alone is not a lookup; the human-readable name is half the answer."""
    text = _panel_text(_mount(tmp_path, _registry()))
    missing = tuple(name for name in ("Iron Rod", "Water", "Constructor") if name not in text)
    assert not missing, f"the panel displayed no display name for {missing}"


def test_the_panel_renders_the_five_counts(tmp_path: Path) -> None:
    """``COUNT_KEYS`` is a cheap header over collections the body also carries."""
    text = _panel_text(_mount(tmp_path, _registry()))
    missing = tuple(
        label
        for label in ("items", "recipes", "buildings", "warnings", "unknown groups")
        if label not in text
    )
    assert not missing, f"the counts grid named no {missing}"


def test_the_panel_renders_each_warning_in_full(tmp_path: Path) -> None:
    """A flagged-and-skipped piece of content is useless without its subject."""
    text = _panel_text(_mount(tmp_path, _registry()))
    missing = tuple(
        part
        for part in (WARNING_CODE, WARNING_SUBJECT, "the entry declared no display name")
        if part not in text
    )
    assert not missing, f"the warning list dropped {missing}"


def test_the_panel_names_each_unknown_group(tmp_path: Path) -> None:
    text = _panel_text(_mount(tmp_path, _registry()))
    assert UNKNOWN_GROUP in text


# ---------------------------------------------------------------------------
# d. Acceptance 2 - the pair is the truth, the decimal is labelled
# ---------------------------------------------------------------------------


def test_a_duration_renders_as_the_exact_pair_the_wire_carried(tmp_path: Path) -> None:
    """10/3 is a rate no decimal can spell, and the pair is what arrived."""
    cells = _cell_texts(_mount(tmp_path, _registry()))
    assert any(cell == "10/3" or "10/3" in cell.split() for cell in cells), (
        f"no cell carried the exact duration 10/3; cells were {cells}"
    )


def test_the_decimal_beside_a_rate_is_marked_an_approximation(tmp_path: Path) -> None:
    """A decimal that is not labelled approximate reads as the exact value.

    The operator's ruling is that the pair is the truth and is shown, and that a
    rounded decimal may sit beside it ONLY if it is explicitly labelled an
    approximation for display. Rendering the decimal alone is refused.
    """
    cells = _cell_texts(_mount(tmp_path, _registry()))
    approximations = tuple(cell for cell in cells if APPROX in cell)
    assert approximations, f"no cell labelled a decimal approximate; cells were {cells}"
    assert any(re.search(r"3\.33", cell) for cell in approximations), (
        f"the approximation of 10/3 was not rendered; labelled cells were {approximations}"
    )


def test_no_bare_decimal_stands_where_a_rate_belongs(tmp_path: Path) -> None:
    """Every decimal on the panel sits in a cell that calls itself approximate.

    This is the arm that refuses the decimal-alone rendering. A panel that
    dropped the pair and kept the number would still pass the arm above.
    """
    cells = _cell_texts(_mount(tmp_path, _registry()))
    unlabelled = tuple(cell for cell in cells if re.search(r"\d\.\d", cell) and APPROX not in cell)
    assert not unlabelled, f"a decimal was rendered as if exact in {unlabelled}"


#: Ratios whose truncation to three places is worked out by hand here, so the
#: arm below cannot be satisfied by a constant. 10/3 alone would be: a panel
#: that rendered the literal "3.333" for every rate passes every other arm in
#: this file, which is the equivalent-mutant shape - a defect no VALUE the
#: fixture carries can expose unless the fixture carries more than one.
APPROXIMATIONS: Final = (
    ({"num": 10, "den": 3}, "10/3", "approx. 3.333"),
    ({"num": 1, "den": 8}, "1/8", "approx. 0.125"),
    ({"num": 100, "den": 7}, "100/7", "approx. 14.285"),
    ({"num": 4, "den": 1}, "4/1", "approx. 4.000"),
)


def test_each_approximation_is_the_ratio_it_sits_beside(tmp_path: Path) -> None:
    """The decimal is derived from the pair, not copied from one fixture.

    Each row is a SEPARATE mount, because the arm is about the panel computing
    the digits rather than about one lucky constant. 100/7 is included because
    its third place is a truncation and not a rounding - 14.2857 renders as
    14.285, so a panel that rounded would be visible here.
    """
    for pair, exact, approximate in APPROXIMATIONS:
        recipe = {
            "key": RECIPE_KEY,
            "display_name": "Iron Rod",
            "duration": pair,
            "inputs": [],
            "outputs": [],
            "produced_in": [],
        }
        report = _mount(tmp_path, _registry(recipes=[recipe]))
        assert _field_texts(report, "recipe_duration") == (exact,), (
            f"{pair} did not render as the pair {exact}"
        )
        assert _field_texts(report, "recipe_duration_approx") == (approximate,), (
            f"{pair} did not render the approximation {approximate}"
        )


def test_the_panel_states_that_a_decimal_is_for_display_only(tmp_path: Path) -> None:
    text = _panel_text(_mount(tmp_path, _registry()))
    assert "approximation" in text


# ---------------------------------------------------------------------------
# e. Acceptance 4 - absent is not zero
# ---------------------------------------------------------------------------


def test_an_absent_energy_value_is_named_absent_and_not_zeroed(tmp_path: Path) -> None:
    """None and ``Fraction(0)`` are different facts (registry.py:190-202)."""
    texts = _field_texts(_mount(tmp_path, _registry()), "item_energy")
    assert texts, "the items table rendered no energy value cell at all"
    absent = tuple(text for text in texts if ABSENT in text)
    assert absent, f"no item named its energy value absent; cells were {texts}"
    assert not any(re.search(r"\d", text) for text in absent), (
        f"an absent energy value was rendered with a number in it: {absent}"
    )


def test_an_absent_sink_point_count_is_named_absent_and_not_zeroed(tmp_path: Path) -> None:
    texts = _field_texts(_mount(tmp_path, _registry()), "item_sink")
    assert texts, "the items table rendered no sink point cell at all"
    absent = tuple(text for text in texts if ABSENT in text)
    assert absent, f"no item named its sink point count absent; cells were {texts}"
    assert not any(re.search(r"\d", text) for text in absent), (
        f"an absent sink point count was rendered with a number in it: {absent}"
    )


def test_a_declared_zero_energy_value_is_still_rendered_as_a_pair(tmp_path: Path) -> None:
    """The second item declares 0/1, which is a MEASUREMENT and not an absence."""
    cells = _cell_texts(_mount(tmp_path, _registry()))
    assert any("0/1" in cell for cell in cells), (
        f"a declared zero energy value lost its pair; cells were {cells}"
    )


# ---------------------------------------------------------------------------
# f. Acceptance 3 - no registry at all
# ---------------------------------------------------------------------------


def test_a_null_registry_mounts_and_names_the_route_that_did_not_answer(
    tmp_path: Path,
) -> None:
    """A panel sees ``data`` or null and never a reason (app.js:179-184).

    That asymmetry is why the panel must at least name the route: "did not
    answer" is the entire truth available to it, and saying nothing would read
    as an empty registry.
    """
    report = _mount(tmp_path, None)
    assert report["state"] == "mounted"
    assert report["threw"] is None
    text = _panel_text(report)
    assert ROUTE in text
    assert "did not answer" in text


def test_a_null_registry_renders_no_number_at_all(tmp_path: Path) -> None:
    """Zeros over a route that did not answer are a confident lie.

    A reader cannot tell "the registry holds no items" from "nobody asked" once
    a zero is on screen, so the panel renders no digit whatsoever in this state.
    """
    text = _panel_text(_mount(tmp_path, None))
    digits = tuple(char for char in text if char.isdigit())
    assert not digits, f"the panel invented numbers with no registry to read: {text!r}"


# ---------------------------------------------------------------------------
# g. The roster is bounded, and says so when it bounds
# ---------------------------------------------------------------------------


def test_a_large_registry_is_truncated_and_the_truncation_is_declared(
    tmp_path: Path,
) -> None:
    """An unbounded roster is a page that stops being readable at 2000 items."""
    items = [
        _item(
            f"Desc_Filler{index}_C",
            f"Filler {index}",
            "RF_SOLID",
            is_fluid=False,
            energy_value={"num": 1, "den": 1},
            sink_points=1,
        )
        for index in range(OVERSIZED)
    ]
    counts = {
        "items": OVERSIZED,
        "recipes": 0,
        "buildings": 0,
        "warnings": 0,
        "unknown_groups": 0,
    }
    report = _mount(
        tmp_path,
        _registry(
            items=items,
            recipes=[],
            buildings=[],
            warnings=[],
            unknown_groups=[],
            counts=counts,
        ),
    )
    text = _panel_text(report)
    assert f"{ROSTER_CAP} of {OVERSIZED}" in text, (
        f"the roster was cut without saying so; the panel read {text!r}"
    )
    keys = _field_texts(report, "item_key")
    assert len(keys) == ROSTER_CAP, f"the roster rendered {len(keys)} rows, not the declared cap"


def test_an_empty_collection_says_so_rather_than_rendering_nothing(tmp_path: Path) -> None:
    """An empty table and a table that failed to build look identical otherwise."""
    counts = {"items": 0, "recipes": 0, "buildings": 0, "warnings": 0, "unknown_groups": 0}
    report = _mount(
        tmp_path,
        _registry(
            items=[],
            recipes=[],
            buildings=[],
            warnings=[],
            unknown_groups=[],
            counts=counts,
        ),
    )
    assert report["state"] == "mounted"
    empties = panel_harness.nodes_matching(report, {"class": "empty"})
    assert empties, "an empty registry rendered no statement that it was empty"


# ---------------------------------------------------------------------------
# h. The panel touches only what the stand-in - and therefore the seam - has
# ---------------------------------------------------------------------------


def test_the_panel_builds_its_wide_tables_inside_their_own_scroller(
    tmp_path: Path,
) -> None:
    """A wide table scrolls inside its own container and not the page.

    ``app.css`` gives ``.scroll-x`` the overflow container and ``app.js`` gives
    it a tab stop exactly while it overflows (app.js:351-380). A table built
    outside one scrolls the whole page sideways instead.
    """
    report = _mount(tmp_path, _registry())
    tables = panel_harness.nodes_matching(report, {"tag": "table"})
    assert tables, "the panel built no table"
    boxes = panel_harness.nodes_matching(report, {"class": "scroll-x"})
    assert boxes, "the panel built a table with no horizontal scroller around it"
    parents = {row["parent"] for row in tables}
    box_indexes = {row["index"] for row in boxes}
    assert parents <= box_indexes, "a table was built outside a .scroll-x container"


def test_every_scroller_the_panel_builds_declares_its_own_label(tmp_path: Path) -> None:
    """Each scroller announces what it holds rather than announcing "Content".

    ``syncScrollRegions`` reads ``data-scroll-label`` and falls back to
    "Content", which names nothing a reader could act on.
    """
    report = _mount(tmp_path, _registry())
    boxes = panel_harness.nodes_matching(report, {"class": "scroll-x"})
    assert boxes
    unlabelled = tuple(
        row["index"] for row in boxes if not row["attributes"].get("data-scroll-label")
    )
    assert not unlabelled, f"scroller(s) at {unlabelled} would announce themselves as Content"
