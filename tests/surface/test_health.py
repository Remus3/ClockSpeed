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

Every anti-leak arm asserts absence through ``reflected_in``, which decodes the
body, joins and folds every string in it, and hunts the planted path's personal
tokens rather than raw bytes the encoder cannot produce; each arm first plants a
reflecting body that the oracle must find, and ``LEAK_SHAPES`` grades the oracle
against every spelling of an echo an adversary measured slipping past (CS-1034).
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import urllib.parse
from typing import TYPE_CHECKING, Final

import pytest

import clockspeed
from clockspeed.data import version
from clockspeed.surface.api import contract
from clockspeed.surface.api import health as endpoint

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
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

#: The personal segments of the planted path - the account directory and the
#: leaf beneath it, which on a real machine are the Windows account name and a
#: world name. Each is a token no clean body can carry by accident, which is
#: what lets ``reflected_in`` hunt them loosely without over-matching: a common
#: word such as ``someone`` or ``world`` would trip on legitimate prose.
PLANTED_ACCOUNT: Final = "CsPlantAcctQz7"
PLANTED_LEAF: Final = "CsPlantLeafQz7"

#: A home-path-shaped string ASSEMBLED FROM FRAGMENTS. A tracked file may not
#: carry an absolute path under a user home directory (non-negotiable 3), and
#: ``tests/test_scaffold.py`` asserts that across the tree. The world and
#: registry refusal arms import it rather than spelling a second one.
HOME_SHAPED: Final = "C:" + chr(92) + "Users" + chr(92) + PLANTED_ACCOUNT + chr(92) + PLANTED_LEAF

#: The chunk width the split shape cuts the path at. Every token the oracle
#: hunts is longer than one chunk, so NO single string of that shape carries a
#: whole token - only the joined haystack does.
_LEAK_CHUNK: Final = 5

#: The home prefix, once backslashes are forward slashes and case is folded:
#: a drive letter, the home segment, then what lies beneath it.
HOME_PREFIX: Final = re.compile(r"([a-z]:)/+(users|home)/+(.+)")

#: How many rounds of percent-decoding the fold applies before it stops.
PERCENT_DECODE_ROUNDS: Final = 4

#: Every way a handler that echoed the planted path could spell it, each one a
#: value the adversary measured slipping past an exact-string hunt (CS-1034).
#: The keys name the shape; each value turns the path into what would go out.
LEAK_SHAPES: Final[dict[str, Callable[[str], object]]] = {
    "verbatim": lambda path: path,
    "python_repr": lambda path: "unknown parameters " + repr({"path": path}),
    "forward_slash": lambda path: path.replace(chr(92), "/"),
    "lower_case": lambda path: path.lower(),
    "prefix_only": lambda path: path.rsplit(chr(92), 1)[0],
    "split_on_separator": lambda path: path.split(chr(92)),
    "percent_encoded": urllib.parse.quote,
    "percent_encoded_home_prefix": lambda path: urllib.parse.quote(path.split(PLANTED_ACCOUNT)[0]),
    "home_prefix_alone": lambda path: path.split(PLANTED_ACCOUNT)[0],
    "chunked_across_strings": lambda path: [
        path[at : at + _LEAK_CHUNK] for at in range(0, len(path), _LEAK_CHUNK)
    ],
}

#: How many shapes the sweep grades, asserted before it iterates.
EXPECTED_LEAK_SHAPES: Final = 10


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


def personal_tokens(needle: str) -> tuple[str, ...]:
    """The folded tokens of a home-shaped path that would identify this machine.

    The home-prefix shape - the drive and the home segment, separators removed -
    plus every segment beneath it, which on a real machine are the account name
    and whatever the account keeps. A leak that drops the leaf, drops the
    account, changes case or turns the slashes round still carries at least one
    of these.

    Args:
        needle: A home-shaped path, possibly inside a longer string.

    Returns:
        The tokens, each folded by :func:`fold_for_leaks`.

    Raises:
        ValueError: When the needle holds no home-shaped path, so the oracle is
            never asked to grade a needle it has no tokens for.
    """
    shape = HOME_PREFIX.search(needle.lower().replace(chr(92), "/"))
    if shape is None:
        raise ValueError("the needle is not a home-shaped path")
    below = tuple(segment for segment in shape.group(3).split("/") if segment)
    return (fold_for_leaks(shape.group(1) + shape.group(2)), *below)


