"""The game build pin, the docs content hash, and the pin's own integrity field.

`CLAUDE.md` section 4 names this file the owner of the game build pin and the
content hash. Nothing else in the project restates a build string or a docs
hash; a restated fact is a fact that will drift.

WHY THE PIN CARRIES A CHECKSUM OVER ITS OWN FIELDS
--------------------------------------------------
This is the single design decision the whole module turns on, and it comes
from a CI constraint rather than from taste. `.github/workflows/tier1.yml`
runs `tools/drift_guard.py` on a runner that has NO game install. A guard that
could only detect a bad pin by comparing it against live game data would be
blind on exactly the machine that gates every push, so a hand-corrupted pin
would sail through the lane that must never be red.

So the pin carries an ``integrity`` field: a sha256 over the canonical form of
every other field it holds. Editing any value without regenerating the pin
makes the recorded digest disagree with the recomputed one, and that
disagreement is detectable with no install, no network and no game data. Two
independent failure classes therefore have two independent detectors:

  internally inconsistent   the pin was hand-edited      caught anywhere
  live mismatch             the game was patched         caught where the
                                                         install exists

WHY THE PIN IS A GENERATED JSON BLOCK RATHER THAN LOOSE CONSTANTS
-----------------------------------------------------------------
The pin has to be regenerable by a tool - "green after re-extract" is the
CS-200 acceptance criterion - and rewriting a region delimited by two marker
comments is the smallest mechanism that does that without a code generator
templating a whole module. It also keeps the canonical form for the checksum
trivially well defined: it is the JSON, sorted and compact. Everything outside
the two markers is hand-written and is never touched by the rewriter.

WHAT THIS MODULE DOES NOT DO
----------------------------
- It never locates the install. ``clockspeed/data/locate.py`` owns that, and
  this module takes bytes and a build string from its caller. That is what
  keeps the whole file testable with no game present.
- It never opens the docs file. ``clockspeed/data/docs_extract.py`` owns the
  read; this module consumes the parsed groups.
- It never writes to the game install, and ``write_pin`` writes only to a path
  the caller names inside this repository (non-negotiable 1).
- It states no overclock clock ceiling. See OVERCLOCK_POTENTIAL_SHARD_SLOTS.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from clockspeed.data.docs_extract import (
    KEY_CLASS_NAME,
    DocsDocument,
    DocsGroup,
    decode_docs_bytes,
    load_document,
)

__all__ = [
    "DOCS_RELATIVE",
    "DOCS_RELATIVE_PARTS",
    "GAME_CHANGELIST",
    "OVERCLOCK_POTENTIAL_SHARD_SLOTS",
    "PIN_BEGIN_MARKER",
    "PIN_END_MARKER",
    "SCHEMA",
    "PinError",
    "PinFormatError",
    "build_pin",
    "census",
    "changelist_of",
    "compare",
    "extract_pin_block",
    "integrity_digest",
    "is_registry_building_entry",
    "pin",
    "render_pin_block",
    "rewrite_pin_source",
    "validate_pin",
    "write_pin",
]

# --- pin shape --------------------------------------------------------------

#: Pin format version. Bumped when the SHAPE of the payload changes, never when
#: a measured value changes - a new game build re-measures, it does not
#: re-shape. A pin from an unknown schema is a validation failure rather than a
#: best-effort read, because a shape this build does not understand cannot be
#: compared field by field against live data.
SCHEMA: Final = 2

#: The docs file, relative to the install root. Named here because the pin is
#: about that specific file and records its own subject. `scripts/verify_env.py`
#: lists the same artifact among the five it probes; that script is an
#: environment reporter above this layer and cannot be imported from inside the
#: package (docs/ARCHITECTURE.md import direction), so the two state the path
#: independently rather than one reaching across the seam for it.
DOCS_RELATIVE_PARTS: Final = ("CommunityResources", "Docs", "en-US.json")
DOCS_RELATIVE: Final = "/".join(DOCS_RELATIVE_PARTS)

#: The key holding the checksum over every other key.
INTEGRITY_KEY: Final = "integrity"

#: Top-level keys every pin must carry, with the type each must have.
_REQUIRED_FIELDS: Final = (
    ("schema", int),
    ("game_build", str),
    ("docs_relative", str),
    ("docs_bytes", int),
    ("docs_sha256", str),
    ("census", dict),
)

#: Census keys every pin must carry. Named so a pin that lost one is a
#: validation failure rather than a comparison that silently checks less.
_REQUIRED_CENSUS_KEYS: Final = (
    "group_count",
    "entry_count",
    "distinct_class_names",
    "group_entry_counts",
    "power_consumption_exponents",
    "power_consumption_exponent_groups",
    "max_potential_values",
    "potential_shard_slots_values",
    "override_potential_shard_slots_values",
    "power_shard_extra_potential",
    "power_shard_group_size",
    "registry_building_field_presence",
)

_SHA256_HEX_LENGTH: Final = 64
_HEX_DIGITS: Final = frozenset("0123456789abcdef")

# --- the docs fields the census counts --------------------------------------

#: The balance field the S7 spike measured across the shipped data. Its VALUE
#: SET is what a balance patch moves, which is why the census records the set
#: and its per-value counts rather than any single number.
FIELD_POWER_EXPONENT: Final = "mPowerConsumptionExponent"

#: The three fields ADR 0005 requires the guard to watch alongside it. Their
#: roles are recorded there; what matters here is that any of them moving
#: silently invalidates OVERCLOCK_POTENTIAL_SHARD_SLOTS.
FIELD_MAX_POTENTIAL: Final = "mMaxPotential"
FIELD_POTENTIAL_SHARD_SLOTS: Final = "mPotentialShardSlots"
FIELD_OVERRIDE_SHARD_SLOTS: Final = "mOverridePotentialShardSlots"

#: The shard descriptor group and the two fields that identify a shard type and
#: the potential it unlocks (ADR 0005).
POWER_SHARD_GROUP: Final = "FGPowerShardDescriptor"
FIELD_POWER_SHARD_TYPE: Final = "mPowerShardType"
FIELD_EXTRA_POTENTIAL: Final = "mExtraPotential"

#: Which census key each counted field lands in. Data rather than a branch, so
#: adding a watched field is one line here and one line in _REQUIRED_CENSUS_KEYS.
_CENSUS_KEY_BY_FIELD: Final = {
    FIELD_POWER_EXPONENT: "power_consumption_exponents",
    FIELD_MAX_POTENTIAL: "max_potential_values",
    FIELD_POTENTIAL_SHARD_SLOTS: "potential_shard_slots_values",
    FIELD_OVERRIDE_SHARD_SLOTS: "override_potential_shard_slots_values",
}

#: The watched fields, in the order the presence census reports them. Derived
#: from the table above rather than listed again, so a field added there is
#: counted both ways at once.
WATCHED_BUILDING_FIELDS: Final = tuple(_CENSUS_KEY_BY_FIELD)

# --- the published-building population --------------------------------------

#: The other half of the registry's published-building predicate.
#: ``mPowerConsumption`` is named here and in ``clockspeed/data/registry.py``
#: independently, because the two modules are peers over
#: ``clockspeed/data/docs_extract.py`` and neither may import the other - the
#: allowed-import matrix in ``tests/data/test_phase2_gate.py`` is that contract.
#: The restatement is therefore deliberate, and it is fenced by a test that
#: compares the two predicates entry by entry rather than by a shared import.
FIELD_POWER_CONSUMPTION: Final = "mPowerConsumption"

#: Carrying either of these is what makes a docs entry a published Building.
REGISTRY_BUILDING_MARKER_FIELDS: Final = (FIELD_POWER_CONSUMPTION, FIELD_POWER_EXPONENT)

#: The census key recording, per watched field, how many published buildings
#: carry it and how many do not.
CENSUS_KEY_BUILDING_FIELD_PRESENCE: Final = "registry_building_field_presence"


def is_registry_building_entry(entry: Mapping[str, object]) -> bool:
    """Decide whether one docs entry is a building the registry publishes.

    States the registry's own predicate a second time on purpose - see
    :data:`FIELD_POWER_CONSUMPTION` for why an import is not available - so the
    census can describe the population the registry publishes rather than every
    entry in the file.

    Args:
        entry: One docs entry, verbatim.

    Returns:
        True when the entry carries either power field. Presence of the KEY is
        the whole test, matching the registry: an entry whose power value is
        unreadable is still published, and the registry's own warning channel
        is what reports the value.
    """
    return any(marker in entry for marker in REGISTRY_BUILDING_MARKER_FIELDS)


# --- the constant ADR 0005 specifies and deliberately leaves empty -----------

#: The per-building overclock shard slot count. **UNKNOWN. Not measured.**
#:
#: This is `mDefaultPotentialShardSlots` on the buildable subsystem. ADR 0005
#: establishes that it is NOT in the docs data - the subsystem is not exported
#: to that file at all - and NOT in the shipped headers, which declare the field
#: `EditDefaultsOnly` with no initializer. So there is no source on this machine
#: to read it from, and this constant is the one written-down number the ADR
#: permits. It ships with no value.
#:
#: It is None, not a number, on purpose. Per non-negotiable 7 unknown content is
#: flagged and skipped, never silently wrong: a solver reading None must say the
#: ceiling is unmeasured rather than assume one. A ceiling silently defaulted to
#: 1.0 and a ceiling silently defaulted to any other value are the same bug.
#:
#: It must be RE-CHECKED EVERY GAME PATCH alongside the build pin, and it may
#: only be filled in by an ADR recording what was read on this machine. ADR 0005
#: fences the one route that feels derived and is not: do not take an assumed
#: ceiling back through `ceiling = mMaxPotential + slots * mExtraPotential` to
#: recover a slot count, and do not derive anything from
#: `mPowerConsumptionExponent` - the exponent sitting within rounding of a
#: log2 relation is a relation between two balance values, not a measurement.
OVERCLOCK_POTENTIAL_SHARD_SLOTS: Final[int | None] = None

# --- generated block --------------------------------------------------------

#: The marker lines delimiting the generated pin. Located by whole-line equality
#: rather than by substring search, precisely so these two definitions - which
#: contain the marker text verbatim - are not mistaken for the markers
#: themselves.
PIN_BEGIN_MARKER: Final = "# --- BEGIN GENERATED PIN ---"
PIN_END_MARKER: Final = "# --- END GENERATED PIN ---"

_REGENERATE_COMMAND: Final = "python tools/drift_guard.py --re-extract"

# --- BEGIN GENERATED PIN ---
# Generated from the live install. Do not hand-edit: every field below is
# covered by the "integrity" checksum, and editing one without regenerating
# turns tools/drift_guard.py guard (h) red.
# Regenerate with: python tools/drift_guard.py --re-extract
_PIN_JSON: Final = """
{
  "census": {
    "distinct_class_names": 2868,
    "entry_count": 2868,
    "group_count": 114,
    "group_entry_counts": {
      "FGAmmoTypeInstantHit": 2,
      "FGAmmoTypeProjectile": 13,
      "FGAmmoTypeSpreadshot": 1,
      "FGBuildable": 16,
      "FGBuildableAttachmentMerger": 1,
      "FGBuildableAttachmentSplitter": 1,
      "FGBuildableBarrierCorner": 1,
      "FGBuildableBeam": 8,
      "FGBuildableBlueprintDesigner": 3,
      "FGBuildableCircuitSwitch": 1,
      "FGBuildableConveyorBelt": 6,
      "FGBuildableConveyorLift": 6,
      "FGBuildableConveyorMonitor": 1,
      "FGBuildableCornerWall": 12,
      "FGBuildableCornerWallLightweight": 24,
      "FGBuildableDockingStation": 2,
      "FGBuildableDoor": 10,
      "FGBuildableDroneStation": 1,
      "FGBuildableElevator": 1,
      "FGBuildableElevatorFloorStop": 1,
      "FGBuildableFactory": 3,
      "FGBuildableFactoryBuilding": 3,
      "FGBuildableFactorySimpleProducer": 1,
      "FGBuildableFloodlight": 2,
      "FGBuildableFoundationLightweight": 153,
      "FGBuildableFrackingActivator": 1,
      "FGBuildableFrackingExtractor": 1,
      "FGBuildableGeneratorFuel": 3,
      "FGBuildableGeneratorGeoThermal": 1,
      "FGBuildableGeneratorNuclear": 1,
      "FGBuildableJumppad": 1,
      "FGBuildableLadder": 1,
      "FGBuildableLightSource": 2,
      "FGBuildableLightsControlPanel": 1,
      "FGBuildableMAM": 1,
      "FGBuildableManufacturer": 8,
      "FGBuildableManufacturerVariablePower": 3,
      "FGBuildableMergerPriority": 1,
      "FGBuildablePassthrough": 2,
      "FGBuildablePassthroughPipeHyper": 1,
      "FGBuildablePillarLightweight": 9,
      "FGBuildablePipeHyper": 1,
      "FGBuildablePipeHyperJunction": 2,
      "FGBuildablePipeReservoir": 2,
      "FGBuildablePipeline": 4,
      "FGBuildablePipelineJunction": 2,
      "FGBuildablePipelinePump": 3,
      "FGBuildablePoleBase": 1,
      "FGBuildablePoleConveyor": 1,
      "FGBuildablePolePipe": 2,
      "FGBuildablePoleStackable": 3,
      "FGBuildablePortal": 1,
      "FGBuildablePortalSatellite": 1,
      "FGBuildablePowerBooster": 1,
      "FGBuildablePowerPole": 11,
      "FGBuildablePowerStorage": 1,
      "FGBuildablePriorityPowerSwitch": 1,
      "FGBuildableRadarTower": 1,
      "FGBuildableRailroadAttachment": 1,
      "FGBuildableRailroadSignal": 2,
      "FGBuildableRailroadStation": 1,
      "FGBuildableRailroadTrack": 1,
      "FGBuildableRampLightweight": 78,
      "FGBuildableResourceExtractor": 4,
      "FGBuildableResourceSink": 1,
      "FGBuildableResourceSinkShop": 1,
      "FGBuildableSnowCannon": 1,
      "FGBuildableSnowDispenser": 1,
      "FGBuildableSpaceElevator": 1,
      "FGBuildableSplitterSmart": 2,
      "FGBuildableStackableShelf": 1,
      "FGBuildableStair": 2,
      "FGBuildableStorage": 5,
      "FGBuildableTradingPost": 1,
      "FGBuildableTrainPlatformCargo": 2,
      "FGBuildableTrainPlatformEmpty": 2,
      "FGBuildableWalkway": 1,
      "FGBuildableWalkwayLightweight": 10,
      "FGBuildableWall": 3,
      "FGBuildableWallLightweight": 73,
      "FGBuildableWaterPump": 1,
      "FGBuildableWidgetSign": 10,
      "FGBuildableWire": 2,
      "FGBuildingDescriptor": 547,
      "FGCentralStorageContainer": 1,
      "FGChainsaw": 1,
      "FGChargedWeapon": 1,
      "FGConsumableDescriptor": 5,
      "FGConsumableEquipment": 2,
      "FGCustomizationRecipe": 106,
      "FGEquipmentDescriptor": 17,
      "FGEquipmentStunSpear": 3,
      "FGEquipmentZipline": 1,
      "FGGasMask": 1,
      "FGGolfCartDispenser": 2,
      "FGHoverPack": 1,
      "FGItemDescriptor": 122,
      "FGItemDescriptorBiomass": 16,
      "FGItemDescriptorNuclearFuel": 3,
      "FGItemDescriptorPowerBoosterFuel": 1,
      "FGJetPack": 1,
      "FGJumpingStilts": 1,
      "FGObjectScanner": 1,
      "FGParachute": 1,
      "FGPipeHyperStart": 1,
      "FGPortableMinerDispenser": 1,
      "FGPowerShardDescriptor": 2,
      "FGRecipe": 872,
      "FGResourceDescriptor": 13,
      "FGSchematic": 574,
      "FGSuitBase": 1,
      "FGVehicleDescriptor": 8,
      "FGVehiclePathSegment": 5,
      "FGWeapon": 2
    },
    "max_potential_values": {
      "1.000000": 62
    },
    "override_potential_shard_slots_values": {
      "False": 62
    },
    "potential_shard_slots_values": {
      "0": 62
    },
    "power_consumption_exponent_groups": 34,
    "power_consumption_exponents": {
      "1.321929": 20,
      "1.600000": 42
    },
    "power_shard_extra_potential": {
      "PST_Overclock": "0.500000",
      "PST_ProductionBoost": "0.000000"
    },
    "power_shard_group_size": 2,
    "registry_building_field_presence": {
      "mMaxPotential": {
        "absent": 6,
        "present": 62
      },
      "mOverridePotentialShardSlots": {
        "absent": 6,
        "present": 62
      },
      "mPotentialShardSlots": {
        "absent": 6,
        "present": 62
      },
      "mPowerConsumptionExponent": {
        "absent": 6,
        "present": 62
      }
    }
  },
  "docs_bytes": 10640180,
  "docs_relative": "CommunityResources/Docs/en-US.json",
  "docs_sha256": "a81d250e96aa13db3c0bf8c332c199ad930b2f15323e2c1a069afa4c07f971bb",
  "game_build": "++FactoryGame+rel-main-anniversary-2026-CL-502094",
  "integrity": "fafa13c09e18e9e8f5868292a09c0dad89e93c39ffd50810fa8015257da227d8",
  "schema": 2
}
"""
# --- END GENERATED PIN ---


class PinError(ValueError):
    """Base class for every failure this module raises.

    A :class:`ValueError` subclass, matching ``clockspeed/data/blobs.py``, so a
    caller already guarding a conversion catches it broadly while a caller that
    wants to report pin trouble specifically can catch it precisely.
    """


class PinFormatError(PinError):
    """The generated block is missing, malformed, or is not JSON."""


def _parse_pin_text(text: str) -> dict[str, Any]:
    """Parse the generated block's JSON, returning an empty pin on failure.

    Deliberately fail-soft, and this is the one place in the module that is.
    A corrupt pin must turn ONE guard red with a message naming the problem; it
    must not make this module unimportable and surface as an import traceback
    inside an unrelated caller. :func:`validate_pin` reports the empty pin as
    missing every required field, and :func:`extract_pin_block` - the path the
    drift guard takes - raises loudly instead.

    Args:
        text: The JSON text from the generated block.

    Returns:
        The parsed payload, or an empty mapping if it is not a JSON object.
    """
    try:
        payload = json.loads(text)
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


_PIN: Final[dict[str, Any]] = _parse_pin_text(_PIN_JSON)

#: The pinned build string, read from the generated block. Empty only if the
#: block is corrupt, which the drift guard reports.
GAME_BUILD: Final[str] = str(_PIN.get("game_build", ""))

#: The pinned docs content hash and size.
DOCS_SHA256: Final[str] = str(_PIN.get("docs_sha256", ""))
DOCS_BYTES: Final[int] = int(_PIN.get("docs_bytes", 0) or 0)

#: A build string's trailing changelist: ``CL-`` then ASCII digits, ending the
#: string. ``[0-9]`` rather than ``\d``, which would admit non-ASCII digits, and
#: ``\Z`` rather than ``$``, which would admit a trailing newline. The
#: look-behind keeps ``CL-`` a token of its own, not the tail of a longer word.
_CHANGELIST_SUFFIX: Final = re.compile(r"(?<![A-Za-z0-9])CL-([0-9]+)\Z")


def changelist_of(build: str) -> int | None:
    """Read the changelist a build string names in its trailing ``CL-<digits>``.

    The changelist is DERIVED from the build string, never stored beside it: a
    number written down twice is a number that drifts (`CLAUDE.md` section 4).

    Args:
        build: A build string such as ``GAME_BUILD``.

    Returns:
        The changelist, or None when the build carries no well-formed trailing
        changelist - including an empty build. Never a default
        number: a stand-in would be indistinguishable from a measured value.
    """
    match = _CHANGELIST_SUFFIX.search(build)
    return int(match.group(1)) if match else None


#: The pinned build's changelist, read out of GAME_BUILD. None when the pin is
#: corrupt or its build string carries no changelist.
GAME_CHANGELIST: Final[int | None] = changelist_of(GAME_BUILD)


def pin() -> dict[str, Any]:
    """Return the tracked pin payload.

    Returns:
        A deep copy, so a caller that edits the result cannot corrupt module
        state for every later caller in the same process.
    """
    return copy.deepcopy(_PIN)


# --- canonical form and integrity -------------------------------------------


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    """Render a payload to the one byte sequence its checksum is taken over.

    Sorted keys, no insignificant whitespace, ASCII-escaped. Sorted keys are
    what makes the digest independent of insertion order, and ASCII escaping is
    what keeps the result byte-identical on a machine with a different default
    encoding.

    Args:
        payload: Any JSON-serializable mapping.

    Returns:
        The canonical encoding.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


