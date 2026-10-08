"""What is and is not known about the grammar INSIDE one property payload.

WHAT CHANGED, AND WHAT DELIBERATELY DID NOT
---------------------------------------------
This module once existed to hold a measurement that was NOT shipped. The
measurement has now shipped: the tag grammar lives in
``clockspeed/save/objects.py`` as production code, and ``read_properties``
returns decoded values for the types whose encoding was measured. A grammar
that lives only in a test file cannot be used by ``world.py``, which was the
point of the item.

WHAT DID NOT CHANGE IS THE LIMIT. The PROPERTY walk - not the body walk, which
is boundary-exact - is TERMINATOR-exact: a variable trailing run follows the
terminator on every payload of the three pairs this grammar reads, which is not
the same as every payload in the library - and save version 60 still refuses
this grammar outright. Both are asserted below rather than described, because
a comment
does not fail.

So this module is the ARTIFACT for that measurement. It re-derives the result
from the real library on every run rather than restating a number, and it
asserts INVARIANTS rather than the counts themselves - an absolute count here
would go red the next time the operator plays the game, which is a lie with a
timestamp on it rather than a test.

WHAT IS MEASURED
------------------
A payload is Unreal TAGGED property serialization, not the unversioned form:
the names and type words are in the bytes. One tag reads

    name:str, type:str, size:int32, index:int32, <type-specific tag data>,
    has_guid:uint8, [guid:16 bytes if set], <value: size bytes>

repeating until ``name`` is the literal ``None``. An ACTOR's payload opens
first with a parent reference and its component list; a COMPONENT's does not.
On pairs (10,36), (13,42) and (14,52) every payload in the library reaches that
terminator.

WHAT IS NOT MEASURED, AND IS THEREFORE NOT CLAIMED
----------------------------------------------------
1. **The run AFTER the terminator.** A payload does not end at ``None``; a
   variable trailing run follows, and its grammar is unmeasured. So the tag
   walk is terminator-exact and NOT boundary-exact, and
   :func:`test_the_run_after_the_terminator_is_unmeasured` pins that distinction
   on purpose - it is what stops a later slice from reporting this as a closed
   byte-exact result on the strength of the terminator alone.
2. **Save version 60.** It refuses this grammar outright: not one payload of it
   reaches a terminator. A single leading byte accounts for some of the gap and
   nothing like all of it, so no offset is claimed here. Save 60's payload
   grammar is its own measurement and has not been made.
3. **The value grammar of the types NOT in :data:`_MEASURED_VALUE_TYPES`** -
   struct, array, set, map and text. Each is named in
   ``objects.UNMEASURED_PAYLOAD_REGIONS`` with what is pinned and what is not
   claimed, and :func:`test_every_unmeasured_type_the_library_holds_is_recorded_as_data`
   asserts that table stays complete against the library rather than against a
   list somebody remembered to update.

AND THE HALF THAT NEEDS NO SAVE LIBRARY
-----------------------------------------
Everything above ran only on the one machine that has the operator's saves. On
CI, on a fresh clone, on a reviewer's laptop, every one of those tests skipped
and the ~450-line decoder executed ZERO lines. CLAUDE.md section 7 settles that
the rule suite must run with no game installed, so the second half of this
module is a payload assembled byte by byte in the repo and pushed through the
SHIPPED decoder.

It proves SELF-CONSISTENCY and never conformance: a fixture built from the same
belief as the reader agrees with the reader by construction. The real-library
sweeps stay the only evidence about the format, and the rotation control inside
them stays the only evidence about the alignment.

PRIVACY. A payload is world content, so every helper reading a REAL save
RETURNS on failure rather than raising - pytest renders the arguments and the
locals of every frame in a failing traceback, and the cheapest way to guarantee
no body reaches a log is to have no failure path that unwinds through a frame
holding one. That now covers the DISCOVERY calls too: ``resolve_save_root``,
``resolve_account_dir``, the save glob and ``cached_usmap`` all used to run
before any handler, so a failure in one unwound through a frame holding the
account directory. Every assertion about a sweep is also reduced to a scalar
before it is written, because pytest prints the operands it compared.

WHAT THE HANDLERS HOLD, AND THE ONE THING THEY DO NOT. Every handler here names
``Exception`` AND ``SystemExit``. ``SystemExit`` is named separately because it
derives from ``BaseException``, so ``except Exception`` does not hold it -
:func:`test_the_forced_failures_are_outside_the_narrow_catch` asserts that
hierarchy rather than leaving it to a reader, and every read-containment grader
in this package forces BOTH failures for the same reason.

``KeyboardInterrupt`` is still free to unwind, and that is a decision with a
measurement under it rather than an inherited habit. Measured on this machine on
2026-08-16, against the pinned pytest: a ``KeyboardInterrupt`` forced out of a
read makes pytest's terminal reporter print its ``reprcrash`` line and direct the
operator to ``--full-trace``, and the run rendered no frame, no argument and no
path. The same probe under ``SystemExit``, before the handlers named it, rendered
the save path, the account directory and the Windows account name. So the
abortability that argues for letting an interrupt through costs no disclosure,
while the type that discloses gains nothing from being let through. Nothing here
claims that holds for a pytest this project has not run.

**Only counts and repo literals come out, and both are mechanisms rather than
arguments.** The sweeps return integers, plus two kinds of word set - the
measured type words and the recorded region keys - and each of those is
INTERSECTED WITH A LITERAL ALREADY IN TRACKED SOURCE inside the sweep, so no
word that is not already written down can leave. That distinction is not
cosmetic: an earlier revision returned the distinct type words raw, defended as
format vocabulary rather than world content, which is true exactly while the
walk is synchronised and false in the one case the assertion using them fires
in. Misaligned by one record across this library, the walk yields a word that
is not a type word at all - and the intersection drops exactly those.

The one thing the sweeps DO hold internally is the property name to type-word
map, without which the non-negotiable-7 assertion is a tautology: the shipped
decoder returns a name-keyed mapping carrying no type word, so with nothing to
join on, the only checkable property of a decoded value is its Python shape,
which every implementation satisfies. The map never leaves the judging frame.
"""

from __future__ import annotations

import os
import re
import struct
import traceback
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path
from types import FrameType, MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects, usmap
from tests.save import reach_guard
from tests.save.reach_guard import (
    _assert_library_reach_is_declared,
    _assert_no_test_is_gutted,
)

#: Pairs whose payloads this grammar reads to a terminator, measured.
TAGGED_PAIRS: Final = ((10, 36), (13, 42), (14, 52))

#: The pair that refuses it, measured. Not interpolated from its neighbours.
UNMEASURED_PAIR: Final = (14, 60)

#: Type words needing extra tag data before the guid flag, by how much.
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

_STRUCT_GUID_BYTES: Final = 16
_TAG_CAP: Final = 1 << 14


def _text(body: bytes, at: int, end: int) -> tuple[str, int] | None:
    """Read one length-prefixed string, returning None rather than raising.

    Args:
        body: The decompressed body.
        at: Where the length prefix starts.
        end: The first byte past this payload.

    Returns:
        The text and the offset after it, or None if it does not read.
    """
    if at + 4 > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    if count == 0:
        return ("", at + 4)
    if count < 0:
        width, terminator, encoding = -count * 2, 2, "utf-16-le"
    else:
        width, terminator, encoding = count, 1, "utf-8"
    if width > objects.MAX_STRING_BYTES or at + 4 + width > end:
        return None
    try:
        return (body[at + 4 : at + 4 + width - terminator].decode(encoding), at + 4 + width)
    except UnicodeDecodeError:
        return None


def _skip_actor_head(body: bytes, at: int, end: int) -> int | None:
    """Step over an actor payload's parent reference and component list.

    Args:
        body: The decompressed body.
        at: The payload's first byte.
        end: The first byte past the payload.

    Returns:
        Where the property tags begin, or None if the head does not read.
    """
    for _ in range(2):
        step = _text(body, at, end)
        if step is None:
            return None
        at = step[1]
    if at + 4 > end:
        return None
    (count,) = struct.unpack_from("<i", body, at)
    at += 4
    if count < 0 or count > objects.MAX_OBJECTS:
        return None
    for _ in range(2 * count):
        step = _text(body, at, end)
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
    if type_word == "BoolProperty":
        # The value itself lives in the tag, and `size` is 0 for it.
        return at + 1 if at + 1 <= end else None
    for _ in range(_TAG_EXTRA_STRINGS.get(type_word, 0)):
        step = _text(body, at, end)
        if step is None:
            return None
        at = step[1]
    if type_word == "StructProperty":
        at += _STRUCT_GUID_BYTES
        if at > end:
            return None
    return at


def _read_one_tag(body: bytes, at: int, end: int) -> tuple[int, str, int, int] | None:
    """Read one tag past its name, value included.

    Args:
        body: The decompressed body.
        at: Just past the tag's name.
        end: The first byte past the payload.

    Returns:
        The offset after the value, the type word, where the value starts and
        its declared size. None if the tag breaks. The value extent is carried
        out because the value-start rotation control needs to move the value
        read while leaving the tag walk exactly where it is.
    """
    type_read = _text(body, at, end)
    if type_read is None:
        return None
    type_word, after = type_read
    if after + 8 > end:
        return None
    (size,) = struct.unpack_from("<i", body, after)
    nxt = _skip_tag_extra(body, after + 8, end, type_word)
    if nxt is None or nxt + 1 > end:
        return None
    flag = body[nxt]
    nxt += 1
    if flag == 1:
        nxt += _STRUCT_GUID_BYTES
    elif flag != 0:
        return None
    if size < 0 or nxt + size > end:
        return None
    return (nxt + size, type_word, nxt, size)


#: The type words whose value is one or more length-prefixed strings, so the
#: value carries its OWN length and the tag's declared size is a second,
#: independent statement of it. That redundancy is what the rotation control
#: below re-reads at moved offsets. ByteProperty is deliberately out: it has
#: two measured shapes and only one of them is string-bearing, so including it
#: would make the denominator depend on a judgement rather than on a type word.
_STRING_BEARING_TYPES: Final = frozenset(
    {"StrProperty", "NameProperty", "EnumProperty", "ObjectProperty", "SoftObjectProperty"}
)

#: The value-start offsets the control re-reads at. 0 is the shipped alignment
#: and must be the only one that holds.
_VALUE_ROTATIONS: Final = (-2, -1, 0, 1, 2)

#: The collapse the rotations must show, as a FACTOR rather than as a count -
#: an absolute count here would go red on the operator's next autosave. A
#: rotated offset must agree on under a hundredth of what the shipped one does.
_COLLAPSE_FACTOR: Final = 100


def _tally_value_rotation(
    body: bytes, type_word: str, value_start: int, size: int, rotation: Counter[int]
) -> None:
    """Re-read one string-bearing value at each rotated offset, and tally.

    THE TAG WALK IS NOT MOVED. Only the offset the VALUE is read from is, which
    is what makes this evidence about the value grammar rather than about
    payload attribution. The judgement is the SHIPPED decoder's own: it returns
    a value only when the bytes account for the declared size exactly, so a
    non-None here is the shipped-redundancy oracle agreeing.

    Args:
        body: The decompressed body.
        type_word: The tag's type word.
        value_start: Where the value really begins.
        size: The value's declared extent.
        rotation: The accumulator, keyed by delta and mutated in place.
    """
    rotation[_ROTATION_DENOMINATOR] += 1
    for delta in _VALUE_ROTATIONS:
        decoded = objects._decode_value(body, type_word, value_start + delta, size, None)  # noqa: SLF001
        if decoded is not None:
            rotation[delta] += 1


#: The key the string-bearing denominator is tallied under. Chosen outside the
#: delta range so it cannot collide with one.
_ROTATION_DENOMINATOR: Final = 1000


def _walk_tags(
    body: bytes, at: int, end: int, rotation: Counter[int] | None = None
) -> tuple[int, Mapping[str, str]] | None:
    """Walk property tags to the ``None`` terminator, keeping name to type.

    IT RETURNS THE NAME-TO-TYPE MAP RATHER THAN A BARE SET OF WORDS, and that
    is what makes the unmeasured-type assertion able to fail at all. The
    shipped decoder returns a mapping keyed by property NAME; the tag's type
    word is not in it. Without a join on the name there is nothing to test a
    decoded value's PROVENANCE against, and the only thing left to check is its
    Python shape - which is the closed set of shapes any implementation can
    return, so the check is true by construction.

    The map holds property names, which are world content. It never leaves the
    judging frame: :func:`_tally_one_record` reduces it to counts and to words
    intersected with a repo literal, and :func:`_sweep_payload_tags` keeps only
    its values.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the payload.
        rotation: When supplied, the value-start rotation accumulator. Only the
            tag sweep passes one, so the tally is over the library exactly once.

    Returns:
        The offset just past the terminator and the record's property name to
        type-word map, or None if the walk breaks.
    """
    types: dict[str, str] = {}
    for _ in range(_TAG_CAP):
        name = _text(body, at, end)
        if name is None:
            return None
        if name[0] == "None":
            return (name[1], types)
        tag = _read_one_tag(body, name[1], end)
        if tag is None:
            return None
        at, type_word, value_start, size = tag
        types[name[0]] = type_word
        if rotation is not None and type_word in _STRING_BEARING_TYPES:
            _tally_value_rotation(body, type_word, value_start, size, rotation)
    return None


@dataclass(frozen=True)
class _TagSweep:
    """What the payload sweep observed, as scalars and nothing else.

    NO DECODED STRING LEAVES THE SWEEP, and that is a mechanism here rather
    than a hope. An earlier revision returned the distinct type WORDS and an
    assertion rendered one with ``!r``, on the reasoning that a property type
    word is format vocabulary and not world content. That reasoning holds only
    while the walk is SYNCHRONISED, and the assertion fires exactly when it is
    not: under a deliberate one-record misalignment across this library the
    walk yields 17 distinct words instead of 16, one of which is not a type
    word at all. So the words are now reduced to counts INSIDE the sweep, where
    no frame renders them, and the guarantee in the module docstring is true by
    construction instead of by argument.

    Attributes:
        payloads: Payloads examined, per pair.
        walked: Of those, ones reaching a terminator, per pair.
        exact: Of those, ones whose terminator IS the payload's final byte.
        distinct_type_words: How many distinct property type words were seen.
        malformed_type_words: How many of those are not shaped like an Unreal
            property type word. The judgement is made in the sweep; only the
            count comes out.
        unrecorded_type_words: How many distinct type words are neither
            decoded nor named in ``objects.UNMEASURED_PAYLOAD_REGIONS``.
            Judged in the sweep for the same reason as the field above.
        region_keys_the_library_holds: Which keys of
            ``objects.UNMEASURED_PAYLOAD_REGIONS`` were actually seen as a
            top-level type word. THIS ONE CARRIES WORDS AND IS STILL CONTAINED,
            by a mechanism rather than by an argument: it is intersected with
            that table's own keys INSIDE the sweep, so every word that can
            leave is provably a literal already in tracked source. A
            desynchronised walk yields words outside the table, and those are
            dropped by the intersection rather than reported.
        string_bearing_tags: How many tags carry a value that states its own
            length, and so can be checked against the tag's declared size.
        redundancy_agreements: How many of those agreed, by VALUE-START delta.
            Delta 0 is the shipped alignment. The others are the control.
        failures: Exception type names from any save that did not walk.
    """

    payloads: Mapping[tuple[int, int], int]
    walked: Mapping[tuple[int, int], int]
    exact: Mapping[tuple[int, int], int]
    distinct_type_words: int
    malformed_type_words: int
    unrecorded_type_words: int
    region_keys_the_library_holds: frozenset[str]
    string_bearing_tags: int
    redundancy_agreements: Mapping[int, int]
    failures: tuple[str, ...]


def _library_save_paths() -> tuple[Path, ...]:
    """Every save file on this machine, or an empty tuple.

    IT HOLDS EVERY `Exception` AND EVERY `SystemExit`, stated that way rather
    than as "it never raises" because that absolute is false: a
    `KeyboardInterrupt` still unwinds, deliberately. See the module docstring.

    THE DISCOVERY CALLS USED TO SIT OUTSIDE EVERY ``try`` IN BOTH SWEEPS, which
    is the one shape this module's containment discipline cannot survive: the
    account directory's NAME is the platform account id, and a failure in
    ``resolve_account_dir`` or in the glob unwinds through a frame holding it,
    where a traceback renderer showing locals prints it (CLAUDE.md section 2,
    non-negotiable 3). Every one of those calls is inside the ``try`` here, and
    ``root`` and ``account`` are bound in THIS frame and nowhere else, so there
    is no failure path that unwinds through a frame holding either.

    Nothing is reported about the failure - not even a type name, which the
    per-save handlers below do collect. A type name is safe; a frame that has
    to unwind to produce one is not.

    Returns:
        The save paths, sorted, or an empty tuple when there is no library.
    """
    try:
        root = locate.resolve_save_root()
        account = locate.resolve_account_dir(root) if root is not None else None
        return () if account is None else tuple(sorted(account.glob("*.sav")))
    # `SystemExit` is named because it is NOT an `Exception` - `except
    # Exception` alone lets it through, and it unwinds carrying the account
    # directory exactly as any other type would. `KeyboardInterrupt` is
    # deliberately still free to unwind; see the module docstring.
    except (Exception, SystemExit):
        return ()


def _cached_usmap_or_none() -> usmap.PropertyMap | None:
    """Load the shipped property mapping, or None.

    IT HOLDS EVERY `Exception` AND EVERY `SystemExit`, on the same terms as
    :func:`_library_save_paths`.

    The other call the decode sweep made outside every ``try``. It resolves the
    game install, so the same argument as :func:`_library_save_paths` applies.

    Returns:
        The mapping, or None when there is none or it did not load.
    """
    try:
        return usmap.cached_usmap()
    except (Exception, SystemExit):  # see _library_save_paths
        return None


def _sweep_payload_tags() -> _TagSweep | None:
    """Walk every payload of every real save and return COUNTS ONLY.

    Contained as ``test_objects._sweep_the_real_library`` is: every step
    wrapped, every failure reduced to a type NAME inside this helper before it
    can reach a frame anyone renders, and never a path, a body or a decoded
    world string out.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None

    payloads: dict[tuple[int, int], int] = {}
    walked: dict[tuple[int, int], int] = {}
    exact: dict[tuple[int, int], int] = {}
    words: set[str] = set()
    rotation: Counter[int] = Counter()
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file and a save of a
            # version this project does not parse - stay silent skips, because
            # the library legitimately holds both and the callers treat any
            # recorded failure as fatal.
            continue
        except (Exception, SystemExit) as exc:
            # THE BACKSTOP, for the reason the broad handler below states:
            # anything unexpected escaping here unwinds through
            # `path.read_bytes()`, whose bound `self` IS the save path, and
            # pytest renders the arguments of every frame it unwinds with no
            # opt-in flag.
            failures.append(type(exc).__name__)
            continue
        pair = (parsed.header_version, parsed.save_version)
        if pair not in objects.MEASURED_BODY_LAYOUTS:
            continue
        # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
        # carrying the save bytes, which is the leak this containment closes.
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            for record in table.records:
                end = record.body_offset + record.body_length
                payloads[pair] = payloads.get(pair, 0) + 1
                start: int | None = record.body_offset
                if record.kind == objects.KIND_ACTOR:
                    start = _skip_actor_head(body, record.body_offset, end)
                if start is None:
                    continue
                walk = _walk_tags(body, start, end, rotation)
                if walk is None:
                    continue
                landed, types = walk
                words.update(types.values())
                walked[pair] = walked.get(pair, 0) + 1
                if landed == end:
                    exact[pair] = exact.get(pair, 0) + 1
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    # The words are JUDGED here and discarded here. Nothing below this line can
    # render one, which is what makes the module's "counts only" a mechanism.
    return _TagSweep(
        payloads=MappingProxyType(payloads),
        walked=MappingProxyType(walked),
        exact=MappingProxyType(exact),
        distinct_type_words=len(words),
        malformed_type_words=sum(
            1 for word in words if not (word.isascii() and word.endswith("Property"))
        ),
        unrecorded_type_words=len(
            (words - _MEASURED_VALUE_TYPES) - set(objects.UNMEASURED_PAYLOAD_REGIONS)
        ),
        region_keys_the_library_holds=frozenset(words & set(objects.UNMEASURED_PAYLOAD_REGIONS)),
        string_bearing_tags=rotation[_ROTATION_DENOMINATOR],
        redundancy_agreements=MappingProxyType(
            {delta: rotation[delta] for delta in _VALUE_ROTATIONS}
        ),
        failures=tuple(sorted(set(failures))),
    )


def _sweep_or_skip() -> _TagSweep:
    """Fetch the sweep, skipping the test when there is no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_payload_tags()
    if sweep is None:
        pytest.skip("no save library on this machine - the payload sweep is not gradeable here")
    assert sweep.failures == (), f"failures walking real bodies: {sweep.failures}"
    return sweep


def _assert_walker_is_live(sweep: _TagSweep) -> None:
    """THE NON-VACUITY CONTROL - prove the detector detects before asserting a zero.

    THIS EXISTS BECAUSE THE ZEROS BELOW ARE OTHERWISE INERT. An assertion that
    some count is 0 passes just as happily when the walker is broken and finds
    nothing as when it works and there is genuinely nothing to find, so on its
    own it guards nothing. That is the failure class that left session 5 with
    six vacuously-passing assertions, and what eventually caught it was a
    control of exactly this shape - one proving the detector works, on the host
    it is running on, in the same run.

    Both mutants this was validated against are caught here and nowhere else:
    a no-op attribution empties ``walked`` entirely, and rotating the alignment
    by one record leaves it SHORT of ``payloads`` rather than empty - which is
    why the assertion is equality and not ``> 0``. The weaker form passes under
    the rotation, and that was measured rather than assumed.

    Args:
        sweep: The sweep to check.
    """
    present = [pair for pair in TAGGED_PAIRS if pair in sweep.payloads]
    assert present, (
        "no save of a tagged pair is on this machine, so every zero asserted below "
        "would be vacuous; this control refuses to let them pass unexamined"
    )
    for pair in present:
        assert sweep.walked.get(pair, 0) == sweep.payloads[pair], (
            f"the walker reaches a terminator on only {sweep.walked.get(pair, 0)} of "
            f"{sweep.payloads[pair]} payloads of pair {pair}, so it is not working on this "
            "host and any zero asserted against it is vacuous rather than true"
        )


def test_three_pairs_reach_a_property_terminator_on_every_payload() -> None:
    """The positive result, as an invariant rather than as a count.

    Asserting "every payload" rather than "77263 payloads" is deliberate: the
    operator plays this game, so an absolute count is a number that goes red on
    the next autosave for no defect at all.
    """
    sweep = _sweep_or_skip()

    for pair in TAGGED_PAIRS:
        if pair not in sweep.payloads:
            continue
        assert sweep.walked.get(pair, 0) == sweep.payloads[pair], (
            f"pair {pair} reaches a property terminator on only "
            f"{sweep.walked.get(pair, 0)} of {sweep.payloads[pair]} payloads"
        )


def test_save_60_refuses_the_grammar_the_other_pairs_accept() -> None:
    """The negative result, and it is about THIS MODULE'S LEGACY READER.

    THE NAME IS KEPT DELIBERATELY. It reads as a claim about the save and the
    claim below is narrower, but `docs/LEDGER.md` and `docs/history_notes.md`
    cite this symbol by name and both are append-only - renaming it would rot
    two citations in records that are never edited to chase a rename. The
    docstring is where the claim lives, so the docstring is what changed.

    WHAT THIS ARM MEASURES, NARROWED 2026-09-11 BECAUSE ITS OLD WORDING BECAME
    FALSE. The sweep below carries its own independent reader of the LEGACY tag
    grammar. Its zero is a true statement about that grammar and, until CS-980,
    this docstring read it as a statement about the file: "save 60 reaches a
    terminator on no payload at all". Ground truth refuted that - a third-party
    tool renders container contents out of exactly these saves, and the shipped
    reader now decodes every payload of the pair under a different tag grammar
    measured from the bytes. Only the legacy grammar refuses them, which is
    precisely why a third dispatch exists.

    SO THE ARM IS KEPT AND ITS CLAIM IS SHRUNK. The legacy reader must go on
    refusing this pair: if it ever stopped, the two grammars would have
    converged and the dispatch that tells them apart would be grading nothing.
    What the SHIPPED reader does with the pair is graded in
    ``tests/save/test_property_payload_14_60.py``, which is where the positive
    claim belongs.

    ADR 0005's refuted arithmetic route is still the hazard being pinned: three
    measured neighbours make a fourth look derivable, and it was not.

    The zero here is guarded by :func:`_assert_walker_is_live`, without which
    it also passes when the walker reaches a terminator on NOTHING at all.
    """
    sweep = _sweep_or_skip()
    _assert_walker_is_live(sweep)
    if UNMEASURED_PAIR not in sweep.payloads:
        pytest.skip("no save of the unmeasured pair on this machine")

    assert sweep.walked.get(UNMEASURED_PAIR, 0) == 0, (
        f"the LEGACY reader now reaches a terminator on "
        f"{sweep.walked.get(UNMEASURED_PAIR, 0)} payloads of pair {UNMEASURED_PAIR}. "
        "That is the two grammars converging, which would make the dispatch "
        "between them grade nothing - measure it properly rather than relaxing "
        "this arm"
    )


def test_the_run_after_the_terminator_is_unmeasured() -> None:
    """THE HONESTY CONTROL, and the reason this module is not a closed result.

    Reaching the terminator is NOT reaching the payload's final byte. A
    variable trailing run follows it whose grammar nobody here has measured, so
    this asserts that the PROPERTY walk is terminator-exact and is NOT
    boundary-exact. The BODY walk is boundary-exact; they are different walks.

    It is written as an assertion rather than a comment because a comment does
    not fail. If a later slice measures the trailing run, this test is what
    tells them the claim changed - and the honest edit then is to replace it
    with a boundary-exact assertion, not to delete it.

    IT DID NOT DO THAT JOB WHEN IT WAS FIRST WRITTEN, which an adversary
    demonstrated: with no live control, ``exact`` is 0 when the walk is deleted
    outright, so the test stayed green while asserting that the distinction it
    names still holds. A control that calls itself the honesty control and
    cannot fail is worse than no control, because it is also a claim.
    """
    sweep = _sweep_or_skip()
    _assert_walker_is_live(sweep)
    measured = [pair for pair in TAGGED_PAIRS if pair in sweep.payloads]

    # NOT ONE payload of the whole library lands on its boundary, so the
    # trailing run is universal rather than occasional - which is why "reaches
    # the terminator" must never be reported as "reads the payload".
    for pair in measured:
        assert sweep.exact.get(pair, 0) == 0, (
            f"pair {pair} now lands on the payload boundary for "
            f"{sweep.exact.get(pair, 0)} of {sweep.walked.get(pair, 0)} payloads. If that is "
            "real, the trailing run has been measured and this module's stated limit is out "
            "of date - replace this with a boundary-exact assertion rather than deleting it"
        )


#: The type words whose VALUE encoding this project has measured, transcribed
#: here rather than imported from :mod:`clockspeed.save.objects`. Sharing the
#: constant would make this suite a restatement of that module's opinion
#: instead of a check on it, which is the same reasoning that module records
#: above its own ``Measured layout constants`` block. THE CITATION IS BY NAME
#: RATHER THAN BY LINE: a line number is the same rot as a restated count, and
#: correcting one only resets the clock - this one had already drifted.
#: THE THREE CONTAINER WORDS ARE HERE FOR THEIR ELEMENT FRAMING - CS-830, and
#: what that promotes is narrower than the others in this set. For a scalar the
#: whole VALUE is measured; for a container what is measured is the element
#: count, the element type words and every element's EXTENT, and the interior of
#: a struct element is not. That distinction is graded in
#: ``tests/save/test_container_elements.py`` rather than restated here - what
#: this transcription owes is agreement with the shipped set, and nothing else.
_MEASURED_VALUE_TYPES: Final = frozenset(
    {
        "ArrayProperty",
        "BoolProperty",
        "ByteProperty",
        "EnumProperty",
        "FloatProperty",
        "Int8Property",
        "IntProperty",
        "MapProperty",
        "NameProperty",
        "ObjectProperty",
        "SetProperty",
        "SoftObjectProperty",
        "StrProperty",
        "UInt32Property",
    }
)

