"""CS-405 - what the serialized ``mInventoryPotential`` component carries.

WHAT THE EXPERIMENT IS. ADR 0005 settled that the overclock clock ceiling is in
no file on this machine, and left ONE integer operand unmeasured - the shard
slot count. It kept exactly one route open: ``mInventoryPotential`` at
``FGBuildableFactory.h:663`` is declared ``EditDefaultsOnly, SaveGame``, so the
potential inventory component of a built overclockable building IS serialized.
If its serialized form carries a slot count, that is a direct measurement of
the missing operand. ADR 0005 labelled that UNVERIFIED and filed it as a
phase-4 experiment. This module runs it, and ADR 0009 records what it found.

WHAT THE TAG WAS ALREADY MEASURED TO BE, AND WHY THAT IS NOT THE ANSWER.
``mInventoryPotential`` decodes as an ``ObjectProperty`` - a level string and an
object path - and not as a bare integer. That refutes the naive reading of YES
without establishing NO, because a count may live BEHIND the reference, in the
record the path names. Following the reference is what CS-831 shipped and what
this module consumes.

THE POPULATION IS THE TAG, NOT THE SUCCESSFUL RESOLUTION, on the reasoning
``tests/save/test_reference_resolution.py`` states at length: counting only the
tags that landed would let the decoder choose its own denominator. Every
``mInventoryPotential`` tag the shipped reader walks past enters the count and
lands in exactly one of RESOLVED, UNRESOLVED or UNDECODED.

THE TAG WALK IS NAME-AWARE AND THE PUBLIC READER IS NOT, which is why this
module walks tags itself rather than summing ``PropertyResult`` counters. The
shipped refusal counter is not narrowed by property name - it counts every
``ObjectProperty`` tag that disagreed with its declared size - so it cannot be
attributed to this population from a result alone. The walk here uses the
shipped reader, the shipped decoder and the shipped reference narrowing, and
contributes only the name filter and the buckets.

THE TARGET IS THE RECORD THE REFERENCE NAMES, read with the shipped public
reader. What is measured on it is the SHAPE of what it carries: how many
top-level tags decoded, how many of those names fall in the slot-count
vocabulary ADR 0005 fixes, how many carry an integer at all, how many tags
remain of a type whose value encoding is unmeasured, how many onward reference
tags there are for the chain to continue through, and what the containers on
it bound - which, since CS-1038, includes the struct-element interiors they
bound and now READ.

THESE ASSERTIONS ARE THE RE-RUN TRIGGER AND ARE MEANT TO REDDEN. The library
grows whenever the operator plays, and ADR 0009's outcome holds only while the
shape below holds. A red run here is the signal to supersede that ADR with the
new reading rather than a defect in this file - so a later reader repairing a
failure by weakening an assertion has thrown away the finding.

WHICH CASE CATCHES WHICH CHANGE IS NOT WRITTEN DOWN, here or in ADR 0009. That
is ADR 0008: a detection claim is a measured fact about the suite, CLAUDE.md
section 4 forbids restating a measured fact in prose, and a sentence naming the
case that reddens under a given fault rots on the next rename. Each case below
states what IT asserts and what a failure OF IT would mean, in its own
docstring, next to its own assertions, where the claim cannot outlive them.

NO COUNT FROM THIS SWEEP IS WRITTEN INTO THIS FILE'S PROSE. Every figure is
taken over the operator's own live library, which grows on each autosave, so a
corpus number in a docstring is false on a timer - CLAUDE.md section 4, and a
docstring is prose. The numbers are derived on every run instead.

WHAT MAY BE NAMED HERE AND WHY. ``mInventoryPotential`` and the ceiling
operands are FORMAT IDENTIFIERS, and ADR 0005's licence position records the
identifiers, the member paths and the paraphrased semantics as committable
facts about a data format. No save byte, no player string, no path and no
account id reaches any assertion message: the sweep reduces every save to
integers inside its own frame before returning.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects
from tests.save import reach_guard, test_decode_oracles, test_properties

#: The tag ADR 0005 sends this experiment after, spelled as the payload spells
#: it. A FORMAT IDENTIFIER - ADR 0005 cites the declaration at
#: ``FGBuildableFactory.h:663`` and records the identifiers as committable.
POTENTIAL_TAG_NAME: Final = "mInventoryPotential"

#: The type word whose interior CS-829 measured and CS-1038 carried inside a
#: container element. This experiment CONSUMES that reading and grades none of
#: it: what it counts is how many element interiors came back, never what any of
#: them says.
STRUCT_TYPE_WORD: Final = "StructProperty"

#: The names a slot count would arrive under if the component carried one.
#: These are the ceiling equation's operands as ADR 0005 names them, plus the
#: override flag that gates the per-building one. THE SET IS THE QUESTION: a
#: target bearing any of these keys is the YES outcome, and a target bearing
#: none of them over the whole population refutes YES at the top level.
#:
#: NAMING THEM HERE IS NOT THE THING ADR 0006 FENCES. That fence forbids the
#: four from ``clockspeed/data/registry.py``, whose job is to publish fields a
#: solver reads, and the test asserting it is scoped to that module's own
#: string constants. Here they are a SEARCH VOCABULARY, and nothing in this
#: file publishes, stores or computes with a value found under any of them.
SLOT_COUNT_KEYS: Final = frozenset(
    {
        "mPotentialShardSlots",
        "mDefaultPotentialShardSlots",
        "mOverridePotentialShardSlots",
        "mMaxPotential",
        "mExtraPotential",
    }
)


# ---------------------------------------------------------------------------
# The real library - skip-if-absent, counts only
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PotentialSweep:
    """COUNTS ONLY. No field here can hold a path, a name or a value.

    Attributes:
        saves: How many saves of a tagged pair were walked.
        records: How many records the tag walk was asked about.
        abandoned: Payloads the shipped walk broke on before a terminator. A
            record abandoned here contributes no tag, so this is carried rather
            than discarded - a population shrinking silently is the failure
            mode the tag denominator exists to prevent.
        tags: ``mInventoryPotential`` reference TAGS walked past. The
            denominator the decoder cannot shrink.
        resolved: Tags whose object path is borne by a record in the same save.
        unresolved: Tags that decoded and matched no record.
        unresolved_empty_path: Of those, how many carry an EMPTY object
            path. A null reference rather than a missing target - the
            building has no potential inventory component at all. Counted
            apart because the two mean different things and a bucket
            holding both explains neither.
        undecoded: Tags whose bytes yielded no pair at all.
        ambiguous: Resolutions onto a path borne by more than one record. A
            subset of ``resolved`` and not a fourth bucket.
        targets: Distinct target RECORDS read, deduplicated per save by payload
            offset, so a component referenced twice is read once.
        target_keys: Top-level property names the targets decoded, summed.
        slot_keyed_targets: Targets carrying at least one name in
            :data:`SLOT_COUNT_KEYS`. THE DECIDER.
        int_valued_keys: Decoded top-level values on the targets that are a
            python ``int`` and not a ``bool``, summed. A slot count would be
            one of these, so zero here bounds the answer from the other side -
            it is not merely "not under those names" but "no integer at all".
        targets_with_unmeasured: Targets carrying at least one tag whose value
            encoding this project does not decode.
        unmeasured_tags: Those tags, summed over every target.
        onward_reference_tags: ``ObjectProperty`` tags ON the targets, summed.
            Non-zero would mean the chain continues past the component.
        container_tags: Decoded container values on the targets, summed.
        container_elements: Element halves those containers bounded, summed.
        decoded_elements: Bounded elements this project read a value from.
        undecoded_elements: Bounded elements it read no value from - None means
            NOT DECODED HERE and never EMPTY, per ``objects.ContainerElement``.
        struct_elements: Bounded elements whose own type word is
            :data:`STRUCT_TYPE_WORD`. Held against ``struct_valued_elements``
            and ``undecoded_elements`` so every one of them is accounted for as
            READ or as SKIPPED, rather than left as a remainder.
        struct_valued_elements: Bounded elements that decoded to an
            ``objects.StructValue`` - a struct element whose interior CS-1038
            read. A subset of ``struct_elements`` and of ``decoded_elements``:
            no other element word can produce one, and a struct element that
            was bounded by a DERIVED width is refused and stays undecoded.
        int_valued_elements: Decoded element values that are an ``int`` and not
            a ``bool``. The same bound as ``int_valued_keys``, one level down.
        pair_tags: Version pair to how many tags it contributed, sorted. A
            FORMAT FACT - the pairs are already public in
            ``test_properties.TAGGED_PAIRS``.
        failures: Exception TYPE NAMES, and nothing else about them.
    """

    saves: int
    records: int
    abandoned: int
    tags: int
    resolved: int
    unresolved: int
    unresolved_empty_path: int
    undecoded: int
    ambiguous: int
    targets: int
    target_keys: int
    slot_keyed_targets: int
    int_valued_keys: int
    targets_with_unmeasured: int
    unmeasured_tags: int
    onward_reference_tags: int
    container_tags: int
    container_elements: int
    decoded_elements: int
    undecoded_elements: int
    struct_elements: int
    struct_valued_elements: int
    int_valued_elements: int
    pair_tags: tuple[tuple[tuple[int, int], int], ...]
    failures: tuple[str, ...]


_SWEEP_KEYS: Final = (
    "saves",
    "records",
    "abandoned",
    "tags",
    "resolved",
    "unresolved",
    "unresolved_empty_path",
    "undecoded",
    "ambiguous",
    "targets",
    "target_keys",
    "slot_keyed_targets",
    "int_valued_keys",
    "targets_with_unmeasured",
    "unmeasured_tags",
    "onward_reference_tags",
    "container_tags",
    "container_elements",
    "decoded_elements",
    "undecoded_elements",
    "struct_elements",
    "struct_valued_elements",
    "int_valued_elements",
)


def _is_plain_int(value: object) -> bool:
    """Report whether a decoded value is an integer and not a boolean.

    ``bool`` IS AN ``int`` IN PYTHON, and a component full of flags would
    otherwise read as a component full of candidate slot counts. Excluding it
    is what makes a zero here mean something.

    Args:
        value: A decoded property or element value.

    Returns:
        True when the value is an integer that is not a boolean.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _fold_elements(value: objects.ContainerValue, into: dict[str, int]) -> None:
    """Fold one decoded container's elements into the accumulator.

    Args:
        value: The decoded container.
        into: The accumulator, mutated in place.
    """
    into["container_tags"] += 1
    into["container_elements"] += len(value.elements)
    for element in value.elements:
        if element.value is None:
            into["undecoded_elements"] += 1
        else:
            into["decoded_elements"] += 1
            if _is_plain_int(element.value):
                into["int_valued_elements"] += 1
        if element.type_word == STRUCT_TYPE_WORD:
            into["struct_elements"] += 1
        if isinstance(element.value, objects.StructValue):
            into["struct_valued_elements"] += 1


