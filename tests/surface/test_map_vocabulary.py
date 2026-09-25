"""CS-1189 - ``/api/map`` serves only item keys the registry's closed vocabulary names.

WHAT WAS FOUND. An item key is whatever string a save's ``ItemClass`` carried,
reduced by ``clockspeed.audit.placement.class_name_of_path`` - which returns a
DOTLESS string unchanged. So a key shaped like a home path, or like a platform
account id, survived the reduction as a "class name" and ``/api/map`` served it
verbatim in the inventory section.

WHAT IS COVERED HERE, AND THE AUTHORITY FOR EACH ARM

a. THE PLANTS GO THROUGH THE REAL LOADER. Two PII-SHAPED keys - never PII, both
   assembled at runtime from obviously synthetic parts - ride in a (14,60)
   array of struct built with ``tests/save/synthetic.py``'s own encoders, next
   to one key the fixture registry DOES name. A control asserts all three reach
   the audit layer's inventory model, so the absence arm cannot pass because
   the plant never decoded.
b. NEITHER PLANT REACHES THE BODY OR THE ROUTE RESPONSE'S REPR. Asserted over
   the encoded wire bytes, in both the raw and the JSON-escaped spelling, and
   over ``repr`` of the ``contract.Response`` the route returns.
c. AN UNKNOWN KEY IS FLAGGED AND SKIPPED (CLAUDE.md section 3 rule 7). One
   ``map``-sourced warning carries the count of withheld totals and no key
   text; the known key is still served with its display name.
d. NO REGISTRY, NO VOCABULARY: FAIL CLOSED. Every key is withheld and the
   existing ``registry-unavailable`` warning says why.
e. PLACEMENT CLASS NAMES WERE MEASURED WITH THE SAME PLANTS. They do not leak:
   ``clockspeed/audit/placement.py`` admits a built class only through its own
   closed allowlist and ``clockspeed/save/world.py`` admits a node the same way.
   A negative control widens that allowlist in memory and asserts the plant
   then DOES reach the body, so the absence arm is proved able to see one.
f. ``MachineState.class_name`` BEFORE ANY ROUTE SERVES IT. No surface module
   imports ``clockspeed.audit.machines`` today. A structural arm fails the day
   one does and reads ``.class_name`` anywhere but as the argument of
   ``clockspeed.surface.api.map.closed_key``; planted modules in a temporary
   copy of the package prove the arm live and prove its control passes.

NO REAL CONTENT REACHES THIS MODULE. Every string is invented, every save is
synthetic bytes, and the registry is the hand-built literal
``tests/surface/test_map.py`` publishes.
"""

from __future__ import annotations

import ast
import json
import shutil
import struct
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

