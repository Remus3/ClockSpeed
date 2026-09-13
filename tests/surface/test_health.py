"""CS-601 slice S3 - ``/api/health``, the one endpoint that must never fail.

What is covered, and the authority for each arm:

a. HEALTH IS 200 AND NOTHING ELSE, EVER. It is the probe the companion window
   and the operator both reach for when something is wrong, so an endpoint that
   can answer 503 has made "is the server up" unanswerable exactly when it
   matters. Absence is reported INSIDE a 200 body as a two-value enum.
b. HEALTH NAMES NO PATH. Presence is ``present``/``absent`` and ``loaded``/
   ``absent`` - never a save path, never an install directory, never an account
   directory (non-negotiable 3, and ``clockspeed/surface/api/__init__.py``).
   The arm plants a home-path-shaped provider and asserts the wire is unchanged.
c. THE ENDPOINT SET IS THE ONE BOOTSTRAP.md SECTION 7.1 PUBLISHES, and a
   durability arm reads that file rather than trusting a list written here.
   This mirrors ``tests/surface/test_contract.py``, which pins
   ``OPEN_BLOCKERS`` to the OPEN item lines of ``ROADMAP.md`` for the same
   reason: the package opens no file, so the anti-drift arm lives in the tests.
d. NOTHING THE CALLER HANDS THE HANDLER REACHES THE WIRE. The route templates
   are literals in the shipped module and the liveness value is a closed
   two-word vocabulary, so a server that bound a map keyed by raw request paths
   could not publish one. That is asserted by planting exactly such a map.
e. THE LIVENESS MAP IS TOTAL. A template the server never registered reads as
   ``not_implemented`` rather than vanishing from the body, so a client always
   sees one key per published template and never has to tell absent from
   unknown.

Test-quality discipline (CONVENTIONS.md section 7.2, and this package's own
``__init__``): every sweep binds a scalar and asserts an expected count before
it iterates, and no assertion renders a provider's contents.
"""

from __future__ import annotations

import ast
import inspect
import re
from typing import TYPE_CHECKING, Final

import clockspeed
from clockspeed.data import version
from clockspeed.surface.api import contract
from clockspeed.surface.api import health as endpoint

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: How many endpoints BOOTSTRAP.md section 7.1 lists. The count is asserted so a
#: scanner that silently matches nothing cannot pass the arm that consumes it.
#: MOVED FROM 9 TO 10 BY CS-912, which added ``/api/registry`` - the vocabulary
#: route ``/api/solve`` and ``/api/optimize`` were unreachable without - and FROM
#: 10 TO 11 BY CS-977, which added ``/api/map``: ``/api/world`` counts nodes and
#: never lists them, so nothing published a coordinate and no surface could draw
#: the world.
EXPECTED_ENDPOINTS: Final = 12

#: The backticked route in the section 7.1 sentence. ``/api/plan?target=...``
#: carries a query string, which ``contract.ENDPOINT_PATTERN`` refuses outright,
#: so the scanner takes the path half - the template is the route, never the
#: question the caller asks of it.
BOOTSTRAP_ROUTE: Final = re.compile(r"`(/api/[^`?]*)[^`]*`")

#: The sentence the scanner reads, so a match elsewhere in the file cannot
#: silently widen the population.
BOOTSTRAP_ENDPOINT_HEADING: Final = "Endpoints, minimum:"

#: Presence is a two-value enum. Anything else is a location.
EXPECTED_PRESENCE_WORDS: Final = 2
EXPECTED_LIVENESS_WORDS: Final = 2

#: The top-level keys a health body carries.
EXPECTED_DATA_KEYS: Final = 5

#: A home-path-shaped string ASSEMBLED FROM FRAGMENTS. A tracked file may not
#: carry an absolute path under a user home directory (non-negotiable 3), and
#: ``tests/test_scaffold.py`` asserts that across the tree.
HOME_SHAPED: Final = "C:" + chr(92) + "Users" + chr(92) + "someone" + chr(92) + "world"


# ---------------------------------------------------------------------------
# Stand-ins. Neither holds anything real; both satisfy the published protocol.
# ---------------------------------------------------------------------------


class _Worlds:
    """A world provider whose answer is whatever it was built with."""

    def __init__(self, value: object) -> None:
        """Hold the answer.

        Args:
            value: What ``world()`` returns. None is the no-save case.
        """
        self._value = value

    def world(self) -> object:
        """Answer with the held value.

        Returns:
            The held value.
        """
        return self._value


class _Registries:
    """A registry provider whose answer is whatever it was built with."""

    def __init__(self, value: object) -> None:
        """Hold the answer.

        Args:
            value: What ``registry()`` returns. None is the no-install case.
        """
        self._value = value

    def registry(self) -> object:
        """Answer with the held value.

        Returns:
            The held value.
        """
        return self._value


