"""What is and is not known about the grammar INSIDE one property payload.

WHY THIS MODULE EXISTS AT ALL, AND WHY IT SHIPS NO DECODER
------------------------------------------------------------
CS-413 located and attributed every payload in every real save, which is the
seam ``clockspeed/save/objects.py`` now populates. The layer above that - what
the bytes INSIDE a payload mean - was measured far enough to be worth keeping
and NOT far enough to ship, and the gap between those two states is exactly the
thing a project loses when a measurement lives only in a session transcript. A
prior session recorded that a preamble "is measured" and recorded the
measurement nowhere, and the next slice paid for the re-derivation.

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
3. **Any property VALUE.** Nothing here decodes one, and nothing here is wired
   into ``clockspeed/save/``.

PRIVACY. A payload is world content, so every helper below RETURNS on failure
rather than raising - pytest renders the arguments of every frame in a failing
traceback, and the cheapest way to guarantee no body reaches a log is to have no
failure path that unwinds through a frame holding one.

**Counts only come out, and that is now structural rather than argued.** The
sweep returns integers; it holds no decoded string to return. The first
revision of this module DID return the distinct property type words, defended
as format vocabulary rather than world content - which is true exactly while
the walk is synchronised, and false in the one case the assertion using them
fires in. An adversary measured it: misaligned by one record across this
library, the walk yields a word that is not a type word at all. The words are
now judged inside the sweep and only the counts leave it.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects

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


def _read_one_tag(body: bytes, at: int, end: int) -> tuple[int, str] | None:
    """Read one tag past its name, value included.

    Args:
        body: The decompressed body.
        at: Just past the tag's name.
        end: The first byte past the payload.

    Returns:
        The offset after the value and the type word, or None if it breaks.
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
    return (nxt + size, type_word)


def _walk_tags(body: bytes, at: int, end: int, seen: set[str]) -> int | None:
    """Walk property tags to the ``None`` terminator.

    Args:
        body: The decompressed body.
        at: Where the first tag begins.
        end: The first byte past the payload.
        seen: Accumulator for the type words encountered.

    Returns:
        The offset just past the terminator, or None if the walk breaks.
    """
    for _ in range(_TAG_CAP):
        name = _text(body, at, end)
        if name is None:
            return None
        if name[0] == "None":
            return name[1]
        tag = _read_one_tag(body, name[1], end)
        if tag is None:
            return None
        at, type_word = tag
        seen.add(type_word)
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
        failures: Exception type names from any save that did not walk.
    """

    payloads: Mapping[tuple[int, int], int]
    walked: Mapping[tuple[int, int], int]
    exact: Mapping[tuple[int, int], int]
    distinct_type_words: int
    malformed_type_words: int
    failures: tuple[str, ...]


def _sweep_payload_tags() -> _TagSweep | None:
    """Walk every payload of every real save and return COUNTS ONLY.

    Contained as ``test_objects._sweep_the_real_library`` is: every step
    wrapped, every failure reduced to a type NAME inside this helper before it
    can reach a frame anyone renders, and never a path, a body or a decoded
    world string out.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root) if root is not None else None
    if account is None:
        return None

    payloads: dict[tuple[int, int], int] = {}
    walked: dict[tuple[int, int], int] = {}
    exact: dict[tuple[int, int], int] = {}
    words: set[str] = set()
    failures: list[str] = []
    for path in sorted(account.glob("*.sav")):
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
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
                landed = _walk_tags(body, start, end, words)
                if landed is None:
                    continue
                walked[pair] = walked.get(pair, 0) + 1
                if landed == end:
                    exact[pair] = exact.get(pair, 0) + 1
        except Exception as exc:
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