def integrity_digest(payload: Mapping[str, Any]) -> str:
    """Compute the checksum a pin records in its ``integrity`` field.

    Taken over every field EXCEPT ``integrity`` itself, which is the only way
    the recorded value can be compared against a recomputed one.

    Args:
        payload: A pin payload, with or without its integrity field.

    Returns:
        The lowercase hex sha256 digest.
    """
    without = {key: value for key, value in payload.items() if key != INTEGRITY_KEY}
    return hashlib.sha256(canonical_bytes(without)).hexdigest()


def _looks_like_digest(value: object) -> bool:
    """Report whether a value has the shape of a lowercase hex sha256 digest.

    Args:
        value: The candidate.

    Returns:
        True if it is a 64-character lowercase hex string.
    """
    return isinstance(value, str) and len(value) == _SHA256_HEX_LENGTH and set(value) <= _HEX_DIGITS


def _field_problems(payload: Mapping[str, Any]) -> list[str]:
    """Check the required top-level fields and the required census keys.

    Args:
        payload: The pin payload.

    Returns:
        One message per missing or wrongly typed field.
    """
    problems: list[str] = []
    for name, expected in _REQUIRED_FIELDS:
        if name not in payload:
            problems.append(f"missing required field {name!r}")
        elif not isinstance(payload[name], expected):
            problems.append(
                f"field {name!r} is a {type(payload[name]).__name__}, expected {expected.__name__}"
            )
    body = payload.get("census")
    if isinstance(body, dict):
        problems.extend(
            f"missing required census key {key!r}"
            for key in _REQUIRED_CENSUS_KEYS
            if key not in body
        )
    return problems