import clockspeed.surface
from clockspeed.audit import inventory as inventory_model
from clockspeed.audit import placement as placement_model
from clockspeed.data.locate import MIN_ACCOUNT_ID_DIGITS
from clockspeed.save import world
from clockspeed.surface.api import contract
from clockspeed.surface.api import map as endpoint
from tests.save import synthetic
from tests.surface.test_map import (
    ITEM_DISPLAY_NAME,
    ITEM_KEY,
    answer,
    body_of,
    empty_property_map,
    fixture_registry,
    rows,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

# ---------------------------------------------------------------------------
# The plants. PII-SHAPED, NOT PII: each is assembled at runtime from invented
# fragments, so this file holds no drive-path literal and no account-id-shaped
# digit run for tests/data/test_phase2_gate.py or tests/test_scaffold.py to find.
# ---------------------------------------------------------------------------

#: The distinctive fragment inside the home-path-shaped plant. The absence
#: assertion keys on it as well as on the whole key, because the JSON encoder
#: escapes a backslash and the raw key would then never match the wire anyway.
HOME_PLANT_MARKER: Final = "VocabPlantHomeZa01"

#: How many digits the account-shaped plant carries: two past the floor the
#: resolver treats as an account id, so it is unambiguously in that shape.
ACCOUNT_PLANT_DIGITS: Final = MIN_ACCOUNT_ID_DIGITS + 2

#: The amounts each stack carries. Distinct, so a count served under the wrong
#: key cannot look right.
KNOWN_AMOUNT: Final = 5
HOME_AMOUNT: Final = 7
ACCOUNT_AMOUNT: Final = 11

#: The two unknown keys this fixture plants.
UNKNOWN_PLANTS: Final = 2

#: The one row the registry names and therefore the one that is served.
ONE_ROW: Final = 1

#: The (14,60) property names the audit layer recognises as an item stack. Taken
#: from the audit layer's own published vocabulary rather than restated.
ITEM_KEY_NAME: Final = next(iter(inventory_model.ITEM_KEY_PROPERTY_NAMES))
ITEM_COUNT_NAME: Final = next(iter(inventory_model.ITEM_COUNT_PROPERTY_NAMES))

#: The known item's full path, reduced by the audit layer to ``ITEM_KEY``.
KNOWN_ITEM_PATH: Final = "/Synthetic/Items/Desc_SyntheticOre." + ITEM_KEY

#: The actor whose payload carries the stacks. Every string invented.
HOLDER_CLASS_PATH: Final = "/Synthetic/Parts/Build_SyntheticVocab.Build_SyntheticVocab_C"
HOLDER_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticVocab_C_0"
STACKS_NAME: Final = "mSyntheticVocabStacks"
STACK_STRUCT_WORD: Final = "SyntheticVocabStack"

HEADER_VERSION: Final = 14
SAVE_VERSION: Final = 60


def home_shaped_key() -> str:
    """A DOTLESS string shaped like an absolute path under a user home.

    Dotless on purpose: ``class_name_of_path`` returns such a string unchanged,
    which is exactly how the finding reached the wire.

    Returns:
        The key.
    """
    drive = chr(ord("A") + 2) + ":"
    separator = chr(0x5C)
    return separator.join((drive, "Users", HOME_PLANT_MARKER, "Saved", "SaveGames"))


def account_shaped_key() -> str:
    """A digit run in the shape the resolver treats as a platform account id.

    Returns:
        The key.
    """
    return "".join(str((index * 7 + 3) % 10) for index in range(ACCOUNT_PLANT_DIGITS))


def planted_keys() -> tuple[str, str]:
    """Both unknown plants, in a fixed order.

    Returns:
        The home-path-shaped key and the account-shaped key.
    """
    return home_shaped_key(), account_shaped_key()


def needles_of(key: str) -> tuple[bytes, ...]:
    """Every byte spelling a key could take on the wire.

    Args:
        key: The planted key.

    Returns:
        The raw spelling, the JSON-escaped spelling and, for the home-shaped
        plant, its distinctive fragment.
    """
    escaped = json.dumps(key)[1:-1]
    spellings = {key, escaped}
    if HOME_PLANT_MARKER in key:
        spellings.add(HOME_PLANT_MARKER)
    return tuple(sorted(spelling.encode("ascii") for spelling in spellings))


def stack(key: str, amount: int) -> bytes:
    """One (14,60) struct interior naming an item and an amount.

    Args:
        key: The ``ItemClass`` value, written as a string property.
        amount: The ``Amount`` value.

    Returns:
        The encoded tag list.
    """
    return synthetic.type_tree_tag_list(
        (
            synthetic.type_tree_property_tag(
                ITEM_KEY_NAME,
                synthetic.type_name_tree(synthetic.TREE_STR_TYPE_WORD),
                synthetic.fstring(key),
            ),
            synthetic.type_tree_property_tag(
                ITEM_COUNT_NAME,
                synthetic.type_name_tree(synthetic.TREE_INT_TYPE_WORD),
                struct.pack("<i", amount),
            ),
        )
    )


def planted_blob(*, placement_plants: bool = False) -> bytes:
    """A levelled (14,60) save carrying the plants in ONE of two places.

    ONE PLACE PER WORLD, NEVER BOTH. A world carrying both would let the item
    plant satisfy - or fail - the placement measurement, and the two findings
    would be indistinguishable on the wire.

    Args:
        placement_plants: False plants the keys as three item stacks on one
            actor's payload; True plants them instead as the TYPE PATHS of two
            records, for the placement measurement.

    Returns:
        The whole blob.
    """
    home, account = planted_keys()
    elements = (
        stack(KNOWN_ITEM_PATH, KNOWN_AMOUNT),
        stack(home, HOME_AMOUNT),
        stack(account, ACCOUNT_AMOUNT),
    )
    payload = synthetic.type_tree_property_payload(
        (synthetic.type_tree_array_of_struct_tag(STACKS_NAME, STACK_STRUCT_WORD, elements),),
        head=synthetic.actor_payload_head(synthetic.MAP_NAME, synthetic.TREE_DECODABLE_ROOT, ()),
        trailing=synthetic.DECODABLE_TRAILING_RUN,
    )
    stacks = synthetic.SyntheticLevel(
        name="Persistent_Level:SyntheticVocabCell_0",
        objects=(
            synthetic.SyntheticObject(
                HOLDER_CLASS_PATH, synthetic.TREE_DECODABLE_ROOT, HOLDER_INSTANCE
            ),
        ),
        payloads=(payload,),
    )
    placed = synthetic.SyntheticLevel(
        name="Persistent_Level:SyntheticVocabCell_1",
        objects=tuple(
            synthetic.SyntheticObject(
                plant,
                synthetic.TREE_DECODABLE_ROOT,
                "Persistent_Level:PersistentLevel.SyntheticVocabPlaced_" + str(index),
            )
            for index, plant in enumerate(planted_keys())
        ),
    )
    body = synthetic.build_levelled_body(
        (placed if placement_plants else stacks,),
        synthetic.DECODABLE_PERSISTENT,
        header_version=HEADER_VERSION,
        save_version=SAVE_VERSION,
        grids=synthetic.LEVELLED_GRIDS,
    )
    header = synthetic.build_header(header_version=HEADER_VERSION, save_version=SAVE_VERSION)
    framed = synthetic.build_chunks(
        synthetic.body_with_prefix(body, HEADER_VERSION),
        framing=synthetic.default_framing(HEADER_VERSION),
    )
    return header + framed


def planted_world(*, placement_plants: bool = False) -> world.WorldModel:
    """Drive the planted save through the REAL loader.

    Args:
        placement_plants: Forwarded to :func:`planted_blob`.

    Returns:
        The loaded world.
    """
    return world.load_world_from_bytes(
        planted_blob(placement_plants=placement_plants), property_map=empty_property_map()
    )


def leaks_in(response: contract.Response) -> list[str]:
    """Name which plant reached the wire or the repr, by position only.

    The PLANT ITSELF IS NEVER RETURNED, so a failure message cannot echo the
    very shape this file exists to keep off every output.

    Args:
        response: The route's response.

    Returns:
        One label per plant found, empty when neither was.
    """
    wire = contract.encode(response.payload)
    rendered = repr(response).encode("ascii", "backslashreplace")
    labels = ("home-path-shaped", "account-shaped")
    found: list[str] = []
    for label, key in zip(labels, planted_keys(), strict=True):
        for needle in needles_of(key):
            if needle in wire:
                found.append(label + " in body")
            if needle in rendered:
                found.append(label + " in repr")
    return sorted(set(found))


# ---------------------------------------------------------------------------
# a - the plants really are in the model the endpoint is handed
# ---------------------------------------------------------------------------


def test_the_plants_are_pii_shaped_and_dotless() -> None:
    """A plant with a dot would be reduced by the audit layer and prove nothing."""
    home, account = planted_keys()
    assert "." not in home, "the home-shaped plant carries a dot"
    assert "." not in account, "the account-shaped plant carries a dot"
    assert home[1] == ":", "the home-shaped plant is not drive-rooted"
    assert HOME_PLANT_MARKER in home, "the marker is not inside the plant"
    digits = len(account)
    assert account.isdigit(), "the account-shaped plant is not a digit run"
    assert digits >= MIN_ACCOUNT_ID_DIGITS, "digit run too short: " + str(digits)


def test_every_plant_reaches_the_inventory_model_through_the_real_loader() -> None:
    """The anti-vacuity control: an absence on the wire must not be an absent plant."""
    held = inventory_model.inventory_of(planted_world())
    keys = {total.item_key for total in held.items}
    known = ITEM_KEY in keys
    assert known, "the known key did not reach the model"
    reached = sum(1 for plant in planted_keys() if plant in keys)
    assert reached == UNKNOWN_PLANTS, "plants reaching the model: " + str(reached)


# ---------------------------------------------------------------------------
# b - neither plant reaches the body or the response repr
# ---------------------------------------------------------------------------


def test_neither_planted_item_key_reaches_the_map_body_or_the_response_repr() -> None:
    """The finding itself, graded on the encoded wire AND on the route's Response."""
    response = answer(planted_world(), fixture_registry())
    assert response.http_status == contract.HTTP_OK, response.http_status
    found = leaks_in(response)
    assert found == [], "planted keys reached the output: " + ", ".join(found)


def test_the_leak_detector_finds_a_plant_in_a_planted_leaky_payload() -> None:
    """The oracle is not blind to its subject: a raw echo IS found."""
    home, account = planted_keys()
    leaky = contract.ok(endpoint.ENDPOINT, {"inventory": [{"item_key": home}, {"k": account}]})
    found = leaks_in(leaky)
    assert found == ["account-shaped in body", "home-path-shaped in body"], ", ".join(found)


# ---------------------------------------------------------------------------
# c - an unknown key is flagged and skipped; a known one is still served
# ---------------------------------------------------------------------------


def test_a_known_item_key_is_still_served_with_its_display_name() -> None:
    """The check withholds the unknown, not everything."""
    data = body_of(answer(planted_world(), fixture_registry()))
    served = rows(data, "inventory")
    count = len(served)
    assert count == ONE_ROW, "inventory rows served: " + str(count)
    row = served[0]
    assert frozenset(row) == frozenset(endpoint.INVENTORY_KEYS), sorted(row)
    assert row["item_key"] == ITEM_KEY, "the known key was not served"
    assert row["display_name"] == ITEM_DISPLAY_NAME, "the display name was not joined"
    assert row["count"] == KNOWN_AMOUNT, "the known count moved"


def test_an_unknown_item_key_is_flagged_under_the_map_source_with_a_count() -> None:
    """Rule 7: flagged and skipped, never silently dropped."""
    data = body_of(answer(planted_world(), fixture_registry()))
    flagged = [
        row
        for row in rows(data, "warnings")
        if row["source"] == endpoint.SOURCE_MAP and row["code"] == endpoint.WARN_ITEM_KEY_UNKNOWN
    ]
    raised = len(flagged)
    assert raised == ONE_ROW, "unknown-key warnings raised: " + str(raised)
    row = flagged[0]
    assert frozenset(row) == frozenset(endpoint.WARNING_KEYS), sorted(row)
    assert row["count"] == UNKNOWN_PLANTS, "withheld count: " + str(row["count"])


def test_no_unknown_key_warning_is_raised_when_every_key_is_known() -> None:
    """The flag is a fact about THIS world, not a constant the body always carries."""
    registry = fixture_registry()
    data = body_of(answer(planted_world(), registry))
    codes_with = {str(row["code"]) for row in rows(data, "warnings")}
    assert endpoint.WARN_ITEM_KEY_UNKNOWN in codes_with, sorted(codes_with)

    empty = world.load_world_from_bytes(
        synthetic.build_save(objects=()),
        property_map=empty_property_map(),
        body_layout=world.BODY_LAYOUT_FLAT,
    )
    data = body_of(answer(empty, registry))
    codes_without = {str(row["code"]) for row in rows(data, "warnings")}
    assert endpoint.WARN_ITEM_KEY_UNKNOWN not in codes_without, sorted(codes_without)


def test_the_unknown_key_code_is_a_map_code_of_this_modules_own() -> None:
    """Published beside the other WARN_* constants, distinct from every one."""
    codes = (
        endpoint.WARN_REGISTRY_UNAVAILABLE,
        endpoint.WARN_EXTRACTION_RATE_UNAVAILABLE,
        endpoint.WARN_NO_MODELLED_EXTRACTOR_BUILT,
    )
    assert endpoint.WARN_ITEM_KEY_UNKNOWN not in codes, endpoint.WARN_ITEM_KEY_UNKNOWN
    assert "WARN_ITEM_KEY_UNKNOWN" in endpoint.__all__, "the code is not published"
    assert GUARD_NAME in endpoint.__all__, "the check is not published"
    assert endpoint.closed_key.__name__ == GUARD_NAME, endpoint.closed_key.__name__


def test_the_closed_key_check_is_a_membership_lookup() -> None:
    """A join like display_name_of, never a computation and never a synthesis."""
    vocabulary = fixture_registry().items
    assert endpoint.closed_key(vocabulary, ITEM_KEY) == ITEM_KEY
    assert endpoint.closed_key(vocabulary, home_shaped_key()) is None
    assert endpoint.closed_key({}, ITEM_KEY) is None
    assert endpoint.closed_key(None, ITEM_KEY) is None


# ---------------------------------------------------------------------------
# d - no registry: no vocabulary exists, so every key is withheld
# ---------------------------------------------------------------------------


def test_with_no_registry_every_item_key_is_withheld_and_the_body_says_why() -> None:
    """Fail closed: without a vocabulary nothing can be shown to be publisher content."""
    response = answer(planted_world(), None)
    data = body_of(response)
    served = len(rows(data, "inventory"))
    assert served == 0, "inventory rows served with no registry: " + str(served)
    codes = {
        str(row["code"]) for row in rows(data, "warnings") if row["source"] == endpoint.SOURCE_MAP
    }
    assert endpoint.WARN_REGISTRY_UNAVAILABLE in codes, sorted(codes)
    found = leaks_in(response)
    assert found == [], "planted keys reached the output: " + ", ".join(found)


# ---------------------------------------------------------------------------
# e - placement class names, measured with the same plants
# ---------------------------------------------------------------------------


def test_a_planted_type_path_reaches_the_record_table() -> None:
    """The anti-vacuity control for the placement measurement."""
    model = planted_world(placement_plants=True)
    names = {placement_model.class_name_of_path(rec.type_path) for rec in model.objects.records}
    reached = sum(1 for plant in planted_keys() if plant in names)
    assert reached == UNKNOWN_PLANTS, "plants reaching the record table: " + str(reached)


def test_a_planted_type_path_never_reaches_a_placement_row_or_a_tally() -> None:
    """MEASURED: the audit layer's closed allowlist keeps both plants off the map."""
    response = answer(planted_world(placement_plants=True), fixture_registry())
    found = leaks_in(response)
    assert found == [], "planted class names reached the output: " + ", ".join(found)


def test_the_placement_measurement_can_see_a_plant_the_allowlist_admits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NEGATIVE CONTROL: widen the allowlist in memory and the plant DOES arrive."""
    widened = frozenset({*placement_model.BUILT_CLASS_ALLOWLIST, *planted_keys()})
    monkeypatch.setattr(placement_model, "BUILT_CLASS_ALLOWLIST", widened)
    response = answer(planted_world(placement_plants=True), fixture_registry())
    found = leaks_in(response)
    assert "home-path-shaped in body" in found, ", ".join(found)
    assert "account-shaped in body" in found, ", ".join(found)


# ---------------------------------------------------------------------------
# f - MachineState.class_name before any route serves it
# ---------------------------------------------------------------------------

MACHINES_MODULE: Final = "clockspeed.audit.machines"
#: Spelled rather than read off the function, so this module still COLLECTS
#: when the function is missing and the arms below fail on their assertions;
#: ``test_the_unknown_key_code_is_a_map_code_of_this_modules_own`` binds the two.
GUARD_NAME: Final = "closed_key"
GENERIC_WALKERS: Final = frozenset({"asdict", "astuple", "vars", "__dict__", "fields"})
SURFACE_ROOT: Final = Path(clockspeed.surface.__file__).resolve().parent


def _imports_machines(tree: ast.AST) -> bool:
    """Whether a module reaches the machines model by any import spelling.

    Args:
        tree: The parsed module.

    Returns:
        True for ``import clockspeed.audit.machines``, ``from clockspeed.audit
        import machines``, ``from clockspeed.audit.machines import ...`` and a
        string naming the module (an ``importlib`` call).
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == MACHINES_MODULE or alias.name.startswith(MACHINES_MODULE + ".")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom):
            if node.module == MACHINES_MODULE:
                return True
            if node.module == "clockspeed.audit" and any(
                alias.name == "machines" for alias in node.names
            ):
                return True
        if isinstance(node, ast.Constant) and node.value == MACHINES_MODULE:
            return True
    return False


