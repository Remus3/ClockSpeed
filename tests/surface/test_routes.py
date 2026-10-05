"""CS-601 slice S6 - the wiring: the route table and the process entry point.

WHAT THIS GRADES. ``clockspeed/surface/api/routes.py`` is the only module that
knows every endpoint module at once, and ``clockspeed/surface/__main__.py`` is
the only one that knows the process. Neither computes anything, so what is
gradeable about them is COMPOSITION: that the table holds exactly the endpoint
set the specification names, that no two routes claim the same verb on the same
path, that the table is built once rather than per call, and that the entry
point starts and refuses in the ways a runbook can branch on.

THE ENDPOINT SET IS PARSED OUT OF ``BOOTSTRAP.md`` AND NEVER IMPORTED FROM THE
CODE. Importing the set from ``routes.ROUTES`` and then asserting ``ROUTES``
holds that many would be a tautology. The parse here anchors on the literal
"Endpoints, minimum:" sentence rather than on the section heading, which is a
DIFFERENT anchor from the one ``tests/surface/test_acceptance.py`` uses on the
same sentence - two parsers that fail on different document edits are worth more
than two copies of one parser.

EVERY COUNT IS BOUND TO A SCALAR BEFORE IT IS ASSERTED. ``pytest``'s assertion
rewriting renders the asserted EXPRESSION independently of the message, so
asserting on a comprehension over route objects would print the handlers - and a
handler's ``__repr__`` names a closure cell. Binding the count first means the
rendering is an integer.

WHAT IS DELIBERATELY NOT HERE. Nothing in this module stands up a listener to
grade a response body: ``tests/surface/test_acceptance.py`` drives the live
server over verified TLS and is written blind to this implementation, so
repeating it here would only produce a second opinion from the same author. The
two arms below that DO reach for the server ask one question apiece - whether
the table this slice assembles is one the server will accept, and whether a bind
refusal reaches the process exit code - because those are seam questions this
slice owns the answer to and no other module asks.
"""

from __future__ import annotations

import importlib
import json
import os
import socket
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pytest

from clockspeed.surface import __main__ as entry
from clockspeed.surface import server
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract, health, pending
from clockspeed.surface.api.routes import (
    ENDPOINT_STATUS,
    METHOD_BOUNDARY_ROUTES,
    ROUTES,
    SERVING_ROUTES,
    build_routes,
)
from tests.test_make_cert import cert_pair

# ---------------------------------------------------------------------------
# What BOOTSTRAP.md section 7.1 names, parsed rather than transcribed
# ---------------------------------------------------------------------------

#: How many endpoints the specification names. The parse is asserted against this
#: before anything iterates, so a parser that found nothing cannot let a sweep
#: pass vacuously.
#:
#: NOT NAMED FOR ITS VALUE, AND THAT IS THE LESSON CS-912 LEFT HERE. It was
#: spelled as the count itself until ``/api/registry`` made the specification
#: name ten, at which point a constant whose NAME was its value either had to be
#: renamed or had to start lying. A count changes; what it MEANS does not - and
#: CS-977's ``/api/map`` moved it again, which is exactly what the name allows.
PUBLISHED_ENDPOINTS: Final = 12

#: The sentence the endpoint set lives in. Anchoring on the sentence rather than
#: on the section heading means a section renumbering does not silently empty
#: this parse.
_SENTENCE: Final = "Endpoints, minimum:"

#: The paragraph ends at the first blank line after that sentence.
_PARAGRAPH_END: Final = "\n\n"


def bootstrap_templates(document: str) -> tuple[str, ...]:
    """The route templates BOOTSTRAP.md section 7.1 names, in document order.

    Args:
        document: The whole of ``BOOTSTRAP.md``.

    Returns:
        Each backticked span beginning ``/api`` in the "Endpoints, minimum:"
        paragraph, query string stripped, duplicates dropped, order preserved.

    Raises:
        ValueError: The sentence is absent. That means the document moved under
            this parser rather than that the route table is wrong, and the two
            must not be confused.
    """
    start = document.find(_SENTENCE)
    if start < 0:
        raise ValueError("BOOTSTRAP.md no longer carries the endpoint sentence")
    paragraph = document[start:]
    end = paragraph.find(_PARAGRAPH_END)
    if end >= 0:
        paragraph = paragraph[:end]

    found: list[str] = []
    for chunk in paragraph.split("`")[1::2]:
        if not chunk.startswith("/api"):
            continue
        template = chunk.split("?", 1)[0]
        if template not in found:
            found.append(template)
    return tuple(found)


