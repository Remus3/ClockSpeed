"""CS-601 slice S5 - a plain-HTTP loopback stand-in so the dashboard can be SEEN.

WHY THIS EXISTS, MEASURED RATHER THAN ASSUMED. The browser pane available to
this project refuses to load HTTPS backed by a self-signed certificate: the
navigation is denied BEFORE the TLS handshake, so no screenshot of the real
dashboard is obtainable. Plain HTTP on loopback renders and screenshots without
complaint. BOOTSTRAP.md section 7.1 mandates HTTPS for the dashboard, so the
production listener cannot move to HTTP and this module is what closes the gap:
it serves THE REAL ASSET FILES, unmodified, beside canned ``/api/*`` answers, so
the CS-600 five-phase visual audit grades the page this project actually ships
in a state it actually reaches.

THIS IS TEST CODE AND IS NEVER A SHIPPING PATH. It lives under ``tests/`` and
not under ``clockspeed/``, it is not importable from the shipping package, and
``tests/surface/test_web_assets.py`` asserts both. A stand-in that answered on
plain HTTP and was reachable from the package would be a way to serve this
dashboard without TLS, which is exactly what section 7.1 forbids.

SAME ORIGIN, WHICH IS THE WHOLE POINT OF SERVING THE ASSETS RATHER THAN OPENING
THEM AS FILES. The page fetches ``/api/health`` and ``/api/world`` relative to
its own origin. Loaded from ``file:``, those fetches fail and the audit grades
an empty page; served from here, they behave exactly as they do in production,
including under the ``connect-src 'self'`` half of the Content-Security-Policy,
which this module sends verbatim from the server's own constant.

NOTHING CANNED HERE IS PERSONAL DATA, AND THE SHAPE IS WHAT MAKES THAT SAFE
RATHER THAN A PROMISE. The world token is :func:`masked_token` applied to a seed
sentence authored in this file, so the digest has production's exact shape over
an input this repository wrote. No path, no account name, no world name and no
save filename appears in any canned body; ``test_web_assets.py`` sweeps every
served byte for each of those shapes and proves the sweep fires.

THE ENVELOPES ARE BUILT BY THE SHIPPED CONSTRUCTORS. Every body below comes out
of ``contract.ok``, ``contract.not_implemented`` or ``contract.no_such_route``,
so a canned answer cannot drift from the envelope the real endpoints produce,
cannot name a blocking item the contract has closed, and cannot carry a float.
Hand-writing the JSON would have made this module a second description of the
wire format, and CLAUDE.md section 4 names a restated fact as one that drifts.

WHAT IT DELIBERATELY DOES NOT SERVE, AND NOT FOR THE REASON THIS PARAGRAPH USED
TO GIVE. ``/api/advice/<id>/state`` gets no concrete path here, and
``/api/advice/<id>/derivation`` gets one per canned card and no other. The reason
recorded until now was that ``server.routing``
REFUSED to register a template carrying a path parameter, that dispatch matched a
request path EXACTLY, and that therefore neither endpoint had a concrete path in
production. ALL THREE ARE NOW FALSE. ``routing`` registers both, ``match_route``
matches a concrete path against either and captures the segment, and both answer
over the wire: ``GET .../derivation`` since CS-1270, ``POST .../state`` since
CS-1269 - 403 without the same-origin proof - and 405 for ``GET .../state``. A
stale justification is worse than a red test,
because an arm resting on it keeps passing and reads as verified.

WHY NO TEMPLATE IS PROBED, ON A REASON THAT IS TRUE TODAY. The audit grades ONE
page, and no repaint of that page asks for either template.
``clockspeed/surface/web/app.js``
publishes every route each with the concrete path - if there is one - it may
safely GET, and both ``<id>`` rows carry none; each therefore reports the
liveness ``/api/health`` already publishes for it and names that as the source in
its own "read from" column. MEASURED rather than argued: this same harness,
widened in memory to serve both against a stand-in id, rendered a page identical
in every byte the audit reads - the note line was BYTE-IDENTICAL either way and
both rows stayed "not probed". Two more canned answers buy nothing observable.

THE COUNT THAT USED TO SIT IN THAT SENTENCE IS GONE ON PURPOSE. It read "5 of 9
routes answered a direct GET", transcribed from a run, and CS-912's tenth route
made it "6 of 10" without touching this file - the third time this paragraph
went stale. The invariant is that widening changes nothing, and that is true at
any counts, so the numbers are not restated here. The claim this paragraph used
to make about being pinned was also wrong: the arm it named pins only the two
``<id>`` rows, and it was a DIFFERENT row gaining a probe path that falsified
the sentence.

THE DERIVATION'S IDS ARE THE CANNED CARDS' OWN, AND THAT IS ALL THE DIVERGENCE THERE IS.
Since CS-1371 the advice panel reads a card identifier out of ``/api/advice`` and asks
the derivation route with it on a click, so each canned card has a derivation under its
own id. :data:`CANNED` is keyed by exact path, so any other id is a 404 here where
production answers 400; the panel only ever asks with an id it was listed, so no audited
press reaches that difference. The ids are words and not production's 64-hex digest,
because ``test_web_assets.py``'s personal-data sweep reads a digest that long as a hex
account id. The state route's 501 body is still built and published in
:data:`PENDING_BODIES`, so the walking skeleton knows what blocks it even where nothing
here asks.

THE ADVICE PANEL'S STATES, FOR THE AUDIT (CS-1371). Before a request ``/api/advice``
lists :data:`HELD_CARDS`, two visible and one hidden. A stated request answers by its
target alone: :data:`TARGET_RANKED` a plan.adopt card and ``ranked``,
:data:`TARGET_ROUTED` a plan.redesign card and ``no-plan``/``routed`` with trimmed
recipes, :data:`TARGET_NO_ROUTE` no card and ``no-plan``/``no-route`` with unmade items,
:data:`TARGET_ROUTE_REFUSED` no card and ``no-plan``/``route-refused``. The rate, the
direction and the policy go through the real checks and move nothing else, so typing a
bad rate shows the panel a real refusal. A canned listing holds only what its state is
named for, where a real one would also hold the world's own cards: that is what makes
the no-card state reachable here at all. :func:`main` prints this table too.

RUNNING IT STANDALONE, which is how the merger drives the audit::

    python -m tests.surface.audit_harness

It prints the URL it bound, then the routes and the stated targets, and serves until
interrupted. The port is whatever
the operating system hands out: ``config/ports.json`` owns the dashboard's
allocation and a test server must never claim from it.
"""

from __future__ import annotations

import json
import sys
import threading
from fractions import Fraction
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final
from urllib.parse import parse_qsl

import clockspeed
from clockspeed.advisor.rules import fuel as fuel_rules
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.advisor.rules import power as power_rules
from clockspeed.audit import placement
from clockspeed.data import version
from clockspeed.data.registry import Building, Recipe
from clockspeed.save.header import masked_token
from clockspeed.save.objects import REASON_CLASS_NOT_MODELLED
from clockspeed.save.world import (
    SOURCE_USMAP,
    SOURCE_WORLD,
    WARN_NO_PROPERTY_MAP,
    WARN_NODE_SEMANTICS_UNAVAILABLE,
)
from clockspeed.solve import power
from clockspeed.surface import config, server
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, health, pending, registry, solve
from clockspeed.surface.api import map as map_endpoint
from clockspeed.surface.api import power as power_endpoint
from clockspeed.surface.api import world as world_endpoint
from clockspeed.surface.providers import StoreAdviceSource

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

__all__ = [
    "CANNED",
    "PENDING_BODIES",
    "REQUESTED_PORT",
    "SYNTHETIC_WORLD_SEED",
    "AuditHarness",
    "main",
]


# ---------------------------------------------------------------------------
# Binding
# ---------------------------------------------------------------------------

#: Ask the operating system for a free port. NOT a number from the dashboard's
#: reserved band: ``config/ports.json`` owns that allocation, and a stand-in
#: that claimed one would collide with the real listener whenever both ran.
REQUESTED_PORT: Final = 0

#: How long a connection may sit idle before its thread is released.
CONNECTION_TIMEOUT: Final = 30.0

#: How long a shutdown waits before the listener is closed anyway.
SHUTDOWN_TIMEOUT: Final = 5.0


# ---------------------------------------------------------------------------
# The synthetic world
# ---------------------------------------------------------------------------

