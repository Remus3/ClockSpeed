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
   reaches ``clockspeed.audit.machines`` today, so the rule is FAIL CLOSED: any
   reach at all - a static import in any spelling, relative and star included,
   ``from clockspeed import audit`` then ``.machines``, a runtime import it
   cannot show is harmless, ``sys.modules`` - is refused, and the message says
   to add one sanctioned accessor that applies
   ``clockspeed.surface.api.map.closed_key``. Following ``class_name`` after
   the reach was refuted: ``repr``, an f-string, a ``match`` pattern,
   ``attrgetter`` and a local lookalike of the check all read it unseen.
   Every probe form is planted in a temporary copy of the package, and a
   control proves harmless sibling imports are not refused.

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

#: Spelled rather than read off the function, so this module still COLLECTS
#: when the function is missing and the arms fail on their assertions;
#: ``test_the_unknown_key_code_is_a_map_code_of_this_modules_own`` binds the two.
GUARD_NAME: Final = "closed_key"

MACHINES_MODULE: Final = "clockspeed.audit.machines"
AUDIT_PACKAGE: Final = "clockspeed.audit"
MACHINES_NAME: Final = "machines"
SURFACE_PACKAGE: Final = "clockspeed.surface"
SURFACE_ROOT: Final = Path(clockspeed.surface.__file__).resolve().parent

#: What the rule says when it fires. FAIL CLOSED: no route serves a machine
#: today, so the first one to need it is told where the check lives rather than
#: left to invent a spelling this rule has not seen.
REMEDY: Final = (
    "no clockspeed/surface module may reach " + MACHINES_MODULE + " (CS-1189): add ONE"
    " sanctioned accessor that passes every MachineState.class_name through"
    " clockspeed.surface.api.map.closed_key, then admit exactly that module here"
)

#: The calls that import by NAME at runtime. Any one of them is refused unless
#: its target is a string constant that names neither the machines module nor
#: the audit package - a computed name cannot be shown to be neither.
DYNAMIC_IMPORTERS: Final = frozenset(
    {
        "import_module",
        "__import__",
        "find_spec",
        "spec_from_file_location",
        "module_from_spec",
        "run_module",
        "run_path",
        "load_module",
        "exec_module",
    }
)

#: Modules whose OBJECT, once bound, reaches the machines model by attribute.
PARENT_PACKAGES: Final = frozenset({"clockspeed", AUDIT_PACKAGE})


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


def _absolute(node: ast.ImportFrom, package: str) -> str:
    """Resolve an ``ImportFrom``'s module to its absolute dotted name.

    Args:
        node: The import.
        package: The package the importing module sits in.

    Returns:
        The absolute module name the import reads from.
    """
    if not node.level:
        return node.module or ""
    parts = package.split(".")
    base = parts[: len(parts) - (node.level - 1)]
    return ".".join([*base, node.module] if node.module else base)


def _reaches_by_import(node: ast.AST, package: str) -> bool:
    """Whether one static import statement reaches the machines model.

    Args:
        node: Any node.
        package: The importing module's package, for a relative import.

    Returns:
        True for the module itself or anything under it, for ``machines`` or
        ``*`` taken from the audit package, relative spellings included.
    """
    if isinstance(node, ast.Import):
        return any(
            alias.name == MACHINES_MODULE or alias.name.startswith(MACHINES_MODULE + ".")
            for alias in node.names
        )
    if isinstance(node, ast.ImportFrom):
        module = _absolute(node, package)
        if module == MACHINES_MODULE or module.startswith(MACHINES_MODULE + "."):
            return True
        return module == AUDIT_PACKAGE and any(
            alias.name in {MACHINES_NAME, "*"} for alias in node.names
        )
    return False


