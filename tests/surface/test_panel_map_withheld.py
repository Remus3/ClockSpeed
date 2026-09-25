"""CS-1189 - the Map panel names every item total ``/api/map`` withheld.

WHY THIS FILE EXISTS. ``/api/map`` withholds an item total whose key the
registry's closed vocabulary does not name, and withholds every total when there
is no registry at all, and says so with ``item-key-unknown`` or
``registry-unavailable``. The panel printed a warning under WHAT I HAVE only when
the served list was EMPTY, so with one known item and one withheld one the
withheld row vanished and its warning appeared nowhere - a silently partial
answer, which ``CLAUDE.md`` section 3 rule 7 forbids ("flagged and skipped,
never silently wrong"). The arms below mount the panel against canned bodies
with a known row served beside each warning and assert the page names the
warning's code and its count in the WHAT I HAVE list.

The canned bodies, the mount and the tree readers are
``tests/surface/test_panel_map.py``'s own, imported rather than copied, so these
arms answer to the same row guard as every other panel arm.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import map as map_endpoint
from tests.surface import panel_harness
from tests.surface.test_panel_map import INVENTORY_ID, MODULE, _entries, _mount, _text

if TYPE_CHECKING:
    from pathlib import Path

#: How many totals the canned warning says were withheld. Distinct from every
#: other number the canned body carries, so its appearance proves the count.
WITHHELD_COUNT: Final = 37

#: The one item row the canned body serves, and the one line a withheld warning
#: adds beside it.
SERVED_ROWS: Final = 1
WITH_ONE_WITHHELD_LINE: Final = 2


def _withheld(code: str) -> dict[str, object]:
    """One endpoint-raised warning, in the ``WARNING_KEYS`` shape.

    Args:
        code: The warning code.

    Returns:
        The warning row.
    """
    return {"source": map_endpoint.SOURCE_MAP, "code": code, "count": WITHHELD_COUNT}


def test_an_unknown_key_warning_is_named_beside_a_served_item(tmp_path: Path) -> None:
    """The refuted case: one known row served, the withheld one named, count included."""
    code = map_endpoint.WARN_ITEM_KEY_UNKNOWN
    report = _mount(tmp_path, warnings=[_withheld(code)])
    rows = _entries(report, INVENTORY_ID)
    assert len(rows) == WITH_ONE_WITHHELD_LINE, f"rows under WHAT I HAVE: {rows}"
    assert "Iron Ore" in rows[0], f"the served item moved: {rows}"
    assert code in rows[1], f"the withheld warning is not named: {rows}"
    assert str(WITHHELD_COUNT) in rows[1], f"the withheld count is not printed: {rows}"


def test_a_registry_unavailable_warning_is_named_beside_a_served_item(tmp_path: Path) -> None:
    """Every total withheld for want of a vocabulary is named, whatever else was served."""
    code = map_endpoint.WARN_REGISTRY_UNAVAILABLE
    report = _mount(tmp_path, warnings=[_withheld(code)])
    rows = _entries(report, INVENTORY_ID)
    assert len(rows) == WITH_ONE_WITHHELD_LINE, f"rows under WHAT I HAVE: {rows}"
    assert code in rows[1], f"the registry warning is not named: {rows}"
    assert str(WITHHELD_COUNT) in rows[1], f"the warning's count is not printed: {rows}"


def test_an_empty_inventory_still_names_the_withheld_count(tmp_path: Path) -> None:
    """The empty case keeps its disclaimer AND gains the withheld line with its count."""
    code = map_endpoint.WARN_ITEM_KEY_UNKNOWN
    report = _mount(tmp_path, inventory=[], warnings=[_withheld(code)])
    printed = _text(report, INVENTORY_ID)
    assert "not a claim" in printed, f"the empty inventory is not disclaimed: {printed!r}"
    assert "withheld" in printed, f"the withheld totals are not named: {printed!r}"
    assert str(WITHHELD_COUNT) in printed, f"the withheld count is not printed: {printed!r}"


def test_an_unrelated_warning_adds_no_line_under_what_i_have(tmp_path: Path) -> None:
    """CONTROL: only the two withholding codes are printed there.

    So the arms above are not satisfied by a panel that dumps every warning
    into the list.
    """
    report = _mount(tmp_path, warnings=[_withheld("node-semantics-unavailable")])
    rows = _entries(report, INVENTORY_ID)
    assert len(rows) == SERVED_ROWS, f"an unrelated warning was listed: {rows}"


def test_the_panel_spells_both_codes_exactly_as_the_endpoint_publishes_them() -> None:
    """A code the panel spelled differently would never match the wire."""
    source = (panel_harness.WEB_DIR / MODULE).read_text(encoding="utf-8")
    for code in (map_endpoint.WARN_ITEM_KEY_UNKNOWN, map_endpoint.WARN_REGISTRY_UNAVAILABLE):
        assert '"' + code + '"' in source, f"{MODULE} does not name {code!r}"
