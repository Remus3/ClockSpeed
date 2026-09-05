"""CS-897 - the four arms that spend the deep archive's rot pin.

WHY THIS MODULE EXISTS. ``tests/test_docs_citations.py`` records exactly one doc
as unguarded and the CS-897 round answered that exemption by MEASURING what it
hides: every arm that module owns, run against the deep archive, each finding
count spent against a typed integer. The measurement is derivation and lives in
``tests/archive_rot_guard.py``; the pin and the four arms that spend it are here,
moved out of a file with 1483 bytes left under the ceiling
``tests/data/test_phase2_gate.py`` holds every file in ``tests/`` to.

THE EXEMPTION ITSELF DID NOT MOVE, DELIBERATELY. :data:`UNGUARDED_DOCS`, the
path it names and the cardinality pin over it are the citation guard's own
subject, and one of the arms over them is cited by ``docs/LEDGER.md`` as a
``path::name`` pointer. The boundary is drawn on SUBJECT - what the exemption
HIDES, against what it IS - and it happens to cost no citation.

HOW THIS MODULE READS THE ONE IT SPLIT FROM. A name that is not a container is
imported plainly; a CONTAINER is read through the module object instead, as
``test_docs_citations.UNGUARDED_DOCS``. That is not style. An imported container
lands in this module's ``globals()`` and the registry walk then demands a row for
it HERE, which would either duplicate a record that already exists one file over
or, worse, invite a second one that disagrees with it. One owner, one row.

WHAT THE FIXTURES COST. They are this module's own instances of the corpus
fixtures the parent builds - module-scoped, so the tracked-file read happens once
more for this file. That is the price of a second module and it is paid
deliberately: a corpus re-derived HERE with its own boundary would be a second
thing to rot, so the fixtures are IMPORTED rather than rewritten and the two
modules read the same bytes by the same code.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Final

import pytest

from tests import archive_rot_guard, test_docs_citations
from tests.archive_rot_guard import (
    _ARCHIVE_HEADER_LINES,
    _ARCHIVE_SITE_FLOOR,
    _ROT_CITATION,
    _ROT_EMPTY,
    _ROT_FORM,
    _ROT_NAME,
    _ROT_PATH,
    _ROT_RANGE,
    ARCHIVE_HEADER_CLAIMS,
    archive_rot,
    archive_sites,
)
from tests.bare_path_guard import (
    REPO_ROOT,
    bare_path_sites,
    declares_untracked,
    floor_problems,
    graded_floor_names,
    sibling_imports,
)
from tests.test_docs_citations import (
    _BARE_PLANT_LEAF,
    _PLANTED_DEAD_NAME,
    DEEP_ARCHIVE,
    NEWLINE,
    bare_path,
    line_key,
    literal_pin_problems,
    scoped_text,
)
from tests.test_docs_citations import (
    file_lines as _file_lines,
)
from tests.test_docs_citations import (
    known_names as _known_names,
)
from tests.test_docs_citations import (
    line_pointer_carriers as _line_pointer_carriers,
)
from tests.test_docs_citations import (
    live_source_roots as _live_source_roots,
)
from tests.test_docs_citations import (
    markdown_texts as _markdown_texts,
)
from tests.test_docs_citations import (
    module_basenames as _module_basenames,
)
from tests.test_docs_citations import (
    sources as _sources,
)
from tests.test_docs_citations import (
    tracked as _tracked,
)

# THE CORPUS FIXTURES, REBOUND UNDER THE NAMES PYTEST RESOLVES THEM BY. pytest
# reads fixtures out of the COLLECTING module's namespace, so a fixture defined
# one file over is invisible here until its name is bound here - and the fixtures
# below are exactly the ones the four arms and the archive fixtures request, one
# hop or two down the chain.
#
# ALIASED AND REBOUND RATHER THAN IMPORTED PLAINLY, and the difference is a
# suppression that is not written. A plain import of a name a test then takes as
# a PARAMETER is reported twice - unused at module scope, then redefined by the
# parameter - and the usual answer is a noqa on each. Neither report is about a
# real fault, and a suppression that has to be repeated once per fixture is a
# suppression somebody will widen. The rebinding makes each import genuinely
# used, so the arms below carry no noqa at all.
#
# THEY ARE NOT RE-DERIVED HERE, DELIBERATELY. A second corpus with its own
# boundary would be a second thing to rot, and this family has already measured
# two populations disagreeing over one file.
file_lines = _file_lines
known_names = _known_names
line_pointer_carriers = _line_pointer_carriers
live_source_roots = _live_source_roots
markdown_texts = _markdown_texts
module_basenames = _module_basenames
sources = _sources
tracked = _tracked

#: How many modules the import cycle below must cover before the arm that walks
#: it is measuring the split it describes. A FLOOR rather than a pin: a fifth
#: module joining the cycle should not spend an adjudication, and losing one
#: must redden - a derivation that walked ONE module would report a confident
#: clean answer about no cycle at all.
_CYCLE_MODULE_FLOOR: Final = 4

#: THE TWO-WAY COUNT PIN, WHICH IS WHAT MAKES THE EXEMPTION MEASURED RATHER
#: THAN ASSERTED. Every arm's finding count against the archive, recorded as a
#: typed integer. OVER a number is rot nobody has looked at; UNDER it is a pin
#: left slack after the archive shrank, which is banked room for an append. The
#: idiom is :func:`forgiveness_budget_problems`' and :func:`decline_budget_problems`',
#: and so is the reason it is spent EXACTLY. DECLARED HERE RATHER THAN WITH THE
#: DERIVATION, because the registry walk requires a bounded table's contract to
#: be defined by the module that holds the table - which is what keeps a pin
#: and the arm that defends it from drifting into different files.
#:
#: PER ARM, NEVER POOLED, for the doctrine :func:`decline_budget_problems`
#: states: a threshold summed over a population is met by its strongest member
#: while the weakest goes unmeasured. Pooled, a pointer whose target line went
#: blank would move from :data:`_ROT_FORM` to :data:`_ROT_EMPTY` and the total
#: would not move at all.
#:
#: WHAT THE ARM DOES AND DOES NOT CLAIM, stated because the acceptance clause
#: it answers is easy to over-read. It does NOT judge whether a site is quoted
#: or cited - that is CS-899 and it is open. It reddens on ANY change to the
#: archive's rot, which is WIDER than the clause asks, and the discrimination
#: is done BY A HUMAN at the moment the pin is bumped. The arm is what forces
#: that moment to exist; it is not what supplies the judgement.
#:
#: THE SIXTH ENTRY IS NOT A DEAD POINTER and is pinned anyway. Those pointers
#: resolve; the forbid leg refuses the FORM because a symbol form cannot be
#: invalidated by an edit above it. It is part of what the exemption hides, so
#: leaving it out would be a boundary nobody re-derives - the founding finding
#: of the module this one was split out of, one more time.
ARCHIVE_ROT: Final[Mapping[str, int]] = {
    _ROT_CITATION: 5,
    _ROT_RANGE: 0,
    _ROT_EMPTY: 3,
    _ROT_NAME: 3,
    _ROT_PATH: 4,
    _ROT_FORM: 13,
}


@pytest.fixture(scope="module")
def archive_text(file_lines: Mapping[str, Sequence[str]]) -> str:
    """The deep archive's own bytes, read from the map every other arm reads.

    NOT A SECOND READ OF THE FILE. ``file_lines`` has already read every
    tracked file, and a second reader that split lines differently would put
    the archive's pointers in range for one arm and out of it for another -
    which is the disagreement that fixture's own docstring exists to prevent.

    THE ABSENCE IS LOUD. A KeyError here would say the archive stopped being
    tracked, which is a finding rather than a reason to measure zero.
    """
    lines = file_lines.get(DEEP_ARCHIVE)

    assert lines is not None, (
        f"{DEEP_ARCHIVE} is not a tracked file, so the exemption recorded for it in"
        " UNGUARDED_DOCS forgives nothing and the measurement below is about no file."
    )
    return scoped_text(DEEP_ARCHIVE, NEWLINE.join(lines))


@pytest.fixture(scope="module")
def archive_declared_untracked(archive_text: str) -> frozenset[str]:
    """R2's answer for the ARCHIVE's cited paths, in one batched call.

    Its own call rather than ``live_declared_untracked``, because that fixture
    asks about the line-pointer population and the archive is exactly the file
    that population excludes.
    """
    cited = {site.cited for site in bare_path_sites({DEEP_ARCHIVE: archive_text})}
    return declares_untracked(sorted(cited))


@pytest.fixture(scope="module")
def archive_rot_of(
    sources: Mapping[str, str],
    file_lines: Mapping[str, Sequence[str]],
    known_names: frozenset[str],
    module_basenames: frozenset[str],
    tracked: list[str],
    archive_declared_untracked: frozenset[str],
    live_source_roots: frozenset[str],
) -> Callable[[str, Mapping[str, Sequence[str]] | None], dict[str, int]]:
    """:func:`archive_rot` with the live corpus bound, so a plant varies ONE thing.

    A CLOSURE RATHER THAN EIGHT ARGUMENTS AT EVERY CALL SITE, and it is a
    control's requirement rather than tidiness: the teeth arm below re-measures
    seven times and every input except the planted one must be the SAME object
    each time, or a delta of one could be the plant or could be a corpus that
    moved underneath it.
    """

    def measure(text: str, lines: Mapping[str, Sequence[str]] | None = None) -> dict[str, int]:
        return archive_rot(
            text,
            sources,
            file_lines if lines is None else lines,
            known_names,
            module_basenames,
            tracked,
            archive_declared_untracked,
            live_source_roots,
        )

    return measure


@pytest.fixture(scope="module")
def archive_rot_counts(
    archive_rot_of: Callable[[str, Mapping[str, Sequence[str]] | None], dict[str, int]],
    archive_text: str,
) -> dict[str, int]:
    return archive_rot_of(archive_text, None)


def test_the_deep_archive_exemption_rests_on_the_claim_its_own_header_makes(
    archive_text: str,
) -> None:
    """CS-897's first conjunct: a reason that is TRUE OF EVERY MEMBER.

    THE REASON IT REPLACED WAS TRUE OF TWO SITES AND FALSE OF THE REST. It said
    the archive's dead pointers sit inside citation-guard detail blocks whose
    SUBJECT is a pointer being dead - quoting rather than citing - and that
    describes exactly two of them. A failed-paths note about a harness file
    that was written and removed is not one. Neither is a plain "that leaf
    records this" reference, nor five dead path-and-symbol citations, nor three
    line pointers landing on nothing, nor three identifiers this tree binds
    nowhere. The reason was written about the sites that provoked it and
    quietly acquired a population it does not cover.

    THE REPLACEMENT IS ANCHORED RATHER THAN ASSERTED. "Its pointers rot by
    construction" is a claim about the file's STATUS, and this file declares
    its own status in its header - so the reason quotes that declaration and
    this arm checks BOTH ENDS: the header must still carry each sentence, and
    the record must still rest on it. An exemption argued from a declaration
    nobody re-reads is precisely how WAKEUP_NOTES.md shipped here on a reason
    its own table contradicted.

    WHAT THIS DOES NOT DO, stated for the reason every other ceiling in this
    module states its own: a false sentence bolted onto a true anchor still
    reads as a reason. What is removed is an exemption whose GROUND has
    silently gone away.
    """
    recorded = test_docs_citations.UNGUARDED_DOCS[DEEP_ARCHIVE]
    header = NEWLINE.join(archive_text.split(NEWLINE)[:_ARCHIVE_HEADER_LINES])

    assert ARCHIVE_HEADER_CLAIMS, "the anchor set is empty, so both legs below check nothing"
    absent = [claim for claim in ARCHIVE_HEADER_CLAIMS if claim not in header]

    assert not absent, (
        "the deep archive's header no longer declares what the exemption rests on:\n"
        + NEWLINE.join(f"  {claim}" for claim in absent)
        + NEWLINE
        + "Re-argue the exemption against what the file now says about itself."
    )
    unquoted = [claim for claim in ARCHIVE_HEADER_CLAIMS if claim not in recorded]

    assert not unquoted, (
        "the recorded reason does not rest on the header claims that make it true of"
        " every member:\n"
        + NEWLINE.join(f"  {claim}" for claim in unquoted)
        + NEWLINE
        + "A reason describing SOME of what an exemption hides is the CS-897 defect."
    )


def test_the_deep_archives_rot_is_measured_and_pinned_per_arm(
    archive_rot_counts: Mapping[str, int],
    archive_text: str,
    markdown_texts: Mapping[str, str],
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """CS-897's second conjunct: the population is MEASURED, and pinned both ways.

    WHAT THIS BUYS THAT THE REASON CANNOT. A reason is a sentence; this is a
    number. Every arm the citation guard owns is run against the archive and its
    finding count is spent against a typed integer. OVER is rot that arrived
    after the last person looked. UNDER is a pin left slack once the archive
    shrank, which is banked room for an append nobody would have to defend -
    the direction :func:`forgiveness_budget_problems` learnt to check the hard
    way.

    IT IS WIDER THAN THE CLAUSE, WHICH IS THE POINT. The clause asks that the
    members the reason does not cover be recorded individually. Telling those
    members apart is CS-899, open and unsolved, and a keyword detector for it
    fails permissively - forgiving a real dead citation forever with nothing
    red. So this reddens on ANY new dead pointer in the archive, covered or
    not, and the discrimination is performed BY A HUMAN at the moment the pin
    is bumped. The arm is what forces that moment; it does not supply the
    judgement, and it must not be read as if it did.

    FOUR VACUITY LEGS, because a clean count is silence unless the sweep
    arrived. The archive must be TRACKED, must be inside the markdown
    population, must be OUTSIDE the line-pointer population - that exclusion is
    the whole thing being compensated for - and must still spell sites above a
    floor.
    """
    assert DEEP_ARCHIVE in test_docs_citations.UNGUARDED_DOCS, (
        f"{DEEP_ARCHIVE} is no longer recorded unguarded, so it is adjudicated like any"
        " other doc and this pin is a second, unneeded population."
    )
    assert DEEP_ARCHIVE in markdown_texts, (
        f"{DEEP_ARCHIVE} left the in-domain markdown population, so the boundary"
        " contracts stopped noticing the exemption at all."
    )
    assert DEEP_ARCHIVE not in line_pointer_carriers, (
        f"{DEEP_ARCHIVE} is now inside the line-pointer population, so the live arms"
        " judge it and this pin has become a second answer to the same question."
    )
    short = floor_problems(
        "citation sites in the deep archive", archive_sites(archive_text), _ARCHIVE_SITE_FLOOR
    )

    assert not short, NEWLINE.join(short) + " The sweep has stopped reading the archive."
    # THE REGISTRY WALKED IS THE ONE THAT WAS ALWAYS WALKED: the module this arm
    # was split out of, read through its module object rather than through the
    # name, so the split moved the arm and not the population. THE RESIDUAL IS
    # DISCLOSED: a tuple-keyed forgiveness declared in THIS module would go
    # unread here. There is exactly one table here, ARCHIVE_ROT, and it is keyed
    # by the arm names rather than by a carrier - so widening the walk
    # would change no verdict today, and doing it inside a slice whose job is a
    # file split would be doing two jobs.
    parent = vars(test_docs_citations)
    tupled = [
        name
        for name in test_docs_citations.FORGIVENESS_TABLES
        if any(isinstance(key, tuple) for key in parent[name])
    ]

    assert tupled, (
        "no registered forgiveness table is keyed by a carrier, so the check below walks"
        " nothing and its clean answer would be about no table at all"
    )
    keyed = sorted(
        f"  {name} answers a site carried by the archive: {key}"
        for name in test_docs_citations.FORGIVENESS_TABLES
        for key in parent[name]
        if isinstance(key, tuple) and key and key[0] == DEEP_ARCHIVE
    )

    assert not keyed, (
        "a live forgiveness table has started answering a site in the deep archive:"
        + NEWLINE
        + NEWLINE.join(keyed)
        + NEWLINE
        + ":func:`archive_rot` passes every table EMPTY, so that entry silences nothing"
        " and the pin still reports the site - but the exemption is now being answered in"
        " two places, and only one of them costs a number. Answer it in the pin."
    )
    judged = len(test_docs_citations.JUDGED_SHAPES)

    assert len(ARCHIVE_ROT) >= judged, (
        f"{len(ARCHIVE_ROT)} arms are counted against the archive and this family judges"
        f" {judged} shapes, so a shape has no arm here. A sixth shape added to"
        " JUDGED_SHAPES must bring an arm with it, or the exemption quietly starts hiding"
        " a population nothing counts - which is CS-897 itself, one shape along."
    )
    assert set(archive_rot_counts) == set(ARCHIVE_ROT), (
        "the measured arms and the pinned arms are not the same set:"
        f" measured {sorted(archive_rot_counts)}, pinned {sorted(ARCHIVE_ROT)}"
    )
    drifted = [
        f"  {arm}: {archive_rot_counts[arm]} found against a pin of {ARCHIVE_ROT[arm]}"
        for arm in sorted(ARCHIVE_ROT)
        if archive_rot_counts[arm] != ARCHIVE_ROT[arm]
    ]

    assert not drifted, (
        "the deep archive's rot has moved under its exemption:"
        + NEWLINE
        + NEWLINE.join(drifted)
        + NEWLINE
        + "OVER the pin is rot nobody has read: look at the new site, decide whether the"
        " recorded reason covers it, and bump the pin in the same change. UNDER it is a"
        " pin gone slack after a repair: lower it, or the room is banked for an append."
    )


def test_the_archive_rot_measure_reddens_on_a_new_dead_pointer_of_every_shape(
    archive_text: str,
    archive_rot_counts: Mapping[str, int],
    archive_rot_of: Callable[[str, Mapping[str, Sequence[str]] | None], dict[str, int]],
    file_lines: Mapping[str, Sequence[str]],
) -> None:
    """CS-897's third conjunct: the ARM, proved to redden per shape.

    THE PIN ALONE PROVES NOTHING ABOUT REACH. A measurement that agrees with a
    number reads identically whether every arm ran or whether all six returned
    zero and the pin was written to match - and that is not hypothetical here,
    because a future repair of the archive would make every pin legitimately
    zero and the agreement vacuous. So each shape is planted with a pointer
    THIS TREE CANNOT RESOLVE and the arm that owns it must move by exactly one
    while the other five stand still.

    A PLANTED POINTER IS EXACTLY THE MEMBER THE OLD REASON DID NOT DESCRIBE.
    It sits in no citation-guard detail block, its subject is not a pointer
    being dead, and it is dead all the same - which is the clause's "a dead
    citation the stated reason does not describe", posed six times.

    THE PLANTS ARE IN MEMORY AND ASSEMBLED AT CALL TIME. Nothing is written to
    a tracked doc, and no dead path or pointer is ever spelled adjacently in
    this module's own source - :func:`bare_path` and :func:`line_key` exist for
    that hazard and the self-infliction arm would report it if they did not.
    """
    synthetic = bare_path("clockspeed", "synthetic", "planted_mod.py")
    absent = bare_path("nowhere-this-repo-owns", "planted_mod.py")
    dead_module = bare_path("tests", "synthetic", "test_planted.py")
    planted_lines = dict(file_lines)
    planted_lines[synthetic] = ["", "def _a_live_declaration() -> None:", "    pass"]
    plants = (
        (_ROT_CITATION, f"Verification: {dead_module}::{_PLANTED_DEAD_NAME}."),
        (_ROT_RANGE, f"Filed at {line_key(absent, 1)}."),
        (_ROT_EMPTY, f"Filed at {line_key(synthetic, 1)}."),
        (_ROT_NAME, f"Verification: ::{_PLANTED_DEAD_NAME}."),
        (_ROT_PATH, f"Filed against `{bare_path('docs', _BARE_PLANT_LEAF)}`."),
        (_ROT_FORM, f"Filed at {line_key(synthetic, 2)}."),
    )

    assert {arm for arm, _text in plants} == set(ARCHIVE_ROT), (
        "a pinned arm has no plant, so the pin covers a shape nothing proves is read:"
        f" {sorted(set(ARCHIVE_ROT) - {arm for arm, _text in plants})}"
    )
    for arm, sentence in plants:
        counts = archive_rot_of(
            archive_text + NEWLINE + NEWLINE + sentence + NEWLINE, planted_lines
        )
        moved = {
            other: (counts[other], archive_rot_counts[other])
            for other in ARCHIVE_ROT
            if counts[other] != archive_rot_counts[other]
        }

        assert moved == {arm: (archive_rot_counts[arm] + 1, archive_rot_counts[arm])}, (
            f"planting one dead pointer of the shape {arm!r} did not move that arm by"
            f" exactly one and nothing else. Moved: {moved}. Either the arm does not"
            " reach the archive, or the plant is answered by a shape it was not written"
            " for and the pin is measuring something other than what it names."
        )


#: A typed pin and a derived one, as SOURCE, so the check below can be posed in
#: both directions without mutating this file. Strings rather than tables, so
#: neither reaches the container walk and neither is a fixture the arm has to
#: keep in step with the real pin.
_TYPED_PIN_SOURCE: Final = 'PIN: Final[Mapping[str, int]] = {"a": 3, "b": 0}' + NEWLINE
_DERIVED_PIN_SOURCE: Final = (
    'PIN: Final[Mapping[str, int]] = {"a": len(SOMETHING), "b": 0}' + NEWLINE
)
#: The same disarm in TWO statements - a typed decoy the walk once stopped at,
#: then a rebind to a call. Both statements are needed; either alone is clean.
_REBOUND_PIN_SOURCE: Final = (
    'PIN: Final[Mapping[str, int]] = {"a": 3}' + NEWLINE + "PIN = _derived()" + NEWLINE
)


def test_the_archive_rot_pin_is_typed_rather_than_computed_from_what_it_measures() -> None:
    """THE PERMANENT DISARM, AND FOR THIS PIN IT IS ONE LINE.

    :func:`derived_bound_problems` closes the same attack against a ceiling
    over a TABLE - it reports a bound whose expression mentions the table it
    bounds. :data:`ARCHIVE_ROT` bounds a FILE, so there is no registered name
    for that walk to see: a value written as a call would make the pin agree
    with the derivation by construction, in a diff carrying no number to query,
    and every leg of the arm above would still pass.

    FOUR DIRECTIONS BEFORE THE LIVE ONE. A typed synthetic source reports
    nothing; the same source with ONE value computed reports exactly one, which
    proves the walk parses, reaches module scope and fires; a name this module
    does not bind reports that it measured nothing rather than passing; and a
    typed decoy followed by a later rebind to a call reports both the second
    binding and the call, which is the TWO-statement form of the same disarm
    and read as clean until it was measured. Only then is the real source's
    clean answer worth reading.
    """
    assert literal_pin_problems(_TYPED_PIN_SOURCE, "PIN") == [], (
        "a pin whose values are typed integers was reported, so the check refuses the"
        " shape it exists to require"
    )
    derived = literal_pin_problems(_DERIVED_PIN_SOURCE, "PIN")

    assert len(derived) == 1, f"a computed pin value was not the single finding: {derived}"
    assert "len(SOMETHING)" in derived[0]
    missing = literal_pin_problems(_TYPED_PIN_SOURCE, "A_NAME_THIS_MODULE_DOES_NOT_BIND")

    assert len(missing) == 1, "a pin that is not there was reported as clean"
    assert "measured nothing" in missing[0]
    rebound = literal_pin_problems(_REBOUND_PIN_SOURCE, "PIN")
    # The second binding, and the call it rebinds to. Named, and named LOCALLY:
    # ruff's PLR2004 reads a bare 2 in the comparison as a magic value, and a
    # module-scope name would owe the container walk a registration.
    both_faults = 2

    assert len(rebound) == both_faults, f"a typed decoy plus a later rebind passed: {rebound}"
    assert "bound 2 times" in rebound[0]
    assert "_derived()" in rebound[1]

    problems = literal_pin_problems(Path(__file__).read_text(encoding="ascii"), "ARCHIVE_ROT")

    assert not problems, (
        "the deep archive's rot pin is not typed:"
        + NEWLINE
        + NEWLINE.join(f"  {problem}" for problem in problems)
    )


@pytest.mark.parametrize(
    ("what", "floor"),
    [
        ("citation sites in the deep archive", _ARCHIVE_SITE_FLOOR),
        ("modules in the archive-rot import cycle", _CYCLE_MODULE_FLOOR),
    ],
)
def test_every_non_vacuity_floor_rejects_a_population_that_measured_nothing(
    what: str, floor: int
) -> None:
    """THE FLOOR, GRADED - because it could be set to zero with the suite green.

    IT TRAVELLED WITH THE ARM THAT USES IT, and that is the whole reason this
    pair is here rather than left behind. :func:`graded_floor_names` derives what
    a module grades from that module's own USE SITES, so a floor whose
    :func:`floor_problems` call moved one file over would have been graded by
    nothing while the parametrization it left behind reported itself stale.

    THREE DIRECTIONS: nothing measured is rejected, one short is rejected, and
    the floor itself is accepted, so this is about the boundary rather than
    about the floor being large.
    """
    assert floor_problems(what, 0, floor), (
        f"the floor under {what} is {floor}, which ACCEPTS a population of nothing -"
        " the defect it exists to prevent, restored"
    )
    assert floor_problems(what, floor - 1, floor), f"the floor under {what} is off by one"
    assert floor_problems(what, floor, floor) == [], (
        f"the floor under {what} rejects a population that exactly meets it"
    )


def test_every_floor_this_module_uses_is_one_this_arm_grades() -> None:
    """CLOSING THE CLASS, so a SECOND floor here cannot arrive ungraded.

    The parametrization above is checked against what this module's SOURCE
    passes as a floor, rather than against a list somebody keeps in step by hand.
    """
    used = graded_floor_names(Path(__file__).read_text(encoding="ascii"))

    assert used, "this module passes no named floor to the floor check at all"
    graded = {"_ARCHIVE_SITE_FLOOR", "_CYCLE_MODULE_FLOOR"}
    ungraded = sorted(used - graded)

    assert not ungraded, (
        f"floors used but not graded: {ungraded}. Add each to the parametrization"
        " above, so a floor that could be zeroed is one something asks about."
    )
    stale = sorted(graded - used)

    assert not stale, f"graded floors this module no longer uses as floors: {stale}"


#: Wall-clock bound for the import probes below (CS-896). Each iteration is a
#: fresh interpreter plus a package import, and the loop runs once per module
#: in the cycle family, so this is a spawned-Python-child bound rather than a
#: git one - 300s, matching tests/test_locals_rendering.py. The bound is PER
#: CALL, so a family that grows does not erode the headroom of any one probe.
IMPORT_PROBE_TIMEOUT: Final = 300


def test_every_module_in_this_split_imports_first_without_a_cycle() -> None:
    """THE IMPORT CYCLE, ENTERED FROM EVERY SIDE, IN A FRESH INTERPRETER EACH TIME.

    THIS ARM EXISTS BECAUSE REASONING ABOUT IT GOT IT WRONG. The split makes the
    family a cycle by construction - the module that judges reaches the two
    halves so the class-closing walks can see them, and both reach back. Python
    tolerates that only while every name a partially-initialised module is asked
    for is already bound, which is a property of STATEMENT ORDER in three files
    at once. MEASURED at the moment this module was written: four entry orders
    imported cleanly and the FIFTH raised ImportError, so a suite that only ever
    enters through a ``test_*`` file was green over a real break.

    A FRESH INTERPRETER PER MODULE, because ``sys.modules`` is the whole
    subject. Importing a second module in a process that already imported the
    first proves nothing: the cycle is resolved before the second import begins.

    THE POPULATION IS DERIVED FROM THE IMPORT STATEMENTS rather than listed. A
    hand-list is right the day it is written and short the day a fourth module
    joins - the identical fault :func:`namespace_closure` exists to avoid one
    level up. The floor under it is what keeps a derivation that returned one
    module from reading as a clean answer about a cycle nobody entered.
    """
    family = sorted(
        {__name__, archive_rot_guard.__name__}
        | sibling_imports(Path(__file__).read_text(encoding="ascii"))
        | sibling_imports(Path(archive_rot_guard.__file__).read_text(encoding="ascii"))
    )
    short = floor_problems(
        "modules in the archive-rot import cycle", len(family), _CYCLE_MODULE_FLOOR
    )

    assert not short, NEWLINE.join(short) + (
        " The derivation has stopped reading the import statements, so the entries"
        " below are not the cycle this arm describes."
    )
    broken = []
    for dotted in family:
        done = subprocess.run(
            [sys.executable, "-c", f"import {dotted}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=IMPORT_PROBE_TIMEOUT,
        )
        if done.returncode:
            last = done.stderr.strip().splitlines()[-1] if done.stderr.strip() else "no stderr"
            broken.append(f"  importing {dotted} FIRST failed: {last}")

    assert not broken, (
        "a module in this split cannot be the first one imported:"
        + NEWLINE
        + NEWLINE.join(broken)
        + NEWLINE
        + "The cycle only resolves while every name a partially-initialised module is"
        " asked for is already bound. Move the offending import to the FOOT of the"
        " module that owns it, so its own names exist before it hands control away."
    )


#: EVERY FORGIVENESS TABLE THIS MODULE HOLDS, and the contract that BOUNDS it.
#: :data:`ARCHIVE_ROT` is a forgiveness in the only sense that matters - it is
#: the one place a finding against the deep archive may be answered - so it sits
#: here rather than in the derivation module, WITH the arm that bounds it. The
#: registry walk requires a bounded table's contract to be defined by the module
#: that holds the table, which is what keeps a pin and its defence from drifting
#: into different files.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {
    "ARCHIVE_ROT": "test_the_deep_archives_rot_is_measured_and_pinned_per_arm",
}

#: The other half of the same walk: every module-scope container that forgives
#: NOTHING, with the reason it does not.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "ARCHIVE_HEADER_CLAIMS": (
        "the deep archive's own header sentences its exemption must rest on; widening it"
        " can only demand more of the record"
    ),
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
}
