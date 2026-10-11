"""The world-state model, and the one entry point that produces it.

WHAT THIS MODULE OWNS
-----------------------
``docs/ARCHITECTURE.md`` section 1.1: **the world model is the only save-layer
type any higher layer is allowed to hold.** ``audit/`` and ``progress/`` consume
it; nothing above this layer sees save bytes, a chunk frame or a property map.

It owns one more thing that nothing else can own: **the two version scalars.**
``chunks.decompress_body`` discards both the header version and the save
version, and every reader in ``objects`` needs both. This module is the only
place that holds them at once, so threading them is not plumbing - it is the
seam, and getting it wrong is the defect the corpus was built to catch.

THE COMPOSITION, IN ORDER
---------------------------
``workdir.copy_for_read`` -> ``header.parse_header`` -> ``chunks.decompress_body``
-> ``usmap.cached_usmap`` -> ``objects.parse_body`` -> ``objects.read_properties``
once per walked record -> :class:`WorldModel`.

Nothing here re-implements any of them. Each sibling was proven separately and
this module is deliberately thin: every byte-level decision lives one layer
down, where it has its own fixtures and its own error taxonomy.

TWO DISPATCHES, THREADED SEPARATELY AND NEVER DERIVED
-------------------------------------------------------
The body length prefix width follows the HEADER version; the transform delta
follows the SAVE version. Across the entire real library the two covary, so a
composer that read one scalar and derived the other is correct on every real
file and on every real-shaped fixture. Both are passed through explicitly, and
``tests/save/test_world.py::test_save_cross_proves_the_composer_threads_both_scalars``
asserts the PAIR against ``synthetic.SAVE_CROSS``, whose pair occurs in no real
file and which is therefore the only fixture that can separate them.

AN ABSENT PROPERTY MAP IS THE DEFAULT PATH, NOT AN EDGE CASE
--------------------------------------------------------------
``usmap.cached_usmap()`` returns None on a machine with no install and NEVER
raises for absence. CI and every fresh clone run in exactly that state, so the
None branch is the common one. It is recorded as a warning and the load
continues with no property map: ``objects.parse_object_headers`` takes
``known_classes=None`` to mean "no registry was supplied", and a walk that
flagged every class in that state would report a world of pure unknown content
rather than a world it has not checked.

EITHER PROPERTY READER ACCEPTS None, and neither used to (CS-960). While the
map was mandatory, a composer that called the reader unconditionally broke on
every machine that had never had the game installed, and that trap is now
gone: the mapping was never an input to the decode, so an absent one costs the
resolution report and nothing else. **That removal is what lets this module
call a reader at all** (CS-961). The no-install path is the COMMON one, so a
decode that needed a registry would decode nothing in CI, on a fresh clone, or
on any machine that has never had the game - which is not a reduced capability
but an absent one.

WHAT EITHER PROPERTY READER CAN DECODE IS ``objects``' FACT, and it is stated
at ``objects.read_properties`` rather than a second time here. A capability
restated in a second module is one that goes stale in the second module, which
is precisely what happened to this paragraph: it named a reason - the data
section's grammar - that had since been measured, while the conclusion it was
attached to stayed true and kept the whole sentence reading as current.

WHAT THIS MODULE STATES IS NARROWER AND IS ITS OWN, and under CS-961 it became
a POSITIVE claim where it had been an absence. Decoded property values reach
:class:`WorldModel` through :class:`WorldProperties` and one
:class:`RecordProperties` per walked record - and through nothing else. The
capability is bounded on four sides, each of them mechanical rather than a
matter of review:

- THE READER IS ``objects.read_properties``, NEVER ``objects.parse_properties``.
  The second is the DISCARDING accessor: it throws away ``resolved`` and the
  per-record warnings, and both are things this model publishes, so reaching
  for it would be a defect rather than a style choice.
  ``tests/save/test_world.py::test_the_world_layer_states_no_property_capability_it_does_not_own``
  binds that pair from the AST.
- THE KEY IS A RECORD INDEX, NEVER A BYTE OFFSET. An offset is a position in
  bytes this layer promised nothing above it would ever see, so publishing one
  is the reach-past-your-neighbour the seam discipline forbids; an index into
  ``WorldModel.objects.records`` is a position in a collection the consumer
  already holds. ``ObjectRecord.body_offset`` and ``body_length`` STAY WHERE
  THEY ARE - they are diagnostics this package reads and publishes to nobody.
  The one FACT a higher layer needs from them - whether the walk paired a
  record with any payload at all - crosses as
  :attr:`RecordProperties.payload_present`, a boolean, never as the length
  (CS-1266).

  **THAT RULE IS ABOUT EVERY REACHABLE VALUE, NOT ONLY THE KEY**, and the first
  version of this module obeyed it at the key and broke it three levels down.
  ``read_properties`` decodes an array, a set or a map to an
  ``objects.ContainerValue`` whose ``elements`` carry ``start`` - an absolute
  offset into the decompressed body - and those went out verbatim inside
  ``RecordProperties.values``. Neither decodable fixture produced a container,
  so no arm had one to look at. THE REPAIR IS A PUBLISHED CONTAINER TYPE WITH NO
  POSITION IN IT: :class:`ContainerContents` and :class:`ContainerEntry` carry
  the element type word, its extent and its value, and an entry's place among
  its siblings is its index in a tuple the consumer holds. Nothing is dropped -
  a container published short of its elements would make present world content
  read as absent, which non-negotiable 7 forbids. The narrowing is recursive,
  because a container can sit inside a struct interior, and it is graded
  STRUCTURALLY rather than by a list of known types:
  ``tests/save/test_world.py::test_no_published_property_value_carries_an_absolute_body_offset``
  walks everything reachable from ``WorldModel.properties`` and asserts no
  integer lands inside the record's own payload extent, with the raw reader
  result as the control that the walk can see one when it is there.
- THE DECODE IS EAGER, AND THE PAYLOAD DIES WITH THE WALK. A lazy entry would
  have to retain the decompressed body, which is the one thing no type any
  higher layer holds may carry - so neither new type declares a ``bytes`` or a
  ``Path`` field, asserted against the shipped-tree guard's own carrier set by
  ``tests/save/test_world.py::test_no_published_world_type_annotates_a_carrier_field``.
- WHAT IS DECODED IS AN ECHO PATH IN BOTH HALVES. Property NAMES are read out
  of the save's own bytes and VALUES are player-authored, so non-negotiable 12
  covers the whole entry. Both new types hand-write a ``repr`` rendering counts
  and flags and no string at all, on the terms ``objects.PropertyResult``
  already set, and
  ``tests/save/test_world.py::test_no_body_byte_reaches_any_echo_path`` sweeps
  six channels for a marker planted in the payload.

  THAT SWEEP MEASURES THE DECODED VALUE AND NOT THE FILE, and the two are
  different channels. Its marker is deflated into the blob, so it can never
  appear in the RAW save - which is what :func:`load_world_from_bytes` takes as
  a parameter and what its own frame held on every raise path until CS-961.
  ``tests/save/test_world.py::test_no_clockspeed_frame_holds_the_raw_save_on_any_refusal_path``
  plants a second marker in the plaintext header and grades THIS LAYER'S OWN
  FRAMES. The CAUSE CHAIN is not covered and still leaks the raw save out of
  ``header`` and ``chunks``; that is CS-963, measured and filed, not fixed here.

WHAT AN ENTRY MAY NOT DO IS READ AS "NOT SET" (non-negotiable 7). Every walked
record gets an entry, and an entry whose payload did not read under the measured
grammar says so through ``payload_read`` and carries
``objects.WARN_UNPARSED_PROPERTY_PAYLOAD``, rather than publishing an empty
mapping that a consumer cannot tell from a record holding nothing.

AN OVERRUNNING EXTENT IS NOT THAT CASE AND IS DELIBERATELY FATAL. A record
whose declared payload extent runs past the body is claiming bytes that do not
exist, and ``objects.read_properties`` raises rather than flags for exactly
that reason - reporting it as merely unparsed would let a truncated or
misattributed body pass as a world this project simply does not model. The
extents came out of THIS layer's own walk of THIS body, so an overrun is a
contradiction in the walk rather than content the walk did not understand.
:func:`_decode_properties` therefore runs inside the same guard as the walk and
reaches the caller as a :class:`WorldLoadError` at :data:`STAGE_OBJECTS` with
no new stage and no new taxonomy.

**IT IS ALSO UNREACHABLE FROM HERE BY CONSTRUCTION**, which is a stronger
statement than "no fixture reaches it" and is the reason the branch is kept
rather than deleted. ``objects`` builds each extent as ``(cursor.offset,
length)`` and then skips ``length``, which bounds-checks against the body, so
an extent produced by this walk cannot overrun the body this walk read; and the
flat reader attributes no extent at all. The branch is a guard against that
construction changing one layer down, and the frame scrub behind it is graded
by an arm that injects the overrunning record directly - see
:func:`_decode_properties` for what that arm measures and for the wider claim
it replaced.

A mapping that is PRESENT and unreadable is a different thing entirely and does
raise, because collapsing the two would hide a shipped-format change behind the
same value that means "no install".

UNLOCK STATE IS READ FROM THREE CARRIERS, AND SAYS WHAT IT STILL CANNOT READ
------------------------------------------------------------------------------
ADR 0004 measured WHICH unlock fields exist in a mature world - 246 schematic
paths including the alt-recipe purchases, 360 recipe paths, the game phase, the
research trees, the scanned resources and the feature booleans. ADR 0016 then
measured the SAVE-SIDE carriers and the grammar, and :func:`_read_unlocks` reads
three of them: ``mPurchasedSchematics``, ``mAvailableRecipes`` and
``mCurrentGamePhase``. Everything in :data:`UNLOCK_CARRIERS_UNREAD` is still
unread, which is why :data:`WARN_UNLOCK_GRAMMAR_UNMEASURED` is raised on EVERY
load and not only on an empty one - per non-negotiable 7, a partial reading
reported as complete is the confident wrong answer, and a warning that goes
silent once something was found goes silent exactly on the worlds with the most
still missing.

TWO THINGS THIS READER IS NOT. It does not key on the C++ class that DECLARES a
property - a save carries the blueprint deriving from it, so the keys are
``BP_SchematicManager_C`` and not ``AFGSchematicManager``, and CS-1039's first
cut matched zero records on every real world while every synthetic arm passed.
And it does not treat the phase as an integer: it is an ``ObjectProperty``
naming a ``GP_*`` asset, so :attr:`UnlockState.current_game_phase` is a string.

That is not a placeholder to be quietly filled in by inference. ADR 0004's
single most important engineering consequence is that **an absent unlock array
means EMPTY, never missing and never an error.** A reader that assumes presence
either crashes on a fresh onboarding world or reports a mature world's state for
a new one, and the second failure produces confident wrong advice. An empty
unlock set that says so is correct; a fabricated one is not.

WHICH SAVES THIS CAN ACTUALLY READ - ALL FOUR PAIRS, AS A SKELETON
--------------------------------------------------------------------
**A green test suite here does NOT mean "the save reader reads saves."** Read
this paragraph before believing one. The limit MOVED under CS-407; it did not
go away, and the new one is easier to overlook than the old one.

``load_world`` reads a body whose ``(header version, save version)`` pair is in
``objects.MEASURED_BODY_LAYOUTS``. That set now holds all four pairs the
operator's real library contains, and each walks a real body of its pair to the
exact final byte with nothing left over:

- **header 10** with **save 36**
- **header 13** with **save 42**
- **header 14** with **save 52**
- **header 14** with **save 60**

**WHAT IS MEASURED IS THE SKELETON, NOT THE BODY.** Roughly three quarters of
every real body is opaque property payload this walk steps over by declared
length - 69.5% to 77.7% across the eight real save-52 files, and 12100463 of
18086289 bytes on the one real save-42 file. What the grammar names is a 1.8%
to 2.7% framing skeleton plus its length-prefixed strings. So a record COUNT
out of this module is trustworthy, and a record's PROPERTIES are decoded from
exactly that stepped-over payload, one record at a time and one payload at a
time. Whether any given one READ is therefore a per-record answer rather than a
property of the load, which is why :class:`RecordProperties` carries it.

A pair outside the measured set is still refused EAGERLY with a
:class:`WorldLoadError` whose cause is ``objects.UnsupportedBodyLayoutError``,
before a byte of the body is walked. ``synthetic.SAVE_CROSS`` - header 14 with
save 36 - is such a pair, and deliberately: it occurs in no real file, so no
real body of it can ever be measured, and it is exactly the case where deriving
a layout from a neighbour sharing one version scalar looks reasonable. A layout
guessed that way produces a walk that is confidently WRONG rather than one that
fails, and non-negotiable 7 forbids exactly that: unknown content is flagged
and skipped, never fatal, and NEVER SILENTLY WRONG. An empty or wrong world is
worse than a refusal, because nothing downstream can tell.

CS-407 also measured that a real body is not a flat record table at all: it
opens with a version-dependent preamble and then carries a LIST OF LEVELS, each
with its own record table, collectable list and payload section.

THE BODY LAYOUT IS AN EXPLICIT CHOICE, AND ITS DEFAULT IS THE REAL ONE
------------------------------------------------------------------------
``objects`` exposes two readers, and this module routes between them on the
caller's ``body_layout`` argument rather than on a probe of the bytes:

- :data:`BODY_LAYOUT_LEVELLED`, **the default**, calls ``objects.parse_body`` -
  the layout a real save actually has.
- :data:`BODY_LAYOUT_FLAT` calls ``objects.parse_object_headers`` - the single
  flat table the synthetic corpus is built on. It pins the offset arithmetic and
  the two-scalar version dispatch, ``synthetic.SAVE_CROSS`` above all, which is
  a header/save pair that exists in no real file and therefore has no real body
  to be levelled.

**A silent try-flat-then-levelled fallback is refused.** It would keep every
corpus fixture green while hiding the wrong-shape defect this routing exists to
remove: a real body that failed the levelled walk would quietly fall through to
a reader that returns a wrong count instead of an error. Sniffing the bytes for
a shape is the same defect wearing a probe. So the choice is named, it is the
caller's, and the value a caller gets by not thinking about it is the one that
is correct for a REAL save.

An unrecognised layout is a CALLER bug, not a bad save, so it raises
``ValueError`` and deliberately NOT :class:`WorldLoadError` - a caller catching
the load error to tolerate a corrupt save must not thereby swallow its own typo.

Resource-node SEMANTICS are likewise unavailable, and that is a measurement
rather than a gap. ADR 0003: a save stores deltas from level defaults, so a
node's purity and resource type - which never change from the level asset - are
never written to the save at all. Geometry is exact and free; semantics need
the asset-extraction path. :class:`ResourceNode` carries placement and nothing
else, and says so.

PLACEMENT MEANS THE WHOLE TRANSFORM, AND FOR ONE RELEASE IT DID NOT (CS-1013).
:func:`_node_or_none` bound ``record.transform`` and then read one of its three
blocks, discarding the rotation and the scale on the same line that kept the
translation. That was a drop, not a measurement: unlike purity, both values ARE
in the file and are already parsed by ``objects.Transform`` before this function
sees them. The distinction matters because a consumer cannot tell an absent
field from an unmeasurable one, and this package had exactly one of each sitting
side by side. Semantics remain genuinely unavailable; geometry is now complete.

Geometry is free only for a record that HAS a transform, and CS-430 is the case
where one does not. A record whose class is a measured node class but which
carries no transform is skipped - inventing coordinates for it would be the
confident wrong answer non-negotiable 7 forbids - and it is now also FLAGGED
with :data:`WARN_NODE_TRANSFORM_ABSENT`. The skip was always right; the silence
was the defect, because a node list short by one is indistinguishable from a
world that holds one fewer node.

WHAT THE FLAG MAY SAY ABOUT THAT LOSS IS NARROWER THAN CS-430 CLAIMED, and
CS-433 is the correction. Its detail closed "their placement is unrecoverable
from this save", which the save refutes. ``objects``' levelled reader builds a
transform on the ACTOR branch and closes a COMPONENT with a parent path
instead, so the one record shape that reaches this branch is the one shape that
arrives carrying a parent path - and across the real library that path names a
placed record for the large majority of transform-less records, measured rather
than assumed. UNRECOVERED BY THIS READER, NOT UNRECOVERABLE FROM THE SAVE.

The distinction matters because :attr:`WorldWarning.detail` is a finished
operator-facing sentence rather than an internal note. :data:`_WARNING_DETAIL`
authors it, :func:`_warning` attaches it unaltered and it reaches
:class:`WorldModel` verbatim, so the wording chosen here is the wording that
ships and an overstated loss is shipped text rather than a comment. It is also
the defect CS-430 was written to remove, moved from the subject key into the
detail text: a silent drop and a misdescribed one are both losses the operator
cannot audit.
``tests/save/test_world.py::test_the_absence_warning_detail_claims_no_loss_the_raising_record_refutes``
grades the sentence against the record that raised it, which no check in
CS-430 did.

REACH: this branch is driven by the synthetic levelled fixtures in
``tests/save/test_world.py`` and by nothing else on the corpus this project has
measured - a sweep of the real library found records carrying no transform in
quantity and not one of a measured node class. ADR 0003's node classes were
counted in a real world as ACTORS carrying valid transforms, and the actor
branch is the one that builds a transform - so the flag guards a shape the
reader must survive rather than reporting one it meets. Do not read the sweep
as permanent: it is a property of the saves measured, not of the format.

IT IS A RECURRING SHAPE IN THIS PACKAGE rather than a one-off, which is the
reason to state it here rather than in a comment: a check that was missing
(CS-417), a check that discarded without flagging (CS-419), and a filter that
dropped without flagging (CS-430) are the same defect wearing three
mechanisms. Every one of them satisfies the "never fatal" half of
non-negotiable 7 - which is the half satisfied by accident - and fails the
"never silently wrong" half, which has to be satisfied on purpose because the
failure renders as a success. No count is written here on purpose; the shape is
what a reader needs, and a tally in prose is a number with no owner.

THE ERROR TAXONOMY, AND THE COUPLING THAT MAKES IT SAFE
---------------------------------------------------------
Every sibling failure is wrapped in :class:`WorldLoadError` with
``raise ... from exc``. That chain makes the CAUSE's own text part of this
module's formatted traceback, so wrapping WIDENS the echo path that
non-negotiable 12 governs.

**It is safe here only because every sibling already guarantees its exception
text is clean** - a field name from a closed vocabulary, a byte offset, an
expected and an actual length, a version scalar, a fixed reason, and nothing
else. ``header.py``, ``chunks.py``, ``objects.py`` and ``usmap.py`` each ENFORCE
the closed vocabulary at runtime: each declares ``FIELD_NAMES`` and routes the
field through ``_checked_field``, which refuses anything outside it before a
message exists. ``workdir.py`` renders a path only through ``locate.redact()``.

WHAT IS PINNED BEYOND THAT DIFFERS BY MODULE, and the difference is recorded
here rather than averaged into one reassuring sentence. ``header.py`` and
``objects.py`` plant markers in the PARSED BYTES and assert they reach no
exception surface on any failure path, which is the strongest form; neither has
a test that plants a value outside the vocabulary and asserts the refusal.
``chunks.py`` has that refusal test, and additionally pins its attribute set,
its reason constants and its rendering, but plants nothing in its bytes.
``usmap.py`` has the refusal test and nothing further, so it is the WEAKEST of
the four - it also reads an INSTALL file rather than a save, which is why its
field vocabulary is the largest and reaches the taxonomy through a reader
parameter rather than as a literal at the raise site.

AN EARLIER WORDING OF THIS PARAGRAPH SAID ALL FOUR PINNED THE GUARANTEE WITH A
PLANTED-MARKER TEST. That was false when written and stayed false: two of the
four enforced nothing at all, and this paragraph was the stated justification
for every ``raise ... from exc`` below it (CS-852). **Weakening any
one of those taxonomies silently converts every wrapped error here into a
leak**, and this paragraph is the record of what that guarantee is holding up,
so nobody relaxes one without seeing the load it carries.

This module adds no message content of its own beyond a stage name from a
closed set and the cause's CLASS NAME, both of which are module-defined
vocabulary rather than anything read out of a save.

THE WORLD TOKEN IS PERSONAL DATA
----------------------------------
It identifies a world, and the advice ledger keys on it. It is legal in memory
and in the gitignored ledger, and FORBIDDEN in every tracked file, every log
line and every error message. :class:`WorldModel` therefore hand-writes its
``__repr__`` to emit counts and version scalars with the token MASKED through
``header.masked_token`` - the mask that already exists, rather than a second
one. This is the widest repr in the layer, because every consumer above holds
one of these.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import Final, NoReturn

from clockspeed.save.chunks import ChunkError, DecompressedBody, decompress_body
from clockspeed.save.header import (
    HeaderError,
    SaveHeader,
    masked_token,
    parse_header,
    read_header,
)
from clockspeed.save.objects import (
    WARN_UNPARSED_PROPERTY_PAYLOAD,
    WARN_UNRESOLVED_SCHEMA,
    ContainerValue,
    ObjectError,
    ObjectRecord,
    ObjectReference,
    ObjectTable,
    PropertyResult,
    RecordIndex,
    StructValue,
    class_name_of,
    index_records,
    parse_body,
    parse_object_headers,
    read_properties,
)
from clockspeed.save.usmap import (
    WARN_DESYNCHRONISED_SECTION,
    WARN_UNRESOLVED_NAME,
    PropertyMap,
    UsmapError,
    UsmapWarning,
    cached_usmap,
)
from clockspeed.save.workdir import WorkDirError, copy_for_read, discard_copy

__all__ = [
    "BODY_LAYOUTS",
    "BODY_LAYOUT_FLAT",
    "BODY_LAYOUT_LEVELLED",
    "EMPTY_UNLOCK_STATE",
    "EMPTY_WORLD_PARENTS",
    "EMPTY_WORLD_PROPERTIES",
    "NODE_CLASS_NAMES",
    "READER_REFUSAL_TYPES",
    "SAVE_VERDICT_STAGES",
    "SOURCE_CHUNKS",
    "SOURCE_HEADER",
    "SOURCE_OBJECTS",
    "SOURCE_USMAP",
    "SOURCE_WORLD",
    "STAGES",
    "STAGE_CHUNKS",
    "STAGE_COPY",
    "STAGE_HEADER",
    "STAGE_OBJECTS",
    "STAGE_USMAP",
    "TARGET_AMBIGUOUS",
    "TARGET_RESOLVED",
    "TARGET_STATES",
    "TARGET_UNRESOLVED",
    "WARN_NEWER_SAVE_REFUSED",
    "WARN_NEWEST_SAVE_UNIDENTIFIED",
    "WARN_NODE_SEMANTICS_UNAVAILABLE",
    "WARN_NODE_TRANSFORM_ABSENT",
    "WARN_NO_PROPERTY_MAP",
    "WARN_UNLOCK_GRAMMAR_UNMEASURED",
    "ContainerContents",
    "ContainerEntry",
    "RecordProperties",
    "ReferenceTarget",
    "ResourceNode",
    "UnlockState",
    "WorldLoadError",
    "WorldModel",
    "WorldParents",
    "WorldProperties",
    "WorldWarning",
    "load_newest_world",
    "load_world",
    "load_world_from_bytes",
    "read_world_token",
    "refuse_again",
]

# ---------------------------------------------------------------------------
# The closed vocabularies
# ---------------------------------------------------------------------------

#: The stage a load failed at. A closed set, because a stage name travels into
#: an exception message and anything built from file content would be an echo
#: path.
STAGE_COPY: Final = "copy"
STAGE_HEADER: Final = "header"
STAGE_CHUNKS: Final = "chunks"
STAGE_USMAP: Final = "usmap"
STAGE_OBJECTS: Final = "objects"

STAGES: Final = (STAGE_COPY, STAGE_HEADER, STAGE_CHUNKS, STAGE_USMAP, STAGE_OBJECTS)

#: The stages whose refusal is a VERDICT ON THE SAVE'S OWN BYTES - the same
#: bytes draw the same refusal on every read, so a caller may skip the save and
#: may remember the refusal for as long as the file is unchanged.
#:
#: - :data:`STAGE_HEADER` parses the header out of the bytes alone.
#: - :data:`STAGE_CHUNKS` inflates the body out of the bytes alone.
#: - :data:`STAGE_OBJECTS` walks the inflated body. The installed property map
#:   is handed in, but it drives the resolution report and never the decode,
#:   and an unknown class is flagged rather than refused - see
#:   :func:`_decode_properties` and the module docstring - so the refusal is
#:   still the bytes' alone.
#:
#: THE REST ARE NOT, AND THE PARTITION IS EXHAUSTIVE.
#:
#: - :data:`STAGE_COPY` is the ENVIRONMENT: the game holding the file
#:   mid-autosave, a file that vanished, a work root that will not take the
#:   copy. The same bytes read a moment later may load.
#: - :data:`STAGE_USMAP` is the INSTALL: the game's property-map file failing
#:   to read, whatever the save holds. One transient failure there says nothing
#:   about any save, and remembering it against one pins the failure on a save
#:   that is fine.
#:
#: ``tests/save/test_newest_world.py`` asserts the partition covers
#: :data:`STAGES` with no overlap, so a stage added later is classified by a
#: decision rather than by omission.
SAVE_VERDICT_STAGES: Final = (STAGE_HEADER, STAGE_CHUNKS, STAGE_OBJECTS)

#: Every class name a reader at a :data:`SAVE_VERDICT_STAGES` stage raises when
#: it refuses a save's bytes - the header, chunk and object readers' own
#: refusal taxonomies, base classes included. THE CLOSED VOCABULARY OF A
#: REFUSAL'S CAUSE TYPE (CS-1309): a fallback flag's subject and a remembered
#: verdict are checked against it and REFUSED when outside it, so a cause type
#: rewritten anywhere between the reader and the flag - a write time spelled in
#: letters, a name - fails closed rather than reaching the panel. Spelled as
#: literals so the vocabulary is readable here and provable statically;
#: ``tests/save/test_newest_world.py`` asserts it equals the three taxonomies'
#: subclass walk, so a refusal class added to a reader reddens there first.
READER_REFUSAL_TYPES: Final = frozenset(
    {
        "ChunkBudgetExceededError",
        "ChunkDecompressError",
        "ChunkError",
        "ChunkFramingError",
        "ChunkTruncatedError",
        "HeaderError",
        "HeaderFormatError",
        "HeaderReadError",
        "HeaderTruncatedError",
        "ObjectBudgetExceededError",
        "ObjectError",
        "ObjectFormatError",
        "ObjectTruncatedError",
        "PersonalDataOptInRequiredError",
        "UnsupportedBodyLayoutError",
        "UnsupportedHeaderVersionError",
        "UnsupportedSaveVersionError",
    }
)

#: Which body reader a load uses. See the module docstring for why this is the
#: caller's explicit choice rather than a probe of the bytes.
#:
#: :data:`BODY_LAYOUT_LEVELLED` is the DEFAULT because it is what a real save
#: needs, and a default is what a caller gets by not thinking about it. The flat
#: reader is correct only for the synthetic corpus, so making IT the default
#: would mean the safe path had to be opted into - which is the arrangement that
#: produced the defect CS-409 removed.
BODY_LAYOUT_LEVELLED: Final = "levelled"
BODY_LAYOUT_FLAT: Final = "flat"

BODY_LAYOUTS: Final = (BODY_LAYOUT_LEVELLED, BODY_LAYOUT_FLAT)

#: Which layer noticed a warning. The same five names, because a caller asking
#: "where did this come from" is asking about the same layers.
SOURCE_HEADER: Final = STAGE_HEADER
SOURCE_CHUNKS: Final = STAGE_CHUNKS
SOURCE_USMAP: Final = STAGE_USMAP
SOURCE_OBJECTS: Final = STAGE_OBJECTS
SOURCE_WORLD: Final = "world"

#: The usmap subjects that mean a CLASS NAME left the mapping. The first is a
#: PREFIX completed by a digit run and nothing else; the second is exact. See
#: :func:`_drops_a_class_name` for why the bare forms are the only ones that
#: count, and for the three neighbouring conditions that must NOT be added here.
_DROPPED_SCHEMA_PREFIX: Final = "schema-"
_STOPPED_SCHEMA_SECTION: Final = "schemas"

#: Where one published reference landed - CS-400. THREE STATES, NEVER
#: COLLAPSED: a path borne by exactly one record is RESOLVED to it, by none is
#: UNRESOLVED, by more than one is AMBIGUOUS. See :class:`ReferenceTarget` for
#: why ambiguous is its own state here when ``objects.ReferenceResolution``
#: counts it inside resolved.
TARGET_RESOLVED: Final = "resolved"
TARGET_UNRESOLVED: Final = "unresolved"
TARGET_AMBIGUOUS: Final = "ambiguous"

TARGET_STATES: Final = (TARGET_RESOLVED, TARGET_UNRESOLVED, TARGET_AMBIGUOUS)

WARN_NO_PROPERTY_MAP: Final = "no-property-map"
WARN_UNLOCK_GRAMMAR_UNMEASURED: Final = "unlock-grammar-unmeasured"
WARN_NODE_SEMANTICS_UNAVAILABLE: Final = "node-semantics-unavailable"
WARN_NODE_TRANSFORM_ABSENT: Final = "node-transform-absent"

#: A newer save was refused by the reader and skipped - :func:`load_newest_world`.
#: The SUBJECT is WHY, never WHICH: the refusing stage and the cause type, both
#: closed vocabulary, and nothing about the file - not its name, which carries
#: the world name, and not its size or write time, which say when the operator
#: last played and single the file out of a listing (non-negotiables 3 and 12;
#: ``clockspeed/surface/api/world.py`` withholds the header's own times for the
#: same reason). The COUNT is how many skipped saves were refused that way.
#: Raised only when the walk KNOWS the world it serves is the refused newest
#: save's own - see :func:`load_newest_world`.
WARN_NEWER_SAVE_REFUSED: Final = "newer-save-refused"

#: The newest save was refused BEFORE its world could be read, so the world
#: served is the newest save the reader accepts and MAY BE ANOTHER WORLD - see
#: :func:`load_newest_world`. Subject and count as
#: :data:`WARN_NEWER_SAVE_REFUSED`. Neither world is named: no world token, no
#: world name, not even a masked one, reaches the flag (non-negotiables 3 and
#: 12).
WARN_NEWEST_SAVE_UNIDENTIFIED: Final = "newest-save-unidentified"

#: The ``objects`` warning codes that report SCHEMA RESOLUTION rather than
#: anything about the payload, and which :class:`RecordProperties` therefore
#: does NOT repeat in its ``warning_codes``.
#:
#: TWO REASONS, AND THE SECOND IS THE ONE THAT BITES. ``resolved`` already
#: carries this fact in the three states ``objects.PropertyResult`` defines, so
#: a code saying it again is a second copy of one fact in one object - the
#: drift class CLAUDE.md section 4 exists to stop. And it would make the field
#: ENVIRONMENT DEPENDENT: ``usmap.cached_usmap()`` answers None on a machine
#: with no game install and a mapping on one with, so a record of a class no
#: shipped registry models carries this code on the operator's machine and not
#: in CI. An assertion about a payload flag would then be green in one place
#: and red in the other while the payload was identical, which is the shape
#: states it was written to avoid:
#: tests/save/test_world.py::test_a_synthetic_world_publishes_one_decoded_property_value_end_to_end
#:
#: THE PAYLOAD CODES ARE NOT FILTERED. ``WARN_UNPARSED_PROPERTY_PAYLOAD``,
#: ``WARN_UNMEASURED_PROPERTY_TYPE`` and ``WARN_MEASURED_VALUE_DISAGREED`` all
#: describe what happened to the bytes and all reach ``warning_codes``
#: unaltered.
_RESOLUTION_WARNING_CODES: Final = frozenset({WARN_UNRESOLVED_SCHEMA})

#: One fixed line per warning code. Keyed rather than formatted, so a detail can
#: never be built from something read out of a save.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_NO_PROPERTY_MAP: (
            "no property mapping is available, so no class was checked against a registry;"
            " absence of a registry claims nothing about unmodelled content"
        ),
        WARN_UNLOCK_GRAMMAR_UNMEASURED: (
            "unlock state is empty because its serialized grammar has never been measured;"
            " ADR 0004 measured which fields exist and not how they are written"
        ),
        WARN_NODE_SEMANTICS_UNAVAILABLE: (
            "resource nodes carry placement only; purity and resource type are level"
            " defaults that a save never writes, so node semantics need asset extraction"
        ),
        WARN_NODE_TRANSFORM_ABSENT: (
            "a record of a measured resource-node class carried no transform, so it was"
            " skipped rather than published with invented coordinates; the node list is"
            " short by this many, and this reader does not recover their placement from"
            " the parent path such a record carries"
        ),
    }
)

#: The fallback flags' fixed lines, keyed by (code, more than one save). Two
#: lines per code so the sentence AGREES WITH THE COUNT the flag carries
#: (CS-1309 F3) while spelling no number itself - the count is its own field,
#: and a digit in the detail is a channel a value could ride.
_FALLBACK_DETAIL: Final[Mapping[tuple[str, bool], str]] = MappingProxyType(
    {
        (WARN_NEWER_SAVE_REFUSED, False): (
            "a newer save was refused by the reader and skipped, so this world is read"
            " from an older save and may be behind the game; the subject names the stage"
            " that refused it and the cause"
        ),
        (WARN_NEWER_SAVE_REFUSED, True): (
            "newer saves were refused by the reader and skipped, so this world is read"
            " from an older save and may be behind the game; the subject names the stage"
            " that refused them and the cause, and the count how many"
        ),
        (WARN_NEWEST_SAVE_UNIDENTIFIED, False): (
            "the newest save was refused before its world was read, so it could not be"
            " identified and the world shown may be a different one, read from the newest"
            " save the reader accepts past a refused save; the subject names the stage"
            " that refused it and the cause"
        ),
        (WARN_NEWEST_SAVE_UNIDENTIFIED, True): (
            "the newest save was refused before its world was read, so it could not be"
            " identified and the world shown may be a different one, read from the newest"
            " save the reader accepts past refused saves; the subject names the stage"
            " that refused them and the cause, and the count how many"
        ),
    }
)

#: The resource-node actor classes ADR 0003 MEASURED in a real world - 459, 118,
#: 31, 17 and 1 instance of them respectively, every one carrying a valid
#: transform. Matched on the CLASS NAME rather than on the full path, so a
#: namespaced or mod-authored path reaches the same branch.
NODE_CLASS_NAMES: Final = frozenset(
    {
        "BP_ResourceNode_C",
        "BP_FrackingSatellite_C",
        "BP_ResourceNodeGeyser_C",
        "BP_FrackingCore_C",
        "BP_ResourceDeposit_C",
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class WorldLoadError(Exception):
    """A save could not be loaded, named by the stage that refused it.

    Deliberately NOT a subclass of any sibling error: a caller that catches this
    to tolerate a bad save must not thereby swallow a ``HeaderError`` raised by
    some other path.

    The original is attached with ``raise ... from`` rather than dropped,
    because the sibling taxonomies carry the structural detail - the field, the
    offset, the expected and actual lengths - and re-deriving it here would mean
    inventing it. See the module docstring for the guarantee that makes chaining
    safe, and for what breaks if a sibling relaxes it.

    Attributes:
        stage: One of :data:`STAGES`.
        cause_type: The class name of the wrapped error. Module-defined
            vocabulary, never a value read out of a save.
    """

    def __init__(self, stage: str, cause_type: str) -> None:
        """Build the one-line message from the two closed-vocabulary fields.

        Args:
            stage: One of :data:`STAGES`.
            cause_type: The wrapped error's class name.
        """
        self.stage = stage
        self.cause_type = cause_type
        super().__init__(f"save load failed at the {stage} stage: {cause_type}")


# ---------------------------------------------------------------------------
# The models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorldWarning:
    """One thing a layer flagged and carried anyway.

    Every layer's advisories are normalised into this one stream so a consumer
    never has to reach into a sub-model to find a flag - which would be exactly
    the reach-past-your-neighbour the seam discipline forbids.

    The code, the fixed detail and the SUBJECT travel up. The scalars a
    sub-warning carries - a byte offset, a type id - stay on the sub-warning and
    are reachable through :attr:`WorldModel.header` and
    :attr:`WorldModel.objects`, because promoting them would mean giving one
    field four different meanings depending on which layer filled it in.

    THE SUBJECT IS THE EXCEPTION TO THAT, AND CS-440 IS WHY. It means the same
    thing in every layer that has one - the structural token naming WHICH thing
    was flagged - so it is the one field that does not change meaning on the way
    up. Without it a consumer learned that some usmap name did not decode and
    could not learn which position, which leaves a flag nothing can act on.

    NONE IS NOT THE EMPTY STRING HERE. ``chunks.ChunkWarning`` and
    ``objects.ObjectWarning`` declare no subject field at all, and rendering
    that as ``""`` would make an absent channel indistinguishable from a present
    but empty one - the collapse ``usmap._NameTable`` refuses for a name that
    did not decode, re-introduced one layer up.

    Attributes:
        source: Which layer noticed it, from the ``SOURCE_*`` constants.
        code: The originating layer's own warning code.
        detail: One fixed line naming the consequence. Never built from content.
        subject: The originating layer's structural token for WHAT was flagged,
            or None when that layer's warning type carries no subject. A
            structural token only - never a name read out of a file, which is
            the guarantee ``header.HeaderWarning`` and ``usmap.UsmapWarning``
            each make about their own.
        count: How many occurrences this aggregates.
    """

    source: str
    code: str
    detail: str
    subject: str | None = None
    count: int = 1


@dataclass(frozen=True, repr=False)
class UnlockState:
    """What the player has unlocked.

    NO LONGER EMPTY ON EVERY PATH - CS-1039. :func:`_read_unlocks` reads the
    three carriers :data:`UNLOCK_CARRIERS` names out of the decoded payloads,
    so a collection here can now hold what a save actually wrote. The ones it
    does NOT read are named in :data:`UNLOCK_CARRIERS_UNREAD`, and
    :data:`WARN_UNLOCK_GRAMMAR_UNMEASURED` is still raised on every load
    because of them: an empty unlock set with no warning is indistinguishable
    from a world that genuinely has nothing unlocked, and the difference
    between those two is the difference between honest silence and confident
    wrong advice.

    THE ABSENT-ARRAY RULE IS THE ONE ADR 0004 ASKED TO BE PRESERVED and it is.
    An array that is not present in the file is EMPTY, never missing and never
    an error - a fresh onboarding world writes no ``mPurchasedSchematics`` at
    all, and the reader contributes nothing for a carrier it does not find
    rather than refusing.

    ``repr`` IS HAND WRITTEN AND RENDERS COUNTS ONLY, which it did not need to
    be while every field was empty. ``purchased_schematics`` and ``recipes``
    hold OBJECT PATHS read out of a save. A path may cross this seam and may
    not reach a repr, a log line or an exception (non-negotiable 12), and a
    test runner reprs a value before a human chooses what to print.
    ``tests/save/test_world.py::test_the_unlock_state_renders_no_object_path``
    grades it against a populated state rather than an empty one.

    Attributes:
        purchased_schematics: Schematic paths bought, including the
            ``Schematic_Alternate_*`` entries that are pillar 2's alt-recipe
            purchase state.
        recipes: Unlocked recipe paths, including ``Recipe_Alternate_*``.
        current_game_phase: The ASSET PATH of the phase the world is in, or
            None when no carrier named one. A STRING AND NOT AN INDEX, retyped
            off ``int | None`` by CS-1039 because ADR 0016 measured the value
            to be a top-level ``ObjectProperty`` naming a ``GP_*`` asset and
            measured that no ``Phase``-named property in either readable world
            decoded to an integer at all. CS-913's acceptance, which its own
            item-notes section owns, requires the same retype, so this delivery
            OVERLAPS that item.
        feature_flags: Feature-level unlocks as discrete booleans - blueprints,
            building overclock, building efficiency, the map, the customizer.
            Overclock availability is a direct precondition for power and clock
            advice, so a rule requiring it declares the flag and cannot fire
            without it.
        scanned_resources: The scanned-resource state, which is the input that
            keeps ADR 0003's degraded node mode viable.
        trading_post_level: The tutorial trading post's tier, or None. ALWAYS
            None TODAY, and honestly so: ADR 0016's measured carrier table
            records no carrier type path for ``mTradingPostLevel`` at all, so
            there is no class name to key it on. The field exists because the
            filed acceptance names the carrier and because inventing a class
            name to key it on is the exact defect CS-1039's first cut shipped.
            It is listed in :data:`UNLOCK_CARRIERS_UNREAD`.
    """

    purchased_schematics: frozenset[str]
    recipes: frozenset[str]
    current_game_phase: str | None
    feature_flags: Mapping[str, bool]
    scanned_resources: frozenset[str]
    trading_post_level: int | None = None

    @property
    def is_empty(self) -> bool:
        """Whether nothing at all was recovered.

        EVERY FIELD IS CONSULTED, INCLUDING THE ONE CS-1039 ADDED. A field
        omitted here makes a state holding only that field report itself empty,
        which is the confident wrong answer in the one place a caller asks
        whether it may trust anything at all.

        Returns:
            True when every collection is empty and neither integer was read.
        """
        return not (
            self.purchased_schematics
            or self.recipes
            or self.feature_flags
            or self.scanned_resources
            or self.current_game_phase is not None
            or self.trading_post_level is not None
        )

    def __repr__(self) -> str:
        """Render counts and flags, and withhold every path.

        THE PHASE IS RENDERED AS A PRESENCE AND NOT AS ITS VALUE. It used to
        be an integer here, and rendering an integer was safe; CS-1039 retyped
        it to the ASSET PATH the save actually names, and an object path may
        not reach a repr. The privacy arm caught exactly that the moment the
        retype landed, which is the argument for the arm rather than for the
        annotation. ``trading_post_level`` stays a number and is rendered,
        because it is an ordinal the game's own progression defines and is
        never a string read out of a save.

        The feature flags are counted rather than named for the habit's sake:
        the names are module-side today and a later edit widening them to
        something read from a file must not silently turn this into an echo
        path.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}("
            f"purchased_schematics={len(self.purchased_schematics)}, "
            f"recipes={len(self.recipes)}, "
            f"current_game_phase={self.current_game_phase is not None}, "
            f"feature_flags={len(self.feature_flags)}, "
            f"scanned_resources={len(self.scanned_resources)}, "
            f"trading_post_level={self.trading_post_level})"
        )


