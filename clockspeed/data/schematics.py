"""The normalized schematic model - tier, type, cost and prerequisites, read once.

CS-1043 S1. ``clockspeed/data/registry.py`` deliberately does not model
``FGSchematic`` (its ``UNMODELED_GROUP_SHORT_NAMES``), and that ruling stands:
this module is a SIBLING of the registry, not an edit to it. It takes an
already-loaded :class:`~clockspeed.data.docs_extract.DocsDocument`, exactly as
:func:`clockspeed.data.registry.build_registry` does, and publishes a TYPED,
frozen :class:`SchematicCatalog`. ``clockspeed/progress/`` consumes that model
and never the document's verbatim strings (docs/ARCHITECTURE.md section 3).

It opens no file, locates no install and imports nothing above
``clockspeed/data/blobs.py`` and ``clockspeed/data/docs_extract.py``, which is
what lets the whole model be proven against a hand-authored synthetic group on
a machine with no game installed.

THE MEASURED SHAPES THIS READS, BY NAME
---------------------------------------
- ``mCost`` is an item-amount blob - the ``mIngredients`` grammar that
  :func:`~clockspeed.data.blobs.parse_item_amounts` owns - or the empty string.
- A minority of ``mCost`` blobs carry entries with NO ``Amount=`` at all,
  ``((ItemClass="<path>"))``, and the parser refuses them.
- ``mTechTier`` is an integer string and ``mType`` is an enum token.
- ``mSchematicDependencies`` is a JSON list, not a string, and each element is
  a mapping in one of exactly two keysets: a purchased-schematics dependency
  (``Class``, ``mSchematics``, ``mRequireAllSchematicsToBePurchased``) or a
  game-phase dependency (``Class``, ``mGamePhase``,
  ``mOnlyAllowInSelectedPhase``). ``mSchematics`` is a quoted class-path blob,
  the grammar :func:`~clockspeed.data.blobs.parse_class_paths` owns.
- ``FullName`` is a class half, one space and a path half -
  ``BlueprintGeneratedClass /Game/<package>.<ClassName>``. The path half is
  published as :attr:`Schematic.asset_path`, the join key CS-1343 names for a
  save's ``mPurchasedSchematics`` reference.

FLAG AND SKIP, NEVER FATAL AND NEVER SILENTLY WRONG (non-negotiable 7)
---------------------------------------------------------------------
- **An amount-less cost is None, never a defaulted amount.** The document
  names an item and does not say how many. Publishing 1 invents a quantity and
  publishing 0 invents a free milestone; both are confident numbers of the
  right type. :class:`~clockspeed.data.blobs.BlobParseError` is caught PER
  SCHEMATIC, that schematic's cost is published as None under the named code
  :data:`WARN_COST_WITHOUT_AMOUNT`, and every other schematic is read as
  normal. Any other refused cost blob is None under
  :data:`WARN_UNREADABLE_COST`.
- **An empty cost is the empty tuple, and it is not None.** ``""`` is a real
  and valid value - a schematic that costs nothing - while None means the cost
  is unknown. The two are different facts and stay distinguishable.
- **A negative or zero cost amount is None, never published**, under the
  named code :data:`WARN_NONPOSITIVE_AMOUNT`. Neither has been shipped, and a
  refund or a free line would be a confident number of the right type.
- **A short prerequisite list is a wrong availability answer**, so a
  dependency this module cannot read in full is flagged and
  :attr:`Schematic.dependencies_complete` is published False rather than the
  readable remainder passing for the whole. That covers an unknown shape, an
  unreadable ``mSchematics`` list, an empty phase token, a True/False flag in
  neither spelling and a repeated phase dependency.
- **An ABSENT dependency list is unknown, not "no prerequisites".** The
  shipped document carries ``mSchematicDependencies`` on every schematic entry
  and says "none" with the EMPTY LIST, so a missing key is unmeasured content:
  flagged, incomplete, and never fatal.
- **An asset path is read, never guessed.** ``FullName`` is not on every docs
  entry (``clockspeed/data/docs_extract.py``, beside ``KEY_CLASS_NAME``), so
  one that is absent, not a string, or not exactly two non-empty halves around
  one space publishes :attr:`Schematic.asset_path` None and is flagged. The
  path is never rebuilt from the ClassName and never reduced with
  :func:`class_name_of_path`: matching on a trailing token is the
  name-matching heuristic the join must not use.
- **A field outside the measured keyset is flagged and read past**, aggregated
  by field name so one new field on every entry is one warning row with a
  count rather than one row per schematic.

The accounting is checked rather than assumed: :func:`verify_accounting` runs
on every catalog this module builds and raises
:class:`SchematicIntegrityError` unless every offered entry is either a
published schematic or a skipped one, and every published schematic's cost is
either parsed or flagged. That error deliberately does NOT subclass ValueError,
so the per-schematic BlobParseError handler can never swallow it.

NO FLOATS, ANYWHERE (non-negotiable 6). An amount goes from the parser's int
straight to a :class:`~fractions.Fraction`; a tier goes from an ASCII digit
string straight to an int. There is no ``float`` in this file.

UNITS ARE NOT CONVERTED. A cost amount is the blob's integer exactly as
written. Units are a property of the ITEM, which lives in another group, and
resolving them is a join against the registry, not something knowable from a
cost blob (``clockspeed/data/blobs.py`` states the same rule).

WHAT THIS MODULE NEVER DOES. It never writes, never coerces a value it cannot
read into a default, and never echoes document content into a warning detail:
details name fields, codes and counts. A warning subject is a ClassName, a
group short name or a field name.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final, NamedTuple

from clockspeed.data.blobs import BlobParseError, parse_class_paths, parse_item_amounts
from clockspeed.data.docs_extract import KEY_CLASS_NAME, DocsDocument

__all__ = [
    "KEY_COST",
    "KEY_DEPENDENCIES",
    "KEY_DEPENDENCY_CLASS",
    "KEY_DEPENDENCY_SCHEMATICS",
    "KEY_FULL_NAME",
    "KEY_GAME_PHASE",
    "KEY_ONLY_IN_SELECTED_PHASE",
    "KEY_REQUIRE_ALL",
    "KEY_TECH_TIER",
    "KEY_TYPE",
    "KNOWN_SCHEMATIC_FIELDS",
    "PHASE_DEPENDENCY_CLASS",
    "PURCHASED_DEPENDENCY_CLASS",
    "SCHEMATIC_GROUP_SHORT_NAMES",
    "WARN_COST_WITHOUT_AMOUNT",
    "WARN_DUPLICATE_CLASS_NAME",
    "WARN_EMPTY_VALUE",
    "WARN_MISSING_CLASS_NAME",
    "WARN_MISSING_FIELD",
    "WARN_NONPOSITIVE_AMOUNT",
    "WARN_NON_STRING_VALUE",
    "WARN_REPEATED_PHASE_DEPENDENCY",
    "WARN_UNKNOWN_DEPENDENCY",
    "WARN_UNKNOWN_FIELD",
    "WARN_UNPARSABLE_FLAG",
    "WARN_UNPARSABLE_TIER",
    "WARN_UNREADABLE_COST",
    "WARN_UNREADABLE_DEPENDENCIES",
    "WARN_UNREADABLE_DEPENDENCY",
    "WARN_UNREADABLE_FULL_NAME",
    "CostLine",
    "PhaseDependency",
    "PurchaseDependency",
    "Schematic",
    "SchematicCatalog",
    "SchematicIntegrityError",
    "SchematicWarning",
    "class_name_of_path",
    "normalize_schematics",
    "verify_accounting",
]

# ---------------------------------------------------------------------------
# The group and its keys
# ---------------------------------------------------------------------------

#: The docs groups whose entries are schematics. Whitelisted on NativeClass,
#: never detected by shape - the registry's rule, for the registry's reason.
SCHEMATIC_GROUP_SHORT_NAMES: Final = frozenset({"FGSchematic"})

KEY_COST: Final = "mCost"
KEY_TECH_TIER: Final = "mTechTier"
KEY_TYPE: Final = "mType"
KEY_DEPENDENCIES: Final = "mSchematicDependencies"
KEY_DEPENDENCY_CLASS: Final = "Class"
KEY_DEPENDENCY_SCHEMATICS: Final = "mSchematics"
KEY_REQUIRE_ALL: Final = "mRequireAllSchematicsToBePurchased"
KEY_GAME_PHASE: Final = "mGamePhase"
KEY_ONLY_IN_SELECTED_PHASE: Final = "mOnlyAllowInSelectedPhase"
KEY_FULL_NAME: Final = "FullName"

#: The one character a FullName separates its class half from its path half
#: with - ``BlueprintGeneratedClass /Game/<package>.<ClassName>``.
_FULL_NAME_SEPARATOR: Final = " "
#: A readable FullName is exactly this many non-empty halves around that
#: separator: the class half, then the path half.
_FULL_NAME_HALVES: Final = 2

#: The class token a purchased-schematics dependency's ``Class`` path ends in.
PURCHASED_DEPENDENCY_CLASS: Final = "BP_SchematicPurchasedDependency_C"
#: The class token a game-phase dependency's ``Class`` path ends in.
PHASE_DEPENDENCY_CLASS: Final = "BP_GamePhaseReachedDependency_C"

# A dependency is recognized by its keyset AND its class token together - an
# allowlist of whole shapes. A new dependency class wearing an old keyset is a
# different rule the game added, and reading it as the old one would be
# silently wrong, so it is flagged instead.
_PURCHASED_DEPENDENCY_KEYS: Final = frozenset(
    {KEY_DEPENDENCY_CLASS, KEY_DEPENDENCY_SCHEMATICS, KEY_REQUIRE_ALL}
)
_PHASE_DEPENDENCY_KEYS: Final = frozenset(
    {KEY_DEPENDENCY_CLASS, KEY_GAME_PHASE, KEY_ONLY_IN_SELECTED_PHASE}
)

#: Every field the pinned build's schematic entries were measured to carry.
#: Fields outside it are flagged under WARN_UNKNOWN_FIELD and read past; fields
#: inside it that this model does not read (icons, descriptions, unlocks) are
#: known content deliberately left to a later item, and are not flagged.
KNOWN_SCHEMATIC_FIELDS: Final = frozenset(
    {
        KEY_CLASS_NAME,
        KEY_FULL_NAME,
        KEY_COST,
        "mDependenciesBlocksSchematicAccess",
        "mDescription",
        "mDisplayName",
        "mGameplayTags",
        "mHiddenUntilDependenciesMet",
        "mIncludeInBuilds",
        "mIsPlayerSpecific",
        "mMenuPriority",
        "mRelevantEvents",
        "mRelevantShopSchematics",
        KEY_DEPENDENCIES,
        "mSchematicIcon",
        "mSchematicUnlockTag",
        "mSmallSchematicIcon",
        "mStatisticGameplayTag",
        "mSubCategories",
        KEY_TECH_TIER,
        "mTimeToComplete",
        KEY_TYPE,
        "mUnlockDescription",
        "mUnlockIconBig",
        "mUnlockIconCategory",
        "mUnlockIconSmall",
        "mUnlockName",
        "mUnlocks",
    }
)

# The amount-less cost shape, recognized whole so it gets its own named code
# rather than sharing one with an arbitrary malformed blob. Anchored end to end
# and tiled the way the parser tiles, so only that exact shape matches.
_AMOUNTLESS_COST_RE: Final = re.compile(r'\(\(ItemClass="[^"]*"\)(?:,\(ItemClass="[^"]*"\))*\)')

# A tier is ASCII digits and nothing else. ``int()`` alone is too lenient: it
# accepts surrounding whitespace, a sign, underscores and non-ASCII digits.
_TIER_RE: Final = re.compile(r"[0-9]+")

_FLAG_SPELLINGS: Final[Mapping[str, bool]] = MappingProxyType({"True": True, "False": False})

# ---------------------------------------------------------------------------
# Warning codes
# ---------------------------------------------------------------------------

WARN_COST_WITHOUT_AMOUNT: Final = "cost-without-amount"
WARN_DUPLICATE_CLASS_NAME: Final = "duplicate-class-name"
WARN_EMPTY_VALUE: Final = "empty-value"
WARN_MISSING_CLASS_NAME: Final = "missing-class-name"
WARN_MISSING_FIELD: Final = "missing-field"
WARN_NON_STRING_VALUE: Final = "non-string-value"
WARN_NONPOSITIVE_AMOUNT: Final = "non-positive-amount"
WARN_REPEATED_PHASE_DEPENDENCY: Final = "repeated-phase-dependency"
WARN_UNKNOWN_DEPENDENCY: Final = "unknown-dependency-shape"
WARN_UNKNOWN_FIELD: Final = "unknown-field"
WARN_UNPARSABLE_FLAG: Final = "unparsable-flag"
WARN_UNPARSABLE_TIER: Final = "unparsable-tier"
WARN_UNREADABLE_COST: Final = "unreadable-cost"
WARN_UNREADABLE_DEPENDENCIES: Final = "unreadable-dependencies"
WARN_UNREADABLE_DEPENDENCY: Final = "unreadable-dependency"
WARN_UNREADABLE_FULL_NAME: Final = "unreadable-full-name"


class SchematicIntegrityError(Exception):
    """The catalog's accounting does not close.

    Deliberately NOT a :class:`ValueError`, and therefore not catchable as a
    :class:`~clockspeed.data.blobs.BlobParseError`: the per-schematic handler
    that flags an unreadable cost must never be able to swallow the check that
    every schematic was accounted for.
    """


class CostLine(NamedTuple):
    """One line of a schematic's cost: an item class and an exact amount.

    A named tuple, so a line IS the ``(item class, amount)`` pair and reads as
    one.

    Attributes:
        item_class: The item's ClassName - the text after the final ``.`` of
            the asset path, with the ``Type'...'`` wrapper's closing quote
            stripped (:func:`class_name_of_path`). It is the key
            :attr:`clockspeed.data.registry.Registry.items` is keyed by.
        amount: The blob's integer amount as an exact Fraction, verbatim and
            NOT unit-converted - see the module docstring.
    """

    item_class: str
    amount: Fraction


@dataclass(frozen=True)
class PurchaseDependency:
    """A prerequisite that other schematics have been purchased.

    Attributes:
        schematics: The prerequisite schematics' ClassNames, in source order.
        require_all: True when every one is required, False when any one is
            enough, and None when the flag could not be read - flagged, and
            never guessed as either.
    """

    schematics: tuple[str, ...]
    require_all: bool | None


@dataclass(frozen=True)
class PhaseDependency:
    """A prerequisite that the game has reached a phase.

    Attributes:
        phase: The game-phase enum token, verbatim (an ``EGP_`` token).
        only_in_selected_phase: True when the schematic is available only IN
            that phase rather than from it onward, and None when unreadable.
    """

    phase: str
    only_in_selected_phase: bool | None


@dataclass(frozen=True)
class Schematic:
    """One schematic, normalized.

    Attributes:
        class_name: The ClassName, the model's key.
        tech_tier: The tier as an int, or None when the field is absent or is
            not an ASCII digit string - flagged, never defaulted to zero.
        type_token: The ``mType`` enum token verbatim, or None when absent or
            empty - flagged.
        cost: The cost lines in source order. The EMPTY tuple is a schematic
            that costs nothing; None is a cost this build could not read -
            an amount-less blob among them - and is always flagged.
        purchase_dependencies: Every purchased-schematics prerequisite read in
            full, in source order.
        phase_dependency: The game-phase prerequisite, or None when there is
            none. A second one is flagged and the first is kept.
        dependencies_complete: False when any prerequisite could not be read
            in full, so the two fields above are known to be a remainder.
        asset_path: The PATH half of the entry's ``FullName`` verbatim - the
            object path after the one space that separates it from the class
            half - published as this side of the join CS-1343 names against a
            save's schematic references. None when ``FullName`` is absent, not
            a string, or not exactly one class half and one path half -
            flagged, and never rebuilt from the ClassName or reduced to a
            trailing token. Defaulted to None, the unknown reading, only so a
            hand-built Schematic stays constructible;
            :func:`normalize_schematics` always passes it.
    """

    class_name: str
    tech_tier: int | None
    type_token: str | None
    cost: tuple[CostLine, ...] | None
    purchase_dependencies: tuple[PurchaseDependency, ...]
    phase_dependency: PhaseDependency | None
    dependencies_complete: bool
    asset_path: str | None = None

    @property
    def dependency_schematics(self) -> tuple[str, ...]:
        """Every prerequisite schematic's ClassName, flattened and de-duplicated.

        Returns:
            The names in first-seen order. Whether each group is any-of or
            all-of is on :attr:`purchase_dependencies`, not here.
        """
        names = (
            name for dependency in self.purchase_dependencies for name in dependency.schematics
        )
        return tuple(dict.fromkeys(names))

    @property
    def game_phase(self) -> str | None:
        """The game-phase prerequisite's token, if there is one.

        Returns:
            The verbatim ``EGP_`` token, or None.
        """
        return None if self.phase_dependency is None else self.phase_dependency.phase


@dataclass(frozen=True)
class SchematicWarning:
    """One piece of schematic content that was flagged, and why.

    Attributes:
        code: One of the module's WARN_* constants.
        subject: A ClassName, a group short name, or - for an unknown field -
            the field name.
        detail: One line naming the consequence, never echoing a value.
        count: How many occurrences this row aggregates.
    """

    code: str
    subject: str
    detail: str
    count: int = 1


@dataclass(frozen=True)
class SchematicCatalog:
    """Every schematic one document yielded, and the accounting that closes over it.

    Attributes:
        schematics: ClassName to schematic, in file order. Read-only.
        warnings: Everything flagged, sorted, aggregated by code, subject and
            detail.
        entries_offered: Entries in every schematic group of the document.
        entries_skipped: Entries that could not be keyed - no ClassName, or a
            repeated one.
        costs_parsed: Published schematics whose cost was read, empty included.
        costs_flagged: Published schematics whose cost is None.
    """

    schematics: Mapping[str, Schematic]
    warnings: tuple[SchematicWarning, ...]
    entries_offered: int
    entries_skipped: int
    costs_parsed: int
    costs_flagged: int


class _WarningLog:
    """Accumulates warnings, aggregating repeats by ``(code, subject, detail)``."""

    def __init__(self) -> None:
        """Start an empty log."""
        self._counts: dict[tuple[str, str, str], int] = {}

    def add(self, code: str, subject: str, detail: str) -> None:
        """Record one occurrence.

        Args:
            code: One of the WARN_* constants.
            subject: What is being flagged.
            detail: One line naming the consequence.
        """
        key = (code, subject, detail)
        self._counts[key] = self._counts.get(key, 0) + 1

    def emit(self) -> tuple[SchematicWarning, ...]:
        """Publish the accumulated warnings.

        Returns:
            One warning per distinct ``(code, subject, detail)``, sorted, so two
            runs over the same input publish byte-identical warnings.
        """
        return tuple(
            SchematicWarning(code, subject, detail, count)
            for (code, subject, detail), count in sorted(self._counts.items())
        )


def class_name_of_path(path: str) -> str:
    """Reduce an Unreal object path to the class name a model is keyed by.

    The rule ``clockspeed/audit/placement.py`` ``class_name_of_path`` applies -
    the text after the final ``.``, or the whole input when there is none -
    plus the strip of the ``Type'...'`` wrapper's closing quote that
    ``clockspeed/data/blobs.py`` applies to an item key. Written here rather
    than imported because the data layer imports nothing above itself.

    Args:
        path: An object path, wrapped or bare.

    Returns:
        The trailing class name.
    """
    tail = path.rpartition(".")[2] if "." in path else path
    return tail.removesuffix("'")


def _text(entry: Mapping[str, object], key: str, subject: str, log: _WarningLog) -> str | None:
    """Read one scalar field, flagging an absent value and a non-string one.

    Args:
        entry: The entry mapping.
        key: The field name.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The verbatim string, or None when the field is absent or not a string.
    """
    value = entry.get(key)
    if isinstance(value, str):
        return value
    if value is None:
        log.add(WARN_MISSING_FIELD, subject, f"{key} is absent; read as unknown, never defaulted")
    else:
        log.add(
            WARN_NON_STRING_VALUE,
            subject,
            f"{key} is present but is not a string; read as unknown, never as absent",
        )
    return None


def _flag(value: object, key: str, subject: str, log: _WarningLog) -> bool | None:
    """Read one boolean dependency field against the document's two spellings.

    Args:
        value: The raw value.
        key: The field name, for the warning.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        True or False for exactly ``'True'`` or ``'False'``, otherwise None.
    """
    flag = _FLAG_SPELLINGS.get(value) if isinstance(value, str) else None
    if flag is None:
        log.add(
            WARN_UNPARSABLE_FLAG,
            subject,
            f"{key} is neither True nor False; read as unknown, never as either",
        )
    return flag


def _tech_tier(entry: Mapping[str, object], subject: str, log: _WarningLog) -> int | None:
    """Read mTechTier as an int.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The tier, or None when absent or not an ASCII digit string.
    """
    text = _text(entry, KEY_TECH_TIER, subject, log)
    if text is None:
        return None
    if _TIER_RE.fullmatch(text) is None:
        log.add(
            WARN_UNPARSABLE_TIER,
            subject,
            f"{KEY_TECH_TIER} is not a whole number; tier unknown, never zero",
        )
        return None
    return int(text)


def _type_token(entry: Mapping[str, object], subject: str, log: _WarningLog) -> str | None:
    """Read mType verbatim.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The enum token, or None when absent, not a string or empty.
    """
    text = _text(entry, KEY_TYPE, subject, log)
    if text is None:
        return None
    if not text:
        log.add(WARN_EMPTY_VALUE, subject, f"{KEY_TYPE} is empty; type unknown")
        return None
    return text


def _asset_path(entry: Mapping[str, object], subject: str, log: _WarningLog) -> str | None:
    """Read the PATH half of FullName verbatim.

    Split on the separator and nothing else: no ``.`` is parsed and the path
    half is never cut down to a trailing token, because reducing a path to its
    trailing token is the name-matching heuristic the join must not use.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The path half, or None when FullName is absent, not a string, or not
        exactly two non-empty halves around one separator.
    """
    text = _text(entry, KEY_FULL_NAME, subject, log)
    if text is None:
        return None
    halves = text.split(_FULL_NAME_SEPARATOR)
    if len(halves) != _FULL_NAME_HALVES or not all(halves):
        log.add(
            WARN_UNREADABLE_FULL_NAME,
            subject,
            f"{KEY_FULL_NAME} is not one class half and one path half around one "
            "separator; asset path unknown, never guessed",
        )
        return None
    return halves[1]


def _cost(
    entry: Mapping[str, object], subject: str, log: _WarningLog
) -> tuple[CostLine, ...] | None:
    """Read mCost, catching a refused blob for this schematic alone.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The cost lines - empty for an empty blob - or None when the field is
        absent, not a string, or refused by the item-amount grammar.
    """
    blob = _text(entry, KEY_COST, subject, log)
    if blob is None:
        return None
    try:
        amounts = parse_item_amounts(blob)
    except BlobParseError:
        # Caught per schematic and NOT chained into the warning: the error's
        # message quotes the blob, and a detail names fields, never values.
        if _AMOUNTLESS_COST_RE.fullmatch(blob) is not None:
            log.add(
                WARN_COST_WITHOUT_AMOUNT,
                subject,
                f"{KEY_COST} names its items with no Amount; cost unknown, never 0 or 1",
            )
        else:
            log.add(
                WARN_UNREADABLE_COST,
                subject,
                f"{KEY_COST} does not match the item-amount grammar; cost unknown",
            )
        return None
    # Neither sign has been shipped. A negative line is a refund and a zero line
    # is a free one, and publishing either is a confident number of the right
    # type - so both are flagged under one named code and the cost is unknown.
    if any(amount.amount < 0 for amount in amounts):
        log.add(
            WARN_NONPOSITIVE_AMOUNT,
            subject,
            f"{KEY_COST} carries a negative amount; cost unknown, never a refund",
        )
        return None
    if any(amount.amount == 0 for amount in amounts):
        log.add(
            WARN_NONPOSITIVE_AMOUNT,
            subject,
            f"{KEY_COST} carries a zero amount; cost unknown, never a free line",
        )
        return None
    return tuple(CostLine(amount.item_key, Fraction(amount.amount)) for amount in amounts)


@dataclass
class _Dependencies:
    """The working state of one schematic's dependency read."""

    purchases: list[PurchaseDependency]
    phase: PhaseDependency | None = None
    complete: bool = True


