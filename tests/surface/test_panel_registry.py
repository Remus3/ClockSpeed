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
     (``clockspeed/surface/api/registry.py::_amount``). The pair is the truth and
     is shown as the pair; a decimal may sit beside it ONLY labelled as an
     approximation. Non-negotiable 6 does not stop at the browser.
  2. ABSENT IS NOT ZERO. ``energy_value`` and ``sink_points`` are both nullable
     (``clockspeed/data/registry.py::Item`` and
     ``clockspeed/surface/api/registry.py::_optional_amount``), and the data layer states
     that None and zero are different facts. A confident zero over an absent
     measurement is the one unacceptable rendering.
  3. A NULL PAYLOAD RENDERS WITHOUT THROWING AND WITHOUT INVENTING NUMBERS.
     Under the seam grader's canned probes ``data.registry`` is null, and a
     throw would redden an arm this slice does not own.

THE BASELINE PIN, AND WHY IT LIVES HERE.
``tests/surface/test_panel_seam.py::test_the_network_detector_fires_on_every_primitive_it_claims``
takes ``PANEL_MODULES[0]`` as the CLEAN BASELINE for the network detector that
grades all four panels, and sorted, that is this slice's module. The ordering
is alphabetical and no arm in that
file declares it. If a module sorting before ``panel_registry.js`` is ever
added, the baseline moves silently to a file nobody checked. Worse, the baseline
is a CONCATENATION PREFIX: a sink in the baseline makes the fire-check compute
an empty set and PASS while grading nothing - a gate that skips its checks
reporting PASS, one layer down. The pin below makes that move visible.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Final

from clockspeed.surface.api import contract
from clockspeed.surface.api import registry as api_registry
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
UNKNOWN_GROUP: Final = "FGBuildableWeirdThing"

#: The warning fixture's code, spelled the way the only thing that builds one
#: spells it. Every member of the closed set whose first entry is
#: ``clockspeed/data/registry.py::WARN_DUPLICATE_CLASS_NAME`` is lowercase and
#: hyphenated, so the underscored synthetic this constant used to carry was a
#: fixture that disagreed with its producer - and a fixture that disagrees with
#: its producer is what lets a guard calibrated to the producer look wrong.
WARNING_CODE: Final = "empty-display-name"
WARNING_SUBJECT: Final = "Desc_Mystery_C"

#: The warning fixture's detail, and the one every renders-in-full arm reads.
WARNING_DETAIL: Final = "the entry declared no display name"

#: What the panel substitutes for a field whose shape it does not accept. The
#: SAME marker ``clockspeed/surface/web/panel_warnings.js`` uses, deliberately:
#: the two panels render the same kind of record into the same document, and a
#: reader should not have to learn a second vocabulary to read the second table.
WITHHELD: Final = "[withheld - unexpected shape]"

#: Two characters spelled as code points, so that no tracked line in this file
#: carries a path-shaped literal. Non-negotiable 3 is a rule about the tracked
#: BYTE and not about the author's intent, and the pre-commit gate reads the
#: byte. Everything hostile below is assembled at runtime from these.
BACKSLASH: Final = chr(92)
COLON: Final = chr(58)

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
    (``clockspeed/surface/api/registry.py::_amount``), not off prose. The first
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
                "detail": WARNING_DETAIL,
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
    (``tests/surface/panel_harness.py::_HARNESS_SOURCE``), so its ``textContent`` is the
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


def _windows_path() -> str:
    """A drive-rooted path, assembled at runtime and never written down.

    The account segment is the word PLAYER and is nobody's account name. What
    the arms grade is the SHAPE, because the shape is what a leak would wear:
    the drive marker and the separator are the two characters that make a
    string on this platform a path rather than a token.
    """
    return BACKSLASH.join(("C" + COLON, "Users", "PLAYER", "AppData", "world.sav"))


def _object_path() -> str:
    """A publisher-owned Unreal object path, which is a LEGITIMATE subject.

    ``clockspeed/data/blobs.py::parse_class_paths`` returns whatever sits
    between two double quotes VERBATIM, and
    ``clockspeed/data/registry.py::_class_name_from_path`` returns the WHOLE
    path when the token carries no ``.`` separator at all - so a slash-bearing
    subject is a real registry reading and not a defect. An arm that only
    withheld things would be satisfied by a panel that withheld this too.
    """
    return "/" + "/".join(("Script", "FactoryGame", "FGBuildableAutomatedWorkBench"))


