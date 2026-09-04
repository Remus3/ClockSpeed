#!/usr/bin/env python3
"""CS-442 - the Verification pointer in ``docs/`` is guarded, or it is not evidence.

WHY THIS MODULE EXISTS, and the structural fact is sharper than the typo that
opened the item: NOTHING IN THIS REPOSITORY READ ``docs/``.
``tests/save/test_oracle_citations`` scans ``clockspeed/``,
``tests/save/test_absolute_claims`` scans ``tests/``, and neither looked at
``docs/`` at all. So the VERIFICATION POINTER - the one field
``docs/LEDGER.md`` declares mandatory, and the entire reason that file is
trustworthy - was the least guarded prose in the project.

THE RESOLVER IS IMPORTED, NOT TRANSCRIBED, for the reason
``test_absolute_claims`` states about itself: another copy of it would be
another place to get it subtly wrong. :func:`module_scope_names` WIDENS the
imported resolver rather than replacing it, and the widening is stated in its
docstring because it is the difference between the two questions - a pytest
node id can only address a module-level function, while a docs citation may
legitimately name a class or a module-level constant.

SIX TRAPS SHAPE THIS MODULE. Each was measured on the real corpus, and a
checker that misses any one of them is red on correct history, which is the
failure that gets a guard switched off.

1. A DEAD CITATION IS NOT ONE THING. A record that was RIGHT WHEN WRITTEN and
   whose target the tree later moved is not a defect in the record. A record
   that was WRONG WHEN WRITTEN is. ``docs/LEDGER.md`` is append-only, so the
   second cannot be repaired by editing the entry that carries it - it needs a
   later correcting record. :data:`DISPOSITIONS` is where that distinction is
   recorded, and every entry in it is MACHINE-CHECKED rather than believed.

2. AN UNQUALIFIED CITATION IS NOT A DEAD ONE. A bare basename like
   ``registry.py:206`` resolved repo-relative and then declared missing
   manufactures a finding. A census that did exactly that reported six dead
   targets and all six were artifacts. This module DECLINES to judge an
   unqualified pointer and says so out loud rather than passing it in silence.

3. A ``file:line`` POINTER INTO ``docs/LEDGER.md`` ROTS BY CONSTRUCTION. That
   file is append-only NEWEST FIRST, so prepending an entry shifts every line
   number below it. Asserting one would redden on correct history.

4. A CITATION CAN ASSERT AN ABSENCE. A correction record proving an earlier
   pointer is dead cites the dead name ON PURPOSE - its evidence is that
   ``grep -c`` returns 0. Reddening on it would punish the record for doing the
   right thing. That is the :data:`DELIBERATE` disposition, and the ledger
   already contains one such record.

5. A PATH CAN BE ELIDED, and recovering it by inheritance manufactures
   findings. The ledger writes one full citation and then ``::name`` for
   further tests in the same file. Resolving those against "the last full
   citation seen" MANUFACTURES findings on correct records, because a paragraph
   may interleave an unrelated full citation while the elisions after it still
   mean the earlier file. :data:`ELIDED_RE` reads
   the shape and asks the question that needs no path - does the tree bind this
   name - which is the same question the bare arm asks.

6. A LINE POINTER CAN BE THE SUBJECT OF A CORRECTION RATHER THAN A CITATION.
   QUOTING AND CITING ARE INDISTINGUISHABLE BY SHAPE - it is the same fault as
   trap 4 in the line-pointer arm, and it is the recorded reason
   ``docs/history_notes.md`` is exempt from this module entirely. A CS-889 note
   spells three pointers that were already dead when it was filed, precisely in
   order to say so. Reporting one would punish the record for doing the right
   thing, so the site carries a DELIBERATE disposition and stays silent.

WHAT THIS MODULE DOES NOT COVER, recorded rather than left to be discovered.
:data:`UNGUARDED_DOCS` is the whole of it, and it is a RECORD rather than a
silence: every in-domain markdown file carrying a citation is either guarded or
named there with its reason, checked in both directions, so the unguarded set
cannot grow or linger unnoticed. ``docs/history_notes.md`` is its ONE member,
because the deep archive's dead pointers sit inside the detail blocks OF these
very items, whose subject IS a pointer being dead, so quoting and citing cannot
be told apart by shape there. Guarding it later is a one-line change that this
contract then FORCES, by failing the record that has stopped being needed.

TWO THINGS THAT WENT WRONG ON THE FIRST BUILD OF THAT BOUNDARY, kept here
because both are the same mistake wearing different clothes - a rule that
reads narrower than what it governs.

A. CARRYING A CITATION WAS DECIDED BY THE PATH ARM ALONE. It asked
   :func:`citations_in`, which needs a ``path.py`` before the separator, so a
   doc carrying ONLY an elided ``::name`` - the very shape added to this module
   in the same change - was not a carrier at all. Neither was one carrying only
   a bare ``grep -c`` identifier or only a ``file:line`` pointer. Such a doc
   could never be reported, and, worse, a maintainer who CORRECTLY recorded one
   was told the record was stale and to delete it. :data:`JUDGED_SHAPES` is now
   the single answer to what this module judges, :func:`carries_a_citation`
   reads it, and a contract walks this module's own compiled patterns and fails
   on any that the boundary does not read - so the NEXT arm cannot fall out.

B. AN EXEMPTION SHIPPED THAT THIS MODULE'S OWN TABLE CONTRADICTED.
   ``WAKEUP_NOTES.md`` was recorded unguarded on the reason "every citation in
   it resolves today". One did not, and :data:`DISPOSITIONS` already recorded
   that same name as dead under the ledger key. The repair was not to rewrite
   the sentence - a record nothing verifies is the whole failure mode - but to
   GUARD the file, at a cost of one disposition. It is in :data:`GUARDED_DOCS`
   now, and so is ADR 0008, which the widened boundary surfaced the moment it
   could see a doc that names test modules and nothing else.

CS-889 CLOSES AS AN HONEST PARTIAL AND THE CLAUSE IS NOT MET AS A UNIVERSAL.
CS-882 is the precedent. What was actually bought, measured on the tree this
was written against rather than asserted about it:

- TEN live instances discharged. Six are RECORDED as dispositions, because
  their carriers state they may not be edited - five in ``docs/LEDGER.md``,
  which declares itself append-only in its own header, and one in a phase 4
  leaf where the obvious symbol conversion WOULD have resolved and would have
  resolved to a claim CS-440 has since made false. Four are REPAIRED to the
  symbol form by slices that own those files.
- THE CLASS IS CLOSED AGAINST NEW ADDITIONS in the scoped population. A line
  pointer at a tracked Python module written after this pin is reported on
  arrival, because it is in neither table.
- WHAT REMAINS UNVERIFIED, and it is the larger number: every member of
  :data:`UNVERIFIED_LINE_POINTERS` resolves in RANGE and has NOT been checked
  against the sentence that spells it, and every member of
  :data:`UNFORBIDDEN_LINE_POINTERS` is a pointer the forbid rule cannot reach
  at all because its target has no symbol form. Both are open residuals of
  CS-889. Neither table claims anything else, and calling either one an
  adjudication would be the laundering this module exists to prevent.

THE FORBID RULE IS THIS PROJECT'S OWN PRACTICE, NOT AN IMPORT. ``docs/LEDGER.md``
already says of two stale by-line citations that they are deliberately not
edited and that the correcting paragraph is the repair - and it ends that
correction with the rule in its own words: cite that module BY NAME, not by
line. The lesson was in the prose and absent from the guard.

AND ONE SENTENCE THAT WAS TRUE OF THE ARM AND FALSE OF THE TREE, recorded so
it is not repeated: "zero real violations in the guarded set". The sweep that
produced it examined only the NON-RESOLVING pointers. Every instance CS-889
discharged lives in the RESOLVING subset, which nothing had content-checked.
A guard's contract and the corpus it runs on are two different claims.

A DISPOSITION IS GRANTED PER SITE, NOT PER NAME. The table is keyed
``(doc, name)``, which forgives every spelling of that name in that doc
forever - including citations written long after the one that was adjudicated.
Three new ledger entries citing already-forgiven names were planted and the
module stayed green on all three. Each entry now records HOW MANY sites it
answers and a count that no longer matches is reported. A line number would
have been the obvious key and is the wrong one, for the same reason trap 3
declines to judge a ``file:line`` pointer into an append-only file.
"""

from __future__ import annotations

import ast
import re
import string
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from tests.save import test_oracle_citations as oracle_citations

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# Non-negotiable 4 is 7-bit ASCII, so the highest byte an authored file may
# carry is 0x7E - the tilde, the last printable character in the range.
HIGHEST_ASCII: Final = 0x7E

# The ledger is scoped to its entries. The two pairs above the heading are the
# preamble's ILLUSTRATIVE pointers - they show the shape of a valid citation and
# name no real test - so judging them would redden the documentation of the rule.
LEDGER: Final = "docs/LEDGER.md"
ENTRIES_HEADING: Final = "## Entries"

# ROADMAP.md and docs/GATED.md carry citations too and both measured clean, so
# they are guarded from the start rather than after they rot.
#
# ADR 0008 JOINED THE MOMENT THE BOUNDARY LEARNED TO READ EVERY ARM. It names
# three test MODULES and no test, so the path arm and the file:line arm find
# nothing in it and the bare arm's basename filter answers all three - measured
# zero on every arm, which is why guarding it was the cheap answer and
# recording it the expensive one. It was invisible to the boundary until
# JUDGED_SHAPES existed, which is exactly the silence CS-442 was opened on.
# WAKEUP_NOTES.md IS GUARDED BECAUSE ITS EXEMPTION WAS MEASURABLY FALSE. It
# was first RECORDED unguarded, on the stated reason "every citation in it
# resolves today". That reason was false on the record's own first run, and
# this module's DISPOSITIONS table already held the counter-evidence under the
# ledger key. Guarding it costs exactly one disposition and closes the gap
# permanently; repairing the sentence instead would have left a record that
# nothing verifies, which is the shape that ships false declarations.
ADR_0008: Final = "docs/adr/0008-detection-claims-are-derived-never-written.md"

#: The ADR recording the 2026-08-25 split of `docs/item_notes.md` into an index
#: over per-phase leaves. GUARDED on arrival rather than left to be noticed: it
#: cites the guard, the budget tool and this module by path, and an ADR is the
#: kind of doc that is written once and read for years, so a pointer that rots
#: in it rots unobserved.
ADR_0010: Final = "docs/adr/0010-item-notes-is-an-index-over-per-phase-leaves.md"

#: The ADR recording the 2026-08-29 split of that follow-up leaf again, at the
#: CS-850 seam. GUARDED FOR ADR 0010's REASON AND FOR ONE OF ITS OWN. Its whole
#: subject is that the ID-to-leaf mapping has exactly ONE code owner, and it
#: names that owner by path - an ADR that declined to name it, to stay below
#: this module's boundary, would be self-defeating and would have bought its
#: silence with the precision that makes it useful. Being guarded is the
#: feature here rather than the cost: the naming it argues for is exactly what
#: makes it a carrier, so the two decisions stand or fall together.
ADR_0011: Final = "docs/adr/0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md"

#: The CS-601 surface decisions: the 501/503 refusal split, `detail` looked up by
#: reason rather than built from content, the exact-rational wire form, and the
#: ruling that `/api/world` is BACKED. GUARDED rather than recorded unguarded,
#: because every pointer it makes is load-bearing for the decision it records -
#: it cites `docs/item_notes/phase4.md` for what phase 4 can and cannot do, and
#: the save layer for the size that makes a 501 there a false statement. An ADR
#: whose evidence has silently stopped resolving argues from nothing.
ADR_0012: Final = "docs/adr/0012-dashboard-refusal-vocabulary-and-wire-form.md"

#: The CS-602 decision to pin ONE certificate by byte identity and defer every
#: other host to Chromium. GUARDED rather than recorded unguarded, and the
#: reason is what the pointers carry: it cites the module that makes the
#: decision and the guard that grades the wiring, and six graders showed that
#: the wiring was the half nothing was checking. An ADR that argues a security
#: property from a test whose name has since moved argues from nothing.
ADR_0014: Final = "docs/adr/0014-the-shell-trusts-one-pinned-certificate.md"

#: The LIVE per-item detail file, created 2026-08-23 when the operator ruled the
#: NOTE bodies out of `ROADMAP.md`. IT IS GUARDED RATHER THAN RECORDED UNGUARDED,
#: and the reason is the move itself: every body in it came VERBATIM out of
#: `ROADMAP.md`, which is guarded. Recording it unguarded would have dropped that
#: coverage at the instant the text changed file, leaving citations that were
#: checked yesterday unchecked today with nothing red - which is the exact shape
#: this contract exists to make impossible.
ITEM_NOTES: Final = "docs/item_notes.md"