def validate_pin(payload: Mapping[str, Any]) -> list[str]:
    """Check a pin against itself, with no game install and no network.

    This is the half of the guard that works everywhere. It answers exactly one
    question - "was this pin edited by hand" - and it answers it out of the
    pin's own integrity field.

    Args:
        payload: The pin payload.

    Returns:
        One message per problem, empty when the pin is internally consistent.
        The list is ordered: structural problems first, then schema, then the
        checksum, because a checksum mismatch on a pin that is already missing
        fields is the less useful of the two messages.
    """
    problems = _field_problems(payload)

    schema = payload.get("schema")
    if isinstance(schema, int) and schema != SCHEMA:
        problems.append(f"pin schema is {schema}, this build understands schema {SCHEMA}")

    recorded = payload.get(INTEGRITY_KEY)
    if recorded is None:
        problems.append(
            f"the {INTEGRITY_KEY!r} field is ABSENT - a pin with no integrity field "
            "cannot be checked on a machine with no game install"
        )
    elif not _looks_like_digest(recorded):
        problems.append(f"the {INTEGRITY_KEY!r} field is not a lowercase hex sha256 digest")
    else:
        recomputed = integrity_digest(payload)
        if recomputed != recorded:
            problems.append(
                f"{INTEGRITY_KEY} MISMATCH - recorded {recorded[:12]}..., recomputed "
                f"{recomputed[:12]}...; a field was edited without regenerating the pin"
            )
    return problems