def _warning(**overrides: Any) -> dict[str, Any]:
    """One warning row, keyed exactly as ``registry.WARNING_KEYS`` spells it."""
    row: dict[str, Any] = {
        "code": WARNING_CODE,
        "subject": WARNING_SUBJECT,
        "detail": WARNING_DETAIL,
        "count": 1,
    }
    row.update(overrides)
    return row


def _count_values(report: Mapping[str, Any]) -> dict[str, str]:
    """The counts grid as label to rendered value, read off the grid itself.

    ANCHORED TO THE NODE THAT CARRIES THE VALUES rather than to whole-panel
    text, and that is the whole point of this helper. An arm that searched the
    panel's text for the five labels could not tell a right count from a wrong
    one at all: every label still appears while every number beside it reads
    zero. Reading the ``dd`` beside each ``dt`` is what makes the assertion
    about the count rather than about the word next to it.

    Returns:
        Each label mapped to the text of the ``dd`` beside it, or an empty
        mapping when the panel built no grid at all.
    """
    grids = panel_harness.nodes_matching(report, {"tag": "dl", "id": "registry-counts"})
    if not grids:
        return {}
    rows = report["nodes"]
    boxes = sorted(row["index"] for row in rows if row["parent"] == grids[0]["index"])
    pairs: dict[str, str] = {}
    for box in boxes:
        label: str | None = None
        for row in rows:
            if row["parent"] != box:
                continue
            if str(row["tag"]).upper() == "DT":
                label = str(row["text"])
            elif str(row["tag"]).upper() == "DD" and label is not None:
                pairs[label] = str(row["text"])
    return pairs


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


def test_the_panel_renders_the_five_count_values(tmp_path: Path) -> None:
    """``COUNT_KEYS`` is a cheap header over collections the body also carries.

    WIDENED FROM A LABEL SEARCH. The arm this replaces asserted only that the
    five lowercase labels appeared somewhere in the whole-panel text, so no arm
    anywhere in the repo asserted that a count VALUE reached the document. Both
    halves of that were measured against planted mutants rather than argued:

      - replacing every rendered count with the digit zero leaves the old arm
        GREEN, because the five labels are still there beside the wrong
        numbers. That is the mutant this arm exists to kill, and it does.
      - deleting the counts grid outright does NOT survive the old arm, which
        is worth recording because the refutation that prompted this widening
        said it did. The reasoning offered was that each label is a substring
        of a table heading such as "Registry items" - but that string is the
        value of a ``data-scroll-label`` ATTRIBUTE and never text, and the
        ``h3`` titles beside it are capitalised. The old arm was vacuous about
        values, not about the grid's existence.

    This arm dies on both mutants, because it reads the values off the grid.
    """
    values = _count_values(_mount(tmp_path, _registry()))
    assert values == {
        "items": "2",
        "recipes": "1",
        "buildings": "1",
        "warnings": "1",
        "unknown groups": "1",
    }, f"the counts grid published {values}"


def test_the_panel_renders_a_legitimate_warning_in_full(tmp_path: Path) -> None:
    """A flagged-and-skipped piece of content is useless without its subject.

    NARROWED FROM ``renders_each_warning_in_full``, which pinned an UNGUARDED
    rendering: the panel put ``code``, ``subject`` and ``detail`` on the page
    through a bare string check, so a subject shaped like a filesystem path
    rendered here in full while ``panel_warnings.js`` withheld the same value
    on the same page and in the same screenshot. The claim had to narrow to
    survive the repair - but it narrowed to a LEGITIMATE warning rather than
    away, because a panel that withholds everything is the other way to fail
    this arm and would have passed a weaker successor.
    """
    rendered = {
        "code": _field_texts(_mount(tmp_path, _registry()), "warning_code"),
        "subject": _field_texts(_mount(tmp_path, _registry()), "warning_subject"),
        "detail": _field_texts(_mount(tmp_path, _registry()), "warning_detail"),
    }
    assert rendered == {
        "code": (WARNING_CODE,),
        "subject": (WARNING_SUBJECT,),
        "detail": (WARNING_DETAIL,),
    }, f"the warning row published {rendered}"


def test_the_panel_names_each_unknown_group(tmp_path: Path) -> None:
    text = _panel_text(_mount(tmp_path, _registry()))
    assert UNKNOWN_GROUP in text