#: The shape a load produces when no carrier record was found at all - which is
#: every synthetic fixture, and a real world in which none of the four read
#: carriers is present. A module-level constant rather than a fresh instance per
#: load, because it is immutable and identical every time.
EMPTY_UNLOCK_STATE: Final = UnlockState(
    purchased_schematics=frozenset(),
    recipes=frozenset(),
    current_game_phase=None,
    feature_flags=MappingProxyType({}),
    scanned_resources=frozenset(),
    trading_post_level=None,
)


@dataclass(frozen=True, repr=False)
class ResourceNode:
    """One resource-node actor: where it is, and nothing about what it holds.

    ADR 0003 measured both halves of that sentence. 626 node actors with 626
    valid transforms - geometry is exact and free. And ``mPurity``,
    ``mResourceNodeType`` and ``mResourceClass`` occur ZERO times in any save
    examined across three worlds and four game builds, because a save stores
    deltas from level defaults and a node's resource type never changes from
    the level asset. Semantics are not missing from this type by omission; they
    are not in the file.

    ``repr`` withholds the instance name, which is world content, and renders
    the class name, which is a game constant ADR 0003 already publishes.

    Attributes:
        class_name: The actor class, from :data:`NODE_CLASS_NAMES`.
        instance_name: The instance name, verbatim.
        translation: World coordinates, from the record's transform.
        rotation: The rotation quaternion IN FILE ORDER, from the same
            transform. Carried rather than dropped since CS-1013 - see the
            module docstring. The components are deliberately unnamed, because
            ``objects.Transform`` names none of them either.
        scale: The per-axis scale, from the same transform.
    """

    class_name: str
    instance_name: str
    translation: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    scale: tuple[float, float, float]

    def __repr__(self) -> str:
        """Render the class and the coordinates, and withhold the instance name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(class_name={self.class_name!r}, at={self.translation})"


@dataclass(frozen=True, repr=False)
class ContainerEntry:
    """One element half of a published container, WITHOUT ITS POSITION.

    ``objects.ContainerElement`` carries ``start`` - an absolute offset into the
    decompressed body - and it is right to: it is a save-layer diagnostic read
    inside that package. Publishing one is a different thing entirely. An offset
    is a position in a buffer this layer promised nothing above it would ever
    see, and CS-961 exists precisely to stop handing out offsets into a buffer
    nobody holds; shipping one inside the fix would be the defect wearing the
    repair. **THE CHOICE MADE HERE IS THAT THERE IS NO POSITION AT ALL.** The
    entry's place among its siblings is its index in
    :attr:`ContainerContents.entries`, which is a position in a collection the
    consumer already has - the same substitution :class:`WorldProperties` makes
    one level up.

    NOTHING IS DROPPED TO ACHIEVE THAT. The element's type word, its extent and
    its decoded value all survive, because a container published short of its
    elements would make world content that IS present read as absent, which
    non-negotiable 7 forbids more strongly than the leak it would fix.

    ``repr`` renders no value, on the terms :class:`RecordProperties` already
    set: an element's value is player-authored world content and a test runner
    reprs a value before a human chooses what to print.

    Attributes:
        type_word: The element's own type word, carried from
            ``objects.ContainerElement``. Shipped vocabulary, never anything
            invented here.
        length: How many bytes the element spanned. An EXTENT, which is a size
            rather than a position, so it locates nothing in a buffer.
        value: The decoded value, or None when ``objects`` does not decode that
            element's type. NONE MEANS "NOT DECODED", NEVER "EMPTY" - the
            distinction ``objects.ContainerElement`` draws, carried verbatim.
            DECODED WORLD CONTENT where it is not None.
    """

    type_word: str
    length: int
    value: object | None = None

    def __repr__(self) -> str:
        """Render the type word and the extent, and withhold the value.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(type_word={self.type_word!r}, "
            f"length={self.length}, decoded={self.value is not None})"
        )