def _purchase(
    raw: Mapping[str, object],
    subject: str,
    log: _WarningLog,
) -> PurchaseDependency | None:
    """Read one purchased-schematics dependency in full, or refuse it.

    Args:
        raw: The dependency mapping, already matched on keyset and class.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The dependency, or None when its schematic list cannot be read.
    """
    blob = raw.get(KEY_DEPENDENCY_SCHEMATICS)
    paths: tuple[str, ...] | None = None
    if isinstance(blob, str):
        try:
            paths = parse_class_paths(blob)
        except BlobParseError:
            paths = None
    if paths is None:
        log.add(
            WARN_UNREADABLE_DEPENDENCY,
            subject,
            f"{KEY_DEPENDENCY_SCHEMATICS} does not match the class-path grammar; "
            "prerequisites incomplete",
        )
        return None
    require_all = _flag(raw.get(KEY_REQUIRE_ALL), KEY_REQUIRE_ALL, subject, log)
    return PurchaseDependency(tuple(class_name_of_path(path) for path in paths), require_all)


def _phase(raw: Mapping[str, object], subject: str, log: _WarningLog) -> PhaseDependency | None:
    """Read one game-phase dependency in full, or refuse it.

    Args:
        raw: The dependency mapping, already matched on keyset and class.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        The dependency, or None when its phase token is not a non-empty string.
    """
    phase = raw.get(KEY_GAME_PHASE)
    if not isinstance(phase, str) or not phase:
        log.add(
            WARN_UNREADABLE_DEPENDENCY,
            subject,
            f"{KEY_GAME_PHASE} is not a phase token; prerequisites incomplete",
        )
        return None
    only = _flag(raw.get(KEY_ONLY_IN_SELECTED_PHASE), KEY_ONLY_IN_SELECTED_PHASE, subject, log)
    return PhaseDependency(phase, only)