# --- census -----------------------------------------------------------------


def _tally(counters: dict[str, Counter[str]], entry: Mapping[str, object]) -> None:
    """Count one entry's watched field values into the running counters.

    The value type is ``object``, not ``str``, and the ``isinstance`` guard
    below is load-bearing rather than defensive. Every SCALAR in the document is
    a string, but a handful of fields are JSON lists on the pinned build - the
    schematic unlock and dependency arrays, and the generator fuel arrays. An
    annotation promising ``str`` would be a promise the artifact breaks, and it
    previously forced the caller to narrow a type it could not honestly narrow.

    Args:
        counters: Counter per census key, mutated in place.
        entry: One docs entry, verbatim. Values may be non-string; those are
            counted by no census key rather than coerced.
    """
    for field, key in _CENSUS_KEY_BY_FIELD.items():
        value = entry.get(field)
        if isinstance(value, str):
            counters[key][value] += 1


def _building_field_presence(groups: Sequence[DocsGroup]) -> dict[str, dict[str, int]]:
    """Count how many published buildings carry each watched field, and how many do not.

    This is the half a per-value counter cannot report. ``max_potential_values``
    and its three siblings count the VALUES of the entries that carry a field,
    so an entry carrying none of them is invisible to every one of them - and
    the absent case is a live branch in ``clockspeed/data/registry.py``, where a
    missing field becomes None rather than an invented number.

    Args:
        groups: The RECOGNIZED groups only. The registry builds its buildings
            from those, so counting an unrecognized group's entries here would
            describe a population nothing publishes. This is the one place the
            census deliberately reads less than the whole document.

    Returns:
        field name -> {"absent": int, "present": int}, key-sorted at both
        levels so the result is byte-stable under the pin's canonical form.
    """
    presence = {field: {"absent": 0, "present": 0} for field in WATCHED_BUILDING_FIELDS}
    for group in groups:
        for entry in group.entries:
            if not is_registry_building_entry(entry):
                continue
            for field, counts in presence.items():
                counts["present" if field in entry else "absent"] += 1
    return {field: dict(sorted(counts.items())) for field, counts in sorted(presence.items())}