#: How a building's class path is recognised in a type path.
_BUILDING_MARKERS: Final = (".Build_", "/Build_")

#: An object reference decodes to a level name and an object path.
_OBJECT_REFERENCE_PARTS: Final = 2

#: The band an ordinary world float32 falls in, as a DOMAIN bound rather than a
#: value fitted to this corpus: a coordinate, a clock speed, a power figure or a
#: fraction sits between a thousandth and a billion in absolute value. It is
#: deliberately loose. What it has to separate is ordinary magnitudes from the
#: 1e-38-and-1e38 debris a byte-swapped read produces, and that separation
#: survives moving either end by orders of magnitude.
_FLOAT_PLAUSIBLE_LOW: Final = 1e-3
_FLOAT_PLAUSIBLE_HIGH: Final = 1e9

#: The delta applied to one shipped width at a time. A MUTATION rather than a
#: measurement, which is why a number is written here where a count would not
#: be. Minus one is the smallest fault that is not an equivalent mutant: widths
#: are stepped through ``range()``, which treats a negative exactly as it treats
#: zero, and every shipped width is at least one so none can go negative.
_WIDTH_MUTATION: Final = -1

#: The unmutated configuration's key in the census accumulators. Not a width
#: name, and chosen to collide with none.
_SHIPPED: Final = "<shipped>"

#: The two widths that live outside the two tables, named so the census can
#: address them the same way. Both are attributes of the shipped module.
_GUID_WIDTH_NAME: Final = "GUID_BYTES"
_SOFT_TAIL_NAME: Final = "_SOFT_OBJECT_TAIL_BYTES"

#: The type words the two byte-order oracles in this module actually score.
#: Transcribed rather than imported, for the reason the measured-set
#: transcription gives: importing the constant under test asserts only that the
#: module equals itself. Keep in step with :func:`_tally_decoded_values`.
_MAGNITUDE_SCORED_TYPES: Final = frozenset({"FloatProperty", "IntProperty"})

#: Byte positions within a stored 4-byte scalar, named so the two readings are
#: not two anonymous shifts. Index 3 is the most significant byte under the
#: declared little-endian order; index 0 becomes the most significant one when
#: the same bytes are read the other way.
_HIGH_BYTE_AS_READ_SHIFT: Final = 24
_ONE_BYTE_MASK: Final = 0xFF
_FOUR_BYTE_MASK: Final = 0xFFFFFFFF


@dataclass(frozen=True)
class _DecodeSweep:
    """What the DECODE sweep observed, as scalars and nothing else.

    Same containment as :class:`_TagSweep` and for the same reason: a decoded
    property VALUE is world content in a way a type word only becomes when the
    walk desynchronises. Nothing here holds one. The judgements - is this
    record a building, did it carry a measured type, did the shipped decoder
    return anything - are all made INSIDE the sweep, and only integers leave.

    Attributes:
        buildings: Building records whose payload reached a terminator.
        buildings_with_a_measured_tag: Of those, ones carrying at least one tag
            whose type is in :data:`_MEASURED_VALUE_TYPES`, judged by THIS
            module's walker rather than by the shipped one.
        buildings_yielding_a_value: Of those, ones the SHIPPED decoder returned
            at least one property for.
        records_with_no_tag_at_all: Records whose property list is empty. Not a
            defect - it is why the count above is not every building.
        buildings_yielding_a_value_rotated: The same decode run against a
            payload extent moved one byte forward. THE CONTROL - see
            :func:`test_the_decode_collapses_when_the_payload_start_is_rotated`.
        unmeasured_tags: Tags whose type word is outside the measured set.
        values_off_type: Decoded values whose Python type is not one the
            measured set can produce. A WEAK CHECK, kept with its limit stated:
            the measured set spans bool, int, float, str and a 2-tuple of str,
            which is very nearly the whole space of things any decoder would
            return, so this cannot see a value fabricated from an unmeasured
            type. The field below is what does.
        decoded_values: How many values the shipped decoder returned in total.
            The liveness floor for the two fields below.
        decoded_values_from_an_unmeasured_type: Decoded values whose TAG TYPE
            WORD is outside :data:`_MEASURED_VALUE_TYPES`. Non-negotiable 7's
            actual claim, and it is only checkable because
            :func:`_walk_tags` carries the name-to-type join.
        decoded_names_this_walk_never_saw: Decoded names this module's own walk
            found no tag for. Separated from the field above so a disagreement
            between the two walkers reads as a disagreement rather than as a
            provenance failure.
        measured_types_present: Which measured type words the library actually
            carries at top level. Intersected with :data:`_MEASURED_VALUE_TYPES`
            INSIDE the sweep, so every word that can leave is provably one of
            the literals in this file.
        measured_types_yielding: Of those, the ones the shipped decoder
            returned at least one value for. Contained identically.
        rotated_actor_buildings: Of the buildings the rotation control moves,
            how many are actors - the ones whose payload opens with a head.
        rotated_actor_buildings_failing_in_the_head: Of those, how many
            collapse inside :func:`_skip_actor_head`, before one property tag
            is examined. THIS IS THE FIELD THAT NAMES WHAT THAT CONTROL
            ACTUALLY TESTS.
        failures: Exception type names from any save that did not sweep.
        int32_values: Decoded values whose TAG TYPE WORD is IntProperty. The
            liveness floor for the two fields below.
        int32_high_byte_zero_as_read: Of those, how many carry a zero in the
            most significant STORED byte under the declared order.
        int32_high_byte_zero_if_swapped: Of those, how many would carry a zero
            in that position if the four bytes were read the other way. It is
            the SAME population scored the other way, so the two exchange
            values under a byte-order mutant rather than drifting apart.
        float32_values: Decoded values whose tag type word is FloatProperty.
        float32_plausible_as_read: Of those, how many are finite, non-zero and
            inside :data:`_FLOAT_PLAUSIBLE_LOW` to :data:`_FLOAT_PLAUSIBLE_HIGH`
            in absolute value.
        float32_plausible_if_swapped: The same judgement applied to the same
            bytes read the other way.
    """

    buildings: int
    buildings_with_a_measured_tag: int
    buildings_yielding_a_value: int
    records_with_no_tag_at_all: int
    buildings_yielding_a_value_rotated: int
    unmeasured_tags: int
    values_off_type: int
    decoded_values: int
    decoded_values_from_an_unmeasured_type: int
    decoded_names_this_walk_never_saw: int
    measured_types_present: frozenset[str]
    measured_types_yielding: frozenset[str]
    rotated_actor_buildings: int
    rotated_actor_buildings_failing_in_the_head: int
    failures: tuple[str, ...]
    int32_values: int = 0
    int32_high_byte_zero_as_read: int = 0
    int32_high_byte_zero_if_swapped: int = 0
    float32_values: int = 0
    float32_plausible_as_read: int = 0
    float32_plausible_if_swapped: int = 0


@dataclass
class _DecodeTally:
    """The decode sweep's running accumulators, gathered so the folder takes one.

    Attributes:
        counts: Integer tallies, by key.
        measured_present: Measured type words seen at top level.
        measured_yielding: Measured type words that produced a value.
    """

    counts: Counter[str]
    measured_present: set[str]
    measured_yielding: set[str]


def _is_measured_shape(value: object) -> bool:
    """Whether a decoded value has a shape the measured types can produce.

    The measured types yield these Python shapes: ``bool`` from BoolProperty,
    ``int`` from the integer widths and a raw ByteProperty, ``float`` from
    FloatProperty, ``str`` from the one-string types, a 2-tuple of ``str`` from
    the object references, and - since CS-830 - an ``objects.ContainerValue``
    from the three container words. Anything else means a decoder returned
    something no measured branch can produce.

    THE CONTAINER SHAPE IS ADMITTED BY ITS TYPE RATHER THAN BY DUCK-TYPING, so
    a decoder returning some other structure for a container still reddens
    here. It remains the WEAK check its field docstring says it is: the point
    of admitting the shape is not to grade containers - that is
    ``tests/save/test_container_elements.py`` - it is to stop this check going
    red for a value it was never about.

    Args:
        value: One decoded property value.

    Returns:
        True when the shape is one a measured type produces.
    """
    if isinstance(value, objects.ContainerValue):
        return True
    if isinstance(value, tuple):
        return len(value) == _OBJECT_REFERENCE_PARTS and all(
            isinstance(part, str) for part in value
        )
    return isinstance(value, (bool, int, float, str))


def _is_building(type_path: str) -> bool:
    """Whether a class path names a built structure.

    Args:
        type_path: The record's class path.

    Returns:
        True when the path carries a building marker.
    """
    return any(marker in type_path for marker in _BUILDING_MARKERS)


def _is_plausible_magnitude(value: float) -> bool:
    """Whether a float32 sits in the ordinary-world band.

    IT RELIES ON COMPARISON SEMANTICS FOR THE NON-FINITE CASES rather than on a
    finiteness call, and that is deliberate - do not "fix" it by adding one. A
    comparison against a NaN is False either way, ``abs`` of an infinity exceeds
    the upper bound, and an exact zero falls under the lower one, so all three
    are excluded by the band itself. Zero has to be excluded rather than counted
    plausible because its bit pattern is symmetric: it reads as zero under both
    byte orders and so discriminates nothing, while inflating both sides of the
    comparison that rests on this.

    Args:
        value: One decoded float32.

    Returns:
        True when the magnitude is an ordinary one.
    """
    return _FLOAT_PLAUSIBLE_LOW <= abs(value) <= _FLOAT_PLAUSIBLE_HIGH


def _tally_int32_byte_order(value: int, tally: _DecodeTally) -> None:
    """Score one int32 for the small-magnitude signature under both readings.

    The byte positions are derived by masking rather than by re-packing, so this
    is total over any Python int and cannot raise on a value a mutated decoder
    put out of int32 range.

    Args:
        value: One decoded int32, as the shipped reader returned it.
        tally: The accumulator, mutated in place.
    """
    stored = value & _FOUR_BYTE_MASK
    tally.counts["int32"] += 1
    if (stored >> _HIGH_BYTE_AS_READ_SHIFT) & _ONE_BYTE_MASK == 0:
        tally.counts["int32_high_zero"] += 1
    if stored & _ONE_BYTE_MASK == 0:
        tally.counts["int32_high_zero_swapped"] += 1


def _tally_float32_byte_order(value: float, tally: _DecodeTally) -> None:
    """Score one float32 for ordinary magnitude under both readings.

    Args:
        value: One decoded float32, as the shipped reader returned it.
        tally: The accumulator, mutated in place.
    """
    tally.counts["float32"] += 1
    stored = struct.pack("<f", value)
    (swapped,) = struct.unpack(">f", stored)
    if _is_plausible_magnitude(value):
        tally.counts["float32_plausible"] += 1
    if _is_plausible_magnitude(swapped):
        tally.counts["float32_plausible_swapped"] += 1


def _tally_decoded_values(
    decoded: Mapping[str, object], types: Mapping[str, str], tally: _DecodeTally
) -> None:
    """Judge one record's decoded values against the tags they came out of.

    THE JOIN ON ``name`` IS THE WHOLE POINT. The shipped decoder returns a
    mapping keyed by property name and carries no type word, so without this
    join there is nothing to check a value's PROVENANCE against and the only
    remaining oracle is its Python shape - which every implementation satisfies.

    Args:
        decoded: What the shipped decoder returned for one record.
        types: The record's property name to type-word map, from this module's
            own walk of the same payload.
        tally: The accumulator, mutated in place.
    """
    tally.counts["decoded"] += len(decoded)
    for name, value in decoded.items():
        word = types.get(name)
        if word is None:
            tally.counts["decoded_unseen"] += 1
        elif word in _MEASURED_VALUE_TYPES:
            tally.measured_yielding.add(word)
        else:
            tally.counts["from_unmeasured"] += 1
        if not _is_measured_shape(value):
            tally.counts["off_type"] += 1
        # KEYED ON THE TAG TYPE WORD, never on the Python type, because `bool`
        # is a subclass of `int` and a BoolProperty would otherwise be scored
        # as an int32 whose bytes were never stored as one.
        if word == "IntProperty" and isinstance(value, int) and not isinstance(value, bool):
            _tally_int32_byte_order(value, tally)
        elif word == "FloatProperty" and isinstance(value, float):
            _tally_float32_byte_order(value, tally)


def _tally_one_record(
    body: bytes,
    record: objects.ObjectRecord,
    property_map: usmap.PropertyMap,
    tally: _DecodeTally,
) -> None:
    """Fold one record's decode result into the running counts.

    THE JUDGEMENTS HAPPEN HERE and only integers and repo-literal words leave,
    which is the same containment :class:`_TagSweep` uses. This frame is the
    only one that ever holds a decoded value or a property name, and it holds
    either no longer than the predicate it reduces it to.

    EVERY RECORD IS DECODED, not only the buildings. The building counters
    below still answer CS-413's own clause, but the per-type coverage the
    non-negotiable-7 assertions rest on has to be gathered over the whole
    library: a type carried by no building would otherwise be reported as
    covered by a sweep that never looked at one.

    Args:
        body: The decompressed body.
        record: The record to decode.
        property_map: The parsed mapping.
        tally: The accumulator, mutated in place.
    """
    end = record.body_offset + record.body_length
    start: int | None = record.body_offset
    if record.kind == objects.KIND_ACTOR:
        start = _skip_actor_head(body, record.body_offset, end)
    if start is None:
        return
    walk = _walk_tags(body, start, end)
    if walk is None:
        return
    types = walk[1]
    words = set(types.values())
    if not words:
        tally.counts["no_tags"] += 1
    tally.counts["unmeasured"] += len(words - _MEASURED_VALUE_TYPES)
    tally.measured_present |= words & _MEASURED_VALUE_TYPES

    decoded = objects.read_properties(body, record, property_map).properties
    _tally_decoded_values(decoded, types, tally)

    if not _is_building(record.type_path):
        return
    tally.counts["buildings"] += 1
    if not words & _MEASURED_VALUE_TYPES:
        return
    tally.counts["with_measured"] += 1
    if decoded:
        tally.counts["yielding"] += 1
    moved = record.with_payload(record.body_offset + 1, record.body_length - 1)
    if objects.read_properties(body, moved, property_map).properties:
        tally.counts["rotated"] += 1
    # WHERE the rotated read actually dies, which is what makes the name of
    # the test consuming this honest rather than aspirational.
    if record.kind == objects.KIND_ACTOR:
        tally.counts["rotated_actors"] += 1
        moved_end = moved.body_offset + moved.body_length
        if _skip_actor_head(body, moved.body_offset, moved_end) is None:
            tally.counts["rotated_head_failed"] += 1


@lru_cache(maxsize=1)
def _sweep_decoded_values() -> _DecodeSweep | None:
    """Run the SHIPPED decoder over every real payload and return COUNTS ONLY.

    Contained exactly as :func:`_sweep_payload_tags` is - see that docstring.
    The one addition is that decoded VALUES pass through this frame, so it
    holds none of them beyond the predicate it reduces them to.

    Cached because four tests consume it and the sweep reads every save on the
    machine; the tag sweep above predates the cache and re-reads per test.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    property_map = _cached_usmap_or_none()
    if not saves or property_map is None:
        return None

    tally = _DecodeTally(counts=Counter(), measured_present=set(), measured_yielding=set())
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file and a save of a
            # version this project does not parse - stay silent skips, because
            # the library legitimately holds both and the callers treat any
            # recorded failure as fatal.
            continue
        except (Exception, SystemExit) as exc:
            # THE BACKSTOP, for the reason the broad handler below states:
            # anything unexpected escaping here unwinds through
            # `path.read_bytes()`, whose bound `self` IS the save path, and
            # pytest renders the arguments of every frame it unwinds with no
            # opt-in flag.
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in TAGGED_PAIRS:
            continue
        # BROAD BY DESIGN, for the reason given in _sweep_payload_tags.
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            for record in table.records:
                _tally_one_record(body, record, property_map, tally)
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return _DecodeSweep(
        buildings=tally.counts["buildings"],
        buildings_with_a_measured_tag=tally.counts["with_measured"],
        buildings_yielding_a_value=tally.counts["yielding"],
        records_with_no_tag_at_all=tally.counts["no_tags"],
        buildings_yielding_a_value_rotated=tally.counts["rotated"],
        unmeasured_tags=tally.counts["unmeasured"],
        values_off_type=tally.counts["off_type"],
        decoded_values=tally.counts["decoded"],
        decoded_values_from_an_unmeasured_type=tally.counts["from_unmeasured"],
        decoded_names_this_walk_never_saw=tally.counts["decoded_unseen"],
        # Intersected with this module's own literal, so no word that is not
        # already written down in tracked source can leave the sweep.
        measured_types_present=frozenset(tally.measured_present & _MEASURED_VALUE_TYPES),
        measured_types_yielding=frozenset(tally.measured_yielding & _MEASURED_VALUE_TYPES),
        rotated_actor_buildings=tally.counts["rotated_actors"],
        rotated_actor_buildings_failing_in_the_head=tally.counts["rotated_head_failed"],
        failures=tuple(sorted(set(failures))),
        int32_values=tally.counts["int32"],
        int32_high_byte_zero_as_read=tally.counts["int32_high_zero"],
        int32_high_byte_zero_if_swapped=tally.counts["int32_high_zero_swapped"],
        float32_values=tally.counts["float32"],
        float32_plausible_as_read=tally.counts["float32_plausible"],
        float32_plausible_if_swapped=tally.counts["float32_plausible_swapped"],
    )


def _decode_sweep_or_skip() -> _DecodeSweep:
    """Fetch the decode sweep, skipping the test when there is no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_decoded_values()
    if sweep is None:
        pytest.skip("no save library or no property mapping on this machine")
    assert sweep.failures == (), f"failures decoding real bodies: {sweep.failures}"
    return sweep


@dataclass(frozen=True)
class _WidthCensus:
    """What each shipped width is worth, as COUNTS ONLY.

    Same containment as the sweeps above. The keys are the shipped tables' own
    keys, which are literals in tracked source rather than anything read out of
    a save, so no world content can leave through them.

    Attributes:
        payloads: Payload extents enumerated across the tagged pairs.
        reach_shipped: Of those, how many reach a terminator unmutated.
        disagreements_shipped: Measured values whose bytes disagreed, unmutated.
        reach_by_cursor_width: Width name to how many payloads still reach a
            terminator with that width alone mis-stated.
        disagreements_by_extent_width: Width name to how many values disagreed
            with that width alone mis-stated.
        reach_by_extent_width: The same extent mutants scored by REACH, which is
            what shows they do not move the cursor.
        failures: Exception type names from any save that did not sweep.
    """

    payloads: int
    reach_shipped: int
    disagreements_shipped: int
    reach_by_cursor_width: Mapping[str, int]
    disagreements_by_extent_width: Mapping[str, int]
    reach_by_extent_width: Mapping[str, int]
    failures: tuple[str, ...]


@contextmanager
def _width_mutated(word: str) -> Iterator[None]:
    """Mis-state ONE shipped width for the duration of the block.

    The four shipped widths live in four different shapes - two mapping values
    and two bare module attributes - so the dispatch below is over WHERE the
    width lives rather than over what it means. Every branch restores in a
    ``finally``, including the one that raises.

    Args:
        word: A width name, from either shipped table or the two module
            attributes named in this file's constants.

    Yields:
        Nothing. The module is mutated for the body of the block.
    """
    if word == _GUID_WIDTH_NAME:
        original = objects.GUID_BYTES
        objects.GUID_BYTES = original + _WIDTH_MUTATION  # type: ignore[misc]
        try:
            yield
        finally:
            objects.GUID_BYTES = original  # type: ignore[misc]
    elif word == _SOFT_TAIL_NAME:
        tail = objects._SOFT_OBJECT_TAIL_BYTES  # noqa: SLF001
        objects._SOFT_OBJECT_TAIL_BYTES = tail + _WIDTH_MUTATION  # type: ignore[misc]  # noqa: SLF001
        try:
            yield
        finally:
            objects._SOFT_OBJECT_TAIL_BYTES = tail  # type: ignore[misc]  # noqa: SLF001
    elif word in objects._TAG_EXTRA_STRINGS:  # noqa: SLF001
        shipped = dict(objects._TAG_EXTRA_STRINGS)  # noqa: SLF001
        bent = dict(shipped)
        bent[word] = shipped[word] + _WIDTH_MUTATION
        objects._TAG_EXTRA_STRINGS = MappingProxyType(bent)  # type: ignore[misc]  # noqa: SLF001
        try:
            yield
        finally:
            objects._TAG_EXTRA_STRINGS = MappingProxyType(shipped)  # type: ignore[misc]  # noqa: SLF001
    else:
        widths = dict(objects._FIXED_WIDTH_VALUES)  # noqa: SLF001
        width, code = widths[word]
        bent_widths = dict(widths)
        bent_widths[word] = (width + _WIDTH_MUTATION, code)
        objects._FIXED_WIDTH_VALUES = MappingProxyType(bent_widths)  # type: ignore[misc]  # noqa: SLF001
        try:
            yield
        finally:
            objects._FIXED_WIDTH_VALUES = MappingProxyType(widths)  # type: ignore[misc]  # noqa: SLF001


def _walk_extents(extents: list[tuple[bytes, int, int]]) -> tuple[int, int]:
    """Run the SHIPPED payload walker over one save's extents.

    Args:
        extents: Body, first tag offset and payload end, per record.

    Returns:
        How many reached a terminator, and how many values disagreed.
    """
    reached = disagreed = 0
    for body, start, end in extents:
        walked = objects._decode_payload(body, start, end)  # noqa: SLF001
        if walked is not None:
            disagreed += walked[2]
            reached += 1 if walked[3] else 0
    return reached, disagreed


def _extents_of(body: bytes, table: objects.ObjectTable) -> list[tuple[bytes, int, int]]:
    """Every payload extent in one parsed body.

    Args:
        body: The decompressed body.
        table: Its parsed record table.

    Returns:
        Body, first tag offset and payload end, per record whose head resolved.
    """
    out: list[tuple[bytes, int, int]] = []
    for record in table.records:
        end = record.body_offset + record.body_length
        start: int | None = record.body_offset
        if record.kind == objects.KIND_ACTOR:
            start = _skip_actor_head(body, record.body_offset, end)
        if start is not None:
            out.append((body, start, end))
    return out


def _width_classes() -> tuple[dict[str, int], dict[str, int]]:
    """The two width classes, built from the shipped module's own tables.

    Extracted so the disjointness check below can run in a frame that holds no
    save data. See :func:`test_the_two_width_classes_are_disjoint`.

    Returns:
        The cursor-advancing widths and the fixed-extent widths.
    """
    cursor = dict.fromkeys(objects._TAG_EXTRA_STRINGS, _WIDTH_MUTATION)  # noqa: SLF001
    cursor[_GUID_WIDTH_NAME] = _WIDTH_MUTATION
    extent = dict.fromkeys(objects._FIXED_WIDTH_VALUES, _WIDTH_MUTATION)  # noqa: SLF001
    extent[_SOFT_TAIL_NAME] = _WIDTH_MUTATION
    return cursor, extent


def test_the_two_width_classes_are_disjoint() -> None:
    """A width name in both classes would make one class's count the other's.

    IT LIVES HERE RATHER THAN IN THE SWEEP, AND THE PLACEMENT IS THE WHOLE
    POINT. Inside ``_sweep_width_census`` this check had two bad homes and no
    good one. In the per-save loop it sat under ``except (Exception,
    SystemExit)``, which catches ``AssertionError`` - so it could never
    actually fail a run, only add the bare word ``AssertionError`` to a
    failures list, and ``@lru_cache`` then cached that result. Hoisted above
    the loop it DID propagate, but it unwound through a frame where ``saves``
    holds the real library paths, and those carry the Windows account name, the
    numeric platform account id and the world name (non-negotiables 3 and 11).
    A CS-852 adversary measured one marker occurrence hoisted against zero
    inside the try. Trading a swallowed check for a real disclosure is not a
    repair.

    In its own function the frame holds two dicts of width NAMES and nothing
    else, no caller frame holds a save path, and the check finally does what it
    says: it runs once, it propagates, and it keeps its message. It also stops
    depending on the library being reachable and on some save reaching a tagged
    version pair, which is why it grades more than it did in either old home.
    """
    cursor, extent = _width_classes()
    overlap = sorted(cursor.keys() & extent.keys())
    assert overlap == [], (
        "a width name is in both classes, so one class's count would silently "
        f"be the other's: {overlap}"
    )


