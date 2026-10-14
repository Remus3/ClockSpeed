"""CS-1315 slice B - the three pricing doors serve the registry's provenance.

THE CLAUSE. ``docs/item_notes/phase5.md`` under CS-1315 ends "nothing prices a
figure from an unverified registry silently". ``/api/power``, ``/api/solve``
and ``/api/optimize`` each price figures from the registry, so each 200 body
carries ``build_state.registry_verified`` and the audit's own registry code
under the CS-1316 warning shape - the slice B contract recorded in
``docs/LEDGER.md`` before the code.

What is covered, and the authority for each arm:

a. EVERY DOOR, EVERY OUTCOME. Each door is driven over four registries: one
   built from the pinned docs bytes (verified, no registry code), one from
   other bytes (``registry-mismatch``), one with no byte source and one under
   an empty pin (both ``registry-unverified``). The codes are the audit's own
   constants, served verbatim under the ``build`` source at count one.
b. THE PIN IS READ AT CALL TIME. ``clockspeed.data.version.DOCS_SHA256`` is
   replaced AFTER every module here was imported; a door that bound the pin at
   import would still serve the mismatch.
c. THE SURFACE COMPARES NOTHING. ``clockspeed/surface/api/provenance.py`` is
   parsed: it imports no hashing module, holds no comparison operator, reads
   no ``source_sha256`` and calls ``registry_check_of`` - the one comparison
   ``clockspeed/audit/build.py`` owns.

Every hash here is ``tests.advisor.build_fixtures.docs_pin`` read at test time
or the invented ``OFF_PIN_DOCS_SHA256``; no digest is typed. Every registry is
a synthetic corpus built through the real seam; no game data is read.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.audit import build as build_model
from clockspeed.data import version
from clockspeed.data.registry import build_registry
from clockspeed.solve import optimize, ratio
from clockspeed.surface.api import contract, provenance, solve
from clockspeed.surface.api import power as power_endpoint
from tests.advisor.build_fixtures import OFF_PIN_DOCS_SHA256, docs_pin
from tests.data import synthetic as power_corpus
from tests.solve import synthetic as solve_corpus

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from clockspeed.data.registry import Registry

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: The three doors that price a figure from the registry.
DOORS: Final = ("power", "solve", "optimize")
EXPECTED_DOORS: Final = 3

#: The four registry outcomes every door is driven through.
CASES: Final = ("equal", "mismatch", "no-byte-source", "empty-pin")
EXPECTED_CASES: Final = 4

#: The keys the build state carries on these doors, and the warning row keys.
EXPECTED_BUILD_STATE_KEYS: Final = ("registry_verified",)
EXPECTED_WARNING_KEYS: Final = ("source", "code", "count")

#: The two registry codes the audit raises. Read off the audit, never typed.
REGISTRY_CODES: Final = frozenset(
    {build_model.WARN_REGISTRY_MISMATCH, build_model.WARN_REGISTRY_UNVERIFIED}
)

#: The comparison operators the surface module must not hold. ``Is`` and
#: ``IsNot`` are absent on purpose: a None test compares no two hashes.
COMPARISON_OPS: Final = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)

#: The modules a hash could be computed with.
HASHING_MODULES: Final = frozenset({"hashlib", "hmac", "_hashlib", "_sha256"})

PROVENANCE_SOURCE: Final = Path(provenance.__file__)


# ---------------------------------------------------------------------------
# The doors
# ---------------------------------------------------------------------------


class _StubRegistryProvider:
    """Hands back one registry. A stub rather than a mock: one method."""

    def __init__(self, value: Registry) -> None:
        """Record the registry.

        Args:
            value: The registry this provider hands back.
        """
        self._value = value

    def registry(self) -> Registry:
        """The registry this stub was built with.

        Returns:
            The registry.
        """
        return self._value


def _power_registry() -> Registry:
    """The power corpus, built through the real seam. It has no byte source."""
    return build_registry(power_corpus.synthetic_document())


def _power(registry: Registry) -> contract.Response:
    handler = power_endpoint.make_handler(_StubRegistryProvider(registry))
    return handler({power_endpoint.PARAM_BUILDING: power_corpus.BLENDER_BUILDING})


def _solve(registry: Registry) -> contract.Response:
    handler = solve.solve_handler(_StubRegistryProvider(registry))
    return handler(
        {
            solve.PARAM_TARGETS: f"{solve_corpus.SOLVE_ROD_ITEM}=50",
            solve.PARAM_RECIPES: f"{solve_corpus.ROD_RECIPE},{solve_corpus.PLATE_RECIPE}",
            solve.PARAM_RAW_ITEMS: solve_corpus.SOLVE_ORE_ITEM,
            solve.PARAM_BYPRODUCT_POLICY: ratio.BYPRODUCT_SINKABLE,
        }
    )


def _optimize(registry: Registry) -> contract.Response:
    handler = solve.optimize_handler(_StubRegistryProvider(registry))
    both = f"{solve_corpus.ALT_GADGET_RECIPE},{solve_corpus.STD_GADGET_RECIPE}"
    return handler(
        {
            solve.PARAM_TARGETS: f"{solve_corpus.SOLVE_TRINKET_ITEM}=30",
            solve.PARAM_CANDIDATES: both,
            solve.PARAM_UNLOCKED: both,
            solve.PARAM_RAW_ITEMS: solve_corpus.SOLVE_ORE_ITEM,
            solve.PARAM_BYPRODUCT_POLICY: ratio.BYPRODUCT_SINKABLE,
            solve.PARAM_OBJECTIVE: f"{optimize.OBJECTIVE_BUILDINGS}=1",
        }
    )


#: Door name to (the registry it prices from, the call that asks it).
_DOOR_CALLS: Final[
    Mapping[str, tuple[Callable[[], Registry], Callable[[Registry], contract.Response]]]
] = {
    "power": (_power_registry, _power),
    "solve": (solve_corpus.solve_registry, _solve),
    "optimize": (solve_corpus.solve_registry, _optimize),
}


def served(door: str, source_sha256: str | None) -> Mapping[str, object]:
    """The ``data`` object one door serves over a registry carrying one source hash.

    Args:
        door: One of :data:`DOORS`.
        source_sha256: The hash stamped on the registry, or None for none.

    Returns:
        The data object of the door's 200.
    """
    build, ask = _DOOR_CALLS[door]
    registry = dataclasses.replace(build(), source_sha256=source_sha256)
    response = ask(registry)
    status = response.http_status
    assert status == contract.HTTP_OK, response.payload
    data = response.payload["data"]
    assert isinstance(data, dict)
    return data


def build_rows(data: Mapping[str, object]) -> list[Mapping[str, object]]:
    """Every served warning row under the build source.

    Args:
        data: A door's data object.

    Returns:
        The rows, in body order.
    """
    rows = data["warnings"]
    assert isinstance(rows, list)
    return [row for row in rows if row["source"] == build_model.SOURCE_BUILD]


def served_case(door: str, case: str, monkeypatch: pytest.MonkeyPatch) -> Mapping[str, object]:
    """Serve one door under one of :data:`CASES`.

    Args:
        door: One of :data:`DOORS`.
        case: One of :data:`CASES`.
        monkeypatch: For the empty-pin case, which empties the pin.

    Returns:
        The data object.
    """
    pinned = docs_pin()
    if case == "equal":
        return served(door, pinned)
    if case == "mismatch":
        return served(door, OFF_PIN_DOCS_SHA256)
    if case == "no-byte-source":
        return served(door, None)
    monkeypatch.setattr(version, "DOCS_SHA256", "")
    return served(door, pinned)


#: What each case must serve: ``registry_verified`` and the registry codes.
EXPECTED: Final[Mapping[str, tuple[bool, tuple[str, ...]]]] = {
    "equal": (True, ()),
    "mismatch": (False, (build_model.WARN_REGISTRY_MISMATCH,)),
    "no-byte-source": (False, (build_model.WARN_REGISTRY_UNVERIFIED,)),
    "empty-pin": (False, (build_model.WARN_REGISTRY_UNVERIFIED,)),
}


# ---------------------------------------------------------------------------
# a. Every door, every outcome
# ---------------------------------------------------------------------------


def test_the_populations_are_the_sizes_this_module_claims() -> None:
    doors = len(DOORS)
    cases = len(CASES)
    assert doors == EXPECTED_DOORS
    assert cases == EXPECTED_CASES
    assert set(_DOOR_CALLS) == set(DOORS)
    assert set(EXPECTED) == set(CASES)


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("door", DOORS)
def test_every_door_serves_the_registry_state_the_audit_reached(
    door: str, case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = served_case(door, case, monkeypatch)
    verified, codes = EXPECTED[case]

    state = data["build_state"]
    assert isinstance(state, dict)
    assert tuple(state) == EXPECTED_BUILD_STATE_KEYS
    assert state["registry_verified"] is verified

    rows = build_rows(data)
    served_codes = tuple(str(row["code"]) for row in rows if row["code"] in REGISTRY_CODES)
    assert served_codes == codes
    for row in rows:
        assert tuple(row) == EXPECTED_WARNING_KEYS
        assert row["count"] == 1


@pytest.mark.parametrize("door", DOORS)
def test_a_verified_registry_serves_no_build_warning_at_all(door: str) -> None:
    data = served(door, docs_pin())
    rows = build_rows(data)
    count = len(rows)
    assert count == 0, rows


def test_the_power_body_publishes_both_keys_in_its_total_key_set() -> None:
    assert "build_state" in power_endpoint.DATA_KEYS
    assert "warnings" in power_endpoint.DATA_KEYS


@pytest.mark.parametrize("door", DOORS)
def test_the_served_shape_is_the_one_provenance_publishes(door: str) -> None:
    data = served(door, None)
    for key in provenance.DATA_KEYS:
        assert key in data, key
    assert provenance.BUILD_STATE_KEYS == EXPECTED_BUILD_STATE_KEYS
    assert provenance.WARNING_KEYS == EXPECTED_WARNING_KEYS
    assert provenance.WARNING_SOURCES == (build_model.SOURCE_BUILD,)


def test_the_optimize_plan_carries_no_second_copy_of_the_state() -> None:
    data = served("optimize", None)
    plan = data["plan"]
    assert isinstance(plan, dict)
    assert "build_state" not in plan
    assert "warnings" not in plan


# ---------------------------------------------------------------------------
# b. The pin is read at call time
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("door", DOORS)
def test_the_pin_is_read_when_the_door_answers_not_when_it_was_imported(
    door: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The registry carries the invented off-pin digest. Against the pin as it
    # was at import that is a mismatch; the pin is replaced now, so a door
    # reading it at call time serves the registry as verified.
    monkeypatch.setattr(version, "DOCS_SHA256", OFF_PIN_DOCS_SHA256)

    data = served(door, OFF_PIN_DOCS_SHA256)

    state = data["build_state"]
    assert isinstance(state, dict)
    assert state["registry_verified"] is True
    count = len(build_rows(data))
    assert count == 0


# ---------------------------------------------------------------------------
# c. The surface compares nothing
# ---------------------------------------------------------------------------


def _tree() -> ast.Module:
    return ast.parse(PROVENANCE_SOURCE.read_bytes().decode("ascii"))


def imported_modules(tree: ast.AST) -> list[str]:
    """Every module an import statement in a tree names.

    Args:
        tree: A parsed module.

    Returns:
        The dotted names, in walk order.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.append(node.module)
    return found


