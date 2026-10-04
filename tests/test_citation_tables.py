#!/usr/bin/env python3
"""CS-1066 - the citation family's tables, corpus and budgets.

WHY THIS MODULE EXISTS, and the reason is the size gate rather than a design
one - which is worth saying plainly instead of inventing a nobler motive after
the fact. ``tests/test_docs_citations.py`` reached 4 bytes under the ceiling
``tests/data/test_phase2_gate.py`` holds every file under ``tests/`` to, and
that ceiling is a NON-NEGOTIABLE 2 GUARD: it is the one check that catches a
trimmed slice of real game data dropped into a fixture directory, which no
content assertion would catch because a real slice parses perfectly. Raising it
to fit prose would launder a data-hygiene guard for a code-size reason, and
shaving the prose is deletion in the CLAUDE.md section 4 sense for a module
whose reasoning IS the artifact. So the module was split a second time, on the
seam ``tests/bare_path_guard.py`` already established.

WHAT MOVED IS THE RECORD AND THE CORPUS, NOT THE JUDGEMENT. Every table that
FORGIVES something is here, with the budget that bounds it and the contract that
spends the budget; so is the live corpus those tables are checked against. The
arms that judge citations stay where they were and import what they need. No
test identifier changed in the move, and the collected count is asserted equal
either side of it.

WHY THE BUDGETS AND THEIR CONTRACTS TRAVELLED WITH THE TABLES, which is a
mechanism rather than tidiness. :func:`tests.bare_path_guard.registry_problems`
requires a bounded table's contract to be a ``test_``-prefixed callable defined
in the SAME namespace as the table. A table relocated here whose contract stayed
one file over would be registered against a name this module does not define,
which that walk reports - so the pairing is enforced rather than remembered.

THE DEPENDENCY RUNS ONE WAY, DELIBERATELY. Nothing here imports
``tests/test_docs_citations.py``. That module imports this one at its top,
takes the CONTAINERS through the module object and the FUNCTIONS and FIXTURES by
name, and the asymmetry is what keeps the third member of this family out of the
import cycle the other two already have to prove they survive.

AND TAKING THE CONTAINERS THROUGH THE MODULE OBJECT IS NOT STYLE. An imported
container lands in the importing module's ``globals()``, where its own container
walk finds it and demands a registry row - so a table bounded HERE would need a
second contract THERE, which is two places for one ratchet to drift. The alias
form keeps each table answered exactly once, and what that costs - a table this
module holds being invisible to the single-module walk - is already paid by
``tests/test_bare_path_citations.py``, which walks every module in the closure
over a population derived from the import graph.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import pytest

from tests.bare_path_guard import (
    DECLARED_ABSENT,
    DECLARED_UNTRACKED,
    FIXTURE_LITERAL,
    REPO_ROOT,
    UNTRACKED_ROOT,
    BarePathReason,
    BarePathSite,
    bare_path_budget_problems,
    bare_path_ladder,
    bare_path_sites,
    declares_untracked,
    pinned_rung_problems,
    source_roots,
)

# The ledger is scoped to its entries. The two pairs above the heading are the
# preamble's ILLUSTRATIVE pointers - they show the shape of a valid citation and
# name no real test - so judging them would redden the documentation of the rule.
LEDGER: Final = "docs/LEDGER.md"
ENTRIES_HEADING: Final = "## Entries"

#: The Python packaging manifest, read by :func:`source_roots` for the roots
#: this repository declares it ships. Carries no separator, so the bare-path
#: shape - which requires one - does not read this literal as a citation.
MANIFEST: Final = "pyproject.toml"

#: One newline, bound rather than spelled inline, so a message assembled from a
#: list reads the same in every arm that builds one.
NEWLINE: Final = "\n"


# `.claude/` is OUT OF DOMAIN rather than exempt. It is Claude Code
# configuration, it appears nowhere in the CLAUDE.md doc-topology table, and
# its prose instructs an agent rather than recording a verification. A guard
# that reddened on a harness-config edit would be reddening on something that
# is not documentation at all.
OUT_OF_DOMAIN: Final = ".claude/"

# Dated material, excluded from every search for current truth by CLAUDE.md
# section 4. Named so the CS-889 boundary control can assert on it rather than
# spell it inline.
DATED_ARCHIVE: Final = "docs/_archive/"

# THE BOUNDARY OF THE GUARDED SET, which until now nothing re-derived.
# GUARDED_DOCS is a hand-maintained tuple, so a doc that STARTS carrying
# citations joins the unguarded set in silence - which is this module's own
# founding finding, "nothing in this repository read docs/", repeating one
# level up. So every in-domain markdown file carrying a citation is either
# guarded or RECORDED here with its reason, and the record is checked in BOTH
# directions: an entry for a doc that has since been guarded, or that no longer
# carries a citation, FAILS. Nothing may join this set quietly and nothing may
# linger in it after it stops being needed.
#
# MEASURED, NOT ASSUMED, AND THE MEASUREMENT EVICTED A MEMBER. The first run of
# that contract reported TWO carriers the item had recorded one of, and
# WAKEUP_NOTES.md was written in here on the reason "every citation in it
# resolves today". THAT REASON WAS FALSE ON ITS FIRST RUN: WAKEUP_NOTES.md
# spends test_the_header_scan_advertises_no_bound_it_cannot_enforce, which this
# tree binds nowhere and which DISPOSITIONS below already recorded as dead
# under the ledger key. An exemption table nothing verifies is precisely how a
# false declaration ships, and this one shipped inside the module that says so.
#
# It was not repaired in prose. The file was GUARDED, at a cost of one
# disposition, and the record deleted - so the archive is the only member, and
# a contract below keeps it the only one.

#: The deep archive, named ONCE so the exemption, the boundary contracts and
#: the CS-897 measurement below cannot drift apart over which file they mean.
#: A plain string literal rather than a backticked one, so the bare-path arm
#: reads no citation here - it resolves at R0 either way, and spelling it
#: without the quoting is one less thing to have to be right about.
DEEP_ARCHIVE: Final = "docs/history_notes.md"

UNGUARDED_DOCS: Final[Mapping[str, str]] = {
    DEEP_ARCHIVE: (
        "the deep archive - a record whose pointers rot BY CONSTRUCTION. Its own header"
        " declares Section status: HISTORICAL and says the file holds NOTHING current, and"
        " that nothing in it may be cited as the present state of the project. Every line"
        " in it was therefore written against a tree that has since moved, and repairing a"
        " pointer inside it would falsify the record rather than fix it. TRUE OF EVERY"
        " MEMBER, which the reason this replaces was not: that one said the dead pointers"
        " sit inside citation-guard detail blocks whose SUBJECT is a pointer being dead, so"
        " quoting and citing cannot be told apart by shape - true of two sites and of none"
        " of the rest. The population is MEASURED instead, and pinned per arm, so rot"
        " arriving after this record was written reddens even though the file is unguarded."
    ),
}


def bare_path(*segments: str) -> str:
    """Join path segments AT CALL TIME, for :func:`line_key`'s reason.

    This module is a tracked file that the bare-path arm reads like any other
    carrier, so a dead path written out as a literal here would be a finding
    this module manufactured against itself. Two halves joined at call time
    never sit adjacent in the source and cannot match.

    THE SHAPE ALREADY DECLINES MOST OF THAT and this is the belt to its braces:
    a literal in Python source carries no backticks, and a non-docstring
    literal is declined at R4 besides. Neither is a reason to spell a dead path
    where the next widening of the pattern would find it.

    Args:
        segments: Path segments, in order, repo-relative.

    Returns:
        The path, POSIX-separated, in the spelling :data:`tests.bare_path_guard.BARE_PATH_RE` reads.
    """
    return "/".join(segments)


#: The leaf whose detail spends the elided CS-492 pointer recorded in
#: :data:`DISPOSITIONS`. MEASURED, not reasoned about: the pointer sits in a
#: CS-8nn block discussing CS-492's residuals, not in CS-492's own section, so
#: the leaf that carries it is the FOLLOW-UP leaf and not the one holding the
#: item the pointer names. Named rather than spelled inline so a later relocate
#: pass moves the key with the body.
ITEM_NOTES_DEAD_POINTER_LEAF: Final = "docs/item_notes/phase4-followups.md"

#: The phase 4 leaf, and the CS-850 follow-up leaf split out of it. Named
#: because CS-889 records adjudicated line pointers against both, and a key
#: spelled inline in two places is a key that drifts when a leaf is renamed.
ITEM_NOTES_PHASE4: Final = "docs/item_notes/phase4.md"
ITEM_NOTES_850_LEAF: Final = "docs/item_notes/phase4-followups-850.md"


def line_key(path: str, line: int) -> str:
    """The :data:`DISPOSITIONS` key for one ``file:line`` pointer.

    ASSEMBLED RATHER THAN SPELLED, and that is the whole reason it exists. This
    module is itself a tracked Python file, so the CS-889 arms below read it
    the way they read every other carrier. A key written out as a literal
    would be a real, resolvable pointer sitting in the guard that judges
    pointers - the module-and-symbol placeholder made exactly that mistake
    once, and ``test_the_dot_py_spelling_of_the_placeholder_is_a_citation_no_floor_protects``
    is the record of it. A path and an integer joined at call time cannot
    match, because the two halves never sit adjacent in the source.

    Args:
        path: The cited file, repo-relative and POSIX-separated.
        line: The cited line number.

    Returns:
        The key, in the same spelling :data:`tests.test_docs_citations.LINE_POINTER_RE` matches.
    """
    return f"{path}:{line}"


# --- dispositions -----------------------------------------------------------

MOVED: Final = "MOVED"
RENAMED: Final = "RENAMED"
NO_TARGET: Final = "NO_TARGET"
DELIBERATE: Final = "DELIBERATE"


@dataclass(frozen=True)
class Disposition:
    """One recorded answer for one citation that does not resolve as written.

    Attributes:
        kind: MOVED, RENAMED, NO_TARGET or DELIBERATE.
        target: For MOVED and RENAMED, the live ``path::name`` this citation
            should be read as. Empty for the other two, which have nothing to
            verify against.
        why: The evidence, in one line, so the table is auditable without
            re-deriving it.
        at: WHICH sites of this citation the forgiveness answers, as the
            identity :func:`tests.test_docs_citations.citation_site_identities`
            derives - one per site, in ascending offset order. Each is the
            digest of the enclosing heading joined to the digest of the LINE
            the site sits on, plus an ordinal that separates sites sharing
            BOTH. Neither digest is a line number and neither is transcribed.

            A COUNT WAS THE FIRST KEY HERE AND IT ANSWERED THE WRONG QUESTION -
            CS-1121. Without any key at all the entry is ``(doc, name)`` and
            nothing else, so a forgiveness granted for one adjudicated site
            covers a brand-new dead citation of the same name at a NEW site in
            the same doc; three planted ledger entries citing already-forgiven
            names left the whole module green, and the count was the repair.
            But a count says HOW MANY sites a record forgives and never WHICH,
            so a COMPENSATING SWAP walks straight through it: delete the one
            adjudicated site and add a brand-new dead citation of the same name
            in the same edit, and the cardinality is unchanged. Measured green
            on a live ledger entry before this repair.

            AN IDENTITY IS STRICTLY STRONGER THAN THE COUNT IT REPLACES,
            because the count is recoverable from it - duplicates are kept, so
            a site arriving with no deletion lengthens the tuple exactly as it
            used to raise the count. It is also churn-free in the way a line
            number is not: the ledger is append-only newest-first, so
            prepending an entry moves every site below it while rewriting
            nothing under any heading, and neither half of this identity moves.

            THE HEADING ALONE WAS NOT ENOUGH AND THE FIRST BUILD OF CS-1121
            SHIPPED IT ANYWAY, disclosing the gap as a residual holding at one
            crowded entry. An adversary measured the live table: EVERY entry
            was silent on a within-heading swap and none reddened. The gap was
            the GRANULARITY, not the crowding - headings covering more than one
            entry were common - so the acceptance, which does not say WHERE the
            swap happens, was unmet everywhere. That is not a residual; it is
            the defect one level up, and an item does not close by disclosing
            that it did not happen. No figure is written here: the population
            is what ``test_a_within_heading_compensating_swap_is_reported_at_every_entry``
            walks, and a number in this prose would rot on the next entry filed.

            THE DISCLOSURE'S OWN FENCE WAS THE FALSE PART. It claimed a line
            number was the only thing that could separate two sites under one
            heading. If that were true the acceptance would be
            self-contradictory. It is false, and the counter-example already
            shipped in the module that derives this identity:
            :func:`tests.test_docs_citations.landing_digest` keys the CS-889
            pin on the CONTENT of its own landing line - derived, not
            transcribed, not a position. So the second half of this identity is
            the digest of the line the site sits on, which moves only when the
            sentence that spells the citation is rewritten - a change to what
            the forgiveness answers rather than churn from an edit above.

            THE ORDINAL IS PERMITTED WHERE A POSITION IS NOT, and the
            distinction is the whole of why CS-889 refuses a line number. A
            line number moves whenever ANYTHING above it is edited, which on an
            append-only newest-first ledger is every session, on sites nothing
            touched.

            WHEN THE ORDINAL MOVES, MEASURED RATHER THAN ARGUED, because the
            sentence that stood here was measured FALSE in both of its halves.
            It said "only when a byte-identical sibling under the same heading
            is added or removed"; at the time, a byte-identical line under a
            DIFFERENT section moved it - that was the heading-text collision,
            now repaired by the chain - and a sibling differing only in
            surrounding whitespace moved it too, because
            :func:`tests.test_docs_citations.landing_digest` strips. Re-measured
            after the chain change, the ordinal moves when, and only when,
            another site of the SAME citation is added or removed EARLIER in
            the doc, under the SAME heading chain, on a line identical after
            stripping. A sibling under a different chain does not move it; a
            different line under the same chain does not move it. It is a count
            of indistinguishables, not a place.

            STORED AS DIGESTS because some live headings and landings spell a
            bare repo-relative path, and a table holding them verbatim would
            seed bare-path sites inside the guard that judges bare paths - the
            fault :func:`line_key` avoids, arriving by a third door. HOW MANY
            is deliberately not written anywhere: the sentence that once gave a
            figure was read two ways by two reviewers who disagreed, which is
            CLAUDE.md section 4's point about a hardcoded count. The population
            is re-measured every run instead, by
            ``test_the_digest_is_not_cosmetic_because_the_anchors_carry_paths``.

            THESE VALUES WERE DERIVED FROM THE TREE, WHICH GRANTS NOTHING NEW.
            Each records which sites an ALREADY ADJUDICATED count covered, on a
            corpus that was green when they were cut; no citation is forgiven
            here that was not forgiven before, and
            :data:`FORGIVEN_LINE_POINTER_CEILING` is unmoved. That is why
            deriving them is not the laundering
            :data:`UNVERIFIED_LINE_POINTERS` refuses for a RESOLVER, which
            would have derived a claim nobody ever made.
    """

    kind: str
    target: str
    why: str
    at: tuple[str, ...]


# EVERY ENTRY HERE IS CHECKED, IN THREE DIRECTIONS. A MOVED or RENAMED target
# that stops resolving fails; an entry whose citation no longer appears - or
# which now resolves on its own - ALSO fails; and an entry whose IDENTIFIED
# SITES no longer match the doc fails too, in BOTH directions and on a swap
# that balances. That last one is the newest and the one an exemption table is
# normally missing: without it the key is a name, a name is forgiven forever,
# and the next dead citation that happens to spell the same name is forgiven on
# arrival. It was a COUNT until CS-1121, which bought the first half of that
# and not the second - a count answers how many sites a record forgives and
# never which, so a compensating swap walked through it. Every identity below
# is MEASURED from the doc, not asserted about it, and is opaque by
# construction: see :attr:`Disposition.at` for why the heading is digested
# rather than spelled.
DISPOSITIONS: Final[Mapping[tuple[str, str], Disposition]] = {
    # --- class 1: the record was RIGHT when written; CS-495 moved the tests.
    (
        LEDGER,
        "tests/save/test_properties.py"
        "::test_every_library_reaching_module_in_the_package_is_declared",
    ): Disposition(
        MOVED,
        "tests/save/test_reach_guard.py"
        "::test_every_library_reaching_module_in_the_package_is_declared",
        "CS-471 cited test_properties.py; CS-495 relocated the reach-guard"
        " suite. Not a record defect.",
        ("964a53cdbd44:6c97d1e1accd:0",),
    ),
    (
        LEDGER,
        "tests/save/test_properties.py"
        "::test_the_suite_wide_guard_catches_a_module_that_declares_nothing",
    ): Disposition(
        MOVED,
        "tests/save/test_reach_guard.py"
        "::test_the_suite_wide_guard_catches_a_module_that_declares_nothing",
        "CS-471 citation, relocated by CS-495. Not a record defect.",
        ("964a53cdbd44:58f358b909de:0",),
    ),
    (
        LEDGER,
        "tests/save/test_properties.py"
        "::test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating",
    ): Disposition(
        MOVED,
        "tests/save/test_reach_guard.py"
        "::test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating",
        "CS-471 citation, relocated by CS-495. Not a record defect.",
        ("964a53cdbd44:4aa9c6ef7db6:0",),
    ),
    # STILL CLASS 1 - right when written - but the tree RENAMED rather than moved
    # it. CS-862 retired the name because a green run renders the test NAME and
    # nothing else, so an arm claiming more than it grades makes that claim in the
    # one place a docstring narrowing cannot reach. TWO SITES: the CS-829 entry
    # that cited it live, and the CS-862 entry that records the retirement and
    # therefore has to spell the retired name.
    (
        LEDGER,
        "tests/save/test_struct_interior.py"
        "::test_degrading_the_record_table_cannot_improve_this_modules_grade",
    ): Disposition(
        RENAMED,
        "tests/save/test_struct_controls.py"
        "::test_the_table_control_takes_its_window_from_the_body_not_the_degraded_record",
        "CS-829 cited it live; CS-862 renamed it to the one bit it grades. Not a record defect.",
        ("4c77d4206721:b2950d2595d5:0", "6d225e8cb5e8:b2950d2595d5:0"),
    ),
    # --- class 2: WRONG WHEN WRITTEN, one unambiguous live target. Each is
    # corrected by a later ledger record, because this file is append-only.
    (
        LEDGER,
        "tests/save/test_absolute_claims.py"
        "::test_the_scanned_prose_carries_no_unbacked_absolute_claim",
    ): Disposition(
        RENAMED,
        "tests/save/test_absolute_claims.py"
        "::test_the_fenced_prose_carries_no_unbacked_absolute_claim",
        "one-word slip, scanned for fenced; the cited name is in no commit in history.",
        ("992a3a12711e:da8cd481b8ef:0", "8538ee7a513d:5fd8cb6f2e26:0"),
    ),
    (
        LEDGER,
        "tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected",
    ): Disposition(
        RENAMED,
        "tests/data/test_registry.py"
        "::test_the_misspelled_game_keys_are_used_verbatim_not_autocorrected",
        "the word game was dropped; the cited name is in no commit in history.",
        ("992a3a12711e:d51811dcb9b0:0", "696eaf45001d:102bd651c318:0"),
    ),
    (
        LEDGER,
        "tests/save/test_workdir.py"
        "::test_the_refusal_message_carries_no_non_digit_account_directory",
    ): Disposition(
        RENAMED,
        "tests/save/test_workdir.py"
        "::test_the_refusal_message_carries_no_raw_account_directory_of_a_non_digit_shape",
        "CS-454 is about the non-digit shape, and the surviving variant"
        " postdates the entry and matches its sentence.",
        ("992a3a12711e:5114b7d97341:0", "12703e0bf652:fbce5d892134:0"),
    ),
    # --- class 3: WRONG WHEN WRITTEN, and NO target may be assigned.
    (
        LEDGER,
        "tests/save/test_properties.py::test_the_reach_guard_catches_every_spliced_shape",
    ): Disposition(
        NO_TARGET,
        "",
        "no test bears this meaning: CS-441 records 26 of 46 spliced shapes"
        " still escaping, and stays OPEN.",
        ("992a3a12711e:8754964a9180:0", "5aa8fc50cd75:d05b6850bfeb:0"),
    ),
    (
        ITEM_NOTES_DEAD_POINTER_LEAF,
        "test_a_parameter_spelled_like_a_primitive_binds_nothing_and_serves_nothing",
    ): Disposition(
        NO_TARGET,
        "",
        "no test bears this name in any tracked file: it names a test CS-492"
        " round nine PROPOSED and never merged, and the nine rounds are"
        " refuted. THE POINTER WAS ALWAYS DEAD - it sat in docs/history_notes"
        ".md, which is recorded UNGUARDED, so nothing checked it. The"
        " 2026-08-23 relocation moved the text into a guarded doc and the"
        " guard found it on first contact, which is the arm working rather"
        " than a defect the move introduced.",
        ("fd7e2d72c6d5:f31b3920312b:0",),
    ),
    # --- CS-1126: a record the guard had never read. The CS-909 record sat
    # inside the ledger's `## Entry shape` template block, ABOVE the entries
    # heading this module scopes the ledger to, so its pointer went unchecked
    # from the day 8777a89 renamed the test it cites. Relocating the record's
    # unchanged bytes under `## Entries` put it in scope and the guard found it
    # on first contact - the same shape as the item-notes relocation above.
    (
        LEDGER,
        "tests/shell/test_shell_assets.py::test_main_consumes_every_seam_it_was_given",
    ): Disposition(
        RENAMED,
        "tests/shell/test_shell_assets.py::test_main_consumes_the_seam_it_was_given",
        "the CS-909 record cites the single test 8210a3c added; 8777a89, the same"
        " item's repair, split it into one case per seam under this name.",
        ("190b8ab597ab:b25b1e0f814b:0",),
    ),
    # --- CS-1112: the item-notes routing rows were removed, so four guard (j)
    # arms the CS-1086 and CS-1113 closures cite were renamed for what they now
    # grade. The ledger is append-only, so each record keeps the name it had.
    (
        LEDGER,
        "tests/data/test_item_notes_index.py"
        "::test_every_state_the_retired_no_section_check_saw_still_fails",
    ): Disposition(
        RENAMED,
        "tests/data/test_item_notes_index.py"
        "::test_every_placement_of_a_routed_items_section_is_graded",
        "the CS-1113 closure cites the arm proving the retired check covered; CS-1112"
        " restored the check with the rows gone and renamed the arm for what it grades.",
        ("031fabe32f28:80a6098be1ff:0",),
    ),
    # --- the bare-identifier arm, which sees what a path scanner cannot.
    (LEDGER, "test_an_unreadable_roadmap_as_the_only_non_pass_guard_is_not_clean"): Disposition(
        RENAMED,
        "tests/data/test_drift_guard_data.py"
        "::test_an_unreadable_roadmap_warns_all_four_markdown_readers_and_is_not_clean",
        "the CS-1117 closure cites the name it had; CS-1120 renamed it for its four WARNs.",
        ("53375f8f7489:aa4872cfd690:0",),
    ),
    (LEDGER, "test_a_row_agreeing_with_its_section_but_not_the_derivation_is_red"): Disposition(
        RENAMED,
        "tests/data/test_item_notes_index.py"
        "::test_a_section_agreeing_with_a_leftover_row_but_not_the_derivation_is_red",
        "the CS-1086 closure cites it; CS-1112 removed the rows it planted and renamed it.",
        ("c1b91cdc224f:d1130cde5326:0",),
    ),
    (LEDGER, "test_a_detail_field_with_no_row_is_red"): Disposition(
        RENAMED,
        "tests/data/test_item_notes_index.py::test_a_detail_field_with_no_section_is_red",
        "the CS-1086 closure cites it; CS-1112 removed the rows, so the field is graded"
        " against the section its derived leaf must hold.",
        ("c1b91cdc224f:e1104ac37514:0",),
    ),
    (LEDGER, "test_a_row_with_no_detail_field_is_red"): Disposition(
        RENAMED,
        "tests/data/test_item_notes_index.py"
        "::test_a_section_whose_line_carries_no_detail_field_is_red",
        "the CS-1086 closure cites it; CS-1112 removed the rows, so the unrouted"
        " direction is a section rather than a row.",
        ("c1b91cdc224f:ecf9260a64a6:0",),
    ),
    (LEDGER, "test_the_header_scan_advertises_no_bound_it_cannot_enforce"): Disposition(
        RENAMED,
        "tests/test_precommit_gate.py"
        "::test_the_header_scan_time_bound_declares_the_scope_it_actually_has",
        "added by ee36d0d, the CS-436 commit, alongside the live sibling the same entry cites.",
        (
            "992a3a12711e:d4ce758127b5:0",
            "992a3a12711e:f5544de92a3e:0",
            "97113dea2f42:f555758fdd2c:0",
        ),
    ),
    # THE WAKEUP_NOTES.md ENTRY FOR THAT SAME DEAD NAME IS GONE, RETIRED
    # 2026-08-22 (session 33), and it is worth one comment because it is the
    # only disposition this table has ever had to retire. It forgave exactly ONE
    # site, and that site lived inside session 30's note. Session 33 landed,
    # `WAKEUP_NOTES.md` keeps three sessions, session 30 moved to
    # `docs/history_notes.md` - which is the ONE unguarded doc - and the count
    # went to zero. Both site arms went RED on a correct doc-hygiene move,
    # exactly as predicted, and the fix is retirement rather than a recount.
    # THE LEDGER-KEYED ENTRY ABOVE STAYS: the ledger still spells the name, and
    # the key carries the DOC precisely so one file's forgiveness is never
    # another's.
    (LEDGER, "test_the_scanned_prose_carries_no_unbacked_absolute_claim"): Disposition(
        RENAMED,
        "tests/save/test_absolute_claims.py"
        "::test_the_fenced_prose_carries_no_unbacked_absolute_claim",
        "THE SECOND SITE of the same slip, spent bare inside a grep -c with no path attached.",
        ("97a1f6c81501:c567fffe7439:0",),
    ),
    (LEDGER, "test_no_recorded_gap_is_blocked_by_a_frozen_file"): Disposition(
        DELIBERATE,
        "",
        "the CS-411 correction record cites this name to prove it is DEAD;"
        " grep -c returning 0 IS its evidence.",
        ("3d0cbbc94fe6:e0f37129fd02:0", "e2eaae9436ad:a00197fa42f8:0"),
    ),
    (LEDGER, "test_the_exclusion_is_discovery_only_not_containment"): Disposition(
        DELIBERATE,
        "",
        "the SECOND name in that same CS-411 correction, and the reason it needed"
        " an entry only now: it is spelled ONLY in the elided form, so until"
        " ELIDED_RE the guard had never seen it.",
        ("3d0cbbc94fe6:21fdc36a4fbf:0", "e2eaae9436ad:68d9b541dff9:0"),
    ),
    # --- class 4: CS-889. A LINE POINTER whose target the tree has moved out
    # from under it. Keyed by line_key() rather than spelled, because this
    # module is itself a carrier the CS-889 arms read.
    #
    # THE LEDGER ONES ARE RECORDED, NEVER REPAIRED, and that is this file's own
    # settled practice rather than a concession made here. `docs/LEDGER.md`
    # declares itself append-only in its own header, and has already answered
    # this exact question twice in its own text - once leaving a stale citation
    # "exactly as written, because this file is append-only", and once saying of
    # two stale by-LINE citations that they are deliberately NOT edited and that
    # the correcting paragraph is the repair. That second correction states the
    # forbid leg's rule as the project's own practice, in the project's own
    # words: cite that module BY NAME, not by line.
    #
    # THE CS-910 PAIR IS THE FIRST MOVED RATHER THAN NO_TARGET IN THIS CLASS.
    # Both entries read their line as the `import verify_env` that makes the
    # tools rung resolve, and CS-910 gave each module a module-scope resolver
    # import, which pushed that line down inside the function that already
    # owned it. The declaration the prose describes is therefore still live and
    # nameable, so a target may be assigned instead of refused.
    (LEDGER, line_key("tools/drift_guard.py", 312)): Disposition(
        MOVED,
        "tools/drift_guard.py::_load_verify_env",
        "the entry reads that line as the deferred `import verify_env`, which"
        " now sits at :372 inside _load_verify_env. Note the entry's prose and"
        " its frozen digest ALREADY disagreed at 53ac4b5 - the digest held"
        " `def _exc_text(...)` while the sentence describes the import - so the"
        " pin was recording an unexamined site, exactly as it claims to.",
        ("e2eaae9436ad:b81a88324ea7:0",),
    ),
    (LEDGER, line_key("tools/facts_probe.py", 121)): Disposition(
        MOVED,
        "tools/facts_probe.py::_build_string",
        "the entry reads that line as the deferred `import verify_env` that"
        " makes the tools rung cost 9 errors and not 4. It now sits at :136"
        " inside _build_string, whose docstring carries the same reasoning the"
        " ledger entry does - the reader lives in scripts/verify_env.py and"
        " stays there.",
        ("e2eaae9436ad:feed734cd609:0",),
    ),
    # CS-1169 converted this from a CS-1162 line pin: the CS-1159 grant record
    # reads the line as the gate's placeholder allowlist, and the CS-1169 member
    # constant pushed that declaration down. It is still live and nameable.
    (LEDGER, line_key("tools/precommit_gate.py", 434)): Disposition(
        MOVED,
        "tools/precommit_gate.py::PLACEHOLDER_RE",
        "the CS-1159 grant record contrasts that line - the placeholder"
        " allowlist that passed a canonical EXAMPLE key - against the denied"
        " string. CS-1169 added PLACEHOLDER_MEMBERS above it, so the declaration"
        " moved down; its name is the stable citation.",
        ("458e6f0c9f53:c199e3edfedf:0",),
    ),
    (LEDGER, line_key("tools/precommit_gate.py", 2311)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as emitting the PASS banner only on an empty"
        " report.diagnostics. The line is blank today and its neighbourhood now"
        " holds the label-redaction rule, so no live symbol may be assigned"
        " without inventing one.",
        ("2e34d8e0bd39:cb6d5b7f39cd:0",),
    ),
    (LEDGER, line_key("tools/precommit_gate.py", 704)): Disposition(
        NO_TARGET,
        "",
        "prose and digest ALREADY disagreed at d9398e6 - the digest held the"
        " save-header budget constant. CS-1083 moved it; nothing is nameable.",
        ("396296006455:002005f7ce98:0",),
    ),
    (LEDGER, line_key("tools/precommit_gate.py", 1802)): Disposition(
        NO_TARGET,
        "",
        "prose and digest ALREADY disagreed at d9398e6 - the digest held a"
        " stage_for_lint docstring line. CS-1083 moved it; nothing to name.",
        ("b394c3c9f377:0f1d9cab3a43:0",),
    ),
    (LEDGER, line_key("tests/test_precommit_gate.py", 1174)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as a SECOND label-shape assertion over"
        " LEAK_MARKER. The line is blank today and the block below it opens an"
        " unrelated CS-202-B section.",
        ("637316b51867:1e4c01de7aea:0",),
    ),
    (LEDGER, line_key("scripts/verify_env.py", 358)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as a bare str(exc) outside CS-202's stated"
        " shape. The line is blank today and the neighbourhood is the ports"
        " loader.",
        ("396296006455:e8bd2e8a24fb:0",),
    ),
    (LEDGER, line_key("tools/precommit_gate.py", 517)): Disposition(
        NO_TARGET,
        "",
        "the entry contrasts that line, as the gate widening what it refuses to"
        " commit, against the resolver's digit filter. The line is a lone"
        " closing bracket today, so it names no declaration to contrast with.",
        ("8309b6af0abd:a8a0f0a25b3f:0",),
    ),
    (LEDGER, line_key("scripts/make_cert.py", 222)): Disposition(
        MOVED,
        "scripts/make_cert.py::_restrict",
        "RIGHT WHEN WRITTEN and moved since: the entry says that line chmods the"
        " key 0600 inside _restrict, and the line now sits inside the openssl"
        " argv builder. _restrict is live and is the target the sentence means.",
        ("1c6e39beba48:96ef7d77d36c:0",),
    ),
    # THE ONLY ROW IN THIS TABLE THAT COST A CEILING NOTCH, and the only one so
    # far that ever has. Granted by an adjudicator that authored neither CS-928
    # nor this row, and defended in `docs/LEDGER.md` rather than typed; the
    # raise it forced sits in the same change, on
    # `FORGIVEN_LINE_POINTER_CEILING` below.
    #
    # THE POINTER WAS RIGHT WHEN WRITTEN, demonstrated rather than asserted: at
    # the citing commit `db3b404` the cited line and the one after it were the
    # solve/ clause and the first line of the advisor/ raw-docs clause, which
    # are the two the CS-300 sentence names. CS-928 rewrote section 3 under it
    # and the line went blank.
    #
    # NEITHER RECORDED REPAIR REACHES IT. By-name citation, which this project
    # states as the repair, would mean editing a record inside a carrier whose
    # own header forbids editing records. The line-count-neutral repair that
    # answered the CS-896 restructure is not merely costly here but incoherent:
    # the two pointers into this section moved by five lines and by eight, so
    # no single padding restores both, and the one that moved by eight was
    # repaired this session, so restoring the old offsets would re-break it.
    (LEDGER, line_key("docs/ARCHITECTURE.md", 136)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as the seam clause scoping the raw-docs"
        " prohibition to the advisor layer rather than to every layer. The line"
        " is blank today. NO_TARGET rather than MOVED because `resolves`"
        " answers only Python module-scope names, so a markdown heading handed"
        " to it would be reported dead - the durable target is therefore"
        " carried here in full for a human to audit, since no machine can:"
        " section `## 3. Seam discipline` of docs/ARCHITECTURE.md, the"
        " surviving `solve/ never reads a save` clause under it, and the"
        " paragraph beginning `One rule on this list constrains code that does"
        " not exist yet`.",
        ("0e59d4000faf:9fad20ba61c4:0",),
    ),
    # CS-1162: TWO SITES IN ONE CS-1159 GRANT RECORD, BOTH BLANK, and they take
    # the CS-300/CS-928 route above rather than `UNFORBIDDEN_LINE_POINTERS`. That
    # table's own comment says blankness is not what it forgives, and it is scoped
    # to targets with NO symbol form - both of these are tracked Python modules
    # that have one, so it does not reach them and must not be widened to.
    #
    # THE GRANT RECORD ALREADY NAMES BOTH SYMBOLS IN PROSE, which is why the
    # durable target below is near-transcription rather than adjudication of a
    # sentence nobody can check: the record says the interpreter token is read by
    # `_settings_interpreter`, and that the fail-open branch is promised by the
    # wrapper's own written contract.
    #
    # NEITHER RECORDED REPAIR REACHES THEM, on the CS-300 reasoning verbatim.
    # By-name citation would mean editing a record inside a carrier whose header
    # forbids editing records, so the correction is a LATER record and these rows
    # carry the durable target for a human to audit.
    (LEDGER, line_key("tests/test_pretooluse_gate.py", 599)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as the helper that takes the first"
        " whitespace token of the first PreToolUse command and feeds it to"
        " shutil.which, which is what makes quoting the interpreter a"
        " reddening change. The line is blank today. NO_TARGET rather than"
        " MOVED because the durable target is carried here in full: the"
        " module-scope helper _settings_interpreter of"
        " tests/test_pretooluse_gate.py, and the arm named in the same"
        " sentence, test_the_configured_interpreter_can_actually_be_resolved.",
        ("656e8b5002da:c9b9c44755dc:0",),
    ),
    (LEDGER, line_key("tools/pretooluse_gate.py", 29)): Disposition(
        NO_TARGET,
        "",
        "the entry reads those lines as the wrapper's promise to exit 0 on its"
        " own error, quoting the fail-open grounds verbatim. The line is blank"
        " today. NO_TARGET rather than MOVED because the durable target is a"
        " passage of the MODULE DOCSTRING and not a declaration, so `resolves`"
        " - which answers only module-scope names - would report any spelling"
        " of it dead: the section headed THE TWO HALVES OF THE CONTRACT, AND"
        " WHY THEY POINT OPPOSITE WAYS in tools/pretooluse_gate.py, and the"
        " FAIL OPEN clause beneath it.",
        ("656e8b5002da:e1d54b3998fd:0",),
    ),
    # WRONG FROM BIRTH, NOT MERELY STALE, so it is not re-cut: the text its digest
    # froze is a `_strip_generated_pin` docstring line, never the cited table.
    (LEDGER, line_key("tests/data/test_phase2_gate.py", 775)): Disposition(
        NO_TARGET,
        "",
        "the entry reads those lines as the gate REQUIRING the registry and"
        " version edges into docs_extract. Durable targets, since the dead form"
        " leaves a machine nothing to check: ALLOWED_IMPORTS and the"
        " permitted-neighbours import arm of tests/data/test_phase2_gate.py.",
        ("d8a63e8c575f:aae9ef3973d8:0", "0e59d4000faf:9fad20ba61c4:0"),
    ),
    # CS-210 GREW THE GENERATED PIN, so two sites this append-only file cites
    # slid down. Re-derived this cycle rather than carried: at the pre-change
    # commit line 352 was the pin's `"integrity"` VALUE line and line 815 was
    # inside `extract_pin_block`'s `except ValueError as exc:` handler. Neither
    # sentence may be repointed where it stands, and both describe declarations
    # that are still live and nameable, so both take a target rather than a
    # refusal. The integrity line is the harder of the two: it sat INSIDE the
    # generated block, which carries no module-scope name at all, and the
    # digest printed on it changed in the same cycle - so a line-count-neutral
    # repair would restore a pointer at a value that is itself stale.
    (LEDGER, line_key("clockspeed/data/version.py", 352)): Disposition(
        MOVED,
        "clockspeed/data/version.py::INTEGRITY_KEY",
        "the entry reads that line as the pin's `integrity` value, refuting a"
        " base64-shaped premise by measuring it a 64-character lowercase hex"
        " sha256. INTEGRITY_KEY is the live declaration of the field the"
        " sentence is about, and _SHA256_HEX_LENGTH beside it states the length"
        " it asserts.",
        ("8309b6af0abd:a6f195850698:0",),
    ),
    (LEDGER, line_key("clockspeed/data/version.py", 815)): Disposition(
        MOVED,
        "clockspeed/data/version.py::extract_pin_block",
        "the CS-202 scope ruling reads that line as one of the exception"
        " renderings outside its two named files - the `except ValueError as"
        " exc:` whose handler names msg, lineno and colno rather than str() on"
        " the object. That handler is still there and is still the only one in"
        " the function, so the enclosing definition names it unambiguously.",
        ("396296006455:e8bd2e8a24fb:0",),
    ),
    # THE ONE THE REPAIR SLICE REFUSED, and the refusal is the strongest
    # evidence in CS-889 for why a wrong-but-resolving pointer is worse than a
    # dead one. The obvious symbol conversion WOULD have resolved: at an earlier
    # commit that line was a four-argument WorldWarning construction inside
    # _carried. But CS-440 threaded `subject` into the usmap branch, so the
    # note's claim that the site DROPS THE SUBJECT is no longer true of
    # _carried - and the only surviving four-argument form there is the chunks
    # branch, whose absent subject that function's own docstring justifies as
    # CORRECT. A reader following the converted pointer would land on the branch
    # the note was never about, backed by a docstring saying it is right.
    (ITEM_NOTES_PHASE4, line_key("clockspeed/save/world.py", 919)): Disposition(
        NO_TARGET,
        "",
        "the note reads that line as a four-argument WorldWarning that drops the"
        " subject. The line is blank today, _carried has moved, and CS-440 made"
        " the note's claim false of it - so a symbol conversion would resolve to"
        " a sentence that is no longer true.",
        ("b26dc763e023:88daad605b5f:0",),
    ),
    # THE TRAP THAT MANUFACTURES A FINDING ON CORRECT PROSE lived here as a
    # DELIBERATE entry for `scripts/make_cert.py` at line 224 - the CS-889 note
    # spelled that pointer as the SUBJECT of a correction rather than as a
    # citation, and QUOTING AND CITING ARE INDISTINGUISHABLE BY SHAPE. The entry
    # is gone because the site is: CS-889 closed and its note relocated to
    # `docs/history_notes.md`, which is exempt from this module for exactly that
    # reason. The stale-entry contract reported it on the very next run, which is
    # the record being checked in both directions rather than believed.
    #
    # --- class 5: the record was RIGHT when written; CS-1066 moved the symbols.
    #
    # THE SAME SHAPE AS CLASS 1 AND MEASURED RATHER THAN ARGUED FROM IT. Five
    # names left `tests/test_docs_citations.py` for this file when the citation
    # family split a second time, and `docs/LEDGER.md` cites every one of them by
    # path and symbol. A RE-IMPORT DOES NOT RESCUE ANY OF THEM:
    # :func:`tests.test_docs_citations.module_scope_names` walks ClassDef,
    # AnnAssign and Assign and never ImportFrom, so a name bound by an import is
    # not a name that module BINDS for this resolver's purposes - which is
    # deliberate, since a citation that resolves only through somebody's import
    # statement is one an unrelated import cleanup silently kills.
    #
    # THE LEDGER CANNOT BE EDITED. Its own header declares it append-only
    # newest-first, so the repair class 1 would otherwise want - repoint the
    # citation - is an edit that file forbids. A later correcting record is the
    # sanctioned form, and these rows are the machine-checked half of it.
    #
    # NOTHING HERE IS UNVERIFIABLE, WHICH IS THE WHOLE DIFFERENCE BETWEEN THIS
    # AND FORGIVING A PIN. Every row is MOVED with a live target, so each is
    # checked in all three directions on every run: the target must resolve, the
    # citation must still be spelled, and the site count must still match. Not
    # one NO_TARGET and not one DELIBERATE rides along, because those are the
    # kinds that name nothing to check.
    (
        LEDGER,
        "tests/test_docs_citations.py::DISPOSITIONS",
    ): Disposition(
        MOVED,
        "tests/test_citation_tables.py::DISPOSITIONS",
        "CS-1066 relocated the disposition and pin tables out of the module that"
        " judges. Not a record defect.",
        ("8436f4052a2a:9a4673332e87:0",),
    ),
    (
        LEDGER,
        "tests/test_docs_citations.py::UNVERIFIED_LINE_POINTERS",
    ): Disposition(
        MOVED,
        "tests/test_citation_tables.py::UNVERIFIED_LINE_POINTERS",
        "CS-1066 relocated the grandfathered pin table with the dispositions it is"
        " budgeted alongside. Not a record defect.",
        ("d8a63e8c575f:e0dd268d8a61:0",),
    ),
    (
        LEDGER,
        "tests/test_docs_citations.py::FORGIVEN_LINE_POINTER_CEILING",
    ): Disposition(
        MOVED,
        "tests/test_citation_tables.py::FORGIVEN_LINE_POINTER_CEILING",
        "CS-1066 moved the ceiling with the two tables it counts, because a budget"
        " and its subject may not live in different files. Not a record defect.",
        ("d8a63e8c575f:c06e418cc49f:0", "8436f4052a2a:10b9f0049a00:0"),
    ),
    (
        LEDGER,
        "tests/test_docs_citations.py"
        "::test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow",
    ): Disposition(
        MOVED,
        "tests/test_citation_tables.py"
        "::test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow",
        "CS-1066 moved the contract with the tables it bounds, which"
        " tests/bare_path_guard.py::registry_problems requires. Not a record defect.",
        ("ceeba188e71e:be7e0df85f47:0", "8436f4052a2a:c6f3292a07ef:0"),
    ),
    (
        LEDGER,
        "tests/test_docs_citations.py::test_the_deep_archive_is_the_only_doc_left_unguarded",
    ): Disposition(
        MOVED,
        "tests/test_citation_tables.py::test_the_deep_archive_is_the_only_doc_left_unguarded",
        "CS-1066 moved the contract with UNGUARDED_DOCS, for the same reason the"
        " budget arm above travelled. Not a record defect.",
        ("18fd50697c39:e127d81b8db9:0",),
    ),
    # --- class 6: the record was RIGHT when written; CS-1167 RENAMED the symbol.
    # The single pooled canary became one canary per rule, so the old name has
    # no one-to-one successor in meaning - but the construction the ledger cites
    # it for, a credential shape ASSEMBLED FROM FRAGMENTS, is exactly what the
    # per-rule table holds. RENAMED with a live target, checked every run.
    (
        LEDGER,
        "tools/outbound_gate.py::CANARY_CREDENTIAL",
    ): Disposition(
        RENAMED,
        "tools/outbound_gate.py::CREDENTIAL_CANARIES",
        "CS-1167 replaced the single canary with one per rule. Not a record defect.",
        ("ce711a9bd17c:4f5302be7ef4:0",),
    ),
    # --- class 7: the record was RIGHT when written; CS-1193 MOVED the two
    # whole-population forced arms out of the canary population module into
    # their own file, after the CS-1177 entry cited them. Names unchanged.
    (
        LEDGER,
        "tests/test_canary_population.py"
        "::test_a_helper_raise_under_showlocals_renders_no_canary_forced_red_output",
    ): Disposition(
        MOVED,
        "tests/test_canary_population_forced.py"
        "::test_a_helper_raise_under_showlocals_renders_no_canary_forced_red_output",
        "CS-1177 citation, relocated by CS-1193. Not a record defect.",
        ("690192831736:40b2c3e72a51:0",),
    ),
    (
        LEDGER,
        "tests/test_canary_population.py"
        "::test_a_new_canary_module_in_no_list_is_picked_up_and_graded_forced_red_output",
    ): Disposition(
        MOVED,
        "tests/test_canary_population_forced.py"
        "::test_a_new_canary_module_in_no_list_is_picked_up_and_graded_forced_red_output",
        "CS-1177 citation, relocated by CS-1193. Not a record defect.",
        ("690192831736:40b2c3e72a51:0",),
    ),
}


# --- CS-889: the two pinned line-pointer populations ------------------------

#: The forbidden class, GRANDFATHERED. Every entry is a live ``file:line``
#: pointer at a tracked Python module whose RANGE resolves and whose CONTENT
#: has NOT been checked against the sentence that spells it.
#:
#: THIS TABLE CLAIMS NOTHING ABOUT WHETHER THESE POINTERS ARE RIGHT, and it is
#: deliberately not a :class:`Disposition` for exactly that reason. A
#: disposition is an ADJUDICATION - somebody read the citation, read the target
#: and recorded a verdict. Nobody has done that here. Filing these as
#: dispositions would dress up "unexamined" as "answered", which is the
#: laundering shape this repository keeps paying for. What the table DOES buy
#: is closure against NEW additions: a pointer of this shape written after this
#: pin is reported on arrival, because it is not in here.
#:
#: PINNING THE SITES RATHER THAN THEIR COUNT is what makes it checkable in both
#: directions. A count is satisfied by any set of the same size, so one pointer
#: could be swapped for another and the pin would hold. An entry here that no
#: longer appears is reported as stale, which is the direction a baseline
#: normally is not checked in.
#:
#: CONTENT-CORRECTNESS IS THE OPEN RESIDUAL OF CS-889 and it is stated here
#: rather than left to be rediscovered. Making it sound needs a human to state
#: the intended symbol for every member, which was priced and declined for this
#: round; deriving the pin from today's tree instead would bake in whatever the
#: pointer happens to hit and ship GREEN on the very defects it was built for.
#:
#: EACH SITE IS ANCHORED TO A DIGEST OF THE LINE IT FROZE, and that answers a
#: refutation the first build of this table earned: a pin keyed on
#: ``(carrier, path, line)`` alone FOLLOWS THE ROT. Edit anything above a
#: pinned line and the pointer stays in range, stays non-blank, stays matched
#: by the identical key, and is grandfathered forever while now naming a
#: different declaration - immunised against detection rather than merely
#: unexamined.
#:
#: THE ANCHOR IS A CHANGE CLAIM, NOT A CORRECTNESS CLAIM, and that distinction
#: is what makes it affordable where a content-anchored RESOLVER was rejected.
#: A resolver pinning the intended symbol would be derived from today's tree
#: and would ship green on the very defects it was built for. A digest claims
#: only that the line has not MOVED since it was frozen, which is exactly the
#: mechanism CS-889 was filed on, at zero human adjudication cost.
#:
#: THE MAINTENANCE COST WAS MEASURED RATHER THAN ARGUED, because the standing
#: objection to asserting content is that it "would redden on every edit above
#: it, which is a guard nobody keeps". Over the twelve commits between the SHA
#: these pins were cut at and the SHA they sit at now, ONE of the 48 drifted.
#: An enclosing-symbol anchor was measured
#: against the same window as the cheaper alternative and caught ZERO of them -
#: the drifted line moved from a function's docstring onto its own ``def``
#: line, so the enclosing symbol never changed. It is quieter because it
#: detects less. One adjudication per session, on a list whose whole purpose
#: is to shrink to nothing, is the ratchet working rather than noise.
#:
#: A DIGEST RATHER THAN THE LINE ITSELF, and this is not squeamishness about
#: table size. One of these landings is a comment that spells a
#: module-and-symbol citation, so a table storing landings verbatim would put a
#: real, resolvable citation inside the guard that judges citations - the fault
#: :func:`line_key` exists to avoid, arriving by another door.
UNVERIFIED_LINE_POINTERS: Final[Mapping[tuple[str, str, int], str]] = {
    ("docs/LEDGER.md", "clockspeed/data/docs_extract.py", 443): "7d6e8ff5649f",
    ("docs/LEDGER.md", "clockspeed/data/locate.py", 187): "53bcd3acffa2",
    ("docs/LEDGER.md", "clockspeed/data/locate.py", 657): "c0f880c0e553",
    ("docs/LEDGER.md", "clockspeed/save/usmap.py", 46): "82be9ba39f87",
    ("docs/LEDGER.md", "scripts/install_hooks.py", 310): "4facec475176",
    ("docs/LEDGER.md", "tools/edit_lint_check.py", 82): "c52969cc5a4b",
    ("docs/LEDGER.md", "tools/edit_lint_check.py", 113): "a7515962ef0b",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 39): "0d5e3276442e",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 141): "fa085c760a09",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 187): "53bcd3acffa2",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/workdir.py", 688): "e2d30d6ce513",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/save/test_value_anchoring.py",
        1082,
    ): "b12596d6aa74",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/test_exception_rendering.py",
        75,
    ): "8e15edc2fdf7",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/test_redaction_scope.py",
        26,
    ): "cc9d482be931",
    ("docs/item_notes/phase4-followups.md", "scripts/install_hooks.py", 44): "f9e42ccd54cc",
    ("docs/item_notes/phase4-followups.md", "tests/save/reach_guard.py", 1504): "267881c9c71a",
    (
        "docs/item_notes/phase4-followups.md",
        "tests/save/test_absolute_claims.py",
        192,
    ): "c6f4b966d451",
    ("docs/item_notes/phase4.md", "tests/data/test_locate.py", 858): "7b83ed5742f3",
    ("docs/item_notes/phase4.md", "tests/save/synthetic.py", 1093): "b260445518a9",
    ("docs/item_notes/phase4.md", "tests/save/test_byte_order_status.py", 878): "5d5874e29659",
    ("docs/item_notes/phase4.md", "tests/save/test_objects.py", 834): "98fb3674bec1",
    ("docs/item_notes/phase4.md", "tests/save/test_phase4_gate.py", 2089): "d2973a15655f",
}


#: THE RATCHET'S RECORDED BUDGET - every forgiveness this arm honours, counted
#: in one number. 48 grandfathered pins plus 7 adjudicated line-pointer
#: dispositions. :func:`forgiveness_budget_problems` checks it in BOTH
#: directions, so the number can only come down.
#:
#: IT DOES NOT REACH ZERO in general - a quoting-not-citing site is correct prose
#: about a pointer having been wrong and must stay forgiven for as long as it is
#: spelled in a GUARDED doc. Everything above that floor is meant to be repaired
#: away, and the ceiling comes down with each repair: 55 to 54 when CS-889 closed
#: and its note moved to `docs/history_notes.md`, which is exempt from this module
#: for exactly the quoting-versus-citing reason, taking the last such site out of
#: the guarded set with it.
#:
#: 54 TO 53 WHEN CS-910 MOVED THREE PINNED LINES. Three pins left the table and
#: two dispositions arrived, which is a net repair of one: the item-notes leaf
#: took the symbol form outright, and the two ledger sites were RECORDED rather
#: than repaired for the reason class 4 gives - so they moved from an unexamined
#: pin to an adjudicated MOVED with a live target, which is a smaller
#: forgiveness but still a forgiveness. The ratchet caught this itself; the
#: ceiling was not lowered by hand until it did.
#:
#: 53 TO 66, AND THIS RAISE TIGHTENS THE RATCHET RATHER THAN LOOSENING IT. An
#: adversary demonstrated that the budget counted only LINE-POINTER-keyed
#: dispositions, so 13 of the 21 rows in DISPOSITIONS cost nothing: dropping the
#: four unverifiable symbol-form rows failed five arms while the budget stayed
#: green at 53 against 53. A symbol-keyed forgiveness was therefore FREE - no
#: ceiling to raise, no number in the diff to defend - which is the exact escape
#: the docstring below claims the budget closed. The count now spans both tables
#: whole, so the number is bigger and the hole is smaller. NOTHING WAS FORGIVEN
#: TO GET HERE: 45 pins plus 21 dispositions, both enumerated, both already in
#: the tree before this change.
#:
#: 66 TO 65, A REPAIR RATHER THAN AN APPEND. The phase-4 followups note pinned
#: a line in tests/conftest.py; an unrelated edit added one line above that
#: target and the pin followed the rot, landing on the comment above the name
#: it meant. It was converted to the symbol form, which an edit above cannot
#: invalidate, so the line form is GONE rather than re-cut. The ceiling drops
#: with it: 65 recorded against 66 is exactly the banked slack this ratchet
#: exists to refuse.
#: 65 TO 66, THE FIRST RAISE IN THIS RATCHET'S RECORDED HISTORY THAT ACTUALLY
#: BUYS A FORGIVENESS. Neither raise above is precedent for it, and the
#: distinction is the entire price. 53 to 66 widened the counted POPULATION and
#: forgave nothing - its own paragraph says so - and 66 to 65 was a repair. This
#: one adds a NO_TARGET disposition for a pointer no repair can reach, so
#: "a ratchet that has only ever come down" is FALSE and is deliberately not
#: written anywhere here. The true and narrower claim is that until now no raise
#: had ever spent a forgiveness.
#:
#: IT WAS UNAVOIDABLE RATHER THAN CONVENIENT. The carrier is `docs/LEDGER.md`,
#: which forbids editing the record that spells the pointer, so the by-name
#: repair cannot be applied to it; and the line-count-neutral alternative is not
#: merely costly but incoherent, because the two pointers into the rewritten
#: section moved by five lines and by eight and no single padding restores both.
#: Silently raising a ceiling to make a red test green stays forbidden - what
#: happened here is the argued raise the docstring below was built to permit,
#: and the argument is in `docs/LEDGER.md` under CS-928.
#:
#: THE NOTCH IS RECLAIMED, and this is stated so the forgiveness is not
#: permanent by default: when this arm can verify a markdown target by HEADING
#: PRESENCE the way it already verifies a Python one by name, the row above
#: converts from an unverifiable NO_TARGET to a checked MOVED and the ceiling
#: comes back to 65. That capability is the target side of the line-pointer
#: gap filed as CS-937. Nothing else discharges it: a later record merely
#: MENTIONING the file is the markdown keyword detector CS-899 already priced
#: and REFUSED for failing in the permissive direction.
#:
#: 66 TO 64, 2026-09-10 BY CS-961, AND IT IS THE RATCHET COMING DOWN RATHER THAN
#: AN ARGUED RAISE. Two pins into `clockspeed/save/world.py` left the table
#: because the doc that spelled them now names its two sites by their STAGE
#: constant instead of by line, so there is no pointer left to forgive. A
#: ceiling held at 66 over 64 forgivenesses is the slack half of this arm's own
#: finding - room banked for the next append - so it comes down with them.
#:
#: WHY THOSE TWO WERE RETIRED RATHER THAN REPOINTED, since three other pins in
#: this same item WERE repointed and stayed. A repoint is honest only while the
#: digest carries over unchanged, which is the guard proving the new line holds
#: byte-identical content. Those three did. The STAGE_HEADER raise did not: it
#: gained an indent level when the raw save was scrubbed from the frame, so its
#: line CHANGED as well as moved, and re-cutting a digest from today's tree is
#: exactly the laundering the comment above forbids. Its neighbour went with it
#: because the sentence carrying both reads as one claim. The doc already wrote
#: a third such site in prose as a bare line number for this reason.
#:
#: 61 TO 60, 2026-09-10 BY CS-210, AND THE CHANGE IS THE NET OF TWO MOVEMENTS
#: THAT MUST BE READ SEPARATELY OR THE NUMBER LOOKS ARBITRARY.
#:
#: THE FIRST MOVEMENT IS A REPAIR AND IT IS THE WHOLE DROP. The item-notes leaf for
#: ROADMAP `Phase 2` pinned a line in `clockspeed/data/registry.py`. CS-210 was the only
#: item in that leaf, so closing it moved the body to `docs/history_notes.md` and removed
#: the leaf - which is also why the leaf is named by its phase here and not by its path,
#: since a path this change deleted is a bare path the arms below would report dead,
#: and the deep archive is exempt from this module for the quoting-versus-citing reason
#: the 55-to-54 paragraph above gives. The pointer is not repaired in the sense of now
#: resolving - it left the guarded corpus, which is the same discharge CS-889 took. The
#: forgiveness is gone from THIS arm's books, so the ceiling comes down with it.
#: The pointer is not thereby unguarded: `tests/test_archive_rot.py` counts it, and its
#: `_ROT_FORM` pin went UP by one in the same change. A forgiveness that merely changes
#: which arm carries it must be visible in both, or the pair of numbers is a way to lose
#: one.
#:
#: THE SECOND MOVEMENT IS A SWAP AND IT MOVES THE NUMBER BY NOTHING. Growing the
#: generated pin moved two `clockspeed/data/version.py` lines this file pinned; both left
#: the table and two MOVED dispositions arrived in their place, so the counted population
#: is unchanged. It does not come down, because nothing was repaired - both sites are
#: still forgiven, merely forgiven with a live target attached instead of a frozen digest.
#: It does not go up, because the swap spends no new forgiveness. This is the case the 53
#: to 66 paragraph made countable: with both tables counted whole, converting a pin into a
#: disposition is visible as the nothing it is, where under the old line-pointer-only
#: count it would have read as a raise.
#:
#: THOSE TWO PINS WERE RETIRED RATHER THAN REPOINTED, on the CS-961 criterion. A repoint
#: is honest only while the digest carries over unchanged. One of the two lines was the
#: pin's own `integrity` VALUE, and regenerating the census changed that value as well as
#: its line number - so its content did not carry over, and re-cutting the digest from
#: today's tree would be the laundering the comment above forbids. Its neighbour is an
#: `except` clause that did carry over, but it takes the enclosing-symbol form for the
#: better reason: a function body is the anchor an edit above it cannot invalidate, which
#: is the repair this table exists to shrink toward.
#:
#: 60 TO 58, 2026-09-11, BY THE MERGE OF `main` INTO `lane/queue` AND NOT BY ANY
#: EDIT OF ITS OWN. Two retirements landed on separate branches and neither could see
#: the other: CS-210 above took 61 to 60 here, and CS-968 on `main` retired two
#: `tests/test_hook_interpreter_ladder.py` pins - one in `docs/LEDGER.md`, one in
#: `docs/item_notes/phase4-followups.md` - taking 61 to 59 there. The two sets are
#: disjoint, so the merged tree carries three fewer forgivenesses than the base and the
#: ceiling is 58. It is recorded here rather than left to arithmetic because a ceiling
#: that arrives by merge is the one case where no commit on either side argued for the
#: number that now stands.
#:
#: 58 TO 57, 2026-09-12 BY CS-964 AT THE MERGE OF `cs964-seam`, AND IT IS A REPAIR
#: RATHER THAN A RETIREMENT. The pin was `docs/item_notes/phase4-followups-850.md`
#: into `tests/save/test_header.py` line 1048, an `__cause__` nullity assertion the
#: CS-857 prose counted by line. The seam rewrote that sentence to name the test by
#: its own symbol - `test_read_header_does_not_leak_the_original_oserror_as_context`
#: - so there is no line pointer left to forgive and the forgiveness leaves the books
#: rather than moving to another arm. That is the enclosing-symbol form the 61-to-60
#: paragraph above argues for in so many words: a function body is the anchor an edit
#: above it cannot invalidate, and it is the direction this table exists to shrink in.
#: It comes down by one because the repair spent nothing and banked nothing.
#:
#: IT IS RECORDED AS ARRIVING AT A MERGE because the seam branch carried the repair
#: and `main` carried the 58, and neither side's commit argued for 57 - the same case
#: the 60-to-58 paragraph above already names, one branch further along.
#:
#: 57 TO 50, 2026-09-13 BY CS-854 - SEVEN REPAIRS PLUS ONE SWAP. Seven pins left
#: because their docs now cite the enclosing SYMBOL, located by the TEXT each
#: digest froze and NOT by the occupant of the old offset. The eighth moved from
#: an unexamined pin to an adjudicated NO_TARGET, which is budget-neutral.
#:
#: 50 TO 55, 2026-09-15 BY CS-1066, AND EVERY ONE OF THE FIVE IS A CHECKED MOVED
#: ROW. This is the class-1 case the table opens with, arriving five at once
#: because a FILE SPLIT moves symbols the way a relocation of tests once did.
#: `docs/LEDGER.md` cites five names that left `tests/test_docs_citations.py` for
#: this file; the ledger is append-only by its own header so the citations cannot
#: be repointed, and a re-import does not rescue them because the resolver walks
#: what a module BINDS and never what it imports.
#:
#: IT IS A RAISE AND IT IS NOT THE 65-TO-66 KIND, which is the distinction that
#: paragraph exists to make. That one spent a NO_TARGET - a forgiveness naming
#: nothing anybody can check. These five are MOVED with live targets, checked in
#: three directions every run: the target resolves, the citation is still
#: spelled, and the site count still matches. A row here that stops being true
#: reddens, which is not something the unverifiable kinds can claim.
#:
#: THE NUMBER IS THE MEASURED ONE. Five rows, seven sites, both derived by
#: running this module's own resolver against the corpus after the move rather
#: than counted by eye - two earlier estimates of the same quantity, made by
#: reading the diff, were 6 names and 3 names and neither was right.
#:
#: 54 TO 55 WHEN CS-1120 RENAMED A TEST THE CS-1117 CLOSURE CITES. The CS-1120
#: acceptance ordered the stale arm name corrected, and the ledger is append-only, so
#: the CS-1117 record keeps the name it had when written. One RENAMED row with a live
#: target, checked in three directions like the MOVED five above - not the unverifiable
#: NO_TARGET kind. The alternative, keeping a misdescribing test name so a record
#: resolves, would trade a true name for a green guard.
#:
#: 55 TO 56 WHEN CS-1126 MOVED THE CS-909 RECORD UNDER `## Entries`. The record's
#: pointer had been dead since 8777a89 renamed the test it cites, and nothing saw
#: it because the record sat in the shape template above the scoped heading. The
#: acceptance orders the record's bytes unchanged and the ledger is append-only, so
#: the pointer cannot be repaired in place. One RENAMED row with a live target,
#: checked in three directions - the same kind as the 54-to-55 raise, not NO_TARGET.
#:
#: 56 TO 60 WHEN CS-1112 RENAMED FOUR TESTS THE CS-1086 AND CS-1113 CLOSURES CITE.
#: The adjudicated removal of the item-notes routing rows made every row-planting
#: guard (j) arm's name false; the grant ordered them rewritten with no assertion
#: loosened, and named RENAMED dispositions as the route. Four RENAMED rows with live
#: targets, checked in three directions - the 54-to-55 kind, not NO_TARGET.
#:
#: 60 TO 63, 2026-09-20 BY CS-1162, AND IT IS A RAISE THIS FILE HAS TO DEFEND.
#: All three sites are in `docs/LEDGER.md` and all three arrived in ONE session's
#: CS-1159 records - two blank landings adjudicated as NO_TARGET above, one live
#: line pointer grandfathered into the pin above. THE HONEST PART OF THE NUMBER
#: IS THAT IT IS A RECURRENCE AND NOT A NEW GAP: the CS-1159 adjudicator record
#: already states "a line pointer into a living document is a citation with a
#: shelf life", and was itself corrected on exactly this before publishing - then
#: a later record under the same ID did it three more times. The raise is
#: therefore not the price of a mechanism that was missing; it is the price of
#: one that was stated and not followed, which is why CS-1162 put the clause in
#: the Entry-shape row of `docs/LEDGER.md` rather than restating it in prose.
#:
#: WHY NONE OF THE THREE IS A REPAIR INSTEAD. The carrier is append-only by its
#: own header, so no pointer inside a published record can be repointed where it
#: stands - the CS-300 paragraph above makes the same argument at length. The SIX
#: sibling pointers found in the same sweep, in `docs/item_notes/phase7.md` under
#: `## CS-1160`, were repaired by symbol instead and cost NOTHING, because that
#: file is live and forgiveness there would have been free and therefore wrong.
#: A seventh in `docs/history_notes.md` was rewritten to symbol form at
#: relocation time, while it was still repairable, and its archive pin did not
#: move.
#:
#: RAISED TO 64 BY CS-1167, AND FOR A RENAME RATHER THAN A POINTER. The CS-939
#: record cites the single outbound canary by path and symbol; CS-1167 replaced
#: it with one canary per rule, so the citation is right-when-written and dead
#: now. The carrier is append-only, the live target exists, and the class 6
#: row in DISPOSITIONS is RENAMED - checked in all three directions every run.
#:
#: RAISED TO 66 BY CS-1193, FOR A MOVE. The CS-1177 record cites the two
#: whole-population forced arms in the canary population module; CS-1193 moved
#: both, names unchanged, into their own file to bring the tier-1 fast shard
#: back under its ceiling. Right-when-written and dead now, in an append-only
#: carrier, with a live target - the two class 7 rows in DISPOSITIONS are
#: MOVED and checked in all three directions every run.
FORGIVEN_LINE_POINTER_CEILING: Final = 66


#: R2's live membership, DISCLOSED. Every entry is a citation at a path this
#: repository declares it will never track, so the arm cannot check it and says
#: so. `.gitignore` carries the local config override for exactly the reason
#: the citations are legitimate: the file is per-machine and its absence from
#: the index is the point.
#:
#: PINNED IN BOTH DIRECTIONS AND BUDGETED. Appending an entry ALONE makes this
#: table disagree with what the ladder derives and reddens on the spot. Appending
#: one TOGETHER WITH the dead citation it describes does not - derived and pinned
#: agree again - which is why a ceiling counts the rows as well. The first build
#: said "there is nothing to be bought by adding to it" and that was false as
#: written; see :func:`tests.bare_path_guard.decline_budget_problems`.
DECLINED_AS_DECLARED_UNTRACKED: Final[Mapping[tuple[str, str, str], int]] = {
    (
        "docs/item_notes/lane-start-failure-record.md",
        "ops/loop/config.json",
        "## 5. Hypotheses discriminated",
    ): 1,
    ("ROADMAP.md", "config/local.json", "## Phase 4 - save reader"): 1,
    ("clockspeed/solve/optimize.py", "config/local.json", ""): 1,
    ("tools/inbox_watch.py", "data/inbox_report.txt", ""): 1,
    (
        "clockspeed/surface/providers.py",
        "config/local.json",
        "SaveWorldProvider.__init__",
    ): 1,
    (
        "docs/item_notes/phase4.md",
        "config/local.json",
        "### detail - relocated from `docs/history_notes.md` 2026-08-23",
    ): 1,
    ("tests/save/test_workdir.py", "config/local.json", "isolate_from_the_real_machine"): 1,
    ("tools/precommit_gate.py", "config/local.json", ""): 1,
    (
        "docs/LEDGER.md",
        ".claude/settings.local.json",
        "### 2026-09-06 - CS-932 - CLOSED. The inbox has a watcher, and the"
        " two design points came from the two siblings that had already got"
        " them wrong once",
    ): 1,
    (
        "docs/item_notes/phase7.md",
        ".claude/settings.local.json",
        "#### 5. CS-952 is sequenced BEFORE the flip and is a hard blocker",
    ): 1,
    (
        "docs/LEDGER.md",
        ".claude/settings.local.json",
        "### 2026-09-20 - CS-1159 - FROZEN-FILE GRANT. NOT A COMPLETION RECORD."
        " NOTHING CLOSED. CS-1159 STAYS OPEN and this entry does not close it."
        " Granted by an adjudicator BEFORE the edit. Two cwd-relative hook"
        " commands in `.claude/settings.json` may be anchored to"
        " `$CLAUDE_PROJECT_DIR`, and nothing else in that file may change",
    ): 1,
    (
        "docs/LEDGER.md",
        ".claude/settings.local.json",
        "### 2026-09-08 - CS-952 - NOT A COMPLETION RECORD. A frozen-file grant"
        " was issued and deliberately NOT SPENT; the claim was corrected"
        " instead, and the guard that would have caught it twice earlier now"
        " exists",
    ): 1,
    ("tests/test_session_start_wiring.py", ".claude/settings.local.json", ""): 1,
    ("tools/inbox_watch.py", ".claude/settings.local.json", ""): 1,
    ("tests/test_outbound_send.py", "data/outbound_deliveries.json", ""): 1,
    ("ops/loop/queue_loop.py", "ops/loop/config.json", ""): 1,
    (
        "docs/adr/0023-whether-a-filename-is-personal-data.md",
        "ops/loop/config.json",
        "## Decision",
    ): 1,
    (
        "docs/item_notes/phase4-followups-900.md",
        "data/outbound_deliveries.json",
        "### MEASURED 2026-09-08 (session 76), four adversarial lenses against the REPAIRED sender",
    ): 1,
    # CS-1231 - the VENDORED fleet kit's common block names the kit's live status
    # file, which is gitignored runtime state by construction. The heading cell
    # is the block's own 80-column banner rule, which the ladder reads as the
    # nearest heading. The doc may not be edited, so the guard takes the row.
    (
        "ops/fleet_kit/FLEET-COMMON.md",
        "ops/loop/control/inbox_status.json",
        "################################################################################",
    ): 1,
    # CS-1231 - the same byte-pinned block, embedded in CLAUDE.md between its
    # FLEET-COMMON markers. It cannot be reworded locally, and the nearest
    # heading-shaped line is its banner rule.
    ("CLAUDE.md", "ops/loop/control/inbox_status.json", "#" * 80): 1,
}

#: R3's live membership, DISCLOSED. Three are the names of the three files
#: CS-928 proved never existed, spelled at module scope by the guard that now
#: asserts their absence - each twice, once in the roster it walks and once in
#: the prose that says why. Three are a guard's own metasyntactic example
#: paths, under roots this repository does not own.
#:
#: WHAT THIS ROW SET USED TO BE IS THE POINT OF READING IT. Six of the nine
#: were `docs/ARCHITECTURE.md` spelling those same three names - the rows below
#: carry the spelling - under Pillar 5, section 5.1 and section 6.2, in
#: sentences that said what each of those files DID. They said it of files that
#: do not exist. The rung declined them for a reason that was true and
#: irrelevant - `advisor/` is not a repository root, so the ladder could not
#: resolve them either way - and the disclosure recorded the decline without
#: anything ever asking whether the sentence above it was true. CS-928 asked.
#: The six sites are gone; the three that replaced them are a test ASSERTING
#: the absence rather than a doc ASSUMING the presence, which is the same
#: spelling doing the opposite job.
#:
#: PINNED AND BUDGETED, for the table above's reason.
DECLINED_UNDER_AN_UNTRACKED_ROOT: Final[Mapping[tuple[str, str, str], int]] = {
    ("tests/data/test_drift_guard_data.py", "notes/DONE.md", "_WORK_ITEM_CLAUDE_MD"): 1,
    ("tests/test_chained_cause_census.py", "also/not/frozen.py", "_FROZEN_MARKDOWN"): 1,
    ("tests/test_chained_cause_census.py", "not/frozen.py", "_FROZEN_MARKDOWN"): 1,
    ("THIRD_PARTY.md", "execnet/gateway_base.py", "### Python dependencies"): 1,
    ("THIRD_PARTY.md", "licenses/LICENSE.txt", "### Python dependencies"): 1,
    ("THIRD_PARTY.md", "pathspec/_meta.py", "### Python dependencies"): 1,
}

#: R4's live membership, DISCLOSED. Every entry is a synthetic fixture path
#: inside a Python string literal that is not a docstring - data a guard feeds
#: itself, which is supposed not to exist and would be a defect if it did.
#:
#: PINNED AND BUDGETED, for the tables above's reason. This is the rung
#: whose price is easiest to underrate: a real dead citation moved inside a
#: non-docstring literal becomes invisible, so the disclosure has to name every
#: site the rung answers rather than merely count them.
DECLINED_AS_A_FIXTURE_LITERAL: Final[Mapping[tuple[str, str, str], int]] = {
    (
        "tests/save/test_absolute_claims.py",
        "tests/synthetic/test_beta.py",
        "_CONTROL_BARE_SHAPE",
    ): 1,
    (
        "tests/save/test_absolute_claims.py",
        "tests/synthetic/test_beta.py",
        "_CONTROL_DENIED_EXCLUSION",
    ): 1,
    (
        "tests/save/test_absolute_claims.py",
        "tests/synthetic/test_beta.py",
        "_CONTROL_NEGATED_SHAPE",
    ): 1,
    ("tests/save/test_absolute_claims.py", "tests/synthetic/test_beta.py", "_CONTROL_SPAN"): 1,
    (
        "tests/save/test_absolute_claims.py",
        "tests/synthetic/test_beta.py",
        "_CONTROL_STATED_EXCLUSION",
    ): 1,
    ("tests/test_chained_cause_census.py", "scripts/example.py", ""): 1,
    ("tests/test_chained_cause_census.py", "scripts/example.py", "_FROZEN_MARKDOWN"): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/_archive/digest-2026-09-01.md",
        "test_a_dated_artifact_inside_the_archive_is_not_stale",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/also.md",
        "test_an_empty_comment_closes_itself",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/cited.md",
        "test_a_backticked_path_mention_is_a_reference",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/digest-2026-09-01.md",
        "test_a_dated_artifact_outside_the_archive_is_stale",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/ledger.md",
        "BASE_FILES",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/self.md",
        "test_a_self_reference_does_not_rescue_an_orphan",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/shown.md",
        "test_a_mention_after_a_closed_comment_on_its_line_is_a_reference",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "docs/shown.md",
        "test_an_empty_comment_closes_itself",
    ): 1,
    (
        "tests/test_doc_sweep.py",
        "tools/x.py",
        "test_a_fragment_into_a_non_markdown_target_is_skipped_and_counted",
    ): 1,
}

#: THE THREE DECLINE DISCLOSURES' RECORDED BUDGETS, one per rung and never
#: pooled, for the reason :func:`tests.bare_path_guard.decline_budget_problems` states. Each is an
#: integer literal a person typed, which
#: :func:`tests.bare_path_guard.derived_bound_problems` is what keeps true.
#: 7 TO 8 FOR CS-952, WHICH IS AN ITEM ABOUT THE PATH ITS NEW ROW NAMES. The
#: item records that the inbox watcher's whole wiring lives in the gitignored
#: per-machine settings override, so a fresh clone runs no watcher while the
#: property was published as YES. The citation cannot be checked because that
#: file is per-machine by design, and naming it is the item's entire content -
#: so the row is bought rather than the sentence reworded to slip past the
#: ladder.
#:
#: THIS COMMENT DELIBERATELY DESCRIBES THAT PATH RATHER THAN CITING IT. The
#: first draft wrote it as a code span and thereby created a SECOND undisclosed
#: citation, inside the guard's own file, which the guard then caught. A
#: disclosure that has to disclose itself ratchets forever.
#:
#: 8 TO 9 FOR CS-700, WHICH INHERITS CS-952'S PURCHASE RATHER THAN MAKING A NEW
#: ONE. The public-flip plan sequences CS-952 as a hard blocker on the flip -
#: gate item 7 is a clean-checkout probe, and a fresh clone runs no watcher for
#: exactly the reason the row above records. The plan's section 5 has to name
#: the same per-machine override file to say what the blocker IS, so it buys the
#: same row against a second carrier. The alternative was to describe the file
#: obliquely in the one document whose job is to be executable by a session that
#: was not here, which trades a disclosed row for an ambiguous instruction.
#: THIS COMMENT DESCRIBES THAT PATH RATHER THAN CITING IT, for the reason the
#: paragraph above gives.
#: 9 TO 12 FOR CS-952'S REPAIR, AND THE THREE ROWS ARE THE REPAIR RATHER THAN A
#: COST OF IT. The defect was a published claim that a watcher fires, when the
#: hook declaring it lives in a per-machine override file this repository does
#: not track. Every correction of that claim has to say WHICH FILE holds the
#: wiring, because "it is wired somewhere untracked" is the ambiguity that let
#: the row read as a property of the repository twice. So the ledger record, the
#: tool whose own docstring made the claim, and the guard that now grades the
#: claim against the shipped wiring each name it once. Describing it obliquely
#: was available and was rejected for the same reason the row above rejects it:
#: an oblique instruction is a row not bought and a reader not told.
#: 12 TO 11 WHEN CS-952 CLOSED AND ITS DETAIL LEFT THE LIVE LEAF. The row the
#: item note held is gone rather than moved: the closed section relocated to
#: `docs/history_notes.md`, which this corpus does not carry, so the site stopped
#: existing rather than changing carrier. A relocation on closure therefore
#: REFUNDS a disclosed row, and the ceiling has to come down with it or the
#: refund becomes headroom nobody voted for.
#: 11 TO 12 FOR CS-958'S DELIVERY RECORD. The sender writes its record under
#: `data/`, which is gitignored because the record is a generated runtime
#: artifact rather than a tracked fact. The test module names that default path
#: once, to say what the environment override it uses is an override OF - an arm
#: that redirected the record without naming what it redirected would leave the
#: next reader unable to tell an override from an invention. The module under
#: test buys no row: it builds the same path from components rather than
#: spelling it, which is not a citation.
#: 12 TO 13 WHEN CS-958'S REFUTATION RECORD NAMED THE RECORD IT PROTECTS. The
#: item note has to say WHICH file an adversary was forbidden to append to, and
#: naming it is the whole content of that constraint - a note that said "the
#: delivery record" would leave the next grader to guess, and a grader that
#: guesses wrong writes to the operator's live history. The row is bought for
#: the leaf that carries the finding, not for the item: when CS-958 closes and
#: its detail relocates to `docs/history_notes.md`, this row REFUNDS and the
#: ceiling comes back down with it, exactly as CS-952's did.
#: 13 TO 14 WHEN SESSION 91 FILED THE LANE START-FAILURE DIAGNOSIS. That annex
#: names the lane's optional model-config file to record that it DOES NOT EXIST
#: - the whole
#: content of the refuted model-config hypothesis is the file's absence, so the
#: path has to be spelled or the row says nothing a reader can check. The file is
#: gitignored and will never be tracked, which is what puts it on this rung. The
#: row is bought for the leaf that carries the finding: if that diagnosis
#: relocates to `docs/history_notes.md` the row REFUNDS and the ceiling comes
#: back down to 13.
#: 14 TO 15 FOR CS-1095'S OVER-CAP REPORT, AND THE REASON IS WHY THE ROW
#: CANNOT BE REPOINTED. `tools/inbox_watch.py` names the report it writes,
#: because the cross-repo watcher contract requires the over-cap pointer line
#: to name the file it wrote, and the watcher writes that file ATOMICALLY
#: BEFORE stdout so the pointer can never name an absent one. The report lives
#: under the generated-artifact directory the ignore rules already exclude, so
#: it will never be tracked - which is the whole of what puts it on this rung,
#: the same standing the local configuration row has. Repointing it would mean
#: the transcript names a file the reader cannot find, which is the defect that
#: clause of the contract exists to prevent. The row REFUNDS and the ceiling
#: returns to 14 if the report ever stops being named in the transcript.
#:
#: NOTE FOR THE NEXT EDITOR OF THIS BLOCK: do not spell an untracked path in
#: this comment. The first draft cited two and the guard counted its own
#: disclosure as two fresh declines, because this table is part of the corpus
#: it describes. Name the rung and the symbol, never the path.
#:
#: 15 TO 16 FOR THE CS-1159 GRANT RECORD'S RESIDUE POINTER, 2026-09-20 BY
#: CS-1162, AND IT IS THE SAME STANDING THE TWO EARLIER `docs/LEDGER.md` ROWS
#: HAVE. The grant record flags that the SessionStart hook in the same rung's
#: local settings file carries the identical relative path, is out of scope, and
#: can never be pinned by a tracked test because the index will never carry it -
#: which is the rung's whole criterion and the reason the citation is legitimate
#: rather than dead. It is the residue of the grant, named so a reader does not
#: have to rediscover it, and there is nowhere else to name it from. The row
#: REFUNDS and the ceiling returns to 15 if that sentence ever stops naming the
#: file. Appended TOGETHER WITH the citation it describes would have been the
#: silent path this budget exists to price; the citation was already in the tree
#: and red, so this row is the disclosure catching up with it.
#:
#: 16 TO 17 FOR THE LANE DRIVER'S USAGE BACK-OFF COMMENT, 2026-09-24 BY CS-1178.
#: The comment above the usage-refusal back-off constant in the lane driver names
#: the lane's machine-local configuration file to say why the value is a named
#: constant and NOT a key there: that file is ignored, absent from every
#: worktree, so a value held in it would be one no arm and no reviewer can see.
#: The citation is the argument itself - the untracked file IS the reason - so
#: repointing it would delete the reason, and there is nowhere tracked to point.
#: Same standing as the lane-start failure record's row, which names the same
#: file. The row REFUNDS and the ceiling returns to 16 if that comment ever stops
#: naming the file. As above, the citation was already in the tree and red when
#: this row was added; it was not appended together with it.
#:
#: 17 TO 18 FOR ADR 0023's RULE 5, 2026-09-25 BY CS-1158. Rule 5 names the lane's
#: machine-local configuration file as its example of a fixed name this
#: repository chose itself - the class of skipped path whose name RENDERS and so
#: serves as the renderer's control. The example IS an untracked file by
#: construction: it is skipped because git ignores it, which is what makes it an
#: example of rule 5 at all, and there is nothing tracked to repoint it at. Same
#: standing as the two rows above that name the same file. The row REFUNDS and
#: the ceiling returns to 17 if the ADR ever stops naming the file. The citation
#: arrived with the ADR at the CS-1158 merge and was red before this row existed.
#:
#: 18 TO 20 FOR THE VENDORED FLEET KIT, 2026-10-03 BY CS-1231 - TWO ROWS, ONE
#: CITATION IN TWO FILES. FLEET-COMMON.md names the kit's live status file under
#: the lane's control directory, which this tree gitignores as runtime state, and
#: the file is byte-pinned by the kit's MANIFEST.json; the same block is embedded
#: byte-for-byte in CLAUDE.md between its FLEET-COMMON markers. Neither copy can
#: be repointed here. Each row REFUNDS, and the ceiling returns to 18, if a kit
#: version stops naming the file.
DECLARED_UNTRACKED_CEILING: Final = 20
#: 9 TO 6 WHEN CS-928 DELETED THE THREE FALSE ADVISOR ATTRIBUTIONS. Six
#: `docs/ARCHITECTURE.md` rows left the rung and three arrived from the guard
#: that now asserts those files absent, so the disclosure holds six rows and the
#: ceiling comes down to six. It counts ROWS, not sites: the three new rows
#: disclose two sites each.
#:
#: 6 TO 9 FOR CS-1185'S LICENCE REGISTER, 2026-09-25. Under its Python
#: dependencies heading the register names, for three packages, the file
#: inside the INSTALLED distribution that carries its licence text or its
#: copyright holder - a path relative to that package's own root, which this
#: repository does not own and which is never tracked here. Naming the file is
#: the register's evidence for the verdict it records, so repointing it would
#: delete the evidence, and there is nowhere tracked to point. The citations
#: were already in the tree and red when these rows were added; they were not
#: appended together with them. The rows REFUND and the ceiling comes back
#: down if the register ever stops naming those files.
#: 9 TO 6 FOR CS-500, 2026-10-04. The three advisor rows refunded: the files
#: now exist, so the rung resolves their spellings instead of declining them.
UNTRACKED_ROOT_CEILING: Final = 6
#: 7 TO 16 FOR CS-1184'S DOC SWEEP TESTS, 2026-09-25. Every new row is a
#: synthetic markdown or code path that the sweep's own unit tests write into a
#: throwaway repository under a temporary directory, to plant an orphan, a
#: reference, a dated artifact or a non-markdown anchor target and grade what
#: the sweep reports. Each is supposed NOT to exist in this tree, and would be
#: a defect if it did. The rows are bought for the test module, not for the
#: item, so closing CS-1184 refunds none of them. As above, the literals were
#: already in the tree and red when these rows were added.
FIXTURE_LITERAL_CEILING: Final = 16


#: THE ONLY BUDGET IN THIS SECTION. Everything above is a disclosure that
#: cannot be added to; this is the escape hatch, and it ratchets.
#:
#: FOUR ENTRIES, TWO OF ONE KIND AND TWO SINGLETONS, and each is checked
#: against the corpus in three directions by
#: :func:`tests.bare_path_guard.bare_path_reason_problems`.
#:
#: - ONE PLANNED MODULE, named twice by the two phase leaves that plan it - the
#:   card-state store phase 5 will build. A leaf that plans a module has to be
#:   able to name it, and creating an empty module to satisfy a guard would be
#:   the guard writing the code. The citation is right and the tree has not
#:   caught up. The rows below carry the spelling; this bullet does not, for
#:   the reason the fourth one gives.
#:
#:   THIS BULLET USED TO READ "THREE PLANNED MODULES, cited repo-relative in
#:   the module map", and the module-map half was WRONG - not stale, wrong. It
#:   forgave `docs/ARCHITECTURE.md` for attributing owned capability to three
#:   advisor modules that have never existed, on the argument that "deleting
#:   the rows would make the architecture doc silent about the phase it exists
#:   to describe". CS-928 refuted that: the doc now says NOT BUILT and names
#:   what `BOOTSTRAP.md` specifies, which is neither silence nor a false
#:   attribution. The three rows went with it and their forgivenesses are spent
#:   down here. A record that outlives what it answered is the direction
#:   :func:`tests.test_docs_citations.stale_pin_problems` exists to catch, and it caught these.
#: - ONE PATH DELIBERATELY NOT CREATED, QUOTED RATHER THAN CITED. ADR 0010
#:   records the decision that the item-notes family gets no index file of that
#:   name, and it names the path in order to say so. This is trap 4 in the
#:   bare-path arm: a record whose evidence is that the target is absent would
#:   be punished for being right.
#: - ONE OF THE SIBLING MODULE'S OWN, which is the self-infliction the section
#:   warns about arriving anyway. A docstring in ``tests/test_docs_citations.py``
#:   explains a synthetic corpus by naming its third member, and that member is
#:   metasyntactic by construction. Recorded rather than reworded, because the
#:   sentence is precise and the alternative - describing the member without
#:   naming it - trades a checked record for vaguer prose. The row lives HERE
#:   because this file holds the table; the site it answers is still over there,
#:   which is why its key names that file rather than this one.
#: CS-899's rung, disclosed in both directions exactly as the other declines
#: are, and BUDGETED besides - a decline is invisibility bought for a reason,
#: and the reason has to be defensible whether it is spelled in a table or in
#: the carrier.
#:
#: WHAT A ROW HERE COSTS, AND WHY IT IS NOT THE SAME PURCHASE AS A FORGIVENESS.
#: A row can only be added together with a declaration a human wrote into a
#: tracked doc, and that declaration goes red on its own the moment the path it
#: calls absent becomes tracked. So this table does not buy permanent silence:
#: it records which carriers are currently making an absence claim, and the
#: claim is re-checked against the tree on every run.
#:
#: ALL THREE ROWS CAME OFF :data:`BARE_PATH_REASONS` IN THE SAME CHANGE, and
#: that ceiling fell by three. This is a MOVE rather than a widening, and the
#: two budgets together say so.
DECLARED_ABSENT_IN_DOC: Final[Mapping[tuple[str, str, str], int]] = {
    (
        "docs/adr/0010-item-notes-is-an-index-over-per-phase-leaves.md",
        bare_path("docs", "item_notes", "README.md"),
        "## Decision",
    ): 1,
}

#: The ceiling on the rung above. Spelled rather than derived, for the reason
#: :func:`tests.bare_path_guard.derived_bound_problems` enforces on every other
#: bound in this family.
#: 3 TO 1 FOR CS-500, 2026-10-04: the ledger landed, both absence
#: declarations on it were dropped and their rows refunded.
DECLARED_ABSENT_CEILING: Final = 1

BARE_PATH_REASONS: Final[Mapping[tuple[str, str, str], BarePathReason]] = {
    # CS-899 RETIRED THREE ROWS FROM HERE AND DID NOT FORGIVE THEM ELSEWHERE.
    # All three were markdown discussing-prose - an ADR recording that a path is
    # deliberately not created, and two leaves naming the phase 5 ledger module
    # that does not exist yet. Each now DECLARES the absence on its own line and
    # is answered by the ladder's :data:`tests.bare_path_guard.DECLARED_ABSENT`
    # rung, which is checked in three directions rather than spent once. What is
    # left here is the one site that is NOT a markdown carrier.
    # THE CARRIER IS SPELLED AS A PLAIN LITERAL HERE, AND THAT IS THE RIGHT
    # SPELLING AT THIS SITE FOR THE REASON THE OTHER ONE WAS WRONG AT ITS OWN.
    # `tests/test_docs_citations.py` derives its own path rather than spelling
    # it, because a module that cites ITSELF is a site the self-infliction arm
    # then measures against its own spelling instead of against the tree. This
    # row is in a SIBLING module, so the objection does not apply: the key names
    # another file, exactly as every other row here does, and deriving it would
    # mean importing that module for a string - which is the one import this
    # file may not take, since the dependency runs the other way. The literal
    # carries no backticks, so the bare-path shape does not read it as a
    # citation at all - the same reason :data:`MANIFEST` above is safe to spell.
    (
        "tests/test_docs_citations.py",
        bare_path("docs", "prose.md"),
        "test_a_doc_carrying_no_citation_is_asked_for_neither_a_guard_nor_a_record",
    ): BarePathReason(
        "the sibling module's own metasyntactic corpus member, named by the docstring"
        " that explains what the corpus is for. It is supposed not to exist.",
        1,
    ),
}

#: THE BARE-PATH RATCHET'S RECORDED BUDGET, SEPARATE from the line-pointer one
#: for the reason :func:`bare_path_budget_problems` states. Checked in BOTH
#: directions, so it can only come down.
#:
#: 7 TO 4 WHEN CS-928 REPAIRED THE MODULE MAP. Three forgivenesses were spent on
#: rows that attributed owned capability to three files that do not exist; the
#: rows are gone and the ceiling comes down with them. The ratchet caught this
#: itself - the reason table reported all three stale before the number moved.
BARE_PATH_REASON_CEILING: Final = 1


def scoped_text(doc: str, text: str) -> str:
    """Return the part of a doc whose citations are adjudicated.

    Args:
        doc: The repo-relative doc path.
        text: Its full text.

    Returns:
        For the ledger, everything below the entries heading - the preamble's
        illustrative pointers are documentation of the citation SHAPE and name
        no real test. For every other doc, the whole text.
    """
    if doc != LEDGER:
        return text
    _head, marker, tail = text.partition("\n" + ENTRIES_HEADING)
    return tail if marker else text


def forgiveness_budget_problems(
    pins: Iterable[tuple[str, str, int]],
    dispositions: Mapping[tuple[str, str], Disposition],
    ceiling: int,
) -> list[str]:
    """THE RATCHET. Every way of silencing this arm is counted, and it may only shrink.

    WHY THIS EXISTS, and it is the sharpest refutation this module has taken.
    An adversary appended three tuples to the pin and two fabricated
    :class:`Disposition` entries whose reason strings nothing verifies, and got
    the whole suite GREEN with every live defect still in the tree. Five table
    appends, zero repairs. Leaving findings red rather than laundering them was
    RESTRAINT, and restraint is not a mechanism - the next agent under time
    pressure had a one-line escape from every finding this arm will ever make.

    THE BUDGET SPANS BOTH TABLES BECAUSE THE ESCAPE DOES. Counting only the pin
    would leave the fabricated-disposition half of that attack working, and a
    disposition is the STRONGER escape of the two - it silences leg 1 as well.

    ADJUDICATING A PIN IS BUDGET-NEUTRAL, which is what keeps the ratchet from
    obstructing the repair it exists to force. Moving a site out of the pin and
    into :data:`DISPOSITIONS` spends one forgiveness either way, so the ceiling
    does not move. That matters most where the fix cannot be a symbol
    conversion: a pin carried by the append-only ledger has nowhere else to go,
    and the budget lets it be upgraded from unexamined to answered for free
    while still refusing a genuinely NEW forgiveness.

    WHAT THIS DOES NOT DO, stated because the gap is real. It cannot tell a
    fabricated reason from a true one: a ``NO_TARGET`` or ``DELIBERATE`` record
    names nothing to verify, by construction. What it removes is the ability to
    add one SILENTLY. Recording a new forgiveness now reddens the suite until
    the ceiling is raised in the same change, so the raise sits in the diff as
    a number somebody has to defend - and the two-way check below means it
    cannot be left slack afterwards to bank room for the next one.

    Args:
        pins: The grandfathered sites.
        dispositions: The full table; only line-pointer keys are counted.
        ceiling: The recorded budget.

    Returns:
        One line per direction that has drifted. OVER the ceiling is a
        forgiveness added without argument. UNDER it is a ceiling gone slack
        after a repair, which is banked room for a future append.
    """
    # EVERY DISPOSITION COSTS, NOT ONLY THE LINE-POINTER-KEYED ONES. Counting
    # only the line form left 13 of 21 rows free, so a symbol-keyed
    # `Disposition(NO_TARGET, ...)` silenced a brand-new dead citation with no
    # ceiling to raise and no number in the diff for anyone to defend - which is
    # the precise escape the docstring below says the budget closed. MEASURED:
    # dropping the four unverifiable symbol-form rows failed five arms while the
    # budget stayed green at 53 against 53, so they were load-bearing and free.
    spent = len(set(pins)) + len(set(dispositions))
    if spent > ceiling:
        return [
            f"{spent} forgivenesses recorded against a ceiling of {ceiling}."
            " Something was added to the pin or to DISPOSITIONS. That is a finding"
            " to argue, not a line to type: repair the pointer, or raise the"
            " ceiling in this same change and say why in the record."
        ]
    if spent < ceiling:
        return [
            f"{spent} forgivenesses recorded against a ceiling of {ceiling}."
            f" A pointer was repaired and the ceiling was not lowered to match."
            f" Lower it to {spent} - a slack ceiling is banked room for an append"
            " nobody will have to defend."
        ]
    return []


#: Wall-clock bound for the git plumbing below (CS-896). An unbounded child
#: cannot fail the test that owns it - it burns the CI job's whole budget until
#: the lane is cancelled, which is evidence of nothing. 120s matches the git
#: timeout in tests/test_doc_budget.py and tests/test_commit_msg_gate.py. It is
#: deliberately generous: the job is to bound a hang, not to police speed, and a
#: tight value under two-worker contention on a 2-vCPU runner is a new flake.
GIT_TIMEOUT: Final = 120


def tracked_files() -> list[str]:
    """Every path in this checkout's index, POSIX-separated."""
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
        timeout=GIT_TIMEOUT,
    ).stdout
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


