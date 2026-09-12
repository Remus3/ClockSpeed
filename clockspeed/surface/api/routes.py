"""The whole route table, assembled once, from the endpoint modules beside it.

Owns (BOOTSTRAP.md section 7.1): which endpoint module answers which template,
and the server's own view of which of those templates are live.

THIS IS THE ONLY MODULE IN THE PACKAGE THAT KNOWS EVERY ENDPOINT AT ONCE, and it
is deliberately the only one. Every module beside it publishes its own routes and
imports none of its siblings, so each stays gradeable on its own; the cost of
that is that something has to join them, and this is that something. It computes
nothing, opens nothing and decides nothing about a response - it names.

THE TABLE IS BUILT AT IMPORT AND NOT PER CALL. :data:`ROUTES` is a module
constant, so its members are the same objects on every read. A function that
rebuilt the table would hand a fresh :class:`~clockspeed.surface.api.contract.Route`
to every caller, and a caller holding one from an earlier build - the server's
routing table, say, against a health body's liveness map - would be comparing
objects that are equal to nothing. Building once also means the closures each
handler holds are created once, which is what makes "is this the route the
server registered" an identity question rather than a value question.

THE ORDER IS THE SPECIFICATION'S ORDER, JOINED RATHER THAN RESTATED.
``clockspeed/surface/api/health.py`` already publishes every template in
``BOOTSTRAP.md`` section 7.1's order, because its liveness body is keyed by them;
this module orders its table by that same tuple rather than writing a second copy
of the sequence. Two copies of an ordering is exactly the drift the doc topology
rule exists to stop, and here it would be silent: a table in a different order
still holds the same number of routes. THE COUNT IS NEVER WRITTEN DOWN IN THIS
MODULE, deliberately - ``health.ENDPOINT_TEMPLATES`` is its one owner, and
CS-912's tenth route moved it without editing a literal here, as CS-977's
eleventh did again.

THE ASSEMBLY IS TOTAL IN BOTH DIRECTIONS, CHECKED AT IMPORT. A published
template with no route, or a route whose template is not a published one, raises
:class:`RouteAssemblyError` before the module finishes loading. Refusing at
import rather than at request time means the failure lands where a developer is
looking - a failed import - instead of as a 404 on one endpoint that nobody
drives until later.

THE 405 BOUNDARY ROUTES ARE PUBLISHED APART FROM THE REST, and that separation is
load-bearing rather than tidy. ``/api/advice/<id>/state`` answers POST; a GET on
it is a wrong verb on a real resource, which is 405 and not 501. That boundary
needs a second route on a template the published set already carries, so folding
the two sets together would produce a table with one more entry than there are
templates, in which one template appears twice. Anything reading the table as
``{route.template: route.method}`` - which is how the acceptance module reads it
- would silently keep whichever of the two iteration reached last, and the count
would still look right.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract, health, pending, solve, world
from clockspeed.surface.api import map as map_endpoint
from clockspeed.surface.api import registry as registry_endpoint
from clockspeed.surface.providers import InstalledRegistryProvider, SaveWorldProvider

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

__all__ = [
    "ENDPOINT_STATUS",
    "METHOD_BOUNDARY_ROUTES",
    "ROUTES",
    "SERVING_ROUTES",
    "RouteAssemblyError",
    "build_routes",
]

#: The verb ``/api/health`` and ``/api/world`` answer. Spelled here because those
#: two modules publish an endpoint constant and no method constant - a handler
#: does not know what verb reached it - so this is the single place either
#: route's verb exists. EVERY OTHER TEMPLATE ARRIVES CARRYING ITS OWN, and
#: ``clockspeed/surface/api/registry.py`` was written that way on purpose so this
#: constant's claim about which two routes need it stayed true when the tenth
#: route landed (CS-912) and when the eleventh did (CS-977) -
#: ``clockspeed/surface/api/map.py`` publishes its own ``METHOD_GET`` too.
METHOD_GET: Final = "GET"

#: Every template with a layer beneath it today. Read from the endpoint modules'
#: own constants rather than written out, so a module that renames its endpoint
#: moves one literal. The complement of this set within
#: :data:`health.ENDPOINT_TEMPLATES` is the unbuilt half, which is why the
#: unbuilt half is never spelled here at all.
BACKED_TEMPLATES: Final = (
    health.ENDPOINT,
    world.ENDPOINT,
    registry_endpoint.ENDPOINT,
    solve.SOLVE_ENDPOINT,
    solve.OPTIMIZE_ENDPOINT,
    map_endpoint.ENDPOINT,
)

#: What the server says about its own route table, in the two words
#: ``clockspeed/surface/api/health.py`` narrows to. DERIVED FROM THE PARTITION
#: rather than hand-listed: a template this module could not build a backed route
#: for reads not implemented, which is the honest answer and is also what a
#: hand-written map would eventually stop saying.
#:
#: A ``MappingProxyType`` rather than a ``dict`` because it is bound into the
#: health handler by closure and lives for the process. A plain dict there would
#: let anything holding a reference rewrite what the server reports about itself.
ENDPOINT_STATUS: Final[Mapping[str, str]] = MappingProxyType(
    {
        template: health.LIVE if template in BACKED_TEMPLATES else health.NOT_LIVE
        for template in health.ENDPOINT_TEMPLATES
    }
)


class RouteAssemblyError(RuntimeError):
    """The route table does not cover the published endpoint set exactly once.

    Raised at import. Carries a fixed line and the offending TEMPLATES, which are
    literals authored in this repository - no request value and no path from this
    machine can reach a route template, so naming them here is safe in a way that
    naming a request path would not be.
    """


def _checked(routes: tuple[contract.Route, ...]) -> tuple[contract.Route, ...]:
    """Return the routes, or refuse a table that is not a bijection onto the set.

    Args:
        routes: The assembled table, one route per published template.

    Returns:
        The routes, unchanged.

    Raises:
        RouteAssemblyError: A published template has no route, a route names a
            template that is not published, or a template is claimed twice.
    """
    published = frozenset(health.ENDPOINT_TEMPLATES)
    claimed = [route.template for route in routes]

    unknown = sorted(frozenset(claimed) - published)
    if unknown:
        raise RouteAssemblyError(f"a route names a template section 7.1 does not: {unknown}")

    missing = sorted(published - frozenset(claimed))
    if missing:
        raise RouteAssemblyError(f"section 7.1 names a template with no route: {missing}")

    twice = sorted({template for template in claimed if claimed.count(template) > 1})
    if twice:
        raise RouteAssemblyError(f"a template is claimed by more than one route: {twice}")

    return routes


def build_routes(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
) -> tuple[contract.Route, ...]:
    """Assemble one route per published template, with the providers bound in.

    THE PROVIDERS ARE PARAMETERISED CONCRETELY, AND THAT IS THIS MODULE'S JOB
    RATHER THAN A TIGHTENING FOR ITS OWN SAKE. Both protocols are GENERIC in
    ``contract.py`` so that the endpoint package names no layer below its
    neighbour, and that module's docstring says where the concrete name belongs:
    "the endpoint that actually holds a world parameterises the protocol at its
    own use site". This is a use site - it is the module that binds a provider
    into a handler - so the names land here, under ``TYPE_CHECKING``, exactly as
    ``world.py`` and ``solve.py`` already spell them for the handlers below.

    ``[object]`` HERE WAS A FALSE STATEMENT ABOUT THIS FUNCTION'S OWN CONTRACT.
    It advertised that any provider of anything would do, and then handed the
    value to ``world.make_handler``, which reads counts, unlocks and warnings
    off it as a ``WorldModel``, and to ``solve.routes``, which solves against it
    as a ``Registry``. A provider of ``object`` satisfying that signature would
    have been accepted here and failed there. ``health.make_handler`` keeps
    ``[object]`` and is right to: it asks only WHETHER each exists and never
    touches the value, and both protocols are covariant, so a concrete provider
    is accepted there unchanged.

    THE PROVIDERS ARRIVE AS ARGUMENTS AND ARE NOT RESOLVED HERE. This module is
    imported by the acceptance suite on a machine that may have neither a game
    nor a save, so a resolution step at assembly time would make importing the
    table an act that touches the filesystem. Every provider this project ships
    is lazy - it stores callables and reads nothing until asked - so binding them
    in costs nothing until a request arrives.

    Args:
        worlds: Whatever hands up the current world, or says there is not one.
        registries: Whatever hands up the registry, or says there is no install.

    Returns:
        One route per published template, in ``BOOTSTRAP.md`` section 7.1's order.

    Raises:
        RouteAssemblyError: The table is not a bijection onto the published set.
    """
    assembled = (
        contract.Route(
            method=METHOD_GET,
            template=health.ENDPOINT,
            handler=health.make_handler(worlds, registries, ENDPOINT_STATUS),
        ),
        contract.Route(
            method=METHOD_GET,
            template=world.ENDPOINT,
            handler=world.make_handler(worlds),
        ),
        *registry_endpoint.routes(registries),
        # THE ONE ROUTE BESIDES HEALTH THAT TAKES BOTH PROVIDERS. A map is a
        # world joined against the registry - the display names and the
        # extraction rates come from one, everything else from the other -
        # and it answers 200 with a stated gap when the registry is absent
        # rather than refusing, because the geometry is true without one.
        *map_endpoint.routes(worlds, registries),
        *solve.routes(registries),
        *pending.routes(),
    )
    order = health.ENDPOINT_TEMPLATES
    ordered = tuple(sorted(_checked(assembled), key=lambda route: order.index(route.template)))
    return _checked(ordered)


#: The published set, bound to the providers this machine runs. Built once, at
#: import, so every reader sees the same objects - see the module docstring.
ROUTES: Final = build_routes(SaveWorldProvider(), InstalledRegistryProvider())

#: The routes that exist only to say the verb is wrong. Provider-free, so these
#: are shared by every table rather than rebuilt per provider set.
METHOD_BOUNDARY_ROUTES: Final = pending.method_boundary_routes()

#: What a server is handed: the published set first, in specification order, then
#: the boundary. A server that synthesises 405 from a template match needs only
#: the published set and answers identically either way, because both go through
#: ``contract.method_not_allowed``.
SERVING_ROUTES: Final = ROUTES + METHOD_BOUNDARY_ROUTES
