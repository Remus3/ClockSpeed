"""What is and is not known about the grammar INSIDE one property payload.

WHAT CHANGED, AND WHAT DELIBERATELY DID NOT
---------------------------------------------
This module once existed to hold a measurement that was NOT shipped. The
measurement has now shipped: the tag grammar lives in
``clockspeed/save/objects.py`` as production code, and ``read_properties``
returns decoded values for the types whose encoding was measured. A grammar
that lives only in a test file cannot be used by ``world.py``, which was the
point of the item.

WHAT DID NOT CHANGE IS THE LIMIT. The walk is TERMINATOR-exact and still not
BOUNDARY-exact - a variable trailing run follows the terminator on every
payload in the library - and save version 60 still refuses this grammar
outright. Both are asserted below rather than described, because a comment
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

import ast
import re
import struct
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import FrameType, MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects, usmap

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
    """The NEGATIVE result, pinned so nobody interpolates a fourth pair.

    ADR 0005's refuted arithmetic route is exactly this shape: three measured
    neighbours make the fourth look derivable. It is not - save 60 reaches a
    terminator on no payload at all, and a single leading byte accounts for
    some of the gap and nothing like all of it. Pinning the refusal is what
    keeps a later slice from closing it by resemblance.

    The zero here is guarded by :func:`_assert_walker_is_live`, without which
    it also passes when the walker reaches a terminator on NOTHING at all.
    """
    sweep = _sweep_or_skip()
    _assert_walker_is_live(sweep)
    if UNMEASURED_PAIR not in sweep.payloads:
        pytest.skip("no save of the unmeasured pair on this machine")

    assert sweep.walked.get(UNMEASURED_PAIR, 0) == 0, (
        f"pair {UNMEASURED_PAIR} now reaches a terminator on "
        f"{sweep.walked.get(UNMEASURED_PAIR, 0)} payloads; if that is real it is a "
        "measurement worth making properly rather than a reason to relax this test"
    )


def test_the_run_after_the_terminator_is_unmeasured() -> None:
    """THE HONESTY CONTROL, and the reason this module is not a closed result.

    Reaching the terminator is NOT reaching the payload's final byte. A
    variable trailing run follows it whose grammar nobody here has measured, so
    this asserts that the walk is terminator-exact and is NOT boundary-exact.

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
_MEASURED_VALUE_TYPES: Final = frozenset(
    {
        "BoolProperty",
        "ByteProperty",
        "EnumProperty",
        "FloatProperty",
        "Int8Property",
        "IntProperty",
        "NameProperty",
        "ObjectProperty",
        "SoftObjectProperty",
        "StrProperty",
        "UInt32Property",
    }
)

#: How a building's class path is recognised in a type path.
_BUILDING_MARKERS: Final = (".Build_", "/Build_")