#: The seed the masked world token is derived from. A SENTENCE THIS REPOSITORY
#: WROTE, which says out loud what it is. Running it through the shipped mask
#: gives the digest production's exact prefix and width without any real token
#: coming near this file - and re-deriving the mask here instead would be a
#: second implementation of a redaction control, which is how a subtly wrong one
#: comes to look identical to a correct one.
SYNTHETIC_WORLD_SEED: Final = "clockspeed-audit-harness-synthetic-world"

#: Class paths for the unmodelled-content list. AUTHORED HERE AND OBVIOUSLY SO -
#: nothing is lifted from the shipped game assets or from any wiki, which
#: CLAUDE.md section 7 settles. One is deliberately long and one is deliberately
#: namespaced like a mod, because those are the two that stress the page: the
#: long one tests wrapping, and the mod-shaped one is the string that must
#: render as TEXT and never as markup.
SYNTHETIC_UNKNOWN_CLASSES: Final = (
    (
        "/Game/ExampleContent/Buildable/Factory/ExampleAssembler/"
        "Build_ExampleAssemblerMkTwo.Build_ExampleAssemblerMkTwo_C",
        41,
        11,
    ),
    ("/ExampleMod/Buildables/Build_ExampleSplitter.Build_ExampleSplitter_C", 12, 908),
    ("/Game/ExampleContent/Build_ExamplePipeJunction.Build_ExamplePipeJunction_C", 6, 1544),
)

#: The counts a populated world reports. Chosen to look like a mid-game factory
#: so the audit grades realistic column widths rather than single digits.
SYNTHETIC_COUNTS: Final = MappingProxyType(
    {
        "objects": 18452,
        "levels": 43,
        "nodes": 1287,
        "unknown_classes": len(SYNTHETIC_UNKNOWN_CLASSES),
        "warnings": 2,
    }
)

#: The unlock summary. Sizes rather than lists, exactly as the endpoint serves.
SYNTHETIC_UNLOCKS: Final = MappingProxyType(
    {
        "purchased_schematics": 61,
        "recipes": 214,
        "scanned_resources": 7,
        "current_game_phase": 2,
        "feature_flags": {"overclock": True, "alternate_recipes": True, "hypertubes": False},
        "is_empty": False,
    }
)

#: The advisories a load carries. THE SOURCE AND THE CODE ARE IMPORTED FROM THE
#: SAVE LAYER, so a renamed code goes red here rather than shipping a word that
#: layer no longer uses. The detail lines are short synthetic stand-ins and are
#: NOT the real ones - the real text lives in a private mapping that a test may
#: not reach across the seam, and this page never renders a detail line anyway.
#: The SUBJECT is the code, which is what the save layer's own warnings carry.
SYNTHETIC_WARNINGS: Final = (
    (SOURCE_WORLD, WARN_NODE_SEMANTICS_UNAVAILABLE, "resource nodes carry placement only", 1287),
    (SOURCE_USMAP, WARN_NO_PROPERTY_MAP, "no property mapping was supplied to this load", 1),
)


def _build_changelist() -> int:
    """The changelist the pinned game build names, read from its one owner.

    ``clockspeed.data.version.GAME_CHANGELIST`` is the pin's only parse of its
    build string (CS-1288). It is read HERE, at call time, rather than captured
    at import or re-parsed with a second pattern: a number written down twice is
    a number that drifts (CLAUDE.md section 4), and a second parse is a second
    reading of the same number.

    Returns:
        The pinned changelist.

    Raises:
        AssertionError: The pin carries no changelist. A stand-in such as zero
            would be indistinguishable from a measured value on the page the
            audit grades.
    """
    changelist = version.GAME_CHANGELIST
    if changelist is None:
        message = "the pinned build carries no changelist for the harness world"
        raise AssertionError(message)
    return changelist


def _unknown_classes() -> list[dict[str, object]]:
    """Render the synthetic unmodelled classes in the endpoint's own shape.

    Returns:
        One mapping per class, keyed by ``world.UNKNOWN_CLASS_KEYS``.
    """
    return [
        {
            "type_path": type_path,
            "count": count,
            "reason": REASON_CLASS_NOT_MODELLED,
            "first_index": first_index,
        }
        for type_path, count, first_index in SYNTHETIC_UNKNOWN_CLASSES
    ]


#: CS-1240: the save each synthetic class was first read in, among the three
#: saves the harness world claims were read since the server started. One per
#: label the panel prints - an earlier save, this save, and a middle one.
SYNTHETIC_SAVES_READ: Final = 3
SYNTHETIC_FIRST_SEEN: Final = (1, 3, 2)


def _unmodelled() -> dict[str, object]:
    """Render the synthetic unmodelled classes as the ``unmodelled`` object.

    Ordered by stable id, as ``clockspeed.save.sightings.report`` orders them.

    Returns:
        The object, keyed by ``world.UNMODELLED_KEYS``.
    """
    paired = sorted(
        (type_path, count, first_seen)
        for (type_path, count, _index), first_seen in zip(
            SYNTHETIC_UNKNOWN_CLASSES, SYNTHETIC_FIRST_SEEN, strict=True
        )
    )
    return {
        "scope": world_endpoint.FIRST_SEEN_SCOPE,
        "checked": True,
        "keyed": True,
        "this_save": SYNTHETIC_SAVES_READ,
        "saves_read": SYNTHETIC_SAVES_READ,
        "classes": [
            {
                "stable_id": type_path,
                "count": count,
                "reason": REASON_CLASS_NOT_MODELLED,
                "first_seen": first_seen,
            }
            for type_path, count, first_seen in paired
        ],
    }


def _warnings() -> list[dict[str, object]]:
    """Render the synthetic advisories in the endpoint's own shape.

    Returns:
        One mapping per warning, keyed by ``world.WARNING_KEYS``.
    """
    return [
        {"source": source, "code": code, "detail": detail, "subject": code, "count": count}
        for source, code, detail, count in SYNTHETIC_WARNINGS
    ]


def _world_data() -> dict[str, object]:
    """Build the ``/api/world`` data object a populated save produces.

    Returns:
        The body, keyed exactly as ``clockspeed/surface/api/world.py`` keys it.
    """
    return {
        "world": masked_token(SYNTHETIC_WORLD_SEED),
        "header_version": 13,
        "save_version": 46,
        "build_changelist": _build_changelist(),
        "body_offset": 1229,
        "is_modded": True,
        "counts": dict(SYNTHETIC_COUNTS),
        "contains_unmodeled_content": True,
        "unlocks": dict(SYNTHETIC_UNLOCKS),
        "warnings": _warnings(),
        "unknown_classes": _unknown_classes(),
        "unmodelled": _unmodelled(),
    }


# ---------------------------------------------------------------------------
# The map body - the one canned answer with a SHAPE rather than a scalar
# ---------------------------------------------------------------------------

#: The synthetic world the map body describes, as (class name, count) pairs laid
#: out on a deterministic lattice by :func:`_map_placements`. IT IS AUTHORED
#: RATHER THAN SAMPLED. A slice of a real save would be personal data under
#: non-negotiable 11, and a handful of points would grade a page that the real
#: one - hundreds of nodes deep - renders quite differently. These populations
#: are the order of magnitude the pinned development world actually carries, so
#: the visual audit sees a plausible density instead of a diagram.
_MAP_NODE_CLASSES: Final = (
    ("BP_ResourceNode_C", 46),
    ("BP_ResourceDeposit_C", 19),
    ("BP_FrackingSatellite_C", 12),
    ("BP_ResourceNodeGeyser_C", 4),
    ("BP_FrackingCore_C", 2),
)

#: The built population, on the same terms. Mixed tiers on purpose: a legend
#: with one entry proves nothing about a legend with seven.
_MAP_BUILT_CLASSES: Final = (
    ("Build_MinerMk1_C", 9),
    ("Build_SmelterMk1_C", 7),
    ("Build_ConstructorMk1_C", 5),
    ("Build_GeneratorCoal_C", 3),
    ("Build_WaterPump_C", 2),
    ("Build_StorageContainerMk1_C", 2),
)

#: The lattice's extent in the game's own units, and its step. Whole numbers,
#: rendered with a fractional part, so every coordinate on this wire has the
#: SHAPE a real one has - a decimal string - without carrying a real one.
_MAP_SPAN: Final = 240000
_MAP_STEP: Final = 7919