@lru_cache(maxsize=1)
def _sweep_width_census() -> _WidthCensus | None:
    """Score every shipped width by what mis-stating it costs. COUNTS ONLY.

    Contained exactly as :func:`_sweep_decoded_values` is - see that docstring.
    ONE DECOMPRESSION PER SAVE, with every configuration walked while that
    body is alive, so the peak cost is one body rather than the whole library.

    THE MUTATION IS APPLIED TO THE SHIPPED MODULE and to nothing else. Each
    width is read as a module global inside the reader, so replacing the
    attribute is a real fault in the real walker - no subprocess, no second
    checkout, no stale bytecode. Every one is restored in a ``finally``.

    Returns:
        The census, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None

    cursor, extent = _width_classes()

    reach: Counter[str] = Counter()
    disagree: Counter[str] = Counter()
    payloads = 0
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        except (Exception, SystemExit) as exc:  # see _sweep_decoded_values
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in TAGGED_PAIRS:
            continue
        # BROAD BY DESIGN, for the reason given in _sweep_payload_tags.
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            extents = _extents_of(body, table)
            payloads += len(extents)
            base = _walk_extents(extents)
            reach[_SHIPPED] += base[0]
            disagree[_SHIPPED] += base[1]
            for word in {**cursor, **extent}:
                with _width_mutated(word):
                    got = _walk_extents(extents)
                reach[word] += got[0]
                disagree[word] += got[1]
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return _WidthCensus(
        payloads=payloads,
        reach_shipped=reach[_SHIPPED],
        disagreements_shipped=disagree[_SHIPPED],
        reach_by_cursor_width=MappingProxyType({word: reach[word] for word in cursor}),
        disagreements_by_extent_width=MappingProxyType({word: disagree[word] for word in extent}),
        reach_by_extent_width=MappingProxyType({word: reach[word] for word in extent}),
        failures=tuple(sorted(set(failures))),
    )


def _width_census_or_skip() -> _WidthCensus:
    """Fetch the width census, skipping the test when there is no library.

    Returns:
        The census.
    """
    census = _sweep_width_census()
    if census is None:
        pytest.skip("no save library on this machine")
    assert census.failures == (), f"failures walking real bodies: {census.failures}"
    return census


def test_a_real_building_yields_at_least_one_decoded_property_value() -> None:
    """CS-413's decode clause, asserted as an EQUALITY rather than as a floor.

    ``> 0`` would be satisfied by a decoder that works on one building and
    fails on every other, which is the shape the project has already been
    bitten by - a liveness floor still passes a rotated alignment. So the claim
    is that EVERY building carrying a measured type decodes, and the floor is
    kept only to stop the equality passing vacuously at 0 == 0.

    NOTE WHAT IS DELIBERATELY NOT ASSERTED: that every building decodes. It
    does not, and that is measured rather than excused - some carry only types
    whose value grammar is unmeasured, and :data:`_DecodeSweep.records_with_no_tag_at_all`
    counts records whose property list is empty outright. An equality against
    ``buildings`` would be false, and writing it would have been the failure
    this project calls guessing.
    """
    sweep = _decode_sweep_or_skip()

    assert sweep.buildings_with_a_measured_tag > 0, (
        "no building on this machine carries a measured property type, so the "
        "equality below would pass vacuously at 0 == 0"
    )
    assert sweep.buildings_yielding_a_value == sweep.buildings_with_a_measured_tag, (
        f"the decoder returned a value for {sweep.buildings_yielding_a_value} of "
        f"{sweep.buildings_with_a_measured_tag} buildings that carry a type it claims to "
        "have measured; a decoder that works on some is a decoder that is wrong about "
        "which types it has measured"
    )


def test_the_decode_collapses_when_the_payload_start_is_rotated() -> None:
    """THE PAYLOAD-ATTRIBUTION CONTROL, and it is NOT evidence about values.

    IT WAS NAMED FOR SOMETHING IT DOES NOT TEST. Moving a record's payload
    start forward by one byte does collapse the decode, but the collapse
    happens inside :func:`_skip_actor_head` - the second assertion below
    measures that rather than describing it, and on this library it is EVERY
    actor building, not most of them. Not one property tag is examined, so this
    exercises zero lines of the tag grammar and zero lines of the value
    grammar. What it genuinely rules out is a payload attribution that would
    work equally well one byte over, which is worth having and is all it is.

    THE CONTROL THAT DOES COVER THE VALUE GRAMMAR IS
    :func:`test_the_shipped_redundancy_oracle_collapses_when_only_the_value_read_is_rotated`,
    which leaves the tag walk exactly where it is and moves only the offset a
    value is read from. Read the two together; neither substitutes for the
    other.

    The liveness floor stays, because an equality against zero is passable by a
    decoder that does nothing at all.
    """
    sweep = _decode_sweep_or_skip()

    assert sweep.buildings_yielding_a_value > 0, (
        "the decoder yielded nothing at the shipped alignment, so the collapse "
        "asserted below is the collapse of something that never worked"
    )
    assert sweep.buildings_yielding_a_value_rotated == 0, (
        f"{sweep.buildings_yielding_a_value_rotated} buildings still decode with their "
        "payload moved one byte forward. A grammar that reads the same world through a "
        "rotated window is not aligned to anything, and the decoded values are then not "
        "evidence about this save format"
    )
    assert sweep.rotated_actor_buildings > 0, (
        "no actor building was rotated at all, so the scope claim below is vacuous"
    )
    assert sweep.rotated_actor_buildings_failing_in_the_head == sweep.rotated_actor_buildings, (
        f"{sweep.rotated_actor_buildings_failing_in_the_head} of "
        f"{sweep.rotated_actor_buildings} rotated actor payloads fail in the actor head. "
        "If that is no longer ALL of them, this control has started reaching the tag "
        "grammar and its name and docstring are understating it - widen them rather "
        "than deleting this assertion"
    )


def test_the_shipped_redundancy_oracle_collapses_when_only_the_value_read_is_rotated() -> None:
    """THE CONTROL THAT ACTUALLY EXERCISES THE VALUE GRAMMAR.

    A string-bearing value states its own length, and the tag states the same
    length again a few bytes earlier. Those are two independent numbers in the
    shipped file, so their agreement is evidence the reader is where it thinks
    it is - but only if the agreement COLLAPSES when the read is moved. An
    oracle that holds at every offset is measuring self-consistency and calling
    it alignment.

    THE TAG WALK IS NOT MOVED HERE. It stays exactly where the shipped grammar
    puts it and only the offset the VALUE is read from shifts, which is what
    separates this from the payload-start control above - that one dies in the
    actor head before any of this runs. The judgement is the SHIPPED decoder's,
    not a copy of it: ``objects._decode_value`` returns a value only when the
    bytes account for the declared size exactly.

    ASSERTED AS A RATE AND A FACTOR, never as counts. The operator plays this
    game, so an absolute figure here is red on the next autosave for no defect
    at all - which is the same reason the count this replaces was deleted from
    ``objects.py`` rather than corrected.
    """
    sweep = _sweep_or_skip()
    _assert_walker_is_live(sweep)

    assert sweep.string_bearing_tags > 0, (
        "no string-bearing tag was seen anywhere in the library, so every rate below "
        "would be vacuous"
    )
    assert sweep.redundancy_agreements[0] == sweep.string_bearing_tags, (
        f"the tag's declared size and the value's own length prefix agree on only "
        f"{sweep.redundancy_agreements[0]} of {sweep.string_bearing_tags} string-bearing "
        "tags at the SHIPPED alignment. The oracle the value grammar rests on does not "
        "hold, so the collapse asserted below would be the collapse of nothing"
    )
    for delta in _VALUE_ROTATIONS:
        if delta == 0:
            continue
        agreed = sweep.redundancy_agreements[delta]
        assert agreed * _COLLAPSE_FACTOR < sweep.string_bearing_tags, (
            f"read at a value-start offset of {delta:+d}, the redundancy oracle still "
            f"agrees on {agreed} of {sweep.string_bearing_tags} tags. An oracle that "
            "survives being moved is not evidence about alignment, and the value "
            "grammar would then rest on nothing"
        )


def test_no_value_of_an_unmeasured_type_is_ever_decoded() -> None:
    """Non-negotiable 7 at the value seam - flagged and skipped, never guessed.

    THE ORACLE IS PROVENANCE, NOT SHAPE, and the difference is the whole test.
    The first revision asserted that no decoded value had a Python type outside
    bool, int, float, str and a 2-tuple of str - which is very nearly the whole
    space of things any decoder can return, so it was true by construction. An
    adversary measured it: wrapping ``objects._decode_value`` to return
    ``body[at:at + size].decode("latin-1")`` for StructProperty, an unmeasured
    type, fabricated tens of thousands of values out of unread bytes and left
    every assertion in this file green.

    What can fail is a join on the tag's TYPE WORD, which the shipped decoder's
    name-keyed mapping does not carry and :func:`_walk_tags` now supplies. The
    shape check is kept below it, weak and labelled, because it still catches a
    branch returning something structurally impossible.
    """
    sweep = _decode_sweep_or_skip()

    assert sweep.unmeasured_tags > 0, (
        "no tag of an unmeasured type was seen anywhere in the library, so the "
        "skip-rather-than-guess assertion below would be vacuous"
    )
    assert sweep.decoded_values > 0, (
        "the decoder returned no value at all on a host that has a library, so every "
        "zero below is the zero of a decoder that did nothing"
    )
    assert sweep.decoded_names_this_walk_never_saw == 0, (
        f"{sweep.decoded_names_this_walk_never_saw} decoded properties have no tag in "
        "this module's own walk of the same payload. The two walkers disagree, so the "
        "provenance assertion below is judging against a map that does not describe "
        "what the shipped decoder read"
    )
    assert sweep.decoded_values_from_an_unmeasured_type == 0, (
        f"{sweep.decoded_values_from_an_unmeasured_type} decoded values came from a tag "
        "whose type word is outside the measured set, which is a value read out of "
        "bytes this project has never measured (non-negotiable 7). The values and the "
        "names are deliberately not rendered - they are world content"
    )
    assert sweep.values_off_type == 0, (
        f"{sweep.values_off_type} decoded values have a shape no measured type can "
        "produce, which means a branch is returning something it did not measure. The "
        "values are deliberately not rendered - they are world content"
    )


def test_every_measured_type_the_library_exercises_yields_at_least_one_value() -> None:
    """Coverage stated PER TYPE, because the building equality is not per type.

    :func:`test_a_real_building_yields_at_least_one_decoded_property_value`
    counts a building as covered the moment ONE of its properties decodes, so a
    decoder honouring three of its eleven declared types satisfies it. Measured
    on the merged tree: deleting the decode of BoolProperty, EnumProperty,
    Int8Property, IntProperty, NameProperty, SoftObjectProperty, StrProperty
    and UInt32Property - all eight at once - suppressed thousands of real
    decodes and left the whole suite green. Only ByteProperty, FloatProperty
    and ObjectProperty were genuinely covered, and only because they happen to
    be near universal in this operator's world. That is coverage by accident of
    the corpus.

    THE UNEXERCISED SET IS ASSERTED EMPTY RATHER THAN IGNORED. A type the
    library does not carry is not covered by anything here, and a silent gap is
    the thing this assertion exists to refuse - so it fails loudly and says
    which type, rather than quietly proving less than it appears to.

    Every word rendered below came out of :data:`_MEASURED_VALUE_TYPES`, a
    literal in this file, never out of a save.
    """
    sweep = _decode_sweep_or_skip()

    assert sweep.measured_types_present, (
        "the library carries no measured property type at top level, so every "
        "per-type claim below would be vacuous"
    )
    uncovered = sorted(sweep.measured_types_present - sweep.measured_types_yielding)
    assert not uncovered, (
        f"{uncovered} appear as top-level tags in this library and the shipped decoder "
        "returned no value for any of them. A type in MEASURED_VALUE_TYPES that never "
        "decodes is a type the module is wrong about having measured"
    )
    unexercised = sorted(_MEASURED_VALUE_TYPES - sweep.measured_types_present)
    assert not unexercised, (
        f"{unexercised} are declared measured but no save on this machine carries one "
        "at top level, so nothing here covers them. Record that gap deliberately - do "
        "not let it pass as coverage"
    )


def test_the_int32_byte_order_is_discriminated_by_the_stored_high_byte() -> None:
    """THE BYTE ORDER, SCORED AGAINST THE GAME'S DATA RATHER THAN OUR WRITER.

    SCORED IS NOT SETTLED, AND THE DIFFERENCE IS MEASURED RATHER THAN CONCEDED.
    The two assertions below rule the whole-word REVERSAL out on the game's own
    bytes. THEY DO NOT NARROW THE ORDER TO ONE ARRANGEMENT, and that is still
    true of this test after the candidate set narrowed - what closed it was a
    third oracle in another module, not these assertions. What the value oracles
    leave standing between them is recorded as data in
    ``objects.BYTE_ORDER_SURVIVING_CANDIDATES`` and derived from the library by
    ``tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate``,
    so the residual is a constant the suite checks rather than a sentence here
    that nobody grades. ``objects.VALUE_BYTE_ORDER_STATUS`` carries the matching
    per-type status word, and it records what THIS type's own population settles
    rather than what the joint intersection reaches.

    WHICH CANDIDATES SURVIVE IS DELIBERATELY NOT EXPLAINED HERE. The members are
    derived by the test named above and checked against the shipped constant. An
    earlier draft of this paragraph described the mechanism - that both oracles
    turn on the EXTREME stored byte positions - and that description was measured
    FALSE: the two oracles are ONE-ENDED in opposite directions, and each
    survives rearrangements that move the end the other one holds. What they left
    standing between them was a pair differing only in the two MIDDLE stored
    bytes, because the two constraints are INTERSECTED and neither is two-ended.
    The corrected mechanism belongs beside the derivation that measures it rather
    than in an ungraded copy here.

    THIS ORACLE IS ALSO NOT ANCHORED TO THE BYTES IT GRADES. Displacing the
    int32 value start so the decode reads a neighbouring field rather than the
    value leaves both assertions below GREEN, so a green result here is a claim
    about a POPULATION's byte-order signature and not evidence that the bytes
    scored were the value's own. The anchoring this lacks is carried by
    ``tests/save/test_value_anchoring.py::test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent``,
    whose own control is
    ``tests/save/test_value_anchoring.py::test_the_extent_anchor_control_catches_a_displaced_fixed_width_read``.

    CS-421'S DEMONSTRATION SAID FLIPPING ``IntProperty`` TO ``">i"`` REDDENS
    ONLY SYNTHETIC-FIXTURE TESTS, AND THAT SENTENCE WAS MEASURED FALSE
    2026-08-23. It stood in THIS docstring while this very test is one of the
    things the flip reddens, which is the ADR 0008 shape: a reader checking the
    claim by running the named mutant finds the thing it denies.

    RE-MEASURED, not inherited. The mutant was asserted live in the LOADED
    module rather than merely written to the file, the floor was a full-suite
    green run at the same tree, and the same named tests were re-run 13 of 13
    after the revert - so the reds are the mutant's and not a library that moved
    under the run. The flip fails 13 tests in ``tests/save`` and FIVE are
    LIBRARY-BACKED rather than synthetic: this one, plus
    ``test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate``,
    ``test_the_int32_oracle_still_separates_a_type_it_can_separate``,
    ``test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches``
    and
    ``test_the_mantissa_coarseness_oracle_separates_the_middle_swap_from_the_identity``.

    THE SENTENCE WAS TRUE WHEN IT WAS WRITTEN. What made it false is the
    magnitude oracle below and CS-469's third oracle, both of which landed under
    it while nobody re-ran the demonstration. Do not restore it, and do not cite
    the flip as an open gap without re-running it first.

    THE ORACLE'S PREMISE IS A FACT ABOUT THE GAME, WHICH IS WHY IT ESCAPES THAT
    CIRCULARITY. A save's int32 fields are counts, indices and enum ordinals,
    so their magnitudes are small, so the most significant of the four STORED
    bytes is zero far more often than not. Under the opposite reading that same
    position holds what was the least significant byte, where zero is uncommon.
    Nothing in the argument refers to how this project writes a fixture.

    THE PIVOT IS ONE HALF OF THE POPULATION AND NO MEASURED CONSTANT APPEARS
    HERE. A threshold sitting at an observed value is what makes
    ``_JOIN_WORD_FLOOR`` red on a correct grammar once the corpus moves, which
    is CS-432. Majority against minority is structural, and the two counters
    exchange values under the mutant rather than drifting, so the margin does
    not have to be guessed at.

    STATED LIMIT, AND IT IS MEASURED RATHER THAN REASONED. This discriminates
    BYTE ORDER and not fabrication: replacing the whole fixed-width decode with
    a plausible small constant leaves both oracles here GREEN, because such a
    constant carries a zero high byte exactly as a real small value does. CS-455
    owns that gap and its ROADMAP entry carries the measured acceptance. The
    accepting set is deliberately NOT restated here - a band written into a
    docstring is the same rot one generation on.

    THE FIRST DRAFT OF THIS PARAGRAPH NAMED THE ROTATION CONTROL AS THE TEST
    THAT COVERS THAT GAP, AND THAT WAS FALSE.
    :func:`test_the_decode_collapses_when_the_payload_start_is_rotated`
    perturbs the WALK, and a fabricated value does not move the walk, so it
    could not have covered it. CS-455 records what was measured. Recorded here
    as an open residual rather than attributed to a test that does not do it.

    It is library-backed and skips with no game installed, which is the CI gap
    CS-426 owns. A synthetic fixture cannot close it: one packed from the same
    belief the reader unpacks with is the circularity above, in a new costume.
    """
    sweep = _decode_sweep_or_skip()

    assert sweep.int32_values > 0, (
        "no int32 value decoded anywhere in this library, so both comparisons "
        "below would be claims about an empty population"
    )
    assert sweep.int32_high_byte_zero_as_read * 2 > sweep.int32_values, (
        f"the stored high byte is zero on only {sweep.int32_high_byte_zero_as_read} "
        f"of {sweep.int32_values} int32 values as read. Small magnitudes stored in "
        "the declared order put a zero there on most of them, so a minority means "
        "the declared order is not the stored one"
    )
    assert sweep.int32_high_byte_zero_if_swapped * 2 < sweep.int32_values, (
        f"reading the same bytes the other way puts a zero in the high position on "
        f"{sweep.int32_high_byte_zero_if_swapped} of {sweep.int32_values}, which is a "
        "majority. Both readings cannot carry the small-magnitude signature, so this "
        "one has stopped discriminating and the test above proves less than it says"
    )


def test_the_float32_byte_order_is_discriminated_by_plausible_magnitude() -> None:
    """The same question for float32, measured separately rather than inferred.

    IT WOULD BE CHEAPER TO ARGUE THAT ONE SERIALIZER WRITES ONE BYTE ORDER, so
    settling int32 settles this too. That inference is probably true and it is
    still an inference, and session 11 recorded four separate slices whose only
    defect was measuring one thing and stating a wider one. So float32 carries
    its own oracle over its own population.

    THE DISCRIMINATOR IS MAGNITUDE PLAUSIBILITY, NOT FINITENESS. Finiteness
    looks like the natural choice and was measured useless before this was
    written: it holds on very nearly the whole population under BOTH readings,
    because a swapped float32 is still a finite number far more often than not -
    just an absurd one. The two rates are deliberately not written here. The
    operator plays this game, so a percentage in a docstring is a figure the
    next autosave can falsify for no defect at all, which is the reason the
    counts this replaces were kept out of the assertions below as well.

    WHAT THIS ORACLE LEAVES OPEN IS RECORDED RATHER THAN DESCRIBED. It does not
    narrow the byte order to one arrangement on its own, and neither does the
    int32 oracle; what survives every value oracle is held in
    ``objects.BYTE_ORDER_SURVIVING_CANDIDATES`` and derived from the library by
    ``tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate``.
    No account of WHICH rearrangements either oracle admits is written here -
    the last such account in this file was measured false, and the derivation
    is the thing that can be graded.

    THE BAND BELOW IS WHY A THIRD ORACLE WAS NEEDED, and naming the limit here
    is more use than defending it. The band is a DOMAIN bound and it is not
    narrowable to settle a byte order. THE EVIDENCE FOR THAT IS A DERIVATION AND
    NOT A COUNT ON THIS PAGE:
    ``tests/save/test_value_anchoring.py::test_the_mantissa_coarseness_oracle_separates_the_middle_swap_from_the_identity``
    asserts that the ordering swapping the two MIDDLE stored bytes survives this
    oracle, so this oracle demonstrably does not rule it out.

    DO NOT REACH FOR THE SWAPPED COUNT BELOW TO SUPPORT THAT. It scores the
    whole-word REVERSAL - ``pack`` little, ``unpack`` big - which is a different
    rearrangement from the middle swap, and a revision of this paragraph cited
    it for exactly that purpose and was measured wrong. Do not narrow
    ``_FLOAT_PLAUSIBLE_LOW`` or ``_FLOAT_PLAUSIBLE_HIGH`` to chase a
    discrimination they cannot make.

    The band below is a DOMAIN bound on what a coordinate, a clock speed or a
    power figure can be, not a value fitted to this corpus.

    Exact zero is excluded from both counts rather than assigned to either: its
    bit pattern is symmetric, so it reads as zero under both orders and can
    discriminate nothing. Counting it as plausible would inflate both sides by
    the same amount and narrow the very margin this test rests on.
    """
    sweep = _decode_sweep_or_skip()

    assert sweep.float32_values > 0, (
        "no float32 value decoded anywhere in this library, so both comparisons "
        "below would be claims about an empty population"
    )
    assert sweep.float32_plausible_as_read * 2 > sweep.float32_values, (
        f"only {sweep.float32_plausible_as_read} of {sweep.float32_values} float32 "
        "values land in the plausible band as read. A world's floats are mostly "
        "ordinary magnitudes, so a minority means the declared order is not the "
        "stored one"
    )
    assert sweep.float32_plausible_if_swapped * 2 < sweep.float32_values, (
        f"reading the same bytes the other way is plausible on "
        f"{sweep.float32_plausible_if_swapped} of {sweep.float32_values}, a majority. "
        "Both readings cannot be the ordinary-magnitude one, so this test has stopped "
        "discriminating between them"
    )


def test_no_fixed_width_decode_depends_on_the_byte_order_of_its_format_code() -> None:
    """The shipped dispatch must key on the TYPE, not on a spelling.

    FOUND BY THE BYTE-ORDER ORACLES ABOVE, which could not be proven against a
    ``">f"`` mutant because the shipped decoder raised before either assertion
    ran. ``_decode_fixed_width`` chose its return branch by comparing the format
    code to the literal ``"<f"``, so a float read in the other order fell into
    the integer branch, where ``int`` of a NaN raises ``ValueError``.

    NOTHING WAS BROKEN ON THE SHIPPED TABLE and this is not a bug report about
    today's behaviour - it is an unstated invariant. The module required its
    float entry to be spelled with one particular byte-order prefix and said so
    nowhere, which is the CS-422 shape: a rule the file relies on and does not
    state. The remedy is to ask the question the branch actually means.

    THE POPULATION IS DERIVED FROM THE SHIPPED TABLE rather than listed here, so
    an entry added later is covered without anyone remembering to add it. The
    byte pattern is hand-authored and this test reads no save, so it runs on a
    machine with no game installed - which the oracles above do not.
    """
    # A pattern that is an ordinary small integer read one way and a NaN read
    # the other, so the float row exercises the branch that used to raise.
    pattern = b"\x7f\xc0\x00\x00"

    assert objects._FIXED_WIDTH_VALUES, "no fixed-width entry to check"  # noqa: SLF001
    for word, (width, code) in objects._FIXED_WIDTH_VALUES.items():  # noqa: SLF001
        body = pattern[:width]
        for order in ("<", ">"):
            spec = (width, order + code[1:])
            (expected,) = struct.unpack(spec[1], body)
            decoded = objects._decode_fixed_width(body, 0, width, spec)  # noqa: SLF001
            assert type(decoded) is type(expected), (
                f"{word} decoded to {type(decoded).__name__} under byte order "
                f"{order!r} while struct yields {type(expected).__name__}. The "
                "branch is keyed on the format code's spelling rather than on "
                "the value it produced"
            )


def test_every_measured_value_type_names_the_oracle_that_backs_it() -> None:
    """CS-421 clause 1, and the scope is DERIVED rather than listed.

    The evidence table's key set is compared against
    :data:`objects.MEASURED_VALUE_TYPES` computed in the same run, so a type
    added to the measured set without recording what backs it reddens here
    instead of inheriting the last entry's credibility by silence. Listing the
    expected keys in this file would make the check an allowlist with the sign
    flipped, which is the shape CS-420 clause 2 exists to refuse.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    recorded = frozenset(objects.EVIDENCE_FOR_VALUE_TYPE)
    missing = sorted(objects.MEASURED_VALUE_TYPES - recorded)
    assert not missing, (
        f"{missing} are decoded but nothing records what backs the decode. A type "
        "whose evidence is unstated reads as evidenced"
    )
    extra = sorted(recorded - objects.MEASURED_VALUE_TYPES)
    assert not extra, (
        f"{extra} carry an evidence entry and are not decoded at all, so the table "
        "describes a decode that does not happen"
    )

    known = {
        objects.EVIDENCE_DECLARED_WIDTH,
        objects.EVIDENCE_REDUNDANCY,
        objects.EVIDENCE_CROSS_SECTION,
        objects.EVIDENCE_MAGNITUDE,
    }
    for word, oracles in objects.EVIDENCE_FOR_VALUE_TYPE.items():
        assert oracles, f"{word} names an empty evidence set, which claims nothing"
        unknown = sorted(oracles - known)
        assert not unknown, f"{word} cites {unknown}, which is no declared evidence class"


def test_the_magnitude_oracle_covers_exactly_the_types_marked_with_it() -> None:
    """CS-421 clause 2's live half - the table is TIED to the running controls.

    The rest of the evidence table records a class and is checked for
    completeness rather than for truth. This entry is different: the two
    byte-order oracles in this module score exactly two type words, and if the
    table claims a third the claim is unbacked, while if it claims one fewer a
    shipped control has stopped being credited.

    :data:`_MAGNITUDE_SCORED_TYPES` is this module's transcription of what those
    oracles score, kept here for the reason
    :func:`test_the_shipped_measured_set_matches_this_module_transcription`
    gives: a suite that imports the constant it is checking asserts only that
    the module equals itself.
    """
    marked = frozenset(
        word
        for word, oracles in objects.EVIDENCE_FOR_VALUE_TYPE.items()
        if objects.EVIDENCE_MAGNITUDE in oracles
    )
    assert marked == _MAGNITUDE_SCORED_TYPES, (
        f"the table credits {sorted(marked)} with a magnitude oracle while this "
        f"module scores {sorted(_MAGNITUDE_SCORED_TYPES)}. One of the two moved "
        "without the other"
    )

    width_only = frozenset(objects.WIDTH_ONLY_VALUE_TYPES)
    assert not width_only & marked, (
        f"{sorted(width_only & marked)} are recorded as backed by a declared width "
        "alone and as carrying a magnitude oracle, which cannot both be true"
    )
    assert width_only, (
        "no type is recorded as width-only. That would mean every decoded type "
        "gained a second oracle, which is a claim worth making deliberately"
    )


def test_a_cursor_width_is_discriminated_and_never_on_a_majority_of_payloads() -> None:
    """CS-422's 'immediately', replaced by a per-width derivation.

    ``objects._TAG_EXTRA_STRINGS`` claimed that mis-stating any one of its
    widths "desynchronises the walk immediately". That is FALSE for every one of
    them, not merely for the two CS-422 named, and this test is what says so in
    a form that cannot rot: the whole relation is computed from the shipped
    table in the same run.

    TWO ASSERTIONS, AND THE SECOND IS THE ONE THAT REFUTES THE ADVERB. Each
    width, mis-stated, must cost at least one payload - otherwise nothing in the
    suite could tell that width from a wrong one. And each must leave a MAJORITY
    of payloads still reaching their terminator, which is the measured shape and
    the opposite of "immediately".

    THE SECOND ASSERTION PINS A WEAKNESS, DELIBERATELY. If a later change makes
    a mis-stated width break most payloads, this goes red on an improvement -
    and the correct response is to update the claim in ``objects.py``, which is
    the whole point. A claim nobody can falsify is what four rounds of hand
    repair produced.

    `GUID_BYTES` is graded here rather than with the value widths because it
    MOVES THE CURSOR - it is stepped over inside a tag - so a wrong value
    desynchronises the walk exactly as a tag-extra count does.
    """
    census = _width_census_or_skip()

    assert census.payloads > 0, "no payload enumerated, so every claim below is vacuous"
    assert census.reach_shipped == census.payloads, (
        f"the shipped widths take only {census.reach_shipped} of {census.payloads} "
        "payloads to a terminator, so the baseline this census compares against is "
        "already broken"
    )
    scope = frozenset(objects._TAG_EXTRA_STRINGS) | {_GUID_WIDTH_NAME}  # noqa: SLF001
    assert frozenset(census.reach_by_cursor_width) == scope, (
        "the census scope and the shipped cursor widths disagree, so a width "
        "exists that nothing here grades"
    )

    for word, reached in sorted(census.reach_by_cursor_width.items()):
        assert reached < census.reach_shipped, (
            f"mis-stating {word} costs no payload at all, so no reach oracle can "
            "tell the shipped width from a wrong one"
        )
        assert reached * 2 > census.reach_shipped, (
            f"mis-stating {word} leaves only {reached} of {census.reach_shipped} "
            "payloads reaching, which is a minority. The module records that a "
            "mis-stated width is discriminated on a minority of payloads and that "
            "is no longer true - fix the claim there, not this assertion"
        )


def test_an_extent_width_cannot_desynchronise_and_is_caught_by_disagreement() -> None:
    """The OTHER half of CS-422's rule, and why one oracle could not serve both.

    A width that only bounds a VALUE cannot move the walk: the cursor advances
    by the tag's own declared size, so a wrong value width drops the value and
    is reported as a disagreement instead. Grading these by terminator reach -
    the oracle the tag-extra widths are graded by - reports them as undetectable
    when they are in fact detected, which is how one file came to hold two
    evidence standards with no rule between them.

    THE BASELINE IS ZERO AND THAT IS WHAT MAKES THE COUNTS READABLE. The shipped
    configuration disagrees with itself on no value anywhere in the library, so
    every count here is attributable to the mutation rather than to a background
    rate.

    Note what this does NOT claim: that the width is the RIGHT one. A
    disagreement count proves the declared size is load-bearing, not that the
    bytes are read the right way round - see the two byte-order oracles above,
    which are a different question over the same widths.
    """
    census = _width_census_or_skip()

    assert census.payloads > 0, "no payload enumerated, so every claim below is vacuous"
    assert census.disagreements_shipped == 0, (
        f"the shipped widths already disagree on {census.disagreements_shipped} values, "
        "so a mutation's count cannot be attributed to the mutation"
    )
    scope = frozenset(objects._FIXED_WIDTH_VALUES) | {_SOFT_TAIL_NAME}  # noqa: SLF001
    assert frozenset(census.disagreements_by_extent_width) == scope, (
        "the census scope and the shipped extent widths disagree, so a width "
        "exists that nothing here grades"
    )

    for word, disagreed in sorted(census.disagreements_by_extent_width.items()):
        assert disagreed > 0, (
            f"mis-stating {word} produces no disagreement, so nothing distinguishes "
            "the shipped width from a wrong one"
        )
        reached = census.reach_by_extent_width[word]
        assert reached == census.payloads, (
            f"mis-stating {word} cost {census.payloads - reached} payloads their "
            "terminator, so it moves the cursor after all and belongs with the "
            "cursor widths rather than here"
        )


