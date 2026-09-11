"""CS-962 slice S4 - the Scope panel says where each figure came from, and what is absent.

WHY THIS PANEL EXISTS AT ALL. The dashboard is a self-diagnostic, and a reader
standing in front of it cannot otherwise tell whether a number was extracted
from the game's shipped document or read out of their own save. Those two have
different failure modes: a registry figure is wrong for everybody on this game
build, a world figure is wrong for this player only. A page that mixes them
without saying so is a page whose every number has to be taken on trust.

AND A GAP MUST BE NAMED RATHER THAN LEFT BLANK. The larger hazard is not a
mislabelled figure, it is an absent one. ``/api/world`` counts five collections
and lists none of them (``world.COUNT_KEYS``), ``/api/registry`` serves a
building as an identifier and a name and nothing else (``registry.BUILDING_KEYS``),
and node purity is not in a save file at all (``clockspeed/save/world.py``
``ResourceNode``). A reader who sees no power figure and is told nothing
concludes the power is zero. Non-negotiable 7 forbids exactly that confident
wrong answer in the data path; this panel is the same rule applied to the page.

WHAT THESE ARMS PIN, AND HOW THEY ARE MEANT TO GO RED
=====================================================

The panel makes two KINDS of claim and they are graded differently.

**Claims it DERIVES from a payload** - which routes the server reports as not
implemented, which panels registered, whether a registry and a world are
present - are graded by handing the mount a synthetic payload and reading the
claim back out of the DOM. Those arms fail if the panel stops reading.

**Claims it can only STATE**, because no payload carries them - that
``/api/world`` never lists its objects, that no power figure is served - are
graded in two halves. The panel's text is asserted to name the thing, AND the
source of truth is asserted still to withhold it. If ``registry.BUILDING_KEYS``
grows a power field, :func:`test_every_stated_gap_is_still_a_gap_at_its_source`
goes red and the sentence on the page is revisited, rather than quietly
becoming a lie. That is the only defence available against a doc-shaped fact:
a restated fact that nothing checks is a fact that will drift.

THE CS-500 DECISION, AND IT IS NOT AN ANALOGY
=============================================

The spec proposed asserting that the literal ``CS-500`` is absent from this
module, noting that the existing ban at ``test_web_assets.py`` covers only
``app.js`` and ``index.html``. THE ARM IS KEPT, and for a reason stronger than
consistency with a neighbouring file.

A panel is handed six payloads and nothing else (``app.js`` ``panelData``).
``blocked_by`` - the only place the blocking item id is ever written - lives on
the REFUSAL envelope (``contract.PAYLOAD_KEYS_REFUSAL``), which ``bodyData``
discards. The one payload that mentions the pending routes at all is
``data.health.endpoints``, whose values are narrowed to the two words of
``health.LIVENESS_WORDS`` and carry no id. So this panel CANNOT read the id.
Typing it would therefore not be a hardcode that merely duplicates the wire; it
would be a claim the page has no way of checking against the server, on a page
whose entire purpose is to report what it can and cannot check. The ban is the
panel's own honesty rule applied to itself, and the panel names the id's absence
as a gap instead of printing it.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.save.world import ResourceNode
from clockspeed.surface.api import contract, health, pending, registry, world
from tests.surface import panel_harness

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: The module under grade.
MODULE: Final = "panel_scope.js"

#: The seam module, read when an arm pins a name this panel reads off it.
SEAM: Final = "app.js"

#: The id the panel puts on the list of things the page cannot show.
GAPS_ID: Final = "scope-gaps"

#: The id the panel puts on the list of routes health reports as unbacked.
PENDING_ID: Final = "scope-pending"

#: The three headings. Spelled here because the panel is the thing being
#: graded and an arm that read them off the panel would assert nothing.
GROUP_HEADINGS: Final = ("REGISTRY-DERIVED", "WORLD-DERIVED", "HEALTH-DERIVED")

#: The world collections that are COUNTED and never LISTED - derived, so a
#: collection that starts being served drops out of the expectation by itself.
WORLD_COUNTED_ONLY: Final = tuple(sorted(set(world.COUNT_KEYS) - set(world.DATA_KEYS)))

#: The unlock members served as a size rather than as their contents. Asserted
#: below to still be members of :data:`world.UNLOCK_KEYS`, so a rename reddens.
UNLOCK_SIZES: Final = ("purchased_schematics", "recipes", "scanned_resources")

#: The envelope members a refusal carries and a success does not - which is
#: exactly the set ``bodyData`` drops before a panel ever sees a body.
ENVELOPE_ONLY: Final = tuple(sorted(contract.PAYLOAD_KEYS_REFUSAL - contract.PAYLOAD_KEYS_OK))

#: Every token the CANNOT-SHOW list must name. Derived where a derivation
#: exists; the rest are pinned at their source by
#: :func:`test_every_stated_gap_is_still_a_gap_at_its_source`.
GAP_TOKENS: Final = (
    *WORLD_COUNTED_ONLY,
    *UNLOCK_SIZES,
    *ENVELOPE_ONLY,
    "purity",
    "resource type",
    "produced_in",
    "power",
    "masked",
)

#: What a gap entry may name as the place the thing is absent from. A save file
#: is here because two of the gaps are not an endpoint's choice at all - the
#: bytes are not in the file.
GAP_SOURCES: Final = (*health.ENDPOINT_TEMPLATES, "the save file", "every route")


def _text(report: Mapping[str, Any], node_id: str) -> str:
    """The joined text of the one node carrying ``node_id``.

    Args:
        report: A report from :func:`panel_harness.mount`.
        node_id: The element id to find.

    Returns:
        That node's ``textContent``.
    """
    rows = panel_harness.nodes_matching(report, {"id": node_id})
    if len(rows) != 1:
        pytest.fail(
            f"{MODULE} built {len(rows)} nodes with id {node_id!r}; expected exactly one. "
            f"The tree held: {[row['tag'] + '#' + row['id'] for row in report['nodes']]}"
        )
    return str(rows[0]["text"])


def _entries(report: Mapping[str, Any], node_id: str) -> tuple[str, ...]:
    """The text of each direct child of the list carrying ``node_id``.

    Args:
        report: A report from :func:`panel_harness.mount`.
        node_id: The list element's id.

    Returns:
        One string per child row, in document order.
    """
    rows = panel_harness.nodes_matching(report, {"id": node_id})
    if len(rows) != 1:
        pytest.fail(f"{MODULE} built {len(rows)} nodes with id {node_id!r}; expected exactly one")
    parent = rows[0]["index"]
    return tuple(str(row["text"]) for row in report["nodes"] if row["parent"] == parent)


def _health(**overrides: Any) -> dict[str, Any]:
    """A synthetic ``/api/health`` data object carrying exactly its own keys.

    Args:
        **overrides: Members to replace on the default body.

    Returns:
        A mapping keyed by :data:`health.DATA_KEYS`.
    """
    body: dict[str, Any] = {
        "app_version": "0.0.0-test",
        "game_build_pin": "test-pin",
        "registry": health.PRESENT,
        "world": health.LOADED,
        "endpoints": {
            template: (
                health.NOT_LIVE
                if any(template == endpoint for _method, endpoint in pending.UNBACKED)
                else health.LIVE
            )
            for template in health.ENDPOINT_TEMPLATES
        },
    }
    body.update(overrides)
    return body


def _plant(tmp_path: Path, drop: str) -> Path:
    """Copy the shipped panel with the first line naming ``drop`` deleted.

    THE MUTATION IS A DELETION OF ONE SOURCE LINE, not a rewrite, because the
    fault being simulated is an author dropping an entry from the list - the
    exact regression the gap arm exists to catch.

    Args:
        tmp_path: Where the mutant is written.
        drop: A substring identifying the one line to remove.

    Returns:
        The mutant module's path.

    Raises:
        AssertionError: If the substring does not select exactly one line, in
            which case the mutation never applied and its survival would be
            indistinguishable from a passing test.
    """
    source = (panel_harness.WEB_DIR / MODULE).read_text(encoding="ascii")
    lines = source.split("\n")
    hits = [index for index, line in enumerate(lines) if drop in line]
    assert len(hits) == 1, f"{drop!r} selects {len(hits)} lines in {MODULE}; the mutation is unsafe"
    del lines[hits[0]]
    mutant = tmp_path / "planted_panel_scope.js"
    mutant.write_bytes("\n".join(lines).encode("ascii"))
    return mutant


def test_the_panel_names_all_three_derivation_groups(tmp_path: Path) -> None:
    """The page says which routes feed which panels, in one place.

    A reader cannot ask a figure where it came from, so the page has to say it
    unprompted. All three group headings appear, and each names the route it
    stands for.
    """
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=_health()))
    assert report["load_threw"] is None, report["load_threw"]
    assert report["state"] == panel_harness.STATE_MOUNTED, report["threw"]

    text = report["nodes"][0]["text"]
    missing = [heading for heading in GROUP_HEADINGS if heading not in text]
    assert not missing, f"{MODULE} names no derivation group {missing}"
    for route in ("/api/registry", "/api/solve", "/api/world", "/api/health"):
        assert route in text, f"{MODULE} names no source route {route}"


def test_the_panel_names_every_documented_gap_and_where_it_is_absent_from(
    tmp_path: Path,
) -> None:
    """Every entry of the CANNOT-SHOW list names a thing AND a place it is not.

    A gap with no source reads as an apology rather than a fact. Naming the
    route makes it checkable: a reader can send the request themselves and see
    the key is not there.
    """
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=_health()))
    gaps = _text(report, GAPS_ID)

    missing = [token for token in GAP_TOKENS if token not in gaps]
    assert not missing, f"the cannot-show list of {MODULE} never names {missing}"

    unsourced = [
        entry for entry in _entries(report, GAPS_ID) if not any(s in entry for s in GAP_SOURCES)
    ]
    assert not unsourced, f"these gap entries name no source: {unsourced}"


def test_deleting_one_gap_entry_turns_the_gap_arm_red(tmp_path: Path) -> None:
    """The gap arm is load-bearing: drop one entry and it fails.

    An arm that has never been red proves nothing. This plants the regression
    it exists to catch - an author quietly removing a line from the list - and
    asserts the check above would have caught it.
    """
    mutant = _plant(tmp_path, "produced_in")
    report = panel_harness.mount(tmp_path, mutant, panel_harness.null_payload(health=_health()))
    assert report["state"] == panel_harness.STATE_MOUNTED, report["threw"]
    gaps = _text(report, GAPS_ID)
    assert "produced_in" not in gaps, "the mutation did not apply; its survival would mean nothing"
    survivors = [token for token in GAP_TOKENS if token in gaps]
    assert "produced_in" not in survivors


def test_the_panel_lists_the_routes_health_reports_as_unbacked(tmp_path: Path) -> None:
    """The 501 rows are READ off the payload, never typed.

    ``data.health.endpoints`` is the only payload that mentions the unbacked
    routes. Feeding a body that marks a route live and another not implemented
    and reading the list back is what distinguishes a panel that reads from a
    panel that recites.
    """
    unbacked = tuple(endpoint for _method, endpoint in pending.UNBACKED)
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=_health()))
    listed = _entries(report, PENDING_ID)

    for endpoint in unbacked:
        assert any(endpoint in entry for entry in listed), f"{endpoint} is not listed as unbacked"
    for entry in listed:
        assert any(endpoint in entry for endpoint in unbacked), f"{entry!r} is not unbacked"

    live_everywhere = _health(endpoints=dict.fromkeys(health.ENDPOINT_TEMPLATES, health.LIVE))
    calm = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=live_everywhere))
    assert not _entries(calm, PENDING_ID), "a page where every route is live still lists one"


def test_the_panel_mounts_on_an_all_null_payload_and_says_health_did_not_answer(
    tmp_path: Path,
) -> None:
    """A scope note that cannot say what it knows is worse than useless.

    Under the seam grader's canned probes four of the six payloads are null,
    and all six can be. The panel must still mount, must still carry its gap
    list - which is prose and needs no payload - and must say plainly that the
    derived half is unavailable rather than printing an empty list as if it
    were an empty answer.
    """
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    assert report["load_threw"] is None, report["load_threw"]
    assert report["threw"] is None, report["threw"]
    assert report["state"] == panel_harness.STATE_MOUNTED

    text = report["nodes"][0]["text"]
    assert "/api/health" in text
    assert "did not answer" in text, f"{MODULE} does not say health was unavailable: {text!r}"
    for token in GAP_TOKENS:
        assert token in _text(report, GAPS_ID), f"the gap list lost {token!r} on a null payload"


def test_the_panel_never_types_the_blocking_item_id() -> None:
    """The id is unreadable from a payload, so printing it would be unverifiable.

    See the module docstring: ``blocked_by`` is a refusal-envelope member and
    ``bodyData`` drops the envelope, so no panel can obtain the id. The arm at
    ``test_web_assets.py::test_the_script_never_hardcodes_the_blocking_item_id``
    covers ``app.js`` and ``index.html`` only; this extends the same rule to
    this module on its own merits rather than by analogy.
    """
    source = (panel_harness.WEB_DIR / MODULE).read_text(encoding="ascii")
    assert pending.PENDING_BLOCKER not in source, f"{MODULE} hardcodes the blocking item id"
    assert "blocked_by" in ENVELOPE_ONLY, "blocked_by is no longer refusal-only; revisit the panel"


def test_the_panel_reads_the_seams_own_panel_list(tmp_path: Path) -> None:
    """The panels named on the page come from the seam, not from a typed list.

    ``server.py`` owns which panel modules are served; a second list here would
    be the copy that goes stale. The panel reads the registration array instead,
    so under this harness - where exactly one module is loaded - it names
    exactly one panel, and that is the honest answer.
    """
    seam = (panel_harness.WEB_DIR / SEAM).read_text(encoding="ascii")
    assert "panelEntries" in seam, "the seam no longer publishes panelEntries; the panel is blind"

    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=_health()))
    assert report["panel_id"] == "scope"
    listed = _entries(report, "scope-panels")
    assert listed == ("scope",), f"the panel list is {listed!r}, not the one module this run loaded"


def test_every_stated_gap_is_still_a_gap_at_its_source() -> None:
    """The half of the panel no payload can grade, pinned at the files that own it.

    These are the prose claims. Each assertion here is the condition that makes
    the corresponding sentence on the page true; when one fails, the sentence is
    wrong and must be rewritten rather than left to rot.
    """
    assert WORLD_COUNTED_ONLY, "no world collection is counted-only; the gap entry is stale"
    for name in WORLD_COUNTED_ONLY:
        assert name in world.COUNT_KEYS
        assert name not in world.DATA_KEYS

    for name in UNLOCK_SIZES:
        assert name in world.UNLOCK_KEYS, f"{name} is no longer an unlock member"

    assert registry.BUILDING_KEYS == ("key", "display_name"), (
        "a building now carries more than an identifier and a name; the no-power claim is stale"
    )
    assert "produced_in" in registry.RECIPE_KEYS

    assert set(contract.PAYLOAD_KEYS_REFUSAL) - set(contract.PAYLOAD_KEYS_OK) == set(ENVELOPE_ONLY)

    fields = {field.name for field in dataclasses.fields(ResourceNode)}
    assert not {name for name in fields if "purity" in name or "resource" in name}, (
        f"ResourceNode now carries node semantics {fields}; the save-has-no-purity claim is stale"
    )

    assert set(health.LIVENESS_WORDS) == {health.LIVE, health.NOT_LIVE}, (
        "health.endpoints carries more than two words; it may now carry the blocking id"
    )
