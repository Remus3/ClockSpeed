"""``/api/registry`` - the normalized registry, serialized by an ALLOW-LIST.

Owns (BOOTSTRAP.md section 7.1): the JSON rendering of one
``clockspeed.data.registry.Registry``, and nothing else. It computes nothing, it
opens nothing, and it obtains the registry through the provider the server binds
into it rather than by reading the game install.

WHY THIS ROUTE EXISTS AT ALL, AND WHAT WAS BROKEN WITHOUT IT (CS-912).
``/api/solve`` and ``/api/optimize`` both require ``targets``, ``recipes`` and
``raw_items``, and every value in all three is a registry ClassName. MEASURED on
the route table this endpoint joins, before it joined it: with a registry
present, ZERO of the routes then published named a single item or recipe
identifier in any response body. Both solver doors were therefore LIVE and
UNREACHABLE at once - a caller could not name a target without inventing an
identifier, and an invented identifier is exactly what
``clockspeed/solve/ratio.py`` refuses as a caller shape bug. This route
publishes the vocabulary the other two consume, and
``tests/surface/test_registry.py`` drives a whole solve built from nothing but
one response of this one.

THE BODY IS BUILT BY NAMING EVERY FIELD, ONE AT A TIME, AND THAT IS THE WHOLE
DESIGN. There is no ``dataclasses.asdict``, no ``astuple``, no ``vars()``, no
``__dict__`` read and no ``dataclasses.fields`` walk anywhere in this module, and
``tests/surface/test_registry.py`` asserts that on the shipped AST against five
planted walkers. ``clockspeed/surface/api/world.py`` states the rule this
inherits: a generic walker ships whatever field somebody adds upstream, so adding
a field becomes a decision NOBODY makes. The risk is not hypothetical here -
``Building`` already carries five power measurements and ``Recipe`` two more, and
every one of them is a ``Fraction`` that a walker would hand to ``json.dumps``,
which cannot serialize one at all.

EVERY RATE LEAVES AS ``{"num": n, "den": d}``, WHICH IS NON-NEGOTIABLE 6 AT THE
SURFACE. ``Recipe.duration``, ``RecipeIO.amount`` and ``Item.energy_value`` are
all exact ``Fraction`` values, and one of the measured fluid amounts in the
shipped document is genuinely fractional. As a bare JSON number a browser reads
that as an IEEE double; ``contract.rational`` transcribes it as two integers and
divides nothing, because ``surface/`` never computes and a division here would
manufacture the exact float the spelling exists to prevent. An ABSENT
measurement stays ``null`` rather than becoming a zero: ``Item.energy_value`` is
None on most entries and a confident zero is what a plan cannot detect.

WHAT IS DELIBERATELY WITHHELD, AND WHY EACH IS NOT AN OVERSIGHT:

  every power field      ``Building`` carries a declared draw, an exponent, an
                         estimated range and an unsharded clock base, and
                         ``Recipe`` carries two variable-power terms. Serving
                         them is a power-modelling surface with its own
                         questions - ADR 0005 and ADR 0006 record that the
                         overclock ceiling is NOT derivable from any file on this
                         machine - and a walking skeleton does not earn it. What
                         this route owes ``/api/solve`` is the IDENTIFIERS, and
                         a building is here so a ``produced_in`` token has a name
                         to render rather than so a plan can be priced.
  any filesystem path    This endpoint takes no parameters and names no path.
  anything save-derived  A registry is built from the shipped document alone. No
                         value below can have come from a save file, which is why
                         nothing here is redacted and nothing here needs to be.

THE ORDER IS THE REGISTRY'S OWN AND IS NOT SORTED HERE. ``build_registry``
inserts in document order and ``clockspeed/solve/ratio.py`` states that solve
variables run in registry order regardless, so re-ordering on the way out would
be this layer deciding something its neighbour already decided - and would make
the page's list disagree with the solver's. Two builds of one document produce
the same order, so the wire stays byte-deterministic (CLAUDE.md section 1).

UNMODELLED CONTENT IS PUBLISHED, NOT HIDDEN. ``warnings`` and ``unknown_groups``
cross the wire for the reason non-negotiable 7 exists: a body that served the
clean half and dropped the flagged half is a quiet partial answer wearing a
complete one's face. A recipe side naming an item this registry holds no
descriptor for is served AS IT STANDS, because erasing it would turn a flagged
gap into a silently wrong recipe.

NO REGISTRY IS 503, NEVER 501. ``clockspeed/data/registry.py`` is written and
builds a real registry; what is absent on a machine with no game is its INPUT.
Rendering that as 501 would report the data layer as unwritten - see the 501/503
split in ``clockspeed/surface/api/contract.py``, which must not collapse.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# THE REGISTRY ARRIVES THROUGH THE PROVIDER, NEVER THROUGH A FILE. The package
# docstring forbids this package from opening anything at all - not a save, not
# the raw docs, not the install - so `build_registry` is not called here and is
# not imported. The server obtains the registry and binds the provider into the
# handler by closure, which is also why nothing here imports the server.
#
# `clockspeed.data.registry`'s types are named ONLY under TYPE_CHECKING, to
# parameterise `contract.RegistryProvider` at the use site the way that
# protocol's docstring directs. That is naming the neighbour's model rather than
# reaching past it, and a typing-only import costs no runtime reach at all.

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping
    from fractions import Fraction

    from clockspeed.data.registry import (
        Building,
        Item,
        Recipe,
        RecipeIO,
        Registry,
        RegistryWarning,
    )

__all__ = [
    "BUILDING_KEYS",
    "COUNT_KEYS",
    "DATA_KEYS",
    "ENDPOINT",
    "ITEM_KEYS",
    "METHOD_GET",
    "RECIPE_IO_KEYS",
    "RECIPE_KEYS",
    "WARNING_KEYS",
    "make_handler",
    "routes",
]

#: The route template this endpoint answers. A literal authored here, never a
#: path read off a request line.
ENDPOINT: Final = "/api/registry"

#: The verb this route answers. Spelled HERE rather than in
#: ``clockspeed/surface/api/routes.py`` so that module's own ``METHOD_GET``
#: stays what its comment says it is - the single place ``/api/health`` and
#: ``/api/world`` state their verb - and so a module that owns an endpoint owns
#: its method too, as ``clockspeed/surface/api/solve.py`` already does.
METHOD_GET: Final = "GET"

#: Exactly the top-level keys a success body carries. Published so a test can
#: bind the shape to the builder and so neither can drift from the other.
DATA_KEYS: Final = ("items", "recipes", "buildings", "counts", "warnings", "unknown_groups")

#: One item's keys. ``form`` is served BESIDE ``is_fluid`` rather than being
#: reduced to it, because ``RF_INVALID`` is neither solid nor fluid and a
#: boolean alone cannot say so - which is the same reason
#: ``clockspeed/data/registry.py`` keeps both.
ITEM_KEYS: Final = ("key", "display_name", "form", "is_fluid", "energy_value", "sink_points")

#: One recipe's keys. ``produced_in`` names MODELLED buildings only; the
#: unresolved tokens beside it in the registry are not served, because a token
#: that resolves to nothing is a fact about the extraction rather than a producer
#: a caller can do anything with, and ``warnings`` already carries it flagged.
RECIPE_KEYS: Final = ("key", "display_name", "duration", "inputs", "outputs", "produced_in")

#: One side of one recipe. Two keys, and the amount is an exact ratio.
RECIPE_IO_KEYS: Final = ("item_key", "amount")

#: One building's keys. Deliberately the identifier and the name and nothing
#: else - see the module docstring on why no power measurement is served.
BUILDING_KEYS: Final = ("key", "display_name")

#: What the body counts. The three collections are ALSO listed in full, so these
#: are a cheap header rather than a substitute for reading them; ``warnings`` and
#: ``unknown_groups`` are counted here for the same reason
#: ``clockspeed/surface/api/world.py`` counts its own.
COUNT_KEYS: Final = ("items", "recipes", "buildings", "warnings", "unknown_groups")

#: One flagged-and-skipped piece of content. ``detail`` is a fixed line the data
#: layer authored and never builds from document content, and ``subject`` is a
#: class name, a group short name or a group index - publisher-owned content of
#: exactly the class ``clockspeed/surface/api/world.py`` already serves as
#: ``UnknownClass.type_path``, and never anything save-derived.
WARNING_KEYS: Final = ("code", "subject", "detail", "count")


def _amount(value: Fraction) -> dict[str, int]:
    """Render one exact amount as a numerator and a denominator.

    Args:
        value: The exact amount.

    Returns:
        The two integers, through the contract's own transcription.
    """
    return contract.rational(value)


def _optional_amount(value: Fraction | None) -> dict[str, int] | None:
    """Render an optional exact measurement, keeping ABSENT distinct from zero.

    Args:
        value: The exact measurement, or None when the entry declares none.

    Returns:
        The two integers, or None. None is NOT replaced by a zero: the data
        layer states that None and ``Fraction(0)`` are different facts, and a
        confident zero is the one unacceptable rendering of an absent one.
    """
    if value is None:
        return None
    return contract.rational(value)


def _side(side: RecipeIO) -> dict[str, object]:
    """Render one side of one recipe.

    Args:
        side: The normalized ingredient or product.

    Returns:
        The mapping, keyed by :data:`RECIPE_IO_KEYS`. The item key is served even
        when this registry holds no descriptor for it - see the module docstring.
    """
    return {"item_key": side.item_key, "amount": _amount(side.amount)}


def _item(item: Item) -> dict[str, object]:
    """Render one item.

    Args:
        item: The resolved item.

    Returns:
        The mapping, keyed by :data:`ITEM_KEYS`.
    """
    return {
        "key": item.key,
        "display_name": item.display_name,
        "form": item.form,
        "is_fluid": item.is_fluid,
        "energy_value": _optional_amount(item.energy_value),
        "sink_points": item.sink_points,
    }


def _recipe(recipe: Recipe) -> dict[str, object]:
    """Render one recipe.

    Args:
        recipe: The joined recipe.

    Returns:
        The mapping, keyed by :data:`RECIPE_KEYS`.
    """
    return {
        "key": recipe.key,
        "display_name": recipe.display_name,
        "duration": _amount(recipe.duration),
        "inputs": [_side(side) for side in recipe.inputs],
        "outputs": [_side(side) for side in recipe.outputs],
        "produced_in": list(recipe.produced_in),
    }


def _building(building: Building) -> dict[str, object]:
    """Render one building.

    Args:
        building: The power-consuming buildable.

    Returns:
        The mapping, keyed by :data:`BUILDING_KEYS`.
    """
    return {"key": building.key, "display_name": building.display_name}


def _warning(warning: RegistryWarning) -> dict[str, object]:
    """Render one flagged-and-skipped piece of content.

    Args:
        warning: The advisory the build raised.

    Returns:
        The mapping, keyed by :data:`WARNING_KEYS`.
    """
    return {
        "code": warning.code,
        "subject": warning.subject,
        "detail": warning.detail,
        "count": warning.count,
    }


def _counts(registry: Registry) -> dict[str, int]:
    """Count each collection the body carries.

    Args:
        registry: The normalized registry.

    Returns:
        The counts, keyed by :data:`COUNT_KEYS`.
    """
    return {
        "items": len(registry.items),
        "recipes": len(registry.recipes),
        "buildings": len(registry.buildings),
        "warnings": len(registry.warnings),
        "unknown_groups": len(registry.unknown_groups),
    }


def _body(registry: Registry) -> dict[str, object]:
    """Build the success body by naming every field it carries.

    Args:
        registry: The normalized registry.

    Returns:
        The body, keyed by :data:`DATA_KEYS`. Each collection is served in the
        registry's own order - see the module docstring on why it is not sorted.
    """
    return {
        "items": [_item(item) for item in registry.items.values()],
        "recipes": [_recipe(recipe) for recipe in registry.recipes.values()],
        "buildings": [_building(building) for building in registry.buildings.values()],
        "counts": _counts(registry),
        "warnings": [_warning(warning) for warning in registry.warnings],
        "unknown_groups": list(registry.unknown_groups),
    }


def make_handler(registries: contract.RegistryProvider[Registry]) -> contract.Handler:
    """Bind a registry provider and return the handler that answers this route.

    THE PROVIDER IS BOUND BY CLOSURE RATHER THAN PASSED PER REQUEST, which is the
    shape ``contract.Handler`` publishes: the server binds what an endpoint needs
    before registering it, so this module never imports the server and never
    learns how a registry was obtained.

    Args:
        registries: Whatever hands over the registry, or says there is not one.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request.

        Args:
            query: The parsed query parameters. This endpoint accepts none.

        Returns:
            200 with the registry, 503 when this machine has no game install, or
            400 when the request named a parameter. The 400 reflects NOTHING of
            what it refused - on this machine a query value can be a save path or
            an account directory.
        """
        if query:
            return contract.bad_request(ENDPOINT, contract.REASON_UNKNOWN_PARAMETER)
        registry = registries.registry()
        if registry is None:
            return contract.unavailable(ENDPOINT, contract.REASON_NO_GAME_INSTALL)
        return contract.ok(ENDPOINT, _body(registry))

    return handle


def routes(registries: contract.RegistryProvider[Registry]) -> tuple[contract.Route, ...]:
    """Every route this module publishes, with the provider already bound.

    Args:
        registries: Whatever hands this endpoint the registry.

    Returns:
        The one GET route.
    """
    return (contract.Route(method=METHOD_GET, template=ENDPOINT, handler=make_handler(registries)),)