@pytest.fixture(scope="module")
def tracked() -> list[str]:
    return tracked_files()


@pytest.fixture(scope="module")
def sources(tracked: list[str]) -> dict[str, str]:
    return {
        path: (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in tracked
        if path.endswith(".py")
    }


@pytest.fixture(scope="module")
def file_lines(tracked: list[str]) -> dict[str, list[str]]:
    """Every tracked file's lines, so a pointer's LANDING can be read.

    The range arm needs only a count; the CS-889 arms need the line itself.
    Reading once and deriving the count keeps the two from disagreeing about
    what a line even is - both split on the same newline character, and a
    second reader that split differently would report a pointer in range for
    one arm and out of it for the other.
    """
    lines: dict[str, list[str]] = {}
    for path in tracked:
        try:
            body = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines[path] = body.split("\n")
    return lines


@pytest.fixture(scope="module")
def line_counts(file_lines: Mapping[str, Sequence[str]]) -> dict[str, int]:
    return {path: len(lines) for path, lines in file_lines.items()}


@pytest.fixture(scope="module")
def line_pointer_carriers(file_lines: Mapping[str, Sequence[str]]) -> dict[str, str]:
    """Every text a ``file:line`` pointer is read out of, keyed by carrier.

    EVERY TRACKED FILE, MINUS THE RECORDED EXEMPTIONS. The first build of this
    fixture read the guarded docs plus tracked Python modules, and justified
    the Python half with the argument that a population stopping at ``docs/``
    "would have reported them absent rather than judged them". THAT ARGUMENT
    APPLIES VERBATIM TO EVERY OTHER EXTENSION AND WAS NOT FOLLOWED. It cost a
    live defect: a blank-line pointer cited from a JavaScript test was green,
    and ``pyproject.toml`` held a pointer at the SAME ``(path, line)`` pair
    already grandfathered under a doc carrier - the identical pointer inside
    the population from one carrier and outside it from another.

    A SUFFIX LIST WOULD HAVE BEEN THE OBVIOUS FIX AND IS THE WRONG ONE. It is a
    hand-maintained boundary, so the next extension to start carrying a pointer
    joins the unguarded set in silence - which is this module's founding
    finding, "nothing in this repository read docs/", repeating a third time.
    Taking every tracked file makes the boundary complete BY CONSTRUCTION.

    IT COSTS NO EXTRA READ. ``file_lines`` has already read every tracked file
    for the range arm, so the widening is a re-key of bytes already in memory.

    THE EXEMPTIONS ARE THE ONES THIS MODULE ALREADY RECORDS, reused rather than
    duplicated: :data:`UNGUARDED_DOCS` for the deep archive, whose pointers rot
    by construction and whose population is counted by
    ``tests/test_archive_rot.py`` instead, plus the dated archive and the
    harness configuration that are out of domain entirely. A second exemption
    table would be a second place for the same fact to rot.

    The ledger is SCOPED and everything else is not: scoping exists to keep the
    ledger's illustrative preamble out of adjudication, and no other file has
    one.
    """
    carriers: dict[str, str] = {}
    for path, lines in file_lines.items():
        if path in UNGUARDED_DOCS or path.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN)):
            continue
        carriers[path] = scoped_text(path, "\n".join(lines))
    return carriers