def _fold_target(result: objects.PropertyResult, into: dict[str, int]) -> None:
    """Fold ONE target component's decoded shape into the accumulator.

    IT TAKES A DECODED RESULT AND EMITS INTEGERS. Nothing here returns, stores
    or renders a property name or a value; the membership test against
    :data:`SLOT_COUNT_KEYS` is done and discarded inside this frame.

    Args:
        result: What the shipped reader made of the target record.
        into: The accumulator, mutated in place.
    """
    into["targets"] += 1
    into["target_keys"] += len(result.properties)
    into["unmeasured_tags"] += result.unmeasured_value_count
    into["onward_reference_tags"] += result.reference_tag_count
    if result.unmeasured_value_count:
        into["targets_with_unmeasured"] += 1
    if not SLOT_COUNT_KEYS.isdisjoint(result.properties):
        into["slot_keyed_targets"] += 1
    for value in result.properties.values():
        if _is_plain_int(value):
            into["int_valued_keys"] += 1
        if isinstance(value, objects.ContainerValue):
            _fold_elements(value, into)


def _collect_potential_tags(
    body: bytes,
    record: objects.ObjectRecord,
    index: objects.RecordIndex,
    into: dict[str, int],
    found: dict[int, objects.ObjectRecord],
) -> None:
    """Walk one record's tags, keep the potential ones, and bucket each.

    IT SHARES THE WALK, THE ADVANCE, THE DECODER AND THE NARROWING WITH THE
    SHIPPED READER and contributes only the name filter and the buckets, so it
    grades none of those - it consumes them. That is the same boundary
    ``tests/save/test_reference_resolution.py`` draws around its second join.

    Args:
        body: The decompressed body.
        record: The record whose payload to walk.
        index: The shipped record index for the same save.
        into: The accumulator, mutated in place.
        found: Target payload offset to the record, mutated in place, so a
            component referenced twice in one save is read once.
    """
    end = record.body_offset + record.body_length
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
    if start is None:
        into["abandoned"] += 1
        return
    tags = test_decode_oracles._walk_with_the_shipped_reader(body, start, end)  # noqa: SLF001
    if tags is None:
        into["abandoned"] += 1
        return
    for name, word, at, size in tags:
        if word != objects.REFERENCE_TYPE_WORD or name != POTENTIAL_TAG_NAME:
            continue
        into["tags"] += 1
        value = objects._decode_value(body, word, at, size, None)  # noqa: SLF001
        reference = objects._as_reference(name, value)  # noqa: SLF001
        if reference is None:
            into["undecoded"] += 1
            continue
        targets = index.records_for(reference.object_path)
        if not targets:
            into["unresolved"] += 1
            if not reference.object_path:
                into["unresolved_empty_path"] += 1
            continue
        into["resolved"] += 1
        if len(targets) > 1:
            into["ambiguous"] += 1
        for target in targets:
            found.setdefault(target.body_offset, target)