# ---------------------------------------------------------------------------
# c2. The warning stream is guarded, because the DOM is where a leak becomes an
#     image file. See the guard's own doctrine in the module under grade.
# ---------------------------------------------------------------------------


def test_a_subject_shaped_like_a_filesystem_path_is_withheld(tmp_path: Path) -> None:
    """The refutation this section exists to discharge.

    ``panel_warnings.js`` withholds a subject wearing this shape and this panel
    used to render it in full - same document, same screenshot out of
    ``tools/dashboard_probe.py``. A path on this machine carries the Windows
    account name, so non-negotiables 3, 11 and 12 are what the inconsistency
    put at stake, and the weaker of two sinks is the one that decides.
    """
    body = _registry(warnings=[_warning(subject=_windows_path())])
    rendered = _field_texts(_mount(tmp_path, body), "warning_subject")
    assert rendered == (WITHHELD,), f"the panel published the subject as {rendered}"


def test_a_detail_carrying_a_path_separator_is_withheld(tmp_path: Path) -> None:
    """A detail is authored prose, and no authored line here carries a separator.

    Every detail the producer builds is an f-string over the module's own
    ``KEY_*`` constants, plus the four closed reasons whose first is
    ``clockspeed/data/docs_extract.py::REASON_NOT_A_MAPPING``. Not one of them
    holds a slash, a backslash or a colon, so refusing all three costs the
    panel nothing it can legitimately show.
    """
    body = _registry(warnings=[_warning(detail="skipped " + _windows_path())])
    rendered = _field_texts(_mount(tmp_path, body), "warning_detail")
    assert rendered == (WITHHELD,), f"the panel published the detail as {rendered}"


def test_a_code_outside_the_closed_set_shape_is_withheld(tmp_path: Path) -> None:
    """A code is a lowercase hyphenated token and the set of them is closed."""
    body = _registry(warnings=[_warning(code="C" + COLON + BACKSLASH + "boom")])
    rendered = _field_texts(_mount(tmp_path, body), "warning_code")
    assert rendered == (WITHHELD,), f"the panel published the code as {rendered}"


def test_a_publisher_owned_object_path_subject_still_renders(tmp_path: Path) -> None:
    """THE ARM THAT KEEPS THE REPAIR HONEST, and it is not a formality.

    A copy of ``panel_warnings.js``'s subject guard would refuse this value:
    its token set excludes the forward slash and its one slash-bearing
    exception admits digits over digits only. But the registry stream carries
    slash-bearing subjects legitimately -
    ``clockspeed/data/registry.py::_class_name_from_path`` returns the WHOLE
    path when the token holds no ``.`` - and
    ``clockspeed/data/blobs.py::parse_class_paths`` says in as many words that
    dropping such a token erases the evidence it was ever present. Withholding
    it here would hide exactly what flag-and-skip exists to publish.
    """
    body = _registry(warnings=[_warning(subject=_object_path())])
    rendered = _field_texts(_mount(tmp_path, body), "warning_subject")
    assert rendered == (_object_path(),), f"the panel published the subject as {rendered}"


def test_a_withheld_field_still_shows_which_warning_fired(tmp_path: Path) -> None:
    """A refusal is rendered, not dropped.

    Silently omitting the row would make a refusal indistinguishable from an
    absence, and the reader would have no way to learn that anything was
    flagged at all. The code and the count survive a withheld subject.
    """
    body = _registry(warnings=[_warning(subject=_windows_path(), count=7)])
    report = _mount(tmp_path, body)
    surviving = (
        _field_texts(report, "warning_code"),
        _field_texts(report, "warning_count"),
    )
    assert surviving == ((WARNING_CODE,), ("7",)), f"the row published {surviving}"


def test_an_unknown_group_name_shaped_like_a_path_is_withheld(tmp_path: Path) -> None:
    """The sibling case sharing the root cause, and it is on the same page.

    ``unknown_groups`` is the second publisher-owned token stream this panel
    renders, it reaches the document through the same bare string check the
    warning row used, and ``panel_warnings.js`` runs its own unknown groups
    through the token guard. Repairing one and not the other would have left
    the page's weakest sink exactly where it was.
    """
    body = _registry(unknown_groups=[_windows_path(), UNKNOWN_GROUP])
    rendered = _field_texts(_mount(tmp_path, body), "unknown_group")
    assert rendered == (WITHHELD, UNKNOWN_GROUP), f"the group list published {rendered}"


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
    """None and ``Fraction(0)`` are different facts.

    Stated by
    ``clockspeed/surface/api/registry.py::_optional_amount``.
    """
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