@pytest.fixture(scope="module")
def module_basenames(tracked: list[str]) -> frozenset[str]:
    """Tracked module basenames without the extension.

    A bare ``test_properties`` is a MODULE, not a test. Hoisted to a fixture
    because every guarded doc's bare arm needs it, and recomputing it per
    parametrization would re-walk the index once per doc.
    """
    return frozenset(path.rsplit("/", 1)[-1][:-3] for path in tracked if path.endswith(".py"))


def in_domain(path: str) -> bool:
    """Whether a tracked path is documentation this module adjudicates.

    A NAMED PREDICATE RATHER THAN A COMPREHENSION, because a filter written
    inline into a fixture cannot be tested: asking the fixture whether its
    output contains what it filtered out re-asserts the comprehension and
    cannot fail. This can be asked about a path that does not exist.

    THE DATED ARCHIVE IS EXCLUDED FOR THE REASON IT IS EXCLUDED EVERYWHERE
    ELSE. :func:`line_pointer_carriers` has skipped it since it was built, and
    this predicate did not, so one tracked file was outside one arm's
    population and inside the other's. It cost nothing while every judged shape
    needed a separator after the path, and it would cost the moment a shape
    reads the bare path: CLAUDE.md section 4 keeps dated artifacts out of every
    search for current truth, and a widened guarded set would have taken one in.

    Args:
        path: A repo-relative POSIX path.

    Returns:
        True for tracked markdown outside :data:`OUT_OF_DOMAIN` and
        :data:`DATED_ARCHIVE`.
    """
    return path.endswith(".md") and not path.startswith((OUT_OF_DOMAIN, DATED_ARCHIVE))