#: Four orientations about the vertical axis, as the exact decimal strings the
#: wire carries. A canned orientation must have the SHAPE a real one has - an
#: array of strings, never numbers - because a panel that parsed a number here
#: would pass the audit and fail on the live wire.
#:
#: DELIBERATELY NOT UNIT, AND NOT FOUR QUARTER TURNS (CS-1021). Only entries 0
#: and 2 are unit quaternions: the identity and the half turn. Entries 1 and 3,
#: the ``0.5`` pairs, have a norm-squared of one half, and a real quarter turn
#: about the vertical axis is ``0.70710678`` in both of its last two components
#: - a value no short exact decimal spells. These are chosen for SHAPE and
#: exactness, not realism: the game does not produce the ``0.5`` spellings. A
#: panel that read entry 1 as a yaw through ``atan2(2(wz + xy), 1 - 2(y^2 +
#: z^2))`` would get 45 degrees rather than 90; through the rotation-angle
#: formula ``2 * acos(w)`` it would get 120. No panel reads an orientation
#: today. The save layer transcribes and never normalises, so no unit-norm arm
#: belongs there either (CS-1021's ruling).
#: ``test_the_canned_rotations_are_unit_exactly_where_the_comments_say`` in
#: ``tests/surface/test_map.py`` pins every number in this paragraph.
_MAP_QUARTER_TURNS: Final = (
    ("0.0", "0.0", "0.0", "1.0"),
    ("0.0", "0.0", "0.5", "0.5"),
    ("0.0", "0.0", "1.0", "0.0"),
    ("0.0", "0.0", "-0.5", "0.5"),
)

#: Unbuilt scale. Every real building carries it, so a fixture that varied it
#: would grade a case the game does not produce.
_MAP_UNIT_SCALE: Final = ("1.0", "1.0", "1.0")


def _map_placements(
    populations: tuple[tuple[str, int], ...], phase: int
) -> tuple[list[dict[str, object]], dict[str, int]]:
    """Lay a population out on a deterministic lattice.

    The walk is a fixed stride around a ring, so the same input yields the same
    output on every run and on every machine - a canned body that moved between
    runs would make a visual audit unrepeatable.

    Args:
        populations: Class name and how many of it to place.
        phase: An offset that separates one population from another, so nodes
            and built actors do not land on identical coordinates.

    Returns:
        The placement rows, and the per-class counts. The counts are DERIVED
        from the rows rather than copied from the input, so the two cannot
        disagree - which is the property the panel's legend depends on.
    """
    rows: list[dict[str, object]] = []
    counts: dict[str, int] = {}
    seed = _MAP_STEP + phase
    for class_name, count in populations:
        for _ in range(count):
            # A TEXTBOOK LINEAR CONGRUENTIAL STEP, NOT A STRIDE AROUND A RING.
            # The stride version laid every population out on three straight
            # diagonals - deterministic, and nothing like a world. A visual
            # audit against a fixture that could not occur grades a page nobody
            # will ever see. This is still fully deterministic: same seed, same
            # points, every run and every machine.
            seed = (seed * 1103515245 + 12345) % 2147483648
            x = (seed % (2 * _MAP_SPAN)) - _MAP_SPAN
            seed = (seed * 1103515245 + 12345) % 2147483648
            y = (seed % (2 * _MAP_SPAN)) - _MAP_SPAN
            seed = (seed * 1103515245 + 12345) % 2147483648
            z = (seed % 20000) - 10000
            # THE ORIENTATION IS DRAWN FROM THE SAME LATTICE, so a rendered
            # fixture shows buildings at differing angles rather than a field of
            # identical ones. Every component is exactly representable so the
            # string is short and exact; two of the four are deliberately not
            # unit quaternions - see ``_MAP_QUARTER_TURNS``.
            seed = (seed * 1103515245 + 12345) % 2147483648
            quarter = _MAP_QUARTER_TURNS[seed % len(_MAP_QUARTER_TURNS)]
            rows.append(
                {
                    "class_name": class_name,
                    "x": f"{x}.0",
                    "y": f"{y}.0",
                    "z": f"{z}.0",
                    "rotation": list(quarter),
                    "scale": list(_MAP_UNIT_SCALE),
                }
            )
        counts[class_name] = count
    return rows, counts


def _map_data() -> dict[str, object]:
    """Build the ``/api/map`` data object a populated save produces.

    KEYED FROM THE ENDPOINT'S OWN TUPLES, not from a second list written here.
    ``clockspeed/surface/api/map.py`` owns the key set; a hand-written copy is
    the restated fact CLAUDE.md section 4 names as one that will drift, and the
    drift would be silent - a canned body missing a key renders as a panel with
    an empty section rather than as a failure.

    Returns:
        The body, keyed exactly as the endpoint keys it.
    """
    nodes, node_counts = _map_placements(_MAP_NODE_CLASSES, phase=0)
    built, built_counts = _map_placements(_MAP_BUILT_CLASSES, phase=3557)
    body: dict[str, object] = {
        "schema": map_endpoint.SCHEMA,
        "masked_token": masked_token(SYNTHETIC_WORLD_SEED),
        "coordinate_units": placement.COORDINATE_UNITS,
        "node_semantics_available": False,
        "node_orientation_available": True,
        "bounds": {
            "min_x": f"-{_MAP_SPAN}.0",
            "max_x": f"{_MAP_SPAN}.0",
            "min_y": f"-{_MAP_SPAN}.0",
            "max_y": f"{_MAP_SPAN}.0",
            "min_z": "-10000.0",
            "max_z": "10000.0",
        },
        "nodes": nodes,
        "node_counts": node_counts,
        "built": built,
        "built_counts": built_counts,
        "inventory": [],
        "throughput": [
            {
                "class_name": "Build_MinerMk1_C",
                "display_name": "Miner Mk.1",
                "built": 9,
                "per_minute_normal": "60",
                "per_minute_unit": map_endpoint.RATE_UNIT,
                "allowed_forms": ["RF_SOLID"],
                "purity_scaling": {"impure": "1/2", "normal": "1", "pure": "2"},
                "purity_scaling_measured": False,
                "purity_known": False,
            },
            {
                "class_name": "Build_WaterPump_C",
                "display_name": "Water Extractor",
                "built": 2,
                "per_minute_normal": "120000",
                "per_minute_unit": map_endpoint.RATE_UNIT,
                "allowed_forms": ["RF_LIQUID"],
                "purity_scaling": {"impure": "1/2", "normal": "1", "pure": "2"},
                "purity_scaling_measured": False,
                "purity_known": False,
            },
        ],
        # CS-1316. The harness world is the pinned build's own and its registry
        # the pinned docs', so the audit page shows the on-pin state - no build
        # code, no marking - which is what the pinned development world serves.
        "build_state": {
            "save_changelist": _build_changelist(),
            "pinned_changelist": _build_changelist(),
            "save_build_matches": True,
            "registry_verified": True,
        },
        "warnings": [
            {
                "source": SOURCE_WORLD,
                "code": WARN_NODE_SEMANTICS_UNAVAILABLE,
                "count": sum(count for _name, count in _MAP_NODE_CLASSES),
            },
            {"source": "inventory", "code": "inventory-total-empty", "count": 1},
        ],
    }
    missing = tuple(key for key in map_endpoint.DATA_KEYS if key not in body)
    surplus = tuple(key for key in body if key not in map_endpoint.DATA_KEYS)
    if missing or surplus:
        message = f"canned map body does not match the endpoint: {missing} {surplus}"
        raise AssertionError(message)
    _assert_rows_match(body)
    _assert_build_state_matches(body)
    return body


def _assert_build_state_matches(body: dict[str, object]) -> None:
    """Bind the canned BUILD STATE to the endpoint's own key tuple (CS-1316).

    The same one-level-down guard :func:`_assert_rows_match` is for the rows:
    the top-level check sees that ``build_state`` is present and nothing about
    what it holds, so a canned state missing a key the panel reads would pass
    it and render as a state the endpoint never serves.

    Args:
        body: The canned body, already checked at the top level.

    Raises:
        AssertionError: When the build state is not a mapping, or its key set
            differs from ``map_endpoint.BUILD_STATE_KEYS`` in either direction.
    """
    state = body["build_state"]
    if not isinstance(state, dict):
        message = "canned map body carries no build state mapping"
        raise AssertionError(message)
    published = frozenset(map_endpoint.BUILD_STATE_KEYS)
    keys = frozenset(state)
    if keys != published:
        missing = tuple(sorted(published - keys))
        surplus = tuple(sorted(keys - published))
        message = f"canned build state does not match the endpoint: {missing} {surplus}"
        raise AssertionError(message)


