"""The trailing run after a payload's property terminator - CS-828.

WHAT THIS MODULE GRADES, AND WHAT IT DELIBERATELY DOES NOT CLAIM.

The run between a payload's property terminator and its declared final byte was
recorded by :data:`clockspeed.save.objects.UNMEASURED_PAYLOAD_REGIONS` as wholly
opaque, with a 4-byte floor OBSERVED as ``declared_end - terminator_end`` and no
reading of its interior offered at all. This module grades the first reading of
it: the run OPENS with an int32 field, and that field's value is read out of the
bytes rather than inferred from the run's width.

**THE RUN IS NOT THEREBY CLOSED, AND NOTHING HERE SAYS IT IS.** Part of what
follows the lead field is still unread, it is class-keyed extra data rather than
padding, and :data:`clockspeed.save.objects.TrailingRun` carries its width as
``unread`` precisely so a consumer reads the remainder as an open figure instead
of an absent one.

**WHAT IS COMPLETELY READ IS WIDER THAN THE LEAD FIELD ALONE, AND THIS PARAGRAPH
REPLACES A SENTENCE THAT SAID OTHERWISE.** Two further readings have shipped
against this run since - the count-prefixed item list and the object-reference
pair - and each closes the remainder of the classes a derivation names off the
body being read. This module said the lead field was the whole of what closes
for as long as it swept with those two readings switched OFF, which is the
defect :func:`test_the_sweep_reads_the_remainder_with_the_derived_vocabularies`
now holds shut. What remains open is filed as its own row.

THE LIBRARY HALF REPORTS COUNTS ONLY. Every sweep here is contained the way
``tests/save/test_properties.py`` contains its own: every step wrapped, every
failure reduced to a type NAME before it can reach a frame anyone renders, and
never a path, a body, a class path or a decoded world string out. A class path
read out of a save is game content and a save path contains the platform account
id (CLAUDE.md section 2, non-negotiable 3), so neither is counted BY name here -
every population below is keyed by the version pair and counted as an integer.

THE SYNTHETIC HALF NEEDS NO SAVE LIBRARY and runs on a machine with no game
installed, which is where the reader's own arms live. The library half is
skip-if-absent and grades the claim about the WORLD.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.save import chunks, header, objects
from tests.save import reach_guard, synthetic

#: Reaches the save library and is graded for containment, name to what it does.
#: THE GUARD IS OWNED BY ``reach_guard`` AND CONSUMED HERE, so every module of
#: this package shares one implementation rather than a transcription each.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_library_save_paths": "resolves the save root and the account directory, and globs",
        "_sweep_trailing_runs": "reads and parses every save in the library",
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. EMPTY, AND DELIBERATELY SO: every route into the library here
#: runs through one of the two graded helpers above, and the guard REJECTS a
#: declaration whose subject no longer reaches, so a placeholder entry written
#: to look thorough would turn this module red rather than green. An entry here
#: has to earn itself.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

#: The lead int32 of :data:`tests.save.synthetic.DECODABLE_TRAILING_RUN`, which
#: is `11 22 33 44` little-endian. DELIBERATELY NON-ZERO: the value the library
#: carries is zero on every payload, so a fixture that also read zero would be
#: satisfied by a reader that returned a constant instead of reading bytes.
_SYNTHETIC_LEAD: int = 0x44332211

#: How many bytes of :data:`tests.save.synthetic.DECODABLE_TRAILING_RUN` sit
#: past its lead field.
_SYNTHETIC_UNREAD: int = 4

_BODY_PREFIX: bytes = b"\xab" * 16
_BODY_SUFFIX: bytes = b"\xcd" * 16

#: The object-type discriminator each kind is written with, DERIVED from the
#: shipped map rather than transcribed. A literal 0 and 1 here would be a second
#: copy of the module's own table, and the copy is what drifts.
_OBJECT_TYPE_BY_KIND: dict[str, int] = {
    kind: value
    for value, kind in objects._KIND_BY_OBJECT_TYPE.items()  # noqa: SLF001
}


def _record_for(payload: bytes, *, actor: bool) -> objects.ObjectRecord:
    """Build the record that attributes ``payload`` inside the synthetic body.

    Args:
        payload: The payload the body will carry.
        actor: Whether the record is an actor.

    Returns:
        The record.
    """
    kind = objects.KIND_ACTOR if actor else objects.KIND_COMPONENT
    return objects.ObjectRecord(
        kind=kind,
        type_path="/Synthetic/Path.Synthetic_C",
        root_object="Synthetic_Root",
        instance_name="Synthetic_Instance",
        transform=None,
        parent=None,
        object_type=_OBJECT_TYPE_BY_KIND[kind],
        was_placed_in_level=0,
        body_offset=len(_BODY_PREFIX),
        body_length=len(payload),
    )


# ---------------------------------------------------------------------------
# The reader itself, with no save library anywhere
# ---------------------------------------------------------------------------


def test_the_lead_field_is_read_out_of_the_bytes_rather_than_inferred() -> None:
    """A non-zero lead comes back as the value the bytes carry.

    THE CONTROL AGAINST A CONSTANT-RETURNING READER. The whole library reads
    zero, so an arm whose fixture also reads zero would pass against a reader
    that never looked at a byte.
    """
    run = objects.read_trailing_run(synthetic.DECODABLE_TRAILING_RUN, 0, 8)

    assert run == objects.TrailingRun(width=8, lead=_SYNTHETIC_LEAD, unread=_SYNTHETIC_UNREAD)


def test_a_run_of_exactly_the_lead_field_leaves_nothing_unread() -> None:
    """The population the reading actually closes, named as such."""
    run = objects.read_trailing_run(b"\x07\x00\x00\x00", 0, 4)

    assert run == objects.TrailingRun(width=4, lead=7, unread=0)


def test_a_run_shorter_than_the_lead_field_reads_no_lead() -> None:
    """A short run is REPORTED, not guessed at.

    Non-negotiable 7: unknown content is flagged and skipped. A run too short
    to hold the field yields a run whose ``lead`` is absent and whose whole
    width is unread, rather than a decoded value or a raise.
    """
    run = objects.read_trailing_run(b"\x07\x00", 0, 2)

    assert run == objects.TrailingRun(width=2, lead=None, unread=2)


def test_a_run_reaching_past_the_body_is_refused() -> None:
    """A declared end outside the buffer yields no run at all."""
    assert objects.read_trailing_run(b"\x07\x00\x00", 0, 4) is None


def test_a_negative_run_is_refused() -> None:
    """A terminator past the declared end yields no run at all."""
    assert objects.read_trailing_run(b"\x00" * 16, 12, 8) is None


@pytest.mark.parametrize("actor", [True, False])
def test_the_walk_carries_the_run_onto_the_result(actor: bool) -> None:
    """Both record kinds reach the reader through the shipped walk.

    THE PLUMBING ARM, and it is separate from the reader's own arms on purpose:
    a correct reader nothing calls reads nothing, and an actor and a component
    reach the tag walk by different routes.
    """
    payload = synthetic.tagged_property_payload(
        (),
        head=(
            synthetic.actor_payload_head("Persistent_Level", "Synthetic_Root", ()) if actor else b""
        ),
        trailing=synthetic.DECODABLE_TRAILING_RUN,
    )
    body = _BODY_PREFIX + payload + _BODY_SUFFIX

    result = objects.read_properties(body, _record_for(payload, actor=actor))

    assert result.trailing_run == objects.TrailingRun(
        width=8, lead=_SYNTHETIC_LEAD, unread=_SYNTHETIC_UNREAD
    )


def test_a_payload_whose_walk_breaks_carries_no_run() -> None:
    """No run is invented for a payload that never reached a terminator."""
    body = _BODY_PREFIX + b"\x7f" * 32 + _BODY_SUFFIX
    record = _record_for(b"\x7f" * 32, actor=False)

    assert objects.read_properties(body, record).trailing_run is None


def test_the_region_entry_no_longer_calls_the_floor_unread() -> None:
    """The shipped table records the reading, so the two cannot drift apart.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo. The entry named the
    run's interior as offering no reading at all; that sentence is now false
    and this arm is what makes leaving it in place red.
    """
    entry = objects.UNMEASURED_PAYLOAD_REGIONS["trailing_run"]

    assert "no reading of its interior is offered" not in entry
    assert objects.read_trailing_run.__name__ in entry
    assert f"{objects.TrailingRun.__name__}.unread" in entry


# ---------------------------------------------------------------------------
# The library half - skip-if-absent, COUNTS ONLY
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _RunSweep:
    """What the library sweep observed. Integers and type names only.

    Attributes:
    EVERY FIELD HERE IS READ BY AN ARM. A count the sweep collects and nothing
    grades is a measurement nobody takes - it reads as coverage from the outside
    and is not, which is why a DISTINCT-WIDTH census that had been tallied here
    was removed rather than left for a later reader to mistake for a claim.

    Attributes:
        terminated: Payloads that reached a terminator, by version pair. THE
            DENOMINATOR, and it is taken from the WALK rather than from the
            reader under test - see :func:`_run_of_record`.
        with_lead: Of those, how many yielded a run carrying a lead field.
        zero_lead: Of those, how many read the lead as zero.
        fully_read: Of those, how many have nothing UNREAD past the lead
            field. NOT the same as having nothing past it at all, and the
            difference is the whole subject of ``read_by_derivation``: a
            remainder a derived vocabulary read leaves ``unread`` at zero and
            lands here, so this population is the lead-field-alone runs PLUS
            every remainder the shipped reader closes.
        partly_read: Of those, how many carry unread bytes past it.
        read_by_derivation: Of those, how many had the remainder PAST the lead
            read by one of the four derived vocabularies - an item list, a
            reference pair, a count-prefixed reference list or a zero
            remainder. THE ARM OVER THIS FIGURE IS
            WHAT HOLDS THE SWEEP TO
            THE SHIPPED READER: every reading is gated on a vocabulary a caller
            must pass, so a sweep that omits them reads every remainder as
            unread and reports a partition no consumer of this module sees.
        failures: The type names of any unexpected failure.
    """

    terminated: MappingProxyType
    with_lead: MappingProxyType
    zero_lead: MappingProxyType
    fully_read: MappingProxyType
    partly_read: MappingProxyType
    read_by_derivation: MappingProxyType
    failures: tuple[str, ...]


def _library_save_paths() -> tuple[Path, ...]:
    """Every save file on this machine, or an empty tuple.

    IT HOLDS EVERY ``Exception`` AND EVERY ``SystemExit``, and every discovery
    call sits INSIDE the ``try``: the account directory's NAME is the platform
    account id, and a failure unwinding through a frame that holds it is an
    echo path under non-negotiable 3. ``root`` and ``account`` are bound in
    this frame and nowhere else.

    Returns:
        The save paths, sorted, or an empty tuple when there is no library.
    """
    try:
        root = locate.resolve_save_root()
        account = locate.resolve_account_dir(root) if root is not None else None
        return () if account is None else tuple(sorted(account.glob("*.sav")))
    except (Exception, SystemExit):
        return ()


def _run_of_record(
    body: bytes,
    record: objects.ObjectRecord,
    *,
    save_version: int,
    header_version: int,
    item_list_classes: Collection[str],
    reference_pair_classes: Mapping[str, int],
    reference_list_classes: Mapping[str, int],
    zero_remainder_classes: Collection[str],
) -> tuple[bool, objects.TrailingRun | None]:
    """Read one record's trailing run, or say the walk never reached one.

    THE DENOMINATOR IS TAKEN FROM THE WALK AND NOT FROM THE READER UNDER TEST,
    and that is the whole reason the arms below can go red. A payload that
    reached its terminator is one the walk did not refuse, which the shipped
    warning reports; counting instead the payloads that came back WITH a run
    would let a reader returning None for a whole class shrink the numerator and
    the denominator together and stay green.

    **THE FOUR VOCABULARIES ARE REQUIRED KEYWORDS AND CARRY NO DEFAULT, WHICH IS
    THE POINT OF PASSING THEM AT ALL.** Every remainder reading CS-828 has
    shipped is gated on one, and :func:`objects.read_properties` defaults them
    all to empty - so a caller that simply forgets them gets a reader that declines
    every remainder and reports it as ``unread``, silently. That is the shape
    this helper carried until the arm named in
    :func:`test_the_sweep_reads_the_remainder_with_the_derived_vocabularies`
    measured it. A default here would put the same silence back.

    A PAIR RATHER THAN A SENTINEL. An earlier draft returned a module-level
    marker object for the refused case, which typed as ``TrailingRun | None |
    object`` - and that collapses to ``object``, so the type checker had nothing
    left to hold. The two answers are genuinely independent facts about one
    record and are returned as two.

    Args:
        body: The decompressed body.
        record: The record to read.
        save_version: The save version the pair names.
        header_version: The header version the pair names.
        item_list_classes: The item-list carrier classes derived off this body.
        reference_pair_classes: The reference-pair carrier classes derived off
            this body, each to the tail width that derivation derived.
        reference_list_classes: The reference-LIST carrier classes derived off
            this body, each to the per-entry prefix width that derivation
            derived.
        zero_remainder_classes: The zero-remainder carrier classes derived off
            this body.

    Returns:
        (whether the walk reached a terminator, the run the reader returned).
        The run is None both when the walk did not terminate and when it did
        and the reader declined - the first element is what tells those apart.
    """
    if not record.body_length:
        return (False, None)
    result = objects.read_properties(
        body,
        record,
        save_version=save_version,
        header_version=header_version,
        item_list_classes=item_list_classes,
        reference_pair_classes=reference_pair_classes,
        reference_list_classes=reference_list_classes,
        zero_remainder_classes=zero_remainder_classes,
    )
    refused = any(
        warning.code == objects.WARN_UNPARSED_PROPERTY_PAYLOAD for warning in result.warnings
    )
    return (False, None) if refused else (True, result.trailing_run)


class _Tally:
    """The running counts of the library sweep. INTEGERS AND NOTHING ELSE.

    A CLASS RATHER THAN FIVE LOCALS, and not for tidiness: the classification
    below is the one place a run enters or leaves a population, so a reader
    checking what a count means has one method to read rather than five
    increments scattered through a nested loop.

    **NO ARM ASSERTS AN IDENTITY OVER THESE COUNTS, and that is deliberate
    rather than an omission.** A draft carried one - that ``with_lead`` equals
    ``fully_read`` plus ``partly_read`` - and it was a tautology of the if/else
    below rather than a measurement: the branch has no third exit, so no reader
    this test can be given makes the sum come out false. It was removed with its
    claim. Every count here is instead graded against ``terminated``, which
    :func:`_run_of_record` takes from the WALK and not from the reader.
    """

    def __init__(self) -> None:
        """Start every population empty."""
        self.terminated: Counter[tuple[int, int]] = Counter()
        self.with_lead: Counter[tuple[int, int]] = Counter()
        self.zero_lead: Counter[tuple[int, int]] = Counter()
        self.fully_read: Counter[tuple[int, int]] = Counter()
        self.partly_read: Counter[tuple[int, int]] = Counter()
        self.read_by_derivation: Counter[tuple[int, int]] = Counter()

    def add(self, pair: tuple[int, int], terminated: bool, run: objects.TrailingRun | None) -> None:
        """Count one record's outcome.

        Args:
            pair: The version pair the save carries.
            terminated: Whether the walk reached a terminator.
            run: The run the reader returned, or None.
        """
        if not terminated:
            return
        self.terminated[pair] += 1
        if run is None or run.lead is None:
            return
        self.with_lead[pair] += 1
        if run.lead == objects.TRAILING_RUN_LEAD_MEASURED_VALUE:
            self.zero_lead[pair] += 1
        if (
            run.items is not None
            or run.references is not None
            or run.reference_list is not None
            or run.zero_remainder is not None
        ):
            self.read_by_derivation[pair] += 1
        if run.unread:
            self.partly_read[pair] += 1
        else:
            self.fully_read[pair] += 1

    def sweep(self, failures: list[str]) -> _RunSweep:
        """Freeze the counts into the sweep the arms read.

        Args:
            failures: The exception type names collected on the way.

        Returns:
            The sweep.
        """
        return _RunSweep(
            terminated=MappingProxyType(dict(self.terminated)),
            with_lead=MappingProxyType(dict(self.with_lead)),
            zero_lead=MappingProxyType(dict(self.zero_lead)),
            fully_read=MappingProxyType(dict(self.fully_read)),
            partly_read=MappingProxyType(dict(self.partly_read)),
            read_by_derivation=MappingProxyType(dict(self.read_by_derivation)),
            failures=tuple(sorted(set(failures))),
        )


@lru_cache(maxsize=1)
def _sweep_trailing_runs() -> _RunSweep | None:
    """Read the trailing run of every payload of every real save, COUNTS ONLY.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None

    tally = _Tally()
    failures: list[str] = []
    for path in saves:
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            # The two EXPECTED failures - an unreadable file and a version this
            # project does not parse - stay silent skips. The library holds
            # both legitimately and the arms below treat a recorded failure as
            # fatal.
            continue
        except (Exception, SystemExit) as exc:
            # THE BACKSTOP. Anything unexpected escaping here unwinds through
            # `path.read_bytes()`, whose bound `self` IS the save path.
            failures.append(type(exc).__name__)
            continue
        pair = (parsed.header_version, parsed.save_version)
        if pair not in objects.MEASURED_BODY_LAYOUTS:
            continue
        # BROAD BY DESIGN: a narrower catch lets an unexpected type escape
        # carrying the save bytes.
        try:
            body = chunks.decompress_body(
                data, parsed.body_offset, header_version=parsed.header_version
            ).payload
            table = objects.parse_body(
                body, save_version=parsed.save_version, header_version=parsed.header_version
            )
            # DERIVED OFF THIS BODY AND NEVER TRANSCRIBED, which is the rule every
            # one of these readings ships under - a vocabulary carried between saves would be a
            # hand-maintained list of game content, and a body that stops
            # demonstrating the grammar must derive nothing and say so.
            item_list_classes = objects.derive_item_list_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            reference_pair_classes = objects.derive_reference_pair_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            reference_list_classes = objects.derive_reference_list_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            zero_remainder_classes = objects.derive_zero_remainder_classes(
                body,
                table.records,
                save_version=parsed.save_version,
                header_version=parsed.header_version,
            )
            for record in table.records:
                terminated, run = _run_of_record(
                    body,
                    record,
                    save_version=parsed.save_version,
                    header_version=parsed.header_version,
                    item_list_classes=item_list_classes,
                    reference_pair_classes=reference_pair_classes,
                    reference_list_classes=reference_list_classes,
                    zero_remainder_classes=zero_remainder_classes,
                )
                tally.add(pair, terminated, run)
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
    return tally.sweep(failures)


