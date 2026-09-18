#!/usr/bin/env python3
"""CS-1121 - the arms that grade WHICH sites a disposition forgives.

WHY THIS MODULE EXISTS, and it is the size gate again rather than a design
idea, which is worth saying plainly. ``tests/test_docs_citations.py`` crossed
the approach band ``tests/data/test_phase2_gate.py`` holds every file under
``tests/`` to. That ceiling is a NON-NEGOTIABLE 2 GUARD - the one check that
catches a trimmed slice of real game data dropped into a fixture directory -
so raising it to fit prose launders a data-hygiene control for a code-size
reason, and shaving the prose is deletion in the CLAUDE.md section 4 sense for
arms whose reasoning IS the artifact. The guard's own remedy is RELOCATE, and
this is the relocation. It is the seam CS-1066 already established, used a
third time.

WHAT MOVED IS THE GRADING, NOT THE RULE. Every pattern, every derivation and
every table stays where it was; this module imports them and asserts about
them. Nothing here re-implements a traversal, which is the drift CS-1121 spent
two rounds paying for.

WHAT DID NOT MOVE, and the reason is a citation rather than a preference.
``docs/LEDGER.md`` cites three of the disposition arms by ``path::name``. An
arm that changes module makes its own record dead, inside the very guard that
judges dead records, so those three stayed put and only arms nothing cites
were relocated.

THE DEPENDENCY RUNS ONE WAY. This module imports
``tests/test_docs_citations.py``, which imports ``tests/test_citation_tables.py``.
Nothing imports back.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

import pytest

from tests import test_citation_tables as tables
from tests.bare_path_guard import BARE_PATH_RE
from tests.test_citation_tables import (
    DELIBERATE,
    LEDGER,
    NEWLINE,
    Disposition,
    bare_path,
)
from tests.test_citation_tables import (
    file_lines as _file_lines,
)
from tests.test_citation_tables import (
    line_pointer_carriers as _line_pointer_carriers,
)
from tests.test_citation_tables import (
    tracked as _tracked,
)
from tests.test_docs_citations import (
    UnanchoredCitationSiteError,
    citation_site_anchors,
    citation_site_identities,
    citation_site_offsets,
    citation_sites,
    disposition_site_problems,
    disposition_texts,
    judged_bare_hits,
)

# THE CORPUS FIXTURES, REBOUND UNDER THE NAMES PYTEST RESOLVES THEM BY. A
# fixture reaches a test through its own module namespace, so an import alias
# alone does not bind it - and the CHAIN has to come too: line_pointer_carriers
# requests file_lines, which requests tracked, and a fixture whose
# dependency is unbound here fails as "fixture not found" on the DEPENDENCY, not
# on the one the arm asked for. Measured on the first run of this module.
file_lines = _file_lines
line_pointer_carriers = _line_pointer_carriers
tracked = _tracked


#: The forgiveness CS-1121's proving arm swaps under. ASSEMBLED FROM HALVES
#: rather than spelled, for the reason :func:`tests.test_citation_tables.line_key`
#: gives - a full ``path::name``
#: written as one literal in this module is a real, resolvable citation sitting
#: inside the guard that judges citations. The two halves never sit adjacent in
#: the source, so no pattern reads them as one.
#:
#: PINNED RATHER THAN PICKED AT RUNTIME, because an arm that selected "any
#: single-site entry" would keep passing while quietly changing what it tested.
#: The arm re-derives this entry's sites and asserts there is exactly one
#: before it swaps anything.
_SWAP_VICTIM: Final = (
    bare_path("tests", "save", "test_properties.py")
    + "::"
    + "test_every_library_reaching_module_in_the_package_is_declared"
)

#: What the deleted half of the swap leaves behind. Carries no separator and no
#: ``test_`` prefix, so nothing reads the hole as a citation of its own.
_REDACTED_SITE: Final = "REDACTED-FORMER-SITE"

#: The sentence the within-heading swap re-adds the citation on. It must differ
#: from the line it replaces in more than whitespace, because
#: :func:`tests.test_docs_citations.landing_digest` strips before hashing - a
#: re-add that only reindented
#: would be the SAME site by construction and the swap would not be one.
_WITHIN_HEADING_PROSE: Final = "- A later sentence nobody adjudicated spends `{}` again."


def test_every_recorded_site_is_one_the_count_arm_also_sees(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The identity and the count cannot disagree, because ONE traversal answers both.

    STRUCTURAL TODAY AND ASSERTED ANYWAY, said plainly rather than left to read
    as a discovery: :func:`citation_sites` is the LENGTH of
    :func:`citation_site_offsets` and every identity comes from one of those
    offsets, so the two cannot differ while that holds. What it buys is the
    moment it stops - the first prototype of CS-1121 re-implemented the bare
    rule where the table lives, because the offsets were not exposed, and that
    copy reported THREE sites where this one reports one on a live key.

    GRADED PER ENTRY, NOT POOLED. A summed total is met by its strongest
    member, so every disagreement is collected by name.
    """
    texts = disposition_texts(line_pointer_carriers)

    disagreed: list[str] = []
    for doc, cited in tables.DISPOSITIONS:
        text = texts.get(doc, "")
        try:
            derived = len(citation_site_identities(text, cited))
        except UnanchoredCitationSiteError:
            # Reported by the sibling arm as a finding against this entry. Here
            # it is skipped rather than raised, for the same reason that one is
            # per entry: an unanchorable site must not stop the other entries
            # being graded.
            continue
        if derived != citation_sites(text, cited):
            disagreed.append(f"{doc} :: {cited}")
    disagreed.sort()

    assert disagreed == [], (
        "the identity derivation and the count arm read different populations, so"
        " the table's key and the table's audit disagree about the same doc:\n"
        + "\n".join(f"  {entry}" for entry in disagreed)
    )