def _assert_rows_match(body: dict[str, object]) -> None:
    """Bind the canned PLACEMENT ROWS to the endpoint's own row tuple.

    THE TOP-LEVEL CHECK ABOVE GUARDS ONE LEVEL AND CS-1013 DRIFTED UNDERNEATH
    IT. ``PLACEMENT_KEYS`` grew from four entries to six while every canned row
    here still carried four, and ``_map_data`` returned normally - so this
    fixture would have stayed green straight through the real defect, the day a
    panel reads a rotation off a row that has none. A guard that checks the
    outer envelope and not the rows is a guard that has already been passed by
    the thing it exists to catch.

    Args:
        body: The canned body, already checked at the top level.

    Raises:
        AssertionError: When a placement row's key set differs from
            ``map_endpoint.PLACEMENT_KEYS`` in either direction, naming the
            section and the difference.
    """
    sections = (
        ("nodes", map_endpoint.PLACEMENT_KEYS),
        ("built", map_endpoint.PLACEMENT_KEYS),
        ("warnings", map_endpoint.WARNING_KEYS),
    )
    for section, key_tuple in sections:
        published = frozenset(key_tuple)
        rows = body[section]
        if not isinstance(rows, list) or not rows:
            message = f"canned map body has no {section} rows, so this guard grades nothing"
            raise AssertionError(message)
        for row in rows:
            keys = frozenset(row)
            if keys != published:
                missing = tuple(sorted(published - keys))
                surplus = tuple(sorted(keys - published))
                message = f"canned {section} row does not match the endpoint: {missing} {surplus}"
                raise AssertionError(message)


# ---------------------------------------------------------------------------
# The canned answers
# ---------------------------------------------------------------------------

#: The route template ``clockspeed/surface/api/world.py`` answers. Spelled here
#: because that module names it ``ENDPOINT``, which collides with the health
#: module's constant of the same name at any shared import site.
WORLD_ENDPOINT: Final = "/api/world"

#: Which templates the server's own route table would report as live. The five
#: in ``pending.UNBACKED`` have no layer beneath them; the rest do. THE COUNT
#: OF THE REST IS NOT SPELLED HERE: it read "four" from nine templates until
#: CS-912 published a tenth, which is the third sentence in this repository
#: that a new route falsified without touching the file it sat in.
_UNBACKED_TEMPLATES: Final = frozenset(template for _method, template in pending.UNBACKED)


def _liveness() -> dict[str, str]:
    """The endpoint map ``/api/health`` publishes, one entry per template.

    Built by asking ``pending.UNBACKED`` which routes are unbacked rather than
    by listing them again, so a route that gains a layer flips here for free.

    Returns:
        Template to liveness word, over every published template.
    """
    return {
        template: health.NOT_LIVE if template in _UNBACKED_TEMPLATES else health.LIVE
        for template in health.ENDPOINT_TEMPLATES
    }


def _health_data() -> dict[str, object]:
    """Build the ``/api/health`` data object.

    The two version facts are READ FROM THEIR OWNERS rather than restated, which
    is what makes the header line the audit sees the real one.

    Returns:
        The body, keyed exactly as ``clockspeed/surface/api/health.py`` keys it.
    """
    return {
        "app_version": clockspeed.__version__,
        "game_build_pin": version.GAME_BUILD,
        "registry": health.PRESENT,
        "world": health.LOADED,
        "endpoints": _liveness(),
    }


#: Every unbacked route's 501, keyed by TEMPLATE and built by the shipped
#: constructor. All are published, including the state route carrying a path
#: parameter that this harness serves no concrete path for - the skeleton knows
#: what blocks it even where nothing here asks. Production DOES route it; see
#: the module docstring for why the stand-in still does not.
PENDING_BODIES: Final[Mapping[str, contract.Response]] = MappingProxyType(
    {
        template: contract.not_implemented(template, pending.BLOCKERS[template])
        for _method, template in pending.UNBACKED
    }
)


def _plan_data() -> dict[str, object]:
    """A solved production plan, every numeric leaf an exact ratio.

    NOT ONE BARE NUMBER ANYWHERE IN IT. ``contract.encode`` refuses a float
    outright, and a bare JSON number is read by a browser as an IEEE double,
    which is the value non-negotiable 6 keeps out of the answer path.

    Returns:
        The data object, shaped as ``clockspeed/surface/api/solve.py`` shapes it.
    """
    return {
        "steps": [
            {"recipe_key": "Recipe_ExamplePlate_C", "machines": contract.rational(Fraction(9, 2))},
            {"recipe_key": "Recipe_ExampleRod_C", "machines": contract.rational(Fraction(7, 4))},
        ],
        "targets": {"Desc_ExamplePlate_C": contract.rational(Fraction(45, 1))},
        "raw_inputs": {"Desc_ExampleOre_C": contract.rational(Fraction(135, 2))},
        "byproducts": {},
        "excluded": [{"recipe_key": "Recipe_ExampleAlt_C", "reason": "recipe-not-unlocked"}],
        "byproduct_policy": "sink",
    }


#: The four stated targets the audit reaches the advice panel's states by, one each. All
#: four are keys this file already serves. The first two have a display name in the
#: registry stand-in below and the last two have none, so the target list shows the
#: panel's fallback beside its names.
TARGET_RANKED: Final = "Item_ExamplePlate_C"
TARGET_ROUTED: Final = "Item_ExampleOre_C"
TARGET_NO_ROUTE: Final = "Desc_ExamplePlate_C"
TARGET_ROUTE_REFUSED: Final = "Desc_ExampleOre_C"

#: Every stated target, in the order the registry stand-in serves them.
AUDIT_TARGETS: Final = (TARGET_RANKED, TARGET_ROUTED, TARGET_NO_ROUTE, TARGET_ROUTE_REFUSED)


def _registry_data() -> dict[str, object]:
    """Build the ``/api/registry`` data object.

    SMALL AND SYNTHETIC ON PURPOSE. The real route serves the whole normalized
    registry off the shipped documents; this harness must answer on a machine
    with no game installed, and the audit reads the liveness row rather than the
    contents. THE REAL COUNTS ARE NOT SPELLED HERE - `clockspeed/data/version.py`
    owns them, they cannot be re-measured without the install, and an earlier
    draft of this docstring carried two of them here in the same change that
    removed them from `app.js` for being exactly that.

    Keyed by :data:`registry.BODY_KEYS`, with every rational served through
    ``contract.rational`` because ``contract`` refuses a float at any
    depth and ``json.dumps`` cannot encode a ``Fraction`` at all.

    Returns:
        The body, keyed exactly as ``clockspeed/surface/api/registry.py`` keys it.
    """
    body: dict[str, object] = {
        "items": [
            {
                "key": "Item_ExampleOre_C",
                "display_name": "Example Ore",
                "form": "solid",
                "is_fluid": False,
                "energy_value": None,
                "sink_points": 1,
            },
            {
                "key": "Item_ExamplePlate_C",
                "display_name": "Example Plate",
                "form": "solid",
                "is_fluid": False,
                "energy_value": None,
                "sink_points": 3,
            },
        ],
        "recipes": [
            {
                "key": "Recipe_ExamplePlate_C",
                "display_name": "Example Plate",
                "duration": contract.rational(Fraction(2, 1)),
                "inputs": [
                    {"item_key": "Item_ExampleOre_C", "amount": contract.rational(Fraction(3, 2))}
                ],
                "outputs": [
                    {"item_key": "Item_ExamplePlate_C", "amount": contract.rational(Fraction(1, 1))}
                ],
                "produced_in": ["Build_ExampleSmelter_C"],
            }
        ],
        "buildings": [{"key": "Build_ExampleSmelter_C", "display_name": "Example Smelter"}],
        "counts": {
            "items": 2,
            "recipes": 1,
            "buildings": 1,
            "warnings": 0,
            "unknown_groups": 0,
        },
        "warnings": [],
        "unknown_groups": [],
        # CS-1371: what the advice panel's target list reads. Not what the real function
        # would answer over these rows, which is the one plate: the stand-in lists a key
        # per state the audit has to reach, and no canned recipe makes the others.
        registry.PLAN_TARGETS_KEY: list(AUDIT_TARGETS),
    }
    _assert_keys_match("registry body", body, registry.BODY_KEYS)
    return body