@dataclass(frozen=True, repr=False)
class ContainerContents:
    """What one array, set or map property published to a higher layer.

    THE NARROWING OF ``objects.ContainerValue``, AND THE ONLY FIELD THAT
    CHANGES IS THE ELEMENT LIST. Everything the save layer measured about the
    container - its own type word, the element type words its tag carried, the
    count it declared, which of ``objects.ELEMENT_SHAPES`` bounded it, and the
    struct word an array of structs names - is carried VERBATIM, because each is
    shipped vocabulary or a count rather than a position. What is replaced is
    ``elements``: :class:`ContainerEntry` is ``objects.ContainerElement`` minus
    its absolute ``start``.

    ``element_shape`` IS CARRIED RATHER THAN DROPPED because the three shapes
    are not equally strong - ``objects`` records which one bounded the elements
    so a consumer can tell a self-delimiting reading from a derived one, and
    flattening that away here would publish a weak reading as a strong one.

    ``repr`` renders counts and shipped words only, on the same terms as
    :class:`ContainerEntry`.

    Attributes:
        type_word: The container's own type word, from
            ``objects.CONTAINER_TYPE_WORDS``.
        element_words: The element type words the tag carried - one for an array
            or a set, a key word and a value word for a map.
        element_count: The count the container itself declared. NOT the same as
            ``len(entries)``: a map yields two entries per declared entry, and a
            container whose declared count disagrees with its bytes is a fact a
            consumer needs rather than one to reconcile away.
        entries: One entry per element HALF, in the order the bytes carry them.
        element_shape: Which of ``objects.ELEMENT_SHAPES`` bounded the elements.
        struct_word: The struct type word an array of ``StructProperty`` names
            in its inner tag, or None.
    """

    type_word: str
    element_words: tuple[str, ...]
    element_count: int
    entries: tuple[ContainerEntry, ...]
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
            f"entries={len(self.entries)}, "
            f"element_shape={self.element_shape!r}, "
            f"struct_word={self.struct_word is not None})"
        )