def answer(
    world_value: object = None,
    registry_value: object = None,
    endpoint_status: dict[str, str] | None = None,
) -> contract.Response:
    """Build a handler and ask it one question.

    Args:
        world_value: What the world provider answers with.
        registry_value: What the registry provider answers with.
        endpoint_status: The liveness map the server would bind.

    Returns:
        The response.
    """
    handler = endpoint.make_handler(
        _Worlds(world_value),
        _Registries(registry_value),
        {} if endpoint_status is None else endpoint_status,
    )
    return handler({})


def bootstrap_endpoints(text: str) -> tuple[str, ...]:
    """Read the route templates out of BOOTSTRAP.md section 7.1.

    Args:
        text: The whole file.

    Returns:
        The templates, in file order, with any query string dropped.
    """
    lines = text.splitlines()
    opened = [index for index, line in enumerate(lines) if BOOTSTRAP_ENDPOINT_HEADING in line]
    if not opened:
        return ()
    start = opened[0]
    sentence: list[str] = []
    for line in lines[start:]:
        sentence.append(line)
        if line.rstrip().endswith("."):
            break
    return tuple(BOOTSTRAP_ROUTE.findall(" ".join(sentence)))


def call_names(tree: ast.AST) -> frozenset[str]:
    """Every simple name called in a tree, plus every called attribute name.

    Args:
        tree: A parsed module.

    Returns:
        The callee names.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            found.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            found.add(node.func.attr)
    return frozenset(found)


# ---------------------------------------------------------------------------
# 1 - health is 200 and nothing else (arm a)
# ---------------------------------------------------------------------------


def test_health_answers_200_with_no_world_and_no_registry() -> None:
    """The state a fresh machine with no game and no save is in."""
    response = answer()
    assert response.http_status == contract.HTTP_OK
    assert contract.contract_problems(response) == ()


def test_health_answers_200_with_both_present() -> None:
    """The state the operator's own machine is in."""
    response = answer(world_value=object(), registry_value=object())
    assert response.http_status == contract.HTTP_OK
    assert contract.contract_problems(response) == ()


def test_health_answers_200_even_when_a_parameter_it_does_not_accept_arrives() -> None:
    """A probe that 400s on a stray query is a probe that cannot be relied on."""
    handler = endpoint.make_handler(_Worlds(None), _Registries(None), {})
    response = handler({"target": "anything", "path": HOME_SHAPED})
    blob = contract.encode(response.payload)
    reflected = HOME_SHAPED.encode("ascii") in blob
    assert response.http_status == contract.HTTP_OK
    assert reflected is False


# ---------------------------------------------------------------------------
# 2 - presence is an enum, never a location (arm b)
# ---------------------------------------------------------------------------


def test_presence_and_liveness_are_closed_two_word_vocabularies() -> None:
    """Two values each. A third would be somewhere for a location to hide."""
    assert len(endpoint.PRESENCE_WORDS) == EXPECTED_PRESENCE_WORDS
    assert len(endpoint.LIVENESS_WORDS) == EXPECTED_LIVENESS_WORDS
    assert set(endpoint.PRESENCE_WORDS) == {endpoint.PRESENT, endpoint.ABSENT}
    assert set(endpoint.LIVENESS_WORDS) == {endpoint.LIVE, endpoint.NOT_LIVE}


def test_a_present_registry_and_world_render_as_words_not_as_what_they_are() -> None:
    """The provider hands over a path-shaped object and a word goes out."""
    response = answer(world_value=HOME_SHAPED, registry_value=HOME_SHAPED)
    data = response.payload["data"]
    blob = contract.encode(response.payload)
    reflected = HOME_SHAPED.encode("ascii") in blob
    assert isinstance(data, dict)
    assert data["world"] == endpoint.LOADED
    assert data["registry"] == endpoint.PRESENT
    assert reflected is False


def test_an_absent_registry_and_world_render_as_absent() -> None:
    """The negative half. Without it the arm above is satisfied by a constant."""
    data = answer().payload["data"]
    assert isinstance(data, dict)
    assert data["world"] == endpoint.ABSENT
    assert data["registry"] == endpoint.ABSENT


# ---------------------------------------------------------------------------
# 3 - the endpoint set is BOOTSTRAP.md's (arm c)
# ---------------------------------------------------------------------------


def test_the_published_templates_are_the_ones_bootstrap_lists(repo_root: Path) -> None:
    """The anti-drift arm. When section 7.1 grows a route, this goes red.

    It did, for CS-912's tenth. The count above was moved BY HAND afterwards,
    which is the whole point of the arm: a route cannot join the specification
    and the liveness body without somebody noticing in between.
    """
    listed = bootstrap_endpoints((repo_root / "BOOTSTRAP.md").read_text(encoding="ascii"))
    assert len(listed) == EXPECTED_ENDPOINTS
    assert sorted(listed) == sorted(endpoint.ENDPOINT_TEMPLATES)


def test_the_bootstrap_scanner_discriminates() -> None:
    """The negative control. A scanner matching nothing passes the arm above."""
    found = bootstrap_endpoints("Nothing here names a route at all.\n")
    assert found == ()


