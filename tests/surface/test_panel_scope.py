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

A CLAIM ABOUT THE PAGE IS GRADED AGAINST THE PAGE
=================================================

This module shipped with a sentence saying the page could not show a refusal's
``reason``, ``detail`` or ``blocked_by``. All three were on screen: ``app.js``
prints ``blocked_by`` into the endpoint table and a refusal ``detail`` into the
World note, and the solve bench prints all three, because the seam hands that
one callback the whole envelope rather than the reduced body. The arm that was
supposed to catch it asserted only that the token ``blocked_by`` APPEARED in the
list, which grades whether a sentence was printed and never whether it was true.

So :func:`test_no_envelope_member_the_seam_prints_is_called_absent` reads the
shipped assets and derives, in both directions, which envelope members this page
renders. A member the seam prints may not be called absent; a member it prints
nowhere must be named. A renderer that starts printing one turns that arm red.

THE CS-500 DECISION, AND IT IS NOT AN ANALOGY
=============================================

The spec proposed asserting that the literal ``CS-500`` is absent from this
module, noting that the existing ban at ``test_web_assets.py`` covers only
``app.js`` and ``index.html``. THE ARM IS KEPT, and for a reason stronger than
consistency with a neighbouring file.

A repaint hands a panel six reduced payloads and one action door (``app.js``
``panelData``), and ``bodyData`` has already dropped the envelope
``blocked_by`` rides on (``contract.PAYLOAD_KEYS_REFUSAL``). The one payload
that mentions the pending routes at all is ``data.health.endpoints``, whose
values are narrowed to the two words of ``health.LIVENESS_WORDS`` and carry no
id. The page does show the id - ``app.js`` reads it straight off each probe -
but no repaint hands one to THIS panel, and a panel may issue no request of its
own, so typing the id here would be a claim this module has no way of checking
against the server, on a panel whose entire purpose is to report what it can and
cannot check. The ban is the panel's own honesty rule applied to itself.
"""

from __future__ import annotations

import dataclasses
import re
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

#: The id the panel puts on the list of panels registered on this page.
PANELS_ID: Final = "scope-panels"

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

#: The panel modules that hold a request door, and therefore the only ones with
#: a refusal envelope of their own to render. Sorted, because ``_renders``
#: returns its matches sorted and an order written by hand here would be a
#: second fact about the same set.
REFUSAL_PRINTING_BENCHES: Final = ("panel_optimize.js", "panel_power.js", "panel_solve.js")

#: Every browser asset the page loads, read off disk rather than listed, so an
#: asset added to the directory is scanned without an edit here.
WEB_ASSETS: Final = tuple(sorted(path.name for path in panel_harness.WEB_DIR.glob("*.js")))

#: A JavaScript comment of either kind. The panel makes claims about what the
#: page RENDERS, so the grader has to be given code and not prose.
_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/|//[^\n]*")

#: How a shipped asset spells the parsed body of a refusal. ``bodyData`` returns
#: ``body.data`` and every renderer that wants the envelope binds the whole body
#: to one of these two names first, so a member read off one of them is a member
#: this page puts on screen - and a warning record's own ``detail``, which is
#: read off ``entry`` and ``record``, is correctly not one.
_REFUSAL_NAMES: Final = ("body", "refusal")


def _code(name: str) -> str:
    """One shipped asset with every comment stripped.

    Args:
        name: The asset's file name.

    Returns:
        Its source with block and line comments replaced by a space.
    """
    return _COMMENT.sub(" ", (panel_harness.WEB_DIR / name).read_text(encoding="ascii"))


def _renders(key: str) -> tuple[str, ...]:
    """Which shipped assets read ``key`` off a refusal envelope and put it on screen.

    THIS IS THE ORACLE THE PANEL'S CANNOT-SHOW LIST IS GRADED AGAINST, and it
    exists because the arm it replaces graded the PRESENCE of a sentence and
    never its truth: the panel told the reader the page could not show
    ``blocked_by`` while ``app.js`` was printing it into the endpoint table on
    the same screen. A claim about the page has to be measured against the page.

    Args:
        key: An envelope member name.

    Returns:
        The asset names that read it, sorted, or an empty tuple.
    """
    forms = tuple(f"{holder}.{key}" for holder in _REFUSAL_NAMES)
    forms += tuple(f'{holder}["{key}"]' for holder in _REFUSAL_NAMES)
    return tuple(name for name in WEB_ASSETS if any(form in _code(name) for form in forms))


#: The envelope members the seam itself prints. A sentence calling one of these
#: unavailable is false on the page it is printed on, so the panel must not.
ENVELOPE_ON_THE_PAGE: Final = tuple(key for key in ENVELOPE_ONLY if SEAM in _renders(key))

#: The envelope members the seam prints nowhere, which are the only ones the
#: CANNOT-SHOW list may name. Derived, so the day ``app.js`` starts printing one
#: it moves out of this tuple and
#: :func:`test_no_envelope_member_the_seam_prints_is_called_absent` goes red.
ENVELOPE_OFF_THE_PAGE: Final = tuple(key for key in ENVELOPE_ONLY if SEAM not in _renders(key))

#: Every token the CANNOT-SHOW list must name. Derived where a derivation
#: exists; the rest are pinned at their source by
#: :func:`test_every_stated_gap_is_still_a_gap_at_its_source`.
GAP_TOKENS: Final = (
    *WORLD_COUNTED_ONLY,
    *UNLOCK_SIZES,
    *ENVELOPE_OFF_THE_PAGE,
    "purity",
    "resource type",
    "produced_in",
    "power",
    "masked",
)

#: A count written beside a list, which is the shape of the second defect this
#: repair closes: the lede said three routes and then named four.
_COUNTED_ROUTES: Final = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+routes?\b",
    re.IGNORECASE,
)

#: The shipped panel modules, stacked in this order by :func:`_stack` with the
#: module under grade LAST so the harness captures and mounts it.
STACK: Final = tuple(name for name in WEB_ASSETS if name.startswith("panel_") and name != MODULE)

#: The id a panel module registers itself under, read out of the module.
_DECLARED_ID: Final = re.compile(r'registerPanel\(\s*"([a-z_]+)"')

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
    """Copy the shipped panel with the whole list entry naming ``drop`` deleted.

    THE MUTATION IS A DELETION, not a rewrite, because the fault being simulated
    is an author dropping an entry from the list - the exact regression the gap
    arm exists to catch. It takes the WHOLE entry because a gap entry is written
    as a wrapped concatenation and deleting one of its lines would leave a unary
    plus on a string literal: valid JavaScript, an element reading ``NaN``, and a
    mutant that is no longer the fault being modelled.

    Args:
        tmp_path: Where the mutant is written.
        drop: A substring identifying the one line the entry is named on.

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
    start = hits[0]
    while start > 0 and lines[start].lstrip().startswith("+"):
        start -= 1
    end = hits[0]
    while end + 1 < len(lines) and lines[end + 1].lstrip().startswith("+"):
        end += 1
    del lines[start : end + 1]
    mutant = tmp_path / "planted_panel_scope.js"
    mutant.write_bytes("\n".join(lines).encode("ascii"))
    return mutant


