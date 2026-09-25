"""CS-912 - ``/api/registry``, the route that makes ``/api/solve`` reachable.

THE GAP THIS CLOSES, MEASURED RATHER THAN ARGUED. ``/api/solve`` and
``/api/optimize`` both require ``targets``, ``recipes`` and ``raw_items``, and
every one of those is a registry ClassName. Before this route existed nothing
the surface served named a single item or recipe, so a caller could not build a
valid request without INVENTING an identifier - and an invented identifier is
refused by the solve layer as a caller shape bug. The two endpoints were live
and unreachable at the same time.

What is covered, and the authority for each arm:

a. THE END-TO-END ARM AND ITS PAIRED CONTROL ARE ONE UNIT.
   :func:`test_a_solve_request_built_only_from_the_registry_body_answers_a_plan`
   derives a whole solve request by walking the registry BODY - not the registry
   object, not the fixture, the encoded response - and drives ``/api/solve`` with
   it. On its own that arm proves nothing: a request built from the fixture
   directly would pass it identically. The control,
   :func:`test_the_foreign_identifier_detector_fires_on_an_added_key`, ADDS one
   identifier the body never published, leaving every real one in place, and
   asserts both that the detector sees it and that the solve refuses with
   ``invalid_parameter`` specifically. An arm with no control is a claim about
   its own author's care - and a control that cannot say WHY the refusal came
   is barely more than one, which is what the first version of it was.
b. THE BODY IS BUILT BY NAMING EVERY FIELD. No ``asdict``, no ``astuple``, no
   ``vars()``, no ``dataclasses.fields`` walk and no ``__dict__`` read anywhere in
   the shipped module, asserted on its AST and proved able to fire against five
   planted walkers. ``clockspeed/surface/api/world.py`` states the rule and the
   reason: a generic walker ships whatever field somebody adds upstream, and
   adding a field then becomes a decision nobody makes.
c. EVERY RATE LEAVES AS ``{"num": n, "den": d}``. ``Recipe.duration``,
   ``RecipeIO.amount`` and ``Item.energy_value`` are all ``Fraction``, and
   ``contract.encode`` refuses a float outright - but a serializer that called
   ``float()`` on the way out would satisfy the type checker and lose the value.
   The arm reads the RAW ENCODED BYTES, because the object graph is not what a
   browser parses.
d. NO INSTALL, NO SAVE, NO SOCKET. Every arm here runs against
   ``tests/solve/synthetic.py``'s hand-authored corpus through a stub provider,
   which is what ``tests/surface/__init__.py`` requires of this whole directory
   and what BOOTSTRAP.md section 8.1 requires of the rule suite.
e. THE TENTH ROUTE IS A BIJECTION MEMBER, NOT AN EXTRA.
   ``clockspeed/surface/api/routes.py`` refuses a surplus route AT IMPORT, so a
   route table that carried this endpoint without ``health.ENDPOINT_TEMPLATES``
   naming it would not import at all.

Test-quality discipline (CONVENTIONS.md section 7.2, and this package's own
``__init__``): every sweep binds a scalar before it is asserted, and every
detector used to prove an absence is also run against a planted positive.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import re
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.data import registry as data_registry
from clockspeed.data.registry import build_registry
from clockspeed.solve import ratio
from clockspeed.surface.api import contract, health
from clockspeed.surface.api import registry as endpoint
from clockspeed.surface.api import solve as solve_endpoint
from clockspeed.surface.api.routes import ENDPOINT_STATUS, ROUTES
from tests.data import synthetic as rich
from tests.solve import synthetic
from tests.surface.test_health import planted_reflection, reflected_in

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from clockspeed.data.registry import Registry

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: What the hand-authored corpus holds. Asserted before anything iterates it, so
#: a fixture that silently emptied could not make a sweep pass vacuously.
CORPUS_ITEMS: Final = 12
CORPUS_RECIPES: Final = 11
CORPUS_BUILDINGS: Final = 3

#: The generic walkers, any one of which would ship a field nobody chose to
#: publish. Spelled exactly as ``tests/surface/test_world.py`` spells them,
#: because the rule is that module's and this one inherits it rather than
#: inventing a second version of it.
GENERIC_WALKERS: Final = ("asdict", "astuple", "vars", "fields", "__dict__", "__dataclass_fields__")

#: The keys ``contract.rational`` spells an exact ratio with.
RATIONAL_KEYS: Final = frozenset({"num", "den"})

#: A JSON string literal, so the number scanner can blank strings out before it
#: looks for a bare number. Without this the scanner reports every digit inside a
#: ClassName, and a scanner that cannot be trusted is one whose silence means
#: nothing.
JSON_STRING: Final = re.compile(rb'"(?:[^"\\]|\\.)*"')

#: A JSON number token, matched only outside strings.
JSON_NUMBER: Final = re.compile(rb"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

#: An identifier this corpus does not contain, in any position. Shaped like a
#: registry ClassName on purpose - the control has to be refused for being
#: ABSENT rather than for being malformed, and ``solve.KEY_PATTERN`` would refuse
#: a malformed one before the registry was ever consulted.
FOREIGN_KEY: Final = "Desc_NotInTheRegistry_C"

#: Exactly one identifier is substituted in the control, so the count the
#: detector reports is a value this module can assert rather than a range.
ONE_FOREIGN_KEY: Final = 1

#: What the target rate is set to. Any exact rate does; this one is spelled as a
#: plain integer so the request text carries no shape the grammar could refuse
#: for a reason unrelated to the identifiers being graded.
TARGET_RATE: Final = "1"


# ---------------------------------------------------------------------------
# Stubs. Neither holds anything real; both satisfy the published protocol.
# ---------------------------------------------------------------------------


class _StubRegistryProvider:
    """Hands back one registry, or None to stand for a machine with no install.

    A hand-written stub rather than a mock: the protocol has one method, and a
    mock would agree with whatever this module asserted about it.
    """

    def __init__(self, value: Registry | None) -> None:
        """Record what this provider will hand back.

        Args:
            value: The registry, or None for the no-install case.
        """
        self._value = value

    def registry(self) -> Registry | None:
        """The registry this stub was built with.

        Returns:
            The registry, or None.
        """
        return self._value


@pytest.fixture(scope="module")
def corpus() -> Registry:
    """The hand-authored solve corpus, built through the real seam.

    Returns:
        The registry every arm in this module serves.
    """
    return synthetic.solve_registry()


@pytest.fixture(scope="module")
def flawed() -> Registry:
    """A second corpus that deliberately does NOT build cleanly.

    ``tests/solve/synthetic.py``'s corpus carries no warning at all, by design -
    it is the one every phase 3 arm solves against. That makes it the wrong
    fixture for non-negotiable 7, because a body that silently dropped every
    flagged thing would look identical over it. ``tests/data/synthetic.py``'s
    corpus is the opposite: it declares a duplicate class name, an empty display
    name, a missing duration, an unresolvable producer, an unknown group and a
    recipe side naming an item it holds no descriptor for. Both are hand-authored
    in this repository, which is the settled fixture rule.

    Returns:
        The registry built from that corpus.
    """
    return build_registry(rich.synthetic_document())


@pytest.fixture(scope="module")
def body(corpus: Registry) -> Mapping[str, object]:
    """One 200 body from the shipped handler, as the ``data`` object.

    Args:
        corpus: The registry to serve.

    Returns:
        The ``data`` object of a successful response.
    """
    response = endpoint.make_handler(_StubRegistryProvider(corpus))({})
    assert response.http_status == contract.HTTP_OK, response.http_status
    data = response.payload["data"]
    assert isinstance(data, dict), type(data).__name__
    return data


# ---------------------------------------------------------------------------
# Reading the body. Every helper below reads the RESPONSE and never the fixture.
# ---------------------------------------------------------------------------


def body_of(response: contract.Response) -> Mapping[str, object]:
    """The ``data`` object of a 200, narrowed and asserted successful.

    Args:
        response: A response this endpoint built.

    Returns:
        The ``data`` object.
    """
    assert response.http_status == contract.HTTP_OK, response.http_status
    data = response.payload["data"]
    assert isinstance(data, dict), type(data).__name__
    return data


def producers_of(entry: Mapping[str, object]) -> tuple[str, ...]:
    """One recipe entry's ``produced_in`` list, narrowed.

    Args:
        entry: A served recipe.

    Returns:
        The building keys, in the order served.
    """
    found = entry["produced_in"]
    assert isinstance(found, list), type(found).__name__
    return tuple(str(token) for token in found)


def entries(data: Mapping[str, object], section: str) -> list[dict[str, object]]:
    """One section of the body, narrowed from ``object`` to the list it is.

    THE NARROWING IS AN ASSERTION RATHER THAN A CAST. ``contract.ok`` publishes a
    ``Mapping[str, object]``, which is the honest static type of a JSON body, so
    every read of it has to prove its own shape. Doing that in one place means
    each arm below reads a list of mappings instead of restating the same three
    isinstance checks, and it means a section that stopped being a list fails
    HERE with the section named rather than as an opaque ``TypeError`` inside a
    comprehension.

    Args:
        data: The ``data`` object.
        section: The key to read.

    Returns:
        The entries.
    """
    found = data[section]
    assert isinstance(found, list), f"{section} is not a list: {type(found).__name__}"
    return found


def by_key(data: Mapping[str, object], section: str) -> dict[str, dict[str, object]]:
    """One section of the body, indexed by the identifier each entry publishes.

    Args:
        data: The ``data`` object.
        section: The key to read.

    Returns:
        Identifier to entry.
    """
    return {str(entry["key"]): entry for entry in entries(data, section)}


def sides(entry: Mapping[str, object], name: str) -> list[dict[str, object]]:
    """One recipe entry's input or output list, narrowed.

    Args:
        entry: A served recipe.
        name: ``inputs`` or ``outputs``.

    Returns:
        The sides.
    """
    found = entry[name]
    assert isinstance(found, list), f"{name} is not a list: {type(found).__name__}"
    return found


def published_keys(data: Mapping[str, object], section: str) -> tuple[str, ...]:
    """Every identifier one section of the body published, in body order.

    Args:
        data: The ``data`` object.
        section: ``items``, ``recipes`` or ``buildings``.

    Returns:
        The ``key`` of each entry, in the order the body listed them.
    """
    return tuple(str(entry["key"]) for entry in entries(data, section))


def first_producers(data: Mapping[str, object]) -> dict[str, str]:
    """The first recipe the body lists as producing each item.

    FIRST RATHER THAN CHEAPEST, AND THAT IS DELIBERATE. Choosing between two
    recipes that make one item is pillar 2's job and needs an objective; this
    module is proving the identifiers are usable, not that they are optimal. The
    corpus deliberately holds competing pairs - two trinket recipes and two twin
    recipes - so a walk that took every producer would hand the solver an
    underdetermined system and the arm would fail for a reason that has nothing
    to do with the route under test.

    Args:
        data: The ``data`` object.

    Returns:
        Item key to the recipe key that makes it.
    """
    found: dict[str, str] = {}
    for entry in entries(data, "recipes"):
        for side in sides(entry, "outputs"):
            found.setdefault(str(side["item_key"]), str(entry["key"]))
    return found


def solve_request_from(data: Mapping[str, object], target: str) -> dict[str, str]:
    """Build a whole ``/api/solve`` request by walking the body alone.

    THE POINT OF THE WHOLE MODULE IS IN THIS FUNCTION'S ARGUMENTS. It takes the
    response ``data`` and a target key that came out of it, and it reads nothing
    else - no registry object, no fixture, no literal ClassName. Whatever it
    produces is therefore buildable by any client holding only what the route
    returned, which is exactly what CS-912's acceptance clause asks to be shown.

    Args:
        data: The ``data`` object.
        target: The item to solve for. Must be one the body published.

    Returns:
        The request parameters, spelled in ``clockspeed/surface/api/solve.py``'s
        grammar. Items reached by the walk that nothing in the body produces
        become the raw set, which is the honest reading of a chain leaf.
    """
    producers = first_producers(data)
    recipes = by_key(data, "recipes")

    chosen: list[str] = []
    raw: list[str] = []
    pending = [target]
    seen: set[str] = set()
    while pending:
        item = pending.pop()
        if item in seen:
            continue
        seen.add(item)
        recipe_key = producers.get(item)
        if recipe_key is None:
            if item != target:
                raw.append(item)
            continue
        if recipe_key not in chosen:
            chosen.append(recipe_key)
        pending.extend(str(side["item_key"]) for side in sides(recipes[recipe_key], "inputs"))

    return {
        solve_endpoint.PARAM_TARGETS: f"{target}{solve_endpoint.ASSIGNMENT}{TARGET_RATE}",
        solve_endpoint.PARAM_RECIPES: solve_endpoint.SEPARATOR.join(chosen),
        solve_endpoint.PARAM_RAW_ITEMS: solve_endpoint.SEPARATOR.join(raw),
        solve_endpoint.PARAM_BYPRODUCT_POLICY: ratio.BYPRODUCT_BALANCED,
    }


def foreign_identifiers(
    parameters: Mapping[str, str], published: frozenset[str]
) -> tuple[str, ...]:
    """Every identifier in a solve request the registry body did not publish.

    THE POLICY WORD IS NOT AN IDENTIFIER AND IS NOT GRADED HERE.
    ``byproduct_policy`` is solve-grammar vocabulary owned by
    ``clockspeed/solve/ratio.py``, not registry content, so a route that
    published it would be publishing the wrong layer's fact.

    Args:
        parameters: A ``/api/solve`` request.
        published: Every identifier the registry body carried.

    Returns:
        The offending identifiers, sorted. Empty when the request is buildable
        from the body alone.
    """
    named: set[str] = set()
    for member in parameters[solve_endpoint.PARAM_TARGETS].split(solve_endpoint.SEPARATOR):
        named.add(member.partition(solve_endpoint.ASSIGNMENT)[0])
    for name in (solve_endpoint.PARAM_RECIPES, solve_endpoint.PARAM_RAW_ITEMS):
        members = parameters[name].split(solve_endpoint.SEPARATOR)
        named.update(member for member in members if member)
    return tuple(sorted(named - published))


def bare_numbers(raw: bytes) -> tuple[bytes, ...]:
    """Every JSON number token outside a string literal, with strings blanked.

    Args:
        raw: The encoded body.

    Returns:
        The number tokens found.
    """
    outside = JSON_STRING.sub(b'""', raw)
    return tuple(JSON_NUMBER.findall(outside))


# ---------------------------------------------------------------------------
# AST detectors, each proved able to fire before it is trusted
# ---------------------------------------------------------------------------


def docstring_ids(tree: ast.AST) -> frozenset[int]:
    """The identity of every docstring node in a tree.

    Needed because a substring sweep over the source grades the PROSE: the
    shipped module's docstring names the generic walkers in order to say it holds
    none of them.

    Args:
        tree: A parsed module.

    Returns:
        The ``id()`` of each docstring constant node.
    """
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, holders) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            found.add(id(first.value))
    return frozenset(found)


def code_tokens(tree: ast.AST) -> frozenset[str]:
    """Every identifier and non-docstring string literal a tree actually uses.

    A string literal counts because ``getattr(model, "__dict__")`` is a generic
    walk spelled without ever naming the attribute as an attribute.

    Args:
        tree: A parsed module.

    Returns:
        The tokens.
    """
    skip = docstring_ids(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif (
            isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip
        ):
            found.add(node.value)
    return frozenset(found)


@pytest.fixture(scope="module")
def endpoint_tree() -> ast.Module:
    """The shipped endpoint module, parsed.

    Returns:
        The parse tree.
    """
    return ast.parse(inspect.getsource(endpoint))


# ---------------------------------------------------------------------------
# a. The route exists at all, and is one of the published set
# ---------------------------------------------------------------------------


def test_the_endpoint_is_a_template_the_specification_set_publishes() -> None:
    assert endpoint.ENDPOINT in health.ENDPOINT_TEMPLATES, endpoint.ENDPOINT


def test_the_endpoint_is_spellable_as_a_route_template() -> None:
    assert contract.ENDPOINT_PATTERN.fullmatch(endpoint.ENDPOINT) is not None, endpoint.ENDPOINT


def test_the_module_publishes_one_get_route_for_its_own_template() -> None:
    published = endpoint.routes(_StubRegistryProvider(None))
    count = len(published)
    expected = 1
    assert count == expected, f"expected {expected} route, found {count}"
    assert published[0].template == endpoint.ENDPOINT, published[0].template
    assert published[0].method == endpoint.METHOD_GET, published[0].method


# ---------------------------------------------------------------------------
# b. The corpus, asserted before any sweep reads it
# ---------------------------------------------------------------------------


def test_the_corpus_holds_the_population_every_sweep_below_assumes(corpus: Registry) -> None:
    items = len(corpus.items)
    recipes = len(corpus.recipes)
    buildings = len(corpus.buildings)
    assert items == CORPUS_ITEMS, items
    assert recipes == CORPUS_RECIPES, recipes
    assert buildings == CORPUS_BUILDINGS, buildings


def test_the_body_publishes_every_member_of_the_registry_it_was_given(
    body: Mapping[str, object], corpus: Registry
) -> None:
    for section, held in (
        ("items", corpus.items),
        ("recipes", corpus.recipes),
        ("buildings", corpus.buildings),
    ):
        served = published_keys(body, section)
        assert len(served) == len(held), f"{section}: served {len(served)}, held {len(held)}"
        assert frozenset(served) == frozenset(held), section


def test_the_body_invents_no_identifier_the_registry_does_not_hold(
    body: Mapping[str, object], corpus: Registry
) -> None:
    known = frozenset(corpus.items) | frozenset(corpus.recipes) | frozenset(corpus.buildings)
    served: set[str] = set()
    for section in ("items", "recipes", "buildings"):
        served.update(published_keys(body, section))
    invented = tuple(sorted(served - known))
    count = len(invented)
    assert count == 0, f"{count} identifier(s) the registry does not hold: {invented}"


def test_the_body_carries_exactly_the_keys_the_module_publishes(
    body: Mapping[str, object],
) -> None:
    assert frozenset(body) == frozenset(endpoint.DATA_KEYS), sorted(body)


def test_every_entry_carries_exactly_the_keys_its_own_shape_publishes(
    body: Mapping[str, object],
) -> None:
    shapes = (
        ("items", endpoint.ITEM_KEYS),
        ("recipes", endpoint.RECIPE_KEYS),
        ("buildings", endpoint.BUILDING_KEYS),
    )
    wrong: list[str] = []
    for section, keys in shapes:
        served = entries(body, section)
        assert served, f"{section} is empty; the sweep below would grade nothing"
        wrong.extend(
            f"{section}[{index}]"
            for index, entry in enumerate(served)
            if frozenset(entry) != frozenset(keys)
        )
    count = len(wrong)
    assert count == 0, f"{count} entry/entries carry the wrong keys: {wrong}"


def test_every_recipe_side_carries_exactly_the_two_keys_a_side_publishes(
    body: Mapping[str, object],
) -> None:
    every = [
        side
        for entry in entries(body, "recipes")
        for name in ("inputs", "outputs")
        for side in sides(entry, name)
    ]
    seen = len(every)
    assert seen > 0, "no recipe side was read; the sweep would grade nothing"
    wrong = tuple(
        index
        for index, side in enumerate(every)
        if frozenset(side) != frozenset(endpoint.RECIPE_IO_KEYS)
    )
    count = len(wrong)
    assert count == 0, f"{count} of {seen} recipe sides carry the wrong keys"


# ---------------------------------------------------------------------------
# c. THE ACCEPTANCE ARM AND ITS PAIRED CONTROL
# ---------------------------------------------------------------------------


def test_a_solve_request_built_only_from_the_registry_body_answers_a_plan(
    body: Mapping[str, object], corpus: Registry
) -> None:
    published = frozenset(published_keys(body, "items")) | frozenset(
        published_keys(body, "recipes")
    )
    target = _solvable_target(body)
    request = solve_request_from(body, target)

    foreign = foreign_identifiers(request, published)
    stray = len(foreign)
    assert stray == 0, f"{stray} identifier(s) in the request were never published: {foreign}"

    response = solve_endpoint.solve_handler(_StubRegistryProvider(corpus))(request)
    assert response.http_status == contract.HTTP_OK, response.payload.get("reason")
    data = response.payload["data"]
    assert isinstance(data, dict), type(data).__name__
    steps = data["steps"]
    assert isinstance(steps, list), type(steps).__name__
    planned = len(steps)
    assert planned > 0, "the solve answered 200 with no production steps in it"


def test_the_foreign_identifier_detector_fires_on_an_added_key(
    body: Mapping[str, object], corpus: Registry
) -> None:
    published = frozenset(published_keys(body, "items")) | frozenset(
        published_keys(body, "recipes")
    )
    target = _solvable_target(body)
    request = dict(solve_request_from(body, target))

    # THIS ADDS RATHER THAN SUBSTITUTES, AND THE DIFFERENCE IS THE WHOLE ARM.
    # The derived request names exactly ONE recipe - the producer of the target -
    # so replacing the first element dropped that producer as collateral. The
    # refusal that followed was then fully explained by the missing producer:
    # MEASURED, removing that recipe and adding NO foreign key at all also
    # refuses, with reason `chain_unsolvable`. A bare `not 200` cannot tell the
    # two apart, so the control was green against a solve layer that ignores
    # unpublished identifiers entirely - demonstrated with a live mutant that
    # turned `tests/solve` red and left this module at 41 passed.
    original = request[solve_endpoint.PARAM_RECIPES].split(solve_endpoint.SEPARATOR)
    assert original, "the derived request names no recipe, so nothing can be added to it"
    request[solve_endpoint.PARAM_RECIPES] = solve_endpoint.SEPARATOR.join([*original, FOREIGN_KEY])

    foreign = foreign_identifiers(request, published)
    stray = len(foreign)
    assert stray == ONE_FOREIGN_KEY, f"the detector reported {stray} foreign identifiers"
    assert foreign == (FOREIGN_KEY,), foreign

    response = solve_endpoint.solve_handler(_StubRegistryProvider(corpus))(request)
    answered = response.http_status
    assert answered != contract.HTTP_OK, (
        "a request naming an identifier the registry never published still answered a plan"
    )
    # THE REASON IS ASSERTED, NOT ONLY THE REFUSAL. `chain_unsolvable` and
    # `invalid_parameter` are both non-200, and only the second one is a
    # statement about the identifier this arm planted.
    reason = response.payload.get("reason")
    assert reason == contract.REASON_INVALID_PARAMETER, (
        f"the solve refused, but for {reason!r} rather than for the foreign identifier"
    )


def test_the_end_to_end_derivation_cannot_pass_over_a_registry_with_no_recipes() -> None:
    """The vacuity control for the acceptance arm, and the one it needed most.

    THE PAIRED CONTROL ABOVE GRADES THE DETECTOR; THIS ONE GRADES THE ARM. A
    foreign-identifier check is satisfied trivially by a request that names no
    identifiers at all, so an ``/api/registry`` that published an empty catalogue
    would sail through :func:`foreign_identifiers` with nothing to report - and
    the acceptance arm would be green over a route that published nothing. Here
    the same body is built from a corpus with every recipe removed, and the
    derivation is asserted to REFUSE rather than to produce a request. That is
    what makes the acceptance arm a claim about the route's CONTENT rather than
    about its shape.
    """
    empty = synthetic.registry_with(drop=frozenset(synthetic.solve_registry().recipes))
    served = len(empty.recipes)
    assert served == 0, f"the variant still holds {served} recipe(s)"

    data = body_of(endpoint.make_handler(_StubRegistryProvider(empty))({}))
    assert entries(data, "items"), "the variant published no item either; this grades nothing"
    assert not entries(data, "recipes"), "the variant published a recipe"

    with pytest.raises(AssertionError, match="no producible item"):
        _solvable_target(data)


def _solvable_target(data: Mapping[str, object]) -> str:
    """The first published item some recipe makes, read out of the body.

    Args:
        data: The ``data`` object.

    Returns:
        The target key. Chosen from the body rather than written down, so this
        module names no ClassName of its own anywhere in the acceptance path.

    Raises:
        AssertionError: The body published no item any recipe produces, which
            makes every arm below unbuildable rather than merely failing.
    """
    producers = first_producers(data)
    for key in published_keys(data, "items"):
        if key in producers:
            return key
    raise AssertionError("the body published no producible item")


# ---------------------------------------------------------------------------
# d. Exactness survives to the wire
# ---------------------------------------------------------------------------


def test_every_rate_in_the_body_is_an_exact_ratio_and_never_a_bare_number(
    body: Mapping[str, object],
) -> None:
    durations = [entry["duration"] for entry in entries(body, "recipes")]
    seen = len(durations)
    assert seen == CORPUS_RECIPES, seen
    wrong = tuple(
        index
        for index, value in enumerate(durations)
        if not isinstance(value, dict) or frozenset(value) != RATIONAL_KEYS
    )
    count = len(wrong)
    assert count == 0, f"{count} of {seen} durations are not exact ratios"


def test_the_encoded_bytes_carry_no_bare_number_outside_a_rational(
    body: Mapping[str, object],
) -> None:
    response = contract.ok(endpoint.ENDPOINT, body)
    raw = contract.encode(response.payload)
    decimals = tuple(token for token in bare_numbers(raw) if b"." in token or b"e" in token.lower())
    count = len(decimals)
    assert count == 0, f"{count} decimal number token(s) reached the wire"


def test_the_bare_number_scanner_sees_a_planted_decimal() -> None:
    planted = b'{"a":"Desc_1.5_C","b":1.5}'
    found = tuple(token for token in bare_numbers(planted) if b"." in token)
    assert found == (b"1.5",), found


def test_the_encoder_refuses_a_body_whose_rate_became_a_float(corpus: Registry) -> None:
    data = body_of(endpoint.make_handler(_StubRegistryProvider(corpus))({}))
    recipes = entries(data, "recipes")
    planted = dict(data)
    planted["recipes"] = [{**recipes[0], "duration": 1.5}, *recipes[1:]]
    with pytest.raises(ValueError, match=re.escape(contract.FLOAT_ON_THE_WIRE)):
        contract.encode(contract.ok(endpoint.ENDPOINT, planted).payload)


def test_a_fractional_amount_in_the_corpus_reaches_the_wire_exactly(
    body: Mapping[str, object], corpus: Registry
) -> None:
    fractional = tuple(
        (key, side.amount)
        for key, recipe in corpus.recipes.items()
        for side in recipe.inputs + recipe.outputs
        if side.amount.denominator != 1
    )
    found = len(fractional)
    assert found > 0, "the corpus holds no fractional amount, so this arm grades nothing"

    recipes = by_key(body, "recipes")
    mismatched = tuple(
        key
        for key, amount in fractional
        if not any(
            side["amount"] == {"num": amount.numerator, "den": amount.denominator}
            for name in ("inputs", "outputs")
            for side in sides(recipes[key], name)
        )
    )
    count = len(mismatched)
    assert count == 0, f"{count} fractional amount(s) did not survive: {mismatched}"


# ---------------------------------------------------------------------------
# e. The body is built by naming every field
# ---------------------------------------------------------------------------


def test_the_shipped_module_holds_no_generic_walker(endpoint_tree: ast.Module) -> None:
    used = code_tokens(endpoint_tree) & frozenset(GENERIC_WALKERS)
    count = len(used)
    assert count == 0, f"{count} generic walker(s) in the shipped module: {sorted(used)}"


def test_the_generic_walker_detector_fires_on_every_planted_shape() -> None:
    plants = (
        "import dataclasses\nd = dataclasses.asdict(model)\n",
        "import dataclasses\nd = dataclasses.astuple(model)\n",
        "d = vars(model)\n",
        "import dataclasses\nd = dataclasses.fields(model)\n",
        "d = getattr(model, '__dict__')\n",
    )
    expected = len(plants)
    walkers = frozenset(GENERIC_WALKERS)
    caught = sum(1 for plant in plants if walkers & code_tokens(ast.parse(plant)))
    assert caught == expected, f"the detector saw {caught} of {expected} planted walkers"


def test_the_shipped_module_opens_no_file_and_names_no_layer_below_its_neighbour(
    endpoint_tree: ast.Module,
) -> None:
    imported: set[str] = set()
    for node in ast.walk(endpoint_tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = tuple(
        sorted(
            name
            for name in imported
            if name.startswith(("clockspeed.save", "clockspeed.advisor", "pathlib"))
            or name == "clockspeed.data.docs_extract"
        )
    )
    count = len(forbidden)
    assert count == 0, f"{count} forbidden import(s): {forbidden}"

    opens = tuple(
        node.func.id
        for node in ast.walk(endpoint_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"
    )
    opened = len(opens)
    assert opened == 0, "the endpoint module opens a file"


# ---------------------------------------------------------------------------
# e2. Every upstream field is a DECISION - published, or withheld on the record
# ---------------------------------------------------------------------------

#: Every field of every registry type this endpoint serves, split into the ones
#: it publishes and the ones it deliberately does not. THE SPLIT IS DECLARED
#: RATHER THAN DERIVED, which is the whole point: a field added to any of these
#: dataclasses upstream lands in neither half and turns
#: :func:`test_every_upstream_field_is_either_published_or_withheld_on_the_record`
#: red, so somebody has to decide about it. The shipped module names its fields
#: one at a time precisely so a new one CANNOT reach the wire by itself - that is
#: the safe direction, and this arm is what stops it also being the silent one.
WITHHELD_FIELDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "Item": (),
        "RecipeIO": (),
        "Recipe": (
            "variable_power_constant",
            "variable_power_factor",
            "unresolved_produced_in",
        ),
        "Building": (
            "power_consumption",
            "power_exponent",
            "estimated_min_power",
            "estimated_max_power",
            "is_variable_power",
            "unsharded_clock_base",
        ),
        "RegistryWarning": (),
    }
)

#: Which published key tuple describes each type.
PUBLISHED_FIELDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "Item": endpoint.ITEM_KEYS,
        "RecipeIO": endpoint.RECIPE_IO_KEYS,
        "Recipe": endpoint.RECIPE_KEYS,
        "Building": endpoint.BUILDING_KEYS,
        "RegistryWarning": endpoint.WARNING_KEYS,
    }
)

#: How many of the withheld fields carry an exact ``Fraction``: five on
#: ``Building`` - the declared draw, the exponent, both estimated bounds and the
#: unsharded clock base - and two more on ``Recipe``. Every one is a value
#: ``json.dumps`` cannot serialize at all, which is why a generic walker in the
#: shipped module would not merely over-share; it would crash the encoder on the
#: first building it reached. MEASURED, and it caught a hand count of 6 that was
#: wrong the first time this constant was written.
FRACTION_BEARING_WITHHELD: Final = 7


def test_every_upstream_field_is_either_published_or_withheld_on_the_record() -> None:
    types = {
        "Item": data_registry.Item,
        "RecipeIO": data_registry.RecipeIO,
        "Recipe": data_registry.Recipe,
        "Building": data_registry.Building,
        "RegistryWarning": data_registry.RegistryWarning,
    }
    graded = len(types)
    assert graded == len(PUBLISHED_FIELDS) == len(WITHHELD_FIELDS), graded

    undecided: list[str] = []
    for name, klass in types.items():
        held = frozenset(field.name for field in dataclasses.fields(klass))
        decided = frozenset(PUBLISHED_FIELDS[name]) | frozenset(WITHHELD_FIELDS[name])
        undecided.extend(f"{name}.{field}" for field in sorted(held - decided))
        stale = frozenset(WITHHELD_FIELDS[name]) - held
        assert not stale, f"{name} withholds a field it no longer has: {sorted(stale)}"
    count = len(undecided)
    assert count == 0, f"{count} upstream field(s) nobody decided about: {undecided}"


def test_no_withheld_field_is_read_anywhere_in_the_shipped_module(
    endpoint_tree: ast.Module,
) -> None:
    withheld = frozenset(field for fields in WITHHELD_FIELDS.values() for field in fields)
    assert withheld, "nothing is declared withheld; this arm grades nothing"
    read = frozenset(
        node.attr for node in ast.walk(endpoint_tree) if isinstance(node, ast.Attribute)
    )
    leaked = tuple(sorted(withheld & read))
    count = len(leaked)
    assert count == 0, f"{count} withheld field(s) are read in the shipped module: {leaked}"


def test_the_withheld_power_fields_are_the_ones_that_would_break_the_encoder() -> None:
    """The reason the withholding matters, measured rather than asserted in prose.

    Every withheld ``Building`` field and both withheld ``Recipe`` power terms are
    ``Fraction | None``. ``json.dumps`` cannot serialize a ``Fraction`` at all, so
    a generic walker would not quietly over-share these - it would raise on the
    first entry. That is worth pinning, because it is the reason the field-naming
    rule is a correctness requirement here and not only a privacy one.
    """
    fraction_bearing = 0
    for klass in (data_registry.Building, data_registry.Recipe):
        withheld = frozenset(WITHHELD_FIELDS[klass.__name__])
        for field in dataclasses.fields(klass):
            if field.name in withheld and "Fraction" in str(field.type):
                fraction_bearing += 1
    assert fraction_bearing == FRACTION_BEARING_WITHHELD, fraction_bearing

    with pytest.raises(TypeError):
        json.dumps({"duration": Fraction(5, 2)})


# ---------------------------------------------------------------------------
# f. Refusals
# ---------------------------------------------------------------------------


def test_a_machine_with_no_install_is_unavailable_and_never_unimplemented() -> None:
    response = endpoint.make_handler(_StubRegistryProvider(None))({})
    assert response.http_status == contract.HTTP_UNAVAILABLE, response.http_status
    assert response.payload["reason"] == contract.REASON_NO_GAME_INSTALL, response.payload["reason"]


def test_a_request_naming_a_parameter_is_refused_and_reflects_nothing(corpus: Registry) -> None:
    handler = endpoint.make_handler(_StubRegistryProvider(corpus))
    supplied = "C:" + chr(92) + "Users" + chr(92) + "someone"
    response = handler({"path": supplied})
    assert response.http_status == contract.HTTP_BAD_REQUEST, response.http_status
    assert response.payload["reason"] == contract.REASON_UNKNOWN_PARAMETER, response.payload
    raw = contract.encode(response.payload)
    planted = reflected_in(planted_reflection(response.payload, supplied), supplied)
    assert planted is True, "the oracle cannot find the path in a body that reflects it"
    reflected = reflected_in(raw, supplied)
    assert reflected is False, "the refusal reflected what it refused"


def test_every_response_this_endpoint_can_build_conforms_to_the_contract(
    corpus: Registry,
) -> None:
    responses = (
        endpoint.make_handler(_StubRegistryProvider(corpus))({}),
        endpoint.make_handler(_StubRegistryProvider(None))({}),
        endpoint.make_handler(_StubRegistryProvider(corpus))({"anything": "1"}),
    )
    graded = len(responses)
    expected = 3
    assert graded == expected, graded
    faults = tuple(
        f"{response.http_status}: {problem}"
        for response in responses
        for problem in contract.contract_problems(response)
    )
    count = len(faults)
    assert count == 0, f"{count} contract fault(s): {faults}"


# ---------------------------------------------------------------------------
# g. Nothing about this machine reaches the body
# ---------------------------------------------------------------------------


def test_the_body_carries_no_path_shaped_value(body: Mapping[str, object]) -> None:
    raw = contract.encode(contract.ok(endpoint.ENDPOINT, body).payload)
    text = raw.decode("ascii")
    shapes = (chr(92), "://", "C:", "/Users/", "/home/")
    found = tuple(shape for shape in shapes if shape in text)
    count = len(found)
    assert count == 0, f"{count} path-shaped substring(s) in the body"


def test_the_encoded_body_is_seven_bit_and_deterministic(body: Mapping[str, object]) -> None:
    payload = contract.ok(endpoint.ENDPOINT, body).payload
    first = contract.encode(payload)
    second = contract.encode(payload)
    assert first == second, "two encodes of one payload disagreed"
    high = tuple(byte for byte in first if byte > contract.MAX_ASCII_BYTE)
    count = len(high)
    assert count == 0, f"{count} byte(s) above 0x7E reached the wire"


def test_the_counts_agree_with_the_lists_the_same_body_carries(
    body: Mapping[str, object],
) -> None:
    counts = body["counts"]
    assert isinstance(counts, dict), type(counts).__name__
    assert frozenset(counts) == frozenset(endpoint.COUNT_KEYS), sorted(counts)
    disagreeing = tuple(
        section
        for section in ("items", "recipes", "buildings")
        if counts[section] != len(published_keys(body, section))
    )
    count = len(disagreeing)
    assert count == 0, f"{count} count(s) disagree with the list beside them: {disagreeing}"


def test_unmodelled_content_is_flagged_rather_than_dropped(
    body: Mapping[str, object], corpus: Registry
) -> None:
    warnings = body["warnings"]
    groups = body["unknown_groups"]
    assert isinstance(warnings, list), type(warnings).__name__
    assert isinstance(groups, list), type(groups).__name__
    assert len(warnings) == len(corpus.warnings), len(warnings)
    assert tuple(groups) == tuple(corpus.unknown_groups), groups
    wrong = tuple(
        index
        for index, entry in enumerate(warnings)
        if frozenset(entry) != frozenset(endpoint.WARNING_KEYS)
    )
    count = len(wrong)
    assert count == 0, f"{count} warning(s) carry the wrong keys"


def test_the_warning_shape_is_graded_against_a_registry_that_actually_warns(
    flawed: Registry,
) -> None:
    raised = len(flawed.warnings)
    groups = len(flawed.unknown_groups)
    assert raised > 0, "the flawed corpus raised no warning, so the shape arm grades nothing"
    assert groups > 0, "the flawed corpus reported no unknown group"

    data = body_of(endpoint.make_handler(_StubRegistryProvider(flawed))({}))
    served = entries(data, "warnings")
    assert len(served) == raised, f"served {len(served)} of {raised} warnings"
    served_groups = data["unknown_groups"]
    assert isinstance(served_groups, list), type(served_groups).__name__
    assert tuple(served_groups) == flawed.unknown_groups, len(served_groups)
    wrong = tuple(
        index
        for index, entry in enumerate(served)
        if frozenset(entry) != frozenset(endpoint.WARNING_KEYS)
    )
    count = len(wrong)
    assert count == 0, f"{count} warning(s) carry the wrong keys"


def test_a_recipe_side_naming_an_unmodelled_item_is_kept_rather_than_dropped(
    flawed: Registry,
) -> None:
    """Non-negotiable 7: unknown content is FLAGGED and skipped, never erased.

    The flawed corpus holds a recipe side referencing an item it has no
    descriptor for. ``clockspeed/data/registry.py`` keeps that side and flags it,
    and a serializer that quietly dropped it would turn a flagged gap into a
    silently wrong recipe - which is the exact failure the non-negotiable names.
    """
    dangling = tuple(
        (key, side.item_key)
        for key, recipe in flawed.recipes.items()
        for side in recipe.inputs + recipe.outputs
        if side.item_key not in flawed.items
    )
    found = len(dangling)
    assert found > 0, "the flawed corpus holds no dangling item reference; this arm grades nothing"

    data = body_of(endpoint.make_handler(_StubRegistryProvider(flawed))({}))
    served = by_key(data, "recipes")
    lost = tuple(
        f"{key}:{item_key}"
        for key, item_key in dangling
        if not any(
            side["item_key"] == item_key
            for name in ("inputs", "outputs")
            for side in sides(served[key], name)
        )
    )
    count = len(lost)
    assert count == 0, f"{count} flagged recipe side(s) were dropped on the way out: {lost}"


def test_the_body_order_is_the_registry_order_and_not_a_sort(
    body: Mapping[str, object], corpus: Registry
) -> None:
    for section, held in (
        ("items", corpus.items),
        ("recipes", corpus.recipes),
        ("buildings", corpus.buildings),
    ):
        served = published_keys(body, section)
        assert served == tuple(held), f"{section} was reordered on the way out"


def test_an_optional_measurement_absent_from_the_registry_stays_absent(
    body: Mapping[str, object], corpus: Registry
) -> None:
    absent = tuple(key for key, item in corpus.items.items() if item.energy_value is None)
    found = len(absent)
    assert found > 0, "every corpus item declares an energy value; this arm grades nothing"
    items = by_key(body, "items")
    defaulted = tuple(key for key in absent if items[key]["energy_value"] is not None)
    count = len(defaulted)
    assert count == 0, f"{count} absent energy value(s) were defaulted on the way out"


def test_an_exact_energy_value_leaves_as_a_ratio_and_never_as_a_bare_number(
    flawed: Registry,
) -> None:
    held = {
        key: item.energy_value
        for key, item in flawed.items.items()
        if item.energy_value is not None
    }
    declared = tuple(held)
    fractional = tuple(key for key in declared if held[key].denominator != 1)
    assert declared, "the corpus declares no energy value; this arm grades nothing"
    assert fractional, "every declared energy value is a whole number; a float would survive"

    data = body_of(endpoint.make_handler(_StubRegistryProvider(flawed))({}))
    served = {key: entry["energy_value"] for key, entry in by_key(data, "items").items()}
    wrong = tuple(
        key
        for key in declared
        if served[key] != {"num": held[key].numerator, "den": held[key].denominator}
    )
    count = len(wrong)
    assert count == 0, f"{count} energy value(s) did not leave as an exact ratio: {wrong}"


def test_a_recipe_names_the_buildings_the_registry_resolved_for_it(
    body: Mapping[str, object], corpus: Registry
) -> None:
    served = by_key(body, "recipes")
    wrong = tuple(
        key
        for key, recipe in corpus.recipes.items()
        if tuple(producers_of(served[key])) != recipe.produced_in
    )
    count = len(wrong)
    assert count == 0, f"{count} recipe(s) name the wrong producers: {wrong}"


def test_every_produced_in_token_names_a_building_the_same_body_published(
    body: Mapping[str, object],
) -> None:
    buildings = frozenset(published_keys(body, "buildings"))
    dangling = tuple(
        sorted(
            {
                str(token)
                for entry in entries(body, "recipes")
                for token in producers_of(entry)
                if token not in buildings
            }
        )
    )
    count = len(dangling)
    assert count == 0, f"{count} produced_in token(s) name no published building: {dangling}"


def test_every_recipe_side_names_an_item_the_same_body_published(
    body: Mapping[str, object],
) -> None:
    items = frozenset(published_keys(body, "items"))
    dangling = tuple(
        sorted(
            {
                str(side["item_key"])
                for entry in entries(body, "recipes")
                for name in ("inputs", "outputs")
                for side in sides(entry, name)
                if side["item_key"] not in items
            }
        )
    )
    count = len(dangling)
    assert count == 0, f"{count} recipe side(s) name no published item: {dangling}"


# ---------------------------------------------------------------------------
# h. The route table and the liveness map
# ---------------------------------------------------------------------------


def test_the_health_body_reports_this_route_live() -> None:
    assert ENDPOINT_STATUS[endpoint.ENDPOINT] == health.LIVE, ENDPOINT_STATUS[endpoint.ENDPOINT]


def test_the_route_table_carries_this_template_exactly_once() -> None:
    claimed = tuple(route for route in ROUTES if route.template == endpoint.ENDPOINT)
    count = len(claimed)
    expected = 1
    assert count == expected, f"the template is claimed {count} time(s)"


def _amounts(served: Sequence[Mapping[str, object]]) -> tuple[Fraction, ...]:
    """Read a served recipe side back as exact ratios.

    Args:
        served: The served sides.

    Returns:
        One Fraction per side, rebuilt from the two published integers. Built
        with ``Fraction(num, den)`` rather than by dividing, so this reader is
        exact for the same reason the writer is.
    """
    rebuilt: list[Fraction] = []
    for side in served:
        amount = side["amount"]
        assert isinstance(amount, dict), type(amount).__name__
        rebuilt.append(Fraction(int(amount["num"]), int(amount["den"])))
    return tuple(rebuilt)


def test_a_served_amount_reads_back_as_the_fraction_the_registry_holds(
    body: Mapping[str, object], corpus: Registry
) -> None:
    served = by_key(body, "recipes")
    wrong = tuple(
        key
        for key, recipe in corpus.recipes.items()
        if _amounts(sides(served[key], "inputs")) != tuple(side.amount for side in recipe.inputs)
        or _amounts(sides(served[key], "outputs")) != tuple(side.amount for side in recipe.outputs)
    )
    count = len(wrong)
    assert count == 0, f"{count} recipe(s) did not read back exactly: {wrong}"
