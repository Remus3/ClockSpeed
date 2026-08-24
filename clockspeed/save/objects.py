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
   corroborate any of this: its payloads are opaque filler, so it pins the
   tiling arithmetic and nothing about the grammar.

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
from collections.abc import Container, Mapping
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
    "CONTAINER_ADJACENT_OWNERS",
    "CONTAINER_TYPE_WORDS",
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
    "KIND_ACTOR",
    "KIND_COMPONENT",
    "LEVEL_TAIL_NONE",
    "LEVEL_TAIL_SUMMARY",
    "LEVEL_TAIL_WORD",
    "MAX_CUSTOM_VERSIONS",
    "MAX_GRIDS",
    "MAX_LEVELS",
    "MAX_LEVEL_TAIL_ENTRIES",
    "MAX_OBJECTS",
    "MAX_OBJECT_DATA_BYTES",
    "MAX_STRING_BYTES",
    "MEASURED_BODY_LAYOUTS",
    "MEASURED_HEADER_VERSIONS",
    "MEASURED_VALUE_TYPES",
    "REASON_NO_DISCRIMINATION_TEST",
    "REASON_SAMPLE_SIZE",
    "REASON_SHIPPED_ALIGNMENT_ONLY",
    "REFERENCE_COUNT_COMMON_MODE",
    "REFERENCE_TYPE_WORD",
    "TRANSFORM_BYTES",
    "TRANSFORM_DELTA_BY_SAVE_VERSION",
    "TRANSFORM_FLOAT_COUNT",
    "UNKNOWN_CLASS_REASONS",
    "UNMEASURED_PAYLOAD_REGIONS",
    "UNRESOLVED_ASSET_SHAPED",
    "UNRESOLVED_EMPTY_PATH",
    "UNRESOLVED_SAVE_OBJECT_SHAPED",
    "UNRESOLVED_SHAPES",
    "VALUE_BYTE_ORDER_STATUS",
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
    "ContainerElement",
    "ContainerValue",
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
    "ReferenceResolution",
    "Transform",
    "UnknownClass",
    "UnsupportedBodyLayoutError",
    "UnsupportedSaveVersionError",
    "class_name_of",
    "classify_unresolved",
    "container_candidate_words",
    "index_records",
    "parse_body",
    "parse_object_headers",
    "parse_properties",
    "read_properties",
    "resolve_references",
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
        "level_trailer",
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
        resolved: Whether the property map models that class at all.
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
    """

    properties: Mapping[str, object]
    schema_name: str
    resolved: bool
    warnings: tuple[ObjectWarning, ...]
    unmeasured_value_count: int = 0
    disagreeing_value_count: int = 0
    references: tuple[ObjectReference, ...] = ()
    reference_tag_count: int = 0
    undecoded_reference_count: int = 0

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
            f"undecoded_reference_count={self.undecoded_reference_count})"
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
            # Re-raised from None: a UnicodeDecodeError message QUOTES the
            # offending bytes, and exception context is an echo path.
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


def _read_collectables(cursor: _Cursor) -> int:
    """Read one collectable list.

    MEASURED as a count followed by that many PAIRS OF STRINGS - measured in
    the sense that reading it any other way stops the whole-body walk short of
    the final byte. No meaning is claimed for either string.

    Args:
        cursor: Positioned at the count.

    Returns:
        How many entries were read.
    """
    count = _read_bounded_count(cursor, "collectable_count", MAX_OBJECTS)
    for _ in range(count):
        cursor.string("collectable")
        cursor.string("collectable")
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
    corroborate it: its payloads are opaque filler.

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
        _read_collectables(cursor)
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
        _read_collectables(cursor)


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
    for _ in range(level_count):
        _read_level(
            cursor,
            layout,
            named=True,
            known_classes=known_classes,
            records=records,
            unknown=unknown,
            warnings=warnings,
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
    )
    # MEASURED as present, and observed to be zero. Its MEANING is unmeasured,
    # so it is consumed and not interpreted - a walk without it stops exactly
    # four bytes short of the end of a real body.
    cursor.int32("level_trailer")

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
    )


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
            "declined because no discrimination test has been put to it, so an "
            "exception to the rule rather than an application of it. The "
            "StructProperty entry of UNMEASURED_PAYLOAD_REGIONS records that "
            "the tag's declared size DOES bound the region, so it is stepped "
            "over exactly and costs no synchronisation, and that THE INTERIOR "
            "is what is unmeasured. That is what this code names. What would "
            "settle it is a control against the interior framing",
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

#: The one inner word whose element is a NESTED property tag list, closed by
#: the same terminator name a payload uses. Its interior is CS-829's.
_ELEMENT_TAG_LIST_WORD: Final = "StructProperty"

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
            "final byte. It is UNIVERSAL ACROSS THE THREE PAIRS THIS GRAMMAR "
            "READS - not one of their payloads ends at its terminator - while "
            "(14,60) reaches no terminator at all, so it has no such run and is "
            "scoped out of CS-828 and into CS-G05. Its width is 4 on the large "
            "majority and "
            "variable above that, spanning 4 to 5008 bytes on the (10,36) and "
            "(13,42) pairs and 4 to 1053802 on (14,52), across roughly 235 "
            "distinct widths per pair. A 4-byte floor holding on every payload "
            "of those three pairs is the one regularity - (14,60) has no such "
            "run at all; whether it is one field or "
            "the head of a longer structure is NOT claimed, and no reading of "
            "its interior is offered. This is the region that keeps the PROPERTY "
            "walk terminator-exact rather than boundary-exact. The BODY walk is "
            "boundary-exact and is a different question - conflating the two put a "
            "false sentence in a tracked file on 2026-08-23"
        ),
        "StructProperty": (
            "45208 instances, the largest opaque region by count. The tag's "
            "declared size DOES bound it, so it is stepped over exactly and "
            "costs no synchronisation - the interior is what is unmeasured. "
            "The struct's own type word is present in the tag and the observed "
            "vocabulary is led by FactoryCustomizationData, InventoryStack, "
            "Box and LinearColor. InventoryStack is NOT reachable from a "
            "building directly - measured 2026-08-23, no building record "
            "carries one; a building holds an ObjectProperty reference to an "
            "inventory component and the stacks sit there inside an array. So "
            "the chain is CS-831, then CS-830, then this region. TWO OF THE "
            "THREE HAVE LANDED AND THIS ONE HAS NOT, which changes what is "
            "opaque without changing that it is opaque: CS-830 now BOUNDS a "
            "struct element inside a container, carries out the inner tag's own "
            "struct word, and reads nothing between those bounds. So the region "
            "is smaller and better addressed than it was, and every byte of it "
            "is still unmeasured"
        ),
        "TextProperty": (
            "10 instances, all of declared size 45. Unreal's text serialization "
            "is a tagged union over history types and 10 instances of one size "
            "cannot distinguish its cases"
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


def _element_tag_list_end(body: bytes, at: int, end: int) -> int | None:
    """Walk one NESTED property tag list and report where it closes.

    An element of a struct is a tag list closed by the same terminator name a
    payload uses. NOTHING INSIDE IT IS DECODED HERE - the walk reads each tag's
    header only, to step by its declared size. The interior is CS-829's, and
    reading a value out of it would be exactly the guess this decode declines.

    Args:
        body: The decompressed body.
        at: Where the first nested tag begins.
        end: The first byte past the element region.

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
        tag = _read_tag_header(body, name[1], end)
        if tag is None:
            return None
        _word, value_at, size, _in_tag_byte = tag
        cursor = value_at + size
    return None