def test_the_width_rule_partitions_every_shipped_width_and_declines_no_decoded_one() -> None:
    """CS-422's rule over the shipped tables, and the partition halves are blind.

    THE NAME OF THIS TEST OVERSTATES WHAT THE PARTITION HALVES GRADE, and the
    docstring that stood here overstated it the same way. ``ungoverned`` and
    ``phantom`` difference ``CURSOR_WIDTHS | EXTENT_WIDTHS`` against a
    ``shipped`` set built below, and both sides are assembled from the SAME two
    module tables - ``_TAG_EXTRA_STRINGS`` and ``_FIXED_WIDTH_VALUES`` - plus
    two literal names. The tables cancel, so adding a width to either one moves
    both sides together. Measured rather than reasoned: a word added to either
    table leaves this test GREEN. The case the name advertises - a shipped width
    sitting outside the rule - is the case these two assertions do not grade.

    WHAT THEY DO STILL CATCH, recorded because deleting them would drop it and
    because "structurally empty" overstates it in the other direction. The two
    literal names are transcribed HERE as :data:`_GUID_WIDTH_NAME` and
    :data:`_SOFT_TAIL_NAME` and spelled independently in ``objects.py``, so that
    pair does NOT cancel. Renaming one on the module side alone turns
    ``ungoverned`` red. That is a transcription check over two names, and it is
    the whole of what the partition half is worth.

    CS-458 OWNS THE REPAIR, and its acceptance is the right one: derive the
    governed set and the shipped set from INDEPENDENT sources, proven by a
    mutant that introduces a cursor-advancing width without registering it.
    Until that lands, the executable grading of the width rule lives in
    ``tests/save/test_width_rule.py``.

    THE OTHER TWO ASSERTIONS ARE NOT PART OF THAT COMPLAINT, and they are why
    this test stays. Disjointness compares two separately built tables, so a
    word reaching both is a real finding: a width graded by both oracles would
    let a failure under one be excused by a pass under the other. The
    declined-and-decoded intersection reads ``DECLINED_VALUE_READINGS`` against
    ``MEASURED_VALUE_TYPES``, two independently maintained tables, and it is the
    invariant that caught the first draft of this work - the declined table was
    keyed by bare type word while `ArrayProperty` legitimately ships a TAG-EXTRA
    width, so the name read as though the whole word were declined. The closing
    ``.strip()`` truthiness check is close to worthless and is kept only because
    an empty rule string is cheap to exclude.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    cursor = objects.CURSOR_WIDTHS
    extent = objects.EXTENT_WIDTHS

    overlap = sorted(cursor & extent)
    assert not overlap, (
        f"{overlap} are graded as both a cursor width and an extent width, so a "
        "failure under one oracle could be excused by a pass under the other"
    )

    shipped = (
        frozenset(objects._TAG_EXTRA_STRINGS)  # noqa: SLF001
        | frozenset(objects._FIXED_WIDTH_VALUES)  # noqa: SLF001
        | {_GUID_WIDTH_NAME, _SOFT_TAIL_NAME}
    )
    ungoverned = sorted(shipped - (cursor | extent))
    assert not ungoverned, (
        f"{ungoverned} are shipped widths that the rule's two classes do not "
        "cover, so nothing states what evidence let them ship"
    )
    phantom = sorted((cursor | extent) - shipped)
    assert not phantom, (
        f"{phantom} are classified and are not shipped widths, so the rule "
        "describes an entry that does not exist"
    )

    both = sorted(frozenset(objects.DECLINED_VALUE_READINGS) & objects.MEASURED_VALUE_TYPES)
    assert not both, (
        f"{both} are recorded as declined value readings and are decoded anyway, "
        "so the module contradicts itself about its own evidence"
    )
    assert objects.WIDTH_SHIPPING_RULE.strip(), "the rule is empty, so nothing governs"


def test_the_shipped_measured_set_matches_this_module_transcription() -> None:
    """The two transcriptions of the measured set must agree.

    This suite states the measured type set independently rather than importing
    it, for the reason that module records above its ``Measured layout
    constants`` block: a suite that imports the constant it is checking asserts
    only that the module equals itself. The cost of transcribing is that the
    two can drift, and this is what catches the drift.

    It needs no save library - it is a claim about the repo, not about a world.
    """
    assert objects.MEASURED_VALUE_TYPES == _MEASURED_VALUE_TYPES


def test_every_unmeasured_type_the_library_holds_is_recorded_as_data() -> None:
    """CS-412's shape, applied to the payload interior.

    A partial recorded as an adjective is not resumable. So every type word the
    decoder SKIPS must appear by name in
    :data:`objects.UNMEASURED_PAYLOAD_REGIONS`, which is the structure a later
    slice executes against. The trailing run is in that table too, and is the
    reason the PROPERTY walk is terminator-exact rather than boundary-exact.

    THE ASSERTION RUNS AGAINST THE LIBRARY, not against a hardcoded list, so a
    game update introducing a new property type turns this red instead of
    letting it drift out of date silently. The word itself is never rendered -
    the judgement happens inside the sweep, exactly as it does for the
    malformed-word count, because the case where a word is NOT vocabulary is
    the desynchronised walk.
    """
    sweep = _sweep_or_skip()
    _assert_walker_is_live(sweep)

    assert sweep.unrecorded_type_words == 0, (
        f"{sweep.unrecorded_type_words} property type words are neither decoded nor "
        "recorded as an unmeasured region, so a later slice inherits a sentence instead "
        "of evidence. Add each to objects.UNMEASURED_PAYLOAD_REGIONS with what is pinned "
        "and what is not claimed, rather than widening the measured set to silence this"
    )
    assert "trailing_run" in objects.UNMEASURED_PAYLOAD_REGIONS, (
        "the run after the property terminator is the region that keeps this walk "
        "terminator-exact rather than boundary-exact, and it must stay recorded"
    )


def test_every_type_word_is_format_vocabulary_and_never_world_content() -> None:
    """A structural invariant on the vocabulary, not a hardcoded list of it.

    A list would need editing every time the game adds a property type. The
    SHAPE does not: an Unreal property type word is ASCII and ends in
    ``Property``, and anything else coming out of that field means the walk is
    reading something that is not a tag.

    THE COUNT IS ASSERTED, NEVER THE WORD. The judgement happens inside the
    sweep - see :class:`_TagSweep` - because the one case where a word is NOT
    format vocabulary is the desynchronised walk, which is precisely the case
    this assertion fires in. Rendering the offending word to explain the
    failure would print a fragment of a real save into the log.

    The ``> 0`` here is the live control: without it, a walk that reads nothing
    at all yields no malformed words and passes.
    """
    sweep = _sweep_or_skip()

    assert sweep.distinct_type_words > 0, (
        "the walk produced no property type word at all on a host that has a save "
        "library, so the malformed-count below would be vacuous"
    )
    assert sweep.malformed_type_words == 0, (
        f"{sweep.malformed_type_words} of {sweep.distinct_type_words} distinct type words "
        "are not shaped like an Unreal property type word, which means the tag walk is "
        "reading something that is not a tag. The words themselves are deliberately not "
        "rendered here - a desynchronised walk yields world content, not vocabulary"
    )


# ---------------------------------------------------------------------------
# THE SYNTHETIC PAYLOAD - the half of this module that needs no save library
#
# WHY IT EXISTS. Every assertion above this line reads the operator's own save
# library, so on any machine without one - CI, a fresh clone, a reviewer's
# laptop - they all skip and the decoder at ``objects.py`` executes ZERO lines.
# CLAUDE.md section 7 settles that the rule suite must run on a machine with no
# game installed, and that fixtures are small synthetic registries hand
# authored in the repo. These bytes are hand authored here.
#
# WHAT IT PROVES AND WHAT IT CANNOT. It proves the shipped decoder is SELF
# CONSISTENT: given bytes laid out the way this project SAYS a payload is laid
# out, it returns the values that were encoded, skips the types it says it does
# not measure, and stops at the terminator. IT IS NOT EVIDENCE THAT THE GRAMMAR
# MATCHES THE GAME - a fixture built from the same belief as the reader agrees
# with the reader by construction. The real-library sweeps above are the only
# evidence about the format, and the rotation control inside them is the only
# evidence about the alignment. Neither claim may ever be transferred to this
# fixture.
#
# NO PRIVACY COST. Every byte below was typed here. Nothing was sliced out of a
# save, so these names and values may be rendered freely in a failure message,
# which is exactly why the assertions here can be specific where the sweeps
# above can only be counts.
# ---------------------------------------------------------------------------

#: Bytes ahead of the payload inside the synthetic body, so the fixture
#: exercises a non-zero ``body_offset`` rather than the degenerate 0.
_BODY_PREFIX: Final = bytes(range(24))

#: Bytes past the payload, so an over-read is detectable rather than benign.
_BODY_SUFFIX: Final = bytes(range(200, 208))

#: Stands in for the variable run that follows the terminator on every real
#: payload. Its presence is what makes the fixture prove TERMINATOR exactness
#: rather than accidentally proving boundary exactness.
_TRAILING_RUN: Final = b"\xde\xad\xbe\xef\x01\x02\x03\x04"

_SYNTHETIC_CLASS_PATH: Final = "/Synthetic/Build_SyntheticThing.Build_SyntheticThing_C"
_SYNTHETIC_SCHEMA: Final = "Build_SyntheticThing_C"
_SYNTHETIC_LEVEL: Final = "Persistent_Level"
_SYNTHETIC_ROOT: Final = "Persistent_Level:PersistentLevel"
_SYNTHETIC_INSTANCE: Final = "Persistent_Level:PersistentLevel.Build_SyntheticThing_C_0"
_SYNTHETIC_COMPONENT: Final = "Persistent_Level:PersistentLevel.SyntheticComponent_0"
_SYNTHETIC_TARGET: Final = "Persistent_Level:PersistentLevel.SyntheticTarget_0"
_SYNTHETIC_ASSET: Final = "/Synthetic/Assets/SyntheticAsset.SyntheticAsset_C"

_SYNTHETIC_INT: Final = -1234567
_SYNTHETIC_UINT32: Final = 4000000000
_SYNTHETIC_FLOAT: Final = 1.5
_SYNTHETIC_INT8: Final = -42
_SYNTHETIC_BYTE: Final = 200
_SYNTHETIC_STR: Final = "SyntheticStrValue"
_SYNTHETIC_NAME: Final = "SyntheticNameValue"
_SYNTHETIC_ENUM_WORD: Final = "ESyntheticEnum"
_SYNTHETIC_ENUM_MEMBER: Final = "ESyntheticEnum::Second"
_SYNTHETIC_BYTE_ENUM_WORD: Final = "ESyntheticByteEnum"
_SYNTHETIC_BYTE_ENUM_MEMBER: Final = "ESyntheticByteEnum::Third"
_SYNTHETIC_STRUCT_WORD: Final = "SyntheticStructPayload"
_SYNTHETIC_ARRAY_INNER: Final = "IntProperty"

#: The three containers the fixture carries - CS-830. EACH HOLDS MORE THAN ONE
#: ELEMENT, deliberately: a container of one element is bounded by dividing its
#: region by one, which any width satisfies, so a single-element fixture would
#: grade the framing far more weakly than it appears to.
#:
#: THE MAP'S TWO HALVES ARE DIFFERENT WIDTHS AND DIFFERENT SHAPES - a
#: fixed-width key beside a length-prefixed value - so a decoder that read one
#: half twice, or that swapped the key word for the value word, cannot close the
#: region by accident.
#: How wide an int32 element is. TRANSCRIBED rather than imported from
#: ``objects``, on the same terms as the measured set above: a suite that
#: imports the constant it checks asserts only that the module equals itself.
_INT32_BYTES: Final = 4

_SYNTHETIC_ARRAY: Final = (7, 9, 11)
_SYNTHETIC_SET_INNER: Final = "IntProperty"
_SYNTHETIC_SET: Final = (13, 17)
_SYNTHETIC_MAP_KEY: Final = "IntProperty"
_SYNTHETIC_MAP_VALUE: Final = "StrProperty"
_SYNTHETIC_MAP: Final = ((23, "SyntheticMapFirst"), (29, "SyntheticMapSecond"))

#: How many tags of an UNMEASURED type the fixture payload carries. Named so
#: the expected warning count is not a bare literal in three assertions.
_SYNTHETIC_UNMEASURED_TAGS: Final = 1

#: The object-type discriminator for an actor, carried by the record rather
#: than interpreted by :func:`objects.read_properties`.
_OBJECT_TYPE_ACTOR: Final = 1
_OBJECT_TYPE_COMPONENT: Final = 0


def _i32(value: int) -> bytes:
    """Encode one little-endian int32.

    Args:
        value: The number.

    Returns:
        Its four bytes.
    """
    return struct.pack("<i", value)


def _fstring(text: str, *, wide: bool = False) -> bytes:
    """Encode one length-prefixed string, its NUL terminator included.

    THE BODY SIDE HAD NO WIDE SPELLING UNTIL CS-964, and this is the encoder for
    five test modules' planted payloads. Unreal writes a string as UTF-8 with a
    POSITIVE count or UTF-16-LE with a NEGATIVE one, and it picks the second the
    moment a character is not ASCII - which the fields carrying personal data,
    the ones a person types, routinely are. So every body-side privacy arm was
    measured against the encoding its subject is least likely to use.

    ``wide`` is KEYWORD-ONLY so that EVERY existing positional call site keeps
    its current meaning untouched, and so that a wide fixture has to say so at
    the call. The count of those sites is deliberately not spelled here: it was
    filed as 56, re-derived as 47 by a verifier that tokenized rather than
    grepped, and it is decoration either way - the property is that no
    positional caller changed meaning, which does not need a population size to
    state and cannot be kept true by one (CLAUDE.md section 4).

    It mirrors ``synthetic.fstring``'s flag rather than introducing a
    second convention - a parallel builder is a fixture that drifts away from
    the one every other arm uses, which the acceptance clause forbids by name.

    Args:
        text: ASCII text. Non-empty when ``wide`` is set - see below.
        wide: Encode UTF-16-LE with a negative count instead of UTF-8.

    Returns:
        The prefix and the bytes, in the shape ``objects._payload_text`` reads.

    Raises:
        ValueError: ``wide`` was set for empty text. There is no wide encoding
            of the empty string - the count field carries a bare zero and says
            nothing about the encoding - and ``synthetic.fstring`` returns that
            narrow spelling SILENTLY for this case. A silent narrow fallback
            would hand an arm the exact encoding it was written to stop
            measuring, with nothing to say so, so this one refuses instead.
    """
    if wide:
        if not text:
            raise ValueError(
                "there is no wide encoding of the empty string, so a wide fixture cannot "
                "plant one - refusing rather than silently emitting the narrow spelling"
            )
        return _i32(-(len(text) + 1)) + text.encode("utf-16-le") + b"\x00\x00"
    raw = text.encode("ascii") + b"\x00"
    return _i32(len(raw)) + raw


def _spliced_wide(blob: bytes, *texts: str) -> bytes:
    """``blob`` with each text's narrow field replaced by its wide spelling.

    THE ALTERNATIVE WAS A SECOND BUILDER, AND THE ACCEPTANCE CLAUSE FORBIDS ONE
    BY NAME. A parallel wide builder beside the narrow one is a fixture that can
    drift away from the one every other arm uses, and the drift would be
    invisible: both would parse, and only the arms on one of them would be
    measuring the encoding they claim to. Splicing keeps ONE builder and makes
    the change to it assertable - which a parallel builder could not be.

    IT REFUSES TO GUESS. If the narrow field is not present EXACTLY once there
    is no single place to put the wide one, and a splice that took the first of
    several would build a fixture no arm could reason about. That refusal is the
    reason this is a helper rather than two lines inlined per arm.

    Args:
        blob: The fixture bytes, built by the narrow path like every other.
        texts: The field texts to respell, each of which must appear exactly
            once in its narrow encoding. Non-empty - there is no wide encoding
            of the empty string.

    Returns:
        The blob, with those fields wide and everything else untouched.

    Raises:
        AssertionError: A field was absent, or present more than once, or the
            splice did not land.
    """
    for text in texts:
        narrow = _fstring(text)
        wide = _fstring(text, wide=True)
        assert blob.count(narrow) == 1, (
            f"the {text!r} field appears {blob.count(narrow)} times in its narrow spelling, "
            "so this splice would be guessing which one the arm meant"
        )
        blob = blob.replace(narrow, wide, 1)
        assert narrow not in blob, f"the narrow {text!r} field survived the splice"
        assert wide in blob, f"the wide {text!r} field is not in the spliced blob"
    return blob


def _tag_head(name: str, type_word: str, size: int, extra: bytes) -> bytes:
    """Build one property tag up to but not including its value.

    Args:
        name: The property name.
        type_word: The tag's type word.
        size: The value's declared extent.
        extra: The type-specific tag data between the index field and the
            property-guid flag.

    Returns:
        The tag header, ending with a CLEAR property-guid flag.
    """
    return _fstring(name) + _fstring(type_word) + _i32(size) + _i32(0) + extra + b"\x00"


def _scalar_tag(name: str, type_word: str, value: bytes) -> bytes:
    """A tag whose value is a fixed-width number or a single bare string.

    Args:
        name: The property name.
        type_word: The tag's type word.
        value: The encoded value.

    Returns:
        The whole tag.
    """
    return _tag_head(name, type_word, len(value), b"") + value


def _bool_tag(name: str, raised: bool) -> bytes:
    """A BoolProperty, whose value rides in the tag and whose size is 0.

    Args:
        name: The property name.
        raised: The value.

    Returns:
        The whole tag.
    """
    return _tag_head(name, "BoolProperty", 0, bytes([int(raised)]))


def _enum_tag(name: str, type_word: str, enum_word: str, member: str) -> bytes:
    """An EnumProperty, or the enum-named shape of a ByteProperty.

    Args:
        name: The property name.
        type_word: ``EnumProperty`` or ``ByteProperty``.
        enum_word: The enum named in the tag data.
        member: The member name carried as the value.

    Returns:
        The whole tag.
    """
    value = _fstring(member)
    return _tag_head(name, type_word, len(value), _fstring(enum_word)) + value


def _raw_byte_tag(name: str, value: int) -> bytes:
    """The other measured ByteProperty shape - one raw byte, enum word ``None``.

    Args:
        name: The property name.
        value: The byte.

    Returns:
        The whole tag.
    """
    return _tag_head(name, "ByteProperty", 1, _fstring("None")) + bytes([value])


def _reference_tag(name: str, type_word: str, level: str, path: str) -> bytes:
    """An ObjectProperty or SoftObjectProperty - a level reference and a path.

    Args:
        name: The property name.
        type_word: ``ObjectProperty`` or ``SoftObjectProperty``.
        level: The level reference.
        path: The object path.

    Returns:
        The whole tag.
    """
    value = _fstring(level) + _fstring(path)
    if type_word == "SoftObjectProperty":
        value += _i32(0)
    return _tag_head(name, type_word, len(value), b"") + value


def _struct_tag(name: str, struct_word: str, opaque: bytes) -> bytes:
    """An UNMEASURED StructProperty, present so the fixture proves it is skipped.

    Args:
        name: The property name.
        struct_word: The struct's own type word, carried in the tag data.
        opaque: The interior, which this project does not read.

    Returns:
        The whole tag.
    """
    extra = _fstring(struct_word) + bytes(objects.GUID_BYTES)
    return _tag_head(name, "StructProperty", len(opaque), extra) + opaque


def _array_tag(name: str, inner_word: str, value: bytes) -> bytes:
    """An ArrayProperty - an element count and its elements, since CS-830.

    Args:
        name: The property name.
        inner_word: The element type word, carried in the tag data.
        value: The element count and the elements.

    Returns:
        The whole tag.
    """
    return _tag_head(name, "ArrayProperty", len(value), _fstring(inner_word)) + value


def _set_tag(name: str, inner_word: str, value: bytes) -> bytes:
    """A SetProperty - a lead field, an element count and its elements.

    Args:
        name: The property name.
        inner_word: The element type word, carried in the tag data.
        value: The lead field, the element count and the elements.

    Returns:
        The whole tag.
    """
    return _tag_head(name, "SetProperty", len(value), _fstring(inner_word)) + value


def _map_tag(name: str, key_word: str, value_word: str, value: bytes) -> bytes:
    """A MapProperty, whose tag carries TWO element type words rather than one.

    Args:
        name: The property name.
        key_word: The key half's type word.
        value_word: The value half's type word.
        value: The lead field, the entry count and the entries.

    Returns:
        The whole tag.
    """
    extra = _fstring(key_word) + _fstring(value_word)
    return _tag_head(name, "MapProperty", len(value), extra) + value


def _decoded_shape(properties: Mapping[str, object]) -> dict[str, object]:
    """Reduce decoded properties to a form an expectation can be written against.

    A :class:`objects.ContainerValue` carries ABSOLUTE body offsets on every
    element, so comparing one against a hand-written literal would mean
    hand-computing where each element lands in the fixture payload. That is the
    fragile transcription this suite exists to avoid, and getting it wrong would
    show up as a test that has to be edited whenever an unrelated tag ahead of
    it changes length.

    WHAT IS DROPPED IS THE OFFSET AND NOTHING ELSE. Every element's type word,
    its LENGTH and its decoded value survive, so a framing that bounded the
    wrong number of elements, at the wrong widths, or decoded the wrong values
    still reddens. Where each element sits is graded on the real library by
    ``tests/save/test_container_elements.py``, which checks the elements consume
    the declared size exactly - a check an offset-free comparison cannot make
    and this fixture was never making.

    Args:
        properties: What the shipped reader decoded.

    Returns:
        The same mapping with every container reduced to a comparable tuple.
    """
    reduced: dict[str, object] = {}
    for name, value in properties.items():
        if isinstance(value, objects.ContainerValue):
            reduced[name] = (
                value.type_word,
                value.element_words,
                value.element_count,
                value.element_shape,
                value.struct_word,
                tuple((item.type_word, item.length, item.value) for item in value.elements),
            )
        else:
            reduced[name] = value
    return reduced


#: Padding appended past a string value so the tag's DECLARED size exceeds what
#: the string's own length prefix accounts for. That is the shipped-redundancy
#: oracle failing on a MEASURED type, which means the reader is not where it
#: believes it is - a different thing entirely from an unmeasured type.
_DISAGREEMENT_PADDING: Final = 6

#: One report per skip reason - unmeasured type, and measured-but-disagreeing.
_DISTINCT_SKIP_REPORTS: Final = 2


def _disagreeing_string_tag(name: str, text: str) -> bytes:
    """A MEASURED type whose bytes do not account for its declared size.

    The walk still steps over it correctly, because it steps by the DECLARED
    size - which is exactly why this condition is silent unless it is reported.

    Args:
        name: The property name.
        text: The string actually encoded.

    Returns:
        The whole tag.
    """
    value = _fstring(text) + bytes(_DISAGREEMENT_PADDING)
    return _tag_head(name, "StrProperty", len(value), b"") + value


def _actor_head(components: tuple[str, ...]) -> bytes:
    """The parent reference and component list an ACTOR payload opens with.

    Args:
        components: Component object paths, each paired with the level.

    Returns:
        The head, ending where the first tag begins.
    """
    out = _fstring(_SYNTHETIC_LEVEL) + _fstring(_SYNTHETIC_ROOT)
    out += _i32(len(components))
    for path in components:
        out += _fstring(_SYNTHETIC_LEVEL) + _fstring(path)
    return out


#: Every measured type word, encoded once - twice for ByteProperty, which has
#: two measured shapes. The falsy cases are deliberate: a False bool and an
#: empty string are the values a decoder that confuses "absent" with "empty"
#: silently drops, and the expected mapping below asserts they are present.
_MEASURED_TAGS: Final = (
    _scalar_tag("mSyntheticInt", "IntProperty", struct.pack("<i", _SYNTHETIC_INT)),
    _scalar_tag("mSyntheticUInt32", "UInt32Property", struct.pack("<I", _SYNTHETIC_UINT32)),
    _scalar_tag("mSyntheticFloat", "FloatProperty", struct.pack("<f", _SYNTHETIC_FLOAT)),
    _scalar_tag("mSyntheticInt8", "Int8Property", struct.pack("<b", _SYNTHETIC_INT8)),
    _scalar_tag("mSyntheticStr", "StrProperty", _fstring(_SYNTHETIC_STR)),
    _scalar_tag("mSyntheticEmptyStr", "StrProperty", _i32(0)),
    _scalar_tag("mSyntheticName", "NameProperty", _fstring(_SYNTHETIC_NAME)),
    _bool_tag("mSyntheticBool", True),
    _bool_tag("mSyntheticBoolFalse", False),
    _raw_byte_tag("mSyntheticByteRaw", _SYNTHETIC_BYTE),
    _enum_tag(
        "mSyntheticByteNamed",
        "ByteProperty",
        _SYNTHETIC_BYTE_ENUM_WORD,
        _SYNTHETIC_BYTE_ENUM_MEMBER,
    ),
    _enum_tag("mSyntheticEnum", "EnumProperty", _SYNTHETIC_ENUM_WORD, _SYNTHETIC_ENUM_MEMBER),
    _reference_tag("mSyntheticObject", "ObjectProperty", _SYNTHETIC_LEVEL, _SYNTHETIC_TARGET),
    _reference_tag(
        "mSyntheticSoftObject", "SoftObjectProperty", _SYNTHETIC_LEVEL, _SYNTHETIC_ASSET
    ),
    # THE THREE CONTAINERS - CS-830. They are here rather than among the
    # unmeasured tags because their element framing is decoded now, and
    # ``test_the_synthetic_fixture_exercises_every_measured_type_word`` requires
    # one tag of every measured word. THE SET IS DELIBERATELY NOT THE ARRAY WITH
    # A DIFFERENT WORD: it carries a LEAD FIELD ahead of its count, so a fixture
    # that built it like an array would leave a decoder ignoring that field
    # green here and red on the first real save.
    _array_tag(
        "mSyntheticArray",
        _SYNTHETIC_ARRAY_INNER,
        _i32(len(_SYNTHETIC_ARRAY)) + b"".join(_i32(value) for value in _SYNTHETIC_ARRAY),
    ),
    _set_tag(
        "mSyntheticSet",
        _SYNTHETIC_SET_INNER,
        _i32(0) + _i32(len(_SYNTHETIC_SET)) + b"".join(_i32(value) for value in _SYNTHETIC_SET),
    ),
    _map_tag(
        "mSyntheticMap",
        _SYNTHETIC_MAP_KEY,
        _SYNTHETIC_MAP_VALUE,
        _i32(0)
        + _i32(len(_SYNTHETIC_MAP))
        + b"".join(_i32(key) + _fstring(text) for key, text in _SYNTHETIC_MAP),
    ),
)

#: The one UNMEASURED region the fixture carries, so "flagged and skipped" is
#: exercised rather than described. IT WAS TWO UNTIL CS-830 decoded the array's
#: element framing; the struct's interior is what is still opaque, and it is
#: CS-829's.
_UNMEASURED_TAGS: Final = (
    _struct_tag("mSyntheticStruct", _SYNTHETIC_STRUCT_WORD, bytes(range(32))),
)

#: What the shipped decoder must return for the payload above. Written out in
#: full rather than derived from the builders, so an encoder bug and a decoder
#: bug cannot cancel.
_EXPECTED_PROPERTIES: Final[Mapping[str, object]] = MappingProxyType(
    {
        "mSyntheticInt": _SYNTHETIC_INT,
        "mSyntheticUInt32": _SYNTHETIC_UINT32,
        "mSyntheticFloat": _SYNTHETIC_FLOAT,
        "mSyntheticInt8": _SYNTHETIC_INT8,
        "mSyntheticStr": _SYNTHETIC_STR,
        "mSyntheticEmptyStr": "",
        "mSyntheticName": _SYNTHETIC_NAME,
        "mSyntheticBool": True,
        "mSyntheticBoolFalse": False,
        "mSyntheticByteRaw": _SYNTHETIC_BYTE,
        "mSyntheticByteNamed": _SYNTHETIC_BYTE_ENUM_MEMBER,
        "mSyntheticEnum": _SYNTHETIC_ENUM_MEMBER,
        "mSyntheticObject": (_SYNTHETIC_LEVEL, _SYNTHETIC_TARGET),
        "mSyntheticSoftObject": (_SYNTHETIC_LEVEL, _SYNTHETIC_ASSET),
        # THE CONTAINERS, in the offset-free shape :func:`_decoded_shape`
        # produces. Every element's WORD, LENGTH and VALUE is stated; only
        # where it sits in the payload is not - see that function for why.
        "mSyntheticArray": (
            "ArrayProperty",
            (_SYNTHETIC_ARRAY_INNER,),
            len(_SYNTHETIC_ARRAY),
            objects.ELEMENT_SHAPE_SELF_DELIMITING,
            None,
            tuple((_SYNTHETIC_ARRAY_INNER, _INT32_BYTES, value) for value in _SYNTHETIC_ARRAY),
        ),
        "mSyntheticSet": (
            "SetProperty",
            (_SYNTHETIC_SET_INNER,),
            len(_SYNTHETIC_SET),
            objects.ELEMENT_SHAPE_SELF_DELIMITING,
            None,
            tuple((_SYNTHETIC_SET_INNER, _INT32_BYTES, value) for value in _SYNTHETIC_SET),
        ),
        "mSyntheticMap": (
            "MapProperty",
            (_SYNTHETIC_MAP_KEY, _SYNTHETIC_MAP_VALUE),
            len(_SYNTHETIC_MAP),
            objects.ELEMENT_SHAPE_SELF_DELIMITING,
            None,
            tuple(
                half
                for key, text in _SYNTHETIC_MAP
                for half in (
                    (_SYNTHETIC_MAP_KEY, _INT32_BYTES, key),
                    (_SYNTHETIC_MAP_VALUE, len(_fstring(text)), text),
                )
            ),
        ),
    }
)


def _synthetic_payload(*, actor: bool) -> bytes:
    """Assemble one whole payload, terminator and trailing run included.

    Args:
        actor: Whether to open with the ACTOR head. A COMPONENT payload opens
            directly with its tags, and reading one as the other
            desynchronises on the first tag - which is what
            :func:`test_the_synthetic_component_payload_needs_no_actor_head`
            pins.

    Returns:
        The payload bytes.
    """
    head = _actor_head((_SYNTHETIC_COMPONENT,)) if actor else b""
    tags = b"".join((*_MEASURED_TAGS, *_UNMEASURED_TAGS))
    return head + tags + _fstring("None") + _TRAILING_RUN


def _synthetic_record(payload: bytes, *, actor: bool = True, **extra: int) -> objects.ObjectRecord:
    """Build the record that attributes ``payload`` inside the synthetic body.

    Args:
        payload: The payload the body will carry.
        actor: Whether the record is an actor.
        **extra: ``body_offset`` or ``body_length`` overrides, for the
            out-of-range cases.

    Returns:
        The record.
    """
    fields: dict[str, int] = {
        "body_offset": len(_BODY_PREFIX),
        "body_length": len(payload),
        **extra,
    }
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR if actor else objects.KIND_COMPONENT,
        type_path=_SYNTHETIC_CLASS_PATH,
        root_object=_SYNTHETIC_ROOT,
        instance_name=_SYNTHETIC_INSTANCE,
        transform=None,
        parent=None,
        object_type=_OBJECT_TYPE_ACTOR if actor else _OBJECT_TYPE_COMPONENT,
        was_placed_in_level=0,
        body_offset=fields["body_offset"],
        body_length=fields["body_length"],
    )


def _synthetic_body(payload: bytes) -> bytes:
    """Wrap a payload in leading and trailing bytes that are not part of it.

    Args:
        payload: The payload.

    Returns:
        The body.
    """
    return _BODY_PREFIX + payload + _BODY_SUFFIX


def _synthetic_map(*schema_names: str) -> usmap.PropertyMap:
    """Build a property map from usmap's own public types, with no file.

    Args:
        *schema_names: The schema names the map resolves.

    Returns:
        The map.
    """
    container = usmap.UsmapContainer(
        magic=usmap.USMAP_MAGIC,
        version=0,
        compression_method=usmap.COMPRESSION_NONE,
        compressed_size=0,
        decompressed_size=0,
        header_size=0,
    )
    schemas = {
        name: usmap.Schema(name=name, super_name=None, properties=()) for name in schema_names
    }
    return usmap.PropertyMap(
        names=tuple(schema_names),
        enums=MappingProxyType({}),
        schemas=MappingProxyType(schemas),
        warnings=(),
        container=container,
        body_consumed=0,
    )


# ---------------------------------------------------------------------------
# The decoder, exercised end to end with no save library anywhere
# ---------------------------------------------------------------------------


def test_the_synthetic_actor_payload_decodes_to_exactly_the_values_encoded() -> None:
    """Every measured type word, round tripped through the SHIPPED decoder.

    This is the whole of CS-413's decode claim that CI can defend. It is
    self-consistency and nothing more - see the section comment above.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    result = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert _decoded_shape(result.properties) == dict(_EXPECTED_PROPERTIES)
    assert result.resolved
    assert result.schema_name == _SYNTHETIC_SCHEMA