def _declared_id(name: str) -> str:
    """The panel id a shipped module registers itself under.

    Args:
        name: The module's file name.

    Returns:
        The id string it passes to ``registerPanel``.
    """
    match = _DECLARED_ID.search(_code(name))
    if match is None:
        pytest.fail(f"{name} registers no panel id, so the stacked arm cannot expect one")
    return match.group(1)


def _stack(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    """Every shipped panel module concatenated into one file, ``MODULE`` last.

    WHY A STACK RATHER THAN A SECOND HARNESS CALL. ``panel_harness`` loads one
    module per run, and an arm that asserts the panel names exactly the one
    module this run loaded is satisfied by a hardcoded one-element return -
    which an adversary confirmed survives. Concatenating the shipped modules
    puts four real registrations into ``panelEntries`` in a known order, so the
    expectation is a four-element list no literal in the panel produces. The
    module under grade goes last because the harness mounts the LAST accepted
    registration.

    Args:
        tmp_path: Where the stacked module is written.

    Returns:
        The stacked module's path, and the ids it registers in order.
    """
    names = (*STACK, MODULE)
    parts = [(panel_harness.WEB_DIR / name).read_text(encoding="ascii") for name in names]
    target = tmp_path / "stacked_panels.js"
    target.write_bytes("\n".join(parts).encode("ascii"))
    return target, tuple(_declared_id(name) for name in names)


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
    """No repaint hands this panel the id, so printing it would be unverifiable here.

    See the module docstring. ``blocked_by`` is a refusal-envelope member and
    ``bodyData`` drops the envelope, so the id never reaches a panel on a
    repaint; the page shows it because ``app.js`` reads it off each probe
    itself. The arm at
    ``test_web_assets.py::test_the_script_never_hardcodes_the_blocking_item_id``
    covers ``app.js`` and ``index.html`` only; this extends the same rule to
    this module on its own merits rather than by analogy.
    """
    source = (panel_harness.WEB_DIR / MODULE).read_text(encoding="ascii")
    assert pending.PENDING_BLOCKER not in source, f"{MODULE} hardcodes the blocking item id"
    assert "blocked_by" in ENVELOPE_ONLY, "blocked_by is no longer refusal-only; revisit the panel"
    assert SEAM in _renders("blocked_by"), (
        f"{SEAM} no longer prints blocked_by, so the page may now hide the id entirely; "
        f"the panel's gap list has to be revisited"
    )


def test_the_panel_lists_the_panel_ids_the_seam_published(tmp_path: Path) -> None:
    """``data.panels`` is READ, and three ids no module on disk registers prove it.

    The seam publishes the registered ids as an array of strings on the payload.
    Feeding names no shipped module uses is what separates a panel that reads
    the list from one that recites a list of its own.
    """
    published = ["alpha", "beta", "scope"]
    payload = dict(panel_harness.null_payload(health=_health()))
    payload["panels"] = published

    report = panel_harness.mount(tmp_path, MODULE, payload)
    assert report["state"] == panel_harness.STATE_MOUNTED, report["threw"]
    assert _entries(report, PANELS_ID) == tuple(published)


def test_an_empty_published_panel_list_is_honoured_rather_than_replaced(tmp_path: Path) -> None:
    """An empty array is an answer, and the answer is that nothing registered.

    The seam's contract is that ``data.panels`` is present on every mount and is
    an empty array when nothing registered - never absent and never null. So an
    empty array must be printed as empty, not quietly swapped for the fallback,
    even though the fallback would here find this very panel.
    """
    payload = dict(panel_harness.null_payload(health=_health()))
    payload["panels"] = []

    report = panel_harness.mount(tmp_path, MODULE, payload)
    assert report["state"] == panel_harness.STATE_MOUNTED, report["threw"]
    assert _entries(report, PANELS_ID) == ()
    assert "registered nothing" in report["nodes"][0]["text"]


@pytest.mark.parametrize("published", [None, "scope", 7, {"0": "scope"}])
def test_a_payload_without_an_array_falls_back_to_the_registration_array(
    tmp_path: Path, published: Any
) -> None:
    """A payload that omits ``data.panels`` still names every panel that registered.

    THE FALLBACK IS DELIBERATE AND IS GRADED. ``data.panels`` is a seam landing
    beside this panel, so a page served an older ``app.js`` hands a payload
    without it - and rendering an empty list there would be the panel telling
    the reader that no panel registered while four are on the screen. The
    fallback reads ``panelEntries``, which is why the stacked module's four
    registrations come back in registration order.

    Args:
        tmp_path: Where the stacked module is written.
        published: What the payload carries under ``panels``, none of it an array.
    """
    seam = _code(SEAM)
    assert "panelEntries" in seam, (
        "the seam no longer publishes panelEntries; the fallback is blind"
    )

    stacked, ids = _stack(tmp_path)
    assert len(ids) > 1, "the stack holds one module, so its expectation is a literal again"

    payload = dict(panel_harness.null_payload(health=_health()))
    if published is not None:
        payload["panels"] = published

    report = panel_harness.mount(tmp_path, stacked, payload)
    assert report["load_threw"] is None, report["load_threw"]
    assert report["panel_id"] == "scope", (
        "the stacked module did not end with the panel under grade"
    )
    assert _entries(report, PANELS_ID) == ids


def test_the_published_list_wins_over_the_registration_array(tmp_path: Path) -> None:
    """With both available the panel prints what the seam published.

    The fallback is a bridge, not a second source of truth. Four modules are
    registered and the payload publishes one id; the one id is what prints, so
    the fallback is provably not consulted when ``data.panels`` is an array.
    """
    stacked, ids = _stack(tmp_path)
    assert len(ids) > 1

    payload = dict(panel_harness.null_payload(health=_health()))
    payload["panels"] = ["only-this-one"]

    report = panel_harness.mount(tmp_path, stacked, payload)
    assert _entries(report, PANELS_ID) == ("only-this-one",)


def test_no_envelope_member_the_seam_prints_is_called_absent(tmp_path: Path) -> None:
    """Every CANNOT-SHOW sentence about the refusal envelope is true of THIS page.

    THIS IS THE ARM THE DEFECT GOT PAST. Its predecessor asserted that the token
    ``blocked_by`` appeared in the list text, which is a check on whether a
    sentence was printed rather than on whether it was true - and the sentence
    was false: ``app.js`` reads ``result.body.blocked_by`` and prints it into
    the blocked-by column of the endpoint table, and reads a refusal ``detail``
    into the World note, both on the same screen as a panel saying the page
    could not show either.

    So the list is graded against the assets, in both directions. A member the
    seam prints may not be called absent, and a member it prints nowhere must
    be named - which means a wire or a renderer that starts serving one turns
    this red instead of leaving a false sentence on screen to rot.
    """
    # A known-good control first: an oracle that matched nothing would report
    # every member absent, and the "must be named" half would pass for the
    # wrong reason while the "may not be called absent" half went blind.
    assert SEAM in _renders("blocked_by"), (
        f"{SEAM} no longer reads a refusal blocked_by, or _renders has gone blind; "
        f"it found {ENVELOPE_ONLY} at {[(key, _renders(key)) for key in ENVELOPE_ONLY]}"
    )
    # THE BENCHES, AND ONLY THE BENCHES. A refusal reason reaches the page from
    # exactly the panels that ASK for something, because only a panel holding a
    # door has a refusal to render. It was the solve bench alone until the
    # optimize and power benches got doors of their own; anything else printing
    # one would mean a panel rendering an envelope no request of its own
    # produced, which is the class of false sentence this whole arm exists for.
    assert _renders("reason") == REFUSAL_PRINTING_BENCHES, (
        "exactly the asking benches print a refusal reason; "
        f"now {_renders('reason')}. The panel's sentence about it must be rewritten."
    )
    assert ENVELOPE_ON_THE_PAGE, "the seam prints no envelope member; this arm grades a split"
    assert ENVELOPE_OFF_THE_PAGE, "the seam prints every envelope member; this arm grades a split"

    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=_health()))
    gaps = _text(report, GAPS_ID)

    false_claims = [key for key in ENVELOPE_ON_THE_PAGE if key in gaps]
    assert not false_claims, (
        f"{MODULE} calls {false_claims} absent, but {SEAM} prints each of them on this page"
    )
    unnamed = [key for key in ENVELOPE_OFF_THE_PAGE if key not in gaps]
    assert not unnamed, f"{SEAM} prints {unnamed} nowhere and {MODULE} never says so"


def test_the_panel_prints_no_route_count(tmp_path: Path) -> None:
    """A count typed beside a list of routes is a sentence that drifts, and it did.

    The lede said every figure came from one of THREE routes and then named
    four. A number written next to a list it does not come from has no way to
    stay right, so the panel names the routes and counts none of them.
    """
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload(health=_health()))
    counted = _COUNTED_ROUTES.findall(report["nodes"][0]["text"])
    assert not counted, (
        f"{MODULE} prints a route count {counted}; the routes it names are the only tally, "
        "and a typed one drifts from them"
    )


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