def _shape_of(raw: object) -> str | None:
    """Name which measured dependency shape a raw element is, if any.

    Args:
        raw: One element of the dependency list.

    Returns:
        PURCHASED_DEPENDENCY_CLASS or PHASE_DEPENDENCY_CLASS when the keyset
        and the class token BOTH match one measured shape, otherwise None.
    """
    if not isinstance(raw, dict):
        return None
    token = raw.get(KEY_DEPENDENCY_CLASS)
    if not isinstance(token, str):
        return None
    keys = frozenset(raw)
    name = class_name_of_path(token)
    if keys == _PURCHASED_DEPENDENCY_KEYS and name == PURCHASED_DEPENDENCY_CLASS:
        return PURCHASED_DEPENDENCY_CLASS
    if keys == _PHASE_DEPENDENCY_KEYS and name == PHASE_DEPENDENCY_CLASS:
        return PHASE_DEPENDENCY_CLASS
    return None


def _dependencies(entry: Mapping[str, object], subject: str, log: _WarningLog) -> _Dependencies:
    """Read mSchematicDependencies, element by element.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName.
        log: The warning log.

    Returns:
        What was read in full, with ``complete`` False if anything was not.
    """
    state = _Dependencies(purchases=[])
    raw_list = entry.get(KEY_DEPENDENCIES)
    if not isinstance(raw_list, list):
        log.add(
            WARN_UNREADABLE_DEPENDENCIES,
            subject,
            f"{KEY_DEPENDENCIES} is absent or not a list; prerequisites unknown",
        )
        state.complete = False
        return state
    for raw in raw_list:
        shape = _shape_of(raw)
        if shape is None:
            log.add(
                WARN_UNKNOWN_DEPENDENCY,
                subject,
                "a dependency matches neither measured shape; prerequisites incomplete",
            )
            state.complete = False
        elif shape == PURCHASED_DEPENDENCY_CLASS:
            purchase = _purchase(raw, subject, log)
            if purchase is None or purchase.require_all is None:
                state.complete = False
            if purchase is not None:
                state.purchases.append(purchase)
        else:
            phase = _phase(raw, subject, log)
            if phase is None or phase.only_in_selected_phase is None:
                state.complete = False
            if phase is not None and state.phase is not None:
                log.add(
                    WARN_REPEATED_PHASE_DEPENDENCY,
                    subject,
                    "more than one game-phase dependency; keeping the first",
                )
                state.complete = False
            elif phase is not None:
                state.phase = phase
    return state


