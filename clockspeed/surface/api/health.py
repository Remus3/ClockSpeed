"""``/api/health`` - is the server up, what is it, and what is wired to it.

Owns (BOOTSTRAP.md section 7.1): the liveness answer. It computes nothing, it
opens nothing, and it reports presence as a WORD rather than as a location.

HEALTH ANSWERS 200 AND NOTHING ELSE, EVER. It is what the companion window
polls and what the operator reaches for when something is already wrong, so an
endpoint that can answer 503 has made "is the server up" unanswerable at
exactly the moment the question is asked. Absence is reported INSIDE the 200
body, which is why the two presence fields are enums rather than codes. A
parameter this endpoint does not accept is ignored rather than refused, for the
same reason: a probe that 400s on a stray query string is a probe nobody can
rely on.

HEALTH NAMES NO PATH. "Is there a registry" and "is there a world" are answered
``present``/``absent`` and ``loaded``/``absent``. The save directory is named
after a numeric platform account id and the install path contains the Windows
account name, so a health body that answered WHERE either one was found would
publish both (non-negotiable 3, and the privacy constraint
``clockspeed/surface/api/__init__.py`` says this layer carries alone).

NOTHING THE SERVER HANDS THIS HANDLER REACHES THE WIRE. The route templates
published below are literals authored in this repository, and the body is built
by looking each one up - so a liveness map keyed by raw request paths, which on
this machine can be a save path, cannot publish a key. The value is narrowed to
a closed two-word vocabulary on the way out for the same reason. The map is also
TOTAL: a template the server never registered reads as not implemented rather
than vanishing, so a client always sees one key per published template and never
has to tell an absent key from an unknown route.

THE TEMPLATE LIST IS BOOTSTRAP.md SECTION 7.1'S, AND THE ANTI-DRIFT ARM LIVES
IN THE TESTS. This package opens no file, so the list cannot be read from the
specification at runtime; ``tests/surface/test_health.py`` reads that section
and asserts the two agree, exactly as ``tests/surface/test_contract.py`` pins
``contract.OPEN_BLOCKERS`` to the OPEN item lines of ``ROADMAP.md``. When
section 7.1 grows a route, the arm goes red rather than the body going quietly
stale - and it did: the tenth arrived with CS-912, and every count in the suite
had to be moved by hand because that is what the arm is FOR. THE COUNT IS NOT
WRITTEN DOWN HERE, deliberately; the tuple below is the one place it exists.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Both presences arrive through the providers the server binds by closure, so
# this module never imports the server and never asks the filesystem anything.
# The two version facts are READ FROM THEIR OWNERS - `clockspeed.__version__`
# and `clockspeed.data.version.GAME_BUILD` - and are never restated here. A
# version written down twice is a fact that will drift (CLAUDE.md section 4).

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import clockspeed
from clockspeed.data import version
from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "ABSENT",
    "DATA_KEYS",
    "ENDPOINT",
    "ENDPOINT_TEMPLATES",
    "LIVE",
    "LIVENESS_WORDS",
    "LOADED",
    "NOT_LIVE",
    "PRESENCE_WORDS",
    "PRESENT",
    "make_handler",
]

#: The route template this endpoint answers.
ENDPOINT: Final = "/api/health"

#: A registry was found on this machine.
PRESENT: Final = "present"

#: Nothing was found. The SAME word for a missing registry and a missing world,
#: because the two questions have the same two answers and a reader should not
#: have to learn a second vocabulary for the second field.
ABSENT: Final = "absent"

#: A world is loaded. Spelled apart from ``present`` because a world is loaded
#: rather than found - the registry exists on disk, the world exists in memory.
LOADED: Final = "loaded"

#: Presence is a two-value enum. A third value is somewhere for a location to
#: hide, which is the whole failure this vocabulary exists to prevent.
PRESENCE_WORDS: Final = (PRESENT, ABSENT)

#: The route is registered and answers.
LIVE: Final = "live"

#: The route is not registered, or the layer beneath it has not been built.
NOT_LIVE: Final = "not_implemented"

#: Liveness is a two-value enum, narrowed on the way out so nothing a caller
#: supplied can be published verbatim.
LIVENESS_WORDS: Final = (LIVE, NOT_LIVE)

#: Every route BOOTSTRAP.md section 7.1 publishes, in that section's order.
#: ``/api/plan`` appears there as ``/api/plan?target=<milestone>``; the query
#: string is the QUESTION a caller asks, not part of the route, and
#: ``contract.ENDPOINT_PATTERN`` refuses one outright.
#:
#: THE SECTION SAYS "MINIMUM", AND ``/api/registry`` IS WHAT THAT WORD BOUGHT
#: (CS-912). It sits beside ``/api/world`` because the two answer the same kind
#: of question - what is on this machine - and because it must precede the two
#: solver doors that consume its vocabulary: with a registry present and no such
#: route, MEASURED ZERO of the templates then published named a single item or
#: recipe identifier in any body, so both solver doors were live and unreachable
#: at once.
#:
#: ``/api/map`` ARRIVED THE SAME WAY, UNDER THE SAME WORD (CS-977), AND SITS
#: LAST. It CONSUMES both routes above it - a world from the save layer and the
#: extractor vocabulary from the registry - so CS-912's own argument puts it
#: after them, and last is after them. Appending rather than inserting is also
#: what kept the page's route table (``clockspeed/surface/web/app.js``, bound to
#: this tuple by EQUALITY in ``tests/surface/test_route_table_binding.py``) from
#: needing an edit in a slice that did not own it.
#:
#: ``/api/power`` IS THE THIRD ARRIVAL UNDER THE SAME WORD, AND IT SITS LAST FOR
#: THE SAME REASON ``/api/map`` DOES. It CONSUMES ``/api/registry`` - a power
#: question is asked about a building, and the building vocabulary comes from
#: there - so CS-912's own argument puts it after that route, and last is after
#: it. ``clockspeed/solve/power.py`` was written, tested and reachable from NO
#: route: MEASURED ZERO of the templates above it named a megawatt figure, a
#: clock or the un-sharded base in any body, so the whole power half of the
#: solve layer was live and unaskable at once - which is the same fault CS-912
#: and CS-977 each found, wearing a third face.
ENDPOINT_TEMPLATES: Final = (
    "/api/health",
    "/api/world",
    "/api/registry",
    "/api/advice",
    "/api/advice/<id>/derivation",
    "/api/advice/<id>/state",
    "/api/solve",
    "/api/optimize",
    "/api/audit",
    "/api/plan",
    "/api/map",
    "/api/power",
)

#: Exactly the keys a health body carries.
DATA_KEYS: Final = ("app_version", "game_build_pin", "registry", "world", "endpoints")


def _liveness(endpoint_status: Mapping[str, str]) -> dict[str, str]:
    """Render the route table as one key per published template, two-word values.

    TOTAL BY CONSTRUCTION, IN BOTH DIRECTIONS. The keys come from
    :data:`ENDPOINT_TEMPLATES` and never from the mapping, so a key the caller
    supplied cannot be published; and every value is narrowed to
    :data:`LIVENESS_WORDS`, so a value the caller supplied cannot be either.
    A template the mapping does not mention reads as not implemented, which is
    the honest answer for a route the server did not register.

    Args:
        endpoint_status: What the server says about its own route table. Extra
            keys are ignored and missing keys read as not implemented, so this
            never has to refuse anything and never raises.

    Returns:
        One entry per published template.
    """
    return {
        template: LIVE if endpoint_status.get(template) == LIVE else NOT_LIVE
        for template in ENDPOINT_TEMPLATES
    }


def make_handler(
    worlds: contract.WorldProvider[object],
    registries: contract.RegistryProvider[object],
    endpoint_status: Mapping[str, str],
) -> contract.Handler:
    """Bind both providers and the server's route table, and return the handler.

    THE PROVIDERS ARE BOUND BY CLOSURE, which is the shape ``contract.Handler``
    publishes. The route table is bound the same way and for a stronger reason:
    the server is the only thing that knows which routes it registered, so
    reading that from a list written in this module would be the same fact in
    two places - and the copy here would be the one that went stale.

    The world and registry types are not named. This endpoint asks each provider
    one question - is there one - and holding a save-layer type to ask it would
    reach past three layers to spell an annotation it does not use.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        endpoint_status: The server's own view of which routes are live.

    Returns:
        The handler.
    """

    def handle(_query: Mapping[str, str]) -> contract.Response:
        """Answer one request. Always 200.

        The query is ignored rather than validated - see the module docstring.

        Args:
            _query: The parsed query parameters, unused.

        Returns:
            The 200 response.
        """
        return contract.ok(
            ENDPOINT,
            {
                "app_version": clockspeed.__version__,
                "game_build_pin": version.GAME_BUILD,
                "registry": PRESENT if registries.registry() is not None else ABSENT,
                "world": LOADED if worlds.world() is not None else ABSENT,
                "endpoints": _liveness(endpoint_status),
            },
        )

    return handle