def _item_notes_leaves() -> tuple[str, ...]:
    """Return every leaf of the item-notes family, repo-relative and sorted.

    DERIVED, NOT LISTED, and the reason is this module's own founding finding
    one level up. A hand-typed tuple of leaf names would let a leaf added by a
    later relocate pass carry citations that nothing checks, silently, exactly
    as a doc that STARTS carrying citations used to join the unguarded set in
    silence. The set-boundary contract below would catch it - but catching it
    as a FAILURE the next session has to adjudicate is worse than never letting
    it happen.

    Returns:
        Each leaf's repo-relative path, sorted, empty if the family is absent.
    """
    leaves = REPO_ROOT / "docs" / "item_notes"
    if not leaves.is_dir():
        return ()
    return tuple(f"docs/item_notes/{path.name}" for path in sorted(leaves.glob("*.md")))


#: The leaves of the item-notes family. `docs/item_notes.md` was ONE file until
#: 2026-08-25, when it became an index over `docs/item_notes/` with one leaf per
#: phase; the bodies - and so every citation in them - moved into the leaves.
ITEM_NOTES_LEAVES: Final = _item_notes_leaves()

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

GUARDED_DOCS: Final = (
    LEDGER,
    "ROADMAP.md",
    "docs/GATED.md",
    "WAKEUP_NOTES.md",
    ADR_0008,
    ADR_0010,
    ADR_0011,
    ADR_0012,
    ADR_0014,
    ITEM_NOTES,
    *ITEM_NOTES_LEAVES,
    # A memory leaf that cites a test by name. Guarded rather than recorded,
    # because every pointer in it resolves today and a durable lesson whose
    # cited proof has been deleted is worse than no lesson.
    "memory/moving-an-assert-can-create-the-leak.md",
    "memory/a-guard-can-measure-spelling.md",
    "memory/a-guard-can-be-green-by-accident.md",
)

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
UNGUARDED_DOCS: Final[Mapping[str, str]] = {
    "docs/history_notes.md": (
        "the deep archive, and its dead citations sit inside the detail blocks OF the"
        " citation-guard items themselves - blocks whose SUBJECT is a pointer being dead -"
        " so quoting and citing are indistinguishable by shape and a guard would be red on"
        " correct history."
    ),
}

# A path segment may begin with a dot - `.github/workflows/tier1.yml:250` is a
# real citation, and a pattern anchored on an alphanumeric drops the dot and
# then reports a path that does not exist. Measured, on that exact pointer.
_PATH = r"\.?[A-Za-z0-9_][A-Za-z0-9_/.-]*"

CITATION_RE: Final = re.compile(rf"({_PATH}\.py)::([A-Za-z_][A-Za-z0-9_]*)")
LINE_POINTER_RE: Final = re.compile(
    rf"({_PATH}\.(?:py|md|json|toml|yml|yaml|cfg|txt|ini)):([0-9]+)"
)

# A bare test identifier, NOT preceded by "::" or "." - those forms are the
# other two arms' business. The length floor keeps ordinary words out.
BARE_RE: Final = re.compile(r"(?<![:.\w])(test_[a-z0-9_]{8,})\b")

# THE PATH-ELISION IDIOM: one full `path.py::name` citation, then `::name` for
# further tests in the SAME file. `docs/LEDGER.md` writes most of its bare
# identifiers that way, and both arms above are blind to it BY CONSTRUCTION -
# the path arm needs a `<path>.py` before the separator, and BARE_RE's
# lookbehind excludes a name preceded by ":" so a full citation's right half is
# not judged twice.
#
# THE PATH IS NOT RECOVERED, DELIBERATELY. Inheriting "the last full citation
# seen" was measured to MANUFACTURE findings on correct records, because the
# ledger interleaves an unrelated full citation mid-paragraph while the
# elisions that follow still mean the earlier file. So an elided pointer is
# judged the way a bare one is - does ANY module in the tree bind this name -
# which is the question that can be answered without guessing.
#
# The same length floor does the same work: the metasyntactic `path::name` and
# `path::test_name` placeholders that document the citation SHAPE are both
# below it, and judging those would redden the documentation of the rule.
ELIDED_RE: Final = re.compile(r"(?<![A-Za-z0-9_])::(test_[a-z0-9_]{8,})\b")