#: A building key for the canned power answer. AUTHORED IN THIS FILE, like every
#: other identifier the harness serves - no name here is read off an install.
_POWER_BUILDING: Final = "Build_ExampleSmelter_C"

#: The canned clock, away from the reference so the answer is the DEFERRED one.
#: Deliberately not 1: at the reference clock the draw is an exact scalar and the
#: symbolic term is absent, so a fixture pinned there would render the one shape
#: that cannot expose a surface which evaluates the power law.
_POWER_CLOCK: Final = Fraction(3, 2)

#: The canned building AS AN ENTRY, so every canned ``reason`` can be READ from
#: ``clockspeed/solve/power.py`` rather than written here (CS-1031). Authored in
#: this file like every other identifier the harness serves. Each value is the
#: one the canned body already depicts: a scalar draw of 4, an un-sharded base
#: of 1 - so the canned clock of 3/2 is clamped - and an exponent that is
#: DELIBERATELY NOT A SHIPPED ONE, for the reason recorded at the deferred term.
_POWER_ENTRY: Final = Building(
    key=_POWER_BUILDING,
    display_name="Example Smelter",
    power_consumption=Fraction(4),
    power_exponent=Fraction(11, 7),
    estimated_min_power=None,
    estimated_max_power=None,
    is_variable_power=False,
    unsharded_clock_base=Fraction(1),
)

#: The recipe the variable-inputs section is read against. It declares neither
#: variable-power operand, which is what the canned section depicts.
_POWER_RECIPE: Final = Recipe(
    key="Recipe_ExampleIngot_C",
    display_name="Example Ingot",
    duration=Fraction(2),
    inputs=(),
    outputs=(),
    produced_in=(_POWER_BUILDING,),
    variable_power_constant=None,
    variable_power_factor=None,
)


def _power_data() -> dict[str, object]:
    """Build the ``/api/power`` data object, bound to the endpoint's own keys.

    THE GUARD IS THE POINT, AND IT IS CS-1013'S LESSON APPLIED TO A SECOND BODY.
    That item found ``PLACEMENT_KEYS`` grown from four entries to six while every
    canned map row still carried four, with the top-level check passing happily
    over them: a guard that checks the outer envelope and not the nested objects
    has already been passed by the thing it exists to catch. This body is five
    nested objects deep, so every one of them is bound to the tuple
    ``clockspeed/surface/api/power.py`` publishes for it, in BOTH directions.

    THE NUMBERS ARE EXACT PAIRS BECAUSE THE REAL ENDPOINT SENDS PAIRS. A canned
    body carrying a bare number would let the audit grade a page rendering a
    float, which is the one rendering the whole power path exists to prevent.

    THE DEFERRED TERM IS UNEVALUATED HERE TOO. ``clockspeed/solve/power.py``
    records that ``Fraction ** Fraction`` returns a float for the shipped
    exponent; this fixture carries the two operands and applies neither, so a
    panel that evaluated one would have nothing correct to compare against.

    EVERY REASON IS READ, NONE IS WRITTEN (CS-1031). Each of the five is the
    ``reason`` field of what the public function in ``clockspeed/solve/power.py``
    returns for :data:`_POWER_ENTRY` - the same functions the endpoint calls -
    and :func:`_assert_reason_published` refuses a section whose branch fields
    disagree with what that function computed, so a reason cannot be read off
    one branch and served beside another.

    Returns:
        The body, keyed by ``power_endpoint.DATA_KEYS``.

    Raises:
        AssertionError: When the body or any nested object differs from the
            endpoint's published key tuple in either direction, or when a
            section's reason or branch differs from what its owner published.
    """
    decl = power.declared_draw(_POWER_ENTRY)
    drawn = power.draw_at_clock(_POWER_ENTRY, _POWER_CLOCK)
    capped = power.clock_ceiling(_POWER_ENTRY)
    clamp = power.clamp_to_unsharded_base(_POWER_ENTRY, _POWER_CLOCK)
    inputs = power.variable_power_inputs(_POWER_ENTRY, _POWER_RECIPE)
    declared = {
        "shape": power.SHAPE_FIXED,
        "megawatts": contract.rational(Fraction(4)),
        "minimum": None,
        "maximum": None,
        "modeled": True,
        "reason": decl.reason,
    }
    ceiling = {
        "base": contract.rational(Fraction(1)),
        "slots": None,
        "known": False,
        "reason": capped.reason,
    }
    at_clock = {
        "outcome": power.OUTCOME_DEFERRED,
        "megawatts": None,
        "coefficient": contract.rational(Fraction(4)),
        "deferred": {
            "base": contract.rational(_POWER_CLOCK),
            # DELIBERATELY NOT A SHIPPED EXPONENT, AND DELIBERATELY IRRATIONAL
            # WHEN APPLIED. CS-105 keeps the real exponent out of every file
            # that could restate it, and 11/7 cannot be mistaken for a
            # measurement; (3/2) ** (11/7) has no exact rational value, so a
            # surface that evaluated the term would produce a float this
            # fixture gives it nothing correct to be confused with.
            "exponent": contract.rational(Fraction(11, 7)),
        },
        "reason": drawn.reason,
    }
    clamped = {
        "clock": contract.rational(Fraction(1)),
        "base": contract.rational(Fraction(1)),
        "clamped": True,
        "reason": clamp.reason,
    }
    variable = {
        "constant": None,
        "factor": None,
        "minimum": None,
        "maximum": None,
        "modeled": False,
        "reason": inputs.reason,
    }
    body: dict[str, object] = {
        "building_key": _POWER_BUILDING,
        "declared": declared,
        "ceiling": ceiling,
        "at_clock": at_clock,
        "clamped": clamped,
        "variable_inputs": variable,
        # CS-1315 slice B. The harness registry stands for one built from the
        # pinned docs bytes, so the bench shows the verified state and no code.
        "build_state": {"registry_verified": True},
        "warnings": [],
    }

    _assert_keys_match("power body", body, power_endpoint.DATA_KEYS)
    _assert_keys_match("power declared", declared, power_endpoint.DECLARED_KEYS)
    _assert_keys_match("power ceiling", ceiling, power_endpoint.CEILING_KEYS)
    _assert_keys_match("power at_clock", at_clock, power_endpoint.AT_CLOCK_KEYS)
    _assert_keys_match("power deferred term", at_clock["deferred"], power_endpoint.TERM_KEYS)
    _assert_keys_match("power clamped", clamped, power_endpoint.CLAMPED_KEYS)
    _assert_keys_match("power variable_inputs", variable, power_endpoint.VARIABLE_KEYS)

    _assert_reason_published(
        "power declared", declared, decl.reason, {"shape": decl.shape, "modeled": decl.modeled}
    )
    _assert_reason_published(
        "power ceiling", ceiling, capped.reason, {"known": capped.known, "slots": capped.slots}
    )
    _assert_reason_published("power at_clock", at_clock, drawn.reason, {"outcome": drawn.outcome})
    _assert_reason_published("power clamped", clamped, clamp.reason, {"clamped": clamp.clamped})
    _assert_reason_published(
        "power variable_inputs", variable, inputs.reason, {"modeled": inputs.modeled}
    )
    return body


def _assert_reason_published(
    what: str,
    section: Mapping[str, object],
    published: str,
    branch: Mapping[str, object],
) -> None:
    """Bind one canned ``reason`` to the reason its owner publishes (CS-1031).

    A REASON IS A FACT ``clockspeed/solve/power.py`` OWNS, exactly as a key
    tuple is a fact the endpoint owns. The earlier cut bound one of five and
    hand-authored the other four, three of them shortened or reworded from the
    published prose, so a panel arm graded against the canned body could pass
    while the real endpoint said something else. This guard refuses that at
    import.

    THE BRANCH IS CHECKED FIRST, because a reason read off the wrong branch is
    a published reason that is still wrong for the section: the canned fields
    that decide which reason the owner publishes must agree with what the owner
    computed for the canned entry, or the reason describes some other answer.

    Args:
        what: What to call the section in the message. A literal authored here.
        section: The canned object.
        published: The reason the owner published for the canned entry.
        branch: The canned keys that select the branch, mapped to the values
            the owner computed for them.

    Raises:
        AssertionError: A branch field differs from the owner's value, or the
            canned reason is not the published one.
    """
    for key, value in branch.items():
        if section.get(key) != value:
            message = f"canned {what} depicts a different branch than its owner computed: {key}"
            raise AssertionError(message)
    if section.get("reason") != published:
        message = f"canned {what} reason is not the one its owner publishes"
        raise AssertionError(message)