def test_the_synthetic_fixture_exercises_every_measured_type_word() -> None:
    """The fixture's own non-vacuity control - a round trip of three types proves three.

    Written against the module's transcription of the measured set rather than
    against a count, so adding a measured type without extending the fixture is
    red instead of silently uncovered.
    """
    payload = _synthetic_payload(actor=True)
    words = set()
    for tag in _MEASURED_TAGS:
        # The type word is the SECOND length-prefixed string of a tag.
        after_name = _payload_text_or_fail(tag, 0)[1]
        words.add(_payload_text_or_fail(tag, after_name)[0])

    assert words == set(_MEASURED_VALUE_TYPES), (
        "the synthetic fixture does not carry one tag of every measured type; "
        f"missing {sorted(set(_MEASURED_VALUE_TYPES) - words)}, "
        f"unexpected {sorted(words - set(_MEASURED_VALUE_TYPES))}"
    )
    assert len(payload) > len(_TRAILING_RUN), "the fixture payload is empty"


def _payload_text_or_fail(data: bytes, at: int) -> tuple[str, int]:
    """Read one length-prefixed string out of SYNTHETIC bytes, or fail loudly.

    Safe to fail loudly precisely because the bytes are hand authored here -
    the containment the sweeps above need does not apply to a fixture.

    Args:
        data: The synthetic bytes.
        at: Where the length prefix starts.

    Returns:
        The text and the offset after it.
    """
    step = objects._payload_text(data, at, len(data))  # noqa: SLF001
    assert step is not None, f"the synthetic fixture does not read at offset {at}"
    return step


def test_the_synthetic_component_payload_needs_no_actor_head() -> None:
    """The measured asymmetry: a component's payload opens directly with tags."""
    payload = _synthetic_payload(actor=False)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload, actor=False)

    result = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert _decoded_shape(result.properties) == dict(_EXPECTED_PROPERTIES)


def test_reading_a_component_payload_as_an_actor_desynchronises() -> None:
    """The control for the test above - without it, the head could be ignored.

    A reader that skipped the actor head unconditionally, or never, would pass
    one of the two shapes. This asserts the wrong choice FAILS rather than
    quietly returning a subset.
    """
    payload = _synthetic_payload(actor=False)
    body = _synthetic_body(payload)
    mismatched = _synthetic_record(payload, actor=True)

    result = objects.read_properties(body, mismatched, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert result.properties == {}
    assert [warning.code for warning in result.warnings] == [objects.WARN_UNPARSED_PROPERTY_PAYLOAD]


def test_the_synthetic_payload_flags_and_skips_every_unmeasured_type() -> None:
    """Non-negotiable 7 at the value seam, provable with no save library.

    The unmeasured tag is stepped over by its DECLARED size, so its presence
    must cost the walk nothing and must be counted rather than guessed.

    THE ARRAY USED TO BE THE SECOND ONE AND NOW DECODES - CS-830 - so what is
    asserted here narrowed rather than weakened: the struct's interior is what
    is still unmeasured, and it is the one this case pins. The containers'
    element framing is graded in ``tests/save/test_container_elements.py``, and
    the counter below is what stops a decode being credited to both halves.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    result = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert result.unmeasured_value_count == _SYNTHETIC_UNMEASURED_TAGS
    assert "mSyntheticStruct" not in result.properties
    assert [warning.code for warning in result.warnings] == [objects.WARN_UNMEASURED_PROPERTY_TYPE]
    assert result.warnings[0].actual == _SYNTHETIC_UNMEASURED_TAGS


def test_the_synthetic_walk_stops_at_the_terminator_and_not_at_the_boundary() -> None:
    """The fixture models the trailing run, so terminator exactness is testable.

    The payload's declared extent runs past its ``None`` terminator by exactly
    :data:`_TRAILING_RUN`, and the decode must be unaffected by its contents.
    Shortening the extent to end AT the terminator must decode identically -
    which is what proves the trailing run is stepped over rather than read.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    full = _synthetic_record(payload)
    clipped = _synthetic_record(payload, body_length=len(payload) - len(_TRAILING_RUN))

    property_map = _synthetic_map(_SYNTHETIC_SCHEMA)
    with_run = objects.read_properties(body, full, property_map)
    without_run = objects.read_properties(body, clipped, property_map)

    assert dict(with_run.properties) == dict(without_run.properties)
    assert _decoded_shape(with_run.properties) == dict(_EXPECTED_PROPERTIES)


def _disagreement_payload() -> bytes:
    """A payload carrying one of EACH skip reason, plus one value that decodes.

    Returns:
        The payload bytes.
    """
    return (
        _actor_head(())
        + _scalar_tag("mSyntheticInt", "IntProperty", struct.pack("<i", _SYNTHETIC_INT))
        + _struct_tag("mSyntheticStruct", _SYNTHETIC_STRUCT_WORD, bytes(8))
        + _disagreeing_string_tag("mSyntheticTornStr", _SYNTHETIC_STR)
        + _fstring("None")
        + _TRAILING_RUN
    )


def test_a_measured_value_that_disagrees_is_reported_apart_from_unknown_content() -> None:
    """The two reasons a value is skipped mean OPPOSITE things and must differ.

    An unmeasured TYPE is expected and benign - it is what non-negotiable 7
    exists to flag and skip, and it says nothing about whether the walk is
    correct. A MEASURED type whose bytes do not account for the tag's declared
    size is the shipped-redundancy oracle failing in production: the reader is
    not where it believes it is, and every value decoded after it in the same
    payload is suspect.

    Both used to increment one counter and emit one warning code, so a caller
    could not tell a world holding content this project does not model from a
    parse that had lost its place. That is "silently wrong", the half of
    non-negotiable 7 with no second chance, and it is the same conflation
    CS-417 records one module over.

    THIS IS TESTABLE ONLY AGAINST A SYNTHETIC PAYLOAD, and that is a finding
    rather than a convenience: re-measured, the real library produces ZERO
    disagreements today, so a real-library assertion here would be vacuous in
    exactly the way that hides a regression.
    """
    payload = _disagreement_payload()
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    result = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert result.unmeasured_value_count == 1, "the StructProperty is the unmeasured one"
    assert result.disagreeing_value_count == 1, "the torn StrProperty is the disagreement"
    by_code = {warning.code: warning.actual for warning in result.warnings}
    # TWO SEPARATE REPORTS, not one report carrying a sum. Asserting the size
    # of the mapping is what catches a "split" that gave both conditions the
    # same code - a direct equality between the two constants is a fact the
    # type checker collapses statically, so it would assert nothing at runtime.
    assert len(by_code) == _DISTINCT_SKIP_REPORTS, (
        f"the two skip reasons produced {len(by_code)} distinct warning code(s); a "
        "caller cannot separate unmodelled content from a walk that has lost its place"
    )
    assert by_code[objects.WARN_MEASURED_VALUE_DISAGREED] == 1
    assert by_code[objects.WARN_UNMEASURED_PROPERTY_TYPE] == 1
    # Neither skipped value is published, and the walk still finished: stepping
    # by the DECLARED size is why a disagreement is silent without this report.
    assert "mSyntheticTornStr" not in result.properties
    assert "mSyntheticStruct" not in result.properties
    assert result.properties["mSyntheticInt"] == _SYNTHETIC_INT


def test_every_tag_whose_value_was_dropped_is_still_named() -> None:
    """CS-1264. A dropped VALUE is not a dropped TAG, and the name says which tag it was.

    A consumer asking whether a tag was PRESENT - a production boost - must get
    an answer when that tag's value did not decode, or a torn or unmeasured tag
    reads exactly like an absent one. The same fixture as the arm above, so the
    two counts it grades and the names graded here describe one payload: the
    torn value and the unmeasured struct are named, the decoded int is not.
    """
    payload = _disagreement_payload()

    result = objects.read_properties(
        _synthetic_body(payload), _synthetic_record(payload), _synthetic_map(_SYNTHETIC_SCHEMA)
    )

    assert result.undecoded_names == frozenset({"mSyntheticTornStr", "mSyntheticStruct"})
    assert result.properties["mSyntheticInt"] == _SYNTHETIC_INT


def test_a_payload_that_decodes_whole_names_no_dropped_tag() -> None:
    """The control: a payload whose every value decoded names nothing as dropped."""
    payload = (
        _actor_head(())
        + _scalar_tag("mSyntheticInt", "IntProperty", struct.pack("<i", _SYNTHETIC_INT))
        + _fstring("None")
        + _TRAILING_RUN
    )

    result = objects.read_properties(
        _synthetic_body(payload), _synthetic_record(payload), _synthetic_map(_SYNTHETIC_SCHEMA)
    )

    assert result.properties["mSyntheticInt"] == _SYNTHETIC_INT
    assert result.undecoded_names == frozenset()


def test_the_dropped_tag_names_are_withheld_from_the_result_repr() -> None:
    """A name read out of the save's own bytes is world content: a count renders, never a name."""
    payload = _disagreement_payload()

    result = objects.read_properties(
        _synthetic_body(payload), _synthetic_record(payload), _synthetic_map(_SYNTHETIC_SCHEMA)
    )

    assert "mSyntheticTornStr" in result.undecoded_names
    assert "mSyntheticTornStr" not in repr(result)
    assert "mSyntheticStruct" not in repr(result)
    assert "undecoded_names=2" in repr(result)


def test_the_payload_walk_repr_renders_a_count_and_never_a_dropped_name() -> None:
    """The walk's own record is the third type holding the names, and it renders a count.

    Built directly, so the arm grades what the repr PRINTS rather than which
    class the census lists: a repr rendering the names, sorted or not, is red
    here whatever the walk would have produced.
    """
    rendering = repr(
        objects._PayloadWalk(  # noqa: SLF001 - the private record is the subject
            properties={},
            unmeasured=1,
            disagreed=1,
            terminated=True,
            references=(),
            reference_tags=0,
            undecoded_references=0,
            undecoded_names=frozenset({"mSyntheticTornStr", "mSyntheticStruct"}),
        )
    )

    assert "mSyntheticTornStr" not in rendering
    assert "mSyntheticStruct" not in rendering
    assert "undecoded_names=2" in rendering


def test_an_unmeasured_type_alone_raises_no_disagreement_report() -> None:
    """The negative control - without it the split could be a second name for one thing.

    The main fixture carries two unmeasured tags and no torn value, so it must
    report the first and NOT the second. A conflated implementation that simply
    renamed the counter would fail here.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    result = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert result.unmeasured_value_count == _SYNTHETIC_UNMEASURED_TAGS
    assert result.disagreeing_value_count == 0
    assert objects.WARN_MEASURED_VALUE_DISAGREED not in [
        warning.code for warning in result.warnings
    ]


def test_an_unresolved_schema_still_decodes_and_is_still_flagged() -> None:
    """Resolution and decode are reported INDEPENDENTLY, per the shipped reader.

    The shipped mapping carries no ``Build_*`` schema, so this is the state
    essentially every real building is in. A reader that gated the decode on
    resolution would be permanently empty exactly where pillar 3 needs it.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    result = objects.read_properties(body, record, _synthetic_map("SomeOtherSchema_C"))

    assert not result.resolved
    assert _decoded_shape(result.properties) == dict(_EXPECTED_PROPERTIES)
    assert objects.WARN_UNRESOLVED_SCHEMA in [warning.code for warning in result.warnings]


# ---------------------------------------------------------------------------
# CS-960 - the decode with NO property map at all
#
# ``usmap.cached_usmap()`` answers None on a machine with no game install, so
# CI and every fresh clone are in that state. A reader that required a map
# decoded nothing there. The map was never an INPUT to the decode - a payload
# is tagged serialization and carries its own names, type words and widths -
# so the only thing an absent map may cost is the RESOLUTION report.
#
# AND ABSENT IS NOT UNMODELLED. With no map supplied nothing has claimed the
# class is unknown, so ``resolved`` answers None and no unresolved-schema
# warning is raised. Emitting one would be the confident-wrong answer
# non-negotiable 7 forbids, and it mirrors what this module already does one
# layer up, where ``known_classes=None`` flags nothing.
# ---------------------------------------------------------------------------


#: The ``PropertyResult`` fields a missing map is ALLOWED to move. Everything
#: else is the decode itself, and the decode does not consult the map.
#:
#: THE SET IS SUBTRACTED FROM THE DATACLASS RATHER THAN LISTED BESIDE IT, so a
#: field added to :class:`objects.PropertyResult` later is compared by default
#: and has to be exempted deliberately rather than forgotten into safety.
_MAP_SENSITIVE_RESULT_FIELDS: Final = frozenset({"resolved", "warnings"})


#: A value inside the readable struct below, distinct from every scalar the
#: base fixture carries so an interior that came back with the wrong field
#: cannot match by coincidence.
_STRUCT_INTERIOR_INT: Final = 4242


def _readable_struct_tag() -> bytes:
    """A ``StructProperty`` whose interior is a well-formed nested TAG LIST.

    THE BASE FIXTURE'S STRUCT TAG IS DELIBERATELY OPAQUE - it is there to prove
    an unmeasured type is skipped and counted - so it yields no interior at
    all. An arm claiming "no struct interior differs" against a result carrying
    zero interiors is claiming nothing, so this tag supplies the population.

    Returns:
        The whole tag.
    """
    interior = _scalar_tag("mInteriorField", "IntProperty", _i32(_STRUCT_INTERIOR_INT)) + _fstring(
        "None"
    )
    return _struct_tag("mReadableStruct", _SYNTHETIC_STRUCT_WORD, interior)


#: The two states a SUPPLIED map can be in, so the comparison below runs
#: against both. Against the modelled map the warning tuples are equal
#: outright; against the unmodelled one the mapped decode carries an
#: unresolved-schema warning the unmapped decode must not, which is the only
#: state where the warning half of the claim is non-vacuous.
_SUPPLIED_MAP_STATES: Final = ("modelled", "unmodelled")


def _mapped_and_unmapped(map_state: str) -> tuple[objects.PropertyResult, objects.PropertyResult]:
    """Decode ONE synthetic payload twice - with a supplied map, and with none.

    The same body and the same record both times, so any difference between
    the two results is attributable to the map and to nothing else.

    The payload is the base fixture plus :func:`_readable_struct_tag`, so all
    three populations the acceptance clause names - decoded values, decoded
    references and decoded struct interiors - are non-empty and are actually
    being compared.

    Args:
        map_state: Whether the supplied map models the fixture's class, from
            :data:`_SUPPLIED_MAP_STATES`.

    Returns:
        ``(mapped, unmapped)``.
    """
    supplied = _synthetic_map(_SYNTHETIC_SCHEMA if map_state == "modelled" else "SomeOtherSchema_C")
    head = _actor_head((_SYNTHETIC_COMPONENT,))
    tags = b"".join((*_MEASURED_TAGS, *_UNMEASURED_TAGS)) + _readable_struct_tag()
    payload = head + tags + _fstring("None") + _TRAILING_RUN
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)
    return (
        objects.read_properties(body, record, supplied),
        objects.read_properties(body, record, None),
    )


@pytest.mark.parametrize("map_state", _SUPPLIED_MAP_STATES)
def test_a_decode_with_no_map_differs_from_the_mapped_one_in_nothing_but_resolution(
    map_state: str,
) -> None:
    """CS-960's load-bearing arm. Every field is compared, not a count of them.

    A COUNT WOULD BE MET BY THE STRONGEST MEMBER while a weak one went
    unmeasured - the same values with a lost reference, or a struct interior
    that read one field short, both keep ``len(properties)`` intact. So the
    comparison walks :class:`objects.PropertyResult`'s own field list and
    demands equality on everything the exemption set does not name.

    ``properties`` is compared as the raw mapping rather than through
    :func:`_decoded_shape`: the reduction there drops each container element's
    ABSOLUTE body offset, which is exactly the kind of interior a decode
    reading from a different starting point would move. Both decodes run
    against the same bytes, so the offsets must match exactly and there is no
    reason to grade them loosely here.

    Args:
        map_state: Whether the supplied map models the class. BOTH ARE RUN
            because the warning half of the claim is vacuous against a
            modelled map - neither decode raises an unresolved-schema warning
            there, so an equality between the two tuples would hold however
            the no-map branch were written.
    """
    mapped, unmapped = _mapped_and_unmapped(map_state)

    # NON-VACUITY FIRST. An equality between two empty results is an equality
    # about nothing, and each of the three populations the acceptance clause
    # names - values, references, struct interiors - has to be present for
    # this arm to be saying anything about it.
    assert mapped.properties, "no values decoded, so the value comparison is vacuous"
    assert mapped.references, "no references decoded, so the reference comparison is vacuous"
    assert mapped.struct_interiors, "no struct interiors, so that comparison is vacuous"

    carried = {field.name for field in fields(mapped)}
    compared = sorted(carried - _MAP_SENSITIVE_RESULT_FIELDS)
    assert carried >= _MAP_SENSITIVE_RESULT_FIELDS, (
        "the exemption set names a field PropertyResult does not carry, so a real field "
        "may be going uncompared under a stale name"
    )

    differing = [name for name in compared if getattr(mapped, name) != getattr(unmapped, name)]
    assert not differing, (
        f"decoding the same payload without a property map changed {differing}. The map is "
        "not an input to the decode - a payload is tagged serialization - so the only "
        f"permitted differences are {sorted(_MAP_SENSITIVE_RESULT_FIELDS)}"
    )

    # The permitted two, asserted rather than merely excused. The warning tuple
    # may lose the unresolved-schema entry and MUST keep every other warning in
    # the same order.
    assert mapped.resolved is (map_state == "modelled")
    assert unmapped.resolved is None
    assert (
        tuple(
            warning for warning in mapped.warnings if warning.code != objects.WARN_UNRESOLVED_SCHEMA
        )
        == unmapped.warnings
    )
    carried_the_schema_warning = objects.WARN_UNRESOLVED_SCHEMA in [
        warning.code for warning in mapped.warnings
    ]
    assert carried_the_schema_warning is (map_state == "unmodelled"), (
        "the subtraction above only says anything where the mapped decode actually "
        "carries the warning, and this fixture state is not producing it"
    )


def test_resolution_reports_absent_unmodelled_and_modelled_as_three_distinct_states() -> None:
    """ABSENT and UNMODELLED may not collapse, and ``is`` is what stops them.

    ``False`` and ``None`` compare equal under ``not`` and under a truthiness
    test, so an arm written with ``assert not result.resolved`` would pass on
    either and would let a later edit answer False where no map was supplied -
    which is this project claiming the class is unmodelled on the strength of
    having looked at nothing.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    absent = objects.read_properties(body, record, None)
    unmodelled = objects.read_properties(body, record, _synthetic_map("SomeOtherSchema_C"))
    modelled = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert absent.resolved is None
    assert unmodelled.resolved is False
    assert modelled.resolved is True
    assert {absent.resolved, unmodelled.resolved, modelled.resolved} == {None, False, True}


def test_no_unresolved_schema_warning_is_raised_when_no_map_was_supplied() -> None:
    """No map means nothing has claimed the class is unknown.

    The warning's meaning is "a mapping was consulted and does not model this
    class". Raising it for an absent mapping would report unknown content that
    nothing measured, and would drown the real ones: on a machine with no
    install EVERY record would carry it.

    The unmodelled case is asserted alongside so this arm cannot pass by the
    warning having been deleted outright.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    absent = objects.read_properties(body, record, None)
    unmodelled = objects.read_properties(body, record, _synthetic_map("SomeOtherSchema_C"))

    assert objects.WARN_UNRESOLVED_SCHEMA not in [warning.code for warning in absent.warnings]
    assert objects.WARN_UNRESOLVED_SCHEMA in [warning.code for warning in unmodelled.warnings]


def test_a_zero_length_payload_reports_an_absent_map_the_same_way() -> None:
    """The early return is a SECOND construction site for the resolution report.

    ``read_properties`` builds a :class:`objects.PropertyResult` on four paths.
    A fix applied to the last one alone would answer None where the payload has
    content and False where it has none, which is the same class of split this
    module's frame-leak arm was bitten by.
    """
    body = _synthetic_body(b"")
    record = _synthetic_record(b"", body_length=0)

    result = objects.read_properties(body, record, None)

    assert result.resolved is None
    assert result.warnings == ()
    assert result.properties == {}