def _sweep_or_skip() -> _RunSweep:
    """Fetch the sweep, skipping the arm when there is no library.

    Returns:
        The sweep.
    """
    sweep = _sweep_trailing_runs()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    NEEDS NO SAVE LIBRARY - it is a claim about this module's source. Both
    directions are held by the guard: a function that reaches must be declared,
    and a declaration that no longer reaches is rejected, so an exemption cannot
    outlive the code it described.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER in THIS module, forced rather than asserted about.

    NEEDS NO SAVE LIBRARY. The splice is the pre-repair shape - the locators and
    the glob outside every ``try`` - wired in exactly as the real helper here
    is, and run against a COPY in ``tmp_path`` so nothing tracked is mutated and
    no restore is needed.
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
        reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert "_spliced_uncontained_helper" in str(caught.value)

    # The positive control: the same guard on the unspliced source passes, so
    # the red above is the splice rather than the guard rejecting everything.
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_sweep_reaches_every_pair_this_item_covers() -> None:
    """THE NON-VACUITY CONTROL, and it runs before every claim below.

    An arm whose population is empty passes for that reason alone. The three
    pairs CS-828 names are the pairs whose payloads reach a terminator, so a
    sweep that reached none of them, or reached one and not the others, is a
    sweep whose later assertions grade nothing.
    """
    sweep = _sweep_or_skip()
    reached = frozenset(pair for pair, count in sweep.terminated.items() if count)

    assert sweep.failures == ()
    assert reached >= objects.TRAILING_RUN_PAIRS