def _assert_keys_match(what: str, section: object, key_tuple: tuple[str, ...]) -> None:
    """Bind one canned object to the key tuple its endpoint publishes for it.

    TWO-WAY, AND REFUSING AN EMPTY SECTION, exactly as
    :func:`_assert_rows_match` is. A one-way check passes over a fixture that
    has lost a key, and an empty object satisfies every subset rule there is
    while grading nothing at all.

    Args:
        what: What to call the object in the message. A literal authored here.
        section: The canned object.
        key_tuple: The endpoint's own published tuple of its keys.

    Raises:
        AssertionError: The object is not a non-empty mapping, or its key set
            differs from the published tuple in either direction.
    """
    if not isinstance(section, dict) or not section:
        message = f"canned {what} is not a non-empty object, so this guard grades nothing"
        raise AssertionError(message)
    published = frozenset(key_tuple)
    keys = frozenset(section)
    if keys != published:
        missing = tuple(sorted(published - keys))
        surplus = tuple(sorted(keys - published))
        message = f"canned {what} does not match the endpoint: {missing} {surplus}"
        raise AssertionError(message)


def _advice_card(
    card_id: str,
    *,
    rule_id: str,
    domain: str,
    headline: str,
    reason: str,
    visible: bool = True,
) -> dict[str, object]:
    """One listed card, keyed exactly as the endpoint keys one.

    THE ID IS A WORD, NOT production's 64-hex digest. See the module docstring.

    Args:
        card_id: The id, lowercase, which the derivation's path carries.
        rule_id: The rule, read off its spec by the caller so a rename reddens here.
        domain: The rule's domain, read the same way.
        headline: Tier 1, authored here over synthetic names.
        reason: Tier 2, the same.
        visible: Whether the listing flags it visible. A hidden card reads as dismissed.

    Returns:
        The card.
    """
    card: dict[str, object] = {
        "id": card_id,
        "rule_id": rule_id,
        "domain": domain,
        "headline": headline,
        "reason": reason,
        "state": "new" if visible else "dismissed",
        "snoozed_until": None,
        "muted": False,
        "visible": visible,
    }
    _assert_keys_match("advice card", card, tuple(advice_endpoint.CARD_KEYS))
    return card


#: The two visible cards a world's listing holds before anything is stated.
_CARD_DRAW: Final = _advice_card(
    "audit-card-power-draw",
    rule_id=power_rules.GAP_RULE.rule_id,
    domain=power_rules.GAP_RULE.domain,
    headline="Resolve 1 unpriced machine before planning power",
    reason="The clocked draw is a floor of 4.00 to 4.00 MW: 0 clocks unread and 1 machine"
    " unmodeled, of 2",
)

_CARD_SUPPLY: Final = _advice_card(
    "audit-card-fuel-supply",
    rule_id=fuel_rules.SUPPLY_RULE.rule_id,
    domain=fuel_rules.SUPPLY_RULE.domain,
    headline="Supply 10.00 m3 more Synthetic Example Fuel per minute to Synthetic Example"
    " Generator x1",
    reason="Synthetic Example Generator x1 burns 10.00 m3 per minute and none reaches it",
)

#: Listed flagged hidden, which is what the panel has to leave off the page.
_CARD_DISMISSED: Final = _advice_card(
    "audit-card-fuel-demand",
    rule_id=fuel_rules.DEMAND_RULE.rule_id,
    domain=fuel_rules.DEMAND_RULE.domain,
    headline="Plan 15.00 items of Synthetic Example Coal per minute for Synthetic Example"
    " Burner x1",
    reason="This card was dismissed, so nothing on the page should read this sentence",
    visible=False,
)

#: What a world's listing holds before anything is stated.
HELD_CARDS: Final = (_CARD_DRAW, _CARD_SUPPLY, _CARD_DISMISSED)

_CARD_ADOPT: Final = _advice_card(
    "audit-card-plan-adopt",
    rule_id=plan_rules.ADOPT_RULE.rule_id,
    domain=plan_rules.ADOPT_RULE.domain,
    headline=f"Build the planned production chain for {TARGET_RANKED}",
    reason=f"It makes 10.00 per minute of {TARGET_RANKED} with 2.00 machine equivalents",
)

_CARD_REDESIGN: Final = _advice_card(
    "audit-card-plan-redesign",
    rule_id=plan_rules.REDESIGN_RULE.rule_id,
    domain=plan_rules.REDESIGN_RULE.domain,
    headline=f"Plan toward {TARGET_ROUTED}",
    reason="This route runs 3 locked and 1 held recipe(s); the locked recipes must unlock"
    " first on this route; the stated direction did not choose this route and it was never"
    " compared with what is built",
)

#: Every step line each card's derivation reads, by id. Long lines on purpose, in the
#: shape the real derivation has, so an audit sees how tier 3 wraps.
_DERIVATION_STEPS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "audit-card-power-draw": (
            "Read power.clocked_draw.complete = false from audit.balance.clocked_draw.complete",
            "Read power.clocked_draw.floor = 4.00 from audit.balance.clocked_draw.floor",
            "Decide the draw is a floor, so no gap figure is offered",
        ),
        "audit-card-fuel-supply": (
            'Read fuel.verdict = FuelVerdict(generator="Build_ExampleSmelter_C", demand=10.00,'
            " supplied=0.00) from audit.fuel.verdicts.verdict",
            "Compute the shortfall as 10.00 - 0.00 = 10.00 m3 per minute",
        ),
        "audit-card-fuel-demand": (
            'Read fuel.verdict = FuelVerdict(generator="Build_ExampleSmelter_C", demand=15.00,'
            " supplied=0.00) from audit.fuel.verdicts.verdict",
        ),
        "audit-card-plan-adopt": (
            'Read plan.status = "ranked" from advisor.plans.status',
            'Read plan.badge = StrategyBadge(strongest="within-raw", cleared=("within-raw"),'
            ' checks=(ThresholdCheck(strategy="within-raw", cleared=true, score=10.00,'
            ' reference=10.00, bound=1.00, reason=""))) from solve.strategy.ranked_plan.badge',
            'Read plan.selection = ("Recipe_ExamplePlate_C") from solve.strategy.ranked_plan',
            "Compute plan machine equivalents as 2.00",
        ),
        "audit-card-plan-redesign": (
            'Read plan.redesign.status = "routed" from advisor.plans.redesign.status',
            "Read plan.redesign.plan = ProductionPlan(steps=(PlanStep(recipe_key="
            '"Recipe_ExamplePlate_C", machines=1.00), PlanStep(recipe_key="Recipe_ExampleRod_C",'
            ' machines=1.00), PlanStep(recipe_key="Recipe_ExampleIngot_C", machines=1.00)))'
            " from solve.ratio.solve_for_targets",
            'Read plan.redesign.locked = ("Recipe_ExampleRod_C", "Recipe_ExampleIngot_C") from'
            " advisor.plans.redesign.locked",
            'Read plan.redesign.held = ("Recipe_ExamplePlate_C") from advisor.plans.redesign.held',
        ),
    }
)


def _derivation_answer(card: Mapping[str, object]) -> contract.Response:
    """The derivation route's answer for one canned card, in the real text's shape.

    THE ONE DEPARTURE IS THE STEP COUNT IN "Steps (n):". The real text's bare "Steps:" then
    a line break encodes as a letter, a colon and a backslash, which is the shape the
    personal-data sweep in ``test_web_assets.py`` exists to read as a drive-lettered path.

    Args:
        card: A canned card.

    Returns:
        The 200, built by the shipped constructor.
    """
    steps = _DERIVATION_STEPS[str(card["id"])]
    lines = (
        f"Derivation of rule {card['rule_id']} (domain {card['domain']})",
        f"Advice: {card['headline']}",
        f"Because: {card['reason']}",
        "Target milestone: none",
        f"Steps ({len(steps)}):",
        *(f"  {number}. {step}" for number, step in enumerate(steps, start=1)),
    )
    body: dict[str, object] = {
        "id": card["id"],
        "rule_id": card["rule_id"],
        "derivation": "\n".join(lines),
    }
    _assert_keys_match("advice derivation", body, tuple(advice_endpoint.DERIVATION_KEYS))
    return contract.ok(advice_endpoint.DERIVATION_ENDPOINT, body)