@pytest.fixture(scope="module")
def specified_endpoints(repo_root: Path) -> tuple[str, ...]:
    """The endpoint set, parsed out of the specification once per module.

    Args:
        repo_root: Repository root.

    Returns:
        The templates, in document order.
    """
    parsed = bootstrap_templates((repo_root / "BOOTSTRAP.md").read_text(encoding="utf-8"))
    parsed_count = len(parsed)
    assert parsed_count == PUBLISHED_ENDPOINTS, (
        "BOOTSTRAP section 7.1 no longer names that many endpoints"
    )
    return parsed


# ---------------------------------------------------------------------------
# Providers that answer "there is nothing on this machine"
# ---------------------------------------------------------------------------


class _NoWorld:
    """A world provider on a machine with no save. Opens nothing."""

    def world(self) -> None:
        """The current world.

        Returns:
            None, always.
        """
        return


class _NoRegistry:
    """A registry provider on a machine with no game installed. Opens nothing."""

    def registry(self) -> None:
        """The normalized registry.

        Returns:
            None, always.
        """
        return


#: The transport codes a route may answer with when the machine has neither a
#: save nor an install. 200 is impossible for the two that need one, 400 is the
#: honest answer to a parameterless call on a route that requires parameters,
#: 501 is the unbuilt half and 503 is the missing-data half.
BARE_MACHINE_CODES: Final = frozenset(
    {
        contract.HTTP_OK,
        contract.HTTP_BAD_REQUEST,
        contract.HTTP_NOT_IMPLEMENTED,
        contract.HTTP_UNAVAILABLE,
    }
)

#: An environment that names a game directory, a save root and an account
#: directory that do not exist, plus a local-config path that does not exist.
#: Setting all four is what makes "no game installed and no save present" true on
#: a machine that has both, without touching either.
_ABSENT_MARKER: Final = "s6-no-such-directory"

#: The module the singleton arm re-imports to prove the table is not rebuilt.
_ROUTES_MODULE: Final = "clockspeed.surface.api.routes"


def _bare_machine_env(tmp_path: Path) -> dict[str, str]:
    """A copy of the environment with every game and save seam pointed at nothing.

    All four overrides are set together. Setting three would leave the fourth
    resolution pass free to find the operator's real install or real save, and
    the arms below would then be measuring this machine rather than a bare one.

    Args:
        tmp_path: A directory to hang the non-existent names off.

    Returns:
        The environment mapping, ready for ``subprocess``.
    """
    absent = tmp_path / _ABSENT_MARKER
    env = dict(os.environ)
    env["CLOCKSPEED_GAME_DIR"] = str(absent / "game")
    env["CLOCKSPEED_SAVE_ROOT"] = str(absent / "saves")
    env["CLOCKSPEED_ACCOUNT_DIR"] = str(absent / "account")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(absent / "local.json")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(_REPO_ROOT)
    return env


#: This repository's root, from this file's own location rather than from a
#: working directory - a subprocess started somewhere else must still import it.
_REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: A probe that runs INSIDE the bare-machine environment and reports what the
#: real providers found and what the real handlers answered. Written to a file
#: rather than passed with ``-c`` so no shell quoting stands between the source
#: here and the source that runs.
_BARE_MACHINE_PROBE: Final = """import json

from clockspeed.surface.api.routes import build_routes
from clockspeed.surface.providers import InstalledRegistryProvider, SaveWorldProvider

worlds = SaveWorldProvider()
registries = InstalledRegistryProvider()
found = {
    "world": worlds.world() is not None,
    "registry": registries.registry() is not None,
}
table = build_routes(worlds, registries)
codes = {route.template: route.handler({}).http_status for route in table}
print(json.dumps({"found": found, "codes": codes, "size": len(table)}))
"""


# ---------------------------------------------------------------------------
# The table: size first, so nothing below can sweep an empty sequence
# ---------------------------------------------------------------------------


def test_the_route_table_is_exactly_the_size_the_specification_names() -> None:
    table_size = len(ROUTES)
    assert table_size == PUBLISHED_ENDPOINTS, (
        "the route table is not the size BOOTSTRAP section 7.1 names"
    )


def test_the_route_templates_are_the_ones_the_specification_names(
    specified_endpoints: tuple[str, ...],
) -> None:
    published = tuple(route.template for route in ROUTES)
    published_count = len(published)
    assert published_count == PUBLISHED_ENDPOINTS, "the route table changed size under this arm"
    assert published == specified_endpoints, (
        "the route table is not the endpoint set BOOTSTRAP section 7.1 names, in its order"
    )