def _callee_name(call: ast.Call) -> str | None:
    """The bare name a call is made through.

    Args:
        call: The call node.

    Returns:
        ``f`` for ``f(...)`` and ``a.f(...)``, else None.
    """
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _module_faults(tree: ast.AST) -> list[int]:
    """Every line where a machines-importing module serves a class name unchecked.

    Args:
        tree: The parsed module.

    Returns:
        The offending line numbers; empty when the module does not import the
        machines model at all.
    """
    if not _imports_machines(tree):
        return []
    routed: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _callee_name(node) == GUARD_NAME:
            routed.update(id(arg) for arg in node.args)
            routed.update(id(keyword.value) for keyword in node.keywords)
    return sorted(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Call)) and _is_unchecked(node, routed)
    )


def _is_unchecked(node: ast.Attribute | ast.Call, routed: set[int]) -> bool:
    """Whether one node reads a machine's class name past the check.

    Args:
        node: An attribute read or a call.
        routed: The ids of every node passed straight into the check.

    Returns:
        True for a ``.class_name`` read not passed straight into the check, a
        ``getattr`` naming it, a generic dataclass walker, or a ``__dict__``
        read - the last two dump the field without ever spelling it.
    """
    if isinstance(node, ast.Attribute):
        if node.attr == "class_name":
            return id(node) not in routed
        return node.attr == "__dict__"
    callee = _callee_name(node)
    if callee == "getattr":
        return any(isinstance(arg, ast.Constant) and arg.value == "class_name" for arg in node.args)
    return callee in GENERIC_WALKERS