@dataclass(frozen=True, repr=False)
class ReferenceTarget:
    """Where one published reference landed in the record table - CS-400.

    THE JOIN, PUBLISHED AS A RECORD INDEX AND NEVER AS AN OFFSET. An index is
    a position in :attr:`WorldModel.objects.records`, a collection every
    consumer already holds, on the same terms :class:`WorldProperties` keys by
    one. A consumer following a building to its inventory component reads this
    and never calls into ``objects`` - which is the seam: the save layer owns
    the path grammar and the resolution, and a higher layer that ran the
    resolution itself would be reaching past its neighbour.

    THE RESOLUTION IS ``objects``' OWN. The lookup is
    ``objects.RecordIndex.records_for`` over the table
    ``objects.index_records`` builds, the same pairing
    ``objects.resolve_references`` counts with, so the published join and the
    save layer's partition cannot disagree about which records a path names.

    AMBIGUOUS IS ITS OWN STATE HERE, AND THAT IS A DIFFERENCE FROM
    ``objects.ReferenceResolution`` RATHER THAN A CONTRADICTION. That type
    counts an ambiguous reference INSIDE resolved, because its question is
    whether a path is borne at all. This type answers a consumer about to take
    ONE record, and handing it one of several as if it were the only one is
    the confident wrong answer non-negotiable 7 forbids. So every candidate is
    kept and none is claimed.

    ``repr`` renders the state, which is closed vocabulary, and a count. The
    indices are positions rather than world content, and are withheld anyway
    so a later edit widening this type does not inherit a rendering habit.

    Attributes:
        state: One of :data:`TARGET_STATES`.
        record_indices: Every record index bearing the reference's path, in
            table order. EMPTY when unresolved, ONE when resolved, MORE THAN
            ONE when ambiguous - the state is derived from this length and is
            carried beside it so a consumer branches on a word, not a count.
    """

    state: str
    record_indices: tuple[int, ...]

    @property
    def record_index(self) -> int | None:
        """The one record this reference names, when there is exactly one.

        Returns:
            The index when resolved; None when unresolved or ambiguous. None
            never distinguishes those two - :attr:`state` does.
        """
        return self.record_indices[0] if self.state == TARGET_RESOLVED else None

    def __repr__(self) -> str:
        """Render the state and the candidate count.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(state={self.state!r}, candidates={len(self.record_indices)})"


def _reference_target(found: tuple[int, ...]) -> ReferenceTarget:
    """Classify one lookup into the three published states.

    Args:
        found: Every record index bearing the reference's path.

    Returns:
        The target.
    """
    if not found:
        return ReferenceTarget(state=TARGET_UNRESOLVED, record_indices=())
    if len(found) == 1:
        return ReferenceTarget(state=TARGET_RESOLVED, record_indices=found)
    return ReferenceTarget(state=TARGET_AMBIGUOUS, record_indices=found)


@dataclass(frozen=True, repr=False)
class RecordProperties:
    """What one record's payload yielded, and what it did not.

    ONE OF THESE EXISTS FOR EVERY WALKED RECORD, INCLUDING THE ONES THAT
    YIELDED NOTHING. That is non-negotiable 7 rather than tidiness: a record
    ABSENT from :attr:`WorldProperties.by_record_index` is indistinguishable
    from one whose payload genuinely held no property, and an absence that
    reads as "not set" is the confident wrong answer the rule forbids. So the
    two ways of holding nothing are spelled differently - ``payload_read``
    True with an empty mapping means the payload was read and held nothing,
    and False means it was not read at all.

    ``repr`` is hand written and withholds every string, on the terms
    :class:`objects.PropertyResult` already set and for a stronger reason:
    every layer above the save layer holds a :class:`WorldModel`, and this
    object hangs off it. The VALUES are player-authored and the KEYS are
    property names read out of the save's own bytes, so both halves of every
    entry are world content under non-negotiable 12, and ``schema_name`` is a
    fragment of a class path :class:`ObjectRecord` already withholds. A test
    runner reprs a value before a human chooses what to print.
    ``tests/save/test_world.py::test_no_body_byte_reaches_any_echo_path``
    plants a marker in a property name AND in a property value and sweeps six
    rendering channels for it.

    NO FIELD HERE IS A CARRIER. ``bytes`` and ``Path`` are the two annotations
    ``tests/repr_rendering_guard.py`` names as able to render raw save content
    or a home directory, and
    ``tests/save/test_world.py::test_no_published_world_type_annotates_a_carrier_field``
    asserts their absence. This is also why the decode is eager: a lazy entry
    would have to retain the decompressed body to answer later.

    Attributes:
        values: The decoded properties, by name, from
            ``objects.PropertyResult.properties``. Holds values of the types
            ``objects.MEASURED_VALUE_TYPES`` names and no others - a property
            whose type encoding is unmeasured is absent here and counted in
            ``unmeasured_value_count``, so an absent name never means "this
            property is not set". DECODED WORLD CONTENT: a consumer that
            renders it is an echo path under non-negotiable 12.

            EVERY VALUE IS CARRIED VERBATIM EXCEPT A CONTAINER, WHICH IS
            NARROWED. ``objects.ContainerValue`` holds elements carrying an
            absolute offset into the decompressed body; a container reaches
            here as :class:`ContainerContents` instead, whose entries carry the
            element type word, its extent and its value and NO position. The
            narrowing is recursive, so a container nested inside a struct
            interior is narrowed too. See :func:`_published_value`.
        schema_name: The class name the record's type path resolved to. A
            fragment of world content, withheld from ``repr``.
        resolved: Whether the property mapping models that class. THREE
            STATES, CARRIED VERBATIM AND NEVER FLATTENED (CS-960). None means
            NO MAPPING WAS SUPPLIED, so nothing was consulted and nothing is
            claimed - the state CI and every fresh clone are in. False means
            one WAS supplied and does not model this class. True means it
            does. Collapsing None into False would report a world of unknown
            content on the strength of having looked at nothing.
        payload_read: Whether the payload read under the measured grammar. A
            record the walk attributed NO extent to - which is every record
            from the flat reader - is True with an empty mapping: there was no
            payload to fail on. False is the flagged case and always arrives
            with ``objects.WARN_UNPARSED_PROPERTY_PAYLOAD`` in
            ``warning_codes``, because it is derived from that code rather
            than tracked beside it. Whether there WAS a payload is
            :attr:`payload_present`, which this field does not answer.
        unmeasured_value_count: How many tags carried a type whose value
            encoding is unmeasured, from the reader.
        disagreeing_value_count: How many tags carried a MEASURED type whose
            bytes disagreed with the declared size. Counted apart from the
            field above because the two mean opposite things: non-zero here is
            a reason to distrust this record's other values, and non-zero
            above is not.
        warning_codes: The reader's own codes for what was flagged about this
            payload, in the order it raised them. Closed vocabulary from
            ``objects``, never anything read out of a save. Codes reporting
            schema RESOLUTION are excluded - see
            :data:`_RESOLUTION_WARNING_CODES` for why the exclusion is not a
            style choice.
        references: The record's top-level ``objects.REFERENCE_TYPE_WORD``
            values, ONE PER TAG AND IN TAG ORDER, carried from
            ``objects.PropertyResult.references`` - CS-1039. A TUPLE RATHER
            THAN A MAPPING, for the reason that type gives: two tags sharing a
            name may not collapse into one, because a population that loses a
            member is no longer the population. ``values`` tolerates that
            collapse because a caller there asks BY NAME.

            NOT A DUPLICATE OF ``values``. A reference tag's decoded value is
            in ``values`` too, as the measured pair, but keyed by name and
            therefore unordered and collapsible; this is the ordered
            population the acceptance names. DECODED WORLD CONTENT holding
            OBJECT PATHS - ``objects.ObjectReference`` withholds all three of
            its strings from its own repr, and this type's repr renders a
            length.
        struct_interiors: One ``objects.StructValue`` per TOP-LEVEL struct tag
            whose interior read, in tag order, from
            ``objects.PropertyResult.struct_interiors`` - CS-1039. Reported
            APART FROM ``values`` because that is what the reader measured: a
            struct written as native raw bytes is not read at all, so
            ``StructProperty`` stays outside ``objects.MEASURED_VALUE_TYPES``
            and a struct tag still counts in ``unmeasured_value_count``.
            Putting an interior into ``values`` would claim the type's
            top-level value is measured, which for the native form is false.

            EVERY INTERIOR IS NARROWED RATHER THAN FORWARDED, and the
            distinction is load-bearing. ``objects.StructValue`` declares no
            position of its own, which makes forwarding it look safe; what its
            ``properties`` mapping HOLDS can be an ``objects.ContainerValue``
            whose elements each carry an absolute offset into the decompressed
            body. :func:`_published_value` already owns that narrowing and
            this population goes through it, so what arrives is a struct whose
            containers are :class:`ContainerContents`.

            THE ARRAY-OF-STRUCT CASE IS NOT THIS ONE and is not duplicated
            here. Interiors belonging to a container's ELEMENTS already cross
            inside that container's own published entries; this field is the
            TOP-LEVEL tag population, which crossed nowhere before CS-1039.
        reference_targets: Where each of ``references`` landed in the record
            table, ONE PER REFERENCE AND IN THE SAME ORDER, so
            ``reference_targets[i]`` is the target of ``references[i]`` -
            CS-400. See :class:`ReferenceTarget` for the three states. EMPTY
            on an entry built without the join, which only a caller
            constructing this type by hand produces; every entry
            :func:`load_world_from_bytes` publishes is aligned.
        undecoded_names: The name of every tag counted in
            ``unmeasured_value_count`` or ``disagreeing_value_count``, carried
            verbatim from ``objects.PropertyResult.undecoded_names`` - CS-1264.
            So "is a tag of this name present" has an answer when its value was
            dropped: a name absent from BOTH this and :attr:`values` was not on
            a payload that read. Names only, never a value. WORLD CONTENT on
            the terms :attr:`values` states, so ``repr`` renders a count.
        payload_present: CS-1266. Whether the object walk paired this record
            with ANY payload. False for every record of the flat walk and for
            every record of a level whose record and payload counts disagree
            (``objects.WARN_PAYLOAD_COUNT_DISAGREEMENT``) - the reader hands
            back a read, empty entry for such a record without reading a byte,
            so :attr:`payload_read` True with no values is a payload that held
            nothing only when this is True. Derived here, inside the save
            package, from the record's extent; the extent itself is a position
            and is never published. A flag, so ``repr`` renders it. True by
            default, for an entry built by hand.
    """

    values: Mapping[str, object]
    schema_name: str
    resolved: bool | None
    payload_read: bool
    unmeasured_value_count: int = 0
    disagreeing_value_count: int = 0
    warning_codes: tuple[str, ...] = ()
    references: tuple[ObjectReference, ...] = ()
    struct_interiors: tuple[StructValue, ...] = ()
    reference_targets: tuple[ReferenceTarget, ...] = ()
    undecoded_names: frozenset[str] = frozenset()
    payload_present: bool = True

    def __repr__(self) -> str:
        """Render counts and flags, and withhold every string.

        The warning codes are rendered as a COUNT even though they are closed
        vocabulary and safe. Rendering the population rather than its members
        is the habit that survives a later edit widening what a code may hold,
        and this repr is the one a test runner reaches for unasked.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(values={len(self.values)}, "
            f"resolved={self.resolved}, "
            f"payload_read={self.payload_read}, "
            f"unmeasured_value_count={self.unmeasured_value_count}, "
            f"disagreeing_value_count={self.disagreeing_value_count}, "
            f"warning_codes={len(self.warning_codes)}, "
            f"references={len(self.references)}, "
            f"struct_interiors={len(self.struct_interiors)}, "
            f"reference_targets={len(self.reference_targets)}, "
            f"undecoded_names={len(self.undecoded_names)}, "
            f"payload_present={self.payload_present})"
        )


@dataclass(frozen=True, repr=False)
class WorldProperties:
    """Every walked record's decoded properties, keyed by RECORD INDEX.

    THE KEY IS THE WHOLE POINT AND IS NOT A BYTE OFFSET. An offset is a
    position in a buffer this layer promised nothing above it would ever see,
    so publishing one would hand a consumer the reach past its neighbour the
    seam discipline forbids - and would do it in the one type every higher
    layer holds. An index into :attr:`WorldModel.objects.records` is a
    position in a collection that consumer already has, so following it needs
    nothing this layer withheld.

    ``ObjectRecord.body_offset`` and ``body_length`` are untouched by that and
    stay where they are. They are diagnostics read INSIDE this package - the
    decode below reads them - and they are published to nobody.

    ``repr`` renders the population size and nothing about any member, for the
    reason :class:`RecordProperties` gives.

    Attributes:
        by_record_index: One entry per walked record, keyed by that record's
            index in :attr:`WorldModel.objects.records`. TOTAL over that
            table: a record with no entry cannot be told from a record whose
            payload held nothing, which non-negotiable 7 forbids.
    """

    by_record_index: Mapping[int, RecordProperties]

    @property
    def total(self) -> int:
        """How many records got an entry.

        Equal to the walked record count by construction, and worth asking
        rather than deriving: a consumer holding this object can check the two
        agree without reaching into the record table.

        Returns:
            The count.
        """
        return len(self.by_record_index)

    @property
    def unread_payload_count(self) -> int:
        """How many entries report a payload that did not read.

        The honest denominator for anything computed off these values. A
        consumer that treats an empty mapping as "this record has no
        properties" is wrong by exactly this many records.

        Returns:
            The count.
        """
        return sum(1 for entry in self.by_record_index.values() if not entry.payload_read)

    def __repr__(self) -> str:
        """Render the two counts, and nothing about any entry.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(total={self.total}, "
            f"unread_payload_count={self.unread_payload_count})"
        )


#: The shape a :class:`WorldModel` built without a property pass carries. A
#: module-level constant on the same terms as :data:`EMPTY_UNLOCK_STATE`: it is
#: immutable and identical every time, and it is what lets
#: :attr:`WorldModel.properties` be DEFAULTED - which keeps
#: :func:`load_world_from_bytes` the one place in the tree that constructs a
#: :class:`WorldModel` at all.
EMPTY_WORLD_PROPERTIES: Final = WorldProperties(by_record_index=MappingProxyType({}))


@dataclass(frozen=True, repr=False)
class WorldParents:
    """Where each component's parent path landed in the record table - CS-400 S2b.

    WHY THIS JOIN EXISTS BESIDE :attr:`RecordProperties.reference_targets`.
    Measured on the local library, counts only: the inventory carrier of a
    miner, a water pump or a truck station is named by NONE of its parent
    actor's top-level reference tags. The link lives in the actor head's
    component list, which ``objects.resolve_references`` steps over by design
    (CS-834), so the reference join cannot reach it however it resolves. The
    unresolved references on those actors are a recipe asset and, on a water
    pump, a level object no record bears - neither names the carrier. What does
    name the owner is the carrier's OWN record: ``ObjectRecord.parent``.

    THE RESOLUTION IS ``objects``' OWN, on the terms :class:`ReferenceTarget`
    states: the parent path is looked up through ``objects.RecordIndex
    .records_for`` over ``objects.index_records``, the same index the reference
    join uses, so a higher layer follows a component to its owner by reading
    a record index and never matches a path itself. The three states are
    :data:`TARGET_STATES`, never collapsed - an ambiguous parent keeps every
    candidate and claims none.

    THE TARGET IS WHATEVER RECORD BEARS THE PATH. This join does not assert the
    target is an ACTOR; ``ObjectRecord.kind`` is published beside it and a
    consumer that needs an actor reads it there.

    ``repr`` renders the per-state counts and nothing about any member.

    Attributes:
        by_record_index: One target per record carrying a parent path, keyed by
            that record's index in :attr:`WorldModel.objects.records`. TOTAL
            over those records; an actor, which carries a transform where a
            component carries a parent path, has no entry.
    """

    by_record_index: Mapping[int, ReferenceTarget]

    @property
    def total(self) -> int:
        """How many records got an entry.

        Returns:
            The count.
        """
        return len(self.by_record_index)

    def count(self, state: str) -> int:
        """How many entries landed in one state.

        Args:
            state: One of :data:`TARGET_STATES`.

        Returns:
            The count; zero for a word outside the vocabulary.
        """
        return sum(1 for target in self.by_record_index.values() if target.state == state)

    def __repr__(self) -> str:
        """Render the total and the per-state counts.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(total={self.total}, "
            f"resolved={self.count(TARGET_RESOLVED)}, "
            f"unresolved={self.count(TARGET_UNRESOLVED)}, "
            f"ambiguous={self.count(TARGET_AMBIGUOUS)})"
        )