def test_no_two_routes_claim_the_same_method_on_the_same_template() -> None:
    pairs = [(route.method, route.template) for route in SERVING_ROUTES]
    pair_count = len(pairs)
    assert pair_count > 0, "the serving table is empty, so this arm proves nothing"
    seen = {pair: pairs.count(pair) for pair in pairs}
    duplicates = sorted(
        f"{method} {template}" for (method, template), count in seen.items() if count > 1
    )
    duplicate_count = len(duplicates)
    assert duplicate_count == 0, f"a method and template pair is registered twice: {duplicates}"


def test_every_route_method_is_one_the_server_admits() -> None:
    strays = sorted(
        {route.method for route in SERVING_ROUTES if route.method not in server.KNOWN_METHODS}
    )
    stray_count = len(strays)
    assert stray_count == 0, f"a route names a method the server does not admit: {strays}"


# ---------------------------------------------------------------------------
# The 405 boundary is published apart from the endpoint set
# ---------------------------------------------------------------------------


def test_the_method_boundary_route_is_not_one_of_the_published_set() -> None:
    boundary_count = len(METHOD_BOUNDARY_ROUTES)
    assert boundary_count > 0, "no method-boundary route was published at all"

    published_pairs = {(route.method, route.template) for route in ROUTES}
    folded = sorted(
        f"{route.method} {route.template}"
        for route in METHOD_BOUNDARY_ROUTES
        if (route.method, route.template) in published_pairs
    )
    folded_count = len(folded)
    assert folded_count == 0, f"a boundary route was folded into the set: {folded}"

    templates = {route.template for route in ROUTES}
    orphans = sorted(
        route.template for route in METHOD_BOUNDARY_ROUTES if route.template not in templates
    )
    orphan_count = len(orphans)
    assert orphan_count == 0, f"a boundary route names an unpublished template: {orphans}"


def test_the_serving_table_is_the_set_plus_the_boundary_and_nothing_else() -> None:
    serving_size = len(SERVING_ROUTES)
    assert serving_size == PUBLISHED_ENDPOINTS + len(METHOD_BOUNDARY_ROUTES), (
        "the serving table is not the endpoint set plus the boundary routes"
    )
    assert tuple(SERVING_ROUTES[:PUBLISHED_ENDPOINTS]) == tuple(ROUTES), (
        "the serving table does not open with the endpoint set, in its order"
    )


def test_the_advice_state_route_is_post_and_a_get_on_it_answers_405() -> None:
    state = [route for route in ROUTES if route.template == advice_endpoint.STATE_ENDPOINT]
    state_count = len(state)
    assert state_count == 1, "the advice-state template is not published exactly once"
    assert state[0].method == advice_endpoint.METHOD_POST, "the advice-state route is not a POST"

    boundary = [
        route
        for route in METHOD_BOUNDARY_ROUTES
        if route.template == advice_endpoint.STATE_ENDPOINT
        and route.method == advice_endpoint.METHOD_GET
    ]
    boundary_count = len(boundary)
    assert boundary_count == 1, "a GET on the advice-state template is not published as a boundary"

    response = boundary[0].handler({})
    assert response.http_status == contract.HTTP_METHOD_NOT_ALLOWED, (
        "a GET on the advice-state template did not answer 405"
    )


# ---------------------------------------------------------------------------
# Built once at import, not per call
# ---------------------------------------------------------------------------


def test_the_table_is_built_at_import_and_its_members_are_stable_singletons() -> None:
    first = importlib.import_module(_ROUTES_MODULE)
    second = importlib.import_module(_ROUTES_MODULE)

    assert isinstance(first.ROUTES, tuple), "the route table is not a built sequence"
    assert first.ROUTES is second.ROUTES, "the route table is not one object"
    identities = {id(route) for route in first.ROUTES} & {id(route) for route in ROUTES}
    shared = len(identities)
    assert shared == PUBLISHED_ENDPOINTS, (
        "the route table's members are not stable across two reads"
    )


def test_building_a_table_twice_yields_distinct_objects_from_the_module_constant() -> None:
    built = build_routes(_NoWorld(), _NoRegistry())
    built_count = len(built)
    assert built_count == PUBLISHED_ENDPOINTS, "build_routes did not produce the endpoint set"
    assert built is not ROUTES, "build_routes handed back the module constant instead of a table"