def _python_files(root: Path) -> Iterator[Path]:
    """Every Python module under a package root, in a fixed order.

    Args:
        root: The package directory.

    Yields:
        Each ``.py`` path.
    """
    yield from sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def machine_seam_faults(root: Path) -> tuple[int, list[str]]:
    """Scan a surface package tree for an unchecked ``MachineState.class_name``.

    Args:
        root: The package directory to scan.

    Returns:
        How many modules were scanned, and one ``relative-path:line`` label per
        fault.
    """
    scanned = 0
    faults: list[str] = []
    for path in _python_files(root):
        scanned += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(root).as_posix()
        faults.extend(relative + ":" + str(line) for line in _module_faults(tree))
    return scanned, faults


@pytest.fixture
def surface_copy(tmp_path: Path) -> Path:
    """A throwaway copy of the shipped surface package, for planting modules in.

    Args:
        tmp_path: pytest's per-test directory.

    Returns:
        The copy's root.
    """
    target = tmp_path / "surface"
    shutil.copytree(
        SURFACE_ROOT, target, ignore=shutil.ignore_patterns("__pycache__", "web", "*.pyc")
    )
    return target


RAW_PLANTS: Final = (
    "from clockspeed.audit import machines\n\n"
    "def serve(state: machines.MachineState) -> dict[str, object]:\n"
    '    return {"class_name": state.class_name}\n',
    "import clockspeed.audit.machines\n\n"
    "def serve(state: object) -> object:\n"
    "    return state.class_name\n",
    "from clockspeed.audit.machines import MachineState\n\n"
    "def serve(state: MachineState) -> object:\n"
    '    return getattr(state, "class_name")\n',
    "from dataclasses import asdict\n"
    "from clockspeed.audit.machines import MachineState\n\n"
    "def serve(state: MachineState) -> object:\n"
    "    return asdict(state)\n",
)


