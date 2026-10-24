"""CS-1240: the Unmodelled content panel lists each class by stable id.

THE CLAIM. ``clockspeed/surface/web/panel_unmodelled.js`` renders
``data.world.unmodelled`` - the object ``clockspeed/surface/api/world.py``
builds from the save layer's sighting report - as one row per unmodelled class:
its stable id (the class path, as TEXT), its record count in this save, the
save it was first read in, and the reason it was skipped. It states the scope
of "first read" in words - since this server started - and says plainly when
nothing was checked, when everything resolved, and when the world did not
answer. It renders the rows in the order the body carries them and computes
nothing.

Every payload here is hand-written and synthetic; the panel is mounted under
node through ``tests.surface.panel_harness``, which is the seam grader's own
narrow stand-in DOM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from clockspeed.save.objects import REASON_CLASS_NOT_MODELLED
from clockspeed.surface.api import world as endpoint
from tests.surface import panel_harness

if TYPE_CHECKING:
    from pathlib import Path

#: The shipped module under test.
MODULE: Final = "panel_unmodelled.js"

#: Two synthetic class paths, namespaced by an invented mod root.
CLASS_X: Final = "/SightMod/Parts/Build_SightX.Build_SightX_C"
CLASS_Y: Final = "/SightMod/Parts/Build_SightY.Build_SightY_C"

#: The words the panel must use for the scope of "first read".
SCOPE_WORDS: Final = "since this server started"


def _text(report: Any) -> str:
    """The whole panel's text, joined by the stand-in from the tree.

    Args:
        report: A harness report.

    Returns:
        The text of node 0, which is the panel's own section.
    """
    return str(report["nodes"][0]["text"])


def _mount(tmp_path: Path, data: Any) -> Any:
    """Mount the panel and assert it mounted rather than failing.

    Args:
        tmp_path: Scratch directory.
        data: The payload.

    Returns:
        The report.
    """
    report = panel_harness.mount(tmp_path, MODULE, data)
    assert report["load_threw"] is None, report["load_threw"]
    assert report["threw"] is None, report["threw"]
    assert report["state"] == "mounted"
    return report


def _entry(stable_id: object, count: object, first_seen: object) -> dict[str, object]:
    """One listed class, shaped as ``world.UNMODELLED_CLASS_KEYS`` names it.

    Args:
        stable_id: The class path.
        count: The record count.
        first_seen: The first-read ordinal.

    Returns:
        The entry.
    """
    return {
        "stable_id": stable_id,
        "count": count,
        "reason": REASON_CLASS_NOT_MODELLED,
        "first_seen": first_seen,
    }


def _world(
    classes: list[dict[str, object]],
    *,
    this_save: int = 1,
    saves_read: int = 1,
    checked: bool = True,
) -> dict[str, object]:
    """A ``data.world`` carrying an ``unmodelled`` object and nothing else needed.

    Args:
        classes: The listed classes.
        this_save: This save's ordinal.
        saves_read: How many saves were read.
        checked: Whether a property map was supplied.

    Returns:
        The world payload.
    """
    unmodelled = {
        "scope": endpoint.FIRST_SEEN_SCOPE,
        "checked": checked,
        "this_save": this_save,
        "saves_read": saves_read,
        "classes": classes,
    }
    assert tuple(unmodelled) == endpoint.UNMODELLED_KEYS
    return {"unmodelled": unmodelled, "contains_unmodeled_content": bool(classes)}


def _rows(report: Any) -> list[list[str]]:
    """Each body row's cell texts, in document order.

    Args:
        report: A harness report.

    Returns:
        One list of cell texts per ``tr`` under a ``tbody``.
    """
    nodes = report["nodes"]
    bodies = {row["index"] for row in nodes if row["tag"] == "TBODY"}
    rows = [row for row in nodes if row["tag"] == "TR" and row["parent"] in bodies]
    return [[str(cell["text"]) for cell in nodes if cell["parent"] == row["index"]] for row in rows]


def test_the_panel_mounts_an_all_null_payload_and_says_the_world_did_not_answer(
    tmp_path: Path,
) -> None:
    """Null is the ordinary case before a world loads; it must not throw."""
    report = _mount(tmp_path, panel_harness.null_payload())
    text = _text(report)
    assert "Unmodelled content" in text
    assert "did not answer" in text
    assert _rows(report) == []


def test_one_unknown_class_is_listed_by_stable_id_with_its_count_and_first_seen_save(
    tmp_path: Path,
) -> None:
    """Acceptance 1 on the page: the class path, its count, and its save."""
    data = panel_harness.null_payload(world=_world([_entry(CLASS_X, 2, 1)]))
    report = _mount(tmp_path, data)
    assert _rows(report) == [[CLASS_X, "2", "this save", REASON_CLASS_NOT_MODELLED]]


def test_a_class_first_read_in_an_earlier_save_names_that_save(tmp_path: Path) -> None:
    """X was first read two saves ago; Y first appeared in this one."""
    data = panel_harness.null_payload(
        world=_world([_entry(CLASS_X, 3, 1), _entry(CLASS_Y, 1, 3)], this_save=3, saves_read=3)
    )
    report = _mount(tmp_path, data)
    firsts = [row[2] for row in _rows(report)]
    assert firsts == ["save 1 of 3", "this save"]


def test_the_rows_keep_the_order_the_body_carries(tmp_path: Path) -> None:
    """The save layer orders by stable id; the panel re-sorts nothing."""
    data = panel_harness.null_payload(world=_world([_entry(CLASS_Y, 1, 1), _entry(CLASS_X, 1, 1)]))
    report = _mount(tmp_path, data)
    ids = [row[0] for row in _rows(report)]
    assert ids == [CLASS_Y, CLASS_X]


def test_the_scope_of_first_read_is_stated_in_words(tmp_path: Path) -> None:
    """A reader is told the ordinals count saves read since this server started."""
    data = panel_harness.null_payload(
        world=_world([_entry(CLASS_X, 1, 1)], this_save=2, saves_read=2)
    )
    text = _text(_mount(tmp_path, data))
    assert SCOPE_WORDS in text
    assert "read 2 of 2" in text


def test_an_unchecked_world_says_nothing_was_checked_and_lists_nothing(tmp_path: Path) -> None:
    """No property map is not "everything resolved"."""
    data = panel_harness.null_payload(world=_world([], checked=False))
    report = _mount(tmp_path, data)
    text = _text(report)
    assert "not checked" in text
    assert "resolved" not in text
    assert _rows(report) == []


def test_a_checked_world_with_nothing_unmodelled_says_every_class_resolved(
    tmp_path: Path,
) -> None:
    """The empty case is named, not left as an empty table."""
    report = _mount(tmp_path, panel_harness.null_payload(world=_world([])))
    assert "every class in this save resolved" in _text(report)
    assert _rows(report) == []


def test_a_malformed_entry_is_withheld_never_rendered_as_something_else(tmp_path: Path) -> None:
    """A non-string id, a fractional count and a missing ordinal each read withheld."""
    data = panel_harness.null_payload(world=_world([_entry(7, 1.5, None)]))
    report = _mount(tmp_path, data)
    assert _rows(report) == [["withheld", "withheld", "withheld", REASON_CLASS_NOT_MODELLED]]


def test_a_class_path_with_markup_renders_as_text(tmp_path: Path) -> None:
    """A mod-authored path is TEXT: the panel builds nodes and never parses markup."""
    planted = "/SightMod/<b>Bold</b>.Bold_C"
    data = panel_harness.null_payload(world=_world([_entry(planted, 1, 1)]))
    report = _mount(tmp_path, data)
    bold = sum(1 for row in report["nodes"] if row["tag"] == "B")
    assert bold == 0
    assert _rows(report)[0][0] == planted
