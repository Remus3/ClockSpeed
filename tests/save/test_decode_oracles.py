"""Oracles that grade the SHIPPED decode grammar rather than a copy of it.

WHY THIS MODULE EXISTS AND WHY IT IS NOT PART OF ``test_properties``. That
module transcribes the tag grammar - its own ``_TAG_EXTRA_STRINGS``, its own
``_STRUCT_GUID_BYTES``, its own reader - and walks the library with the copy.
That is the right shape for what it does, because a transcription that
disagrees with the module under test is exactly what its synthetic fixtures are
built to expose. But it has one consequence no test inside it can reach:

**A WIDTH THAT IS WRONG IN BOTH COPIES IS WRONG IN NEITHER TEST.** Mis-state
``ArrayProperty`` in ``clockspeed/save/objects.py`` and every assertion in
``test_properties`` still passes, because that module never reads the shipped
constant. Two copies of one belief are not two pieces of evidence - they are
one belief written twice, and the provenance oracles are blind to a fault they
share. CLAUDE.md section 5 names this directly: agreement between two agents is
not evidence when both derive from the same source.

So every walk in THIS module runs on the shipped reader. It holds no width of
its own: names come from ``objects._payload_text``, tag headers from
``objects._read_tag_header``, and the cursor advances by the value extent that
shipped header read reports. Break a shipped width and this module goes red.

THE THREE ORACLES ARE NOT INTERCHANGEABLE, and the difference is measured
rather than assumed:

  THE SHIPPED-WALK REACH is the only one of the three that discriminates the
  widths. It is checked as EQUALITY - every payload of every tagged pair
  reaches its terminator - because a ``> 0`` floor is known to survive a
  rotated alignment on this project's own corpus.

  THE CROSS-SECTION and THE USMAP JOIN are EXTERNAL evidence: one about the
  reference-to-record pairing, read out of a section a different cursor pass
  parsed; one about the name-to-type-word pairing, read out of a different FILE
  the game ships. Both are worth having and neither is a width check.

  IN PARTICULAR THE USMAP JOIN DOES NOT GUARD THE COMMON MODE, and believing it
  did would be the more dangerous error. Its bijection was measured against a
  mutant of every width in ``objects._TAG_EXTRA_STRINGS`` and it survived all
  of them with zero violations - under one of them byte-identically. The
  mechanism is plain once seen: a wrong width breaks the walk, a broken walk
  contributes no pairs at all, and the pairs that do survive are therefore all
  correct pairs. A bijection over a shrinking population of correct pairs stays
  pristine while the grammar rots. Only the reach test grades the widths.

THE JOIN IS FLAT - a tag name is joined to a ``type_id`` in the record's OWN
schema and the super chain is not walked. Walking the chain was measured too:
it joins strictly more tags and yields the same bijection, with no word
claiming two ids and no id claimed by two words. The flat join is kept because
it is the narrower claim of the two, not because the chain refuted anything.

PRIVACY, non-negotiables 11 and 12. Every helper that touches a real body is
called inside the sweep's own ``try``, discovery included, and a failure is
reported as a type NAME rather than as an object - a save path, a body, an
instance name and a decoded value are all things pytest would render out of a
frame it unwinds. Property names and type words are judged INSIDE the sweep and
discarded there; nothing below that line can render one. Only counts leave.

Every assertion here is a shape, a rate or a factor. No absolute count is
written down, because the corpus is the operator's own live library and it
grows on every autosave.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects, usmap

# IMPORTED, NEVER COPIED. ``_library_save_paths`` and ``_cached_usmap_or_none``
# each close a leak their own docstrings describe - the discovery calls that
# resolve the account directory sit inside their ``try`` - and a third
# transcription of that containment is a third place to get it subtly wrong.
# The module is imported whole rather than its names lifted, so that every use
# site says out loud which module the value came from. That matters most for
# the two transcribed constants, which are the SUBJECT of the last test here.
from tests.save import test_properties

#: The property terminator, as the shipped walk spells it.
_TERMINATOR: Final = "None"

#: The type word whose value names a saved object. SoftObjectProperty carries
#: the same two-string shape but names ASSETS, and was measured to resolve
#: against the record table at a flat zero, so it is not in this population.
_REFERENCE_WORD: Final = "ObjectProperty"

#: A decoded object reference is a level reference and an object path.
_REFERENCE_PARTS: Final = 2

#: Value-start deltas the reference is re-read at, with the TAG WALK HELD
#: FIXED. That is what makes the collapse evidence about the value grammar
#: rather than about payload attribution.
_REFERENCE_ROTATIONS: Final = (-1, 1)

#: The unrotated reading, named so the liveness floor and the collapse
#: assertions index the same mapping.
_TRUE_OFFSET: Final = 0

#: Keys into the joined-tag counter.
_TRUE_JOIN: Final = "true"
_SHIFTED_JOIN: Final = "shifted"


@dataclass(frozen=True)
class _JoinShape:
    """One join's shape, as counts only - never the words or the ids.

    Attributes:
        tags: How many tags joined.
        words: How many distinct type words the joined tags carried.
        ids: How many distinct raw type ids they paired with.
        words_to_many_ids: Words claiming more than one id. Zero is bijective.
        ids_to_many_words: Ids claimed by more than one word. Same.
    """

    tags: int
    words: int
    ids: int
    words_to_many_ids: int
    ids_to_many_words: int


@dataclass(frozen=True)
class _OracleSweep:
    """What one pass over the real library measured. COUNTS ONLY.

    Attributes:
        payloads: Records seen, by version pair.
        reached: Records whose payload reached its terminator under the
            SHIPPED reader, by version pair.
        references: Reference tags that decoded at all, by value-start delta.
        resolutions: Those whose object path named a record in the table, by
            the same delta.
        join: The flat usmap join's shape.
        shifted: The one-tag-shifted join's shape - the control.
        failures: Exception type NAMES, never the exceptions.
    """

    payloads: Mapping[tuple[int, int], int]
    reached: Mapping[tuple[int, int], int]
    references: Mapping[int, int]
    resolutions: Mapping[int, int]
    join: _JoinShape
    shifted: _JoinShape
    failures: tuple[str, ...]


@dataclass
class _Accumulators:
    """Everything one sweep folds into, mutated in place.

    Bundled rather than passed as loose arguments so that the per-save walker
    keeps a signature a reader can hold, and so that adding a measurement does
    not change every call site.

    Attributes:
        payloads: Records seen, by version pair.
        reached: Records whose payload reached a terminator, by version pair.
        references: Reference tags that decoded, by value-start delta.
        resolutions: Reference tags that resolved, by the same delta.
        joined: Distinct type word and raw type id pairs, truly paired.
        shifted: The same under the one-tag shift.
        join_tags: How many tags contributed to each join.
    """

    payloads: Counter[tuple[int, int]] = field(default_factory=Counter)
    reached: Counter[tuple[int, int]] = field(default_factory=Counter)
    references: Counter[int] = field(default_factory=Counter)
    resolutions: Counter[int] = field(default_factory=Counter)
    joined: set[tuple[str, int]] = field(default_factory=set)
    shifted: set[tuple[str, int]] = field(default_factory=set)
    join_tags: Counter[str] = field(default_factory=Counter)


def _walk_with_the_shipped_reader(
    body: bytes, start: int, end: int
) -> tuple[tuple[str, str, int, int], ...] | None:
    """Walk one payload's tags using the SHIPPED reader and no local width.

    THIS TRANSCRIBES NOTHING, which is the whole point of the module. The name
    read, the tag header and the tag-count ceiling are all shipped symbols; the
    only thing this function contributes is the loop and the cursor advance,
    and the advance is computed from what the shipped header read returned
    rather than from any width stated here.

    Args:
        body: The decompressed body.
        start: Where the first tag begins.
        end: The first byte past the payload.

    Returns:
        Every tag as name, type word, value start and declared size, or None
        when the walk broke before reaching a terminator.
    """
    tags: list[tuple[str, str, int, int]] = []
    at = start
    for _ in range(objects._MAX_TAGS_PER_PAYLOAD):  # noqa: SLF001
        name = objects._payload_text(body, at, end)  # noqa: SLF001
        if name is None:
            return None
        if name[0] == _TERMINATOR:
            return tuple(tags)
        read = objects._read_tag_header(body, name[1], end)  # noqa: SLF001
        if read is None:
            return None
        type_word, value_at, size, _in_tag_byte = read
        tags.append((name[0], type_word, value_at, size))
        at = value_at + size
    return None


def _tally_references(
    body: bytes,
    tags: tuple[tuple[str, str, int, int], ...],
    names: frozenset[str],
    into: _Accumulators,
) -> None:
    """Resolve every reference tag against the record table, true and rotated.

    The judgement is the SHIPPED decoder's own: ``_decode_value`` returns a
    pair only when the two strings account for the declared size exactly.

    Args:
        body: The decompressed body.
        tags: The payload's tags, from the unrotated walk.
        names: Every instance name in the table, from ``parse_body``.
        into: The accumulators, mutated in place.
    """
    for _name, type_word, value_at, size in tags:
        if type_word != _REFERENCE_WORD:
            continue
        for delta in (_TRUE_OFFSET, *_REFERENCE_ROTATIONS):
            value = objects._decode_value(  # noqa: SLF001
                body, type_word, value_at + delta, size, None
            )
            if not isinstance(value, tuple) or len(value) != _REFERENCE_PARTS:
                continue
            into.references[delta] += 1
            if value[1] in names:
                into.resolutions[delta] += 1


def _tally_join(
    tags: tuple[tuple[str, str, int, int], ...],
    flat: Mapping[str, int],
    into: _Accumulators,
) -> None:
    """Pair each tag name with a type word - its own, and the next tag's.

    THE SHIFTED PAIRING IS THE CONTROL. A join that is a genuine function of
    the type word must stop being one when the word is taken from the wrong
    tag; if it survives that, it was never measuring the pairing at all.

    Args:
        tags: The payload's tags, from the unrotated walk.
        flat: Property name to raw type id, from the record's OWN schema.
        into: The accumulators, mutated in place.
    """
    for index, (name, type_word, _value_at, _size) in enumerate(tags):
        type_id = flat.get(name)
        if type_id is None:
            continue
        into.join_tags[_TRUE_JOIN] += 1
        into.joined.add((type_word, type_id))
        if index + 1 < len(tags):
            into.join_tags[_SHIFTED_JOIN] += 1
            into.shifted.add((tags[index + 1][1], type_id))


def _shape_of(pairs: set[tuple[str, int]], tags: int) -> _JoinShape:
    """Reduce a set of pairs to counts, DISCARDING the words and the ids.

    Nothing downstream of this function can render a type word, which is what
    makes the module's "counts only" a mechanism rather than a promise.

    Args:
        pairs: The observed type word and raw type id pairs.
        tags: How many tags contributed.

    Returns:
        The shape.
    """
    words_to_ids: dict[str, set[int]] = {}
    ids_to_words: dict[int, set[str]] = {}
    for word, type_id in pairs:
        words_to_ids.setdefault(word, set()).add(type_id)
        ids_to_words.setdefault(type_id, set()).add(word)
    return _JoinShape(
        tags=tags,
        words=len(words_to_ids),
        ids=len(ids_to_words),
        words_to_many_ids=sum(1 for ids in words_to_ids.values() if len(ids) > 1),
        ids_to_many_words=sum(1 for words in ids_to_words.values() if len(words) > 1),
    )


def _schema_property_ids(
    property_map: usmap.PropertyMap | None, type_path: str
) -> Mapping[str, int] | None:
    """Map property name to raw type id for one record's OWN schema.

    FLAT - the super chain is not walked. See the module docstring for what
    walking it was measured to give.

    Args:
        property_map: The shipped mapping, or None when there is no install.
        type_path: The record's class path.

    Returns:
        The mapping, or None when the schema does not resolve.
    """
    if property_map is None:
        return None
    schema = property_map.schemas.get(objects.class_name_of(type_path))
    if schema is None:
        return None
    return {entry.name: entry.type_id for entry in schema.properties}


def _sweep_one_save(data: bytes, parsed: header.SaveHeader, into: _Accumulators) -> None:
    """Walk one save and fold it into the accumulators.

    THE CALLER HOLDS THE ``try``. This function is allowed to raise; its only
    call site is inside the sweep's broad handler, which reduces whatever comes
    out to a type name before any frame holding ``data`` or ``body`` is
    rendered.

    Args:
        data: The save file's bytes.
        parsed: Its parsed header.
        into: The accumulators, mutated in place.
    """
    pair = (parsed.header_version, parsed.save_version)
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    table = objects.parse_body(
        body, save_version=parsed.save_version, header_version=parsed.header_version
    )
    property_map = test_properties._cached_usmap_or_none()  # noqa: SLF001
    names = frozenset(record.instance_name for record in table.records)
    for record in table.records:
        into.payloads[pair] += 1
        end = record.body_offset + record.body_length
        start: int | None = record.body_offset
        if record.kind == objects.KIND_ACTOR:
            start = objects._skip_actor_head(body, record.body_offset, end)  # noqa: SLF001
        if start is None:
            continue
        tags = _walk_with_the_shipped_reader(body, start, end)
        if tags is None:
            continue
        into.reached[pair] += 1
        _tally_references(body, tags, names, into)
        flat = _schema_property_ids(property_map, record.type_path)
        if flat is not None:
            _tally_join(tags, flat, into)


@lru_cache(maxsize=1)
def _sweep_decode_oracles() -> _OracleSweep | None:
    """Walk every real save once and return COUNTS ONLY. IT NEVER RAISES.

    Cached because all three library-backed tests share it and the walk is the
    expensive part.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None

    into = _Accumulators()
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        if (parsed.header_version, parsed.save_version) not in test_properties.TAGGED_PAIRS:
            continue
        # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
        # carrying the save bytes, which is the leak this containment closes.
        try:
            _sweep_one_save(data, parsed, into)
        except Exception as exc:
            failures.append(type(exc).__name__)
            continue
    # The names and the words are JUDGED here and discarded here.
    return _OracleSweep(
        payloads=MappingProxyType(dict(into.payloads)),
        reached=MappingProxyType(dict(into.reached)),
        references=MappingProxyType(dict(into.references)),
        resolutions=MappingProxyType(dict(into.resolutions)),
        join=_shape_of(into.joined, into.join_tags[_TRUE_JOIN]),
        shifted=_shape_of(into.shifted, into.join_tags[_SHIFTED_JOIN]),
        failures=tuple(sorted(set(failures))),
    )