def _binds_a_parent(tree: ast.AST, package: str) -> bool:
    """Whether a module binds ``clockspeed`` or ``clockspeed.audit`` as an object.

    Args:
        tree: The parsed module.
        package: The module's package.

    Returns:
        True when an attribute named ``machines`` could then be the model.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name in PARENT_PACKAGES for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom):
            module = _absolute(node, package)
            if module == "clockspeed" and any(alias.name in {"audit", "*"} for alias in node.names):
                return True
    return False


def _docstring_ids(tree: ast.AST) -> set[int]:
    """The ids of every bare string statement - docstrings, which run nothing.

    Args:
        tree: The parsed module.

    Returns:
        The ids of those constants.
    """
    return {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
    }


def _dynamic_reach(call: ast.Call) -> bool:
    """Whether one runtime import call could reach the machines model.

    Args:
        call: A call through a name in :data:`DYNAMIC_IMPORTERS`.

    Returns:
        True unless its target is a string constant naming neither the model
        nor the audit package.
    """
    if not call.args:
        return True
    target = call.args[0]
    if not (isinstance(target, ast.Constant) and isinstance(target.value, str)):
        return True
    return MACHINES_NAME in target.value or target.value.startswith(AUDIT_PACKAGE)


def _module_faults(tree: ast.AST, package: str) -> list[int]:
    """Every line where a surface module reaches the machines model, by any form.

    FAIL CLOSED. The rule does not try to follow ``class_name`` once the model
    is in hand - ``repr``, an f-string, a ``match`` pattern, ``attrgetter`` and
    a local lookalike of the check all read it without spelling a checkable
    call - so it refuses the REACH itself: a static import in any spelling, a
    runtime import whose name it cannot show is harmless, ``sys.modules``, a
    ``machines`` attribute off a bound parent package, and any executable
    string naming the module.

    Args:
        tree: The parsed module.
        package: The module's package.

    Returns:
        The offending line numbers.
    """
    parent_bound = _binds_a_parent(tree, package)
    docstrings = _docstring_ids(tree)
    return sorted(
        {
            getattr(node, "lineno", 0)
            for node in ast.walk(tree)
            if _node_reaches(node, package, parent_bound=parent_bound, docstrings=docstrings)
        }
    )


def _node_reaches(node: ast.AST, package: str, *, parent_bound: bool, docstrings: set[int]) -> bool:
    """Whether one node is a reach :func:`_module_faults` refuses.

    Args:
        node: Any node.
        package: The module's package.
        parent_bound: Whether the module binds a parent package object.
        docstrings: The ids of the module's bare string statements.

    Returns:
        True for a refused reach.
    """
    if _reaches_by_import(node, package):
        return True
    if isinstance(node, ast.Call) and _callee_name(node) in DYNAMIC_IMPORTERS:
        return _dynamic_reach(node)
    if isinstance(node, ast.Attribute):
        if node.attr == "modules" and isinstance(node.value, ast.Name):
            return node.value.id == "sys"
        return node.attr == MACHINES_NAME and parent_bound
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return id(node) not in docstrings and _names_the_model(
            node.value, parent_bound=parent_bound
        )
    return False


def _names_the_model(text: str, *, parent_bound: bool) -> bool:
    """Whether an executable string names the machines model.

    Args:
        text: The string constant.
        parent_bound: Whether the module binds a parent package object, so a
            bare ``"machines"`` can be an attribute name for ``getattr``.

    Returns:
        True when it does.
    """
    return MACHINES_MODULE in text or (text == MACHINES_NAME and parent_bound)


def _python_files(root: Path) -> Iterator[Path]:
    """Every Python module under a package root, in a fixed order.

    Args:
        root: The package directory.

    Yields:
        Each ``.py`` path.
    """
    yield from sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def machine_seam_faults(root: Path) -> tuple[int, list[str]]:
    """Scan a surface package tree for any module reaching the machines model.

    Args:
        root: The package directory to scan, standing for
            ``clockspeed.surface``.

    Returns:
        How many modules were scanned, and one ``relative-path:line`` label per
        fault.
    """
    scanned = 0
    faults: list[str] = []
    for path in _python_files(root):
        scanned += 1
        relative = path.relative_to(root)
        package = ".".join([SURFACE_PACKAGE, *relative.parent.parts])
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        label = relative.as_posix()
        faults.extend(label + ":" + str(line) for line in _module_faults(tree, package))
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


def test_no_shipped_surface_module_reaches_the_machines_model() -> None:
    """The arm that fails the day a surface module reaches MachineState at all."""
    scanned, faults = machine_seam_faults(SURFACE_ROOT)
    expected = sum(1 for _ in _python_files(SURFACE_ROOT))
    assert expected > 0, "the surface package holds no module, so this arm grades nothing"
    assert scanned == expected, "modules scanned: " + str(scanned)
    assert faults == [], REMEDY + ". Found: " + ", ".join(faults)


def test_the_machine_seam_rule_admits_what_the_surface_legitimately_does(
    surface_copy: Path,
) -> None:
    """CONTROL: harmless sibling imports and prose are not refused.

    A sibling audit import, a runtime import of an unrelated module, a
    ``.machines`` read off a solver step and a docstring naming the module are
    not faults, so the refusals below are about the reach and nothing else.
    """
    source = (
        '"""Mentions ' + MACHINES_MODULE + ' in prose only."""\n\n'
        "import importlib\n"
        "from clockspeed.audit import inventory\n\n"
        "def serve(model: object, step: object) -> object:\n"
        "    json = importlib.import_module('json')\n"
        "    return (json, inventory.inventory_of(model), step.machines)\n"
    )
    (surface_copy / "api" / "planted_machines.py").write_text(source, encoding="utf-8")
    scanned, faults = machine_seam_faults(surface_copy)
    assert scanned > 0, "the copy holds no module"
    assert faults == [], "a harmless module was flagged: " + ", ".join(faults)


_HEAD: Final = "from clockspeed.audit import machines\n\n"

#: Every way a surface module can reach the machines model, one plant each. The
#: first seven are the adversary's probe forms (repr, f-string, match pattern,
#: attrgetter, a local fake check, the package import, a concatenated
#: importlib name); the rest close the neighbouring spellings.
REACH_PLANTS: Final = {
    "repr": _HEAD + "def serve(s: object) -> object:\n    return {'m': repr(s)}\n",
    "fstring": _HEAD + "def serve(s: object) -> object:\n    return {'m': f'{s}'}\n",
    "match": _HEAD
    + (
        "def serve(s: object) -> object:\n"
        "    match s:\n"
        "        case machines.MachineState(class_name=c):\n"
        "            return {'c': c}\n"
        "    return None\n"
    ),
    "attrgetter": _HEAD
    + (
        "import operator\n\n"
        "def serve(s: object) -> object:\n"
        "    return operator.attrgetter('class_name')(s)\n"
    ),
    "fake-check": _HEAD
    + (
        "def closed_key(v: object, k: str) -> str:\n"
        "    return k\n\n"
        "def serve(s: machines.MachineState) -> object:\n"
        "    return {'c': closed_key(None, s.class_name)}\n"
    ),
    "package-import": (
        "from clockspeed import audit\n\n"
        "def serve(model: object) -> object:\n"
        "    return [m.class_name for m in audit.machines.machines_of(model)]\n"
    ),
    "importlib-concat": (
        "import importlib\n\n"
        "def serve(model: object) -> object:\n"
        "    mod = importlib.import_module('clockspeed.audit.' + 'machines')\n"
        "    return [m.class_name for m in mod.machines_of(model)]\n"
    ),
    "dunder-import": (
        "def serve(model: object) -> object:\n"
        "    return __import__('clockspeed.audit', fromlist=['mach' + 'ines'])\n"
    ),
    "bare-package": (
        "import clockspeed.audit\n\n"
        "def serve(model: object) -> object:\n"
        "    return getattr(clockspeed.audit, 'machines')\n"
    ),
    "relative": "from ...audit import machines\n",
    "star": "from clockspeed.audit import *\n",
    "sys-modules": (
        "import sys\n\n"
        "def serve() -> object:\n"
        "    return sys.modules['clockspeed.audit.' + 'machines']\n"
    ),
    "plain-import": "import clockspeed.audit.machines\n",
    "from-module": "from clockspeed.audit.machines import MachineState\n",
}


@pytest.mark.parametrize("form", sorted(REACH_PLANTS))
def test_the_machine_seam_rule_refuses_every_planted_reach(surface_copy: Path, form: str) -> None:
    """LIVE: each planted module that reaches the machines model is refused."""
    planted_path = surface_copy / "api" / "planted_machines.py"
    planted_path.write_text(REACH_PLANTS[form], encoding="utf-8")
    _, faults = machine_seam_faults(surface_copy)
    planted = [fault for fault in faults if fault.startswith("api/planted_machines.py:")]
    assert planted, "the planted " + form + " reach was not refused"
    assert len(planted) == len(faults), "a shipped module was flagged: " + ", ".join(faults)
