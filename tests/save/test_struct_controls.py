"""The struct-grade controls that degrade a shipped READING - CS-829.

WHY THESE SIT BESIDE THE MODULE THEY GRADE RATHER THAN INSIDE IT. They were
written in ``tests/save/test_struct_interior.py`` and were moved out whole when
that file crossed the 262144-byte ceiling
``tests/data/test_phase2_gate.py::test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data``
holds over this directory. That ceiling is what stands between this repo and a
slice of real game data committed as hand-authored material, so the file moved
and the bound did not. Each body below is the body it was; the sweep these
controls degrade, and the corpus helpers they share with the control that
stayed, are imported from next door.

WHAT AN ANTI-MONOTONE CONTROL IS FOR. The equalities next door compare two
readings of the same bytes, and an equality of that shape is satisfied just as
well by BOTH sides losing the same records. So a control degrades one side on
purpose and requires the grade to get no better for it. A degradation that
leaves every arm green, or that improves the grade, says the equality was
measuring the population rather than the reading.

THESE TWO DEGRADE A READING AND THE THIRD DOES NOT, which is why the third one
stayed where it is. :class:`_EarlyTerminator` degrades a shipped READER and
:func:`_degrade_one_record` degrades the shipped record table's OUTPUT; both
separate the two readings, which is what lets either go red. The shared-scalar
control, ``test_a_stricter_shared_ceiling_cannot_improve_this_modules_grade``,
degrades a constant BOTH readings consult, separates nothing, and is still in
``tests/save/test_struct_interior.py`` beside the sweep it reads.

BOTH PLANTS ARE APPLIED IN PROCESS AND NEVER ON DISK, for the reason
:class:`_EarlyTerminator` states: the harness Bash timeout KILLS rather than
unwinds, so a ``finally`` that would restore a mutated file never runs.

COUNTS ONLY LEAVE THIS MODULE, on the terms the sibling states for itself. No
assertion message here renders a struct word, a property name, a decoded value,
a path, a world name or an account id.

THE LIBRARY IS REACHED THROUGH THE SIBLING'S OWN GUARD. The arms that need a
corpus open with ``_sweep_or_skip``, so the line between a skip and a red is
drawn in one place for this module and for the one next door alike.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects
from tests.save import independent_table, reach_guard, test_properties
from tests.save.test_struct_interior import (
    _POPULATION_EVIDENCE_DESTROYED,
    _POPULATION_GRADED,
    _POPULATION_GRAMMAR_SET_ASIDE,
    _POPULATION_NO_RECORD,
    _POPULATION_NO_STRUCT_IN_BYTES,
    _census_hits,
    _classify_graded_population,
    _corpus_line,
    _grade_the_pair_this_module_can_read,
    _independent_sites_of,
    _shipped_sites_of,
    _sweep_or_skip,
    _the_second_reading_implements,
)


@dataclass
class _EarlyTerminator:
    """A shipped tag-list degradation applied IN PROCESS and never on disk.

    IT IS THE MUTANT THE THIRD REFUTATION MEASURED, in the class that every arm
    this module carried was blind to. Claiming a tag NAME is the payload
    terminator makes the shipped walk CLOSE EARLY: the record is still
    ACCEPTED, its later tags are never enumerated, and ``objects._walk_payload``
    behind ``read_properties`` closes at the very same byte because both consume
    this one verdict. So ``sites_seen`` and ``shipped_tags`` fall together, the
    cross-check between them stays green, ``head_unread``, ``partial_saves``,
    ``contested_pairs`` and ``census_unreached`` do not move, and the residue
    gets SMALLER - the check improving as the reader gets worse.

    IN PROCESS RATHER THAN ON DISK, and that is not a preference. The harness
    Bash tool's timeout KILLS rather than unwinds, so a ``finally`` that would
    restore a mutated file never runs and the mutation survives to poison every
    later measurement in the session.

    Attributes:
        original: The shipped reader, called for every read.
        armed: Whether the degradation is currently active.
        fired: How many reads it actually altered - a COUNT, because a mutant
            that never applied and one that survived produce identical output.
    """

    original: Callable[[bytes, int, int], tuple[str, int] | None]
    armed: bool = False
    fired: int = 0

    def __call__(self, body: bytes, at: int, end: int) -> tuple[str, int] | None:
        """Read one string, sometimes claiming it is the payload terminator.

        Args:
            body: The decompressed body.
            at: Where the length prefix starts.
            end: The first byte past this payload.

        Returns:
            What the shipped reader returned, or a terminator verdict in its
            place.
        """
        read = self.original(body, at, end)
        if read is None or not self.armed:
            return read
        if read[0] == objects._PAYLOAD_TERMINATOR or at % _CONTROL_MODULUS:  # noqa: SLF001
            return read
        self.fired += 1
        return (objects._PAYLOAD_TERMINATOR, read[1])  # noqa: SLF001


#: Which string offsets the control degrades. A BOUND ON HOW OFTEN THE MUTANT
#: FIRES, not a measurement of anything: any modulus exercises the same loss
#: class, and the arm asserts the firing count rather than assuming it.
_CONTROL_MODULUS: Final = 16


@dataclass
class _ControlCounts:
    """What the degradation control observed. COUNTS ONLY.

    Attributes:
        records: Records measured under both readings.
        pristine_sites: Struct sites the shipped walk reached undegraded.
        degraded_sites: The same under the degradation.
        independent_pristine: Struct sites this module's own reading found
            while the degradation was disarmed.
        independent_degraded: The same while it was armed - it must not move,
            which is the entire claim.
        pristine_reached: Records the shipped walk enumerated undegraded.
        degraded_reached: The same under the degradation.
        still_accepted: Records the shipped walk enumerated BOTH times.
        lost_in_still_accepted: Sites deleted from records that stayed
            accepted. THE LOSS CLASS every other arm here is blind to.
    """

    records: int = 0
    pristine_sites: int = 0
    degraded_sites: int = 0
    independent_pristine: int = 0
    independent_degraded: int = 0
    pristine_reached: int = 0
    degraded_reached: int = 0
    still_accepted: int = 0
    lost_in_still_accepted: int = 0


def _run_degradation_control(probe: _EarlyTerminator) -> _ControlCounts | None:
    """Measure every record twice, with the degradation disarmed and armed.

    EACH SAVE IS READ ONCE AND MEASURED TWICE. The operator plays this game
    while a session runs, so re-reading the library between the two passes
    would race a real autosave and report the difference as a defect.

    Args:
        probe: The installed degradation, armed and disarmed around each pass.

    Returns:
        The counts, or None when no save library is reachable.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    counts = _ControlCounts()
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            # INSIDE THE HANDLER BECAUSE `body` IS LIVE IN THIS FRAME. It used
            # to sit after it, and pytest renders the arguments of the first
            # and the deepest traceback frame with no opt-in flag, so a raise
            # out there put real save bytes into a transcript.
            mine = independent_table.independent_records(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        if mine is None or len(mine) != len(table.records):
            continue
        for index, record in enumerate(table.records):
            end = record.body_offset + record.body_length
            own_record = mine[index]
            counts.records += 1
            probe.armed = False
            pristine_ok, pristine = _shipped_sites_of(body, record, end)
            _own_ok, own_pristine = _independent_sites_of(body, own_record)
            probe.armed = True
            degraded_ok, degraded = _shipped_sites_of(body, record, end)
            _own_degraded_ok, own_degraded = _independent_sites_of(body, own_record)
            probe.armed = False
            counts.pristine_sites += pristine
            counts.degraded_sites += degraded
            counts.independent_pristine += own_pristine
            counts.independent_degraded += own_degraded
            counts.pristine_reached += pristine_ok
            counts.degraded_reached += degraded_ok
            if pristine_ok and degraded_ok:
                counts.still_accepted += 1
                counts.lost_in_still_accepted += max(pristine - degraded, 0)
    return counts


def test_degrading_the_shipped_tag_reader_cannot_improve_this_modules_grade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE ANTI-MONOTONE CONTROL - the check must get WORSE when the reader does.

    THE HEADLINE FINDING THAT KEPT CS-829 OPEN was that this module's grade
    IMPROVED as the shipped reader was degraded, three times, at three different
    functions, each time after a repair at the previous one. A green run is
    worth nothing until something asserts that direction, so this asserts it
    directly rather than arguing it.

    FOUR THINGS ARE ASSERTED, because a mutant that NEVER APPLIED and one that
    SURVIVED produce identical output: that the patch LANDED, that it FIRED with
    a count, that the pristine floor was measured BEFORE it was armed, and that
    the revert LANDED.

    WHAT THE DEGRADATION DOES AND WHY IT IS THE RIGHT ONE. See
    :class:`_EarlyTerminator`: it leaves records ACCEPTED and deletes tags from
    inside them, which is the one loss class every shape guard, every cross-check
    against ``read_properties`` and every census in this module is blind to,
    because both walks consume the one verdict it moves.

    NO EVIDENCE IS A SKIP AND THAT IS WHY THIS OPENS WITH THE SWEEP GUARD. This
    arm used to reach the library through :func:`_run_degradation_control`
    alone, which skips only when there is no library AT ALL - so on a library
    holding nothing but saves of a version pair this project does not parse it
    went RED at ``pristine_sites > 0`` while seventeen sibling arms SKIPPED on
    the identical corpus, for the identical reason, through
    :func:`_sweep_or_skip`. Measured on this machine: every single save of one
    of the four version pairs present reddens three arms that bypass that guard
    and none of the seventeen that use it. Autosave rotation alone reaches that
    state, so the guard is shared rather than re-derived here.

    THE THREE SKIPS BELOW ARE INGREDIENTS, NOT OUTCOMES. Each names a thing the
    control needs before its comparison means anything - a record to measure, a
    site to take away, and a record that stayed accepted while losing one - and
    none of them is derived from which corpora were observed failing, which
    would be the fitted-proof defect one level up.
    """
    _sweep_or_skip()

    original = objects._payload_text  # noqa: SLF001
    probe = _EarlyTerminator(original=original)
    monkeypatch.setattr(objects, "_payload_text", probe)
    assert objects._payload_text is probe, (  # noqa: SLF001
        "the degradation was not installed, so everything measured below is the "
        "pristine reader twice and this control proves nothing"
    )

    counts = _run_degradation_control(probe)

    # THE REVERT IS ASSERTED BEFORE ANY SKIP CAN LEAVE, and the ordering is the
    # repair rather than a tidy-up. Every guard below is a skip, and a skip taken
    # while the module is still patched would leave the fourth of the four
    # mutation assertions - that the revert LANDED - unrun on exactly the corpora
    # that take it. The fixture's own teardown would still restore the reader;
    # what would be lost is the check that says so.
    monkeypatch.undo()
    assert objects._payload_text is original, (  # noqa: SLF001
        "the shipped reader was NOT restored, so every later measurement in this "
        "process is taken against a degraded module"
    )

    if counts is None:
        pytest.skip("no save library on this machine - the control has nothing to degrade")
    if counts.records == 0:
        pytest.skip(
            "no save this run read parses into a record table, so the control "
            "measured no record at all and a degradation has nothing to cost"
        )

    assert probe.fired > 0, (
        "the degradation never altered a single read. A mutant that did not apply and "
        "one that survived produce the same output, so this run says nothing about "
        "whether the arms above can see reader loss. THIS STAYS AN ASSERTION rather "
        "than joining the skips below: its population is the reads taken while the "
        "patch was armed, and the guard above has already established that records "
        "were measured, so a zero here is the patch being inert and not an absent "
        "corpus"
    )

    if counts.pristine_sites == 0:
        pytest.skip(
            "the undegraded reader found no struct site in the records this run read, "
            "so there is nothing for the degradation to take away and a fall below "
            "would measure an absent population rather than a loss"
        )
    if counts.lost_in_still_accepted == 0:
        pytest.skip(
            f"the degradation fired {probe.fired} times and deleted no struct site "
            "from a record that stayed ACCEPTED, so the one loss class this control "
            "exists to exercise is absent from the saves this run read. Either every "
            "degraded record here was refused outright - which other arms catch - or "
            "this corpus is too small to hold one, and nothing measured in a single "
            "run separates those two"
        )

    assert counts.independent_degraded == counts.independent_pristine, (
        f"this module's own reading found {counts.independent_pristine} struct sites "
        f"undegraded and {counts.independent_degraded} with the shipped reader "
        "degraded. IT MUST NOT MOVE: it is the denominator precisely because it takes "
        "nothing from the shipped module but constants, and if a shipped patch can "
        "move it then the equality above is two views of one reader again"
    )

    assert counts.degraded_sites < counts.pristine_sites, (
        f"the degraded shipped walk reached {counts.degraded_sites} struct sites where "
        f"the pristine one reached {counts.pristine_sites}. The degradation did not "
        "cost the shipped reader anything measurable, so this control is not "
        "exercising the direction it claims to"
    )
    assert counts.degraded_sites < counts.independent_degraded, (
        f"the shipped walk lost sites under degradation and the equality still holds "
        f"at {counts.degraded_sites} against {counts.independent_degraded}. THE CHECK "
        "IS STILL ANTI-MONOTONE: the population shrank with the reader instead of the "
        "grade going red, which is the exact shape that refuted this item three times"
    )


# ---------------------------------------------------------------------------
# THE SECOND ANTI-MONOTONE CONTROL - the RECORD TABLE, not the tag reader
#
# WHAT THE FIRST CONTROL CANNOT SEE. ``_EarlyTerminator`` degrades
# ``objects._payload_text``, which the shipped walk calls and this module's own
# reading does not, so the two SEPARATE under it and the equality can go red.
# THE RECORD TABLE IS THE SUBSTRATE THEY STILL SHARE: ``_sweep_one_record``
# takes ``record.body_offset``, ``record.body_length`` and ``record.kind`` off
# the same table for the independent reading as for the shipped one, so a defect
# THERE moves the numerator and the denominator by the same amount and reddens
# nothing.
#
# THE DEGRADATION IS APPLIED TO THE TABLE'S OUTPUT AND NEVER BY MONKEYPATCH.
# The degraded records are built in memory from the pristine ones, so nothing
# shipped is patched, there is no revert to assert and none to miss, and the
# harness Bash timeout - which KILLS rather than unwinds - has nothing to leave
# behind. That is the safer half of a trade the first control cannot make,
# because a tag reader has no output object to rewrite.
# ---------------------------------------------------------------------------


#: How far a degraded payload's first byte moves. ONE BYTE, because the point is
#: a start BOTH readings take together, not a start so wrong that only a bounds
#: check is being exercised. It is a constant rather than a literal so no
#: comparison below reads as a magic number.
_TABLE_CONTROL_SHIFT: Final = 1


def _degrade_one_record(record: objects.ObjectRecord) -> objects.ObjectRecord | None:
    """Relabel an actor and move the payload start, holding the extent END.

    THIS IS THE DEGRADATION THE SESSION-40 ADVERSARY RECORDED. A record's KIND
    selects which of two payload starts a reading takes - an actor's head is
    skipped, a component's is not - and its extent says where the payload lies.
    Both readings in this module take all three fields off the same record, so
    moving them moves the two site totals TOGETHER: a large share of the
    corpus's struct sites left the population, every arm stayed green and the
    residue IMPROVED. The share is re-measured by the arm below rather than
    transcribed here, because a number written into prose is a number that rots.

    THE END IS HELD RATHER THAN SHIFTED. A start and a length that both move
    keep the payload the same width, which a bounds check could notice; holding
    the end makes the degraded extent a strictly narrower window inside the real
    one, so no reading here reaches a byte the pristine record did not own.

    ``with_payload`` does the shift rather than ``dataclasses.replace``, for the
    reason given at
    :meth:`clockspeed.save.objects.ObjectRecord.with_payload` - ADR 0007's write
    gate scans for the NAME ``replace``. The relabel builds the record directly,
    because no shipped method changes a record's kind and this module does not
    add one.

    Args:
        record: The pristine record. It is frozen and is not mutated.

    Returns:
        The degraded record, or None when the payload is too short to shift -
        which is NOT a degradation and must never be counted as one.
    """
    if record.body_length < _TABLE_CONTROL_SHIFT:
        return None
    offset = record.body_offset + _TABLE_CONTROL_SHIFT
    length = record.body_length - _TABLE_CONTROL_SHIFT
    if record.kind != objects.KIND_ACTOR:
        return record.with_payload(offset, length)
    return objects.ObjectRecord(
        kind=objects.KIND_COMPONENT,
        type_path=record.type_path,
        root_object=record.root_object,
        instance_name=record.instance_name,
        transform=record.transform,
        parent=record.parent,
        object_type=record.object_type,
        was_placed_in_level=record.was_placed_in_level,
        body_offset=offset,
        body_length=length,
    )


@dataclass
class _TableReading:
    """What both readings found over ONE presentation of a record population.

    COUNTS ONLY. Every field is an integer, so the generated repr is countable
    output on the same terms as :class:`_ControlCounts` - no offset, no extent,
    no version pair and no string reaches it.

    Attributes:
        shipped_sites: Struct sites the SHIPPED walk reached.
        independent_sites: Struct sites THIS MODULE'S own reading reached.
        shipped_reached: Records the shipped walk enumerated.
        independent_reached: Records this module's own reading enumerated.
    """

    shipped_sites: int = 0
    independent_sites: int = 0
    shipped_reached: int = 0
    independent_reached: int = 0

    def add(
        self, body: bytes, record: objects.ObjectRecord, own: independent_table.IndependentRecord
    ) -> None:
        """Fold one record in - the shipped reading from ``record``, ours from ``own``.

        THAT SEPARATION IS THE WHOLE MECHANISM, and it is what the arm below
        grades. ``record`` is the shipped table's and is the thing degraded;
        ``own`` is the second reading's record for the same position and is
        taken from the BODY, so the degradation cannot reach it. If the
        independent total still moves, the two are one reading wearing two
        names. Before CS-829 round 5 both arguments were the same object and it
        moved every time.

        Args:
            body: The decompressed body.
            record: The shipped record to measure, pristine or degraded.
            own: The second reading's record for this position. THE SAME OBJECT
                is passed on the pristine and the degraded pass - degrading it
                too would be degrading the thing under test.
        """
        end = record.body_offset + record.body_length
        shipped_ok, shipped = _shipped_sites_of(body, record, end)
        own_ok, own_sites = _independent_sites_of(body, own)
        self.shipped_sites += shipped
        self.independent_sites += own_sites
        self.shipped_reached += shipped_ok
        self.independent_reached += own_ok


@dataclass
class _TableControlCounts:
    """One version pair's record table, measured pristine and degraded.

    Attributes:
        records: Records of this pair measured under both presentations.
        altered: Records the degradation actually CHANGED - the FIRING COUNT. A
            mutant that never applied and one that survived produce identical
            output, so this is asserted rather than assumed.
        census: Struct type words the BYTES carry inside these records' PRISTINE
            extents. No reader can move it, which is what separates "this pair
            carries no struct content" from "the reading destroyed the evidence
            that it does".
        pristine: Both readings over the table as ``objects.parse_body`` built
            it.
        degraded: Both readings over the degraded table.
    """

    records: int = 0
    altered: int = 0
    census: int = 0
    pristine: _TableReading = field(default_factory=_TableReading)
    degraded: _TableReading = field(default_factory=_TableReading)


@dataclass(frozen=True)
class _TableControlResult:
    """The library reduced to the one version pair the control grades.

    THE PAIR ITSELF NEVER LEAVES :func:`_run_table_degradation_control`.
    :class:`tests.save.test_struct_interior._SaveShape` states the rule this follows: a version pair
    is reduced to counts before it reaches anything a repr can render - not because a build number
    is personal data, but because "only counts leave" stops holding the first time it is argued case
    by case.

    Attributes:
        pairs: How many distinct version pairs parsed into a record table.
        library_records: Records over every one of them, graded or not.
        chosen: The graded pair's counts.
        failures: Saves whose fold raised. A COUNT, never a type name and never
            a path - this control feeds the shipped readers misaligned offsets
            on purpose, so a raise there is a containment question first and a
            coverage question second. The arm asserts it at zero, which is what
            keeps the handler from becoming a silent drop.
        saves: Saves this run folded. Part of the corpus statement CS-1054
            added, and the count that makes two runs comparable at all.
        set_aside_pairs: Version pairs excluded from the choice because
            ``objects.COMPLETE_TYPE_NAME_PAIRS`` declares a payload grammar this
            module's own reading does not express.
        set_aside_records: Records those pairs carried.
        set_aside_sites: Struct sites this module's own reading found inside
            them. ASSERTED AT ZERO by the arm: the set-aside rests on a
            declaration, and a site found in a set-aside pair means the
            declaration no longer describes this reading.
    """

    pairs: int
    library_records: int
    chosen: _TableControlCounts
    failures: int = 0
    saves: int = 0
    set_aside_pairs: int = 0
    set_aside_records: int = 0
    set_aside_sites: int = 0


def _fold_table_control(
    body: bytes,
    record: objects.ObjectRecord,
    own: independent_table.IndependentRecord,
    into: _TableControlCounts,
) -> None:
    """Measure ONE record twice - as the table presents it, and degraded.

    The two measurements are taken from the SAME read of the SAME body, back to
    back, so nothing between them can differ.

    ``own`` IS NOT DEGRADED AND THAT IS DELIBERATE. It is the second reading's
    own record, read from the body rather than from the shipped table, and it is
    the thing whose invariance is under test. Degrading it too would be
    degrading the measuring instrument along with the thing measured, and the
    arm would then be unable to fail.

    Args:
        body: The decompressed body.
        record: The pristine SHIPPED record.
        own: The second reading's record for the same position.
        into: The pair's accumulator, mutated in place.
    """
    into.records += 1
    end = record.body_offset + record.body_length
    into.census += _census_hits(body, record.body_offset, end)
    into.pristine.add(body, record, own)
    degraded = _degrade_one_record(record)
    # COUNTED BY WHETHER THE RECORD ACTUALLY CHANGED, NOT BY WHETHER A
    # DEGRADATION WAS ATTEMPTED. `degraded is not None` was the old test and it
    # is exactly the defect a firing count exists to prevent: an adversary made
    # `_degrade_one_record` return its argument unchanged and this counter still
    # reported the full population, so a degradation that altered nothing was
    # indistinguishable from one that altered everything - which is the sentence
    # in the arm's own docstring, turned on itself.
    into.altered += degraded is not None and degraded != record
    # A record too short to shift is measured AGAIN AS ITSELF rather than
    # dropped: both passes have to range over the same population, or the
    # comparison below is between two different worlds.
    into.degraded.add(body, record if degraded is None else degraded, own)


def _run_table_degradation_control() -> _TableControlResult | None:
    """Read each save ONCE, measure every record TWICE, and grade one pair.

    EACH SAVE IS READ ONCE AND MEASURED TWICE, for the reason
    :func:`_run_degradation_control` states: the operator plays this game while
    a session runs, so re-reading the library between two passes races a real
    autosave and reports the difference as a defect. The degraded records are
    built from the pristine ones already in hand.

    THE GRADED PAIR IS DERIVED AND NOT TRANSCRIBED, on the same terms as this
    module's struct vocabulary. It is the pair carrying the MOST records of
    those that parsed AND whose payload grammar this module's own reading
    expresses, ties broken by the pair itself so the choice cannot depend on the
    order the library happens to be walked in. A pair written into this file
    would be a hand-maintained list that rots the first time the operator's
    library gains or loses a save.

    THE GRAMMAR CLAUSE IS CS-1054 AND IT IS NOT A NARROWING. The block above
    :class:`_TableControlResult` states what was measured: without it this
    control graded a pair whose payloads neither reading here can walk, and
    reported "no site" as evidence destroyed. What was set aside is set aside by
    a SHIPPED DECLARATION, and the arm asserts those pairs yield no site, so the
    exclusion cannot grow or go stale in silence.

    THE COUNTS ARE KEPT PER PAIR RATHER THAN POOLED, and that is what makes this
    a ONE-pair degradation without a second read of anything: a save carries
    exactly one pair, so a pair's tally is exactly what degrading that pair
    alone would have produced.

    KEY ORDER, A TRAP THIS REPO HAS ALREADY PAID FOR.
    ``objects.BODY_LAYOUT_BY_PAIR`` is keyed ``(header_version, save_version)``
    while the key here is ``(save_version, header_version)``, matching
    :class:`tests.save.test_struct_interior._SaveShape`. Neither is ever indexed with the other.

    Returns:
        The reduction, or None when NO save library is reachable at all - which
        is a different claim from "the library holds nothing this project
        parses", and that one comes back as a result whose counts are zero.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None
    by_pair: dict[tuple[int, int], _TableControlCounts] = {}
    failures = 0
    folded = 0
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            # PAIRED POSITIONALLY, AND ONLY WHERE PAIRING IS DEFINED - the same
            # refusal `_sweep_one_save` makes. A save the second reading
            # declines contributes NOTHING here rather than a half-measured
            # record, because this control's whole claim is a comparison
            # between two readings and one of them would be missing.
            #
            # IT IS INSIDE THE HANDLER BECAUSE `body` IS LIVE IN THIS FRAME.
            # It used to sit after it. pytest renders the arguments of the
            # first and the deepest traceback frame with no opt-in flag, so an
            # exception raised out there put real save bytes into a transcript
            # - measured by an adversary at 240 rendered characters carrying a
            # `/Game/...` asset path on 3 of this machine's 20 saves.
            mine = independent_table.independent_records(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        if mine is None or len(mine) != len(table.records):
            continue
        folded += 1
        counts = by_pair.setdefault(
            (parsed.save_version, parsed.header_version), _TableControlCounts()
        )
        # THE FOLD IS WRAPPED TOO, AND THAT IS NOT BELT AND BRACES. This control
        # hands the shipped readers DELIBERATELY MISALIGNED offsets - that is
        # what `_degrade_one_record` is for - so it drives `objects._payload_text`
        # and `objects._skip_actor_head` through inputs no other caller gives
        # them, with `body` live in this frame. An uncaught raise there renders
        # save bytes into a traceback. A failure is COUNTED and asserted at zero
        # by the arm rather than swallowed, so the containment cannot quietly
        # become a silent drop.
        try:
            for index, record in enumerate(table.records):
                _fold_table_control(body, record, mine[index], counts)
        except (Exception, SystemExit):
            # Counted, not swallowed - the arm asserts this at zero.
            failures += 1
    graded, set_aside_pairs, set_aside_records = _grade_the_pair_this_module_can_read(by_pair)
    return _TableControlResult(
        pairs=len(by_pair),
        library_records=sum(counts.records for counts in by_pair.values()),
        chosen=_TableControlCounts() if graded is None else by_pair[graded],
        failures=failures,
        saves=folded,
        set_aside_pairs=set_aside_pairs,
        set_aside_records=set_aside_records,
        set_aside_sites=sum(
            counts.pristine.independent_sites
            for pair, counts in by_pair.items()
            if not _the_second_reading_implements(pair)
        ),
    )


def test_a_changed_corpus_and_destroyed_evidence_are_not_the_same_verdict() -> None:
    """CS-1054's distinction, graded in BOTH DIRECTIONS with no save at all.

    THE TWO ARMS BELOW IT ARE LIBRARY-BACKED AND CANNOT GRADE THIS. They see
    whatever the operator's library happens to hold at the second they run, and
    the whole finding is that the library moves: at 9f4fe6d the same arm passed
    inside a whole-suite run and failed on the same commit with a clean tree
    twenty-five minutes later, because one autosave had landed and changed which
    version pair was graded. A distinction that only one of those two corpora
    exercises is a distinction nothing checks.

    :func:`_classify_graded_population` is a pure function of four integers
    precisely so this arm can drive both directions, here, on a machine with no
    game installed.

    THE FIRST DIRECTION IS THE ONE THAT WAS WRONG. A corpus whose every pair
    carries a payload grammar declared in ``objects.COMPLETE_TYPE_NAME_PAIRS``
    yields no site to a reading that expresses only the legacy grammar, and the
    bytes still carry the words. That is a corpus that CHANGED and it MUST NOT
    be a red.

    THE SECOND DIRECTION IS THE ONE THAT MUST STILL FIRE. A graded pair this
    reading DOES express, whose bytes carry struct words and in which the
    reading finds none, is evidence destroyed, and nothing added here may turn
    that into a skip.

    THE NUMBERS ARE THE MEASURED ONES from this machine at 27482eb - 172810
    census words over 80801 records in the set-aside pair, 91450 over 77263 in
    the largest pair this module reads - so the fixture is the real shape rather
    than a convenient one. They are counts, and counts are the only thing about
    a save this file is allowed to carry.
    """
    changed = _classify_graded_population(
        graded_records=0, set_aside_records=80801, census=172810, independent_sites=0
    )
    assert changed == _POPULATION_GRAMMAR_SET_ASIDE, (
        f"a corpus holding only pairs whose grammar this module does not express was "
        f"classified {changed!r}. The library gaining a save in a newer format is the "
        "corpus CHANGING, and calling that destroyed evidence is the red CS-1054 was "
        "filed for"
    )

    destroyed = _classify_graded_population(
        graded_records=77263, set_aside_records=80801, census=91450, independent_sites=0
    )
    assert destroyed == _POPULATION_EVIDENCE_DESTROYED, (
        f"a graded pair whose bytes carry 91450 struct type words across 77263 records, "
        f"in which this module's own reading found none, was classified {destroyed!r}. "
        "THAT MUST STAY A RED. An empty population satisfies every equality below it, "
        "which is why this arm is an assertion and never a skip"
    )

    # THE TWO REMAINING CLASSIFICATIONS, so the routing above cannot quietly
    # collapse into two answers. A pair with no struct word in its BYTES is an
    # absent population and not a loss; a run that folded nothing has no
    # population at all.
    absent = _classify_graded_population(
        graded_records=77263, set_aside_records=0, census=0, independent_sites=0
    )
    assert absent == _POPULATION_NO_STRUCT_IN_BYTES, (
        f"a graded pair whose bytes carry no struct type word was classified {absent!r} "
        "rather than an absent population, so a corpus holding nothing to lose would be "
        "reported as having lost it"
    )
    empty = _classify_graded_population(
        graded_records=0, set_aside_records=0, census=0, independent_sites=0
    )
    assert empty == _POPULATION_NO_RECORD, (
        f"a run that folded no record at all was classified {empty!r}"
    )
    graded = _classify_graded_population(
        graded_records=77263, set_aside_records=80801, census=91450, independent_sites=30642
    )
    assert graded == _POPULATION_GRADED, (
        f"a graded pair this reading found 30642 sites in was classified {graded!r}, so "
        "the ordinary case does not reach the comparisons this control exists for"
    )


def test_the_table_control_takes_its_window_from_the_body_not_the_degraded_record() -> None:
    """THE SECOND ANTI-MONOTONE CONTROL - the substrate BOTH readings share.

    WHY A SECOND CONTROL IS NOT A DUPLICATE OF THE FIRST.
    :func:`test_degrading_the_shipped_tag_reader_cannot_improve_this_modules_grade`
    degrades a reader this module's own walk does not call, so the two readings
    separate under it. They still share the RECORD TABLE: ``_sweep_one_record``
    takes each record's payload start, its extent and its KIND off that one
    table for the independent reading as for the shipped one. A defect there
    moves both, and no arm in this module can currently see it.

    WHAT THE DEGRADATION DOES AND WHY IT IS THE RIGHT ONE. See
    :func:`_degrade_one_record`: for one version pair it relabels every actor a
    component and slides every payload start one byte with the extent END held.
    Relabelling changes which start a reading takes and sliding changes where it
    takes it from, which is the pair of fields a record table exists to state -
    so a table that states them wrongly is exactly the defect this arm is for.

    WHAT THIS ARM DOES NOT PROVE, MEASURED AND STATED RATHER THAN LEFT TO BE
    INFERRED. It does NOT prove the second reading is independent, and an
    earlier version of this docstring said it did. :func:`_fold_table_control`
    hands the SAME ``body`` and the SAME ``own`` object to both passes, so the
    equality below is ``sum f(x) == sum f(x)`` over identical arguments - an
    adversary instrumented it and measured every one of the call pairs
    receiving arguments identical by IDENTITY, and the equality held under six
    deliberately garbage readings including one that was the shipped record
    table verbatim. What it grades is the WIRING: that ``own`` is not derived
    from the degraded record. That is one bit, it is worth having, and it is
    not a proof about :mod:`tests.save.independent_table`. That module's
    independence is graded elsewhere and by something else - the DYNAMIC SEAM
    ARMS this item's follow-up CS-862 added to
    ``tests/save/test_independent_table.py``, which degrade the shipped record
    table at its SOURCE rather than at its output and redden for a wrapper.

    AND THAT IS WHY THIS ARM IS NAMED FOR THE WIRING RATHER THAN FOR THE GRADE.
    A reader of a GREEN run sees the NAME and nothing else - no docstring, no
    assertion message - so a name claiming more than the arm grades is a claim
    made in the one place the narrowing above cannot reach. It used to be
    ``test_degrading_the_record_table_cannot_improve_this_modules_grade``.

    THE GRADED PAIR IS DERIVED, NEVER TRANSCRIBED, on the same terms as this
    module's struct vocabulary: it is the version pair carrying the most records
    of those that parsed. :func:`_run_table_degradation_control` states how, and
    the pair never leaves that function - only counts do.

    THREE GUARDS, EACH ALREADY PAID FOR IN THIS REPO. The FIRING COUNT is
    asserted, because a mutant that never applied and one that survived produce
    identical output. The population is asserted NON-EMPTY before anything
    ranges over it, because an empty population satisfies every equality - a
    finding born in this very item. And the empty case is split the way
    :func:`_sweep_or_skip` splits it: a zero the BYTE CENSUS contradicts is
    evidence destroyed and stays an assertion, while a zero the bytes agree with
    is a skip naming the ingredient it lacks.

    AND A FOURTH, WHICH IS CS-1054. The corpus is a directory the operator
    writes to while a session runs, so this arm now STATES which corpus it
    measured - saves, pairs, records, graded records, records set aside - in
    every message it can emit, and its graded pair is chosen only from pairs
    whose payload grammar this module's own reading expresses. Without that it
    graded whichever pair the last autosave made largest and reported a grammar
    it cannot walk as evidence destroyed. Measured at 9f4fe6d: green inside a
    whole-suite run, red on the same commit with a clean tree twenty-five
    minutes later, nothing in the repository moved. The set-aside is itself
    asserted at zero sites, and the changed-versus-destroyed distinction is
    graded synthetically in both directions by
    :func:`test_a_changed_corpus_and_destroyed_evidence_are_not_the_same_verdict`,
    because a library-backed arm can only ever see the one corpus it ran on.
    """
    _sweep_or_skip()

    result = _run_table_degradation_control()
    if result is None:
        pytest.skip("no save library on this machine - there is no record table to degrade")
    chosen = result.chosen
    corpus = _corpus_line(
        saves=result.saves,
        pairs=result.pairs,
        library_records=result.library_records,
        graded_records=chosen.records,
        set_aside_pairs=result.set_aside_pairs,
        set_aside_records=result.set_aside_records,
    )
    control_failures = result.failures
    assert control_failures == 0, (
        f"{control_failures} saves raised inside the fold. This control feeds the shipped "
        "readers misaligned offsets deliberately, so a raise there is contained rather "
        "than rendered - but it is asserted here so containment cannot become a silent "
        f"drop, which is the shape that has refuted this item repeatedly. {corpus}"
    )

    # THE SET-ASIDE IS ASSERTED, NOT ASSUMED - CS-1054. The pairs excluded from
    # the choice are excluded on a shipped DECLARATION about their grammar, and
    # a declaration nothing checks is a comment. A site found by this module's
    # own reading inside one of them means the reading now expresses a grammar
    # the exclusion still says it does not, and the pair belongs back in the
    # graded population. A RED HERE IS GOOD NEWS.
    set_aside_sites = result.set_aside_sites
    assert set_aside_sites == 0, (
        f"this module's own reading found {set_aside_sites} struct sites inside the "
        f"{result.set_aside_records} records of the {result.set_aside_pairs} version "
        "pairs set aside for carrying a declared complete-type-name payload grammar. "
        "The set-aside says this reading cannot express those payloads and it just "
        f"did, so the exclusion is STALE and those pairs must be graded. {corpus}"
    )

    census = chosen.census
    independent_pristine = chosen.pristine.independent_sites
    population = _classify_graded_population(
        graded_records=chosen.records,
        set_aside_records=result.set_aside_records,
        census=census,
        independent_sites=independent_pristine,
    )
    if population == _POPULATION_GRAMMAR_SET_ASIDE:
        pytest.skip(
            "every version pair this run read carries a payload grammar declared in "
            "objects.COMPLETE_TYPE_NAME_PAIRS, which this module's own tag reading does "
            "not express, so there is no pair it could grade. THE CORPUS CHANGED AND "
            f"NOTHING WAS DESTROYED - that is the distinction CS-1054 exists for. {corpus}"
        )
    if population == _POPULATION_NO_RECORD:
        pytest.skip(
            "no save this run read parses into a record table, so the control measured "
            f"no record at all and a degraded table has nothing to cost. {corpus}"
        )

    records = chosen.records
    altered = chosen.altered
    assert altered > 0, (
        f"the degradation changed none of the {records} records of the graded pair. A "
        "mutant that did not apply and one that survived produce the same output, so "
        "this run says nothing about whether a defect in the record table is visible "
        "here. THIS STAYS AN ASSERTION rather than joining the skips: its population is "
        "the graded pair's records, which the guard above has already established is "
        "non-empty, so a zero here is the degradation being inert and not an absent "
        f"corpus. {corpus}"
    )

    if population == _POPULATION_NO_STRUCT_IN_BYTES:
        pytest.skip(
            "the graded version pair's records carry no struct type word in their BYTES, "
            "so this pair holds no site a degraded table could take away and every "
            f"comparison over it would be measuring an absent population. {corpus}"
        )
    # THE ORIGINAL ASSERTION, UNCHANGED IN SHAPE AND IN STRENGTH. Everything
    # CS-1054 added above is ROUTING: the two skips it introduces are the
    # classifications this comparison never distinguished, and reaching this
    # line means the population is one this module's own reading expresses and
    # the bytes say carries struct content. A zero here is still destroyed
    # evidence and is still a red.
    assert independent_pristine > 0, (
        f"the byte census found {census} struct type words inside the graded pair's "
        f"{records} records while this module's own reading found no site in them at "
        "all. THAT IS EVIDENCE DESTROYED AND NOT AN ABSENT CORPUS - the line "
        "`_sweep_or_skip` draws - so it stays an assertion, because an empty population "
        "satisfies every equality below. The graded pair is one this reading DOES "
        f"express, so a changed corpus is not the explanation. {corpus}"
    )

    independent_degraded = chosen.degraded.independent_sites
    shipped_pristine = chosen.pristine.shipped_sites
    shipped_degraded = chosen.degraded.shipped_sites
    assert independent_degraded == independent_pristine, (
        f"graded {records} of {result.library_records} records over {result.pairs} "
        f"version pairs, degrading {altered} of them. This module's own reading found "
        f"{independent_pristine} struct sites over the pristine record table and "
        f"{independent_degraded} over the degraded one, opening "
        f"{chosen.pristine.independent_reached} records and then "
        f"{chosen.degraded.independent_reached}. The shipped walk read "
        f"{shipped_pristine} sites and then {shipped_degraded}. THE INDEPENDENT TOTAL "
        "MUST NOT MOVE. It is the denominator every equality in this module stands on, "
        "and it is meant to owe the shipped module nothing but constants - but it takes "
        "its start, its extent and its kind off the very record table degraded here, so "
        "a defect in that table moves the numerator and the denominator together and no "
        "grade can go red"
    )

    assert shipped_degraded < shipped_pristine, (
        f"the shipped walk reached {shipped_degraded} struct sites over the degraded "
        f"record table where it reached {shipped_pristine} over the pristine one. The "
        "degradation did not cost the shipped reader anything measurable, so this "
        "control is not exercising the direction it claims to"
    )
    assert shipped_degraded < independent_degraded, (
        f"the shipped walk lost sites under a degraded record table and the equality "
        f"still holds at {shipped_degraded} against {independent_degraded}. THE CHECK "
        "IS STILL ANTI-MONOTONE: the population shrank with the table instead of the "
        "grade going red, which is the exact shape that refuted this item repeatedly"
    )


# ---------------------------------------------------------------------------
# The reach declaration - CS-471
#
# The package-wide guard in tests/save/test_reach_guard.py ENUMERATES this
# directory rather than waiting to be called, so a new library-reaching module
# is in scope the moment it exists. This module is one, and these two maps are
# what it owes.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches. The
#: key is the function's own ``__name__`` and the reason comes from
#: ``reach_guard``, so a rename moves both together.
#:
#: ONE ENTRY PER CONTROL, THOUGH EACH CONTROL IS SEVERAL FUNCTIONS, on the terms
#: the sibling states for its own sweep. The two named here are the only ones
#: that ever hold a save path; the folds and the tallies beneath them are handed
#: bytes and hand counts back. Naming one of those would be an exemption
#: outliving the code it described, which is the failure the package-wide guard
#: exists to catch.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        _run_degradation_control.__name__: reach_guard.REACH_READS_THE_LIBRARY,
        _run_table_degradation_control.__name__: reach_guard.REACH_READS_THE_LIBRARY,
    }
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty:
#: no path-holding read is stubbed here, and the relabelled record the table
#: control builds never leaves the process.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})
