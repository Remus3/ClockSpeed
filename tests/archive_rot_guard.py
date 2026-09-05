"""CS-897 - the deep archive's rot, derived one module away from the arms.

WHY THIS MODULE EXISTS. ``tests/test_docs_citations.py`` exempts one file from
every arm it owns - the deep archive, whose pointers rot BY CONSTRUCTION - and
CS-897 answered that exemption by MEASURING what it hides rather than by
widening the sentence that grants it. The measurement is six arm runs against
one file, and it is derivation: a pure function of an injected corpus, with no
assertion in it. The pin those numbers are spent against, and the four arms that
spend them, live in ``tests/test_archive_rot.py``.

THE SPLIT IS FOR SIZE AND THE SIZE IS A DATA-HYGIENE CONTROL. Every file under
``tests/`` is held under a ceiling by
``tests/data/test_phase2_gate.py::test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data``,
whose subject is a trimmed slice of real game data dropped in "just for tests".
That ceiling is not raised to make room for prose. The module that judges
citations had 1483 bytes of headroom left, so the cleanest seam in it was moved
out whole - 28 references out of the archive machinery into its host, three back.

WHAT THIS FILE MAY AND MAY NOT HOLD. Derivation only, and the registry pair
below says so in a form something checks: this module declares
:data:`FORGIVENESS_TABLES` EMPTY, and every module-scope container it holds must
sit in that mapping or in :data:`NOT_A_FORGIVENESS`. The walk is
``tests/test_bare_path_citations.py``'s, over a population derived from the
import graph, so a forgiveness table relocated into this file is as red here as
it would be in the module it came from. RELOCATION IS THE SAME EVASION AS
NAMING, and a file split is the door that opens it.

THE IMPORT BACK INTO THE MODULE THAT JUDGES IS ABSOLUTE AND IT IS LOAD-BEARING.
:func:`sibling_imports` reads import STATEMENTS out of source and keeps the ones
naming a module under the tests package; a relative ``from . import x`` produces
no such name and is a disclosed hole in that walk. Everything below is imported
by its dotted path for that reason and not for taste.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Final

from tests.bare_path_guard import bare_path_ladder, bare_path_problems, bare_path_sites

# CS-897 - AN EXEMPTION'S REASON MUST BE TRUE OF EVERY MEMBER, AND THAT ONE IS
# NOT. The reason UNGUARDED_DOCS records for the deep archive once described a
# pointer spelled INSIDE a citation-guard detail block whose subject is that
# pointer being dead - quoting rather than citing. Measured against the
# archive as it stands, that describes TWO of the sites and none of the rest: a
# failed-paths note about a harness file written and removed, a plain "that leaf
# records this" reference, five dead path-and-symbol citations, three line
# pointers landing on nothing, three identifiers this tree binds nowhere. The
# reason was true when the exemption was written about the sites it was written
# about, and it silently acquired a population it does not describe.
#
# DISCRIMINATING QUOTING FROM CITING IN MARKDOWN IS CS-899, WHICH IS OPEN. A
# keyword or negation detector was priced and REFUSED: it fails in the
# PERMISSIVE direction, so a real dead citation is forgiven forever with
# nothing red - the laundering this family of guards exists to prevent, bought
# for a regex. What ships instead sidesteps that question rather than answering it.
#
# THE REASON IS RESTATED SO IT IS TRUE OF EVERY MEMBER, AND THE POPULATION IS
# PINNED. The archive's pointers rot BY CONSTRUCTION - it preserves text
# written against trees that no longer exist - and that is true of all of them
# without asking what any one sentence MEANS. The reason is anchored to
# sentences the file's own header carries, checked in both directions by
# test_the_deep_archive_exemption_rests_on_the_claim_its_own_header_makes.

#: The sentences the deep archive's own header spells that the exemption's
#: reason RESTS ON, and which the reason must therefore quote. Checked in both
#: directions: the header must still say it, and the record must still say it.
#: An exemption argued from a file's declared status is only as good as the
#: declaration, so the declaration is not taken on trust - WAKEUP_NOTES.md is
#: the precedent, recorded unguarded on a reason nothing verified and evicted
#: by the first run that did.
#:
#: SPELT SHORT OF A LINE BREAK. The header wraps mid-sentence, so a claim
#: carried to the end of its sentence would never match the file it is read
#: out of - measured, on the third one.
ARCHIVE_HEADER_CLAIMS: Final = (
    "Section status: HISTORICAL",
    "holds NOTHING current",
    "may be cited as the present state",
)

#: How much of the archive counts as its HEADER. The claims above are its
#: standing declaration about itself, so a match 4000 lines down inside a
#: quoted note would not be the declaration at all.
_ARCHIVE_HEADER_LINES: Final = 30

#: The floor under the archive's judged-site population, so the pin that spends
#: this derivation cannot read as an answer when the sweep stopped reading the
#: file. A FLOOR ON
#: SITES RATHER THAN ON FINDINGS, and the difference is what keeps it from
#: fighting a repair: a repaired pointer is still a site, so this number does
#: not fall when the archive is cleaned up, and it does fall to zero the moment
#: the sweep stops arriving.
#:
#: HOW IT WAS CHOSEN. 639 sites measured across the five shapes, the largest
#: single shape contributing 410 of them. This sits above 639 minus that shape,
#: so losing ANY ONE shape entirely reddens rather than passing quietly.
_ARCHIVE_SITE_FLOOR: Final = 550

#: The six answers this family's arms would give about the deep archive, one
#: per arm. Declared HERE, with the derivation that produces them, so the pin
#: one module over and the measure cannot disagree about what an arm is called.
#: NAMED rather than positional, so a count moving between arms cannot be
#: absorbed by a total that stays the same.
_ROT_CITATION: Final = "dead path-and-symbol citations"
_ROT_RANGE: Final = "line pointers out of range or at an untracked path"
_ROT_EMPTY: Final = "line pointers landing on nothing"
_ROT_NAME: Final = "bare and elided identifiers bound nowhere"
_ROT_PATH: Final = "bare paths resolving nowhere"
_ROT_FORM: Final = "line pointers at a tracked module in the refused form"


def archive_sites(text: str) -> int:
    """How many sites of ANY judged shape the deep archive spells.

    THE NON-VACUITY MEASUREMENT, and it reads :data:`JUDGED_SHAPES` rather
    than a list of its own for the reason the boundary contract does: a SIXTH
    shape added to the module that judges would otherwise leave this number
    describing a narrower file than the one the pin is taken over.

    Args:
        text: The archive's scoped text.

    Returns:
        The total across every shape. Overlapping matches are counted once per
        shape and a site may be seen by two shapes - which is right for a floor
        asking whether the sweep ARRIVED, and would be wrong for a pin.
    """
    return sum(len(shape.findall(text)) for shape in JUDGED_SHAPES)


def archive_rot(
    text: str,
    sources: Mapping[str, str],
    file_lines: Mapping[str, Sequence[str]],
    known_names: Iterable[str],
    module_basenames: Iterable[str],
    tracked: Iterable[str],
    declared_untracked: Iterable[str],
    roots_of_source: Iterable[str],
) -> dict[str, int]:
    """Run every arm the module that judges has against the deep archive, and COUNT.

    THE EXEMPTION'S POPULATION, DERIVED. :data:`UNGUARDED_DOCS` takes the
    archive out of every live arm, so until this function existed the size of
    what that bought was unmeasured - and an exemption whose population nobody
    measures is how a reason that was true of two sites ends up covering
    twenty-eight.

    EVERY FORGIVENESS TABLE IS PASSED EMPTY, DELIBERATELY. No live table
    CARRIES an archive site - the archive has never been in a population that
    could key one - so injecting them would change nothing today and would hand
    a future agent a one-line silencer for a finding this measure exists to
    surface. The pin is the only place an archive finding may be answered, and
    a pin bump is a number in the diff.

    THAT CLAIM IS CHECKED RATHER THAN STATED HERE, by a leg of
    ``test_the_deep_archives_rot_is_measured_and_pinned_per_arm``, because a
    sentence about a table's contents is exactly the fault this family exists
    to find. It needed to be: three keys DO spell the archive, all three inside
    an ANCHOR - the heading a note was relocated out from under - which is a
    carrier's heading text and never a key this measure would consult. Read as
    prose, "the archive is in none of them" is false; read as the question that
    matters, whose carrier is the archive, it is true.

    A PURE FUNCTION OF ITS ARGUMENTS, for :func:`bare_path_ladder`'s reason:
    every input is injected, so a control can plant a dead citation of each
    shape and prove the corresponding arm fires rather than merely that the
    live corpus sits where the pin says.

    Args:
        text: The archive's scoped text.
        sources: Repo-relative path to module text, for the resolver.
        file_lines: Every tracked file's lines, for the line-pointer arms.
        known_names: Every name bound at module scope anywhere in the tree.
        module_basenames: Tracked module basenames, so a module is not read as
            a test.
        tracked: Every path in the index, for the bare-path ladder's R0.
        declared_untracked: What the repo declares it will never track, R2.
        roots_of_source: R1's candidate set.

    Returns:
        One count per arm, keyed by the :data:`ARCHIVE_ROT` names.
    """
    line_counts = {path: len(lines) for path, lines in file_lines.items()}
    ranged, _declined = line_pointer_problems(text, line_counts)
    py_sites, other_sites = line_pointer_sites({DEEP_ARCHIVE: text}, file_lines)
    empty, forbidden = line_pointer_content_problems(py_sites, other_sites, sources, {}, {})
    answered = bare_path_ladder(
        bare_path_sites({DEEP_ARCHIVE: text}), tracked, declared_untracked, {}, roots_of_source
    )
    return {
        _ROT_CITATION: len(unresolved_citations(DEEP_ARCHIVE, text, sources, {})),
        _ROT_RANGE: len(ranged),
        _ROT_EMPTY: len(empty),
        _ROT_NAME: len(bare_name_problems(DEEP_ARCHIVE, text, known_names, module_basenames, {})),
        _ROT_PATH: len(bare_path_problems(answered)),
        _ROT_FORM: len(forbidden),
    }


#: EVERY FORGIVENESS TABLE THIS MODULE HOLDS, and the contract that BOUNDS it.
#: EMPTY, WHICH IS A CLAIM AND NOT AN ABSENCE - this module derives, it does not
#: forgive, and the pin the derivation is spent against is one file over with the
#: arm that spends it. The claim is checked rather than trusted: every container
#: here must sit in this mapping or in :data:`NOT_A_FORGIVENESS`, so a table
#: added here has to be registered before the suite is green, and registering it
#: here demands a contract this module defines - which a derivation module has
#: none of, and that is the point.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {}

#: The other half of the same walk: every module-scope container that forgives
#: NOTHING, with the reason it does not. Recorded rather than filtered, for the
#: reason the unguarded-doc record is recorded - a filter is a boundary nobody
#: re-derives, and the next container that happens to match it joins the
#: unwalked set in silence.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "ARCHIVE_HEADER_CLAIMS": (
        "the deep archive's own header sentences its exemption must rest on; widening it"
        " can only demand more of the record"
    ),
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "JUDGED_SHAPES": "widens what counts as a citation; adding to it can only add findings",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
}


# THE ONE EDGE THAT CLOSES THE IMPORT CYCLE, AND ITS PLACEMENT IS MEASURED
# RATHER THAN REASONED ABOUT. The family is a cycle by construction: the module
# that judges reaches this one so the class-closing walks can see it, and this
# one reaches back for the arms it runs. Python tolerates a cycle only when
# every name a partially-initialised module is asked for is already bound, and
# at the TOP of this file that is false in one entry order - importing this
# module FIRST starts the parent, whose own foot import starts the arms module,
# which then asks this one for names it has not reached yet. MEASURED, on that
# exact order: ImportError, "cannot import name _ARCHIVE_HEADER_LINES from
# partially initialized module". Four of the five entry orders were clean, which
# is why reasoning about it was not enough and
# test_every_module_in_this_split_imports_first_without_a_cycle exists.
#
# AT THE FOOT, every name above is bound before this statement can hand control
# to anything, so no importer of this module can be asked for a name it has not
# reached. E402 is answered by that, not waved through, and every function above
# resolves these names at CALL time - by which point the statement has run.
from tests.test_docs_citations import (  # noqa: E402
    DEEP_ARCHIVE,
    JUDGED_SHAPES,
    bare_name_problems,
    line_pointer_content_problems,
    line_pointer_problems,
    line_pointer_sites,
    unresolved_citations,
)