def _flag_unknown_fields(entry: Mapping[str, object], log: _WarningLog) -> None:
    """Flag every field outside the measured keyset, aggregated by field name.

    Args:
        entry: The entry mapping.
        log: The warning log.
    """
    for key in entry:
        if key not in KNOWN_SCHEMATIC_FIELDS:
            log.add(
                WARN_UNKNOWN_FIELD,
                key,
                "field is outside the measured schematic keyset; read past, not modelled",
            )


def verify_accounting(catalog: SchematicCatalog) -> None:
    """Check that every entry and every cost is accounted for.

    Each published cost count is recomputed from the model itself, so the check
    holds against the published schematics rather than against the counters
    that produced them.

    Args:
        catalog: The catalog to check.

    Raises:
        SchematicIntegrityError: Published plus skipped is not the number
            offered, or parsed plus flagged is not the number published, or
            either cost count disagrees with the model.
    """
    published = len(catalog.schematics)
    flagged = sum(1 for schematic in catalog.schematics.values() if schematic.cost is None)
    if published + catalog.entries_skipped != catalog.entries_offered:
        raise SchematicIntegrityError(
            f"{published} published plus {catalog.entries_skipped} skipped is not the "
            f"{catalog.entries_offered} schematic entries offered"
        )
    if catalog.costs_parsed + catalog.costs_flagged != published:
        raise SchematicIntegrityError(
            f"{catalog.costs_parsed} parsed plus {catalog.costs_flagged} flagged costs is not "
            f"the {published} schematics published"
        )
    if catalog.costs_flagged != flagged:
        raise SchematicIntegrityError(
            f"{catalog.costs_flagged} costs counted as flagged, but {flagged} published "
            "schematics carry no cost"
        )