def comparisons(tree: ast.AST) -> int:
    """How many comparison operators a tree holds.

    Args:
        tree: A parsed module.

    Returns:
        The count.
    """
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        for op in node.ops
        if isinstance(op, COMPARISON_OPS)
    )


def attributes(tree: ast.AST) -> set[str]:
    """Every attribute name a tree reads or calls.

    Args:
        tree: A parsed module.

    Returns:
        The names.
    """
    return {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}


def test_the_provenance_module_imports_no_hashing_module() -> None:
    imported = imported_modules(_tree())
    count = len(imported)
    assert count > 0, "an empty import list would satisfy this vacuously"
    hashing = [name for name in imported if name.split(".")[0] in HASHING_MODULES]
    assert hashing == []


def test_the_provenance_module_compares_nothing() -> None:
    tree = _tree()
    found = comparisons(tree)
    assert found == 0
    read = attributes(tree)
    assert "source_sha256" not in read
    assert "registry_check_of" in read
    assert "DOCS_SHA256" in read


def test_the_provenance_module_never_binds_the_pin_at_import() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module == "clockspeed.data.version":
            names = [alias.name for alias in node.names]
            assert "DOCS_SHA256" not in names, names


def test_the_comparison_detectors_fire_on_planted_positives() -> None:
    planted = ast.parse(
        "import hashlib\ndef f(registry, pin):\n    return registry.source_sha256 == pin\n"
    )
    found = comparisons(planted)
    assert found == 1
    assert "hashlib" in imported_modules(planted)
    assert "source_sha256" in attributes(planted)