def test_every_published_template_is_a_template_the_contract_can_spell() -> None:
    """A query string, an uppercase segment or a drive letter is refused there."""
    templates = endpoint.ENDPOINT_TEMPLATES
    assert len(templates) == EXPECTED_ENDPOINTS
    unspellable = sorted(
        template for template in templates if contract.ENDPOINT_PATTERN.fullmatch(template) is None
    )
    assert unspellable == []


# ---------------------------------------------------------------------------
# 4 - nothing the caller hands over reaches the wire (arm d)
# ---------------------------------------------------------------------------


def test_a_liveness_map_keyed_by_a_raw_path_publishes_none_of_it() -> None:
    """The keys on the wire are literals in the shipped module, not the map's.

    A server that bound a map keyed by request paths - which on this machine can
    be a save path or an account directory - must not be able to publish one
    through this endpoint.
    """
    response = answer(endpoint_status={HOME_SHAPED: endpoint.LIVE, "/api/health": endpoint.LIVE})
    data = response.payload["data"]
    blob = contract.encode(response.payload)
    reflected = HOME_SHAPED.encode("ascii") in blob
    assert isinstance(data, dict)
    assert sorted(data["endpoints"]) == sorted(endpoint.ENDPOINT_TEMPLATES)
    assert reflected is False


def test_a_liveness_value_outside_the_vocabulary_is_not_published() -> None:
    """Anything that is not the live word renders as the not-live word."""
    smuggled = "live-at-" + HOME_SHAPED
    response = answer(endpoint_status={"/api/health": smuggled})
    data = response.payload["data"]
    blob = contract.encode(response.payload)
    reflected = smuggled.encode("ascii") in blob
    assert isinstance(data, dict)
    endpoints = data["endpoints"]
    assert isinstance(endpoints, dict)
    assert endpoints["/api/health"] == endpoint.NOT_LIVE
    assert reflected is False


# ---------------------------------------------------------------------------
# 5 - the liveness map is total (arm e)
# ---------------------------------------------------------------------------


def test_an_unregistered_template_reads_as_not_implemented_rather_than_vanishing() -> None:
    """One key per published template, so absent is never confused with unknown."""
    data = answer(endpoint_status={"/api/health": endpoint.LIVE}).payload["data"]
    assert isinstance(data, dict)
    endpoints = data["endpoints"]
    assert isinstance(endpoints, dict)
    assert len(endpoints) == EXPECTED_ENDPOINTS
    assert endpoints["/api/health"] == endpoint.LIVE
    assert endpoints["/api/plan"] == endpoint.NOT_LIVE


# ---------------------------------------------------------------------------
# 6 - the body's own shape and its two pinned facts
# ---------------------------------------------------------------------------


def test_the_body_carries_exactly_the_published_keys() -> None:
    """Five: the app version, the game build pin, the two presences, the routes."""
    data = answer().payload["data"]
    assert isinstance(data, dict)
    assert len(endpoint.DATA_KEYS) == EXPECTED_DATA_KEYS
    assert sorted(data) == sorted(endpoint.DATA_KEYS)


def test_the_versions_are_read_from_their_owners_and_not_restated() -> None:
    """``clockspeed.__version__`` and ``clockspeed.data.version.GAME_BUILD``.

    A version restated in a second place is a fact that will drift (CLAUDE.md
    section 4), so this arm reads both owners and compares.
    """
    data = answer().payload["data"]
    assert isinstance(data, dict)
    assert data["app_version"] == clockspeed.__version__
    assert data["game_build_pin"] == version.GAME_BUILD


def test_the_endpoint_holds_no_formatting_site_and_no_raise() -> None:
    """No f-string, no ``.format``, no ``raise``, no logger and no printer.

    Health is the endpoint an operator hits when something is already wrong, so
    it is the one that must not answer with a message built from content.
    """
    tree = ast.parse(inspect.getsource(endpoint))
    formatted = sum(
        1 for node in ast.walk(tree) if isinstance(node, ast.JoinedStr | ast.FormattedValue)
    )
    raised = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Raise))
    source = inspect.getsource(endpoint)
    assert formatted == 0
    assert raised == 0
    assert "format" not in call_names(tree)
    assert "logging" not in source
    assert "print(" not in source


def test_the_endpoint_opens_no_file() -> None:
    """The package docstring forbids it outright, so the module names no opener."""
    openers = sorted(
        call_names(ast.parse(inspect.getsource(endpoint)))
        & {"open", "read_text", "read_bytes", "locate", "load_world"}
    )
    assert openers == []


def test_both_providers_satisfy_the_protocols_the_contract_publishes() -> None:
    """The stand-ins are the seam the server will bind across, not a shape here."""
    assert isinstance(_Worlds(None), contract.WorldProvider)
    assert isinstance(_Registries(None), contract.RegistryProvider)