def test_the_synthetic_decode_touches_no_save_locator(monkeypatch) -> None:
    """THE PROOF THAT THIS HALF NEEDS NO LIBRARY, rather than the claim of it.

    Every locator entry point is replaced with one that raises, so a decode
    path that quietly reached for the machine's save directory would fail here
    instead of passing on this operator's machine and skipping on CI.
    """

    def _refuse(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("the synthetic decode path must not reach for a save library")

    monkeypatch.setattr(locate, "resolve_save_root", _refuse)
    monkeypatch.setattr(locate, "resolve_account_dir", _refuse)
    monkeypatch.setattr(usmap, "cached_usmap", _refuse)

    payload = _synthetic_payload(actor=True)
    result = objects.read_properties(
        _synthetic_body(payload), _synthetic_record(payload), _synthetic_map(_SYNTHETIC_SCHEMA)
    )

    assert _decoded_shape(result.properties) == dict(_EXPECTED_PROPERTIES)


# ---------------------------------------------------------------------------
# Non-negotiable 12 at this seam - what a repr and a raising frame may hold
# ---------------------------------------------------------------------------

#: Planted in a synthetic value, a synthetic property NAME and a synthetic
#: schema name. Nothing real is ever used for this: the assertion is that the
#: marker does NOT come out, so a real string would be the one thing that
#: cannot be used to prove it.
_LEAK_MARKER: Final = "SYNTHETIC_WORLD_CONTENT_MARKER"


def _renderings(value: object) -> tuple[str, ...]:
    """Every text rendering a logger, a test runner or a formatter would take.

    Args:
        value: The object under test.

    Returns:
        The renderings.
    """
    return (
        repr(value),
        str(value),
        f"{value}",
        f"{value!r}",
        f"{value!s}",
        format(value),
        repr([value]),
        repr({"entry": value}),
    )


def test_a_property_result_repr_renders_no_decoded_name_value_or_schema() -> None:
    """Non-negotiable 12, at the type that now carries decoded save values.

    :class:`objects.ObjectRecord` and :class:`objects.ObjectTable` have hand
    written reprs that render structure and withhold every string, because a
    test runner and most loggers repr an object before a human chooses what to
    print. :class:`objects.PropertyResult` was exempt only while its
    ``properties`` mapping was empty on every path. It is not any more: the
    VALUES are player-authored strings and the KEYS are property names decoded
    out of the save's own bytes, so both halves of every entry are world
    content, and ``schema_name`` is a class-path fragment ``ObjectRecord``
    already withholds.
    """
    result = objects.PropertyResult(
        properties=MappingProxyType({f"{_LEAK_MARKER}_KEY": f"{_LEAK_MARKER}_VALUE"}),
        schema_name=f"{_LEAK_MARKER}_SCHEMA",
        resolved=False,
        warnings=(),
        unmeasured_value_count=3,
    )

    for rendering in _renderings(result):
        assert _LEAK_MARKER not in rendering, (
            "a PropertyResult rendering carries a decoded property name, a decoded "
            f"value or the schema name it resolved to:\n  {rendering}"
        )
    # Non-vacuity: a repr that rendered nothing at all would pass the loop
    # above while telling an operator nothing. Structure must still come out.
    assert "properties=1" in repr(result)
    assert "resolved=False" in repr(result)
    assert "unmeasured_value_count=3" in repr(result)


def _frames_beneath_the_caller(exc: BaseException) -> tuple[FrameType, ...]:
    """Every frame the exception passed through BELOW the frame that called in.

    The caller's own frame is excluded deliberately: in this module that frame
    is the test, and the test is the thing holding the fixture body on purpose.
    What is asserted is what ``clockspeed`` itself leaves behind.

    Args:
        exc: The raised exception, taken as a PARAMETER rather than rendered.

    Returns:
        The frames, outermost first.
    """
    frames: list[FrameType] = []
    entry = exc.__traceback__
    walk = entry.tb_next if entry is not None else None
    while walk is not None:
        frames.append(walk.tb_frame)
        walk = walk.tb_next
    return tuple(frames)


def _rendered_spellings(marker: str) -> tuple[str, ...]:
    r"""Every spelling of the marker a RENDERER could put in front of a person.

    TWO, AND THE SECOND ONE IS THE ONE CS-964 IS ABOUT. A renderer handed a
    UTF-16-LE slice prints the letters each followed by an escaped null, so the
    marker ``Needle`` appears as ``N\\x00e\\x00e\\x00d\\x00l\\x00e\\x00``. A person
    reads that at a glance; an ASCII substring search does not find it at all.

    THE ESCAPED SPELLING IS TAKEN FROM ``repr`` ITSELF rather than assembled by
    interleaving a literal, because ``repr`` decides its own escaping and a
    hand-built spelling would be a second implementation of it - wrong the first
    time a marker carries a quote or a backslash.

    Args:
        marker: The planted marker, in its plain text.

    Returns:
        The plain spelling first, then the wide-rendered one.
    """
    # repr(bytes) is always `b`, a quote, the body, the same quote.
    rendered = repr(marker.encode("utf-16-le"))
    escaped = rendered[2:-1]
    return (marker, escaped) if escaped != marker else (marker,)


def _assert_the_needle_is_observable(marker: str, needle: bytes) -> None:
    """Prove both oracles CAN see this needle before an arm concludes from silence.

    THE CONTROL THE ACCEPTANCE CLAUSE NAMES, in one line per arm. An arm's empty
    verdict means "nothing holds the value" only if the oracle could have seen
    the value at all - and session 80 shipped three arms where it could not. A
    correct-looking fixture, a refusal that never enters the frame holding the
    value, and an oracle blind to the value's spelling all produce the SAME
    empty output as a genuinely clean parser. Reading cannot tell them apart;
    only a control can.

    WHAT IT CATCHES is the trap this item's own note names in capitals: moving
    the marker constant to its wide spelling while the fixture still carries the
    narrow one makes an arm VACUOUS rather than wide. Handed the text and the
    needle bytes, this refuses a pair that does not describe one value, so the
    mismatch fails loudly at the top of the arm instead of passing quietly at
    the bottom.

    THE THREE CHECKS ARE THE THREE HOLDER FAMILIES, deliberately - a decoded
    string, a value one attribute hop inside a withholding object, and a
    rendering. Each is a family some arm in this suite actually sweeps, and an
    oracle can be live for one and blind to another.

    Args:
        marker: The planted marker, in its plain text.
        needle: The same value in the spelling the fixture carries.

    Raises:
        AssertionError: The pair does not describe one value, or an oracle
            cannot observe it.
    """
    assert _reaches_the_needle(marker, needle, 0) == [""], (
        f"the structural sweep cannot see {needle!r} in the decoded text {marker!r}. "
        "Either the needle is not this marker's spelling, or the str branch is blind "
        "to it - and an arm built on this pair would measure nothing"
    )
    assert _reaches_the_needle(_WithholdingHolder(marker), needle, 0) == ["._buffer"], (
        f"the structural sweep cannot reach {needle!r} one attribute hop inside a "
        "withholding holder, which is the shape the save layer actually uses"
    )
    rendered = _safe_repr(needle)
    assert any(spelling in rendered for spelling in _rendered_spellings(marker)), (
        f"no spelling the rendering sweep hunts appears in {rendered!r}, so the repr "
        f"oracle is blind to {marker!r} in this encoding"
    )


def _leaking_locals(frame: FrameType, marker: str) -> tuple[str, ...]:
    """Names in one frame whose RENDERING carries the marker, in any spelling.

    Rendering is the oracle rather than identity, because that is exactly what
    a traceback formatter showing locals prints.

    IT ASKS FOR EVERY SPELLING A RENDERER WOULD PRINT, not only the ASCII one.
    A wide-encoded buffer renders legibly and the plain marker is genuinely
    absent from that rendering, so the ASCII-only question reported clean over a
    frame that was printing the value - an oracle blind to its own subject. See
    :func:`test_the_rendering_sweep_is_not_blind_to_a_wide_buffer_in_a_frame_local`.

    Args:
        frame: The frame to inspect.
        marker: The planted marker.

    Returns:
        The offending local names.
    """
    spellings = _rendered_spellings(marker)
    return tuple(
        name
        for name, value in frame.f_locals.items()
        if any(spelling in _safe_repr(value) for spelling in spellings)
    )


def _safe_repr(value: object) -> str:
    """Repr a frame local without letting a hostile repr break the sweep.

    Args:
        value: The local.

    Returns:
        Its repr, or a placeholder if repr itself raised.
    """
    try:
        return repr(value)
    # `SystemExit` for the reason `_library_save_paths` gives: it is not an
    # `Exception`, and escaping here unwinds through a frame holding the local.
    except (Exception, SystemExit):  # a broken repr is not this test's subject
        return ""


def _chained_exceptions(exc: BaseException) -> tuple[BaseException, ...]:
    """``exc`` plus every exception reachable from it through the cause chain.

    THE CHAIN IS THE POINT, AND IT IS WHY CS-963 WENT UNSEEN FOR AN ITEM AND A
    HALF. :func:`_frames_beneath_the_caller` follows ``__traceback__`` alone, so
    a frame belonging to a CAUSE was outside every privacy sweep in this layer
    by construction - not missed, unreachable. ``raise ... from exc`` puts those
    frames in the rendered traceback all the same, and both ``pytest
    --showlocals`` and ``TracebackException(capture_locals=True)`` print their
    locals verbatim.

    BOTH LINKS ARE FOLLOWED. ``__cause__`` is the explicit ``from exc`` and
    ``__context__`` is the implicit one a raise inside an ``except`` block sets
    even when the author wrote no ``from``; a renderer shows either, so a walker
    that followed only the explicit link would be blind to exactly the raise
    shape an author did not think about.

    ``__suppress_context__`` IS HONOURED, AND THAT IS A MEASUREMENT RATHER THAN
    A PREFERENCE. ``raise ... from None`` sets it, and ``traceback`` - which is
    what ``pytest`` and ``TracebackException`` both render through - then prints
    neither the suppressed exception nor its frames. Sweeping them anyway would
    report a leak through a channel no renderer has, and this layer uses
    ``from None`` deliberately where a library message could quote bytes. The
    agreement between this rule and the renderer is pinned by
    :func:`test_the_walker_honours_suppression_exactly_as_the_renderer_does`.

    Cycles are possible - ``__context__`` can point back into a chain already
    walked - so identity is tracked rather than assuming a finite line.

    Args:
        exc: The raised exception, taken as a PARAMETER rather than rendered.

    Returns:
        Every exception in the chain, the head first.
    """
    reached: list[BaseException] = []
    seen: set[int] = set()
    queue: list[BaseException] = [exc]
    while queue:
        node = queue.pop(0)
        if id(node) in seen:
            continue
        seen.add(id(node))
        reached.append(node)
        links = [node.__cause__]
        if not node.__suppress_context__:
            links.append(node.__context__)
        queue.extend(link for link in links if link is not None)
    return tuple(reached)


def _frames_in_the_cause_chain(exc: BaseException) -> tuple[FrameType, ...]:
    """Every frame a renderer would show for ``exc``, cause chain included.

    The head exception's entry frame is dropped for the reason
    :func:`_frames_beneath_the_caller` gives: it is the caller, and in these
    modules the caller is the test, which holds the fixture on purpose. A
    CHAINED exception's frames are ALL kept - its outermost frame is the shipped
    frame containing the ``try``, which is a frame under test rather than the
    caller, and dropping it would re-open a hole one level down.

    A frame can appear in more than one traceback in the chain, so identity is
    tracked and each is reported once.

    Args:
        exc: The raised exception.

    Returns:
        The frames, outermost first, head traceback first.
    """
    frames: list[FrameType] = []
    seen: set[int] = set()
    for index, node in enumerate(_chained_exceptions(exc)):
        entry = node.__traceback__
        walk = entry.tb_next if (index == 0 and entry is not None) else entry
        while walk is not None:
            if id(walk.tb_frame) not in seen:
                seen.add(id(walk.tb_frame))
                frames.append(walk.tb_frame)
            walk = walk.tb_next
    return tuple(frames)


#: A marker bound in the CAUSE's frame and nowhere else, for the control below.
_CAUSE_CHAIN_MARKER: Final = "PlantedCauseChainMarker"


def _raise_holding_the_marker() -> None:
    """Bind the marker as a frame local and raise out of that frame.

    Raises:
        ValueError: Always. The message does NOT carry the marker, so the only
            channel by which it can be found is the frame local.
    """
    held = _CAUSE_CHAIN_MARKER
    assert held  # the local must be live at the raise, not optimised away
    raise ValueError("a refusal whose message says nothing")


def _raise_chaining_over_the_marker() -> None:
    """Re-raise a second exception FROM the first, as the save layer does.

    Raises:
        RuntimeError: Always, chained from the ValueError above.
    """
    try:
        _raise_holding_the_marker()
    except ValueError as exc:
        raise RuntimeError("the outer refusal") from exc


def test_the_direct_walker_cannot_see_a_local_held_in_a_cause_frame() -> None:
    """THE BLINDNESS, PINNED AS A PROPERTY OF THE OLD WALKER.

    This is half of CS-963's known-good control and it is stated as a POSITIVE
    fact about ``_frames_beneath_the_caller`` rather than as an absence: the
    marker IS visible to the oracle in the value that holds it, the cause frame
    IS in the chain, and the direct walker still returns no frame holding it.

    Without this arm the widened walker below could be quietly reverted to the
    direct one and every cause-chain assertion in this layer would go green
    again while measuring nothing - which is precisely the failure CS-963 was
    filed for. An oracle that cannot observe the value it is asked about passes
    for that reason alone.
    """
    with pytest.raises(RuntimeError) as caught:
        _raise_chaining_over_the_marker()
    raised = caught.value

    # CONTROL: the oracle can see the marker in a value that holds it, so an
    # empty verdict below is about the WALKER and not about the oracle.
    assert _CAUSE_CHAIN_MARKER in _safe_repr(_CAUSE_CHAIN_MARKER)

    direct = tuple(
        frame.f_code.co_name
        for frame in _frames_beneath_the_caller(raised)
        if _leaking_locals(frame, _CAUSE_CHAIN_MARKER)
    )
    assert direct == (), (
        "the direct walker now reaches a cause frame, so this arm no longer pins the "
        f"blindness it exists to pin. Frames it found: {direct}"
    )


def test_the_cause_chain_walker_sees_a_local_held_in_a_cause_frame() -> None:
    """THE KNOWN-GOOD CONTROL CS-963's acceptance requires, standing alone.

    Every cause-chain privacy assertion in this layer is an assertion that a
    sweep found NOTHING. That verdict is worth exactly as much as the proof
    that the same sweep finds something when something IS there, and that proof
    must not depend on the production code under test - otherwise a scrub
    landing in ``header.py`` would silently disarm the control along with the
    leak.

    So the leaking frame here is synthetic, local to this module, and holds the
    marker in a frame the walker must reach only by following ``__cause__``.
    """
    with pytest.raises(RuntimeError) as caught:
        _raise_chaining_over_the_marker()
    raised = caught.value

    found = tuple(
        frame.f_code.co_name
        for frame in _frames_in_the_cause_chain(raised)
        if _leaking_locals(frame, _CAUSE_CHAIN_MARKER)
    )
    assert found == ("_raise_holding_the_marker",), (
        "the cause-chain walker did not find the planted local in the cause's own frame, "
        f"so every empty verdict it returns elsewhere is vacuous. Frames it found: {found}"
    )


def test_the_cause_chain_walker_terminates_on_a_self_referential_chain() -> None:
    """A CYCLE MUST NOT HANG THE SWEEP.

    ``__context__`` is set implicitly and can be made to point back into a chain
    already walked. A walker that assumed a finite line would spin here, and a
    privacy sweep that hangs is a privacy sweep that gets deleted.
    """
    first = ValueError("first")
    second = RuntimeError("second")
    second.__cause__ = first
    first.__context__ = second

    # Named rather than inline: the pair IS the fixture, so the expectation is
    # derived from it and cannot drift away from what the arm actually builds.
    both = (second, first)
    assert _chained_exceptions(second) == both, (
        "the walker did not return exactly the two exceptions in the cycle, so it either "
        "spun, stopped early, or reported a frame twice"
    )


def _raise_suppressing_the_marker() -> None:
    """Re-raise with ``from None``, the shape this layer uses deliberately.

    Raises:
        RuntimeError: Always, with the ValueError's context SUPPRESSED.
    """
    try:
        _raise_holding_the_marker()
    except ValueError:
        raise RuntimeError("the outer refusal, context suppressed") from None


def test_the_walker_honours_suppression_exactly_as_the_renderer_does() -> None:
    """THE WALKER'S ONE DELIBERATE BLIND SPOT, MEASURED AGAINST THE RENDERER.

    ``raise ... from None`` is used in ``header.py`` and ``chunks.py`` where a
    library's own message could quote bytes. ``traceback`` prints neither the
    suppressed exception nor its frames, so a sweep that reached them would
    report a leak through a channel that does not exist.

    THIS IS ASSERTED AS AGREEMENT, NOT AS A CHOICE. The renderer is run and its
    output checked, so if CPython ever began showing suppressed contexts this
    arm reddens and the walker is wrong rather than merely different. Without
    that half it would be this module asserting its own preference back to
    itself.
    """
    with pytest.raises(RuntimeError) as caught:
        _raise_suppressing_the_marker()
    raised = caught.value

    rendered = "".join(traceback.format_exception(type(raised), raised, raised.__traceback__))
    assert "_raise_holding_the_marker" not in rendered, (
        "the renderer DOES show the suppressed cause's frames, so the walker skipping them "
        f"is a real blind spot rather than agreement:\n{rendered}"
    )

    walked = tuple(
        frame.f_code.co_name
        for frame in _frames_in_the_cause_chain(raised)
        if _leaking_locals(frame, _CAUSE_CHAIN_MARKER)
    )
    assert walked == (), (
        "the walker reached a frame the renderer does not show, so an empty verdict "
        f"elsewhere is stricter than the channel it claims to measure. Frames: {walked}"
    )


def test_an_out_of_range_payload_extent_raises_for_an_unresolved_class_too() -> None:
    """The reachability this merge widened, PINNED as deliberate.

    Before the decode landed, an unresolved class returned before the extent
    was ever checked - so on this project's own measurement, where essentially
    no building resolves, the structural check ran on almost nothing. Reaching
    it for every record is the correct direction and is kept: an extent running
    past the body is not unknown CONTENT that non-negotiable 7 covers, it is a
    record claiming bytes that do not exist, and collapsing the two would
    report a truncated or misattributed body as merely unmodelled.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    overrun = _synthetic_record(payload, body_length=len(body))

    with pytest.raises(objects.ObjectTruncatedError) as caught:
        objects.read_properties(body, overrun, _synthetic_map())

    assert caught.value.field == "property_payload"
    assert caught.value.offset == len(_BODY_PREFIX)


#: EVERY exported way into the property readers, so the frame assertion below
#: covers the module's stated public surface rather than one entry point of it.
#: Both names are in ``objects.__all__``; ``parse_properties`` is the one
#: ``world.py`` points a caller at, and it propagates the same error.
#:
#: THE ENTRY POINTS ARE ENUMERATED RATHER THAN LISTED BY HAND WHERE POSSIBLE -
#: a hand-list goes stale between being written and being worked. What keeps
#: this one honest is :func:`test_the_frame_assertion_covers_every_exported_
#: property_reader`, which derives the same set from ``objects.__all__`` and
#: fails if a third reader is exported without arriving here.
_PROPERTY_READERS: Final = ("read_properties", "parse_properties")


#: The two map states the frame scrub has to survive, CS-960. ``del`` on a name
#: bound to None is perfectly legal, so the None path costs the mechanism
#: nothing - but "costs nothing" is a prediction until the arm runs it, and the
#: no-map call is now the DEFAULT one on any machine with no game install.
_MAP_STATES: Final = ("mapped", "unmapped")


def _raise_through(
    entry_point: str, body: bytes, record: objects.ObjectRecord, map_state: str
) -> BaseException:
    """Call one exported reader with an out-of-range extent and return the error.

    Args:
        entry_point: The name of the reader, from :data:`_PROPERTY_READERS`.
        body: The synthetic body.
        record: A record whose declared extent runs past it.
        map_state: ``"mapped"`` or ``"unmapped"``, from :data:`_MAP_STATES`.

    Returns:
        The raised exception, so the caller can walk its traceback.
    """
    reader = getattr(objects, entry_point)
    supplied = _synthetic_map() if map_state == "mapped" else None
    with pytest.raises(objects.ObjectTruncatedError) as caught:
        reader(body, record, supplied)
    return caught.value


@pytest.mark.parametrize("map_state", _MAP_STATES)
@pytest.mark.parametrize("entry_point", _PROPERTY_READERS)
def test_no_clockspeed_frame_holds_the_body_when_the_extent_raises(
    entry_point: str, map_state: str
) -> None:
    """The leak the widened reachability opened, closed at EVERY exported way in.

    The ``ObjectTruncatedError`` MESSAGE is clean and always was; that is not
    the channel. A renderer showing locals - ``pytest -l`` is one - prints the
    whole decompressed body verbatim from any frame that still holds it, which
    is a mitigation the mechanism defeats.

    IT IS PARAMETRIZED OVER THE ENTRY POINTS BECAUSE ITS FIRST REVISION WAS NOT,
    and that is the more important half of this fix. It asserted a general
    property - "a clockspeed frame in the raised traceback still holds the save
    body" - while exercising ``read_properties`` alone, and
    :func:`_frames_beneath_the_caller` drops the entry frame. So it passed green
    while its own failure message was FALSE for ``parse_properties``, whose
    frame held the body across the raise it documents itself as propagating.
    A green test whose name denies a live leak is worse than no test, because
    the next author reads the name and stops looking.

    The record is deliberately not asserted against: its own ``__repr__``
    withholds every string it carries, which is this module's existing control
    and is checked elsewhere.

    IT IS ALSO PARAMETRIZED OVER THE MAP STATE, CS-960. Both raise sites drop
    ``property_map`` alongside ``body``, and ``del`` on a name bound to None is
    legal - but the no-map call is now the DEFAULT one wherever there is no
    game install, so the path that runs everywhere is the one that has to be
    exercised rather than the one that runs on the operator's machine.

    Args:
        entry_point: The exported reader under test.
        map_state: Whether a property map was supplied at all.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload) + _LEAK_MARKER.encode("ascii")
    overrun = _synthetic_record(payload, body_length=len(body))

    raised = _raise_through(entry_point, body, overrun, map_state)

    leaks = {
        frame.f_code.co_name: _leaking_locals(frame, _LEAK_MARKER)
        for frame in _frames_in_the_cause_chain(raised)
        if _leaking_locals(frame, _LEAK_MARKER)
    }
    assert not leaks, (
        f"entered through objects.{entry_point} with a {map_state} call, a clockspeed "
        "frame in the raised traceback still holds the save body. A renderer showing "
        "locals prints it verbatim, head and tail (non-negotiable 12). Offending "
        f"frame(s) and local name(s): {leaks}"
    )
    # NON-VACUITY. Without this the sweep passes just as happily when the
    # marker was never in any frame to begin with, which is the ABSOLUTE_PATH
    # failure this project has already been bitten by. The frame that CALLED in
    # - _raise_through, which the sweep drops - genuinely holds the body, and
    # the sweep must be able to see it.
    entry = raised.__traceback__
    assert entry is not None
    assert _leaking_locals(entry.tb_frame, _LEAK_MARKER), (
        "the marker is not visible in the calling frame either, so the assertion "
        "above proves nothing about what was removed"
    )


def test_the_frame_assertion_covers_every_exported_property_reader() -> None:
    """A hand-written entry-point list is a list that goes stale. This is the guard.

    ``objects.__all__`` is the module's STATED public surface. Any exported
    name that takes a body and hands it to the reader below it is another frame
    that can hold the body across a raise, so it belongs in
    :data:`_PROPERTY_READERS`. Deriving the set here rather than trusting the
    tuple is what makes a third reader red instead of silently uncovered.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    exported_readers = {
        name
        for name in objects.__all__
        if name.endswith("_properties") and callable(getattr(objects, name, None))
    }
    assert exported_readers, "no property reader is exported at all; this is vacuous"
    assert exported_readers == set(_PROPERTY_READERS), (
        f"objects.__all__ exports {sorted(exported_readers)} as property readers but the "
        f"frame assertion is parametrized over {sorted(_PROPERTY_READERS)}. Every "
        "exported reader holds the body in its own frame while the one below it raises, "
        "so each one has to be exercised - a general claim proved at one entry point is "
        "a claim about that entry point"
    )


# ---------------------------------------------------------------------------
# The module's own two-way classification of property type words
# ---------------------------------------------------------------------------

#: An Unreal property type word as it appears inside prose - capitalised, ASCII
#: and suffixed ``Property``.
_TYPE_WORD_IN_PROSE: Final = re.compile(r"\b[A-Z][A-Za-z0-9_]*Property\b")


def _type_words_named_by_the_region_table() -> frozenset[str]:
    """Every property type word the unmeasured-region table NAMES in its prose.

    Returns:
        The words. Safe to render in a failure message: every one of them came
        out of a literal in tracked source, never out of a save.
    """
    named: set[str] = set()
    for text in objects.UNMEASURED_PAYLOAD_REGIONS.values():
        named.update(_TYPE_WORD_IN_PROSE.findall(text))
    return frozenset(named)


def _type_words_named_by_other_entries(key: str) -> frozenset[str]:
    """The same, excluding one entry's own text so it cannot justify itself.

    Args:
        key: The entry to exclude.

    Returns:
        The words every OTHER entry names.
    """
    named: set[str] = set()
    for other, text in objects.UNMEASURED_PAYLOAD_REGIONS.items():
        if other != key:
            named.update(_TYPE_WORD_IN_PROSE.findall(text))
    return frozenset(named)


def test_every_type_word_the_module_names_is_on_one_side_of_its_own_split() -> None:
    """A type word in neither half of a two-way classification is a gap, not a note.

    ``MEASURED_VALUE_TYPES`` and ``UNMEASURED_PAYLOAD_REGIONS`` are that split.
    A word the module NAMES and places in neither is one nobody can act on:
    the library sweep's completeness check would go red the first time a real
    payload carried it, and only on a machine that has a library.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    named = _type_words_named_by_the_region_table()
    assert named, "the region table names no type word at all, so this is vacuous"

    unclassified = (
        named - set(objects.MEASURED_VALUE_TYPES) - set(objects.UNMEASURED_PAYLOAD_REGIONS)
    )
    assert not unclassified, (
        f"{sorted(unclassified)} are named by objects.UNMEASURED_PAYLOAD_REGIONS and "
        "appear in neither half of that module's own two-way classification. Record "
        "each as a region with what is pinned and what is not claimed, or state why "
        "it belongs in MEASURED_VALUE_TYPES - do not delete the word"
    )


def test_no_type_word_sits_on_both_sides_of_the_module_s_own_split() -> None:
    """The half of the two-way classification the union check never held.

    :func:`test_every_type_word_the_module_names_is_on_one_side_of_its_own_split`
    requires every word the region table names to sit in one half or the other.
    IT IS A UNION CHECK AND A WORD IN BOTH HALVES SATISFIES IT - more
    comfortably than a word in either, because it is covered twice. A two-way
    classification needs both halves to be true of it, and only one of them was
    ever asserted.

    THIS IS THE MECHANISM CS-481 RIDES, ONE TABLE ALONG. The byte-order half of
    it is graded where the status data lives - see
    ``tests/save/test_byte_order_status.py::test_no_word_carries_a_byte_order_status_the_module_records_as_unclaimed``
    - and NEITHER SUBSUMES THE OTHER, which is measured rather than assumed:
    the reproduction on that item holds its word OUT of
    ``objects.MEASURED_VALUE_TYPES`` while leaving it in the fixed-width table,
    so the intersection asserted here stays empty while the status mapping
    contradicts the region table. The reverse route - a word added to a
    string-valued family while its region entry stands - is invisible from
    there and lands here.

    IT LISTS NOTHING. Both operands are shipped tables read in the same run, and
    what is asserted is that they do not contradict each other.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo, not about a world.
    """
    measured = objects.MEASURED_VALUE_TYPES
    regions = objects.UNMEASURED_PAYLOAD_REGIONS
    assert measured, "objects.MEASURED_VALUE_TYPES is empty, so this test grades nothing"
    assert regions, (
        "objects.UNMEASURED_PAYLOAD_REGIONS is empty, so this test grades nothing - and "
        "emptying it is also the cheapest way to satisfy it, which is why it is refused."
    )

    both = sorted(frozenset(measured) & frozenset(regions))
    assert not both, (
        f"{both} are recorded by objects.py as types whose value encoding is MEASURED and "
        "decoded, and ALSO as payload regions whose entry states what this module does "
        "not claim about that same encoding. Both cannot be true, and the entry a reader "
        "believes decides whether they treat the decode as evidence or as a gap. Cite the "
        "measurement where the type is decoded and retire the region entry, or drop the "
        "type from the measured set - do not leave the module saying both."
    )


def test_the_region_table_holds_no_key_nothing_justifies() -> None:
    """The OTHER direction of the completeness check, which was checked one way.

    :func:`test_every_unmeasured_type_the_library_holds_is_recorded_as_data`
    asserts every unmeasured word the library holds has an entry. Measured
    against the merged tree, the reverse did not hold: adding a bogus
    ``NoSuchProperty`` entry passed. So a key must be justified by something -
    the library holding it at top level, or another entry naming it. An entry's
    own text is excluded, because a claim that cites itself is not a citation.

    Every name rendered below is a key of a table in tracked source, so naming
    them costs nothing that the source does not already say.
    """
    sweep = _sweep_or_skip()
    _assert_walker_is_live(sweep)

    unjustified = sorted(
        key
        for key in objects.UNMEASURED_PAYLOAD_REGIONS
        if key != "trailing_run"
        and key not in sweep.region_keys_the_library_holds
        and key not in _type_words_named_by_other_entries(key)
    )
    assert not unjustified, (
        f"{unjustified} are recorded as unmeasured payload regions, but this library "
        "holds no top-level tag of them and no other entry names them. An entry for a "
        "type nothing has ever produced is a record of a measurement that was never "
        "made"
    )


# ---------------------------------------------------------------------------
# parse_properties states no capability it does not own
# ---------------------------------------------------------------------------

#: The clause CS-418 fixed in ``world.py`` and left standing here.
_STALE_EMPTINESS_CLAIM: Final = "Always empty"


def test_parse_properties_claims_no_emptiness_read_properties_has_refuted() -> None:
    """The CS-418 defect, at the second site in the same merge.

    ``parse_properties`` is in ``objects.__all__`` and is what ``world.py``
    points a caller at, and its docstring said the mapping is "Always empty
    today". That is false in the DANGEROUS direction: it tells the next
    consumer the return is safe to print, when it is decoded world content.

    THE BEHAVIOUR IS ASSERTED FIRST so the prose check below is a refutation
    rather than a spelling preference. The limit is stated rather than hidden:
    this pins one phrase, so a differently worded false claim would still get
    through. What stops that is the rule the fix follows - do not restate a
    capability this function does not own; point at the owner.
    """
    payload = _synthetic_payload(actor=True)
    decoded = objects.parse_properties(
        _synthetic_body(payload), _synthetic_record(payload), _synthetic_map(_SYNTHETIC_SCHEMA)
    )

    assert _decoded_shape(decoded) == dict(_EXPECTED_PROPERTIES), (
        "parse_properties no longer returns what read_properties decoded, so the "
        "docstring assertion below is about the wrong function"
    )
    doc = objects.parse_properties.__doc__ or ""
    assert _STALE_EMPTINESS_CLAIM not in doc, (
        "objects.parse_properties still documents its return as always empty, which "
        "the decode immediately above refutes. Point at read_properties as the owner "
        "of what can be decoded rather than restating it here"
    )


# ---------------------------------------------------------------------------
# Discovery containment - no frame holding the account directory may unwind
# ---------------------------------------------------------------------------