def normalize_schematics(document: DocsDocument) -> SchematicCatalog:
    """Build the schematic catalog from a loaded docs document.

    Args:
        document: The document, as :func:`clockspeed.data.docs_extract.load_document`
            produced it. Only its recognized groups are read.

    Returns:
        The catalog, its accounting already verified.

    Raises:
        SchematicIntegrityError: The accounting does not close - a defect in
            this module, never a property of the document.
    """
    log = _WarningLog()
    built: dict[str, Schematic] = {}
    offered = skipped = parsed = flagged = 0
    for group in document.groups:
        if group.short_name not in SCHEMATIC_GROUP_SHORT_NAMES:
            continue
        for entry in group.entries:
            offered += 1
            name = entry.get(KEY_CLASS_NAME)
            if not isinstance(name, str) or not name:
                log.add(
                    WARN_MISSING_CLASS_NAME,
                    group.short_name,
                    f"entry has no {KEY_CLASS_NAME}; it cannot be keyed",
                )
                skipped += 1
                continue
            if name in built:
                log.add(WARN_DUPLICATE_CLASS_NAME, name, "ClassName repeats; keeping the first")
                skipped += 1
                continue
            _flag_unknown_fields(entry, log)
            cost = _cost(entry, name, log)
            if cost is None:
                flagged += 1
            else:
                parsed += 1
            dependencies = _dependencies(entry, name, log)
            built[name] = Schematic(
                class_name=name,
                tech_tier=_tech_tier(entry, name, log),
                type_token=_type_token(entry, name, log),
                cost=cost,
                purchase_dependencies=tuple(dependencies.purchases),
                phase_dependency=dependencies.phase,
                dependencies_complete=dependencies.complete,
                asset_path=_asset_path(entry, name, log),
            )
    catalog = SchematicCatalog(
        schematics=MappingProxyType(built),
        warnings=log.emit(),
        entries_offered=offered,
        entries_skipped=skipped,
        costs_parsed=parsed,
        costs_flagged=flagged,
    )
    verify_accounting(catalog)
    return catalog
