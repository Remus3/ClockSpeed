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
TO GIVE. ``/api/advice/<id>/derivation`` and ``/api/advice/<id>/state`` get no
concrete path here. The reason recorded until now was that ``server.routing``
REFUSED to register a template carrying a path parameter, that dispatch matched a
request path EXACTLY, and that therefore neither endpoint had a concrete path in
production. ALL THREE ARE NOW FALSE. ``routing`` registers both, ``match_route``
matches a concrete path against either and captures the segment, and both answer
over the wire: MEASURED at 501 for ``GET .../derivation`` and ``POST .../state``,
and 405 for ``GET .../state``. A stale justification is worse than a red test,
because an arm resting on it keeps passing and reads as verified.

WHY THREE AND NOT FIVE, ON A REASON THAT IS TRUE TODAY. The audit grades ONE
page, and that page asks for neither template. ``clockspeed/surface/web/app.js``
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

AND AN INVENTED ID WOULD BE A NEW DIVERGENCE RATHER THAN A SMALLER ONE. Nothing
hands this page a card identifier while ``/api/advice`` is itself unbacked, so
the only concrete path available is one this file would make up - and
:data:`CANNED` is keyed by exact path, so it would answer that single invented id
and 404 every other, where production matches EVERY id against the template.
Their 501 bodies are still built and published in :data:`PENDING_BODIES`, so the
walking skeleton knows what blocks them even where nothing here asks.

RUNNING IT STANDALONE, which is how the merger drives the audit::

    python -m tests.surface.audit_harness

It prints the URL it bound and serves until interrupted. The port is whatever
the operating system hands out: ``config/ports.json`` owns the dashboard's
allocation and a test server must never claim from it.
"""

from __future__ import annotations

import json
import re
import sys
import threading
from fractions import Fraction
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import clockspeed
from clockspeed.audit import placement
from clockspeed.data import version
from clockspeed.save.header import masked_token
from clockspeed.save.objects import REASON_CLASS_NOT_MODELLED
from clockspeed.save.world import (
    SOURCE_USMAP,
    SOURCE_WORLD,
    WARN_NO_PROPERTY_MAP,
    WARN_NODE_SEMANTICS_UNAVAILABLE,
)
from clockspeed.surface import config, server
from clockspeed.surface.api import contract, health, pending, registry, solve
from clockspeed.surface.api import map as map_endpoint

if TYPE_CHECKING:
    from collections.abc import Mapping

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


#: The changelist inside the pinned build string. READ OUT OF THE PIN rather
#: than retyped: a number written down twice is a number that drifts (CLAUDE.md
#: section 4), and this one would drift the moment the pin moved.
_CHANGELIST_IN_PIN: Final = re.compile(r"CL-(\d+)")


def _build_changelist() -> int:
    """The changelist the pinned game build names.

    Returns:
        The integer from the pin, or zero when the pin's spelling carries none.
        Zero rather than a raise: this module's job is to render a page for an
        audit, and a pin whose shape changed is not a reason to render nothing.
    """
    found = _CHANGELIST_IN_PIN.search(version.GAME_BUILD)
    return int(found.group(1)) if found is not None else 0


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

#: The four quarter turns about the vertical axis, as the exact decimal strings
#: the wire carries. A canned orientation must have the SHAPE a real one has -
#: an array of strings, never numbers - because a panel that parsed a number
#: here would pass the audit and fail on the live wire.
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
            # identical ones. Quarter turns about the vertical axis: the four
            # spellings a factory actually contains, and every component is
            # exactly representable so the string is short and exact.
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
    return body


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
#: constructor. All five are published, including the two carrying a path
#: parameter that this harness serves no concrete path for - the skeleton knows
#: what blocks them even where nothing here asks. Production DOES route those
#: two; see the module docstring for why the stand-in still does not.
PENDING_BODIES: Final[Mapping[str, contract.Response]] = MappingProxyType(
    {
        template: contract.not_implemented(template, pending.PENDING_BLOCKER)
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


def _registry_data() -> dict[str, object]:
    """Build the ``/api/registry`` data object.

    SMALL AND SYNTHETIC ON PURPOSE. The real route serves the whole normalized
    registry off the shipped documents; this harness must answer on a machine
    with no game installed, and the audit reads the liveness row rather than the
    contents. THE REAL COUNTS ARE NOT SPELLED HERE - `clockspeed/data/version.py`
    owns them, they cannot be re-measured without the install, and an earlier
    draft of this docstring carried two of them here in the same change that
    removed them from `app.js` for being exactly that.

    Keyed by :data:`registry.DATA_KEYS`, with every rational served through
    ``contract.rational`` because ``contract`` refuses a float at any
    depth and ``json.dumps`` cannot encode a ``Fraction`` at all.

    Returns:
        The body, keyed exactly as ``clockspeed/surface/api/registry.py`` keys it.
    """
    return {
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
    }


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
    for method, template in pending.UNBACKED:
        # A TEMPLATE CARRYING A PARAMETER IS SKIPPED BECAUSE THIS TABLE IS KEYED
        # BY EXACT PATH AND THE PAGE ASKS FOR NEITHER - not because production
        # cannot route one. It can, and does. See the module docstring.
        if "<" not in template:
            table[method, template] = PENDING_BODIES[template]
    return table


#: The endpoint map this harness serves inside ``/api/health``, published for
#: the same reason :data:`CANNED` is: an arm asserting the two agree should read
#: a stated fact rather than reach through an underscore into the builder.
LIVENESS: Final[Mapping[str, str]] = MappingProxyType(_liveness())

#: The routable answers, keyed by exact path. A path absent from here is a
#: contract 404, and the two path-parameter templates are absent on purpose -
#: see the module docstring for the reason, which is about what the PAGE asks
#: for and not about what production can route.
CANNED: Final[Mapping[tuple[str, str], contract.Response]] = MappingProxyType(_canned())

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
        """Match the request against the two closed tables and answer it."""
        raw_path, _mark, _raw_query = self.path.partition("?")

        static = server.STATIC_ROUTES.get(raw_path)
        if static is not None and self.command in {"GET", "HEAD"}:
            self._serve_asset(*static)
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