def census(document: DocsDocument) -> dict[str, Any]:
    """Measure the structural and balance invariants a patch would move.

    Everything here is DERIVED from the groups it is given. Nothing is
    hardcoded, and no value is read from a second source, so a census taken on
    a patched install differs from a pinned one exactly where the game changed.

    Args:
        document: The loaded document. Every key but the building presence
            one counts ``all_groups`` - every well-formed group, recognized
            or not - because counting only the recognized ones would
            silently under-count on a build carrying a group the pin has
            never seen, which is precisely the case a census exists to
            detect. The document is taken whole rather than as one group
            sequence so that the one key measured over a NARROWER
            population cannot be handed the wrong list.

    Returns:
        The census payload. Every mapping is key-sorted so the result is
        byte-stable under :func:`canonical_bytes`.
    """
    counters: dict[str, Counter[str]] = {key: Counter() for key in _CENSUS_KEY_BY_FIELD.values()}
    group_entries: Counter[str] = Counter()
    class_names: set[str] = set()
    exponent_groups: set[str] = set()
    shard_extra: dict[str, str] = {}
    shard_group_size = 0
    entry_total = 0

    for group in document.all_groups:
        group_entries[group.short_name] += len(group.entries)
        is_shard_group = group.short_name == POWER_SHARD_GROUP
        if is_shard_group:
            shard_group_size += len(group.entries)
        for entry in group.entries:
            entry_total += 1
            name = entry.get(KEY_CLASS_NAME)
            if isinstance(name, str):
                class_names.add(name)
            if isinstance(entry.get(FIELD_POWER_EXPONENT), str):
                exponent_groups.add(group.short_name)
            _tally(counters, entry)
            if is_shard_group:
                shard_type = entry.get(FIELD_POWER_SHARD_TYPE)
                extra = entry.get(FIELD_EXTRA_POTENTIAL)
                if isinstance(shard_type, str) and isinstance(extra, str):
                    shard_extra[shard_type] = extra

    body: dict[str, Any] = {
        "group_count": len(document.all_groups),
        "entry_count": entry_total,
        CENSUS_KEY_BUILDING_FIELD_PRESENCE: _building_field_presence(document.groups),
        "distinct_class_names": len(class_names),
        "group_entry_counts": dict(sorted(group_entries.items())),
        "power_consumption_exponent_groups": len(exponent_groups),
        "power_shard_extra_potential": dict(sorted(shard_extra.items())),
        "power_shard_group_size": shard_group_size,
    }
    for key, counter in counters.items():
        body[key] = dict(sorted(counter.items()))
    return dict(sorted(body.items()))