def _explode(*_args: object, **_kwargs: object) -> object:
    """Fail the way a locator can fail, without naming anything real.

    Args:
        *_args: Ignored.
        **_kwargs: Ignored.

    Raises:
        RuntimeError: Always.
    """
    raise RuntimeError("synthetic locator failure")


def _raise_system_exit(*_args: object, **_kwargs: object) -> bytes:
    """Fail with the non-``OSError`` that is ALSO not an ``Exception``.

    ``SystemExit`` derives from ``BaseException``, so ``except Exception`` does
    not hold it - :func:`test_the_forced_failures_are_outside_the_narrow_catch`
    asserts that hierarchy rather than leaving it to a reader. Any library
    called during a read or a locate may raise one, and ``sys.exit`` inside a
    plugin or an atexit path is the ordinary way it arrives.

    Args:
        *_args: Ignored.
        **_kwargs: Ignored.

    Raises:
        SystemExit: Always.
    """
    raise SystemExit("synthetic exit during a library reach")


#: Every DISCOVERY grader in this package runs both of these, as
#: ``(type name, callable)``. One is an ``Exception`` and one is not, which is
#: the distinction a handler naming only ``Exception`` does not survive.
_FORCED_DISCOVERY_FAILURES: Final = (
    ("RuntimeError", _explode),
    ("SystemExit", _raise_system_exit),
)


def _contained_call(call: Callable[[], object]) -> tuple[str | None, object]:
    """Run a contained call and reduce BOTH outcomes to something safe to render.

    THE TEST THAT GRADES A LEAK MUST NOT BE THE LEAK. Every sweep here is
    written to return None rather than raise, so a containment regression shows
    up as an exception unwinding OUT of the call - and letting that reach pytest
    renders every frame it passed through, which is exactly the save path, the
    account directory and the body bytes these tests exist to contain. The
    escape is caught here and reduced to its type NAME, so the caller can assert
    on a string that names a class and nothing else.

    ``BaseException`` rather than ``Exception`` because this is a grader rather
    than production code: a ``KeyboardInterrupt`` arriving mid-sweep would
    otherwise unwind through those same frames on its way out.

    Args:
        call: The contained call under test.

    Returns:
        ``(escaped type name, None)`` when it raised, else ``(None, its value)``.
    """
    try:
        return None, call()
    except BaseException as exc:  # broad on purpose - see the docstring above
        return type(exc).__name__, None


def _assert_sweep_declines(label: str, call: Callable[[], object]) -> None:
    """Assert one sweep declined, rendering only a name and a boolean.

    Args:
        label: What to call the sweep in a failure message.
        call: The sweep.
    """
    escaped, value = _contained_call(call)
    assert escaped is None, (
        f"the {label} let {escaped} unwind instead of containing it, and every frame "
        "it unwound through held a save path or the account directory"
    )
    declined = value is None
    assert declined, f"the {label} did not decline"


def _assert_every_sweep_declines() -> None:
    """Every sweep THIS module's graders reach must decline rather than unwind.

    Which sweeps those are is stated by the calls below and nowhere else. The
    real-library helpers in ``tests/save/test_objects.py`` and
    ``tests/save/test_world.py`` are outside this grader's reach and carry their
    own, under CS-427; a count of "all the sweeps" written here would be a
    restated fact and would drift the moment either module grew one.

    EVERY SUBJECT IS REDUCED TO A SCALAR BEFORE IT IS ASSERTED ON. pytest
    rewrites an assertion to render the operands it compared, so
    ``assert _library_save_paths() == ()`` prints the discovered save paths on
    failure - the account directory, which is the exact thing these tests
    exist to keep out of a log. The assertions below can only ever print an
    integer, a boolean or an exception type NAME.

    THE THIRD SWEEP WENT UNGRADED FROM THE DAY IT WAS WRITTEN.
    ``test_decode_oracles._sweep_decode_oracles`` is a third walk over the real
    library with its own discovery call, and nothing here reached it: splicing
    the known-bad discovery shape into it - the locators called outside the
    ``try``, which is what every real-library helper in
    ``tests/save/test_objects.py`` and ``tests/save/test_world.py`` also carried
    until CS-427 - left this suite byte-identically green while the spliced
    sweep leaked the account directory. Two sweeps being contained was never
    evidence about a third, which is why those two modules now grade themselves
    rather than being reasoned about from here.

    The import is function-local because ``test_decode_oracles`` imports THIS
    module at its top, so a module-level import here would close that cycle.
    """
    from tests.save import test_decode_oracles  # noqa: PLC0415 - breaks an import cycle

    oracle_sweep = test_decode_oracles._sweep_decode_oracles  # noqa: SLF001
    _sweep_decoded_values.cache_clear()
    oracle_sweep.cache_clear()
    try:
        escaped, discovered = _contained_call(lambda: len(_library_save_paths()))
        assert escaped is None, f"the discovery let {escaped} unwind"
        assert discovered == 0, "the discovery raised instead of returning nothing"
        _assert_sweep_declines("tag sweep", _sweep_payload_tags)
        _assert_sweep_declines("decode sweep", _sweep_decoded_values)
        _assert_sweep_declines("oracle sweep", oracle_sweep)
    finally:
        # Both sweeps are cached and other tests consume them, so a None cached
        # under a monkeypatched locator would skip those tests silently.
        _sweep_decoded_values.cache_clear()
        oracle_sweep.cache_clear()


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    _FORCED_DISCOVERY_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_root_lookup_does_not_unwind_through_any_sweep(
    monkeypatch, _forced, raiser
) -> None:
    """The discovery calls used to sit outside every ``try`` in both sweeps.

    ``resolve_save_root`` and ``resolve_account_dir`` were called before the
    broad handler that contains everything else, so a failure in either
    unwound through a frame holding ``account`` - a path carrying both the
    Windows account name and the numeric platform account id (CLAUDE.md
    section 2). Every one of the module's own privacy arguments rests on
    "there is no failure path that unwinds through a frame holding one", and
    that was the path.

    NAMED "any" RATHER THAN "either" because the grader now reaches a third
    sweep in ``test_decode_oracles``, which no containment test reached while
    this one was called ``either``.
    """
    monkeypatch.setattr(locate, "resolve_save_root", raiser)
    _assert_every_sweep_declines()


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    _FORCED_DISCOVERY_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_account_directory_lookup_does_not_unwind_through_any_sweep(
    monkeypatch, _forced, raiser
) -> None:
    """The second of the three, and the one whose frame holds the account id."""
    monkeypatch.setattr(locate, "resolve_save_root", lambda: Path("synthetic-root"))
    monkeypatch.setattr(locate, "resolve_account_dir", raiser)
    _assert_every_sweep_declines()


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    _FORCED_DISCOVERY_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_glob_does_not_unwind_through_any_sweep(
    monkeypatch, _forced, raiser
) -> None:
    """The third uncontained call - it was in the ``for`` statement itself."""
    monkeypatch.setattr(Path, "glob", raiser)
    _assert_every_sweep_declines()


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    _FORCED_DISCOVERY_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_usmap_load_does_not_unwind_through_the_decode_sweep(
    monkeypatch, _forced, raiser
) -> None:
    """The call the DECODE sweep added that the older tag sweep never had.

    ``cached_usmap`` resolves the game install, so it fails for the same
    reasons the locators do and it sat outside the same ``try``.
    """
    monkeypatch.setattr(usmap, "cached_usmap", raiser)
    _sweep_decoded_values.cache_clear()
    try:
        # Reduced to a boolean first, for the reason on _assert_every_sweep_
        # declines. That reason used to be that usmap.PropertyMap carried the
        # DEFAULT repr and rendered its whole name table; CS-424 replaced that
        # repr with structure and counts, so the echo is gone from the type
        # itself. The reduction stays because it is the stronger guarantee: a
        # quiet repr is a promise a later edit can withdraw, while a comparison
        # whose operands are booleans has no mapping to render in the first
        # place.
        loader_declined = _cached_usmap_or_none() is None
        assert loader_declined, "the contained usmap loader let the failure unwind"
        sweep_declined = _sweep_decoded_values() is None
        assert sweep_declined, "the decode sweep did not decline"
    finally:
        _sweep_decoded_values.cache_clear()


# ---------------------------------------------------------------------------
# Read containment - no frame holding a save path may unwind either
# ---------------------------------------------------------------------------

#: A save path that names nothing real. The read containment below is graded on
#: this rather than on the library, so it runs on a machine with no game
#: installed and never puts a real path into a frame in the first place.
_SYNTHETIC_SAVE: Final = Path("synthetic-save.sav")


def _raise_memory_error(*_args: object, **_kwargs: object) -> bytes:
    """Fail the way a large read really can - outside the narrow catch.

    ``MemoryError`` is an ``Exception`` and is neither an ``OSError`` nor a
    ``HeaderError``, which is the whole property that made it the leak. It is a
    plausible failure of ``read_bytes`` on a save this size rather than an
    invented one, and the narrow catch let it straight through.

    Args:
        *_args: Ignored.
        **_kwargs: Ignored.

    Raises:
        MemoryError: Always.
    """
    raise MemoryError("synthetic allocation failure")


#: The two forced failures every read-containment grader in this package runs,
#: as ``(type name, callable)``. Both are non-``OSError``; one is an
#: ``Exception`` and one is not, which is the distinction a containment that
#: catches only ``Exception`` does not survive.
_FORCED_READ_FAILURES: Final = (
    ("MemoryError", _raise_memory_error),
    ("SystemExit", _raise_system_exit),
)


def _assert_read_failure_is_contained(
    label: str, call: Callable[[], object], expected: str = "MemoryError"
) -> None:
    """Assert one sweep reduced an unexpected read failure to a type NAME.

    ``failures`` is read with ``getattr`` so that a sweep which DECLINED rather
    than recording the failure fails this assertion too, with the same message
    and without a second branch that could render the sweep itself.

    Args:
        label: What to call the sweep in a failure message.
        call: The sweep.
        expected: The type name the sweep must have recorded. Defaults to
            ``MemoryError`` so that callers written before ``SystemExit`` was
            forced keep their meaning unchanged.
    """
    escaped, value = _contained_call(call)
    assert escaped is None, (
        f"{escaped} escaped the {label} instead of being reduced to a type name "
        "inside it, and the frame it unwound through held the save path"
    )
    reported = getattr(value, "failures", None)
    assert reported == (expected,), (
        f"the {label} reported {reported} rather than the one contained {expected}, "
        "so the unexpected read failure was not recorded as a type name"
    )


def test_the_forced_failures_are_outside_the_narrow_catch() -> None:
    """The hierarchy every containment in this package is built on, asserted.

    Both forced failures must be non-``OSError`` - that is the wording of the
    contract they grade. ``SystemExit`` must additionally be outside
    ``Exception``, because a containment written as ``except Exception`` holds
    one and not the other, and pytest's own outcome exceptions must be outside
    BOTH so that widening a handler to hold ``SystemExit`` cannot swallow a
    ``skip`` or a ``fail``.
    """
    for _name, raiser in _FORCED_READ_FAILURES:
        with pytest.raises(BaseException) as caught:  # noqa: PT011 - the class IS the subject
            raiser()
        assert not isinstance(caught.value, OSError)

    assert not issubclass(SystemExit, Exception)
    assert issubclass(MemoryError, Exception)
    assert not issubclass(pytest.skip.Exception, Exception | SystemExit)
    assert not issubclass(pytest.fail.Exception, Exception | SystemExit)


# ---------------------------------------------------------------------------
# THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard itself lives in ``tests/save/reach_guard.py`` and is applied to
# every module in this package by the suite-wide test in
# ``tests/save/test_reach_guard.py``, which walks the package directory rather
# than waiting to be called. What stays here is this module's own declarations
# and the checks that grade THIS file rather than the guard: that no test in it
# is gutted, that its reaching functions are declared, and that the guard
# catches an uncontained helper spliced into a copy of its source - the last of
# those in two tests, one plain shape and one matrix of the shapes that escaped
# an earlier guard.
# ---------------------------------------------------------------------------


#: This module's own library-reaching helpers, name to why it reaches.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_library_save_paths": "holds the locators and the save glob",
        "_sweep_payload_tags": "reads every save in the library",
        "_sweep_decoded_values": "reads every save in the library",
        "_sweep_width_census": "reads every save in the library",
    }
)

#: Functions that touch a primitive WITHOUT consuming a real path, name to why.
_EXEMPT_LIBRARY_REACH: Final = MappingProxyType(
    {
        reach_guard.MODULE_SCOPE_REACH: (
            "Path(...).resolve() at module scope, building the shipped package's "
            "directory as a constant so the CS-963 cause-chain sweep can tell a "
            "clockspeed frame from a test helper's. It resolves a TRACKED SOURCE "
            "FILE - objects.py itself - never a save directory and never the "
            "account directory, and it is computed once rather than per frame"
        ),
        "_assert_every_sweep_declines": (
            "a grader, not a consumer: it calls the contained discovery inside "
            "_contained_call and reduces the result to an integer before asserting"
        ),
    }
)


def test_no_test_in_this_module_is_gutted_to_an_early_return() -> None:
    """CS-433 - the guard against the cheapest way to fake a green suite."""
    _assert_no_test_is_gutted(Path(__file__))