@pytest.fixture(scope="module")
def markdown_texts(tracked: list[str]) -> dict[str, str]:
    return {path: doc_text(path) for path in tracked if in_domain(path)}


def doc_text(doc: str) -> str:
    return (REPO_ROOT / doc).read_text(encoding="ascii", errors="replace")


@pytest.fixture(scope="module")
def live_bare_path_sites(line_pointer_carriers: Mapping[str, str]) -> list[BarePathSite]:
    """Every bare-path spelling in the LINE-POINTER population.

    THE EXISTING POPULATION, CONSUMED RATHER THAN REBUILT. Its boundary - every
    tracked file less the recorded exemptions - is already asserted in both
    directions by a contract, so a second population here would be a second
    thing to rot and a second place for the two to disagree. That disagreement
    is not hypothetical: `in_domain` and this very fixture's boundary already
    diverged once over the dated archive.
    """
    return bare_path_sites(line_pointer_carriers)


@pytest.fixture(scope="module")
def live_declared_untracked(live_bare_path_sites: Sequence[BarePathSite]) -> frozenset[str]:
    """R2's answer for the live corpus, in ONE batched call rather than one per path."""
    return declares_untracked(sorted({site.cited for site in live_bare_path_sites}))


@pytest.fixture(scope="module")
def live_source_roots(tracked: list[str]) -> frozenset[str]:
    """R1's candidate set for the live repository, derived from its own manifests."""
    return source_roots(tracked, (REPO_ROOT / MANIFEST).read_text(encoding="ascii"))