#: The shape a :class:`WorldModel` built without the parent join carries, on
#: the terms :data:`EMPTY_WORLD_PROPERTIES` gives.
EMPTY_WORLD_PARENTS: Final = WorldParents(by_record_index=MappingProxyType({}))


@dataclass(frozen=True, repr=False)
class WorldModel:
    """Everything above the save layer is allowed to know about a world.

    THE ONLY SAVE-LAYER TYPE A HIGHER LAYER HOLDS (``docs/ARCHITECTURE.md``
    section 1.1). ``audit/`` and ``progress/`` consume this and never save
    bytes.

    Attributes:
        token: The header's save identifier - the stable, filename-independent
            world key the advice ledger is keyed by. PERSONAL DATA: legal in
            memory and in the gitignored ledger, forbidden in every tracked
            file, log line and error message.
        header: The parsed header, carrying its own warnings and scalars.
        objects: The walked record table, carrying its own warnings and the two
            version scalars the walk was dispatched on.
        unlocks: What the player has unlocked. Empty on every path today - see
            :class:`UnlockState`.
        nodes: Resource-node actors with their placement. Geometry only.
        warnings: Every layer's advisories, normalised into one stream.
        properties: Each walked record's decoded properties, keyed by record
            index. DECODED WORLD CONTENT in both halves of every entry - see
            :class:`RecordProperties`. DEFAULTED to
            :data:`EMPTY_WORLD_PROPERTIES` rather than required, which is what
            keeps :func:`load_world_from_bytes` the only place in the tree
            that BUILDS this class out of a save: a field with no default would
            have to be supplied at every future site, and the first thing a
            caller with no payload in scope would reach for is a mapping it
            invented. The one other construction site, :func:`_with_flags`,
            builds nothing - it COPIES a world ``load_world_from_bytes`` built,
            every field carried by enumeration, and only appends warnings.
            NOT ON THE WIRE. ``clockspeed/surface/api/world.py`` serializes a
            fixed key set and this field has not joined it, asserted by
            ``tests/save/test_world.py::test_no_body_byte_reaches_any_echo_path``.
        parents: Each component's parent path followed to a record index -
            CS-400 S2b, see :class:`WorldParents`. DEFAULTED to
            :data:`EMPTY_WORLD_PARENTS` on the terms ``properties`` gives.
            Not on the wire either.
    """

    token: str
    header: SaveHeader
    objects: ObjectTable
    unlocks: UnlockState
    nodes: tuple[ResourceNode, ...]
    warnings: tuple[WorldWarning, ...]
    properties: WorldProperties = EMPTY_WORLD_PROPERTIES
    parents: WorldParents = EMPTY_WORLD_PARENTS

    @property
    def contains_unmodeled_content(self) -> bool:
        """Whether this world holds content the project does not model.

        Delegated rather than recomputed, so the answer cannot drift from the
        table it is about. False when no registry was supplied: absence of a
        registry claims nothing.

        Returns:
            True when at least one class path went unresolved.
        """
        return self.objects.contains_unmodeled_content

    def __repr__(self) -> str:
        """Render counts and version scalars, with the token MASKED.

        The widest repr in the layer - every consumer above holds one of these,
        and a test runner or a logger reprs an object before a human chooses
        what to print. The map name is omitted for the same reason
        ``SaveHeader`` omits it: its POSITION is version dependent, so a
        dispatch bug would put an operator-authored string in it, and this
        rendering has to stay safe even when the parse is wrong.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(token={masked_token(self.token)!r}, "
            f"header_version={self.header.header_version}, "
            f"save_version={self.header.save_version}, "
            f"objects={len(self.objects.records)}, "
            f"properties={self.properties.total}, "
            f"unread_payloads={self.properties.unread_payload_count}, "
            f"nodes={len(self.nodes)}, "
            f"unmodelled_classes={len(self.objects.unknown_classes)}, "
            f"warnings={len(self.warnings)})"
        )


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def _warning(source: str, code: str, count: int = 1) -> WorldWarning:
    """Build one world warning from this module's own fixed detail table.

    Args:
        source: One of the ``SOURCE_*`` constants.
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(source=source, code=code, detail=_WARNING_DETAIL[code], count=count)


def _drops_a_class_name(warning: UsmapWarning) -> bool:
    """Whether one usmap warning means a CLASS NAME left the mapping.

    TWO CONDITIONS, FOUND BY GREPPING THE ROOT CAUSE RATHER THAN THE SYMPTOM.
    ``usmap._read_schema`` drops a schema whose own name index does not resolve,
    and ``usmap._read_schemas`` catches a desynchronised entry and returns the
    schemas it has, losing every one after it. Both leave a class the registry
    DOES model absent from ``schemas``; only the first is the one CS-435 named,
    and a fix keyed to it alone would have left the second standing.

    THE KEY IS THE ``(code, subject)`` PAIR AND NOT EITHER HALF ALONE.
    ``usmap._read_schema`` gives its three failures three distinct subjects
    deliberately (CS-431), and only the bare ``schema-<N>`` one drops the
    schema: ``schema-<N>-super`` keeps the schema and loses its super type, and
    ``schema-<N>-property`` keeps it and loses one property. Matching the code
    alone - or matching the prefix without checking what follows it - would
    withdraw a TRUE claim on both of those, trading one wrong answer for a
    weaker one everywhere.

    THE CONDITIONS THAT LOOK RELATED AND ARE NOT are on the same grep and are
    named here so nobody re-adds them: a DUPLICATE schema keeps the later
    definition under the same key, so no name leaves the mapping; a TRAILING
    section sits past a schema count that was honoured in full; an unknown
    PROPERTY TYPE costs a property rather than a class.
    ``tests/save/test_world.py::test_a_usmap_condition_that_loses_no_class_name_does_not_downgrade``
    holds all three on the false side.

    THIS IS A CROSS-MODULE STRING CONTRACT, stated plainly because it is the
    fragile part of this function.
    ``tests/save/test_world.py::test_a_real_usmap_whose_schema_name_did_not_decode_downgrades_the_reason``
    runs the REAL parser over patched synthetic bytes and grades the key against
    its actual producer, so the vocabulary moving turns that test red rather
    than turning this check silently inert.

    Args:
        warning: One warning from a parsed mapping.

    Returns:
        True when the condition it reports removed a class name.
    """
    if warning.code == WARN_DESYNCHRONISED_SECTION:
        return warning.subject == _STOPPED_SCHEMA_SECTION
    if warning.code != WARN_UNRESOLVED_NAME:
        return False
    position = warning.subject.removeprefix(_DROPPED_SCHEMA_PREFIX)
    return position != warning.subject and position.isdigit()


def _registry_incomplete(mapping: PropertyMap | None) -> bool:
    """Whether the mapping lost part of itself while being parsed.

    THIS IS THE HALF OF CS-435 THAT LIVES HERE (CS-440). A class the registry
    models but whose schema was lost reaches ``objects`` as a path absent from
    ``known_classes``, and was published as "is not a class the supplied
    registry models" - a sentence that is false for exactly that input. Neither
    neighbour can see the pair: ``usmap`` does not know which save is being
    read, and ``objects`` is handed a container of names in which a dropped
    entry and an absent one are the same bytes. This is the seam where both
    facts are in scope at once.

    Args:
        mapping: The resolved property map, or None when none was resolved.

    Returns:
        True when at least one class name is known to have left the mapping.
        False for an absent mapping: no registry claims nothing, which is the
        position ``known_classes=None`` already takes downstream.
    """
    if mapping is None:
        return False
    return any(_drops_a_class_name(warning) for warning in mapping.warnings)


def _resolve_property_map(
    supplied: PropertyMap | None,
) -> tuple[PropertyMap | None, list[WorldWarning]]:
    """Take the caller's mapping, or find the installed one.

    Args:
        supplied: A mapping to use as-is, or None to resolve one.

    Returns:
        The mapping or None, and any warnings raised in getting there.

    Raises:
        WorldLoadError: A mapping file exists but could not be read or parsed.
            Absence is NOT this case and never raises.
    """
    if supplied is not None:
        return supplied, []
    try:
        found = cached_usmap()
    except UsmapError as exc:
        raise WorldLoadError(STAGE_USMAP, type(exc).__name__) from exc
    if found is None:
        return None, [_warning(SOURCE_USMAP, WARN_NO_PROPERTY_MAP)]
    return found, []


def _nodes_from(table: ObjectTable) -> tuple[tuple[ResourceNode, ...], list[WorldWarning]]:
    """Pick the resource-node actors out of a walked record table.

    THE SKIP IS CORRECT AND THE SILENCE WAS NOT (CS-430). A record whose class
    IS a measured node class but which carries no transform is still skipped -
    publishing it would mean inventing coordinates, which is the confident-wrong
    answer non-negotiable 7 exists to forbid. What changed is that the loss is
    now NAMED. Dropped silently, a world short one node is indistinguishable
    from a world that genuinely holds that many, and nothing downstream can tell
    which it is holding.

    :func:`_node_or_none` answers one question - is this a publishable node -
    and returns None for two unrelated reasons. The condition this warning names
    is therefore re-derived from the record by :func:`_untransformed_node_class`
    rather than inferred from that None, so a third future reason for None
    cannot be quietly reported as a missing transform.

    WHAT THE WARNING MAY CLAIM IS BOUNDED BY WHAT THE RECORD HOLDS (CS-433).
    Such a record reaches here from the COMPONENT branch of ``objects``' levelled
    reader, which closes with a parent path in place of a transform block - so
    it arrives carrying a route this function does not follow. The detail
    therefore reports the loss as UNRECOVERED HERE rather than as unrecoverable
    from the save, and following that route is separate work rather than a thing
    this warning may quietly imply has been ruled out.

    Args:
        table: The walked table.

    Returns:
        One :class:`ResourceNode` per publishable record, in file order, and the
        warning naming how many measured node records were skipped for want of a
        transform. The warning list is empty when none were.
    """
    nodes: list[ResourceNode] = []
    untransformed = 0
    for record in table.records:
        node = _node_or_none(record)
        if node is not None:
            nodes.append(node)
        elif _untransformed_node_class(record):
            untransformed += 1
    warnings = (
        [_warning(SOURCE_WORLD, WARN_NODE_TRANSFORM_ABSENT, untransformed)] if untransformed else []
    )
    return tuple(nodes), warnings


def _node_or_none(record: ObjectRecord) -> ResourceNode | None:
    """Convert one record to a node, or return None when it is not one.

    Args:
        record: The record to inspect.

    Returns:
        The node, or None when the class is not a measured node class or the
        record carried no transform.
    """
    name = class_name_of(record.type_path)
    if name not in NODE_CLASS_NAMES or record.transform is None:
        return None
    return ResourceNode(
        class_name=name,
        instance_name=record.instance_name,
        translation=record.transform.translation,
        rotation=record.transform.rotation,
        scale=record.transform.scale,
    )


def _untransformed_node_class(record: ObjectRecord) -> bool:
    """Whether this record is a measured node class that carried no transform.

    The exact condition :data:`WARN_NODE_TRANSFORM_ABSENT` names, stated once
    and asked of the record directly. A record of a class this project does not
    model is NOT this case: it is already reported through
    ``ObjectTable.unknown_classes``, and counting it here would turn every
    ordinary record in a world into a lost-node warning.

    Args:
        record: The record to inspect.

    Returns:
        True when the class name is in :data:`NODE_CLASS_NAMES` and the record
        carries no transform.
    """
    return class_name_of(record.type_path) in NODE_CLASS_NAMES and record.transform is None


#: THE CARRIERS THIS MODULE READS, KEYED BY THE RECORD CLASS NAME A SAVE
#: ACTUALLY WRITES AND BY THE PROPERTY NAME TOGETHER. Each value is the
#: :class:`UnlockState` field that carrier feeds.
#:
#: THE CLASS NAMES ARE SAVE-SIDE, NOT C++ DECLARING CLASSES, AND THE FIRST
#: CUT OF THIS ITEM GOT THAT WRONG. It keyed on ``AFGSchematicManager``,
#: ``AFGRecipeManager`` and ``AFGGamePhaseManager`` - the classes the shipped
#: headers DECLARE the properties on. A save carries the blueprint that
#: derives from them, so :func:`class_name_of` returns ``BP_SchematicManager_C``
#: and no key matched any record on any real world while every synthetic arm
#: passed. That is non-negotiable 7's silently-wrong outcome reached through a
#: fixture and an oracle taken from the same wrong source.
#:
#: THE TYPE PATHS ARE RECORDED IN
#: ``docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`` under
#: "The carriers", measured by running the decoder over real saves.
#: The control arm whose absence let the first cut ship is
#: tests/save/test_world.py::test_every_unlock_carrier_key_is_reachable_from_the_adr_carrier_table
#: It parses that table and asserts every key here is reachable from it. The
#: name is kept on ONE line deliberately: a citation broken across a wrap reads
#: as a truncated symbol to the oracle-citation guard, which is how it got here.
#:
#: ``mTradingPostLevel`` IS ABSENT AND THAT IS DELIBERATE. The item note names
#: it as a HUB-tier carrier, but ADR 0016's measured table records no carrier
#: type path for it at all. Keying it would mean inventing a class name, which
#: is exactly the defect above. It is listed in :data:`UNLOCK_CARRIERS_UNREAD`
#: and :attr:`UnlockState.trading_post_level` stays None until a carrier is
#: measured.
UNLOCK_CARRIERS: Final[Mapping[tuple[str, str], str]] = MappingProxyType(
    {
        ("BP_SchematicManager_C", "mPurchasedSchematics"): "purchased_schematics",
        ("FGRecipeManager", "mAvailableRecipes"): "recipes",
        ("BP_GamePhaseManager_C", "mCurrentGamePhase"): "current_game_phase",
    }
)

#: The carriers that are NOT read, so the warning below reports a specific gap
#: rather than a general one. The first two were named in the item note as
#: explicitly retained; the next two decode but have nowhere on
#: :class:`UnlockState` to land; the last has no measured carrier at all.
UNLOCK_CARRIERS_UNREAD: Final = (
    "mPaidOffSchematic",
    "mSavedOngoingResearch",
    "mUnlockedResearchTrees",
    "mTargetGamePhase",
    "mTradingPostLevel",
)

#: The fields :data:`UNLOCK_CARRIERS` fills from an ARRAY of asset references.
#: The remaining field is read from a TOP-LEVEL reference tag, and the two
#: arrive on different attributes of :class:`RecordProperties`.
_UNLOCK_PATH_FIELDS: Final = frozenset({"purchased_schematics", "recipes"})

#: WHICH ASSET ROOTS A REFERENCE FIELD MAY PUBLISH, PER FIELD. An ALLOWLIST and
#: never a denylist: this repository has measured a denylist leaking four times,
#: once across four green commits wearing a different field each time, and only
#: an allowlist of good values held.
#:
#: THE RISK THIS GUARDS IS NOT THE FIELD IT HOLDS TODAY, IT IS THE SECOND ONE.
#: ``objects.ObjectReference``'s own docstring says all three of its fields are
#: WORLD CONTENT and that ``object_path`` is THE JOIN KEY matched against a
#: record's ``instance_name``. Nothing in that population structurally separates
#: a shipped asset path from a record instance path - both are strings on the
#: same attribute - so a second name added to :data:`_UNLOCK_REFERENCE_FIELDS`
#: would reach the published state, and from there the wire, with no friction at
#: all. The allowlist is what makes that addition a deliberate act.
#:
#: WHY ``/Game/`` IS PERMITTED TO CROSS. A ``/Game/FactoryGame/...`` path is
#: SHIPPED content, byte-identical on every install, and carries no account id,
#: no world name, no Windows user and no home path - so it is outside
#: non-negotiables 3, 11 and 12 rather than excused from them. It is also an
#: established category rather than a new exposure: ``clockspeed/surface/api/
#: world.py`` already publishes ``objects.UnknownClass.type_path`` verbatim on
#: exactly that justification.
UNLOCK_ASSET_ROOTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "current_game_phase": ("/Game/",),
    }
)