# ---------------------------------------------------------------------------
# The liveness map health publishes is total over the endpoint set
# ---------------------------------------------------------------------------


def test_the_liveness_map_names_every_template_and_no_other(
    specified_endpoints: tuple[str, ...],
) -> None:
    keys = frozenset(ENDPOINT_STATUS)
    key_count = len(keys)
    assert key_count == PUBLISHED_ENDPOINTS, "the liveness map is not the size of the endpoint set"
    assert keys == frozenset(specified_endpoints), (
        "the liveness map and the specified endpoint set are not the same set"
    )
    words = frozenset(ENDPOINT_STATUS.values())
    assert words <= frozenset(health.LIVENESS_WORDS), (
        "the liveness map carries a word outside the published vocabulary"
    )


def test_every_unbuilt_endpoint_reads_not_live_and_every_backed_one_reads_live() -> None:
    unbuilt = {template for _method, template in pending.UNBACKED}
    unbuilt_count = len(unbuilt)
    assert unbuilt_count > 0, "no unbuilt endpoint was published, so this arm proves nothing"

    lying = sorted(
        template for template in unbuilt if ENDPOINT_STATUS.get(template) != health.NOT_LIVE
    )
    lying_count = len(lying)
    assert lying_count == 0, f"an unbuilt endpoint is reported live: {lying}"

    backed = frozenset(ENDPOINT_STATUS) - unbuilt
    backed_count = len(backed)
    assert backed_count == PUBLISHED_ENDPOINTS - unbuilt_count, "the two halves do not add up"
    silent = sorted(template for template in backed if ENDPOINT_STATUS.get(template) != health.LIVE)
    silent_count = len(silent)
    assert silent_count == 0, f"a backed endpoint is reported not implemented: {silent}"


# ---------------------------------------------------------------------------
# Every handler answers on a machine with no game and no save
# ---------------------------------------------------------------------------


def test_every_handler_answers_without_a_game_or_a_save() -> None:
    table = build_routes(_NoWorld(), _NoRegistry())
    handled = len(table)
    assert handled == PUBLISHED_ENDPOINTS, "the table under test is not the endpoint set"

    faults: list[str] = []
    for route in table:
        response = route.handler({})
        if response.http_status not in BARE_MACHINE_CODES:
            faults.append(f"{route.template} answered {response.http_status}")
        faults.extend(
            f"{route.template} {problem}" for problem in contract.contract_problems(response)
        )
    fault_count = len(faults)
    assert fault_count == 0, "; ".join(faults)


def test_the_world_route_answers_503_rather_than_raising_when_nothing_is_detected() -> None:
    table = build_routes(_NoWorld(), _NoRegistry())
    world = [route for route in table if route.template == "/api/world"]
    world_count = len(world)
    assert world_count == 1, "the world template is not published exactly once"
    response = world[0].handler({})
    assert response.http_status == contract.HTTP_UNAVAILABLE, (
        "an undetectable world did not answer 503"
    )


def test_health_still_answers_200_on_a_machine_with_nothing_installed() -> None:
    table = build_routes(_NoWorld(), _NoRegistry())
    liveness = [route for route in table if route.template == health.ENDPOINT]
    liveness_count = len(liveness)
    assert liveness_count == 1, "the health template is not published exactly once"
    response = liveness[0].handler({})
    assert response.http_status == contract.HTTP_OK, "health did not answer 200"


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------


def test_the_bare_machine_environment_really_has_no_game_and_no_save(tmp_path: Path) -> None:
    """MEASURE the premise the two arms below assert against, rather than assume it.

    The operator plays on this machine, so a save and an install are both
    normally present. An arm that claimed "with no game installed" while the
    subprocess could still see both would be measuring the opposite of what it
    says. This runs the REAL providers inside the scrubbed environment and reads
    back what they found - if the scrub stops working, this goes red first and
    names the reason.
    """
    probe = tmp_path / "s6-bare-machine-probe.py"
    probe.write_text(_BARE_MACHINE_PROBE, encoding="ascii")
    completed = subprocess.run(
        [sys.executable, "-B", str(probe)],
        capture_output=True,
        env=_bare_machine_env(tmp_path),
        cwd=str(_REPO_ROOT),
        timeout=300,
        check=False,
    )
    exit_code = completed.returncode
    stderr = completed.stderr.decode("ascii", "replace")
    assert exit_code == 0, f"the probe exited {exit_code}: {stderr}"

    reported = json.loads(completed.stdout.decode("ascii", "replace"))
    assert reported["found"]["world"] is False, "the scrubbed environment still found a save"
    assert reported["found"]["registry"] is False, "the scrubbed environment still found an install"