def _sweep_one_save(
    data: bytes,
    parsed: header.SaveHeader,
    property_map: object,
    into: dict[str, int],
    pairs: dict[tuple[int, int], int],
) -> None:
    """Walk one save, follow every potential reference, and fold the targets.

    THE CALLER HOLDS THE ``try``, on the terms
    ``tests/save/test_reference_resolution.py`` states: this function is
    allowed to raise, and its only call site reduces whatever comes out to a
    type name before any frame holding ``data`` or ``body`` is rendered.

    Args:
        data: The save file's bytes.
        parsed: Its parsed header.
        property_map: The shipped mapping, which this sweep supplies on purpose.
            ``read_properties`` accepts None since CS-960 - see the caller's
            ``Returns`` clause for why this sweep does not take that path.
        into: The accumulator, mutated in place.
        pairs: Version pair to tag count, mutated in place.
    """
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    index = objects.index_records(table)
    into["saves"] += 1
    # Keyed by payload offset - an integer - so a component referenced by two
    # buildings is READ ONCE and no name leaves this frame.
    found: dict[int, objects.ObjectRecord] = {}
    before = into["tags"]
    for record in table.records:
        into["records"] += 1
        _collect_potential_tags(body, record, index, into, found)
    pair = (parsed.header_version, parsed.save_version)
    pairs[pair] = pairs.get(pair, 0) + into["tags"] - before
    for target in found.values():
        _fold_target(
            objects.read_properties(body, target, property_map),  # type: ignore[arg-type]
            into,
        )