#: The character an object path uses to separate its LEVEL from the object
#: inside it - ``Persistent_Level:PersistentLevel.Thing_C_0``. A shipped asset
#: path never carries one and a record instance path always does, so its
#: presence is the structural tell the allowlist alone would miss: a world whose
#: level happened to be named so the path began ``/Game/`` would otherwise pass
#: the root check while naming a record.
_INSTANCE_SEPARATOR: Final = ":"

#: The fields read from :attr:`RecordProperties.references` rather than from
#: ``values``. ADR 0016 measured that ``mCurrentGamePhase`` is a TOP-LEVEL
#: ``ObjectProperty`` tag naming a ``GP_*`` asset, and that no ``Phase``-named
#: property in either readable world's record table decoded to an INTEGER at
#: all. A reader admitting only ``int`` therefore cannot read it, which is what
#: the first cut of this item shipped.
#:
#: EVERY MEMBER MUST BE CLASSIFIED IN :data:`UNLOCK_ASSET_ROOTS`. A member that
#: is not is refused at runtime rather than published unchecked - see
#: :func:`_permitted_asset_path` - so the guard fails CLOSED on a field nobody
#: classified instead of passing it through.
_UNLOCK_REFERENCE_FIELDS: Final = frozenset(UNLOCK_ASSET_ROOTS)

_REFERENCE_PARTS: Final = 2


def _permitted_asset_path(field: str, path: str) -> str | None:
    """One reference value, admitted only if it is a shipped asset path.

    THREE REFUSALS, AND THE ORDER OF THEM DOES NOT MATTER BECAUSE EACH IS
    INDEPENDENT. An unclassified field is refused, because a field nobody
    classified is a field nobody decided about. A path carrying
    :data:`_INSTANCE_SEPARATOR` is refused, because that is a record instance
    path and world content. A path under no permitted root is refused, because
    the list is of what MAY cross rather than of what may not.

    THE REFUSAL IS SILENT AND THAT IS ALREADY HONEST. Every load carries
    :data:`WARN_UNLOCK_GRAMMAR_UNMEASURED` unconditionally, so a state missing a
    value it refused is never reported as a complete reading - which is the
    guarantee non-negotiable 7 asks for, and it is one this function does not
    have to make a second time.

    Args:
        field: The :class:`UnlockState` field the value would be bound to.
        path: The object path half of the decoded reference.

    Returns:
        The path when it may be published, and None otherwise.
    """
    roots = UNLOCK_ASSET_ROOTS.get(field)
    if roots is None:
        return None
    if _INSTANCE_SEPARATOR in path:
        return None
    if not any(path.startswith(root) for root in roots):
        return None
    return path


def _unlock_paths(value: object) -> frozenset[str]:
    """Every object path inside one published container value.

    NON-NEGOTIABLE 7 IS THE WHOLE SHAPE OF THIS FUNCTION. An element whose
    value is not the measured reference pair is SKIPPED rather than refused and
    rather than guessed at - a container that decoded partially still yields
    the members that decoded, and a value of some other shape yields nothing at
    all instead of raising out of a reader whose contract is to flag and skip.

    THE OBJECT PATH HALF IS AN ASSET PATH AND JOINS THE REGISTRY, NEVER THE
    RECORD TABLE. ADR 0016 measured every element of these arrays across both
    readable worlds: the level reference is empty and the object path is a
    ``/Game/FactoryGame/...`` asset path, and NOT ONE element joined a record's
    ``instance_name``. So this returns the path and looks nothing up - a reader
    that resolved these against the record table would find nothing and report
    an empty unlock set for a world that has one.

    Args:
        value: One entry of ``RecordProperties.values``, of any shape.

    Returns:
        The object path half of every element that decoded as a reference.
        Empty when the value is not a published container.
    """
    if not isinstance(value, ContainerContents):
        return frozenset()
    paths: set[str] = set()
    for entry in value.entries:
        element = entry.value
        if isinstance(element, tuple) and len(element) == _REFERENCE_PARTS:
            path = element[1]
            if isinstance(path, str):
                paths.add(path)
    return frozenset(paths)


def _unlock_reference(entry: RecordProperties, name: str, field: str) -> str | None:
    """The asset path one TOP-LEVEL reference tag names, or None.

    READ FROM ``references`` RATHER THAN FROM ``values``, and that is the
    correction this function exists for. ADR 0016 measured ``mCurrentGamePhase``
    as a top-level ``ObjectProperty`` tag naming a ``GP_*`` asset, and measured
    that no ``Phase``-named property in either readable world's record table
    decoded to an integer at all - which the C++ agrees with, declaring
    ``TObjectPtr<UFGGamePhase>``. The first cut of this item read it through an
    int-only narrowing, so it could not have read a real save's phase under any
    fixture.

    ``references`` IS THE POPULATION CS-1039's OTHER HALF PUBLISHED. Reading
    the phase is the first consumer of it inside this module, which is why the
    two halves were filed as one item.

    Args:
        entry: One record's published properties.
        name: The reference tag's property name.
        field: The :class:`UnlockState` field it would be bound to, which is
            what :func:`_permitted_asset_path` classifies against.

    Returns:
        The object path of the FIRST tag with that name, or None when the
        record carries none. First rather than last because the population is
        in tag order and a duplicate would mean a save wrote the property
        twice, which ADR 0016 did not observe.
    """
    for reference in entry.references:
        if reference.property_name == name:
            # THE GUARD SITS AT THE SAVE SEAM RATHER THAN AT THE WIRE, because
            # the wire is not the only consumer - every layer above holds the
            # model. A value refused here never enters it.
            return _permitted_asset_path(field, reference.object_path)
    return None


def _read_unlocks(
    table: ObjectTable, properties: WorldProperties
) -> tuple[UnlockState, list[WorldWarning]]:
    """Recover the unlock state from the payloads the second pass decoded.

    IT READS NO BYTES OF ITS OWN, BY DESIGN. Every value it needs is already in
    :class:`WorldProperties`, keyed by record index, so this function consumes
    the seam above the decoder rather than reaching past it - and cannot hold a
    position in the decompressed body, because nothing it touches carries one.

    THE OWNING CLASS AND THE PROPERTY NAME ARE MATCHED TOGETHER. See
    :data:`UNLOCK_CARRIERS` for why a bare-name match would accept a
    declaration that cannot be in a save.

    THE WARNING IS STILL RAISED ON EVERY LOAD and is not conditional on having
    found nothing. Four declarations in :data:`UNLOCK_CARRIERS_UNREAD` carry
    ``SaveGame`` and are not read, so a state built here is INCOMPLETE even
    when it is full - and a caller told "complete" about a partial reading is
    the confident wrong answer the warning exists to prevent. A conditional
    warning would go silent exactly on the worlds that have the most unread.

    Args:
        table: The walked record table, for each record's class path.
        properties: The decoded payloads, keyed by index into ``table.records``.

    Returns:
        The state and the warning that says what is still not read.
    """
    paths: dict[str, set[str]] = {field: set() for field in _UNLOCK_PATH_FIELDS}
    assets: dict[str, str] = {}
    for index, record in enumerate(table.records):
        entry = properties.by_record_index.get(index)
        if entry is None:
            continue
        owner = class_name_of(record.type_path)
        for (carrier, name), field in UNLOCK_CARRIERS.items():
            if carrier != owner:
                continue
            # THE TWO POPULATIONS ARE READ FROM DIFFERENT ATTRIBUTES BECAUSE
            # THE READER PUTS THEM THERE. An array of asset references is a
            # container in `values`; a top-level reference tag is in
            # `references` and in `values` BOTH, but only the first keeps the
            # typed pair - see `_unlock_reference` for what ADR 0016 measured.
            if field in _UNLOCK_PATH_FIELDS:
                paths[field].update(_unlock_paths(entry.values.get(name)))
            elif (asset := _unlock_reference(entry, name, field)) is not None:
                assets[field] = asset
    state = UnlockState(
        purchased_schematics=frozenset(paths["purchased_schematics"]),
        recipes=frozenset(paths["recipes"]),
        current_game_phase=assets.get("current_game_phase"),
        feature_flags=MappingProxyType({}),
        scanned_resources=frozenset(),
        trading_post_level=None,
    )
    if state.is_empty:
        # THE CONSTANT RATHER THAN AN EQUAL-BUT-DISTINCT INSTANCE, so the
        # no-carrier path keeps producing the one shape the module documents
        # and every arm that asserts identity against it stays meaningful.
        state = EMPTY_UNLOCK_STATE
    return state, [_warning(SOURCE_WORLD, WARN_UNLOCK_GRAMMAR_UNMEASURED)]


def _checked_layout(body_layout: str) -> str:
    """Refuse an unrecognised body layout before anything is parsed.

    A caller bug is not a bad save, so this is a ``ValueError`` and NOT a
    :class:`WorldLoadError` - a caller catching the load error to tolerate a
    corrupt save must not thereby swallow its own typo.

    The message renders the ALLOWED set and never the supplied value. A layout
    string is caller-supplied rather than read out of a save, so echoing it is
    not a leak today; it is withheld because "echo the argument back" is the
    habit that eventually echoes an argument holding save content, and this
    module's whole error taxonomy is built on not having that habit.

    Args:
        body_layout: The caller's choice.

    Returns:
        The layout, unchanged, when it is one of :data:`BODY_LAYOUTS`.

    Raises:
        ValueError: It is not.
    """
    if body_layout not in BODY_LAYOUTS:
        raise ValueError(f"body_layout must be one of {BODY_LAYOUTS}")
    return body_layout


def _walk_body(
    payload: bytes,
    parsed: SaveHeader,
    mapping: PropertyMap | None,
    body_layout: str,
) -> ObjectTable:
    """Route the body to the reader the caller chose.

    NO FALLBACK, BY DESIGN. Whichever reader is chosen either produces a table
    or raises; a second attempt with the other reader would turn a wrong-shape
    body into a wrong ANSWER, which is the one outcome non-negotiable 7 rules
    out. See the module docstring.

    Args:
        payload: The decompressed body, length prefix included.
        parsed: The header, for the two version scalars.
        mapping: The property map, or None when none was resolved.
        body_layout: One of :data:`BODY_LAYOUTS`, already checked.

    Returns:
        The walked table.

    Raises:
        ObjectError: The chosen reader refused the body. Includes
            ``UnsupportedBodyLayoutError`` for a pair with no measured layout -
            which since CS-407 means a pair occurring in no real save, every
            real one having been measured.
    """
    # THE CS-963 SCRUB, ADDED IN THE REPAIR ROUND AFTER AN ADVERSARIAL PASS FOUND
    # THIS FRAME STILL HOLDING THE WHOLE DECOMPRESSED BODY. It is the object
    # stage's refusal that unwinds through here, and `world.py` chains it, so a
    # locals-showing renderer prints the body out of this frame as the CAUSE.
    #
    # THE ARM THAT SHOULD HAVE CAUGHT IT WAS VACUOUS, which is the more useful
    # half: its fixture cut the body at the halfway point while the planted marker
    # sat past that cut, so the marker was never in the bytes the sweep walked. An
    # empty verdict over a population the value cannot be in is a statement about
    # the fixture, not about this frame (non-negotiable 12).
    try:
        # THE SEAM. Both scalars are threaded SEPARATELY into either reader:
        # header_version drives the body length prefix width and nothing else,
        # save_version drives the transform delta and nothing else. Deriving either
        # from the other is correct on every real file and wrong on SAVE_CROSS.
        reader = parse_body if body_layout == BODY_LAYOUT_LEVELLED else parse_object_headers
        return reader(
            payload,
            save_version=parsed.save_version,
            header_version=parsed.header_version,
            known_classes=None if mapping is None else mapping.schemas,
            # THE SECOND SEAM, and it goes with the first. Handing over the schema
            # NAMES without saying that the registry lost some of its own is what
            # let a modelled class be published as unmodelled (CS-440): the two
            # facts only exist together here, and either alone is an answer nobody
            # can audit.
            registry_incomplete=_registry_incomplete(mapping),
        )
    except BaseException:
        del payload
        raise


def _decode_properties(
    payload: bytes, table: ObjectTable, mapping: PropertyMap | None
) -> WorldProperties:
    """Decode every walked record's properties, eagerly, in one pass.

    THE SECOND PASS OVER THE BODY, AND IT LIVES HERE FOR ONE REASON: this is
    the only scope in the project where the decompressed payload and the walked
    record extents are both alive. Folding it into ``objects.parse_body``'s
    return was refused - that return is parametrized over by
    ``tests/save/test_objects.py`` and ``tests/save/test_phase4_gate.py``, and
    the flat reader attributes no extent at all, so half the corpus would be
    carrying a field it can never fill.

    EAGER RATHER THAN LAZY, AND THE COST IS DELIBERATE. A lazy entry would have
    to keep the decompressed body reachable for as long as any consumer held a
    :class:`WorldModel`, which is every layer above this one. That is the one
    thing no published type may do, and it is why neither new type declares a
    field the shipped-tree carrier guard would fire on. Decoding now and
    dropping the buffer is the only arrangement in which "the payload dies with
    the walk" is a fact rather than a convention.

    THE BODY IS A PARAMETER AND IT IS DELETED BEFORE ANY UNWIND, which is the
    mechanism ``objects.read_properties`` and ``objects.parse_properties``
    already use at their own raise sites. The MESSAGE was never the channel -
    the frame is. A traceback renderer that shows locals, and pytest does,
    prints ``payload`` verbatim, and that is the whole decompressed world under
    non-negotiable 12. A deleted fast local is simply absent from
    ``frame.f_locals``, which is what a renderer cannot reach around. The catch
    is BROAD and unconditional on purpose: the frame carries the body out on
    any unwind, not only on the one error this function documents, so narrowing
    it to ``ObjectError`` would re-open the frame for every exception type a
    later edit introduces. Because the re-raise is unconditional there is
    nothing for the broad catch to swallow.

    WHAT GRADES THAT SCRUB, STATED AT THE WIDTH IT WAS MEASURED AT.
    ``tests/save/test_world.py::test_the_documented_property_overrun_scrubs_the_frame_that_holds_the_body``
    drives the refusal below by handing this function a record whose extent
    overruns, asserts this frame is IN the raised traceback, and asserts it
    holds no payload; removing the ``del`` reddens it. An earlier wording said
    the section-12 sweep walked "every refusal this layer has" and so covered
    this one. IT DID NOT AND COULD NOT: that sweep drives three shapes through
    ``load_world_from_bytes``, none of which reaches this branch, so the ``del``
    below was executed by no test at all while a sentence here claimed it was.
    A claim wider than its measurement is the failure this repository keeps
    paying for.

    THE BRANCH IS UNREACHABLE THROUGH ``load_world_from_bytes`` BY
    CONSTRUCTION, WHICH IS WHY THE ARM INJECTS A RECORD. ``objects`` builds each
    extent as ``(cursor.offset, length)`` and then skips ``length``, which
    bounds-checks against the body, so an extent this walk produced cannot
    overrun the body this walk read; and the flat reader attributes
    ``body_length=0``, which ``read_properties`` skips outright. That is
    stronger than "untested" and it is a reason to KEEP the branch rather than
    delete it: the construction that makes it unreachable lives one layer down
    and is free to move, and a scrub that only runs when that happens is
    exactly the one nobody would notice was missing.

    Args:
        payload: The decompressed body the table was walked out of.
        table: The walked table, for its records and their extents.
        mapping: The property map, or None when none was resolved. It drives
            the resolution report alone and never the decode - see
            ``objects.read_properties``.

    Returns:
        One entry per walked record, keyed by that record's index in
        ``table.records``.

    Raises:
        ObjectError: A record's declared payload extent runs past the body.
            Deliberately NOT caught here - see the module docstring for why an
            overrun is fatal where an unreadable payload is flagged.
    """
    decoded: dict[int, RecordProperties] = {}
    # THE JOIN IS BUILT ONCE PER TABLE, OFF THE SAVE LAYER'S OWN INDEX. Records
    # are mapped to their positions BY IDENTITY: two records may compare equal
    # field for field (an instance name is measured not to be unique), and an
    # equality-keyed map would fold them into one index.
    record_index = index_records(table)
    positions = {id(record): position for position, record in enumerate(table.records)}
    try:
        for index, record in enumerate(table.records):
            decoded[index] = _record_properties(
                read_properties(
                    payload,
                    record,
                    mapping,
                    # THE THIRD SEAM, AND CS-G05's REPAIR RESTS ON IT. The
                    # property TAG grammar is version dispatched exactly as
                    # the body skeleton is, and this is the only scope where
                    # the walked table's pair and the decompressed body are
                    # both alive - so a reader that could read (14,60)
                    # perfectly would still publish nothing without these
                    # two lines. Threaded SEPARATELY for the reason
                    # `_walk_body` gives: deriving either scalar from the
                    # other is correct on every real file and wrong on
                    # SAVE_CROSS.
                    save_version=table.save_version,
                    header_version=table.header_version,
                ),
                record_index,
                positions,
                # CS-1266. The FACT the extent carries, read here where the
                # extent may be read, so no layer above ever needs the length.
                payload_present=record.body_length > 0,
            )
    except BaseException:
        del payload, mapping
        raise
    return WorldProperties(by_record_index=MappingProxyType(decoded))