def build_pin(raw: bytes, game_build: str, *, docs_relative: str = DOCS_RELATIVE) -> dict[str, Any]:
    """Build a complete, internally consistent pin from docs bytes.

    Pure: given the same bytes and the same build string it returns the same
    payload, on any machine, with or without a game installed. That is what
    lets the whole pin be tested from synthetic material.

    Args:
        raw: The complete docs file bytes.
        game_build: The build string read off the installed binaries by the
            caller. This module never reads it itself - that is a property of
            the install, and locating the install is another layer's job.
        docs_relative: The docs path the pin records as its subject.

    Returns:
        The pin payload, integrity field included.

    Raises:
        DocsDecodeError: The bytes did not decode under their sniffed encoding.
        DocsStructureError: The decoded text is not a JSON list of groups.
    """
    document = load_document(decode_docs_bytes(raw))
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "game_build": game_build,
        "docs_relative": docs_relative,
        "docs_bytes": len(raw),
        "docs_sha256": hashlib.sha256(raw).hexdigest(),
        "census": census(document),
    }
    payload[INTEGRITY_KEY] = integrity_digest(payload)
    return payload


# --- comparison against live data -------------------------------------------

#: Cap on how many sub-key differences one census key reports. A balance patch
#: that moves a hundred groups should name the first few and say how many more,
#: rather than burying the verdict under its own detail.
_MAX_REPORTED_DIFFERENCES: Final = 12