@pytest.fixture(scope="module")
def live_bare_path_ladder(
    live_bare_path_sites: Sequence[BarePathSite],
    tracked: list[str],
    live_declared_untracked: frozenset[str],
    live_source_roots: frozenset[str],
) -> dict[str, list[BarePathSite]]:
    return bare_path_ladder(
        live_bare_path_sites,
        tracked,
        live_declared_untracked,
        BARE_PATH_REASONS,
        live_source_roots,
    )


def test_the_deep_archive_is_the_only_doc_left_unguarded() -> None:
    """CS-809's acceptance as literally written: a check that it stays the only one.

    The contracts above bound the unguarded set - nothing joins it quietly and
    nothing lingers in it. This one pins its MEMBERSHIP, so a second exemption
    is a deliberate edit here with a reason someone had to write, rather than a
    line added to a table while the suite stays green. WAKEUP_NOTES.md is the
    reason this is worth pinning: it was recorded here on a reason that
    measured false, and the set having one member is what makes a second one
    conspicuous.
    """
    assert DEEP_ARCHIVE == "docs/history_notes.md", (
        f"DEEP_ARCHIVE now names {DEEP_ARCHIVE}. Naming the file once is what keeps the"
        " exemption, the boundary contracts and the CS-897 rot pin talking about the same"
        " file - and it is also what would let the membership check below be satisfied by"
        " REDEFINING the name rather than by guarding the newcomer, so the name is pinned"
        " to a literal here. That is the one place the path may be spelled twice."
    )
    assert set(UNGUARDED_DOCS) == {DEEP_ARCHIVE}, (
        "the recorded-unguarded set is no longer the deep archive alone:\n"
        + "\n".join(f"  {doc}" for doc in sorted(UNGUARDED_DOCS))
        + "\nGuard the newcomer, or change this contract deliberately and say why."
    )