# EVERY SHAPE THIS MODULE JUDGES, IN ONE PLACE, because the boundary contract
# needs the same answer the arms use and once did not have it. It decided
# carrier-hood with the PATH pattern alone, so a doc carrying only an elided
# `::name`, only a bare `grep -c` identifier or only a `file:line` pointer was
# not a carrier at all - it could join the unguarded set in silence, and a
# maintainer who correctly recorded it was told the record was STALE.
#
# THE MEMBERSHIP IS ASSERTED AGAINST THE MODULE ITSELF rather than trusted:
# test_every_pattern_this_module_judges_by_also_decides_what_carries_a_citation
# walks this module's own compiled patterns and fails on any that is not here.
# That is what keeps a FUTURE arm from falling out of the boundary the way the
# elided arm did - the arm and the boundary cannot drift apart quietly.
JUDGED_SHAPES: Final = (CITATION_RE, LINE_POINTER_RE, BARE_RE, ELIDED_RE)


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
        The key, in the same spelling :data:`LINE_POINTER_RE` matches.
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
        sites: HOW MANY TIMES the doc spells this citation. Without it the key
            is ``(doc, name)`` and nothing else, so a forgiveness granted for
            one adjudicated site silently covers a brand-new dead citation of
            the same name at a NEW site in the same doc - which measured true:
            three new ledger entries citing already-forgiven names left the
            whole module green. A count is the cheapest key that closes it and
            the only one that does not churn, because line numbers move every
            time an entry is prepended to an append-only file.
    """

    kind: str
    target: str
    why: str
    sites: int


# EVERY ENTRY HERE IS CHECKED, IN THREE DIRECTIONS. A MOVED or RENAMED target
# that stops resolving fails; an entry whose citation no longer appears - or
# which now resolves on its own - ALSO fails; and an entry whose SITE COUNT no
# longer matches the doc fails too. That last one is the newest and the one an
# exemption table is normally missing: without it the key is a name, a name is
# forgiven forever, and the next dead citation that happens to spell the same
# name is forgiven on arrival. Every count below is MEASURED from the doc, not
# asserted about it.
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
        1,
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
        1,
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
        1,
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
        "tests/save/test_struct_interior.py"
        "::test_the_table_control_takes_its_window_from_the_body_not_the_degraded_record",
        "CS-829 cited it live; CS-862 renamed it to the one bit it grades. Not a record defect.",
        2,
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
        2,
    ),
    (
        LEDGER,
        "tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected",
    ): Disposition(
        RENAMED,
        "tests/data/test_registry.py"
        "::test_the_misspelled_game_keys_are_used_verbatim_not_autocorrected",
        "the word game was dropped; the cited name is in no commit in history.",
        2,
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
        2,
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
        2,
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
        1,
    ),
    # --- the bare-identifier arm, which sees what a path scanner cannot.
    (LEDGER, "test_the_header_scan_advertises_no_bound_it_cannot_enforce"): Disposition(
        RENAMED,
        "tests/test_precommit_gate.py"
        "::test_the_header_scan_time_bound_declares_the_scope_it_actually_has",
        "added by ee36d0d, the CS-436 commit, alongside the live sibling the same entry cites.",
        3,
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
        1,
    ),
    (LEDGER, "test_no_recorded_gap_is_blocked_by_a_frozen_file"): Disposition(
        DELIBERATE,
        "",
        "the CS-411 correction record cites this name to prove it is DEAD;"
        " grep -c returning 0 IS its evidence.",
        2,
    ),
    (LEDGER, "test_the_exclusion_is_discovery_only_not_containment"): Disposition(
        DELIBERATE,
        "",
        "the SECOND name in that same CS-411 correction, and the reason it needed"
        " an entry only now: it is spelled ONLY in the elided form, so until"
        " ELIDED_RE the guard had never seen it.",
        2,
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
    (LEDGER, line_key("tools/precommit_gate.py", 2311)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as emitting the PASS banner only on an empty"
        " report.diagnostics. The line is blank today and its neighbourhood now"
        " holds the label-redaction rule, so no live symbol may be assigned"
        " without inventing one.",
        1,
    ),
    (LEDGER, line_key("tests/test_precommit_gate.py", 1174)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as a SECOND label-shape assertion over"
        " LEAK_MARKER. The line is blank today and the block below it opens an"
        " unrelated CS-202-B section.",
        1,
    ),
    (LEDGER, line_key("scripts/verify_env.py", 358)): Disposition(
        NO_TARGET,
        "",
        "the entry reads that line as a bare str(exc) outside CS-202's stated"
        " shape. The line is blank today and the neighbourhood is the ports"
        " loader.",
        1,
    ),
    (LEDGER, line_key("tools/precommit_gate.py", 517)): Disposition(
        NO_TARGET,
        "",
        "the entry contrasts that line, as the gate widening what it refuses to"
        " commit, against the resolver's digit filter. The line is a lone"
        " closing bracket today, so it names no declaration to contrast with.",
        1,
    ),
    (LEDGER, line_key("scripts/make_cert.py", 222)): Disposition(
        MOVED,
        "scripts/make_cert.py::_restrict",
        "RIGHT WHEN WRITTEN and moved since: the entry says that line chmods the"
        " key 0600 inside _restrict, and the line now sits inside the openssl"
        " argv builder. _restrict is live and is the target the sentence means.",
        1,
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
        1,
    ),
    # THE TRAP THAT MANUFACTURES A FINDING ON CORRECT PROSE, and the reason
    # `docs/history_notes.md` is exempt from this module entirely: QUOTING AND
    # CITING ARE INDISTINGUISHABLE BY SHAPE. This site is the SUBJECT of a
    # correction - prose about a pointer having been wrong - not a citation
    # anything should follow. Reporting it would punish the record for doing
    # the right thing, which is exactly what DELIBERATE exists for.
    (ITEM_NOTES_850_LEAF, line_key("scripts/make_cert.py", 224)): Disposition(
        DELIBERATE,
        "",
        "QUOTED, NOT CITED: the CS-889 note spells it as the subject of a"
        " correction recording that the pointer was already dead when filed.",
        1,
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
UNVERIFIED_LINE_POINTERS: Final[frozenset[tuple[str, str, int]]] = frozenset(
    (
        ("ROADMAP.md", "tests/save/test_container_elements.py", 839),
        ("ROADMAP.md", "tests/save/test_inventory_potential.py", 316),
        ("ROADMAP.md", "tests/save/test_reference_resolution.py", 968),
        ("docs/LEDGER.md", "clockspeed/data/docs_extract.py", 443),
        ("docs/LEDGER.md", "clockspeed/data/locate.py", 187),
        ("docs/LEDGER.md", "clockspeed/data/locate.py", 657),
        ("docs/LEDGER.md", "clockspeed/data/version.py", 352),
        ("docs/LEDGER.md", "clockspeed/data/version.py", 815),
        ("docs/LEDGER.md", "clockspeed/save/objects.py", 2945),
        ("docs/LEDGER.md", "clockspeed/save/usmap.py", 46),
        ("docs/LEDGER.md", "scripts/install_hooks.py", 310),
        ("docs/LEDGER.md", "tests/data/test_phase2_gate.py", 775),
        ("docs/LEDGER.md", "tests/test_hook_interpreter_ladder.py", 1678),
        ("docs/LEDGER.md", "tools/drift_guard.py", 312),
        ("docs/LEDGER.md", "tools/edit_lint_check.py", 82),
        ("docs/LEDGER.md", "tools/edit_lint_check.py", 113),
        ("docs/LEDGER.md", "tools/facts_probe.py", 121),
        ("docs/LEDGER.md", "tools/precommit_gate.py", 570),
        ("docs/LEDGER.md", "tools/precommit_gate.py", 704),
        ("docs/LEDGER.md", "tools/precommit_gate.py", 1802),
        ("docs/item_notes/phase2.md", "clockspeed/data/registry.py", 84),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 39),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 141),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 187),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/header.py", 927),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/objects.py", 1747),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/workdir.py", 688),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/world.py", 989),
        ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/world.py", 1109),
        ("docs/item_notes/phase4-followups-850.md", "scripts/verify_env.py", 370),
        ("docs/item_notes/phase4-followups-850.md", "tests/conftest.py", 426),
        ("docs/item_notes/phase4-followups-850.md", "tests/save/test_container_elements.py", 839),
        ("docs/item_notes/phase4-followups-850.md", "tests/save/test_container_elements.py", 1168),
        ("docs/item_notes/phase4-followups-850.md", "tests/save/test_header.py", 1048),
        ("docs/item_notes/phase4-followups-850.md", "tests/save/test_inventory_potential.py", 316),
        ("docs/item_notes/phase4-followups-850.md", "tests/save/test_reference_resolution.py", 968),
        ("docs/item_notes/phase4-followups-850.md", "tests/save/test_value_anchoring.py", 1082),
        ("docs/item_notes/phase4-followups-850.md", "tests/test_exception_rendering.py", 75),
        ("docs/item_notes/phase4-followups-850.md", "tests/test_redaction_scope.py", 26),
        ("docs/item_notes/phase4-followups-850.md", "tools/drift_guard.py", 463),
        ("docs/item_notes/phase4-followups.md", "scripts/install_hooks.py", 44),
        ("docs/item_notes/phase4-followups.md", "tests/save/reach_guard.py", 1504),
        ("docs/item_notes/phase4-followups.md", "tests/save/test_absolute_claims.py", 192),
        ("docs/item_notes/phase4-followups.md", "tests/test_hook_interpreter_ladder.py", 122),
        ("docs/item_notes/phase4.md", "clockspeed/data/locate.py", 796),
        ("docs/item_notes/phase4.md", "clockspeed/save/objects.py", 588),
        ("docs/item_notes/phase4.md", "clockspeed/save/objects.py", 890),
        ("docs/item_notes/phase4.md", "clockspeed/save/objects.py", 2608),
        ("docs/item_notes/phase4.md", "clockspeed/save/workdir.py", 796),
        ("docs/item_notes/phase4.md", "tests/data/test_locate.py", 858),
        ("docs/item_notes/phase4.md", "tests/save/synthetic.py", 1079),
        ("docs/item_notes/phase4.md", "tests/save/test_byte_order_status.py", 878),
        ("docs/item_notes/phase4.md", "tests/save/test_objects.py", 776),
        ("docs/item_notes/phase4.md", "tests/save/test_phase4_gate.py", 2089),
    )
)

#: The pointers the forbid rule DOES NOT reach, pinned so the hole stays
#: countable. A ``.yml``, ``.md`` or ``.toml`` target has no symbol form, so
#: forbidding the line form there would leave no way to cite it at all - the
#: rule would be asking for something that does not exist. That is a STATED
#: PRICE rather than a convenient boundary: these pointers rot on an edit above
#: them exactly as the Python ones do, and nothing in this module checks their
#: content either.
#:
#: Pinned as sites for :data:`UNVERIFIED_LINE_POINTERS`' reason - a count alone
#: is satisfied by any set of the same size.
UNFORBIDDEN_LINE_POINTERS: Final[frozenset[tuple[str, str, int]]] = frozenset(
    (
        ("docs/LEDGER.md", ".github/workflows/tier1.yml", 130),
        ("docs/LEDGER.md", ".github/workflows/tier1.yml", 250),
        ("docs/LEDGER.md", "docs/ARCHITECTURE.md", 136),
        ("tests/test_docs_citations.py", ".github/workflows/tier1.yml", 250),
        ("tests/test_precommit_gate.py", "docs/ARCHITECTURE.md", 144),
    )
)


# --- resolution -------------------------------------------------------------


def module_scope_names(source: str) -> frozenset[str]:
    """Every name a module binds at module scope.

    A DELIBERATE SUPERSET of ``test_oracle_citations.module_scope_functions``,
    which is imported rather than re-implemented and supplies the function half.
    The widening is the difference between the two questions this repository
    asks. A pytest node id carrying one ``::`` can only address a module-level
    FUNCTION, so that module is right to stop there. A docs citation is prose
    and may name a class or a module-level constant - and
    ``clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES`` is a real
    one. Resolving functions alone reports it dead, which was measured here
    before this function existed.

    Args:
        source: The module's full text.

    Returns:
        Module-level function, class and assignment-target names.

    Raises:
        SyntaxError: If the source does not parse.
    """
    names = set(oracle_citations.module_scope_functions(source))
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return frozenset(names)


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


def citation_sites(text: str, cited: str) -> int:
    """How many times a doc SPELLS one citation, counted by the arm that judges it.

    The arms de-duplicate: one dead name is one finding however often it
    appears, which is right for reporting and wrong for forgiving. A
    disposition keyed on ``(doc, name)`` alone forgives every site of that name
    forever, including sites written long after the one that was adjudicated.
    Counting is what turns "this name is answered" into "these N spellings of
    it are answered".

    THE LINE-POINTER BRANCH WAS ADDED BY CS-889 AND IS NOT A CONVENIENCE. That
    item records dead ``file:line`` pointers inside the append-only ledger, so
    they have to be keyed here like any other forgiven citation. Without the
    branch a key built by :func:`line_key` falls through to the bare arm, whose
    pattern demands a ``test_`` prefix, so every such key counts ZERO sites and
    the whole table reports itself stale on the first run. That was measured
    before the branch was written, not reasoned about.

    Args:
        text: The scoped doc text - the same text the arm reads.
        cited: A full ``path.py::name`` key, a :func:`line_key` pointer key, or
            a bare identifier key.

    Returns:
        The number of occurrences, counted with the same pattern the owning arm
        judges by, so the count cannot disagree with what the arm sees.
    """
    if "::" in cited:
        path, _, name = cited.partition("::")
        return sum(1 for found in CITATION_RE.findall(text) if found == (path, name))
    pointer = LINE_POINTER_RE.fullmatch(cited)
    if pointer:
        want = (pointer.group(1), pointer.group(2))
        return sum(1 for found in LINE_POINTER_RE.findall(text) if found == want)
    return judged_bare_names(text).count(cited)


def disposition_site_problems(
    texts: Mapping[str, str],
    dispositions: Mapping[tuple[str, str], Disposition],
) -> list[str]:
    """Every recorded disposition whose site count no longer matches its doc.

    Args:
        texts: Guarded doc path to its scoped text.
        dispositions: The recorded answers.

    Returns:
        One line per entry whose recorded multiplicity has drifted. MORE sites
        than recorded is a NEW dead citation arriving under an old forgiveness;
        FEWER is a record that has outgrown what it answers. Both are the table
        drifting from the corpus, and the table is only worth what it is
        checked against.
    """
    problems: list[str] = []
    for (doc, cited), recorded in sorted(dispositions.items()):
        found = citation_sites(texts.get(doc, ""), cited)
        if found != recorded.sites:
            problems.append(
                f"{doc} :: {cited} - forgives {recorded.sites} site(s), the doc spells it {found}"
            )
    return problems


def citations_in(text: str) -> list[tuple[str, str]]:
    """Extract distinct ``(path, name)`` citations, in order of appearance."""
    out: list[tuple[str, str]] = []
    for path, name in CITATION_RE.findall(text):
        pair = (path, name)
        if pair not in out:
            out.append(pair)
    return out


def carries_a_citation(text: str) -> bool:
    """Whether a doc holds anything this module would judge, in ANY spelling.

    The boundary contract's question, and deliberately WIDER than
    :func:`citations_in`, which answers the path arm's narrower one. A doc
    carrying only ``::name``, only a bare ``grep -c`` identifier or only a
    ``file:line`` pointer carries a pointer that can rot, and a boundary that
    could not see it left the doc unable to be reported OR recorded.

    Args:
        text: The doc's full text. The whole text rather than the scoped part:
            a pointer in a preamble is still a pointer, and scoping decides
            what to ADJUDICATE, not what to notice.

    Returns:
        True if any pattern in :data:`JUDGED_SHAPES` matches.
    """
    return any(pattern.search(text) for pattern in JUDGED_SHAPES)


def unresolved_citations(
    doc: str,
    text: str,
    sources: Mapping[str, str],
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
) -> list[tuple[str, str, str]]:
    """Every citation in one doc that neither resolves nor carries a disposition.

    Args:
        doc: The repo-relative doc path, used to key :data:`DISPOSITIONS`.
        text: The doc's full text.
        sources: Repo-relative POSIX path to module text. Injected rather than
            read from disk, so a control can supply a corpus with no filesystem
            involved - the same reason the imported resolver takes one.
        dispositions: The recorded answers. Injected for the same reason, and
            because the target-verification branch below only fires when a
            recorded target STOPS resolving - which never happens on the live
            table, so it is a guard on a non-default path and would ship
            untested if a control could not reach it. A mutation battery caught
            exactly that.

    Returns:
        ``(path, name, reason)`` for each citation that is a defect.
    """
    table = DISPOSITIONS if dispositions is None else dispositions
    problems: list[tuple[str, str, str]] = []
    for path, name in citations_in(scoped_text(doc, text)):
        if resolves(path, name, sources):
            continue
        recorded = table.get((doc, f"{path}::{name}"))
        if recorded is None:
            problems.append((path, name, "dead and carries NO recorded disposition"))
            continue
        if recorded.kind in (MOVED, RENAMED):
            target_path, _, target_name = recorded.target.partition("::")
            if not resolves(target_path, target_name, sources):
                problems.append(
                    (path, name, f"its {recorded.kind} target {recorded.target} does not resolve")
                )
    return problems


def resolves(path: str, name: str, sources: Mapping[str, str]) -> bool:
    """Whether ``path`` exists in ``sources`` and binds ``name`` at module scope."""
    source = sources.get(path)
    if source is None:
        return False
    try:
        return name in module_scope_names(source)
    except SyntaxError:
        return False


# --- the file:line arm ------------------------------------------------------


def line_pointer_problems(
    text: str,
    line_counts: Mapping[str, int],
) -> tuple[list[str], list[str]]:
    """Judge every ``file:line`` pointer that can honestly be judged.

    Args:
        text: The scoped doc text.
        line_counts: Repo-relative POSIX path to that file's line count. A path
            absent from this mapping is not a tracked file.

    Returns:
        ``(problems, declined)``. A pointer is DECLINED rather than judged when
        it names the ledger itself, whose line numbers shift every time an entry
        is prepended, or when it is an unqualified bare basename carrying no
        directory - resolving one repo-relative and calling it missing is how a
        census manufactured six findings that were all artifacts.

        Only the pointer's RANGE is judged. Asserting what sits AT the line
        would redden on every edit above it, which is a guard nobody keeps.
    """
    problems: list[str] = []
    declined: list[str] = []
    seen: set[tuple[str, str]] = set()
    for path, lineno in LINE_POINTER_RE.findall(text):
        if (path, lineno) in seen:
            continue
        seen.add((path, lineno))
        if path == LEDGER:
            declined.append(f"{path}:{lineno} - the ledger's own line numbers rot by construction")
        elif "/" not in path:
            declined.append(
                f"{path}:{lineno} - unqualified basename, no directory to resolve against"
            )
        elif path not in line_counts:
            problems.append(f"{path}:{lineno} - names a path that is not a tracked file")
        elif int(lineno) > line_counts[path]:
            problems.append(f"{path}:{lineno} - beyond the end of a {line_counts[path]}-line file")
    return problems, declined


# --- CS-889: the file:line arm reads what the line SAYS, not just where it is -
#
# THE DEFECT THE RANGE ARM CANNOT SEE. `line_pointer_problems` above judges a
# pointer's RANGE and stops, by explicit design, for two sound reasons that
# CS-889 does not overturn: asserting what sits AT a line "would redden on
# every edit above it, which is a guard nobody keeps", and resolving a bare
# basename repo-relative once manufactured six phantom findings. Both refusals
# stand. The CONSEQUENCE of the first is what this section repairs - a pointer
# invalidated by an edit ABOVE it stays in range, so it stays green, and it
# names something that is no longer there.
#
# TWO LEGS, AND EACH IS USELESS WITHOUT THE OTHER. Measured, not reasoned
# about, and the measurement is why both ship.
#
# LEG 1, EMPTINESS. A pointer whose target line is blank, or is punctuation and
# nothing else, does not resolve to a declaration. Mechanically decidable, no
# semantic judgement, no per-edit churn, and it cannot manufacture a finding
# because nobody deliberately cites a blank line. It reddened on seven live
# sites at CS-889's baseline.
#
# LEG 2, FORBID-WITH-RECORD. A line pointer at a tracked Python module is
# forbidden outright, because `path.py::name` is a drop-in replacement that
# resolves through the symbol table and CANNOT be invalidated by an edit above
# it. This is not a new rule invented here - `docs/LEDGER.md` already states it
# as its own practice, of two stale by-line citations it declines to edit:
# "Cite that module BY NAME, not by line."
#
# LEG 1 ALONE IS REFUTED AND THE REFUTATION IS PINNED. It is GREEN on a pointer
# that lands on a real line of the wrong declaration - CS-889's primary target
# landed on a docstring roughly eighty lines above the class it claimed to
# name, and the line was neither blank nor punctuation.
#
# LEG 2 ALONE IS ALSO REFUTED, in the other direction: on its own it lets a
# KNOWN-WRONG pointer be recorded away with the same shrug as an unexamined
# one, which is laundering. So a site with an adjudicated defect carries a
# :class:`Disposition` stating that defect, and only the unexamined remainder
# is grandfathered into :data:`UNVERIFIED_LINE_POINTERS`.
#
# WHAT WAS PRICED AND REJECTED, recorded so it is not re-pitched cheaply. A
# content-anchored resolver pinning (carrier, path, line, enclosing symbol)
# would catch the wrong-declaration case exactly. Its pin would be DERIVED from
# today's tree, so it would bake in whatever symbol each pointer currently
# lands in and ship green on the very defects it was built for - a guard green
# by accident. Making it sound needs a human to state the intended symbol for
# every member of the forbidden class.


def lands_on_nothing(landing: str) -> bool:
    """Whether a target line carries no declaration at all.

    THE CHEAPEST HONEST QUESTION ABOUT CONTENT, and the reason leg 1 does not
    inherit the range arm's refusal to look. "What declaration is at this
    line" needs a human. "Is there anything here" does not, moves only when
    the target file changes, and has no false-positive story: a pointer is
    never deliberately aimed at a blank line or a lone bracket.

    Args:
        landing: The target line, as read from the file, indentation included.

    Returns:
        True when the line is empty, whitespace, or ASCII punctuation only.
    """
    body = landing.strip()
    return not body or all(character in string.punctuation for character in body)


def line_pointer_sites(
    carriers: Mapping[str, str],
    file_lines: Mapping[str, Sequence[str]],
) -> tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]]:
    """Split every judgeable ``file:line`` pointer into the two classes.

    THE DECLINES ARE THE RANGE ARM'S, REUSED RATHER THAN RESTATED. A pointer
    into the ledger itself, an unqualified basename, a path that is not
    tracked, or a line past the end of its file is dropped here for exactly the
    reasons :func:`line_pointer_problems` documents - and dropping them is also
    what excludes the synthetic Python fixtures that this module and its
    siblings plant, without a carve-out written for them. That was the stated
    requirement: reuse a test that already exists rather than invent an
    exemption that a later fixture can fall outside of.

    Args:
        carriers: Carrier path to the text its pointers are read from. WIDER
            than :data:`GUARDED_DOCS` on purpose - two of the pointers CS-889
            discharged sat in tracked Python modules rather than in a doc, so a
            population stopping at the docs would have declared them absent.
        file_lines: Repo-relative POSIX path to that file's lines. A path
            absent from this mapping is not a tracked file.

    Returns:
        ``(py_sites, other_sites)``, both ``(carrier, path, line, landing)``
        with the landing text included so the caller need not re-read the file.
        PY_SITES is every pointer at a tracked Python module - the class the
        forbid leg governs, because a symbol form exists there. OTHER_SITES is
        every pointer at a tracked non-Python file, which has no symbol form to
        be redirected to and so cannot be forbidden.

        THE SPLIT GOVERNS THE FORBID LEG ONLY. The emptiness leg reads both,
        because a pointer at a blank line names nothing whatever the target's
        extension is - and a split that also narrowed leg 1 would have bought a
        tidier boundary by making a whole class of dead pointer invisible,
        which is the trade this module exists to refuse.
    """
    py_sites: list[tuple[str, str, int, str]] = []
    other_sites: list[tuple[str, str, int, str]] = []
    for carrier in sorted(carriers):
        seen: set[tuple[str, int]] = set()
        for path, raw in LINE_POINTER_RE.findall(carriers[carrier]):
            line = int(raw)
            if (path, line) in seen or path == LEDGER or "/" not in path:
                continue
            seen.add((path, line))
            lines = file_lines.get(path)
            if lines is None or line > len(lines):
                continue
            found = py_sites if path.endswith(".py") else other_sites
            found.append((carrier, path, line, lines[line - 1]))
    return py_sites, other_sites


def line_pointer_content_problems(
    py_sites: Iterable[tuple[str, str, int, str]],
    other_sites: Iterable[tuple[str, str, int, str]],
    sources: Mapping[str, str],
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
    baseline: Iterable[tuple[str, str, int]] | None = None,
) -> tuple[list[str], list[str]]:
    """Judge every judgeable pointer along both legs.

    Args:
        py_sites: The Python-target half of :func:`line_pointer_sites`, which
            both legs read.
        other_sites: Its non-Python half, which only the emptiness leg reads.
        sources: Repo-relative path to module text, for verifying a recorded
            redirect. Injected for the reason :func:`unresolved_citations`
            gives: the verification branch only fires when a recorded target
            STOPS resolving, so a control has to be able to reach it.
        dispositions: The adjudicated answers, keyed by :func:`line_key`.
        baseline: The grandfathered sites, unexamined and recorded as such.

    Returns:
        ``(empty, forbidden)``. EMPTY is leg 1 - the pointer resolves to
        nothing at all. FORBIDDEN is leg 2 - the pointer resolves to SOMETHING
        and this module cannot say it is the right thing, so the line form is
        refused in favour of the symbol form. A recorded redirect whose target
        has itself stopped resolving is reported in the second list, because a
        record that points at nothing forgives nothing.

    THE TWO FORGIVENESSES ARE NOT INTERCHANGEABLE, and the ordering below is
    the whole difference. An ADJUDICATED disposition answers the pointer, so it
    silences both legs - somebody read it and recorded a verdict. The
    GRANDFATHERED baseline answers only leg 2, because it claims nothing about
    content and blankness is not a content claim. Forgiving leg 1 with it would
    let a pinned pointer go blank under a later edit and stay silent, which is
    the one failure this section is built to prevent - a pin that quietly
    absorbs the defect it was supposed to make countable.
    """
    table = DISPOSITIONS if dispositions is None else dispositions
    grandfathered = set(UNVERIFIED_LINE_POINTERS if baseline is None else baseline)
    empty: list[str] = []
    forbidden: list[str] = []
    for forbiddable, group in ((True, py_sites), (False, other_sites)):
        for carrier, path, line, landing in group:
            recorded = table.get((carrier, line_key(path, line)))
            if recorded is not None:
                if recorded.kind in (MOVED, RENAMED):
                    target_path, _, target_name = recorded.target.partition("::")
                    if not resolves(target_path, target_name, sources):
                        forbidden.append(
                            f"{carrier} -> {path} line {line} - its {recorded.kind} target"
                            f" {recorded.target} does not resolve"
                        )
                continue
            if lands_on_nothing(landing):
                empty.append(
                    f"{carrier} -> {path} line {line} - the target line is blank or"
                    " punctuation only, so the pointer names no declaration"
                )
            elif forbiddable and (carrier, path, line) not in grandfathered:
                forbidden.append(
                    f"{carrier} -> {path} line {line} - a line pointer at a tracked Python"
                    f" module, and it lands on {landing.strip()!r}. Cite the symbol form,"
                    " which an edit above it cannot invalidate."
                )
    return empty, forbidden


def stale_pin_problems(
    live: Iterable[tuple[str, str, int]],
    pinned: Iterable[tuple[str, str, int]],
) -> list[str]:
    """Every pinned site that the corpus no longer spells.

    THE DIRECTION A BASELINE IS NORMALLY NOT CHECKED IN, and this module has
    already paid once for skipping it: an exemption shipped on a reason its own
    table contradicted. A pin that outlives what it answered forgives nothing
    and hides the fact that the population moved.

    Args:
        live: The sites the corpus spells right now.
        pinned: The recorded sites.

    Returns:
        One line per pinned site that is no longer present.
    """
    present = set(live)
    return [
        f"{carrier} -> {path} line {line} - pinned, but the corpus no longer spells it"
        for carrier, path, line in sorted(set(pinned) - present)
    ]


# --- the bare-identifier arm ------------------------------------------------


def judged_bare_names(text: str) -> list[str]:
    """Every identifier the bare arm judges, in order of appearance.

    TWO SPELLINGS, ONE QUESTION. A name spent bare inside a ``grep -c`` and the
    same name spelled ``::name`` with its path elided are both asking whether
    the tree binds that identifier, and neither carries a path to check. They
    are collected here rather than at each call site because the two that need
    them - the arm that judges and the check that the disposition table has not
    gone stale - MUST agree on the population. A disposition recorded for a
    name only one of them can see is a forgiveness entry the other reports as
    unused, which is the failure the table is built to prevent.

    A FULL ``path.py::name`` CITATION IS BLANKED WHOLE, PATH AND ALL, and the
    path half is the half that needs it. The two lookbehinds already keep the
    NAME half out - both patterns refuse a name preceded by ``:`` - so blanking
    is not what stops a citation being judged twice; that credit belonged to
    the lookbehinds and was measured off this line. What the blanking stops is
    the citation's PATH being read as a bare identifier: in
    ``tests/synthetic/test_plantedxx.py::test_a_real_one`` the basename
    ``test_plantedxx`` clears the length floor and follows a ``/``, so without
    the blanking it reaches the arm and is reported dead whenever that module
    is not tracked - a manufactured finding, on a citation the path arm is
    already judging. ``test_the_whole_of_a_full_citation_is_blanked_not_just_the_name_half``
    is the observation; before it existed, deleting this line survived.

    Args:
        text: The scoped doc text.

    Returns:
        The matched identifiers, source order preserved, duplicates included.
    """
    stripped = CITATION_RE.sub(" ", text)
    found = [(match.start(), match.group(1)) for match in BARE_RE.finditer(stripped)]
    found += [(match.start(), match.group(1)) for match in ELIDED_RE.finditer(stripped)]
    return [name for _offset, name in sorted(found)]


def bare_name_problems(
    doc: str,
    text: str,
    known_names: Iterable[str],
    module_basenames: Iterable[str],
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
) -> list[tuple[str, str]]:
    """Judge ``test_*`` identifiers carrying no path, in either spelling.

    This is the shape the item calls the most important one to cover: the
    mandatory Verification field spends them inside ``grep -c <name>``, with no
    path attached, and a ``path::name`` scanner is structurally blind to them.
    One dead citation in the ledger is visible ONLY here.

    :func:`judged_bare_names` supplies the population, so the ELIDED ``::name``
    spelling is judged by the same rule as the bare one and a disposition keyed
    on the name covers both sites of a name spent in both forms.

    Args:
        doc: The repo-relative doc path, used to key :data:`DISPOSITIONS`.
        text: The scoped doc text.
        known_names: Every name bound at module scope anywhere in the tree.
        module_basenames: Tracked module basenames without the extension. A
            bare ``test_properties`` is a MODULE, not a test, and reporting it
            would be noise - the imported resolver's own docstring names that
            ambiguity as the reason it reads a local citation permissively.
        dispositions: The recorded answers, injected for the same reason as
            in :func:`unresolved_citations` - the redirect-verification
            branch is a guard on a non-default path and a control has to be
            able to reach it.

    Returns:
        ``(name, reason)`` for each bare identifier that is a defect.
    """
    table = DISPOSITIONS if dispositions is None else dispositions
    known = set(known_names)
    modules = set(module_basenames)
    problems: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name in judged_bare_names(text):
        if name in seen or name in known or name in modules:
            continue
        seen.add(name)
        recorded = table.get((doc, name))
        if recorded is None:
            problems.append((name, "bound nowhere in the tree and carries NO recorded disposition"))
        elif recorded.kind in (MOVED, RENAMED):
            _target_path, _, target_name = recorded.target.partition("::")
            if target_name not in known:
                problems.append(
                    (name, f"its {recorded.kind} target {recorded.target} does not resolve")
                )
    return problems


# --- the boundary of the guarded set ----------------------------------------


def guarded_set_problems(
    docs: Mapping[str, str],
    guarded: Iterable[str],
    recorded: Mapping[str, str],
) -> tuple[list[str], list[str]]:
    """Judge which docs are guarded at all, rather than what a guarded doc says.

    Every other contract in this module asks whether a citation resolves. This
    one asks the question one level up - whether the file carrying it is looked
    at by anything - because that is the question whose wrong answer opened
    CS-442 in the first place.

    A doc counts as CARRYING a citation when :func:`carries_a_citation` says
    so - that is, when it holds ANY shape this module judges, in any of the
    four spellings, judged on the whole text rather than the scoped part: a
    pointer in a preamble is still a pointer, and the scoping exists to decide
    what to ADJUDICATE, not what to notice.

    ASKING THE PATH PATTERN ALONE WAS THE ORIGINAL DEFECT. It made a doc
    carrying only an elided ``::name`` invisible in BOTH directions - never
    reported as unguarded, and, worse, a correct record for it reported as
    stale. The boundary now reads exactly what the arms read.

    Args:
        docs: In-domain repo-relative markdown path to full text. Injected, so
            a control can pose the question against a corpus with no
            filesystem involved.
        guarded: The docs the other contracts adjudicate.
        recorded: Repo-relative path to the one-line reason it is deliberately
            NOT guarded.

    Returns:
        ``(unrecorded, stale)``. UNRECORDED is a doc carrying citations that is
        neither guarded nor recorded - the set growing in silence. STALE is a
        record that has stopped being needed, which is the direction an
        exemption table normally is not checked in and the direction that lets
        a false declaration ship.
    """
    guarded_set = set(guarded)
    carriers = {doc for doc, text in docs.items() if carries_a_citation(text)}

    unrecorded = sorted(doc for doc in carriers if doc not in guarded_set and doc not in recorded)

    stale: list[str] = []
    for doc in sorted(recorded):
        if doc in guarded_set:
            stale.append(f"{doc} - now guarded, so the record forgives nothing")
        elif doc not in docs:
            stale.append(f"{doc} - not an in-domain tracked markdown file")
        elif doc not in carriers:
            stale.append(f"{doc} - carries no citation, so there is nothing to leave unguarded")
    return unrecorded, stale


# --- the live corpus --------------------------------------------------------


def tracked_files() -> list[str]:
    """Every path in this checkout's index, POSIX-separated."""
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
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
def line_pointer_carriers(tracked: list[str]) -> dict[str, str]:
    """Every text a ``file:line`` pointer is read out of, keyed by carrier.

    THE GUARDED DOCS PLUS TRACKED PYTHON MODULES, and the second half is not a
    widening for its own sake. CS-889's measured population held two pointers
    that sat in Python source rather than in a doc - one in a probe's comment
    and one in a test's - and a population that stopped at ``docs/`` would have
    reported them absent rather than judged them.

    The docs are SCOPED and the modules are not: scoping exists to keep the
    ledger's illustrative preamble out of adjudication, and a module has no
    such preamble.
    """
    carriers = {doc: scoped_text(doc, doc_text(doc)) for doc in GUARDED_DOCS}
    for path in tracked:
        if path.endswith(".py"):
            carriers[path] = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
    return carriers