#: An object reference decodes to a level name and an object path.
_OBJECT_REFERENCE_PARTS: Final = 2


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

    The measured types yield exactly four Python shapes: ``bool`` from
    BoolProperty, ``int`` from the integer widths and a raw ByteProperty,
    ``float`` from FloatProperty, ``str`` from the one-string types, and a
    2-tuple of ``str`` from the object references. Anything else means a
    decoder returned something no measured branch can produce.

    Args:
        value: One decoded property value.

    Returns:
        True when the shape is one a measured type produces.
    """
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
    reason the walk is terminator-exact rather than boundary-exact.

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

#: How many tags of an UNMEASURED type the fixture payload carries. Named so
#: the expected warning count is not a bare literal in three assertions.
_SYNTHETIC_UNMEASURED_TAGS: Final = 2

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


def _fstring(text: str) -> bytes:
    """Encode one length-prefixed UTF-8 string, its NUL terminator included.

    Args:
        text: ASCII text.

    Returns:
        The prefix and the bytes, in the shape ``objects._payload_text`` reads.
    """
    raw = text.encode("ascii") + b"\x00"
    return _i32(len(raw)) + raw


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


def _array_tag(name: str, inner_word: str, opaque: bytes) -> bytes:
    """An UNMEASURED ArrayProperty, present for the same reason.

    Args:
        name: The property name.
        inner_word: The element type word, carried in the tag data.
        opaque: The elements, which this project does not read.

    Returns:
        The whole tag.
    """
    return _tag_head(name, "ArrayProperty", len(opaque), _fstring(inner_word)) + opaque


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
)

#: The two UNMEASURED regions the fixture carries, so "flagged and skipped" is
#: exercised rather than described.
_UNMEASURED_TAGS: Final = (
    _struct_tag("mSyntheticStruct", _SYNTHETIC_STRUCT_WORD, bytes(range(32))),
    _array_tag("mSyntheticArray", _SYNTHETIC_ARRAY_INNER, _i32(2) + _i32(7) + _i32(9)),
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

    assert dict(result.properties) == dict(_EXPECTED_PROPERTIES)
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

    assert dict(result.properties) == dict(_EXPECTED_PROPERTIES)


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

    The two unmeasured tags are stepped over by their DECLARED size, so their
    presence must cost the walk nothing and must be counted rather than guessed.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload)
    record = _synthetic_record(payload)

    result = objects.read_properties(body, record, _synthetic_map(_SYNTHETIC_SCHEMA))

    assert result.unmeasured_value_count == _SYNTHETIC_UNMEASURED_TAGS
    assert "mSyntheticStruct" not in result.properties
    assert "mSyntheticArray" not in result.properties
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
    assert dict(with_run.properties) == dict(_EXPECTED_PROPERTIES)


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
    assert dict(result.properties) == dict(_EXPECTED_PROPERTIES)
    assert objects.WARN_UNRESOLVED_SCHEMA in [warning.code for warning in result.warnings]


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

    assert dict(result.properties) == dict(_EXPECTED_PROPERTIES)


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


def _leaking_locals(frame: FrameType, marker: str) -> tuple[str, ...]:
    """Names in one frame whose RENDERING carries the marker.

    Rendering is the oracle rather than identity, because that is exactly what
    a traceback formatter showing locals prints.

    Args:
        frame: The frame to inspect.
        marker: The planted marker.

    Returns:
        The offending local names.
    """
    return tuple(name for name, value in frame.f_locals.items() if marker in _safe_repr(value))


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


def _raise_through(entry_point: str, body: bytes, record: objects.ObjectRecord) -> BaseException:
    """Call one exported reader with an out-of-range extent and return the error.

    Args:
        entry_point: The name of the reader, from :data:`_PROPERTY_READERS`.
        body: The synthetic body.
        record: A record whose declared extent runs past it.

    Returns:
        The raised exception, so the caller can walk its traceback.
    """
    reader = getattr(objects, entry_point)
    with pytest.raises(objects.ObjectTruncatedError) as caught:
        reader(body, record, _synthetic_map())
    return caught.value


@pytest.mark.parametrize("entry_point", _PROPERTY_READERS)
def test_no_clockspeed_frame_holds_the_body_when_the_extent_raises(entry_point: str) -> None:
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

    Args:
        entry_point: The exported reader under test.
    """
    payload = _synthetic_payload(actor=True)
    body = _synthetic_body(payload) + _LEAK_MARKER.encode("ascii")
    overrun = _synthetic_record(payload, body_length=len(body))

    raised = _raise_through(entry_point, body, overrun)

    leaks = {
        frame.f_code.co_name: _leaking_locals(frame, _LEAK_MARKER)
        for frame in _frames_beneath_the_caller(raised)
        if _leaking_locals(frame, _LEAK_MARKER)
    }
    assert not leaks, (
        f"entered through objects.{entry_point}, a clockspeed frame in the raised "
        "traceback still holds the save body. A renderer showing locals prints it "
        "verbatim, head and tail (non-negotiable 12). Offending frame(s) and local "
        f"name(s): {leaks}"
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

    assert dict(decoded) == dict(_EXPECTED_PROPERTIES), (
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
# The library-reach guard, owned here and consumed by the sibling modules
# ---------------------------------------------------------------------------

#: Attribute names through which a function can come to hold a REAL save path
#: or the REAL account directory.
#:
#: KEYED ON THE RISKY PRIMITIVES, NEVER ON THE CONTAINED ROUTE. An earlier
#: version of this guard keyed on ``_library_save_paths`` alone - the SAFE
#: route - so a function using the raw locators never entered the flagged set
#: and both the subset and the equality assertion stayed true. It detected safe
#: functions and was blind to unsafe ones, which is the inversion
#: ``test_the_guard_catches_a_spliced_uncontained_helper`` in each consuming
#: module now forces.
#:
#: ``glob`` and ``read_bytes`` are included even though neither yields a real
#: path on its own. Their whole cost is the ``_EXEMPT_LIBRARY_REACH`` map in each
#: consuming module, and that map is asserted LIVE - every exemption must still
#: touch a primitive - so the price is visible in the tree rather than argued for
#: here, and it cannot rot into a silent allowance. ``rglob`` and ``read_text``
#: are NOT included: they flag repo-source reads and ``tmp_path`` walks that no
#: discovery primitive feeds.
_LIBRARY_PRIMITIVES: Final = (
    "resolve_save_root",
    "resolve_account_dir",
    "latest_save",
    "_library_save_paths",
    "glob",
    "read_bytes",
)


def _module_scope_functions(module_path: Path) -> dict[str, ast.FunctionDef]:
    """Every module-scope function in a file, by name.

    Args:
        module_path: The file to parse.

    Returns:
        The functions, keyed by name.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _calls_any(node: ast.FunctionDef, names: frozenset[str]) -> bool:
    """Whether a function calls any of the named attributes or bare names.

    Args:
        node: The function.
        names: The names to look for.

    Returns:
        True when at least one call matches.
    """
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        func = inner.func
        if isinstance(func, ast.Attribute) and func.attr in names:
            return True
        if isinstance(func, ast.Name) and func.id in names:
            return True
    return False


def _returns_personal_data(node: ast.FunctionDef) -> bool:
    """Whether a function's RETURN ANNOTATION carries a path or save bytes.

    Derived from the annotation rather than declared in a second list, so the
    set cannot drift from the signatures it describes. A helper returning a
    ``Path`` hands its caller the account directory; one returning ``bytes``
    hands it a save body. A helper returning a counts-only sweep or a tuple of
    scalars hands over nothing personal, so its callers are not reach sites.

    Args:
        node: The function.

    Returns:
        True when the annotation mentions ``Path`` or ``bytes``.
    """
    if node.returns is None:
        return False
    rendered = ast.unparse(node.returns)
    return "Path" in rendered or "bytes" in rendered


def _assert_library_reach_is_declared(
    module_path: Path, *, graded: Mapping[str, str], exempt: Mapping[str, str]
) -> None:
    """Assert every function in a module that can hold a real save path is declared.

    Two ways a function comes to hold one, and both are checked, because the
    first alone missed a helper that took its path from a sibling rather than
    from a primitive:

    - DIRECTLY, by calling one of :data:`_LIBRARY_PRIMITIVES`.
    - INDIRECTLY, by calling a declared helper whose return annotation carries a
      path or save bytes, per :func:`_returns_personal_data`. Test functions are
      included in this half: a test holding a real body is a reach site whatever
      it is called.

    Args:
        module_path: The consuming module's own file.
        graded: Helper name to the reason it reaches the library. Each has a
            containment grader in the consuming module that forces a failure
            through it.
        exempt: Function name to the reason it reaches or touches WITHOUT being
            grader-able - a test function rather than a helper, or a primitive
            applied to something that is not the real library. Asserted still
            reaching, so an exemption cannot outlive the code it describes.
    """
    functions = _module_scope_functions(module_path)
    primitives = frozenset(_LIBRARY_PRIMITIVES)
    declared_names = frozenset(graded) | frozenset(exempt)

    direct = frozenset(name for name, node in functions.items() if _calls_any(node, primitives))
    propagating = frozenset(
        name for name in graded if name in functions and _returns_personal_data(functions[name])
    )
    indirect = frozenset(name for name, node in functions.items() if _calls_any(node, propagating))

    assert direct, "no function here touches a library primitive, so the guard is vacuous"
    assert direct <= declared_names, (
        f"undeclared functions touch a library primitive: {sorted(direct - declared_names)}"
    )
    assert indirect <= declared_names, (
        f"undeclared functions take a save path from a graded helper: "
        f"{sorted(indirect - declared_names)}"
    )
    assert declared_names <= frozenset(functions), (
        f"a declaration names a function that no longer exists: "
        f"{sorted(declared_names - frozenset(functions))}"
    )
    assert frozenset(graded) <= direct | indirect, (
        f"a graded helper no longer reaches the library: "
        f"{sorted(frozenset(graded) - (direct | indirect))}"
    )
    assert frozenset(exempt) <= direct | indirect, (
        f"an exemption outlived the code it describes: "
        f"{sorted(frozenset(exempt) - (direct | indirect))}"
    )


#: This module's own library-reaching helpers, name to why it reaches.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_library_save_paths": "holds the locators and the save glob",
        "_sweep_payload_tags": "reads every save in the library",
        "_sweep_decoded_values": "reads every save in the library",
    }
)

#: Functions that touch a primitive WITHOUT consuming a real path, name to why.
_EXEMPT_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_assert_every_sweep_declines": (
            "a grader, not a consumer: it calls the contained discovery inside "
            "_contained_call and reduces the result to an integer before asserting"
        ),
    }
)


def test_every_library_reaching_function_here_is_declared() -> None:
    """This module guards itself with the guard it lends its siblings.

    It owns :func:`_assert_library_reach_is_declared`, and a guard whose owner
    is outside its own scope is the arrangement that let a third sweep ship
    ungraded one file over.
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
