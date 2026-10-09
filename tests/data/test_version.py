"""Tests for clockspeed.data.version - the game build pin and its integrity field.

Every test in this module runs on a machine that has never had the game
installed. That is not a convenience: it is the property the whole design of
the pin turns on. `.github/workflows/tier1.yml` runs the drift guard on a
runner with no install, so the ONLY way a corrupted pin can be detected there
is out of the pin's own internal integrity field - a checksum the pin carries
over its own fields. Nothing here reads the real docs file, and nothing here
asserts a value measured off one particular machine's install.

Two things this module deliberately does NOT do:

- It does not hardcode the real docs sha256 or the real entry counts as
  expected values. Those pin one operator's install and would fail everywhere
  else. The tracked pin is asserted to be SELF-consistent, never to hold a
  particular number.
- It does not compute, assert or imply an overclock clock ceiling. ADR 0005
  records that the ceiling is UNKNOWN and fences the specific trap of deriving
  it from ``2 ** 1.321929``. ``test_overclock_shard_slot_count_is_unknown``
  exists so that filling the constant in is a conscious act.

All fixture material below is hand-authored synthetic content (BOOTSTRAP.md
section 8.1). No class name, description or byte sequence is lifted from the
shipped game data.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import clockspeed.data.version as version_module
from clockspeed.data.version import (
    CENSUS_KEY_BUILDING_FIELD_PRESENCE,
    DOCS_RELATIVE,
    FIELD_MAX_POTENTIAL,
    OVERCLOCK_POTENTIAL_SHARD_SLOTS,
    PIN_BEGIN_MARKER,
    PIN_END_MARKER,
    SCHEMA,
    WATCHED_BUILDING_FIELDS,
    PinFormatError,
    build_pin,
    compare,
    extract_pin_block,
    integrity_digest,
    pin,
    rewrite_pin_source,
    validate_pin,
    write_pin,
)

# ---------------------------------------------------------------------------
# Synthetic corpus
# ---------------------------------------------------------------------------

# Group short names are facts about the data FORMAT, so the real ones are used
# - the census keys on them and ADR 0005 names FGPowerShardDescriptor
# explicitly. Every ClassName below is invented.
SYNTHETIC_BUILD = "++SyntheticGame+rel-test-CL-1"

_OVERCLOCKABLE = {
    "mMaxPotential": "1.000000",
    "mPotentialShardSlots": "0",
    "mOverridePotentialShardSlots": "False",
}


def _wrapped(short_name: str) -> str:
    """Return a NativeClass value in the wrapped shape the real file uses.

    Args:
        short_name: The trailing class token, e.g. ``FGRecipe``.

    Returns:
        A full NativeClass value that reduces to ``short_name``.
    """
    return f"/Script/CoreUObject.Class'/Script/FactoryGame.{short_name}'"


def _group(short_name: str, entries: list[dict[str, str]]) -> dict[str, Any]:
    """Build one synthetic ``{NativeClass, Classes}`` group.

    Args:
        short_name: The trailing class token for the group.
        entries: The group's entries.

    Returns:
        The group mapping, shaped exactly like a group in the shipped file.
    """
    return {"NativeClass": _wrapped(short_name), "Classes": entries}


def synthetic_groups() -> list[dict[str, Any]]:
    """Return the baseline synthetic document: four groups, seven entries.

    Returns:
        A fresh list every call, so a test that mutates one cannot leak into
        another.
    """
    return [
        _group(
            "FGBuildableManufacturer",
            [
                {
                    "ClassName": "Build_SynthAssembler_C",
                    "mPowerConsumptionExponent": "1.321929",
                    **_OVERCLOCKABLE,
                },
                {
                    "ClassName": "Build_SynthConstructor_C",
                    "mPowerConsumptionExponent": "1.321929",
                    **_OVERCLOCKABLE,
                },
            ],
        ),
        _group(
            "FGBuildableStorage",
            [
                {
                    "ClassName": "Build_SynthStore_C",
                    "mPowerConsumptionExponent": "1.600000",
                    **_OVERCLOCKABLE,
                }
            ],
        ),
        _group(
            "FGPowerShardDescriptor",
            [
                {
                    "ClassName": "Desc_SynthOverclockShard_C",
                    "mPowerShardType": "PST_Overclock",
                    "mExtraPotential": "0.500000",
                    "mExtraProductionBoost": "0.000000",
                },
                {
                    "ClassName": "Desc_SynthBoostShard_C",
                    "mPowerShardType": "PST_ProductionBoost",
                    "mExtraPotential": "0.000000",
                    "mExtraProductionBoost": "1.000000",
                },
            ],
        ),
        _group(
            "FGRecipe",
            [
                {"ClassName": "Recipe_SynthPlate_C", "mManufactoringDuration": "2.000000"},
                {"ClassName": "Recipe_SynthRod_C", "mManufactoringDuration": "4.000000"},
            ],
        ),
    ]


#: A group short name no shipped build carries, so a group built under it is
#: UNRECOGNIZED and its entries are outside the registry's published set. Used
#: to prove the building census counts what the registry would publish rather
#: than every power-bearing entry in the file.
UNRECOGNIZED_GROUP = "FGSynthUnknownGroup"


def groups_with_an_unpotentialed_building() -> list[dict[str, Any]]:
    """Return the baseline corpus plus the two entries the presence census needs.

    One power-bearing entry in a RECOGNIZED group carrying none of the watched
    fields - the shape the shipped document ships six of - and one carrying the
    same power field in an unrecognized group, which the registry never
    publishes and which the census must therefore not count.

    Returns:
        A fresh group list every call.
    """
    groups = synthetic_groups()
    groups.append(
        _group(
            "FGBuildableFloodlight",
            [{"ClassName": "Build_SynthFloodlight_C", "mPowerConsumption": "10.000000"}],
        )
    )
    groups.append(
        _group(
            UNRECOGNIZED_GROUP,
            [{"ClassName": "Build_SynthUnknown_C", "mPowerConsumption": "20.000000"}],
        )
    )
    return groups


def encode_docs(groups: list[dict[str, Any]]) -> bytes:
    """Encode a synthetic group list the way the shipped locale file is encoded.

    UTF-16 with a byte-order mark, which is the measured family for 54 of the
    55 shipped locale files (BOOTSTRAP.md section 3.2). Encoding rather than
    hand-writing bytes keeps the fixture readable while still exercising the
    real decode path.

    Args:
        groups: The synthetic groups.

    Returns:
        Encoded document bytes.
    """
    return json.dumps(groups).encode("utf-16")


# Counts derived by hand from synthetic_groups() above. Named rather than
# inlined so a change to the corpus fails in one obvious place.
EXPECTED_GROUP_COUNT = 4
EXPECTED_ENTRY_COUNT = 7
EXPECTED_EXPONENT_COUNTS = {"1.321929": 2, "1.600000": 1}
EXPECTED_EXPONENT_GROUPS = 2
EXPECTED_SHARD_GROUP_SIZE = 2

# The published buildings in groups_with_an_unpotentialed_building(): the
# three overclockable ones the baseline carries, plus the floodlight. The
# entry in the unrecognized group is deliberately not among them.
EXPECTED_VARIANT_BUILDING_COUNT = 4

# The highest byte 7-bit ASCII admits. Named so the assertion below reads as
# the project rule it enforces rather than as a magic number.
MAX_ASCII_BYTE = 0x7E

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_SOURCE = REPO_ROOT / "clockspeed" / "data" / "version.py"


@pytest.fixture
def synthetic_pin() -> dict[str, Any]:
    """A freshly built, internally consistent pin over the synthetic corpus.

    Returns:
        The pin payload.
    """
    return build_pin(encode_docs(synthetic_groups()), SYNTHETIC_BUILD)


# ---------------------------------------------------------------------------
# The tracked pin
# ---------------------------------------------------------------------------


def test_the_tracked_pin_is_internally_consistent() -> None:
    payload = pin()
    assert validate_pin(payload) == []
    assert payload["schema"] == SCHEMA
    assert payload["docs_relative"] == DOCS_RELATIVE


def test_pin_returns_a_copy_so_a_caller_cannot_corrupt_module_state() -> None:
    payload = pin()
    original = payload["census"]["entry_count"]
    payload["census"]["entry_count"] = -1
    assert pin()["census"]["entry_count"] == original


# ---------------------------------------------------------------------------
# The changelist - DERIVED from the build pin, never typed (CS-1288)
# ---------------------------------------------------------------------------
#
# No changelist number is written into this file. The tracked one is read back
# out of GAME_BUILD by an independent spelling of the rule, and every parse
# case below runs on a synthetic build string.


#: The synthetic branch every hand-built parse case hangs its suffix on.
_BRANCH = "++SyntheticGame+rel-test"


def test_the_pinned_changelist_is_read_out_of_the_pinned_build() -> None:
    build = version_module.GAME_BUILD
    head, sep, digits = build.rpartition("-CL-")
    assert sep, "the tracked build carries no -CL- suffix - this test would compare nothing"
    assert head, "the tracked build is a bare suffix - not a build string"
    assert digits.isascii(), "the tracked build's suffix is not ASCII"
    assert digits.isdigit(), "the tracked build's suffix is not digits"

    changelist = version_module.GAME_CHANGELIST

    assert type(changelist) is int
    assert changelist == int(digits)
    assert build.endswith(f"-CL-{changelist}")


def test_changelist_of_reads_the_widest_changelist_it_admits() -> None:
    widest = 10**version_module.CHANGELIST_MAX_DIGITS - 1
    assert version_module.changelist_of(f"{_BRANCH}-CL-{widest}") == widest


def test_the_changelist_width_is_the_widest_that_always_fits_a_signed_64_bit_integer() -> None:
    width = version_module.CHANGELIST_MAX_DIGITS
    int64_max = 2**63 - 1
    assert 10**width - 1 <= int64_max
    assert 10 ** (width + 1) - 1 > int64_max
    # Far below the lowest value Python lets the int-string limit be set to, so
    # int() over an admitted suffix can never raise under any configured limit.
    assert width < sys.int_info.str_digits_check_threshold


def test_changelist_of_a_changelist_one_digit_too_wide_is_none() -> None:
    too_wide = "9" * (version_module.CHANGELIST_MAX_DIGITS + 1)
    assert version_module.changelist_of(f"{_BRANCH}-CL-{too_wide}") is None


def test_changelist_of_a_changelist_past_the_int_string_limit_is_none() -> None:
    # int() over this many digits raises ValueError under the default limit; a
    # corrupt pin carrying it must read as None, never raise.
    overlong = "9" * (sys.int_info.default_max_str_digits + 1)
    assert version_module.changelist_of(f"{_BRANCH}-CL-{overlong}") is None


@pytest.mark.parametrize(
    "build",
    [
        # Canonical positive decimal only: a submitted changelist is never 0, 0
        # is the stand-in a harness here already uses for "no changelist", and a
        # leading zero breaks the round trip build.endswith(f"-CL-{n}").
        pytest.param(f"{_BRANCH}-CL-0", id="zero"),
        pytest.param(f"{_BRANCH}-CL-007", id="leading-zeros"),
        # -CL- exactly: a CL- glued to anything but a hyphen is not the token.
        pytest.param(f"{_BRANCH}-CL-5CL-7", id="glued-to-a-digit"),
        pytest.param(f"{_BRANCH}_CL-7", id="underscore-separator"),
        pytest.param(f"{_BRANCH}+CL-7", id="plus-separator"),
        pytest.param(f"{_BRANCH}" + chr(0x00E9) + "CL-7", id="non-ascii-letter-separator"),
        pytest.param("CL-7", id="no-branch"),
    ],
)
def test_changelist_of_a_noncanonical_changelist_token_is_none(build: str) -> None:
    assert version_module.changelist_of(build) is None


def test_changelist_of_reads_the_trailing_changelist_of_a_synthetic_build() -> None:
    synthetic_changelist = 42
    assert version_module.changelist_of(SYNTHETIC_BUILD) == 1
    assert (
        version_module.changelist_of(f"++SyntheticGame+rel-other-CL-{synthetic_changelist}")
        == synthetic_changelist
    )


@pytest.mark.parametrize(
    "build",
    [
        "",
        "++SyntheticGame+rel-test",
        "++SyntheticGame+rel-test-CL",
        "++SyntheticGame+rel-test-CL-",
    ],
)
def test_changelist_of_a_build_with_no_changelist_suffix_is_none(build: str) -> None:
    assert version_module.changelist_of(build) is None


@pytest.mark.parametrize(
    "build",
    [
        "++SyntheticGame+rel-test-CL-12x",
        "++SyntheticGame+rel-test-CL-1.5",
        "++SyntheticGame+rel-test-CL--7",
        "++SyntheticGame+rel-test-CL-+7",
        "++SyntheticGame+rel-test-CL- 7",
        "++SyntheticGame+rel-test-CL-7 ",
        "++SyntheticGame+rel-test-CL-7\n",
        "++SyntheticGame+rel-test-CL-" + chr(0x0661) + chr(0x0662),
        "++SyntheticGame+rel-test-CL-1" + chr(0x0662),
        "++SyntheticGame+rel-test-CL-7-hotfix",
        "++SyntheticGame+rel-test-xCL-7",
    ],
)
def test_changelist_of_a_build_with_malformed_changelist_digits_is_none(build: str) -> None:
    assert version_module.changelist_of(build) is None


# ---------------------------------------------------------------------------
# Internal integrity - the half that works with no game install
# ---------------------------------------------------------------------------


def test_a_well_formed_pin_validates_with_no_install_present(
    synthetic_pin: dict[str, Any],
) -> None:
    assert validate_pin(synthetic_pin) == []


def test_a_pin_with_one_mutated_field_fails_validation(synthetic_pin: dict[str, Any]) -> None:
    synthetic_pin["census"]["entry_count"] = EXPECTED_ENTRY_COUNT + 1
    problems = validate_pin(synthetic_pin)
    assert problems
    assert any("integrity" in problem.lower() for problem in problems)


def test_a_pin_with_a_mutated_top_level_field_fails_validation(
    synthetic_pin: dict[str, Any],
) -> None:
    synthetic_pin["game_build"] = SYNTHETIC_BUILD + "-tampered"
    problems = validate_pin(synthetic_pin)
    assert problems
    assert any("integrity" in problem.lower() for problem in problems)


def test_a_pin_with_the_integrity_field_stripped_fails_validation(
    synthetic_pin: dict[str, Any],
) -> None:
    del synthetic_pin["integrity"]
    problems = validate_pin(synthetic_pin)
    assert problems
    assert any("integrity" in problem.lower() for problem in problems)


def test_a_pin_with_a_non_hex_integrity_field_fails_validation(
    synthetic_pin: dict[str, Any],
) -> None:
    synthetic_pin["integrity"] = "not a digest"
    assert validate_pin(synthetic_pin)


def test_a_pin_from_an_unknown_schema_fails_validation(synthetic_pin: dict[str, Any]) -> None:
    synthetic_pin["schema"] = SCHEMA + 1
    synthetic_pin["integrity"] = integrity_digest(synthetic_pin)
    problems = validate_pin(synthetic_pin)
    assert problems
    assert any("schema" in problem.lower() for problem in problems)


def test_a_pin_missing_a_required_field_fails_validation(synthetic_pin: dict[str, Any]) -> None:
    del synthetic_pin["docs_sha256"]
    assert validate_pin(synthetic_pin)


def test_the_integrity_digest_ignores_key_order(synthetic_pin: dict[str, Any]) -> None:
    reordered = dict(reversed(list(synthetic_pin.items())))
    assert integrity_digest(reordered) == integrity_digest(synthetic_pin)


def test_the_integrity_digest_moves_when_any_field_moves(synthetic_pin: dict[str, Any]) -> None:
    before = integrity_digest(synthetic_pin)
    synthetic_pin["docs_bytes"] = int(synthetic_pin["docs_bytes"]) + 1
    assert integrity_digest(synthetic_pin) != before


# ---------------------------------------------------------------------------
# Building a pin from a document
# ---------------------------------------------------------------------------


def test_build_pin_measures_the_bytes_it_was_given() -> None:
    raw = encode_docs(synthetic_groups())
    payload = build_pin(raw, SYNTHETIC_BUILD)
    assert payload["docs_bytes"] == len(raw)
    assert payload["docs_sha256"] == hashlib.sha256(raw).hexdigest()
    assert payload["game_build"] == SYNTHETIC_BUILD


def test_build_pin_counts_groups_and_entries(synthetic_pin: dict[str, Any]) -> None:
    census = synthetic_pin["census"]
    assert census["group_count"] == EXPECTED_GROUP_COUNT
    assert census["entry_count"] == EXPECTED_ENTRY_COUNT
    assert census["distinct_class_names"] == EXPECTED_ENTRY_COUNT


def test_build_pin_records_the_exponent_set_and_the_groups_carrying_it(
    synthetic_pin: dict[str, Any],
) -> None:
    census = synthetic_pin["census"]
    assert census["power_consumption_exponents"] == EXPECTED_EXPONENT_COUNTS
    assert census["power_consumption_exponent_groups"] == EXPECTED_EXPONENT_GROUPS


def test_build_pin_records_the_adr_0005_shard_invariants(synthetic_pin: dict[str, Any]) -> None:
    census = synthetic_pin["census"]
    assert census["power_shard_group_size"] == EXPECTED_SHARD_GROUP_SIZE
    assert census["power_shard_extra_potential"]["PST_Overclock"] == "0.500000"
    assert census["max_potential_values"] == {"1.000000": 3}
    assert census["potential_shard_slots_values"] == {"0": 3}
    assert census["override_potential_shard_slots_values"] == {"False": 3}


# ---------------------------------------------------------------------------
# CS-210 - the absent branch of each watched field, counted over the buildings
# the registry actually publishes
# ---------------------------------------------------------------------------


def test_the_census_counts_a_watched_field_as_present_on_every_baseline_building(
    synthetic_pin: dict[str, Any],
) -> None:
    # The baseline corpus carries all three overclock fields on all three of
    # its power-bearing entries, so every absent count is a real measured zero
    # rather than a key that was never written. Without this half the variant
    # below could pass on a census that only ever counted absences.
    presence = synthetic_pin["census"][CENSUS_KEY_BUILDING_FIELD_PRESENCE]
    assert sorted(presence) == sorted(WATCHED_BUILDING_FIELDS)
    for field in WATCHED_BUILDING_FIELDS:
        assert presence[field] == {"absent": 0, "present": 3}, field


def test_the_census_counts_the_registry_published_buildings_that_lack_a_watched_field() -> None:
    # The point of the key: a per-value count answers WHICH VALUES a field
    # takes among the entries that carry it, and says nothing at all about the
    # entries that carry none. Only the absent half can ground the branch that
    # reads an absent field as None.
    payload = build_pin(encode_docs(groups_with_an_unpotentialed_building()), SYNTHETIC_BUILD)
    presence = payload["census"][CENSUS_KEY_BUILDING_FIELD_PRESENCE]
    for field in WATCHED_BUILDING_FIELDS:
        assert presence[field] == {"absent": 1, "present": 3}, field


def test_the_building_census_ignores_an_entry_no_recognized_group_holds() -> None:
    # The unrecognized group in the variant corpus carries the same power field
    # as the floodlight beside it. The registry builds from the RECOGNIZED
    # groups only, so counting that entry would make the key describe a
    # population the registry never publishes.
    payload = build_pin(encode_docs(groups_with_an_unpotentialed_building()), SYNTHETIC_BUILD)
    census = payload["census"]
    counted = census[CENSUS_KEY_BUILDING_FIELD_PRESENCE][FIELD_MAX_POTENTIAL]
    assert counted["absent"] + counted["present"] == EXPECTED_VARIANT_BUILDING_COUNT
    # Positive half: the entry really is in the document the census read, so
    # the exclusion above is a measurement rather than a corpus that never
    # carried it.
    assert census["group_entry_counts"][UNRECOGNIZED_GROUP] == 1


def test_the_tracked_pin_grounds_the_absent_max_potential_branch_in_shipped_data() -> None:
    # CS-210. Before this key the claim "a registry-published building can lack
    # mMaxPotential at all" was asserted nowhere against the shipped document -
    # only against one hand-authored corpus entry. The pin is measured from the
    # install by tools/drift_guard.py --re-extract, so this assertion reads the
    # shipped document on a machine with no game on it.
    presence = pin()["census"][CENSUS_KEY_BUILDING_FIELD_PRESENCE]
    counted = presence[FIELD_MAX_POTENTIAL]
    assert counted["absent"] > 0, (
        "the shipped document records no registry-published building without "
        f"{FIELD_MAX_POTENTIAL}, so the absent-is-None branch is grounded in the "
        "synthetic corpus alone"
    )
    assert counted["present"] > 0, (
        f"the shipped document records no registry-published building carrying "
        f"{FIELD_MAX_POTENTIAL}, so the present branch is ungrounded"
    )


# ---------------------------------------------------------------------------
# Comparing a pin against live data
# ---------------------------------------------------------------------------


def test_compare_reports_nothing_for_the_same_document(synthetic_pin: dict[str, Any]) -> None:
    live = build_pin(encode_docs(synthetic_groups()), SYNTHETIC_BUILD)
    assert compare(synthetic_pin["census"], live["census"]) == []


def test_a_third_exponent_value_is_reported_as_drift(synthetic_pin: dict[str, Any]) -> None:
    patched = synthetic_groups()
    patched.append(
        _group(
            "FGBuildableGeneratorFuel",
            [
                {
                    "ClassName": "Build_SynthGenerator_C",
                    "mPowerConsumptionExponent": "1.700000",
                    **_OVERCLOCKABLE,
                }
            ],
        )
    )
    live = build_pin(encode_docs(patched), SYNTHETIC_BUILD)
    problems = compare(synthetic_pin["census"], live["census"])
    assert any("mPowerConsumptionExponent" in problem for problem in problems)
    assert any("1.700000" in problem for problem in problems)


def test_a_changed_overclock_shard_extra_potential_is_reported_as_drift(
    synthetic_pin: dict[str, Any],
) -> None:
    patched = synthetic_groups()
    for group in patched:
        for entry in group["Classes"]:
            if entry.get("mPowerShardType") == "PST_Overclock":
                entry["mExtraPotential"] = "0.750000"
    live = build_pin(encode_docs(patched), SYNTHETIC_BUILD)
    problems = compare(synthetic_pin["census"], live["census"])
    assert any("PST_Overclock" in problem for problem in problems)


def test_an_overridden_shard_slot_count_is_reported_as_drift(
    synthetic_pin: dict[str, Any],
) -> None:
    patched = synthetic_groups()
    patched[0]["Classes"][0]["mOverridePotentialShardSlots"] = "True"
    live = build_pin(encode_docs(patched), SYNTHETIC_BUILD)
    problems = compare(synthetic_pin["census"], live["census"])
    assert any("mOverridePotentialShardSlots" in problem for problem in problems)


def test_a_changed_group_size_is_reported_as_drift(synthetic_pin: dict[str, Any]) -> None:
    patched = synthetic_groups()
    patched[3]["Classes"].append({"ClassName": "Recipe_SynthBeam_C"})
    live = build_pin(encode_docs(patched), SYNTHETIC_BUILD)
    problems = compare(synthetic_pin["census"], live["census"])
    assert any("FGRecipe" in problem for problem in problems)


# ---------------------------------------------------------------------------
# ADR 0005 - the constant that has no value
# ---------------------------------------------------------------------------


def test_overclock_shard_slot_count_is_unknown() -> None:
    # ADR 0005: the slot count is NOT in the docs data and NOT in Headers.zip.
    # It is measured or it is UNKNOWN. Filling it in must be a conscious act
    # that updates this test, and it may only be done by an ADR that records
    # what was read on this machine. Deriving it from the power exponent is
    # explicitly fenced off by that ADR.
    assert OVERCLOCK_POTENTIAL_SHARD_SLOTS is None


# ---------------------------------------------------------------------------
# The generated block - extraction, rewriting, writing
# ---------------------------------------------------------------------------


def test_extract_pin_block_reads_the_payload_out_of_the_tracked_source() -> None:
    source = VERSION_SOURCE.read_text(encoding="utf-8")
    assert extract_pin_block(source) == pin()


def test_extract_pin_block_refuses_a_source_with_no_markers() -> None:
    with pytest.raises(PinFormatError, match="marker"):
        extract_pin_block("# a module with no generated block\n")


def test_extract_pin_block_refuses_a_block_that_is_not_json(
    synthetic_pin: dict[str, Any],
) -> None:
    source = rewrite_pin_source(VERSION_SOURCE.read_text(encoding="utf-8"), synthetic_pin)
    anchor = '_PIN_JSON: Final = """\n{'
    assert anchor in source, "the anchor moved - this test would mutate nothing"
    broken = source.replace(anchor, anchor + ",", 1)
    assert broken != source, "the mutation did not apply - a failed mutation looks GREEN"
    with pytest.raises(PinFormatError, match="JSON"):
        extract_pin_block(broken)


def test_a_module_with_an_unparseable_pin_still_imports(tmp_path: Path) -> None:
    # A corrupt pin must turn ONE guard red with a message naming the problem.
    # It must not make this module unimportable, which would surface as an
    # import traceback inside whatever unrelated caller happened to touch it
    # first. So the corruption is reported by validate_pin, not raised here.
    source = VERSION_SOURCE.read_text(encoding="utf-8")
    anchor = '_PIN_JSON: Final = """\n{'
    assert anchor in source, "the anchor moved - this test would mutate nothing"
    broken = source.replace(anchor, anchor + ",", 1)
    assert broken != source, "the mutation did not apply - a failed mutation looks GREEN"

    module = _import_source_copy(tmp_path, broken, "clockspeed_broken_version")

    assert module.pin() == {}
    assert validate_pin(module.pin()) != []
    # No build, so no changelist - and never a default number standing in.
    assert module.GAME_BUILD == ""
    assert module.GAME_CHANGELIST is None


def test_a_module_whose_pinned_build_has_an_overlong_changelist_still_imports(
    tmp_path: Path,
) -> None:
    # GAME_CHANGELIST is computed at import, so a changelist int() refuses to
    # convert would make a corrupt pin take the whole module down. It must read
    # as None and leave the corruption for validate_pin to report.
    source = VERSION_SOURCE.read_text(encoding="utf-8")
    anchor = f'"game_build": {json.dumps(version_module.GAME_BUILD)}'
    assert anchor in source, "the anchor moved - this test would mutate nothing"
    overlong = "9" * (sys.int_info.default_max_str_digits + 1)
    broken = source.replace(anchor, anchor[:-1] + overlong + '"', 1)
    assert broken != source, "the mutation did not apply - a failed mutation looks GREEN"

    module = _import_source_copy(tmp_path, broken, "clockspeed_overlong_changelist_version")

    assert module.GAME_BUILD.endswith(overlong)
    assert module.GAME_CHANGELIST is None
    assert validate_pin(module.pin()) != []


def _import_source_copy(tmp_path: Path, source: str, name: str) -> Any:
    """Import a mutated copy of version.py as a module of its own.

    Args:
        tmp_path: Where the copy is written.
        source: The mutated module source.
        name: The module name, also the copy's file stem.

    Returns:
        The executed module.
    """
    target = tmp_path / f"{name}.py"
    target.write_text(source, encoding="utf-8", newline="\n")
    spec = importlib.util.spec_from_file_location(name, target)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rewrite_pin_source_replaces_only_the_generated_block(
    synthetic_pin: dict[str, Any],
) -> None:
    source = VERSION_SOURCE.read_text(encoding="utf-8")
    updated = rewrite_pin_source(source, synthetic_pin)
    assert updated != source, "the rewrite did not apply - a mutation that fails looks GREEN"
    assert extract_pin_block(updated) == synthetic_pin

    head = source.split(PIN_BEGIN_MARKER, 1)[0]
    tail = source.split(PIN_END_MARKER)[-1]
    assert updated.split(PIN_BEGIN_MARKER, 1)[0] == head
    assert updated.split(PIN_END_MARKER)[-1] == tail


def test_rewrite_pin_source_refuses_a_source_with_no_markers(
    synthetic_pin: dict[str, Any],
) -> None:
    with pytest.raises(PinFormatError, match="marker"):
        rewrite_pin_source("print('hello')\n", synthetic_pin)


def test_write_pin_writes_lf_bytes_and_leaves_a_validating_module(
    tmp_path: Path, synthetic_pin: dict[str, Any]
) -> None:
    target = tmp_path / "version.py"
    target.write_bytes(VERSION_SOURCE.read_bytes())

    write_pin(target, synthetic_pin)

    data = target.read_bytes()
    assert b"\r\n" not in data, "write_pin must not emit CRLF - content hashes are load bearing"
    assert max(data) <= MAX_ASCII_BYTE, "the pin file must stay 7-bit ASCII"
    written = extract_pin_block(target.read_text(encoding="utf-8"))
    assert written == synthetic_pin
    assert validate_pin(written) == []


def test_write_pin_leaves_no_temporary_file_behind(
    tmp_path: Path, synthetic_pin: dict[str, Any]
) -> None:
    target = tmp_path / "version.py"
    target.write_bytes(VERSION_SOURCE.read_bytes())
    write_pin(target, synthetic_pin)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["version.py"]
