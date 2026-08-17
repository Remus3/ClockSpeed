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
   as closed. The walk is TERMINATOR-exact and NOT boundary-exact: a variable
   trailing run follows the property terminator on every payload in the
   library, and it is the ``trailing_run`` entry of that table. And the
   (14,60) pair reads under this grammar on NO payload at all, so it reports
   exactly what it reported before any of this landed.

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
    "BYTE_ORDER_STATUSES",
    "BYTE_ORDER_SURVIVING_CANDIDATES",
    "BYTE_ORDER_UNSCORED",
    "BYTE_ORDER_VACUOUS",
    "CRITERION_CURSOR_REACH",
    "CRITERION_VALUE_DISAGREEMENT",
    "CURSOR_WIDTHS",
    "DECLINED_VALUE_READINGS",
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
    "MAX_OBJECTS",
    "MAX_OBJECT_DATA_BYTES",
    "MAX_STRING_BYTES",
    "MEASURED_BODY_LAYOUTS",
    "MEASURED_HEADER_VERSIONS",
    "MEASURED_VALUE_TYPES",
    "REASON_NO_DISCRIMINATION_TEST",
    "REASON_SAMPLE_SIZE",
    "REASON_SHIPPED_ALIGNMENT_ONLY",
    "TRANSFORM_BYTES",
    "TRANSFORM_DELTA_BY_SAVE_VERSION",
    "TRANSFORM_FLOAT_COUNT",
    "UNKNOWN_CLASS_REASONS",
    "UNMEASURED_PAYLOAD_REGIONS",
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
    "ObjectBudgetExceededError",
    "ObjectError",
    "ObjectFormatError",
    "ObjectRecord",
    "ObjectTable",
    "ObjectTruncatedError",
    "ObjectWarning",
    "PropertyResult",
    "Transform",
    "UnknownClass",
    "UnsupportedBodyLayoutError",
    "UnsupportedSaveVersionError",
    "class_name_of",
    "parse_body",
    "parse_object_headers",
    "parse_properties",
    "read_properties",
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

#: A named level closes on 12 constant bytes and then a package summary.
LEVEL_TAIL_SUMMARY: Final = "summary"

#: CONSTANT BLOBS, SKIPPED BY LENGTH, exactly as BOOTSTRAP.md already does for
#: the 28-byte header tail. NO INTERIOR BOUNDARY IN ANY OF THESE IS OBSERVABLE,
#: so none is claimed and none is decoded.
#:
#: The 70-byte run is the sharpest case rather than the laziest: every
#: candidate split was searched and none is supported - not 4+6, not 8+2, not
#: 16+10. Every head int32 has exactly one distinct value across the corpus and
#: the trailing run has one, so the interior is UNFALSIFIABLE, not merely
#: unmeasured. What IS pinned is the pair (70, 20): the count's position at +70
#: and the 20-byte entry width are the unique survivors of a brute-force search
#: over F in [0,84) x K in [1,256], robust to three plausibility caps and
#: over-determined by four distinct counts against four distinct widths.
_PACKAGE_SUMMARY_HEAD_BYTES: Final = 70
_CUSTOM_VERSION_ENTRY_BYTES: Final = 20
_LEVEL_TAIL_CONSTANT_BYTES: Final = 12
_GRID_OPAQUE_BYTES: Final = 8
_GRID_CELL_OPAQUE_BYTES: Final = 4
_COMPONENT_PRE_WORD_BYTES: Final = 4