@pytest.fixture(scope="module")
def live_line_pointers(
    line_pointer_carriers: Mapping[str, str], file_lines: Mapping[str, Sequence[str]]
) -> tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]]:
    return line_pointer_sites(line_pointer_carriers, file_lines)


@pytest.fixture(scope="module")
def known_names(sources: Mapping[str, str]) -> frozenset[str]:
    names: set[str] = set()
    for source in sources.values():
        try:
            names |= module_scope_names(source)
        except SyntaxError:
            continue
    return frozenset(names)


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

    Args:
        path: A repo-relative POSIX path.

    Returns:
        True for tracked markdown outside :data:`OUT_OF_DOMAIN`.
    """
    return path.endswith(".md") and not path.startswith(OUT_OF_DOMAIN)


@pytest.fixture(scope="module")
def markdown_texts(tracked: list[str]) -> dict[str, str]:
    return {path: doc_text(path) for path in tracked if in_domain(path)}


def doc_text(doc: str) -> str:
    return (REPO_ROOT / doc).read_text(encoding="ascii", errors="replace")


# --- contract 1: every citation resolves or carries a checked disposition ----


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_every_path_name_citation_in_a_guarded_doc_resolves(
    doc: str, sources: Mapping[str, str]
) -> None:
    problems = unresolved_citations(doc, doc_text(doc), sources)

    assert not problems, (
        "dead citations in "
        + doc
        + ":\n"
        + "\n".join(f"  {path}::{name} - {why}" for path, name, why in problems)
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_every_file_line_pointer_in_a_guarded_doc_is_in_range(
    doc: str, line_counts: Mapping[str, int]
) -> None:
    problems, _declined = line_pointer_problems(scoped_text(doc, doc_text(doc)), line_counts)

    assert not problems, (
        "broken file:line pointers in "
        + doc
        + ":\n"
        + "\n".join(f"  {problem}" for problem in problems)
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_every_bare_identifier_in_a_guarded_doc_resolves(
    doc: str, known_names: frozenset[str], module_basenames: frozenset[str]
) -> None:
    problems = bare_name_problems(
        doc, scoped_text(doc, doc_text(doc)), known_names, module_basenames
    )

    assert not problems, (
        "dead bare identifiers in "
        + doc
        + ":\n"
        + "\n".join(f"  {name} - {why}" for name, why in problems)
    )


# A name of the elided shape that this tree binds nowhere. Spelled `::name`
# on purpose: it is the shape the arm was widened to read, so a plant in this
# spelling proves BOTH that the arm reaches the doc and that the widening is
# what carries it there.
_PLANTED_DEAD_NAME: Final = "test_a_planted_name_this_tree_binds_nowhere"
_PLANTED_DEAD_LINE: Final = f"\n\nVerification: `::{_PLANTED_DEAD_NAME}`.\n"


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_the_bare_arm_has_teeth_on_every_guarded_doc(
    doc: str, known_names: frozenset[str], module_basenames: frozenset[str]
) -> None:
    """Every guarded doc is REACHED, measured per doc rather than assumed.

    The arm above passes on all of them today, and a passing arm proves nothing
    about coverage - it reads the same on a doc that is clean and on a doc
    nobody asked about. This module shipped with exactly that hole: the arm was
    hardcoded to the ledger while its two siblings were parametrized, so a dead
    ``::name`` in ROADMAP.md or docs/GATED.md left the whole module green.

    The plant is in memory. Nothing is written to a tracked doc.
    """
    planted = scoped_text(doc, doc_text(doc)) + _PLANTED_DEAD_LINE

    problems = bare_name_problems(doc, planted, known_names, module_basenames)

    assert [name for name, _why in problems] == [_PLANTED_DEAD_NAME], (
        f"a dead elided pointer planted in {doc} was not the single finding, so "
        "the arm does not reach this doc or the doc already carries another"
    )


def test_every_markdown_file_carrying_a_citation_is_guarded_or_recorded_unguarded(
    markdown_texts: Mapping[str, str],
) -> None:
    """CS-809's acceptance, in the direction that keeps the exclusion BOUNDED.

    Leaving a file out of the guarded set is a legitimate answer. Leaving it
    out SILENTLY is not, and until this contract existed there was no
    difference between the two.
    """
    unrecorded, _stale = guarded_set_problems(markdown_texts, GUARDED_DOCS, UNGUARDED_DOCS)

    assert not unrecorded, (
        "markdown carrying citations that nothing guards and nothing records:\n"
        + "\n".join(f"  {doc}" for doc in unrecorded)
        + "\nGuard it, or record it in UNGUARDED_DOCS with the reason."
    )


def test_every_recorded_unguarded_doc_still_needs_its_record(
    markdown_texts: Mapping[str, str],
) -> None:
    """The other direction, for the same reason :data:`DISPOSITIONS` has one."""
    _unrecorded, stale = guarded_set_problems(markdown_texts, GUARDED_DOCS, UNGUARDED_DOCS)

    assert not stale, "stale entries in UNGUARDED_DOCS:\n" + "\n".join(
        f"  {problem}" for problem in stale
    )


def test_every_unguarded_record_states_a_reason_and_none_is_also_guarded() -> None:
    """The record's own shape, so an entry cannot be a bare path with no case."""
    for doc, why in UNGUARDED_DOCS.items():
        assert why.strip(), f"{doc} is recorded as unguarded and states no reason"
        assert doc not in GUARDED_DOCS, f"{doc} is recorded as unguarded AND listed as guarded"


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
    assert set(UNGUARDED_DOCS) == {"docs/history_notes.md"}, (
        "the recorded-unguarded set is no longer the deep archive alone:\n"
        + "\n".join(f"  {doc}" for doc in sorted(UNGUARDED_DOCS))
        + "\nGuard the newcomer, or change this contract deliberately and say why."
    )


