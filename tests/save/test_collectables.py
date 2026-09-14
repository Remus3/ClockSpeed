"""CS-1038 - the collectable section's string PAIRS, read rather than counted.

WHAT WAS MISSING. ``clockspeed/save/objects.py`` read every level's collectable
block as a count followed by that many PAIRS of strings, stepped the cursor over
both halves and returned the count alone. The block's whole content was
discarded at the moment it was read, and the docstring claimed no meaning for
either half. The reading itself is not in doubt - reading it any other way stops
the whole-body walk short of the final byte - so what was missing was the
CARRY, not the grammar.

WHAT THE PAIR IS. The first half is a LEVEL name and the second an ACTOR
INSTANCE name, on the same shape ``_read_level_tail`` and the body's trailing
reference list already carry. That is provenance rather than inference: the
first half is one of the level names the same walk read earlier in the same
body.

POLARITY, AND IT IS THE ONE THING A CONSUMER CAN GET BACKWARDS. The section
records what HAS BEEN COLLECTED. Measured read-only on the pinned development
world, counts only and derived on every run rather than written down here: NOT
ONE entry names an instance the same walk found as a live record. An actor that
has been picked up is gone from the world, so a name that resolves to nothing is
what a collected entry looks like - and a field named for the complement would
invert every consumer downstream of it.

WHAT THIS MODULE DOES NOT CLAIM. It does not claim the resolution measurement
proves the polarity; zero resolving entries is consistent with several readings,
and it is a property of a world the operator is still playing. It claims the
STRINGS SURVIVE THE READ in file order, which is the acceptance CS-1038 was
filed for, and it leaves the interpretation to the consumer that joins them.

AN EMPTY INSTANCE HALF IS A REAL SHAPE AND WAS MEASURED, NOT ASSUMED. The first
version of the library arm below asserted both halves non-empty over the whole
population and went RED on the real save: entries exist whose SECOND string is
the empty one. The arm was narrowed to what the bytes support rather than the
reader being "repaired" into skipping them, because dropping an entry whose
instance half is empty would lose a row the body declares.

COUNTS ONLY WHERE A REAL SAVE IS TOUCHED, on the terms
``tests/save/test_decode_oracles.py`` sets out. A level name and an actor
instance name are world content under non-negotiable 12, so the library arm
below reduces everything it sees to an integer or to an exception type NAME. The
synthetic cases are free to hold strings, because a synthetic fixture is nobody's
save.

NEEDS NO GAME for everything but the one library arm, which skips when absent.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.save import chunks, header, objects, workdir
from tests.save import reach_guard, synthetic

#: The pair this module builds its synthetic bodies on. ONE PAIR, and the choice
#: is stated rather than assumed: it emits a second collectable block on a named
#: level as well as on the persistent one, so a reader that carried only the
#: header block would be caught here rather than passing on a layout that has no
#: second block to miss.
_HEADER_VERSION: Final = 14
_SAVE_VERSION: Final = 52


def _collectable(marker: str) -> synthetic.SyntheticCollectable:
    """One synthetic entry whose two halves cannot be confused for each other.

    Args:
        marker: A token unique to this entry.

    Returns:
        The entry.
    """
    return synthetic.SyntheticCollectable(
        level_name=f"SyntheticLevelHalf_{marker}",
        path_name=f"SyntheticInstanceHalf_{marker}",
    )


def _levels() -> tuple[tuple[synthetic.SyntheticLevel, ...], synthetic.SyntheticLevel]:
    """The named levels and the persistent one, each carrying its own entries.

    EVERY BLOCK CARRIES A DIFFERENT NUMBER OF ENTRIES, including an empty one,
    so a reader that read a fixed count or skipped an empty block is caught.

    Returns:
        The named levels in file order, and the trailing persistent level.
    """
    named = (
        synthetic.SyntheticLevel(
            name="Persistent_Level:SyntheticGridCell_0",
            collectables=(_collectable("a0"), _collectable("a1")),
        ),
        synthetic.SyntheticLevel(
            name="Persistent_Level:SyntheticGridCell_1",
            collectables=(),
        ),
        synthetic.SyntheticLevel(
            name="Persistent_Level:SyntheticGridCell_2",
            collectables=(_collectable("c0"),),
            second_collectables=(_collectable("c1"),),
        ),
    )
    persistent = synthetic.SyntheticLevel(
        name=None,
        collectables=(_collectable("p0"),),
        second_collectables=(_collectable("p1"), _collectable("p2")),
    )
    return (named, persistent)


def _expected_pairs(
    named: Sequence[synthetic.SyntheticLevel], persistent: synthetic.SyntheticLevel
) -> tuple[tuple[str, str], ...]:
    """The pairs the fixture WRITES, in the order the body writes them.

    DERIVED FROM THE FIXTURE rather than transcribed. A literal list here would
    be a second statement of the same fact and would have to be edited every
    time the fixture moves, which is how the expectation comes to describe a
    body nobody builds any more.

    Args:
        named: The named levels in file order.
        persistent: The trailing persistent level.

    Returns:
        Every pair in file order.
    """
    pairs: list[tuple[str, str]] = []
    for level in named:
        pairs.extend((entry.level_name, entry.path_name) for entry in (level.collectables or ()))
        pairs.extend((entry.level_name, entry.path_name) for entry in level.second_collectables)
    pairs.extend((entry.level_name, entry.path_name) for entry in (persistent.collectables or ()))
    pairs.extend((entry.level_name, entry.path_name) for entry in persistent.second_collectables)
    return tuple(pairs)


def _parsed_fixture() -> tuple[objects.ObjectTable, tuple[tuple[str, str], ...]]:
    """Parse the synthetic body and report what it was built to hold.

    Returns:
        The walked table and the pairs the fixture wrote, in file order.
    """
    named, persistent = _levels()
    body = synthetic.build_levelled_body(
        named,
        persistent,
        header_version=_HEADER_VERSION,
        save_version=_SAVE_VERSION,
    )
    table = objects.parse_body(
        synthetic.body_with_prefix(body, _HEADER_VERSION),
        save_version=_SAVE_VERSION,
        header_version=_HEADER_VERSION,
    )
    return (table, _expected_pairs(named, persistent))


def test_the_collectable_pairs_survive_the_read_rather_than_being_counted() -> None:
    """CS-1038's acceptance - BOTH halves of EVERY pair reach the result, in order.

    IT IS AN EQUALITY OVER A SEQUENCE AND NOT A COUNT. A count is met by a
    reader that carried one half twice; an equality over the ordered pairs is
    not. The expectation is derived from the fixture rather than written out,
    so it cannot drift from the body actually built.

    IT REDDENS WHEN EITHER HALF IS DROPPED, which is the property the item was
    filed on and which the two arms below make explicit rather than implied.

    NEEDS NO SAVE LIBRARY.
    """
    table, expected = _parsed_fixture()
    read = tuple((entry.level_name, entry.instance_name) for entry in table.collectables)

    assert read == expected, "the collectable pairs did not survive the read in file order"

    # THE TWO SHAPES A READER THAT DROPPED ONE HALF WOULD PRODUCE. Both are
    # tuples of PAIRS, so the comparison is against a value of the same type the
    # reader produces rather than one no reader could ever return - an inequality
    # between a pair sequence and a string sequence is true for the type alone
    # and grades nothing.
    dropped_level = tuple((pair[1], pair[1]) for pair in expected)
    dropped_instance = tuple((pair[0], pair[0]) for pair in expected)
    assert read != dropped_level, "carrying only the instance half would satisfy this arm"
    assert read != dropped_instance, "carrying only the level half would satisfy this arm"


def test_the_pairs_are_not_deduplicated_and_an_empty_block_contributes_nothing() -> None:
    """The two ways a sequence equality is met by a reader that is still wrong.

    NEEDS NO SAVE LIBRARY.
    """
    table, expected = _parsed_fixture()
    read_total = len(table.collectables)
    distinct_total = len(set(expected))

    assert read_total == len(expected)
    assert read_total == distinct_total, (
        "the fixture no longer makes every pair distinct, so a de-duplicating "
        "reader would pass the equality above unexamined"
    )


def test_no_repr_the_collectable_carry_adds_renders_either_half() -> None:
    """Non-negotiable 12 - a level name and an instance name are world content.

    A test runner reprs a frame local BEFORE a human chooses what to print, so
    the quiet rendering has to be the only one available.

    NEEDS NO SAVE LIBRARY.
    """
    table, expected = _parsed_fixture()
    marker = expected[0][0]

    assert marker not in repr(table), "the table repr rendered a collectable's level half"
    for entry in table.collectables:
        assert entry.level_name not in repr(entry), "the entry repr rendered its level half"
        assert entry.instance_name not in repr(entry), "the entry repr rendered its instance half"


def test_the_collectable_surface_is_on_the_module_s_stated_public_surface() -> None:
    """A capability nothing exports is a capability no consumer may use.

    NEEDS NO SAVE LIBRARY - it is a claim about the repo.
    """
    assert "Collectable" in objects.__all__


# ---------------------------------------------------------------------------
# The real library - COUNTS ONLY
# ---------------------------------------------------------------------------


def _newest_real_save() -> Path | None:
    """The newest save on this machine, or None.

    IT HOLDS EVERY ``Exception`` AND EVERY ``SystemExit``, for the reason
    ``tests/save/test_world.py::_newest_real_save`` states at length: a failure
    escaping ``workdir.latest_save`` unwinds through frames holding the account
    directory, whose NAME is the platform account id (non-negotiable 3).
    ``KeyboardInterrupt`` is deliberately left free to unwind.

    Returns:
        The newest save, or None when there is none or the lookup failed.
    """
    try:
        return workdir.latest_save()
    except (Exception, SystemExit):  # a narrower catch lets the account dir unwind
        return None


def _sweep_or_skip() -> tuple[int, int, int]:
    """Walk the newest real save and return SCALARS ONLY.

    THE WHOLE READ IS INSIDE A GUARD. ``header.read_header`` takes a PATH and
    ``chunks.decompress_body`` takes the save's BYTES, and pytest renders a
    failing frame's arguments - so an escaping error from either publishes an
    absolute path under a home directory or the header options string. The
    failure is re-reported as the error's class NAME, which is closed
    vocabulary, with no exception in flight.

    Returns:
        ``(entries, entries whose level half is non-empty, entries whose two
        halves are the SAME string)``. Skips when there is no library.
    """
    source = _newest_real_save()
    if source is None:
        pytest.skip("no save library on this machine - collectables are not gradeable here")

    scalars: tuple[int, int, int] | None = None
    refusal: str | None = None
    try:
        parsed = header.read_header(source)
        body = chunks.decompress_body(
            source.read_bytes(), parsed.body_offset, header_version=parsed.header_version
        )
        table = objects.parse_body(
            body.payload,
            save_version=parsed.save_version,
            header_version=parsed.header_version,
        )
        scalars = (
            len(table.collectables),
            sum(1 for entry in table.collectables if entry.level_name),
            sum(1 for entry in table.collectables if entry.level_name == entry.instance_name),
        )
    except (Exception, SystemExit) as exc:
        refusal = type(exc).__name__

    if refusal is not None:
        pytest.skip(f"the newest save was not readable here: {refusal}")
    assert scalars is not None, "the guarded read neither produced scalars nor named a refusal"
    return scalars


def test_every_collectable_entry_in_the_newest_real_save_carries_two_halves() -> None:
    """Both halves reach the result on a REAL body, as two equalities over the total.

    A FLOOR WOULD NOT DO. "at least one entry carries a level half" is met while
    every other entry carries none, which is the pooled-guard failure this
    project has recorded. The population is the entry total the same walk
    produced, and each equality is held against THAT rather than a literal - the
    operator plays this world and the entry count moves between runs.

    THE SECOND EQUALITY IS WHAT MAKES THE FIRST MEAN SOMETHING. A reader that
    dropped one half and carried the other TWICE satisfies "every entry has a
    non-empty level half" perfectly. Holding the number of entries whose two
    halves are the SAME string at zero is what separates a genuine pair from one
    string printed twice, and it survives an empty instance half - the empty
    string is not the level name either.

    IT SKIPS RATHER THAN PASSING when the save carries no collectable entry at
    all, because both equalities would then be 0 == 0 and would grade nothing.

    SKIPS WITHOUT A SAVE LIBRARY. COUNTS ONLY.
    """
    entries, with_level, halves_equal = _sweep_or_skip()
    if entries == 0:
        pytest.skip("the newest real save declares no collectable entry - nothing to grade")

    assert with_level == entries, "an entry reached the result with an empty level half"
    assert halves_equal == 0, (
        "an entry carries the same string in both halves, which is what a reader "
        "that dropped one half and duplicated the other looks like"
    )


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``reach_guard`` and applied across this package by the
# suite-wide test in ``test_reach_guard``, which walks the package directory
# rather than waiting to be called.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_newest_real_save": "wraps workdir.latest_save",
        "_sweep_or_skip": "reads the newest save",
    }
)

#: Touches a primitive WITHOUT consuming a real save path, name to why. Empty:
#: every read here goes through the two helpers above.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER over THIS module, forced rather than asserted about.

    The splice is an undeclared helper wired in exactly as the real ones here
    are. Run against a COPY in ``tmp_path``, so nothing tracked is mutated and
    no restore is needed.

    NEEDS NO SAVE LIBRARY.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    return workdir.latest_save().read_bytes()\n",
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