def test_every_payload_that_terminates_yields_a_lead_field() -> None:
    """Every payload the WALK terminated yields a run carrying a lead field.

    **WHAT THIS ARM DOES NOT SAY, stated here because a draft of it did say the
    stronger thing and the stronger thing is false.** It does NOT say the
    field's PRESENCE has stopped being arithmetic. ``read_trailing_run`` returns
    a lead exactly when the run is at least :data:`clockspeed.save.objects.TRAILING_RUN_LEAD_BYTES`
    wide, and that width is still ``declared_end - terminator_end`` - the
    subtraction CS-828's clause names. The field's VALUE is read from the bytes;
    its presence is not, and that half of the clause is unmet.

    WHAT IT DOES SAY is that the reader produced a field for every payload the
    walk reached a terminator on, graded against a denominator the reader cannot
    move. A reader declining a whole class of runs reddens here.
    """
    sweep = _sweep_or_skip()
    short = sum(
        sweep.terminated[pair] - sweep.with_lead.get(pair, 0) for pair in objects.TRAILING_RUN_PAIRS
    )

    assert short == 0


def test_the_lead_field_reads_zero_on_every_payload_of_the_three_pairs() -> None:
    """The contents of the field, measured rather than assumed.

    A NON-ZERO LEAD IS NOT A DEFECT IN THIS READER and this arm is not a
    correctness check on the walk. It is the measurement CS-828 asks for: what
    the run's first field actually carries across the whole library.

    GRADED AGAINST ``terminated`` AND NOT AGAINST ``with_lead``. Subtracting
    from the reader's own output would let a reader that returned no lead at all
    satisfy this arm by emptying both sides, which is the shape the module's
    denominator discipline exists to refuse - and an earlier draft of this arm
    had exactly it, rescued only by the arm above being a separate test.
    """
    sweep = _sweep_or_skip()
    not_measured_zero = sum(
        sweep.terminated[pair] - sweep.zero_lead.get(pair, 0) for pair in objects.TRAILING_RUN_PAIRS
    )

    assert not_measured_zero == 0