def test_the_real_providers_degrade_to_503_rather_than_crashing_on_a_bare_machine(
    tmp_path: Path,
) -> None:
    """Auto-detection with nothing to detect is an answer, not a failure.

    Driven through the REAL ``SaveWorldProvider`` and ``InstalledRegistryProvider``
    in a subprocess rather than through stubs, because the thing being graded is
    what those two do when every path they resolve is absent - and a stub that
    returns None proves only that None is handled.
    """
    probe = tmp_path / "s6-bare-machine-probe.py"
    probe.write_text(_BARE_MACHINE_PROBE, encoding="ascii")
    completed = subprocess.run(
        [sys.executable, "-B", str(probe)],
        capture_output=True,
        env=_bare_machine_env(tmp_path),
        cwd=str(_REPO_ROOT),
        timeout=300,
        check=False,
    )
    exit_code = completed.returncode
    stderr = completed.stderr.decode("ascii", "replace")
    assert exit_code == 0, f"the probe exited {exit_code}: {stderr}"

    reported = json.loads(completed.stdout.decode("ascii", "replace"))
    size = reported["size"]
    assert size == PUBLISHED_ENDPOINTS, "the table built on a bare machine is not the endpoint set"

    codes = reported["codes"]
    assert codes["/api/world"] == contract.HTTP_UNAVAILABLE, (
        "an undetectable world did not answer 503 through the real provider"
    )
    strays = sorted(
        f"{template} answered {code}"
        for template, code in codes.items()
        if code not in BARE_MACHINE_CODES
    )
    stray_count = len(strays)
    assert stray_count == 0, f"a route answered outside the admitted set: {strays}"


def test_help_exits_zero_with_no_game_installed_and_no_save_present(tmp_path: Path) -> None:
    """``--help`` on a bare machine, which is where an operator meets this first.

    The bare-machine premise is measured by the arm above rather than assumed
    here. This arm on its own would pass with or without the scrub, because
    ``argparse`` exits before any path on this machine is resolved - which is
    itself the property worth having, and is why the scrub is proven elsewhere.
    """
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "clockspeed.surface", "--help"],
        capture_output=True,
        env=_bare_machine_env(tmp_path),
        cwd=str(_REPO_ROOT),
        timeout=300,
        check=False,
    )
    exit_code = completed.returncode
    stderr = completed.stderr.decode("ascii", "replace")
    assert exit_code == 0, f"--help exited {exit_code}: {stderr}"
    text = completed.stdout.decode("ascii", "replace")
    assert "--port" in text, "the help text does not name the port flag"
    assert entry.NO_WORLD_FLAG in text, "the help text does not name the save-detection flag"


def test_the_help_text_names_no_path_from_this_machine(tmp_path: Path) -> None:
    """``prog`` is spelled, not taken from ``sys.argv[0]``.

    Under ``-m`` the default program name argparse would render is the absolute
    path of ``__main__.py``, and on this machine that path contains the Windows
    account name (non-negotiable 3).
    """
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "clockspeed.surface", "--help"],
        capture_output=True,
        env=_bare_machine_env(tmp_path),
        cwd=str(_REPO_ROOT),
        timeout=300,
        check=False,
    )
    text = completed.stdout.decode("ascii", "replace")
    leaked = len(text)
    assert leaked > 0, "the help text was empty, so this proves nothing"
    assert "__main__.py" not in text, "the help text renders this file's own path"
    assert str(Path.home()) not in text, "the help text renders a home directory"


def test_the_auto_detect_flag_is_off_by_default_and_can_be_turned_off() -> None:
    detecting = entry.world_provider(auto_detect=True)
    assert hasattr(detecting, "world"), "the auto-detect provider does not satisfy the protocol"
    assert isinstance(detecting, contract.WorldProvider), (
        "the auto-detect provider does not satisfy WorldProvider"
    )

    disabled = entry.world_provider(auto_detect=False)
    assert disabled.world() is None, "the disabled provider still handed back a world"


def test_the_parser_defaults_to_auto_detecting_the_world() -> None:
    parsed = entry.parse_args([])
    assert parsed.auto_detect_world is True, "the world is not auto-detected by default"
    turned_off = entry.parse_args([entry.NO_WORLD_FLAG])
    assert turned_off.auto_detect_world is False, "the disable flag did not turn auto-detect off"