@lru_cache(maxsize=1)
def _sweep_potential() -> _PotentialSweep | None:
    """Walk each real save once and return COUNTS ONLY.

    IT CONTAINS ``Exception`` AND ``SystemExit``, AND STOPS THERE, on the terms
    ``tests/save/test_decode_oracles.py`` argues at length: a save path, a body
    and an instance name are things pytest renders out of a frame it unwinds,
    and ``path.read_bytes()`` is a bound method whose ``self`` IS the save path.
    ``KeyboardInterrupt`` is deliberately left free to unwind.

    Returns:
        The sweep, or None when no save library is reachable or the shipped
        property mapping did not load. SINCE CS-960 THAT SECOND CONDITION IS A
        CHOICE THIS SWEEP MAKES RATHER THAN A REQUIREMENT IT INHERITS:
        ``read_properties`` decodes with no map at all, but it then reports
        resolution against no registry, and a sweep whose subject is what
        resolved may not quietly change what it resolved against.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    try:
        property_map = test_properties._cached_usmap_or_none()  # noqa: SLF001
    except (Exception, SystemExit):
        # Contained for the reason test_decode_oracles gives: the load opens a
        # file under the game install, so an uncontained type here unwinds
        # through a frame holding that path.
        property_map = None
    if property_map is None:
        return None

    into = dict.fromkeys(_SWEEP_KEYS, 0)
    pairs: dict[tuple[int, int], int] = {}
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file, and a save of a
            # version this project does not parse. The library legitimately
            # holds both, and any recorded failure is treated as fatal below.
            continue
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in test_properties.TAGGED_PAIRS:
            continue
        try:
            _sweep_one_save(data, parsed, property_map, into, pairs)
        except (Exception, SystemExit) as exc:
            # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
            # carrying the save bytes, which is the leak this containment
            # closes.
            failures.append(type(exc).__name__)
            continue
    # The names and the paths are JUDGED here and discarded here.
    return _PotentialSweep(
        pair_tags=tuple(sorted(pairs.items())),
        failures=tuple(sorted(set(failures))),
        **into,
    )


def _sweep_or_skip() -> _PotentialSweep:
    """Fetch the sweep, skipping when this machine cannot grade it.

    THREE MACHINE SHAPES SKIP, on the reasoning
    ``tests/save/test_reference_resolution.py`` sets out: no library at all, no
    shipped property mapping, and a library holding not one save of a version
    pair this project parses. "Absent" has to mean absent of anything
    gradeable rather than absent of files.

    THE FAILURE ASSERTION COMES FIRST so an unreadable library reddens rather
    than skipping quietly. Only an empty-but-clean walk skips.

    Returns:
        The sweep.
    """
    sweep = _sweep_potential()
    if sweep is None:
        pytest.skip(
            "no save library or no shipped property mapping on this machine - "
            "the inventory potential experiment is not gradeable here"
        )
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    if sweep.saves == 0:
        pytest.skip(
            "the save library holds no save of a version pair this project "
            "parses - the inventory potential experiment is not gradeable here"
        )
    return sweep


def _rendered(sweep: _PotentialSweep) -> str:
    """Render the whole sweep as integers, for an assertion message.

    EVERY FIELD IS A COUNT OR A VERSION PAIR, so this is safe to put in a
    failure message - which is the point of a counts-only sweep type.

    Args:
        sweep: The sweep.

    Returns:
        The rendering.
    """
    return repr(sweep)


def test_the_potential_population_exists_and_the_probe_ran() -> None:
    """The tag population is non-empty, so this is not the INCONCLUSIVE state.

    INCONCLUSIVE means the probe DID NOT RUN - no world in the library holds a
    built overclockable building with the component serialized at all. That is
    a legitimate outcome and it is NOT this one. Separating the two is the
    whole reason the population is asserted before anything is concluded from
    its shape.
    """
    sweep = _sweep_or_skip()

    assert sweep.tags > 0, (
        f"no {POTENTIAL_TAG_NAME} tag in the library - the probe did not run "
        f"and the outcome is INCONCLUSIVE rather than measured: {_rendered(sweep)}"
    )
    assert sweep.targets > 0, (
        f"tags resolved to no target record, so nothing was read: {_rendered(sweep)}"
    )


def test_every_potential_tag_lands_in_exactly_one_bucket() -> None:
    """The partition is total: every tag walked past is accounted for.

    THIS IS A REAL SUM AND NOT AN IDENTITY. The three buckets are incremented
    in one exhaustive branch here, but the total is incremented BEFORE that
    branch and off the walk, so a tag dropped between the two moves one side
    and not the other.
    """
    sweep = _sweep_or_skip()

    assert sweep.tags == sweep.resolved + sweep.unresolved + sweep.undecoded, (
        f"a potential tag was walked past and never bucketed: {_rendered(sweep)}"
    )
    assert sweep.ambiguous <= sweep.resolved, (
        f"ambiguity is a subset of resolution, not a fourth bucket: {_rendered(sweep)}"
    )
    assert sum(count for _, count in sweep.pair_tags) == sweep.tags, (
        f"the version-pair census disagrees with the tag total: {_rendered(sweep)}"
    )
    assert all(pair in test_properties.TAGGED_PAIRS for pair, _ in sweep.pair_tags), (
        f"a pair outside TAGGED_PAIRS contributed tags: {_rendered(sweep)}"
    )
    assert sweep.unresolved_empty_path <= sweep.unresolved, (
        f"more empty-path references than unresolved ones: {_rendered(sweep)}"
    )


def test_no_target_of_a_potential_reference_carries_a_slot_count_key() -> None:
    """CS-405's decider - the YES outcome, stated so the library can refute it.

    ADR 0005 option (b) survives exactly to the extent that the component the
    reference names carries the missing operand under one of the names the ADR
    fixes. Over the whole population it does not.

    THIS IS THE RE-RUN TRIGGER. If a slot count ever appears, this reddens, and
    that red is the signal to supersede ADR 0009 with the reading - not a
    defect here.
    """
    sweep = _sweep_or_skip()

    assert sweep.slot_keyed_targets == 0, (
        f"a target carries a slot-count key - ADR 0009 is superseded by the "
        f"reading, not by this failure: {_rendered(sweep)}"
    )


def test_no_target_carries_an_integer_valued_top_level_property() -> None:
    """The other side of the bound - no top-level integer, under any name.

    THE NAME VOCABULARY ALONE IS TOO WEAK to support an absence, because a
    count could be serialized under a name ADR 0005 never saw. This clause does
    not depend on the vocabulary: it asserts that not one decoded TOP-LEVEL
    value on any target is an integer. A slot count has to be an integer, so a
    top level with no integer in it carries no slot count whatever the names.

    ITS SCOPE IS THE TOP LEVEL AND STOPS THERE. The decoded container elements
    one level down DO include integers, and an earlier revision of this case
    asserted they did not. THAT ASSERTION WAS MEASURED FALSE against the
    library on the run that introduced it, and it is deleted rather than
    weakened: the honest reading of those integers is the whole reason ADR 0009
    records a bounded outcome instead of a flat NO, so an assertion that wished
    them away would have manufactured the stronger result.
    """
    sweep = _sweep_or_skip()

    assert sweep.int_valued_keys == 0, (
        f"a target carries an integer-valued top-level property, which the "
        f"slot-count vocabulary would have missed: {_rendered(sweep)}"
    )


def test_the_integer_elements_below_the_top_level_are_unattributed() -> None:
    """What stops this outcome being a flat NO, recorded rather than argued.

    THE CONTAINERS ON THE TARGETS BOUND INTEGER ELEMENTS. This module does not
    say what any of them means, and it must not: an element's semantics come
    from its container's own tag and from the struct interior beside it, and
    CS-829 owns that interior. Attributing one of these to the shard slot count
    would be an inference from shape, which is the class of move ADR 0005's
    fence list exists to stop.

    IT IS ASSERTED NON-ZERO SO THE LIMIT CANNOT BE QUIETLY LOST. A later reader
    who finds this red because the integers are gone is looking at a changed
    library or a changed decoder, and either way ADR 0009's bounded outcome has
    to be re-derived rather than assumed to have hardened into a NO.
    """
    sweep = _sweep_or_skip()

    assert sweep.int_valued_elements > 0, (
        f"no integer element remains below the top level - the outcome may now "
        f"be a flat NO, which is an ADR change rather than a green run: {_rendered(sweep)}"
    )
    assert sweep.int_valued_elements <= sweep.decoded_elements, (
        f"more integer elements than decoded elements: {_rendered(sweep)}"
    )


def test_every_top_level_tag_on_every_target_decodes() -> None:
    """What CS-830 changed, and what makes the outcome distinguishable.

    AN UNREAD TAG IS NOT AN ABSENT ONE - non-negotiable 7 flags rather than
    assumes - so "the top level carries no count" cannot be said while any tag
    on it is of a type this project does not decode. CS-830 brought the
    container words into ``objects.MEASURED_VALUE_TYPES``, and the residue at
    the top level went to nothing.

    THAT IS THE DIFFERENCE between "not yet measured" and "measured, and it is
    not there", and it is the reason this experiment could be concluded at all.
    """
    sweep = _sweep_or_skip()

    assert sweep.unmeasured_tags == 0, (
        f"a target carries a tag of an unmeasured type, so the top level is "
        f"not fully read and no absence may be concluded from it: {_rendered(sweep)}"
    )
    assert sweep.targets_with_unmeasured == 0, (
        f"a target carries unread top-level content: {_rendered(sweep)}"
    )
    assert sweep.target_keys > 0, (
        f"the targets decoded no property at all, which would make the "
        f"absence vacuous rather than measured: {_rendered(sweep)}"
    )


def test_the_container_decode_is_what_empties_the_unmeasured_residue() -> None:
    """CS-830's contribution here, as a counterfactual over THIS run's counts.

    THE DEPENDENCE IS MEASURED RATHER THAN RECOUNTED FROM HISTORY. Without the
    container words in ``objects.MEASURED_VALUE_TYPES`` every container tag on
    every target would be unread, so the top-level residue would be exactly
    ``container_tags`` rather than nothing. Asserting that number is positive
    is asserting that CS-830 is load-bearing for this experiment's conclusion -
    a claim derived from this run, not from a note about an earlier one.

    IT ALSO PINS THE MEMBERSHIP that makes it so, so a later change quietly
    dropping a container word from the measured set reddens here rather than
    silently reopening the residue.
    """
    sweep = _sweep_or_skip()

    assert set(objects.MEASURED_VALUE_TYPES) >= objects.CONTAINER_TYPE_WORDS, (
        "a container word left MEASURED_VALUE_TYPES, so the top-level residue "
        "this experiment reports as empty is no longer empty"
    )
    assert sweep.container_tags > 0, (
        f"no container on any target, so CS-830 changed nothing here and this "
        f"clause is vacuous: {_rendered(sweep)}"
    )
    assert sweep.target_keys > sweep.container_tags, (
        f"the targets carry nothing but containers, so the top level was never "
        f"read for anything else: {_rendered(sweep)}"
    )


def test_the_reference_chain_stops_at_the_target() -> None:
    """The residue is not another hop - the targets hold no onward reference.

    IF A TARGET CARRIED AN ``ObjectProperty`` this experiment would be
    unfinished rather than concluded, because the count could sit one record
    further on. It carries none, so the only unread thing left is interior.
    """
    sweep = _sweep_or_skip()

    assert sweep.onward_reference_tags == 0, (
        f"a target carries an onward reference tag, so the chain continues and "
        f"the experiment is not finished: {_rendered(sweep)}"
    )


def test_the_struct_element_residue_is_read_and_whatever_is_left_is_still_its_own() -> None:
    """THE RE-RUN THIS CASE ASKED FOR. CS-829's seam landed, so the residue moved.

    WHAT THIS CASE ASSERTED BEFORE, AND WHY IT WAS RIGHT THEN. CS-830 bounded
    and typed every element and deliberately read NO struct interior, so the
    unread elements were EXACTLY the struct elements and the case asserted that
    equality, plus ``undecoded_elements > 0`` to keep the bounded outcome from
    being quietly lost. Its own docstring said it would redden when CS-829
    landed and named that the correct signal to re-run. CS-1038 carried the
    measured interior grammar inside a container element and it reddened on
    schedule, with the unread count at zero.

    WHAT IT ASSERTS NOW. The equality is not weakened, it is REFINED: every
    struct element is either READ or SKIPPED, and nothing that is not a struct
    element is unread. A struct element whose half was bounded by a DERIVED
    width is a raw region rather than a tag list, and
    ``objects._decode_element_interior`` refuses it on purpose - that skip is
    non-negotiable 7 and is counted here rather than dropped, so it may exist
    without the residue stopping being wholly this seam's.

    ``undecoded_elements > 0`` IS DELETED RATHER THAN INVERTED, and its subject
    is what makes that the honest move: it asserted that SOMETHING was unread,
    and on this library nothing is. Inverting it to ``== 0`` would pin an
    absence that the derived-width skip above is entitled to break on the next
    autosave, which would be a false red rather than a finding.

    THE BOUNDED OUTCOME IS NOT LOST WITH IT, AND THE BOUND MOVED RATHER THAN
    CLOSED. ADR 0009 is bounded because content below the top level is read and
    NOT ATTRIBUTED, and there is now more of it, not less: the interiors
    themselves. THIS SWEEP DOES NOT SEARCH AN INTERIOR FOR A SLOT-COUNT KEY -
    :func:`_fold_target` reads :data:`SLOT_COUNT_KEYS` against the TOP LEVEL
    alone - so a target's interiors are read-and-unsearched rather than
    unread, and no flat NO may be concluded from this run. The non-attribution
    half is asserted by
    ``tests/save/test_inventory_potential.py::test_the_integer_elements_below_
    the_top_level_are_unattributed`` and is not restated here.

    ``struct_valued_elements > 0`` IS THE LIVENESS CONTROL. Without it every
    clause below is satisfied by a decoder that read no interior at all, which
    is precisely the state this case was written in.
    """
    sweep = _sweep_or_skip()

    assert sweep.container_tags > 0, (
        f"no container on any target, so there is no residue to attribute and "
        f"this clause is vacuous: {_rendered(sweep)}"
    )
    assert sweep.struct_elements > 0, (
        f"no struct element on any target, so the clauses below are vacuous "
        f"rather than satisfied: {_rendered(sweep)}"
    )
    assert sweep.struct_valued_elements > 0, (
        f"not one struct element yielded an interior, so the residue is unread "
        f"again and ADR 0009's bound is back where CS-830 left it: {_rendered(sweep)}"
    )
    assert sweep.struct_valued_elements + sweep.undecoded_elements == sweep.struct_elements, (
        f"the struct elements do not partition into READ and SKIPPED, so either "
        f"an element that is not a struct is unread - the residue is no longer "
        f"wholly this seam's - or a non-struct element published an interior: "
        f"{_rendered(sweep)}"
    )
    assert sweep.struct_valued_elements <= sweep.decoded_elements, (
        f"more interiors were read than elements decoded: {_rendered(sweep)}"
    )
    assert sweep.decoded_elements + sweep.undecoded_elements == sweep.container_elements, (
        f"an element is neither decoded nor undecoded: {_rendered(sweep)}"
    )


def test_the_target_population_is_bounded_by_the_resolved_tags() -> None:
    """Deduplication may shrink the target set and may never grow it.

    A COMPONENT REFERENCED BY TWO BUILDINGS IS READ ONCE, so ``targets`` is at
    most ``resolved``. More targets than resolutions would mean the fold ran on
    something the walk never resolved.
    """
    sweep = _sweep_or_skip()

    assert sweep.targets <= sweep.resolved, (
        f"more targets were read than references resolved: {_rendered(sweep)}"
    )


# ---------------------------------------------------------------------------
# Library reach declarations - reach_guard grades this module
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches. The
#: key is the function's own ``__name__`` and the reason comes from
#: ``reach_guard``, so a rename moves both together.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_potential.__name__: reach_guard.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard. EMPTY: no
#: case here breaks a primitive or applies one to something synthetic.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