# ---------------------------------------------------------------------------
# i. The common-mode pin - the fixture is bound to the ENDPOINT, not to a spec
#
# WHY THIS SECTION EXISTS, AND WHY IT IS NOT CEREMONY. Every fixture above was
# hand-typed from a planner-authored spec file in a scratchpad, and so was the
# panel it grades. That is one shared input, not two independent ones. If a key
# is misspelled in that spec, the fixture carries the misspelling, the panel
# reads the misspelling, the arm asserts against the misspelling, AND THE SUITE
# IS GREEN - while the live page renders "not declared" forever and nothing
# ever goes red. CLAUDE.md section 5 names the shape exactly: agreement between
# two agents is not evidence, because two agents deriving from the same stale
# doc are wrong the same way. The cure is to test the SHARED INPUT, which is
# what the four arms below do - they bind both the fixture and the panel to
# ``clockspeed/surface/api/registry.py``, which is the thing that actually
# serves the bytes.
#
# EQUALITY, NEVER SUBSET. A subset check passes forever while a key the
# endpoint GAINS goes unfixtured and unrendered - the page silently stops
# showing a new field and no arm notices. Each assertion below is an equality.
# ---------------------------------------------------------------------------

#: Exactly the two keys ``clockspeed/surface/api/contract.py::rational`` puts on
#: an exact ratio. Derived by CALLING the transcriber rather than by retyping
#: its output, so a rename there reddens here rather than in a browser.
RATIONAL_KEYS: Final = frozenset(contract.rational(Fraction(10, 3)))

#: The bracket-subscript reads ``panel_registry.js`` performs on a payload.
#: The leading character class is what separates a SUBSCRIPT from a bare array
#: literal: the module builds a one-element header list spelled ``["group"]``
#: at panel_registry.js:465, which reads no key at all and must not be counted
#: as one.
SUBSCRIPT: Final = re.compile(r'[A-Za-z0-9_)\]]\["([a-z_]+)"\]')


def _module_source() -> str:
    """The shipped panel asset, as text.

    Returns:
        The source of the module under grade.
    """
    return str((panel_harness.WEB_DIR / MODULE).read_text(encoding="ascii"))


def test_the_fixture_body_is_keyed_exactly_as_the_endpoint_keys_one() -> None:
    """Every level of the canonical fixture equals the endpoint's own key tuple.

    THE ARM WALKS DOWN, not just across the top. A fixture carrying
    ``warnings: [...]`` against an endpoint carrying ``warnings: {"items": []}``
    is the identical defect one level down and is equally invisible from the
    top-level key set alone, so each nested record is checked against the tuple
    ``clockspeed/surface/api/registry.py`` publishes for it.
    """
    body = _registry()
    assert set(body) == set(api_registry.DATA_KEYS), (
        "the fixture's top-level keys are not the ones /api/registry serves"
    )
    # THE CONTAINER TYPE IS CHECKED BEFORE ITS KEYS. A fixture carrying
    # ``counts: [{...}]`` against an endpoint carrying ``counts: {...}`` is the
    # nesting half of this defect, and comparing key sets first would raise a
    # TypeError that names a Python type rather than the wire shape that drifted.
    assert isinstance(body["counts"], dict), (
        f"counts is served as a mapping (registry.py:293-300), not {type(body['counts']).__name__}"
    )
    for collection in ("items", "recipes", "buildings", "warnings", "unknown_groups"):
        assert isinstance(body[collection], list), (
            f"{collection} is served as a list (registry.py:313-320),"
            f" not {type(body[collection]).__name__}"
        )
    assert set(body["counts"]) == set(api_registry.COUNT_KEYS), (
        "the fixture's counts block is not keyed the way the endpoint counts"
    )
    for item in body["items"]:
        assert set(item) == set(api_registry.ITEM_KEYS), f"item {item.get('key')!r}"
    for recipe in body["recipes"]:
        assert set(recipe) == set(api_registry.RECIPE_KEYS), f"recipe {recipe.get('key')!r}"
        for field in ("inputs", "outputs", "produced_in"):
            assert isinstance(recipe[field], list), f"{field} is served as a list"
        for side in list(recipe["inputs"]) + list(recipe["outputs"]):
            assert isinstance(side, dict), f"a recipe side is a mapping, not {type(side).__name__}"
            assert set(side) == set(api_registry.RECIPE_IO_KEYS), f"side {side!r}"
            assert isinstance(side["amount"], dict), "an amount is a num/den mapping"
            assert set(side["amount"]) == RATIONAL_KEYS, f"amount of {side!r}"
        assert isinstance(recipe["duration"], dict), "a duration is a num/den mapping"
        assert set(recipe["duration"]) == RATIONAL_KEYS, "duration is not a num/den pair"
    for building in body["buildings"]:
        assert set(building) == set(api_registry.BUILDING_KEYS), f"building {building!r}"
    for warning in body["warnings"]:
        assert set(warning) == set(api_registry.WARNING_KEYS), f"warning {warning!r}"
    for group in body["unknown_groups"]:
        assert isinstance(group, str), "an unknown group is a bare name (registry.py:319)"