# ---------------------------------------------------------------------------
# The two seam arms: the table has to be one the server accepts, and a bind
# refusal has to reach the process exit code.
# ---------------------------------------------------------------------------


def test_the_table_this_slice_assembles_is_one_the_server_will_route() -> None:
    """The composition the acceptance module performs, asked as one question.

    ``tests/surface/test_acceptance.py`` calls ``serve(config, ROUTES)``. That
    call reaches ``server.routing`` before it reaches the certificate or the
    socket, so if the table will not build, every arm downstream of that fixture
    reports a listener failure rather than the thing it grades. Asking here
    separates the two.
    """
    table = server.routing(SERVING_ROUTES)
    routed = len(table)
    assert routed == PUBLISHED_ENDPOINTS, (
        "the server did not route the endpoint set this slice assembled"
    )


def test_a_bind_failure_exits_non_zero_and_names_the_port(tmp_path: Path) -> None:
    """A held port must produce the bind exit code, with the port in the message.

    The port is held by this process for the duration, so the failure is real
    rather than simulated. The exit code is asserted to be the SPECIFIC bind code
    rather than merely non-zero: an unhandled exception also exits non-zero, and
    "non-zero" would accept it.
    """
    cert_path, key_path = cert_pair(tmp_path)
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        holder.bind(("127.0.0.1", 0))
        holder.listen(1)
        held = holder.getsockname()[1]
        exit_code = entry.main(
            [
                "--port",
                str(held),
                "--cert-dir",
                str(cert_path.parent),
                entry.NO_WORLD_FLAG,
            ]
        )
    finally:
        holder.close()

    assert key_path.exists(), "the key was not minted, so the certificate path was not exercised"
    assert exit_code == server.EXIT_BIND_FAILED, (
        f"a held port exited {exit_code} rather than the bind code {server.EXIT_BIND_FAILED}"
    )


def test_the_bind_message_names_the_port_it_could_not_take() -> None:
    """``BindError`` has to carry the number, or the runbook cannot name it."""
    rendered = str(server.BindError(8999))
    assert "8999" in rendered, "a bind refusal does not name the port it could not take"


def test_the_exit_codes_the_runbook_branches_on_are_distinct() -> None:
    codes = (server.EXIT_OK, server.EXIT_BIND_FAILED, server.EXIT_CERTIFICATE, entry.EXIT_CONFIG)
    distinct = len(frozenset(codes))
    assert distinct == len(codes), "two exit codes collide, so a runbook cannot tell them apart"
    assert server.EXIT_OK == 0, "the success code is not zero"
    nonzero = tuple(code for code in codes if code != server.EXIT_OK)
    nonzero_count = len(nonzero)
    assert nonzero_count == len(codes) - 1, "a refusal code went missing"


def test_the_entry_point_source_names_no_second_port() -> None:
    """A SPELLING check, not a behavioural one - the bind arm above is the proof.

    Kept because it is the cheap half: the obvious spellings of a second attempt
    are caught before anyone has to stand up a listener to find out. It cannot
    catch a second attempt written some other way, which is exactly why it is not
    the arm that grades the behaviour.
    """
    source = Path(server.__file__).with_name("__main__.py").read_text(encoding="ascii")
    lowered = source.lower()
    named = sorted(
        spelling
        for spelling in ("port + 1", "port+1", "next_port", "another port", "second attempt")
        if spelling in lowered
    )
    named_count = len(named)
    assert named_count == 0, f"the entry point spells a second port attempt: {named}"


def test_the_module_body_is_seven_bit_ascii() -> None:
    for name in ("routes.py",):
        path = Path(contract.__file__).with_name(name)
        raw = path.read_bytes()
        high = sum(1 for byte in raw if byte > contract.MAX_ASCII_BYTE)
        assert high == 0, f"{name} carries {high} byte(s) above 7-bit ASCII"
    entry_path = Path(server.__file__).with_name("__main__.py")
    entry_raw = entry_path.read_bytes()
    entry_high = sum(1 for byte in entry_raw if byte > contract.MAX_ASCII_BYTE)
    assert entry_high == 0, f"__main__.py carries {entry_high} byte(s) above 7-bit ASCII"


def test_the_liveness_map_is_not_mutable_by_a_caller() -> None:
    assert not isinstance(ENDPOINT_STATUS, dict), (
        "the liveness map is a plain dict, so a handler could rewrite the server's own view"
    )
    assert isinstance(ENDPOINT_STATUS, Mapping), "the liveness map is not a mapping at all"