def _sweep_or_skip() -> _OracleSweep:
    """Fetch the sweep, skipping when this machine has no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_decode_oracles()
    if sweep is None:
        pytest.skip("no save library on this machine - the decode oracles are not gradeable here")
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    return sweep


def _pairs_present(sweep: _OracleSweep) -> tuple[tuple[int, int], ...]:
    """The tagged version pairs this machine actually holds a save of.

    Args:
        sweep: The sweep.

    Returns:
        The pairs, which the caller asserts is non-empty before reading a zero.
    """
    return tuple(pair for pair in test_properties.TAGGED_PAIRS if pair in sweep.payloads)


def test_the_shipped_walker_reaches_a_terminator_on_every_real_payload() -> None:
    """THE COMMON-MODE GUARD - the one oracle here that grades the widths.

    ``test_properties`` asserts the same reach against its OWN transcription of
    the tag grammar, so it stays green when a shipped width is wrong. This
    asserts it against the shipped reader, and that is the entire difference.

    THE CONTROL IS EQUALITY, NOT A FLOOR, and that is measured rather than
    stylistic: this project has already established that a ``> 0`` sweep passes
    under a rotated alignment, which leaves the reach SHORT of the payload
    count rather than at zero. Only equality separates the two.

    Every width in ``objects._TAG_EXTRA_STRINGS`` and the shipped
    ``GUID_BYTES`` was mutated one at a time and this assertion went red for
    every one of them. Two of those mutants - the SetProperty and MapProperty
    widths - are caught HERE AND NOWHERE ELSE in the suite, because they move
    so few payloads that every rate-based oracle absorbs them.
    """
    sweep = _sweep_or_skip()
    present = _pairs_present(sweep)
    assert present, (
        "no save of a tagged pair is on this machine, so this assertion would be "
        "vacuous; it refuses to pass unexamined"
    )
    for pair in present:
        assert sweep.reached.get(pair, 0) == sweep.payloads[pair], (
            f"the SHIPPED reader reaches a terminator on only {sweep.reached.get(pair, 0)} "
            f"of {sweep.payloads[pair]} payloads of pair {pair}; under the measured "
            "grammar it reaches one on every payload of every tagged pair, so a "
            "shortfall means a shipped width no longer matches the bytes"
        )


def test_object_references_resolve_against_the_record_table_and_collapse_when_rotated() -> None:
    """THE CROSS-SECTION ORACLE - evidence from a section this walk never reads.

    An ObjectProperty's value is a level reference and an object path, and the
    path names a record in the object table. That table is parsed by
    ``parse_body`` in a different pass over a different section of the body, so
    a reference resolving against it is a claim the payload walk cannot make
    true by itself - the two have to agree about where things are.

    THE CONTROL RE-READS THE VALUE AT PLUS AND MINUS ONE BYTE WITH THE TAG WALK
    HELD FIXED, so what moves is the value grammar alone and not the
    attribution. Resolutions must go to zero at both. The liveness floor above
    it is what stops those zeros being vacuous: a sweep that resolved nothing
    at the true offset would satisfy the collapse trivially.

    NO CROSS-SAVE CONTROL SHIPS HERE, deliberately. Resolving one save's
    references against a DIFFERENT save's record index was measured and does
    NOT collapse - it lands within a small factor of the own-index result,
    because this library is many snapshots of a single world and the two record
    tables largely name the same objects. Shipping it as a control would be
    false evidence dressed as a second oracle.
    """
    sweep = _sweep_or_skip()
    decoded = sweep.references.get(_TRUE_OFFSET, 0)
    resolved = sweep.resolutions.get(_TRUE_OFFSET, 0)
    assert decoded > 0, (
        "no object reference decoded at its true offset, so the collapse asserted "
        "below would hold for want of anything to collapse"
    )
    assert resolved > 0, (
        "no object reference resolved against the record table, so this oracle is "
        "inert on this machine and its zeros are vacuous rather than true"
    )
    for delta in _REFERENCE_ROTATIONS:
        assert sweep.resolutions.get(delta, 0) == 0, (
            f"{sweep.resolutions.get(delta, 0)} references still resolve when the "
            f"value is read {delta} bytes from where the tag says it starts; a result "
            "that survives being moved is not evidence about alignment"
        )


def test_the_usmap_type_id_join_is_a_bijection_and_collapses_under_a_one_tag_shift() -> None:
    """THE DIFFERENT-FILE ORACLE - and it is NOT a guard on the tag widths.

    The usmap is generated from the game's own assets and carries a raw type
    byte per property. Joining each tag's name to that byte in the record's own
    schema pairs the save's type WORD with the asset's type ID, and the pairing
    is one-to-one in both directions: no word claims two ids, no id is claimed
    by two words. That is genuine external evidence about the WORD-to-ID
    pairing, from a file this module never otherwise reads.

    WHAT IT IS NOT is a check on ``objects._TAG_EXTRA_STRINGS``. Every width
    there was mutated and this bijection survived all of them with zero
    violations - under the ByteProperty mutant, byte-identically. A wrong width
    breaks the walk, a broken walk yields no pairs, and the pairs that remain
    are all correct, so the bijection stays clean over a shrinking population.
    An earlier framing called this join the fix for that common mode; the
    measurement refutes it, and the reach test above is the artifact that
    actually discriminates the widths.

    THE SHIFT CONTROL is what makes the bijection mean anything: pair each
    tag's name with the NEXT tag's type word and the one-to-one property has to
    break in both directions. It does. The shifted join is asserted live for
    the same reason the cross-section oracle carries a floor - a control that
    joined nothing would "break" the bijection by being empty.
    """
    sweep = _sweep_or_skip()
    assert sweep.join.tags > 0, (
        "no tag joined the shipped mapping, so the bijection asserted below holds "
        "over an empty set and grades nothing"
    )
    assert sweep.join.words_to_many_ids == 0, (
        f"{sweep.join.words_to_many_ids} type words each pair with more than one raw "
        "type id, so the save's type word is not a function of the asset's type byte"
    )
    assert sweep.join.ids_to_many_words == 0, (
        f"{sweep.join.ids_to_many_words} raw type ids are each claimed by more than "
        "one type word, so the mapping is not injective"
    )
    assert sweep.shifted.tags > 0, (
        "the shifted control joined nothing, so its violations below would be absent "
        "for want of data rather than because the shift is detectable"
    )
    assert sweep.shifted.words_to_many_ids > 0, (
        "pairing each tag's name with the NEXT tag's type word still yields a "
        "one-to-one word-to-id map, so this join does not depend on the tag walk "
        "landing on the right tag and is not evidence about the pairing"
    )
    assert sweep.shifted.ids_to_many_words > 0, (
        "pairing each tag's name with the NEXT tag's type word still yields a "
        "one-to-one id-to-word map, so the control does not discriminate"
    )


def test_both_tag_grammar_transcriptions_agree() -> None:
    """DECLARES the common mode rather than claiming to close it.

    ``test_properties`` transcribes the tag grammar and walks the library with
    the copy. This asserts the copy still matches the shipped original, which
    is worth having on its own: a drifted transcription would make that
    module's evidence about a grammar the shipped code no longer uses.

    BUT AGREEMENT HERE IS NOT EVIDENCE THAT EITHER IS RIGHT. It is one belief
    written in two places, and every oracle that runs against the copy is blind
    to a fault the two share. That is precisely why the reach test in this
    module walks with the SHIPPED constants instead - it grades the belief
    itself rather than grading whether two copies of it match.

    Needs no save library, so it is the one test here that runs everywhere.
    """
    assert objects._TAG_EXTRA_STRINGS == test_properties._TAG_EXTRA_STRINGS, (  # noqa: SLF001
        "the tag grammar transcribed in tests/save/test_properties.py no longer "
        "matches the shipped constant, so that module's library evidence is about a "
        "grammar clockspeed/save/objects.py does not use"
    )
    assert objects.GUID_BYTES == test_properties._STRUCT_GUID_BYTES, (  # noqa: SLF001
        "the guid width transcribed in tests/save/test_properties.py no longer "
        "matches the shipped constant, with the same consequence"
    )