def test_the_shipped_surface_serves_no_unchecked_machine_class_name() -> None:
    """The arm that fails the day a route serves MachineState without the check."""
    scanned, faults = machine_seam_faults(SURFACE_ROOT)
    expected = sum(1 for _ in _python_files(SURFACE_ROOT))
    assert expected > 0, "the surface package holds no module, so this arm grades nothing"
    assert scanned == expected, "modules scanned: " + str(scanned)
    assert faults == [], "unchecked machine class names: " + ", ".join(faults)


@pytest.mark.parametrize("source", RAW_PLANTS, ids=("from-audit", "import", "getattr", "asdict"))
def test_the_machine_seam_arm_finds_a_planted_unchecked_route(
    surface_copy: Path, source: str
) -> None:
    """LIVE: a planted module serving the class name raw is found, in every spelling."""
    (surface_copy / "api" / "planted_machines.py").write_text(source, encoding="utf-8")
    _, faults = machine_seam_faults(surface_copy)
    count = len(faults)
    assert count == ONE_ROW, "faults found: " + ", ".join(faults)
    assert faults[0].startswith("api/planted_machines.py:"), faults[0]


def test_the_machine_seam_arm_passes_a_planted_route_that_uses_the_check(
    surface_copy: Path,
) -> None:
    """CONTROL: the same planted route, routed through closed_key, is not a fault."""
    source = (
        "from clockspeed.audit import machines\n"
        "from clockspeed.surface.api import map as endpoint\n\n"
        "def serve(state: machines.MachineState, vocabulary: object) -> dict[str, object]:\n"
        '    return {"class_name": endpoint.closed_key(vocabulary, state.class_name)}\n'
    )
    (surface_copy / "api" / "planted_machines.py").write_text(source, encoding="utf-8")
    scanned, faults = machine_seam_faults(surface_copy)
    assert scanned > 0, "the copy holds no module"
    assert faults == [], "a checked route was flagged: " + ", ".join(faults)