# --- contract 2: the disposition table cannot accumulate false declarations --


def test_every_recorded_disposition_is_still_in_use(sources: Mapping[str, str]) -> None:
    """An entry that stopped being needed is a false declaration waiting to happen.

    Checked in the direction an exemption table normally is NOT. A citation that
    was repaired, or a doc that stopped carrying it, leaves an entry here that
    forgives something no longer present - and the next citation that happens to
    match it is forgiven silently. This repository has an open item about
    exactly that shape, so the table is built with the check from the start.
    """
    texts = {doc: scoped_text(doc, doc_text(doc)) for doc in GUARDED_DOCS}
    unused = []
    for doc, cited in DISPOSITIONS:
        still_cited = citation_sites(texts.get(doc, ""), cited) > 0
        if "::" in cited:
            path, _, name = cited.partition("::")
            if still_cited and resolves(path, name, sources):
                unused.append((doc, cited, "now resolves on its own"))
                continue
        if not still_cited:
            unused.append((doc, cited, f"no longer cited in {doc}"))

    assert not unused, "stale entries in DISPOSITIONS:\n" + "\n".join(
        f"  {doc} :: {cited} - {why}" for doc, cited, why in unused
    )


def test_every_recorded_disposition_covers_exactly_the_sites_it_records() -> None:
    """A forgiveness is granted per SITE, not per name, and the count says how many.

    The table's keys are ``(doc, name)``, so without this a single adjudicated
    dead citation buys silence for every later citation of the same name in the
    same doc. That is not hypothetical: three new ledger entries, each citing a
    name this table already forgives, were planted and the module stayed green
    on all three. A dead pointer written today is a defect whatever was
    adjudicated about the same name a year ago.

    A LINE NUMBER WOULD HAVE BEEN THE OBVIOUS KEY AND IS THE WRONG ONE. The
    ledger is append-only newest-first, so prepending one entry moves every
    site below it - the same rot that makes trap 3 decline to judge a
    ``file:line`` pointer into that file. A count moves only when the prose
    that spells the citation moves.
    """
    texts = {doc: scoped_text(doc, doc_text(doc)) for doc in GUARDED_DOCS}

    problems = disposition_site_problems(texts, DISPOSITIONS)

    assert not problems, (
        "DISPOSITIONS no longer matches the docs it forgives:\n"
        + "\n".join(f"  {problem}" for problem in problems)
        + "\nA site that appeared since the record was written is a NEW citation."
        " Adjudicate it, then update the count."
    )


def test_a_second_site_for_a_forgiven_citation_is_reported() -> None:
    """The control, in both spellings, so the count is not a decorative field."""
    bare = ("ROADMAP.md", "test_a_name_that_is_not_bound")
    full = ("ROADMAP.md", "tests/synthetic/test_planted.py::test_a_name_that_is_not_there")
    one_of_each = {
        bare: Disposition(DELIBERATE, "", "cited to prove it is dead", 1),
        full: Disposition(NO_TARGET, "", "no test bears this meaning", 1),
    }
    once = {
        "ROADMAP.md": 'grep -c "test_a_name_that_is_not_bound" x\n'
        "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n"
    }
    twice = {"ROADMAP.md": once["ROADMAP.md"] * 2}

    assert disposition_site_problems(once, one_of_each) == [], (
        "the recorded count did not match a doc spelling each citation once, so "
        "the report below proves nothing about a SECOND site"
    )
    reported = disposition_site_problems(twice, one_of_each)
    assert [line.rpartition(" - ")[2] for line in reported] == [
        "forgives 1 site(s), the doc spells it 2",
        "forgives 1 site(s), the doc spells it 2",
    ], f"a second site went unreported in one spelling: {reported}"


def test_a_disposition_for_a_citation_that_has_vanished_is_reported() -> None:
    """The other direction: a record that outlived what it answered."""
    key = ("ROADMAP.md", "test_a_name_that_is_not_bound")
    table = {key: Disposition(DELIBERATE, "", "cited to prove it is dead", 1)}

    problems = disposition_site_problems({"ROADMAP.md": "no pointer here at all\n"}, table)

    assert len(problems) == 1, "a record forgiving a citation nothing spells was accepted"
    assert "the doc spells it 0" in problems[0]


def test_every_correctable_disposition_names_a_target_and_the_others_do_not() -> None:
    """The table's own shape, so a MOVED entry cannot silently carry no target."""
    for (doc, cited), recorded in DISPOSITIONS.items():
        assert recorded.kind in (MOVED, RENAMED, NO_TARGET, DELIBERATE), (
            f"{doc}::{cited} carries an unknown disposition {recorded.kind!r}"
        )
        if recorded.kind in (MOVED, RENAMED):
            assert "::" in recorded.target, (
                f"{doc}::{cited} is {recorded.kind} and names no path::name target"
            )
        else:
            assert recorded.target == "", (
                f"{doc}::{cited} is {recorded.kind} and must name no target"
            )
        assert recorded.why.strip(), f"{doc}::{cited} records no evidence"
        assert recorded.sites >= 1, (
            f"{doc}::{cited} forgives {recorded.sites} sites, so it answers nothing"
            " that is written - delete it, or record the count it covers"
        )


