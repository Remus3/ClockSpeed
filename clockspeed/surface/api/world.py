"""``/api/world`` - the current parsed world state, serialized by an ALLOW-LIST.

Owns (BOOTSTRAP.md section 7.1): the JSON rendering of one
``clockspeed.save.world.WorldModel``, and nothing else. It computes nothing, it
opens nothing, and it obtains the world through the provider the server binds
into it rather than by reading a save.

THIS IS THE ENDPOINT A REAL SAVE REACHES THE WIRE THROUGH. On this machine the
server auto-detects and loads the operator's own save at startup, so every value
named below is derived from a personal-data-bearing artifact (non-negotiables 11
and 12) rather than from a hypothetical one.

THE BODY IS BUILT BY NAMING EVERY FIELD, ONE AT A TIME, AND THAT IS THE WHOLE
DESIGN. There is no ``dataclasses.asdict``, no ``astuple``, no ``vars()``, no
``__dict__`` read and no ``dataclasses.fields`` walk anywhere in this module,
and ``tests/surface/test_world.py`` asserts that on the shipped AST together
with the COMPLETE set of attribute names read here. A generic walker is
precisely how the save header's options string - which carries a platform
account identifier and the player's display name in plaintext - ships the day
somebody adds it to ``SaveHeader``. Naming fields means adding a field is a
decision somebody makes; walking them means it is a decision nobody makes.

WHAT IS DELIBERATELY WITHHELD, AND WHY EACH ONE IS NOT AN OVERSIGHT:

  the raw token          ``clockspeed/save/world.py`` declares it PERSONAL
                         DATA, forbidden in every tracked file, log line and
                         error message. Only ``masked_token`` crosses the wire,
                         which answers the only question a reader has of it -
                         whether two responses are about the SAME world.
  ``map_name``           A game constant, documented as one, and still withheld.
                         ``SaveHeader.__repr__`` omits it and says why: its
                         POSITION is version dependent, so a dispatch bug puts
                         an operator-authored string in it, and a response body
                         is exactly the surface that has to stay safe when the
                         parse is wrong.
  the two time fields    ``datetime_ticks`` and ``play_duration`` are when the
                         operator last played and for how long. Behavioural
                         data no advice needs.
  every node string      ``ResourceNode.instance_name`` is world content and is
                         withheld from that type's own repr. Nodes are counted
                         and never listed; their coordinates are float32 and a
                         bare JSON number is the IEEE double non-negotiable 6
                         keeps out of the answer path.
  every record string    ``ObjectRecord``'s repr withholds every string because
                         a save body holds the world's contents and its actor
                         names. Records are counted and never listed.
  any filesystem path    This endpoint takes no parameters and names no path.

THE ONE DELIBERATE ASYMMETRY: ``UnknownClass.type_path`` IS served while
``ObjectRecord.type_path`` is NOT. They are the same spelling and different
things. A class path comes from the asset registry - game or mod content, which
``clockspeed/save/usmap.py`` records is publisher-owned and not personal data.
An instance list is a census of the operator's own factory. Reporting
unmodelled classes is not a concession to convenience; it IS non-negotiable 7's
purpose, and BOOTSTRAP.md section 9 requires an explicit "this world contains
content I do not model" rather than a quiet partial answer.

NO WORLD IS 503, NEVER 501. The save layer is written, is eleven thousand lines
and works; what is absent is its INPUT. Rendering that as 501 would tell the
operator the save reader has not been built - see the 501/503 split in
``clockspeed/surface/api/contract.py``, which must not collapse.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# THE WORLD ARRIVES THROUGH THE PROVIDER, NEVER THROUGH A FILE. The package
# docstring forbids this package from opening anything at all - not a save, not
# the raw docs, not the install - so `load_world` is not called here and is not
# imported. The server obtains the world and binds the provider into the
# handler by closure, which is also why nothing here imports the server.
#
# The ONE runtime name taken from the save layer is `masked_token`, and taking
# it is strictly better than the alternative. The mask is the redaction control
# `clockspeed/save/header.py` owns; re-deriving a digest here would be the same
# fact written in two places, and a hand-rolled one that is subtly wrong looks
# identical to a correct one. `WorldModel` itself is named for typing only and
# is not imported at runtime.

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.save.header import masked_token
from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.world import WorldModel

__all__ = [
    "COUNT_KEYS",
    "DATA_KEYS",
    "ENDPOINT",
    "UNKNOWN_CLASS_KEYS",
    "UNLOCK_KEYS",
    "WARNING_KEYS",
    "make_handler",
]

#: The route template this endpoint answers. A literal authored here, never a
#: path read off a request line.
ENDPOINT: Final = "/api/world"

#: Exactly the top-level keys a success body carries. Published so a test can
#: bind the shape to the builder and so neither can drift from the other.
DATA_KEYS: Final = (
    "world",
    "header_version",
    "save_version",
    "build_changelist",
    "body_offset",
    "is_modded",
    "counts",
    "contains_unmodeled_content",
    "unlocks",
    "warnings",
    "unknown_classes",
)

#: What is counted rather than listed. Every one of these names a collection
#: whose ELEMENTS carry world content or actor names.
COUNT_KEYS: Final = ("objects", "levels", "nodes", "unknown_classes", "warnings")

#: The unlock summary's keys.
UNLOCK_KEYS: Final = (
    "purchased_schematics",
    "recipes",
    "scanned_resources",
    "current_game_phase",
    "feature_flags",
    "is_empty",
)

#: One carried advisory's keys. Every value here is authored by the layer that
#: raised it: ``detail`` is a fixed line never built from content, and
#: ``subject`` is a structural token never a name read out of a file.
WARNING_KEYS: Final = ("source", "code", "detail", "subject", "count")

#: One unmodelled class's keys - the asymmetry the module docstring states.
UNKNOWN_CLASS_KEYS: Final = ("type_path", "count", "reason", "first_index")


def _counts(model: WorldModel) -> dict[str, int]:
    """Count the five collections whose elements are never serialized.

    Args:
        model: The world.

    Returns:
        The counts, keyed by :data:`COUNT_KEYS`.
    """
    objects = model.objects
    return {
        "objects": len(objects.records),
        "levels": objects.level_count,
        "nodes": len(model.nodes),
        "unknown_classes": len(objects.unknown_classes),
        "warnings": len(model.warnings),
    }


def _unlocks(model: WorldModel) -> dict[str, object]:
    """Summarize the unlock state: three sizes, a phase and the feature flags.

    THE THREE COLLECTIONS ARE COUNTED RATHER THAN LISTED. A schematic path and a
    recipe path are game content and would be safe, but the sizes are what any
    advice actually needs and a walking skeleton does not earn the wider
    surface. The feature flags ARE named, because a rule that requires
    overclock availability cannot fire without knowing the flag.

    Args:
        model: The world.

    Returns:
        The summary, keyed by :data:`UNLOCK_KEYS`.
    """
    unlocks = model.unlocks
    flags = {name: bool(value) for name, value in unlocks.feature_flags.items()}
    return {
        "purchased_schematics": len(unlocks.purchased_schematics),
        "recipes": len(unlocks.recipes),
        "scanned_resources": len(unlocks.scanned_resources),
        "current_game_phase": unlocks.current_game_phase,
        "feature_flags": flags,
        "is_empty": unlocks.is_empty,
    }


def _warnings(model: WorldModel) -> list[dict[str, object]]:
    """Render every carried advisory, in the order the load produced them.

    Args:
        model: The world.

    Returns:
        One mapping per warning, keyed by :data:`WARNING_KEYS`.
    """
    return [
        {
            "source": warning.source,
            "code": warning.code,
            "detail": warning.detail,
            "subject": warning.subject,
            "count": warning.count,
        }
        for warning in model.warnings
    ]


def _unknown_classes(model: WorldModel) -> list[dict[str, object]]:
    """Render every class path the supplied registry did not resolve.

    THE ASYMMETRY LIVES HERE. This is the one place a ``type_path`` crosses the
    wire, and the module docstring states why it may: a class path is asset
    registry content, while the instance list carrying the same spelling is a
    census of the operator's own factory.

    Args:
        model: The world.

    Returns:
        One mapping per unmodelled class, keyed by :data:`UNKNOWN_CLASS_KEYS`.
    """
    return [
        {
            "type_path": unknown.type_path,
            "count": unknown.count,
            "reason": unknown.reason,
            "first_index": unknown.first_index,
        }
        for unknown in model.objects.unknown_classes
    ]


def _body(model: WorldModel) -> dict[str, object]:
    """Build the success body by naming every field it carries.

    Args:
        model: The world.

    Returns:
        The body, keyed by :data:`DATA_KEYS`.
    """
    header = model.header
    return {
        "world": masked_token(model.token),
        "header_version": header.header_version,
        "save_version": header.save_version,
        "build_changelist": header.build_changelist,
        "body_offset": header.body_offset,
        "is_modded": header.is_modded,
        "counts": _counts(model),
        "contains_unmodeled_content": model.contains_unmodeled_content,
        "unlocks": _unlocks(model),
        "warnings": _warnings(model),
        "unknown_classes": _unknown_classes(model),
    }


def make_handler(worlds: contract.WorldProvider[WorldModel]) -> contract.Handler:
    """Bind a world provider and return the handler that answers this route.

    THE PROVIDER IS BOUND BY CLOSURE RATHER THAN PASSED PER REQUEST, which is
    the shape ``contract.Handler`` publishes: the server binds what an endpoint
    needs before registering it, so this module never imports the server and
    never learns how a world was obtained.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request.

        Args:
            query: The parsed query parameters. This endpoint accepts none.

        Returns:
            200 with the world, 503 when this machine has no save to read, or
            400 when the request named a parameter. The 400 reflects NOTHING of
            what it refused - on this machine a query value can be a save path
            or an account directory.
        """
        if query:
            return contract.bad_request(ENDPOINT, contract.REASON_UNKNOWN_PARAMETER)
        model = worlds.world()
        if model is None:
            return contract.unavailable(ENDPOINT, contract.REASON_NO_SAVE)
        return contract.ok(ENDPOINT, _body(model))

    return handle
