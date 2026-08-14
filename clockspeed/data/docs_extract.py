"""The one and only reader of the game's shipped English docs file.

Per docs/ARCHITECTURE.md section 1.1, nothing else in Clockspeed is allowed to
open that file. This module sniffs its encoding, decodes it, loads its group
structure, and flags what it does not recognize. It deliberately stops there:
it does not normalize, join, convert or compute - ``clockspeed/data/registry.py``
owns all of that - and it does not locate the install - ``clockspeed/data/locate.py``
owns that, which is why every entry point here takes a Path or bytes argument
and this module imports neither.

WHY THE ENCODING SNIFF IS BYTE-PATTERN ONLY, NEVER A TRIAL DECODE
-----------------------------------------------------------------
Measured in docs/_archive/spike-report-s1-s2-s3-s7.md section S1 and recorded
in BOOTSTRAP.md section 3.2: the locale directory is a MIXED family - 54 of 55
files are UTF-16 LE with a BOM and one is UTF-8 with no BOM. Python's utf-16
codec decodes those UTF-8 bytes WITHOUT raising and returns mojibake, while
utf-8 decoding of UTF-16 bytes fails loudly. The failure is asymmetric, so a
try-decode-and-fall-back sniffer ordered utf-16 first reports success on the
wrong encoding and every downstream value is quietly garbage. Classification
here is therefore a strict test of the leading bytes and nothing else. There is
no try/except around a decode used to CHOOSE an encoding anywhere in this file;
the only try/except around a decode converts a genuine failure into a seam
error after the codec has already been chosen.

Two decoding details that follow from the same measurement:

- Decode with ``utf-16``, which consumes the BOM, not ``utf-16-le``, which
  leaves a U+FEFF as the first character of the decoded text.
- A stray U+FEFF was measured EMBEDDED inside one mDescription value. Only the
  LEADING BOM is a BOM; stripping U+FEFF globally would corrupt that value.

WHY AN UNKNOWN GROUP IS FLAGGED AND SKIPPED RATHER THAN DROPPED OR FATAL
------------------------------------------------------------------------
Non-negotiable 7 (CLAUDE.md section 3): unknown game content is flagged and
skipped, never fatal and never silently wrong. So the group short names the
pinned build ships are DATA (``KNOWN_GROUP_SHORT_NAMES``), the unrecognized
groups are logged, and :class:`DocsDocument` publishes them in full so a
consumer or the drift guard can surface a group this build has never seen.
Nothing is dropped: an unknown group is still parsed and still reachable
through ``DocsDocument.unknown`` and ``DocsDocument.all_groups``. A malformed
group - not a mapping, no NativeClass, Classes not a list - is likewise flagged
and skipped rather than raising. Only a document that is not a JSON list at all
fails loudly, because that is a broken file rather than unknown content.

KNOWN MEANS "THE PINNED BUILD SHIPS IT", NOT "THE REGISTRY CONSUMES IT"
-----------------------------------------------------------------------
The table below holds ALL of the pinned build's groups, not the handful the
registry draws on, and that distinction is the whole value of the flag.

Conflating the two was measured doing real damage. A table of the 21 groups the
registry consumed reported the other 93 STOCK groups as unknown content on
every single run, which is precisely the failure
``clockspeed/data/registry.py`` warns about in prose: a list that is wrong 93
times out of 114 is a list nobody reads, and the one genuinely new group
arrives on line 57 of noise. Worse, it was not only noise - the registry only
ever looks at recognized groups, so ten shipped RF_LIQUID item descriptors were
skipped outright and every recipe touching one published litres under a
contract that promises cubic metres.

Which groups the registry MODELS is therefore the registry's own question,
answered there by field presence rather than by any list of names. This module
answers only "has this build seen this group before", and
``tests/data/test_docs_extract.py`` checks the table against the pin's own
census so the two cannot drift apart. The table is not imported from
``clockspeed/data/version.py``: the pin module imports THIS one, and the
reverse would be a cycle across a seam that is deliberately one-way.

WHAT THIS MODULE NEVER DOES
---------------------------
- It never writes. Every path is opened read-only (non-negotiable 1).
- It never coerces a value. Every scalar in the document is measured to be a
  string, durations included ('2.000000'), and conversion belongs to the
  registry layer, which knows the units. A float() here would silently discard
  precision the solve path needs as an exact Fraction.
- It never echoes file content into an error message or a log line. Diagnostics
  carry byte offsets, class tokens and counts only.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

_LOG = logging.getLogger(__name__)

# --- encoding ---------------------------------------------------------------

#: The two encoding families :func:`sniff_encoding` distinguishes. These are
#: the values callers compare against; the concrete codec used for the decode
#: is an implementation detail because a BOM-bearing and a BOM-less member of
#: the same family need different codec names.
ENCODING_UTF16: Final = "utf-16"
ENCODING_UTF8: Final = "utf-8"

_CODEC_UTF16: Final = "utf-16"
_CODEC_UTF16_BE: Final = "utf-16-be"
_CODEC_UTF8: Final = "utf-8"
_CODEC_UTF8_SIG: Final = "utf-8-sig"

_BOM_UTF16_LE: Final = b"\xff\xfe"
_BOM_UTF16_BE: Final = b"\xfe\xff"
_BOM_UTF8: Final = b"\xef\xbb\xbf"

#: Enough leading bytes to hold the longest BOM plus one UTF-16 code unit.
_BOM_SNIFF_BYTES: Final = 4
_CODE_UNIT_PAIR: Final = 2

# --- document keys ----------------------------------------------------------

#: The two keys every one of the 114 groups carries, and nothing else
#: (spike report S2: distinct group keysets = 1).
KEY_NATIVE_CLASS: Final = "NativeClass"
KEY_CLASSES: Final = "Classes"

#: The measured primary key. Unique across all 2868 entries with zero
#: collisions and zero entries lacking it. FullName is NOT universal - only
#: 1552 entries carry one - so nothing may key on it.
KEY_CLASS_NAME: Final = "ClassName"

# --- the known-group table --------------------------------------------------

# Every name below was OBSERVED in the pinned build, and the table is the whole
# of that build's group census rather than a subset - see the module docstring
# for the measured cost of the subset. A name is added only when a probe has
# seen it, and tests/data/test_docs_extract.py compares this table against the
# pin's own group_entry_counts in both directions, so a name that the game
# stopped shipping is as loud as one it started shipping. Alphabetical, which
# is the order the pin census renders, so the two diff against each other by
# eye as well as by assertion.
_MEASURED_GROUP_SHORT_NAMES: Final = (
    "FGAmmoTypeInstantHit",
    "FGAmmoTypeProjectile",
    "FGAmmoTypeSpreadshot",
    "FGBuildable",
    "FGBuildableAttachmentMerger",
    "FGBuildableAttachmentSplitter",
    "FGBuildableBarrierCorner",
    "FGBuildableBeam",
    "FGBuildableBlueprintDesigner",
    "FGBuildableCircuitSwitch",
    "FGBuildableConveyorBelt",
    "FGBuildableConveyorLift",
    "FGBuildableConveyorMonitor",
    "FGBuildableCornerWall",
    "FGBuildableCornerWallLightweight",
    "FGBuildableDockingStation",
    "FGBuildableDoor",
    "FGBuildableDroneStation",
    "FGBuildableElevator",
    "FGBuildableElevatorFloorStop",
    "FGBuildableFactory",
    "FGBuildableFactoryBuilding",
    "FGBuildableFactorySimpleProducer",
    "FGBuildableFloodlight",
    "FGBuildableFoundationLightweight",
    "FGBuildableFrackingActivator",
    "FGBuildableFrackingExtractor",
    "FGBuildableGeneratorFuel",
    "FGBuildableGeneratorGeoThermal",
    "FGBuildableGeneratorNuclear",
    "FGBuildableJumppad",
    "FGBuildableLadder",
    "FGBuildableLightSource",
    "FGBuildableLightsControlPanel",
    "FGBuildableMAM",
    "FGBuildableManufacturer",
    "FGBuildableManufacturerVariablePower",
    "FGBuildableMergerPriority",
    "FGBuildablePassthrough",
    "FGBuildablePassthroughPipeHyper",
    "FGBuildablePillarLightweight",
    "FGBuildablePipeHyper",
    "FGBuildablePipeHyperJunction",
    "FGBuildablePipeReservoir",
    "FGBuildablePipeline",
    "FGBuildablePipelineJunction",
    "FGBuildablePipelinePump",
    "FGBuildablePoleBase",
    "FGBuildablePoleConveyor",
    "FGBuildablePolePipe",
    "FGBuildablePoleStackable",
    "FGBuildablePortal",
    "FGBuildablePortalSatellite",
    "FGBuildablePowerBooster",
    "FGBuildablePowerPole",
    "FGBuildablePowerStorage",
    "FGBuildablePriorityPowerSwitch",
    "FGBuildableRadarTower",
    "FGBuildableRailroadAttachment",
    "FGBuildableRailroadSignal",
    "FGBuildableRailroadStation",
    "FGBuildableRailroadTrack",
    "FGBuildableRampLightweight",
    "FGBuildableResourceExtractor",
    "FGBuildableResourceSink",
    "FGBuildableResourceSinkShop",
    "FGBuildableSnowCannon",
    "FGBuildableSnowDispenser",
    "FGBuildableSpaceElevator",
    "FGBuildableSplitterSmart",
    "FGBuildableStackableShelf",
    "FGBuildableStair",
    "FGBuildableStorage",
    "FGBuildableTradingPost",
    "FGBuildableTrainPlatformCargo",
    "FGBuildableTrainPlatformEmpty",
    "FGBuildableWalkway",
    "FGBuildableWalkwayLightweight",
    "FGBuildableWall",
    "FGBuildableWallLightweight",
    "FGBuildableWaterPump",
    "FGBuildableWidgetSign",
    "FGBuildableWire",
    "FGBuildingDescriptor",
    "FGCentralStorageContainer",
    "FGChainsaw",
    "FGChargedWeapon",
    "FGConsumableDescriptor",
    "FGConsumableEquipment",
    "FGCustomizationRecipe",
    "FGEquipmentDescriptor",
    "FGEquipmentStunSpear",
    "FGEquipmentZipline",
    "FGGasMask",
    "FGGolfCartDispenser",
    "FGHoverPack",
    "FGItemDescriptor",
    "FGItemDescriptorBiomass",
    "FGItemDescriptorNuclearFuel",
    "FGItemDescriptorPowerBoosterFuel",
    "FGJetPack",
    "FGJumpingStilts",
    "FGObjectScanner",
    "FGParachute",
    "FGPipeHyperStart",
    "FGPortableMinerDispenser",
    "FGPowerShardDescriptor",
    "FGRecipe",
    "FGResourceDescriptor",
    "FGSchematic",
    "FGSuitBase",
    "FGVehicleDescriptor",
    "FGVehiclePathSegment",
    "FGWeapon",
)

#: The default whitelist. Data, not a hardcoded branch: :func:`load_document`
#: takes an override so a caller - or a test - supplies its own set.
KNOWN_GROUP_SHORT_NAMES: Final = frozenset(_MEASURED_GROUP_SHORT_NAMES)

# --- skip reasons -----------------------------------------------------------

# Each reason names the offending KEY verbatim so a log line or a published
# SkippedGroup is actionable without re-reading this module.
REASON_NOT_A_MAPPING: Final = "group is not a JSON mapping"
REASON_MISSING_NATIVE_CLASS: Final = "missing, empty or non-string NativeClass"
REASON_NO_SHORT_NAME: Final = "NativeClass carries no trailing class name"
REASON_CLASSES_NOT_A_LIST: Final = "Classes is missing or is not a JSON list"


class DocsExtractError(Exception):
    """Base class for every failure this module raises."""


class DocsDecodeError(DocsExtractError):
    """The docs bytes did not decode under the encoding their leading bytes name."""


class DocsStructureError(DocsExtractError):
    """The docs text is not a JSON list of groups.

    Raised only for a broken document. Unknown or malformed individual groups
    are flagged and skipped instead (non-negotiable 7).
    """


@dataclass(frozen=True)
class DocsGroup:
    """One ``{NativeClass, Classes}`` group, verbatim.

    Attributes:
        native_class: The full NativeClass value exactly as the file carries
            it, e.g.
            ``/Script/CoreUObject.Class'/Script/FactoryGame.FGRecipe'``.
        short_name: The trailing class token derived from it, e.g. ``FGRecipe``.
        entries: The group's Classes entries, untouched. No conversion happens
            here.

            THE VALUE ANNOTATION IS NARROWER THAN THE DATA, knowingly and
            temporarily. 1152 measured values are NOT strings - two
            ``FGSchematic`` list fields and ``mFuel`` on two generator groups -
            so ``str`` is a promise the document does not keep, and a consumer
            who trusts it will delete the very type check that separates "the
            game shipped something new here" from "the game shipped nothing
            here". ``clockspeed/data/registry.py`` therefore reads entries as
            ``Mapping[str, object]`` on its own side and flags a present
            non-string. Widening this annotation to match reality also requires
            widening ``clockspeed.data.version._tally``, which annotates
            ``Mapping[str, str]`` while already testing ``isinstance`` at
            runtime; that file is outside this change.
    """

    native_class: str
    short_name: str
    entries: tuple[Mapping[str, str], ...]


@dataclass(frozen=True)
class SkippedGroup:
    """A group that could not be read as a group, and why.

    Attributes:
        index: Position in the top-level list, so the operator can find it.
        reason: One of the REASON_* constants.
        native_class: The NativeClass value if there was a usable one, else
            the empty string.
    """

    index: int
    reason: str
    native_class: str


@dataclass(frozen=True)
class DocsDocument:
    """Everything one pass over the docs file produced, including what it refused.

    Attributes:
        groups: Recognized, well-formed groups, in file order.
        unknown: Well-formed groups whose short name is outside the known set.
            Published in full rather than dropped, so unknown content is
            visible and recoverable.
        malformed: Groups that could not be read, each with its reason.
    """

    groups: tuple[DocsGroup, ...]
    unknown: tuple[DocsGroup, ...]
    malformed: tuple[SkippedGroup, ...]

    @property
    def unknown_short_names(self) -> tuple[str, ...]:
        """Short names of every unrecognized group, in file order.

        Returns:
            The short names, for a drift guard or a report to surface.
        """
        return tuple(group.short_name for group in self.unknown)

    @property
    def all_groups(self) -> tuple[DocsGroup, ...]:
        """Every well-formed group, recognized or not.

        Returns:
            The recognized groups followed by the unknown ones.
        """
        return (*self.groups, *self.unknown)

    @property
    def skipped_indexes(self) -> tuple[int, ...]:
        """Top-level positions of the malformed groups.

        Returns:
            One index per malformed group, in file order.
        """
        return tuple(item.index for item in self.malformed)


def _classify(head: bytes) -> tuple[str, str]:
    """Classify leading bytes into an encoding family and a concrete codec.

    Strictly a byte-pattern test: BOM first, then null placement. Never a trial
    decode - see the module docstring for the measurement that forbids it.

    Args:
        head: The first few bytes of the file. Fewer than
            ``_BOM_SNIFF_BYTES`` is accepted; an empty head classifies as
            UTF-8, and the subsequent decode or JSON parse is what fails
            loudly on a file that is neither.

    Returns:
        A ``(family, codec)`` pair. The family is ENCODING_UTF16 or
        ENCODING_UTF8; the codec is the name to hand to ``bytes.decode``, and
        it consumes a leading BOM where one is present.
    """
    if head.startswith((_BOM_UTF16_LE, _BOM_UTF16_BE)):
        return ENCODING_UTF16, _CODEC_UTF16
    if head.startswith(_BOM_UTF8):
        return ENCODING_UTF8, _CODEC_UTF8_SIG
    if len(head) >= _CODE_UNIT_PAIR:
        # A BOM-less UTF-16 file still shows its endianness in the null
        # placement of its first ASCII code unit. The utf-16 codec assumes
        # little-endian when no BOM is present, which is why the LE branch can
        # share a codec with the BOM-bearing case while BE cannot.
        if head[0] != 0 and head[1] == 0:
            return ENCODING_UTF16, _CODEC_UTF16
        if head[0] == 0 and head[1] != 0:
            return ENCODING_UTF16, _CODEC_UTF16_BE
    return ENCODING_UTF8, _CODEC_UTF8


def sniff_encoding(head: bytes) -> str:
    """Report which encoding family the leading bytes belong to.

    Args:
        head: The first bytes of the file. Four is enough for every pattern
            this distinguishes.

    Returns:
        ENCODING_UTF16 or ENCODING_UTF8.
    """
    return _classify(head)[0]


def decode_docs_bytes(raw: bytes) -> str:
    """Decode whole docs-file bytes using the encoding their leading bytes name.

    The whole ~10.6 MB file decodes in one pass, which is measured to complete
    without incident and is the right shape for a one-shot extractor.

    Args:
        raw: The complete file contents.

    Returns:
        The decoded text, with any LEADING byte-order mark consumed. A U+FEFF
        occurring inside a value is left alone - one was measured embedded in
        a description, and a global strip would corrupt it.

    Raises:
        DocsDecodeError: The bytes did not decode under the encoding their
            leading bytes name. The message carries the codec, the failure
            reason and a byte offset - never file content.
    """
    family, codec = _classify(raw[:_BOM_SNIFF_BYTES])
    try:
        return raw.decode(codec)
    except UnicodeDecodeError as exc:
        message = (
            f"docs bytes classified as {family} did not decode with codec "
            f"{codec}: {exc.reason} at byte {exc.start} of {len(raw)}"
        )
        raise DocsDecodeError(message) from exc


def read_docs_text(path: Path) -> str:
    """Read and decode a docs file from disk, read-only.

    Opened as bytes and decoded explicitly rather than through
    ``open(encoding=...)``, because a default-encoding read is exactly the
    silent-mojibake path this module exists to prevent. Nothing here writes,
    creates or touches the file (non-negotiable 1).

    Args:
        path: The docs file. Supplied by the caller - this module never
            locates the install itself.

    Returns:
        The decoded text.

    Raises:
        DocsDecodeError: The file did not decode under its sniffed encoding.
        OSError: The file could not be read.
    """
    return decode_docs_bytes(path.read_bytes())


def derive_short_name(native_class: str) -> str:
    """Reduce a NativeClass value to its trailing class token.

    Measured shapes, both of which must reduce to the same token:
    ``/Script/CoreUObject.Class'/Script/FactoryGame.FGRecipe'`` and the bare
    ``/Script/FactoryGame.FGRecipe``. Derived, never looked up: a hardcoded
    table of names would go stale on the next game patch.

    Args:
        native_class: The verbatim NativeClass value.

    Returns:
        The trailing class token, e.g. ``FGRecipe``, or the empty string if
        the value carries none.
    """
    token = native_class.strip()
    if "'" in token:
        # Unreal wraps the real path in Class'<path>'. The inner path is what
        # names the class; the outer prefix is always CoreUObject.Class.
        quoted = [part for part in token.split("'") if part]
        token = quoted[-1] if quoted else ""
    for separator in (".", "/"):
        if separator in token:
            return token.rsplit(separator, 1)[-1].strip()
    return token


def _build_entries(index: int, short_name: str, raw_classes: list[Any]) -> tuple[Any, ...]:
    """Collect a group's entries, flagging and skipping any that are not mappings.

    Args:
        index: The group's top-level position, for the log line.
        short_name: The group's short name, for the log line.
        raw_classes: The raw Classes list.

    Returns:
        The entry mappings, verbatim and unconverted.
    """
    entries: list[Any] = []
    non_string_values = 0
    for position, raw_entry in enumerate(raw_classes):
        if not isinstance(raw_entry, dict):
            _LOG.warning(
                "docs group %d (%s) entry %d is not a JSON mapping; flagged and skipped",
                index,
                short_name,
                position,
            )
            continue
        non_string_values += sum(1 for value in raw_entry.values() if not isinstance(value, str))
        entries.append(raw_entry)
    if non_string_values:
        # Every SCALAR in the document is a string - durations arrive as
        # '2.000000', never as 2.0. Non-scalar values are a different matter and
        # do occur on the pinned build: list-valued fields such as the schematic
        # unlock and dependency arrays, and the generator fuel arrays. So a
        # non-string is NOT evidence that the build changed, and this warning
        # deliberately does not say so - an earlier revision did, and it would
        # have sent a reader hunting a patch that never happened.
        #
        # It is still worth reporting, because the registry's scalar readers
        # must treat present-but-not-a-string as distinct from absent: absence
        # is the load-bearing signal for "not clock-scalable" and for "no sink
        # value", so silently collapsing the two would invent a fact.
        _LOG.warning(
            "docs group %d (%s) carries %d non-scalar value(s); these are not "
            "readable as scalars and are reported rather than coerced",
            index,
            short_name,
            non_string_values,
        )
    return tuple(entries)


def _build_group(index: int, raw_group: Any) -> DocsGroup | SkippedGroup:
    """Turn one top-level element into a group, or explain why it cannot be one.

    Args:
        index: The element's position in the top-level list.
        raw_group: The parsed element.

    Returns:
        A :class:`DocsGroup`, or a :class:`SkippedGroup` naming the defect.
    """
    if not isinstance(raw_group, dict):
        return SkippedGroup(index, REASON_NOT_A_MAPPING, "")

    native_class = raw_group.get(KEY_NATIVE_CLASS)
    if not isinstance(native_class, str) or not native_class.strip():
        return SkippedGroup(index, REASON_MISSING_NATIVE_CLASS, "")

    short_name = derive_short_name(native_class)
    if not short_name:
        return SkippedGroup(index, REASON_NO_SHORT_NAME, native_class)

    raw_classes = raw_group.get(KEY_CLASSES)
    if not isinstance(raw_classes, list):
        return SkippedGroup(index, REASON_CLASSES_NOT_A_LIST, native_class)

    return DocsGroup(native_class, short_name, _build_entries(index, short_name, raw_classes))


def _parse_document(text: str) -> list[Any]:
    """Parse the docs text into its top-level group list.

    Args:
        text: The decoded document.

    Returns:
        The top-level list.

    Raises:
        DocsStructureError: The text is not JSON, or its root is not a list.
            Both are broken-file conditions rather than unknown content, so
            both are loud.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        message = f"docs text is not valid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        raise DocsStructureError(message) from exc
    if not isinstance(parsed, list):
        message = (
            f"docs document root is a JSON {type(parsed).__name__}, "
            "expected a list of NativeClass groups"
        )
        raise DocsStructureError(message)
    return parsed