def test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow() -> None:
    """THE RATCHET, on the live tables.

    An adversary appended three pins and two fabricated dispositions and shipped
    this module GREEN with every live defect intact. Nothing bounded either
    table. Now every forgiveness is counted against one recorded number, and
    both directions are findings: over the ceiling is an append nobody argued
    for, under it is a ceiling left slack to bank room for the next one.
    """
    problems = forgiveness_budget_problems(
        UNVERIFIED_LINE_POINTERS, DISPOSITIONS, FORGIVEN_LINE_POINTER_CEILING
    )

    assert not problems, "\n".join(problems)


def test_the_bare_path_reason_budget_is_spent_exactly_and_cannot_grow() -> None:
    """THE RATCHET, on the live table, and it is SEPARATE from the line-pointer one.

    CS-889's round-one defect was an arm whose every finding could be silenced
    by appending to a table. That was repaired for line pointers and the repair
    did NOT generalise: a bare-path key spends nothing in
    :func:`forgiveness_budget_problems`, because that function counts only keys
    matching :data:`tests.test_docs_citations.LINE_POINTER_RE`. A bare-path forgiveness would have
    been
    silenceable the day it shipped.
    """
    problems = bare_path_budget_problems(BARE_PATH_REASONS, BARE_PATH_REASON_CEILING)

    assert not problems, "\n".join(problems)