# --- contract 3: the controls. A guard that cannot fail is not a guard. ------

_LIVE_SOURCE: Final = "def test_a_real_one() -> None:\n    pass\n"
_CORPUS: Final = {"tests/synthetic/test_planted.py": _LIVE_SOURCE}


def test_the_checker_fires_on_a_planted_dead_pointer() -> None:
    """THE CONTROL THE ACCEPTANCE ASKS FOR, on a synthetic corpus."""
    text = "Verification: `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`.\n"

    problems = unresolved_citations("ROADMAP.md", text, _CORPUS)

    assert [(p, n) for p, n, _ in problems] == [
        ("tests/synthetic/test_planted.py", "test_a_name_that_is_not_there")
    ], "a planted dead pointer was not reported"


def test_the_checker_passes_the_same_pointer_once_it_resolves() -> None:
    """The other side of the branch, so the control above is not vacuous."""
    text = "Verification: `tests/synthetic/test_planted.py::test_a_real_one`.\n"

    assert unresolved_citations("ROADMAP.md", text, _CORPUS) == []


def test_a_citation_naming_a_module_that_does_not_exist_is_reported() -> None:
    text = "Verification: `tests/synthetic/test_absent.py::test_a_real_one`.\n"

    problems = unresolved_citations("ROADMAP.md", text, _CORPUS)

    assert len(problems) == 1, "a citation into a missing module was not reported"


def test_a_citation_naming_a_module_level_constant_resolves() -> None:
    """The widening in :func:`module_scope_names`, pinned.

    Resolving functions alone reported a real constant dead. That artifact is
    what this test exists to keep from coming back.
    """
    corpus = {"clockspeed/synthetic/mod.py": "_A_CONSTANT: int = 3\n\n\nclass Thing:\n    pass\n"}

    assert (
        unresolved_citations(
            "ROADMAP.md", "see `clockspeed/synthetic/mod.py::_A_CONSTANT`\n", corpus
        )
        == []
    )
    assert (
        unresolved_citations("ROADMAP.md", "see `clockspeed/synthetic/mod.py::Thing`\n", corpus)
        == []
    )


def test_a_leading_dot_in_a_cited_path_survives_the_pattern() -> None:
    """`.github/workflows/tier1.yml:250` is real, and a dot-blind pattern drops it."""
    problems, declined = line_pointer_problems(
        "CI runs it (`.github/workflows/tier1.yml:250`).\n",
        {".github/workflows/tier1.yml": 259},
    )

    assert problems == [], "a valid dotted path was reported as broken"
    assert declined == [], "a valid dotted path was declined instead of judged"


def test_a_line_pointer_beyond_the_end_of_a_file_is_reported() -> None:
    problems, _declined = line_pointer_problems(
        "see `tools/thing.py:900`\n", {"tools/thing.py": 12}
    )

    assert len(problems) == 1, "a pointer past the end of the file was not reported"


def test_an_unqualified_basename_is_declined_rather_than_called_dead() -> None:
    """TRAP 2. A census that judged these reported six findings, all artifacts."""
    problems, declined = line_pointer_problems("see `registry.py:206`\n", {})

    assert problems == [], "an unqualified basename was judged as a defect"
    assert len(declined) == 1, "an unqualified basename was passed in silence"


def test_a_pointer_into_the_ledger_itself_is_declined() -> None:
    """TRAP 3. Prepending one entry shifts every line number below it."""
    problems, declined = line_pointer_problems(f"see `{LEDGER}:128`\n", {LEDGER: 10})

    assert problems == [], "a ledger self-pointer was judged, and it rots by construction"
    assert len(declined) == 1, "a ledger self-pointer was passed in silence"


def test_the_bare_arm_reports_a_dead_name_the_path_arm_cannot_see() -> None:
    """The whole reason the bare arm exists, on a synthetic ledger fragment."""
    text = 'Verification: `grep -c "test_a_name_that_is_not_bound" tests/x.py` returns 1.\n'

    assert unresolved_citations("ROADMAP.md", text, _CORPUS) == [], (
        "the path arm should be blind to a bare identifier - if it is not, this "
        "control no longer proves the bare arm is load-bearing"
    )
    assert bare_name_problems("ROADMAP.md", text, [], []) == [
        (
            "test_a_name_that_is_not_bound",
            "bound nowhere in the tree and carries NO recorded disposition",
        )
    ]


def test_the_bare_arm_does_not_report_a_module_basename() -> None:
    text = "gated by `test_properties` and the retention controls\n"

    assert bare_name_problems("ROADMAP.md", text, [], ["test_properties"]) == []


def test_the_bare_arm_does_not_re_judge_the_name_half_of_a_full_citation() -> None:
    """Otherwise one dead citation is reported twice under two different rules."""
    text = "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n"

    assert bare_name_problems("ROADMAP.md", text, [], []) == []


def test_the_whole_of_a_full_citation_is_blanked_not_just_the_name_half() -> None:
    """The line above this one survived deletion, and it is NOT equivalent.

    The sibling test cannot see the difference, and the reason is a coincidence
    of its fixture rather than a property of the rule: ``test_planted`` is seven
    characters past the prefix and the length floor demands eight, so that path's
    basename never reaches the arm whether it is blanked or not. One character
    more and it does. The two lookbehinds cover the NAME half; only the blanking
    covers the PATH half, and a path whose module is not tracked is then reported
    as a dead bare identifier - a finding manufactured out of a citation the path
    arm is already judging.
    """
    text = "see `tests/synthetic/test_plantedxx.py::test_a_real_one`\n"

    assert judged_bare_names(text) == [], (
        "a full citation's PATH reached the bare arm; the basename "
        "test_plantedxx clears the length floor, so only blanking the whole "
        "citation keeps it out"
    )
    assert bare_name_problems("ROADMAP.md", text, [], []) == [], (
        "the path half of a full citation was reported as a dead bare name"
    )


def test_the_elided_arm_reports_a_dead_name_with_no_path_in_front_of_it() -> None:
    """CS-810's acceptance, on a synthetic corpus.

    A citation spelled `::name` fell between BOTH arms by construction: the
    path arm needs a ``<path>.py`` before the separator and matches nothing,
    and the bare arm's lookbehind excludes a name preceded by ``:`` precisely
    so it does not re-judge the right half of a full citation under a second
    rule. The elided spelling is what remains when a paragraph writes one full
    citation and then names further tests in the SAME file.
    """
    text = (
        "Verification: `tests/synthetic/test_planted.py::test_a_real_one`,\n"
        "`::test_a_name_that_is_not_bound`.\n"
    )

    assert unresolved_citations("ROADMAP.md", text, _CORPUS) == [], (
        "the path arm should stay blind to an elided pointer - if it is not, this "
        "control no longer proves the elided arm is load-bearing"
    )
    assert bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], []) == [
        (
            "test_a_name_that_is_not_bound",
            "bound nowhere in the tree and carries NO recorded disposition",
        )
    ]


def test_the_elided_arm_passes_the_idiom_it_was_widened_to_read() -> None:
    """The idiom is CORRECT prose, and the common case by a wide margin.

    Most elided pointers in the ledger name a live test. If the widening were
    red on those it would be red on correct history, which is the failure that
    gets a guard switched off rather than fixed.
    """
    text = (
        "Verification: `tests/synthetic/test_planted.py::test_a_real_one`,\n"
        "`::test_a_second_real_one`.\n"
    )

    assert judged_bare_names(text) == ["test_a_second_real_one"], (
        "the elided pointer must REACH the arm, or the next line passes vacuously"
    )
    assert (
        bare_name_problems("ROADMAP.md", text, ["test_a_real_one", "test_a_second_real_one"], [])
        == []
    )


def test_the_elided_arm_declines_the_metasyntactic_placeholder() -> None:
    """`path::name` and `path::test_name` DOCUMENT the shape; they cite nothing.

    Both are live in the guarded docs today, describing the citation rule
    itself, and judging them would redden the documentation of the rule. Two
    independent guards keep them out and both are pinned here: the placeholders
    as actually spelled carry a word character before the separator, and
    `test_name` is below the length floor even when nothing precedes it.
    """
    as_spelled = "a citation is written `path::name`, or `path::test_name` in the older notes\n"
    floor_only = "the shape is `::test_name` once the path is elided\n"

    assert judged_bare_names(as_spelled) == []
    assert judged_bare_names(floor_only) == [], "the length floor did not hold on its own"
    assert bare_name_problems("ROADMAP.md", as_spelled, [], []) == []


def test_the_dot_py_spelling_of_the_placeholder_is_a_citation_no_floor_protects() -> None:
    """Written with a `.py`, the placeholder stops being one. Measured, not feared.

    ``path::name`` and ``path::test_name`` are declined twice over - no ``.py``
    before the separator, so the path arm never sees them, and below the length
    floor, so the elided arm does not either. Spell the SAME placeholder
    ``path.py::name`` and both guards are gone at once: it is a well-formed
    citation naming a module this tree does not have, and it is judged like any
    other.

    THIS PIN IS WRITTEN FROM AN INCIDENT, not from caution. A paragraph
    documenting the citation rule spelled it that way in ``docs/history_notes.md``
    and raised that archive's dead-citation count by one - inside the very
    change whose subject was that archive's dead citations. The placeholders
    above are pinned because a floor protects them; this one is pinned because
    nothing does.
    """
    text = "a citation is written `path.py::name`\n"

    assert citations_in(text) == [("path.py", "name")], (
        "the .py spelling did not reach the path arm, so this pin would not "
        "catch the same prose in a guarded doc either"
    )
    judged = unresolved_citations("ROADMAP.md", text, _CORPUS)
    assert [(path, name) for path, name, _why in judged] == [("path.py", "name")], (
        "the .py spelling of the placeholder was forgiven by a floor that does not cover it"
    )
    assert judged_bare_names(text) == [], "the placeholder also reached the bare arm"


def test_a_module_qualified_pointer_is_not_read_as_an_elided_one() -> None:
    """TRAP 2 again, one spelling along: an unqualified citation is not a dead one.

    `test_phase4_gate::test_the_save_suite_passes_with_no_install_and_no_save`
    is real prose in this repo. Its path is ABBREVIATED, not elided - the
    module is right there - so it is the path arm's business and that arm
    declines it for want of a `.py`. Reading it as elided would judge a pointer
    whose module was stated, which is how a census manufactured six findings.

    The module half DOES reach the bare arm, as it always has, and the
    basename filter is what answers it. Only the name half is at issue here.
    """
    text = "gated by `test_phase4_gate::test_a_name_that_is_not_bound`\n"

    assert "test_a_name_that_is_not_bound" not in judged_bare_names(text)
    assert bare_name_problems("ROADMAP.md", text, [], ["test_phase4_gate"]) == []


def test_a_name_spelled_both_bare_and_elided_is_reported_once() -> None:
    """Both spellings feed one arm, so one dead name is still one finding."""
    text = (
        'Verification: `grep -c "test_a_name_that_is_not_bound" x.py` returns 0,\n'
        "and `::test_a_name_that_is_not_bound` names the same thing.\n"
    )

    assert judged_bare_names(text) == [
        "test_a_name_that_is_not_bound",
        "test_a_name_that_is_not_bound",
    ], "both spellings must reach the arm, or the de-duplication below proves nothing"
    assert len(bare_name_problems("ROADMAP.md", text, [], [])) == 1


def test_a_disposition_keyed_on_the_bare_name_also_forgives_the_elided_site() -> None:
    """The seam that let the widening land without re-judging a settled record.

    A correction record proving a name DEAD spends it bare inside a `grep -c`
    AND elided in the entry it corrects. One key covers both, so widening the
    arm did not redden a record doing exactly the right thing - which is the
    DELIBERATE disposition's whole purpose.
    """
    text = (
        'Verification: `grep -c "test_a_name_that_is_not_bound" x.py` returns 0.\n'
        "The entry below spends `::test_a_name_that_is_not_bound`.\n"
    )
    key = ("ROADMAP.md", "test_a_name_that_is_not_bound")
    table = {key: Disposition(DELIBERATE, "", "cited to prove it is dead", 2)}

    assert bare_name_problems("ROADMAP.md", text, [], [], table) == []
    assert len(bare_name_problems("ROADMAP.md", text, [], [], {})) == 1, (
        "without the disposition this text MUST be a finding, or the line above "
        "proves nothing about the disposition"
    )