def fold_for_leaks(text: str) -> str:
    """Lower-case, percent-decode and strip every separator.

    Percent-decoding repeats until the text stops changing, so a value quoted
    twice unfolds too; the bound keeps a hostile string from spinning it.

    Args:
        text: Any string a body carried.

    Returns:
        The folded text.
    """
    for _ in range(PERCENT_DECODE_ROUNDS):
        decoded = urllib.parse.unquote(text)
        if decoded == text:
            break
        text = decoded
    return text.lower().replace(chr(92), "").replace("/", "")


def body_strings(node: object) -> list[str]:
    """Every string in a decoded body, keys included, in document order.

    Args:
        node: A value ``json.loads`` produced.

    Returns:
        The strings, each key immediately before its value's strings.
    """
    if isinstance(node, str):
        return [node]
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            found.append(key)
            found.extend(body_strings(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(body_strings(item))
    return found


def reflected_in(blob: bytes, needle: str) -> bool:
    """Whether an encoded body carries any personal token of ``needle``.

    THE EXACT-STRING HUNT IS BLIND (CS-1034). ``contract.encode`` is
    ``json.dumps``, which writes every backslash as two, so the raw bytes of a
    Windows path never occur in a body that reflects it; and an adversary then
    measured an exact decoded-string hunt missing a ``repr`` echo, a
    forward-slash, lower-case, prefix-only, split or percent-encoded one. So
    the body is decoded, every string in it - keys included - is joined in
    document order into ONE haystack (a path split across strings rejoins
    there), the haystack is folded by :func:`fold_for_leaks`, and the tokens
    :func:`personal_tokens` derives are hunted in it. The planted tokens are
    ones no clean body carries, and
    ``test_the_reflection_oracle_stays_quiet_on_a_clean_body`` holds that floor.

    Args:
        blob: Bytes ``contract.encode`` produced.
        needle: The home-shaped value a leaking body would carry.

    Returns:
        True when the folded body contains any personal token of the needle.
    """
    haystack = fold_for_leaks("".join(body_strings(json.loads(blob.decode("ascii")))))
    return any(token in haystack for token in personal_tokens(needle))


def planted_reflection(payload: Mapping[str, object], needle: str) -> bytes:
    """The body a LEAKING handler would send, built through the real encoder.

    It is the handler's own payload plus the refused value under one more key,
    encoded by ``contract.encode`` so the backslash doubling is the real one -
    a planted positive written by hand could spell the path the way no body
    ever does, and prove the oracle potent against a body that cannot exist.

    Args:
        payload: The payload the handler really built.
        needle: The value a leaking handler would echo.

    Returns:
        The encoded bytes of the reflecting body.
    """
    return contract.encode({**payload, "reflected": needle})


# ---------------------------------------------------------------------------
# 0 - the reflection oracle every anti-leak arm here asserts through
# ---------------------------------------------------------------------------


def test_the_reflection_oracle_finds_a_path_the_encoder_doubled() -> None:
    """The needle as a value, as a key and inside a list is found; its absence is not.

    The first assertion is the reason the oracle exists: the encoded body
    carries the path, and its raw ASCII bytes are nowhere in it.
    """
    as_value = contract.encode({"echo": HOME_SHAPED})
    doubled = HOME_SHAPED.encode("ascii") in as_value
    assert doubled is False, "the encoder no longer doubles a backslash"
    found = (
        reflected_in(as_value, HOME_SHAPED),
        reflected_in(contract.encode({"map": {HOME_SHAPED: 1}}), HOME_SHAPED),
        reflected_in(contract.encode({"rows": [{"at": "at-" + HOME_SHAPED}]}), HOME_SHAPED),
    )
    assert found == (True, True, True), found
    absent = reflected_in(contract.encode({"echo": "elsewhere"}), HOME_SHAPED)
    assert absent is False


def test_the_personal_tokens_are_the_home_prefix_and_each_planted_segment() -> None:
    """The tokens the oracle hunts, and the refusal to grade a needle with none."""
    tokens = personal_tokens("live-at-" + HOME_SHAPED)
    expected = ("c:users", PLANTED_ACCOUNT.lower(), PLANTED_LEAF.lower())
    assert tokens == expected, tokens
    with pytest.raises(ValueError, match="not a home-shaped path"):
        personal_tokens("not a path at all")


def test_the_leak_shape_population_is_the_one_graded() -> None:
    """The count control. A shape dropped from the table is a shape nobody grades."""
    assert len(LEAK_SHAPES) == EXPECTED_LEAK_SHAPES


@pytest.mark.parametrize("shape", sorted(LEAK_SHAPES))
def test_the_reflection_oracle_finds_every_leak_shape(shape: str) -> None:
    """A handler that echoed the path in any of these spellings is caught.

    Each planted body goes through the real ``contract.encode`` under a
    ``detail`` key, the field a leaking refusal would most plausibly add.
    """
    leaked = LEAK_SHAPES[shape](HOME_SHAPED)
    body = contract.encode({"status": "error", "detail": leaked})
    found = reflected_in(body, HOME_SHAPED)
    assert found is True, f"the oracle misses the {shape} shape"


def test_the_reflection_oracle_stays_quiet_on_a_clean_body() -> None:
    """The over-matching floor: common words and path fragments, apart, are clean.

    Every word here is one a legitimate body can carry - including the drive
    letter, the home segment and the word the planted path once used for its
    account - so a hunt loose enough to find the split and folded shapes above
    must still not trip on them.
    """
    clean = {
        "note": "someone asked which users can see this world",
        "drive": "C",
        "route": "/api/world",
        "rows": ["home", "Users", "save", "someone"],
        "status": "error",
    }
    found = reflected_in(contract.encode(clean), HOME_SHAPED)
    assert found is False


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
    reflected = reflected_in(blob, HOME_SHAPED)
    planted = reflected_in(planted_reflection(response.payload, HOME_SHAPED), HOME_SHAPED)
    assert planted is True, "the oracle cannot find the path in a body that reflects it"
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
    reflected = reflected_in(blob, HOME_SHAPED)
    assert isinstance(data, dict)
    leaking = contract.encode({**response.payload, "data": {**data, "world": HOME_SHAPED}})
    planted = reflected_in(leaking, HOME_SHAPED)
    assert planted is True, "the oracle cannot find the path in a body that reflects it"
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
    reflected = reflected_in(blob, HOME_SHAPED)
    assert isinstance(data, dict)
    # The leak this arm guards is a path as a KEY, so the plant is one.
    keyed = {**data, "endpoints": {HOME_SHAPED: endpoint.LIVE}}
    planted = reflected_in(contract.encode({**response.payload, "data": keyed}), HOME_SHAPED)
    assert planted is True, "the oracle cannot find the path in a body that reflects it"
    assert sorted(data["endpoints"]) == sorted(endpoint.ENDPOINT_TEMPLATES)
    assert reflected is False


def test_a_liveness_value_outside_the_vocabulary_is_not_published() -> None:
    """Anything that is not the live word renders as the not-live word."""
    smuggled = "live-at-" + HOME_SHAPED
    response = answer(endpoint_status={"/api/health": smuggled})
    data = response.payload["data"]
    blob = contract.encode(response.payload)
    reflected = reflected_in(blob, smuggled)
    planted = reflected_in(planted_reflection(response.payload, smuggled), smuggled)
    assert planted is True, "the oracle cannot find the value in a body that reflects it"
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