def load_document(
    text: str,
    *,
    known_short_names: frozenset[str] = KNOWN_GROUP_SHORT_NAMES,
) -> DocsDocument:
    """Load every group out of the docs text, flagging what is not recognized.

    The full-fidelity entry point: :func:`load_groups` is the same pass with
    only the recognized groups returned. Nothing is dropped here - unknown and
    malformed groups are both logged and published on the result.

    Args:
        text: The decoded document.
        known_short_names: Group short names the caller recognizes. Defaults
            to KNOWN_GROUP_SHORT_NAMES; supplying a set is how a caller widens
            the whitelist without editing this module.

    Returns:
        The recognized groups, the unknown groups and the malformed ones.

    Raises:
        DocsStructureError: The document is not a JSON list of groups.
    """
    groups: list[DocsGroup] = []
    unknown: list[DocsGroup] = []
    malformed: list[SkippedGroup] = []

    for index, raw_group in enumerate(_parse_document(text)):
        built = _build_group(index, raw_group)
        if isinstance(built, SkippedGroup):
            _LOG.warning("docs group %d flagged and skipped: %s", built.index, built.reason)
            malformed.append(built)
            continue
        if built.short_name not in known_short_names:
            _LOG.warning(
                "docs group %d has an unrecognized NativeClass (short name %r); "
                "flagged and skipped, published on DocsDocument.unknown",
                index,
                built.short_name,
            )
            unknown.append(built)
            continue
        groups.append(built)

    return DocsDocument(tuple(groups), tuple(unknown), tuple(malformed))


def load_groups(text: str) -> tuple[DocsGroup, ...]:
    """Load the recognized groups out of the docs text.

    Args:
        text: The decoded document.

    Returns:
        The recognized, well-formed groups in file order. Unknown and
        malformed groups are logged and omitted; use :func:`load_document`
        when they are needed.

    Raises:
        DocsStructureError: The document is not a JSON list of groups.
    """
    return load_document(text).groups


def index_by_short_name(groups: Sequence[DocsGroup]) -> Mapping[str, DocsGroup]:
    """Index groups by their short name for lookup by the registry.

    Args:
        groups: The groups to index.

    Returns:
        A mapping from short name to group, in the order given. A repeated
        short name keeps the FIRST group and logs the collision - a duplicate
        is mod or patch content, which is flagged and skipped rather than
        fatal (non-negotiable 7), and last-wins would silently replace real
        content with it.
    """
    index: dict[str, DocsGroup] = {}
    for group in groups:
        if group.short_name in index:
            _LOG.warning(
                "duplicate group short name %r; keeping the first and skipping "
                "the later NativeClass",
                group.short_name,
            )
            continue
        index[group.short_name] = group
    return index