@pytest.mark.parametrize(
    ("rung", "pinned"),
    [
        (DECLARED_UNTRACKED, DECLINED_AS_DECLARED_UNTRACKED),
        (UNTRACKED_ROOT, DECLINED_UNDER_AN_UNTRACKED_ROOT),
        (FIXTURE_LITERAL, DECLINED_AS_A_FIXTURE_LITERAL),
        (DECLARED_ABSENT, DECLARED_ABSENT_IN_DOC),
    ],
)
def test_every_bare_path_decline_rung_is_disclosed_in_both_directions(
    rung: str,
    pinned: Mapping[tuple[str, str, str], int],
    live_bare_path_ladder: Mapping[str, Sequence[BarePathSite]],
) -> None:
    """Each rung's price, PINNED rather than described.

    A decline is invisibility bought for a reason. Naming the reason in prose
    costs nothing and proves nothing; pinning the sites means an append
    DISAGREES with what the ladder derives and reddens, so the table cannot be
    used to buy silence. That is :data:`tests.test_docs_citations.UNFORBIDDEN_LINE_POINTERS`' shape,
    and
    it is what separates a disclosure from a permission list.
    """
    assert pinned, f"{rung} discloses nothing, so this arm measures an empty set"

    problems = pinned_rung_problems(live_bare_path_ladder, rung, pinned)

    assert not problems, f"the {rung} disclosure disagrees with the corpus:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


