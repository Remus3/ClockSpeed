"""Oracles that grade the SHIPPED decode grammar rather than a copy of it.

WHY THIS MODULE EXISTS AND WHY IT IS NOT PART OF ``test_properties``. That
module transcribes the tag grammar - its own ``_TAG_EXTRA_STRINGS``, its own
``_STRUCT_GUID_BYTES``, its own reader - and walks the library with the copy.
That is the right shape for what it does, because a transcription that
disagrees with the module under test is exactly what its synthetic fixtures are
built to expose.

WHAT THIS MODULE ADDS IS PROVENANCE. Two copies of one belief are not two
pieces of evidence - CLAUDE.md section 5 names it - so the walk here holds no
width of its own. Names come from ``objects._payload_text``, tag headers from
``objects._read_tag_header``, and the cursor advances by the value extent that
shipped header read reports, so an assertion here grades the shipped grammar
rather than a copy of it. LITERALS ARE STILL TRANSCRIBED, and each is argued
where its constant is defined rather than left for a reader to notice. NO COUNT
OF THEM IS WRITTEN HERE: the figure that stood in this sentence said one and
was wrong, because the reference word beside the terminator is a transcription
on the same reading.

WHETHER PROVENANCE ALSO BUYS DETECTION IS NOT ARGUED IN THIS PROSE. For the tag
widths the relation is derived at runtime by
``test_every_tag_width_is_caught_by_a_library_backed_oracle``. ADR 0008 is why
it is derived rather than stated: a detection claim is a measured fact, and
CLAUDE.md section 4 puts a measured fact in one machine-checked place instead
of in a sentence. The mechanical fence over the wider class of unbounded claim
in this file's prose is ``tests/save/test_absolute_claims.py``, which requires
a sentence like this one to name a test that resolves.

THE THREE ORACLES ARE NOT INTERCHANGEABLE, and what each is FOR is written
below. What each CATCHES is not.

  THE SHIPPED-WALK REACH is checked as EQUALITY rather than as a ``> 0`` floor,
  because a floor was measured to survive a rotated alignment on this project's
  own corpus. Equality is NECESSARY AND NOT SUFFICIENT: a walker that returns
  no tags satisfies it trivially, so the reach test carries a liveness floor
  BESIDE the equality. Both halves are asserted in
  ``test_the_shipped_walker_reaches_a_terminator_on_every_real_payload``.

  THE CROSS-SECTION and THE USMAP JOIN are EXTERNAL evidence: one about the
  reference-to-record pairing, read out of a section a different cursor pass
  parsed; one about the name-to-type-word pairing, read out of a different FILE
  the game ships. What each is evidence ABOUT is the durable half of that
  sentence; what each happens to catch is the derived one.

  THE SHARED-LOCATOR LIMIT, recorded here rather than left for a reader to
  discover. Oracles 1 and 2 are NOT two independent measurements. Oracle 2's
  population is a strict SUBSET of oracle 1's: a reference resolves only after
  it decoded, and it decodes only if its own length prefix accounted for the
  declared size, which is the reach oracle's own condition. On top of that
  containment, both take ``value_at`` from ONE ``objects._read_tag_header``
  call per tag, so a fault in the locator moves the two in the same direction
  by construction. Their agreement is ONE measurement reported twice at two
  strengths - not two measurements that agree. Oracle 2's rotation control
  moves only the offset the value is read from, holding the tag walk fixed, so
  what it varies is the value grammar rather than the payload attribution.

  THE JOIN'S BIJECTION AND ITS WORD COUNT ARE TWO QUANTITIES OVER ONE
  POPULATION, AND THEY DO NOT MOVE TOGETHER. A wrong width breaks the walk, a
  broken walk contributes no pairs, and the pairs that survive are correct
  ones - so a BIJECTION over that shrinking population stays pristine and can
  hold while the grammar rots. That half is asserted directly by
  ``test_every_tag_width_is_caught_by_a_library_backed_oracle``.

  THE DISTINCT-WORD COUNT IS NOT THE COMPLEMENT OF THAT HALF, and a sentence
  saying it falls with the population stood here and was measurably false. A
  thinning population does not imply a falling word count: a width was measured
  that rots thousands of payloads while leaving the count exactly where it was,
  because that width contributes none of the joined words, and thinning the
  join directly through the tag cap drops thousands of tags with the count
  again unmoved. What the same derived test asserts is the honest existential -
  that AT LEAST ONE width moves the count. Do not restore the general form.

THE JOIN IS FLAT - a tag name is joined to a ``type_id`` in the record's OWN
schema and the super chain is not walked. Walking the chain was measured too:
it joins strictly more tags and yields the same bijection, with no word
claiming two ids and no id claimed by two words. The flat join is kept because
it is the narrower claim of the two, not because the chain refuted anything.

PRIVACY, non-negotiables 11 and 12, WRITTEN AS WHAT THE CODE DELIVERS RATHER
THAN AS WHAT WOULD BE REASSURING. A call that touches a real path or a real
body sits inside a ``try`` that reduces whatever comes out of it to an exception
type NAME: the read and the header parse under the pair of handlers in the
sweep, the mapping load under its own, the per-save walk under the broad
handler below them, and discovery inside
``test_properties._library_save_paths``, which holds its own. A save path, a
body, an instance name and a decoded value are things pytest renders out of a
frame it unwinds - and it renders the ARGUMENTS of those frames with no opt-in
flag, which is why the containment has to be total rather than merely present.
``path.read_bytes()`` is a bound method whose ``self`` IS the save path, so a
single uncontained type escaping that line prints the Windows account name, the
platform account id and the world name together. The containment is exercised
by ``test_an_unexpected_read_failure_does_not_unwind_through_the_oracle_sweep``.

THE CONTAINMENT STOPS AT ``BaseException``, AND THAT EDGE IS DELIBERATE RATHER
THAN OVERLOOKED. Both cases were measured by forcing the type out of the read
under ``-q`` alone - no ``-l``, no ``--tb``, no ``--full-trace``.
``SystemExit`` IS CAUGHT: it is not an ``Exception``, it escaped, and it
rendered the path under those default flags, so the handlers name it
explicitly, at no cost to what a read path legitimately does.
``KeyboardInterrupt`` is left to escape AND IT DOES ESCAPE - out of the read,
and out of the discovery call that sits outside any ``try`` in
``_sweep_decode_oracles``. Under the same flags it rendered no path at all -
pytest prints its crash line, plus a hint that ``--full-trace`` would show
more - and swallowing it would cost the ability to abort a walk over a real
library. That is the trade, made in the direction the measurement supports
rather than the direction that reads well.

WHAT "COUNTS ONLY" GOVERNS. It is a rule about CORPUS DATA: a property name, a
type word or a value read out of a real save is judged INSIDE the sweep and
discarded there, and no frame below that line holds one to render. It does not
ban integers-and-other-things in this file - a failure message may name a key
of a shipped constant or one of this module's own function names, because
neither came from anybody's save.

``_JOIN_WORD_FLOOR`` is an absolute count written down in this file, argued
where it is defined and reopened there as a false-red risk by CS-432. The rule
it is an exception to: NO CORPUS-SIZED QUANTITY is written down, because the
corpus is the operator's own live library and it grows on each autosave, so a
payload total, a tag total or a reference total is stale before it can be
committed.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects, usmap

# IMPORTED RATHER THAN COPIED. ``_library_save_paths`` and
# ``_cached_usmap_or_none`` each close a leak their own docstrings describe -
# the discovery calls that resolve the account directory sit inside their
# ``try`` - and a third transcription of that containment is a third place to
# get it subtly wrong. The module is imported whole rather than its names
# lifted, so that a use site says out loud which module the value came from.
# That matters most for the two transcribed constants, which are the SUBJECT of
# the last test here.
from tests.save import test_properties

#: CS-420 contract markers, read by ``tests/save/test_absolute_claims.py``.
#:
#: THE FENCE DERIVES ITS SCOPE BY WALKING THE TREE FOR THESE RATHER THAN BY
#: READING A LIST. A hand-written scope tuple is an allowlist with the sign
#: flipped: deleting the entry naming this module would leave the suite green
#: and the prose here ungoverned. With the marker declared HERE and the tuple
#: asserted equal to what the walk finds, dropping either one alone disagrees
#: with the other and reddens. Unfencing this module takes two edits, and
#: neither is silent.
#:
#: ``CS420_FENCED`` subjects this module's prose to the unbounded-quantifier
#: rule. ``CS420_CENSUSED`` additionally requires that the fence account for
#: the string literals and the comment tokens here, so a prose channel the
#: extractor does not see unbalances a count rather than passing unread.
CS420_FENCED: Final = True
CS420_CENSUSED: Final = True

#: The property terminator, as the shipped walk spells it.
#:
#: THIS IS A TRANSCRIPTION, AND THE ONE THIS MODULE HOLDS. ``objects`` exports
#: no name for the terminator - the literal is bare at its only site, the
#: ``name[0] == "None"`` test inside the shipped payload walk - so there is no
#: name here to import without editing that module.
#:
#: The exposure is BOUNDED rather than absent, which is why a fourth copy is
#: tolerable where a fourth width would not be. Both walks stop on the same
#: word, so changing it in the shipped reader alone would strand this walk past
#: its terminator - a divergence that shows up as a walk running on rather than
#: as a quietly wrong measurement.
#:
#: THAT IS REASONING, NOT A MEASUREMENT, and it is marked as such because no
#: test in the suite mutates it. The shipped literal is bare rather than a
#: module attribute, so there is no name to monkeypatch and the width
#: derivation below is unable to reach it. Do not upgrade this to a claim about
#: which test would catch it without first making something able to.
_TERMINATOR: Final = "None"

#: The type word whose value names a saved object. SoftObjectProperty carries
#: the same two-string shape but names ASSETS, and was measured to resolve
#: against the record table at a flat zero, so it is not in this population.
#:
#: THIS IS A TRANSCRIPTION TOO, AND ITS EXPOSURE IS UNLIKE THE TERMINATOR'S.
#: ``objects`` holds a module-level name carrying this word - the frozenset
#: ``objects._TWO_STRING_VALUES`` - so the argument made for the terminator, that
#: there is no name to import without editing the shipped module, does not
#: transfer here. What that frozenset holds is the PAIR: this word and the
#: SoftObjectProperty one the paragraph above excludes by measurement. Importing
#: it would widen the population back to the pair rather than source this
#: constant, so a swap needs the exclusion re-expressed against the shipped set.
#: THAT IS OPEN WORK AND NOT A THING THIS MODULE DOES, recorded here because a
#: transcription with a reachable source is a weaker exception than one without.
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

#: How many distinct type words the true join must span. A NUMBER IN THIS FILE
#: READ OFF A MEASUREMENT OF THE LIBRARY rather than off the shape of the
#: grammar - ``_REFERENCE_PARTS`` and the rotation deltas are the latter.
#:
#: WHY A FLOOR AT ALL: ``join.tags > 0`` bounds volume and not diversity. The
#: bijection assertions below are vacuously true over a degenerate join, and
#: were measured GREEN with the join collapsed to a single word and a single
#: id. Volume alone does not notice that.
#:
#: THE JUSTIFICATION THAT USED TO STAND HERE IS REFUTED AND IS DELETED RATHER
#: THAN REWORDED. It argued that the count is an engine constant untouched by
#: play, and that a thinned join could not satisfy the floor. Both were
#: measured false: per-save distinct joined word counts run below this number,
#: which is a UNION over a growing library, and a join thinned by thousands of
#: tags through the tag cap still spans the full count and clears the floor. So
#: this floor can go RED ON A CORRECT GRAMMAR if autosave rotation retires the
#: saves contributing a rare word. CS-432 owns the repair and the constant is
#: deliberately left alone here.
_JOIN_WORD_FLOOR: Final = 13


@dataclass(frozen=True)
class _JoinShape:
    """One join's shape, as counts only - not the words and not the ids.

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
        walked_tags: Tags the SHIPPED walk actually yielded, by version pair.
            Carried because ``reached`` alone does not separate a complete walk
            from one that returned zero tags - see the reach test's liveness
            floor.
        references: Reference tags that decoded at all, by value-start delta.
        resolutions: Those whose object path named a record in the table, by
            the same delta.
        join: The flat usmap join's shape.
        shifted: The one-tag-shifted join's shape - the control.
        joinable: Whether the shipped property mapping resolved at all. THE
            SAVES AND THE MAPPING COME FROM DIFFERENT PLACES - saves from
            ``%LOCALAPPDATA%``, the mapping from the game install - and
            uninstalling the game leaves the saves behind. So "a library is
            reachable" does not imply "a mapping is", and a join-dependent
            assertion that gates on the library alone FAILS on that machine
            instead of skipping. Recorded rather than inferred from
            ``join.tags == 0``, which a real fault also produces.
        failures: Exception type NAMES, not the exceptions themselves.
    """

    payloads: Mapping[tuple[int, int], int]
    reached: Mapping[tuple[int, int], int]
    walked_tags: Mapping[tuple[int, int], int]
    references: Mapping[int, int]
    resolutions: Mapping[int, int]
    join: _JoinShape
    shifted: _JoinShape
    joinable: bool
    failures: tuple[str, ...]


@dataclass
class _Accumulators:
    """What one sweep folds into, mutated in place.

    Bundled rather than passed as loose arguments so that the per-save walker
    keeps a signature a reader can hold, and so that adding a measurement does
    not change the call sites.

    Attributes:
        payloads: Records seen, by version pair.
        reached: Records whose payload reached a terminator, by version pair.
        walked_tags: Tags the shipped walk yielded, by version pair.
        references: Reference tags that decoded, by value-start delta.
        resolutions: Reference tags that resolved, by the same delta.
        joined: Distinct type word and raw type id pairs, truly paired.
        shifted: The same under the one-tag shift.
        join_tags: How many tags contributed to each join.
    """

    payloads: Counter[tuple[int, int]] = field(default_factory=Counter)
    reached: Counter[tuple[int, int]] = field(default_factory=Counter)
    walked_tags: Counter[tuple[int, int]] = field(default_factory=Counter)
    references: Counter[int] = field(default_factory=Counter)
    resolutions: Counter[int] = field(default_factory=Counter)
    joined: set[tuple[str, int]] = field(default_factory=set)
    shifted: set[tuple[str, int]] = field(default_factory=set)
    join_tags: Counter[str] = field(default_factory=Counter)


def _walk_with_the_shipped_reader(
    body: bytes, start: int, end: int
) -> tuple[tuple[str, str, int, int], ...] | None:
    """Walk one payload's tags using the SHIPPED reader and no local width.

    IT HOLDS NO WIDTH OF ITS OWN, which is the point of the module. The name
    read, the tag header and the tag-count ceiling are all shipped symbols, and
    the cursor advance is computed from what the shipped header read returned
    rather than from any width stated here. What this function contributes is
    the loop, that advance, and ONE transcribed literal - the ``_TERMINATOR``
    comparison, whose only use site in this module is the line below.

    Args:
        body: The decompressed body.
        start: Where the first tag begins.
        end: The first byte past the payload.

    Returns:
        Each tag as name, type word, value start and declared size, or None
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
    """Resolve each reference tag against the record table, true and rotated.

    The judgement is the SHIPPED decoder's own: ``_decode_value`` returns a
    pair only when the two strings account for the declared size exactly.

    Args:
        body: The decompressed body.
        tags: The payload's tags, from the unrotated walk.
        names: The instance names in the table, from ``parse_body``.
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
    tag; if it survives that, it was not measuring the pairing at all.

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

    No frame downstream of this function holds a type word to render, which is
    what makes the module's "counts only" a mechanism rather than a promise.

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
        into.walked_tags[pair] += len(tags)
        _tally_references(body, tags, names, into)
        flat = _schema_property_ids(property_map, record.type_path)
        if flat is not None:
            _tally_join(tags, flat, into)


@lru_cache(maxsize=1)
def _sweep_decode_oracles() -> _OracleSweep | None:
    """Walk each real save once and return COUNTS ONLY.

    IT CONTAINS ``Exception`` AND ``SystemExit``, AND STOPS THERE. That is
    stated as the two types it holds rather than as an absolute, because the
    absolute is false: a ``KeyboardInterrupt`` unwinds straight out of this
    function, from the read below and also from the
    ``test_properties._library_save_paths`` call that sits outside any ``try``
    here. Both escapes were forced and observed. The module docstring argues
    why that gap is the trade worth making, and the containment that IS claimed
    is exercised by
    ``test_an_unexpected_read_failure_does_not_unwind_through_the_oracle_sweep``.

    Cached because the library-backed tests here share it and the walk is the
    expensive part. The width derivation clears the cache between mutants, so
    the cache is a within-run optimisation rather than a guarantee that the
    walk happens once per session.

    Returns:
        The sweep, or None when no save library is reachable. A sweep is
        returned even when no property mapping resolved - see ``joinable``,
        which is what a join-dependent caller gates on.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None

    # CONTAINED, and it was not on the first draft of this line. The mapping
    # load opens a file under the game install, so this call unwinds through a
    # frame holding that path. `_cached_usmap_or_none` catches Exception and
    # returns None, which covers a missing or unreadable mapping - but not a
    # BaseException, and a SystemExit forced out of the read was MEASURED to
    # render the install path here under `-q` alone. Asking the question
    # outside a `try` reintroduced exactly the leak shape this module exists to
    # close, one line after closing it elsewhere.
    try:
        joinable = test_properties._cached_usmap_or_none() is not None  # noqa: SLF001
    except (Exception, SystemExit):
        joinable = False

    into = _Accumulators()
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file and a save of a
            # version this project does not parse - stay silent skips, because
            # the library legitimately holds both and _sweep_or_skip treats any
            # recorded failure as fatal.
            continue
        except (Exception, SystemExit) as exc:
            # THE BACKSTOP, for the reason the handler below states: anything
            # unexpected escaping here unwinds through `path.read_bytes()`,
            # whose bound `self` IS the save path, and pytest renders the
            # arguments of an unwound frame with no opt-in flag.
            #
            # SystemExit IS NAMED because it is not an Exception and it was
            # MEASURED to render that path under default flags - `-q` alone,
            # no `-l`, no `--tb`, no `--full-trace`. KeyboardInterrupt is left
            # to escape: it rendered no path under those same flags, and
            # swallowing it would cost the ability to abort a walk over a real
            # library. A read path has no legitimate reason to raise
            # SystemExit, so containing it costs none of what that buys.
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in test_properties.TAGGED_PAIRS:
            continue
        # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
        # carrying the save bytes, which is the leak this containment closes.
        # SystemExit for the reason the handler above records.
        try:
            _sweep_one_save(data, parsed, into)
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    # The names and the words are JUDGED here and discarded here.
    return _OracleSweep(
        payloads=MappingProxyType(dict(into.payloads)),
        reached=MappingProxyType(dict(into.reached)),
        walked_tags=MappingProxyType(dict(into.walked_tags)),
        references=MappingProxyType(dict(into.references)),
        resolutions=MappingProxyType(dict(into.resolutions)),
        join=_shape_of(into.joined, into.join_tags[_TRUE_JOIN]),
        shifted=_shape_of(into.shifted, into.join_tags[_SHIFTED_JOIN]),
        joinable=joinable,
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


def _join_sweep_or_skip() -> _OracleSweep:
    """Fetch the sweep for a JOIN-dependent assertion, skipping when it is not gradeable.

    TWO INPUTS, TWO GATES, AND THE SECOND WAS MISSING. A join assertion needs
    the save library AND the property mapping, and those come from different
    places on disk - saves from ``%LOCALAPPDATA%``, the mapping from the game
    install. Uninstalling the game does not delete the save library, so
    "library present, install absent" is an ordinary machine rather than a
    contrived one, and gating on the library alone made a join assertion FAIL
    there rather than skip. Measured before the gate existed: the join oracle
    and the attribution test both went red on a simulated no-install box while
    the rest of the module passed.

    Returns:
        The sweep, with a mapping known to have resolved.
    """
    sweep = _sweep_or_skip()
    if not sweep.joinable:
        pytest.skip("no property mapping on this machine - the usmap join is not gradeable here")
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
    """THE REACH ORACLE WITH NO TRANSCRIPTION ANYWHERE IN ITS CHAIN.

    WHAT THIS TEST IS FOR, AND THE ANSWER IS NOT A LIST OF WHAT IT CATCHES.
    The relation is derived instead, on a run that has its inputs, by
    ``test_every_tag_width_is_caught_by_a_library_backed_oracle``. Do not
    restore a sentence here naming what this test uniquely catches: a claim
    about which test reddens under which fault depends on assertions elsewhere,
    so an addition made in another file falsifies it without anyone editing it.
    ADR 0008 is the rule and ``tests/save/test_absolute_claims.py`` is the
    fence.

    WHAT IS DURABLE IS THE PROVENANCE, and it is a property of this test's own
    body rather than of the rest of the suite. The name read, the tag header
    and the tag cap are shipped symbols and the cursor advances by the extent
    that shipped header read reported, so what this asserts is that THE SHIPPED
    READER matches THE BYTES. ``test_both_tag_grammar_transcriptions_agree``
    asserts something different and weaker by construction: its body compares
    two constants to their copies and touches no shipped-reader internal at
    all, so it can say the two copies match and nothing about whether either is
    right. Those are different claims whichever way the greens fall, and that -
    not a unique catch - is why both exist.

    THE EQUALITY IS NECESSARY AND NOT SUFFICIENT. Equality rather than a ``> 0``
    floor is what rules out a rotated alignment, which leaves the reach SHORT of
    the payload count rather than at zero, so it stays. But equality alone is
    satisfied by a walker that returns NO TAGS - a payload then trivially
    "reaches" - and this assertion was measured GREEN under exactly that mutant.
    The liveness floor below closes it.
    """
    sweep = _sweep_or_skip()
    present = _pairs_present(sweep)
    assert present, (
        "no save of a tagged pair is on this machine, so this assertion would be "
        "vacuous; it refuses to pass unexamined"
    )
    for pair in present:
        # LIVENESS, and it is not redundant with the equality below. A walk that
        # yields no tags satisfies that equality perfectly - reached == payloads
        # because there was no tag to walk before "reaching" - and did so when
        # it was measured. A floor on the tags actually yielded is what
        # separates a complete walk from an absent one.
        assert sweep.walked_tags.get(pair, 0) > 0, (
            f"the SHIPPED walk yielded no tags at all on the {sweep.payloads[pair]} "
            f"payloads of pair {pair}, so the equality below is satisfied by a walk "
            "that did not happen rather than by one that reached its terminators"
        )
        assert sweep.reached.get(pair, 0) == sweep.payloads[pair], (
            f"the SHIPPED reader reaches a terminator on only {sweep.reached.get(pair, 0)} "
            f"of {sweep.payloads[pair]} payloads of pair {pair}; under the measured "
            "grammar the reach equals the payload count on a tagged pair, so a "
            "shortfall means a shipped width no longer matches the bytes"
        )


def test_object_references_resolve_against_the_record_table_and_collapse_when_rotated() -> None:
    """THE CROSS-SECTION ORACLE - evidence from a section this walk does not read.

    An ObjectProperty's value is a level reference and an object path, and the
    path names a record in the object table. That table is parsed by
    ``parse_body`` in a different pass over a different section of the body, so
    a reference resolving against it is a claim the payload walk is unable to
    make true by itself - the two have to agree about where things are.

    THE CONTROL RE-READS THE VALUE AT PLUS AND MINUS ONE BYTE WITH THE TAG WALK
    HELD FIXED, so what moves is the value grammar alone and not the
    attribution. Resolutions must go to zero at both. The liveness floor above
    it is what stops those zeros being vacuous: a sweep that resolved zero
    references at the true offset would satisfy the collapse trivially.

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
    """THE DIFFERENT-FILE ORACLE - two quantities, and they are not alike.

    The usmap is generated from the game's own assets and carries a raw type
    byte per property. Joining each tag's name to that byte in the record's own
    schema pairs the save's type WORD with the asset's type ID, and the pairing
    is one-to-one in both directions: no word claims two ids, no id is claimed
    by two words. That is genuine external evidence about the WORD-to-ID
    pairing, from a file this module does not otherwise read.

    THIS TEST ASSERTS TWO DIFFERENT THINGS ABOUT ONE POPULATION, and the two do
    not move together. A wrong width in ``objects._TAG_EXTRA_STRINGS`` breaks
    the walk, a broken walk yields no pairs, and the pairs that remain are
    correct - so a BIJECTION over that shrinking population stays clean.
    THE DISTINCT-WORD COUNT DOES NOT SIMPLY TRACK THE THINNING, which is the
    error a sentence in this spot made for several rounds: a width was measured
    that rots thousands of payloads and leaves the word count exactly where it
    was. Which width either quantity notices is not recorded in this docstring;
    it is derived by
    ``test_every_tag_width_is_caught_by_a_library_backed_oracle``, which also
    asserts the bijection half rather than trusting this paragraph for it.

    THE SHIFT CONTROL is what makes the bijection mean anything: pair each
    tag's name with the NEXT tag's type word and the one-to-one property has to
    break in both directions. It does. The shifted join is asserted live for
    the same reason the cross-section oracle carries a floor - a control that
    joined zero tags would "break" the bijection by being empty.

    AND A LIVENESS FLOOR ON VOLUME IS NOT ONE ON DIVERSITY, which was measured
    rather than reasoned about. With ``join.tags`` left large and the joined
    pairs collapsed to a single word and a single id, the assertions this test
    shipped at the time passed - a one-element map is trivially one-to-one in
    both directions. So the tag floor is joined by a floor on the distinct type
    words spanned; see ``_JOIN_WORD_FLOOR``, and see CS-432 for the false-red
    risk that floor carries.
    """
    sweep = _join_sweep_or_skip()
    assert sweep.join.tags > 0, (
        "no tag joined the shipped mapping, so the bijection asserted below holds "
        "over an empty set and grades zero pairs"
    )
    # DIVERSITY, which the tag floor above does not bound. THIS ASSERTION IS THE
    # ONE CS-432 IS OPEN AGAINST: the floor sits at a UNION over a growing
    # library rather than at an engine constant, so autosave rotation retiring
    # the saves that contribute a rare word turns it RED ON A CORRECT GRAMMAR.
    # It is loud rather than silent, which is why it ships while CS-432 is open.
    assert sweep.join.words >= _JOIN_WORD_FLOOR, (
        f"the join's distinct type word count is {sweep.join.words}, under the "
        f"floor of {_JOIN_WORD_FLOOR}; the bijection below is one-to-one over "
        "whatever survives, so a thinned join passes it while grading little. "
        "Check CS-432 before treating this as a grammar fault - the floor is "
        "known to be able to redden on a correct grammar"
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
        "the shifted control joined zero tags, so its violations below would be absent "
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
    """DECLARES the two-copy structure rather than claiming to close it.

    ``test_properties`` transcribes the tag grammar and walks the library with
    the copy. This asserts the copy still matches the shipped original, which
    is worth having on its own: a drifted transcription would make that
    module's evidence about a grammar the shipped code no longer uses.

    BUT AGREEMENT HERE IS NOT EVIDENCE THAT EITHER IS RIGHT. It is one belief
    written in two places, and two copies agreeing is silent about whether the
    belief matches the bytes. Only a third party neither copy controls settles
    that, and the bytes are the third party - which is why the reach test in
    this module walks with the SHIPPED constants and grades them against a
    terminator the file either does or does not contain.

    Needs no save library and no game install, so it runs on a bare box.
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


def test_an_unexpected_read_failure_does_not_unwind_through_the_oracle_sweep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The read and the header parse sat under ``except (OSError, HeaderError)``.

    That catch names the two failures somebody predicted and lets any other
    type escape the sweep entirely - three lines above a broad handler whose own
    comment says a narrower catch is the leak. pytest renders the arguments of
    the frames it unwinds with NO opt-in flag, and ``path.read_bytes()`` unwinds
    through a bound method whose ``self`` IS the save path: one line carrying the
    Windows account name, the numeric platform account id and the world name.
    Non-negotiable 3 three times over, non-negotiable 12 once, under completely
    default pytest flags.

    THE SAVE LIST IS SYNTHETIC, so this runs on a machine with no game installed
    and no real path is put into the frame under test. The helpers are imported
    from ``test_properties`` rather than copied, for the reason given at this
    module's own import of it.
    """
    monkeypatch.setattr(
        test_properties,
        "_library_save_paths",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr(Path, "read_bytes", test_properties._raise_memory_error)  # noqa: SLF001
    _sweep_decode_oracles.cache_clear()
    try:
        test_properties._assert_read_failure_is_contained(  # noqa: SLF001
            "oracle sweep", _sweep_decode_oracles
        )
    finally:
        _sweep_decode_oracles.cache_clear()


# ---------------------------------------------------------------------------
# The mutant-to-detector relation, DERIVED. What is below this line exists so
# that no sentence above it has to say which oracle catches which fault.
# ---------------------------------------------------------------------------


#: How each tag width is mutated when the relation is derived. One string fewer
#: is the minimal desynchronising fault. It is a mutation DELTA and not a
#: measurement of anything, which is why it is written down where a count would
#: not be. The direction matters: ``_skip_tag_extra`` steps a width through
#: ``range()``, and ``range()`` treats a negative exactly as it treats zero, so
#: a width that went negative would be an EQUIVALENT mutant wearing a mutant's
#: label. The test asserts no shipped width can, rather than arguing it here.
_WIDTH_MUTATION_DELTA: Final = -1

#: The oracles the relation is over, as the shipped test functions themselves
#: rather than as a local copy of their assertions. Calling them is what makes
#: this a derivation - a fourth transcription of "reached == payloads" would be
#: one more place for the same belief to be written, and this module exists
#: because two copies of one belief are not two pieces of evidence.
#:
#: MEMBERSHIP IS EARNED AND CHECKED. A member is asserted to detect at least
#: one width, which is what makes GUTTING one visible: an earlier draft folded
#: the members through ``any()``, and because the reach oracle is first and
#: reddened on the widths tried, the other two went uninvoked - they could be
#: replaced by empty function bodies and the test still passed. A per-member
#: liveness assertion is the repair, and it is sound only over members measured
#: to detect something.
#:
#: THE CROSS-SECTION ORACLE IS NOT A MEMBER, and that is a measurement rather
#: than a preference: evaluated against the shipped widths with no
#: short-circuit anywhere, it detects ZERO. Its assertions are a liveness floor
#: and a collapse-under-rotation, and both survive a thinned population for the
#: same reason the bijection does, so it would fail a liveness assertion and
#: including a non-detector would overstate what is being derived. It is still
#: evaluated under the mutants, and asserted blind - see
#: :data:`_MEASURED_BLIND`.
#:
#: ``test_both_tag_grammar_transcriptions_agree`` IS NOT A MEMBER EITHER, and
#: its exclusion needs no measurement because arithmetic settles it: mutating
#: one copy makes the two copies unequal, so it reddens on a mutated width by
#: construction without a byte of the library being read. Including it would
#: make the no-survivor shape true by arithmetic. An earlier draft ASSERTED
#: that blanket sensitivity; the assertion was unable to fail, so it was
#: deleted rather than kept as decoration.
_DERIVED_AGAINST: Final = (
    test_the_shipped_walker_reaches_a_terminator_on_every_real_payload,
    test_the_usmap_type_id_join_is_a_bijection_and_collapses_under_a_one_tag_shift,
)

#: Oracles evaluated under the mutants and asserted to detect ZERO widths. This
#: is the honest half of the membership decision: an oracle is excluded because
#: it was measured blind, and the exclusion stays under test, so strengthening
#: one turns this red and says "move it into the derived set" rather than
#: letting it drift out of the relation unnoticed.
#:
#: THIS DOES NOT PROTECT THEM FROM GUTTING. An oracle that detects zero widths
#: is beyond the reach of an attribution test - gutting it to a green no-op and
#: measuring it blind look identical from here. Whatever guards the
#: cross-section oracle has to come from the fault class it IS sensitive to,
#: which is the value-start rotation rather than a tag width. CS-432 owns that.
_MEASURED_BLIND: Final = (
    test_object_references_resolve_against_the_record_table_and_collapse_when_rotated,
)


def _goes_red(oracle: Callable[[], None]) -> bool:
    """Run one shipped oracle against the CURRENTLY CACHED sweep and grade it.

    ONLY AN ``AssertionError`` COUNTS AS A DETECTION. Anything else propagates:
    a skip, a lookup that fell off the end of a counter, an exception out of the
    walk. A detector that fell over is not a detector that fired, and folding
    the two together is how a mutation study reports coverage it does not have.

    Args:
        oracle: A zero-argument test function defined in this module.

    Returns:
        Whether it failed an assertion. Its MESSAGE is not captured - the name
        is enough to identify it, and this module's counts-only discipline is
        worth more than a nicer failure line.
    """
    try:
        oracle()
    except AssertionError:
        return True
    return False


def test_every_tag_width_is_caught_by_a_library_backed_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DERIVES which oracle notices which tag width instead of stating it.

    THIS TEST IS THE STRUCTURAL FIX, and the fault it repairs is not a decoding
    fault. Round after round of prose repair in this file shipped a false
    sentence about which test catches which fault, one written expressly to
    correct its predecessor. The cause was not carelessness: a detection
    claim's truth depends on assertions elsewhere, so ADDING an assertion
    falsifies a sentence that was not edited. The relation is derived here
    instead of being written down.

    HOW. Each width in ``objects._TAG_EXTRA_STRINGS`` is mutated in the SHIPPED
    module and in no other place - the constant is read as a module global
    inside ``objects._skip_tag_extra``, so replacing the attribute is a real
    fault in the real reader, with no subprocess, no second checkout and no
    bytecode cache to go stale. The sweep is re-run from scratch and each
    oracle is CALLED under each mutant, filling a full per-pair table.

    THE FULL TABLE IS THE POINT, and an earlier draft did not build one. It
    asked ``any(_goes_red(o) for o in ...)``, which SHORT-CIRCUITS: the reach
    oracle is first and reddened on the widths it was tried against, leaving
    the others uninvoked. An invocation census showed that, and so did two
    counter-examples - cutting the tuple to the reach oracle alone still
    passed, and replacing the other two with green no-op bodies still passed.
    What that draft derived was a disjunction whose first term saturates, not a
    relation. No short-circuit survives here.

    WHAT IT ASSERTS. Each item describes an assertion in the body below rather
    than making a standing claim about the suite:

      NO SURVIVOR. A shipped width that no member catches fails this test. An
      addition made elsewhere is unable to falsify that shape, because an
      addition adds detections rather than removing one.

      EACH MEMBER DETECTS. A member that catches zero widths fails this test.
      That is what makes gutting a member visible, and it is why membership is
      restricted to oracles measured to detect something.

      THE EXCLUDED ORACLE IS BLIND. The cross-section oracle catching a width
      fails this test, so the measured justification for leaving it out stays
      under test rather than drifting.

      THE BIJECTION HOLDS UNDER THE MUTANTS, over a population asserted
      NON-EMPTY first. That is the mechanism argument above made executable: a
      wrong width breaks the walk, a broken walk contributes no pairs, so a
      surviving pair is still correct and a one-to-one map over a shrinking
      population of correct pairs stays clean. The liveness guard is not
      optional - a fault that drove the join to zero pairs would satisfy the
      shape over the empty set, and faults that do exactly that were measured.
      Red here means the mechanism is wrong, not that the grammar is.

      THE JOIN'S WORD COUNT MOVES ON AT LEAST ONE WIDTH, measured against the
      PRISTINE count from this same run rather than against a written-down
      floor. AN EXISTENTIAL IS THE STRONGEST HONEST FORM HERE. The general
      version - that the word count tracks the thinning - was measured false: a
      width was found that rots thousands of payloads with the count unmoved,
      and thinning the join through the tag cap drops thousands of tags with
      the count unmoved again. Being relative rather than absolute also keeps
      corpus growth from reddening it on a correct grammar.

    WHAT IT COMPARES IS READ AT RUNTIME - the widths from the shipped
    constant's own keys, the word count from a sweep taken in this same run. It
    deliberately does NOT read ``_JOIN_WORD_FLOOR``, whose value is precisely a
    count of how many words the join spans; an earlier draft did, while
    announcing that no count was written down anywhere near it.

    IT SKIPS RATHER THAN FAILS WHEN AN INPUT IS ABSENT, and it needs TWO - the
    save library and the property mapping, which live in different places and
    disappear independently. See :func:`_join_sweep_or_skip`. It is not the
    CI-side guard: CS-426 owns that and stays open.

    Args:
        monkeypatch: Restores the shipped constant even if an assertion below
            escapes the ``finally``.
    """
    shipped = dict(objects._TAG_EXTRA_STRINGS)  # noqa: SLF001
    assert shipped, (
        "objects._TAG_EXTRA_STRINGS is empty, so the loop below would mutate no width "
        "and the assertions in this test would hold over an empty set"
    )
    equivalent = sorted(word for word, n in shipped.items() if n + _WIDTH_MUTATION_DELTA < 0)
    assert not equivalent, (
        f"{equivalent} would go negative under the mutation, and range() treats a "
        "negative count exactly as it treats zero - so those would be EQUIVALENT "
        "mutants and their 'detection' would be a pristine run wearing a label"
    )

    # The pristine control, taken before anything is mutated and while the
    # baseline sweep is still the cached one. A red from an oracle that was
    # already red is silent about the mutant it was collected under, and would
    # be counted below as a detection it did not make. _join_sweep_or_skip is
    # what makes this test SKIP rather than fail when either input is absent.
    baseline = _join_sweep_or_skip()
    graded = (*_DERIVED_AGAINST, *_MEASURED_BLIND)
    already_red = tuple(oracle.__name__ for oracle in graded if _goes_red(oracle))
    assert not already_red, (
        f"{list(already_red)} fail with the shipped constant UNMUTATED, so a failure "
        "under any mutant below would be silent about that mutant and the relation "
        "derived here would credit these oracles with detections they did not make"
    )

    # THE TABLE. detected[oracle name] collects the widths that oracle caught,
    # and the loop below fills a row per oracle per width - no any(), no
    # short-circuit, no early exit. The per-oracle rows are what a disjunction
    # threw away.
    detected: dict[str, list[str]] = {oracle.__name__: [] for oracle in graded}
    survivors: list[str] = []
    bijection_moved: list[str] = []
    join_went_empty: list[str] = []
    words_fell: list[str] = []
    try:
        for width in sorted(shipped):
            mutant = dict(shipped)
            mutant[width] += _WIDTH_MUTATION_DELTA
            monkeypatch.setattr(objects, "_TAG_EXTRA_STRINGS", MappingProxyType(mutant))
            _sweep_decode_oracles.cache_clear()
            sweep = _sweep_decode_oracles()
            assert sweep is not None, (
                f"the sweep found no save library under the {width} mutant though it "
                "found one moments earlier, so discovery broke mid-test and the widths "
                "after this one would be graded against an absent library"
            )
            # A CRASH IS NOT A DETECTION. _sweep_or_skip folds a recorded failure
            # into an AssertionError, which _goes_red would read as an oracle
            # firing - so the failures are read HERE, before any oracle is
            # called, and a raising mutant fails this test loudly instead of
            # being counted as caught.
            assert sweep.failures == (), (
                f"the {width} mutant made the sweep RAISE {sweep.failures} rather than "
                "merely walk badly. That is not a detection: counting it as one would "
                "credit these oracles with catching a fault that in fact escaped them"
            )
            fired = [oracle.__name__ for oracle in graded if _goes_red(oracle)]
            for name in fired:
                detected[name].append(width)
            if not any(oracle.__name__ in fired for oracle in _DERIVED_AGAINST):
                survivors.append(width)
            if sweep.join.tags == 0 or sweep.join.words == 0:
                join_went_empty.append(width)
            if sweep.join.words_to_many_ids or sweep.join.ids_to_many_words:
                bijection_moved.append(width)
            if sweep.join.words < baseline.join.words:
                words_fell.append(width)
    finally:
        # Order matters. The constant is restored FIRST and the cache dropped
        # SECOND, so the cache has no mutated global left to repopulate from;
        # leaving either behind would silently corrupt the tests that run after
        # this one in the same session.
        monkeypatch.undo()
        _sweep_decode_oracles.cache_clear()

    # Type words below are keys of a constant shipped in a tracked file and
    # oracle names are this module's own function names - neither is corpus
    # data, so a failure message may render them. The counts-only rule governs
    # what the SWEEP carries out of a real save, and no value here came from one.
    assert not survivors, (
        f"{survivors} survive a single-copy {_WIDTH_MUTATION_DELTA} mutation with "
        "each member of the derived set green. A width that no oracle here notices "
        "is a width the shipped grammar can rot in without this module saying so - "
        "widen the coverage rather than this assertion"
    )
    idle = sorted(oracle.__name__ for oracle in _DERIVED_AGAINST if not detected[oracle.__name__])
    assert not idle, (
        f"{idle} are members of the derived set and caught NO width. A member that "
        "detects zero widths is indistinguishable from a member gutted to a green "
        "no-op, which is the failure this assertion exists to make visible. Either "
        "the oracle has been weakened, or it belongs in _MEASURED_BLIND instead"
    )
    busy = sorted(oracle.__name__ for oracle in _MEASURED_BLIND if detected[oracle.__name__])
    assert not busy, (
        f"{busy} are recorded as blind to the tag widths but caught "
        f"{ {n: detected[n] for n in busy} }. The exclusion was a measurement and the "
        "measurement has changed - move them into _DERIVED_AGAINST, where their "
        "detection is asserted, rather than leaving the relation understated"
    )
    assert not join_went_empty, (
        f"the join population collapsed to zero pairs under {join_went_empty}, so the "
        "bijection assertion below holds over an empty set. 'Notices none' and 'had "
        "no pair to notice' are the same green without this guard"
    )
    assert not bijection_moved, (
        f"the join's bijection broke under {bijection_moved}, contradicting the "
        "mechanism recorded above it: a broken walk contributes no pairs, so a "
        "surviving pair should still be correct and a one-to-one map over a shrinking "
        "population of correct pairs should stay clean. Re-derive the mechanism before "
        "editing the prose - this run is evidence the argument is incomplete"
    )
    assert words_fell, (
        f"no width moved the join's distinct type word count below the {baseline.join.words} "
        "this same run measured unmutated. This is an EXISTENTIAL and it is the strongest "
        "honest form: the general claim that the count tracks the thinning was measured "
        "false. A red here means no width at all moves the count, so the count grades "
        "zero faults in this run"
    )


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``test_properties`` and applied across this package by
# the suite-wide test that lives beside it, which walks the package directory
# rather than waiting to be called. Before CS-471 this module touched a library
# primitive while declaring no reach at all, and the suite had no check that
# would say so.
#
# The wording here is deliberately free of the CS-420 quantifier vocabulary,
# because two modules carrying this block sit inside that fence.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches.
#: THE KEY IS THE FUNCTION'S OWN ``__name__`` AND THE REASON COMES FROM
#: ``test_properties``, so this censused module adds no string literal here -
#: and the key is the function it names rather than a transcription of it,
#: so a rename moves both together.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {_sweep_decode_oracles.__name__: test_properties.REACH_READS_THE_LIBRARY}
)

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