def test_an_elided_only_name_is_visible_to_the_stale_disposition_check() -> None:
    """The two callers of :func:`judged_bare_names` must agree on the population.

    A disposition recorded for a name spelled ONLY in the elided form is a
    forgiveness entry that the stale-entry check would report as unused if it
    still read the narrow pattern - the table would then fail in one direction
    for an entry the other direction requires. Both read the same function, and
    this is what makes that non-optional.
    """
    text = "the entry cites `tests/x.py::test_a_real_one`, `::test_an_elided_only_name`\n"

    assert "test_an_elided_only_name" in judged_bare_names(text)
    assert "test_a_real_one" not in judged_bare_names(text), (
        "a full citation's right half belongs to the path arm and must not be "
        "judged twice under two different rules"
    )


# --- the boundary controls, on a synthetic markdown corpus -------------------

_MD_CORPUS: Final = {
    "docs/guarded.md": "see `tests/synthetic/test_planted.py::test_a_real_one`\n",
    "docs/loose.md": "see `tests/synthetic/test_planted.py::test_a_real_one`\n",
    "docs/prose.md": "no pointer here at all\n",
}


def test_a_doc_that_carries_citations_and_nothing_looks_at_is_reported() -> None:
    """CS-809's acceptance in the direction that has teeth: silence is the defect."""
    unrecorded, stale = guarded_set_problems(_MD_CORPUS, ["docs/guarded.md"], {})

    assert unrecorded == ["docs/loose.md"]
    assert stale == []


def test_a_doc_carrying_no_citation_is_asked_for_neither_a_guard_nor_a_record() -> None:
    """The set is bounded by what can rot, not by what is markdown.

    THE SECOND HALF IS WHAT MAKES THE FIRST MEAN ANYTHING. An assert-empty on
    its own is silent about whether the subject answered or merely returned
    nothing - a subject gutted to ``return [], []`` passes it. The same corpus
    is asked once more with a live finding in it, so the emptiness above is
    about ``docs/prose.md`` carrying no pointer rather than about the function
    having stopped speaking.
    """
    unrecorded, _stale = guarded_set_problems(_MD_CORPUS, ["docs/guarded.md", "docs/loose.md"], {})

    assert unrecorded == [], "a doc with no pointer in it was made to justify itself"

    still_answering, _stale = guarded_set_problems(_MD_CORPUS, ["docs/guarded.md"], {})
    assert still_answering == ["docs/loose.md"], (
        "the same corpus reports nothing when a doc IS unguarded and carries a "
        "pointer, so the empty result above is silence rather than an answer"
    )


def test_recording_a_doc_unguarded_answers_it_as_well_as_guarding_it_does() -> None:
    """Both are legitimate answers. Only the unstated third option is a defect.

    Paired with its own discriminator for the reason above: removing the record
    MUST turn the same corpus into a finding, or this test is an assert-empty
    that a subject returning nothing at all would satisfy.
    """
    unrecorded, stale = guarded_set_problems(
        _MD_CORPUS, ["docs/guarded.md"], {"docs/loose.md": "the deep archive, quotes not cites"}
    )

    assert (unrecorded, stale) == ([], [])

    without_the_record, _stale = guarded_set_problems(_MD_CORPUS, ["docs/guarded.md"], {})
    assert without_the_record == ["docs/loose.md"], (
        "dropping the record changed nothing, so the pass above was not the record being honoured"
    )


def test_a_record_for_a_doc_that_has_since_been_guarded_is_reported() -> None:
    """The reverse direction, and the one that makes this compose with guarding.

    Whoever later guards the archive gets told to delete its record rather than
    leaving a forgiveness entry behind that forgives nothing and hides the next
    thing that lands on it.
    """
    _unrecorded, stale = guarded_set_problems(
        _MD_CORPUS, ["docs/guarded.md", "docs/loose.md"], {"docs/loose.md": "stale now"}
    )

    assert len(stale) == 1, "a record for an already-guarded doc was accepted"
    assert "now guarded" in stale[0]


def test_a_record_naming_a_doc_that_is_not_tracked_is_reported() -> None:
    _unrecorded, stale = guarded_set_problems(_MD_CORPUS, [], {"docs/deleted.md": "gone"})

    assert len(stale) == 1, "a record for a file that does not exist was accepted"
    assert "not an in-domain tracked markdown file" in stale[0]


def test_a_record_for_a_doc_that_stopped_carrying_citations_is_reported() -> None:
    _unrecorded, stale = guarded_set_problems(_MD_CORPUS, [], {"docs/prose.md": "was a carrier"})

    assert len(stale) == 1, "a record that had stopped being needed was accepted"
    assert "nothing to leave unguarded" in stale[0]


# --- the boundary must read EVERY shape this module judges, not just one -----
#
# ONE DOC, ONE SHAPE EACH. The boundary once decided carrier-hood with
# :func:`citations_in`, which requires a `path.py` prefix, so three of the four
# shapes this module judges did not make a doc a carrier at all - including the
# elided one, added to this module in the same change that left the boundary
# blind to it. Each corpus below carries exactly ONE shape and nothing else, so
# a predicate that reads only some of them fails on the ones it cannot see.

_ONE_SHAPE_EACH: Final = {
    "docs/elided_only.md": "Verification: `::test_a_name_that_is_not_bound_anywhere`.\n",
    "docs/bare_only.md": 'Verification: `grep -c "test_a_name_that_is_not_bound_anywhere" x`\n',
    "docs/line_only.md": "see `tools/thing.py:900`\n",
    "docs/path_only.md": "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n",
}


@pytest.mark.parametrize("doc", sorted(_ONE_SHAPE_EACH))
def test_a_doc_carrying_only_one_judged_shape_is_still_a_carrier(doc: str) -> None:
    """Whatever this module would JUDGE in a doc is what makes the doc a carrier."""
    unrecorded, stale = guarded_set_problems({doc: _ONE_SHAPE_EACH[doc]}, [], {})

    assert unrecorded == [doc], (
        f"{doc} carries a shape this module judges and was not asked for a guard "
        "or a record, so it could join the unguarded set in silence"
    )
    assert stale == []


def test_every_pattern_this_module_judges_by_also_decides_what_carries_a_citation() -> None:
    """The boundary's membership is DERIVED from this module, not hand-listed.

    Fixing the four shapes by hand would leave the FIFTH arm to fall out of the
    boundary exactly the way the elided arm did - a new pattern is added, an arm
    is taught to read it, and nothing says the boundary must learn it too. So
    the check is not "are these four there", it is "does anything this module
    compiles sit outside :data:`JUDGED_SHAPES`". A new ``*_RE`` is red until it
    is answered one way or the other.
    """
    compiled = {
        name: value
        for name, value in globals().items()
        if name.endswith("_RE") and isinstance(value, re.Pattern)
    }

    assert compiled, (
        "this module compiles no pattern named *_RE, so the derivation below "
        "reads an empty set and would pass whatever the boundary ignored"
    )
    missing = sorted(name for name, value in compiled.items() if value not in JUDGED_SHAPES)
    assert not missing, (
        "patterns this module judges by that the boundary contract does not read:\n"
        + "\n".join(f"  {name}" for name in missing)
        + "\nAdd it to JUDGED_SHAPES, or stop judging by it."
    )


@pytest.mark.parametrize("doc", sorted(_ONE_SHAPE_EACH))
def test_recording_a_doc_carrying_only_one_judged_shape_is_not_called_stale(doc: str) -> None:
    """The worse direction of the same blindness, and the one that costs a record.

    A doc the predicate cannot see is not merely unreported - a maintainer who
    CORRECTLY records it is told the record is stale and to delete it, which
    turns a right answer into a wrong one.
    """
    unrecorded, stale = guarded_set_problems(
        {doc: _ONE_SHAPE_EACH[doc]}, [], {doc: "recorded unguarded on purpose"}
    )

    assert (unrecorded, stale) == ([], []), (
        f"a correct record for {doc} was rejected, so recording the doc is not "
        "an available answer for the shape it carries"
    )


def test_the_domain_excludes_a_harness_file_that_would_otherwise_be_a_carrier(
    tracked: list[str],
) -> None:
    """A rule about nothing is worse than no rule - it reads as coverage.

    THE FORM OF THIS TEST IS ITS POINT. Asking the fixture whether it contains
    a ``.claude/`` path proves nothing: the fixture filters them out by
    construction, so that assertion re-states its own comprehension and cannot
    fail however the rule is broken. This asks :func:`in_domain` instead, about
    a path that carries a citation, in BOTH directions - the harness file is
    excluded and its twin one directory over is not.

    MEASURED RESIDUAL, disclosed rather than implied away: no tracked
    ``.claude/*.md`` carries any judged shape today, in any of the four
    spellings, so the exclusion currently suppresses NOTHING. It is a rule
    about a real set of files and an empty set of pointers. That is why the
    planted carrier below is synthetic - it is the only carrier the exclusion
    has ever had to answer for.
    """
    carrier = "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n"
    harness = f"{OUT_OF_DOMAIN}commands/planted.md"

    assert not in_domain(harness), (
        f"{harness} carries a citation and reached the documentation domain; "
        "a harness-config edit would then redden a docs guard"
    )
    assert in_domain("docs/planted.md"), (
        "the same text one directory over was also excluded, so the predicate "
        "rejects documentation rather than harness configuration"
    )
    assert guarded_set_problems({"docs/planted.md": carrier}, [], {})[0] == ["docs/planted.md"], (
        "the planted text is not a carrier at all, so excluding it proves nothing"
    )
    assert [p for p in tracked if p.startswith(OUT_OF_DOMAIN) and p.endswith(".md")], (
        "nothing under .claude/ is tracked markdown, so OUT_OF_DOMAIN excludes nothing and "
        "should be deleted rather than left standing as a rule about an empty set"
    )


# --- contract 4: a disposition is a REDIRECT, and a redirect is verified -----
#
# THESE FOUR EXIST BECAUSE A MUTATION BATTERY FOUND THE GAP. Deleting the
# target-verification branch left the whole module green, because every
# recorded target resolves today - so the branch was a guard on a non-default
# path, which is the shape this project's own TDD rules call out as untested by
# construction. The controls below reach it with a synthetic table.

_REDIRECT_TEXT: Final = "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n"
_REDIRECT_KEY: Final = (
    "ROADMAP.md",
    "tests/synthetic/test_planted.py::test_a_name_that_is_not_there",
)


def test_a_disposition_whose_target_resolves_forgives_the_citation() -> None:
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_planted.py::test_a_real_one", "the target is live", 1
        )
    }

    assert unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table) == []


def test_a_disposition_whose_target_stopped_resolving_is_reported() -> None:
    """The mutant that survived until this test was written."""
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_planted.py::test_gone_now", "the target rotted", 1
        )
    }

    problems = unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table)

    assert len(problems) == 1, "a disposition pointing at a dead target was accepted"
    assert "does not resolve" in problems[0][2]


def test_a_disposition_whose_target_file_vanished_is_reported() -> None:
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_deleted.py::test_a_real_one", "the file is gone", 1
        )
    }

    assert len(unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table)) == 1


def test_a_bare_disposition_whose_target_stopped_resolving_is_reported() -> None:
    """The same non-default branch, on the arm that has no path to check."""
    text = 'Verification: `grep -c "test_a_name_that_is_not_bound" x.py`\n'
    key = ("ROADMAP.md", "test_a_name_that_is_not_bound")

    live = {key: Disposition(RENAMED, "tests/x.py::test_a_real_one", "live", 1)}
    rotted = {key: Disposition(RENAMED, "tests/x.py::test_gone_now", "rotted", 1)}

    assert bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], [], live) == []
    assert len(bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], [], rotted)) == 1


def test_a_no_target_disposition_forgives_without_naming_anything() -> None:
    """A disposition with nothing to verify forgives without naming a target.

    NO_TARGET and DELIBERATE must not be treated as a redirect carrying an
    empty target, which would resolve to nothing and report a defect on a
    citation that was deliberately left unassigned.
    """
    table = {_REDIRECT_KEY: Disposition(NO_TARGET, "", "no test bears this meaning", 1)}

    assert unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table) == []


# --- contract 5: CS-889 - a line pointer must land on something, and the -----
# --- line form is refused where a symbol form exists -------------------------


def test_no_line_pointer_in_the_scoped_population_lands_on_nothing(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
    sources: Mapping[str, str],
) -> None:
    """LEG 1. A pointer at a blank or bracket-only line resolves to nothing.

    Read over BOTH halves of the population. Blankness is not a claim about
    what a symbol form could replace, so the exemption that spares non-Python
    targets from the forbid leg buys them nothing here.
    """
    py_sites, other_sites = live_line_pointers

    empty, _forbidden = line_pointer_content_problems(py_sites, other_sites, sources)

    assert not empty, "line pointers landing on nothing:\n" + "\n".join(
        f"  {problem}" for problem in empty
    )