#: Ceiling on a declared grid or custom-version count, applied before any loop.
MAX_GRIDS: Final = 1 << 12
MAX_CUSTOM_VERSIONS: Final = 1 << 12


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
    """

    properties: Mapping[str, object]
    schema_name: str
    resolved: bool
    warnings: tuple[ObjectWarning, ...]
    unmeasured_value_count: int = 0
    disagreeing_value_count: int = 0

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
            f"disagreeing_value_count={self.disagreeing_value_count})"
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

    A 70-BYTE CONSTANT RUN, A COUNT, THEN THAT MANY 20-BYTE ENTRIES. The run is
    skipped by LENGTH because no interior boundary in it is observable - not
    4+6, not 8+2, not 16+10 - which makes its interior unfalsifiable rather than
    merely unmeasured. ``BOOTSTRAP.md`` already takes exactly this approach to
    the 28-byte header tail.

    The count's position at +70 and the 20-byte entry width ARE pinned, as the
    unique survivors of a brute-force search over offsets and widths.

    Args:
        cursor: Positioned at the summary.

    Raises:
        ObjectBudgetExceededError: The declared count exceeds its ceiling.
        ObjectTruncatedError: The summary runs past the body.
    """
    cursor.skip(_PACKAGE_SUMMARY_HEAD_BYTES, "package_summary")
    count = _read_bounded_count(cursor, "custom_version_count", MAX_CUSTOM_VERSIONS)
    cursor.skip(count * _CUSTOM_VERSION_ENTRY_BYTES, "custom_version")


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
            cursor.skip(_LEVEL_TAIL_CONSTANT_BYTES, "level_tail")
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
#   parsed by a different pass over a different section. The references that do
#   not resolve name assets rather than saved objects, which is why that oracle
#   is reported as a rate and never as a total. The count that stood here is
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
#: reaches its terminator on every payload of every real save of a measured
#: pair.
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
#: which end a value starts at. The pair of byte-order oracles cited in the
#: commentary block above score the real population's magnitudes under both
#: readings; each is proven by a mutant that flips one entry's order, and
#: neither can be satisfied by a fixture this project packs, because both read
#: the game's own saves. What they leave standing is a CANDIDATE SET rather than
#: one order. Which question each entry actually poses now ships as data - see
#: :data:`VALUE_BYTE_ORDER_STATUS` - and the permutations those oracles cannot
#: separate ship as :data:`BYTE_ORDER_SURVIVING_CANDIDATES`.
#:
#: The figures those oracles compute are deliberately NOT restated here. An
#: earlier revision of this comment carried four of them and claimed the
#: encoding was measured while nothing executable checked it; one pair did not
#: reproduce, because the predicate behind the percentage was written down
#: nowhere. Read the counts off a run of the tests instead - and note that the
#: two remaining entries below carry no such oracle, which is recorded in
#: :data:`WIDTH_ONLY_VALUE_TYPES` rather than in a sentence.
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