def _derivation_path(card: Mapping[str, object]) -> str:
    """The concrete path one canned card's derivation answers on.

    Args:
        card: A canned card.

    Returns:
        The path, with the id in the template's one parameter.
    """
    return advice_endpoint.DERIVATION_ENDPOINT.replace(
        f"<{advice_endpoint.ID_PARAMETER}>", str(card["id"])
    )


def _advice_data() -> dict[str, object]:
    """The advice listing before anything is stated: two visible cards and one hidden.

    Returns:
        The data object, shaped as ``clockspeed/surface/api/advice.py`` shapes it.
    """
    body: dict[str, object] = {"new_world": True, "cards": list(HELD_CARDS)}
    _assert_keys_match("advice listing", body, tuple(advice_endpoint.DATA_KEYS))
    return body


def _stated_answer(
    cards: Sequence[dict[str, object]],
    status: str,
    redesign: str,
    *,
    trimmed: tuple[str, ...] = (),
    unmade: tuple[str, ...] | None = None,
) -> contract.Response:
    """The listing one stated request answers, with what it came to.

    THE OUTCOME IS THE REAL ONE, PROJECTED AND TRANSCRIBED BY ITS OWNERS: the advisor's
    function reads the inputs an offer would carry and picks the reason, and the endpoint's
    transcribes it. A reason is a fact the advisor owns, so none is typed here, and a field
    the outcome does not hold is absent as it is on the wire.

    Args:
        cards: The cards this state lists.
        status: The ``plan.status`` word.
        redesign: The ``plan.redesign.status`` word.
        trimmed: What the bound dropped. A search ran on every state here, so this is
            never absent, and empty says it dropped nothing.
        unmade: What nothing makes, on ``no-route``, and None on every other state.

    Returns:
        The 200, built by the shipped constructor.
    """
    outcome = plan_rules.plan_outcome_of(
        {
            **plan_rules.refused_inputs(status, trimmed=trimmed, unchecked=(), unmatched_unlocks=0),
            **plan_rules.redesign_status_inputs(redesign, unmade=unmade),
        }
    )
    body: dict[str, object] = {
        "new_world": False,
        "cards": list(cards),
        "plan_outcome": advice_endpoint._outcome(outcome),  # noqa: SLF001 - the real transcription
    }
    _assert_keys_match("stated advice listing", body, tuple(advice_endpoint.STATED_DATA_KEYS))
    return contract.ok(advice_endpoint.ENDPOINT, body)


#: What each stated target answers. See the module docstring for why by target alone.
STATED_ANSWERS: Final[Mapping[str, contract.Response]] = MappingProxyType(
    {
        TARGET_RANKED: _stated_answer(
            (_CARD_ADOPT,), plan_rules.STATUS_RANKED, plan_rules.REDESIGN_NOT_REACHED
        ),
        TARGET_ROUTED: _stated_answer(
            (_CARD_REDESIGN,),
            plan_rules.STATUS_NO_PLAN,
            plan_rules.REDESIGN_ROUTED,
            trimmed=("Recipe_ExampleAlt_C", "Recipe_ExampleIngot_C"),
        ),
        TARGET_NO_ROUTE: _stated_answer(
            (),
            plan_rules.STATUS_NO_PLAN,
            plan_rules.REDESIGN_NO_ROUTE,
            unmade=("Item_ExampleOre_C", "Desc_ExampleOre_C"),
        ),
        TARGET_ROUTE_REFUSED: _stated_answer(
            (), plan_rules.STATUS_NO_PLAN, plan_rules.REDESIGN_ROUTE_REFUSED
        ),
    }
)

#: Every canned card, each of which answers a derivation.
_ALL_CARDS: Final = (*HELD_CARDS, _CARD_ADOPT, _CARD_REDESIGN)


def _canned() -> dict[tuple[str, str], contract.Response]:
    """Build the whole routable answer table.

    Keyed by method AND path, so a POST to a GET route is a 405 rather than an
    accidental 200 - the same boundary the real dispatcher draws.

    Returns:
        ``(method, path)`` to the response the harness serves for it.
    """
    table: dict[tuple[str, str], contract.Response] = {
        ("GET", health.ENDPOINT): contract.ok(health.ENDPOINT, _health_data()),
        ("GET", WORLD_ENDPOINT): contract.ok(WORLD_ENDPOINT, _world_data()),
        ("GET", registry.ENDPOINT): contract.ok(registry.ENDPOINT, _registry_data()),
        ("GET", map_endpoint.ENDPOINT): contract.ok(map_endpoint.ENDPOINT, _map_data()),
        # A GET, UNLIKE THE TWO SOLVER DOORS BELOW IT. /api/power takes a
        # required parameter and still answers GET, so it is the one row here
        # whose verb cannot be guessed from whether it takes one.
        ("GET", power_endpoint.ENDPOINT): contract.ok(power_endpoint.ENDPOINT, _power_data()),
        # CS-1270: the advice listing is live, so the stand-in answers it.
        ("GET", advice_endpoint.ENDPOINT): contract.ok(advice_endpoint.ENDPOINT, _advice_data()),
        ("POST", solve.SOLVE_ENDPOINT): contract.ok(solve.SOLVE_ENDPOINT, _plan_data()),
        ("POST", solve.OPTIMIZE_ENDPOINT): contract.ok(
            solve.OPTIMIZE_ENDPOINT,
            {
                "backend": "exact",
                "selection": ["Recipe_ExamplePlate_C", "Recipe_ExampleRod_C"],
                "plan": _plan_data(),
                "score": contract.rational(Fraction(23, 5)),
                "objective": {"weights": {"power": contract.rational(Fraction(1, 1))}},
                "excluded": [],
            },
        ),
    }
    for card in _ALL_CARDS:
        table["GET", _derivation_path(card)] = _derivation_answer(card)
    for method, template in pending.UNBACKED:
        # A TEMPLATE CARRYING A PARAMETER IS SKIPPED BECAUSE THIS TABLE IS KEYED
        # BY EXACT PATH - not because production cannot route one. It can, and does.
        # See the module docstring.
        if "<" not in template:
            table[method, template] = PENDING_BODIES[template]
    return table


#: The endpoint map this harness serves inside ``/api/health``, published for
#: the same reason :data:`CANNED` is: an arm asserting the two agree should read
#: a stated fact rather than reach through an underscore into the builder.
LIVENESS: Final[Mapping[str, str]] = MappingProxyType(_liveness())

#: The routable answers, keyed by exact path. A path absent from here is a
#: contract 404. The two path-parameter templates are absent as templates, and each
#: canned card's derivation is here under its own concrete path - see the module
#: docstring for the reason, which is about what the PAGE asks for and not about
#: what production can route.
CANNED: Final[Mapping[tuple[str, str], contract.Response]] = MappingProxyType(_canned())

#: Every body this harness can serve, by a label naming how it is reached, so the arms
#: sweeping canned bodies reach the ones a query selects as well as the ones a path does.
EVERY_ANSWER: Final[Mapping[str, contract.Response]] = MappingProxyType(
    {
        **{f"{method} {path}": response for (method, path), response in CANNED.items()},
        **{
            f"GET {advice_endpoint.ENDPOINT}?{advice_endpoint.TARGET_PARAMETER}={target}": answer
            for target, answer in STATED_ANSWERS.items()
        },
    }
)

#: Reads no store and no clock: only its doors on a statement are ever called here, and
#: those are the advisor's own checks of a rate, a direction and a policy.
_PLAN_DOORS: Final = StoreAdviceSource()

#: How each stated target reads, which :func:`main` prints for whoever drives the audit.
AUDIT_STATE_LABELS: Final[Mapping[str, str]] = MappingProxyType(
    {
        TARGET_RANKED: "plan.adopt card, ranked",
        TARGET_ROUTED: "plan.redesign card, no-plan/routed, trimmed recipes",
        TARGET_NO_ROUTE: "no card, no-plan/no-route, unmade items",
        TARGET_ROUTE_REFUSED: "no card, no-plan/route-refused",
    }
)