def _element_half_end(body: bytes, word: str, at: int, end: int, width: int | None) -> int | None:
    """Where one element half ends, by its own grammar or by a forced width.

    Args:
        body: The decompressed body.
        word: The element half's type word.
        at: The half's first byte.
        end: The first byte past the element region.
        width: A forced raw width, or None to use the word's own grammar.

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
        return _element_tag_list_end(body, at, end)
    return None


def _walk_elements(
    body: bytes,
    words: tuple[str, ...],
    at: int,
    end: int,
    count: int,
    widths: tuple[int | None, ...],
) -> tuple[ContainerElement, ...] | None:
    """Bound every element half, refusing anything that does not close exactly.

    THE EXACT CLOSE IS THE WHOLE DISCRIMINATOR. Returning what could be read
    would make the acceptance equality hold by construction on any framing at
    all, which is why a short or an overrunning walk yields None rather than a
    truncated list.

    Args:
        body: The decompressed body.
        words: The element type words, one per half of an entry.
        at: Where the first element begins.
        end: The first byte past the element region.
        count: How many entries the container declared.
        widths: A forced width per half, each None to use that word's grammar.

    Returns:
        One entry per element half in byte order, or None when the halves do
        not consume the region exactly.
    """
    cursor = at
    found: list[ContainerElement] = []
    for _ in range(count):
        for position, word in enumerate(words):
            step = _element_half_end(body, word, cursor, end, widths[position])
            if step is None:
                return None
            found.append(
                ContainerElement(
                    type_word=word,
                    start=cursor,
                    length=step - cursor,
                    value=_decode_element_value(body, word, cursor, step),
                )
            )
            cursor = step
    return tuple(found) if cursor == end else None


def _decode_element_value(body: bytes, word: str, at: int, end: int) -> object | None:
    """Decode one element's value, or refuse to.

    IT REFUSES FOR A TYPE WHOSE TOP-LEVEL VALUE THIS MODULE DOES NOT DECODE,
    which is why a struct element and an `InterfaceProperty` element come back
    bounded and unread. Bounding an element is a claim about the CONTAINER's
    framing; reading it is a claim about that type's own encoding, and CS-830
    earns only the first.

    Args:
        body: The decompressed body.
        word: The element's type word.
        at: The element's first byte.
        end: The first byte past the element.

    Returns:
        The value, or None when the element's type is not decoded here.
    """
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


def _bound_container_elements(
    body: bytes, words: tuple[str, ...], at: int, end: int, count: int
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

    Returns:
        The shape that bounded them and the elements, or None when none did.
    """
    blank: tuple[int | None, ...] = (None,) * len(words)
    found = _walk_elements(body, words, at, end, count, blank)
    if found is not None:
        return (ELEMENT_SHAPE_SELF_DELIMITING, found)

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
        found = _walk_elements(body, words, at, end, count, (width,) * len(words))
        if found is not None:
            return (ELEMENT_SHAPE_UNIFORM_WIDTH, found)

    # ONE HALF'S WIDTH SOLVED, THE REST BY THEIR OWN GRAMMAR. Admitted only
    # when exactly one width closes the region: two would mean the width is not
    # determined by the bytes, and a decoder that picked one would be fitting.
    for position in range(len(words)):
        solutions: list[tuple[ContainerElement, ...]] = []
        for width in range(_SOLVED_WIDTH_CAP + 1):
            forced: list[int | None] = [None] * len(words)
            forced[position] = width
            found = _walk_elements(body, words, at, end, count, tuple(forced))
            if found is not None:
                solutions.append(found)
                if len(solutions) > 1:
                    break
        if len(solutions) == 1:
            return (ELEMENT_SHAPE_SOLVED_WIDTH, solutions[0])
    return None