def _published_value(value: object) -> object:
    """Narrow one decoded value to what a higher layer is allowed to hold.

    THE WHOLE JOB IS REMOVING ABSOLUTE POSITIONS, and it is recursive because
    the positions are not all at the top. ``objects.ContainerValue`` holds
    ``ContainerElement``s carrying ``start``; a ``ContainerElement``'s own value
    can be another container or a struct; and ``objects.StructValue`` holds an
    interior mapping that can hold either. A one-level narrowing would publish a
    clean array of dirty structs.

    EVERY OTHER VALUE IS RETURNED UNCHANGED AND THAT IS DELIBERATE. A scalar, a
    string and an ``objects.ObjectReference`` carry no position at all - a
    reference names a level and an object path, which is world content this
    layer already publishes and not a place in a buffer - so copying them would
    buy nothing and would put a second shape between the reader and the
    consumer.

    Args:
        value: One decoded value from ``objects.PropertyResult.properties``, or
            from inside another one.

    Returns:
        The value a :class:`RecordProperties` may carry.
    """
    if isinstance(value, ContainerValue):
        return ContainerContents(
            type_word=value.type_word,
            element_words=value.element_words,
            element_count=value.element_count,
            entries=tuple(
                ContainerEntry(
                    type_word=element.type_word,
                    length=element.length,
                    value=_published_value(element.value),
                )
                for element in value.elements
            ),
            element_shape=value.element_shape,
            struct_word=value.struct_word,
        )
    if isinstance(value, StructValue):
        # THE INTERIOR IS REBUILT AND THE TYPE IS KEPT. `StructValue` declares
        # no position of its own, so there is nothing here to narrow away and a
        # third published type would be a shape with no fact behind it. What its
        # `properties` mapping HOLDS can be a container - `objects.
        # _decode_interior_tag` reads a container tag inside an interior on the
        # same grammar as one at top level - so this cannot simply return the
        # value, and a one-level narrowing would publish a clean array of dirty
        # structs.
        #
        # EVERY FIELD IS NAMED RATHER THAN COPIED WITH `dataclasses.replace`,
        # because `replace` is in the write-capable call vocabulary
        # `tests/save/test_world.py::test_the_world_module_has_no_write_capable_
        # call_site` enforces on this module - a name-keyed guard cannot tell
        # `Path.replace` from this one, and widening it to let this through
        # would cost the guard its point. Naming the fields is a coupling to
        # `objects.StructValue`'s shape, and it is BOUND rather than left to
        # review: `tests/save/test_world.py::test_the_struct_narrowing_names_
        # every_field_objects_declares` fails if that type gains one.
        return StructValue(
            struct_word=value.struct_word,
            form=value.form,
            properties=MappingProxyType(
                {name: _published_value(item) for name, item in value.properties.items()}
            ),
            unmeasured=value.unmeasured,
            disagreed=value.disagreed,
            depth=value.depth,
        )
    return value


def _record_properties(
    result: PropertyResult,
    record_index: RecordIndex,
    positions: Mapping[int, int],
    *,
    payload_present: bool = True,
) -> RecordProperties:
    """Narrow one reader result to what a higher layer is allowed to hold.

    THE NARROWING IS THE JOB. ``objects.PropertyResult`` carries reference
    pairs, struct interiors and their tag denominators, every one of which is
    save-layer diagnostic detail rather than a world fact - and publishing them
    would put a second consumer on a shape ``objects`` is free to move.
    ``resolved`` is the field carried VERBATIM and never derived: its three
    states are ``objects``' own measurement, and the flattening this function
    could do - answering False where the reader answered None - is exactly the
    collapse of ABSENT into UNMODELLED that CS-960 removed one layer down.

    THE VALUES ARE NARROWED RATHER THAN CARRIED, and CS-961's repair pass is
    why. ``read_properties`` decodes an ``ArrayProperty``, a ``SetProperty`` or
    a ``MapProperty`` to an ``objects.ContainerValue`` whose elements carry
    ``start`` - an ABSOLUTE OFFSET INTO THE DECOMPRESSED BODY. Handing that
    upward publishes a position in a buffer that is gone by the time any
    consumer holds this object, which is the exact defect this item exists to
    remove and which its acceptance names outright. :func:`_published_value`
    rebuilds those, and only those, into :class:`ContainerContents`; every
    element survives with its type word, its extent and its value.

    ``payload_read`` IS DERIVED FROM THE WARNING RATHER THAN TRACKED BESIDE IT,
    so the flag and the code cannot disagree about the same record. The reader
    raises ``objects.WARN_UNPARSED_PROPERTY_PAYLOAD`` exactly when the payload
    did not read under the measured grammar; a record the walk attributed no
    extent to raises nothing and is True with an empty mapping, because there
    was no payload to fail on.

    EACH REFERENCE IS FOLLOWED TO A RECORD INDEX HERE - CS-400. The lookup is
    the save layer's own (``objects.RecordIndex.records_for``) and what crosses
    is a :class:`ReferenceTarget` holding positions in the table, never a
    record and never an offset.

    Args:
        result: One record's reader result.
        record_index: The table arranged for reference lookup.
        positions: Each record's position in the table, keyed by identity.
        payload_present: Whether the walk paired the record with any payload
            - see :attr:`RecordProperties.payload_present`. The caller derives
            it from the record's extent, which never crosses this function.

    Returns:
        The published entry.
    """
    codes = tuple(
        item.code for item in result.warnings if item.code not in _RESOLUTION_WARNING_CODES
    )
    return RecordProperties(
        values=MappingProxyType(
            {name: _published_value(value) for name, value in result.properties.items()}
        ),
        schema_name=result.schema_name,
        resolved=result.resolved,
        payload_read=WARN_UNPARSED_PROPERTY_PAYLOAD not in codes,
        unmeasured_value_count=result.unmeasured_value_count,
        disagreeing_value_count=result.disagreeing_value_count,
        warning_codes=codes,
        # BOTH POPULATIONS ARE CARRIED IN TAG ORDER, WHICH IS THE READER'S OWN
        # ORDER AND IS NOT RE-DERIVED HERE. Rebuilding either from `properties`
        # would lose it: that mapping is keyed by NAME, so it is unordered with
        # respect to the file and collapses two tags sharing a name into one.
        #
        # THE REFERENCES ARE CARRIED VERBATIM AND THE INTERIORS ARE NOT, and
        # the asymmetry is a fact about the two types rather than a choice.
        # `objects.ObjectReference` holds three strings and no position, so
        # there is nothing to narrow away. `objects.StructValue` holds an
        # interior MAPPING that can hold an `objects.ContainerValue`, whose
        # elements each carry an absolute offset into a buffer that is gone by
        # the time a consumer holds this object - so forwarding an interior
        # would publish a clean struct full of dirty elements. That is the
        # exact defect this seam exists to remove.
        references=result.references,
        struct_interiors=tuple(_published_struct(interior) for interior in result.struct_interiors),
        reference_targets=tuple(
            _reference_target(
                tuple(
                    positions[id(found)]
                    for found in record_index.records_for(reference.object_path)
                )
            )
            for reference in result.references
        ),
        # CS-1264. Names only, so there is nothing to narrow: carried verbatim.
        undecoded_names=result.undecoded_names,
        payload_present=payload_present,
    )


def _parent_targets(table: ObjectTable) -> WorldParents:
    """Follow every component's parent path to a record index - CS-400 S2b.

    The lookup is ``objects``' own index, keyed by instance name exactly as
    the reference join is, and the records are mapped to their positions BY
    IDENTITY for the reason :func:`_decode_properties` gives.

    Args:
        table: The walked record table.

    Returns:
        One target per record carrying a parent path.
    """
    record_index = index_records(table)
    positions = {id(record): position for position, record in enumerate(table.records)}
    return WorldParents(
        by_record_index=MappingProxyType(
            {
                position: _reference_target(
                    tuple(positions[id(found)] for found in record_index.records_for(parent))
                )
                for position, record in enumerate(table.records)
                if (parent := record.parent) is not None
            }
        )
    )


def _published_struct(interior: StructValue) -> StructValue:
    """Narrow one TOP-LEVEL struct interior to what a higher layer may hold.

    A one-line hop through :func:`_published_value` rather than a second
    narrowing, so the top-level population and the one reached through a
    container are narrowed by the SAME code. Two narrowings would be two places
    for the recursion to stop early, and the whole defect this seam removes is a
    recursion that stopped one level too soon.

    The cast is what the hop costs. :func:`_published_value` is typed over
    ``object`` because it is called on every decoded value; its ``StructValue``
    branch returns a ``StructValue`` and no other shape, which is asserted by
    ``tests/save/test_world.py::test_a_container_inside_a_published_struct_
    interior_is_narrowed`` rather than left to the annotation.

    Args:
        interior: One entry of ``objects.PropertyResult.struct_interiors``.

    Returns:
        The interior a :class:`RecordProperties` may carry.
    """
    published = _published_value(interior)
    if not isinstance(published, StructValue):  # pragma: no cover - defended, not reachable
        raise TypeError("the struct narrowing returned a shape that is not a StructValue")
    return published


def load_world_from_bytes(
    data: bytes,
    *,
    property_map: PropertyMap | None = None,
    body_layout: str = BODY_LAYOUT_LEVELLED,
) -> WorldModel:
    """Parse a whole save out of bytes already in memory.

    The composition the module docstring describes, minus the copy: the caller
    has the bytes, so there is nothing to copy and nothing to open.

    WHICH ``(header version, save version)`` PAIRS ARE READABLE IS NOT WRITTEN
    DOWN HERE. ``objects.MEASURED_BODY_LAYOUTS`` is that set and the only place
    the pairs are listed; a body whose pair is outside it is refused before the
    walk. THIS SENTENCE USED TO LIST THEM AND WENT STALE THE DAY THE SET GREW,
    which is what a second copy of a fact does. See the module docstring before
    reading a green result as "this reads saves" - what is measured is a
    SKELETON.

    THE BODY IS WALKED TWICE, FOR TWO DIFFERENT FACTS. The first pass builds
    the record table; the second decodes each record's payload into
    :class:`WorldProperties`. Both run inside one guard and one stage, because
    they are the same bytes and a failure in either is the same refusal. The
    second pass is what makes this function the last scope in which the
    decompressed body is reachable - see the module docstring for the four
    bounds on what it may publish.

    Args:
        data: A whole save file's bytes.
        property_map: A parsed property mapping to check class paths against.
            None resolves the installed one through ``usmap.cached_usmap``,
            which returns None rather than raising when there is no install.
        body_layout: Which body reader to use, from :data:`BODY_LAYOUTS`.
            Defaults to :data:`BODY_LAYOUT_LEVELLED`, the layout a REAL save
            has. :data:`BODY_LAYOUT_FLAT` reads the synthetic corpus's single
            flat table and is never right for a real file.

    Returns:
        The world model.

    Raises:
        WorldLoadError: Any sibling refused the bytes - including a body whose
            version pair has no measured layout. The original is attached as
            the cause.
        ValueError: ``body_layout`` is not one of :data:`BODY_LAYOUTS`. Raised
            before anything is parsed, and NOT a ``WorldLoadError``.
    """
    # `data` IS THE WHOLE SAVE FILE, AND IT IS DROPPED FROM THIS FRAME BEFORE
    # ANY UNWIND. That is the mechanism `objects.read_properties` and
    # `objects.parse_properties` already use at their own raise sites, applied
    # here for a stronger reason: what those hold is the decompressed BODY,
    # where this holds the raw file - and the file's header carries the
    # platform, the account id and the player display name in PLAINTEXT inside
    # its options string (non-negotiable 12, `BOOTSTRAP.md` section 2.2).
    # `header.parse_header` redacts that string on the object it returns, and a
    # traceback renderer showing locals - pytest does - reads past the object to
    # the bytes and prints them verbatim. A deleted fast local is what a
    # renderer cannot reach around.
    #
    # THE GUARD WRAPS THE WHOLE FUNCTION, INCLUDING `_checked_layout`. Every way
    # out of this frame is a way out carrying the file, so covering only the
    # refusals this function documents would leave the caller-bug path - and
    # every exception type a later edit introduces - holding it. Because the
    # re-raise is unconditional there is nothing for the broad catch to swallow.
    #
    # tests/save/test_world.py::test_no_clockspeed_frame_holds_the_raw_save_on_
    # any_refusal_path drives all four and walks the raised traceback. Its
    # marker is planted in the header's OPTIONS STRING rather than in the
    # payload, because a payload marker is deflated into the file and therefore
    # can never appear in `data` - which is why the payload sweep in section 12
    # of that file was green while this frame held the whole save.
    try:
        _checked_layout(body_layout)

        try:
            parsed = parse_header(data)
        except HeaderError as exc:
            raise WorldLoadError(STAGE_HEADER, type(exc).__name__) from exc

        try:
            body = decompress_body(data, parsed.body_offset, header_version=parsed.header_version)
        except ChunkError as exc:
            raise WorldLoadError(STAGE_CHUNKS, type(exc).__name__) from exc

        mapping, warnings = _resolve_property_map(property_map)

        try:
            table = _walk_body(body.payload, parsed, mapping, body_layout)
            # THE SECOND PASS, INSIDE THE SAME GUARD AND WHILE THE PAYLOAD IS
            # STILL IN SCOPE. It is the same stage - the same bytes, walked
            # twice for two different facts - so an overrunning extent reaches
            # the caller as the object stage's refusal with no new stage and no
            # new taxonomy. See the module docstring for why an overrun is fatal
            # here where an unreadable payload is flagged and carried.
            properties = _decode_properties(body.payload, table, mapping)
        except ObjectError as exc:
            # THE BODY IS NOT DROPPED HERE ANY MORE, AND THAT IS A REPAIR RATHER
            # THAN A RELAXATION. This handler used to carry its own `del body`,
            # on the stated grounds that it was the only handler in which the
            # name was bound. That was never true - every other way out of this
            # function after the chunk stage kept it - and the guard at the
            # bottom now drops it on EVERY exit, which strictly dominates this
            # one. Two scrubs where one suffices is worse than it sounds: the
            # redundant one cannot be measured, because removing it changes
            # nothing, and an unmeasurable scrub is indistinguishable from a
            # scrub that never worked. Measured: with both present, deleting
            # either left the suite green.
            raise WorldLoadError(STAGE_OBJECTS, type(exc).__name__) from exc

        unlocks, unlock_warnings = _read_unlocks(table, properties)
        nodes, node_warnings = _nodes_from(table)

        warnings.extend(unlock_warnings)
        if nodes:
            warnings.append(_warning(SOURCE_WORLD, WARN_NODE_SEMANTICS_UNAVAILABLE, len(nodes)))
        warnings.extend(node_warnings)

        return WorldModel(
            token=parsed.world_token,
            header=parsed,
            objects=table,
            unlocks=unlocks,
            nodes=nodes,
            warnings=(*_carried(parsed, body, mapping, table), *warnings),
            properties=properties,
            parents=_parent_targets(table),
        )
    except BaseException:
        del data
        # THE BODY GOES ON EVERY WAY OUT, NOT ONLY THE OBJECT STAGE'S.
        # `del body` in the ObjectError handler covers the one refusal that was
        # thought about; a usmap refusal, a node or unlock failure, the
        # `WorldModel` construction itself, or any exception type a later edit
        # introduces all reach HERE with the decompressed body still bound.
        # `DecompressedBody.__repr__` withholds its payload, which is why no
        # repr-based arm reddened - but a withholding repr is a MITIGATION and
        # this rule is about what the frame HOLDS, not about what it renders.
        # The name is unbound if the header stage refused first, so the drop is
        # conditional: an UnboundLocalError here would replace the real refusal.
        if "body" in locals():
            del body
        raise