def advice_answer(raw_query: str) -> contract.Response:
    """Answer ``/api/advice`` for one query string, refusing as the real route refuses.

    THE ORDER IS THE ROUTE'S OWN, BECAUSE THIS CALLS IT. An unknown name, a partial set and a
    value the advisor refuses all come out of the endpoint's own function through the
    advisor's own door, so a refusal the panel is shown here is the one it would be shown
    there. Only a target off this file's list is answered here, as the route does.

    Args:
        raw_query: What follows the question mark.

    Returns:
        The listing a statement selects, or the refusal.
    """
    endpoint = advice_endpoint.ENDPOINT
    try:
        query = dict(
            parse_qsl(raw_query, keep_blank_values=True, strict_parsing=True, errors="strict")
        )
    except ValueError:
        return contract.bad_request(endpoint, contract.REASON_MALFORMED_QUERY)
    stated = advice_endpoint._stated_plan(endpoint, query, _PLAN_DOORS, own=())  # noqa: SLF001
    if isinstance(stated, contract.Response):
        return stated
    if stated is None:
        return CANNED["GET", endpoint]
    answer = STATED_ANSWERS.get(stated[0])
    if answer is None:
        return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
    return answer


#: Every path this table answers under at least one method.
_KNOWN_PATHS: Final = frozenset(path for _method, path in CANNED)


# ---------------------------------------------------------------------------
# The listener
# ---------------------------------------------------------------------------


class _Handler(BaseHTTPRequestHandler):
    """Answers one request from the two closed tables and from nothing else.

    It writes no value it did not compose: the log is silenced entirely rather
    than left to the stdlib, whose default line echoes the raw request path to
    stderr, and on this machine a request path is caller-chosen text.
    """

    protocol_version = "HTTP/1.1"

    def version_string(self) -> str:
        """Return the banner, which discloses no interpreter version.

        Returns:
            The server's own name.
        """
        return server.SERVER_BANNER

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Discard the stdlib access line, which echoes the request path.

        Args:
            format: Ignored, deliberately.
            args: Ignored, deliberately.
        """
        del format, args

    def log_error(self, format: str, *args: object) -> None:  # noqa: A002
        """Discard the stdlib error line, for the same reason.

        Args:
            format: Ignored, deliberately.
            args: Ignored, deliberately.
        """
        del format, args

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        """Answer the contract's 404 instead of the stdlib's HTML error page.

        The stdlib page interpolates the request path into markup. On this
        machine that path can be anything a caller typed.

        Args:
            code: Ignored, deliberately.
            message: Ignored, deliberately.
            explain: Ignored, deliberately.
        """
        del code, message, explain
        self._respond(contract.no_such_route())

    def _emit(self, code: int, body: bytes, content_type: str, *, csp: bool) -> None:
        """Write one complete response.

        Args:
            code: The transport code.
            body: The already-encoded body.
            content_type: The Content-Type header value.
            csp: Whether to send the Content-Security-Policy, which the real
                server sends on the HTML response only.
        """
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in server.FIXED_HEADERS:
            self.send_header(name, value)
        if csp:
            self.send_header("Content-Security-Policy", server.CONTENT_SECURITY_POLICY)
        self.end_headers()
        self.wfile.write(body)

    def _respond(self, response: contract.Response) -> None:
        """Write one contract response as JSON.

        Args:
            response: What to send.
        """
        self._emit(
            response.http_status,
            contract.encode(response.payload),
            server.CONTENT_TYPE_JSON,
            csp=False,
        )

    def _serve_asset(self, filename: str, content_type: str) -> None:
        """Write one real asset file, read fresh so an edit shows on refresh.

        Args:
            filename: A name from ``server.ASSET_NAMES``, never a request path.
            content_type: What the static table says it is.
        """
        web_dir: Path = self.server.web_dir  # type: ignore[attr-defined]
        try:
            body = (web_dir / filename).read_bytes()
        except OSError:
            self._respond(contract.no_such_route())
            return
        self._emit(HTTPStatus.OK, body, content_type, csp=filename.endswith(".html"))

    def _dispatch(self) -> None:
        """Match the request against the closed tables and answer it.

        The one row a query selects is the advice listing, and only on a GET carrying one;
        every other row is an exact path, whose query is not read.
        """
        raw_path, _mark, raw_query = self.path.partition("?")

        static = server.STATIC_ROUTES.get(raw_path)
        if static is not None and self.command in {"GET", "HEAD"}:
            self._serve_asset(*static)
            return

        if self.command == "GET" and raw_path == advice_endpoint.ENDPOINT and raw_query:
            self._respond(advice_answer(raw_query))
            return

        response = CANNED.get((self.command, raw_path))
        if response is not None:
            self._respond(response)
            return
        if raw_path in _KNOWN_PATHS or static is not None:
            self._respond(contract.method_not_allowed(raw_path))
            return
        self._respond(contract.no_such_route())

    def do_GET(self) -> None:
        """Answer a GET."""
        self._dispatch()

    def do_HEAD(self) -> None:
        """Answer a HEAD."""
        self._dispatch()

    def do_POST(self) -> None:
        """Answer a POST."""
        self._dispatch()


class _Server(ThreadingHTTPServer):
    """The listener, carrying the asset directory the handler reads from.

    NOT A DATACLASS AND THE PATH IS NOT IN A GENERATED REPR, for the reason
    ``clockspeed/surface/providers.py`` states about its own reader: a rendered
    ``Path`` carries the account directory it sits under.
    """

    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], web_dir: Path) -> None:
        """Bind the listener and remember where the assets are.

        Args:
            address: Host and port. The port is normally :data:`REQUESTED_PORT`.
            web_dir: The directory holding the three real asset files.
        """
        super().__init__(address, _Handler)
        self.web_dir = web_dir
        self.timeout = CONNECTION_TIMEOUT


class AuditHarness:
    """One running stand-in: start it, screenshot the page, stop it.

    Not a dataclass, for the reason :class:`_Server` gives.
    """

    def __init__(self, web_dir: Path | None = None) -> None:
        """Wire the harness to an asset directory without binding anything yet.

        Args:
            web_dir: Where the three assets live, or None for the package's own
                ``web`` directory as ``clockspeed/surface/config.py`` resolves
                it. A caller passing one is how a test points at a copy.
        """
        self._web_dir = config.default_web_dir() if web_dir is None else web_dir
        self._server: _Server | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        """The port the operating system handed out.

        Returns:
            The bound port, or 0 before :meth:`start`.
        """
        return 0 if self._server is None else self._server.server_address[1]

    @property
    def url(self) -> str:
        """The base URL this harness answers on.

        Returns:
            The origin, with no trailing slash.
        """
        return f"http://{config.LOOPBACK}:{self.port}"

    def start(self) -> None:
        """Bind an ephemeral port and serve on a background thread.

        Raises:
            RuntimeError: When called on a harness that is already serving.
                Starting twice would leak the first listener, and a leaked
                listener holds a port until the process ends.
        """
        if self._server is not None:
            raise RuntimeError(ALREADY_SERVING)
        self._server = _Server((config.LOOPBACK, REQUESTED_PORT), self._web_dir)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop serving and release the listener, whatever state it is in.

        ``server_close`` runs even when the join times out: the listener being
        released is what the next start depends on, and a bounded wait that
        skipped it would hold the port until the process ended.
        """
        running, thread = self._server, self._thread
        self._server, self._thread = None, None
        if running is None:
            return
        try:
            running.shutdown()
            if thread is not None:
                thread.join(SHUTDOWN_TIMEOUT)
        finally:
            running.server_close()


#: What starting an already-started harness is refused with. A fixed line.
ALREADY_SERVING: Final = "this harness is already serving; stop it before starting it again"


def main() -> int:
    """Serve until interrupted, printing the URL and the canned route table.

    Writes through ``sys.stdout`` rather than ``print`` because ``T20`` bans the
    builtin outside the two directories whose interface IS a printed table.

    Returns:
        Zero. A keyboard interrupt is the expected way to end this.
    """
    harness = AuditHarness()
    harness.start()
    published = sorted(f"{method} {path}" for method, path in CANNED)
    sys.stdout.write(f"{harness.url}\n")
    sys.stdout.write(f"assets: {', '.join(sorted(server.ASSET_NAMES))}\n")
    sys.stdout.write(f"canned: {json.dumps(published)}\n")
    sys.stdout.write(f"stated targets: {json.dumps(dict(AUDIT_STATE_LABELS))}\n")
    sys.stdout.write("interrupt to stop\n")
    sys.stdout.flush()
    try:
        while True:
            threading.Event().wait(CONNECTION_TIMEOUT)
    except KeyboardInterrupt:
        sys.stdout.write("stopping\n")
    finally:
        harness.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