def _read_array_struct_tag(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """Read the inner tag an array of struct carries ahead of its elements.

    An array of ``StructProperty`` writes ONE tag naming the struct and
    declaring the extent of the WHOLE element region, then the elements. The
    struct word is carried out because it is what CS-829 needs; the extent is
    checked against the value's own end rather than trusted.

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
    body: bytes, type_word: str, element_words: tuple[str, ...], at: int, size: int
) -> ContainerValue | None:
    """Decode one container tag's element framing - CS-830.

    NONE MEANS THE FRAMING DID NOT CLOSE, and the caller decides what that
    means: a container whose element word has no grammar at all is UNMODELLED
    CONTENT, where one this module can bound whose bytes then disagree is a walk
    that has lost its place. :func:`_walk_payload` separates the two rather than
    collapsing them, because they mean opposite things.

    Args:
        body: The decompressed body.
        type_word: The container's type word.
        element_words: The element type words its tag carried.
        at: The value's first byte.
        size: The value's declared extent.

    Returns:
        The container, or None when the elements do not consume the declared
        size exactly.
    """
    opened = _open_container(body, type_word, element_words, at, size)
    if opened is None:
        return None
    count, cursor, end = opened

    struct_word: str | None = None
    if type_word == "ArrayProperty" and element_words == (_ELEMENT_TAG_LIST_WORD,):
        inner = _read_array_struct_tag(body, cursor, end)
        if inner is None:
            return None
        struct_word, cursor = inner

    bounded = _bound_container_elements(body, element_words, cursor, end, count)
    if bounded is None:
        return None
    shape, elements = bounded
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


def _refusal_is_unmodelled_content(type_word: str, element_words: tuple[str, ...]) -> bool:
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

    Args:
        type_word: The tag's type word.
        element_words: The element type words a container's tag carried, empty
            for every other type.

    Returns:
        Whether the refusal is unmodelled content rather than a lost walk.
    """
    if type_word in CONTAINER_TYPE_WORDS:
        return not _container_grammar_is_modelled(element_words)
    return type_word not in MEASURED_VALUE_TYPES


def _decode_value(
    body: bytes,
    type_word: str,
    at: int,
    size: int,
    in_tag_byte: int | None,
    element_words: tuple[str, ...] = (),
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

    Returns:
        The decoded value, or None when the type is unmeasured or the bytes
        disagree with the declaration.
    """
    if type_word in CONTAINER_TYPE_WORDS:
        return _decode_container(body, type_word, element_words, at, size)
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
    """

    properties: dict[str, object]
    unmeasured: int
    disagreed: int
    terminated: bool
    references: tuple[ObjectReference, ...]
    reference_tags: int
    undecoded_references: int

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
            f"undecoded_references={self.undecoded_references})"
        )


def _walk_payload(body: bytes, at: int, end: int) -> _PayloadWalk | None:
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

    Returns:
        What the walk observed, or None when it broke before its terminator.
    """
    decoded: dict[str, object] = {}
    references: list[ObjectReference] = []
    unmeasured = 0
    disagreed = 0
    reference_tags = 0
    undecoded_references = 0
    for _ in range(_MAX_TAGS_PER_PAYLOAD):
        name = _payload_text(body, at, end)
        if name is None:
            return None
        if name[0] == _PAYLOAD_TERMINATOR:
            return _PayloadWalk(
                properties=decoded,
                unmeasured=unmeasured,
                disagreed=disagreed,
                terminated=True,
                references=tuple(references),
                reference_tags=reference_tags,
                undecoded_references=undecoded_references,
            )
        tag = _read_tag_header(body, name[1], end)
        if tag is None:
            return None
        type_word, value_start, size, in_tag_byte = tag
        # THE ELEMENT WORDS ARE READ HERE BECAUSE HERE IS WHERE THE OFFSET
        # STILL EXISTS - CS-830. They sit inside the tag, between the index
        # field and the guid flag, and `_read_tag_header` steps over them
        # without handing them back. Widening its return shape in place is how
        # a caller starts unpacking the wrong element in silence, so they are
        # re-read from the name offset this loop already holds.
        element_words: tuple[str, ...] = ()
        if type_word in CONTAINER_TYPE_WORDS:
            read_words = _container_element_words(body, name[1], end, type_word)
            if read_words is None:
                return None
            element_words = read_words
        value = _decode_value(body, type_word, value_start, size, in_tag_byte, element_words)
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
        if value is not None:
            decoded[name[0]] = value
        elif _refusal_is_unmodelled_content(type_word, element_words):
            unmeasured += 1
        else:
            disagreed += 1
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


def read_properties(body: bytes, record: ObjectRecord, property_map: PropertyMap) -> PropertyResult:
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
        property_map: The parsed mapping. Non-optional: handling the
            no-install None is the world layer's job, not this one's.

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
    resolved = name in property_map.schemas
    schema_warnings: tuple[ObjectWarning, ...] = (
        () if resolved else (_warning(WARN_UNRESOLVED_SCHEMA, record.body_offset),)
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
    walked = None if start is None else _walk_payload(body, start, end)
    if walked is None:
        # The payload does not read under the measured grammar at all - which
        # is every payload of the (14,60) pair. Flagged exactly as before, so
        # nothing this slice added changed what that pair reports.
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
        "INT32_SIZE",
        "KIND_ACTOR",
        "MAX_OBJECTS",
        "MAX_STRING_BYTES",
        "MEASURED_VALUE_TYPES",
        "ObjectReference",
        "REFERENCE_TYPE_WORD",
        "UTF16_CHAR_SIZE",
        "_CONTAINER_LEAD_FIELDS",
        "_ELEMENT_FIXED_WIDTHS",
        "_ELEMENT_STRING_COUNTS",
        "_ELEMENT_TAG_LIST_WORD",
        "_FIXED_WIDTH_VALUES",
        "_MAX_CONTAINER_ELEMENTS",
        "_MAX_ELEMENT_TAGS",
        "_MAX_TAGS_PER_PAYLOAD",
        "_ONE_STRING_VALUES",
        "_PAYLOAD_TERMINATOR",
        "_RAW_SHAPE_ELEMENT_WORDS",
        "_REFERENCE_PARTS",
        "_SOFT_OBJECT_TAIL_BYTES",
        "_SOLVED_WIDTH_CAP",
        "_TAG_EXTRA_STRINGS",
        "_TAG_INDEX_FIELD_BYTES",
        "_TWO_STRING_VALUES",
        "_as_reference",
        "_bound_container_elements",
        "_decode_container",
        "_decode_element_value",
        "_decode_fixed_width",
        "_decode_object_reference",
        "_decode_text_value",
        "_decode_value",
        "_element_half_end",
        "_element_tag_list_end",
        "_open_container",
        "_payload_text",
        "_read_array_struct_tag",
        "_read_tag_header",
        "_skip_actor_head",
        "_skip_guid_flag",
        "_skip_tag_extra",
        "_walk_elements",
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
    body: bytes, record: ObjectRecord, property_map: PropertyMap
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
        property_map: The parsed mapping.

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
        return read_properties(body, record, property_map).properties
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