def test_a_compensating_swap_that_keeps_the_site_count_is_reported(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """THE CROSS-HEADING SWAP, ON THE LIVE TABLE RATHER THAN A FIXTURE.

    ONE EDIT WITH TWO HALVES: the single adjudicated site of a real forgiveness
    is deleted and a brand-new dead citation of the SAME name is added under a
    new entry. The cardinality is asserted unchanged rather than assumed, so
    this is a statement about the KEY. Measured against the count-keyed
    predecessor: ``disposition_site_problems`` returned ``[]`` on this edit.

    BOTH HALVES MUST BE REPORTED, because an arm that noticed only the arrival
    would pass a swap that merely moved a site.
    """
    texts = dict(disposition_texts(line_pointer_carriers))
    victim = _SWAP_VICTIM
    original = texts[LEDGER]
    recorded = tables.DISPOSITIONS[(LEDGER, victim)]
    before = citation_site_identities(original, victim)
    assert before == recorded.at, (
        f"the swap subject's record does not match the live doc, so {victim} cannot"
        f" evidence anything: recorded {recorded.at}, derived {before}"
    )
    assert len(before) == 1, (
        f"the swap subject must be a SINGLE-site forgiveness or the deletion below is"
        f" ambiguous, and {victim} spells {len(before)}"
    )

    swapped = original.replace(victim, _REDACTED_SITE, 1)
    swapped += f"\n### CS-0000 - an entry nobody adjudicated\n\n- Verification: `{victim}`.\n"
    after = citation_site_identities(swapped, victim)
    assert len(after) == len(before), (
        "the swap did not balance, so a count-keyed table would have caught it and"
        f" this arm proves nothing about the identity: {before} -> {after}"
    )

    problems = disposition_site_problems({**texts, LEDGER: swapped}, tables.DISPOSITIONS)

    reported = [problem for problem in problems if victim in problem]
    assert len(reported) == 1, f"the compensating swap went unreported: {problems}"
    assert "1 unforgiven, 1 unspelled" in reported[0], (
        f"both halves of the swap must be named, not just its size: {reported[0]}"
    )


def test_the_same_table_and_corpus_without_the_swap_are_silent(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """THE ANTI-VACUITY CONTROL FOR THE ARM ABOVE, and it is not ceremony.

    An anti-vacuity guard has INVERTED an arm in this repository before - on a
    colliding fixture it made the pristine tree red and the mutated one green,
    so the "repair" would have shipped the defect. The two directions are
    therefore asserted separately: the unswapped corpus is silent about the
    swap subject, and the swapped one is not. A red here means the arm above
    reddens on something other than the swap and says nothing about the key.
    """
    texts = disposition_texts(line_pointer_carriers)

    problems = disposition_site_problems(texts, tables.DISPOSITIONS)

    assert [problem for problem in problems if _SWAP_VICTIM in problem] == [], (
        "the unswapped corpus already reports the swap subject, so the sibling arm's"
        f" red is not evidence about the compensating swap: {problems}"
    )


def test_a_within_heading_compensating_swap_is_reported_at_every_entry(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """THE ACCEPTANCE'S CONFIGURATION AT ITS HARDEST, GRADED PER ENTRY.

    The acceptance does not say WHERE the swap happens, and the first build of
    CS-1121 met it only ACROSS headings - measured on this table then, every
    entry was silent under this configuration, because the identity was the
    heading and a site deleted and re-added beneath the same one keeps it.
    :attr:`tables.Disposition.at` carries that history; this arm is the
    configuration that measures it.

    GRADED PER ENTRY AND COLLECTED BY NAME, NEVER POOLED. A population-summed
    threshold is met by its strongest member, so a pooled count would read
    green while the weakest entry was silent.

    THE SAME-SECTION ORACLE IS ADJACENCY, AND NOTHING ELSE. That matters
    because the common-mode risk is real: the heading derivation is the shared
    input to the identity, to
    :attr:`tests.bare_path_guard.BarePathSite.identity` AND to the arm that
    measured the collapse, so nothing routed through it can observe its own
    granularity being wrong - which is how a whole table of silent entries hid
    under a green suite twice. Here the re-added site goes on the line
    IMMEDIATELY AFTER the deleted one, so there are ZERO lines between them and
    no heading of any spelling - ``#``, setext underline or otherwise - can
    separate the two. The argument is arithmetic on line numbers, not a rule
    about what a heading looks like. An earlier version of this docstring
    claimed a raw ``#`` scan carried it; that scan inspected the line the loop
    had just inserted and could never fail, and it is gone.

    THE CARDINALITY IS ASSERTED UNCHANGED at every entry, so each is a
    statement about the KEY and not about the size of the edit.
    """
    texts = disposition_texts(line_pointer_carriers)
    # The ONE precondition the adjacency argument rests on, checked once here
    # rather than pretended to per entry. A per-entry scan for a heading
    # "between the halves" used to sit in the loop below; it inspected the line
    # the loop had just inserted - this constant - so it could never fail, and
    # a check that cannot fail is worse than no check because it reads as one.
    assert not _WITHIN_HEADING_PROSE.startswith("#"), (
        "the re-added line must not itself be a heading, or the two halves of the"
        " swap no longer share a section and this arm tests the cross-heading case"
    )
    silent: list[str] = []
    unbalanced: list[str] = []
    for doc, cited in sorted(tables.DISPOSITIONS):
        text = texts.get(doc, "")
        offsets = citation_site_offsets(text, cited)
        if not offsets:
            unbalanced.append(f"{doc} :: {cited} - the doc spells no site to swap")
            continue
        lines = text.split(NEWLINE)
        index = text.count(NEWLINE, 0, offsets[0])
        lines[index] = lines[index].replace(cited, _REDACTED_SITE)
        lines.insert(index + 1, _WITHIN_HEADING_PROSE.format(cited))
        swapped = NEWLINE.join(lines)
        if citation_sites(swapped, cited) != len(offsets):
            unbalanced.append(f"{doc} :: {cited} - the swap did not balance")
            continue
        reported = disposition_site_problems({**texts, doc: swapped}, tables.DISPOSITIONS)
        if not [problem for problem in reported if cited in problem]:
            silent.append(f"{doc} :: {cited}")

    assert unbalanced == [], (
        "the swap could not be posed at some entries, so their silence would prove"
        " nothing either way:\n" + "\n".join(f"  {entry}" for entry in unbalanced)
    )
    assert silent == [], (
        "a within-heading compensating swap went unreported. The forgiveness is keyed"
        " on something these two sites share, so an unadjudicated citation rides under"
        " it:\n" + "\n".join(f"  {entry}" for entry in silent)
    )


def test_the_same_entries_without_the_within_heading_swap_are_silent(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """THE ANTI-VACUITY CONTROL FOR THE ARM ABOVE, over the SAME population.

    An anti-vacuity guard in this project once made the pristine tree RED and
    the mutated one GREEN on a colliding fixture, so the "repair" would have
    shipped the defect. The arm above would read identically if the table were
    simply broken for every entry - every swap would report, and so would every
    non-swap. This asserts the other direction over the same population, which
    it takes from the table rather than naming a size: with no swap made, not
    one entry is reported.
    """
    texts = disposition_texts(line_pointer_carriers)
    problems = disposition_site_problems(texts, tables.DISPOSITIONS)

    reported = sorted(
        f"{doc} :: {cited}"
        for doc, cited in tables.DISPOSITIONS
        if any(cited in problem for problem in problems)
    )

    assert reported == [], (
        "the unswapped table already reports these entries, so the sibling arm's red"
        " is not evidence about any swap:\n" + "\n".join(f"  {entry}" for entry in reported)
    )


def test_a_site_above_the_first_heading_raises_rather_than_digesting_nothing() -> None:
    """AN UNIDENTIFIABLE SITE IS REFUSED, not folded into one shared value.

    :func:`citation_site_identities` gives the mechanism. BOTH DIRECTIONS here,
    because a guard that raised on everything would pass this for the wrong
    reason: the same citation moved BELOW a heading identifies without
    complaint.
    """
    cited = "test_a_name_that_is_not_bound"
    spelling = f'grep -c "{cited}" x\n'

    with pytest.raises(UnanchoredCitationSiteError):
        citation_site_identities(spelling, cited)

    anchored = citation_site_identities(f"## An entry\n\n{spelling}", cited)
    identified_cleanly = len(anchored) == 1 and all(anchored)
    assert identified_cleanly, (
        "the same site below a heading must identify cleanly, or the refusal above"
        f" says nothing about the missing anchor: {anchored}"
    )


def test_every_offset_indexes_the_name_it_found(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The blanking preserves offsets, asserted DIRECTLY and over no fixed figure.

    :func:`judged_bare_hits` matches against a blanked copy and returns offsets
    meant to index the ORIGINAL, which holds only while the blanking is
    length-preserving. The property is checked directly - at every offset the
    original text spells the identifier the offset is paired with - rather than
    by the spelled population size that used to carry it. A collapse back to
    one space breaks this on the first carrier holding a full citation before a
    bare name; so did reporting an elided match's start instead of its name's.

    THE POPULATION IS DERIVED, NOT SPELLED, and asserted NON-EMPTY, because a
    walk over nothing passes for that reason - an oracle that cannot observe
    its subject passes blind.
    """
    checked = 0
    wrong: list[str] = []
    for carrier, text in sorted(disposition_texts(line_pointer_carriers).items()):
        for offset, name in judged_bare_hits(text):
            checked += 1
            if text[offset : offset + len(name)] != name:
                wrong.append(f"{carrier}: offset {offset} does not spell {name}")

    assert checked, "no carrier spelled a judged bare name, so this walk observed nothing"
    assert wrong == [], (
        "an offset does not index the name it was found for, so every line and heading"
        " derived from one names the wrong place:\n" + "\n".join(f"  {line}" for line in wrong)
    )


def test_two_byte_identical_siblings_under_one_heading_are_told_apart() -> None:
    """THE ORDINAL IS LOAD-BEARING, which is the last case the two digests share.

    Both halves of the identity are content, so two spellings of one citation on
    BYTE-IDENTICAL lines under the same heading agree on both. Without the
    ordinal they would be one identity, and deleting one of them would be
    invisible - the cardinality argument all over again at the narrowest
    granularity there is.

    WHY IT IS NOT A LINE NUMBER FOR DRIFT PURPOSES is argued at
    :attr:`tables.Disposition.at`. BOTH DIRECTIONS here: the twin doc yields
    two DISTINCT identities, and dropping one sibling is reported against a
    record cut from the twin.
    """
    cited = "test_a_name_that_is_not_bound"
    spelling = f'grep -c "{cited}" x'
    twin = f"## An entry\n\n{spelling}\n{spelling}\n"
    single = f"## An entry\n\n{spelling}\n"

    identities = citation_site_identities(twin, cited)

    assert len(set(identities)) == len(identities) == len(citation_site_offsets(twin, cited)), (
        f"byte-identical siblings collapsed to one identity: {identities}"
    )
    record = {("ROADMAP.md", cited): Disposition(DELIBERATE, "", "dead", identities)}
    assert disposition_site_problems({"ROADMAP.md": twin}, record) == [], (
        "the record does not match the doc it was cut from, so the report below"
        " proves nothing about the dropped sibling"
    )
    dropped = disposition_site_problems({"ROADMAP.md": single}, record)
    named_the_loss = len(dropped) == 1 and "0 unforgiven, 1 unspelled" in dropped[0]
    assert named_the_loss, f"dropping one of two identical siblings went unreported: {dropped}"


def test_one_heading_text_under_two_parents_is_two_identities() -> None:
    """CS-1121'S SECOND REFUTATION, ANSWERED: an INSTANCE, not a text.

    The identity keyed on the nearest heading alone, and live docs repeat
    heading text hard - one item-notes leaf spells a single ``### detail``
    sub-heading under many distinct ``## CS-nnn`` sections. Deleting a
    forgiven site and re-adding the identical line under a DIFFERENT section
    left the identity byte-for-byte equal, so the acceptance's own swap was
    silent. Measured on the live table before this repair.

    BOTH DIRECTIONS. The two sites differ under the chain, AND the swap between
    them is now a finding naming both halves - where the nearest-heading key
    reported nothing at all.
    """
    cited = "test_a_name_that_is_not_bound"
    spelling = f'grep -c "{cited}" x'
    first = f"## CS-440\n\n### detail\n\n{spelling}\n"
    second = "## CS-400\n\n### detail\n\nnothing here yet\n"

    identities = citation_site_identities(first + second, cited)
    moved = citation_site_identities(
        f"## CS-440\n\n### detail\n\nREDACTED\n## CS-400\n\n### detail\n\n{spelling}\n", cited
    )

    assert len(identities) == 1, identities
    assert identities != moved, (
        "the same line under a different parent section produced the same identity,"
        f" so a site moved between sections is invisible: {identities} == {moved}"
    )
    record = {("ROADMAP.md", cited): Disposition(DELIBERATE, "", "dead", identities)}
    assert disposition_site_problems({"ROADMAP.md": first + second}, record) == [], (
        "the record does not match the doc it was cut from, so the report below"
        " proves nothing about the move"
    )
    swapped = disposition_site_problems(
        {
            "ROADMAP.md": (
                f"## CS-440\n\n### detail\n\nREDACTED\n## CS-400\n\n### detail\n\n{spelling}\n"
            )
        },
        record,
    )
    named_both = len(swapped) == 1 and "1 unforgiven, 1 unspelled" in swapped[0]
    assert named_both, f"the cross-section swap went unreported or unnamed: {swapped}"


def test_a_sibling_under_another_chain_does_not_move_the_ordinal() -> None:
    """THE MEASURED HALF OF :attr:`tables.Disposition.at`'S ORDINAL CLAIM.

    The sentence that stood there said the ordinal moved only for a
    byte-identical sibling under the same heading, and a byte-identical line
    under a DIFFERENT section moved it anyway - a recorded ``...:0`` silently
    came to name an unadjudicated arrival. The chain repaired that. This is the
    regression guard, in both directions: a sibling under another chain leaves
    the ordinal alone, and one under the SAME chain moves it.
    """
    cited = "test_a_name_that_is_not_bound"
    spelling = f'grep -c "{cited}" x'
    base = f"## Section A\n\n### detail\n\n{spelling}\n"

    elsewhere = citation_site_identities(
        f"## Section Z\n\n### detail\n\n{spelling}\n\n{base}", cited
    )
    alongside = citation_site_identities(
        f"## Section A\n\n### detail\n\n{spelling}\n{spelling}\n", cited
    )

    assert elsewhere[-1] == citation_site_identities(base, cited)[0], (
        f"a sibling under a different chain moved the ordinal: {elsewhere}"
    )
    assert alongside[-1] != alongside[0], (
        f"a sibling under the SAME chain did not move the ordinal: {alongside}"
    )


def test_a_reorder_of_two_sections_is_not_a_finding() -> None:
    """The comparison is a MULTISET, and that is a decision, not an accident.

    It was an ordered tuple while the docstring said multiset. The two disagree
    on exactly one input - two sections swapping places - which the ordered
    form called a problem and then described as "0 unforgiven, 0 unspelled", a
    finding naming nothing. A reorder changes neither which citations are
    forgiven nor where any site sits relative to its own chain.

    BOTH DIRECTIONS, so this is not an argument for a guard that never fires:
    the reorder is silent, and deleting one of the two reordered sites is not.
    """
    cited = "test_a_name_that_is_not_bound"
    spelling = f'grep -c "{cited}" x'
    first = f"## Section A\n\n{spelling}\n"
    second = f"## Section B\n\nsee {spelling} again\n"
    record = {
        ("ROADMAP.md", cited): Disposition(
            DELIBERATE, "", "dead", citation_site_identities(first + second, cited)
        )
    }

    assert disposition_site_problems({"ROADMAP.md": second + first}, record) == [], (
        "swapping two whole sections was reported as a drift, though every site"
        " still sits under the same chain on the same line"
    )
    dropped = disposition_site_problems({"ROADMAP.md": second}, record)
    named_the_loss = len(dropped) == 1 and "0 unforgiven, 1 unspelled" in dropped[0]
    assert named_the_loss, f"deleting one of the reordered sites went unreported: {dropped}"


def test_one_unanchorable_site_does_not_abort_the_other_entries() -> None:
    """The refusal is a FINDING against its entry, not a whole-run abort.

    :class:`UnanchoredCitationSiteError` propagating out of the comparison took
    down every consuming arm as an ERROR, so a single unanchorable site
    anywhere in the corpus stopped the whole table being graded - and a
    forgiveness for a dead citation in a carrier with no heading above it was
    simply unrecordable. No live doc trips it today, which is exactly the
    condition under which such a landmine ships.

    BOTH DIRECTIONS: the unanchorable entry IS reported, and the healthy entry
    beside it is still graded rather than swallowed.
    """
    cited = "test_a_name_that_is_not_bound"
    spelling = f'grep -c "{cited}" x'
    healthy = f"## An entry\n\n{spelling}\n"
    record = {
        ("ROADMAP.md", cited): Disposition(DELIBERATE, "", "dead", ("deadbeef:deadbeef:0",)),
        ("BACKLOG.md", cited): Disposition(
            DELIBERATE, "", "dead", citation_site_identities(healthy, cited)
        ),
    }

    problems = disposition_site_problems({"ROADMAP.md": spelling, "BACKLOG.md": healthy}, record)

    assert len(problems) == 1, (
        f"the unanchorable site was not reported as exactly one finding: {problems}"
    )
    named_the_carrier = "ROADMAP.md" in problems[0] and "no enclosing chain" in problems[0]
    assert named_the_carrier, problems[0]


def test_the_digest_is_not_cosmetic_because_the_anchors_carry_paths(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The reason for digesting is RE-MEASURED rather than spelled as a figure.

    :attr:`tables.Disposition.at` gives the reason; this measures it. A prose
    sentence once gave the population as a number and two readers disagreed
    about it, so no figure is written down - only that the population is not
    empty, which is what makes the digest load-bearing rather than decorative.
    """
    texts = disposition_texts(line_pointer_carriers)

    carriers = [
        anchor
        for doc, cited in tables.DISPOSITIONS
        for anchor in citation_site_anchors(texts.get(doc, ""), cited)
        if BARE_PATH_RE.search(anchor)
    ]

    assert carriers, (
        "no live heading spells a bare repo-relative path any more, so the reason this"
        " identity is digested rather than stored verbatim no longer holds. Re-argue"
        " the digest or drop it - do not leave the docstring asserting a dead reason."
    )
