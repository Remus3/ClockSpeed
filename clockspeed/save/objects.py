"""The object-header walk, and property resolution against the property mapping.

WHAT THIS MODULE OWNS
-----------------------
The decompressed body's leading length prefix, the object record table, the
version-dispatched transform block, and the rule ``docs/ARCHITECTURE.md``
assigns here: **an unknown actor class is logged and SKIPPED, never fatal.**

It takes bytes plus two version scalars. It does not read the header itself, it
does not walk chunks, and it opens no file - so it can be written and tested
beside its neighbours, and ADR 0007 decision item 6 (``workdir.py`` is the only
writer in this package) stays trivially true here.

TWO DISPATCHES, AND THEY ARE INDEPENDENT
------------------------------------------
This is the single most important property in the module, and a parser that
gets it wrong passes almost every fixture.

- The **body length prefix width** follows the HEADER version: an int64 on
  header versions 13 and 14, an int32 on header version 10. Corrected under
  CS-404 this session - an earlier record had the prefix ABSENT on header 10,
  which was a property of one fixture rather than of the format.
- The **transform delta** - the filler between the instance-name string and the
  transform block - follows the SAVE version: 4 on save 36, 8 on saves 52 and
  60, per ADR 0003, which measured 626 node actors with 626 valid transforms.

Across the whole real library the two covary: header 10 always appears with
save 36, header 14 with saves 52 and 60. So a parser reading both decisions off
one field is correct on every real file and on every real-shaped fixture. The
corpus therefore carries ``SAVE_CROSS`` - header 14 with save 36, a combination
in no real file - whose measured pair is (8, 4). It is the only thing that
separates the two dispatches, and it is why they are looked up through two
functions here rather than through one.

SAVE VERSION 42 WAS MEASURED, NOT INTERPOLATED - AND 4 IS WHAT BOTH WOULD SAY
-------------------------------------------------------------------------------
Its delta was absent from the table for exactly as long as it was unmeasured.
With 36 -> 4 beside 52 -> 8, a value of 4 for 42 looks derived, which is what
made guessing it dangerous: every input to that interpolation is a genuine
measurement and the output would not have been. ADR 0005 records the same
failure shape for the overclock exponent.

So the value being 4 settles nothing on its own, and the evidence that settles
it is deliberately of a different KIND from the arithmetic that would have
guessed it. Every actor rotation in a real body is a unit quaternion. At shift
4, all 17763 actors of the one real header-13 body give one; the runner-up
shift scores 1027 and drops to 2 once scale plausibility is included; and the
false-accept mode - a shift that produces unit-norm garbage - was constructed
and shown not to obtain. That is a measurement, not a neighbour's value.

A version with no measured delta still RAISES :class:`UnsupportedSaveVersionError`;
it never defaults. The refusal is EAGER, before a single record is read,
matching ``header.py``'s version prologue. A check placed after the walk would
never fire on a save of an unmeasured version whose object table happens to be
empty, and would fire only once a populated one arrived - a version-dependent
time bomb rather than a version check.

THE CORPUS IS n=1 FOR THIS PAIR. One header-13 save exists on this machine, so
every count behind it is a property of one artifact until a second appears.

UNKNOWN CLASSES ARE THE RELEASE VALVE (non-negotiable 7, BOOTSTRAP.md section 9)
---------------------------------------------------------------------------------
A class path the supplied registry does not model is recorded in
:attr:`ObjectTable.unknown_classes` with a count and a fixed reason, its
property payload is skipped, and **the walk continues to the end of the
table**. :attr:`ObjectTable.contains_unmodeled_content` then reports that the
world holds content this project does not model. Partial coverage is a flagged,
visible state - never a failure and never a silently wrong number. That single
decision is what makes mod tolerance nearly free: a namespaced ``/Mods/`` path
takes the ordinary route and no mod-specific branch exists.

A registry is OPTIONAL, and its absence claims nothing. ``cached_usmap()``
returns None on a machine with no install, and a walk that responded by
flagging every class would report a world of pure unknown content rather than a
world it has not checked. ``known_classes=None`` therefore flags nothing.

WHAT IS MEASURED HERE AND WHAT IS NOT, STATED PLAINLY
-------------------------------------------------------
Measured, and exercised by the corpus: the prefix widths, the record table
grammar for an actor, and the transform deltas for save versions 36, 52 and 60.

NOT measured, and deliberately not invented:

0. **Where the record table actually STARTS in a real body.** CLOSED FOR ALL
   FOUR REAL PAIRS by CS-407, and the answer was not an offset. A real body
   carries no single record table: it opens with a version-dependent preamble
   and then holds a LIST OF LEVELS, each with its own table, collectable list
   and payload section. :func:`parse_body` walks that layout and lands on the
   exact final byte of every real save on this machine.

   :func:`parse_object_headers` still reads the FLAT layout the corpus fixtures
   are built on, unchanged, because it is a consumed public surface and those
   fixtures pin dispatch and offset arithmetic. What changed is the claim it
   carries: passing against the flat corpus is evidence about dispatch and is
   NOT evidence that anything can read a save.

   **A RECORDED REASON HERE WAS WRONG, AND IS CORRECTED RATHER THAN DELETED.**
   This docstring previously declined save version 42's delta of 4 on the
   grounds that the reading "holds only if that version's declared
   header-section size also excludes the collectable count, which both
   neighbouring versions contradict" - two unmeasured assumptions holding each
   other up. THAT OBJECTION IS REFUTED. The grammar it describes was run
   against the real body and stops inside the FIRST level. The declared
   header-section size INCLUDES the collectable block in all 301 levels that
   have one; the other 1943 levels simply have NO BLOCK AT ALL. One thing
   changed, not two, and the old objection is exactly what falls out of
   assuming the block is mandatory - which it is on save 36, where all 202
   levels carry one, and is not anywhere else.

   The delta itself is now measured by a corroborator independent of section
   arithmetic entirely: every actor rotation is a unit quaternion, and 17763 of
   17763 actors read as unit quaternions at shift 4.

1. **The object DATA section.** LOCATED AND ATTRIBUTED. Its framing was
   measured by CS-407 - each level's data section is a count followed by that
   many length-framed payloads, and :func:`_check_section` proves those extents
   tile the section to its exact declared byte on all four real pairs. CS-413
   then settled the remaining question, which was never the framing but the
   ALIGNMENT: WHICH record each payload belongs to.
   :attr:`ObjectRecord.body_offset` and :attr:`ObjectRecord.body_length` now
   carry it, from :func:`parse_body` only - the flat walk leaves them 0,
   because the flat shape is one no real body has.

   THE k-TH PAIRING IS MEASURED, NOT ASSUMED, and the distinction is the whole
   point of the item. An actor's payload opens with its component reference
   list, and each reference names a component record whose own ``parent`` field
   points back at that actor - so the record table and the data section are
   parsed INDEPENDENTLY and then checked against each other. Across all 14 real
   saves the k-th alignment satisfies that cross-check on 9838 of 9838 testable
   actors and both neighbouring alignments satisfy it on 0. The corpus cannot
   corroborate any of this: the payloads in its parametrized matrices are
   filler, so they pin the tiling arithmetic and nothing about the grammar.

   Where a level's entry count and record count disagree the pairing is
   UNDEFINED, so none is invented - the level is flagged with
   :data:`WARN_PAYLOAD_COUNT_DISAGREEMENT` and its records keep 0. Every level
   of every real save on this machine agrees, so that branch is reached by no
   real save and is covered by a body built for it in the test module.
2. **The component record grammar.** MEASURED by CS-407, and the belief
   recorded here previously was right: a component carries a parent path where
   an actor carries its filler and transform block. :func:`_read_levelled_record`
   implements that split and populates :attr:`ObjectRecord.parent`.
   :func:`_read_record`, which serves the flat corpus, still reads the actor
   shape under either discriminator - correct for those fixtures, which encode
   both kinds identically, and wrong for a real body, which is exactly why the
   levelled walk does not share it.
3. **Property VALUE decoding.** PARTIAL, and the partial is recorded as data
   rather than as an adjective. :func:`read_properties` resolves a class path
   to a usmap schema and DECODES every value whose type is in
   :data:`MEASURED_VALUE_TYPES`. Every other type is flagged and skipped, and
   the regions still opaque are named in :data:`UNMEASURED_PAYLOAD_REGIONS`
   with what is pinned and what is not claimed about each - so a later slice
   executes against that table instead of re-deriving it.

   TWO LIMITS ARE WORTH STATING AT THE TOP, because both are easy to misread
   as closed. The PROPERTY walk - not the body walk, which is boundary-exact
   and asserted so against every real save - is TERMINATOR-exact: a variable
   trailing run follows the property terminator on every payload of the three
   pairs this grammar reads, and it is the ``trailing_run`` entry of that
   table. It is NOT every payload in the library, and the next sentence is
   why: the (14,60) pair reads under this grammar on NO payload at all, so it
   reports exactly what it reported before any of this landed.

An unrecognised object-type discriminator is refused rather than skipped, and
that is not a contradiction of non-negotiable 7. That rule covers unknown
CONTENT - a class this project does not model - which can be flagged and
stepped over because the record around it is still readable. A record whose
GRAMMAR is unknown carries no length, so there is nothing to step over and no
way to resume; guessing the actor grammar for it would desynchronise the rest
of the table silently.

THE ERROR TAXONOMY IS A PRIVACY CONTROL, NOT A STYLE
------------------------------------------------------
A save BODY is personal-data-bearing: it holds the world's contents and its
actor names. Non-negotiable 12 therefore makes every exception an echo path.
An error raised here may carry ONLY a field name drawn from :data:`FIELD_NAMES`,
a byte offset, an expected/actual length or count, a version scalar and a fixed
``REASON_*`` string. Never raw bytes, never a decoded string, never a hex
preview, never a path - paths go through ``clockspeed.data.locate.redact()``,
and this module never handles one.

The same discipline covers ``__repr__``. :class:`ObjectRecord` and
:class:`ObjectTable` render structure and withhold every string they carry,
because a test runner and most loggers repr an object before a human chooses
what to print, and the safe rendering has to stay safe even when the parse is
wrong.

FLOATS ARE LEGAL HERE, AND NECESSARY
--------------------------------------
Non-negotiable 6 bans floats from the SOLVE path, and the static AST gate's
pinned module set is the solve package. An actor transform is genuinely float32
on the wire; encoding it as anything else would be a reader that lies about the
format.
"""

from __future__ import annotations

import struct
from collections.abc import Collection, Container, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from clockspeed.save.usmap import PropertyMap

__all__ = [
    "BODY_LAYOUT_BY_PAIR",
    "BYTE_ORDER_ANCHORED_NOT_UNIQUE",
    "BYTE_ORDER_ORACLE_CANNOT_SEPARATE",
    "BYTE_ORDER_STATUSES",
    "BYTE_ORDER_SURVIVING_CANDIDATES",
    "BYTE_ORDER_UNSCORED",
    "BYTE_ORDER_VACUOUS",
    "COMPLETE_TYPE_NAME_PAIRS",
    "CONTAINER_ADJACENT_OWNERS",
    "CONTAINER_TYPE_WORDS",
    "CONTAINER_WORDS_WITHOUT_ELEMENT_GRAMMAR_EVIDENCE",
    "CRITERION_CURSOR_REACH",
    "CRITERION_VALUE_DISAGREEMENT",
    "CURSOR_WIDTHS",
    "DECLINED_VALUE_READINGS",
    "ELEMENT_SHAPES",
    "ELEMENT_SHAPE_SELF_DELIMITING",
    "ELEMENT_SHAPE_SOLVED_WIDTH",
    "ELEMENT_SHAPE_UNIFORM_WIDTH",
    "EVIDENCE_CROSS_SECTION",
    "EVIDENCE_DECLARED_WIDTH",
    "EVIDENCE_FOR_VALUE_TYPE",
    "EVIDENCE_MAGNITUDE",
    "EVIDENCE_REDUNDANCY",
    "EXTENT_WIDTHS",
    "FIELD_NAMES",
    "GUID_BYTES",
    "INVENTORY_ITEM_STRUCT_WORD",
    "ITEM_FORM_AMBIGUOUS",
    "ITEM_FORM_UNCLOSED",
    "ITEM_REFUSAL_REASONS",
    "ITEM_STATE_UNDECODED",
    "KIND_ACTOR",
    "KIND_COMPONENT",
    "LEVEL_TAIL_NONE",
    "LEVEL_TAIL_SUMMARY",
    "LEVEL_TAIL_WORD",
    "MAX_BODY_REFERENCES",
    "MAX_CUSTOM_VERSIONS",
    "MAX_GRIDS",
    "MAX_LEVELS",
    "MAX_LEVEL_TAIL_ENTRIES",
    "MAX_OBJECTS",
    "MAX_OBJECT_DATA_BYTES",
    "MAX_STRING_BYTES",
    "MAX_STRUCT_DEPTH",
    "MEASURED_BODY_LAYOUTS",
    "MEASURED_HEADER_VERSIONS",
    "MEASURED_TAG_FLAG_MASK",
    "MEASURED_VALUE_TYPES",
    "PAYLOAD_TAG_LEAD_BYTES",
    "REASON_NO_DISCRIMINATION_TEST",
    "REASON_SAMPLE_SIZE",
    "REASON_SHIPPED_ALIGNMENT_ONLY",
    "REFERENCE_COUNT_COMMON_MODE",
    "REFERENCE_TYPE_WORD",
    "STRUCT_FORMS_READ",
    "STRUCT_FORM_NATIVE",
    "STRUCT_FORM_TAG_LIST",
    "STRUCT_TYPE_WORD",
    "TRANSFORM_BYTES",
    "TRANSFORM_DELTA_BY_SAVE_VERSION",
    "TRANSFORM_FLOAT_COUNT",
    "UNDISCRIMINATED_ELEMENT_SHAPES",
    "UNKNOWN_CLASS_REASONS",
    "UNMEASURED_PAYLOAD_REGIONS",
    "UNRESOLVED_ASSET_SHAPED",
    "UNRESOLVED_EMPTY_PATH",
    "UNRESOLVED_SAVE_OBJECT_SHAPED",
    "UNRESOLVED_SHAPES",
    "VALUE_BYTE_ORDER_STATUS",
    "VALUE_READING_CRITERIA",
    "WARN_BODY_LENGTH_DISAGREEMENT",
    "WARN_MEASURED_VALUE_DISAGREED",
    "WARN_PAYLOAD_COUNT_DISAGREEMENT",
    "WARN_RESERVED_WORD_SET",
    "WARN_UNMEASURED_HEADER_VERSION",
    "WARN_UNMEASURED_PROPERTY_TYPE",
    "WARN_UNPARSED_DATA_SECTION",
    "WARN_UNPARSED_PROPERTY_PAYLOAD",
    "WARN_UNRESOLVED_SCHEMA",
    "WIDTH_CRITERIA",
    "WIDTH_NON_CRITERIA",
    "WIDTH_ONLY_VALUE_TYPES",
    "WIDTH_RULE_EXCEPTIONS",
    "WIDTH_SHIPPING_GROUNDS",
    "WIDTH_SHIPPING_RULE",
    "BodyLayout",
    "Collectable",
    "ContainerElement",
    "ContainerValue",
    "InventoryItem",
    "InventoryItemRefusal",
    "ItemList",
    "ItemListEntry",
    "ObjectBudgetExceededError",
    "ObjectError",
    "ObjectFormatError",
    "ObjectRecord",
    "ObjectReference",
    "ObjectTable",
    "ObjectTruncatedError",
    "ObjectWarning",
    "PropertyResult",
    "RecordIndex",
    "ReferenceList",
    "ReferencePair",
    "ReferenceResolution",
    "RunReference",
    "StructValue",
    "TrailingRun",
    "Transform",
    "UnknownClass",
    "UnsupportedBodyLayoutError",
    "UnsupportedSaveVersionError",
    "class_name_of",
    "classify_unresolved",
    "container_candidate_words",
    "decode_struct_interior",
    "derive_buildable_group_classes",
    "derive_item_list_classes",
    "derive_reference_list_classes",
    "derive_reference_pair_classes",
    "derive_zero_remainder_classes",
    "index_records",
    "parse_body",
    "parse_object_headers",
    "parse_properties",
    "read_buildable_group_list",
    "read_inventory_item",
    "read_item_list",
    "read_properties",
    "read_reference_list",
    "read_reference_pair",
    "read_trailing_run",
    "read_zero_remainder",
    "resolve_references",
    "uses_complete_type_name",
]

# ---------------------------------------------------------------------------
# Measured layout constants
#
# ADR 0003 owns the transform deltas and ADR 0007 plus BOOTSTRAP.md section 2.4
# own the prefix widths. They are transcribed here rather than imported from
# the test corpus, matching chunks.py: sharing the constant would make the
# suite a restatement of this module's own opinion instead of a check on it.
# tests/save/test_objects.py cross-checks the two transcriptions, which is the
# only evidence that neither slice mistyped the table.
# ---------------------------------------------------------------------------

HEADER_VERSION_10: Final = 10
HEADER_VERSION_13: Final = 13
HEADER_VERSION_14: Final = 14

#: The header versions with a measured body layout. A version outside the set
#: is FLAGGED rather than refused, matching chunks.py: ADR 0007 decision item 3
#: records that the key the framing follows is undetermined, so refusing here
#: would assert a claim the ADR declines to make.
MEASURED_HEADER_VERSIONS: Final = (HEADER_VERSION_10, HEADER_VERSION_13, HEADER_VERSION_14)

#: From this header version the body opens with an int64 length rather than an
#: int32. CORRECTED under CS-404: header 10 carries an int32, not nothing.
HEADER_VERSION_WITH_WIDE_PREFIX: Final = HEADER_VERSION_13

BODY_PREFIX_WIDTH_WIDE: Final = 8
BODY_PREFIX_WIDTH_NARROW: Final = 4

#: MEASURED. The width of the opaque run between the instance-name string and
#: the transform block, by SAVE version (ADR 0003).
#:
#: SAVE VERSION 42 WAS ADDED BY MEASUREMENT, NOT BY INTERPOLATION, and the
#: distinction matters because 4 is also what interpolation would have produced.
#: The evidence is independent of the section arithmetic that consumes the run:
#: every actor rotation in a real body is a unit quaternion, and at shift 4 all
#: 17763 actors of the one real header-13 body give one. The runner-up shift
#: scores 1027 and falls to 2 once scale plausibility is included, and the
#: false-accept mode was constructed and shown not to obtain.
#:
#: IT IS NOT FILLER, despite reading like it. On the (14,52) corpus the run
#: takes 8 distinct values with only bits 3, 6, 19, 21 and 32 ever set - a bit
#: mask rather than an integer - and on (13,42) it is valued 0 in 11775 records
#: and 1 in 5988. Only its WIDTH is read here; see the module docstring for why
#: it is never split into named fields.
TRANSFORM_DELTA_BY_SAVE_VERSION: Final[Mapping[int, int]] = MappingProxyType(
    {36: 4, 42: 4, 52: 8, 60: 8}
)

#: Rotation (4) + translation (3) + scale (3), all float32.
TRANSFORM_FLOAT_COUNT: Final = 10
TRANSFORM_BYTES: Final = TRANSFORM_FLOAT_COUNT * 4

KIND_ACTOR: Final = "actor"
KIND_COMPONENT: Final = "component"

#: The object-type discriminator values with a measured meaning. Anything else
#: is an unknown GRAMMAR and is refused - see the module docstring.
_KIND_BY_OBJECT_TYPE: Final[Mapping[int, str]] = MappingProxyType(
    {0: KIND_COMPONENT, 1: KIND_ACTOR}
)

INT32_SIZE: Final = 4
INT64_SIZE: Final = 8

#: A negative string count selects UTF-16-LE and its magnitude is a CHARACTER
#: count, so the byte count is twice it. A parser treating the magnitude as
#: bytes reads half the string and lands mid-field.
UTF16_CHAR_SIZE: Final = 2

#: The smallest a record can possibly be, before its save-version delta: the
#: object type, three empty strings at four bytes each, the transform block and
#: the trailing int32. Used to refuse an impossible declared count early.
_MINIMUM_RECORD_BYTES: Final = INT32_SIZE * 5 + TRANSFORM_BYTES

# ---------------------------------------------------------------------------
# Stated resource ceilings
#
# Every one is a REFUSAL BOUND applied to a DECLARED value before any
# allocation. A save is untrusted binary input and an unbounded declared length
# read out of one is the whole attack.
# ---------------------------------------------------------------------------

#: Ceiling on the declared record count. A large built world is a few hundred
#: thousand objects, so this is generous against the measurement and finite.
MAX_OBJECTS: Final = 1 << 20

#: Ceiling on any single declared string length, matching header.py.
MAX_STRING_BYTES: Final = 16_384

#: Ceiling on the declared LEVEL count in the levelled layout. The measured real
#: body carries 201 named levels; this is generous against that and finite.
MAX_LEVELS: Final = 1 << 16

#: Ceiling on one object payload's declared BYTE LENGTH. Distinct from
#: :data:`MAX_OBJECTS` on purpose - that one bounds a COUNT of records, and
#: reusing it here is a category error that a synthetic fixture cannot expose.
#: The measured real body carries a single payload of 1056207 bytes, just over
#: the count ceiling, so the first real save this walk ever saw refused itself.
MAX_OBJECT_DATA_BYTES: Final = 1 << 26

# ---------------------------------------------------------------------------
# The body SKELETON grammar, per pair
#
# READ THE WORD SKELETON. Landing on a body's exact final byte proves the
# FRAMING is right; it does not mean the body is understood. Roughly three
# quarters of every real body is opaque property payload this grammar steps
# over by declared length - 69.5% to 77.7% across the eight real (14,52) files,
# and 12100463 of 18086289 bytes on the one real (13,42) file. What is named
# below is a 1.8% to 2.7% skeleton plus its length-prefixed strings. Adding
# pairs does not change that ratio, so "the body grammar is closed" never
# becomes a true sentence; "the body SKELETON grammar is closed" already is.
#
# THE KEY IS THE PAIR, AND THE KEY IS UNDETERMINED. Header version, save
# version and build changelist are all PERFECT predictors of every difference
# in this table, because each header version occurs with exactly one set of
# save versions across the whole real library. Nothing separates them, so this
# module keys on the PAIR and claims no key - the same undetermined keying
# ADR 0007 records for the chunk marker. Writing "save 36 uses 4-byte sizes"
# would assert a key the evidence does not support, and lines 19-22 above
# record that this exact mistake was made once already, under CS-404.
# ---------------------------------------------------------------------------

#: A named level closes on nothing after its data section.
LEVEL_TAIL_NONE: Final = "none"

#: A named level closes on one int32. Position and width only; no meaning.
LEVEL_TAIL_WORD: Final = "word"

#: A named level closes on an opaque word, a COUNTED LIST OF STRING PAIRS,
#: a second opaque word, and then a package summary.
#:
#: THE LIST READ AS 12 CONSTANT BYTES UNTIL CS-482, and the reason it did is
#: the reason it is spelled out here: it declares zero entries on 1522 of the
#: 1525 real (14,60) level tails on the machine this was measured against, so
#: the count and the two words around it are twelve zero bytes on all but
#: three. A save carrying one entry desynchronises a 12-byte reader by 80
#: bytes and the walk then takes the package summary's custom-version count
#: out of the middle of a string.
LEVEL_TAIL_SUMMARY: Final = "summary"

#: CONSTANT BLOBS, SKIPPED BY LENGTH, exactly as BOOTSTRAP.md already does for
#: the 28-byte header tail. NO INTERIOR BOUNDARY IN ANY OF THESE IS OBSERVABLE,
#: so none is claimed and none is decoded.
#:
#: THE 70-BYTE RUN USED TO STAND HERE AND IT WAS THE PARAGRAPH'S BEST
#: EXAMPLE. It is gone, for the same reason and by the same evidence as the
#: level tail below it: an interior boundary IS observable in it. The run is
#: a string, 22 opaque bytes and a second string, which tiles 4 + 22 + 44 to
#: exactly 70 when the two declare 0 and 40 - which they do on all 1530
#: summaries of the five real (14,60) saves, and which is why searching for a
#: split among FIXED widths found none. The second string's terminator lands
#: on +69 and the count on +70, so the tiling has no slack anywhere. What the
#: old search DID establish stands: the count's position at +70 and the
#: 20-byte entry width are the unique survivors over F in [0,84) x K in
#: [1,256], and +70 is where this reading also puts the count.
#:
#: THE LESSON IS THE ONE CS-482 PAID FOR TWICE. A run every save in a corpus
#: fills identically is not a constant; it is a field nothing has varied yet,
#: and the two are indistinguishable from inside the corpus. Only the second
#: value tells them apart, and it arrives as a desynchronised walk.
#:
#: ONE SPAN LEFT THIS LIST RATHER THAN JOINING IT, and it is the reason to
#: distrust the paragraph above. The level tail was a 12-byte member here on
#: exactly the same grounds - no observable interior - until a save arrived
#: whose tail was not 12 bytes long. Its interior was observable all along and
#: no save in the corpus had exercised it, which is a different condition from
#: unfalsifiable and reads identically from inside. What survives here are the
#: two 4-byte words that bracket the tail's entry list, and a 4-byte word has
#: no interior to claim anything about.
_PACKAGE_SUMMARY_MIDDLE_BYTES: Final = 22
_CUSTOM_VERSION_ENTRY_BYTES: Final = 20
_LEVEL_TAIL_LEAD_BYTES: Final = 4
_LEVEL_TAIL_TRAILING_BYTES: Final = 4
_GRID_OPAQUE_BYTES: Final = 8
_GRID_CELL_OPAQUE_BYTES: Final = 4
_COMPONENT_PRE_WORD_BYTES: Final = 4

#: Ceiling on a declared grid or custom-version count, applied before any loop.
MAX_GRIDS: Final = 1 << 12
MAX_CUSTOM_VERSIONS: Final = 1 << 12

#: Ceiling on a level tail's declared entry count. A REFUSAL BOUND AND NOT A
#: MEASUREMENT: the library declares 0 on 1522 of its 1525 (14,60) level
#: tails and 1 on the other three, so nothing measured here is evidence for
#: this number. It is set at the same order as the other two so that a
#: desynchronised walk is refused where it reads a garbage count rather than
#: allocating against one.
MAX_LEVEL_TAIL_ENTRIES: Final = 1 << 12

#: Ceiling on the body's trailing reference count. A REFUSAL BOUND AND NOT A
#: MEASUREMENT, on the same terms as :data:`MAX_LEVEL_TAIL_ENTRIES`: the library
#: declares 0 on seventeen of its twenty saves and 1 on the other three, so
#: nothing measured here is evidence for this number. Set at the same order as
#: its neighbours so a desynchronised walk is refused where it reads a garbage
#: count rather than allocating against one.
MAX_BODY_REFERENCES: Final = 1 << 12


@dataclass(frozen=True)
class BodyLayout:
    """Every way one measured pair's body skeleton differs from another's.

    Attributes:
        transform_delta: Width of the opaque run before an actor's transform
            block. Keyed here on the PAIR; :data:`TRANSFORM_DELTA_BY_SAVE_VERSION`
            keys the same measurement on the save version for the flat walk,
            and a test cross-checks that the two agree on every pair.
        section_size_width: 4 or 8. An 8-byte size is read as an int32 size
            plus a named reserved int32 - see :func:`_read_section_size`.
        package_summary: The body opens with a package summary.
        grid_preamble: The body carries the grid block before the level count.
        data_entry_lead: Opaque bytes before each payload's length prefix.
        data_entry_trailer: Each payload is followed by an int32.
        component_pre_word: A component carries 4 opaque bytes before its
            parent path.
        level_tail: One of the ``LEVEL_TAIL_*`` constants, NAMED levels only.
        second_collectables_named: Named levels close with a second collectable
            block. The persistent level always does.
    """

    transform_delta: int
    section_size_width: int
    package_summary: bool
    grid_preamble: bool
    data_entry_lead: int
    data_entry_trailer: bool
    component_pre_word: bool
    level_tail: str
    second_collectables_named: bool


#: MEASURED (CS-407). The ``(header version, save version)`` pairs whose whole
#: body SKELETON has been derived - meaning a real body of that pair walks to
#: its exact final byte with nothing left over - and the grammar each uses.
#:
#: Landings behind this table: (10,36) 3 of 3 real files exact, (13,42) 1 of 1,
#: (14,52) 8 of 8, (14,60) 2 of 2.
#:
#: THOSE ARE FILE COUNTS, NOT INDEPENDENCE COUNTS, and the difference is large.
#: (13,42) is ONE file. (14,60)'s two bodies are byte-identical from offset 4
#: through 150074, which is exactly the persistent level's first byte, so the
#: package summary, the grid block, the level tail and all 187 named levels are
#: n=1 and only the persistent level's contents are genuinely n=2. (14,52)'s
#: eight files share a byte-identical 69750-byte preamble - it is the static
#: world-partition grid, so n=1 there is a CEILING that more saves of this world
#: cannot raise - they collapse to six distinct structural signatures, and the
#: entire no-header-block branch lives in ONE of them.
#:
#: Adding a pair here is a MEASUREMENT against a real save, never an
#: interpolation from a neighbour, and it is added in both transcriptions at
#: once - here and in ``tests/save/synthetic.py``.
BODY_LAYOUT_BY_PAIR: Final[Mapping[tuple[int, int], BodyLayout]] = MappingProxyType(
    {
        (HEADER_VERSION_10, 36): BodyLayout(
            transform_delta=4,
            section_size_width=INT32_SIZE,
            package_summary=False,
            grid_preamble=False,
            data_entry_lead=0,
            data_entry_trailer=False,
            component_pre_word=False,
            level_tail=LEVEL_TAIL_NONE,
            second_collectables_named=True,
        ),
        (HEADER_VERSION_13, 42): BodyLayout(
            transform_delta=4,
            section_size_width=INT64_SIZE,
            package_summary=False,
            grid_preamble=True,
            data_entry_lead=INT64_SIZE,
            data_entry_trailer=False,
            component_pre_word=False,
            level_tail=LEVEL_TAIL_NONE,
            second_collectables_named=True,
        ),
        (HEADER_VERSION_14, 52): BodyLayout(
            transform_delta=8,
            section_size_width=INT64_SIZE,
            package_summary=False,
            grid_preamble=True,
            data_entry_lead=INT64_SIZE,
            data_entry_trailer=False,
            component_pre_word=True,
            level_tail=LEVEL_TAIL_WORD,
            second_collectables_named=True,
        ),
        (HEADER_VERSION_14, 60): BodyLayout(
            transform_delta=8,
            section_size_width=INT64_SIZE,
            package_summary=True,
            grid_preamble=True,
            data_entry_lead=INT64_SIZE,
            data_entry_trailer=True,
            component_pre_word=True,
            level_tail=LEVEL_TAIL_SUMMARY,
            second_collectables_named=False,
        ),
    }
)

#: The pairs :func:`parse_body` will walk. Derived from the table above so the
#: set and the grammar cannot drift apart.
MEASURED_BODY_LAYOUTS: Final = frozenset(BODY_LAYOUT_BY_PAIR)

# ---------------------------------------------------------------------------
# The closed field vocabulary
#
# The one error parameter allowed to be text. Pinning it to a fixed set means
# no raise site - including one written later - can smuggle a value decoded out
# of the body into a message through it.
# ---------------------------------------------------------------------------

FIELD_NAMES: Final = frozenset(
    {
        "body_length",
        "object_count",
        "object_table",
        "object_type",
        "type_path",
        "root_object",
        "instance_name",
        "transform_delta",
        "transform",
        "was_placed_in_level",
        "save_version",
        "property_payload",
        # The levelled layout (CS-407).
        "body_layout",
        "level_count",
        "level_name",
        # The body's trailing counted reference list (CS-867). It was
        # "level_trailer", an opaque int32 nothing claimed to understand, until
        # three real saves declared it non-zero.
        "body_reference_count",
        "body_reference",
        "header_section",
        "object_data_section",
        "object_data",
        "collectable_count",
        "collectable",
        "parent_object_root",
        # The three further pairs (CS-407 wave 2). Every one of these names a
        # span that is SKIPPED BY LENGTH, not decoded.
        "section_size_reserved",
        "package_summary",
        "custom_version_count",
        "custom_version",
        "grid_count",
        "grid_name",
        "grid_opaque",
        "grid_cell_count",
        "grid_cell_name",
        "grid_cell_opaque",
        "object_data_lead",
        "object_data_trailer",
        "component_pre_word",
        "level_tail",
        # The level tail's entry list (CS-482).
        "level_tail_count",
        "level_tail_entry",
    }
)

# ---------------------------------------------------------------------------
# Fixed reason strings
#
# Every raised message is built from one of these. A test collects them from
# this module and asserts each raised reason is a member, which proves
# mechanically that no decoded body content can reach an exception message.
# ---------------------------------------------------------------------------

REASON_SHORT_BUFFER: Final = "extends past the end of the supplied body"
REASON_DECLARED_LENGTH_ABOVE_CAP: Final = "declares a length above the stated cap"
REASON_NEGATIVE_COUNT: Final = "declares a count below zero, which no table can carry"
REASON_ABOVE_CEILING: Final = "exceeds the stated ceiling for this field"
REASON_UNMEASURED_OBJECT_TYPE: Final = (
    "names an object-type discriminator with no measured record grammar"
)
REASON_UNMEASURED_TRANSFORM_DELTA: Final = (
    "has no measured transform delta, and a delta is never interpolated from its neighbours"
)
REASON_UNDECODABLE_TEXT: Final = "declares text that is not decodable"
REASON_CLASS_NOT_MODELLED: Final = "is not a class the supplied registry models"
#: WORDED AROUND THE CONSEQUENCE RATHER THAN THE MECHANISM, and that is not
#: vagueness (CS-440). Two conditions reach it - a schema whose own name did not
#: resolve, and a schema section that stopped mid-entry - and a sentence naming
#: either mechanism would be FALSE whenever the other one fired. That is CS-430
#: exactly: a flag that fires correctly beside a sentence that does not hold.
#: WHICH mechanism it was is recoverable, from the SUBJECT of the usmap warning
#: carried on ``world.WorldWarning`` for the same load.
REASON_REGISTRY_INCOMPLETE: Final = (
    "could not be checked against a complete registry: part of the supplied"
    " registry did not parse, so how much of the world it models is unknown"
)
REASON_UNMEASURED_BODY_LAYOUT: Final = (
    "names a header and save version pair whose body layout has not been measured,"
    " and a layout is never interpolated from another version's"
)
REASON_SECTION_SIZE_DISAGREEMENT: Final = (
    "declares a section size that disagrees with the bytes the section actually spans"
)

#: The reasons a class path can land in :attr:`ObjectTable.unknown_classes`.
#:
#: TWO, NOT ONE, AND THE SECOND IS WHY (CS-440). While
#: :data:`REASON_CLASS_NOT_MODELLED` was the only member, a class the registry
#: DOES model - but whose schema was dropped because its own name did not
#: resolve - was published under a sentence that is false for that input. The
#: warning fired correctly and the answer beside it was confidently wrong,
#: which is the "never silently wrong" half of non-negotiable 7 rather than the
#: "never fatal" half.
UNKNOWN_CLASS_REASONS: Final = frozenset({REASON_CLASS_NOT_MODELLED, REASON_REGISTRY_INCOMPLETE})

# ---------------------------------------------------------------------------
# Warning codes and their fixed detail lines
# ---------------------------------------------------------------------------

WARN_UNMEASURED_HEADER_VERSION: Final = "unmeasured-header-version"
WARN_BODY_LENGTH_DISAGREEMENT: Final = "body-length-disagreement"
WARN_UNPARSED_DATA_SECTION: Final = "unparsed-data-section"
WARN_UNRESOLVED_SCHEMA: Final = "unresolved-schema"
WARN_UNPARSED_PROPERTY_PAYLOAD: Final = "unparsed-property-payload"
WARN_RESERVED_WORD_SET: Final = "reserved-word-set"
WARN_PAYLOAD_COUNT_DISAGREEMENT: Final = "payload-count-disagreement"
WARN_UNMEASURED_PROPERTY_TYPE: Final = "unmeasured-property-type"
WARN_MEASURED_VALUE_DISAGREED: Final = "measured-value-disagreed"

_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_UNMEASURED_HEADER_VERSION: (
            "the header version is outside the measured set, so the body length prefix "
            "width was taken from the nearest measured rule rather than from a measurement"
        ),
        WARN_BODY_LENGTH_DISAGREEMENT: (
            "the body length prefix disagrees with the bytes that follow it; the walk "
            "followed the bytes present rather than the declaration"
        ),
        WARN_UNPARSED_DATA_SECTION: (
            "bytes remain after the walk and were not read; the flat record table has "
            "no measured data section, and a levelled body reaching this has ended "
            "somewhere the grammar does not account for"
        ),
        WARN_UNRESOLVED_SCHEMA: (
            "the class path does not resolve to a schema in the supplied property map, "
            "so its property payload was skipped"
        ),
        WARN_UNPARSED_PROPERTY_PAYLOAD: (
            "the class resolved and its property payload was located, but no value in "
            "it was decoded; the value grammar is unmeasured and is never guessed at"
        ),
        WARN_RESERVED_WORD_SET: (
            "the second word of an 8-byte section size is non-zero, where every "
            "section measured carries zero; the low word was used as the size and "
            "the walk continued, so a section-size mismatch after this warning "
            "points at this field rather than at the section"
        ),
        WARN_PAYLOAD_COUNT_DISAGREEMENT: (
            "a level declared a different number of payload entries than it has "
            "records, so no payload was attributed to any record in it; the "
            "extents were still walked and the section still closed"
        ),
        WARN_UNMEASURED_PROPERTY_TYPE: (
            "the payload read, and some of its properties carry a type whose value "
            "encoding this project has not measured; those were skipped rather than "
            "guessed at, and the regions are named in UNMEASURED_PAYLOAD_REGIONS"
        ),
        WARN_MEASURED_VALUE_DISAGREED: (
            "the payload read, and some of its properties carry a type whose value "
            "encoding IS measured but whose bytes disagreed with the tag's declared "
            "size; those were skipped rather than published from an offset the walk "
            "may not be at. THIS IS NOT UNKNOWN CONTENT - it means the reader is not "
            "where it believes it is, so every value decoded after it in the same "
            "payload is suspect"
        ),
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


def _checked_field(name: str) -> str:
    """Confirm a field name is in the closed vocabulary before it enters a message.

    The static half of the taxonomy gate proves the parameter is a ``str``.
    This is the runtime half: it proves the ``str`` was drawn from
    :data:`FIELD_NAMES`, so the one parameter allowed to be text cannot smuggle
    a decoded value into an error message.

    Args:
        name: The candidate field name.

    Returns:
        ``name``, unchanged.

    Raises:
        ValueError: The name is not in :data:`FIELD_NAMES`. The message states
            the count of known names rather than echoing the rejected value,
            because the rejected value is exactly the thing under suspicion.
    """
    if name not in FIELD_NAMES:
        raise ValueError(
            f"field name is not one of the {len(FIELD_NAMES)} names this module may report"
        )
    return name


def _render(
    reason: str,
    field: str,
    offset: int,
    expected: int | None,
    actual: int | None,
    version: int | None,
) -> str:
    """Build the message from taxonomy fields only.

    Decimal throughout, deliberately. A hex rendering of an observed value is
    the exact shape non-negotiable 12 forbids, and a habit that reads as
    helpful here becomes a disclosure one layer up.

    Args:
        reason: One of the ``REASON_*`` constants.
        field: The field at fault, already checked.
        offset: The byte offset.
        expected: An expected length or count.
        actual: An observed or declared length or count.
        version: A version scalar.

    Returns:
        The rendered message.
    """
    parts = [f"save object field {field} at byte {offset} {reason}"]
    if expected is not None:
        parts.append(f"expected {expected}")
    if actual is not None:
        parts.append(f"got {actual}")
    if version is not None:
        parts.append(f"save version {version}")
    return "; ".join(parts)


class ObjectError(Exception):
    """Base class for every refusal this module raises.

    A plain :class:`Exception` rather than a :class:`ValueError`, matching
    ``chunks.py`` and ``clockspeed/data/docs_extract.py``: a caller wrapping a
    broad input handler around a save read should have to name this layer to
    swallow it.

    THE ATTRIBUTE SET IS A PRIVACY CONTROL. Non-negotiable 12 makes an
    exception an echo path for a personal-data-bearing artifact, so an instance
    carries only the five channels below plus the fixed reason, and a test pins
    the set with ``vars(exc)`` rather than trusting review.

    Attributes:
        reason: One of the module's ``REASON_*`` constants. Never built from
            body content.
        field: The field at fault, from :data:`FIELD_NAMES`. A name from this
            module's own vocabulary, never a value read from the body.
        offset: The byte offset the fault was found at.
        expected: An expected length or count, or None.
        actual: A declared or observed length or count, or None.
        version: A version scalar, or None.
    """

    def __init__(
        self,
        reason: str,
        *,
        field: str,
        offset: int,
        expected: int | None = None,
        actual: int | None = None,
        version: int | None = None,
    ) -> None:
        """Render a message from the taxonomy fields and nothing else.

        Args:
            reason: One of the ``REASON_*`` constants.
            field: The field at fault, from :data:`FIELD_NAMES`.
            offset: The byte offset.
            expected: An expected length or count.
            actual: An observed or declared length or count.
            version: A version scalar.
        """
        checked = _checked_field(field)
        super().__init__(_render(reason, checked, offset, expected, actual, version))
        self.reason = reason
        self.field = checked
        self.offset = offset
        self.expected = expected
        self.actual = actual
        self.version = version


class ObjectFormatError(ObjectError):
    """A field declared something structurally impossible.

    Distinct from a truncation on purpose. A truncation means the body is
    SHORT; this means the body declares nonsense, and the distinction decides
    whether a caller should suspect a partial write or a wrong format.
    """


class ObjectTruncatedError(ObjectError):
    """The body ended before a field this module needed was complete.

    Every read goes through the bounded cursor, so a truncation arrives here
    rather than as a :class:`struct.error` or an :class:`IndexError` carrying a
    fragment of the buffer.
    """


class ObjectBudgetExceededError(ObjectError):
    """A declared count exceeds a stated ceiling.

    Always raised on the DECLARED value, before the record loop and before any
    list is grown from it.
    """


class UnsupportedSaveVersionError(ObjectError):
    """The save version has no MEASURED transform delta.

    Raised EAGERLY, before any record is read. Interpolating a delta from
    measured neighbours is refused outright - see the module docstring.
    """


class UnsupportedBodyLayoutError(ObjectError):
    """The header and save version pair has no MEASURED whole-body layout.

    Raised EAGERLY by :func:`parse_body`, before a byte of the body is read.
    Three of the four real pairs land here today and that is the correct
    answer for them: a layout guessed from a neighbouring version produces a
    walk that is confidently wrong rather than one that fails, and every
    downstream module then gets written against it.
    """


# ---------------------------------------------------------------------------
# The models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Transform:
    """One actor's placement, exactly as the wire carries it.

    Float32 is the format's own type here and non-negotiable 6 is scoped to the
    solve path, so these are genuine floats rather than a lossy rendering of
    something else.

    Attributes:
        rotation: The rotation quaternion, in file order.
        translation: World coordinates.
        scale: Per-axis scale.
    """

    rotation: tuple[float, float, float, float]
    translation: tuple[float, float, float]
    scale: tuple[float, float, float]


@dataclass(frozen=True, repr=False)
class Collectable:
    """One entry of a level's collectable list - CS-1038.

    ``repr`` is hand written and withholds BOTH strings, on exactly the terms
    :class:`ObjectRecord` states: a level name and an actor instance name are
    world content, and a repr is an echo path under non-negotiable 12 just as
    much as a log line is.

    WHAT THE PAIR IS. The two halves have the shape the level tail and the
    body's trailing reference list already carry - a level name and an object
    inside it. The first half is PROVENANCE rather than inference: it is one of
    the level names the same walk read earlier in the same body.

    POLARITY, AND IT IS THE ONE THING A CONSUMER CAN GET BACKWARDS. The section
    records what HAS BEEN COLLECTED, so an entry names an actor that is no
    longer in the world. A field named for the complement would invert every
    consumer downstream of it, which is why the name here is the positive one.

    WHAT IS NOT CLAIMED. The reading is measured only in the sense that reading
    the block any other way stops the whole-body walk short of the final byte,
    and the polarity is supported rather than proved: measured on the pinned
    development world as counts only, ZERO of the entries name an instance the
    same walk found as a live record, which is what a collected actor looks
    like and is also consistent with other readings. No join is performed here;
    a consumer that wants one performs it against
    :attr:`ObjectRecord.instance_name`.

    Attributes:
        level_name: The pair's first string - a level name.
        instance_name: The pair's second string - an actor instance name, and
            the half a consumer joins on.
    """

    level_name: str
    instance_name: str

    def __repr__(self) -> str:
        """Render presence and withhold both strings.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(level_name={bool(self.level_name)}, "
            f"instance_name={bool(self.instance_name)})"
        )


@dataclass(frozen=True, repr=False)
class ObjectRecord:
    """One entry in the object record table.

    ``repr`` is hand written and withholds every string. A save body holds the
    world's contents and its actor names, and a repr is an echo path under
    non-negotiable 12 just as much as a log line is.

    Attributes:
        kind: :data:`KIND_ACTOR` or :data:`KIND_COMPONENT`, from the
            discriminator. The two read different record grammars, which is
            what :func:`_read_levelled_record` splits on - see item 2 of the
            module docstring for where that split came from.
        type_path: The class path, namespaced and mod tolerant, verbatim.
        root_object: The record's root object path.
        instance_name: The instance name, verbatim.
        transform: An ACTOR's placement, bound by
            :func:`_read_levelled_record` from the record's own transform
            block. None on a COMPONENT, which carries a parent path where an
            actor carries that block. Always present from
            :func:`parse_object_headers`, whose flat walk reads the actor shape
            under either discriminator.
        parent: A COMPONENT's parent object path, verbatim, bound by
            :func:`_read_levelled_record` from the record's own
            ``parent_object_root`` field. None on an ACTOR, which carries a
            transform block where a component carries this string; and None on
            every record :func:`parse_object_headers` returns, because the flat
            walk reads the actor shape under either discriminator and never
            binds it.
        object_type: The raw discriminator, carried rather than interpreted.
        was_placed_in_level: The trailing int32, carried verbatim.
        body_offset: Where this object's PROPERTY PAYLOAD begins in the body.
            Populated by :func:`parse_body` (CS-413); 0 from
            :func:`parse_object_headers`, whose flat shape carries no data
            section, and 0 in a level whose entry and record counts disagree.
        body_length: How many bytes that payload spans, on the same terms. A
            payload is never zero-length in any real save on this machine.
    """

    kind: str
    type_path: str
    root_object: str
    instance_name: str
    transform: Transform | None
    parent: str | None
    object_type: int
    was_placed_in_level: int
    body_offset: int
    body_length: int

    def with_payload(self, offset: int, length: int) -> ObjectRecord:
        """Return this record carrying the extent of its own property payload.

        WHY THIS IS SPELLED OUT RATHER THAN ``dataclasses.replace``. ADR 0007's
        write gate scans this package's AST for write-capable call sites by
        NAME, and ``replace`` is on that list because ``Path.replace`` is how an
        atomic write lands. The scanner cannot tell the two apart without
        resolving the binding, and the conservative reading is the right one for
        a gate whose whole job is refusing unproven writes - so the honest fix
        is to not reach for the name here, rather than to teach the gate an
        exception it would then carry forever.

        Args:
            offset: The payload's first byte in the body.
            length: The payload's declared extent.

        Returns:
            A new record; this one is frozen and is not mutated.
        """
        return ObjectRecord(
            kind=self.kind,
            type_path=self.type_path,
            root_object=self.root_object,
            instance_name=self.instance_name,
            transform=self.transform,
            parent=self.parent,
            object_type=self.object_type,
            was_placed_in_level=self.was_placed_in_level,
            body_offset=offset,
            body_length=length,
        )

    def __repr__(self) -> str:
        """Render structure and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(kind={self.kind!r}, "
            f"object_type={self.object_type}, "
            f"transform={'present' if self.transform is not None else 'absent'}, "
            f"body_offset={self.body_offset}, body_length={self.body_length})"
        )


@dataclass(frozen=True)
class UnknownClass:
    """One class path that did not resolve against the supplied registry.

    Unlike an exception, this IS the reporting channel: naming the class is its
    entire purpose, because BOOTSTRAP.md section 9 requires an explicit "this
    world contains content I do not model" rather than a quiet partial answer.

    "DID NOT RESOLVE" IS NOT "IS NOT MODELLED", and reading :attr:`reason` is
    the only way to tell which of the two this entry is (CS-440). A registry
    that lost part of itself while parsing is incomplete by an unknown amount,
    so for that load the stronger claim is unsupportable and every entry carries
    :data:`REASON_REGISTRY_INCOMPLETE` instead. Treating the two as one is the
    exact confusion this attribute exists to prevent.

    Attributes:
        type_path: The class path that did not resolve.
        count: How many records carried it. A world with two hundred unmodelled
            belts has one problem, not two hundred.
        reason: One of :data:`UNKNOWN_CLASS_REASONS`.
        first_index: The record index it was first seen at.
    """

    type_path: str
    count: int
    reason: str
    first_index: int


@dataclass(frozen=True)
class ObjectWarning:
    """Something worth reporting that is not worth failing over.

    Attributes:
        code: One of the module's ``WARN_*`` constants.
        detail: A fixed line, keyed by code. Never built from body content.
        offset: The byte offset the condition was noticed at.
        expected: An expected length or count, or None.
        actual: An observed length or count, or None.
    """

    code: str
    detail: str
    offset: int
    expected: int | None = None
    actual: int | None = None


@dataclass(frozen=True, repr=False)
class ObjectTable:
    """The walked record table, and everything noticed on the way.

    ``repr`` renders counts only, for the reason given on :class:`ObjectRecord`.

    Attributes:
        records: Every record, in file order.
        unknown_classes: Class paths the supplied registry did not model,
            aggregated with a count. Empty when no registry was supplied -
            absence of a registry claims nothing.
        warnings: Aggregated advisories, empty when nothing was noticed.
        declared_body_length: The length the body's own prefix declared.
        body_consumed: How many body bytes the record table accounted for.
            Less than ``declared_body_length`` when a data section followed.
        body_prefix_width: 8 on header versions 13 and 14, 4 on header 10.
        transform_delta: The filler width this save version dictates.
        save_version: The save version the walk was dispatched on.
        header_version: The header version the walk was dispatched on.
        level_count: How many LEVELS the walk consumed, the trailing persistent
            level included. 0 from :func:`parse_object_headers`, which reads a
            single flat table and knows nothing of levels. DEFAULTED so that
            adding it could not change the construction of any existing caller.
        collectables: Every collectable entry every level declared, FLAT and in
            file order - CS-1038. Empty from :func:`parse_object_headers`, which
            reads a single flat table and walks no collectable block at all;
            empty is therefore "this reader saw none", never "this world has
            none". :class:`Collectable` owns what a pair means and what is not
            claimed about it. DEFAULTED so that adding it could not change the
            construction of any existing caller.
    """

    records: tuple[ObjectRecord, ...]
    unknown_classes: tuple[UnknownClass, ...]
    warnings: tuple[ObjectWarning, ...]
    declared_body_length: int
    body_consumed: int
    body_prefix_width: int
    transform_delta: int
    save_version: int
    header_version: int
    level_count: int = 0
    collectables: tuple[Collectable, ...] = ()

    @property
    def contains_unmodeled_content(self) -> bool:
        """Whether the world holds content this project does not model.

        Returns:
            True when at least one class path went unresolved.
        """
        return bool(self.unknown_classes)

    def __repr__(self) -> str:
        """Render counts and scalars, and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(records={len(self.records)}, "
            f"levels={self.level_count}, "
            f"collectables={len(self.collectables)}, "
            f"unknown_classes={len(self.unknown_classes)}, "
            f"warnings={len(self.warnings)}, "
            f"save_version={self.save_version}, header_version={self.header_version}, "
            f"body_prefix_width={self.body_prefix_width}, "
            f"transform_delta={self.transform_delta})"
        )


@dataclass(frozen=True, repr=False)
class ObjectReference:
    """One decoded ``ObjectProperty`` value, carrying the tag it came from.

    ``repr`` is hand written and withholds every string, for the reason given
    on :class:`ObjectRecord`. ALL THREE FIELDS ARE WORLD CONTENT: the property
    name is read out of the save's own bytes, and the two halves of the value
    name a level and an object inside the player's world.

    WHY THE REFERENCE TRAVELS AS ITS OWN TYPE RATHER THAN AS A TUPLE IN
    :attr:`PropertyResult.properties`. The value map is keyed by property name
    and holds the decoded value, and a ``SoftObjectProperty`` decodes to a
    ``tuple[str, str]`` indistinguishable from this one. A consumer recovering
    references from that map by shape therefore takes both type words silently.
    Carrying the reference separately is what makes the population TYPED - see
    :data:`REFERENCE_TYPE_WORD` for what the other word was measured to do.

    Attributes:
        property_name: The tag's own name, as the payload spells it.
        level_reference: The value's first string. Carried rather than
            interpreted: it was measured to equal the named record's
            ``root_object`` on most of the local library's resolving
            references and to differ on some, so this module states no
            relation between the two.
        object_path: The value's second string. THIS IS THE JOIN KEY - it is
            matched against a record's ``instance_name``, which is the pairing
            the cross-section oracle grades.
    """

    property_name: str
    level_reference: str
    object_path: str

    def __repr__(self) -> str:
        """Render lengths only, and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(property_name_len={len(self.property_name)}, "
            f"level_reference_len={len(self.level_reference)}, "
            f"object_path_len={len(self.object_path)})"
        )


@dataclass(frozen=True, repr=False)
class PropertyResult:
    """What :func:`read_properties` could and could not do with one record.

    ``repr`` is hand written and withholds every string, for the reason given
    on :class:`ObjectRecord`. THAT BECAME LOAD-BEARING WHEN THIS TYPE STARTED
    CARRYING DECODED VALUES. While ``properties`` was empty on every return
    path the default repr was defensible; it is not now. The VALUES include
    player-authored strings and the KEYS are property names read out of the
    save's own bytes, so both halves of every entry are world content, and
    ``schema_name`` is a fragment of the class path :class:`ObjectRecord`
    already withholds. A test runner reprs a value before a human chooses what
    to print - pytest renders it as a frame local - so the safe rendering has
    to be the only one available.

    Attributes:
        properties: The decoded properties, by name. Carries values of the
            types in :data:`MEASURED_VALUE_TYPES` and NO OTHER - a type whose
            value encoding is unmeasured is absent here and counted in
            ``unmeasured_value_count`` instead, so an absent name never means
            "this property is not set". DECODED WORLD CONTENT: a caller that
            renders it is an echo path under non-negotiable 12.
        schema_name: The class name the type path resolved to.
        resolved: Whether the property map models that class at all. THREE
            STATES, AND THE THIRD IS NOT A SHADE OF THE SECOND. None means NO
            MAP WAS SUPPLIED, so nothing has been consulted and nothing is
            claimed - the state CI and every fresh clone are in, because
            ``usmap.cached_usmap()`` answers None with no game install. False
            means a map WAS supplied and does not model this class. Collapsing
            the two would report a world of unmodelled content on the strength
            of having looked at nothing, which is the same distinction
            ``known_classes=None`` already draws one layer up. NEITHER STATE
            GATES THE DECODE - see :func:`read_properties`.
        warnings: What was flagged and skipped.
        unmeasured_value_count: How many tags carried a type whose value
            encoding is unmeasured. DEFAULTED so that adding it could not
            change the construction of any existing caller.
        disagreeing_value_count: How many tags carried a type whose value
            encoding IS measured but whose bytes disagreed with the declared
            size. COUNTED APART FROM THE FIELD ABOVE because the two mean
            opposite things - see :func:`_decode_payload`. Non-zero here is a
            reason to distrust this record's other values; non-zero above is
            not. Defaulted for the same reason.
        references: The decoded :data:`REFERENCE_TYPE_WORD` values, ONE PER
            TAG and in tag order. A tuple rather than a mapping so that two
            tags sharing a name cannot collapse into one - ``properties``
            tolerates that collapse because a caller there asks by name, where
            a population may not lose a member and stay a population. DECODED
            WORLD CONTENT, on the same terms as ``properties``.
        reference_tag_count: How many :data:`REFERENCE_TYPE_WORD` TAGS the walk
            stepped over, whether or not each yielded a value. THE DENOMINATOR
            THE DECODER CANNOT SHRINK, and the reason the population is the tag
            rather than the successful decode: counting only what decoded would
            let a walk that has lost its place drop members instead of
            reporting them. IT IS NOT INDEPENDENT OF THE TWO FIELDS IT
            BOUNDS, and a sentence here said that it was.
            :func:`_walk_payload` moves this counter and the refusal inside one
            exhaustive if/else with nothing between them, so
            ``reference_tag_count == undecoded_reference_count +
            len(references)`` holds by construction on every iteration.
            Relating the three to one another therefore restates one number
            three ways. Relating this one to a tag total taken by some OTHER
            walk does not, and that is where it is graded.
        undecoded_reference_count: How many of those tags yielded no pair,
            because the two strings did not account for the declared size.
            Included in ``disagreeing_value_count`` as well, which counts the
            same condition across every measured type; this field narrows it to
            the reference population so the partition can be checked there.
        struct_interiors: One :class:`StructValue` per top-level struct tag
            whose interior READ, in tag order - CS-829. REPORTED APART FROM
            ``properties`` RATHER THAN INSIDE IT, and that is a claim about what
            is measured rather than a convenience. A struct word written as
            native raw bytes is not read here at all, so ``StructProperty`` is
            NOT in :data:`MEASURED_VALUE_TYPES` and a struct tag still counts in
            ``unmeasured_value_count`` exactly as it did before this slice.
            Putting the interior into ``properties`` would say the type's
            top-level value is measured, which for the native form is false.
            DECODED WORLD CONTENT, on the same terms as ``properties``.
        struct_tag_count: How many top-level struct TAGS the walk stepped over,
            whether or not each yielded an interior. THE DENOMINATOR THE
            DECODER CANNOT SHRINK, on the same terms as ``reference_tag_count``:
            an equality asserted over "the ones that decoded" holds by
            construction, and this is the population it has to stand in.
        trailing_run: The run between this payload's property terminator and
            its declared final byte, with the field it opens with READ - CS-828.
            None on a payload whose walk never reached a terminator, which is
            every payload of a pair outside :data:`TRAILING_RUN_PAIRS`. NOT
            WORLD CONTENT: three integers off the framing, carrying no string
            and no decoded value, which is why it is rendered in ``repr``
            below rather than withheld the way ``properties`` is.
        undecoded_names: The NAME of every tag counted in
            ``unmeasured_value_count`` or ``disagreeing_value_count`` - CS-1264.
            A DROPPED VALUE IS NOT A DROPPED TAG: without this a consumer asking
            whether a tag was PRESENT reads a torn or unmeasured tag exactly as
            an absent one, which is the silently-wrong half of non-negotiable
            7. NAMES ONLY - the value never decoded, so any reading of it would
            be invented. A set, because the question is presence by name and
            the two counts already carry how many. Empty on a walk that never
            reached its terminator, where no tag is known at all. Defaulted for
            the reason the counts are. WORLD CONTENT on the terms
            ``properties`` states: ``repr`` renders a count.
    """

    properties: Mapping[str, object]
    schema_name: str
    resolved: bool | None
    warnings: tuple[ObjectWarning, ...]
    unmeasured_value_count: int = 0
    disagreeing_value_count: int = 0
    references: tuple[ObjectReference, ...] = ()
    reference_tag_count: int = 0
    undecoded_reference_count: int = 0
    struct_interiors: tuple[StructValue, ...] = ()
    struct_tag_count: int = 0
    trailing_run: TrailingRun | None = None
    undecoded_names: frozenset[str] = frozenset()

    def __repr__(self) -> str:
        """Render counts and flags, and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(properties={len(self.properties)}, "
            f"resolved={self.resolved}, "
            f"warnings={len(self.warnings)}, "
            f"unmeasured_value_count={self.unmeasured_value_count}, "
            f"disagreeing_value_count={self.disagreeing_value_count}, "
            f"references={len(self.references)}, "
            f"reference_tag_count={self.reference_tag_count}, "
            f"undecoded_reference_count={self.undecoded_reference_count}, "
            f"struct_interiors={len(self.struct_interiors)}, "
            f"struct_tag_count={self.struct_tag_count}, "
            f"trailing_run={self.trailing_run}, "
            f"undecoded_names={len(self.undecoded_names)})"
        )


@dataclass(frozen=True, repr=False)
class RecordIndex:
    """A record table arranged so a reference can be followed to what it names.

    ``repr`` renders counts only, for the reason given on :class:`ObjectRecord`
    - the keys here are instance names read out of the save's own bytes.

    AN INSTANCE NAME IS NOT UNIQUE, and that is measured rather than assumed:
    the local library holds saves in which a name is borne by more than one
    record, with the same root object and the same kind at different payload
    offsets. So the index maps a name to EVERY record bearing it. A mapping to
    a single record would have to pick one, and picking silently turns an
    ambiguity into a wrong answer that reads like a right one.

    Attributes:
        records_by_name: Instance name to every record bearing it, each tuple
            in table order. WORLD CONTENT in both halves; a caller that renders
            it is an echo path under non-negotiable 12.
    """

    records_by_name: Mapping[str, tuple[ObjectRecord, ...]]

    @property
    def name_count(self) -> int:
        """How many distinct instance names the table carries.

        Returns:
            The count.
        """
        return len(self.records_by_name)

    @property
    def ambiguous_name_count(self) -> int:
        """How many names are borne by more than one record.

        Returns:
            The count. Non-zero is normal on this project's own library and is
            not an error - see the class docstring.
        """
        return sum(1 for found in self.records_by_name.values() if len(found) > 1)

    def records_for(self, object_path: str) -> tuple[ObjectRecord, ...]:
        """Follow one object path to the records bearing it.

        THE ACCESSOR IS TOTAL AND CONFLATES NOTHING. An empty tuple means no
        record bears the path, one means an unambiguous target, and more than
        one means the name is ambiguous. A single-record accessor returning
        None would have to spell "absent" and "ambiguous" the same way, which
        is the conflation :func:`_decode_payload` records one seam over.

        Args:
            object_path: A reference's second string.

        Returns:
            Every record whose instance name is that path, in table order.
        """
        return self.records_by_name.get(object_path, ())

    def __repr__(self) -> str:
        """Render counts only, and withhold every name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(names={self.name_count}, "
            f"ambiguous_names={self.ambiguous_name_count})"
        )


@dataclass(frozen=True, repr=False)
class ReferenceResolution:
    """How one record's references landed against the table, as a partition.

    ``repr`` renders counts only, for the reason given on :class:`ObjectRecord`
    - ``targets`` is keyed by property name and holds records.

    THE PARTITION IS A SHAPE, NOT A CHECK, AND A SENTENCE HERE SOLD IT AS A
    CHECK. ``resolved``, ``unresolved`` and ``undecoded`` do sum to ``total``,
    but they sum to it BY CONSTRUCTION rather than by agreement - see
    :func:`resolve_references` for the derivation - so a reference this module
    drops does not show up in that sum. What the three buckets buy is a stated
    landing place for every tag, and every tag having one is what
    non-negotiable 7 asks of a reader that meets content it cannot follow.
    UNRESOLVED IS THE EXPECTED CASE rather than a fault, and flagging it instead
    of failing is what non-negotiable 7 asks for.

    WHAT UNRESOLVED IS NOT IS ONE THING, AND A SENTENCE HERE SAID IT WAS -
    CS-833. It claimed that a reference naming nothing in the table names an
    ASSET, stated as a universal over the whole bucket. The library falsifies
    it. Members of the bucket carry a path in the SAME shape every resolving
    reference carries and are simply borne by no record in that save, and
    members carry no path at all - neither names an asset. The universal is
    withdrawn and replaced by a partition: :func:`classify_unresolved` sorts
    every member into one of :data:`UNRESOLVED_SHAPES`, and the three counts
    below are carried APART so no consumer has to take the gloss on trust. What
    is still true, and all that is claimed, is that the asset-shaped members are
    the bulk of it.

    Attributes:
        targets: Property name to the records that name resolved to. Resolved
            entries only - a name absent here either did not resolve or did not
            decode. WORLD CONTENT; rendering it is an echo path.
        resolved: References whose path is borne by at least one record.
        unresolved: References that decoded and matched no record. REFINED BY
            THE THREE COUNTS BELOW, which partition it.
        unresolved_asset_shaped: Of ``unresolved``, those whose path begins at
            the content-tree root - the shape a shipped asset carries.
        unresolved_save_object_shaped: Of ``unresolved``, those whose path is in
            the shape a SAVED OBJECT carries and which no record in this table
            bears. THE CLASS THE WITHDRAWN UNIVERSAL DENIED EXISTED.
        unresolved_empty_path: Of ``unresolved``, those carrying no path at all.
        undecoded: Reference TAGS whose bytes yielded no pair at all.
        ambiguous: How many of ``resolved`` landed on a path borne by more than
            one record. A subset of ``resolved`` and NOT a fourth bucket, so it
            is deliberately outside the sum.
        total: Every reference tag the walk stepped over.
    """

    targets: Mapping[str, tuple[ObjectRecord, ...]]
    resolved: int
    unresolved: int
    undecoded: int
    ambiguous: int
    total: int
    # DEFAULTED FOR THE REASON CS-830 DEFAULTED ITS OWN COUNTERS: adding a field
    # to a frozen dataclass that a caller builds by keyword must not break that
    # caller. A consumer predating CS-833 constructs six fields and gets three
    # zeroes, which is honest - it counted no shapes.
    unresolved_asset_shaped: int = 0
    unresolved_save_object_shaped: int = 0
    unresolved_empty_path: int = 0

    def __repr__(self) -> str:
        """Render counts only, and withhold every name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(targets={len(self.targets)}, "
            f"resolved={self.resolved}, unresolved={self.unresolved}, "
            f"unresolved_asset_shaped={self.unresolved_asset_shaped}, "
            f"unresolved_save_object_shaped={self.unresolved_save_object_shaped}, "
            f"unresolved_empty_path={self.unresolved_empty_path}, "
            f"undecoded={self.undecoded}, ambiguous={self.ambiguous}, "
            f"total={self.total})"
        )


# ---------------------------------------------------------------------------
# The bounded cursor
# ---------------------------------------------------------------------------


class _Cursor:
    """A bounds-checked forward reader over one body.

    Every read goes through :meth:`_require`, so there is no path that indexes
    the buffer without first having said how many bytes it needed and how many
    were there. That is what makes every truncation arrive as an
    :class:`ObjectTruncatedError` rather than as a struct error or an index
    error carrying a fragment of the body.
    """

    def __init__(self, data: bytes) -> None:
        """Start at offset zero.

        Args:
            data: The body. Never copied wholesale, never echoed.
        """
        self._data = data
        self.offset = 0

    def __repr__(self) -> str:
        """Withhold the body, deliberately and structurally.

        THE SIBLING OF ``header._Cursor.__repr__``, AND FOUND BY THE ARM RATHER
        THAN BY A GREP. This object is the last thing between the decompressed
        body and a traceback renderer: `parse_body` and the readers below it
        drop their own `body` local on the way out, so after CS-963's repair
        round the buffer survives in `self._data` and nowhere else, and every
        method here that raises leaves `self` in a frame the renderer prints.

        The default ``object.__repr__`` already withholds it. Stating the
        requirement is the difference between a property that HOLDS and a
        property that HAPPENS to hold: making this class a dataclass later,
        whose generated repr would dump the whole body, is now a deliberate act.
        ``tests/save/test_world.py::test_the_only_retained_buffers_are_
        encapsulated_and_every_holder_withholds`` asserts it of every retained
        holder it finds, so a third cursor written tomorrow is covered without
        anyone remembering to add it.

        THE LENGTH IS NOT RENDERED. On a cursor reached from a world load that
        is the exact decompressed size of the player's save.

        Returns:
            The class name and how far the cursor has read. No bytes, no length.
        """
        return f"<_Cursor at offset {self.offset}>"

    @property
    def remaining(self) -> int:
        """How many bytes are left.

        Returns:
            The count, never negative.
        """
        return len(self._data) - self.offset

    def _require(self, count: int, field: str) -> None:
        """Assert ``count`` bytes are available at the cursor.

        Args:
            count: Bytes needed.
            field: The field being read, from :data:`FIELD_NAMES`.

        Raises:
            ObjectTruncatedError: Fewer than ``count`` bytes remain.
        """
        if count > self.remaining:
            raise ObjectTruncatedError(
                REASON_SHORT_BUFFER,
                field=field,
                offset=self.offset,
                expected=count,
                actual=self.remaining,
            )

    def int32(self, field: str) -> int:
        """Read a signed 32-bit little-endian integer.

        Args:
            field: The field being read.

        Returns:
            The value.
        """
        self._require(INT32_SIZE, field)
        (value,) = struct.unpack_from("<i", self._data, self.offset)
        self.offset += INT32_SIZE
        return int(value)

    def int64(self, field: str) -> int:
        """Read a signed 64-bit little-endian integer.

        Args:
            field: The field being read.

        Returns:
            The value.
        """
        self._require(INT64_SIZE, field)
        (value,) = struct.unpack_from("<q", self._data, self.offset)
        self.offset += INT64_SIZE
        return int(value)

    def skip(self, count: int, field: str) -> None:
        """Step over a run of bytes without reading them.

        Args:
            count: How many bytes to skip.
            field: The field being skipped.
        """
        self._require(count, field)
        self.offset += count

    def floats(self, count: int, field: str) -> tuple[float, ...]:
        """Read ``count`` consecutive float32 values.

        Args:
            count: How many floats.
            field: The field being read.

        Returns:
            The values, in file order.
        """
        width = count * INT32_SIZE
        self._require(width, field)
        values = struct.unpack_from(f"<{count}f", self._data, self.offset)
        self.offset += width
        return tuple(float(value) for value in values)

    def string(self, field: str) -> str:
        """Read and decode one length-prefixed string.

        THE BOUND IS APPLIED TO THE BYTE COUNT, before the remaining length is
        consulted and before any slice is taken. The multiply on the UTF-16
        path happens first for exactly that reason: a declared character count
        just under the cap becomes a byte count just over it.

        Args:
            field: The field being read.

        Returns:
            The decoded text, without its trailing null.

        Raises:
            ObjectFormatError: The declared length is above
                :data:`MAX_STRING_BYTES`, or the bytes do not decode.
            ObjectTruncatedError: The declared payload runs past the body.
        """
        at = self.offset
        count = self.int32(field)
        if count == 0:
            return ""
        if count < 0:
            byte_count = -count * UTF16_CHAR_SIZE
            terminator = UTF16_CHAR_SIZE
            encoding = "utf-16-le"
        else:
            byte_count = count
            terminator = 1
            encoding = "utf-8"
        if byte_count > MAX_STRING_BYTES:
            raise ObjectFormatError(
                REASON_DECLARED_LENGTH_ABOVE_CAP,
                field=field,
                offset=at,
                expected=MAX_STRING_BYTES,
                actual=byte_count,
            )
        self._require(byte_count, field)
        raw = self._data[self.offset : self.offset + byte_count - terminator]
        self.offset += byte_count
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            # THE CS-963 SCRUB, AND IT IS THE BYTE-IDENTICAL TWIN OF THE ONE IN
            # `header._Cursor.string`. `raw` is one decoded string's worth of the
            # DECOMPRESSED BODY - a level name, an actor instance name, an object
            # path - and the raise happens inside this frame, so a locals-showing
            # renderer prints those bytes beside the error saying they did not
            # decode (non-negotiable 12). Reachable from
            # `world.load_world_from_bytes` with default arguments.
            #
            # THE COMMIT THAT SCRUBBED THE HEADER TWIN CLAIMED THE SIBLING GREP
            # HAD BEEN RUN AND IT HAD NOT BEEN - not against this module. A
            # claimed grep is not a grep, and an adversary found this by reading
            # the class the repair had just been applied to elsewhere.
            #
            # Re-raised from None: a UnicodeDecodeError message QUOTES the
            # offending bytes, and exception context is an echo path.
            del raw
            raise ObjectFormatError(
                REASON_UNDECODABLE_TEXT, field=field, offset=at, actual=byte_count
            ) from None


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def transform_delta(save_version: int) -> int:
    """Look up the MEASURED transform delta for a save version.

    Args:
        save_version: The save version, from the header.

    Returns:
        The filler width in bytes.

    Raises:
        UnsupportedSaveVersionError: No delta has been measured for it. Never
            interpolated from its neighbours - see the module docstring.
    """
    delta = TRANSFORM_DELTA_BY_SAVE_VERSION.get(save_version)
    if delta is None:
        raise UnsupportedSaveVersionError(
            REASON_UNMEASURED_TRANSFORM_DELTA,
            field="save_version",
            offset=0,
            version=save_version,
        )
    return delta


def body_prefix_width(header_version: int) -> int:
    """How many bytes the body length prefix occupies on this header version.

    Args:
        header_version: The header version, from the header.

    Returns:
        8 on header versions 13 and 14, 4 on header version 10.
    """
    if header_version >= HEADER_VERSION_WITH_WIDE_PREFIX:
        return BODY_PREFIX_WIDTH_WIDE
    return BODY_PREFIX_WIDTH_NARROW


def class_name_of(type_path: str) -> str:
    """Reduce a class path to the object name a usmap schema is keyed by.

    The shipped property mapping keys its schemas by object name, so this is
    the one rule that joins the two. A path with no dot is already a bare
    name and is returned unchanged, which is what keeps a mod-authored or
    hand-written identifier from silently resolving to an empty string.

    Args:
        type_path: The class path as read, namespaced or bare.

    Returns:
        The text after the final dot, or the whole input when there is none.
    """
    return type_path.rpartition(".")[2] if "." in type_path else type_path


# ---------------------------------------------------------------------------
# The walk
# ---------------------------------------------------------------------------


def _warning(
    code: str, offset: int, *, expected: int | None = None, actual: int | None = None
) -> ObjectWarning:
    """Build one warning from the fixed detail table.

    Args:
        code: One of the ``WARN_*`` constants.
        offset: Where the condition was noticed.
        expected: An expected length or count.
        actual: An observed length or count.

    Returns:
        The warning.
    """
    return ObjectWarning(
        code=code, detail=_WARNING_DETAIL[code], offset=offset, expected=expected, actual=actual
    )


def _read_record(cursor: _Cursor, delta: int) -> ObjectRecord:
    """Read one object record at the cursor.

    Args:
        cursor: Positioned at the record's object-type discriminator.
        delta: The save version's filler width before the transform block.

    Returns:
        The record.

    Raises:
        ObjectFormatError: The discriminator has no measured record grammar.
        ObjectTruncatedError: The record runs past the body.
    """
    at = cursor.offset
    object_type = cursor.int32("object_type")
    kind = _KIND_BY_OBJECT_TYPE.get(object_type)
    if kind is None:
        raise ObjectFormatError(
            REASON_UNMEASURED_OBJECT_TYPE, field="object_type", offset=at, actual=object_type
        )

    type_path = cursor.string("type_path")
    root_object = cursor.string("root_object")
    instance_name = cursor.string("instance_name")

    # Opaque by measurement: only the WIDTH of this run is known (ADR 0003).
    # Decoding fields out of it would be decoding an invention.
    cursor.skip(delta, "transform_delta")

    values = cursor.floats(TRANSFORM_FLOAT_COUNT, "transform")
    was_placed_in_level = cursor.int32("was_placed_in_level")

    return ObjectRecord(
        kind=kind,
        type_path=type_path,
        root_object=root_object,
        instance_name=instance_name,
        transform=Transform(
            rotation=(values[0], values[1], values[2], values[3]),
            translation=(values[4], values[5], values[6]),
            scale=(values[7], values[8], values[9]),
        ),
        parent=None,
        object_type=object_type,
        was_placed_in_level=was_placed_in_level,
        body_offset=0,
        body_length=0,
    )


def _read_prefix(cursor: _Cursor, header_version: int) -> tuple[int, int, list[ObjectWarning]]:
    """Read the body length prefix at the version-appropriate width.

    Args:
        cursor: Positioned at byte zero of the body.
        header_version: Drives the width, and only the width.

    Returns:
        The declared length, the width used, and any advisories.
    """
    found: list[ObjectWarning] = []
    if header_version not in MEASURED_HEADER_VERSIONS:
        found.append(_warning(WARN_UNMEASURED_HEADER_VERSION, 0, actual=header_version))

    width = body_prefix_width(header_version)
    declared = (
        cursor.int64("body_length")
        if width == BODY_PREFIX_WIDTH_WIDE
        else cursor.int32("body_length")
    )
    if declared != cursor.remaining:
        found.append(
            _warning(
                WARN_BODY_LENGTH_DISAGREEMENT,
                0,
                expected=declared,
                actual=cursor.remaining,
            )
        )
    return declared, width, found


def _read_count(cursor: _Cursor, delta: int) -> int:
    """Read and bound the declared record count.

    The ceiling is checked BEFORE the buffer bound, so a wildly declared count
    is refused as a budget failure rather than reported as a truncation - the
    two mean different things to a caller and the ordering is what keeps them
    distinguishable.

    Args:
        cursor: Positioned at the count.
        delta: The save version's filler width, part of the minimum record size.

    Returns:
        The count.

    Raises:
        ObjectFormatError: The count is negative.
        ObjectBudgetExceededError: The count exceeds :data:`MAX_OBJECTS`.
        ObjectTruncatedError: The declared records cannot fit in the body.
    """
    at = cursor.offset
    count = cursor.int32("object_count")
    if count < 0:
        raise ObjectFormatError(
            REASON_NEGATIVE_COUNT, field="object_count", offset=at, actual=count
        )
    if count > MAX_OBJECTS:
        raise ObjectBudgetExceededError(
            REASON_ABOVE_CEILING,
            field="object_count",
            offset=at,
            expected=MAX_OBJECTS,
            actual=count,
        )
    needed = count * (_MINIMUM_RECORD_BYTES + delta)
    if needed > cursor.remaining:
        raise ObjectTruncatedError(
            REASON_SHORT_BUFFER,
            field="object_table",
            offset=cursor.offset,
            expected=needed,
            actual=cursor.remaining,
        )
    return count


class _UnknownLog:
    """Aggregates unmodelled class paths, keeping first-seen order.

    Order is stable so two runs on one save agree exactly, which the
    determinism property in CLAUDE.md section 1 requires of everything that
    reaches a rendering.
    """

    def __init__(self) -> None:
        """Start an empty log."""
        self._order: list[str] = []
        self._count: dict[str, int] = {}
        self._first: dict[str, int] = {}

    def add(self, type_path: str, index: int) -> None:
        """Record one unmodelled record.

        Args:
            type_path: The class path.
            index: The record index it was seen at.
        """
        if type_path not in self._count:
            self._order.append(type_path)
            self._count[type_path] = 0
            self._first[type_path] = index
        self._count[type_path] += 1

    def emit(self, *, registry_incomplete: bool = False) -> tuple[UnknownClass, ...]:
        """Publish in first-seen order, under the reason the registry supports.

        THE WEAKER REASON APPLIES TO EVERY ENTRY, AND THAT WIDTH IS DELIBERATE
        (CS-440). What an incomplete registry lost is by construction not
        attributable to a class path - a name that did not resolve and a section
        that stopped early both lose exactly the identity that would say which -
        so there is no path to single out as the affected one. Downgrading all
        of them under-claims for a path that really is unmodelled, and that is
        the safe direction; naming one would be the confident wrong answer.

        Args:
            registry_incomplete: Whether the caller's registry is known to have
                lost part of itself while being parsed. See
                :func:`parse_object_headers`.

        Returns:
            The aggregated entries.
        """
        reason = REASON_REGISTRY_INCOMPLETE if registry_incomplete else REASON_CLASS_NOT_MODELLED
        return tuple(
            UnknownClass(
                type_path=path,
                count=self._count[path],
                reason=reason,
                first_index=self._first[path],
            )
            for path in self._order
        )


def parse_object_headers(
    body: bytes,
    *,
    save_version: int,
    header_version: int,
    known_classes: Container[str] | None = None,
    registry_incomplete: bool = False,
) -> ObjectTable:
    """Walk the object record table out of a decompressed save body.

    THE TWO DISPATCHES ARE INDEPENDENT. ``header_version`` selects the body
    length prefix width and NOTHING else; ``save_version`` selects the
    transform delta and NOTHING else. See the module docstring for why a parser
    conflating them passes every real-shaped fixture.

    THE WALK CONTINUES PAST UNKNOWN CONTENT. A class path the registry does not
    model is recorded and stepped over; parsing runs to the end of the table
    and the result reports that the world holds unmodelled content.

    Args:
        body: The decompressed body exactly as ``chunks.decompress_body``
            returns it, length prefix included.
        save_version: From the header. Drives the transform delta.
        header_version: From the header. Drives the length prefix width.
        known_classes: Class NAMES the caller can model - a property map's
            ``schemas`` mapping satisfies this directly. None means no registry
            was supplied and nothing is claimed unknown.
        registry_incomplete: Whether the caller knows its registry lost part of
            itself while being parsed. THIS MODULE CANNOT DERIVE IT AND MUST NOT
            TRY: ``known_classes`` is a container of names, and an entry that
            was dropped is indistinguishable from an entry that was never there,
            so only the caller that parsed the registry knows. True weakens
            every unknown-class reason to :data:`REASON_REGISTRY_INCOMPLETE`; it
            never adds or removes an entry, and with ``known_classes=None`` it
            claims nothing at all, because a check that never ran cannot produce
            a finding.

    Returns:
        The walked table, with everything flagged and carried.

    Raises:
        UnsupportedSaveVersionError: The save version has no measured transform
            delta. Raised before any byte of the table is read.
        ObjectTruncatedError: The body ends inside the table.
        ObjectFormatError: A count, a declared string length or an object-type
            discriminator is structurally impossible.
        ObjectBudgetExceededError: The declared record count exceeds the stated
            ceiling.
    """
    # EAGER, before a single byte of the table. A version check placed after
    # the walk cannot fire on an empty table and becomes a time bomb.
    delta = transform_delta(save_version)

    cursor = _Cursor(body)
    declared, width, warnings = _read_prefix(cursor, header_version)

    table_start = cursor.offset
    count = _read_count(cursor, delta)

    records: list[ObjectRecord] = []
    unknown = _UnknownLog()
    for index in range(count):
        record = _read_record(cursor, delta)
        records.append(record)
        if known_classes is not None and class_name_of(record.type_path) not in known_classes:
            unknown.add(record.type_path, index)

    consumed = cursor.offset - table_start
    if cursor.remaining:
        warnings.append(
            _warning(WARN_UNPARSED_DATA_SECTION, cursor.offset, actual=cursor.remaining)
        )

    return ObjectTable(
        records=tuple(records),
        unknown_classes=unknown.emit(registry_incomplete=registry_incomplete),
        warnings=tuple(warnings),
        declared_body_length=declared,
        body_consumed=consumed,
        body_prefix_width=width,
        transform_delta=delta,
        save_version=save_version,
        header_version=header_version,
    )


# ---------------------------------------------------------------------------
# The LEVELLED walk - CS-407
#
# A real body does NOT open with an object count. It opens with a
# version-dependent preamble and then carries a LIST OF LEVELS, each with its
# own record table, its own collectable list and its own payload section. The
# walk below is the layout MEASURED for header 10 / save 36, and its oracle is
# the only one that cannot be argued with: on a real body it lands on the exact
# final byte, 202 levels and 25769 records later.
#
# It is a SEPARATE entry point rather than a change to parse_object_headers. A
# concurrent slice consumes that function, and every existing fixture is built
# on the flat layout; switching them over would put a large body of live
# assertions onto new bytes for no gain.
# ---------------------------------------------------------------------------


def _read_bounded_count(cursor: _Cursor, field: str, ceiling: int) -> int:
    """Read a count and refuse an impossible one before anything is allocated.

    Args:
        cursor: Positioned at the count.
        field: The field being read, from :data:`FIELD_NAMES`.
        ceiling: The stated maximum.

    Returns:
        The count.

    Raises:
        ObjectFormatError: The count is negative.
        ObjectBudgetExceededError: The count exceeds ``ceiling``.
    """
    at = cursor.offset
    count = cursor.int32(field)
    if count < 0:
        raise ObjectFormatError(REASON_NEGATIVE_COUNT, field=field, offset=at, actual=count)
    if count > ceiling:
        raise ObjectBudgetExceededError(
            REASON_ABOVE_CEILING, field=field, offset=at, expected=ceiling, actual=count
        )
    return count


def _read_section_size(
    cursor: _Cursor, layout: BodyLayout, field: str, warnings: list[ObjectWarning]
) -> int:
    """Read one section size at the pair's width.

    AN 8-BYTE SIZE IS READ AS AN INT32 SIZE PLUS A NAMED RESERVED INT32, NOT AS
    AN INT64, and the choice is made on asymmetric damage rather than on taste.
    The corpus cannot decide between the two readings and never will: the
    reserved word is zero in all 5890 instances measured on the (14,52) corpus
    and in every instance on the others, and the largest section observed is
    0.45% of 2**31, so no save that can physically exist sets a high word by
    size alone.

    Given that, the two readings differ only in how they FAIL. If the field is
    really an int64, this reader is correct for every save that can exist. If it
    is int32-plus-reserved and that word ever goes non-zero, an int64 reader
    silently computes ``lo + hi * 2**32``, gets an astronomical size, and
    reports a section-size mismatch - a diagnosis pointing at the WRONG FIELD,
    which is the expensive kind of wrong. This reader names the field that
    actually changed.

    A NON-ZERO RESERVED WORD IS FLAGGED, NOT FATAL (non-negotiable 7). Refusing
    a save over a word whose meaning is unknown would be worse than reading it,
    and passing it silently would discard the first evidence anyone has ever had
    about that word.

    Args:
        cursor: Positioned at the size.
        layout: The pair's grammar, for the width.
        field: The section field name, from :data:`FIELD_NAMES`.
        warnings: Accumulator, appended to when the reserved word is set.

    Returns:
        The declared size.
    """
    if layout.section_size_width == INT32_SIZE:
        return cursor.int32(field)
    at = cursor.offset
    size = cursor.int32(field)
    if cursor.int32("section_size_reserved") != 0:
        # The OFFSET is reported and the observed value is not. A word read out
        # of a personal-data-bearing body is not one of the five channels
        # non-negotiable 12 allows into a message, and "expected zero" is the
        # whole of the actionable content anyway.
        warnings.append(_warning(WARN_RESERVED_WORD_SET, at, expected=0))
    return size


def _read_package_summary(cursor: _Cursor) -> None:
    """Step over one package summary.

    TWO STRINGS AROUND 22 OPAQUE BYTES, A COUNT, THEN THAT MANY 20-BYTE
    ENTRIES. This read USED TO BE A 70-BYTE SKIP on the stated grounds that no
    interior boundary was observable - not 4+6, not 8+2, not 16+10.

    THAT GROUND WAS FALSE AND THE SEARCH THAT ESTABLISHED IT COULD NOT HAVE
    FOUND THIS. It searched for a split into FIXED widths, and the boundary
    here is a length prefix: the two strings declare 0 and 40 on all 1530
    summaries of the five real (14,60) saves, tiling 4 + 22 + 44 to exactly 70,
    with the second string's terminator on +69 and the count on +70 - no slack
    at either end. Reading them lands all 17 real saves on their final byte,
    the same oracle the whole levelled grammar rests on.

    A SECOND LENGTH IS WHAT SEPARATES THIS FROM THE OLD READING and no real
    save on the machine carries one, so the corpus alone cannot choose between
    them. The fixture supplies the second length instead, which is what
    tests/save/test_objects.py::test_a_package_summary_name_of_any_length_walks
    does; the 70-byte reader fails it exactly as it failed the level tail, with
    a custom-version count taken out of the middle of a string.

    Args:
        cursor: Positioned at the summary.

    Raises:
        ObjectFormatError: A declared string length is impossible.
        ObjectBudgetExceededError: The declared count exceeds its ceiling.
        ObjectTruncatedError: The summary runs past the body.
    """
    # Read and DISCARDED, on the same terms as a level name: these name
    # packages, which is world content (non-negotiable 12).
    cursor.string("package_summary")
    cursor.skip(_PACKAGE_SUMMARY_MIDDLE_BYTES, "package_summary")
    cursor.string("package_summary")
    count = _read_bounded_count(cursor, "custom_version_count", MAX_CUSTOM_VERSIONS)
    cursor.skip(count * _CUSTOM_VERSION_ENTRY_BYTES, "custom_version")


def _read_level_tail(cursor: _Cursor) -> None:
    """Step over a named level's tail, entry list and all.

    TWO OPAQUE WORDS BRACKET A COUNTED LIST OF STRING PAIRS. Only the widths
    of the two words are read; neither is interpreted, and the corpus cannot
    separate a constant from a field that has taken one value so far.

    THE LIST IS WHAT CS-482 MEASURED and it is anchored rather than assumed.
    A package summary opens with a constant word run. Under THIS reading that
    run sits at +4 from the summary start on every one of the 1530 summaries
    the five real (14,60) saves hold - 1525 level tails and 5 preambles.
    Under the 12-byte reading the walk reaches 900 of those summaries before
    it stops, 897 of them at +4 and 3 at +84 - one per save that declares an
    entry - and 80 is exactly that entry's two strings and their length
    prefixes. Reading them lands every real save of a measured pair on its
    final byte, which
    tests/save/test_objects.py::test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body
    re-derives on any machine holding a library. The three that did not land
    before this change reddened twelve tests, that one among them.

    THE EVIDENCE IS ONE ENTRY, NOT THREE, AND THE DIFFERENCE IS WORTH THE
    SENTENCE. Three level tails declare a non-zero count, one in each of three
    saves, and a refutation pass hashed the three spans and found them
    BYTE-IDENTICAL - three rotations of one autosave of one world. All five
    real (14,60) saves are that same world. So this grammar rests on a single
    observed entry, and the count is the only field of it that has ever varied.

    THREE THINGS FOLLOW THAT THIS READER CANNOT DECIDE, all of them left open
    rather than rounded off:

    - WHETHER THE FIELD IS A COUNT AT ALL. Over an observed population of {0,
      1} a count and a presence flag are the same field. This reads a count
      because every sibling list in this walk is one.
    - HOW A COUNT ABOVE 1 INTERLEAVES. A pair per entry and two parallel lists
      agree at 0 and 1 and diverge at 2. This reads pairs.
    - WHAT THE TWO STRINGS MEAN. They are consumed, not interpreted.

    LANDING ON THE FINAL BYTE DOES NOT SETTLE ANY OF THAT, which is the trap
    the same pass walked into deliberately: it built rival tail grammars -
    a fixed 80-byte blob, two parallel lists, a presence flag - and ALL of them
    land 17 real saves of 17 on the exact final byte. The oracle is necessary
    and it is not sufficient. What actually separates this reading from the
    old 12-byte one is that the two length prefixes tile a CLOSED interval -
    left edge pinned by the declared data-section size, right edge by the
    summary's constant word run - with zero slack, each landing on its own
    terminator; and that arity is decided by the same tiling, since reading one
    string per entry or three fails 3 of 17.

    THE STRINGS ARE READ AND DISCARDED, on the same terms as a level name:
    they name packages, which is world content, and holding one would put it
    into the returned model and into its repr (non-negotiable 12).

    Args:
        cursor: Positioned at the tail.

    Raises:
        ObjectFormatError: The declared entry count is negative.
        ObjectBudgetExceededError: It exceeds
            :data:`MAX_LEVEL_TAIL_ENTRIES`.
        ObjectTruncatedError: The tail runs past the body.
    """
    cursor.skip(_LEVEL_TAIL_LEAD_BYTES, "level_tail")
    count = _read_bounded_count(cursor, "level_tail_count", MAX_LEVEL_TAIL_ENTRIES)
    for _ in range(count):
        cursor.string("level_tail_entry")
        cursor.string("level_tail_entry")
    cursor.skip(_LEVEL_TAIL_TRAILING_BYTES, "level_tail")


def _read_grid_preamble(cursor: _Cursor) -> None:
    """Step over the grid block that precedes the level count on three pairs.

    Each grid carries a name, 8 opaque bytes and a counted cell list; each cell
    carries a name and 4 opaque bytes. NO LABEL IS CLAIMED for either opaque
    run. An earlier reading called the first two words ``cell_size`` and
    ``hash``, and neither survives contact with the values - one observed
    ``cell_size`` is 12798, which is not a plausible round cell size.

    Args:
        cursor: Positioned at the grid count.

    Raises:
        ObjectBudgetExceededError: A declared count exceeds its ceiling.
        ObjectTruncatedError: The block runs past the body.
    """
    for _ in range(_read_bounded_count(cursor, "grid_count", MAX_GRIDS)):
        cursor.string("grid_name")
        cursor.skip(_GRID_OPAQUE_BYTES, "grid_opaque")
        for _ in range(_read_bounded_count(cursor, "grid_cell_count", MAX_OBJECTS)):
            cursor.string("grid_cell_name")
            cursor.skip(_GRID_CELL_OPAQUE_BYTES, "grid_cell_opaque")


def _read_levelled_record(cursor: _Cursor, layout: BodyLayout) -> ObjectRecord:
    """Read one record in the MEASURED levelled grammar.

    THE TWO KINDS DIVERGE HERE, and that is the correction CS-407 carries. An
    actor closes with its opaque run, its transform block and a trailing int32;
    a COMPONENT closes with a parent path instead, preceded on two pairs by 4
    opaque bytes. ``_read_record`` above reads the actor shape under either
    discriminator, which is correct for the flat corpus and desynchronises a
    real body at its first component.

    The component's pre-word WIDTH is pinned decisively rather than by
    consumption alone: a 0-byte rival, an 8-byte rival and an empty-string rival
    each land on 0 of the 8 real (14,52) files. Its TYPE is not pinned - a
    two-int16 reading closes byte-exactly - so it is stepped over rather than
    decoded.

    Args:
        cursor: Positioned at the record's object-type discriminator.
        layout: The pair's grammar.

    Returns:
        The record.

    Raises:
        ObjectFormatError: The discriminator has no measured record grammar.
        ObjectTruncatedError: The record runs past the body.
    """
    at = cursor.offset
    object_type = cursor.int32("object_type")
    kind = _KIND_BY_OBJECT_TYPE.get(object_type)
    if kind is None:
        raise ObjectFormatError(
            REASON_UNMEASURED_OBJECT_TYPE, field="object_type", offset=at, actual=object_type
        )

    type_path = cursor.string("type_path")
    root_object = cursor.string("root_object")
    instance_name = cursor.string("instance_name")

    transform: Transform | None = None
    parent: str | None = None
    was_placed_in_level = 0
    if kind == KIND_ACTOR:
        # Opaque by measurement: only the WIDTH of this run is known (ADR 0003).
        cursor.skip(layout.transform_delta, "transform_delta")
        values = cursor.floats(TRANSFORM_FLOAT_COUNT, "transform")
        was_placed_in_level = cursor.int32("was_placed_in_level")
        transform = Transform(
            rotation=(values[0], values[1], values[2], values[3]),
            translation=(values[4], values[5], values[6]),
            scale=(values[7], values[8], values[9]),
        )
    else:
        if layout.component_pre_word:
            cursor.skip(_COMPONENT_PRE_WORD_BYTES, "component_pre_word")
        parent = cursor.string("parent_object_root")

    return ObjectRecord(
        kind=kind,
        type_path=type_path,
        root_object=root_object,
        instance_name=instance_name,
        transform=transform,
        parent=parent,
        object_type=object_type,
        was_placed_in_level=was_placed_in_level,
        # Attributed by `_read_level` once the data section has been read, via
        # `with_payload`. It cannot happen here: the payload extents live after
        # the whole record table in the file, so nothing at this point in the
        # walk knows them yet.
        body_offset=0,
        body_length=0,
    )


def _read_collectables(cursor: _Cursor, into: list[Collectable]) -> int:
    """Read one collectable list and APPEND its entries in file order - CS-1038.

    MEASURED as a count followed by that many PAIRS OF STRINGS - measured in
    the sense that reading it any other way stops the whole-body walk short of
    the final byte.

    THE STRINGS USED TO BE READ AND DROPPED ON THE SAME LINE, and this is the
    repair rather than a widening. The reading was never in doubt; what was
    missing was the CARRY. The block is the only record in the body of what the
    player has already collected, and four downstream consumers cannot be built
    against a count. :class:`Collectable` owns what the two halves are, what the
    polarity is, and what is not claimed about either.

    IT TAKES THE ACCUMULATOR RATHER THAN RETURNING A LIST, matching the record
    and warning accumulators this walk already threads: one list per body, in
    file order, with no per-level tuple allocated and discarded on the way.

    Args:
        cursor: Positioned at the count.
        into: The body's accumulator, appended to in file order.

    Returns:
        How many entries were read.
    """
    count = _read_bounded_count(cursor, "collectable_count", MAX_OBJECTS)
    for _ in range(count):
        level_name = cursor.string("collectable")
        into.append(Collectable(level_name=level_name, instance_name=cursor.string("collectable")))
    return count


def _check_section(cursor: _Cursor, field: str, at: int, base: int, declared: int) -> None:
    """Assert a section spanned exactly the bytes it declared.

    THIS IS THE WALK'S OWN ORACLE, applied at every level rather than once at
    the end. A drift of a single byte is caught by the level that contains it,
    which is what makes a failure point at a grammar rather than at a total.

    Args:
        cursor: Positioned at the end of the section.
        field: The section field name, from :data:`FIELD_NAMES`.
        at: Where the size was declared.
        base: The first byte the size covers.
        declared: The declared size.

    Raises:
        ObjectFormatError: The walked extent differs from the declared one.
    """
    walked = cursor.offset - base
    if walked != declared:
        raise ObjectFormatError(
            REASON_SECTION_SIZE_DISAGREEMENT,
            field=field,
            offset=at,
            expected=declared,
            actual=walked,
        )


def _read_data_entries(cursor: _Cursor, layout: BodyLayout) -> list[tuple[int, int]]:
    """Walk one level's object data section and LOCATE every payload in it.

    The payload's VALUE grammar is not decoded here; only its framing is, and
    the framing is what locates it. It is THREE QUARTERS OF THE BODY being
    located, not a detail.

    The leading run is skipped whole. On (13,42) its two int32 readings take
    exactly two joint values, (42,0) and (36,1), so the second is perfectly
    determined by the first; on (14,52) they are collinear across 29466
    entries; and an int64 reading closes byte-exactly on (14,60). The 8-byte
    WIDTH is pinned and the split is not, so no split is claimed.

    Args:
        cursor: Positioned at the section's entry count.
        layout: The pair's grammar.

    Returns:
        One ``(offset, length)`` per entry, in file order.

    Raises:
        ObjectTruncatedError: An entry runs past the body.
        ObjectBudgetExceededError: A declared count or length exceeds its cap.
    """
    extents: list[tuple[int, int]] = []
    for _ in range(_read_bounded_count(cursor, "object_count", MAX_OBJECTS)):
        if layout.data_entry_lead:
            cursor.skip(layout.data_entry_lead, "object_data_lead")
        length = _read_bounded_count(cursor, "object_data", MAX_OBJECT_DATA_BYTES)
        extents.append((cursor.offset, length))
        cursor.skip(length, "object_data")
        if layout.data_entry_trailer:
            cursor.int32("object_data_trailer")
    return extents


def _attribute_payloads(
    records: list[ObjectRecord],
    first: int,
    count: int,
    extents: list[tuple[int, int]],
    *,
    at: int,
    warnings: list[ObjectWarning],
) -> None:
    """Give each of a level's records the extent of its own payload (CS-413).

    THE k-TH PAYLOAD BELONGS TO THE k-TH RECORD, AND THAT IS MEASURED. An
    actor's payload opens with its component reference list, and every one of
    those references names a component record whose own ``parent`` field points
    back at that actor - so the record table and the data section are parsed
    independently and then checked against each other. Across all 14 real saves
    the k-th alignment satisfies that cross-check on 9838 of 9838 testable
    actors and both neighbouring alignments satisfy it on 0. The corpus cannot
    corroborate it: the payloads in its parametrized matrices are filler.

    THE COUNT GUARD IS NOT DECORATION. Attribution is only DEFINED when the two
    counts agree. Where they do not, no pairing is invented - a walker that
    zipped the shorter list would pair some records with another record's
    payload and report it as fact, which is the silently wrong answer
    non-negotiable 7 forbids. The level is flagged instead and its records keep
    0. No real save reaches that branch - every level of every real save on this
    machine agrees on the two counts.

    Args:
        records: The accumulator, mutated in place.
        first: Index in ``records`` where this level's records begin.
        count: How many records this level's table declared.
        extents: What :func:`_read_data_entries` located.
        at: Where the data section was declared, for the warning's offset.
        warnings: Accumulator for flagged conditions.
    """
    if len(extents) == count:
        for index, (payload_at, payload_length) in enumerate(extents):
            records[first + index] = records[first + index].with_payload(payload_at, payload_length)
    elif extents or count:
        warnings.append(
            _warning(WARN_PAYLOAD_COUNT_DISAGREEMENT, at, expected=count, actual=len(extents))
        )


def _read_level(
    cursor: _Cursor,
    layout: BodyLayout,
    *,
    named: bool,
    known_classes: Container[str] | None,
    records: list[ObjectRecord],
    unknown: _UnknownLog,
    warnings: list[ObjectWarning],
    collectables: list[Collectable],
) -> None:
    """Read one level: its record table, its collectables and its payload section.

    ``named`` is False for exactly one level per body - the trailing persistent
    level. That asymmetry is measured: a walk expecting a name there stops with
    hundreds of thousands of bytes unread.

    THE HEADER COLLECTABLE BLOCK IS OPTIONAL, AND THE RULE FOR IT IS SIZE-DRIVEN:
    if bytes remain inside the declared header section once the record count is
    exhausted, those bytes are the block. The optionality itself is imposed by
    the format rather than chosen - both rigid alternatives were run against the
    real (14,52) corpus and both die, "always read the block" at level 0 and
    "never read it" at level 64.

    THE SIZE-DRIVEN RULE IS AN A-PRIORI DELIMITER ARGUMENT, NOT A MEASUREMENT,
    and saying so is the honest statement of what is known. Seven of the eight
    real (14,52) bodies are landed byte-exactly by an unconditional "always read
    a block" grammar; only the one 16 MB file distinguishes them, and in that
    file's version-42 levels every named field is degenerate - legacy content
    never re-serialized - so it contributes no evidence about any other field.
    Within it, "no header block", "first entry word is 42" and "second entry
    word is 1" are perfectly confounded, partitioning the identical 1641 levels
    with zero exceptions.

    Two rival formulations were considered and both discarded:

    - TAG-DRIVEN, "present iff the level's data entries are tagged 42". It needs
      a value from a section not yet read, and it is UNDEFINED on 229 of the
      2244 levels of the real (13,42) body because those levels have no entries
      to consult - and both outcomes occur among them, 227 with a block and 2
      without, so no constant completion of the rule is correct.
    - THE PRE-WORD PROXY, "present iff the records' pre-word is non-zero". It
      fits all 2945 sections of the (14,52) corpus and desynchronises on the
      first level whose records all happen to carry zero.

    What the rule buys is RESYNCHRONISATION, not interpretation. 2905 of 2945
    levels have a header-section leftover of exactly 4 zero bytes, and "a
    collectable block with count 0" is byte-indistinguishable from a reserved
    word or a flags word there.

    Args:
        cursor: Positioned at the level.
        layout: The pair's grammar.
        named: Whether the level carries a leading name string.
        known_classes: Class names the caller can model, or None.
        records: Accumulator, appended to in file order.
        unknown: Accumulator for unmodelled class paths.
        warnings: Accumulator for flagged conditions.
        collectables: Accumulator for this body's collectable entries, appended
            to in file order - CS-1038. ONE LIST FOR THE WHOLE BODY rather than
            one per level, because a level is not a thing the returned model
            holds: :class:`ObjectTable` publishes records flat, in file order,
            and a per-level split here would be the only place in the walk
            claiming a level identity the model cannot carry.

    Raises:
        ObjectFormatError: A declared section size disagrees with its content,
            or a count or discriminator is structurally impossible.
        ObjectTruncatedError: The level runs past the body.
        ObjectBudgetExceededError: A declared count exceeds its ceiling.
    """
    if named:
        # Read and DISCARDED. A level name is not needed by any consumer today
        # and holding one would put world content into the returned model and
        # into its repr, which non-negotiable 12 makes an echo path.
        cursor.string("level_name")

    first = len(records)
    at = cursor.offset
    header_size = _read_section_size(cursor, layout, "header_section", warnings)
    base = cursor.offset
    count = _read_bounded_count(cursor, "object_count", MAX_OBJECTS)
    for _ in range(count):
        record = _read_levelled_record(cursor, layout)
        index = len(records)
        records.append(record)
        if known_classes is not None and class_name_of(record.type_path) not in known_classes:
            unknown.add(record.type_path, index)
    if cursor.offset - base < header_size:
        _read_collectables(cursor, collectables)
    _check_section(cursor, "header_section", at, base, header_size)

    data_at = cursor.offset
    data_size = _read_section_size(cursor, layout, "object_data_section", warnings)
    data_base = cursor.offset
    extents = _read_data_entries(cursor, layout)
    _check_section(cursor, "object_data_section", data_at, data_base, data_size)
    _attribute_payloads(records, first, count, extents, at=data_at, warnings=warnings)

    if named:
        if layout.level_tail == LEVEL_TAIL_WORD:
            cursor.int32("level_tail")
        elif layout.level_tail == LEVEL_TAIL_SUMMARY:
            _read_level_tail(cursor)
            _read_package_summary(cursor)
    if not named or layout.second_collectables_named:
        _read_collectables(cursor, collectables)


def parse_body(
    body: bytes,
    *,
    save_version: int,
    header_version: int,
    known_classes: Container[str] | None = None,
    registry_incomplete: bool = False,
) -> ObjectTable:
    """Walk a WHOLE real body, every level of it, in the MEASURED layout.

    This is the entry point a caller holding an actual save wants.
    :func:`parse_object_headers` reads the flat single-table shape the corpus
    fixtures are built on, which CS-407 measured to be a shape no real body has.

    THE REFUSAL IS EAGER AND IS THE POINT. A pair outside
    :data:`MEASURED_BODY_LAYOUTS` raises before a byte is read. Three of the
    four real pairs land there today, and their partial derivations are recorded
    beside the corpus rather than rounded up into a layout.

    Args:
        body: The decompressed body exactly as ``chunks.decompress_body``
            returns it, length prefix included.
        save_version: From the header. Drives the transform delta.
        header_version: From the header. Drives the length prefix width.
        known_classes: Class NAMES the caller can model. None means no registry
            was supplied and nothing is claimed unknown.
        registry_incomplete: As :func:`parse_object_headers`. THIS IS THE READER
            A REAL SAVE GOES THROUGH (CS-409), so a fix applied only to the flat
            reader would leave every real world carrying the reason CS-440
            exists to withdraw.

    Returns:
        Every record from every level, in file order, with the level count and
        everything flagged on the way.

    Raises:
        UnsupportedBodyLayoutError: The pair has no measured body layout.
        UnsupportedSaveVersionError: The save version has no measured transform
            delta.
        ObjectFormatError: A declared size, count or discriminator is
            structurally impossible.
        ObjectTruncatedError: The body ends inside a level.
        ObjectBudgetExceededError: A declared count exceeds its ceiling.
    """
    # THE CS-963 SCRUB. This frame binds the WHOLE decompressed body and every
    # refusal in the levelled walk unwinds through it; `world.py` chains that
    # refusal, so the body reaches a renderer as the cause's locals. The two
    # exported property readers already scrub for exactly this reason - this is the
    # frame ABOVE them, and it was missed because no arm drove a body whose planted
    # marker survived into the bytes the walk refused (non-negotiable 12).
    try:
        layout = BODY_LAYOUT_BY_PAIR.get((header_version, save_version))
        if layout is None:
            raise UnsupportedBodyLayoutError(
                REASON_UNMEASURED_BODY_LAYOUT,
                field="body_layout",
                offset=0,
                actual=header_version,
                version=save_version,
            )
        delta = layout.transform_delta

        cursor = _Cursor(body)
        declared, width, warnings = _read_prefix(cursor, header_version)

        start = cursor.offset
        # The preamble, where the pair has one. Both blocks are stepped over rather
        # than modelled: nothing downstream consumes a world-partition grid today,
        # and holding one would put world content into the returned model.
        if layout.package_summary:
            _read_package_summary(cursor)
        if layout.grid_preamble:
            _read_grid_preamble(cursor)
        level_count = _read_bounded_count(cursor, "level_count", MAX_LEVELS)

        records: list[ObjectRecord] = []
        unknown = _UnknownLog()
        collectables: list[Collectable] = []
        for _ in range(level_count):
            _read_level(
                cursor,
                layout,
                named=True,
                known_classes=known_classes,
                records=records,
                unknown=unknown,
                warnings=warnings,
                collectables=collectables,
            )
        # Exactly one unnamed persistent level closes every measured body.
        _read_level(
            cursor,
            layout,
            named=False,
            known_classes=known_classes,
            records=records,
            unknown=unknown,
            warnings=warnings,
            collectables=collectables,
        )
        # THE BODY'S FINAL INT32 IS READ AS A COUNT OF OBJECT REFERENCES (CS-867),
        # each two length-prefixed strings. It read as an opaque word "observed to
        # be zero" until three real (14,60) saves declared 1 and left 120 bytes
        # unread.
        #
        # THIS IS CS-482 ONE LEVEL UP. There the level tail was 12 constant bytes
        # because the list is empty on 1522 of 1525 real tails; here the word was a
        # constant because it is zero on every save the grammar was derived from.
        # A field observed constant across a corpus is not a constant field.
        #
        # WHAT THIS READING DOES NOT ESTABLISH, on the same terms _read_level_tail
        # states for its own count, and stated here because an adversary measured
        # the first version of this comment asserting it flatly:
        #   - WHETHER THE FIELD IS A COUNT AT ALL. The observed population is
        #     {0: 17, 1: 3} over 20 saves, and the three non-zero tails are
        #     byte-identical and come from ONE world - so this is one distinct
        #     sample, not three. Over {0, 1} a count and a presence flag are the
        #     same field. This reads a count because every sibling list in this walk
        #     is one, and because the structurally identical level_tail_count is
        #     MEASURED at {0: 3131, 1: 39, 2: 8, 4: 3} on the same library and so is
        #     a count there on evidence.
        #   - HOW A COUNT ABOVE 1 INTERLEAVES. Nothing in the corpus reaches 2.
        #
        # LANDING ON THE FINAL BYTE DOES NOT SETTLE EITHER, and the same trap was
        # walked deliberately: a fixed 120-byte record, a flag then one pair,
        # non-zero-means-one, and a count of (string, 90 opaque bytes) ALL land 20
        # real saves of 20 on the exact final byte. UNLIKE CS-482 THERE IS NO RIGHT
        # EDGE TO PIN, because this list ends where the body ends - which is exactly
        # why several readings tile it and why the arm parametrizes the count.
        #
        # WHAT DOES SUPPORT THE PAIR READING is provenance rather than tiling, and
        # it is measured: on all three saves the first string is one of the 471
        # level names this same walk read earlier in the same body, and the pair is
        # identical to one of that body's own level_tail_entry pairs, which CS-482
        # reads as (level name, object path).
        #
        # THE STRINGS ARE READ AND DISCARDED, on the same terms as a level name and
        # a level tail entry: they name a level and an object path, which is world
        # content, and holding one would put it into the returned model and into a
        # rendered surface (non-negotiable 12).
        for _ in range(_read_bounded_count(cursor, "body_reference_count", MAX_BODY_REFERENCES)):
            cursor.string("body_reference")
            cursor.string("body_reference")

        consumed = cursor.offset - start
        if cursor.remaining:
            warnings.append(
                _warning(WARN_UNPARSED_DATA_SECTION, cursor.offset, actual=cursor.remaining)
            )

        return ObjectTable(
            records=tuple(records),
            unknown_classes=unknown.emit(registry_incomplete=registry_incomplete),
            warnings=tuple(warnings),
            declared_body_length=declared,
            body_consumed=consumed,
            body_prefix_width=width,
            transform_delta=delta,
            save_version=save_version,
            header_version=header_version,
            level_count=level_count + 1,
            collectables=tuple(collectables),
        )
    except BaseException:
        del body
        raise


# ---------------------------------------------------------------------------
# The property payload grammar
#
# MEASURED BY CS-413 AGAINST THE REAL LIBRARY, NOT INHERITED FROM PRIOR
# KNOWLEDGE OF HOW UNREAL SERIALIZES. Prior knowledge generated the hypotheses
# below; every one of them was then required to survive a check the shipped
# bytes could have failed, and the checks are named on each constant. Three
# oracles carried the weight, each drawing on evidence from outside this
# module's own grammar - though only the third is independent of this module's
# opinion, since the cross-section oracle takes its value locator from
# _read_tag_header and its record table from parse_body, so what differs there
# is the SECTION being read and not the opinion doing the reading:
#
#   SHIPPED REDUNDANCY - a string-bearing value carries its own length prefix,
#   which must equal the tag's declared size. Those are two separate numbers in
#   the file and they agree on EVERY string-bearing tag in the library, with no
#   exception. The count that used to stand here is deleted rather than
#   corrected: two independent re-derivations disagreed with it, and the
#   disagreement is definitional - the figure is only meaningful alongside a
#   statement of which type words count as string-bearing, which was never
#   written down beside it. The claim that carries the weight is the RATE, and
#   the rate is 100%. tests/save/test_properties.py::test_the_shipped_
#   redundancy_oracle_collapses_when_only_the_value_read_is_rotated re-derives
#   both halves from the library on every run, so this is now machine-checked
#   rather than transcribed.
#
#   CROSS-SECTION - an ObjectProperty names a record, and the record table is
#   parsed by a different pass over a different section. Not every reference
#   resolves, which is why that oracle is reported as a rate and never as a
#   total. WHAT THE UNRESOLVED ONES NAME IS NOT GLOSSED HERE - the sentence
#   that stood in this clause said they name assets rather than saved objects,
#   as a universal over the whole of them, and CS-833 withdrew that against the
#   library; UNRESOLVED_SHAPES holds the partition that replaced it. The
#   sentence is called out rather than quietly rewritten because it was the
#   FOURTH site of one claim, and three is what the item went looking for. The
#   count that stood here is
#   deleted rather than corrected, for the reason the paragraph above gives: it
#   is one corpus at one moment, and that corpus is a live save library which
#   grows. tests/save/test_decode_oracles.py::test_object_references_resolve_
#   against_the_record_table_and_collapse_when_rotated re-derives it on every
#   run, and shows it collapsing to nothing one byte either side.
#
#   DIFFERENT FILE - the usmap is generated from the game's assets and carries
#   a raw type byte per property. The save's type WORD proved to be a function
#   of that byte - one-to-one in both directions, no word claiming two ids, no
#   id claimed by two words, zero contradictions. The word count that stood
#   here is deleted on the same grounds as the two above.
#   tests/save/test_decode_oracles.py::test_the_usmap_type_id_join_is_a_
#   bijection_and_collapses_under_a_one_tag_shift re-derives the shape and its
#   shifted control on every run.
#
#   THAT JOIN CARRIES TWO QUANTITIES AND THEY DO NOT GRADE THE TAG WIDTHS
#   BELOW ALIKE - one population read at two quantities, and collapsing them
#   into a single verdict about "the join" is the expensive mistake. A wrong
#   width breaks the walk and a broken walk contributes no pairs, so a pair
#   that survives is a correct one and a BIJECTION over that shrinking
#   population stays pristine. THE DISTINCT-WORD COUNT IS NOT THE MIRROR OF
#   THAT, and the sentence that said it falls with the population was measured
#   false: a width was found that rots thousands of payloads while leaving the
#   count exactly where it was, because that width contributes none of the
#   joined words, and thinning the join directly through the tag cap drops
#   thousands of tags with the count again unmoved. Which width either quantity
#   notices is NOT recorded here. It is derived by
#   tests/save/test_decode_oracles.py::test_every_tag_width_
#   is_caught_by_a_library_backed_oracle, which mutates each width in
#   _TAG_EXTRA_STRINGS in this module alone - on every run that has the two
#   inputs it needs, a save library and a property mapping, and it SKIPS rather
#   than fails without them. Sentences recording that relation instead were
#   written false three rounds running, the last falsified by the commit that
#   added the floor, which is why the relation is derived and no longer
#   written. The reach oracle -
#   tests/save/test_decode_oracles.py::test_the_shipped_walker_reaches_a_
#   terminator_on_every_real_payload - is where the completeness of that walk
#   is asserted directly, and it walks with THESE constants rather than with a
#   test-side copy of them.
#
#   AND WHAT MIS-STATING A WIDTH ACTUALLY COSTS, which is CS-422's question and
#   is answered per width rather than by one adverb. A cursor width mis-stated
#   by one costs some payloads their terminator and leaves a MAJORITY still
#   reaching it, so "desynchronises immediately" was false for every one of
#   them. tests/save/test_properties.py::test_a_cursor_width_is_
#   discriminated_and_never_on_a_majority_of_payloads derives the whole relation
#   in one run. Its counterpart for the other class -
#   tests/save/test_properties.py::test_an_extent_width_cannot_
#   desynchronise_and_is_caught_by_disagreement - shows why one oracle cannot
#   grade both, and
#   tests/save/test_properties.py::test_the_width_rule_partitions_
#   every_shipped_width_and_declines_no_decoded_one holds every shipped width
#   inside the stated rule.
#
#   AND THE BYTE ORDER, which a width does not imply and which is a separate
#   question over the same entries.
#   tests/save/test_properties.py::test_the_int32_byte_order_is_
#   discriminated_by_the_stored_high_byte and
#   tests/save/test_properties.py::test_the_float32_byte_order_is_
#   discriminated_by_plausible_magnitude score the real population's magnitudes
#   under both readings, and
#   tests/save/test_properties.py::test_the_magnitude_oracle_covers_
#   exactly_the_types_marked_with_it ties EVIDENCE_FOR_VALUE_TYPE to the two of
#   them, so the table cannot credit an oracle that does not run.
#
# AND THE ROTATION CONTROL, which is what makes the above evidence about
# ALIGNMENT rather than about self-consistency. Re-read at VALUE-START offsets
# of -2, -1, +1 and +2 - the tag walk left synchronised, only the value read
# moved - the shipped-redundancy oracle collapses from every string-bearing tag
# to a handful, and the cross-section oracle to nothing. Delta 0 is uniquely
# exact. A result that does not collapse when moved is not evidence, and a
# `> 0` liveness floor would have passed several of these rotations.
#
# THE VALUE-START ROTATION IS THE ONE THAT EXERCISES THE VALUE GRAMMAR, and it
# is worth naming apart from the coarser control that moves a whole payload's
# START by one byte. That coarser one collapses inside the actor-head read,
# before a single property tag is examined, so it is evidence about the payload
# attribution and about nothing below it. Both now ship as tests rather than as
# this paragraph - see tests/save/test_properties.py.
# ---------------------------------------------------------------------------

#: Type words carrying extra tag data before the guid flag, and how many
#: length-prefixed strings of it. MEASURED: with these widths the tag walk
#: reaches its terminator on every payload of every real save of the THREE
#: pairs this grammar reads. NOT of every measured pair - (14,60) is measured
#: and reaches a terminator on none of its payloads, which is CS-G05.
#:
#: MIS-STATING ONE DOES NOT DESYNCHRONISE THE WALK "IMMEDIATELY", WHICH THIS
#: COMMENT USED TO CLAIM AND WHICH IS FALSE FOR EVERY ONE OF THEM. Each width,
#: mis-stated by one, costs some payloads their terminator and leaves a MAJORITY
#: of them still reaching it. The per-width figures are deliberately not written
#: here - they are derived in the same run by the per-width census cited in the
#: commentary block above, which is what turns this from an adverb into a
#: measurement. Read the counts off a run of that test.
#:
#: These are CURSOR widths - see :data:`WIDTH_SHIPPING_RULE` for what that means
#: and for the other class, which a reach oracle cannot grade at all.
_TAG_EXTRA_STRINGS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ByteProperty": 1,
        "EnumProperty": 1,
        "ArrayProperty": 1,
        "SetProperty": 1,
        "MapProperty": 2,
        "StructProperty": 1,
    }
)

#: Fixed-width value types and their measured widths. The WIDTH is measured -
#: every instance in the library declares exactly this size and no other.
#:
#: THE BYTE ORDER IS A SEPARATE QUESTION, AND THE SHIPPED ORACLES NARROW IT
#: RATHER THAN ANSWERING IT. This comment used to say the question "is answered
#: by a test". That claims more than the oracles deliver, which is what CS-421
#: clause 3 came back for. A width rules out a wrong size and says nothing about
#: which end a value starts at. The byte-order oracles cited in the commentary
#: block above score the real population under competing readings; each is
#: proven by a mutant, and none can be satisfied by a fixture this project
#: packs, because all of them read the game's own saves. What they leave
#: standing is a CANDIDATE SET rather than a sentence. Which question each entry
#: actually poses ships as data - see :data:`VALUE_BYTE_ORDER_STATUS` - and the
#: permutations those oracles cannot separate ship as
#: :data:`BYTE_ORDER_SURVIVING_CANDIDATES`, which they have now narrowed to the
#: as-stored ordering alone.
#:
#: The figures those oracles compute are deliberately NOT restated here. An
#: earlier revision of this comment carried four of them and claimed the
#: encoding was measured while nothing executable checked it; one pair did not
#: reproduce, because the predicate behind the percentage was written down
#: nowhere. Read the counts off a run of the tests instead - and note that the
#: two remaining entries below carry no such oracle, which is recorded in
#: :data:`WIDTH_ONLY_VALUE_TYPES` rather than in a sentence.
#:
#: WHAT BOUNDS MEMBERSHIP OF THIS TABLE - CS-481. Placing a word here is what
#: makes :func:`_byte_order_status` speak about it at all, and a width-1 entry
#: retires that word's byte-order question on arithmetic alone. Nothing outside
#: this table used to constrain what may go into it, and that was measured
#: rather than suspected: three lines - a width-1 entry for a type this module
#: claims nothing about, its shipping-grounds entry, and holding the word out of
#: :data:`MEASURED_VALUE_TYPES` - shipped :data:`BYTE_ORDER_VACUOUS` for an
#: EIGHT-byte type, byte-identical to the clean tree on a machine with no game.
#: Two library-free controls bound it now, and they are named in the commentary
#: block below, which is where this module keeps its test citations. WHAT THEY
#: REFUSE, stated so the table
#: carries its own bound: a word in here that
#: :data:`UNMEASURED_PAYLOAD_REGIONS` still records as unclaimed, and a word in
#: here whose declared-size disagreement the shipped payload walk counts as
#: unmodelled content rather than as a walk that has lost its place.
_FIXED_WIDTH_VALUES: Final[Mapping[str, tuple[int, str]]] = MappingProxyType(
    {
        "IntProperty": (4, "<i"),
        "UInt32Property": (4, "<I"),
        "FloatProperty": (4, "<f"),
        "Int8Property": (1, "<b"),
    }
)

#: Value types that are exactly one length-prefixed string.
_ONE_STRING_VALUES: Final = frozenset({"StrProperty", "NameProperty", "EnumProperty"})

#: The one type word of the two below whose value names a SAVED OBJECT, and so
#: the only one a record-table join has anything to look for.
#:
#: IT IS A SEPARATE NAME BECAUSE THE PAIR IS NOT THE POPULATION, and the shape
#: gives a reader no way to tell. SoftObjectProperty carries the identical two
#: strings and decodes to an identical ``tuple[str, str]``, so a consumer
#: filtering :attr:`PropertyResult.properties` by SHAPE takes both and cannot
#: know it did. It names ASSETS: measured against the record table across the
#: local library, not one of them resolved to a saved object when this constant
#: was written. THAT IS PAST TENSE ON PURPOSE - it is an observation of a
#: library that grows whenever the operator plays, so stating it as a standing
#: rate would be a claim that can go false with nobody looking (CLAUDE.md
#: section 4). What the constant expresses is the observation, and expressing
#: it here is what
#: ``tests/save/test_decode_oracles.py`` recorded as needing doing - its own
#: copy of the word had no shipped name to source from except the frozenset
#: below, which would have widened the population back to the pair.
REFERENCE_TYPE_WORD: Final = "ObjectProperty"

#: Value types that are a level reference followed by an object path. DERIVED
#: from the constant above rather than repeating its literal, so the membership
#: the reference join depends on cannot drift from the word it filters by.
_TWO_STRING_VALUES: Final = frozenset({REFERENCE_TYPE_WORD, "SoftObjectProperty"})

#: How many strings a decoded reference is. The GRAMMAR's number, not a
#: measurement of the corpus - :func:`_decode_object_reference` reads exactly
#: this many and returns None on anything else.
_REFERENCE_PARTS: Final = 2

#: The trailing int32 a SoftObjectProperty carries after its two strings. Its
#: WIDTH is pinned by exact consumption on all 116 instances; its meaning is
#: not claimed, which is why it is skipped rather than named.
_SOFT_OBJECT_TAIL_BYTES: Final = 4

#: A guid, wherever one appears in a tag - after a set guid flag, and inside a
#: StructProperty's tag data. Both are stepped over rather than read: their
#: WIDTH is pinned by the walk, which desynchronises immediately at any other,
#: and this module has no use for the value.
GUID_BYTES: Final = 16

# ---------------------------------------------------------------------------
# THE WIDTH SHIPPING RULE AND THE BYTE-ORDER STATUS, BOTH AS DATA
#
# CS-422 asks when a width may ship and CS-421 clause 3 asks what is actually
# open about a fixed-width value's byte order. Both were prose, and prose is
# what a reader has to classify for themselves. Both are now codes plus tables,
# so a test holds the shipped tables against them in one run. The tests that do
# the holding are named here rather than in the doc-comments below, because the
# citation checker reads a column-0 block and is blind to a "#:" line (CS-457).
#
#   THE WIDTH GROUNDS are hand-authored per width, deliberately NOT built by a
#   comprehension over the two width classes. A comprehension would compare a
#   set with itself and could not notice a width added to one shipped table and
#   left ungrounded, which is the defect the first draft of this item was
#   refuted on.
#   tests/save/test_width_rule.py::test_every_shipped_width_names_a_
#   criterion_the_rule_admits holds the grounds against the two classes, and
#   tests/save/test_width_rule.py::test_the_rule_prose_names_every_
#   code_it_governs scans the rule's own text for each code by name.
#
#   THE DECLINES carry a code from the closed vocabulary rather than a sentence
#   a reader has to classify.
#   tests/save/test_width_rule.py::test_every_decline_carries_a_
#   reason_code_from_the_closed_set grades the codes,
#   tests/save/test_width_rule.py::test_every_unmeasured_word_that_
#   ships_a_tag_extra_width_is_declined grades the key set against the shipped
#   tag-extra table, and
#   tests/save/test_width_rule.py::test_the_exception_set_is_
#   derived_from_the_codes grades the exception set as a derivation rather than
#   as a second transcription of the same classification.
#
#   THE BYTE-ORDER STATUS is CS-421 clause 3. The vacuous members are computed
#   from the shipped widths, so a width that stops being one byte stops being
#   vacuous with no sentence edited anywhere.
#   tests/save/test_value_anchoring.py::test_every_one_byte_value_type_
#   is_recorded_as_byte_order_vacuous is what holds that derivation.
#
#   THE WIDTH TABLE'S OWN MEMBERSHIP is what that derivation rests on, and
#   nothing bounded it until CS-481: a word placed in the table needs no tag
#   reader, no decoder agreement and no exemption, because the vacuity branch
#   answers on arithmetic. Two library-free controls bound it now and they read
#   different things, which is why there are two.
#   tests/save/test_byte_order_status.py::test_no_word_carries_a_byte_
#   order_status_the_module_records_as_unclaimed holds the status mapping
#   against UNMEASURED_PAYLOAD_REGIONS, this module's own record of what it
#   claims nothing about, so a width entry cannot stand while a region entry
#   contradicts it.
#   tests/save/test_byte_order_status.py::test_every_fixed_width_word_
#   is_one_the_shipped_walk_counts_as_measured asks the WALK rather than a set:
#   a tag declaring a size the table refuses has to come back counted as a
#   measured type whose bytes disagreed, and not as unmeasured content.
#   tests/save/test_properties.py::test_no_type_word_sits_on_both_sides_
#   of_the_module_s_own_split is the same contradiction one table along, over
#   the measured set rather than over the status data. NEITHER SUBSUMES THE
#   OTHER and that is measured on the reproduction: it holds its word out of
#   MEASURED_VALUE_TYPES, so the intersection that one asserts stays empty
#   while the status mapping contradicts the region table.
#
#   THE TAG-CARRIED EXEMPTION is the other subtrahend of the key bound, and
#   CS-480 derived it from the two shipped sites rather than listing it. That
#   left a route that edits BOTH of them, which is what CS-487 came back for.
#   tests/save/test_byte_order_status.py::test_no_word_the_exemption_admits_
#   is_one_the_module_declines_to_measure is the arm aimed at it, by reading
#   MEASURED_VALUE_TYPES - which neither of those two sites can move, both being
#   function bodies. THAT TABLE IS DERIVED FROM THE WIDTH TABLE, so a width
#   entry enters it for free and this arm is silent on that route. It is also
#   satisfied for free by a word ALREADY in the table, which is why the
#   derivation's saturation arm was widened to every table this module reads a
#   value out of the payload from. The first arm's docstring owns the measured
#   price and the routes that still work; CS-490 owns what survives.
#
#   THE SURVIVING CANDIDATES are the permutations the VALUE oracles leave
#   standing beside the identity, which is now none of them.
#   tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_
#   is_what_the_value_oracles_cannot_separate derives the set from those oracles
#   at runtime and compares it with the shipped literal.
#
#   THE THIRD ORACLE - the one that separates the middle pair the two shipped
#   ones cannot - is mantissa coarseness, CS-469. NO COUNT OF ITS GRADERS IS
#   WRITTEN HERE; two enumerations of them disagreed once already, so they are
#   listed and not tallied.
#   tests/save/test_value_anchoring.py::test_the_mantissa_coarseness_oracle_
#   separates_the_middle_swap_from_the_identity is the claim.
#   tests/save/test_value_anchoring.py::test_the_coarseness_tie_boundary_is_
#   the_mantissa_that_fits_in_the_low_stored_byte derives the boundary twice by
#   two routes and is where the non-circularity rests.
#   tests/save/test_value_anchoring.py::test_the_mantissa_bits_inside_the_
#   low_stored_byte_separate_no_ordering_from_its_swap pins that boundary from
#   above - it cannot fail on any corpus and its docstring says so.
#   tests/save/test_value_anchoring.py::test_the_coarseness_verdict_does_not_
#   depend_on_which_mantissa_width_it_scores pins it from below and quantifies
#   the verdict over every width so no threshold was fitted.
#   tests/save/test_value_anchoring.py::test_the_coarseness_predicate_cannot_
#   pass_both_readings_of_a_swapped_pair is the predicate's library-free control.
#   tests/save/test_value_anchoring.py::test_the_scored_population_is_exactly_
#   what_the_middle_swap_changes grades the admission helper, and
#   tests/save/test_value_anchoring.py::test_the_coarseness_census_reads_the_
#   value_the_shipped_decoder_reads grades the census's OWN offset and its OWN
#   population at the call site - the two things every other test above is blind
#   to.
#
#   tests/save/test_value_anchoring.py::test_the_declared_size_field_census_
#   narrows_the_byte_orders_to_two is the DIFFERENT-FIELD narrowing whose
#   boundary is written down beside that literal. IT IS STILL A NARROWING TO
#   TWO, and the value result reaching one licenses nothing about it.
#
#   THE DECLARED EXTENT is the other half of what a fixed-width read may touch,
#   and it is a different question from which order the bytes inside it are in.
#   tests/save/test_value_anchoring.py::test_no_fixed_width_value_depends_
#   on_a_byte_outside_its_declared_extent is the claim and
#   tests/save/test_value_anchoring.py::test_the_extent_anchor_control_
#   catches_a_displaced_fixed_width_read is its control.
# ---------------------------------------------------------------------------

#: THE CRITERIA THE RULE ADMITS - CS-422. A width ships on one of these. They
#: are codes rather than sentences so that a shipped width can be held against
#: them mechanically instead of being read and judged.
CRITERION_CURSOR_REACH: Final = "cursor_reach"
CRITERION_VALUE_DISAGREEMENT: Final = "value_disagreement"
WIDTH_CRITERIA: Final = frozenset({CRITERION_CURSOR_REACH, CRITERION_VALUE_DISAGREEMENT})

#: THE REASONS THE RULE EXPLICITLY DISCLAIMS, kept as a closed set beside the
#: criteria and disjoint from them. A reading declined on one of these is an
#: EXCEPTION to the rule rather than an application of it, and naming the two
#: apart is what keeps that difference legible without a reader having to
#: classify a paragraph.
#:
#: ``no_discrimination_test`` IS THE HONEST CODE FOR A REGION NOBODY HAS PUT A
#: CONTROL TO, and it is distinct from ``sample_size``. Sample size says the
#: instances exist and are too few to separate the answers; this one says the
#: question was never put. Recording the second as the first reads as a
#: measurement of a population when no measurement was taken.
REASON_SAMPLE_SIZE: Final = "sample_size"
REASON_SHIPPED_ALIGNMENT_ONLY: Final = "shipped_alignment_only"
REASON_NO_DISCRIMINATION_TEST: Final = "no_discrimination_test"
WIDTH_NON_CRITERIA: Final = frozenset(
    {REASON_SAMPLE_SIZE, REASON_SHIPPED_ALIGNMENT_ONLY, REASON_NO_DISCRIMINATION_TEST}
)

#: THE ONE RULE GOVERNING WHEN A WIDTH MAY SHIP - CS-422. This file used to
#: apply two standards to itself with nothing stated between them: it shipped a
#: width on a handful of instances and declined one on thousands.
#:
#: SAMPLE SIZE WAS NEVER THE OPERATIVE CRITERION, which is what dissolves that
#: apparent inconsistency rather than excusing it. A handful of instances are
#: enough when all of them are discriminated, and thousands are not enough when
#: the reading was never put through a discrimination test at all.
#:
#: THE RULE NAMES ITS OWN CODES, and what that buys is narrow enough to state
#: exactly. The codes are tied to the vocabulary BY NAME, so a rule text that
#: stops naming one of them is caught. NOTHING READS WHAT THE RULE SAYS - the
#: check is a substring scan, so a text that names every code and governs
#: nothing, or names every code and inverts the rule, passes it.
WIDTH_SHIPPING_RULE: Final = (
    "A width may ship when mis-stating it changes an observable outcome on at "
    "least one real payload. Which outcome depends on what the width moves, "
    "which is why one oracle cannot grade both classes. A width that advances "
    "the cursor ships on cursor_reach; a width that only bounds a value's "
    "extent ships on value_disagreement; those two are the whole of what this "
    "rule admits. sample_size, shipped_alignment_only and no_discrimination_test "
    "are NOT criteria of this rule, and a reading declined on any of the three "
    "is recorded as an exception to the rule rather than as an application "
    "of it."
)

#: Widths that ADVANCE THE CURSOR. Mis-stating one desynchronises the walk, so
#: it is graded by how many payloads still reach a terminator.
CURSOR_WIDTHS: Final = frozenset(_TAG_EXTRA_STRINGS) | {"GUID_BYTES"}

#: Widths that only BOUND A VALUE'S EXTENT. The cursor advances by the tag's own
#: declared size, so mis-stating one CANNOT desynchronise the walk - it drops the
#: value, which is reported as a disagreement. Grading these by terminator reach
#: reports them undetectable when they are in fact detected, and that mistake is
#: how the two standards got into one file.
EXTENT_WIDTHS: Final = frozenset(_FIXED_WIDTH_VALUES) | {"_SOFT_OBJECT_TAIL_BYTES"}

#: WHICH CRITERION EACH SHIPPED WIDTH RESTS ON - CS-422, as shipped DATA. It
#: covers the union of the two classes above, keyed by the same names those
#: classes use: a type word where the width is the tag-extra count for that
#: word, and the constant's own name where the width is a module constant.
#:
#: HAND-AUTHORED ENTRY BY ENTRY, AND THAT IS THE WHOLE MECHANISM. Deriving this
#: with a comprehension over :data:`CURSOR_WIDTHS` and :data:`EXTENT_WIDTHS`
#: would make it a restatement of those two sets - a set compared with itself,
#: which grades nothing and is exactly the defect this item was sent back for.
#: Written out, it is an INDEPENDENT fifth source: adding an entry to
#: ``_TAG_EXTRA_STRINGS`` or to ``_FIXED_WIDTH_VALUES`` and stopping there
#: leaves that width with no ground recorded here, and the test named in the
#: commentary block above turns red on it. DO NOT COLLAPSE THIS INTO A
#: COMPREHENSION - the redundancy is the point of the table.
WIDTH_SHIPPING_GROUNDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "ArrayProperty": CRITERION_CURSOR_REACH,
        "ByteProperty": CRITERION_CURSOR_REACH,
        "EnumProperty": CRITERION_CURSOR_REACH,
        "MapProperty": CRITERION_CURSOR_REACH,
        "SetProperty": CRITERION_CURSOR_REACH,
        "StructProperty": CRITERION_CURSOR_REACH,
        "GUID_BYTES": CRITERION_CURSOR_REACH,
        "FloatProperty": CRITERION_VALUE_DISAGREEMENT,
        "Int8Property": CRITERION_VALUE_DISAGREEMENT,
        "IntProperty": CRITERION_VALUE_DISAGREEMENT,
        "UInt32Property": CRITERION_VALUE_DISAGREEMENT,
        "_SOFT_OBJECT_TAIL_BYTES": CRITERION_VALUE_DISAGREEMENT,
    }
)

#: VALUE readings DECLINED under the rule above, each recorded against the rule
#: rather than decided on its own terms. This records WHY, so a later slice
#: re-opening one knows what would settle it.
#:
#: EACH ENTRY IS A ``(reason code, prose)`` PAIR and the code is drawn from
#: ``WIDTH_CRITERIA | WIDTH_NON_CRITERIA``. The pair shape is what makes the
#: classification machine-readable: the prose says what a later slice needs to
#: know, and the code says which side of the rule the decline sits on without
#: anyone having to parse the prose to find out.
#:
#: A DECLINE CAN CARRY AN ADMITTED CRITERION, AND THAT IS A DIFFERENT STATE
#: FROM AN EXCEPTION. Two things can be true of a declined reading and
#: collapsing them loses the distinction the rule exists to draw:
#:
#: - THE TEST WAS RUN AND THE READING FAILED IT. The code is then one of
#:   :data:`WIDTH_CRITERIA`, and the decline is an APPLICATION of the rule - the
#:   rule was applied and its answer was no.
#: - THE TEST WAS NEVER RUN, or the reason offered is not one the rule uses. The
#:   code is then one of :data:`WIDTH_NON_CRITERIA`, and the decline is an
#:   EXCEPTION to the rule.
#:
#: Every entry today is in the second state. The first is the state CS-456 will
#: produce when it measures the family. Admitting both vocabularies is what
#: keeps :data:`WIDTH_RULE_EXCEPTIONS` from being this table's key set by
#: construction. WHAT THAT GUARDS IS RE-TRANSCRIPTION, NOT CLASSIFICATION, and
#: the difference is measured rather than reasoned: the shipped constant and the
#: test evaluate the SAME comprehension over the SAME mapping, so reclassifying
#: a decline onto an admitted criterion and re-deriving leaves the suite green.
#: Which code an entry carries is an author's judgement that no check grades.
#:
#: THE PROSE POINTS AT :data:`UNMEASURED_PAYLOAD_REGIONS` AND RESTATES NOTHING
#: FROM IT. Every key here also has an entry there, that table owns the
#: populations, and each code below is chosen from what that entry ALREADY
#: RECORDS rather than from a fresh judgement made here. A figure copied across
#: would be a restated measurement, which is the drift ``CLAUDE.md`` section 4
#: forbids - so these entries carry no figure at all and point instead.
#:
#: IT IS ABOUT VALUE READINGS AND NOT ABOUT TAG-EXTRA WIDTHS, which matters
#: because one type word can carry both. `StructProperty` appears here AND in
#: :data:`CURSOR_WIDTHS`: its tag-extra width ships and is discriminated, while
#: its VALUE reading is declined. Keying this by the bare type word once read as
#: though the whole word were declined, which is why the distinction is stated
#: rather than left to the name.
#:
#: THREE ENTRIES LEFT THIS TABLE RATHER THAN BEING RE-JUSTIFIED IN IT - CS-830.
#: The three container words were declined here, each pointing at a region entry
#: for its population. Their element framing is measured now, so the decline is
#: retired and the region entries with it; what a reader wants in their place is
#: :data:`CONTAINER_TYPE_WORDS` and the commentary block above it. A DECLINE IS
#: WITHDRAWN BY MEASURING THE READING, never by softening the reason, and the
#: shape of this table is what makes the difference visible: a withdrawn decline
#: leaves no entry at all, where a softened one would leave an entry carrying a
#: gentler code.
DECLINED_VALUE_READINGS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "TextProperty": (
            REASON_SAMPLE_SIZE,
            "declined on SAMPLE SIZE, which is a criterion the rule above does "
            "not use, so this entry is an exception to the rule rather than an "
            "application of it. Whether a wrong width for it is discriminated "
            "at all is UNMEASURED. Recorded honestly rather than re-justified: "
            "the decline may well be right, and the reason given for it is not. "
            "The code comes from the TextProperty entry of "
            "UNMEASURED_PAYLOAD_REGIONS, which owns the population and the one "
            "declared size it is seen at and records that the instances present "
            "cannot distinguish the cases of a tagged union",
        ),
        "StructProperty": (
            REASON_NO_DISCRIMINATION_TEST,
            "declined for the NATIVE form only, which is a narrowing of the "
            "whole-type decline this entry used to record. NO FIGURE IS WRITTEN "
            "HERE - the StructProperty entry of UNMEASURED_PAYLOAD_REGIONS owns "
            "the population and this points at it. "
            "A discrimination test HAS now been put to the tag_list form: the "
            "tag-grammar chain admits exactly one end per site out of every end "
            "the declared size allows, a wrong reading refuses, and the interior "
            "names cross-check against the fields the shipped usmap declares "
            "for that struct - see the "
            "StructProperty entry of UNMEASURED_PAYLOAD_REGIONS. What is still "
            "declined is the native form, where the width is whatever the bytes "
            "are and every partition closes by arithmetic, so no reading of it "
            "could have failed. What would settle THAT is an element width a "
            "shipped asset states, or any cross-check a misdeclaration would "
            "break. THE TYPE STAYS OUT OF MEASURED_VALUE_TYPES until it does",
        ),
    }
)

#: THE DECLINES THAT ARE EXCEPTIONS TO THE RULE RATHER THAN APPLICATIONS OF IT,
#: DERIVED from the codes above rather than transcribed. A written-out set would
#: put the same classification in two places, and the copy is the one that goes
#: stale while still reading as authoritative.
#:
#: IT IS A PROPER SUBSET IN PRINCIPLE. A decline carrying a code from
#: :data:`WIDTH_CRITERIA` is an application of the rule and is absent from this
#: set - see the two states recorded above. That every entry lands here TODAY is
#: a fact about today's table rather than a property of the derivation, and the
#: first decline recorded against an admitted criterion drops out of this set
#: with nothing edited here.
#:
#: WHAT THE DERIVATION BUYS IS THAT THIS SET CANNOT BE HAND-WRITTEN OUT OF STEP
#: WITH THE CODES. It buys nothing about whether a given entry carries the right
#: code - the test recomputes this same comprehension over this same mapping, so
#: a decline moved onto an admitted criterion is reported by both alike.
WIDTH_RULE_EXCEPTIONS: Final = frozenset(
    word for word, (code, _) in DECLINED_VALUE_READINGS.items() if code in WIDTH_NON_CRITERIA
)

#: THE BYTE-ORDER STATUS OF EACH FIXED-WIDTH SCALAR VALUE - CS-421 clause 3.
#:
#: THREE STATUSES, WHICH IS NOT THE SAME AS THREE OPEN QUESTIONS, and that is
#: the whole correction. This module's evidence about byte order read as though
#: every fixed-width type were equally unsettled. Two of them are not questions
#: at all, because a one-byte value has exactly one byte order.
BYTE_ORDER_VACUOUS: Final = "vacuous_one_byte"
BYTE_ORDER_ANCHORED_NOT_UNIQUE: Final = "anchored_not_unique"
BYTE_ORDER_UNSCORED: Final = "unscored"

#: AN ORACLE EXISTS, WAS APPLIED TO THIS TYPE'S OWN VALUES, AND CANNOT TELL THE
#: TWO READINGS APART - CS-421 clause 3, route (b).
#:
#: IT IS NOT :data:`BYTE_ORDER_UNSCORED` AND THE DIFFERENCE IS THE WHOLE REASON
#: THE WORD EXISTS. ``unscored`` says nothing looked. This says something looked,
#: with a shipped oracle, at this type's own values, and that EVERY one of them
#: carried the oracle's signature under BOTH readings - so the oracle scores the
#: as-stored reading and the reversed one alike and prefers neither.
#:
#: IT IS NOT A SETTLEMENT, and it must never be read as one. The question stays
#: open; what this records is that a particular oracle has already been tried and
#: is not the thing that will close it.
#:
#: READINGS, NOT ORDERINGS, AND THE SPELLING SAYS SO BECAUSE AN EARLIER ONE DID
#: NOT. The word is about the as-stored reading against its reversal. It does NOT
#: say the oracle is blind across the whole permutation group - measured, it
#: separates half of that group on this very population - and an unqualified
#: "cannot separate" was an over-claim an adversary caught before it shipped.
#:
#: WHAT IT IS NOT EVIDENCE OF. The verdict is a fact about the values this
#: library happens to carry, not a structural property of the oracle meeting the
#: type: a population of the same size and shape carrying almost any other value
#: would drive the same oracle to a green verdict instead. That is recorded where
#: it is derived, and it is why CS-421 did not close ON this word: the close of
#: 2026-08-23 amended its clause 3 and filed this word's population as CS-825,
#: rather than reading the word as a settlement. It still is not one.
#:
#: WHY IT IS NOT :data:`BYTE_ORDER_VACUOUS`: that word is arithmetic about a
#: WIDTH - one byte has one order. This is a fact about an ORACLE meeting a
#: POPULATION, and either side of that could change without the width moving.
BYTE_ORDER_ORACLE_CANNOT_SEPARATE: Final = "oracle_cannot_separate_readings"
BYTE_ORDER_STATUSES: Final = frozenset(
    {
        BYTE_ORDER_VACUOUS,
        BYTE_ORDER_ANCHORED_NOT_UNIQUE,
        BYTE_ORDER_ORACLE_CANNOT_SEPARATE,
        BYTE_ORDER_UNSCORED,
    }
)

#: A value of this width has one byte order, so its order is not open. Named
#: rather than written as a literal in :func:`_byte_order_status`, so the reason
#: travels with the number.
_SINGLE_BYTE_WIDTH: Final = 1

#: The fixed-width types a shipped byte-order oracle actually scores. The
#: oracles are cited in the commentary block above ``_TAG_EXTRA_STRINGS``. A
#: type outside this set and wider than one byte has been scored by nothing,
#: which is what :data:`BYTE_ORDER_UNSCORED` records.
#:
#: THIS SET IS HAND-WRITTEN AND IT IS GRADED - CS-476. It is written here rather
#: than derived because the derivation lives on the other side of the seam: what
#: a type word is scored by is a fact about the test oracles, and this module
#: does not read them. So the tie is asserted from the test side instead, by
#: probing the oracles for which words their judgement actually turns on:
#: tests/save/test_byte_order_status.py::test_no_type_is_marked_anchored_that_no_oracle_scores
#: is the over-claim direction and
#: tests/save/test_byte_order_status.py::test_no_type_an_oracle_scores_is_left_recorded_as_unscored
#: is the other.
#:
#: THIS SET IS ALSO GRADED DIRECTLY AND NOT ONLY THROUGH WHAT IT PRODUCES, by
#: tests/save/test_byte_order_status.py::test_the_hand_written_anchored_set_holds_no_unscored_type
#: - because grading the mapping alone does not reach all of it. A ONE-BYTE word
#: added here is swallowed by the width branch in :func:`_byte_order_status`,
#: which answers first, so it never appears in the mapping and every test over
#: the mapping stays green while this set says something false.
#:
#: WHAT WAS MEASURED, each with a REAL SOURCE EDIT - the mapping below is a
#: comprehension evaluated at import, so an in-process patch of this set leaves
#: it stale and grades a value nothing shipped. Before those tests existed:
#: adding a wider word here that no oracle scores left the save suite green;
#: deleting a word from the mapping below left it green; adding a one-byte word
#: here left it green; and exchanging the string values of BYTE_ORDER_VACUOUS
#: and BYTE_ORDER_ANCHORED_NOT_UNIQUE left it green while the shipped data
#: claimed an oracle backs two one-byte types.
#:
#: RE-DERIVING THAT PRE-STATE NEEDS THIS COMMENT BLOCK REMOVED TOO, and the
#: recipe is written down because it is not obvious. The citations above name a
#: test module by path, so moving that module aside to reproduce the old green
#: turns the package-wide citation resolver RED on a dead citation, plus the
#: phase-4 gate that runs behind it. Those two failures are not the byte-order
#: question and must not be read as it. Take the measurement at a commit before
#: this block, or delete this block along with the module.
_BYTE_ORDER_ANCHORED_VALUES: Final = frozenset({"IntProperty", "FloatProperty"})

#: THE TYPES A SHIPPED ORACLE WAS APPLIED TO AND CAME BACK UNDECIDED ON - CS-421
#: clause 3, route (b). See :data:`BYTE_ORDER_ORACLE_CANNOT_SEPARATE` for what
#: the word claims; this is the population it is claimed of.
#:
#: THIS IS A THIRD HAND-WRITTEN SET AND ITS BOUND IS STATED RATHER THAN IMPLIED.
#: It sits here for the same seam reason :data:`_BYTE_ORDER_ANCHORED_VALUES`
#: does - what an oracle can separate is a fact about the TEST oracles meeting
#: the operator's library, and this module reads neither. What is different from
#: the set above is that this one is graded against a DERIVATION rather than
#: against a probe of which words a dispatch branches on:
#: tests/save/test_value_anchoring.py::test_the_cannot_separate_status_is_derived_from_the_oracle
#: applies the shipped int32 oracle to every four-byte type's own values and
#: requires this set to equal, in BOTH directions, the words it scores
#: identically as stored and reversed.
#:
#: THE RESIDUAL IS THAT THE DERIVATION IS LIBRARY-BACKED AND SKIPS WITHOUT ONE.
#: On a machine with no game installed this set is ungraded, which is CS-426's
#: recorded gap and is not closed here. What DOES still grade it on such a
#: machine is narrower and is stated where it lives:
#: tests/save/test_byte_order_status.py::test_the_cannot_separate_set_is_bounded_without_a_library
#: holds it disjoint from the anchored set, free of one-byte words the width
#: branch would swallow, and free of any word the shipped dispatch already
#: scores. That is a bound, not the verdict - it cannot tell this status from
#: :data:`BYTE_ORDER_UNSCORED`, and only the library-backed derivation can.
#:
#: WHAT WAS MEASURED, with a REAL SOURCE EDIT in each case, because the mapping
#: below is a comprehension evaluated at import and an in-process patch of this
#: set leaves it stale and grades a value nothing shipped. Before the derivation
#: existed, recording this status for a type no oracle had been applied to left
#: the whole save suite green - it is the CS-476 over-claim in a new spelling,
#: and a spelling the vocabulary bound admits by construction once the word is
#: declared.
_BYTE_ORDER_CANNOT_SEPARATE_VALUES: Final = frozenset({"UInt32Property"})


def _byte_order_status(word: str, width: int) -> str:
    """Classify one fixed-width value type's byte-order question.

    VACUITY IS COMPUTED FROM THE SHIPPED WIDTH RATHER THAN LISTED. If a type's
    measured width ever changes from one byte to more, this stops calling its
    byte order vacuous on the same edit that changes the width, instead of
    waiting for someone to remember a sentence elsewhere.

    THE BRANCHES ARE ORDERED AND THE ORDER HIDES THINGS, which is why two of the
    three populations are graded directly and not only through what this
    returns. A one-byte word in either named set never reaches its own branch,
    and a word in both named sets silently takes the earlier one. Neither is
    visible to a test that reads only :data:`VALUE_BYTE_ORDER_STATUS`.

    Args:
        word: The type word.
        width: Its measured value width, from :data:`_FIXED_WIDTH_VALUES`.

    Returns:
        One of :data:`BYTE_ORDER_STATUSES`.
    """
    if width == _SINGLE_BYTE_WIDTH:
        return BYTE_ORDER_VACUOUS
    if word in _BYTE_ORDER_ANCHORED_VALUES:
        return BYTE_ORDER_ANCHORED_NOT_UNIQUE
    if word in _BYTE_ORDER_CANNOT_SEPARATE_VALUES:
        return BYTE_ORDER_ORACLE_CANNOT_SEPARATE
    return BYTE_ORDER_UNSCORED


#: The status per value type, over the fixed-width scalars this module reads.
#:
#: ANCHORED IS NOT UNIQUE, and the status word still says so even though
#: :data:`BYTE_ORDER_SURVIVING_CANDIDATES` is now a singleton. THE TWO ARE
#: ABOUT DIFFERENT THINGS AND THE DIFFERENCE IS MEASURED RATHER THAN ASSERTED.
#: This status is per TYPE and records what THAT type's own scored population
#: settles; the candidate set is the JOINT intersection over both scored
#: populations. Measured: the oracles reading float32 values leave more than one
#: ordering standing between them, and so do the ones reading int32 values, and
#: only intersecting across both reaches one. So no single type here has a
#: uniquely pinned order, and calling one pinned would carry a result from a
#: population that did not produce it.
#:
#: ``BoolProperty`` IS WRITTEN IN EXPLICITLY BECAUSE ITS BYTE IS NOT IN
#: ``_FIXED_WIDTH_VALUES``. Its value byte rides in the TAG - :func:`_read_tag_header`
#: takes it as a single byte at a fixed offset and hands it back separately - so
#: there is no entry in that table to derive a width from. It is one byte, so
#: its byte order is vacuous for the same reason the derived members are.
#:
#: WHAT BOUNDS A HAND-WRITTEN ENTRY HERE - CS-487. A word written in beside that
#: one is exempt from the key bound only while the two shipped tag-carried sites
#: agree it is tag-carried, and CS-480 derived exactly that. AN EDIT TO BOTH
#: SITES ANSWERS BOTH, which is why the exemption also has to intersect a table
#: those two sites cannot move: a word this module builds a value for and
#: :data:`MEASURED_VALUE_TYPES` does not name is the module recording a settled
#: byte order for a type it also records as one it does not decode. THAT ARM IS
#: NOT THE WHOLE OF WHAT BOUNDS THE EXEMPTION - the derivation's saturation arm
#: was widened in the same work, because an attacker who PICKS a word already in
#: that table rather than adding one satisfies the arm for free. Both are named
#: in the commentary block above, and the second of them owns the measured price
#: of every route that still works. No count is restated here.
VALUE_BYTE_ORDER_STATUS: Final[Mapping[str, str]] = MappingProxyType(
    {
        **{
            word: _byte_order_status(word, width)
            for word, (width, _) in _FIXED_WIDTH_VALUES.items()
        },
        "BoolProperty": BYTE_ORDER_VACUOUS,
    }
)

#: THE BYTE PERMUTATIONS THE VALUE ORACLES CANNOT SEPARATE FROM THE IDENTITY.
#: Each tuple is a permutation of STORED byte positions, and this set now holds
#: the identity alone: three oracles between them rule out every rearrangement
#: of a four-byte value's stored bytes.
#:
#: A SINGLETON HERE IS A NARROW CLAIM, NOT A BROAD ONE, and reading it as
#: "the byte order is settled everywhere" is the overclaim this constant exists
#: to prevent. It says exactly that no ordering other than the as-stored one
#: survives all three oracles over the operator's library. It says nothing about
#: any field this module's fixed-width VALUE reader does not read.
#:
#: HOW THE THREE ORACLES DIVIDE THE WORK, because the mechanism is the reason
#: the set is the size it is and an earlier account of it was measured false.
#: NO ORACLE HERE TURNS ON BOTH EXTREMES. The int32 oracle holds exactly for the
#: orderings that leave the LOW position alone, and survives orderings that move
#: the most significant byte. The float32 magnitude oracle holds exactly for the
#: orderings that leave the HIGH position alone, and survives orderings that
#: move the low byte. Intersecting those two one-ended constraints fixes both
#: ends and leaves the pair differing only in the two MIDDLE bytes - which is
#: where the set stood, and why.
#:
#: THE MIDDLE PAIR IS SEPARATED BY MANTISSA COARSENESS - CS-469 - AND THE
#: OBSTACLE WAS NEVER THE DATA. The corpus held the evidence throughout: the
#: census's admitted population is the float32 values whose middle bytes differ,
#: and the run that measures it reports how many there are. What could not use
#: that evidence is the float oracle's magnitude band, and THAT IT CANNOT IS A
#: DERIVED FACT rather than a described one - the middle swap survives that
#: oracle in the runtime derivation, which is asserted by the test named in the
#: commentary block above.
#:
#: NO NUMBER AND NO MECHANISM IS WRITTEN HERE FOR IT. Three were offered in
#: successive revisions - a bound of a factor of two, then a bound approaching
#: four, then an appeal to a shipped count that measures the whole-word REVERSAL
#: and not the middle swap - and all three were measured FALSE. The conclusion
#: did not rest on any of them and does not need a fourth.
#:
#: WHAT COARSENESS ASKS INSTEAD: an authored float - a clock speed, a snapped
#: coordinate, a fraction a designer typed - needs few significant mantissa
#: bits, so its low mantissa bits are zero, and a wrong ordering destroys that.
#: Counting how many values keep it separates the pair.
#: Do not record, here or downstream, that this question was ever data-blocked.
#:
#: THE RESULT IS JOINT ACROSS BOTH SCORED POPULATIONS AND NO SINGLE TYPE'S
#: EVIDENCE PRODUCES IT. Measured: the float32 oracles together still leave more
#: than one ordering standing, and so do the int32 oracle's own survivors
#: intersected with coarseness. Only all three together reach one. That is why
#: :data:`VALUE_BYTE_ORDER_STATUS` still records what a single type's own
#: oracles settle, which is less than what this set records.
#:
#: The set is DERIVED FROM THE ORACLES at runtime by the tests named in the
#: commentary block above and compared against this literal, in that direction:
#: the literal narrows when the derivation narrows. Deleting an oracle widens
#: what survives and reddens the derivation rather than quietly leaving a
#: stronger claim on the books.
#:
#: THE OTHER RESULT IS ABOUT A DIFFERENT FIELD, READ BY A DIFFERENT READER, AND
#: IT LICENSES NOTHING HERE. There is a separate result over the tag's declared
#: SIZE field, censused across all twenty-four orderings of its four bytes.
#:
#: THAT RESULT IS A NARROWING TO TWO AND NOT A SETTLEMENT, which is the same
#: SHAPE as the candidate set above rather than a stronger kind of answer. The
#: as-stored ordering reaches more payloads than any other, but the runner-up
#: only swaps the two HIGH size bytes - and those are both zero for any declared
#: size small enough to leave them so. The census therefore separates the two
#: only on the payloads carrying a size large enough to tell them apart, and
#: that margin is a count the census prints in the run that measures it rather
#: than a figure written here. Several other orderings still leave a majority of
#: payloads reaching. Shipping that one as "exactly one order" while shipping
#: this one as a candidate set would be an asymmetry inviting exactly the
#: inference the rest of this paragraph declines to make.
#:
#: That field is read by :func:`_read_tag_header`; a property VALUE is read by
#: :func:`_decode_fixed_width`. Carrying the first result across to the second
#: needs the premise that this format uses one byte order for every int32 field.
#: THAT PREMISE IS AN ASSUMPTION AND NOT A MEASUREMENT. It is not made here, and
#: the boundary is written down rather than crossed.
BYTE_ORDER_SURVIVING_CANDIDATES: Final[frozenset[tuple[int, int, int, int]]] = frozenset(
    {
        (0, 1, 2, 3),
    }
)

# ---------------------------------------------------------------------------
# CS-830 - the CONTAINER element framing
#
# WHAT A CONTAINER DECODE CLAIMS. The element COUNT, the element type word or
# words, and the EXTENT of every element - where each one starts and how many
# bytes it spans - and those only when the elements so bounded consume the
# tag's declared size EXACTLY. A VALUE comes back only for an element whose own
# type word this module already decodes at top level.
#
# WHAT IT REFUSES TO CLAIM. A `StructProperty` element comes back as a bounded,
# typed region carrying no value at all. The struct INTERIOR is CS-829, and
# reading it here would be this module publishing a guess about a grammar
# nobody has measured. `CONTAINER_ADJACENT_OWNERS` records that hand-off as
# data rather than as a sentence, and the test named below turns red if a
# container-shaped word ever arrives in the shipped tables with no item behind
# it.
#
# THE THREE SHAPES ARE ORDERED BY STRENGTH AND THE ORDER IS LOAD-BEARING, not a
# preference. A SELF-DELIMITING reading is the element's own grammar saying
# where it ends and is falsifiable - get it wrong and the region does not
# close. The two DERIVED readings are weaker, and are reached only where the
# self-delimiting reading has already failed to close. MEASURED, which is why
# the fallback is not an alternative: taken as alternatives, both closed on a
# large majority of the struct arrays, because a container holding ONE element
# is divided by one and any width closes it. Which shape bounded a given
# container therefore travels on the value, so a consumer can tell the strong
# reading from the weak one instead of being handed an average.
#
# THE ELEMENT GRAMMAR IS NOT THE TOP-LEVEL VALUE GRAMMAR, and conflating them
# is the mistake this block exists to avoid. Inside a container an element
# carries no tag, no index field, no guid flag and no declared size, so
# `_FIXED_WIDTH_VALUES` and `_ONE_STRING_VALUES` do not describe it. The two
# tables below describe it, and a word in them is a claim about an ELEMENT and
# never about a top-level value - which is why a word can appear there and not
# in :data:`MEASURED_VALUE_TYPES`.
#
# THE COUNTS ARE DELIBERATELY NOT WRITTEN HERE. The operator plays this game,
# so a population figure in this comment would be false on the next autosave -
# CLAUDE.md section 4. What the corpus says on any given day is derived on
# every run by the sweep in tests/save/test_container_elements.py, and the
# equality it stands in is the acceptance.
# ---------------------------------------------------------------------------

#: The type words whose value is a COUNTED SEQUENCE of elements - CS-830.
#:
#: NAMED RATHER THAN DERIVED, DELIBERATELY. No shipped table equals this
#: triple: every candidate over-includes a word whose interior belongs to
#: another item. :func:`container_candidate_words` derives the wider set and
#: the test named in the commentary block above holds this triple against it,
#: so the transcription is GUARDED rather than pretended to be a derivation.
CONTAINER_TYPE_WORDS: Final = frozenset({"ArrayProperty", "SetProperty", "MapProperty"})

#: Which item owns each container-adjacent word this module does NOT decode.
#: An entry here is a route to the work, not an excuse for the gap.
CONTAINER_ADJACENT_OWNERS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "StructProperty": "CS-829",
        "TextProperty": "CS-832",
    }
)

#: How many int32 fields stand between a container's value start and its
#: element count. MEASURED: the set and the map carry one field ahead of the
#: count and the array carries none. Mis-stating one shifts the count read by
#: four bytes, which the region then fails to close on.
_CONTAINER_LEAD_FIELDS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ArrayProperty": 0,
        "SetProperty": 1,
        "MapProperty": 1,
    }
)

#: How the shape that bounded a container's elements is recorded.
#:
#: `ELEMENT_SHAPE_SELF_DELIMITING` - every element half was bounded by its own
#: grammar: a stated width, a length-prefixed string, or a nested tag list
#: closed by the terminator name. The strongest of the three, and the only one
#: that is falsifiable element by element.
#: `ELEMENT_SHAPE_UNIFORM_WIDTH` - no element grammar applied, and one width
#: was DERIVED by dividing the element region by the number of slots. Its whole
#: discriminator is that the division is exact, so over a SINGLE slot it is the
#: identity and discriminates nothing.
#: `ELEMENT_SHAPE_SOLVED_WIDTH` - one half's width was derived by requiring the
#: region to close, and admitted only because exactly one width in the searched
#: range does. Ambiguity is refused rather than resolved by preference.
ELEMENT_SHAPE_SELF_DELIMITING: Final = "self_delimiting"
ELEMENT_SHAPE_UNIFORM_WIDTH: Final = "uniform_width"
ELEMENT_SHAPE_SOLVED_WIDTH: Final = "solved_width"
ELEMENT_SHAPES: Final = frozenset(
    {
        ELEMENT_SHAPE_SELF_DELIMITING,
        ELEMENT_SHAPE_UNIFORM_WIDTH,
        ELEMENT_SHAPE_SOLVED_WIDTH,
    }
)

# ---------------------------------------------------------------------------
# CS-830, NARROWED ON AN OPERATOR RULING - WHAT A BOUNDED ELEMENT DOES NOT SAY.
#
# THE ITEM WAS MERGED AND THEN REFUTED, and the two records below are what the
# refutation left standing. The distinction it turns on is between the EXTENT of
# a container's element region and the PARTITION of that region into elements.
#
# THE EXTENT IS READ. The tag declares the region's size, the walk requires the
# elements to consume it EXACTLY, and a region that does not close is refused
# rather than truncated. Nothing below weakens that, and it is the bulk of what
# a consumer needs: a container's element region is bounded, typed and stepped
# over exactly.
#
# THE PARTITION IS READ FOR ONE SHAPE AND DERIVED FOR ANOTHER. A
# SELF-DELIMITING element says where it ends in its own grammar, so a wrong
# reading fails to close and the container is refused - the boundaries are
# falsifiable one element at a time. A UNIFORM width is a SPAN DIVIDED BY A
# DECLARED COUNT, and its whole admission test is that the division came out
# even. That is a fact about two integers. It is not a fact about the bytes
# between them, and it does not become one by being checked.
#
# THE DIVISION IS A TAUTOLOGY ONCE IT IS EXACT, which is why no walk failure can
# be read as evidence for it. Under a forced width `_element_half_end` returns
# `at + width` after a bounds check that cannot fail while slots remain, so the
# walk consumes exactly `slots * width` bytes and closes by arithmetic. THE
# CONSEQUENCE IS THAT ANY OTHER PARTITION SUMMING TO THE SPAN WOULD ALSO CLOSE,
# including partitions that are wrong on any reading of the format. Measured, on
# this project's own corpus, by replacing the even division with a deliberately
# wrong one and re-running every library-backed equality: all of them stayed
# green - ``tests/save/test_container_elements.py`` under
# ``test_a_provably_wrong_partition_survives_every_library_backed_equality``.
#
# THE DECLARED COUNT IS NOT CROSS-CHECKED EITHER, and that is the same defect
# CS-830 caught in its own first draft wearing different clothes. A region truly
# holding a few wide elements, declared as one slot per byte, divides exactly
# and is published as that many one-byte elements. Nothing refuses it. The case
# is kept as a test rather than as a sentence, under
# ``test_a_uniform_region_is_partitioned_by_a_declared_count_nothing_cross_checks``.
#
# WHY THE DECODE IS KEPT RATHER THAN DELETED. The elements are still bounded and
# the region still closes; the unproven claim is narrower than the decode. What
# a consumer may rely on for a shape recorded below is the region, the count as
# DECLARED and the element type word - not the extent of any individual element.
#
# NO POPULATION FIGURE IS WRITTEN HERE - CLAUDE.md section 4. Which words are
# affected is a classification and is recorded as data; how many instances each
# holds changes on the operator's next autosave and is derived on every run.
# ---------------------------------------------------------------------------

#: The element shapes whose INTERNAL PARTITION nothing discriminates - the
#: boundaries between one element and the next are DERIVED rather than read, and
#: an equally-closing alternative partition would be accepted identically.
#:
#: A CONSUMER READS THIS BEFORE TRUSTING AN ELEMENT'S EXTENT. The shape word
#: already travels on :class:`ContainerValue`; this is what makes it actionable
#: rather than descriptive.
#:
#: THE SOLVED SHAPE IS DELIBERATELY ABSENT. It admits a width only when EXACTLY
#: ONE in the searched range closes the region and refuses ambiguity rather than
#: resolving it by preference, so its boundaries are pinned by the bytes.
UNDISCRIMINATED_ELEMENT_SHAPES: Final = frozenset({ELEMENT_SHAPE_UNIFORM_WIDTH})

#: The shapes a container whose tag declared a NATIVE-SERIALIZED value may not
#: be published under - see :func:`_decode_container`, which owns the argument.
#:
#: IT IS DERIVED RATHER THAN LISTED, and that is the anti-drift control rather
#: than brevity. Written out as its two members it would silently stop covering
#: a fourth shape the day one is added; derived as "every shape whose partition
#: was not read from the bytes", a new shape is refused under the bit by default
#: and somebody has to argue it OUT. That is the safe direction.
#:
#: IT IS A SUPERSET OF :data:`UNDISCRIMINATED_ELEMENT_SHAPES` AND THE TWO ARE
#: NOT THE SAME QUESTION. That one names the shapes whose internal partition
#: nothing discriminates, and the solved width is deliberately absent from it
#: because exactly one width in the searched range closes the region. This one
#: asks a different question - whether the partition came from the ELEMENT'S OWN
#: GRAMMAR - and a width found by searching for the one that closes did not,
#: however well pinned it is. Under a bit that says the region is not a tag
#: list at all, fitting a width to it is fitting.
_UNEVIDENCED_UNDER_NATIVE_SERIALIZE: Final = ELEMENT_SHAPES - frozenset(
    {ELEMENT_SHAPE_SELF_DELIMITING}
)

#: A container word for which NOT ONE instance in this project's corpus was
#: bounded by the element's own grammar, name to what that leaves unproven.
#:
#: WHAT MEMBERSHIP MEANS. The word's element framing has never once been tested
#: against a reading that could have failed. Every instance fell to a derived
#: partition, so the framing has no falsifiable evidence behind it at all - as
#: distinct from a word that carries derived instances alongside instances its
#: own grammar closed on, where the grammar has at least been exercised.
#:
#: IT IS HELD EQUAL TO WHAT A RUN MEASURES, NOT AS A FLOOR, so it reddens in
#: both directions and cannot come to describe a corpus that has moved. A word
#: that gains grammar evidence has to LEAVE this table.
#:
#: THIS IS NOT THE WHOLE UNDISCRIMINATED POPULATION, and reading it as though it
#: were is the error it is worded against. A word absent from here can still
#: carry containers bounded by a shape in
#: :data:`UNDISCRIMINATED_ELEMENT_SHAPES`, and those carry exactly the same
#: limit - the arrays whose elements are structs are the measured case. The
#: shape is the property; this table records only where a whole word rests on it.
CONTAINER_WORDS_WITHOUT_ELEMENT_GRAMMAR_EVIDENCE: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SetProperty": (
            "every instance carries an element word whose raw shape has no "
            "grammar of its own, so the region is divided by the declared count "
            "and no reading that could have failed was ever attempted. What is "
            "measured is the region and the declared count; the element "
            "boundaries inside it are derived and are not evidence. The "
            "undiscriminated remainder is filed as its own item rather than "
            "left as a note"
        ),
    }
)

#: An ELEMENT of a fixed-width inner word, and how many bytes it spans. These
#: are ELEMENT widths and not tag-value widths - see the commentary block
#: above for why the distinction matters.
#:
#: `Int64Property` IS HERE AND IS NOT IN :data:`MEASURED_VALUE_TYPES`, and that
#: pair of facts is the whole of what this module claims about the word. Its
#: ELEMENT width is measured - the arrays carrying it close on it - and its
#: TOP-LEVEL value is not, so a top-level instance is flagged and skipped like
#: any other unmeasured type. IT HAS NO ENTRY IN
#: :data:`UNMEASURED_PAYLOAD_REGIONS` AND THE ABSENCE IS DELIBERATE: that table
#: records regions the library actually produces, and this library holds no
#: top-level tag of this word at all. An entry there would be a record of a
#: measurement nobody was ever in a position to make, which is what
#: ``tests/save/test_properties.py`` refuses. If one ever appears, that test
#: reddens and asks for the entry then.
_ELEMENT_FIXED_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ByteProperty": 1,
        "Int8Property": 1,
        "FloatProperty": 4,
        "IntProperty": 4,
        "UInt32Property": 4,
        "Int64Property": 8,
    }
)

#: An ELEMENT that is one or more length-prefixed strings, and how many.
#:
#: `InterfaceProperty` IS HERE AND IS NOT IN :data:`MEASURED_VALUE_TYPES`, and
#: that is the distinction the commentary block above draws rather than an
#: oversight. This module has measured its ELEMENT shape - every array of it in
#: the library closes on two strings - and has measured nothing about a
#: top-level `InterfaceProperty` value, of which it has seen none. Promoting it
#: on the strength of the element result would carry a claim across a boundary
#: no measurement crosses.
_ELEMENT_STRING_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "EnumProperty": 1,
        "NameProperty": 1,
        "StrProperty": 1,
        "InterfaceProperty": 2,
        "ObjectProperty": 2,
        "SoftObjectProperty": 2,
    }
)

#: The tag type word whose value is a struct - CS-829. Shipped as a constant
#: rather than spelled at each site for the reason CS-831 gave
#: :data:`REFERENCE_TYPE_WORD`: a word repeated at five sites is five places to
#: get one literal subtly wrong, and a test cannot hold a literal to anything.
STRUCT_TYPE_WORD: Final = "StructProperty"

#: THE TWO SERIALIZATION FORMS A STRUCT INTERIOR TAKES, and the distinction the
#: whole of CS-829 turns on. A usmap schema names a struct's FIELDS. IT DOES NOT
#: STATE ITS FORM, and no shipped asset this project reads does - so which form
#: a struct word uses is MEASURED, per word, over the real library, by
#: ``tests/save/test_struct_interior.py``.
#:
#: :data:`STRUCT_FORM_TAG_LIST` is a nested property tag list closed by the same
#: terminator name a payload uses. IT GIVES A READING THAT CAN FAIL, and what
#: makes it fail is the TAG-GRAMMAR CHAIN: every interior tag's name, type word,
#: declared size and guid flag must read, and the cursor each computes must land
#: on a tag that also reads, until a terminator. Measured, that chain admits
#: exactly ONE end per site out of every end the declared size allows.
#:
#: THE EXACT-CLOSE COMPARISON IS NOT WHAT DISCRIMINATES, and an earlier version
#: of this module said it was. Loosening it to "at or before" leaves the whole
#: library census bit-identical, because on this corpus the first terminator is
#: always the last byte. It is kept because a corpus that placed one earlier
#: would need it, and a test asserts its inertness so that day is visible.
#:
#: :data:`STRUCT_FORM_NATIVE` is raw bytes carrying no tags at all. IT GIVES NO
#: SUCH READING: its width is whatever the bytes are, and any partition of it
#: closes by arithmetic. A check that cannot fail is not a check - which is the
#: finding that refuted CS-830 after it had already merged - so this form is
#: classified here and DECODED NOWHERE.
STRUCT_FORM_TAG_LIST: Final = "tag_list"
STRUCT_FORM_NATIVE: Final = "native"

#: The struct forms this module reads. A SET rather than a bare equality so the
#: day the native form gains evidence - a shipped asset stating an element
#: width, or any reading that could have disagreed - it joins here rather than
#: being special-cased at a call site.
STRUCT_FORMS_READ: Final = frozenset({STRUCT_FORM_TAG_LIST})

#: How deep a struct interior may nest before the reader refuses it. A BOUND,
#: not a measurement of any observed nesting: a payload is untrusted input and
#: a self-referential one would otherwise recurse until the interpreter raises,
#: which is a crash where non-negotiable 7 asks for a flag and a skip.
MAX_STRUCT_DEPTH: Final = 16

#: The one inner word whose element is a NESTED property tag list, closed by
#: the same terminator name a payload uses. THE SAME WORD AS
#: :data:`STRUCT_TYPE_WORD` AND NOW SPELLED AS IT: an element tag list and a
#: top-level struct interior are the same grammar reached from two directions,
#: and keeping two literals let them drift apart in principle.
_ELEMENT_TAG_LIST_WORD: Final = STRUCT_TYPE_WORD

#: The inner words carrying TWO element shapes, and so the only ones a
#: DERIVED width may ever be forced on.
#:
#: WHY THE RESTRICTION EXISTS, measured rather than reasoned. A struct element
#: is written either as a nested tag list or as a RAW body of uniform width -
#: both are real shapes of this format, so falling back from the first to the
#: second reads a known alternative rather than fitting an unknown one. Every
#: other element word has exactly ONE shape, and letting a derived width
#: override it published a wrong value: an array declaring four IntProperty
#: elements while carrying three was rescued by dividing twelve bytes into four
#: threes, where the element's own width said plainly that the region did not
#: close. The test named in the commentary block above is what caught it and is
#: what keeps it caught.
_RAW_SHAPE_ELEMENT_WORDS: Final = frozenset({_ELEMENT_TAG_LIST_WORD})

#: The widest element a SOLVED width may be. A BOUND, not a measurement: the
#: solve exists for the one mixed shape where a fixed-width half sits beside a
#: self-delimiting one, and this only stops the search running the length of a
#: payload. Widening it cannot make a refused container decode - it can only
#: turn a determination into an ambiguity, which is refused.
_SOLVED_WIDTH_CAP: Final = 64

#: A container cannot declare more elements than this. A bound, not a
#: measurement - it stops a corrupt count spinning, exactly as
#: :data:`_MAX_TAGS_PER_PAYLOAD` does one level up.
_MAX_CONTAINER_ELEMENTS: Final = 1 << 20

#: How deep a nested element tag list may run before the walk gives up.
_MAX_ELEMENT_TAGS: Final = 1 << 12


def container_candidate_words() -> frozenset[str]:
    """Derive every word the shipped tables treat as carrying an interior.

    IT DELIBERATELY OVER-INCLUDES. The derivation cannot equal
    :data:`CONTAINER_TYPE_WORDS` - it picks up every word that ships a tag-extra
    string without being a decoded scalar, plus every word whose value reading
    is declined - so it always carries the words other items own. That is what
    makes it a GUARD on the naming rather than a replacement for it: a fourth
    container-shaped word entering any of the four tables it reads lands here,
    and the test named in the commentary block above asks who owns it.

    Returns:
        The candidate words. Safe to render: every one came out of a literal in
        tracked source, never out of a save.
    """
    carries_extra = frozenset(_TAG_EXTRA_STRINGS)
    decoded_scalars = MEASURED_VALUE_TYPES - CONTAINER_TYPE_WORDS
    return (carries_extra - decoded_scalars) | frozenset(DECLINED_VALUE_READINGS)


@dataclass(frozen=True, repr=False)
class ContainerElement:
    """One bounded element of a container, and its value where there is one.

    ``repr`` renders no value, for the reason :class:`PropertyResult` gives:
    an element's bytes are world content and a test runner reprs a frame local
    before a human chooses what to print.

    Attributes:
        type_word: The element's own type word, from the container's tag.
        start: Where the element begins in the decompressed body.
        length: How many bytes it spans.
        value: The decoded value, or None when this module does not decode that
            element's type. NONE MEANS "NOT DECODED HERE", NEVER "EMPTY" - a
            ``StructProperty`` element is bounded and typed and deliberately
            unread, because its interior is CS-829's.
    """

    type_word: str
    start: int
    length: int
    value: object | None = None

    def __repr__(self) -> str:
        """Render the type word and the extent, and withhold the value.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(type_word={self.type_word!r}, "
            f"start={self.start}, length={self.length}, "
            f"decoded={self.value is not None})"
        )


@dataclass(frozen=True, repr=False)
class ContainerValue:
    """What one container tag's value decoded to - CS-830.

    ``repr`` renders counts and shipped words only, on the same terms as
    :class:`ContainerElement`.

    Attributes:
        type_word: The container's own type word.
        element_words: The element type words the tag carries - one for an
            array or a set, a key word and a value word for a map.
        element_count: The count the container itself declared.
        elements: One entry per element HALF, in the order the bytes carry
            them. A map yields two per declared entry, which is why this is not
            the same length as ``element_count``.
        element_shape: Which of :data:`ELEMENT_SHAPES` bounded the elements.
            CARRIED RATHER THAN DISCARDED because the three are not equally
            strong - see the commentary block above.
        struct_word: The struct type word an array of ``StructProperty`` names
            in its inner tag, or None. It is what CS-829 needs to read the
            interior this decode leaves alone.
    """

    type_word: str
    element_words: tuple[str, ...]
    element_count: int
    elements: tuple[ContainerElement, ...]
    element_shape: str
    struct_word: str | None = None

    def __repr__(self) -> str:
        """Render counts and shipped words only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(type_word={self.type_word!r}, "
            f"element_words={self.element_words!r}, "
            f"element_count={self.element_count}, "
            f"elements={len(self.elements)}, "
            f"element_shape={self.element_shape!r}, "
            f"struct_word={self.struct_word is not None})"
        )


@dataclass(frozen=True, repr=False)
class StructValue:
    """What one ``StructProperty`` interior decoded to - CS-829.

    ``repr`` RENDERS COUNTS ONLY AND WITHHOLDS THE STRUCT WORD, on the same
    terms :class:`ContainerValue` withholds it. The word is read out of the
    save's own bytes and the property names and values are decoded world
    content; a test runner reprs a value BEFORE a human chooses what to print,
    so the quiet rendering has to be the only one available.

    Attributes:
        struct_word: The struct type word the tag carried, or None when the
            tag that carried this interior named no word at all. DECODED
            CONTENT, which is why the repr renders its presence rather than the
            word. NONE IS NOT AN ABSENCE OF EVIDENCE ABOUT THE INTERIOR - it is
            an absence of a NAME for it, and the two are separable: a container
            element under the complete-type-name grammar is a tag list this
            module reads in full while its struct word sits one level down a
            type name :func:`_read_type_name` deliberately does not hand back.
            Publishing a fabricated word there would put a string in the model
            that the save never wrote, so the field says None and the interior
            still travels - CS-1038.
        form: Which of the two forms this interior was read under. Always a
            member of :data:`STRUCT_FORMS_READ` on a value that exists at all -
            an interior in a form this module does not read is not decoded, so
            it produces no ``StructValue`` rather than one flagged unread.
        properties: The interior's decoded values, by name. A nested struct
            comes back here as another :class:`StructValue`. DECODED WORLD
            CONTENT: a caller that renders it is an echo path under
            non-negotiable 12.
        unmeasured: Interior tags carrying a type whose value encoding is
            unmeasured. Counted rather than dropped for the reason
            :func:`_decode_payload` gives one level up.
        disagreed: Interior tags carrying a MEASURED type whose bytes did not
            account for the declared size. COUNTED APART from the field above
            because the two mean opposite things.
        depth: How far inside another struct this one sat, 0 at top level.
            Carried so a caller can tell a shallow reading from a deep one
            without re-walking, and so the ceiling is observable.
    """

    struct_word: str | None
    form: str
    properties: Mapping[str, object]
    unmeasured: int = 0
    disagreed: int = 0
    depth: int = 0

    def __repr__(self) -> str:
        """Render counts and the shipped form word, and withhold the rest.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(form={self.form!r}, "
            f"properties={len(self.properties)}, "
            f"unmeasured={self.unmeasured}, disagreed={self.disagreed}, "
            f"depth={self.depth})"
        )


#: THE ONE STRUCT WORD WHOSE NATIVE INTERIOR THIS MODULE READS - CS-400. It is a
#: DISPATCH KEY naming ONE measured grammar, not a struct vocabulary defining a
#: population (the CS-829 fence; ADJ-G Q5). Provenance: the game's shipped
#: headers declare ``FInventoryItem`` with ``TStructOpsTypeTraits`` carrying
#: ``WithSerializer = true`` (``FGInventoryComponent.h``), so it is written by
#: its own serializer rather than as a tag list; the two byte forms read by
#: :func:`read_inventory_item` were measured over the local library and close
#: exactly at the tag's declared size on every site. :data:`STRUCT_FORM_NATIVE`
#: stays OUT of :data:`STRUCT_FORMS_READ`: every other native word is still
#: decoded nowhere.
INVENTORY_ITEM_STRUCT_WORD: Final = "InventoryItem"

#: Why an ``InventoryItem`` interior was refused - a CLOSED vocabulary. Both
#: forms closing is :data:`ITEM_FORM_AMBIGUOUS`; neither closing is
#: :data:`ITEM_FORM_UNCLOSED`. Neither is fatal: the refusal is published in the
#: item's place and the enclosing interior counts it unmeasured.
ITEM_FORM_AMBIGUOUS: Final = "item_form_ambiguous"
ITEM_FORM_UNCLOSED: Final = "item_form_unclosed"
ITEM_REFUSAL_REASONS: Final = frozenset({ITEM_FORM_AMBIGUOUS, ITEM_FORM_UNCLOSED})

#: The closed-vocabulary flag a consumer counts an item under when its state -
#: a NEW-form state block or a non-empty OLD-form legacy state actor - was
#: present and left UNDECODED. Class and count stay readable beside it.
ITEM_STATE_UNDECODED: Final = "item_state_undecoded"

#: The path lead a NEW-form state struct reference must carry. A grammar check
#: that can fail, not a vocabulary: the state struct is a script struct.
_SCRIPT_STRUCT_LEAD: Final = "/Script/"


@dataclass(frozen=True, repr=False)
class InventoryItem:
    """One decoded ``InventoryItem`` native interior - CS-400.

    NOT AN :class:`ObjectReference`, and that is the point (ADJ-G S0-a). An item
    class is not an object in the world: published as a reference it would enter
    :attr:`PropertyResult.references` and every resolution population as a
    permanently unresolved entry. It carries no position field.

    ``repr`` WITHHOLDS BOTH STRINGS. The class path names world content and a
    test runner reprs a value before a human chooses what to print.

    Attributes:
        level_reference: The class reference's first string - empty on every
            measured site, carried rather than interpreted.
        class_path: The item class path, empty for an empty slot. WORLD CONTENT.
        state_undecoded: Whether item state was present and left undecoded -
            counted under :data:`ITEM_STATE_UNDECODED`.
    """

    level_reference: str
    class_path: str
    state_undecoded: bool

    def __repr__(self) -> str:
        """Render lengths and the flag only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(level_reference_len={len(self.level_reference)}, "
            f"class_path_len={len(self.class_path)}, "
            f"state_undecoded={self.state_undecoded})"
        )


@dataclass(frozen=True, repr=False)
class InventoryItemRefusal:
    """An ``InventoryItem`` interior that was refused, and why - CS-400.

    Published in the item's place so a consumer can count the refusal by its
    reason rather than mistake an absent item for an empty slot. Carries only a
    word from :data:`ITEM_REFUSAL_REASONS`, so the default ``repr`` is safe.

    Attributes:
        reason: A member of :data:`ITEM_REFUSAL_REASONS`.
    """

    reason: str

    def __repr__(self) -> str:
        """Render the type only, never the reason word - CS-400.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(reason=<withheld>)"


#: The type words whose VALUE encoding is measured and is therefore decoded.
#: EVERY OTHER TYPE IS FLAGGED AND SKIPPED - non-negotiable 7 - and the ones
#: seen in the library are recorded in :data:`UNMEASURED_PAYLOAD_REGIONS`
#: rather than guessed at from a neighbouring type's shape.
#:
#: THE CONTAINER WORDS ARE HERE FOR THEIR ELEMENT FRAMING AND FOR NOTHING BELOW
#: IT - CS-830. What is measured is the count, the element words and every
#: element's extent, checked by the elements consuming the tag's declared size
#: exactly. What is NOT measured is the interior of a struct element, which
#: stays with :data:`CONTAINER_ADJACENT_OWNERS`. Membership here is what makes
#: :func:`_walk_payload` count a REFUSED container decode as a walk that has
#: lost its place rather than as unmodelled content - and the one case where
#: that would be the wrong reading, an element word with no grammar at all, is
#: separated there rather than collapsed into it.
MEASURED_VALUE_TYPES: Final = (
    frozenset(_FIXED_WIDTH_VALUES)
    | _ONE_STRING_VALUES
    | _TWO_STRING_VALUES
    | CONTAINER_TYPE_WORDS
    | frozenset({"BoolProperty", "ByteProperty"})
)

#: The evidence classes a decoded value's correctness can rest on, named so the
#: table below records a KIND of backing rather than a sentence about one.
#:
#: `EVIDENCE_DECLARED_WIDTH` is the weakest and says the least: every instance
#: in the library declared the width this module expects. It rules out a wrong
#: width and says NOTHING about the bytes being read the right way round.
#: `EVIDENCE_REDUNDANCY` means the value carries its own length prefix, so a
#: mis-read desynchronises the walk instead of returning a wrong answer.
#: `EVIDENCE_CROSS_SECTION` means the value resolves against a structure
#: elsewhere in the same body. `EVIDENCE_MAGNITUDE` means the population's
#: magnitudes discriminate the byte order against the opposite reading.
EVIDENCE_DECLARED_WIDTH: Final = "declared_width"
EVIDENCE_REDUNDANCY: Final = "redundancy"
EVIDENCE_CROSS_SECTION: Final = "cross_section"
EVIDENCE_MAGNITUDE: Final = "magnitude_distribution"

#: WHICH ORACLE BACKS EACH MEASURED TYPE'S VALUE DECODE - CS-421, as shipped
#: DATA so a later slice reads it rather than re-deriving it from a comment.
#:
#: WHAT AN ENTRY CLAIMS AND WHAT IT DOES NOT. It names the evidence CLASS that
#: applies to that type. It does not assert that a named oracle has been shown
#: to discriminate every fault for that type, and reading it that way is the
#: over-statement this table exists to make harder rather than easier. The one
#: entry tied mechanically to a live control is `EVIDENCE_MAGNITUDE`, tied by
#: the coupling test cited in the commentary block above.
#:
#: A TYPE WHOSE SET IS `EVIDENCE_DECLARED_WIDTH` ALONE IS THE THING TO NOTICE -
#: see :data:`WIDTH_ONLY_VALUE_TYPES`, which is derived from this table rather
#: than restated. That is a type whose bytes could be read backwards and no
#: shipped check would say so.
EVIDENCE_FOR_VALUE_TYPE: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        # THE CONTAINER ENTRIES DIFFER FROM ONE ANOTHER, AND THE DIFFERENCE IS
        # MEASURED RATHER THAN TIDY. An array's and a map's elements are
        # bounded by their own grammar on the overwhelming majority of the
        # library, so a mis-read desynchronises inside the region instead of
        # returning a wrong answer - which is what redundancy names. Every SET
        # in the library falls to the DERIVED width instead, whose only backing
        # is that the tag's declared extent divides by the declared count. That
        # is `EVIDENCE_DECLARED_WIDTH` and nothing more, so `SetProperty`
        # belongs in :data:`WIDTH_ONLY_VALUE_TYPES` and is left there rather
        # than lent its neighbours' evidence.
        "ArrayProperty": frozenset({EVIDENCE_DECLARED_WIDTH, EVIDENCE_REDUNDANCY}),
        "BoolProperty": frozenset({EVIDENCE_DECLARED_WIDTH}),
        "ByteProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "EnumProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "FloatProperty": frozenset({EVIDENCE_DECLARED_WIDTH, EVIDENCE_MAGNITUDE}),
        "Int8Property": frozenset({EVIDENCE_DECLARED_WIDTH}),
        "IntProperty": frozenset({EVIDENCE_DECLARED_WIDTH, EVIDENCE_MAGNITUDE}),
        "MapProperty": frozenset({EVIDENCE_DECLARED_WIDTH, EVIDENCE_REDUNDANCY}),
        "NameProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "ObjectProperty": frozenset({EVIDENCE_REDUNDANCY, EVIDENCE_CROSS_SECTION}),
        "SetProperty": frozenset({EVIDENCE_DECLARED_WIDTH}),
        "SoftObjectProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "StrProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "UInt32Property": frozenset({EVIDENCE_DECLARED_WIDTH}),
    }
)

#: The types whose only backing is that the declared size matched, DERIVED from
#: the table above so the two cannot disagree. A type entering or leaving this
#: set is a change in what this module can honestly claim, and deriving it is
#: what stops that change being made by editing a sentence.
WIDTH_ONLY_VALUE_TYPES: Final = frozenset(
    word
    for word, oracles in EVIDENCE_FOR_VALUE_TYPE.items()
    if oracles == frozenset({EVIDENCE_DECLARED_WIDTH})
)

#: WHAT IS STILL OPAQUE INSIDE A PAYLOAD, as a structure rather than an
#: adjective, per CS-412. Each entry names what IS pinned and what is NOT
#: claimed, so a later slice executes against this table instead of
#: re-deriving it. A partial recorded as prose is not resumable.
UNMEASURED_PAYLOAD_REGIONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "trailing_run": (
            "the run between a payload's property terminator and its declared "
            "final byte, NARROWED BY CS-828 RATHER THAN CLOSED. It is "
            "UNIVERSAL ACROSS THE THREE PAIRS THIS GRAMMAR READS - not one of "
            "their payloads ends at its terminator - while (14,60) reaches no "
            "terminator at all, so it has no such run and is scoped out of "
            "CS-828 and into CS-G05. Its width is 4 on the large majority and "
            "variable above that, spanning 4 to 5008 bytes on the (10,36) and "
            "(13,42) pairs and 4 to 1053802 on (14,52), across roughly 235 "
            "distinct widths per pair. WHAT IS NOW READ: the run OPENS WITH A "
            "LEAD FIELD, an int32 decoded out of the bytes by read_trailing_run "
            "and reported on PropertyResult.trailing_run, and the old 4-byte "
            "floor is that field rather than an arithmetic residue. The "
            "question the floor left open - whether it is one field or the head "
            "of a longer structure - is answered for the payloads whose run IS "
            "the field and nothing else, and those are the large majority. "
            "WHAT IS STILL UNMEASURED: every byte past that field, carried as "
            "TrailingRun.unread. It is keyed by the record's CLASS rather than "
            "by its pair - measured, not assumed - so no single grammar reads "
            "it and no partition of it closes by arithmetic; that is the "
            "defect which refuted CS-830 after it had merged and the reason "
            "the remainder is left open here instead of being apportioned. "
            "NARROWED AGAIN BY CS-1068, ON ONE DERIVED CLASS SET AND NOWHERE "
            "ELSE: where the remainder is a COUNT-PREFIXED ITEM LIST it is read "
            "by read_item_list, whose every width comes from the count prefix, "
            "the per-entry length prefixes and two shipped fixed-width "
            "constants and never from the declared end, and the classes that "
            "carry one are picked off the body at read time by "
            "derive_item_list_classes rather than transcribed. On those "
            "classes' payloads unread falls to zero and the list is reported "
            "as TrailingRun.items; on every other class the remainder is "
            "exactly as open as it was. "
            "NARROWED AGAIN BY CS-828, ON A SECOND DERIVED CLASS SET AND "
            "NOWHERE ELSE: where the remainder is TWO OBJECT REFERENCES it is "
            "read by read_reference_pair, whose four widths come from the "
            "strings' own length prefixes and whose tail is one of the two "
            "widths REFERENCE_PAIR_TAIL_WIDTHS allows, never the leftover. THE "
            "TAIL IS NOT AN UNCONDITIONAL SUFFIX - one schema in this library "
            "writes it and two write the same two references and stop - so "
            "derive_reference_pair_classes derives the FORM as well as the "
            "membership, from the body, and admits a class only when every one "
            "of its remainder-bearing records reads at the SAME width. On "
            "those classes' payloads unread falls to zero and the pair is "
            "reported as TrailingRun.references. "
            "NARROWED AGAIN BY CS-828, ON A THIRD DERIVED CLASS SET AND "
            "NOWHERE ELSE: where the remainder is exactly one int32 READING "
            "ZERO it is read by read_zero_remainder, whose width is the "
            "shipped constant ZERO_REMAINDER_BYTES and never the leftover, "
            "and which REFUSES a value other than ZERO_REMAINDER_VALUE. THE "
            "WIDTH IS WHAT REFUSES REAL INPUT - residuals of many other "
            "widths remain open on all three pairs - and the value condition "
            "is measured to refuse no record of this library, which is "
            "recorded at ZERO_REMAINDER_VALUE rather than rounded up. "
            "derive_zero_remainder_classes admits a class only when every one "
            "of its remainder-bearing records in that body reads as the shape, "
            "value included. On those classes' payloads unread falls to zero "
            "and the reading is reported as TrailingRun.zero_remainder. IT IS "
            "NOT A CLAIM THAT THE REGION IS AN EMPTY ITEM LIST: those bytes "
            "are byte-identical to one, no reading of the run can tell them "
            "apart, and CS-1119 owns that question. What is read is the VALUE "
            "at a derived landing point, exactly as the lead field is. "
            "NARROWED AGAIN BY CS-828, ON A FOURTH DERIVED CLASS SET AND "
            "NOWHERE ELSE: where the remainder is a COUNT-PREFIXED LIST OF "
            "OBJECT REFERENCES it is read by read_reference_list, whose entry "
            "count comes out of the bytes, whose string widths come from their "
            "own length prefixes and whose per-entry scalar is one of the two "
            "widths REFERENCE_LIST_ENTRY_PREFIX_WIDTHS allows, never the "
            "leftover. THAT SCALAR IS NOT AN UNCONDITIONAL FIELD - one "
            "carrying class in this library writes it ahead of every reference "
            "and two write the reference alone - so "
            "derive_reference_list_classes derives the FORM as well as the "
            "membership, from the body, and admits a class only when every one "
            "of its remainder-bearing records reads at the SAME width AND at "
            "exactly one of them. A COUNT OF ZERO IS REFUSED, which is how "
            "this reading declines rather than resolves the collision with the "
            "zero-valued residual above. On those classes' payloads unread "
            "falls to zero and the list is reported as "
            "TrailingRun.reference_list. "
            "NARROWED AGAIN BY CS-828, ON A FIFTH DERIVED CLASS SET AND "
            "NOWHERE ELSE: where the remainder is a COUNT-PREFIXED LIST OF "
            "NAMED TRANSFORMS it is read by read_transform_list, whose entry "
            "count comes out of the bytes, whose name widths come from their "
            "own length prefixes and whose per-entry scalar block is "
            "TRANSFORM_LIST_SCALARS scalars at one of the two widths "
            "TRANSFORM_LIST_SCALAR_WIDTHS allows, never the leftover. THAT "
            "SCALAR WIDTH IS NOT A CONSTANT OF THE FORMAT - the carrying class "
            "in this library writes the narrow block on one of the three pairs "
            "and the wide block on the other two - so "
            "derive_transform_list_classes derives the WIDTH as well as the "
            "membership, from the body, and admits a class only when every one "
            "of its remainder-bearing records reads at the SAME width AND at "
            "exactly one of them. A COUNT OF ZERO IS REFUSED, which is how "
            "this reading declines rather than resolves the collision with the "
            "zero-valued residual above. WHAT THE SCALARS DENOTE IS NOT "
            "CLAIMED: their count and width are what the walk consumes, and a "
            "wrong name for them would be worse than none. On those classes' "
            "payloads unread falls to zero and the list is reported as "
            "TrailingRun.transform_list. "
            "NARROWED AGAIN BY CS-828, ON A SIXTH DERIVED CLASS SET AND "
            "NOWHERE ELSE, AND THIS ONE IS THE WIDEST REGION RATHER THAN THE "
            "MOST POPULOUS: where the remainder is a VERSION WORD, a GROUP "
            "COUNT and that many CLASS-KEYED INSTANCE GROUPS it is read by "
            "read_buildable_group_list. Every width it consumes comes from "
            "those two counts, from four length prefixes per instance, from an "
            "extra-data block's own DECLARED SIZE and from the shipped "
            "constants BUILDABLE_INSTANCE_HEAD_BYTES and "
            "BUILDABLE_INSTANCE_MID_BYTES - never the leftover. THE "
            "EXTRA-DATA BLOCK IS NOT AN UNCONDITIONAL FIELD: a per-instance "
            "flag says whether it is there, and what it CONTAINS is not "
            "claimed - its type name and declared size are read and its "
            "interior is stepped by that size. UNLIKE THE FOUR READERS ABOVE "
            "THIS ONE ACCEPTS A COUNT OF ZERO, so the anti-vacuity gate is "
            "moved onto the derivation rather than dropped: "
            "derive_buildable_group_classes admits a class only when one of "
            "its records in that body DEMONSTRATES a NON-EMPTY list landing "
            "exactly on its declared end, and no record of it reads as "
            "something the reader refuses. On those classes' payloads unread "
            "falls to zero and the list is reported as "
            "TrailingRun.buildable_groups. "
            "WHAT REMAINS AFTER THAT, and it is CS-1119 rather than this "
            "entry: whether that zero-valued residual IS an empty item list or "
            "a class carrying no list at all, which no reading of the run "
            "decides; and a remainder that is a large nested structure nothing "
            "in the run describes, carried by a set of classes CS-1119's note "
            "owns the measurement of - its filed headline calls it one class "
            "and that characterisation is measured false. THE RESIDUAL "
            "POPULATION IS NOT ONE SHAPE EITHER, which is a CS-828 measurement "
            "filed as CS-1149 rather than restated here. "
            "NO FIGURE ABOVE IS RESTATED IN ANY TEST: "
            "tests/save/test_trailing_run.py derives the population from this "
            "module's own TRAILING_RUN_PAIRS on every run and reports COUNTS "
            "ONLY. This is the region that keeps the PROPERTY "
            "walk terminator-exact rather than boundary-exact. The BODY walk is "
            "boundary-exact and is a different question - conflating the two put a "
            "false sentence in a tracked file on 2026-08-23"
        ),
        "StructProperty": (
            "the interior of a struct tag, NARROWED BY CS-829 RATHER THAN "
            "CLOSED. The tag's declared size DOES bound it, so it is stepped "
            "over exactly and costs no synchronisation, and the struct's own "
            "type word is present in the tag. WHAT IS NOW READ: the tag_list "
            "form - a nested property tag list, discriminated by the TAG-GRAMMAR "
            "CHAIN rather than by its closing comparison, which is measured "
            "inert on this corpus - decoded by decode_struct_interior and "
            "reported on PropertyResult.struct_interiors. WHAT IS STILL "
            "UNMEASURED: the native form, raw bytes carrying no tags at all. "
            "Its width is whatever the bytes are, so any partition of it closes "
            "by arithmetic and no reading of it could have failed - which is "
            "the defect that refuted CS-830 after it had merged, and the reason "
            "it is classified and not decoded. WHICH WORDS TAKE WHICH FORM IS "
            "NOT WRITTEN HERE: it is derived from the shipped usmap and the "
            "corpus on every run by tests/save/test_struct_interior.py, because "
            "a transcribed struct vocabulary is the hand-maintained list this "
            "project has repeatedly recorded as the thing that rots. THE FORM "
            "IS A PROPERTY OF THE STRUCT TYPE AND THAT IS MEASURED, not "
            "assumed - no word in the corpus is written both ways, and the day "
            "one is, that test says so. StructProperty is deliberately NOT in "
            "MEASURED_VALUE_TYPES while the native form is unread, so a struct "
            "tag still counts as unmodelled content exactly as it did before. "
            "InventoryStack is NOT reachable from a building directly - "
            "measured 2026-08-23, no building record carries one; a building "
            "holds an ObjectProperty reference to an inventory component and "
            "the stacks sit there inside an array. So the chain is CS-831, then "
            "CS-830, then this region, and reading a struct interior does not "
            "shorten it"
        ),
        "TextProperty": (
            "10 instances, all of declared size 45. Unreal's text serialization "
            "is a tagged union over history types and 10 instances of one size "
            "cannot distinguish its cases"
        ),
    }
)

#: A type word whose TOP-LEVEL value this module declines to read, name to THE
#: EVIDENCE THAT WOULD SETTLE THE READING.
#:
#: WHY THIS IS NOT :data:`UNMEASURED_PAYLOAD_REGIONS`, which is the obvious
#: place and is the wrong one. That table records REGIONS THIS LIBRARY ACTUALLY
#: PRODUCES, and ``tests/save/test_properties.py`` refuses a key nothing
#: justifies - an entry for a type no corpus has ever emitted would be a record
#: of a measurement nobody was in a position to make. A word with NO top-level
#: instance therefore cannot be recorded there, and before this table it had
#: nowhere at all to be recorded: CS-830 removed the entry that had been
#: standing in, correctly, and left the refusal with no home. THE TWO TABLES ARE
#: INDEPENDENT. A word may appear in either, both, or neither, and neither one
#: implies the other.
#:
#: WHAT AN ENTRY MUST SAY, AND WHAT IT MAY NOT. It names EVIDENCE - an
#: observation that, if made, would settle the reading. It may not turn on how
#: many instances exist. A sample-size refusal cannot be acted on, because it
#: does not say what a larger sample would have to CONTAIN, and it goes stale
#: silently: a corpus can grow without ever producing the observation that
#: matters. This is the distinction CS-832 is open on.
VALUE_READING_CRITERIA: Final[Mapping[str, str]] = MappingProxyType(
    {
        "Int64Property": (
            "the ELEMENT width is measured - the arrays carrying this word "
            "close on it - and the TOP-LEVEL value encoding is not, because "
            "this library emits no top-level tag of the word at all. THE "
            "CRITERION IS A SINGLE TOP-LEVEL INSTANCE, of any provenance, whose "
            "declared size can be read against the element width already "
            "measured. One such tag settles it or falsifies it; no number of "
            "further ARRAY instances can, since they are evidence about the "
            "element and the element is not in question. This is a refusal for "
            "want of an observation and not for want of a sample"
        ),
    }
)

#: The tag's index field, read as a fixed-array element index. It is 0 on all
#: but a few dozen tags in the library, the exceptions being 1 and 2.
#:
#: THE COUNTS THAT USED TO BE HERE ARE DELETED RATHER THAN CORRECTED. The
#: sentence read "all but N of M tags", and re-derivation shows M was the
#: count of tags AT zero - the numerator - while the true total is M plus N.
#: So the figure presented as the denominator was the numerator, and the
#: sentence contradicted itself as written. Shipping both numbers is worse than
#: shipping neither: a wrong number with a true claim attached reads as
#: verified forever. Correcting one would only reset the clock, since the
#: operator plays this game and any absolute count here goes red on the next
#: autosave. The claim that carries weight needs no figure at all - the field
#: is carried past rather than interpreted, so nothing here depends on its
#: value.
_TAG_INDEX_FIELD_BYTES: Final = 4

#: A payload cannot carry more tags than this. A bound, not a measurement -
#: the largest real payload holds far fewer, and this only stops a corrupt
#: length from spinning.
_MAX_TAGS_PER_PAYLOAD: Final = 1 << 14

#: The name that closes a tag list. SPELLED ONCE because CS-830 gave it a
#: second reader: an element of a struct is a nested tag list closed by this
#: same name, and two copies of one literal are two places for it to drift.
_PAYLOAD_TERMINATOR: Final = "None"


def _payload_text(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """Read one length-prefixed string, returning None rather than raising.

    IT DOES NOT REUSE :meth:`_Cursor.string`, and the difference is the point.
    That reader RAISES, which is right for the record table, whose grammar is
    measured - a failure there is a real defect. Inside a payload an unreadable
    run is expected: it means this project has not measured that value type
    yet, and non-negotiable 7 requires flagging and skipping it rather than
    failing the load of an otherwise readable world.

    Args:
        body: The decompressed body.
        at: Where the length prefix starts.
        end: The first byte past this payload.

    Returns:
        The text and the offset after it, or None if it does not read.
    """
    if at < 0 or at + INT32_SIZE > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    if count == 0:
        return ("", at + INT32_SIZE)
    if count < 0:
        byte_count, terminator, encoding = -count * UTF16_CHAR_SIZE, UTF16_CHAR_SIZE, "utf-16-le"
    else:
        byte_count, terminator, encoding = count, 1, "utf-8"
    if byte_count > MAX_STRING_BYTES or at + INT32_SIZE + byte_count > end:
        return None
    start = at + INT32_SIZE
    try:
        return (body[start : start + byte_count - terminator].decode(encoding), start + byte_count)
    except UnicodeDecodeError:
        # Returned, never raised: a UnicodeDecodeError QUOTES the offending
        # bytes and exception context is an echo path (non-negotiable 12).
        return None


def _skip_actor_head(body: bytes, at: int, end: int) -> int | None:
    """Step over an actor payload's parent reference and component list.

    An ACTOR payload opens with a parent object reference and a list of the
    components it owns; a COMPONENT payload opens directly with its tags. That
    asymmetry is measured - reading an actor as a component desynchronises on
    the first tag - and is the same list CS-413 used to prove payload
    attribution against the component records' own parent fields.

    Args:
        body: The decompressed body.
        at: The payload's first byte.
        end: The first byte past the payload.

    Returns:
        Where the property tags begin, or None if the head does not read.
    """
    for _ in range(2):
        step = _payload_text(body, at, end)
        if step is None:
            return None
        at = step[1]
    if at + INT32_SIZE > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    at += INT32_SIZE
    if count < 0 or count > MAX_OBJECTS:
        return None
    for _ in range(2 * count):
        step = _payload_text(body, at, end)
        if step is None:
            return None
        at = step[1]
    return at


def _skip_tag_extra(body: bytes, at: int, end: int, type_word: str) -> int | None:
    """Step over the tag data whose shape depends on the property type.

    Args:
        body: The decompressed body.
        at: Just past the tag's index field.
        end: The first byte past the payload.
        type_word: The tag's type word.

    Returns:
        Where the guid flag begins, or None if it does not read.
    """
    for _ in range(_TAG_EXTRA_STRINGS.get(type_word, 0)):
        step = _payload_text(body, at, end)
        if step is None:
            return None
        at = step[1]
    if type_word == "StructProperty":
        at += GUID_BYTES
        if at > end:
            return None
    return at


def _skip_guid_flag(body: bytes, at: int, end: int) -> int | None:
    """Step over a tag's optional property guid.

    Args:
        body: The decompressed body.
        at: The flag byte's offset.
        end: The first byte past the payload.

    Returns:
        Where the value begins, or None if the flag is neither 0 nor 1.
    """
    if at + 1 > end:
        return None
    flag = body[at]
    if flag == 1:
        return at + 1 + GUID_BYTES
    return at + 1 if flag == 0 else None


def _read_tag_header(body: bytes, at: int, end: int) -> tuple[str, int, int, int | None] | None:
    """Read one tag past its name, stopping at its value.

    Args:
        body: The decompressed body.
        at: Just past the tag's name.
        end: The first byte past the payload.

    Returns:
        The type word, where the value starts, its declared size and the byte a
        BoolProperty carries in the tag. None if the tag does not read.
    """
    type_read = _payload_text(body, at, end)
    if type_read is None:
        return None
    type_word, after = type_read
    if after + INT32_SIZE + _TAG_INDEX_FIELD_BYTES > end:
        return None
    (size,) = struct.unpack_from("<i", body, after)
    extra_at = after + INT32_SIZE + _TAG_INDEX_FIELD_BYTES

    in_tag_byte: int | None = None
    flag_at: int | None
    if type_word == "BoolProperty":
        if extra_at + 1 > end:
            return None
        in_tag_byte = body[extra_at]
        flag_at = extra_at + 1
    else:
        flag_at = _skip_tag_extra(body, extra_at, end, type_word)
        if flag_at is None:
            return None

    value_at = _skip_guid_flag(body, flag_at, end)
    if value_at is None or size < 0 or value_at + size > end:
        return None
    return (type_word, value_at, size, in_tag_byte)


def _decode_fixed_width(body: bytes, at: int, size: int, spec: tuple[int, str]) -> object | None:
    """Decode one fixed-width numeric value.

    Args:
        body: The decompressed body.
        at: The value's first byte.
        size: The value's declared extent.
        spec: The measured width and its struct code.

    Returns:
        The value, or None when the declared size is not the measured width.
    """
    width, code = spec
    # EQUALITY, not a floor. No save in the library declares any other size for
    # these types, so this branch is defensive rather than measured - loosening
    # it to `size < width` survives the whole suite, which is recorded here so
    # nobody mistakes it for a checked discriminator.
    if size != width or at + size > len(body):
        return None
    (value,) = struct.unpack_from(code, body, at)
    # KEYED ON WHAT WAS UNPACKED, not on how the code is spelled. This read
    # `code == "<f"`, which made the branch depend on a byte-order prefix: the
    # float entry spelled any other way fell into the integer branch, where a
    # NaN raises `ValueError` out of a decoder whose contract is to return None
    # on anything it cannot read. Nothing was wrong with the shipped table - the
    # invariant "the float code is spelled exactly this way" was simply never
    # stated, which is the defect. `struct` already returns the right Python
    # type for every code in the table, so asking it is both narrower and total.
    return float(value) if isinstance(value, float) else int(value)


def _decode_object_reference(body: bytes, type_word: str, at: int, end: int) -> object | None:
    """Decode a level reference and object path pair.

    Args:
        body: The decompressed body.
        type_word: The tag's type word.
        at: The value's first byte.
        end: The first byte past the value.

    Returns:
        The pair, or None when it does not consume the value exactly.
    """
    parts: list[str] = []
    cursor = at
    for _ in range(2):
        step = _payload_text(body, cursor, end)
        if step is None:
            return None
        parts.append(step[0])
        cursor = step[1]
    if type_word == "SoftObjectProperty":
        cursor += _SOFT_OBJECT_TAIL_BYTES
    return (parts[0], parts[1]) if cursor == end else None


def _decode_text_value(body: bytes, type_word: str, at: int, size: int) -> object | None:
    """Decode a value that is one or more length-prefixed strings.

    Args:
        body: The decompressed body.
        type_word: The tag's type word.
        at: The value's first byte.
        size: The value's declared extent.

    Returns:
        The decoded value, or None when the type is unmeasured or the strings
        disagree with the declared size.
    """
    end = at + size
    if type_word in _TWO_STRING_VALUES:
        return _decode_object_reference(body, type_word, at, end)
    if type_word == "ByteProperty" and size == 1:
        # A raw byte, which is the shape when the tag's enum word is the
        # literal None. The enum-name shape falls through to the branch below.
        return None if end > len(body) else int(body[at])
    if type_word in _ONE_STRING_VALUES or type_word == "ByteProperty":
        step = _payload_text(body, at, end)
        return None if step is None or step[1] != end else step[0]
    return None


# ---------------------------------------------------------------------------
# THE (14,60) COMPLETE-TYPE-NAME TAG GRAMMAR - CS-G05
#
# `docs/GATED.md` recorded under CS-G05 that every record of every (14,60) save
# decodes ZERO property tags and that the pair was therefore a CONTROL - a save
# that could not exercise this decoder at all, cause unestablished. THE PREMISE
# WAS WRONG, and ground truth is what refuted it (CLAUDE.md section 8): a
# third-party map tool reads container contents and machine settings out of the
# same file on the same machine, so the data is present and decodable. The zero
# was a defect HERE.
#
# TWO OFFSETS LOCALISED IT, and both were read out of the bytes by hand:
#
#   - ONE OPAQUE BYTE stands between a payload's head and its first tag. On an
#     actor that is just past the component list; on a component it is the
#     payload's first byte. `_skip_actor_head` landed exactly one byte short of
#     the first tag name, so `_payload_text` read that byte as the top of a
#     length prefix and refused every payload in the world. Its WIDTH is pinned
#     and its MEANING is not, which is the footing `transform_delta` and
#     `data_entry_lead` already stand on: it is zero on all 3918 payloads of
#     the pinned development world, and a constant field cannot be told apart
#     from a reserved one. Graded by
#     tests/save/test_property_payload_14_60.py::test_the_opaque_lead_byte_is_load_bearing,
#     which strips the byte from the fixture and asserts the reader refuses it.
#   - THE TAG SPELLS ITS TYPE AS A RECURSIVE NAME - a word, an int32 parameter
#     count, then that many nested names - rather than as a type word followed
#     by per-type extra strings. There is no index field, and the tag closes
#     with a FLAGS BYTE rather than a guid-present flag. A container's element
#     words are the TOP-LEVEL PARAMETERS of that name. Graded by
#     tests/save/test_property_payload_14_60.py::test_a_14_60_container_tag_yields_its_element_words_from_the_type_name,  # noqa: E501
#     which is the arm a lead-byte-only repair cannot pass.
#
# WHY THE SECOND HALF IS NOT OPTIONAL. Stepping the lead byte alone reaches the
# first tag NAME and gets 3215 of 3918 payloads to a terminator with ZERO
# container values, because the element words a container needs are no longer
# where the legacy reader looks, and the 703 that still broke were the ones
# whose flags byte the legacy guid-flag reading refused. Both halves are one
# grammar and neither is a fix on its own.
#
# THE FLAGS BITS ARE MEASURED ONE AT A TIME AND THE UNSEEN ONES ARE NOT
# GUESSED. Over the 9058 tags of the pinned development world the byte takes
# four values: 0x00 on 6123, 0x08 on 757, 0x09 on 2 and 0x10 on 176. 0x08 rides
# only on the four container-and-struct words and adds no bytes; 0x10 rides only
# on `BoolProperty` and IS its true value; 0x01 adds an int32, and that is the
# weakest reading here - it rests on two tags, and what makes it more than a
# coincidence is that dropping the four bytes costs a whole record.
#
# EVERY OTHER BIT REFUSES THE PAYLOAD. 0x02 reads like a property guid and this
# project has seen it on NOT ONE TAG, so the width of whatever follows it is
# unknown; assuming 16 bytes there would publish values read from the wrong
# offset on the first save that carried one, which is the silently wrong answer
# non-negotiable 7 rules out. A flagged payload is recoverable. A wrong value is
# not.
#
# tests/save/test_property_payload_14_60.py grades all of it on a SYNTHETIC
# (14,60) fixture, so every arm runs on a machine with no game and no save.
# ---------------------------------------------------------------------------

#: MEASURED. The pairs whose property payload carries the lead byte and the
#: recursive type name instead of the legacy tag shape. ONE ENTRY, and the two
#: changes were measured together on it - this set names the pair, and claims
#: nothing about whether some future pair could carry one without the other.
COMPLETE_TYPE_NAME_PAIRS: Final[frozenset[tuple[int, int]]] = frozenset({(HEADER_VERSION_14, 60)})

#: The opaque run between a payload's head and its first tag, on the pairs
#: above. Zero everywhere else, which is why the legacy reader never had one.
PAYLOAD_TAG_LEAD_BYTES: Final = 1

#: THE PAIRS WHOSE PAYLOADS CARRY A TRAILING RUN AT ALL - CS-828, and DERIVED
#: rather than transcribed so it cannot drift out of step with either set it is
#: built from. A pair reaches the run only by reaching a property terminator,
#: and the complete-type-name pair reaches no terminator under any grammar this
#: module ships, so it has no such run and is scoped out of CS-828 and into
#: CS-G05. Adding a measured layout puts its pair in here automatically, which
#: is the point: a new pair joins the population the library arms grade instead
#: of being quietly outside it.
TRAILING_RUN_PAIRS: Final[frozenset[tuple[int, int]]] = (
    MEASURED_BODY_LAYOUTS - COMPLETE_TYPE_NAME_PAIRS
)

#: How wide the trailing run's LEAD FIELD is. The run is longer than this on a
#: minority of payloads and never shorter on any real one - see
#: :data:`UNMEASURED_PAYLOAD_REGIONS`.
TRAILING_RUN_LEAD_BYTES: Final = INT32_SIZE

#: What that field CARRIES across this project's whole library - measured, on
#: every payload of every pair in :data:`TRAILING_RUN_PAIRS`, by
#: ``tests/save/test_trailing_run.py``. A NAME FOR A MEASUREMENT, NOT A
#: CONSTRAINT: :func:`read_trailing_run` reads the bytes and never compares
#: against this, so a corpus that carries a different value reports it rather
#: than being refused. The arm that grades the measurement is what would go
#: red, which is where a surprise belongs.
TRAILING_RUN_LEAD_MEASURED_VALUE: Final = 0

#: The fixed-width field each item-list entry OPENS with - CS-1068. It reads
#: zero on every entry of this project's library and is carried rather than
#: interpreted, the same way :attr:`ObjectReference.level_reference` is.
ITEM_LIST_ENTRY_HEAD_BYTES: Final = INT32_SIZE

#: The fixed-width field each item-list entry CLOSES with. DERIVED BY SOLVING
#: RATHER THAN ASSUMED: it is the only width in 0..32 under which every entry of
#: every list in this project's library walks exactly onto its declared end, and
#: ``tests/save/test_item_list.py`` re-derives the walk on every run.
ITEM_LIST_ENTRY_TAIL_BYTES: Final = 12

#: The ceiling :func:`read_item_list` refuses a count above. A REFUSAL, NOT A
#: CLAIM about how long a real list is - a corrupt prefix must not be able to
#: drive an unbounded walk, and nothing compares a corpus count against this.
MAX_ITEM_LIST_ENTRIES: Final = 4096

#: How many object references the pair shape writes - CS-828. Two, and the
#: number is a name for a measurement rather than a limit: a remainder carrying
#: one or three walks to a different place and is refused.
REFERENCE_PAIR_COUNT: Final = 2

#: How many length-prefixed strings that is. Each reference writes a level
#: reference and an object path, exactly as :class:`ObjectReference` carries one.
REFERENCE_PAIR_STRINGS: Final = REFERENCE_PAIR_COUNT * 2

#: The fixed-width tail one schema writes after the two references. DERIVED BY
#: SOLVING RATHER THAN ASSUMED: across this project's library the bytes left
#: after the four prefixes take exactly two values, zero and this one, over
#: every payload of every carrying class - so this is the only non-zero width
#: under which those payloads walk exactly onto their declared end.
#:
#: ITS PRESENCE IS NOT A PROPERTY OF THE RUN, and a reader that treated it as an
#: unconditional suffix would OVER-READ. One schema in the library writes it and
#: two write the same two references and stop, which is why
#: :func:`derive_reference_pair_classes` derives the form from the body rather
#: than from a version table or from ``end - at``.
REFERENCE_PAIR_TAIL_BYTES: Final = 24

#: The tail widths a body may derive. A CLOSED SET, and that is the fence: a
#: width taken from whatever was left over is the CS-830 defect, because every
#: remainder then reads and no reading could fail.
REFERENCE_PAIR_TAIL_WIDTHS: Final[tuple[int, ...]] = (0, REFERENCE_PAIR_TAIL_BYTES)

#: The default vocabulary :func:`read_properties` reads with. EMPTY, so a caller
#: that has not derived reads exactly what CS-828 left, and shared rather than
#: rebuilt so the default is not a new object on every call.
_NO_REFERENCE_PAIR_CLASSES: Final[Mapping[str, int]] = MappingProxyType({})

#: How wide the per-entry scalar the PREFIXED form of the reference LIST writes
#: is - CS-828. One int32, and it is a SHIPPED CONSTANT rather than whatever
#: was left over: a width taken from ``end - at`` closes on every payload and
#: no reading of it could fail, which is the defect that refuted CS-830 after
#: it had merged.
REFERENCE_LIST_ENTRY_PREFIX_BYTES: Final = INT32_SIZE

#: The per-entry prefix widths a body may derive. A CLOSED SET, for the same
#: reason :data:`REFERENCE_PAIR_TAIL_WIDTHS` is one. Measured on this project's
#: library BOTH are written: one carrying class writes the scalar ahead of every
#: reference and two write the reference alone, so a reader assuming either form
#: unconditionally would mis-read every body of the other.
REFERENCE_LIST_ENTRY_PREFIX_WIDTHS: Final[tuple[int, ...]] = (
    0,
    REFERENCE_LIST_ENTRY_PREFIX_BYTES,
)

#: How wide the list's own leading count is. Its VALUE is read out of the bytes
#: and is the thing that says how many entries follow - the one width in this
#: shape that the payload supplies rather than the module.
REFERENCE_LIST_COUNT_BYTES: Final = INT32_SIZE

#: The default vocabulary :func:`read_properties` reads this shape with. EMPTY,
#: so a caller that has not derived reads exactly what CS-828 left.
_NO_REFERENCE_LIST_CLASSES: Final[Mapping[str, int]] = MappingProxyType({})

#: How wide the ZERO REMAINDER shape is - CS-828. One int32, and the width is
#: a SHIPPED CONSTANT rather than whatever was left over: a reader sized by
#: ``end - at`` closes on every payload and no reading of it could fail, which
#: is the defect that refuted CS-830 after it had merged.
ZERO_REMAINDER_BYTES: Final = INT32_SIZE

#: What that field must CARRY for the remainder to read as this shape. Unlike
#: :data:`TRAILING_RUN_LEAD_MEASURED_VALUE` this IS a constraint and not just a
#: name for a measurement: the claim being made is that the region is an EMPTY
#: structure - a zero count or a zero length - so bytes saying otherwise are a
#: DIFFERENT shape and are refused rather than swallowed.
#:
#: **IT IS NOT WHAT MAKES THIS READING FALSIFIABLE, AND AN EARLIER DRAFT OF
#: THIS COMMENT SAID IT WAS.** A CS-828 verifier re-derived the vocabulary over
#: the whole library with this condition deleted and admitted exactly the same
#: classes: on today's corpus the condition refuses NO real record and is
#: exercised only by the synthetic arms. What refuses real input is the WIDTH,
#: which is :data:`ZERO_REMAINDER_BYTES` rather than the leftover - every
#: residual of any other width is declined, and residuals of many other widths
#: are what remains open on all three pairs. That is the property that keeps
#: this off the CS-830 defect, because that defect was a width taken FROM the
#: observation. The value condition is kept because the shape it names is a
#: claim about the bytes, and its weakest case is written here rather than
#: rounded up.
#:
#: WHAT IT DOES NOT CLAIM. Four zero bytes are BYTE-IDENTICAL to an empty
#: count-prefixed item list, which is CS-1068's root cause seen from the other
#: side. Nothing here says which the region IS; CS-1119 owns that question.
ZERO_REMAINDER_VALUE: Final = 0

#: The default vocabulary :func:`read_properties` reads this shape with.
#: EMPTY, so a caller that has not derived reads exactly what CS-828 left.
_NO_ZERO_REMAINDER_CLASSES: Final[Collection[str]] = frozenset()

#: How wide the NAMED-TRANSFORM list's own leading count is - CS-828. Its VALUE
#: is read out of the bytes and is the thing that says how many entries follow.
TRANSFORM_LIST_COUNT_BYTES: Final = INT32_SIZE

#: How many fixed-width scalars each entry writes after its name. A SHIPPED
#: CONSTANT rather than whatever was left over: a per-entry width taken from
#: ``end - at`` closes on every payload and no reading of it could fail, which
#: is the defect that refuted CS-830 after it had merged.
TRANSFORM_LIST_SCALARS: Final = 13

#: The narrow scalar width, written by the older of the measured layouts.
TRANSFORM_LIST_FLOAT_SCALAR_BYTES: Final = 4

#: The wide scalar width, written by the newer ones.
TRANSFORM_LIST_DOUBLE_SCALAR_BYTES: Final = 8

#: The scalar widths a body may derive. A CLOSED SET, for the same reason
#: :data:`REFERENCE_LIST_ENTRY_PREFIX_WIDTHS` is one. Measured on this project's
#: library BOTH are written - the carrying class writes the narrow block on one
#: of the three pairs CS-828 covers and the wide block on the other two - so a
#: reader assuming either width unconditionally would mis-read every body of the
#: other.
TRANSFORM_LIST_SCALAR_WIDTHS: Final[tuple[int, ...]] = (
    TRANSFORM_LIST_FLOAT_SCALAR_BYTES,
    TRANSFORM_LIST_DOUBLE_SCALAR_BYTES,
)

#: How wide the flag byte each entry ends with is. READ AND REPORTED rather
#: than stepped over: a byte this module skipped would be a byte it had
#: partitioned by arithmetic.
TRANSFORM_LIST_ENTRY_FLAG_BYTES: Final = 1

#: The default vocabulary :func:`read_properties` reads this shape with.
#: EMPTY, so a caller that has not derived reads exactly what CS-828 left.
_NO_TRANSFORM_LIST_CLASSES: Final[Mapping[str, int]] = MappingProxyType({})

#: How wide the BUILDABLE GROUP LIST's leading version word is - CS-828. Its
#: VALUE is read out of the bytes and reported; nothing here claims what it
#: denotes, only that the walk begins past it.
BUILDABLE_GROUP_LIST_VERSION_BYTES: Final = INT32_SIZE

#: How wide that list's own group count is. Its VALUE says how many groups
#: follow, which is what drives the walk.
BUILDABLE_GROUP_LIST_COUNT_BYTES: Final = INT32_SIZE

#: How wide each group's leading flag is. READ AND REPORTED rather than stepped
#: over: a field this module skipped would be a field it had partitioned by
#: arithmetic.
BUILDABLE_GROUP_FLAG_BYTES: Final = INT32_SIZE

#: The fixed block each instance opens with, ahead of its first length-prefixed
#: reference. A SHIPPED CONSTANT rather than whatever was left over: a width
#: taken from ``end - at`` closes on every payload and no reading of it could
#: fail, which is the defect that refuted CS-830 after it had merged.
BUILDABLE_INSTANCE_HEAD_BYTES: Final = 84

#: The fixed block each instance writes BETWEEN its two length-prefixed
#: references. A shipped constant for the same reason as the head block.
BUILDABLE_INSTANCE_MID_BYTES: Final = 69

#: How wide the flag that says whether an instance carries a further declared
#: structure is. A ZERO here ends the instance; anything else opens the block.
BUILDABLE_INSTANCE_EXTRA_FLAG_BYTES: Final = INT32_SIZE

#: The word between a set extra-data flag and that block's type name. READ past
#: rather than interpreted - what it denotes is a second claim this reading does
#: not carry, and a wrong name is worse than none.
BUILDABLE_INSTANCE_EXTRA_PAD_BYTES: Final = INT32_SIZE

#: How wide the extra-data block's own DECLARED SIZE is. That size is what the
#: walk steps the block by, so the width comes out of the bytes rather than out
#: of the leftover - and a size that does not land the walk on the next instance
#: makes the whole reading fail rather than stretch.
BUILDABLE_INSTANCE_EXTRA_SIZE_BYTES: Final = INT32_SIZE

#: The narrowest an instance can be - both fixed blocks, four empty length
#: prefixes and the flag. Used only to reject a count no remainder could carry
#: before the walk allocates for it.
_MINIMUM_BUILDABLE_INSTANCE_BYTES: Final = (
    BUILDABLE_INSTANCE_HEAD_BYTES
    + BUILDABLE_INSTANCE_MID_BYTES
    + INT32_SIZE * 4
    + BUILDABLE_INSTANCE_EXTRA_FLAG_BYTES
)

#: The narrowest a group can be - its flag, a one-byte class path and an
#: instance count of zero. Same use as the instance floor above.
_MINIMUM_BUILDABLE_GROUP_BYTES: Final = BUILDABLE_GROUP_FLAG_BYTES + INT32_SIZE + 1 + INT32_SIZE

#: The default vocabulary :func:`read_properties` reads this shape with.
#: EMPTY, so a caller that has not derived reads exactly what CS-828 left.
_NO_BUILDABLE_GROUP_CLASSES: Final[Collection[str]] = frozenset()

#: The flags byte's measured bits. NAMED because a bare hex literal at a use
#: site is a bit nobody can hold a table against.
TAG_FLAG_ARRAY_INDEX: Final = 0x01
TAG_FLAG_NATIVE_SERIALIZE: Final = 0x08
TAG_FLAG_BOOL_TRUE: Final = 0x10

#: Every bit this project has observed, as a mask. A byte with any bit OUTSIDE
#: it refuses the payload rather than being stepped over - see the block above.
MEASURED_TAG_FLAG_MASK: Final = (
    TAG_FLAG_ARRAY_INDEX | TAG_FLAG_NATIVE_SERIALIZE | TAG_FLAG_BOOL_TRUE
)

#: How deep a type name may nest, and how many parameters one level may carry.
#: BOUNDS, NOT MEASUREMENTS - the deepest real name nests three levels and
#: carries at most two parameters. They only stop a corrupt count from spinning.
_MAX_TYPE_NAME_DEPTH: Final = 12
_MAX_TYPE_NAME_PARAMS: Final = 12


def uses_complete_type_name(header_version: int | None, save_version: int | None) -> bool:
    """Whether a pair's payloads carry the complete-type-name tag grammar.

    NONE MEANS "THE CALLER NAMED NO PAIR", and it resolves to the legacy
    grammar. That default is load-bearing rather than tidy: every caller of
    :func:`read_properties` that predates this repair passes three positional
    arguments, so a default selecting the new grammar would silently change what
    all of them read.

    Args:
        header_version: The header version, or None.
        save_version: The save version, or None.

    Returns:
        True only for a pair in :data:`COMPLETE_TYPE_NAME_PAIRS`.
    """
    if header_version is None or save_version is None:
        return False
    return (header_version, save_version) in COMPLETE_TYPE_NAME_PAIRS


def _read_type_name(
    body: bytes, at: int, end: int, depth: int = 0
) -> tuple[str, tuple[str, ...], int] | None:
    """Read one recursive property type name.

    Args:
        body: The decompressed body.
        at: The name's first byte.
        end: The first byte past the payload.
        depth: How deep this call already is, for the nesting bound.

    Returns:
        The type word, its TOP-LEVEL parameter words, and the first byte past
        the whole name. None when any part of it does not read.

        ONLY THE TOP LEVEL COMES BACK, and that is not laziness. The top level
        is exactly what a container's element words are; the deeper levels
        describe a struct interior, which is CS-829's measurement and not this
        function's. Handing back the whole tree would invite a caller to read a
        struct shape out of it that no measurement supports.
    """
    if depth > _MAX_TYPE_NAME_DEPTH:
        return None
    step = _payload_text(body, at, end)
    if step is None:
        return None
    word, cursor = step
    if cursor + INT32_SIZE > end:
        return None
    (count,) = struct.unpack_from("<i", body, cursor)
    cursor += INT32_SIZE
    if count < 0 or count > _MAX_TYPE_NAME_PARAMS:
        return None
    params: list[str] = []
    for _ in range(count):
        nested = _read_type_name(body, cursor, end, depth + 1)
        if nested is None:
            return None
        params.append(nested[0])
        cursor = nested[2]
    return (word, tuple(params), cursor)


def _read_type_tree_tag_header(
    body: bytes, at: int, end: int
) -> tuple[str, int, int, int | None, tuple[str, ...], bool] | None:
    """Read one tag of the complete-type-name grammar, stopping at its value.

    THE RETURN SHAPE IS ITS OWN rather than :func:`_read_tag_header`'s, and the
    fifth element is why: the element words live INSIDE the type name here, so
    the read that produced them is the only place they exist. The legacy grammar
    re-reads its words from the name offset because they sit in the tag data
    after it; re-reading a nested name would be parsing it twice to arrive back
    at what the first parse already had.

    THE SIXTH ELEMENT IS THE NATIVE-SERIALIZE BIT, CARRIED OUT RATHER THAN
    STEPPED OVER. It was defined, folded into the measured mask and consumed by
    nothing - a grep over the package and the suite found the constant's two
    definition lines and no use at all - and :func:`_decode_container` is where
    it earns its name. The alternative was a second read of the flags byte from
    the name offset, which means parsing the whole nested type name again to
    arrive back at a byte this read already had; two derivations of one byte is
    the shape that drifts. Widening here fails LOUDLY instead: every consumer
    of this tuple unpacks it positionally.

    Args:
        body: The decompressed body.
        at: Just past the tag's name.
        end: The first byte past the payload.

    Returns:
        The type word, where the value starts, its declared size, the byte a
        BoolProperty carries in its flags, the type name's top-level parameter
        words, and whether the tag declared :data:`TAG_FLAG_NATIVE_SERIALIZE`.
        None if the tag does not read - including when the flags byte carries a
        bit outside :data:`MEASURED_TAG_FLAG_MASK`.
    """
    named = _read_type_name(body, at, end)
    if named is None:
        return None
    type_word, params, cursor = named
    if cursor + INT32_SIZE + 1 > end:
        return None
    (size,) = struct.unpack_from("<i", body, cursor)
    cursor += INT32_SIZE
    flags = body[cursor]
    cursor += 1
    if flags & ~MEASURED_TAG_FLAG_MASK:
        return None
    if flags & TAG_FLAG_ARRAY_INDEX:
        cursor += INT32_SIZE
    in_tag_byte = None
    if type_word == "BoolProperty":
        # THE BIT IS THE VALUE. The legacy grammar gave a bool its own byte
        # ahead of the guid flag; here one byte does both jobs, and a reader
        # expecting two desynchronises on the tag after every bool.
        in_tag_byte = 1 if flags & TAG_FLAG_BOOL_TRUE else 0
    if size < 0 or cursor + size > end:
        return None
    return (type_word, cursor, size, in_tag_byte, params, bool(flags & TAG_FLAG_NATIVE_SERIALIZE))


def _container_element_words(
    body: bytes, at: int, end: int, type_word: str
) -> tuple[str, ...] | None:
    """Collect the element type words a container's tag carries.

    IT RE-READS RATHER THAN WIDENING :func:`_read_tag_header`'s RETURN SHAPE,
    and that is deliberate. A return shape is an interface: widening one in
    place is how a caller starts reading the wrong tuple element in silence,
    which is the failure ``_walk_payload`` records CS-831 designing around. The
    re-read is a handful of string reads over bytes already in cache.

    Args:
        body: The decompressed body.
        at: Where the tag's TYPE WORD begins - that is, just past its name.
        end: The first byte past the payload.
        type_word: The tag's type word.

    Returns:
        The element type words in tag order, or None when they do not read.
        An empty tuple for a word that carries none, which is not the same as
        None and is why the caller checks for None rather than for falsehood.
    """
    type_read = _payload_text(body, at, end)
    if type_read is None:
        return None
    cursor = type_read[1] + INT32_SIZE + _TAG_INDEX_FIELD_BYTES
    words: list[str] = []
    for _ in range(_TAG_EXTRA_STRINGS.get(type_word, 0)):
        step = _payload_text(body, cursor, end)
        if step is None:
            return None
        words.append(step[0])
        cursor = step[1]
    return tuple(words)


def _element_tag_list_end(body: bytes, at: int, end: int, *, type_tree: bool = False) -> int | None:
    """Walk one NESTED property tag list and report where it closes.

    An element of a struct is a tag list closed by the same terminator name a
    payload uses. NOTHING INSIDE IT IS DECODED HERE - the walk reads each tag's
    header only, to step by its declared size. The interior is CS-829's, and
    reading a value out of it would be exactly the guess this decode declines.

    IT GOES THROUGH :func:`_read_tag_and_words` RATHER THAN CALLING A GRAMMAR
    DIRECTLY, so the pair dispatch lives at the one site that owns it. Under
    the legacy grammar that is the same reading it did before: the element
    words that call also reads come from the same offsets
    :func:`_skip_tag_extra` already stepped over, so a header that read there
    reads them too.

    Args:
        body: The decompressed body.
        at: Where the first nested tag begins.
        end: The first byte past the element region.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one - see :func:`uses_complete_type_name`. DEFAULTED so that adding
            it could not change what any existing caller reads.

    Returns:
        The first byte past the terminator, or None when the list does not close.
    """
    cursor = at
    for _ in range(_MAX_ELEMENT_TAGS):
        name = _payload_text(body, cursor, end)
        if name is None:
            return None
        if name[0] == _PAYLOAD_TERMINATOR:
            return name[1]
        header = _read_tag_and_words(body, name[1], end, type_tree=type_tree)
        if header is None:
            return None
        cursor = header[1] + header[2]
    return None


def _element_half_end(
    body: bytes, word: str, at: int, end: int, width: int | None, *, type_tree: bool = False
) -> int | None:
    """Where one element half ends, by its own grammar or by a forced width.

    THE TWO BRANCHES ARE NOT EQUALLY STRONG AND THE FORCED ONE CANNOT FAIL
    USEFULLY. Under a width it returns ``at + width`` after a bounds check, and
    while slots remain that check holds by arithmetic - so a walk under an even
    division closes whatever the bytes say, and its closing is not evidence
    about them. Under ``None`` the word's own grammar decides, a wrong reading
    does not close, and the refusal IS evidence. See the commentary block above
    :data:`UNDISCRIMINATED_ELEMENT_SHAPES`.

    Args:
        body: The decompressed body.
        word: The element half's type word.
        at: The half's first byte.
        end: The first byte past the element region.
        width: A forced raw width, or None to use the word's own grammar.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one inside a nested tag list - see :func:`uses_complete_type_name`.

    Returns:
        The first byte past the half, or None when it does not read.
    """
    if width is not None:
        return at + width if 0 <= width <= end - at else None
    fixed = _ELEMENT_FIXED_WIDTHS.get(word)
    if fixed is not None:
        return at + fixed if at + fixed <= end else None
    strings = _ELEMENT_STRING_COUNTS.get(word)
    if strings is not None:
        cursor = at
        for _ in range(strings):
            step = _payload_text(body, cursor, end)
            if step is None:
                return None
            cursor = step[1]
        if word == "SoftObjectProperty":
            cursor += _SOFT_OBJECT_TAIL_BYTES
        return cursor if cursor <= end else None
    if word == _ELEMENT_TAG_LIST_WORD:
        return _element_tag_list_end(body, at, end, type_tree=type_tree)
    return None


def _walk_elements(
    body: bytes,
    words: tuple[str, ...],
    at: int,
    end: int,
    count: int,
    widths: tuple[int | None, ...],
    *,
    type_tree: bool = False,
) -> tuple[ContainerElement, ...] | None:
    """Bound every element half, refusing anything that does not close exactly.

    THE EXACT CLOSE IS THE WHOLE DISCRIMINATOR. Returning what could be read
    would make the acceptance equality hold by construction on any framing at
    all, which is why a short or an overrunning walk yields None rather than a
    truncated list.

    IT BOUNDS AND DOES NOT DECODE - CS-1038. This function is the SEARCH:
    :func:`_bound_container_elements` calls it once per candidate shape and up
    to :data:`_SOLVED_WIDTH_CAP` more times per half while solving a width, so
    a decode inside it runs once per CANDIDATE rather than once per element -
    and a struct element's interior is a recursive walk that may hold further
    containers with searches of their own. Every element therefore comes back
    with ``value`` None here, and the WINNING partition is decoded exactly once
    by :func:`_decode_bounded_elements`.

    Args:
        body: The decompressed body.
        words: The element type words, one per half of an entry.
        at: Where the first element begins.
        end: The first byte past the element region.
        count: How many entries the container declared.
        widths: A forced width per half, each None to use that word's grammar.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one inside a nested tag list - see :func:`uses_complete_type_name`.

    Returns:
        One entry per element half in byte order and every value None, or None
        when the halves do not consume the region exactly.
    """
    cursor = at
    found: list[ContainerElement] = []
    for _ in range(count):
        for position, word in enumerate(words):
            step = _element_half_end(body, word, cursor, end, widths[position], type_tree=type_tree)
            if step is None:
                return None
            found.append(
                ContainerElement(type_word=word, start=cursor, length=step - cursor, value=None)
            )
            cursor = step
    return tuple(found) if cursor == end else None


def _decode_element_interior(
    body: bytes,
    at: int,
    end: int,
    *,
    struct_word: str | None,
    own_grammar: bool,
    depth: int,
    type_tree: bool,
) -> StructValue | None:
    """Read a struct ELEMENT's interior, or refuse it - CS-1038.

    THE GATE IS ``own_grammar`` AND IT IS NOT COSMETIC. A struct element has two
    shapes: a nested tag list, and a RAW body whose width was DERIVED by
    dividing the element region. Under a derived width the region is not a tag
    list at all, and reading one out of it would be publishing an interior the
    writer never wrote - the "silently wrong" half of non-negotiable 7. The
    caller passes True only where the half was bounded by the word's OWN
    grammar, which is exactly where a wrong reading would have failed to close.

    THE DEPTH GOES UP BY ONE, exactly as :func:`_decode_interior_tag` counts a
    struct nested directly. Passing the caller's depth through unchanged would
    make :data:`MAX_STRUCT_DEPTH` unreachable: struct, container, struct
    element, container is a cycle whose byte regions strictly shrink and whose
    depth would never move, so it would terminate on the interpreter's stack
    rather than on the bound - a crash where non-negotiable 7 asks for a flag
    and a skip.

    NOTHING HERE IS FATAL. A refusal comes back None and the element stays
    bounded, typed and unread, which is the state every struct element was in
    before this.

    Args:
        body: The decompressed body.
        at: The element's first byte.
        end: The first byte past the element.
        struct_word: The struct word the CONTAINER named, or None when it named
            none. Recorded on the interior; it does not drive the reading.
        own_grammar: Whether this half was bounded by the word's own grammar
            rather than by a derived width.
        depth: How deep the container holding this element sits.
        type_tree: Read the complete-type-name grammar inside the interior - see
            :func:`uses_complete_type_name`.

    Returns:
        The interior, or None when the region is not a tag list closing exactly
        at ``end`` or was not bounded by the element's own grammar.
    """
    if not own_grammar:
        return None
    return _decode_struct_interior(body, struct_word, at, end, depth + 1, type_tree=type_tree)


def _decode_element_value(
    body: bytes,
    word: str,
    at: int,
    end: int,
    *,
    struct_word: str | None = None,
    own_grammar: bool = False,
    depth: int = 0,
    type_tree: bool = False,
) -> object | None:
    """Decode one element's value, or refuse to.

    IT REFUSES FOR A TYPE WHOSE TOP-LEVEL VALUE THIS MODULE DOES NOT DECODE.
    Bounding an element is a claim about the CONTAINER's framing; reading it is
    a claim about that type's own encoding, and CS-830 earned only the first.

    A STRUCT ELEMENT IS THE ONE EXCEPTION AND IT IS EARNED RATHER THAN ASSUMED -
    CS-1038. CS-829 measured the interior grammar and applied it at TOP LEVEL
    ONLY, so every array of struct bounded its elements perfectly and read none
    of them: ``mInventoryStacks``, ``mSplineData`` and their siblings arrived
    typed, bounded and empty. The grammar an element tag list closes under IS
    the interior grammar - :data:`_ELEMENT_TAG_LIST_WORD` is spelled as
    :data:`STRUCT_TYPE_WORD` for exactly that reason - so applying it here reads
    a measured shape rather than a guessed one.

    THE GATE AND THE DEPTH BOUND LIVE IN :func:`_decode_element_interior`, which
    owns the struct branch. They are not restated here - a rule written down at
    two sites rots at the second one.

    Args:
        body: The decompressed body.
        word: The element's type word.
        at: The element's first byte.
        end: The first byte past the element.
        struct_word: The struct word the CONTAINER named, or None when it named
            none. Recorded on the interior; it does not drive the reading.
        own_grammar: Whether this half was bounded by the word's own grammar
            rather than by a derived width.
        depth: How deep the container holding this element sits, so a struct
            nested through a container is bounded by :data:`MAX_STRUCT_DEPTH`
            exactly as one nested directly is.
        type_tree: Read the complete-type-name grammar inside the interior - see
            :func:`uses_complete_type_name`.

    Returns:
        The value, or None when the element's type is not decoded here.
    """
    if word == _ELEMENT_TAG_LIST_WORD:
        return _decode_element_interior(
            body,
            at,
            end,
            struct_word=struct_word,
            own_grammar=own_grammar,
            depth=depth,
            type_tree=type_tree,
        )
    if word not in MEASURED_VALUE_TYPES or word in CONTAINER_TYPE_WORDS:
        return None
    fixed = _FIXED_WIDTH_VALUES.get(word)
    if fixed is not None:
        return _decode_fixed_width(body, at, end - at, fixed)
    if word in _TWO_STRING_VALUES:
        return _decode_object_reference(body, word, at, end)
    if word in _ONE_STRING_VALUES:
        step = _payload_text(body, at, end)
        return None if step is None or step[1] != end else step[0]
    return None


def _decode_bounded_elements(
    body: bytes,
    elements: tuple[ContainerElement, ...],
    widths: tuple[int | None, ...],
    *,
    struct_word: str | None,
    depth: int,
    type_tree: bool,
) -> tuple[ContainerElement, ...]:
    """Decode the values of a partition that has ALREADY WON - CS-1038.

    IT RUNS ONCE PER CONTAINER RATHER THAN ONCE PER CANDIDATE, and that is the
    whole reason it exists apart from :func:`_walk_elements`. The shape search
    walks the region up to :data:`_SOLVED_WIDTH_CAP` times per half, so decoding
    inside it would run a struct element's interior - itself a recursive walk
    that may hold further containers with searches of their own - once per
    CANDIDATE rather than once per element. That is a structural argument about
    the search rather than a benchmark, and no figure is claimed for it.

    WHAT WAS MEASURED IS THAT THE INTERIOR READING ITSELF IS NOT THE COST. With
    the split in place, the shipped container sweep over this machine's library
    took the same time with the interior decode disabled as with it enabled -
    the difference was inside the run-to-run spread. The separation is kept
    because the search is the thing that repeats, not because the decode is
    expensive.

    IT CHANGES NOTHING ABOUT WHICH PARTITION IS CHOSEN, because a value has
    never been part of that decision: :func:`_walk_elements` accepts or refuses
    on whether the halves consume the region exactly, and nothing below that
    close is consulted.

    THE ``own_grammar`` FLAG COMES OFF THE SAME ``widths`` TUPLE the walk was
    bounded under, indexed by the half's position in the entry. A second
    derivation of "was this half read or forced" would be a second place for the
    two to disagree, and they would disagree silently: an interior read out of a
    raw region either refuses or, worse, closes.

    Args:
        body: The decompressed body.
        elements: The winning partition, every value None.
        widths: The forced width per half the partition was bounded under, each
            None where the half's own grammar decided.
        struct_word: The struct word the container named, or None.
        depth: How deep the container sits.
        type_tree: Read the complete-type-name grammar inside a nested tag list.

    Returns:
        The same partition with every decodable value read.
    """
    halves = len(widths)
    return tuple(
        ContainerElement(
            type_word=element.type_word,
            start=element.start,
            length=element.length,
            value=_decode_element_value(
                body,
                element.type_word,
                element.start,
                element.start + element.length,
                struct_word=struct_word,
                own_grammar=widths[index % halves] is None,
                depth=depth,
                type_tree=type_tree,
            ),
        )
        for index, element in enumerate(elements)
    )


def _bound_container_elements(
    body: bytes,
    words: tuple[str, ...],
    at: int,
    end: int,
    count: int,
    *,
    struct_word: str | None = None,
    depth: int = 0,
    type_tree: bool = False,
) -> tuple[str, tuple[ContainerElement, ...]] | None:
    """Bound a container's elements by the STRONGEST shape that closes the region.

    THE ORDER IS LOAD-BEARING AND IS NOT A PREFERENCE. Taking the shapes as
    alternatives rather than as a fallback chain made two of them close on a
    large majority of the struct arrays, because a container holding one element
    is divided by one and ANY width closes it. Trying the falsifiable reading
    first means the derived ones are reached only where nothing stronger applies.

    Args:
        body: The decompressed body.
        words: The element type words, one per half of an entry.
        at: Where the first element begins.
        end: The first byte past the element region.
        count: How many entries the container declared.
        struct_word: The struct word the container named, or None - CS-1038.
            Passed through to a struct element's interior, which records it.
        depth: How deep the container sits, so a struct reached through one is
            bounded by :data:`MAX_STRUCT_DEPTH` exactly as a nested one is.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one inside a nested tag list - see :func:`uses_complete_type_name`.

    Returns:
        The shape that bounded them and the elements, or None when none did.
    """
    blank: tuple[int | None, ...] = (None,) * len(words)
    found = _walk_elements(body, words, at, end, count, blank, type_tree=type_tree)
    if found is not None:
        return (
            ELEMENT_SHAPE_SELF_DELIMITING,
            _decode_bounded_elements(
                body,
                found,
                blank,
                struct_word=struct_word,
                depth=depth,
                type_tree=type_tree,
            ),
        )

    # ONLY A HALF WITH A SECOND KNOWN SHAPE MAY BE FORCED TO A WIDTH, and that
    # restriction is the repair for a real defect rather than a caution. Without
    # it an array of four IntProperty carrying only three of them was rescued by
    # dividing twelve bytes into four threes: the element word's OWN width said
    # the region did not close, and a derived width overrode it and published a
    # value. That is the "silently wrong" half of non-negotiable 7. A word with
    # exactly one element shape is now never overridden - if its shape does not
    # close, the container is refused.
    if not all(word in _RAW_SHAPE_ELEMENT_WORDS for word in words):
        return None

    # ONE WIDTH FOR EVERY HALF, DERIVED BY DIVISION. Its only discriminator is
    # that the division is exact, so over a single slot it is the identity.
    slots = count * len(words)
    if slots > 0 and (end - at) % slots == 0:
        width = (end - at) // slots
        forced_widths = (width,) * len(words)
        found = _walk_elements(body, words, at, end, count, forced_widths, type_tree=type_tree)
        if found is not None:
            return (
                ELEMENT_SHAPE_UNIFORM_WIDTH,
                _decode_bounded_elements(
                    body,
                    found,
                    forced_widths,
                    struct_word=struct_word,
                    depth=depth,
                    type_tree=type_tree,
                ),
            )

    # ONE HALF'S WIDTH SOLVED, THE REST BY THEIR OWN GRAMMAR. Admitted only
    # when exactly one width closes the region: two would mean the width is not
    # determined by the bytes, and a decoder that picked one would be fitting.
    for position in range(len(words)):
        solutions: list[tuple[tuple[ContainerElement, ...], tuple[int | None, ...]]] = []
        for width in range(_SOLVED_WIDTH_CAP + 1):
            forced: list[int | None] = [None] * len(words)
            forced[position] = width
            solved_widths = tuple(forced)
            found = _walk_elements(body, words, at, end, count, solved_widths, type_tree=type_tree)
            if found is not None:
                solutions.append((found, solved_widths))
                if len(solutions) > 1:
                    break
        if len(solutions) == 1:
            elements, solved_widths = solutions[0]
            return (
                ELEMENT_SHAPE_SOLVED_WIDTH,
                _decode_bounded_elements(
                    body,
                    elements,
                    solved_widths,
                    struct_word=struct_word,
                    depth=depth,
                    type_tree=type_tree,
                ),
            )
    return None


def _read_array_struct_tag(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """Read the inner tag an array of struct carries ahead of its elements.

    An array of ``StructProperty`` writes ONE tag naming the struct and
    declaring the extent of the WHOLE element region, then the elements. The
    struct word is carried out because it is what CS-829 needs; the extent is
    checked against the value's own end rather than trusted.

    THERE IS NO SUCH TAG ON THE PAIRS IN :data:`COMPLETE_TYPE_NAME_PAIRS`, AND
    THIS FUNCTION IS NOT CALLED THERE. That is MEASURED rather than assumed -
    see the comment at the one call site in :func:`_decode_container`. Reading
    a tree-grammar tag here anyway was tried and is recorded there as refuted.

    Args:
        body: The decompressed body.
        at: Where the inner tag begins.
        end: The first byte past the container's value.

    Returns:
        The struct type word and where the elements begin, or None when the
        inner tag does not read or does not account for the region exactly.
    """
    name = _payload_text(body, at, end)
    if name is None:
        return None
    word = _payload_text(body, name[1], end)
    if word is None or word[0] != _ELEMENT_TAG_LIST_WORD:
        return None
    cursor = word[1]
    if cursor + INT32_SIZE + _TAG_INDEX_FIELD_BYTES > end:
        return None
    (region,) = struct.unpack_from("<i", body, cursor)
    struct_read = _payload_text(body, cursor + INT32_SIZE + _TAG_INDEX_FIELD_BYTES, end)
    if struct_read is None:
        return None
    elements_at = struct_read[1] + GUID_BYTES + 1
    if region < 0 or elements_at > end or elements_at + region != end:
        return None
    return (struct_read[0], elements_at)


def _open_container(
    body: bytes, type_word: str, element_words: tuple[str, ...], at: int, size: int
) -> tuple[int, int, int] | None:
    """Read a container's lead fields and its element count, or refuse.

    THE ELEMENT WORD COUNT IS CHECKED AGAINST THE SHIPPED TAG-EXTRA TABLE
    rather than trusted from the caller. A map reached with one word instead of
    two would otherwise decode its keys as though they were whole entries, and
    the region would close on some population by luck.

    Args:
        body: The decompressed body.
        type_word: The container's type word.
        element_words: The element type words its tag carried.
        at: The value's first byte.
        size: The value's declared extent.

    Returns:
        The declared element count, where the elements begin and the first byte
        past the value, or None when any of it does not read.
    """
    lead = _CONTAINER_LEAD_FIELDS.get(type_word)
    if lead is None or size < 0 or at + size > len(body):
        return None
    if not element_words or len(element_words) != _TAG_EXTRA_STRINGS.get(type_word, 0):
        return None
    end = at + size
    cursor = at + lead * INT32_SIZE
    if cursor + INT32_SIZE > end:
        return None
    (count,) = struct.unpack_from("<i", body, cursor)
    if count < 0 or count > _MAX_CONTAINER_ELEMENTS:
        return None
    return (count, cursor + INT32_SIZE, end)


def _decode_container(
    body: bytes,
    type_word: str,
    element_words: tuple[str, ...],
    at: int,
    size: int,
    *,
    depth: int = 0,
    type_tree: bool = False,
    native_serialize: bool | None = None,
) -> ContainerValue | None:
    """Decode one container tag's element framing - CS-830.

    NONE MEANS THE FRAMING DID NOT CLOSE, and the caller decides what that
    means: a container whose element word has no grammar at all is UNMODELLED
    CONTENT, where one this module can bound whose bytes then disagree is a walk
    that has lost its place. :func:`_walk_payload` separates the two rather than
    collapsing them, because they mean opposite things.

    A NATIVE-SERIALIZED CONTAINER MAY NOT BE PUBLISHED UNDER A DERIVED WIDTH,
    and that refusal is non-negotiable 7 rather than caution. The derived
    shapes' whole admission test is that an integer divided evenly, or that one
    width in a searched range closed; neither is a fact about the bytes between
    the boundaries. The flags byte is the WRITER saying the value went through a
    native serializer, which is a statement that the region is not the tag list
    the element grammar would be reading - so where the bit is set this module
    has no evidenced partition at all, and publishing an arithmetic one is the
    "silently wrong" half the non-negotiable rules out. Flag it and skip it: the
    caller's advance steps by the tag's own declared size and is unaffected.

    WHAT THIS DOES NOT DO IS DELETE THE DERIVED BRANCHES. They stay reachable
    for every container whose tag did not set the bit, and for the legacy
    grammar, which has no flags byte and therefore says nothing either way -
    ``native_serialize`` is None there and nothing below changes.

    A SELF-DELIMITING CLOSE IS STILL ADMITTED UNDER THE BIT, deliberately. That
    shape is falsifiable element by element: a wrong reading fails to close, so
    its closing is evidence about the bytes rather than about arithmetic, and
    refusing it would be discarding the strong reading along with the weak one.
    A synthetic fixture writes exactly that combination -
    ``tests/save/test_struct_interior_14_60.py`` - so the line between the two
    is exercised rather than asserted.

    WHAT WAS MEASURED, read-only and counts only, over the 11 saves of this
    pair reachable in the library on the run that filed this: 11272 container
    decodes at (14,60). Every one of the 11242 whose tag left the bit clear
    closed SELF-DELIMITING. Every one of the 30 that set it fell to a derived
    width and NOT ONE of them closed self-delimiting. The bit partitions the
    population exactly, which is what makes it a predictor rather than a
    correlation - and the figure is scoped to that pair and that run, because
    the operator plays this game and the population moves.

    Args:
        body: The decompressed body.
        type_word: The container's type word.
        element_words: The element type words its tag carried.
        at: The value's first byte.
        size: The value's declared extent.
        depth: How far inside another struct the tag holding this container
            sits. Carried so a struct ELEMENT's interior is bounded by
            :data:`MAX_STRUCT_DEPTH` - CS-1038. Without it a struct holding a
            container of structs holding a container would recurse on a body
            whose regions strictly shrink, which terminates only when the
            interpreter's stack does.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one for the inner tag and for any nested tag list - see
            :func:`uses_complete_type_name`.
        native_serialize: Whether the tag declared a native-serialized value,
            or None when the grammar states nothing. DEFAULTED so that adding
            it could not change what any existing caller reads.

    Returns:
        The container, or None when the elements do not consume the declared
        size exactly, or when the only reading that closed was a derived width
        on a tag that declared a native-serialized value.
    """
    opened = _open_container(body, type_word, element_words, at, size)
    if opened is None:
        return None
    count, cursor, end = opened

    # THE INNER TAG IS A LEGACY-ONLY FIELD, MEASURED AND NOT ASSUMED. An array
    # of struct writes its element count and then, on the legacy pairs, ONE tag
    # naming the struct and declaring the whole element region. On the pairs in
    # :data:`COMPLETE_TYPE_NAME_PAIRS` it writes the elements straight after
    # the count and no inner tag at all.
    #
    # WHAT WAS MEASURED, read-only and counts only, over every (14,60) save in
    # the library reachable at the time: 6198 `ArrayProperty` tags whose one
    # element word is `StructProperty`. Walking `count` element tag lists from
    # the byte after the count closes the value EXACTLY on 6187 of them and
    # fails on 11. Reading a tree-grammar inner tag there instead read 0 of
    # 6198 - the type name it found was the FIRST ELEMENT'S first property, its
    # int32 was that property's declared size, and the region it implied fell
    # short of the value end by hundreds of bytes on every one.
    #
    # THE STRUCT WORD IS THEREFORE NOT STATED HERE AND IS LEFT None. It is one
    # level further down the tag's own type name, and reading a struct word out
    # of a type name is CS-829's measurement rather than this frame's - see
    # `_read_type_name`, which hands back only the top level for that reason.
    # None already means "this container named no struct word", so nothing here
    # publishes a word the save did not write.
    struct_word: str | None = None
    if (
        not type_tree
        and type_word == "ArrayProperty"
        and element_words == (_ELEMENT_TAG_LIST_WORD,)
    ):
        inner = _read_array_struct_tag(body, cursor, end)
        if inner is None:
            return None
        struct_word, cursor = inner

    bounded = _bound_container_elements(
        body,
        element_words,
        cursor,
        end,
        count,
        struct_word=struct_word,
        depth=depth,
        type_tree=type_tree,
    )
    if bounded is None:
        return None
    shape, elements = bounded
    if native_serialize and shape in _UNEVIDENCED_UNDER_NATIVE_SERIALIZE:
        # THE ONE READING THAT CLOSED IS THE ONE THE TAG SAYS IS NOT THERE.
        # Publishing it would put a width DERIVED BY DIVISION beside widths
        # READ FROM THE BYTES with nothing on the value to tell them apart -
        # see the docstring above.
        return None
    return ContainerValue(
        type_word=type_word,
        element_words=element_words,
        element_count=count,
        elements=elements,
        element_shape=shape,
        struct_word=struct_word,
    )


def _container_grammar_is_modelled(element_words: tuple[str, ...]) -> bool:
    """Whether every element half of a container has a grammar this module reads.

    Args:
        element_words: The element type words the container's tag carried.

    Returns:
        Whether every half is a word this module has an element grammar for.
    """
    return bool(element_words) and all(
        word in _ELEMENT_FIXED_WIDTHS
        or word in _ELEMENT_STRING_COUNTS
        or word == _ELEMENT_TAG_LIST_WORD
        for word in element_words
    )


def _refusal_is_unmodelled_content(
    type_word: str, element_words: tuple[str, ...], *, native_serialize: bool | None = None
) -> bool:
    """Which counter a refused value belongs in - unmodelled content, or a lost walk.

    THE TWO MEAN OPPOSITE THINGS AND THE WHOLE POINT IS NOT COLLAPSING THEM.
    An unmeasured type is content this project has not modelled: expected,
    benign, and exactly what non-negotiable 7 says to flag and skip. A MEASURED
    type whose bytes disagreed is the redundancy oracle running in production -
    the reader is not where it believes it is, and every value after it in the
    same payload is suspect.

    THE CONTAINER CASE IS WHY THIS IS A FUNCTION AND NOT AN ``in`` TEST -
    CS-830. A container's FRAMING is measured, so the word is in
    :data:`MEASURED_VALUE_TYPES` and a refusal normally means the oracle fired.
    But a container whose ELEMENT word this module has no grammar for is
    unmodelled content sitting inside a frame that read perfectly, and the walk
    is not lost - the caller's advance steps by the tag's own declared size and
    is unaffected. Counting that as a disagreement reports new game content as a
    broken reader, which is the direction with no second chance.

    A NATIVE-SERIALIZED CONTAINER IS UNMODELLED CONTENT WHATEVER ITS ELEMENT
    WORDS ARE, and that clause is checked FIRST rather than folded in with the
    grammar test. The bit is the writer saying the value did not go through the
    tagged-property path at all, so the element grammar this module holds is not
    the grammar those bytes are in - the word being one it CAN read says
    nothing, because the region is not the thing the word describes. Reporting
    that as a lost walk would fire the redundancy oracle on content the save
    told us it had written some other way, which is reporting new game content
    as a broken reader: the direction with no second chance.

    Args:
        type_word: The tag's type word.
        element_words: The element type words a container's tag carried, empty
            for every other type.
        native_serialize: Whether the tag declared a native-serialized value,
            or None when the grammar states nothing. DEFAULTED, so the legacy
            grammar and every caller that predates the field route exactly as
            they did.

    Returns:
        Whether the refusal is unmodelled content rather than a lost walk.
    """
    if type_word in CONTAINER_TYPE_WORDS:
        return bool(native_serialize) or not _container_grammar_is_modelled(element_words)
    return type_word not in MEASURED_VALUE_TYPES


def _struct_word_of_tag(body: bytes, name_at: int, end: int) -> str | None:
    """The struct type word a ``StructProperty`` tag carries, or None.

    IT IS RE-READ FROM THE NAME OFFSET rather than handed back by
    :func:`_read_tag_header`, for the reason CS-830 gives at the container
    site: widening that function's return shape in place is how a caller starts
    unpacking the wrong element in silence. The word sits between the tag's
    index field and its guid, which is exactly where
    :func:`_container_element_words` reads a container's element words from -
    the two are the same tag-extra run, and :data:`_TAG_EXTRA_STRINGS` is what
    says how many strings each type puts there.

    Args:
        body: The decompressed body.
        name_at: Where the tag's TYPE WORD begins - that is, just past its name.
        end: The first byte past the payload.

    Returns:
        The struct word, or None when the tag extra does not read.
    """
    words = _container_element_words(body, name_at, end, STRUCT_TYPE_WORD)
    # THE EMPTINESS CHECK IS SEPARATE FROM THE COUNT CHECK AND IS NOT REDUNDANT
    # WITH IT. The count comes from :data:`_TAG_EXTRA_STRINGS`, a SHIPPED WIDTH
    # that the width-mutation census in ``tests/save/test_properties.py``
    # deliberately mis-states on the real module. Mis-stated to zero, the count
    # check passes against an EMPTY tuple and indexing it RAISED - out of a
    # function whose whole contract is to return None on anything it cannot
    # read. Found by that census, not by reasoning: the two conditions look like
    # one until the number they are compared against can be zero.
    if words is None or not words or len(words) != _TAG_EXTRA_STRINGS.get(STRUCT_TYPE_WORD, 0):
        return None
    return words[0]


def _decode_struct_interior(
    body: bytes,
    struct_word: str | None,
    at: int,
    end: int,
    depth: int = 0,
    *,
    type_tree: bool = False,
) -> StructValue | None:
    """Decode one struct interior written as a nested property tag list - CS-829.

    WHAT DISCRIMINATES IS THE TAG-GRAMMAR CHAIN, not the closing comparison,
    and saying otherwise was a measured overstatement in this docstring's first
    version. Every interior tag's name, type word, declared size and guid flag
    must read, and the cursor each computes must land on a tag that also reads,
    until a terminator. That chain refuses a wrong offset, and it is strong
    enough that exactly ONE end closes per site out of every end the declared
    size admits - which is what makes a population of interiors closing evidence
    about the format rather than about arithmetic.

    THE ``end`` EQUALITY BELOW IS CURRENTLY INERT AND IS KEPT ANYWAY. Loosening
    it to "at or before" leaves the entire library census bit-identical. It is
    retained because a corpus that placed a terminator earlier would need it,
    and ``tests/save/test_struct_interior.py`` asserts the inertness, so the day
    it stops being inert is visible rather than silent.

    NONE MEANS "NOT A TAG LIST", WHICH IS NOT THE SAME AS "BROKEN". Most
    refusals here are the NATIVE form doing exactly what it does: raw bytes
    carrying no tags. That is content this project has not measured, the
    caller's own advance steps by the tag's declared size and is unaffected,
    and non-negotiable 7 asks for a flag and a skip. See
    :func:`_refusal_is_unmodelled_content`.

    IT COLLECTS NO REFERENCES, AND THAT IS DELIBERATE RATHER THAN AN OVERSIGHT.
    An ``ObjectProperty`` inside an interior decodes to its pair and lands in
    ``properties`` like any other value, but it does NOT join the population
    :func:`resolve_references` partitions. That population is a top-level tag
    count CS-831 grades an identity against, and widening it here would move a
    denominator this slice has measured nothing about.

    THE LOOP IS NOT :func:`_walk_payload`'S AND THE DIFFERENCE IS THE CONTRACT.
    That walk terminates wherever the terminator falls and collects references;
    this one must close at a stated byte and does not. What the two share is the
    part that matters - :func:`_read_tag_header` and :func:`_payload_text` - so
    there is one tag grammar in this module and not two.

    Args:
        body: The decompressed body.
        struct_word: The struct type word the tag carried, or None when the tag
            named none - see :class:`StructValue`, which owns what None means.
        at: The interior's first byte.
        end: The first byte past the interior, from the tag's declared size.
        depth: How far inside another struct this one sits.
        type_tree: Read the complete-type-name tag grammar inside this interior
            rather than the legacy one - see :func:`uses_complete_type_name`.
            DEFAULTED so that adding it could not change what any existing
            caller reads.

    Returns:
        The decoded interior, or None when it is not a tag list closing exactly
        at ``end``.
    """
    if depth > MAX_STRUCT_DEPTH or at < 0 or at > end or end > len(body):
        return None
    walked = _walk_struct_tags(body, at, end, depth, type_tree=type_tree)
    if walked is None:
        return None
    decoded, unmeasured, disagreed = walked
    return StructValue(
        struct_word=struct_word,
        form=STRUCT_FORM_TAG_LIST,
        properties=MappingProxyType(decoded),
        unmeasured=unmeasured,
        disagreed=disagreed,
        depth=depth,
    )


def _read_item_old_form(body: bytes, at: int, end: int) -> InventoryItem | None:
    """Read the OLD ``InventoryItem`` form, or refuse it.

    Class reference, then the legacy state-actor reference, then EXACTLY the
    declared end. Every width is a string prefix; nothing is fitted.

    Args:
        body: The decompressed body.
        at: The interior's first byte.
        end: The first byte past the interior.

    Returns:
        The item, or None when the form does not close exactly at ``end``.
    """
    strings: list[str] = []
    cursor = at
    for _ in range(4):
        read = _payload_text(body, cursor, end)
        if read is None:
            return None
        strings.append(read[0])
        cursor = read[1]
    if cursor != end:
        return None
    return InventoryItem(
        level_reference=strings[0],
        class_path=strings[1],
        state_undecoded=bool(strings[2] or strings[3]),
    )


def _read_item_state(body: bytes, at: int, end: int) -> bool:
    """Whether a NEW-form state block reads and closes exactly at ``end``.

    The state struct reference must name a ``/Script/`` struct, and the state
    size must take the reading EXACTLY to the tag's declared end, where the
    state's own tag list ends in the terminator - two prefixes agreeing. The
    state bytes are not otherwise interpreted.

    Args:
        body: The decompressed body.
        at: Just past the has-state flag.
        end: The first byte past the interior.

    Returns:
        Whether the block closes.
    """
    level = _payload_text(body, at, end)
    path = None if level is None else _payload_text(body, level[1], end)
    if path is None or not path[0].startswith(_SCRIPT_STRUCT_LEAD):
        return False
    size_at = path[1]
    if size_at + INT32_SIZE > end:
        return False
    (size,) = struct.unpack_from("<i", body, size_at)
    terminator = struct.pack("<i", len(_PAYLOAD_TERMINATOR) + 1) + _PAYLOAD_TERMINATOR.encode()
    terminator += b"\x00"
    state_at = size_at + INT32_SIZE
    return (
        size >= len(terminator)
        and state_at + size == end
        and body[end - len(terminator) : end] == terminator
    )


def _read_item_new_form(body: bytes, at: int, end: int) -> InventoryItem | None:
    """Read the NEW ``InventoryItem`` form, or refuse it.

    Class reference, an int32 has-state flag of 0 or 1, and when it is 1 a
    state block :func:`_read_item_state` bounds; then EXACTLY the declared end.

    Args:
        body: The decompressed body.
        at: The interior's first byte.
        end: The first byte past the interior.

    Returns:
        The item, or None when the form does not close exactly at ``end``.
    """
    level = _payload_text(body, at, end)
    path = None if level is None else _payload_text(body, level[1], end)
    if level is None or path is None or path[1] + INT32_SIZE > end:
        return None
    (has_state,) = struct.unpack_from("<i", body, path[1])
    after = path[1] + INT32_SIZE
    if has_state == 0 and after == end:
        state = False
    elif has_state == 1 and _read_item_state(body, after, end):
        state = True
    else:
        return None
    return InventoryItem(level_reference=level[0], class_path=path[0], state_undecoded=state)


def read_inventory_item(body: bytes, at: int, end: int) -> InventoryItem | InventoryItemRefusal:
    """Read one ``InventoryItem`` native interior under exactly one form - CS-400.

    BOTH FORMS ARE TRIED AND EXACTLY ONE MUST CLOSE (ADJ-G S0-b). The form is not
    chosen from any field outside the item's bytes. Both closing is refused as
    :data:`ITEM_FORM_AMBIGUOUS` rather than one being picked; neither closing as
    :data:`ITEM_FORM_UNCLOSED`. Nothing here raises, and no refusal carries a
    byte or a string of the item.

    Args:
        body: The decompressed body.
        at: The interior's first byte.
        end: The first byte past the interior, from the tag's declared size.

    Returns:
        The decoded item, or the refusal and its reason.
    """
    if at < 0 or at > end or end > len(body):
        return InventoryItemRefusal(reason=ITEM_FORM_UNCLOSED)
    readings = [
        reading
        for reading in (_read_item_old_form(body, at, end), _read_item_new_form(body, at, end))
        if reading is not None
    ]
    if len(readings) > 1:
        return InventoryItemRefusal(reason=ITEM_FORM_AMBIGUOUS)
    if not readings:
        return InventoryItemRefusal(reason=ITEM_FORM_UNCLOSED)
    return readings[0]


def _decode_interior_tag(
    body: bytes,
    header: tuple[str, int, int, int | None, tuple[str, ...], str | None, bool | None],
    name_at: int,
    end: int,
    depth: int,
    *,
    type_tree: bool = False,
) -> tuple[object | None, tuple[str, ...]]:
    """Decode one tag sitting inside a struct interior.

    TWO OUTCOMES, AND COLLAPSING THEM LOSES A DISTINCTION THE CALLER NEEDS. A
    VALUE means the tag decoded. A ``(None, words)`` pair means the tag's type
    is one this module does not read, or its bytes disagreed - the caller sorts
    those two by the element words it is handed back.

    IT ONCE HAD A THIRD, a bare None meaning the TAG ITSELF did not read, and
    that outcome is gone because the tag read moved OUT of this function.
    :func:`_walk_struct_tags` now reads the header through
    :func:`_read_tag_and_words` - the one site that owns the pair dispatch -
    and a header that does not read breaks the walk there, before this is
    called at all.

    THE HEADER ARRIVES WHOLE rather than as six positional arguments. That is
    the shape :func:`_read_tag_and_words` returns, and re-spreading it here
    would be a second place for a caller to start unpacking the wrong element
    in silence - the failure ``_walk_payload`` records CS-831 designing around.

    Args:
        body: The decompressed body.
        header: What :func:`_read_tag_and_words` returned for this tag.
        name_at: Where the tag's type word begins. Still needed because the
            LEGACY grammar keeps the struct word in the tag data rather than in
            the type name, so it is re-read from this offset.
        end: The first byte past the interior.
        depth: How deep the interior holding this tag sits.
        type_tree: Which grammar the header was read under - see
            :func:`uses_complete_type_name`.

    Returns:
        The value and the element words a container's tag carried.
    """
    type_word, value_at, size, in_tag_byte, element_words, named_struct, native = header
    if type_word == STRUCT_TYPE_WORD:
        # THE STRUCT WORD IS A TYPE-NAME PARAMETER AT THIS PAIR, so it comes
        # from the header read. Reaching for it with `_struct_word_of_tag`
        # would read a parameter count as a string length prefix - the hazard
        # :func:`_fold_struct_tag` already names at the top level, verbatim
        # applicable one level in.
        nested = named_struct if type_tree else _struct_word_of_tag(body, name_at, end)
        if nested is None:
            return (None, ())
        # THE ONE NATIVE WORD READ - CS-400. Only when the tag declared native
        # serialization or its grammar cannot state it (None); a tag saying
        # False stays on the tag-list path below, unmeasured, never guessed.
        if nested == INVENTORY_ITEM_STRUCT_WORD and native is not False:
            return (read_inventory_item(body, value_at, value_at + size), ())
        return (
            _decode_struct_interior(
                body, nested, value_at, value_at + size, depth + 1, type_tree=type_tree
            ),
            (),
        )
    return (
        # THE DEPTH GOES DOWN WITH THE VALUE - CS-1038. A container tag inside
        # an interior reads on the same grammar as one at top level, and its
        # struct ELEMENTS are now read too; without the depth each one would
        # restart the nesting count at zero and the ceiling would never be
        # reached on a body whose regions keep shrinking.
        _decode_value(
            body,
            type_word,
            value_at,
            size,
            in_tag_byte,
            element_words,
            depth=depth,
            type_tree=type_tree,
            native_serialize=native,
        ),
        element_words,
    )


def _walk_struct_tags(
    body: bytes, at: int, end: int, depth: int, *, type_tree: bool = False
) -> tuple[dict[str, object], int, int] | None:
    """Walk one struct interior's tag list, refusing anything that does not close.

    Args:
        body: The decompressed body.
        at: The interior's first byte.
        end: The first byte past the interior.
        depth: How deep this interior sits.
        type_tree: Read the complete-type-name tag grammar rather than the
            legacy one - see :func:`uses_complete_type_name`. DEFAULTED so that
            adding it could not change what any existing caller reads.

    Returns:
        The decoded values, the unmeasured count and the disagreement count, or
        None when the list does not close exactly at ``end``.
    """
    decoded: dict[str, object] = {}
    unmeasured = 0
    disagreed = 0
    cursor = at
    for _ in range(_MAX_ELEMENT_TAGS):
        name = _payload_text(body, cursor, end)
        if name is None:
            return None
        if name[0] == _PAYLOAD_TERMINATOR:
            # A terminator short of the declared end means this reading is not
            # the one the writer used. MEASURED INERT on the present corpus -
            # no site closes early, so loosening this to `<=` changes no count -
            # and kept for the corpus that does, with a test asserting the
            # inertness rather than a comment claiming the strength.
            return (decoded, unmeasured, disagreed) if name[1] == end else None
        # BOTH GRAMMARS' TAG HEADERS COME BACK THROUGH ONE CALL, the same one
        # :func:`_walk_payload` uses. There is one tag grammar dispatch in this
        # module and not two, which is what keeps an interior from drifting out
        # of step with the payload that holds it.
        header = _read_tag_and_words(body, name[1], end, type_tree=type_tree)
        if header is None:
            return None
        value, element_words = _decode_interior_tag(
            body, header, name[1], end, depth, type_tree=type_tree
        )
        if isinstance(value, InventoryItemRefusal):
            # PUBLISHED AND COUNTED BOTH - CS-400. The refusal stands in the
            # item's place so a consumer can tell it from an empty slot, and it
            # is still unmodelled content to this interior's own counter.
            decoded[name[0]] = value
            unmeasured += 1
        elif value is not None:
            decoded[name[0]] = value
        elif _refusal_is_unmodelled_content(header[0], element_words, native_serialize=header[6]):
            unmeasured += 1
        else:
            disagreed += 1
        cursor = header[1] + header[2]
    return None


def _fold_struct_tag(
    body: bytes,
    type_word: str,
    name_at: int,
    value_at: int,
    size: int,
    end: int,
    *,
    struct_word: str | None = None,
    type_tree: bool = False,
) -> tuple[int, tuple[StructValue, ...]]:
    """Whether one tag is a struct, and its interior when the interior reads.

    IT TAKES THE TYPE TEST RATHER THAN LEAVING IT TO THE CALLER, and that is
    deliberate rather than golf. :func:`_walk_payload` sits at its branch
    budget, and a walk that grows one more ``if`` per type word is the shape
    that gets refactored badly later. Handing it a pair it can add and extend
    unconditionally keeps the decision here, where the docstring for it is.

    Args:
        body: The decompressed body.
        type_word: The tag's type word.
        name_at: Where the tag's type word begins.
        value_at: The value's first byte.
        size: The value's declared extent.
        end: The first byte past the payload.
        struct_word: The struct word the CALLER already read, or None to read it
            out of the tag data. NOT A CONVENIENCE: on the pairs in
            :data:`COMPLETE_TYPE_NAME_PAIRS` the word is a parameter of the
            type NAME, so `_struct_word_of_tag` would read a parameter count as
            a string length prefix. It refuses almost always, and "almost" is
            the problem - a length that happened to read would publish a struct
            interior decoded against a word this save never wrote.
        type_tree: Read the complete-type-name grammar INSIDE the interior as
            well - see :func:`uses_complete_type_name`. SEPARATE FROM
            ``struct_word`` on purpose: the word says what this tag named, and
            this says what the bytes under it are written in. A caller that
            supplied one and not the other would decode the right word against
            the wrong grammar.

    Returns:
        1 when the tag is a struct and 0 otherwise, and a tuple holding the
        decoded interior or nothing at all.
    """
    if type_word != STRUCT_TYPE_WORD:
        return (0, ())
    if struct_word is None:
        struct_word = _struct_word_of_tag(body, name_at, end)
    interior = (
        None
        if struct_word is None
        else _decode_struct_interior(
            body, struct_word, value_at, value_at + size, type_tree=type_tree
        )
    )
    return (1, () if interior is None else (interior,))


def decode_struct_interior(
    body: bytes, struct_word: str, at: int, end: int, *, type_tree: bool = False
) -> StructValue | None:
    """Decode one ``StructProperty`` interior, or refuse it - CS-829.

    THE STATED SEAM for a caller holding a struct tag's own bounds, and the
    entry point ``tests/save/test_struct_interior.py`` grades the library
    population through. It reads the :data:`STRUCT_FORM_TAG_LIST` form and
    NOTHING ELSE: a struct written as native raw bytes comes back None, because
    its width is whatever the bytes are and no reading of it could have failed.

    Args:
        body: The decompressed body.
        struct_word: The struct type word the tag carried.
        at: The interior's first byte.
        end: The first byte past the interior, from the tag's declared size.
        type_tree: Read the complete-type-name tag grammar rather than the
            legacy one - see :func:`uses_complete_type_name`. DEFAULTED so that
            adding it could not change what any existing caller reads, and
            REQUIRED from a caller holding (14,60) bytes: this seam takes no
            record and no version pair, so the pair cannot be derived here.

    Returns:
        The decoded interior, or None when it is not a tag list closing exactly
        at ``end``.
    """
    return _decode_struct_interior(body, struct_word, at, end, type_tree=type_tree)


def _decode_value(  # noqa: PLR0913
    body: bytes,
    type_word: str,
    at: int,
    size: int,
    in_tag_byte: int | None,
    element_words: tuple[str, ...] = (),
    *,
    depth: int = 0,
    type_tree: bool = False,
    native_serialize: bool | None = None,
) -> object | None:
    """Decode one property value, or return None when its type is unmeasured.

    NONE MEANS "NOT MEASURED", NEVER "EMPTY". A caller distinguishing the two
    matters: an unmeasured type is flagged so the world model can say it does
    not model something, where a genuinely absent value would be silence.

    Every branch VERIFIES the declared size rather than trusting it. That is
    the shipped-redundancy oracle running in production, not only in the
    measurement: a string whose own prefix disagrees with the tag's declared
    size means the walk is not where it believes it is, and returning None
    there flags it instead of publishing a value read from the wrong offset.

    Args:
        body: The decompressed body.
        type_word: The tag's type word.
        at: The value's first byte.
        size: The value's declared extent.
        in_tag_byte: The byte carried in a BoolProperty's tag, or None.
        element_words: The element type words a CONTAINER's tag carried, empty
            for every other type. DEFAULTED so that adding it could not change
            any existing call, which is the same reason the counters on
            :class:`PropertyResult` are defaulted - a caller that predates
            CS-830 passes five arguments and still decodes exactly what it did.
            A container reached WITHOUT them cannot be decoded and comes back
            None, which is honest: the element words are in the tag, and a
            caller that did not read them has not supplied the value's grammar.
        depth: How far inside another struct the tag carrying this value sits.
            IT REACHES ONLY THE CONTAINER BRANCH, because a container is the
            only value that can hold a struct interior - CS-1038 - and carrying
            it is what bounds a struct nested THROUGH a container by
            :data:`MAX_STRUCT_DEPTH`. DEFAULTED at the top level, which is what
            every caller outside a struct interior means.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one inside this value - see :func:`uses_complete_type_name`. IT
            REACHES ONLY THE CONTAINER BRANCH, and that is not an omission:
            what a scalar VALUE looks like did not change at (14,60), only the
            tag framing did, and the only framing inside a value is a
            container's inner tag and its nested tag lists.
        native_serialize: Whether the tag declared a native-serialized value,
            or None when the grammar states nothing. IT REACHES ONLY THE
            CONTAINER BRANCH, for the same reason ``type_tree`` does: the bit
            is a statement about a value's FRAMING, and a container's element
            partition is the only framing this module derives rather than
            reads. DEFAULTED, so a caller that predates it decodes exactly what
            it did.

    Returns:
        The decoded value, or None when the type is unmeasured or the bytes
        disagree with the declaration.
    """
    if type_word in CONTAINER_TYPE_WORDS:
        return _decode_container(
            body,
            type_word,
            element_words,
            at,
            size,
            depth=depth,
            type_tree=type_tree,
            native_serialize=native_serialize,
        )
    if type_word == "BoolProperty":
        # The value rides in the TAG and the declared size is 0. Measured: the
        # byte takes only 0 and 1 across all 4077 instances in the library.
        return None if in_tag_byte is None or in_tag_byte > 1 else bool(in_tag_byte)
    fixed = _FIXED_WIDTH_VALUES.get(type_word)
    if fixed is not None:
        return _decode_fixed_width(body, at, size, fixed)
    # ByteProperty has TWO measured shapes, a raw byte and an enum member name;
    # both are handled below and 5359 instances consume their size exactly.
    return _decode_text_value(body, type_word, at, size)


@dataclass(frozen=True, repr=False)
class ItemListEntry:
    """One entry of a count-prefixed item list - CS-1068.

    ``repr`` is hand written and withholds the class path, for the reason given
    on :class:`ObjectReference`: the path is read out of the player's world and
    a repr is an echo path (non-negotiable 12).

    Attributes:
        item_class: The entry's class path, as the run spells it. WORLD
            CONTENT. Carried rather than interpreted - this module states no
            relation between it and any record's ``type_path``.
    """

    item_class: str

    def __repr__(self) -> str:
        """Render the length only, and withhold the path.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(item_class_len={len(self.item_class)})"


@dataclass(frozen=True, repr=False)
class ItemList:
    """A whole count-prefixed item list, and the width its prefixes describe.

    WHY ``width`` IS CARRIED RATHER THAN RECOMPUTED BY A CONSUMER. It is the
    one figure CS-1068's clause is about: it is summed from the count prefix,
    each entry's own length prefix and two shipped constants, and it is NEVER
    ``declared_end - at``. A consumer recomputing it from the payload's declared
    end would be doing the arithmetic partition that refuted CS-830, so the
    derived figure travels with the reading.

    Attributes:
        declared_count: The count the prefix carries. The number of entries the
            walk then read is ``len(entries)`` and the two agree by
            construction - a walk that could not read that many entries yields
            no list at all.
        entries: The entries, in the order the run writes them.
        width: How many bytes the list occupies, DERIVED from the prefixes.
    """

    declared_count: int
    entries: tuple[ItemListEntry, ...]
    width: int

    def __repr__(self) -> str:
        """Render counts and widths only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(declared_count={self.declared_count}, "
            f"entries={len(self.entries)}, width={self.width})"
        )


def _walk_item_entries(
    body: bytes, at: int, end: int, declared: int
) -> tuple[tuple[ItemListEntry, ...], int] | None:
    """Walk ``declared`` item-list entries, or refuse.

    SEPARATE FROM :func:`read_item_list` so that the reader's own refusals stay
    readable as a list rather than as a nest - the walk has four ways to refuse
    and the reader has three, and putting the seven in one frame made neither
    set legible.

    Args:
        body: The decompressed body.
        at: The first entry's first byte.
        end: The first byte past the payload.
        declared: How many entries the count prefix declared.

    Returns:
        The entries and the offset past the last one, or None.
    """
    entries: list[ItemListEntry] = []
    cursor = at
    for _ in range(declared):
        if cursor + ITEM_LIST_ENTRY_HEAD_BYTES > end:
            return None
        step = _payload_text(body, cursor + ITEM_LIST_ENTRY_HEAD_BYTES, end)
        # AN EMPTY PATH IS REFUSED, and not for tidiness: four zero bytes read
        # as an empty string would make any run of zeroes read as entries.
        if step is None or not step[0]:
            return None
        cursor = step[1] + ITEM_LIST_ENTRY_TAIL_BYTES
        if cursor > end:
            return None
        entries.append(ItemListEntry(item_class=step[0]))
    return (tuple(entries), cursor)


def read_item_list(body: bytes, at: int, end: int) -> ItemList | None:
    """Read a count-prefixed item list out of a payload's trailing remainder.

    **EVERY WIDTH HERE COMES OUT OF THE BYTES - CS-1068's WHOLE CLAUSE.** The
    count prefix says how many entries follow; each entry's own length prefix
    says how wide its class path is; the two fixed-width fields are shipped
    constants. ``end`` is a BOUND and a VALIDATION and is never a source of
    width: the walk refuses rather than stretching to reach it, which is what
    makes the reading falsifiable. A partition taking its width from ``end``
    would close on every payload and could not fail - the defect that refuted
    CS-830 after it had merged - and
    ``tests/save/test_item_list.py`` holds an arm that reddens on exactly that
    swap.

    NOTHING HERE RAISES. A corrupt count, a length prefix reaching past the
    payload and a walk that does not land on ``end`` are all REPORTED as no
    list, per non-negotiable 7.

    THE CLASS THE RUN BELONGS TO IS NOT AN INPUT, and cannot be: an empty list
    is four zero bytes and so is an unrelated class's whole remainder, so the
    bytes alone never say whether a run IS a list. :func:`derive_item_list_classes`
    is what answers that, and it answers it from the corpus.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The list, or None when the run is not one.
    """
    if at < 0 or end > len(body) or at + INT32_SIZE > end:
        return None
    (declared,) = struct.unpack_from("<i", body, at)
    if declared < 0 or declared > MAX_ITEM_LIST_ENTRIES:
        return None
    walked = _walk_item_entries(body, at + INT32_SIZE, end, declared)
    if walked is None or walked[1] != end:
        return None
    return ItemList(declared_count=declared, entries=walked[0], width=walked[1] - at)


@dataclass(frozen=True)
class RunReference:
    """One object reference read out of a payload's trailing remainder.

    THE SAME TWO STRINGS :class:`ObjectReference` CARRIES, and deliberately a
    separate type rather than that one. That class is keyed by the PROPERTY that
    held the reference; a reference in the trailing run belongs to no property,
    so reusing it would have forced an invented property name into the model.

    THE ``repr`` IS HAND-WRITTEN AND WITHHOLDS BOTH STRINGS. An object path read
    out of a save is game content (non-negotiable 2) and an exception rendering
    one is an echo path (non-negotiable 12), so the rendering reports widths.

    Attributes:
        level_reference: The level the reference names, carried rather than
            interpreted.
        object_path: The object the reference names.
    """

    level_reference: str
    object_path: str

    def __repr__(self) -> str:
        """Render widths only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(level_reference={len(self.level_reference)} chars, "
            f"object_path={len(self.object_path)} chars)"
        )


@dataclass(frozen=True)
class ReferencePair:
    """The two object references a payload's trailing remainder can carry.

    Attributes:
        references: The references, in the order the run writes them.
        tail_bytes: How wide a tail followed them - one of
            :data:`REFERENCE_PAIR_TAIL_WIDTHS`, and never a leftover.
        width: How many bytes the pair occupies, DERIVED from the prefixes plus
            that tail.
    """

    references: tuple[RunReference, ...]
    tail_bytes: int
    width: int

    def __repr__(self) -> str:
        """Render counts and widths only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(references={len(self.references)}, "
            f"tail_bytes={self.tail_bytes}, width={self.width})"
        )


def _walk_one_run_reference(body: bytes, at: int, end: int) -> tuple[RunReference, int] | None:
    """Walk one reference's two length-prefixed strings, or refuse.

    AN EMPTY STRING IS REFUSED, and not for tidiness: four zero bytes read as an
    empty string would make any run of zeroes read as a reference, which is the
    same trap :func:`_walk_item_entries` refuses an empty path for.

    Args:
        body: The decompressed body.
        at: The reference's first byte.
        end: The first byte past the payload.

    Returns:
        The reference and the offset past it, or None.
    """
    level = _payload_text(body, at, end)
    if level is None or not level[0]:
        return None
    path = _payload_text(body, level[1], end)
    if path is None or not path[0]:
        return None
    return (RunReference(level_reference=level[0], object_path=path[0]), path[1])


def _walk_run_references(
    body: bytes, at: int, end: int
) -> tuple[tuple[RunReference, ...], int] | None:
    """Walk the pair's four length-prefixed strings, or refuse.

    AN EMPTY STRING IS REFUSED, and not for tidiness: four zero bytes read as an
    empty string would make any run of zeroes read as a reference pair, which is
    the same trap :func:`_walk_item_entries` refuses an empty path for.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The references and the offset past the last one, or None.
    """
    texts: list[str] = []
    cursor = at
    for _ in range(REFERENCE_PAIR_STRINGS):
        step = _payload_text(body, cursor, end)
        if step is None or not step[0]:
            return None
        texts.append(step[0])
        cursor = step[1]
    pairs = tuple(
        RunReference(level_reference=texts[index], object_path=texts[index + 1])
        for index in range(0, REFERENCE_PAIR_STRINGS, 2)
    )
    return (pairs, cursor)


def read_reference_pair(body: bytes, at: int, end: int, *, tail_bytes: int) -> ReferencePair | None:
    """Read two object references out of a payload's trailing remainder - CS-828.

    **EVERY WIDTH HERE COMES OUT OF THE BYTES OR OUT OF A SHIPPED CONSTANT.**
    Each string's own length prefix says how wide it is, and ``tail_bytes`` is
    one of :data:`REFERENCE_PAIR_TAIL_WIDTHS` rather than whatever was left
    over. ``end`` is a BOUND and a VALIDATION and is never a source of width:
    the walk refuses rather than stretching to reach it, which is what makes
    the reading falsifiable. A partition taking its width from ``end`` would
    close on every payload and could not fail - the defect that refuted CS-830
    after it had merged - and ``tests/save/test_reference_pair.py`` holds an arm
    that reddens on exactly that swap.

    NOTHING HERE RAISES. A length prefix reaching past the payload, an empty
    string where the corpus writes a path, and a walk that does not land on
    ``end`` are all REPORTED as no pair, per non-negotiable 7.

    THE FORM IS NOT AN INPUT THE BYTES SUPPLY. Whether a body's carrying class
    writes the tail is a property of the schema rather than of the run, and
    :func:`derive_reference_pair_classes` is what answers it - from the body.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.
        tail_bytes: The tail width to require after the references.

    Returns:
        The pair, or None when the run is not one at that width.
    """
    if at < 0 or end > len(body) or tail_bytes not in REFERENCE_PAIR_TAIL_WIDTHS:
        return None
    walked = _walk_run_references(body, at, end)
    if walked is None or walked[1] + tail_bytes != end:
        return None
    return ReferencePair(references=walked[0], tail_bytes=tail_bytes, width=end - at)


@dataclass(frozen=True)
class ReferenceList:
    """A count-prefixed list of object references a trailing remainder carries.

    Attributes:
        references: The references, in the order the run writes them.
        entry_prefix_bytes: How wide a scalar preceded each one - one of
            :data:`REFERENCE_LIST_ENTRY_PREFIX_WIDTHS`, and never a leftover.
        width: How many bytes the list occupies, DERIVED from the leading
            count, that prefix width and each string's own length prefix.
    """

    references: tuple[RunReference, ...]
    entry_prefix_bytes: int
    width: int

    def __repr__(self) -> str:
        """Render counts and widths only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(references={len(self.references)}, "
            f"entry_prefix_bytes={self.entry_prefix_bytes}, width={self.width})"
        )


def _walk_run_reference_entries(
    body: bytes, at: int, end: int, *, count: int, prefix: int
) -> tuple[tuple[RunReference, ...], int] | None:
    """Walk ``count`` entries of a reference list, or refuse.

    Args:
        body: The decompressed body.
        at: The first entry's first byte.
        end: The first byte past the payload.
        count: How many entries the list's own prefix said there are.
        prefix: How wide a scalar precedes each reference.

    Returns:
        The references and the offset past the last one, or None.
    """
    references: list[RunReference] = []
    cursor = at
    for _ in range(count):
        cursor += prefix
        if cursor > end:
            return None
        walked = _walk_one_run_reference(body, cursor, end)
        if walked is None:
            return None
        references.append(walked[0])
        cursor = walked[1]
    return (tuple(references), cursor)


def read_reference_list(
    body: bytes, at: int, end: int, *, entry_prefix_bytes: int
) -> ReferenceList | None:
    """Read a count-prefixed object-reference list out of a remainder - CS-828.

    **EVERY WIDTH HERE COMES OUT OF THE BYTES OR OUT OF A SHIPPED CONSTANT.**
    The leading int32 says how many entries follow, each string's own length
    prefix says how wide it is, and ``entry_prefix_bytes`` is one of
    :data:`REFERENCE_LIST_ENTRY_PREFIX_WIDTHS` rather than whatever was left
    over. ``end`` is a BOUND and a VALIDATION and is never a source of width:
    the walk refuses rather than stretching to reach it, which is what makes
    the reading falsifiable. A partition taking its width from ``end`` would
    close on every payload and could not fail - the defect that refuted CS-830
    after it had merged - and ``tests/save/test_reference_list.py`` holds an arm
    that reddens on exactly that swap.

    **A COUNT OF ZERO IS REFUSED, AND THAT IS THE COLLISION BEING DECLINED
    RATHER THAN RESOLVED.** Four zero bytes are an empty count-prefixed list
    AND an empty string AND the zero-valued residual
    :func:`read_zero_remainder` reads. Nothing in the run tells those apart -
    CS-1068's root cause seen from a third side - so this reader claims none of
    them and requires at least one entry it can walk.

    NOTHING HERE RAISES. A count claiming more entries than the payload holds, a
    length prefix reaching past it, an empty string where the corpus writes a
    path, and a walk that does not land on ``end`` are all REPORTED as no list,
    per non-negotiable 7.

    THE FORM IS NOT AN INPUT THE BYTES SUPPLY. Whether a body's carrying class
    writes the per-entry scalar is a property of the schema rather than of the
    run, and :func:`derive_reference_list_classes` is what answers it - from the
    body.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.
        entry_prefix_bytes: The scalar width to require ahead of each reference.

    Returns:
        The list, or None when the run is not one in that form.
    """
    if at < 0 or end > len(body) or entry_prefix_bytes not in REFERENCE_LIST_ENTRY_PREFIX_WIDTHS:
        return None
    if end - at < REFERENCE_LIST_COUNT_BYTES:
        return None
    count = struct.unpack_from("<i", body, at)[0]
    entry_floor = entry_prefix_bytes + INT32_SIZE * 2
    if count <= 0 or count > (end - at - REFERENCE_LIST_COUNT_BYTES) // entry_floor:
        return None
    walked = _walk_run_reference_entries(
        body, at + REFERENCE_LIST_COUNT_BYTES, end, count=count, prefix=entry_prefix_bytes
    )
    if walked is None or walked[1] != end:
        return None
    return ReferenceList(
        references=walked[0],
        entry_prefix_bytes=entry_prefix_bytes,
        width=end - at,
    )


@dataclass(frozen=True, repr=False)
class ZeroRemainder:
    """A payload's trailing remainder read as one zero-valued int32 - CS-828.

    **IT SHIPS A HAND-WRITTEN ``__repr__`` THOUGH BOTH ITS FIELDS ARE INTEGERS,
    AND THAT IS THE CONTRACT RATHER THAN CEREMONY.** The repr guard in
    ``tests/repr_rendering_guard.py`` treats a save-layer field as disclosing
    unless every type it names is a scalar or a class that REDACTS ITSELF, and
    a class redacts itself by shipping one of these. Without it,
    :class:`TrailingRun` - which keeps its generated repr - enters the graded
    population the moment it holds a field of this type.
    :class:`ItemList` and :class:`ReferencePair` are here for the same reason.

    Attributes:
        value: The int32 READ at the remainder's first byte. Equal to
            :data:`ZERO_REMAINDER_VALUE` on every reading this shape admits,
            and carried rather than dropped so a consumer reads a value
            rather than a promise.
        width: How many bytes the reading consumed. A SHIPPED CONSTANT and
            never the observed remainder - see :func:`read_zero_remainder`.
    """

    value: int
    width: int

    def __repr__(self) -> str:
        """Render the value and the width, which is everything it holds.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(value={self.value}, width={self.width})"


def read_zero_remainder(body: bytes, at: int, end: int) -> ZeroRemainder | None:
    """Read a payload's trailing remainder as one zero-valued int32 - CS-828.

    **THE WIDTH IS A SHIPPED CONSTANT AND THE VALUE COMES OUT OF THE BYTES.**
    ``end`` is a BOUND and a VALIDATION and is never a source of width: the
    reading refuses rather than stretching to reach it, which is what makes it
    falsifiable. A partition taking its width from ``end`` would close on every
    payload and could not fail - the defect that refuted CS-830 after it had
    merged - and ``tests/save/test_zero_remainder.py`` holds an arm that
    reddens on exactly that swap.

    **AND A NON-ZERO VALUE IS REFUSED, WHICH IS THE SECOND HALF OF THE SAME
    PROPERTY.** A reader consuming four bytes whatever they said would succeed
    on every four-byte remainder in existence. The claim is that the region is
    an EMPTY structure, so bytes that say otherwise are a different shape.

    NOTHING HERE RAISES. A region of the wrong width, one reaching past the
    buffer and one carrying a different value are all REPORTED as no reading,
    per non-negotiable 7.

    THE CLASS THE RUN BELONGS TO IS NOT AN INPUT, and cannot be: four zero
    bytes are also an empty item list and also an unrelated class's whole
    remainder, so the bytes alone never say whether a run IS this shape.
    :func:`derive_zero_remainder_classes` is what answers that, from the body.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The reading, or None when the remainder is not this shape.
    """
    if at < 0 or end > len(body) or end - at != ZERO_REMAINDER_BYTES:
        return None
    (value,) = struct.unpack_from("<i", body, at)
    if value != ZERO_REMAINDER_VALUE:
        return None
    return ZeroRemainder(value=value, width=ZERO_REMAINDER_BYTES)


@dataclass(frozen=True, repr=False)
class TransformListEntry:
    """One entry of a count-prefixed named-transform list - CS-828.

    ``repr`` is hand written and withholds the name, for the reason given on
    :class:`ItemListEntry`: the name is read out of the player's world and a
    repr is an echo path (non-negotiable 12).

    Attributes:
        name: The entry's name, as the run spells it. WORLD CONTENT. Carried
            rather than interpreted - this module states no relation between it
            and any record's ``instance_name``.
        scalars: The fixed-width scalars the entry writes after its name, in
            file order. **THEIR MEANING IS NOT CLAIMED HERE.** Their COUNT is
            :data:`TRANSFORM_LIST_SCALARS` and their width is the one the body
            derived; what each one denotes is a question this reading does not
            answer and does not need to.
        flag: The single byte the entry ends with, READ rather than stepped
            over. Measured at one value on every entry of this project's
            library, which is recorded and not relied on - a byte this reader
            skipped would be a byte it had partitioned by arithmetic.
    """

    name: str
    scalars: tuple[float, ...]
    flag: int

    def __repr__(self) -> str:
        """Render the lengths only, and withhold the name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(name_len={len(self.name)}, "
            f"scalars={len(self.scalars)}, flag={self.flag})"
        )


@dataclass(frozen=True, repr=False)
class TransformList:
    """A whole count-prefixed named-transform list, and its derived width.

    WHY ``width`` IS CARRIED RATHER THAN RECOMPUTED BY A CONSUMER, for the
    reason :class:`ItemList` carries one: it is summed from the count prefix,
    each entry's own length prefix and three shipped constants, and it is NEVER
    ``declared_end - at``. A consumer recomputing it from the payload's declared
    end would be doing the arithmetic partition that refuted CS-830.

    Attributes:
        declared_count: The count the prefix carries. The number of entries the
            walk then read is ``len(entries)`` and the two agree by
            construction - a walk that could not read that many yields no list.
        entries: The entries, in the order the run writes them.
        scalar_bytes: How wide each scalar was - one of
            :data:`TRANSFORM_LIST_SCALAR_WIDTHS`, and never a leftover. It
            travels with the reading because it is a property of the BODY
            rather than of the format, and a consumer that could not tell which
            width it got would have to guess.
        width: How many bytes the list occupies, DERIVED from the prefixes.
    """

    declared_count: int
    entries: tuple[TransformListEntry, ...]
    scalar_bytes: int
    width: int

    def __repr__(self) -> str:
        """Render counts and widths only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(declared_count={self.declared_count}, "
            f"entries={len(self.entries)}, scalar_bytes={self.scalar_bytes}, "
            f"width={self.width})"
        )


def _walk_transform_entries(
    body: bytes, at: int, end: int, *, count: int, scalar_width: int
) -> tuple[tuple[TransformListEntry, ...], int] | None:
    """Walk ``count`` named-transform entries, or refuse.

    SEPARATE FROM :func:`read_transform_list` for the reason
    :func:`_walk_item_entries` is separate from its reader - the walk's four
    refusals and the reader's four read as a list rather than as a nest.

    AN EMPTY NAME IS REFUSED, and not for tidiness: four zero bytes read as an
    empty string would make any run of zeroes read as an entry, which is the
    same trap :func:`_walk_one_run_reference` refuses an empty string for.

    Args:
        body: The decompressed body.
        at: The first entry's first byte.
        end: The first byte past the payload.
        count: How many entries the list's own prefix said there are.
        scalar_width: How wide each scalar is.

    Returns:
        The entries and the offset past the last one, or None.
    """
    block = TRANSFORM_LIST_SCALARS * scalar_width
    code = "<f" if scalar_width == TRANSFORM_LIST_FLOAT_SCALAR_BYTES else "<d"
    entries: list[TransformListEntry] = []
    cursor = at
    for _ in range(count):
        named = _payload_text(body, cursor, end)
        if named is None or not named[0]:
            return None
        after = named[1] + block + TRANSFORM_LIST_ENTRY_FLAG_BYTES
        if after > end:
            return None
        scalars = tuple(
            struct.unpack_from(code, body, named[1] + index * scalar_width)[0]
            for index in range(TRANSFORM_LIST_SCALARS)
        )
        entries.append(
            TransformListEntry(
                name=named[0], scalars=scalars, flag=body[after - TRANSFORM_LIST_ENTRY_FLAG_BYTES]
            )
        )
        cursor = after
    return (tuple(entries), cursor)


def read_transform_list(
    body: bytes, at: int, end: int, *, scalar_width: int
) -> TransformList | None:
    """Read a count-prefixed named-transform list out of a remainder - CS-828.

    **EVERY WIDTH HERE COMES OUT OF THE BYTES OR OUT OF A SHIPPED CONSTANT.**
    The leading int32 says how many entries follow, each name's own length
    prefix says how wide it is, the scalar block is
    :data:`TRANSFORM_LIST_SCALARS` scalars of ``scalar_width`` - one of
    :data:`TRANSFORM_LIST_SCALAR_WIDTHS` and never whatever was left over - and
    the flag is :data:`TRANSFORM_LIST_ENTRY_FLAG_BYTES` wide. ``end`` is a BOUND
    and a VALIDATION and is never a source of width: the walk refuses rather
    than stretching to reach it, which is what makes the reading falsifiable. A
    partition taking its width from ``end`` would close on every payload and
    could not fail - the defect that refuted CS-830 after it had merged - and
    ``tests/save/test_transform_list.py`` holds an arm that reddens on exactly
    that swap.

    **A COUNT OF ZERO IS REFUSED, AND THAT IS A FOURTH SIDE OF THE CS-1068
    COLLISION.** Four zero bytes are an empty count-prefixed item list AND an
    empty string AND the zero-valued residual :func:`read_zero_remainder` reads
    AND an empty list of this shape. Nothing in the run tells those apart, so
    this reader claims none of them and requires at least one entry it can walk.

    **THE SCALARS' MEANING IS NOT CLAIMED AND DOES NOT NEED TO BE.** What CS-828
    asks for is the run's CONTENTS at a derived landing point. Their count and
    width are what the walk consumes; naming them would be a second claim this
    reading does not carry, and a wrong name is worse than none.

    NOTHING HERE RAISES. A count claiming more entries than the payload holds, a
    length prefix reaching past it, an empty name, a scalar width outside the
    allowed set and a walk that does not land on ``end`` are all REPORTED as no
    list, per non-negotiable 7.

    THE WIDTH IS NOT AN INPUT THE BYTES SUPPLY. Which of the two scalar widths a
    body's carrying class writes is a property of that layout rather than of the
    run, and :func:`derive_transform_list_classes` is what answers it - from the
    body.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.
        scalar_width: The scalar width to walk each entry's block at.

    Returns:
        The list, or None when the run is not one in that form.
    """
    if at < 0 or end > len(body) or scalar_width not in TRANSFORM_LIST_SCALAR_WIDTHS:
        return None
    if end - at < TRANSFORM_LIST_COUNT_BYTES:
        return None
    count = struct.unpack_from("<i", body, at)[0]
    entry_floor = (
        INT32_SIZE + TRANSFORM_LIST_SCALARS * scalar_width + TRANSFORM_LIST_ENTRY_FLAG_BYTES
    )
    if count <= 0 or count > (end - at - TRANSFORM_LIST_COUNT_BYTES) // entry_floor:
        return None
    walked = _walk_transform_entries(
        body, at + TRANSFORM_LIST_COUNT_BYTES, end, count=count, scalar_width=scalar_width
    )
    if walked is None or walked[1] != end:
        return None
    # THE WIDTH IS THE WALK'S OWN CURSOR AND NOT ``end - at``, THOUGH THE
    # LANDING CHECK ABOVE HAS JUST MADE THE TWO EQUAL. The sibling readers spell
    # it the second way and are correct for the same reason; spelling it this
    # way means the figure stays derived if a later edit ever loosens that
    # check, rather than silently becoming the observation CS-828 forbids.
    return TransformList(
        declared_count=count,
        entries=walked[0],
        scalar_bytes=scalar_width,
        width=walked[1] - at,
    )


@dataclass(frozen=True, repr=False)
class BuildableInstance:
    """One instance inside a buildable group - CS-828.

    ``repr`` is hand written and withholds every decoded string, for the reason
    given on :class:`ItemListEntry`: each one is read out of the player's world
    and a repr is an echo path (non-negotiable 12).

    Attributes:
        swatch: The first length-prefixed reference the instance writes, as the
            run spells it. WORLD CONTENT, carried rather than interpreted.
        recipe: The second length-prefixed reference, on the same terms.
        reference_level: The object reference's level string. Empty on every
            instance that writes no reference, which is most of them.
        reference_path: The object reference's path string, on the same terms.
        extra_type: The type name of the further declared structure the
            instance carries, or None when its flag is unset. **WHAT THAT
            STRUCTURE CONTAINS IS NOT CLAIMED HERE** - only its own declared
            size is read, and that is what the walk steps by.
        extra_bytes: How many bytes that structure DECLARED, or None. The
            figure comes out of the bytes; it is never ``end`` minus anything.
        flag: The int32 that says whether the block follows, READ rather than
            stepped over.
    """

    swatch: str
    recipe: str
    reference_level: str
    reference_path: str
    extra_type: str | None
    extra_bytes: int | None
    flag: int

    def __repr__(self) -> str:
        """Render lengths and counts only, and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(swatch_len={len(self.swatch)}, "
            f"recipe_len={len(self.recipe)}, "
            f"reference_len={len(self.reference_path)}, "
            f"extra_bytes={self.extra_bytes}, flag={self.flag})"
        )


@dataclass(frozen=True, repr=False)
class BuildableGroup:
    """One class-keyed group of instances inside the list - CS-828.

    Attributes:
        class_path: The length-prefixed path the group is keyed by. WORLD
            CONTENT, withheld by ``repr``.
        declared_count: The instance count the group's own prefix carries. The
            number the walk then read is ``len(instances)`` and the two agree by
            construction - a walk that could not read that many yields no list.
        instances: The instances, in the order the run writes them.
        flag: The int32 the group opens with, READ rather than stepped over.
    """

    class_path: str
    declared_count: int
    instances: tuple[BuildableInstance, ...]
    flag: int

    def __repr__(self) -> str:
        """Render counts only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(class_path_len={len(self.class_path)}, "
            f"declared_count={self.declared_count}, "
            f"instances={len(self.instances)}, flag={self.flag})"
        )


@dataclass(frozen=True, repr=False)
class BuildableGroupList:
    """A whole buildable group list and the width its own prefixes describe.

    WHY ``width`` IS CARRIED RATHER THAN RECOMPUTED BY A CONSUMER, for the
    reason :class:`ItemList` carries one: it is summed from two counts, four
    length prefixes per instance, one declared size per carried block and three
    shipped constants, and it is NEVER ``declared_end - at``. A consumer
    recomputing it from the payload's declared end would be doing the arithmetic
    partition that refuted CS-830.

    Attributes:
        version: The int32 the list opens with, READ and reported. **WHAT IT
            DENOTES IS NOT CLAIMED** - that it is read rather than skipped is
            the whole of what this field asserts.
        declared_count: The group count the prefix carries.
        groups: The groups, in the order the run writes them.
        width: How many bytes the list occupies, DERIVED from the prefixes.
    """

    version: int
    declared_count: int
    groups: tuple[BuildableGroup, ...]
    width: int

    def __repr__(self) -> str:
        """Render counts and widths only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(version={self.version}, "
            f"declared_count={self.declared_count}, groups={len(self.groups)}, "
            f"width={self.width})"
        )


def _walk_one_buildable_instance(  # noqa: PLR0911 - one refusal per field read is the clearest surface
    body: bytes, at: int, end: int
) -> tuple[BuildableInstance, int] | None:
    """Walk one instance, or refuse.

    THE WIDTHS IT CONSUMES ARE TWO SHIPPED BLOCKS, FOUR LENGTH PREFIXES AND -
    only when the flag is set - one DECLARED SIZE. None of them is ``end`` minus
    anything, which is what keeps this off the CS-830 defect.

    Args:
        body: The decompressed body.
        at: The instance's first byte.
        end: The first byte past the payload.

    Returns:
        The instance and the offset past it, or None.
    """
    swatch = _payload_text(body, at + BUILDABLE_INSTANCE_HEAD_BYTES, end)
    if swatch is None:
        return None
    recipe = _payload_text(body, swatch[1] + BUILDABLE_INSTANCE_MID_BYTES, end)
    if recipe is None:
        return None
    level = _payload_text(body, recipe[1], end)
    if level is None:
        return None
    reference = _payload_text(body, level[1], end)
    if reference is None:
        return None
    cursor = reference[1]
    if cursor + BUILDABLE_INSTANCE_EXTRA_FLAG_BYTES > end:
        return None
    (flag,) = struct.unpack_from("<i", body, cursor)
    cursor += BUILDABLE_INSTANCE_EXTRA_FLAG_BYTES
    extra_type: str | None = None
    extra_bytes: int | None = None
    if flag:
        named = _payload_text(body, cursor + BUILDABLE_INSTANCE_EXTRA_PAD_BYTES, end)
        if named is None or not named[0]:
            return None
        cursor = named[1]
        if cursor + BUILDABLE_INSTANCE_EXTRA_SIZE_BYTES > end:
            return None
        (declared,) = struct.unpack_from("<i", body, cursor)
        cursor += BUILDABLE_INSTANCE_EXTRA_SIZE_BYTES
        if declared < 0 or cursor + declared > end:
            return None
        cursor += declared
        extra_type, extra_bytes = named[0], declared
    return (
        BuildableInstance(
            swatch=swatch[0],
            recipe=recipe[0],
            reference_level=level[0],
            reference_path=reference[0],
            extra_type=extra_type,
            extra_bytes=extra_bytes,
            flag=flag,
        ),
        cursor,
    )


def _walk_buildable_groups(
    body: bytes, at: int, end: int, *, count: int
) -> tuple[tuple[BuildableGroup, ...], int] | None:
    """Walk ``count`` groups, or refuse.

    SEPARATE FROM :func:`read_buildable_group_list` for the reason
    :func:`_walk_item_entries` is separate from its reader - the walk's refusals
    and the reader's read as a list rather than as a nest.

    AN EMPTY CLASS PATH IS REFUSED, and not for tidiness: four zero bytes read
    as an empty string would make any run of zeroes read as a group, which is
    the same trap :func:`_walk_one_run_reference` refuses an empty string for.

    Args:
        body: The decompressed body.
        at: The first group's first byte.
        end: The first byte past the payload.
        count: How many groups the list's own prefix said there are.

    Returns:
        The groups and the offset past the last one, or None.
    """
    groups: list[BuildableGroup] = []
    cursor = at
    for _ in range(count):
        if cursor + BUILDABLE_GROUP_FLAG_BYTES > end:
            return None
        (flag,) = struct.unpack_from("<i", body, cursor)
        named = _payload_text(body, cursor + BUILDABLE_GROUP_FLAG_BYTES, end)
        if named is None or not named[0]:
            return None
        cursor = named[1]
        if cursor + INT32_SIZE > end:
            return None
        (declared,) = struct.unpack_from("<i", body, cursor)
        cursor += INT32_SIZE
        if declared < 0 or declared > (end - cursor) // _MINIMUM_BUILDABLE_INSTANCE_BYTES:
            return None
        instances: list[BuildableInstance] = []
        for _ in range(declared):
            walked = _walk_one_buildable_instance(body, cursor, end)
            if walked is None:
                return None
            instances.append(walked[0])
            cursor = walked[1]
        groups.append(
            BuildableGroup(
                class_path=named[0],
                declared_count=declared,
                instances=tuple(instances),
                flag=flag,
            )
        )
    return (tuple(groups), cursor)


def read_buildable_group_list(body: bytes, at: int, end: int) -> BuildableGroupList | None:
    """Read a remainder as a version-prefixed list of class-keyed groups - CS-828.

    **EVERY WIDTH HERE COMES OUT OF THE BYTES OR OUT OF A SHIPPED CONSTANT.**
    The group count says how many groups follow, each group's class path carries
    its own length prefix and its own instance count, each instance carries four
    more length prefixes around two shipped fixed blocks, and a carried
    extra-data block declares its own size. ``end`` is a BOUND and a VALIDATION
    and is never a source of width: the walk refuses rather than stretching to
    reach it, which is what makes the reading falsifiable. A partition taking
    its width from ``end`` would close on every payload and could not fail - the
    defect that refuted CS-830 after it had merged - and
    ``tests/save/test_buildable_groups.py`` holds an arm that reddens on exactly
    that swap.

    **A COUNT OF ZERO IS READ HERE, WHICH THE FOUR SIBLING READERS REFUSE, AND
    THE GATE MOVED RATHER THAN DISAPPEARED.** Those readers refuse a zero count
    because four zero bytes are an empty list AND an empty string AND the
    zero-valued residual, and nothing in the run tells them apart. This shape
    opens with a VERSION word ahead of its count, so an empty list is eight
    bytes - but eight bytes are still eight bytes, and admitting them on the
    reader's own authority would claim any class whose remainder happened to be
    that wide. :func:`derive_buildable_group_classes` is what holds it: a class
    earns its place only by DEMONSTRATING a non-empty list in the very body
    being read.

    **WHAT THE EXTRA-DATA BLOCK CONTAINS IS NOT CLAIMED.** Its type name and its
    own declared size are read; its interior is stepped over by that size and is
    not partitioned. Naming what is inside would be a second claim this reading
    does not carry, and the landing check is what grades the step - a declared
    size that does not put the walk on the next instance makes the whole list
    refuse rather than stretch.

    NOTHING HERE RAISES. A count claiming more groups than the payload holds, a
    length prefix reaching past it, an empty class path, a negative declared
    size and a walk that does not land on ``end`` are all REPORTED as no list,
    per non-negotiable 7.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The list, or None when the remainder is not one in that form.
    """
    head = BUILDABLE_GROUP_LIST_VERSION_BYTES + BUILDABLE_GROUP_LIST_COUNT_BYTES
    if at < 0 or end > len(body) or end - at < head:
        return None
    version, count = struct.unpack_from("<ii", body, at)
    if count < 0 or count > (end - at - head) // _MINIMUM_BUILDABLE_GROUP_BYTES:
        return None
    walked = _walk_buildable_groups(body, at + head, end, count=count)
    if walked is None or walked[1] != end:
        return None
    # THE WIDTH IS THE WALK'S OWN CURSOR AND NOT ``end - at``, for the reason
    # :func:`read_transform_list` spells it that way.
    return BuildableGroupList(
        version=version,
        declared_count=count,
        groups=walked[0],
        width=walked[1] - at,
    )


@dataclass(frozen=True)
class TrailingRun:
    """The run between a payload's property terminator and its declared end.

    THE DEFAULT ``repr`` IS KEPT, and that is a decision rather than an
    omission. :class:`ObjectRecord` and :class:`PropertyResult` hand-write one
    to withhold the strings they carry; every field here is an integer read out
    of the framing, there is no string to withhold, and a hand-written repr
    that rendered the same three integers would be ceremony claiming a control.

    WHAT ``unread`` IS FOR. It is the width of the region CS-828 leaves open,
    carried as a number on every result so a consumer reads the remainder as an
    open figure rather than an absent one. A reading that grows moves it down;
    a reading that silently dropped a region would move it down too, which is
    why ``tests/save/test_trailing_run.py`` grades the partition against the
    denominator rather than the remainder.

    Attributes:
        width: How many bytes the whole run occupies. OBSERVED as the declared
            end less the terminator's end - the one figure CS-828 names as the
            thing not to stop at.
        lead: The int32 the run OPENS with, READ out of the bytes, or None when
            the run is too short to hold the field. Absent on no payload of any
            real save measured so far, and reported rather than assumed.
        unread: How many bytes sit past the lead field that nothing reads. Zero
            on the population whose run IS the field and nothing else, and zero
            on a derived carrier whose remainder :attr:`items` read - CS-1068.
        items: The count-prefixed item list the remainder carried, or None. It
            is present only when the record's class was named by
            :func:`derive_item_list_classes` AND the bytes then read as one:
            naming a class does not zero its remainder, which is what keeps the
            vocabulary a gate on the reading rather than the reading itself.
        references: The two object references the remainder carried, or None -
            CS-828. Present under the same rule :attr:`items` is present under:
            the record's class was named by
            :func:`derive_reference_pair_classes` AND the bytes then read as a
            pair at the width that derivation derived for the body.
        reference_list: The count-prefixed list of object references the
            remainder carried, or None - CS-828. Present under the same rule
            :attr:`items` is present under: the record's class was named by
            :func:`derive_reference_list_classes` AND the bytes then read as a
            list in the form that derivation derived for the body.
        zero_remainder: The zero-valued int32 the remainder carried, or None
            - CS-828. Present under the same rule the two above are: the
            record's class was named by
            :func:`derive_zero_remainder_classes` AND the bytes then read as
            the shape. IT IS NOT A CLAIM THAT THE REGION IS AN EMPTY ITEM
            LIST, which is byte-identical and which no reading of the run can
            tell apart - CS-1119 owns that question.
        transform_list: The count-prefixed list of NAMED TRANSFORMS the
            remainder carried, or None - CS-828. Present under the same rule
            the three above are: the record's class was named by
            :func:`derive_transform_list_classes` AND the bytes then read as a
            list at the scalar width that derivation derived for the body.
        buildable_groups: The version-prefixed list of class-keyed instance
            groups the remainder carried, or None - CS-828. Present under the
            same rule the four above are: the record's class was named by
            :func:`derive_buildable_group_classes` AND the bytes then read as
            the shape. It is the WIDEST region of the run this module reads and
            not the most populous one - one payload of this project's library
            carries over a megabyte of it.
    """

    width: int
    lead: int | None
    unread: int
    items: ItemList | None = None
    references: ReferencePair | None = None
    reference_list: ReferenceList | None = None
    zero_remainder: ZeroRemainder | None = None
    transform_list: TransformList | None = None
    buildable_groups: BuildableGroupList | None = None


def read_trailing_run(body: bytes, terminator_end: int, end: int) -> TrailingRun | None:
    """Read the run that follows a payload's property terminator.

    WHAT THIS ADVANCES OVER THE RECORD IT REPLACES - CS-828. The run was
    recorded as wholly opaque, with a 4-byte floor OBSERVED as
    ``end - terminator_end`` and no reading of its interior offered at all.
    This reads the field the run OPENS with, out of the bytes, on every payload
    that has one. It does NOT close the region: everything past that field is
    class-keyed extra data this module still does not read, and ``unread``
    carries its width so that stays visible.

    NOTHING HERE RAISES. A run too short for the field, a run reaching past the
    buffer and a terminator sitting past the declared end are all REPORTED -
    the first as a run with no lead, the other two as no run at all. That is
    non-negotiable 7 rather than leniency: a payload whose framing disagrees is
    flagged and skipped, and a reader that raised here would make a malformed
    save fatal for the whole walk.

    Args:
        body: The decompressed body.
        terminator_end: The first byte past the payload's terminator.
        end: The first byte past the payload.

    Returns:
        The run, or None when the run is not addressable inside ``body``.
    """
    width = end - terminator_end
    if width < 0 or terminator_end < 0 or end > len(body):
        return None
    if width < TRAILING_RUN_LEAD_BYTES:
        return TrailingRun(width=width, lead=None, unread=width)
    return TrailingRun(
        width=width,
        lead=struct.unpack_from("<i", body, terminator_end)[0],
        unread=width - TRAILING_RUN_LEAD_BYTES,
    )


def _decode_payload(
    body: bytes, at: int, end: int
) -> tuple[dict[str, object], int, int, bool] | None:
    """Walk one payload's property tags and decode every measured value.

    THE TWO REASONS A VALUE DOES NOT COME BACK ARE COUNTED SEPARATELY, and
    that separation is the point rather than a refinement. ``_decode_value``
    returns None for two conditions that mean opposite things:

    UNMEASURED TYPE - this project has never measured that type's value
    encoding. Expected, benign, and exactly what non-negotiable 7 says to flag
    and skip. It says nothing about whether the walk is correct.

    MEASURED TYPE, BYTES DISAGREED - the shipped-redundancy oracle running in
    production. The type IS measured, and the value's own length prefix did not
    account for the tag's declared size, which means the reader is not where it
    believes it is. Every value decoded after it in the same payload is suspect.

    Collapsing the two makes a desynchronised walk look like unmodelled
    content, which is "silently wrong" - the half of non-negotiable 7 that has
    no second chance. It is the same conflation CS-417 records one module over.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the payload.

    Returns:
        The decoded properties, how many tags carried an unmeasured type, how
        many carried a measured type whose bytes disagreed, and whether the
        walk reached its terminator. None when the walk broke, which is every
        payload of an unmeasured pair.
    """
    walked = _walk_payload(body, at, end)
    if walked is None:
        return None
    return (walked.properties, walked.unmeasured, walked.disagreed, walked.terminated)


@dataclass(frozen=True, repr=False)
class _PayloadWalk:
    """Everything one payload walk observed, references included.

    ``repr`` renders counts only: ``properties`` and ``references`` are both
    decoded world content, for the reason :class:`PropertyResult` gives.

    Attributes:
        properties: The decoded values, by name.
        unmeasured: Tags whose type has no measured value encoding.
        disagreed: Tags whose measured type disagreed with its declared size.
        terminated: Whether the walk reached its terminator.
        references: One entry per DECODED reference tag, in tag order.
        reference_tags: Every reference tag stepped over, decoded or not.
        undecoded_references: Reference tags that yielded no pair.
        struct_interiors: One entry per top-level struct tag whose interior
            READ, in tag order - CS-829. A tuple rather than a mapping for the
            reason ``references`` is one: two tags sharing a name may not
            collapse into one when the thing being counted is a population.
        struct_tags: Every top-level struct tag stepped over, decoded or not.
            THE DENOMINATOR THE DECODER CANNOT SHRINK, on the same terms as
            ``reference_tags``: counting only what decoded would let a form this
            module does not read leave the population instead of being reported.
        trailing_run: The run past the terminator - CS-828. Present only on a
            walk that TERMINATED, because a walk that broke never found the
            terminator the run is measured from, and inventing one from the
            declared end would report a region nobody located.
        undecoded_names: The name of every tag counted in ``unmeasured`` or
            ``disagreed`` - CS-1264. See ``PropertyResult.undecoded_names``.
    """

    properties: dict[str, object]
    unmeasured: int
    disagreed: int
    terminated: bool
    references: tuple[ObjectReference, ...]
    reference_tags: int
    undecoded_references: int
    struct_interiors: tuple[StructValue, ...] = ()
    struct_tags: int = 0
    trailing_run: TrailingRun | None = None
    undecoded_names: frozenset[str] = frozenset()

    def __repr__(self) -> str:
        """Render counts only, and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(properties={len(self.properties)}, "
            f"unmeasured={self.unmeasured}, disagreed={self.disagreed}, "
            f"terminated={self.terminated}, references={len(self.references)}, "
            f"reference_tags={self.reference_tags}, "
            f"undecoded_references={self.undecoded_references}, "
            f"struct_interiors={len(self.struct_interiors)}, "
            f"struct_tags={self.struct_tags}, "
            f"undecoded_names={len(self.undecoded_names)})"
        )


def _read_tag_and_words(
    body: bytes, name_at: int, end: int, *, type_tree: bool
) -> tuple[str, int, int, int | None, tuple[str, ...], str | None, bool | None] | None:
    """Read one tag header under either grammar and report what it named.

    THE SEVENTH ELEMENT IS ``None`` UNDER THE LEGACY GRAMMAR AND A BOOL UNDER
    THE OTHER, and the three-valued shape is the honest one. The legacy tag has
    no flags byte at all, so that grammar makes no statement about native
    serialization - and False would be a statement. A consumer reading None as
    False would be treating "the writer did not say" as "the writer said no",
    which is how a pair that never carried the field starts being refused or
    accepted on the strength of a field it does not have.

    WHY THE TWO GRAMMARS MEET HERE AND NOWHERE ELSE - CS-G05. They differ for
    exactly these seven locals and rejoin immediately: what a VALUE looks like did
    not change at (14,60), the tag FRAMING did. Two copies of the decode and the
    bookkeeping below would be two places for the reference and struct counters
    to drift apart, and the loop invariant :func:`_walk_payload` documents rests
    on there being one.

    IT IS A SEPARATE FUNCTION RATHER THAN A BRANCH IN THAT LOOP for the reason
    :func:`_fold_struct_tag` already gives: the loop sits at its branch budget,
    and a walk that grows one more ``if`` per grammar is the shape that gets
    refactored badly later.

    Args:
        body: The decompressed body.
        name_at: Just past the tag's name - where its type begins.
        end: The first byte past the payload.
        type_tree: Read the complete-type-name grammar rather than the legacy
            one. See :func:`uses_complete_type_name`.

    Returns:
        The type word, where the value starts, its declared size, the byte a
        BoolProperty carries, the element words a container's tag named, the
        struct word when this grammar states one, and whether the tag declared
        a native-serialized value - None when the grammar has no such field.
        None when the tag does not read at all.
    """
    if type_tree:
        tree_tag = _read_type_tree_tag_header(body, name_at, end)
        if tree_tag is None:
            return None
        type_word, value_start, size, in_tag_byte, params, native = tree_tag
        # THE WORDS CAME OUT OF THE HEADER READ rather than a second pass: they
        # are the type name's own parameters at this pair, and the legacy re-read
        # below would have to parse the nested name twice to arrive back at
        # them. A struct's word is the first of them.
        container = type_word in CONTAINER_TYPE_WORDS
        struct_word = params[0] if type_word == STRUCT_TYPE_WORD and params else None
        return (
            type_word,
            value_start,
            size,
            in_tag_byte,
            params if container else (),
            struct_word,
            native,
        )

    tag = _read_tag_header(body, name_at, end)
    if tag is None:
        return None
    type_word, value_start, size, in_tag_byte = tag
    # THE ELEMENT WORDS ARE READ HERE BECAUSE HERE IS WHERE THE OFFSET STILL
    # EXISTS - CS-830. They sit inside the tag, between the index field and the
    # guid flag, and `_read_tag_header` steps over them without handing them
    # back. Widening its return shape in place is how a caller starts unpacking
    # the wrong element in silence, so they are re-read from the name offset.
    element_words: tuple[str, ...] = ()
    if type_word in CONTAINER_TYPE_WORDS:
        read_words = _container_element_words(body, name_at, end, type_word)
        if read_words is None:
            return None
        element_words = read_words
    return (type_word, value_start, size, in_tag_byte, element_words, None, None)


def _walk_payload(
    body: bytes, at: int, end: int, *, type_tree: bool = False
) -> _PayloadWalk | None:
    """Walk one payload's tags, decoding values and collecting references.

    THE WALK ITSELF, which :func:`_decode_payload` narrows for the consumers
    that predate the reference collection. The narrowing exists so that adding
    CS-831's three counters could not change a shape those consumers unpack
    positionally - a return shape is an interface, and widening one in place is
    how a caller starts reading the wrong element in silence.

    THE REFERENCE COUNTERS ARE WRITTEN AT THREE SITES AND ARE NOT THEREBY
    INDEPENDENT, and a sentence here claimed that they were. ``reference_tags``
    counts the tag, ``references`` collects the decode and
    ``undecoded_references`` counts the refusal - but all three move inside one
    exhaustive if/else with no ``continue``, ``break`` or ``return`` between
    them, so ``reference_tags == undecoded_references + len(references)`` is a
    LOOP INVARIANT of this walk. THREE SITES IS NOT THREE DERIVATIONS, and the
    partition :func:`resolve_references` states against this total is therefore
    an identity that no miscount inside this loop can make false.

    WHAT A MISCOUNT HERE DOES MOVE is this total against a tag count taken by a
    walk this module does not own, which is the only form of the partition that
    can come out false and is where the grading lives - see
    ``tests/save/test_reference_resolution.py``.

    THE TYPE WORD IS READ HERE BECAUSE HERE IS WHERE IT EXISTS. By the time a
    value reaches a caller it is a ``tuple[str, str]`` that ``ObjectProperty``
    and ``SoftObjectProperty`` share, and the word that told them apart is
    gone - see :data:`REFERENCE_TYPE_WORD`.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the payload.
        type_tree: Read the complete-type-name tag grammar rather than the
            legacy one - see :func:`uses_complete_type_name`. DEFAULTED so that
            adding it could not change what any existing caller reads.

    Returns:
        What the walk observed, or None when it broke before its terminator.
    """
    decoded: dict[str, object] = {}
    references: list[ObjectReference] = []
    struct_interiors: list[StructValue] = []
    undecoded: set[str] = set()
    unmeasured = 0
    disagreed = 0
    reference_tags = 0
    undecoded_references = 0
    struct_tags = 0
    for _ in range(_MAX_TAGS_PER_PAYLOAD):
        name = _payload_text(body, at, end)
        if name is None:
            return None
        if name[0] == _PAYLOAD_TERMINATOR:
            # THE RUN IS READ HERE BECAUSE HERE IS WHERE THE TERMINATOR'S END
            # EXISTS - CS-828. Every other frame has the declared end and not
            # the terminator, so a reader placed anywhere else would have to
            # re-walk the payload to find the one boundary it needs, and two
            # walks over one payload is how a second reading drifts out of step
            # with the first.
            return _PayloadWalk(
                properties=decoded,
                unmeasured=unmeasured,
                disagreed=disagreed,
                terminated=True,
                references=tuple(references),
                reference_tags=reference_tags,
                undecoded_references=undecoded_references,
                struct_interiors=tuple(struct_interiors),
                struct_tags=struct_tags,
                trailing_run=read_trailing_run(body, name[1], end),
                undecoded_names=frozenset(undecoded),
            )
        # BOTH GRAMMARS' TAG HEADERS COME BACK THROUGH ONE CALL - CS-G05.
        # :func:`_read_tag_and_words` says why the divergence lives there and
        # not in this loop.
        header = _read_tag_and_words(body, name[1], end, type_tree=type_tree)
        if header is None:
            return None
        type_word, value_start, size, in_tag_byte, element_words, struct_word, native = header
        value = _decode_value(
            body,
            type_word,
            value_start,
            size,
            in_tag_byte,
            element_words,
            type_tree=type_tree,
            native_serialize=native,
        )
        # A SEPARATE POPULATION FROM ``properties``, AND THE SEPARATION IS THE
        # DESIGN - CS-829. The interior is REPORTED here and the struct word
        # stays OUT of MEASURED_VALUE_TYPES, because the corpus carries struct
        # words written in a form this module does not read. Promoting the type
        # on the strength of the form it DOES read would claim a top-level value
        # reading for all of them, which is the overclaim the item's own note
        # warns against - and it would move ``unmeasured`` for the native form,
        # reporting shipped game content as a decoder that lost its place.
        #
        # NO BRANCH IS ADDED TO THIS LOOP and :func:`_fold_struct_tag` says why.
        struct_step = _fold_struct_tag(
            body,
            type_word,
            name[1],
            value_start,
            size,
            end,
            struct_word=struct_word,
            type_tree=type_tree,
        )
        struct_tags += struct_step[0]
        struct_interiors.extend(struct_step[1])
        if type_word == REFERENCE_TYPE_WORD:
            # KEPT AS ONE BLOCK, and separate from the bookkeeping below it.
            # The two answer different questions - that one asks whether the
            # value came back at all, this one asks whether the reference
            # population gained a member - and interleaving them is how the
            # tag count and the decode count drift apart.
            reference_tags += 1
            reference = _as_reference(name[0], value)
            if reference is None:
                undecoded_references += 1
            else:
                references.append(reference)
        # A DROPPED VALUE IS NOT A DROPPED TAG - CS-1264. Both refusals keep
        # the tag's NAME, never its value, so a consumer asking whether a tag
        # was present gets an answer when the value did not decode.
        if value is not None:
            decoded[name[0]] = value
        elif _refusal_is_unmodelled_content(type_word, element_words, native_serialize=native):
            unmeasured += 1
            undecoded.add(name[0])
        else:
            disagreed += 1
            undecoded.add(name[0])
        at = value_start + size
    return None


def _as_reference(property_name: str, value: object) -> ObjectReference | None:
    """Narrow a decoded value to a reference, or refuse it.

    THE SHAPE IS CHECKED RATHER THAN ASSUMED. ``_decode_value`` is typed as
    returning ``object``, and its reference branch returns the pair only when
    the two strings consume the declared size exactly - so None arrives here
    routinely and means the bytes disagreed. A value of any other shape is
    content this module does not model, and refusing it is what keeps an
    unpack that would raise out of a decoder whose contract is to flag and
    skip (non-negotiable 7).

    Args:
        property_name: The tag's own name.
        value: Whatever :func:`_decode_value` returned for it.

    Returns:
        The reference, or None when the value is not the measured pair.
    """
    if not isinstance(value, tuple) or len(value) != _REFERENCE_PARTS:
        return None
    level_reference, object_path = value
    if not isinstance(level_reference, str) or not isinstance(object_path, str):
        return None
    return ObjectReference(
        property_name=property_name,
        level_reference=level_reference,
        object_path=object_path,
    )


# ---------------------------------------------------------------------------
# Property resolution
# ---------------------------------------------------------------------------


def _run_with_item_list(
    body: bytes,
    record: ObjectRecord,
    run: TrailingRun | None,
    item_list_classes: Collection[str],
) -> TrailingRun | None:
    """Read the run's remainder as an item list when the class carries one.

    THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF. A
    class named here whose bytes do not read comes back exactly as CS-828 left
    it, so a derivation that named everything would close nothing. That is what
    keeps `and nowhere else` a measurement rather than a definition.

    Args:
        body: The decompressed body.
        record: The record the run came from.
        run: The run the walk read, or None.
        item_list_classes: The class names derived as carriers.

    Returns:
        The run, with its remainder read when it read.
    """
    if run is None or run.lead is None or not run.unread:
        return run
    if class_name_of(record.type_path) not in item_list_classes:
        return run
    end = record.body_offset + record.body_length
    items = read_item_list(body, end - run.unread, end)
    if items is None:
        return run
    return TrailingRun(width=run.width, lead=run.lead, unread=run.unread - items.width, items=items)


def _run_with_reference_pair(
    body: bytes,
    record: ObjectRecord,
    run: TrailingRun | None,
    reference_pair_classes: Mapping[str, int],
) -> TrailingRun | None:
    """Read the run's remainder as an object-reference pair when its class carries one.

    THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF, exactly
    as in :func:`_run_with_item_list`. A class named here whose bytes do not read
    at the derived width comes back exactly as CS-828 left it, so a derivation
    that named everything would close nothing. That is what keeps `and nowhere
    else` a measurement rather than a definition.

    Args:
        body: The decompressed body.
        record: The record the run came from.
        run: The run the walk read, or None.
        reference_pair_classes: Each derived carrier class to its tail width.

    Returns:
        The run, with its remainder read when it read.
    """
    if run is None or run.lead is None or not run.unread:
        return run
    tail_bytes = reference_pair_classes.get(class_name_of(record.type_path))
    if tail_bytes is None:
        return run
    end = record.body_offset + record.body_length
    pair = read_reference_pair(body, end - run.unread, end, tail_bytes=tail_bytes)
    if pair is None:
        return run
    return TrailingRun(
        width=run.width,
        lead=run.lead,
        unread=run.unread - pair.width,
        items=run.items,
        references=pair,
    )


def _run_with_reference_list(
    body: bytes,
    record: ObjectRecord,
    run: TrailingRun | None,
    reference_list_classes: Mapping[str, int],
) -> TrailingRun | None:
    """Read the run's remainder as a count-prefixed reference list when its class carries one.

    THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF, exactly
    as in :func:`_run_with_item_list`. A class named here whose bytes do not read
    in the derived form comes back exactly as CS-828 left it, so a derivation
    that named everything would close nothing.

    Args:
        body: The decompressed body.
        record: The record the run came from.
        run: The run the walk read, or None.
        reference_list_classes: Each derived carrier class to its per-entry width.

    Returns:
        The run, with its remainder read when it read.
    """
    if run is None or run.lead is None or not run.unread:
        return run
    entry_prefix_bytes = reference_list_classes.get(class_name_of(record.type_path))
    if entry_prefix_bytes is None:
        return run
    end = record.body_offset + record.body_length
    read = read_reference_list(body, end - run.unread, end, entry_prefix_bytes=entry_prefix_bytes)
    if read is None:
        return run
    return TrailingRun(
        width=run.width,
        lead=run.lead,
        unread=run.unread - read.width,
        items=run.items,
        references=run.references,
        reference_list=read,
    )


def _run_with_transform_list(
    body: bytes,
    record: ObjectRecord,
    run: TrailingRun | None,
    transform_list_classes: Mapping[str, int],
) -> TrailingRun | None:
    """Read the run's remainder as a count-prefixed named-transform list when its class carries one.

    THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF, exactly
    as in :func:`_run_with_item_list`. A class named here whose bytes do not read
    in the derived form comes back exactly as CS-828 left it, so a derivation
    that named everything would close nothing.

    Args:
        body: The decompressed body.
        record: The record the run came from.
        run: The run the walk read, or None.
        transform_list_classes: Each derived carrier class to its scalar width.

    Returns:
        The run, with its remainder read when it read.
    """
    if run is None or run.lead is None or not run.unread:
        return run
    scalar_width = transform_list_classes.get(class_name_of(record.type_path))
    if scalar_width is None:
        return run
    end = record.body_offset + record.body_length
    read = read_transform_list(body, end - run.unread, end, scalar_width=scalar_width)
    if read is None:
        return run
    return TrailingRun(
        width=run.width,
        lead=run.lead,
        unread=run.unread - read.width,
        items=run.items,
        references=run.references,
        reference_list=run.reference_list,
        transform_list=read,
    )


def _run_with_buildable_groups(
    body: bytes,
    record: ObjectRecord,
    run: TrailingRun | None,
    buildable_group_classes: Collection[str],
) -> TrailingRun | None:
    """Read the run's remainder as a buildable group list when its class carries one.

    THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF,
    exactly as in :func:`_run_with_item_list`. A class named here whose bytes
    do not read in the derived form comes back exactly as CS-828 left it, so a
    derivation that named everything would close nothing.

    Args:
        body: The decompressed body.
        record: The record the run came from.
        run: The run the walk read, or None.
        buildable_group_classes: The class names derived as carriers.

    Returns:
        The run, with its remainder read when it read.
    """
    if run is None or run.lead is None or not run.unread:
        return run
    if class_name_of(record.type_path) not in buildable_group_classes:
        return run
    end = record.body_offset + record.body_length
    read = read_buildable_group_list(body, end - run.unread, end)
    if read is None:
        return run
    return TrailingRun(
        width=run.width,
        lead=run.lead,
        unread=run.unread - read.width,
        items=run.items,
        references=run.references,
        reference_list=run.reference_list,
        zero_remainder=run.zero_remainder,
        transform_list=run.transform_list,
        buildable_groups=read,
    )


def _run_with_zero_remainder(
    body: bytes,
    record: ObjectRecord,
    run: TrailingRun | None,
    zero_remainder_classes: Collection[str],
) -> TrailingRun | None:
    """Read the run's remainder as one zero-valued int32 when its class carries one.

    THE VOCABULARY IS A GATE ON THE READING AND NEVER THE READING ITSELF,
    exactly as in :func:`_run_with_item_list`. A class named here whose bytes
    do not read comes back exactly as CS-828 left it, so a derivation that
    named everything would close nothing.

    IT RUNS LAST OF THE SIX, and the order is load-bearing rather than
    arbitrary: a remainder an item list, a reference pair, a reference list, a
    transform list or a buildable group list already read has ``unread`` at zero
    and never reaches here, so no region is counted twice. The ordering is not
    what keeps this reading off those lists' subject either - a zero-valued
    residual reads a COUNT of zero, which :func:`read_reference_list` and
    :func:`read_transform_list` both refuse outright, and it is four bytes wide
    where :func:`read_buildable_group_list` needs at least eight.

    Args:
        body: The decompressed body.
        record: The record the run came from.
        run: The run the walk read, or None.
        zero_remainder_classes: The class names derived as carriers.

    Returns:
        The run, with its remainder read when it read.
    """
    if run is None or run.lead is None or not run.unread:
        return run
    if class_name_of(record.type_path) not in zero_remainder_classes:
        return run
    end = record.body_offset + record.body_length
    read = read_zero_remainder(body, end - run.unread, end)
    if read is None:
        return run
    return TrailingRun(
        width=run.width,
        lead=run.lead,
        unread=run.unread - read.width,
        items=run.items,
        references=run.references,
        reference_list=run.reference_list,
        transform_list=run.transform_list,
        buildable_groups=run.buildable_groups,
        zero_remainder=read,
    )


def derive_item_list_classes(
    body: bytes,
    records: Iterable[ObjectRecord],
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> frozenset[str]:
    """Pick the classes whose trailing remainder is a count-prefixed item list.

    **DERIVED FROM THE CORPUS, NEVER TRANSCRIBED - CS-1068's second clause.** A
    hand-maintained vocabulary of game content is the thing that rots, and
    CS-829's note forbids that shape by name. A class earns its place here by
    DEMONSTRATING the grammar inside the very body being read: one of its
    records must carry a NON-EMPTY list that walks exactly onto its declared
    end. A body that stops carrying one derives nothing and says so, rather
    than going quietly green.

    WHY DEMONSTRATION RATHER THAN A SUCCESSFUL PARSE. An EMPTY list is four zero
    bytes, and so is the whole remainder of several classes that carry no list
    at all - they are byte-identical, so a class admitted on a parse that
    succeeded would admit every one of them and the reading would fall to zero
    everywhere. A non-empty list cannot be produced by accident: its count
    prefix, its per-entry length prefixes and its fixed fields have to agree
    with each other AND land on the declared end.

    THIS IS THE SECOND WALK OVER THE BODY AND THAT IS INHERENT. The vocabulary
    is a property of the body as a whole and no per-record reader can hold it,
    which is exactly the sense in which the remainder is class-keyed.

    Args:
        body: The decompressed body.
        records: The records to derive from - a body's whole table.
        save_version: The save version the body was walked on, or None.
        header_version: The header version the body was walked on, or None.

    Returns:
        The carrier class names.
    """
    derived: set[str] = set()
    for record in records:
        if not record.body_length or class_name_of(record.type_path) in derived:
            continue
        result = read_properties(
            body, record, save_version=save_version, header_version=header_version
        )
        run = result.trailing_run
        if run is None or run.lead is None or not run.unread:
            continue
        end = record.body_offset + record.body_length
        items = read_item_list(body, end - run.unread, end)
        if items is not None and items.declared_count:
            derived.add(class_name_of(record.type_path))
    return frozenset(derived)


def _reference_pair_width_of(body: bytes, at: int, end: int) -> int | None:
    """Which of the allowed tail widths this remainder reads at, if any.

    AT MOST ONE CAN MATCH and that is structural rather than lucky: the walk
    over the four prefixes is deterministic and lands on ONE cursor, so exactly
    one tail width can carry that cursor onto ``end``.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The width, or None when the remainder is not a pair at any of them.
    """
    for tail_bytes in REFERENCE_PAIR_TAIL_WIDTHS:
        if read_reference_pair(body, at, end, tail_bytes=tail_bytes) is not None:
            return tail_bytes
    return None


def derive_reference_pair_classes(
    body: bytes,
    records: Iterable[ObjectRecord],
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> Mapping[str, int]:
    """Pick the classes whose trailing remainder is two object references - CS-828.

    **DERIVED FROM THE CORPUS, NEVER TRANSCRIBED**, for the reason
    :func:`derive_item_list_classes` is: a hand-maintained vocabulary of game
    content is the thing that rots, and CS-829's note forbids that shape by
    name. It answers the FORM as well as the membership, because the tail is not
    an unconditional suffix - measured on this project's library one schema
    writes it and two write the same two references and stop.

    **A CLASS EARNS ITS PLACE BY BEING CONSISTENT, AND THAT IS THE ANTI-VACUITY
    PROPERTY.** Every remainder-bearing record of the class in this body must
    read as a pair, and all of them at the SAME tail width. A reader taking each
    record at whichever width happened to fit would admit every mixture, which is
    arithmetic wearing a derivation's clothes: one class writes one form per
    body, or it writes a form this reader does not know and derives nothing.

    A body that stops carrying the shape therefore says so by deriving nothing,
    rather than going quietly green.

    THIS IS A SECOND WALK OVER THE BODY AND THAT IS INHERENT. The form is a
    property of the body as a whole and no per-record reader can hold it, which
    is exactly the sense in which the remainder is class-keyed.

    Args:
        body: The decompressed body.
        records: The records to derive from - a body's whole table.
        save_version: The save version the body was walked on, or None.
        header_version: The header version the body was walked on, or None.

    Returns:
        Each carrier class name to the tail width its records agree on.
    """
    widths: dict[str, set[int | None]] = {}
    for record in records:
        if not record.body_length:
            continue
        result = read_properties(
            body, record, save_version=save_version, header_version=header_version
        )
        run = result.trailing_run
        if run is None or run.lead is None or not run.unread:
            continue
        end = record.body_offset + record.body_length
        seen = widths.setdefault(class_name_of(record.type_path), set())
        seen.add(_reference_pair_width_of(body, end - run.unread, end))
    derived: dict[str, int] = {}
    for name, seen in widths.items():
        if len(seen) != 1:
            continue
        only = next(iter(seen))
        if only is not None:
            derived[name] = only
    return MappingProxyType(derived)


def _reference_list_form_of(body: bytes, at: int, end: int) -> int | None:
    """Which of the allowed per-entry widths this remainder reads at, if any.

    **MORE THAN ONE MATCH IS REFUSED RATHER THAN RESOLVED BY ORDER, WHICH IS A
    WEAKER CLAIM THAN :func:`_reference_pair_width_of` CAN MAKE AND IS STATED
    RATHER THAN ROUNDED UP.** There the string walk is fixed and only the tail
    moves, so exactly one width can carry one cursor onto ``end``. Here the two
    forms begin their walks at DIFFERENT offsets, so nothing structural forbids
    both landing - and taking the first would make the answer a property of the
    order this module happens to list the widths in.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The width, or None when the remainder is not a list at exactly one.
    """
    reads = tuple(
        width
        for width in REFERENCE_LIST_ENTRY_PREFIX_WIDTHS
        if read_reference_list(body, at, end, entry_prefix_bytes=width) is not None
    )
    return reads[0] if len(reads) == 1 else None


def derive_reference_list_classes(
    body: bytes,
    records: Iterable[ObjectRecord],
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> Mapping[str, int]:
    """Pick the classes whose remainder is a count-prefixed reference list - CS-828.

    **DERIVED FROM THE CORPUS, NEVER TRANSCRIBED**, for the reason
    :func:`derive_item_list_classes` is: a hand-maintained vocabulary of game
    content is the thing that rots, and CS-829's note forbids that shape by
    name. It answers the FORM as well as the membership, because the per-entry
    scalar is not unconditional - measured on this project's library one
    carrying class writes it ahead of every reference and two write the
    reference alone.

    **A CLASS EARNS ITS PLACE BY BEING CONSISTENT, AND THAT IS THE ANTI-VACUITY
    PROPERTY**, exactly as in :func:`derive_reference_pair_classes`. Every
    remainder-bearing record of the class in this body must read as a list, and
    all of them at the SAME per-entry width. A reader taking each record at
    whichever width happened to fit would admit every mixture, which is
    arithmetic wearing a derivation's clothes.

    A body that stops carrying the shape therefore says so by deriving nothing,
    rather than going quietly green.

    Args:
        body: The decompressed body.
        records: The records to derive from - a body's whole table.
        save_version: The save version the body was walked on, or None.
        header_version: The header version the body was walked on, or None.

    Returns:
        Each carrier class name to the per-entry width its records agree on.
    """
    widths: dict[str, set[int | None]] = {}
    for record in records:
        if not record.body_length:
            continue
        result = read_properties(
            body, record, save_version=save_version, header_version=header_version
        )
        run = result.trailing_run
        if run is None or run.lead is None or not run.unread:
            continue
        end = record.body_offset + record.body_length
        seen = widths.setdefault(class_name_of(record.type_path), set())
        seen.add(_reference_list_form_of(body, end - run.unread, end))
    derived: dict[str, int] = {}
    for name, seen in widths.items():
        if len(seen) != 1:
            continue
        only = next(iter(seen))
        if only is not None:
            derived[name] = only
    return MappingProxyType(derived)


def _transform_list_width_of(body: bytes, at: int, end: int) -> int | None:
    """Which of the allowed scalar widths this remainder reads at, if any.

    **MORE THAN ONE MATCH IS REFUSED RATHER THAN RESOLVED BY ORDER**, for the
    reason :func:`_reference_list_form_of` gives. The two widths make the walk
    reach each entry's length prefix at DIFFERENT offsets, so nothing structural
    forbids both landing on ``end`` - and taking the first would make the answer
    a property of the order this module happens to list the widths in.

    Args:
        body: The decompressed body.
        at: The remainder's first byte.
        end: The first byte past the payload.

    Returns:
        The width, or None when the remainder is not a list at exactly one.
    """
    reads = tuple(
        width
        for width in TRANSFORM_LIST_SCALAR_WIDTHS
        if read_transform_list(body, at, end, scalar_width=width) is not None
    )
    return reads[0] if len(reads) == 1 else None


def derive_transform_list_classes(
    body: bytes,
    records: Iterable[ObjectRecord],
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> Mapping[str, int]:
    """Pick the classes whose remainder is a count-prefixed named-transform list - CS-828.

    **DERIVED FROM THE CORPUS, NEVER TRANSCRIBED**, for the reason
    :func:`derive_item_list_classes` is: a hand-maintained vocabulary of game
    content is the thing that rots, and CS-829's note forbids that shape by
    name. It answers the SCALAR WIDTH as well as the membership, because the
    width is not a constant of the format - measured on this project's library
    the carrying class writes the narrow block on one of the three pairs CS-828
    covers and the wide block on the other two.

    **AND IT IS NOT VERSION-KEYED EITHER, WHICH IS THE SAME FENCE
    :func:`derive_reference_pair_classes` STANDS BEHIND.** A table mapping each
    measured layout to a scalar width would have worked on today's library and
    would have been a transcription. The width is derived off the body being
    read, so a body that stops writing the shape derives nothing and says so.

    **A CLASS EARNS ITS PLACE BY BEING CONSISTENT, AND THAT IS THE ANTI-VACUITY
    PROPERTY.** Every remainder-bearing record of the class in this body must
    read as a list, and all of them at the SAME width. A reader taking each
    record at whichever width happened to fit would admit every mixture, which
    is arithmetic wearing a derivation's clothes.

    **THE WEAKEST CASE, AND ON TODAY'S LIBRARY IT IS THE ONLY CASE.** The
    consistency requirement contributes nothing when a class has exactly ONE
    remainder-bearing record in the body: one record agrees with itself. Measured
    over every body of this project's library, EVERY derived carrier on EVERY one
    of the three pairs has exactly one - so the requirement refuses nothing here
    at all, and the WIDTH is as good as observed on all three. A first draft of
    this paragraph said it was the case on two pairs of three; the cycle's
    verifier re-derived it per body and measured that false. The READING is still
    not vacuous - the count must be positive, every name must be non-empty and
    the walk must land exactly on the declared end - and the requirement is kept
    because it is what a body carrying several such records would be held to.

    Args:
        body: The decompressed body.
        records: The records to derive from - a body's whole table.
        save_version: The save version the body was walked on, or None.
        header_version: The header version the body was walked on, or None.

    Returns:
        Each carrier class name to the scalar width its records agree on.
    """
    widths: dict[str, set[int | None]] = {}
    for record in records:
        if not record.body_length:
            continue
        result = read_properties(
            body, record, save_version=save_version, header_version=header_version
        )
        run = result.trailing_run
        if run is None or run.lead is None or not run.unread:
            continue
        end = record.body_offset + record.body_length
        seen = widths.setdefault(class_name_of(record.type_path), set())
        seen.add(_transform_list_width_of(body, end - run.unread, end))
    derived: dict[str, int] = {}
    for name, seen in widths.items():
        if len(seen) != 1:
            continue
        only = next(iter(seen))
        if only is not None:
            derived[name] = only
    return MappingProxyType(derived)


def derive_zero_remainder_classes(
    body: bytes,
    records: Iterable[ObjectRecord],
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> Collection[str]:
    """Pick the classes whose trailing remainder is one zero-valued int32 - CS-828.

    **DERIVED FROM THE CORPUS, NEVER TRANSCRIBED**, for the reason
    :func:`derive_item_list_classes` is: a hand-maintained vocabulary of game
    content is the thing that rots, and CS-829's note forbids that shape by
    name.

    **A CLASS EARNS ITS PLACE BY BEING CONSISTENT, AND THAT IS THE ANTI-VACUITY
    PROPERTY.** Every remainder-bearing record of the class in this body must
    read as the shape - the right width AND the right value. One record
    disagreeing takes the whole class out, so a body that stops carrying the
    shape says so by deriving nothing rather than going quietly green.

    **THE VALUE IS PART OF THE MEMBERSHIP AND NOT ONLY THE WIDTH.** Agreeing on
    a width is agreement about arithmetic; four bytes that read zero are a
    statement the bytes make. A derivation on width alone would admit every
    class whose leftovers happen to measure four, which is arithmetic wearing a
    derivation's clothes.

    THIS IS A SECOND WALK OVER THE BODY AND THAT IS INHERENT, exactly as in
    :func:`derive_reference_pair_classes`: the membership is a property of the
    body as a whole and no per-record reader can hold it.

    Args:
        body: The decompressed body.
        records: The records to derive from - a body's whole table.
        save_version: The save version the body was walked on, or None.
        header_version: The header version the body was walked on, or None.

    Returns:
        The carrier class names.
    """
    verdicts: dict[str, bool] = {}
    for record in records:
        if not record.body_length:
            continue
        result = read_properties(
            body, record, save_version=save_version, header_version=header_version
        )
        run = result.trailing_run
        if run is None or run.lead is None or not run.unread:
            continue
        end = record.body_offset + record.body_length
        reads = read_zero_remainder(body, end - run.unread, end) is not None
        name = class_name_of(record.type_path)
        verdicts[name] = reads and verdicts.get(name, True)
    return frozenset(name for name, reads in verdicts.items() if reads)


def derive_buildable_group_classes(
    body: bytes,
    records: Iterable[ObjectRecord],
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> Collection[str]:
    """Pick the classes whose trailing remainder is a buildable group list - CS-828.

    **DERIVED FROM THE CORPUS, NEVER TRANSCRIBED**, for the reason
    :func:`derive_item_list_classes` is: a hand-maintained vocabulary of game
    content is the thing that rots, and CS-829's note forbids that shape by
    name.

    **A CLASS EARNS ITS PLACE BY DEMONSTRATING THE GRAMMAR, AND THAT IS THE
    ANTI-VACUITY PROPERTY - IT IS NOT MERE CONSISTENCY.** One of the class's
    records in THIS body must carry a NON-EMPTY list that walks exactly onto its
    declared end, and no record of it may read as something this reader refuses.
    The stronger rule is needed here and not on the sibling shapes because this
    reader ACCEPTS an empty list: eight bytes whose second word is zero would
    otherwise admit any class whose leftovers happened to measure eight, which
    is arithmetic wearing a derivation's clothes. A body that stops carrying a
    populated list derives nothing and says so.

    **SO A BODY CARRYING ONLY EMPTY LISTS READS NONE OF THEM**, and that is the
    intended outcome rather than a gap. An empty list claims that a region is a
    structure with no members, and nothing in eight bytes distinguishes that
    from a class whose remainder is eight bytes of something else. The
    demonstration is what supplies the missing evidence, and it has to come from
    the same body because a vocabulary carried between saves is the transcription
    this project forbids.

    THIS IS A SECOND WALK OVER THE BODY AND THAT IS INHERENT, exactly as in
    :func:`derive_reference_pair_classes`: the membership is a property of the
    body as a whole and no per-record reader can hold it.

    Args:
        body: The decompressed body.
        records: The records to derive from - a body's whole table.
        save_version: The save version the body was walked on, or None.
        header_version: The header version the body was walked on, or None.

    Returns:
        The carrier class names.
    """
    reads: dict[str, bool] = {}
    shown: set[str] = set()
    for record in records:
        if not record.body_length:
            continue
        result = read_properties(
            body, record, save_version=save_version, header_version=header_version
        )
        run = result.trailing_run
        if run is None or run.lead is None or not run.unread:
            continue
        end = record.body_offset + record.body_length
        read = read_buildable_group_list(body, end - run.unread, end)
        name = class_name_of(record.type_path)
        reads[name] = read is not None and reads.get(name, True)
        if read is not None and read.groups:
            shown.add(name)
    return frozenset(name for name in shown if reads.get(name, False))


def read_properties(  # noqa: PLR0913 - one keyword per derived remainder vocabulary is the clearest surface
    body: bytes,
    record: ObjectRecord,
    property_map: PropertyMap | None = None,
    *,
    save_version: int | None = None,
    header_version: int | None = None,
    item_list_classes: Collection[str] = (),
    reference_pair_classes: Mapping[str, int] = _NO_REFERENCE_PAIR_CLASSES,
    reference_list_classes: Mapping[str, int] = _NO_REFERENCE_LIST_CLASSES,
    transform_list_classes: Mapping[str, int] = _NO_TRANSFORM_LIST_CLASSES,
    zero_remainder_classes: Collection[str] = _NO_ZERO_REMAINDER_CLASSES,
    buildable_group_classes: Collection[str] = _NO_BUILDABLE_GROUP_CLASSES,
) -> PropertyResult:
    """Decode one record's measured properties and report what was skipped.

    DECODING DOES NOT DEPEND ON THE SCHEMA RESOLVING, and that is a measurement
    rather than a convenience. A payload is TAGGED serialization - every
    property's name and type word are in the save's own bytes - so the mapping
    is not an input to the decode at all. It was the ORACLE the value grammar
    was validated against, which is a different job.

    Gating the decode on resolution would in fact decode nothing that matters:
    the shipped mapping carries NO ``Build_*`` schema and only 2 blueprint
    generated schemas out of 13792, so every one of the 24314 building records
    in this library resolves to nothing. Buildings are exactly what pillar 3
    audits, and a reader that refused them would be permanently empty where it
    is most needed.

    So ``resolved`` and the decode are reported INDEPENDENTLY. An unresolved
    class is still flagged - non-negotiable 7 - and its self-describing
    properties are still read; a property whose TYPE is unmeasured is skipped
    and counted whether the class resolved or not.

    AND THE MAP IS OPTIONAL, WHICH IS THE SAME MEASUREMENT CARRIED TO ITS END
    (CS-960). If the mapping is not an input to the decode then requiring one
    buys nothing and costs everything: ``usmap.cached_usmap()`` answers None on
    a machine with no game install, so a mandatory map meant CI and every fresh
    clone decoded no property at all. Every use of the parameter below this
    line is a membership test on a class name the record table already holds,
    plus two ``del`` statements for privacy - no width, no offset and no type
    word comes from it, and nothing beneath this function even accepts one.
    The signature said "non-optional" because at the commit that wrote it this
    function DECODED NOTHING and the schema lookup was its whole body; decoding
    was added later and the signature was never revisited. A parameter's
    necessity is a claim about the function as it is now.

    WITH NO MAP, ``resolved`` IS None AND NO UNRESOLVED-SCHEMA WARNING IS
    RAISED. Absent is not unmodelled: nothing was consulted, so nothing may be
    claimed, and answering False there would flag every record in the world as
    unknown content on a machine that simply has no install - the
    confident-wrong answer non-negotiable 7 forbids. It is the position
    ``parse_object_headers`` already takes with ``known_classes=None``.

    Nothing here raises for unknown content.

    THE STRUCTURAL CHECK RUNS FIRST, AND IT RUNS FOR EVERY RECORD. It used to
    sit after an early return for an unresolved class, which - on this project's
    own measurement, where essentially no building resolves - meant it ran on
    almost nothing. Reaching it for every record is the correct direction and is
    deliberate: an extent running past the body is NOT the unknown CONTENT
    non-negotiable 7 covers. It is a record claiming bytes that do not exist,
    which is the same class as the unknown-grammar case in the module docstring,
    and reporting it as merely unparsed would let a truncated or misattributed
    body pass as a world this project simply does not model.

    Args:
        body: The decompressed body the record was walked out of.
        record: The record to resolve.
        save_version: The save version the body was walked on, or None. With
            ``header_version`` it selects the property TAG grammar - see
            :func:`uses_complete_type_name`. BOTH DEFAULT TO NONE, which selects
            the legacy grammar, because every caller predating CS-G05 passes
            three positional arguments and a default that changed what they read
            would be a silent regression.
        header_version: The header version the body was walked on, or None.
        property_map: The parsed mapping, or None when none was supplied.
            OPTIONAL, and defaulted so that "no map" is the shape a caller
            falls into rather than one it has to construct. It drives the
            resolution report alone and never the decode.

        item_list_classes: Class names derived as item-list carriers by
            :func:`derive_item_list_classes`. DEFAULTED EMPTY so that adding
            this reading could not change what any existing caller reads.
        reference_pair_classes: Each class name derived as a reference-pair
            carrier to the tail width its records agree on, from
            :func:`derive_reference_pair_classes`. DEFAULTED EMPTY for the same
            reason, so a caller that has not derived reads what CS-828 left.
        reference_list_classes: Each class name derived as a reference-LIST
            carrier to the per-entry prefix width its records agree on, from
            :func:`derive_reference_list_classes`. DEFAULTED EMPTY for the same
            reason.
        transform_list_classes: Each class name derived as a NAMED-TRANSFORM
            list carrier to the scalar width its records agree on, from
            :func:`derive_transform_list_classes`. DEFAULTED EMPTY for the same
            reason.
        buildable_group_classes: Class names derived as buildable-group-list
            carriers by :func:`derive_buildable_group_classes`. DEFAULTED EMPTY
            for the same reason every vocabulary here is.
        zero_remainder_classes: Class names derived as zero-remainder carriers
            by :func:`derive_zero_remainder_classes`. DEFAULTED EMPTY for the
            same reason again - and the default is exactly why the library
            sweep in ``tests/save/test_trailing_run.py`` takes all of them as
            REQUIRED keywords: a default meaning "read less" is invisible to a
            test that measures only what was read.

    Returns:
        What resolved, what did not, and why.

    Raises:
        ObjectTruncatedError: The record's declared payload extent runs past
            the body. A structural impossibility rather than unknown content.
    """
    if record.body_length != 0 and (
        record.body_offset < 0 or record.body_offset + record.body_length > len(body)
    ):
        available = max(len(body) - record.body_offset, 0)
        # THE BODY AND THE MAPPING ARE DROPPED FROM THIS FRAME BEFORE THE RAISE,
        # and that is a mechanism rather than a courtesy. The error MESSAGE was
        # always clean; the channel is the FRAME. A traceback renderer that
        # shows locals - pytest does - prints `body` verbatim, head and tail,
        # which is the whole decompressed world (non-negotiable 12). A clean
        # message with a leaking frame is a mitigation the mechanism defeats.
        # `del` is what a renderer cannot get around: a deleted fast local is
        # simply absent from `frame.f_locals`. The mapping goes for a weaker but
        # real reason - it is not personal data, and this branch has no use for
        # it. It no longer carries the echo it once did: `PropertyMap` rendered
        # its whole name table under a default repr until CS-424 gave it, and
        # its two neighbours, a repr of structure and counts. The `del` stays
        # anyway, because a quiet repr is a promise a later edit can withdraw
        # while a deleted local is a fact the renderer cannot reach around.
        # tests/save/test_properties.py::test_no_clockspeed_frame_holds_the_body_
        # when_the_extent_raises walks the raised traceback and asserts this,
        # so a NEW raise site added to this function is red rather than silent.
        del body, property_map
        raise ObjectTruncatedError(
            REASON_SHORT_BUFFER,
            field="property_payload",
            offset=record.body_offset,
            expected=record.body_length,
            actual=available,
        )

    name = class_name_of(record.type_path)
    # THE ONLY USE OF THE MAP IN THIS FUNCTION, and it feeds the report rather
    # than the decode. None propagates as None: no map was consulted, so the
    # question "does the mapping model this class" has no answer here.
    resolved = None if property_map is None else name in property_map.schemas
    # `is False` RATHER THAN A TRUTHINESS TEST. None is falsy, so `if not
    # resolved` would raise the unresolved-schema warning for a record nothing
    # was ever checked against - which is exactly the collapse of ABSENT into
    # UNMODELLED that the field above forbids, and it would fire on every
    # record on any machine with no game install.
    schema_warnings: tuple[ObjectWarning, ...] = (
        (_warning(WARN_UNRESOLVED_SCHEMA, record.body_offset),) if resolved is False else ()
    )

    if record.body_length == 0:
        # Every record from the FLAT walk, which attributes no extent, and no
        # record at all from a real save - CS-413 measured zero zero-length
        # payloads across all 14 of them. Not unknown content either way.
        return PropertyResult(
            properties=MappingProxyType({}),
            schema_name=name,
            resolved=resolved,
            warnings=schema_warnings,
        )

    end = record.body_offset + record.body_length
    start: int | None = record.body_offset
    if record.kind == KIND_ACTOR:
        start = _skip_actor_head(body, record.body_offset, end)
    type_tree = uses_complete_type_name(header_version, save_version)
    if type_tree and start is not None:
        # THE LEAD BYTE, STEPPED FOR BOTH KINDS. On an actor it sits past the
        # component list, on a component it is the payload's first byte - one
        # field in one place, which is why this is here rather than inside
        # `_skip_actor_head`, whose whole subject is the actor asymmetry.
        lead = start + PAYLOAD_TAG_LEAD_BYTES
        start = lead if lead <= end else None
    walked = None if start is None else _walk_payload(body, start, end, type_tree=type_tree)
    if walked is None:
        # The payload does not read under the grammar the caller's pair
        # selected. A SENTENCE HERE USED TO SAY THIS WAS "every payload of the
        # (14,60) pair" and treat that as a fact about the pair. It was a fact
        # about this function - see the CS-G05 block above
        # :data:`COMPLETE_TYPE_NAME_PAIRS`.
        return PropertyResult(
            properties=MappingProxyType({}),
            schema_name=name,
            resolved=resolved,
            warnings=(
                *schema_warnings,
                _warning(
                    WARN_UNPARSED_PROPERTY_PAYLOAD, record.body_offset, actual=record.body_length
                ),
            ),
        )

    decoded, unmeasured, disagreed = walked.properties, walked.unmeasured, walked.disagreed
    warnings = schema_warnings
    if disagreed:
        # A SEPARATE CODE FROM THE ONE BELOW, because the two mean opposite
        # things - see :func:`_decode_payload`. A caller that cannot tell
        # unmodelled content from a walk that has lost its place cannot decide
        # whether to trust anything else this payload returned.
        warnings = (
            *warnings,
            _warning(WARN_MEASURED_VALUE_DISAGREED, record.body_offset, actual=disagreed),
        )
    if unmeasured:
        # ONE warning per record rather than per tag. Per tag it would be one
        # warning for every unmeasured-type tag in the world, which is a channel
        # nobody reads.
        #
        # A COUNT USED TO STAND HERE AND IS DELETED RATHER THAN CORRECTED. It
        # gave a per-tag figure SMALLER than the instance counts in
        # UNMEASURED_PAYLOAD_REGIONS sum to, which cannot be: a per-tag warning
        # cannot be rarer than the tags that trigger it. Re-measured, the
        # per-tag figure is exactly that sum - the figure written here was
        # simply wrong, and the region table was right. Writing the corrected
        # number here would put a second copy of a count that table already
        # owns into a comment no test reads, which is the drift class
        # CLAUDE.md section 4 exists to stop. The region table is the owner.
        warnings = (
            *warnings,
            _warning(WARN_UNMEASURED_PROPERTY_TYPE, record.body_offset, actual=unmeasured),
        )
    return PropertyResult(
        properties=MappingProxyType(decoded),
        schema_name=name,
        resolved=resolved,
        warnings=warnings,
        unmeasured_value_count=unmeasured,
        disagreeing_value_count=disagreed,
        references=walked.references,
        reference_tag_count=walked.reference_tags,
        undecoded_reference_count=walked.undecoded_references,
        trailing_run=_run_with_zero_remainder(
            body,
            record,
            _run_with_buildable_groups(
                body,
                record,
                _run_with_transform_list(
                    body,
                    record,
                    _run_with_reference_list(
                        body,
                        record,
                        _run_with_reference_pair(
                            body,
                            record,
                            _run_with_item_list(
                                body, record, walked.trailing_run, item_list_classes
                            ),
                            reference_pair_classes,
                        ),
                        reference_list_classes,
                    ),
                    transform_list_classes,
                ),
                buildable_group_classes,
            ),
            zero_remainder_classes,
        ),
        struct_interiors=walked.struct_interiors,
        struct_tag_count=walked.struct_tags,
        undecoded_names=walked.undecoded_names,
    )


# ---------------------------------------------------------------------------
# Reference resolution (CS-831)
#
# THE SEAM. This joins two things this module already owns - the record table
# it walked, and the reference values it decoded - and it reaches for nothing
# else. It takes no body, which is deliberate: a resolver needing one would
# make the join a third parse of the save rather than a join, and would put the
# decompressed world into one more frame that a traceback can render
# (non-negotiable 12).
#
# WHAT WAS THERE BEFORE. The pairing was already MEASURED - the cross-section
# oracle in tests/save/test_decode_oracles.py resolves each reference against
# the record table and reports a rate. What it does with the record it finds is
# add one to a counter and drop it. That is the correct shape for an oracle and
# it is not a capability: no consumer under clockspeed/ could ask which record
# a reference names, which is why a building's mStorageInventory could not be
# followed to the inventory it points at.
# ---------------------------------------------------------------------------


#: EVERY SYMBOL OF THIS MODULE THAT BOTH REFERENCE COUNTS EXECUTE - CS-835.
#:
#: WHAT IT IS FOR. ``tests/save/test_reference_resolution.py`` grades the join
#: by counting the same references a SECOND time and comparing. That second
#: count re-uses this module's reader wholesale, so the two counts are not two
#: pieces of evidence about anything named below: a defect in any of these
#: symbols moves both counts the same way and the comparison stays green. Two
#: derivations off one reader are one reader's opinion stated twice (CLAUDE.md
#: section 5), and this is the list of what that covers.
#:
#: WHY A LIST AND NOT A SECOND READER. CS-835's other arm was a reference count
#: obtained without these primitives. It was measured impossible short of a
#: second implementation of the save grammar, which this project has not built
#: and has recorded not building - the one grammar-free count available bounds
#: the population and cannot equal it (see :func:`resolve_references`). So the
#: limit is written down instead of argued away, and a test holds this list
#: against the surface actually shared, going red when a symbol joins or leaves.
#:
#: IT IS LONG ON PURPOSE AND THE LENGTH IS THE FINDING. The four primitives the
#: item names - ``_payload_text``, ``_read_tag_header``, ``_decode_value`` and
#: ``_skip_actor_head`` - drag in everything they call, and the honest surface
#: is the closure rather than the four. NO COUNT OF THESE NAMES IS WRITTEN IN
#: PROSE anywhere; the set is the record and ``len`` is how anyone asks.
REFERENCE_COUNT_COMMON_MODE: Final = frozenset(
    {
        "CONTAINER_TYPE_WORDS",
        "ContainerElement",
        "ContainerValue",
        "ELEMENT_SHAPE_SELF_DELIMITING",
        "ELEMENT_SHAPE_SOLVED_WIDTH",
        "ELEMENT_SHAPE_UNIFORM_WIDTH",
        "GUID_BYTES",
        "INVENTORY_ITEM_STRUCT_WORD",
        "ITEM_FORM_AMBIGUOUS",
        "ITEM_FORM_UNCLOSED",
        "INT32_SIZE",
        "InventoryItem",
        "InventoryItemRefusal",
        "KIND_ACTOR",
        "MAX_OBJECTS",
        "MAX_STRING_BYTES",
        "MAX_STRUCT_DEPTH",
        "MEASURED_TAG_FLAG_MASK",
        "MEASURED_VALUE_TYPES",
        "ObjectReference",
        "REFERENCE_TYPE_WORD",
        "STRUCT_FORM_TAG_LIST",
        "STRUCT_TYPE_WORD",
        "StructValue",
        "TAG_FLAG_ARRAY_INDEX",
        "TAG_FLAG_BOOL_TRUE",
        "TAG_FLAG_NATIVE_SERIALIZE",
        "UTF16_CHAR_SIZE",
        "_CONTAINER_LEAD_FIELDS",
        "_ELEMENT_FIXED_WIDTHS",
        "_ELEMENT_STRING_COUNTS",
        "_ELEMENT_TAG_LIST_WORD",
        "_FIXED_WIDTH_VALUES",
        "_MAX_CONTAINER_ELEMENTS",
        "_MAX_ELEMENT_TAGS",
        "_MAX_TAGS_PER_PAYLOAD",
        "_MAX_TYPE_NAME_DEPTH",
        "_MAX_TYPE_NAME_PARAMS",
        "_ONE_STRING_VALUES",
        "_PAYLOAD_TERMINATOR",
        "_RAW_SHAPE_ELEMENT_WORDS",
        "_REFERENCE_PARTS",
        "_SCRIPT_STRUCT_LEAD",
        "_SOFT_OBJECT_TAIL_BYTES",
        "_SOLVED_WIDTH_CAP",
        "_TAG_EXTRA_STRINGS",
        "_TAG_INDEX_FIELD_BYTES",
        "_TWO_STRING_VALUES",
        "_UNEVIDENCED_UNDER_NATIVE_SERIALIZE",
        "_as_reference",
        "_bound_container_elements",
        "_container_element_words",
        "_container_grammar_is_modelled",
        "_decode_bounded_elements",
        "_decode_container",
        "_decode_element_interior",
        "_decode_element_value",
        "_decode_fixed_width",
        "_decode_interior_tag",
        "_decode_object_reference",
        "_decode_struct_interior",
        "_decode_text_value",
        "_decode_value",
        "_element_half_end",
        "_element_tag_list_end",
        "_open_container",
        "_payload_text",
        "_read_array_struct_tag",
        "_read_item_new_form",
        "_read_item_old_form",
        "_read_item_state",
        "_read_tag_and_words",
        "_read_tag_header",
        "_read_type_name",
        "_read_type_tree_tag_header",
        "_refusal_is_unmodelled_content",
        "_skip_actor_head",
        "_skip_guid_flag",
        "_skip_tag_extra",
        "_struct_word_of_tag",
        "_walk_elements",
        "_walk_struct_tags",
        "read_inventory_item",
    }
)

#: The leading separator that opens a path into the game's own content tree.
#: THE CRITERION IS THE SEPARATOR, NOT ANY ROOT NAME. Naming an observed root
#: would put a corpus fact in a constant and make the classifier go wrong the
#: first time a save references a root nobody had seen (CLAUDE.md section 4).
_CONTENT_PATH_ROOT: Final = "/"

#: The three shapes an UNRESOLVED reference's path takes, name to what the shape
#: does and does not say - CS-833.
#:
#: THESE ARE SHAPE TESTS AND NOT CLAIMS ABOUT WHAT THE REFERENCE NAMES, and
#: keeping that distinction is the whole of this item. The withdrawn universal
#: went wrong by reading a shape as an identity: it saw that most unresolved
#: paths look like assets and concluded that unresolved MEANS asset. A shape can
#: only ever say what the string looks like, and the two members below that look
#: nothing like an asset are what proved the difference matters.
UNRESOLVED_ASSET_SHAPED: Final = "asset_shaped"
UNRESOLVED_SAVE_OBJECT_SHAPED: Final = "save_object_shaped"
UNRESOLVED_EMPTY_PATH: Final = "empty_path"

UNRESOLVED_SHAPES: Final[Mapping[str, str]] = MappingProxyType(
    {
        UNRESOLVED_ASSET_SHAPED: (
            "the path opens at the content-tree root, which is the shape a "
            "reference to content SHIPPED WITH THE GAME carries. It is the bulk "
            "of the bucket on this project's library and it is the reading the "
            "withdrawn universal generalised from. What it claims is the SHAPE; "
            "that the asset exists, or that the game would resolve it, is not "
            "checked here and could not be without reading the install"
        ),
        UNRESOLVED_SAVE_OBJECT_SHAPED: (
            "the path is in the same shape every RESOLVING reference carries and "
            "no record in this table bears it. THIS IS THE CLASS THAT FALSIFIED "
            "THE UNIVERSAL - it names no asset. What it means is deliberately NOT "
            "claimed: a reference to an object in a level this save did not "
            "carry, a stale link, and a defect in this module's own record walk "
            "would all land here, and separating them needs an oracle this "
            "project does not have. Counting it apart is what makes the question "
            "askable at all"
        ),
        UNRESOLVED_EMPTY_PATH: (
            "the reference decoded and its object path is the empty string. It "
            "names nothing - not an asset and not a saved object - so both other "
            "readings are wrong for it. It is the member a resolver is most "
            "likely to drop silently, because skipping a lookup that cannot "
            "succeed reads as an optimisation (CS-836)"
        ),
    }
)


def classify_unresolved(object_path: str) -> str:
    """Sort one unresolved reference's path into a shape.

    TOTAL BY CONSTRUCTION. The last branch is unconditional, so every string has
    a shape and none is dropped. A classifier that could return nothing would
    rebuild the CS-833 defect one layer down - a reference counted under a
    heading whose stated meaning does not cover it.

    THE ORDER OF THE TESTS IS LOAD-BEARING. The empty string is asked about
    first because it is the one path that is in no shape at all, and asking the
    content-root test first would sort it by the accident that the empty string
    starts with nothing.

    Args:
        object_path: A reference's second string. Not required to be unresolved
            - the function is a shape test and takes any string - though only
            unresolved paths are counted with it.

    Returns:
        One of :data:`UNRESOLVED_SHAPES`.
    """
    if not object_path:
        return UNRESOLVED_EMPTY_PATH
    if object_path.startswith(_CONTENT_PATH_ROOT):
        return UNRESOLVED_ASSET_SHAPED
    return UNRESOLVED_SAVE_OBJECT_SHAPED


def index_records(table: ObjectTable) -> RecordIndex:
    """Arrange a walked record table for reference lookup.

    KEYED ON ``instance_name`` BECAUSE THAT IS THE MEASURED PAIRING. A
    reference's second string is matched against a record's instance name, and
    the two sections are parsed by different passes over different parts of the
    body - which is what makes the cross-section oracle evidence about the
    grammar rather than a restatement of one reader's opinion.

    EVERY RECORD IS INDEXED, including one whose class the registry does not
    model. An unknown class is flagged elsewhere and is still a real object
    that a reference may legitimately name, so dropping it here would turn
    unmodelled content into a broken link (non-negotiable 7).

    Args:
        table: The walked record table.

    Returns:
        The index. Names map to EVERY record bearing them - see
        :class:`RecordIndex` for why that is not a single record.
    """
    grouped: dict[str, list[ObjectRecord]] = {}
    for record in table.records:
        grouped.setdefault(record.instance_name, []).append(record)
    return RecordIndex(
        records_by_name=MappingProxyType({name: tuple(found) for name, found in grouped.items()})
    )


def resolve_references(index: RecordIndex, result: PropertyResult) -> ReferenceResolution:
    """Resolve one record's references against the table, and partition them.

    NOTHING HERE RAISES, and nothing here is an error. A reference that matches
    no record is counted as unresolved and skipped, which is exactly what
    non-negotiable 7 asks for. So is a tag whose bytes yielded no pair.

    WHAT AN UNRESOLVED REFERENCE NAMES IS NO LONGER GLOSSED HERE - CS-833. This
    clause used to say it names an ASSET, as a universal over the bucket, and
    the library falsifies that: see :class:`ReferenceResolution` for what the
    bucket actually holds and :func:`classify_unresolved` for the partition that
    replaced the gloss. Every member is sorted into a shape as it is counted, so
    a consumer reads the split rather than the sentence.

    THE POPULATION IS THE TOP-LEVEL PROPERTY TAG, AND THAT BOUNDARY IS STATED
    HERE BECAUSE NOTHING ELSE OWNED IT - CS-834. What enters
    ``result.references`` is a tag :func:`_walk_payload` stepped over at the top
    level of a payload. THREE CLASSES OF REFERENCE ARE THEREFORE OUTSIDE THIS
    FUNCTION'S REACH, and none of them is a defect in it:

    - A reference nested inside a value the walk steps over as OPAQUE BYTES. A
      :data:`UNMEASURED_PAYLOAD_REGIONS` entry names the struct interior as
      exactly that. CS-830 measured a CONTAINER's element framing, which is not
      the same thing as descending into an element: the walk advances by the
      tag's own declared size either way, so a reference inside an element is
      stepped over with it.
    - A reference in a region of the payload no tag covers, the trailing run
      that :data:`UNMEASURED_PAYLOAD_REGIONS` records among them.
    - THE ACTOR HEAD'S COMPONENT LIST, stepped over by :func:`_skip_actor_head`
      before the first tag is read. It is the one worth naming separately
      because it is the only class that is not opaque at all: the head is parsed
      exactly, the parent reference and the component pairs ARE references in
      this same two-string shape, and they are skipped because they carry no
      property tag rather than because their bytes are unmeasured. A count of
      the reference TYPE WORD does not see them for the same reason.

    HOW FAR THAT BOUNDARY IS MEASURED, AND NO FURTHER. A grammar-free byte scan
    for the length-prefixed type word runs well ahead of this population, and
    ``tests/save/test_reference_resolution.py`` derives the difference on every
    run rather than recording a figure here. It is ONE number and is left as
    one: an earlier attempt apportioned it between named regions, the halves
    summed to a correct total, and re-measurement did not support the split.
    Naming the classes above is not apportioning the count between them, and
    this module claims no such apportionment.

    THE PARTITION AGAINST ``total`` IS AN IDENTITY, AND SAYING SO REPLACES A
    SENTENCE THAT CLAIMED THE OPPOSITE. The loop below does exactly one of
    ``resolved += 1`` or ``unresolved += 1`` per member of
    ``result.references``, and :func:`_walk_payload` already holds
    ``reference_tag_count == undecoded_reference_count + len(references)`` as a
    loop invariant, so ``resolved + unresolved + undecoded == total`` reduces to
    a restatement of both and cannot come out false. A ``ReferenceResolution``
    property that advertised itself as where a caller asks whether it did was
    removed together with the claim, because a self-check that is constant True
    over everything its own producer can build grades nothing.

    THE SAME SUM AGAINST A TAG TOTAL THIS MODULE DID NOT COUNT IS NOT AN
    IDENTITY, and the distinction is the whole of what is gradeable here. A
    defect in this module's tag counting moves ``total`` and leaves a total
    taken by an independent walk where it was, so the two part company - which
    is why the check is made against such a walk in
    ``tests/save/test_reference_resolution.py`` and not against ``total`` here.

    AMBIGUITY IS COUNTED, NOT RESOLVED. An instance name borne by more than one
    record is measured to occur on this project's own library, and this
    function does not guess which one was meant - the resolution counts it and
    hands back all of them.

    Args:
        index: The record table, arranged by :func:`index_records`.
        result: One record's decoded properties, carrying its typed
            references.

    Returns:
        The partition, and the records each resolved reference names.
    """
    targets: dict[str, tuple[ObjectRecord, ...]] = {}
    resolved = 0
    ambiguous = 0
    shapes = dict.fromkeys(UNRESOLVED_SHAPES, 0)
    for reference in result.references:
        found = index.records_for(reference.object_path)
        if not found:
            # THE LOOKUP HAPPENS FIRST AND UNCONDITIONALLY, INCLUDING FOR THE
            # EMPTY PATH - CS-836. Short-circuiting a path nothing can bear
            # reads as an optimisation and is a silent drop: the reference would
            # leave this loop in no bucket, and `total` comes from the walk's own
            # tag counter, so the partition would stop summing to it. A
            # synthetic case holds that sum precisely so the drop cannot survive
            # on a machine with no save library.
            shapes[classify_unresolved(reference.object_path)] += 1
            continue
        resolved += 1
        if len(found) > 1:
            ambiguous += 1
        targets[reference.property_name] = found
    return ReferenceResolution(
        targets=MappingProxyType(targets),
        resolved=resolved,
        # DERIVED FROM THE SHAPES RATHER THAN COUNTED ALONGSIDE THEM, so the
        # bucket and its partition cannot disagree. A second accumulator here
        # would be a fourth site for the same number and the drift that follows.
        unresolved=sum(shapes.values()),
        undecoded=result.undecoded_reference_count,
        ambiguous=ambiguous,
        total=result.reference_tag_count,
        unresolved_asset_shaped=shapes[UNRESOLVED_ASSET_SHAPED],
        unresolved_save_object_shaped=shapes[UNRESOLVED_SAVE_OBJECT_SHAPED],
        unresolved_empty_path=shapes[UNRESOLVED_EMPTY_PATH],
    )


def parse_properties(
    body: bytes,
    record: ObjectRecord,
    property_map: PropertyMap | None = None,
    *,
    save_version: int | None = None,
    header_version: int | None = None,
) -> Mapping[str, object]:
    """Resolve one record's properties, discarding the diagnostics.

    The thin accessor over :func:`read_properties` for a caller that wants only
    the mapping. Prefer the detailed form anywhere the flagged state matters -
    an empty mapping alone cannot tell "this class has no properties" from
    "this class is not modelled".

    WHAT CAN BE DECODED IS :func:`read_properties`' FACT AND IS STATED THERE.
    This clause used to restate it - "always empty today" - and it went stale
    the day the value grammar was measured, in the dangerous direction: it told
    the next consumer the return was safe to print. A capability restated at a
    second site is one that rots at the second site, and this function owns
    only the discarding.

    A THIN WRAPPER IS STILL A FRAME. :func:`read_properties` drops the body
    before it raises, which closes ITS frame and nothing else - this one holds
    the same bytes while that error travels through, so a renderer showing
    locals prints the whole decompressed body from here instead. Every exported
    way into the reader has to be closed, not the one the first test happened
    to exercise.

    Args:
        body: The decompressed body the record was walked out of.
        record: The record to resolve.
        save_version: The save version the body was walked on, or None. With
            ``header_version`` it selects the property TAG grammar - see
            :func:`uses_complete_type_name`. BOTH DEFAULT TO NONE, which selects
            the legacy grammar, because every caller predating CS-G05 passes
            three positional arguments and a default that changed what they read
            would be a silent regression.
        header_version: The header version the body was walked on, or None.
        property_map: The parsed mapping, or None when none was supplied.
            OPTIONAL on the same terms as :func:`read_properties`, and the
            optionality matters MORE here: this is the accessor that discards
            the diagnostics, so a caller reaching for it is one that wants
            values and has no use for a mapping it may not have.

    Returns:
        Whatever :func:`read_properties` decoded, with its diagnostics dropped.
        DECODED WORLD CONTENT - both the names and the values come out of the
        save's own bytes, so a caller that renders this mapping is an echo path
        under non-negotiable 12.

    Raises:
        ObjectTruncatedError: Propagated from :func:`read_properties`, whose
            ``Raises`` clause states when. It leaves this frame carrying no
            body - see the handler below.
    """
    try:
        return read_properties(
            body,
            record,
            property_map,
            save_version=save_version,
            header_version=header_version,
        ).properties
    except BaseException:
        # THE HANDLER CHANGES NOTHING ABOUT WHAT PROPAGATES. It catches, scrubs
        # this frame and re-raises the same exception with the same traceback;
        # its only effect is that `body` is gone from the frame's fast locals
        # by the time any renderer reads them (non-negotiable 12). The mapping
        # goes with it for the reason given in read_properties.
        #
        # IT IS NOT NARROWER ON PURPOSE. A frame carries the body out on ANY
        # unwind, not only on the one error this function currently documents,
        # so catching `ObjectTruncatedError` would re-open the frame for every
        # exception type a later edit introduces - which is exactly how this
        # site was missed the first time. Because the re-raise is unconditional
        # there is nothing for a broad catch to swallow.
        del body, property_map
        raise