#: Value types that are a level reference followed by an object path.
_TWO_STRING_VALUES: Final = frozenset({"ObjectProperty", "SoftObjectProperty"})

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
#   THE SURVIVING CANDIDATES are the permutations the shipped VALUE oracles
#   leave standing beside the identity.
#   tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_
#   is_what_the_value_oracles_cannot_separate derives the set from those oracles
#   at runtime and compares it with the shipped literal, and
#   tests/save/test_value_anchoring.py::test_the_declared_size_field_is_
#   read_in_exactly_one_of_its_twenty_four_byte_orders is the DIFFERENT-FIELD
#   result whose boundary is written down beside that literal.
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
#: because one type word can carry both. `ArrayProperty` appears here AND in
#: :data:`CURSOR_WIDTHS`: its tag-extra width ships and is discriminated, while
#: its VALUE reading is declined. Keying this by the bare type word once read as
#: though the whole word were declined, which is why the distinction is stated
#: rather than left to the name.
DECLINED_VALUE_READINGS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "ArrayProperty": (
            REASON_SHIPPED_ALIGNMENT_ONLY,
            "consumes its declared size exactly on the arrays whose inner word "
            "this module measures - the ArrayProperty entry of "
            "UNMEASURED_PAYLOAD_REGIONS owns that population - but at the "
            "SHIPPED ALIGNMENT ONLY, never under a rotation - which is what "
            "that entry records and where this code comes from. Consumption at "
            "one alignment is not discrimination, so the rule declines it. What "
            "would settle it is a control showing a wrong reading costs "
            "something, not a larger sample",
        ),
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
        "SetProperty": (
            REASON_SAMPLE_SIZE,
            "declined on SAMPLE SIZE, so an exception to the rule rather than "
            "an application of it. It poses the element-framing question "
            "ArrayProperty poses, over a population the SetProperty entry of "
            "UNMEASURED_PAYLOAD_REGIONS owns and records as far too small to "
            "separate the answers - which is where this code comes from",
        ),
        "MapProperty": (
            REASON_NO_DISCRIMINATION_TEST,
            "declined because no discrimination test has been put to it, which "
            "is a reason the rule does not admit, so this is an exception to "
            "the rule rather than an application of it. SAMPLE SIZE IS NOT THE "
            "OBJECTION HERE: the MapProperty entry of UNMEASURED_PAYLOAD_REGIONS "
            "records the tag carrying two extra type words rather than one as "
            "MEASURED and the key and value element framing as not, and says "
            "nothing about the population being too small. Recording it under "
            "sample size would read as a measurement of a population that no "
            "one has taken",
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
BYTE_ORDER_STATUSES: Final = frozenset(
    {BYTE_ORDER_VACUOUS, BYTE_ORDER_ANCHORED_NOT_UNIQUE, BYTE_ORDER_UNSCORED}
)

#: A value of this width has one byte order, so its order is not open. Named
#: rather than written as a literal in :func:`_byte_order_status`, so the reason
#: travels with the number.
_SINGLE_BYTE_WIDTH: Final = 1

#: The fixed-width types a shipped byte-order oracle actually scores. Both
#: oracles are cited in the commentary block above ``_TAG_EXTRA_STRINGS``. A
#: type outside this set and wider than one byte has been scored by nothing,
#: which is what :data:`BYTE_ORDER_UNSCORED` records.
_BYTE_ORDER_ANCHORED_VALUES: Final = frozenset({"IntProperty", "FloatProperty"})


def _byte_order_status(word: str, width: int) -> str:
    """Classify one fixed-width value type's byte-order question.

    VACUITY IS COMPUTED FROM THE SHIPPED WIDTH RATHER THAN LISTED. If a type's
    measured width ever changes from one byte to more, this stops calling its
    byte order vacuous on the same edit that changes the width, instead of
    waiting for someone to remember a sentence elsewhere.

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
    return BYTE_ORDER_UNSCORED


#: The status per value type, over the fixed-width scalars this module reads.
#:
#: ANCHORED IS NOT UNIQUE, and the status word says so. An oracle that scores
#: the population under the shipped reading and under the reversed one rules the
#: reversal out. It does not rule out every other rearrangement of the same
#: bytes - see :data:`BYTE_ORDER_SURVIVING_CANDIDATES` for what it leaves.
#:
#: ``BoolProperty`` IS WRITTEN IN EXPLICITLY BECAUSE ITS BYTE IS NOT IN
#: ``_FIXED_WIDTH_VALUES``. Its value byte rides in the TAG - :func:`_read_tag_header`
#: takes it as a single byte at a fixed offset and hands it back separately - so
#: there is no entry in that table to derive a width from. It is one byte, so
#: its byte order is vacuous for the same reason the derived members are.
VALUE_BYTE_ORDER_STATUS: Final[Mapping[str, str]] = MappingProxyType(
    {
        **{
            word: _byte_order_status(word, width)
            for word, (width, _) in _FIXED_WIDTH_VALUES.items()
        },
        "BoolProperty": BYTE_ORDER_VACUOUS,
    }
)

#: THE BYTE PERMUTATIONS THE SHIPPED VALUE ORACLES CANNOT SEPARATE FROM THE
#: IDENTITY. Each tuple is a permutation of STORED byte positions, and the
#: identity is a member - which is the point. A candidate set holding only the
#: identity would mean the order was pinned, and it is not.
#:
#: WHAT BOUNDS THE SET IS THAT EACH ORACLE CONSTRAINS ONE END ONLY, AND THE
#: SURVIVORS ARE THE INTERSECTION OF THE TWO. NEITHER ORACLE TURNS ON BOTH
#: EXTREMES, and reading it that way gets the mechanism backwards. Measured: the
#: int32 oracle holds exactly for the orderings that leave the LOW position
#: alone, and it survives orderings that MOVE the most significant byte - so it
#: does not by itself rule out a high-end swap. The float32 oracle holds exactly
#: for the orderings that leave the HIGH position alone, and it survives
#: orderings that move the low byte. Only intersecting the two one-ended
#: constraints fixes both ends, and that intersection is what this set is.
#:
#: THE OBSTACLE IS THE ORACLE, NOT THE DATA, and it is worth being exact about
#: which. The library's float32 values overwhelmingly DO have differing middle
#: bytes, so the corpus carries the information that would separate the two
#: survivors. What cannot use it is the shipped float oracle's magnitude band,
#: which is wide enough to admit both readings. A narrower discriminator over
#: the same saves is what would settle this - not more saves.
#:
#: The set is DERIVED FROM THE ORACLES at runtime by the test named in the
#: commentary block above and compared against this literal, so the literal
#: cannot quietly stop describing what they do.
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
        (0, 2, 1, 3),
    }
)

#: The type words whose VALUE encoding is measured and is therefore decoded.
#: EVERY OTHER TYPE IS FLAGGED AND SKIPPED - non-negotiable 7 - and the ones
#: seen in the library are recorded in :data:`UNMEASURED_PAYLOAD_REGIONS`
#: rather than guessed at from a neighbouring type's shape.
MEASURED_VALUE_TYPES: Final = (
    frozenset(_FIXED_WIDTH_VALUES)
    | _ONE_STRING_VALUES
    | _TWO_STRING_VALUES
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
        "BoolProperty": frozenset({EVIDENCE_DECLARED_WIDTH}),
        "ByteProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "EnumProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "FloatProperty": frozenset({EVIDENCE_DECLARED_WIDTH, EVIDENCE_MAGNITUDE}),
        "Int8Property": frozenset({EVIDENCE_DECLARED_WIDTH}),
        "IntProperty": frozenset({EVIDENCE_DECLARED_WIDTH, EVIDENCE_MAGNITUDE}),
        "NameProperty": frozenset({EVIDENCE_REDUNDANCY}),
        "ObjectProperty": frozenset({EVIDENCE_REDUNDANCY, EVIDENCE_CROSS_SECTION}),
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
            "final byte. It is UNIVERSAL - not one payload in the library ends "
            "at its terminator - and its width is 4 on the large majority and "
            "variable above that, spanning 4 to 5008 bytes on the (10,36) and "
            "(13,42) pairs and 4 to 1053802 on (14,52), across roughly 235 "
            "distinct widths per pair. A 4-byte floor holding on every payload "
            "of every pair is the one regularity; whether it is one field or "
            "the head of a longer structure is NOT claimed, and no reading of "
            "its interior is offered. This is the region that keeps the walk "
            "terminator-exact rather than boundary-exact"
        ),
        "StructProperty": (
            "45208 instances, the largest opaque region by count. The tag's "
            "declared size DOES bound it, so it is stepped over exactly and "
            "costs no synchronisation - the interior is what is unmeasured. "
            "The struct's own type word is present in the tag and the observed "
            "vocabulary is led by FactoryCustomizationData, InventoryStack, "
            "Box and LinearColor. InventoryStack is the one pillar 3 needs "
            "for inventory, so it is the natural next measurement"
        ),
        "ArrayProperty": (
            "31983 instances. NOT decoded here, and the reason is that the "
            "evidence is weaker than for the scalars rather than absent: an "
            "int32 count followed by elements consumes the declared size "
            "exactly on all 11976 arrays whose inner type word is IntProperty, "
            "Int64Property, ObjectProperty or SoftObjectProperty, but that was "
            "measured at the shipped alignment ONLY and never put through the "
            "rotation control the scalar types survived. THREE OF THOSE FOUR "
            "WORDS ARE IN MEASURED_VALUE_TYPES AND Int64Property IS NOT, which "
            "is why it has its own entry below rather than being described here "
            "as measured - it was the one word this module named and placed in "
            "neither half of its own classification. The remaining 20007 are "
            "chiefly arrays of StructProperty, whose element framing carries an "
            "inner tag header this project has not measured"
        ),
        "Int64Property": (
            "NAMED BY THE ArrayProperty ENTRY ABOVE as an array inner type, and "
            "recorded here so that every type word this table mentions sits on "
            "one side of the measured/unmeasured split rather than in neither. "
            "Nothing about its VALUE encoding is claimed: not a width, not a "
            "byte order, not an instance count. It is decoded nowhere - not at "
            "top level, and not inside an array, since arrays are not decoded "
            "at all - so a top-level instance is flagged and skipped like any "
            "other unmeasured type. How often one occurs is deliberately not "
            "stated, because nothing here has measured that either"
        ),
        "SetProperty": (
            "81 instances. Same framing question as ArrayProperty and a sample "
            "far too small to separate the answers"
        ),
        "MapProperty": (
            "72 instances. The tag carries TWO extra type words rather than "
            "one, which is measured, and the key/value element framing is not"
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


def _decode_value(
    body: bytes, type_word: str, at: int, size: int, in_tag_byte: int | None
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

    Returns:
        The decoded value, or None when the type is unmeasured or the bytes
        disagree with the declaration.
    """
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
    decoded: dict[str, object] = {}
    unmeasured = 0
    disagreed = 0
    for _ in range(_MAX_TAGS_PER_PAYLOAD):
        name = _payload_text(body, at, end)
        if name is None:
            return None
        if name[0] == "None":
            return (decoded, unmeasured, disagreed, True)
        tag = _read_tag_header(body, name[1], end)
        if tag is None:
            return None
        type_word, value_start, size, in_tag_byte = tag
        value = _decode_value(body, type_word, value_start, size, in_tag_byte)
        if value is not None:
            decoded[name[0]] = value
        elif type_word in MEASURED_VALUE_TYPES:
            disagreed += 1
        else:
            unmeasured += 1
        at = value_start + size
    return None


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
    walked = None if start is None else _decode_payload(body, start, end)
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

    decoded, unmeasured, disagreed, _terminated = walked
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