def _compare_maps(key: str, pinned: Mapping[str, Any], live: Mapping[str, Any]) -> list[str]:
    """Report the sub-key differences between two census mappings.

    Args:
        key: The census key being compared, used in every message.
        pinned: The pinned mapping.
        live: The live mapping.

    Returns:
        One message per differing sub-key, capped, with a count of any
        remainder so a truncated report never reads as a complete one.
    """
    field = next(
        (name for name, census_key in _CENSUS_KEY_BY_FIELD.items() if census_key == key), key
    )
    problems: list[str] = []
    for sub_key in sorted(set(pinned) | set(live)):
        if pinned.get(sub_key) == live.get(sub_key):
            continue
        if sub_key not in pinned:
            problems.append(f"{field}: {sub_key!r} is NEW in the live data ({live[sub_key]!r})")
        elif sub_key not in live:
            problems.append(f"{field}: {sub_key!r} is GONE from the live data")
        else:
            problems.append(
                f"{field}: {sub_key!r} pinned {pinned[sub_key]!r}, live {live[sub_key]!r}"
            )
    if len(problems) > _MAX_REPORTED_DIFFERENCES:
        remainder = len(problems) - _MAX_REPORTED_DIFFERENCES
        problems = problems[:_MAX_REPORTED_DIFFERENCES]
        problems.append(f"{field}: and {remainder} further difference(s) not listed")
    return problems


def compare(pinned: Mapping[str, Any], live: Mapping[str, Any]) -> list[str]:
    """Compare a pinned census against one taken from live data.

    Args:
        pinned: The census recorded in the pin.
        live: The census measured from the installed docs file.

    Returns:
        One message per difference, empty when they agree.
    """
    problems: list[str] = []
    for key in sorted(set(pinned) | set(live)):
        old = pinned.get(key)
        new = live.get(key)
        if old == new:
            continue
        if isinstance(old, dict) and isinstance(new, dict):
            problems.extend(_compare_maps(key, old, new))
        else:
            problems.append(f"{key}: pinned {old!r}, live {new!r}")
    return problems


# --- the generated block ----------------------------------------------------


def _marker_line(lines: Sequence[str], marker: str) -> int:
    """Return the index of the one line that IS the marker.

    Whole-line equality, never a substring search: the marker text also appears
    in this module as a string literal defining the constant, and a substring
    search would find that definition first and rewrite the wrong region.

    Args:
        lines: The source lines, without terminators.
        marker: PIN_BEGIN_MARKER or PIN_END_MARKER.

    Returns:
        The zero-based line index.

    Raises:
        PinFormatError: The marker is absent, or appears more than once.
    """
    hits = [index for index, line in enumerate(lines) if line.strip() == marker]
    if len(hits) != 1:
        raise PinFormatError(
            f"expected exactly one {marker!r} marker line, found {len(hits)}; "
            f"regenerate with: {_REGENERATE_COMMAND}"
        )
    return hits[0]