#: EVERY FORGIVENESS TABLE THIS MODULE HOLDS, and the contract that BOUNDS it.
#: THE REGISTRY TRAVELS WITH THE TABLES, which is what
#: :func:`tests.bare_path_guard.registry_problems` requires of any module in
#: this family: a bounded table's contract must be a ``test_``-prefixed callable
#: THIS namespace defines, so a table cannot be registered here against an arm
#: that lives one file over and might quietly stop reading it.
#:
#: THE CEILING OF THE MECHANISM, STATED, and it is the same one the sibling
#: module states about its own registry: a false sentence in
#: :data:`NOT_A_FORGIVENESS` still silences the walk. What cannot be done is
#: adding one SILENTLY - the entry sits in the diff as a claim somebody has to
#: defend.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {
    "DISPOSITIONS": "test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow",
    "UNVERIFIED_LINE_POINTERS": "test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow",
    "UNGUARDED_DOCS": "test_the_deep_archive_is_the_only_doc_left_unguarded",
    "BARE_PATH_REASONS": "test_the_bare_path_reason_budget_is_spent_exactly_and_cannot_grow",
    "DECLINED_AS_DECLARED_UNTRACKED": (
        "test_every_bare_path_decline_rung_is_disclosed_in_both_directions"
    ),
    "DECLINED_UNDER_AN_UNTRACKED_ROOT": (
        "test_every_bare_path_decline_rung_is_disclosed_in_both_directions"
    ),
    "DECLINED_AS_A_FIXTURE_LITERAL": (
        "test_every_bare_path_decline_rung_is_disclosed_in_both_directions"
    ),
    "DECLARED_ABSENT_IN_DOC": ("test_every_bare_path_decline_rung_is_disclosed_in_both_directions"),
}

#: The other half of the same walk: every module-scope container that forgives
#: NOTHING, with the reason it does not. Recorded rather than filtered out, for
#: the reason the sibling module gives about its own: a filter is a boundary
#: nobody re-derives, and the next table that happens to match it joins the
#: unbounded set in silence.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
}