def _carried(
    parsed: SaveHeader,
    body: DecompressedBody,
    mapping: PropertyMap | None,
    table: ObjectTable,
) -> tuple[WorldWarning, ...]:
    """Normalise every sub-layer's advisories into the one stream.

    THE SUBJECT IS CARRIED FROM THE TWO LAYERS THAT HAVE ONE and left None for
    the two that do not. ``header.HeaderWarning`` and ``usmap.UsmapWarning``
    each declare a ``subject``; ``chunks.ChunkWarning`` and
    ``objects.ObjectWarning`` declare none, so there is nothing to carry and
    None says exactly that. Inventing a token for them - the class path, the
    offset, the empty string - would put a value in a field whose whole purpose
    is that the ORIGINATING layer chose it.

    Args:
        parsed: The header, for its warnings.
        body: The decompressed body, for its warnings.
        mapping: The property map, for its warnings. May be None.
        table: The object table, for its warnings.

    Returns:
        Every carried warning, header first and in layer order.
    """
    out: list[WorldWarning] = [
        WorldWarning(source=SOURCE_HEADER, code=item.code, detail=item.detail, subject=item.subject)
        for item in parsed.warnings
    ]
    out.extend(
        WorldWarning(source=SOURCE_CHUNKS, code=item.code, detail=item.detail, count=item.count)
        for item in body.warnings
    )
    if mapping is not None:
        out.extend(
            WorldWarning(
                source=SOURCE_USMAP,
                code=item.code,
                detail=item.detail,
                subject=item.subject,
                count=item.count,
            )
            for item in mapping.warnings
        )
    out.extend(
        WorldWarning(source=SOURCE_OBJECTS, code=item.code, detail=item.detail)
        for item in table.warnings
    )
    return tuple(out)


def load_world(
    path: Path | str,
    *,
    property_map: PropertyMap | None = None,
    body_layout: str = BODY_LAYOUT_LEVELLED,
) -> WorldModel:
    """Copy a save out of harm's way, then parse it.

    THE COPY IS NOT A COURTESY. The game holds handles during autosave, so
    parsing in place eventually meets a locked or half-written file.
    ``workdir.copy_for_read`` owns that copy and is the ONLY module in this
    package with a write - which is what makes "no other save module writes" a
    static assertion rather than a rule reviewers have to remember.

    This function opens for READ ONLY, in binary, and nothing else. The save
    directory is never opened for write for any reason (non-negotiable 1).

    Args:
        path: The save to load. May be the save in place; it is copied first.
        property_map: As :func:`load_world_from_bytes`.
        body_layout: As :func:`load_world_from_bytes`.

    Returns:
        The world model.

    Raises:
        WorldLoadError: The copy failed, or any sibling refused the bytes.
        ValueError: ``body_layout`` is not one of :data:`BODY_LAYOUTS`. Checked
            HERE as well as downstream, so a caller's typo is not paid for with
            a file copy first and is not masked by a copy that fails for its own
            unrelated reason.
    """
    _checked_layout(body_layout)

    try:
        copy = copy_for_read(Path(path))
    except WorkDirError as exc:
        raise WorldLoadError(STAGE_COPY, type(exc).__name__) from exc

    with copy.open("rb") as handle:
        data = handle.read()

    # THE SAME SCRUB AS :func:`load_world_from_bytes`, AND FOR THE SAME REASON.
    # This frame reads the whole file into a local of its own and hands it down,
    # so a refusal raised below unwinds through TWO frames holding the same raw
    # save - and a renderer showing locals prints the header's plaintext options
    # string out of either one (non-negotiable 12). Repairing only the callee
    # would have left this frame leaking on exactly the same failures.
    # tests/save/test_world.py::test_no_clockspeed_frame_holds_the_raw_save_when_
    # the_path_loader_refuses drives it through a real file on disk.
    #
    # A REFUSED SAVE'S COPY GOES WITH THE REFUSAL (CS-1309 F4). The refusal is
    # the whole answer about these bytes - the dashboard's provider remembers
    # it rather than copying again - so the copy has no later reader, and a
    # fallback walk past a run of refused saves used to leave one full-size
    # copy per save in the work root for good. A copy of a save that LOADED is
    # kept, as before. ``workdir.discard_copy`` removes only a file in its own
    # copies directory carrying its own suffix, never anything in the save
    # directory.
    try:
        return load_world_from_bytes(data, property_map=property_map, body_layout=body_layout)
    except BaseException:
        del data
        discard_copy(copy)
        raise


def _refusal_subject(refusal: WorldLoadError) -> str:
    """Name a refused save by WHY it was refused, never by anything about the file.

    The file name is ``<world>_<...>.sav`` and its directory is the platform
    account id; its size and its write time say when the operator last played
    and single one file out of a listing. None of them is a subject
    (non-negotiables 3 and 12). The two fields read here are both closed
    vocabulary - a stage constant and an exception class name - and
    ``tests/save/test_newest_world.py`` grades this function's syntax tree for
    reading anything else.

    Args:
        refusal: The typed refusal.

    Returns:
        ``<stage>.<cause type>``.
    """
    return f"{refusal.stage}.{refusal.cause_type}"


def _refusal_flags(subjects: Iterable[str], code: str) -> tuple[WorldWarning, ...]:
    """One fallback flag per distinct subject, counting its saves.

    A run of saves refused the same way is ONE line on the panel carrying how
    many, not one identical line per file - the subject no longer tells them
    apart, by design, so repeating it would add rows and no information. The
    detail is the line for one save or for several, so it agrees with the
    count without spelling it.

    FAIL CLOSED ON THE VOCABULARY (CS-1309 F-C). The syntax-tree grade on
    :func:`_refusal_subject` proves what THAT function reads, and nothing about
    what reaches it: a refusal whose ``cause_type`` was rewritten anywhere
    between the reader and here would pass it. So every subject is checked
    HERE, where the flag is built, against :data:`SAVE_VERDICT_STAGES` and
    :data:`READER_REFUSAL_TYPES`, and one outside either refuses the whole
    walk rather than reaching the panel.

    Args:
        subjects: One subject per skipped save, newest first.
        code: :data:`WARN_NEWER_SAVE_REFUSED` or
            :data:`WARN_NEWEST_SAVE_UNIDENTIFIED`.

    Returns:
        The flags, in the order each subject was first met.

    Raises:
        ValueError: A subject outside the closed vocabulary. The message names
            no value.
    """
    counted: dict[str, int] = {}
    for subject in subjects:
        stage, _, cause = subject.partition(".")
        if stage not in SAVE_VERDICT_STAGES or cause not in READER_REFUSAL_TYPES:
            raise ValueError("a refusal subject outside the closed vocabulary was refused")
        counted[subject] = counted.get(subject, 0) + 1
    return tuple(
        WorldWarning(
            source=SOURCE_WORLD,
            code=code,
            detail=_FALLBACK_DETAIL[(code, count > 1)],
            subject=subject,
            count=count,
        )
        for subject, count in counted.items()
    )


def _with_flags(model: WorldModel, flags: tuple[WorldWarning, ...]) -> WorldModel:
    """Return a copy of ``model`` whose warnings end with ``flags``.

    EVERY FIELD IS CARRIED BY ENUMERATION, so a field added to
    :class:`WorldModel` later is copied rather than silently reset to its
    default. Spelled with ``fields`` rather than ``dataclasses.replace``
    because the save package's write scanner bans the call NAME ``replace``
    outright - it is ``os.replace`` and ``Path.replace`` - and that ban is
    kept exact rather than argued around.

    Args:
        model: The world the walk loaded.
        flags: The fallback flags, newest skipped save first.

    Returns:
        The copy.
    """
    carried = {field.name: getattr(model, field.name) for field in fields(model) if field.init}
    carried["warnings"] = (*model.warnings, *flags)
    return type(model)(**carried)


def refuse_again(stage: str, cause_type: str) -> NoReturn:
    """Raise a FRESH refusal rebuilt from two closed-vocabulary words.

    WHY A REMEMBERED VERDICT IS NOT THE REFUSAL ITSELF (CS-1309 F-A). A
    reader's refusal is raised ``from`` the reader's own error, and that error
    can carry a suppressed ``__context__`` - a ``UnicodeDecodeError`` whose
    ``object`` holds the very bytes that failed to decode, up to a whole
    header string: a world token, a level name. ``from None`` hides it from a
    printed traceback and keeps it on the object. A memo holding the refusal
    therefore held save bytes for as long as the file was unchanged, and its
    ``repr`` printed them. The dashboard's provider now keeps only the stage
    and the cause type and calls this to raise the verdict again.

    Both words are checked before anything is built, and the refusal is raised
    ``from None`` OUTSIDE any handler, so it carries no cause and no context:
    nothing but the two words, which the message renders.

    Args:
        stage: One of :data:`SAVE_VERDICT_STAGES`.
        cause_type: One of :data:`READER_REFUSAL_TYPES`.

    Raises:
        WorldLoadError: Always, built from the two words.
        ValueError: A word outside its closed vocabulary. The message names no
            value.
    """
    if stage not in SAVE_VERDICT_STAGES:
        raise ValueError("a remembered stage outside the closed vocabulary was refused")
    if cause_type not in READER_REFUSAL_TYPES:
        raise ValueError("a remembered cause type outside the closed vocabulary was refused")
    raise WorldLoadError(stage, cause_type) from None


def read_world_token(path: Path | str) -> str | None:
    """The world token a save's header names, or None when it names none.

    The walk's way to ask WHICH WORLD a save belongs to without parsing its
    body (CS-1309 F2): a copy, as every read of a save is, then the header's
    bounded prefix, then the copy is discarded - the token is the whole answer
    and the copy has no later reader. A save whose body the reader refuses
    still names its world here, because only its header is read.

    THE TOKEN IS RETURNED AND GOES NOWHERE ELSE. The walk compares it for
    equality and never renders it; no flag, message or log built from it
    exists. It is the same value :attr:`WorldModel.token` already holds.

    Args:
        path: The save. Copied first; never read in place.

    Returns:
        The token, or None when the copy or the header read failed for any
        reason - a header the reader refuses, a file the game holds, a file
        that vanished.
    """
    try:
        copy = copy_for_read(Path(path))
    except WorkDirError:
        return None
    try:
        return read_header(copy).world_token
    except HeaderError:
        return None
    finally:
        discard_copy(copy)


def _of_another_world(
    path: Path, world_token: str | None, identify: Callable[[Path], str | None]
) -> bool:
    """Whether ``path`` is KNOWN to be a save of a world other than ``world_token``.

    A save whose header names no world is not known to be another one, so the
    walk loads it - and the loaded world's own token is checked again, which
    is what keeps a save rewritten between the two reads from being served.

    Args:
        path: The candidate.
        world_token: The refused newest save's world, or None when unknown.
        identify: Reads the world token a save's header names, or None.

    Returns:
        True only when both worlds are known and differ.
    """
    if world_token is None:
        return False
    seen = identify(path)
    return seen is not None and seen != world_token


def load_newest_world(
    candidates: Iterable[Path],
    *,
    load: Callable[[Path], WorldModel] = load_world,
    identify: Callable[[Path], str | None] = read_world_token,
) -> WorldModel | None:
    """Load the newest save the reader accepts, flagging every newer one it refused.

    THE DEFECT THIS EXISTS FOR. The newest file in a save directory is not
    always a save the game wrote: one re-encoded by a third-party tool is
    refused by the object reader, correctly. Picking the newest file and
    stopping there turned that one refusal into no world at all. Non-negotiable
    7: unknown content is flagged and skipped, never fatal, never silently
    wrong - so the walk moves to the next candidate and the world it returns
    carries a flag for what it skipped.

    ONLY THE REFUSED NEWEST SAVE'S OWN WORLD, WHEN THAT WORLD IS KNOWN
    (CS-1309 F2, decided by the merger). An account directory holds every
    world the operator plays, so the next readable save is not necessarily the
    same world.

    - DECISION. When the newest save is refused at a stage AFTER its header -
      chunks or objects - its world token was readable, so it is read again
      through ``identify`` and the walk falls back ONLY to saves of that world:
      another world's save is skipped unread, and a loaded save of another
      world is not served. With no readable save of that world the walk ends
      exactly as when every candidate refused - no world. A token that was
      readable but cannot be recovered now (``identify`` answers None) ends
      the walk the same way, so a transient failure never serves another
      world. When the newest save is refused AT the header, its world is
      unknown: the newest readable save is served, whatever its world, under
      :data:`WARN_NEWEST_SAVE_UNIDENTIFIED`, whose detail says the world shown
      may be a different one. A known-world fallback carries
      :data:`WARN_NEWER_SAVE_REFUSED`. No flag names either world.
    - ALTERNATIVES REJECTED. Falling back across worlds under the "behind the
      game" flag is false advice about a different world. Refusing whenever
      the newest world is unknown leaves a dead dashboard after any
      header-format game update. Naming which world is served is a leak of a
      world token or a world name (non-negotiables 3 and 12).
    - WHY. Never silently wrong (non-negotiable 7) where the walk knows enough
      to be right, and honestly flagged where it cannot.

    ONLY A VERDICT ON THE BYTES FALLS BACK. A :class:`WorldLoadError` whose
    stage is in :data:`SAVE_VERDICT_STAGES` is skipped. Any other stage - the
    copy, which is the environment, and the property map, which is the install
    - says nothing about the save, and falling back past it would serve an
    older world while the newer one is readable. Such a failure STOPS the walk:
    from the newest candidate it propagates; from a later one, the newest
    refusal already met is raised instead, because that is what a caller is
    told whenever the walk ends without a world. Every exception that is not a
    ``WorldLoadError`` propagates unchanged.

    NO CAP. The walk goes on while a candidate remains, because "the newest
    save the reader accepts" is the contract and a cap that hands back no world
    while a readable save remains is the defect again. It stops at the first
    save that loads, and a caller that walks repeatedly - the dashboard's
    provider - remembers the verdicts and the world tokens by file identity,
    so a long run of refused files costs one parse each, once.

    DETERMINISTIC. Candidates are tried in the order given -
    ``workdir.ranked_saves`` hands them over newest first with ties broken by
    name - so two runs over one directory skip the same saves.

    Args:
        candidates: Saves to try, newest first.
        load: Loads one save. Injectable so the walk is graded without a game.
        identify: Reads the world token a save's header names, or None.
            Injectable for the same reason; consulted only once the newest
            save was refused after its header, and only for equality.

    Returns:
        The first world that loads and qualifies - the loader's own object
        when nothing was skipped, otherwise a copy carrying the flags after its
        own warnings - or None when there is no candidate at all.

    Raises:
        WorldLoadError: The NEWEST refusal - exactly what a single load of the
            newest raised before - when no candidate qualifies, or when a later
            candidate failed at a stage that is no verdict on its bytes; or the
            newest candidate's own failure at such a stage.
        ValueError: A refusal outside the closed vocabulary - see
            :func:`_refusal_flags`.
    """
    subjects: list[str] = []
    newest_refusal: WorldLoadError | None = None
    world_token: str | None = None
    for path in candidates:
        if _of_another_world(path, world_token, identify):
            continue
        try:
            model = load(path)
        except WorldLoadError as refusal:
            if refusal.stage not in SAVE_VERDICT_STAGES:
                if newest_refusal is None:
                    raise
                break
            subjects.append(_refusal_subject(refusal))
            if newest_refusal is not None:
                continue
            newest_refusal = refusal
        else:
            if world_token is not None and model.token != world_token:
                continue
            if not subjects:
                return model
            code = WARN_NEWEST_SAVE_UNIDENTIFIED if world_token is None else WARN_NEWER_SAVE_REFUSED
            return _with_flags(model, _refusal_flags(subjects, code))
        # Reached only for the newest refusal, and outside its handler, so the
        # read below runs with no exception in flight.
        if newest_refusal.stage != STAGE_HEADER:
            world_token = identify(path)
            if world_token is None:
                break
    if newest_refusal is not None:
        raise newest_refusal
    return None