def _block_bounds(source: str) -> tuple[list[str], int, int]:
    """Locate the generated block inside a module source text.

    Args:
        source: The whole module source.

    Returns:
        (lines, begin index, end index) with both indexes naming the marker
        lines themselves.

    Raises:
        PinFormatError: A marker is missing, duplicated, or out of order.
    """
    lines = source.split("\n")
    begin = _marker_line(lines, PIN_BEGIN_MARKER)
    end = _marker_line(lines, PIN_END_MARKER)
    if end <= begin:
        raise PinFormatError("the generated pin markers are out of order")
    return lines, begin, end


def render_pin_block(payload: Mapping[str, Any]) -> str:
    """Render the source lines that live between the two markers.

    Args:
        payload: The pin payload.

    Returns:
        The block text, with no leading or trailing newline.
    """
    body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    return "\n".join(
        [
            "# Generated from the live install. Do not hand-edit: every field below is",
            '# covered by the "integrity" checksum, and editing one without regenerating',
            "# turns tools/drift_guard.py guard (h) red.",
            f"# Regenerate with: {_REGENERATE_COMMAND}",
            '_PIN_JSON: Final = """',
            body,
            '"""',
        ]
    )


def extract_pin_block(source: str) -> dict[str, Any]:
    """Read the pin payload out of a module source text.

    The drift guard's path. It reads the pin from the file it is guarding
    rather than importing it, so a corrupt pin is a message from one guard
    instead of an import failure in every consumer - and so no code from the
    guarded tree is executed to find out.

    Args:
        source: The whole module source.

    Returns:
        The parsed payload.

    Raises:
        PinFormatError: The markers are missing, the block holds no quoted JSON
            body, or that body is not a JSON object.
    """
    lines, begin, end = _block_bounds(source)
    block = "\n".join(lines[begin + 1 : end])
    fence = '"""'
    opened = block.find(fence)
    closed = block.find(fence, opened + len(fence)) if opened >= 0 else -1
    if opened < 0 or closed < 0:
        raise PinFormatError("the generated pin block holds no triple-quoted JSON body")
    try:
        payload = json.loads(block[opened + len(fence) : closed])
    except ValueError as exc:
        # Named fields, never the object - the shape docs_extract.py already
        # uses for the same decode. A JSONDecodeError carries msg, lineno and
        # colno, all of which are reasons; str() on it would be fine here but
        # a plain ValueError from a different json backend need not be, and an
        # unrecognised type falls closed to its class name.
        detail = getattr(exc, "msg", None) or type(exc).__name__
        line = getattr(exc, "lineno", 0)
        column = getattr(exc, "colno", 0)
        raise PinFormatError(
            f"the generated pin block is not valid JSON: {detail} at line {line} column {column}"
        ) from exc
    if not isinstance(payload, dict):
        raise PinFormatError(
            f"the generated pin block is a JSON {type(payload).__name__}, expected an object"
        )
    return payload


def rewrite_pin_source(source: str, payload: Mapping[str, Any]) -> str:
    """Return ``source`` with the generated block replaced by ``payload``.

    Everything outside the two marker lines is preserved byte for byte.

    Args:
        source: The whole module source.
        payload: The pin payload to write.

    Returns:
        The updated source.

    Raises:
        PinFormatError: The markers are missing, duplicated or out of order.
    """
    lines, begin, end = _block_bounds(source)
    return "\n".join([*lines[: begin + 1], render_pin_block(payload), *lines[end:]])


#: Windows can hold a brief share-violation on a file another process just
#: read, so the replace is retried rather than failing the whole re-extract.
_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_SECONDS: Final = 0.05


def write_pin(path: Path, payload: Mapping[str, Any]) -> None:
    """Rewrite a version module in place with a new pin, atomically.

    Bytes are written explicitly with LF terminators. On Windows a text-mode
    write turns every LF into CRLF and the matching read hides it, which would
    make the file's own byte count and hash depend on which machine last
    regenerated it - unacceptable in the one file whose job is recording a
    content hash (.gitattributes, CONVENTIONS.md section 10).

    Args:
        path: The version module to rewrite. Inside this repository, never the
            game install - nothing in this project writes there.
        payload: The pin payload to write.

    Raises:
        PinFormatError: The file holds no generated block.
        UnicodeEncodeError: The rewritten source is not 7-bit ASCII. Loud on
            purpose: non-negotiable 4 admits no exception, and a silent UTF-8
            write here would be found later by a gate rather than now.
        OSError: The file could not be read, written or replaced.
    """
    updated = rewrite_pin_source(path.read_text(encoding="utf-8"), payload)
    data = updated.encode("ascii")
    temporary = path.with_name(path.name + ".pin-tmp")
    temporary.write_bytes(data)
    last: OSError | None = None
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            temporary.replace(path)
        except OSError as exc:
            last = exc
            time.sleep(_RENAME_PAUSE_SECONDS * (attempt + 1))
        else:
            return
    temporary.unlink(missing_ok=True)
    raise last if last is not None else OSError("replace failed with no error recorded")