def test_every_nullable_measurement_in_the_fixture_is_a_pair_or_absent() -> None:
    """``energy_value`` is a num/den pair or None - never a bare number.

    ``registry.py:189-202`` returns ``contract.rational`` or None, so a fixture
    carrying a bare int would be grading the panel against a shape the wire
    cannot produce, and the absent-is-not-zero arms would be proving nothing.
    """
    for item in _registry()["items"]:
        energy = item["energy_value"]
        assert energy is None or isinstance(energy, dict), (
            f"energy of {item['key']!r} is a num/den mapping or None,"
            f" never a bare {type(energy).__name__}"
        )
        assert energy is None or set(energy) == RATIONAL_KEYS, f"energy of {item['key']!r}"
        points = item["sink_points"]
        assert points is None or isinstance(points, int), f"sink points of {item['key']!r}"


def test_the_panel_reads_no_wire_key_the_endpoint_does_not_serve() -> None:
    """Every key ``panel_registry.js`` subscripts is one the endpoint publishes.

    THE OTHER HALF OF THE PIN. The arm above binds the FIXTURE to the endpoint;
    this one binds the PANEL to it. Without this half a panel could read a key
    the endpoint never serves and render "not declared" on the live page while
    every fixture arm stayed green, because no fixture would carry the key
    either. The closing assertion runs the other way - every top-level key the
    endpoint serves must actually be read, so a field the panel quietly stops
    rendering reddens instead of vanishing.
    """
    served = (
        set(api_registry.DATA_KEYS)
        | set(api_registry.COUNT_KEYS)
        | set(api_registry.ITEM_KEYS)
        | set(api_registry.RECIPE_KEYS)
        | set(api_registry.RECIPE_IO_KEYS)
        | set(api_registry.BUILDING_KEYS)
        | set(api_registry.WARNING_KEYS)
        | RATIONAL_KEYS
        | {PANEL_ID}
    )
    read = set(SUBSCRIPT.findall(_module_source()))
    assert read, "the subscript scan matched nothing, so it graded nothing"
    assert read <= served, f"the panel reads key(s) /api/registry never serves: {read - served}"
    assert set(api_registry.DATA_KEYS) <= read, (
        f"the panel never reads: {set(api_registry.DATA_KEYS) - read}"
    )


def test_the_panels_count_roster_is_exactly_the_endpoints_count_keys() -> None:
    """``COUNT_LABELS`` names every counted collection and invents none.

    The roster is a literal table inside the asset, so it is the one place the
    panel can drift from ``COUNT_KEYS`` without any subscript changing - the
    scan above reads ``record[COUNT_LABELS[index][0]]`` and learns nothing from
    it. Equality and in order, so a sixth count the endpoint gains reddens here
    rather than going unrendered.
    """
    marker = "var COUNT_LABELS = ["
    source = _module_source()
    assert marker in source, "panel_registry.js no longer declares COUNT_LABELS"
    roster = re.findall(r'\["([a-z_]+)",', source.split(marker, 1)[1].split("];", 1)[0])
    assert tuple(roster) == tuple(api_registry.COUNT_KEYS), (
        f"the panel counts {roster} where the endpoint counts {list(api_registry.COUNT_KEYS)}"
    )