def test_both_halves_of_the_partition_are_populated_on_every_pair() -> None:
    """THE SECOND NON-VACUITY CONTROL, over the partition rather than the sweep.

    Every arm above is satisfied by a library in which every run is the lead
    field alone - and on such a library the ``unread`` figure would be constant
    zero and would grade nothing. This arm says both halves are real on every
    pair, so the remainder CS-828 leaves open is a measured population rather
    than an empty one, and a reader that reported ``unread`` as a constant
    reddens here rather than passing for want of a counterexample.
    """
    sweep = _sweep_or_skip()
    empty = sum(
        1
        for pair in objects.TRAILING_RUN_PAIRS
        if not sweep.fully_read.get(pair, 0) or not sweep.partly_read.get(pair, 0)
    )

    assert empty == 0


def test_the_sweep_reads_the_remainder_with_the_derived_vocabularies() -> None:
    """THE SWEEP READS WITH THE SHIPPED READER, not with a narrower one - CS-828.

    **WHY THIS ARM EXISTS, and it is a defect this module carried rather than a
    refinement of it.** Three of the four readings CS-828 has shipped - the
    count-prefixed item list, the object-reference pair and the zero
    remainder - are gated on a vocabulary the caller passes to
    :func:`clockspeed.save.objects.read_properties`, derived off the very body
    being read. A sweep that omits them gets a reader that declines every one
    of those remainders, reports each as ``unread``, and so grades a
    configuration no consumer of the module uses. The counts it published were
    therefore a claim about a reader that is not the shipped one, and they
    OVERSTATED the open region.

    WHAT IT ASSERTS is that the remainder was read by a derivation on every pair
    this item covers - not how often, which is a figure that moves with the
    library. A sweep that stops passing the vocabularies reddens here on every
    pair at once, and no count in :class:`_RunSweep` can be moved to satisfy it
    without the reading actually happening.

    IT IS NOT A TAUTOLOGY OF THE BRANCH THAT FEEDS IT, which is the trap
    :class:`_Tally` records having fallen into once. ``read_by_derivation`` is
    incremented from ``run.items``, ``run.references`` and
    ``run.zero_remainder`` - three fields
    :func:`clockspeed.save.objects.read_trailing_run` never sets - so nothing in
    the lead-field path can make this arm true.
    """
    sweep = _sweep_or_skip()
    unread_by_derivation = sum(
        1 for pair in objects.TRAILING_RUN_PAIRS if not sweep.read_by_derivation.get(pair, 0)
    )

    assert unread_by_derivation == 0