def test_no_line_pointer_names_a_tracked_python_module_without_a_record(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
    sources: Mapping[str, str],
) -> None:
    """LEG 2. The symbol form is a drop-in that an edit above cannot invalidate."""
    py_sites, other_sites = live_line_pointers

    _empty, forbidden = line_pointer_content_problems(py_sites, other_sites, sources)

    assert not forbidden, "line pointers at tracked Python modules:\n" + "\n".join(
        f"  {problem}" for problem in forbidden
    )


def test_every_grandfathered_line_pointer_is_still_spelled(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
) -> None:
    """The pin, checked in the direction that keeps it from outliving its corpus."""
    py_sites, _other = live_line_pointers
    live = [(carrier, path, line) for carrier, path, line, _landing in py_sites]

    problems = stale_pin_problems(live, UNVERIFIED_LINE_POINTERS)

    assert not problems, (
        "UNVERIFIED_LINE_POINTERS has outlived its corpus:\n"
        + "\n".join(f"  {problem}" for problem in problems)
        + "\nA pointer that was repaired or deleted must leave the pin."
    )


def test_the_unforbidden_line_pointer_residual_is_pinned_in_both_directions(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
) -> None:
    """THE STATED PRICE OF THE FORBID RULE, kept countable rather than silent.

    A pointer at a ``.yml``, ``.md`` or ``.toml`` file is NOT forbidden,
    because those files have no symbol form - forbidding the line form there
    would leave no way to cite them at all. That exemption is a real hole:
    those pointers rot on an edit above them exactly as the Python ones do, and
    nothing in this module checks their content either. Pinning the sites is
    what stops the hole from growing without anyone noticing.
    """
    _py_sites, other = live_line_pointers
    unforbidden = {(carrier, path, line) for carrier, path, line, _landing in other}

    assert set(unforbidden) == set(UNFORBIDDEN_LINE_POINTERS), (
        f"the unforbidden residual is {len(set(unforbidden))} site(s), pinned at"
        f" {len(UNFORBIDDEN_LINE_POINTERS)}."
        f"\n  arrived: {sorted(set(unforbidden) - set(UNFORBIDDEN_LINE_POINTERS))}"
        f"\n  gone: {sorted(set(UNFORBIDDEN_LINE_POINTERS) - set(unforbidden))}"
    )


def test_no_line_pointer_is_both_adjudicated_and_grandfathered() -> None:
    """One site, one forgiveness, so neither table hides the other going stale."""
    adjudicated = {(doc, cited) for doc, cited in DISPOSITIONS if LINE_POINTER_RE.fullmatch(cited)}
    grandfathered = {
        (carrier, line_key(path, line)) for carrier, path, line in UNVERIFIED_LINE_POINTERS
    }

    assert not adjudicated & grandfathered, (
        f"forgiven twice, so retiring either record changes nothing: {adjudicated & grandfathered}"
    )


def test_no_carrier_comes_from_a_doc_this_module_declines_to_read(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The negative controls, asserted on the LIVE population rather than assumed.

    ``docs/history_notes.md`` is the recorded-unguarded deep archive, where
    quoting and citing cannot be told apart by shape; ``docs/_archive/`` is
    dated material excluded from every search for current truth; ``.claude/``
    is harness configuration and out of domain entirely. A carrier from any of
    the three would mean this section had quietly widened past the boundary the
    rest of the module keeps.
    """
    intruders = sorted(
        carrier
        for carrier in line_pointer_carriers
        if carrier in UNGUARDED_DOCS or carrier.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
    )

    assert not intruders, f"carriers read from outside the stated boundary: {intruders}"


# --- the CS-889 controls, on a corpus with no filesystem involved ------------

_LANDING_CORPUS: Final = {
    "clockspeed/synthetic/mod.py": [
        "class Thing:",
        "    pass",
        "",
        "        )",
        "    an ordinary sentence inside a docstring",
    ],
    "docs/synthetic/note.md": ["# a heading", "prose", ""],
}
_LANDING_SOURCE: Final = {"clockspeed/synthetic/mod.py": "def _live_target() -> None:\n    pass\n"}
_SYNTHETIC_MODULE: Final = "clockspeed/synthetic/mod.py"
_SYNTHETIC_DOC: Final = "docs/synthetic/note.md"


def _planted(path: str, line: int) -> dict[str, str]:
    """A one-carrier corpus spelling exactly one pointer.

    ASSEMBLED, NEVER SPELLED, for :func:`line_key`'s reason: this module is
    itself a carrier the arms above read, so a literal pointer written here
    would be a real one.
    """
    return {"ROADMAP.md": f"see `{line_key(path, line)}` for the shape\n"}


def test_a_pointer_landing_on_a_blank_line_is_reported() -> None:
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 3), _LANDING_CORPUS)

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, ())

    assert len(empty) == 1, f"a pointer at a blank line was not reported: {empty}"
    assert forbidden == [], "a blank landing was reported as a forbid-leg finding instead"


def test_a_pointer_landing_on_a_lone_bracket_is_reported() -> None:
    """Punctuation is not a declaration, and a closing bracket is the common case."""
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 4), _LANDING_CORPUS)

    empty, _forbidden = line_pointer_content_problems(py_sites, other, {}, {}, ())

    assert len(empty) == 1, f"a pointer at a bracket-only line was not reported: {empty}"


def test_the_emptiness_leg_is_green_on_a_pointer_that_lands_on_prose() -> None:
    """WHY LEG 1 ALONE IS REFUTED, pinned so it cannot be quietly dropped.

    CS-889's primary target landed on a docstring line roughly eighty lines
    above the declaration its sentence claimed. The line was neither blank nor
    punctuation, so an emptiness check is GREEN on it - which is exactly the
    measurement that made the forbid leg necessary rather than optional.
    """
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, ())

    assert empty == [], "the emptiness leg claimed a finding it cannot honestly make"
    assert len(forbidden) == 1, f"the forbid leg missed what the emptiness leg passes: {forbidden}"


def test_a_grandfathered_pointer_is_forgiven_by_the_forbid_leg_and_not_by_the_other() -> None:
    """The baseline claims nothing about content, so it cannot answer blankness."""
    prose = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)[0]
    blank = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 3), _LANDING_CORPUS)[0]
    pinned = (
        ("ROADMAP.md", _SYNTHETIC_MODULE, 5),
        ("ROADMAP.md", _SYNTHETIC_MODULE, 3),
    )

    assert line_pointer_content_problems(prose, [], {}, {}, pinned) == ([], [])
    empty, forbidden = line_pointer_content_problems(blank, [], {}, {}, pinned)
    assert len(empty) == 1, "a pinned pointer that went blank was forgiven, and it must not be"
    assert forbidden == []


def test_a_recorded_redirect_whose_target_resolves_forgives_the_pointer() -> None:
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5))
    table = {key: Disposition(MOVED, f"{_SYNTHETIC_MODULE}::_live_target", "the target is live", 1)}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    assert line_pointer_content_problems(py_sites, other, _LANDING_SOURCE, table, ()) == ([], [])


def test_a_recorded_redirect_whose_target_stopped_resolving_is_reported() -> None:
    """A record that points at nothing forgives nothing, on the new arm too."""
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5))
    table = {key: Disposition(MOVED, f"{_SYNTHETIC_MODULE}::_gone_now", "the target rotted", 1)}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    _empty, forbidden = line_pointer_content_problems(py_sites, other, _LANDING_SOURCE, table, ())

    assert len(forbidden) == 1, "a redirect at a dead target was accepted"
    assert "does not resolve" in forbidden[0]


def test_a_record_forgives_a_blank_landing_that_the_baseline_may_not() -> None:
    """An ADJUDICATED answer silences both legs; that is what adjudication buys."""
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 3))
    table = {key: Disposition(NO_TARGET, "", "the carrier is append-only", 1)}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 3), _LANDING_CORPUS)

    assert line_pointer_content_problems(py_sites, other, {}, table, ()) == ([], [])


def test_a_pointer_at_a_tracked_non_python_file_is_not_forbidden() -> None:
    """No symbol form exists there, so forbidding would leave no way to cite it."""
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_DOC, 2), _LANDING_CORPUS)
    _empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, ())

    assert py_sites == [], "a non-Python target entered the forbidden class"
    assert other == [("ROADMAP.md", _SYNTHETIC_DOC, 2, "prose")]
    assert forbidden == [], "a non-Python target was refused a form it cannot have"


def test_a_non_python_pointer_that_lands_on_nothing_is_still_reported() -> None:
    """THE EXEMPTION IS FROM THE FORBID LEG ONLY, and this is where that bites.

    A ``.yml`` or ``.md`` target has no symbol form, so the line form is all
    there is and forbidding it would leave no way to cite the file at all. It
    does NOT follow that such a pointer may name nothing: blankness is not a
    claim about what could replace the pointer. An arm that let the forbid
    exemption widen into an emptiness exemption would have bought a tidier
    boundary by making a whole class of dead pointer invisible.
    """
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_DOC, 3), _LANDING_CORPUS)

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, ())

    assert len(empty) == 1, f"a non-Python pointer at a blank line was not reported: {empty}"
    assert forbidden == [], "a non-Python target was reported by the forbid leg"


def test_the_declines_the_range_arm_already_makes_keep_the_synthetic_fixtures_out() -> None:
    """REUSED, NOT RE-INVENTED, which was the stated requirement.

    The synthetic Python fixtures this module and its siblings plant are
    excluded by tests that already existed - an unqualified basename carries no
    directory to resolve against, and a path outside the index is not a tracked
    file. A carve-out written for the fixtures by name would be one a later
    fixture could fall outside of.
    """
    bare = {"ROADMAP.md": "see `" + line_key("planted.py", 5) + "`\n"}
    untracked = _planted("tests/synthetic/test_planted.py", 1)
    ledger_self = {LEDGER: "see `" + line_key(LEDGER, 128) + "`\n"}
    past_end = _planted(_SYNTHETIC_MODULE, 900)

    for carriers in (bare, untracked, ledger_self, past_end):
        assert line_pointer_sites(carriers, _LANDING_CORPUS) == ([], []), (
            f"a declined shape entered the CS-889 population: {carriers}"
        )


def test_a_stale_pin_is_reported() -> None:
    problems = stale_pin_problems([], (("ROADMAP.md", _SYNTHETIC_MODULE, 5),))

    assert len(problems) == 1, "a pin for a pointer nothing spells was accepted"
    assert "no longer spells it" in problems[0]


# The five pointers CS-889 was filed on, REBUILT AS A PLANT because the
# originals no longer exist: `tests/test_make_cert.py` carries ZERO line
# pointers today - an earlier slice repaired all five to symbol form, which is
# the repair this section's forbid leg asks for. So a check phrased "the arm is
# green on the five filed instances" is unrunnable as written, and a check
# phrased "the arm reports them" has to reconstruct them. Two of the five were
# written as line RANGES; the pattern reads the first number of a range, so the
# plant spells them the same way the doc did.
_FILED_CERT_LINES: Final = (222, 224, 279)
_FILED_ENV_LINES: Final = (358, 372)
_FILED_CERT: Final = "scripts/synthetic_cert.py"
_FILED_ENV: Final = "scripts/synthetic_env.py"


def test_each_of_the_five_originally_filed_pointers_is_reported() -> None:
    """The acceptance control, on a reconstruction rather than on a memory."""
    corpus = {
        _FILED_CERT: ["x = 1"] * 300,
        _FILED_ENV: [""] * 400,
    }
    carriers = {
        "ROADMAP.md": "\n".join(
            [f"see `{line_key(_FILED_CERT, line)}`" for line in _FILED_CERT_LINES]
            + [f"and `{line_key(_FILED_ENV, line)}-380`" for line in _FILED_ENV_LINES]
        )
    }

    py_sites, other = line_pointer_sites(carriers, corpus)
    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, ())

    assert len(py_sites) == len(_FILED_CERT_LINES) + len(_FILED_ENV_LINES), (
        f"the plant did not reconstruct all five filed pointers: {py_sites}"
    )
    assert len(empty) == len(_FILED_ENV_LINES), (
        f"the two pointers at blank lines were not both reported: {empty}"
    )
    assert len(forbidden) == len(_FILED_CERT_LINES), (
        f"the three pointers at live lines were not all reported: {forbidden}"
    )


def test_this_test_module_is_seven_bit_ascii() -> None:
    """Non-negotiable 4, checked on this file rather than assumed of it."""
    raw = Path(__file__).read_bytes()

    assert not [byte for byte in raw if byte > HIGHEST_ASCII], (
        "this module carries a byte above the 7-bit range"
    )