def test_every_library_reaching_function_here_is_declared() -> None:
    """This module is graded by the guard it used to own.

    IT OWNED :func:`~tests.save.reach_guard._assert_library_reach_is_declared`
    UNTIL CS-495 MOVED IT, and the sentence here used to justify keeping it: a
    guard whose owner is outside its own scope is the arrangement that let a
    third sweep ship ungraded one file over. That justification did not survive
    CS-471, which walks the package directory and so grades ``reach_guard``
    itself on the same terms as this module. The check stays because a module
    that consumes the guard should force it on its own source, which is the
    reason every other consumer carries this test too - not because the owner
    lives here.
    """
    _assert_library_reach_is_declared(
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER, forced rather than asserted about.

    The splice is the pre-repair shape - the locators and the glob outside every
    ``try``, under a catch naming two families - wired in exactly as the real
    helpers are. Run against a COPY in ``tmp_path``, so the check never mutates
    a tracked file and never needs a restore.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    root = locate.resolve_save_root()\n"
        "    account = locate.resolve_account_dir(root)\n"
        '    for path in sorted(account.glob("*.sav")):\n'
        "        try:\n"
        "            return header.parse_header(path.read_bytes())\n"
        "        except (OSError, header.HeaderError):\n"
        "            continue\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert "_spliced_uncontained_helper" in str(caught.value)

    # The positive control: the same guard on the unspliced source passes, so
    # the red above is the splice rather than the guard rejecting everything.
    _assert_library_reach_is_declared(
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


#: Uncontained helpers the guard must flag, as label mapped to the source to
#: splice and the name the failure has to report.
#:
#: EVERY ENTRY IS A SHAPE THAT ESCAPED A REAL MEASUREMENT, not a shape imagined
#: from the implementation. The plain ``def`` control one function up was the
#: shape the guard caught; these were spliced past it by the adversary that
#: refuted the guard's containment claim. Three root causes are represented: the
#: AST filter naming one node type, ``_calls_any`` matching only a literal call
#: spelling, and a primitive vocabulary carrying no path-bearing name.
#:
#: THE PRIMITIVE SHAPES REACH THE LIBRARY WITHOUT NAMING A LOCATOR, and that is
#: what makes them isolate. A first draft of this matrix spelled
#: ``locate.resolve_save_root()`` inside them as well, so the guard caught them
#: on the locator and reported nothing about the primitive - four of the eight
#: went green against the pre-repair guard and looked like coverage of a gap
#: they never touched. Building the root from the environment instead is both
#: the isolating construction and the realistic one, since hardcoding that path
#: is what non-negotiable 3 forbids.
_UNCONTAINED_SPLICES: Final = MappingProxyType(
    {
        "async-def": (
            "\n\nasync def _spliced_async_helper():\n"
            '    """An async helper carrying the known-bad shape."""\n'
            "    root = locate.resolve_save_root()\n"
            "    account = locate.resolve_account_dir(root)\n"
            '    return sorted(account.glob("*.sav"))\n',
            "_spliced_async_helper",
        ),
        "class-method": (
            "\n\nclass _SplicedReacher:\n"
            '    """A module-scope class whose method reaches the library."""\n'
            "\n"
            "    def reach(self):\n"
            "        root = locate.resolve_save_root()\n"
            "        return locate.resolve_account_dir(root)\n",
            "_SplicedReacher.reach",
        ),
        "rglob": (
            "\n\ndef _spliced_rglob_helper():\n"
            '    """Walks a hardcoded save root with rglob instead of glob."""\n'
            '    root = Path(os.environ["LOCALAPPDATA"]) / "FactoryGame"\n'
            '    return sorted(root.rglob("*.sav"))\n',
            "_spliced_rglob_helper",
        ),
        "iterdir-and-builtin-open": (
            "\n\ndef _spliced_iterdir_helper():\n"
            '    """Lists a hardcoded save root and opens a save by builtin."""\n'
            '    root = Path(os.environ["LOCALAPPDATA"]) / "FactoryGame"\n'
            "    for path in sorted(root.iterdir()):\n"
            '        with open(path, "rb") as handle:\n'
            "            return handle.read(4)\n"
            "    return None\n",
            "_spliced_iterdir_helper",
        ),
        "module-level-alias": (
            "\n\n_spliced_alias = _library_save_paths\n"
            "\n\ndef _spliced_alias_helper():\n"
            '    """Reaches the library through a module-scope alias."""\n'
            "    return [path for path in _spliced_alias()]\n",
            "_spliced_alias_helper",
        ),
        "getattr-by-string": (
            "\n\ndef _spliced_getattr_helper():\n"
            '    """Reaches the locator through getattr rather than a dotted call."""\n'
            '    finder = getattr(locate, "resolve_save_root")\n'
            "    return finder()\n",
            "_spliced_getattr_helper",
        ),
        "os-scandir": (
            "\n\ndef _spliced_scandir_helper():\n"
            '    """Walks a hardcoded save root through the os module."""\n'
            '    root = Path(os.environ["LOCALAPPDATA"]) / "FactoryGame"\n'
            "    return [entry.path for entry in os.scandir(root)]\n",
            "_spliced_scandir_helper",
        ),
        "os-stat": (
            "\n\ndef _spliced_stat_helper():\n"
            '    """Stats one hardcoded save file, naming no other primitive."""\n'
            '    save = Path(os.environ["LOCALAPPDATA"]) / "FactoryGame" / "newest.sav"\n'
            "    return os.stat(save).st_size\n",
            "_spliced_stat_helper",
        ),
    }
)


@pytest.mark.parametrize(
    ("label", "splice", "reported"),
    [(label, splice, reported) for label, (splice, reported) in _UNCONTAINED_SPLICES.items()],
    ids=list(_UNCONTAINED_SPLICES),
)
def test_the_guard_catches_every_uncontained_shape_that_escaped_it(
    tmp_path: Path, label: str, splice: str, reported: str
) -> None:
    """CS-433 - the guard's power against the shapes it was measured to miss.

    The single-shape control one function up passed while seven of these eight
    walked through, which is the failure class where a guard reads as protection
    and grades one spelling of the thing it names. Each shape is spliced into a
    COPY in ``tmp_path``, so nothing tracked is mutated and no restore is needed.

    Args:
        tmp_path: The per-test temporary directory.
        label: The shape's name, used only in a failure message.
        splice: The uncontained source to append.
        reported: The name the guard's failure has to carry.
    """
    spliced = tmp_path / f"spliced_{label.replace('-', '_')}.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + splice,
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        _assert_library_reach_is_declared(
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert reported in str(caught.value), (
        f"the guard failed on the {label} splice without naming {reported}, so it "
        "reddened for some other reason and this shape is still unmeasured"
    )

    # The positive control, run per shape rather than once: the same guard on
    # the unspliced source passes, so the red above is this splice.
    _assert_library_reach_is_declared(
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


@pytest.mark.parametrize(
    ("forced", "raiser"),
    _FORCED_READ_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_read_failure_does_not_unwind_through_either_local_sweep(
    monkeypatch, forced, raiser
) -> None:
    """The read and the header parse sat under ``except (OSError, HeaderError)``.

    That catch names the two failures somebody predicted and lets every other
    type escape the sweep entirely. pytest renders the arguments of the frames
    it unwinds with NO opt-in flag, and ``path.read_bytes()`` unwinds through a
    bound method whose ``self`` IS the save path - one line carrying the Windows
    account name, the numeric platform account id and the world name. That is
    non-negotiable 3 three times over and non-negotiable 12 once, under
    completely default pytest flags.

    Parametrized over both forced failures because ``SystemExit`` is a
    ``BaseException``: a handler naming ``Exception`` alone holds ``MemoryError``
    and leaks on ``SystemExit``, and one forced type cannot tell them apart.

    THE SAVE LIST IS SYNTHETIC, so this runs on a machine with no game
    installed, and the escape is reduced to a type name by ``_contained_call``
    so the test grading the leak cannot become one.
    """
    monkeypatch.setattr(
        "tests.save.test_properties._library_save_paths", lambda: (_SYNTHETIC_SAVE,)
    )
    monkeypatch.setattr(
        "tests.save.test_properties._cached_usmap_or_none",
        lambda: _synthetic_map(_SYNTHETIC_SCHEMA),
    )
    monkeypatch.setattr(Path, "read_bytes", raiser)
    _sweep_decoded_values.cache_clear()
    try:
        _assert_read_failure_is_contained("tag sweep", _sweep_payload_tags, forced)
        _assert_read_failure_is_contained("decode sweep", _sweep_decoded_values, forced)
    finally:
        _sweep_decoded_values.cache_clear()


@dataclass(frozen=True)
class _StubHeader:
    """The three fields both sweeps read off a parsed header, and nothing else.

    Attributes:
        header_version: Half of the layout pair.
        save_version: The other half.
        body_offset: Where the chunk walk would start.
    """

    header_version: int
    save_version: int
    body_offset: int


@pytest.mark.parametrize(
    ("forced", "raiser"),
    _FORCED_READ_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_walk_failure_does_not_unwind_through_either_local_sweep(
    monkeypatch, forced, raiser
) -> None:
    """The BROAD handlers, which the read grader above never reaches.

    That grader forces its failure at ``read_bytes``, which the handler ABOVE
    these catches - so narrowing either broad handler back to ``except
    Exception`` alone changed nothing anywhere, and a survived mutant is an
    ungraded containment whatever else is green.

    THESE ARE THE FRAMES THAT HOLD THE BODY. ``chunks.decompress_body(data, ...)``
    takes the whole save's bytes, so an escape here prints save content rather
    than a path. So the read is made to SUCCEED here and the walk to fail.

    The pair is taken from the intersection the two sweeps gate on, because they
    gate on different sets - ``MEASURED_BODY_LAYOUTS`` and :data:`TAGGED_PAIRS` -
    and a pair outside either would make that sweep skip rather than record.
    """
    header_version, save_version = next(
        iter(sorted(set(TAGGED_PAIRS) & set(objects.MEASURED_BODY_LAYOUTS)))
    )
    monkeypatch.setattr(
        "tests.save.test_properties._library_save_paths", lambda: (_SYNTHETIC_SAVE,)
    )
    monkeypatch.setattr(
        "tests.save.test_properties._cached_usmap_or_none",
        lambda: _synthetic_map(_SYNTHETIC_SCHEMA),
    )
    monkeypatch.setattr(Path, "read_bytes", lambda _self: b"synthetic-not-a-save")
    monkeypatch.setattr(
        header, "parse_header", lambda _data: _StubHeader(header_version, save_version, 0)
    )
    monkeypatch.setattr(chunks, "decompress_body", raiser)
    _sweep_decoded_values.cache_clear()
    try:
        _assert_read_failure_is_contained("tag sweep", _sweep_payload_tags, forced)
        _assert_read_failure_is_contained("decode sweep", _sweep_decoded_values, forced)
    finally:
        _sweep_decoded_values.cache_clear()


class _HostileRepr:
    """A value whose ``repr`` fails the way :func:`_safe_repr` must survive."""

    def __init__(self, raiser: Callable[..., object]) -> None:
        """Store the failure to raise from ``__repr__``."""
        self._raiser = raiser

    def __repr__(self) -> str:
        """Raise rather than render.

        Returns:
            Never returns.
        """
        self._raiser()
        return ""  # pragma: no cover - the raiser always raises


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    _FORCED_READ_FAILURES,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_hostile_repr_does_not_unwind_through_the_safe_repr(_forced, raiser) -> None:
    """``_safe_repr`` renders a frame LOCAL, so its escape carries that local.

    The locals it is pointed at come from frames inside a real-library sweep, so
    a type escaping here unwinds through one holding a save path or a body. It
    must swallow both forced failures and return the placeholder.
    """
    assert _safe_repr(_HostileRepr(raiser)) == ""

    # The positive control: an ordinary value still renders, so the placeholder
    # above is the containment rather than the helper returning "" for anything.
    assert _safe_repr(1) == "1"


#: The shipped package, resolved once. Module scope rather than per call: this
#: is a filesystem primitive, and this module is one of the few that declares a
#: library reach - which is exactly why the sweep lives here instead of being
#: re-derived in every test module that wants it.
_SHIPPED_ROOT: Final = os.path.normcase(str(Path(objects.__file__).resolve().parent.parent))


def _shipped_frames(raised: BaseException, marker: str) -> dict[str, tuple[str, ...]]:
    """Every SHIPPED frame in the cause chain whose locals render the marker.

    The one sweep the save layer's privacy arms share, so that widening it
    widens all of them at once. CS-963 exists because the opposite was true:
    each arm reached for :func:`_frames_beneath_the_caller` on its own, that
    walker followed ``__traceback__`` alone, and so every arm in the layer was
    silent about any frame arriving as a ``__cause__`` - which is how the raw
    save sat live in four shipped frames under arms that were green.

    THE ROOT FILTER IS NOT COSMETIC. The walker keeps the test's helper frames,
    which hold the fixture on purpose; what is asserted is what ``clockspeed``
    itself leaves behind.

    Args:
        raised: The exception, taken as a PARAMETER rather than rendered.
        marker: The planted plaintext needle.

    Returns:
        Offending shipped frame name to the offending local names in it. Empty
        when nothing leaks - which means something only alongside a control
        proving this function can see the marker when one IS present.
    """
    return {
        frame.f_code.co_name: _leaking_locals(frame, marker)
        for frame in _frames_in_the_cause_chain(raised)
        if os.path.normcase(frame.f_code.co_filename).startswith(_SHIPPED_ROOT)
        and _leaking_locals(frame, marker)
    }


def _shipped_frame_names(raised: BaseException) -> set[str]:
    """The names of every frame in the cause chain, for a non-vacuity check.

    An arm that swept a traceback its subject never entered would report no
    leak for the wrong reason, so each one asserts its subject is IN here
    before asserting the sweep came back empty.

    Args:
        raised: The exception.

    Returns:
        The frame names.
    """
    return {frame.f_code.co_name for frame in _frames_in_the_cause_chain(raised)}


#: How deep the structural sweep follows attributes and members. Bounded rather
#: than unlimited: the point is to reach a buffer an object is HOLDING, which in
#: this layer is one or two hops, and an unbounded walk over arbitrary objects
#: is a way to hang a test suite rather than a way to measure anything.
_STRUCTURAL_DEPTH: Final = 6


def _slot_and_attribute_paths(
    value: object, needle: bytes, depth: int, seen: dict[int, int]
) -> list[str]:
    """Paths through declared slots and instance attributes.

    THE MRO IS WALKED, NOT THE MOST-DERIVED CLASS. ``type(value).__slots__``
    finds only the nearest declaration, so a slot inherited from a base was
    invisible - and a slotted holder has no ``__dict__`` to fall back on, which
    makes that the whole of its state.

    Args:
        value: The object to inspect.
        needle: The planted bytes.
        depth: How many hops have been taken.
        seen: Identity to shallowest depth walked.

    Returns:
        The paths.
    """
    found: list[str] = []
    for klass in type(value).__mro__:
        for name in klass.__dict__.get("__slots__", ()) or ():
            if isinstance(name, str) and hasattr(value, name):
                found += [
                    f".{name}{tail}"
                    for tail in _reaches_the_needle(getattr(value, name), needle, depth + 1, seen)
                ]
    for name, member in tuple((getattr(value, "__dict__", None) or {}).items()):
        found += [f".{name}{tail}" for tail in _reaches_the_needle(member, needle, depth + 1, seen)]
    return found


def _reference_paths(value: object, needle: bytes, depth: int, seen: dict[int, int]) -> list[str]:
    """Paths through shapes that hold a reference WITHOUT an attribute.

    Each was measured unreachable by the first cut of this sweep, and each can
    hold a whole save: a closure cell, a partial's bound arguments, the receiver
    of a bound method, and a suspended generator's frame - which is in no
    traceback and is very much alive.

    ``BaseException.args`` is excluded because an exception's args are the
    message channel the repr oracle already grades, and including them would
    report the same finding twice under two different names.

    Args:
        value: The object to inspect.
        needle: The planted bytes.
        depth: How many hops have been taken.
        seen: Identity to shallowest depth walked.

    Returns:
        The paths.
    """
    found: list[str] = []
    for name, member in (
        ("__self__", getattr(value, "__self__", None)),
        ("func", getattr(value, "func", None)),
        ("gi_frame.f_locals", getattr(getattr(value, "gi_frame", None), "f_locals", None)),
    ):
        if member is not None:
            found += [
                f".{name}{tail}" for tail in _reaches_the_needle(member, needle, depth + 1, seen)
            ]
    for index, cell in enumerate(getattr(value, "__closure__", None) or ()):
        try:
            contents = cell.cell_contents
        except ValueError:  # an empty cell is not a holder
            continue
        found += [
            f".__closure__[{index}]{tail}"
            for tail in _reaches_the_needle(contents, needle, depth + 1, seen)
        ]
    if not isinstance(value, BaseException):
        for index, argument in enumerate(getattr(value, "args", None) or ()):
            found += [
                f".args[{index}]{tail}"
                for tail in _reaches_the_needle(argument, needle, depth + 1, seen)
            ]
    return found


def _member_paths(value: object, needle: bytes, depth: int, seen: dict[int, int]) -> list[str]:
    """Paths through container members.

    Args:
        value: The container.
        needle: The planted bytes.
        depth: How many hops have been taken.
        seen: Identity to shallowest depth walked.

    Returns:
        The paths.
    """
    found: list[str] = []
    if isinstance(value, (list, tuple, set, frozenset)):
        for index, member in enumerate(value):
            found += [
                f"[{index}]{tail}" for tail in _reaches_the_needle(member, needle, depth + 1, seen)
            ]
    if isinstance(value, dict):
        for key, member in tuple(value.items()):
            found += [
                f"[{key!r}]{tail}" for tail in _reaches_the_needle(member, needle, depth + 1, seen)
            ]
    return found


def _needle_as_text(needle: bytes) -> tuple[str, ...]:
    """Every text the needle could have been DECODED FROM on the wire.

    Asked of a ``str`` holder only. The holder carries text that the parser
    already decoded, so the question is which spellings of the needle could have
    produced it - not which bytes the needle literally is. Unreal writes a
    string as UTF-8 with a positive count or UTF-16-LE with a negative one, so
    those are the two candidates and there is no third.

    An empty decode is DROPPED rather than returned: ``"" in value`` is true of
    every string alive, so letting one through would make the sweep report a
    holder for anything at all, and an oracle that always fires is as useless as
    one that never does.

    Args:
        needle: The planted bytes, in whichever spelling the fixture used.

    Returns:
        The candidate texts, deduplicated, in a stable order.
    """
    spellings: list[str] = []
    for encoding in ("utf-8", "utf-16-le"):
        try:
            text = needle.decode(encoding)
        except UnicodeDecodeError:
            # An odd-length needle cannot be UTF-16 at all, and a needle with a
            # high byte may not be valid UTF-8. Neither is an error here: it
            # rules that spelling out, which is the answer.
            continue
        if text and text not in spellings:
            spellings.append(text)
    return tuple(spellings)


def _reaches_the_needle(
    value: object, needle: bytes, depth: int, seen: dict[int, int] | None = None
) -> list[str]:
    """Paths under ``value`` at which ``needle`` is reachable, as attribute text.

    THE ORACLE THE REPR ONE CANNOT BE. :func:`_leaking_locals` asks what a frame
    RENDERS, which is the right question for what a traceback prints and the
    wrong one for what a frame HOLDS. A buffer one attribute hop inside an
    object whose ``__repr__`` withholds is invisible to it - and that gap is not
    theoretical, it is where this layer's remaining retention lives.

    IT IS REFLEXIVE RATHER THAN A LIST OF KNOWN TYPES, deliberately. A sweep
    enumerating ``_Cursor._data`` and ``DecompressedBody.payload`` by name would
    be silent the day a third holder is written, which is the failure this whole
    item is about.

    ``seen`` MAPS IDENTITY TO THE SHALLOWEST DEPTH ALREADY WALKED, AND THAT IS A
    BUG FIX RATHER THAN A REFINEMENT. It used to be a flat set: a value first
    reached AT the depth boundary was recorded, its children were then cut off
    by the boundary, and a SHALLOWER path to the same value afterwards hit the
    set and returned nothing. The sweep came back EMPTY with the needle plainly
    reachable two hops down - and an empty verdict is what every arm here reads
    as a pass. Measured by an adversary at chain length five: the needle sat at
    depth two and the walk reported nothing at all.

    A DECODED STRING IS NOT SKIPPED. The first cut returned early for ``str`` on
    the grounds that ``repr()`` shows a string, so the repr oracle covers it -
    true of a bare local and false of a string held INSIDE an object that
    withholds. On a real save the decoded strings are the session name and the
    player display name, so skipping them skipped the subject.

    THE BYTES BRANCH AND THE STR BRANCH ANSWER DIFFERENT QUESTIONS, and running
    both through one comparison is what CS-964 found. A bytes holder holds the
    WIRE spelling, so it must match byte-exact - that exactness is the entire
    reason the wide arms exist. A str holder holds DECODED TEXT, where the
    needle's wire encoding says nothing about what the holder contains.

    The old str branch asked ``needle.decode("utf-8") in value``. Hand that a
    UTF-16-LE needle and the decode SUCCEEDS - every byte of wide ASCII is below
    0x80 - yielding the marker's letters each followed by a null, which no
    decoded string contains. It returned EMPTY, and an empty verdict is what
    every arm here reads as a pass. Since ``_Cursor.string`` decodes BEFORE it
    binds, the frame local on a wide save holds the plain text while the fixture
    spells it wide, so the blindness landed on the one holder family that
    renders the value legibly. See
    :func:`test_the_structural_sweep_is_not_blind_to_a_wide_needle_over_decoded_text`.

    Args:
        value: The local, or something reached from one.
        needle: The planted bytes.
        depth: How many hops have been taken.
        seen: Identity to shallowest depth walked. Omit at the call site.

    Returns:
        One path string per place the needle is reachable. Empty is a real
        verdict ONLY alongside a control showing this function finds a planted
        needle when one IS present.
    """
    if seen is None:
        seen = {}
    if depth > _STRUCTURAL_DEPTH or seen.get(id(value), _STRUCTURAL_DEPTH + 1) <= depth:
        return []
    seen[id(value)] = depth

    if isinstance(value, (bytes, bytearray, memoryview)):
        return [""] if needle in bytes(value) else []
    if isinstance(value, str):
        return [""] if any(text in value for text in _needle_as_text(needle)) else []

    return (
        _slot_and_attribute_paths(value, needle, depth, seen)
        + _reference_paths(value, needle, depth, seen)
        + _member_paths(value, needle, depth, seen)
    )


def _structural_holders(raised: BaseException, needle: bytes) -> dict[str, tuple[str, ...]]:
    """Every SHIPPED frame in the cause chain that HOLDS the needle, however deep.

    Args:
        raised: The exception, taken as a PARAMETER rather than rendered.
        needle: The planted bytes.

    Returns:
        Frame name to the ``local`` / ``local.attr`` paths that reach the needle.
    """
    holders: dict[str, tuple[str, ...]] = {}
    for frame in _frames_in_the_cause_chain(raised):
        if not os.path.normcase(frame.f_code.co_filename).startswith(_SHIPPED_ROOT):
            continue
        paths: list[str] = []
        for name, value in tuple(frame.f_locals.items()):
            paths += [name + tail for tail in _reaches_the_needle(value, needle, 0)]
        if paths:
            holders[frame.f_code.co_name] = tuple(sorted(paths))
    return holders


def _encapsulating_holders(holders: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """The holder paths that reach the buffer through an ATTRIBUTE, not directly.

    A path with no dot in it is a frame local that IS the buffer - a renderer
    prints that, and it is a leak. A path with a dot reaches it through an
    object, and whether that is a leak depends entirely on what the object's
    ``__repr__`` does.

    Args:
        holders: The structural sweep's result.

    Returns:
        The dotted paths, frame-qualified, sorted.
    """
    return tuple(
        sorted(
            f"{frame}:{path}" for frame, paths in holders.items() for path in paths if "." in path
        )
    )


def _bare_holders(holders: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """The holder paths where the frame local IS the buffer - always a leak.

    Args:
        holders: The structural sweep's result.

    Returns:
        The undotted paths, frame-qualified, sorted.
    """
    return tuple(
        sorted(
            f"{frame}:{path}"
            for frame, paths in holders.items()
            for path in paths
            if "." not in path
        )
    )


#: A marker that exists only inside this module, for the structural control.
_STRUCTURAL_MARKER: Final = "PlantedStructuralNeedleXray"


class _WithholdingHolder:
    """Holds a buffer and renders none of it - the shape the save layer uses."""

    def __init__(self, buffer: bytes | str) -> None:
        """Take the buffer.

        EITHER TYPE, because the sweep has two holder families and CS-964's
        control drives both through this one stand-in: a DECODED STRING, which
        is what `_Cursor.string` binds, and a RAW BUFFER, which is what the
        cursor keeps. Annotating it `bytes` alone was a lie the type checker
        was right to reject.

        Args:
            buffer: The bytes, or the decoded text, to hold.
        """
        self._buffer = buffer

    def __repr__(self) -> str:
        """Say nothing about the buffer.

        Returns:
            A fixed string.
        """
        return "<_WithholdingHolder>"


def test_the_structural_sweep_sees_what_the_repr_sweep_cannot() -> None:
    """THE CONTROL FOR THE SECOND ORACLE, and the reason there is a second one.

    Stated as a DIFFERENCE between the two oracles over one value, so it cannot
    pass by both of them being blind. The repr oracle is asserted to return
    NOTHING for a withholding holder - that is the gap, pinned as a positive
    fact - and the structural sweep is asserted to find the buffer through the
    attribute in the same breath.

    An adversary found this gap by holding the whole save in a `_Cursor` and
    watching the project's own sweep return an empty verdict. Neither oracle is
    sufficient alone: repr answers "what does a traceback print", structural
    answers "what does the frame hold", and the acceptance needs both.
    """
    held = _WithholdingHolder(_STRUCTURAL_MARKER.encode("ascii"))

    assert _STRUCTURAL_MARKER not in _safe_repr(held), (
        "the holder renders its buffer, so this arm is not measuring the gap it exists to measure"
    )
    assert _reaches_the_needle(held, _STRUCTURAL_MARKER.encode("ascii"), 0) == ["._buffer"], (
        "the structural sweep cannot reach a buffer one attribute hop away"
    )


#: The same text as _STRUCTURAL_MARKER with its last word changed. Used as the
#: NEGATIVE control below, and non-empty on purpose: synthetic.fstring returns a
#: bare zero count above its own wide branch, so there is no wide encoding of the
#: empty string in either of this suite's two encoders (CS-964).
_STRUCTURAL_MARKER_ABSENT: Final = "PlantedStructuralNeedleYankee"


def test_the_structural_sweep_is_not_blind_to_a_wide_needle_over_decoded_text() -> None:
    """A WIDE NEEDLE MUST STILL FIND DECODED TEXT. CS-964, the seam.

    THE BLINDNESS, stated as the mechanism rather than as a worry. The str
    branch of ``_reaches_the_needle`` asks ``needle.decode("utf-8") in value``.
    Hand it a UTF-16-LE needle and that decode SUCCEEDS - every byte of wide
    ASCII is below 0x80 - and yields the marker's letters each followed by a
    null. No decoded string contains that, so the sweep returns EMPTY and every
    arm downstream reads empty as a pass.

    WHY THAT MATTERS HERE AND NOT ONLY IN THEORY. ``_Cursor.string`` DECODES
    before it binds, so on a wide save the frame local holds the marker's plain
    text while the fixture on disk spells it wide - which is the spelling an arm
    over a wide fixture naturally sweeps with. The oracle would then be blind to
    the one holder family that renders the value legibly.

    THE TWO QUESTIONS ARE DIFFERENT, and that is the fix. A bytes holder holds
    the WIRE spelling and must match byte-exact. A str holder holds DECODED
    TEXT, where the needle's wire encoding is irrelevant to what the holder
    contains. One comparison cannot answer both, and the fences below pin each
    half so the fix cannot be "match more liberally everywhere".
    """
    text = _STRUCTURAL_MARKER
    wide = _STRUCTURAL_MARKER.encode("utf-16-le")
    narrow = _STRUCTURAL_MARKER.encode("utf-8")

    # CONTROL - the subject is real and this helper can see it at all. Without
    # this line a blind oracle and a missing fixture are the same output.
    assert _reaches_the_needle(text, narrow, 0) == [""], (
        "the narrow needle cannot find the marker in plain decoded text, so every "
        "assertion below would be measuring a broken fixture rather than the encoding"
    )
    assert wide != narrow, "the two spellings are the same bytes, so this arm proves nothing"

    # THE CLAIM.
    assert _reaches_the_needle(text, wide, 0) == [""], (
        "the structural sweep is blind to a wide needle over decoded text. On a real "
        "save that text is the session name or the player display name, and an arm "
        "over a wide fixture sweeps with exactly this needle (non-negotiable 12)"
    )

    # THE CLAIM, one attribute hop in - the shape the save layer actually uses.
    assert _reaches_the_needle(_WithholdingHolder(text), wide, 0) == ["._buffer"], (
        "the sweep reaches decoded text held through an attribute only in its narrow spelling"
    )

    # FENCE - the fix must not be "always report a hit". A needle whose text is
    # genuinely absent stays absent at the wide encoding too.
    assert _reaches_the_needle(text, _STRUCTURAL_MARKER_ABSENT.encode("utf-16-le"), 0) == [], (
        "a wide needle for text that is NOT present reports a holder, so the widened "
        "comparison matches anything and no arm built on it measures its own subject"
    )

    # FENCE - the BYTES branch stays byte-exact. A buffer carrying the narrow
    # spelling does not contain the wide one, and widening the str branch must
    # not make the bytes branch decode-tolerant: R2 is why the wide arms exist.
    assert _reaches_the_needle(narrow, wide, 0) == [], (
        "a bytes buffer holding the NARROW spelling was matched by a WIDE needle, so the "
        "bytes branch has gone decode-tolerant and can no longer tell the encodings apart"
    )


def test_the_body_side_encoder_spells_a_string_wide_and_the_reader_reads_it_back() -> None:
    """THE BODY SIDE HAD NO WIDE ENCODER AT ALL. CS-964, the seam.

    ``synthetic.fstring`` grew a ``wide`` flag for the HEADER side, and the body
    side never did: :func:`_fstring` hardcoded ``text.encode("ascii")`` with a
    positive count. It is the encoder for this module, ``test_container_elements``,
    ``test_struct_interior``, ``test_reference_resolution`` and ``test_world``'s
    planted payload - so the whole body half of the population could not be
    driven wide even in principle, whatever an arm's own text claimed.

    That is why this is a seam rather than an arm edit. The acceptance clause
    requires the fixture builders to emit a wide string WITHOUT a second builder
    beside the first, so the existing encoder is taught the spelling and the 56
    positional call sites keep working untouched.

    THE ROUND TRIP IS THE POINT, not the byte shape. An encoder that writes
    something the shipped reader refuses would give every arm built on it a
    refusal for the wrong reason - which is the vacuity this item exists to
    close. So the assertion is that ``objects._payload_text`` reads the wide
    spelling back to the SAME TEXT, measured against the shipped reader rather
    than against this file's idea of the format.
    """
    text = _STRUCTURAL_MARKER
    narrow = _fstring(text)
    wide = _fstring(text, wide=True)

    # CONTROL - the narrow spelling round-trips, so a wide failure below is
    # about the encoding and not about this helper or the reader being broken.
    assert _payload_text_or_fail(narrow, 0)[0] == text, (
        "the narrow spelling does not round-trip, so nothing below measures the wide one"
    )

    # THE WIRE SHAPE. A NEGATIVE count is what makes the reader select
    # utf-16-le, and its magnitude counts CHARACTERS plus the terminator.
    (count,) = struct.unpack_from("<i", wide, 0)
    assert count == -(len(text) + 1), f"the wide count is {count}, not the negative char count"
    assert wide[4:] == text.encode("utf-16-le") + b"\x00\x00", (
        "the wide payload is not utf-16-le followed by a two-byte terminator"
    )

    # THE CLAIM - the shipped reader accepts it and returns the same text.
    assert _payload_text_or_fail(wide, 0)[0] == text, (
        "the shipped body reader does not read the wide spelling back, so every arm "
        "driven wide through this encoder would refuse for the wrong reason"
    )

    # ISOLATION CONTROL - the wide bytes do NOT carry the ASCII spelling. This is
    # what makes an ASCII sweep over them vacuous BY CONSTRUCTION rather than by
    # luck, and it is the property the wide arms are built on.
    assert text.encode("ascii") not in wide, (
        "the wide encoding still carries the ASCII spelling, so it does not isolate "
        "the encoding gap the arms exist to measure"
    )

    # FENCE - THE TWO ENCODERS MUST NOT DRIFT APART ON THE WIDE PATH. This suite
    # already carries two encoders that DISAGREE on the empty string, and neither
    # disagreement is measured. A second divergence is not being added.
    from tests.save import synthetic  # noqa: PLC0415 - local, as the module's other import is

    assert wide == synthetic.fstring(text, wide=True), (
        "the body encoder and the header encoder spell the same wide string differently, "
        "so a fixture's encoding now depends on which helper built it"
    )


def test_the_body_side_encoder_refuses_an_empty_wide_string() -> None:
    """AN EMPTY WIDE STRING IS NOT A THING, AND THE REFUSAL IS LOUD ON PURPOSE.

    ``synthetic.fstring`` returns a bare zero count for empty text ABOVE its own
    wide branch, so ``synthetic.fstring("", wide=True)`` is byte-identical to the
    NARROW empty spelling. Measured in session 80 and re-measured for CS-964.

    That silent fallback is the exact shape of this item's defect: an arm that
    asked for a wide fixture and got a narrow one would measure the encoding it
    was written to stop measuring, and nothing would say so. The body encoder
    therefore REFUSES rather than falling back, so the hazard cannot reach an
    arm quietly.

    The header encoder's own fallback is left alone deliberately - changing it
    is a claim about `synthetic`'s pinned behaviour, not about this seam, and it
    is recorded as its own fence rather than fixed in passing.
    """
    with pytest.raises(ValueError, match="empty"):
        _fstring("", wide=True)

    # The narrow empty string keeps working: 56 call sites rely on it, and this
    # refusal is scoped to the spelling that genuinely has no encoding.
    assert _fstring("") == _i32(1) + b"\x00"


def _frame_holding(value: object) -> FrameType:
    """A frame whose one interesting local IS the value handed in.

    Built from a caught exception's traceback rather than ``inspect`` so this
    helper adds no import, and the module already reads frames this way.

    Args:
        value: The value to bind as a local named ``subject``.

    Returns:
        This function's own frame, with ``subject`` bound.
    """
    subject = value  # noqa: F841 - binding it IS the point
    try:
        raise RuntimeError("frame capture")
    except RuntimeError as error:
        captured = error.__traceback__
        assert captured is not None
        return captured.tb_frame


def test_the_rendering_sweep_is_not_blind_to_a_wide_buffer_in_a_frame_local() -> None:
    r"""A RENDERER PRINTS WIDE BYTES LEGIBLY AND THE ASCII SWEEP SEES NOTHING.

    ``repr()`` of a UTF-16-LE ASCII slice renders the marker's letters each
    followed by an escaped null - ``M\\x00a\\x00r\\x00`` - which a person reads at
    a glance and an ASCII substring search does not find at all. So the frame
    leaks and :func:`_leaking_locals` reports clean, which is an oracle blind to
    its own subject: the shape that passed three arms in session 80.

    THIS IS THE REPR ORACLE, NOT THE STRUCTURAL ONE. The structural sweep asks
    what a frame HOLDS and is already exact about bytes. This asks what a
    traceback PRINTS, and a rendering is exactly where the escaped spelling
    appears. Both oracles are kept - that is settled - so both must be able to
    see the wide spelling in their own terms.
    """
    wide = _STRUCTURAL_MARKER.encode("utf-16-le")
    narrow = _STRUCTURAL_MARKER.encode("utf-8")

    # CONTROL - the sweep finds the NARROW spelling in a frame local, so a wide
    # miss below is about the encoding and not about the helper or the frame.
    assert "subject" in _leaking_locals(_frame_holding(narrow), _STRUCTURAL_MARKER), (
        "the repr sweep cannot see a plain ASCII buffer in a frame local, so nothing "
        "below is measuring the encoding"
    )

    # ISOLATION - the wide rendering genuinely lacks the ASCII spelling, and
    # `isascii()` does NOT rescue it: the escapes are themselves ASCII text.
    rendered = _safe_repr(wide)
    assert _STRUCTURAL_MARKER not in rendered, (
        "the wide rendering already carries the ASCII spelling, so this arm does not "
        "isolate the gap it exists to measure"
    )
    assert rendered.isascii(), "the wide rendering is not ASCII, so an isascii gate would catch it"

    # THE CLAIM.
    assert "subject" in _leaking_locals(_frame_holding(wide), _STRUCTURAL_MARKER), (
        "a frame local RENDERS the wide-encoded marker and the repr sweep reports clean. "
        "On a real save those bytes are the session name or the player display name, "
        "printed legibly by any traceback formatter (non-negotiable 12)"
    )

    # FENCE - the widened oracle must not fire on everything. A frame holding a
    # value with neither spelling in it stays clean.
    assert _leaking_locals(_frame_holding(b"nothing planted here"), _STRUCTURAL_MARKER) == (), (
        "the rendering sweep reports a leak for a local that carries no spelling of the "
        "marker, so it matches anything and no arm built on it measures its subject"
    )


def test_the_splice_helper_swaps_a_narrow_field_for_its_wide_spelling() -> None:
    """PIECE 4 - THE SPLICE, PUBLISHED. CS-964.

    CS-963 spliced a header field to its wide spelling rather than writing a
    second header builder, because a parallel builder is a fixture that can
    drift away from the one every other arm uses - and the acceptance clause
    forbids one by name. That splice was file-local to ``test_header``, and the
    body-side arms need the same operation, so it moves here.

    IT REFUSES TO GUESS. If the narrow field is not in the blob EXACTLY once,
    there is no single place to put the wide one, and a splice that picked the
    first of several would build a fixture nobody could reason about.
    """
    text = _STRUCTURAL_MARKER
    blob = b"head" + _fstring(text) + b"tail"

    spliced = _spliced_wide(blob, text)

    assert spliced.startswith(b"head"), "the splice disturbed the bytes before the field"
    assert spliced.endswith(b"tail"), "the splice disturbed the bytes after the field"
    assert _fstring(text) not in spliced, "the narrow field survived the splice"
    assert _fstring(text, wide=True) in spliced, "the wide field is not in the result"

    # THE ISOLATION PROPERTY every wide arm rests on: the ASCII spelling is
    # genuinely gone, so an ASCII sweep over this blob is vacuous BY
    # CONSTRUCTION rather than by luck.
    assert text.encode("ascii") not in spliced, (
        "the spliced blob still carries the ASCII spelling, so it does not isolate "
        "the encoding gap the arms exist to measure"
    )

    # AND THE SHIPPED READER STILL READS IT - an unparseable fixture would give
    # every arm built on it a refusal for the wrong reason.
    assert _payload_text_or_fail(spliced, len(b"head"))[0] == text, (
        "the shipped body reader cannot read the spliced field back"
    )

    with pytest.raises(AssertionError):
        _spliced_wide(b"no such field here", text)
    with pytest.raises(AssertionError):
        _spliced_wide(blob + _fstring(text), text)


def test_the_observability_control_refuses_a_needle_the_oracles_cannot_see() -> None:
    """PIECE 5 - THE CONTROL EVERY ARM OWES, AND WHAT IT CATCHES. CS-964.

    An arm's empty verdict means "no holder" only if the oracle could have seen
    the value at all. Session 80 shipped THREE arms where it could not, and not
    one was caught by reading - a correct-looking fixture, a sweep that entered
    the wrong frame, and an oracle blind to its subject's spelling all produce
    the same empty output as a clean parser.

    WHAT THIS CATCHES SPECIFICALLY is the trap the item note names: moving the
    marker constant to its wide spelling while the fixture still carries the
    narrow one, which makes an arm VACUOUS rather than wide. The control is
    handed both the text and the needle bytes and asserts they describe the same
    value, so a mismatched pair fails loudly at the top of the arm instead of
    passing silently at the bottom.
    """
    wide = _STRUCTURAL_MARKER.encode("utf-16-le")
    narrow = _STRUCTURAL_MARKER.encode("utf-8")

    # Both real pairings are observable.
    _assert_the_needle_is_observable(_STRUCTURAL_MARKER, narrow)
    _assert_the_needle_is_observable(_STRUCTURAL_MARKER, wide)

    # A needle for a DIFFERENT value is refused - this is the mismatch that
    # would otherwise turn an arm into a measurement of nothing.
    with pytest.raises(AssertionError):
        _assert_the_needle_is_observable(
            _STRUCTURAL_MARKER, _STRUCTURAL_MARKER_ABSENT.encode("utf-16-le")
        )


def test_the_structural_sweep_terminates_on_a_reference_cycle() -> None:
    """A CYCLE MUST NOT HANG THE SWEEP, for the reason the walker's twin gives."""
    first = _WithholdingHolder(b"nothing")
    second = _WithholdingHolder(_STRUCTURAL_MARKER.encode("ascii"))
    first._buffer = second  # type: ignore[assignment]  # noqa: SLF001 - building the cycle
    second._buffer = first  # type: ignore[assignment]  # noqa: SLF001

    assert _reaches_the_needle(first, b"unreachable-now", 0) == []


def test_the_structural_sweep_does_not_go_blind_when_a_deep_path_is_walked_first() -> None:
    """F4 - THE FALSE CLEAN, pinned so it cannot come back.

    ``seen`` used to be a flat identity set. A value first reached AT the depth
    boundary went into it, its children were then cut off by the boundary, and a
    SHALLOWER path to the same value afterwards hit the set and returned
    nothing. The sweep came back EMPTY with the needle two hops down - and every
    arm here reads an empty verdict as a pass.

    THE ORDER IS THE FIXTURE. Attribute iteration follows insertion order, so
    the long chain is bound first and the short one second, which is exactly the
    order that used to poison the result. Asserting the SHORT path is found is
    what makes this a measurement rather than a restatement of the fix.
    """
    buffer = _STRUCTURAL_MARKER.encode("ascii")
    holder = _WithholdingHolder(buffer)

    # THE CHAIN LENGTH IS THE FIXTURE AND IT IS EXACT. The bug only fires when
    # the holder is first reached AT the boundary: one hop shallower and its
    # child is still walked, one deeper and the holder is never recorded at all.
    # Measured against a standalone copy of the old walker - at this length it
    # returns nothing, at every neighbouring length it returns a path. A control
    # that passed under the old walker too would pin nothing.
    deep: object = holder
    for _ in range(_STRUCTURAL_DEPTH - 1):
        deep = _WithholdingHolder(deep)  # type: ignore[arg-type]

    class _TwoWays:
        def __init__(self) -> None:
            self.a_deep = deep
            self.z_short = holder

        def __repr__(self) -> str:
            return "<_TwoWays>"

    found = _reaches_the_needle(_TwoWays(), buffer, 0)
    assert ".z_short._buffer" in found, (
        "the sweep missed the SHALLOW path to a buffer it had already reached deeply and "
        f"truncated. That is an empty verdict about a live holder, which reads as a pass "
        f"everywhere it is used. Paths found: {found}"
    )
