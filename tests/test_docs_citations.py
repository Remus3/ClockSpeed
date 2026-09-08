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
   trap 4 in the line-pointer arm. A CS-889 note spells three pointers that
   were already dead when it was filed, precisely in order to say so. Reporting
   one would punish the record for doing the right thing, so the site carries a
   DELIBERATE disposition and stays silent. Telling the two apart in markdown
   is CS-899, which is OPEN: a keyword or negation detector for it was priced
   and REFUSED, because it fails in the PERMISSIVE direction and forgives a
   real dead citation forever with nothing red.

WHAT THIS MODULE DOES NOT COVER, recorded rather than left to be discovered.
:data:`UNGUARDED_DOCS` is the whole of it, and it is a RECORD rather than a
silence: a file carrying a citation is either read or named there with its
reason, checked in both directions, so the unguarded set cannot grow or linger
unnoticed. ``docs/history_notes.md`` is its ONE member. Guarding it later is a
one-line change that this contract then FORCES, by failing the record that has
stopped being needed.

CS-897 - AN EXEMPTION'S REASON MUST BE TRUE OF EVERY MEMBER, AND THAT ONE WAS
NOT. It read that the archive's dead pointers sit inside citation-guard detail
blocks whose SUBJECT is a pointer being dead, so quoting and citing cannot be
told apart by shape there. MEASURED against the file, that describes TWO of the
sites and none of the rest. The repair is not a wider sentence, because a
sentence is what failed: the reason now rests on what the file DECLARES ABOUT
ITSELF, and the population it hides is COUNTED, per arm, against typed integers.

THAT MACHINERY IS NO LONGER IN THIS FILE, and the move is the size gate rather
than taste. The derivation is ``tests/archive_rot_guard.py`` and the pin with
its four arms is ``tests/test_archive_rot.py``, taken out whole when this module
came within 1483 bytes of the ceiling ``tests/data/test_phase2_gate.py`` holds
every file under ``tests/`` to - a control whose subject is a trimmed slice of
real game data, and which is not raised to make room for prose. WHAT STAYS
HERE IS THE EXEMPTION ITSELF: :data:`UNGUARDED_DOCS`, the path it names and the
pin on its cardinality. The boundary is drawn on SUBJECT - what the exemption
IS, against what it HIDES - and the import at the FOOT of this file is what
keeps the relocated half inside the walked closure rather than outside every
contract that reads it.

THERE ARE TWO POPULATIONS AND THEY HAVE DIFFERENT BOUNDARIES. Saying so is a
correction: this paragraph once read "every in-domain markdown file", and
:func:`in_domain` is markdown-only, while CS-889 had already widened what the
line-pointer arm READS past markdown. The record described a narrower module
than the one that shipped, which is the shape that lets a gap hide inside a
sentence nobody re-derives.

- THE CITATION POPULATION - ``path::name``, bare names, elided names - is the
  markdown one :func:`in_domain` describes, adjudicated over
  :data:`GUARDED_DOCS`.
- THE LINE-POINTER POPULATION is EVERY TRACKED FILE, less the same recorded
  exemptions. Not a suffix list: a hand-maintained one is a boundary that the
  next extension to start carrying a pointer crosses in silence. See
  :func:`line_pointer_carriers` for what that narrower boundary cost.
- THE BARE-PATH POPULATION IS THE LINE-POINTER ONE, consumed rather than
  rebuilt. CS-891 needed every tracked file for the same reason CS-889 did, and
  a third population would be a third thing to rot - these two have already
  disagreed once, over the dated archive.

CS-891 - THE FIFTH SHAPE, AND WHAT IT COST TO ADD ONE. Every shape above needs
a SEPARATOR after the path, so a doc spelling a repo-relative path plainly was
matched by NONE of them: a pointer at a path that does not exist was green in
every file in this repository. That is CS-442's founding finding one more level
up. The arm is a DECLINE LADDER - see :func:`bare_path_ladder` - because the
question a bare path asks cannot be answered yes or no. Resolving a partially
qualified path repo-relative and calling it missing is trap 2 exactly, so R1
resolves a UNIQUE suffix hit and REPORTS an ambiguous one; and three separate
rungs decline a path for a stated mechanical reason rather than reporting it.
Each decline is invisibility bought for a reason, so each rung's live
membership is PINNED and checked in both directions - appending to one makes it
disagree with what the ladder derives.

AND ADDING THE FIFTH SHAPE FALSIFIED ONE OF THIS MODULE'S OWN MEASURED
SENTENCES AND STALED THREE RESTATED COUNTS, recorded rather than quietly
repaired. The harness-domain exclusion said it suppressed NOTHING - true of a
module judging four shapes that all needed a separator, and false the moment
one did not, because harness prose names module and tool paths constantly. That
arm now MEASURES its residual every run instead of asserting it in prose, and
the three sentences that said "four" now name :data:`JUDGED_SHAPES` instead of
counting it. A fact restated where nothing checks it is the fault this module
exists to find, and it had four of its own.

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
- AND CLOSED AGAINST BEING SILENCED, which the first build was not.
  :func:`forgiveness_budget_problems` counts every forgiveness - pins and
  line-pointer dispositions together - against one recorded number that may
  only come down. An adversary had appended three pins and two fabricated
  dispositions and shipped this module GREEN with every live defect intact.
  Leaving findings red rather than laundering them was restraint, and
  restraint is not a mechanism.
- WHAT REMAINS UNVERIFIED, and it is the larger number: every member of
  :data:`UNVERIFIED_LINE_POINTERS` resolves in RANGE and has NOT been checked
  against the sentence that spells it, and every member of
  :data:`UNFORBIDDEN_LINE_POINTERS` is a pointer the forbid rule cannot reach
  at all because its target has no symbol form. Both are open residuals of
  CS-889. Neither table claims anything else, and calling either one an
  adjudication would be the laundering this module exists to prevent.
- THE PINS NO LONGER FOLLOW THE ROT, which is a narrower claim than being
  verified and a much larger one than the first build made. Each is anchored to
  a digest of the line it froze, so a pinned pointer that drifts under a later
  edit is reported rather than grandfathered forever. Unexamined is a state a
  record may honestly report; immunised against detection is not.

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
import hashlib
import re
import string
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from tests.bare_path_guard import (
    _INTERPRETER_NAMES,
    AMBIGUOUS_SUFFIX,
    BARE_PATH_RE,
    DECLARED_UNTRACKED,
    FIXTURE_LITERAL,
    LADDER_RUNGS,
    RECORDED_REASON,
    REPO_ROOT,
    RESOLVED_EXACT,
    RESOLVED_SUFFIX,
    UNRESOLVED,
    UNTRACKED_ROOT,
    BarePathReason,
    BarePathSite,
    bare_path_budget_problems,
    bare_path_ladder,
    bare_path_problems,
    bare_path_reason_problems,
    bare_path_sites,
    declares_untracked,
    decline_budget_problems,
    derived_bound_problems,
    floor_problems,
    graded_floor_names,
    module_containers,
    module_patterns,
    pinned_rung_problems,
    source_roots,
)
from tests.save import test_oracle_citations as oracle_citations

# Non-negotiable 4 is 7-bit ASCII, so the highest byte an authored file may
# carry is 0x7E - the tilde, the last printable character in the range.
HIGHEST_ASCII: Final = 0x7E

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

#: The CS-909 decision that the shell MAY start the surface, and stops only what
#: it started. GUARDED for the same reason 0014 is: it argues from named code -
#: the module holding the spawn and adopt verdicts, and the wiring that consumes
#: them - and the wiring is again the half nothing would otherwise check, since
#: `shell/main.js` imports electron and is loaded by no test in either language.
ADR_0015: Final = "docs/adr/0015-the-shell-may-start-the-surface.md"

#: CS-913 - the unlock carriers and their serialized grammar.
ADR_0016: Final = "docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md"

#: The operating law of the companion and the overlay, adapted 2026-09-05.
HUD_DOCTRINE: Final = "docs/hud_doctrine.md"

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
    ADR_0015,
    # CS-913's measurement. Guarded on arrival rather than recorded unguarded:
    # every citation in it resolves today, and it was authored in the same
    # session that watched three line pointers rot when an import moved the
    # lines beneath them.
    ADR_0016,
    # Guarded on arrival: every arm it names resolves today, and it exists to be
    # read when the overlay is built rather than rediscovered then.
    HUD_DOCTRINE,
    ITEM_NOTES,
    *ITEM_NOTES_LEAVES,
    # A memory leaf that cites a test by name. Guarded rather than recorded,
    # because every pointer in it resolves today and a durable lesson whose
    # cited proof has been deleted is worse than no lesson.
    "memory/moving-an-assert-can-create-the-leak.md",
    "memory/a-guard-can-measure-spelling.md",
    "memory/a-guard-can-be-green-by-accident.md",
    # CS-891 - THE DOCS THAT SPELL A PATH AND NOTHING THIS MODULE YET READS.
    # Every shape in JUDGED_SHAPES needs a separator after the path - a name
    # after "::", or a number after a colon - so a doc naming a module or a
    # tool plainly is not a carrier and has never had to be guarded. The
    # eighteen below are the in-domain markdown files that become carriers the
    # moment a shape reads the bare path, MEASURED by running this module's own
    # predicate against the corpus rather than reasoned about. Guarded in a
    # change that adds no shape, so the arm that reads one does not arrive in
    # the same commit as the population it would judge - and so its first run
    # is a statement about the arm rather than about the widening.
    #
    # ZERO NEW FINDINGS, MEASURED ACROSS ALL THREE EXISTING ARMS on every one
    # of them. That is expected rather than reassuring: none of the three reads
    # a bare path, so the number this widening could have moved was zero by
    # construction. What it buys is that the fifth arm's findings will be the
    # fifth arm's.
    #
    # The six roots of the doc topology. Each spells repo-relative module,
    # tool and config paths - twenty distinct ones in CLAUDE.md, twelve in
    # CONVENTIONS.md - and every one of those resolves to a tracked file today.
    "BACKLOG.md",
    "BOOTSTRAP.md",
    "CLAUDE.md",
    "CONVENTIONS.md",
    "README.md",
    "THIRD_PARTY.md",
    # The three docs whose SUBJECT is where code and commands live, so they
    # spell more paths than anything else here.
    #
    # MEASURED RESIDUAL IN docs/ARCHITECTURE.md, disclosed because a later arm
    # will meet it: of its forty distinct qualified paths, twenty resolve to
    # tracked files and twenty do not. Three name advisor modules that are
    # planned and not yet built; the other seventeen are written relative to a
    # package root stated in the surrounding table rather than to the repo, so
    # resolving them repo-relative would report absences that are artifacts of
    # the reader - trap 2, in the arm that has not been written yet. Guarding
    # the file costs nothing today because no arm reads a bare path.
    "docs/ARCHITECTURE.md",
    "docs/OPERATIONS.md",
    "docs/upstream_watch.md",
    # The ADR family. The five ADRs already guarded above got there by naming a
    # test or a line; these eight name only files - the index, a sibling ADR,
    # docs/GATED.md, a pinned module - and all of them resolve today. Guarding
    # the family whole means a new ADR that cites a test is caught by the
    # boundary contract rather than by whoever notices.
    "docs/adr/README.md",
    "docs/adr/0001-adr-process.md",
    "docs/adr/0003-s4-node-actors-in-save.md",
    "docs/adr/0005-overclock-ceiling-source.md",
    "docs/adr/0006-unsharded-clock-base-and-the-ceiling-fence.md",
    "docs/adr/0007-header-and-chunk-framing-are-version-dependent.md",
    "docs/adr/0009-inventory-potential-top-level-carries-no-slot-count.md",
    "docs/adr/0013-electron-licence-gate.md",
    # The one memory leaf left outside the three above. It names the test
    # module its lesson was learned in, and that module is tracked today - the
    # same reason those three are guarded rather than recorded.
    "memory/a-guard-can-be-accepted-and-unscoped.md",
    # The lane's fork ruling (CS-918). It names the two modules the fork
    # decision is ABOUT, so the whole point of the record is those two pointers
    # staying live - an ADR whose subject has been renamed out from under it
    # argues about nothing.
    "docs/adr/0017-the-lane-forks-the-shared-loop-modules.md",
    # The headless queue lane's worker prompt (CS-918). Guarded on arrival
    # rather than recorded, because every path in it resolves today AND because
    # of who reads it: an unattended worker, once per cycle, with nobody
    # watching. That is precisely where a rotted pointer goes unobserved - the
    # worker would follow it, find nothing, and improvise.
    "tools/headless-queue.md",
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
        The path, POSIX-separated, in the spelling :data:`BARE_PATH_RE` reads.
    """
    return "/".join(segments)


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
JUDGED_SHAPES: Final = (CITATION_RE, LINE_POINTER_RE, BARE_RE, ELIDED_RE, BARE_PATH_RE)


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
        1,
    ),
    (LEDGER, line_key("tools/facts_probe.py", 121)): Disposition(
        MOVED,
        "tools/facts_probe.py::_build_string",
        "the entry reads that line as the deferred `import verify_env` that"
        " makes the tools rung cost 9 errors and not 4. It now sits at :136"
        " inside _build_string, whose docstring carries the same reasoning the"
        " ledger entry does - the reader lives in scripts/verify_env.py and"
        " stays there.",
        1,
    ),
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
    # THE TRAP THAT MANUFACTURES A FINDING ON CORRECT PROSE lived here as a
    # DELIBERATE entry for `scripts/make_cert.py` at line 224 - the CS-889 note
    # spelled that pointer as the SUBJECT of a correction rather than as a
    # citation, and QUOTING AND CITING ARE INDISTINGUISHABLE BY SHAPE. The entry
    # is gone because the site is: CS-889 closed and its note relocated to
    # `docs/history_notes.md`, which is exempt from this module for exactly that
    # reason. The stale-entry contract reported it on the very next run, which is
    # the record being checked in both directions rather than believed.
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
    ("ROADMAP.md", "tests/save/test_container_elements.py", 839): "f14141e92679",
    ("ROADMAP.md", "tests/save/test_inventory_potential.py", 316): "c86d7b08a03a",
    ("ROADMAP.md", "tests/save/test_reference_resolution.py", 968): "f9e88114f42a",
    ("docs/LEDGER.md", "clockspeed/data/docs_extract.py", 443): "7d6e8ff5649f",
    ("docs/LEDGER.md", "clockspeed/data/locate.py", 187): "53bcd3acffa2",
    ("docs/LEDGER.md", "clockspeed/data/locate.py", 657): "c0f880c0e553",
    ("docs/LEDGER.md", "clockspeed/data/version.py", 352): "1e211b03496a",
    ("docs/LEDGER.md", "clockspeed/data/version.py", 815): "d5cb7f2c533e",
    ("docs/LEDGER.md", "clockspeed/save/objects.py", 2945): "bee547e7a02b",
    ("docs/LEDGER.md", "clockspeed/save/usmap.py", 46): "82be9ba39f87",
    ("docs/LEDGER.md", "scripts/install_hooks.py", 310): "4facec475176",
    ("docs/LEDGER.md", "tests/data/test_phase2_gate.py", 775): "edaece1458c2",
    ("docs/LEDGER.md", "tests/test_hook_interpreter_ladder.py", 1678): "341d96509c98",
    ("docs/LEDGER.md", "tools/edit_lint_check.py", 82): "c52969cc5a4b",
    ("docs/LEDGER.md", "tools/edit_lint_check.py", 113): "a7515962ef0b",
    ("docs/LEDGER.md", "tools/precommit_gate.py", 570): "4b165904f3ca",
    ("docs/LEDGER.md", "tools/precommit_gate.py", 704): "7db8a31d0783",
    ("docs/LEDGER.md", "tools/precommit_gate.py", 1802): "7545e5808a11",
    ("docs/item_notes/phase2.md", "clockspeed/data/registry.py", 84): "1a66118b40b6",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 39): "0d5e3276442e",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 141): "fa085c760a09",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/data/locate.py", 187): "53bcd3acffa2",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/header.py", 927): "2b49f05b544d",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/objects.py", 1747): "0e68b6914ed2",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/workdir.py", 688): "e2d30d6ce513",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/world.py", 989): "7b4d51124c45",
    ("docs/item_notes/phase4-followups-850.md", "clockspeed/save/world.py", 1109): "25062ba27287",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/save/test_container_elements.py",
        839,
    ): "f14141e92679",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/save/test_container_elements.py",
        1168,
    ): "b04f24100c34",
    ("docs/item_notes/phase4-followups-850.md", "tests/save/test_header.py", 1048): "0e6ebeb1b024",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/save/test_inventory_potential.py",
        316,
    ): "c86d7b08a03a",
    (
        "docs/item_notes/phase4-followups-850.md",
        "tests/save/test_reference_resolution.py",
        968,
    ): "f9e88114f42a",
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
    (
        "docs/item_notes/phase4-followups.md",
        "tests/test_hook_interpreter_ladder.py",
        122,
    ): "bbf9278cdad0",
    ("docs/item_notes/phase4.md", "tests/data/test_locate.py", 858): "7b83ed5742f3",
    ("docs/item_notes/phase4.md", "tests/save/synthetic.py", 1079): "b260445518a9",
    ("docs/item_notes/phase4.md", "tests/save/test_byte_order_status.py", 878): "5d5874e29659",
    ("docs/item_notes/phase4.md", "tests/save/test_objects.py", 776): "98fb3674bec1",
    ("docs/item_notes/phase4.md", "tests/save/test_phase4_gate.py", 2089): "d2973a15655f",
}

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
#:
#: CS-928 MOVED ONE OF THESE AND COULD NOT MOVE THE OTHER, and the pair is worth
#: reading together because it measures exactly what the stated price above buys.
#: CS-928 rewrote `docs/ARCHITECTURE.md` section 3 and both pointers into it
#: rotted. The `tests/test_precommit_gate.py` one is a REPAIR - :144 named the
#: raw-docs paragraph rather than the `tools/` prohibition the comment claims, so
#: the pointer was re-cut to :141 and this site follows it. Nothing here was
#: forgiven: a repaired pointer moves the pin, it does not spend one.
#:
#: THE LEDGER ONE WAS NOT REPAIRED, because `docs/LEDGER.md` is append-only by
#: its own header and the repair this table would otherwise demand is an edit
#: that file forbids. The correcting record is appended instead. That leaves the
#: pointer live and BLANK, which leg 1 refuses and which no pin here answers -
#: blankness is not what this table forgives. It is REPORTED rather than
#: absorbed; see the CS-300 correction record in `docs/LEDGER.md`, which spells the
#: disposition an adjudicator would have to grant for it to go green.
UNFORBIDDEN_LINE_POINTERS: Final[frozenset[tuple[str, str, int]]] = frozenset(
    (
        ("docs/LEDGER.md", ".github/workflows/tier1.yml", 130),
        ("docs/LEDGER.md", ".github/workflows/tier1.yml", 250),
        ("docs/LEDGER.md", "docs/ARCHITECTURE.md", 136),
        ("tests/test_docs_citations.py", ".github/workflows/tier1.yml", 250),
        ("tests/test_precommit_gate.py", "docs/ARCHITECTURE.md", 141),
    )
)


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
FORGIVEN_LINE_POINTER_CEILING: Final = 66

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


def landing_digest(landing: str) -> str:
    """Anchor one pinned pointer to the text of the line it froze.

    STRIPPED BEFORE HASHING, so a reindent or a trailing-whitespace sweep does
    not spend an adjudication. What must fire is the line meaning something
    else, not the line being moved sideways.

    Args:
        landing: The target line, as read from the file.

    Returns:
        Twelve hex characters of the SHA-256 of the stripped line.
    """
    return hashlib.sha256(landing.strip().encode("utf-8")).hexdigest()[:12]


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
            # LINE ZERO IS NOT LINE MINUS ONE. Files are numbered from 1, so a
            # `:0` pointer names no line at all - but the range test above only
            # refuses numbers ABOVE the end, and `lines[line - 1]` on zero
            # silently hands back the LAST line of the target. Both legs would
            # then judge the pointer while quoting the wrong line as evidence.
            # No such pointer exists in the tree today; the guard is here
            # because the failure is silent and the fix is one branch.
            landing = "" if line < 1 else lines[line - 1]
            found = py_sites if path.endswith(".py") else other_sites
            found.append((carrier, path, line, landing))
    return py_sites, other_sites


def line_pointer_content_problems(
    py_sites: Iterable[tuple[str, str, int, str]],
    other_sites: Iterable[tuple[str, str, int, str]],
    sources: Mapping[str, str],
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
    baseline: Mapping[tuple[str, str, int], str] | None = None,
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
        baseline: The grandfathered sites, unexamined and recorded as such,
            each mapped to the digest of the line it froze.

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
    grandfathered = dict(UNVERIFIED_LINE_POINTERS if baseline is None else baseline)
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
            elif not forbiddable:
                continue
            elif (carrier, path, line) not in grandfathered:
                forbidden.append(
                    f"{carrier} -> {path} line {line} - a line pointer at a tracked Python"
                    f" module, and it lands on {landing.strip()!r}. Cite the symbol form,"
                    " which an edit above it cannot invalidate."
                )
            elif grandfathered[(carrier, path, line)] != landing_digest(landing):
                forbidden.append(
                    f"{carrier} -> {path} line {line} - PINNED, BUT THE LINE HAS MOVED"
                    f" UNDER IT. It now reads {landing.strip()!r}, which is not what the"
                    " pin froze. The pin recorded that this site was unexamined, never"
                    " that it may drift unexamined. Convert it to the symbol form, or"
                    " adjudicate it into DISPOSITIONS - re-cutting the digest keeps a"
                    " pointer that has already been shown to follow the rot."
                )
    return empty, forbidden


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


#: This module's own repo-relative path. DERIVED rather than spelled, because
#: a literal would be a citation this module makes about itself and the
#: self-infliction arm below would then be measuring the spelling rather than
#: the tree.
THIS_MODULE: Final = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

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
#: written; see :func:`decline_budget_problems`.
DECLINED_AS_DECLARED_UNTRACKED: Final[Mapping[tuple[str, str, str], int]] = {
    ("ROADMAP.md", "config/local.json", "## Phase 4 - save reader"): 1,
    ("clockspeed/solve/optimize.py", "config/local.json", ""): 1,
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
        "docs/item_notes/phase4-followups-900.md",
        ".claude/settings.local.json",
        "### FILED 2026-09-07 (session 73), self-disclosed",
    ): 1,
    (
        "docs/item_notes/phase7.md",
        ".claude/settings.local.json",
        "#### 5. CS-952 is sequenced BEFORE the flip and is a hard blocker",
    ): 1,
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
    ("tests/test_architecture_attributions.py", "advisor/cards.py", ""): 2,
    ("tests/test_architecture_attributions.py", "advisor/ledger.py", ""): 2,
    ("tests/test_architecture_attributions.py", "advisor/trace.py", ""): 2,
    ("tests/test_chained_cause_census.py", "also/not/frozen.py", "_FROZEN_MARKDOWN"): 1,
    ("tests/test_chained_cause_census.py", "not/frozen.py", "_FROZEN_MARKDOWN"): 1,
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
}

#: THE THREE DECLINE DISCLOSURES' RECORDED BUDGETS, one per rung and never
#: pooled, for the reason :func:`decline_budget_problems` states. Each is an
#: integer literal a person typed, which
#: :func:`derived_bound_problems` is what keeps true.
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
DECLARED_UNTRACKED_CEILING: Final = 9
#: 9 TO 6 WHEN CS-928 DELETED THE THREE FALSE ADVISOR ATTRIBUTIONS. Six
#: `docs/ARCHITECTURE.md` rows left the rung and three arrived from the guard
#: that now asserts those files absent, so the disclosure holds six rows and the
#: ceiling comes down to six. It counts ROWS, not sites: the three new rows
#: disclose two sites each.
UNTRACKED_ROOT_CEILING: Final = 6
FIXTURE_LITERAL_CEILING: Final = 7

#: THE ONLY BUDGET IN THIS SECTION. Everything above is a disclosure that
#: cannot be added to; this is the escape hatch, and it ratchets.
#:
#: FOUR ENTRIES, TWO OF ONE KIND AND TWO SINGLETONS, and each is checked
#: against the corpus in three directions by
#: :func:`bare_path_reason_problems`.
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
#:   :func:`stale_pin_problems` exists to catch, and it caught these.
#: - ONE PATH DELIBERATELY NOT CREATED, QUOTED RATHER THAN CITED. ADR 0010
#:   records the decision that the item-notes family gets no index file of that
#:   name, and it names the path in order to say so. This is trap 4 in the
#:   bare-path arm: a record whose evidence is that the target is absent would
#:   be punished for being right.
#: - ONE OF THIS MODULE'S OWN, which is the self-infliction the section warns
#:   about arriving anyway. A docstring here explains a synthetic corpus by
#:   naming its third member, and that member is metasyntactic by construction.
#:   Recorded rather than reworded, because the sentence is precise and the
#:   alternative - describing the member without naming it - trades a checked
#:   record for vaguer prose.
BARE_PATH_REASONS: Final[Mapping[tuple[str, str, str], BarePathReason]] = {
    (
        "docs/adr/0010-item-notes-is-an-index-over-per-phase-leaves.md",
        bare_path("docs", "item_notes", "README.md"),
        "## Decision",
    ): BarePathReason(
        "QUOTED, NOT CITED. The ADR's decision is that this path is deliberately not"
        " created, and it names the path in order to record that. Trap 4, in this arm.",
        1,
    ),
    (
        "docs/item_notes/phase4.md",
        bare_path("clockspeed", "advisor", "ledger.py"),
        "### detail - relocated from `docs/history_notes.md` 2026-08-23",
    ): BarePathReason("the same planned phase 5 module, named by the leaf that plans it.", 1),
    (
        "docs/item_notes/phase5.md",
        bare_path("clockspeed", "advisor", "ledger.py"),
        "### detail - relocated from `docs/history_notes.md` 2026-08-23",
    ): BarePathReason("the same planned phase 5 module, named by the leaf that plans it.", 1),
    (
        THIS_MODULE,
        bare_path("docs", "prose.md"),
        "test_a_doc_carrying_no_citation_is_asked_for_neither_a_guard_nor_a_record",
    ): BarePathReason(
        "this module's own metasyntactic corpus member, named by the docstring that"
        " explains what the corpus is for. It is supposed not to exist.",
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
BARE_PATH_REASON_CEILING: Final = 4

#: The floor under the live population, so the live arm cannot pass on nothing.
#: An `assert not problems` is byte-identical whether the property holds or
#: whether the corpus was empty, and this section's population is assembled by
#: a regex over an injected mapping - two places it could silently become
#: empty.
#:
#: HOW THE NUMBER WAS CHOSEN, because the first one was chosen by feel and was
#: slack by a quarter. The population measured 2009 sites over 231 carriers, and
#: its LARGEST single carrier - the append-only ledger, where a dead citation is
#: likeliest to arrive - contributes 482 of them. A floor of 1500 therefore
#: absorbed the total loss of that carrier in silence, which is the one loss the
#: floor most needed to catch. This one sits above 2009 minus that carrier, so
#: losing ANY single carrier reddens, and it still leaves about a hundred sites
#: of ordinary churn before an edit spends an adjudication.
BARE_PATH_POPULATION_FLOOR: Final = 1900

#: EVERY FORGIVENESS TABLE IN THIS MODULE, and the contract that BOUNDS it.
#: CLOSING THE CLASS RATHER THAN THE INSTANCE, which is the fault three
#: consecutive repairs here have reproduced one level up: a hole is filed, the
#: instance is fixed, and the NEXT table of the same shape arrives unbounded.
#: A contract below walks this module's own globals and fails on any container
#: that is in neither this mapping nor :data:`NOT_A_FORGIVENESS`, so a SIXTH
#: escape hatch is red until somebody answers for it.
#:
#: THE CEILING OF THE MECHANISM, STATED: adding a name to
#: :data:`NOT_A_FORGIVENESS` with a false reason still silences it. What cannot
#: be done is adding one SILENTLY - the entry sits in the diff as a sentence
#: somebody has to defend, which is the same bound
#: :func:`forgiveness_budget_problems` claims for itself and no more.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {
    "DISPOSITIONS": "test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow",
    "UNVERIFIED_LINE_POINTERS": "test_the_forgiveness_budget_is_spent_exactly_and_cannot_grow",
    "UNFORBIDDEN_LINE_POINTERS": (
        "test_the_unforbidden_line_pointer_residual_is_pinned_in_both_directions"
    ),
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
}

#: The other half of the same walk: every module-scope container that forgives
#: NOTHING, with the reason it does not. Recorded rather than filtered out,
#: because a filter is a boundary nobody re-derives and a new table that
#: happens to match it joins the unbounded set in silence - which is this
#: module's founding finding, arriving for the fourth time.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "GUARDED_DOCS": "widens what is adjudicated; adding to it can only add findings",
    "ITEM_NOTES_LEAVES": "derived from the filesystem, and widens GUARDED_DOCS",
    "JUDGED_SHAPES": "widens what counts as a citation; adding to it can only add findings",
    "LADDER_RUNGS": "the ladder's rung names, in order",
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
    "_CORPUS": "a synthetic corpus a control judges against",
    "_MD_CORPUS": "a synthetic corpus a control judges against",
    "_ONE_SHAPE_EACH": "a synthetic corpus a control judges against",
    "_LANDING_CORPUS": "a synthetic corpus a control judges against",
    "_LANDING_SOURCE": "a synthetic corpus a control judges against",
    "_REDIRECT_KEY": "one synthetic key a control judges against",
    "_FILED_CERT_LINES": "the CS-889 acceptance reconstruction's line numbers",
    "_FILED_ENV_LINES": "the CS-889 acceptance reconstruction's line numbers",
    "_FILED_BARE_PATH_CARRIERS": "the CS-891 reconstruction's carriers and site counts",
    "_CONTROL_SOURCE_ROOTS": "two directory names a control hands the ladder as R1's roots",
    "_INTERPRETER_NAMES": "the three names the interpreter installs, excluded by exact match",
}


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
    so - that is, when it holds ANY member of :data:`JUDGED_SHAPES`, in any of
    its spellings, judged on the whole text rather than the scoped part: a
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


# --- the shape a pin over a FILE has to be checked for -----------------------


def literal_pin_problems(source: str, name: str) -> list[str]:
    """Whether a named module-scope mapping's values are all TYPED INTEGERS.

    THE PERMANENT DISARM, ONE SHAPE OVER FROM THE ONE
    :func:`derived_bound_problems` closes. That function catches a bound whose
    expression MENTIONS the table it bounds, which is the whole attack against
    a ceiling over a table. A pin over a FILE has no table to mention:
    ``_ROT_PATH: len(bare_path_problems(answered))`` computed at import time,
    or any call at all, would make :data:`ARCHIVE_ROT` agree with the
    derivation by construction and leave NO NUMBER in the diff to query. So the
    question asked here is not provenance but SHAPE - every value must be an
    integer somebody typed.

    THE ABSENT NAME IS A FINDING, NOT A SILENCE. An empty problem list reads
    identically whether the pin is clean or whether it has been renamed out
    from under this check, which is the vacuity fault this module has paid for
    twice.

    SO IS A SECOND BINDING, and that took two statements to disarm rather than
    one: a typed decoy the walk stops at, then a later module-scope rebind to a
    call. The source still reads as typed, the runtime value is computed, and
    no number moves anywhere. So EVERY module-scope binding of the name is
    collected rather than the first one answering for all of them, more than
    one is itself a finding, and a binding that is not a mapping literal is a
    finding rather than something to step past.

    Args:
        source: The module text to parse.
        name: The module-scope name the pin is bound to.

    Returns:
        One line per value that is not a typed integer, one per binding that is
        no mapping literal, one more if the name is bound more than once, or
        one saying the name is not bound at module scope at all.
    """
    bound: list[ast.expr] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.AnnAssign):
            targets: list[ast.expr] = [node.target]
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
        else:
            continue
        if node.value is not None and any(
            isinstance(t, ast.Name) and t.id == name for t in targets
        ):
            bound.append(node.value)
    if not bound:
        return [
            f"no module-scope mapping named {name} was found, so this check measured"
            " nothing and its clean answer is about no pin at all."
        ]
    problems: list[str] = []
    if len(bound) > 1:
        problems.append(
            f"{name} is bound {len(bound)} times at module scope, so the literal a"
            " reader checks is not the value the module ends up with."
        )
    for value in bound:
        if not isinstance(value, ast.Dict):
            problems.append(
                f"{name} is bound at module scope to {ast.unparse(value)}, which is no"
                " mapping literal, so that binding types no value of this pin at all."
            )
            continue
        problems += [
            f"{name} carries a value that is not a typed integer: {ast.unparse(item)}."
            " A pin computed from what it measures agrees by construction, spends"
            " nothing, and leaves no number in the diff for anybody to defend."
            for item in value.values
            # A bool IS an int to isinstance, and `True` is not a count.
            if not (isinstance(item, ast.Constant) and type(item.value) is int)
        ]
    return problems


# --- the live corpus --------------------------------------------------------


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


def test_the_guarded_set_covers_every_doc_the_bare_path_shape_makes_a_carrier(
    markdown_texts: Mapping[str, str],
) -> None:
    """CS-891 - the population was widened BEFORE the arm, and this is what it bought.

    EVERY SHAPE THAT PREDATES THIS ITEM NEEDS A SEPARATOR - a name after "::",
    or a number after a colon - so a doc that spells a repo-relative path and
    nothing else was not a carrier and had never had to be guarded. A shape
    that reads the bare path makes a whole population of docs carriers in ONE
    step, so the widening shipped in a change that added no shape: the arm's
    first run could then be blamed on the arm rather than on the population, and
    the population's on the population.

    IT NOW MEASURES THE SHIPPED PATTERN rather than a local probe of it. While
    the shape did not exist, a probe was the only way to ask; asking the probe
    AFTER the shape shipped would be asserting that two patterns agree, which
    is a weaker claim than the one this contract is for and would go quietly
    stale the moment the shipped one moved.

    THE SEPARATOR IS REQUIRED, and that is trap 2 rather than a preference. An
    unqualified basename resolved repo-relative and then called missing
    MANUFACTURES findings - a census that did it reported six dead targets and
    all six were artifacts.
    """
    older = tuple(shape for shape in JUDGED_SHAPES if shape is not BARE_PATH_RE)

    assert len(older) == len(JUDGED_SHAPES) - 1, (
        "BARE_PATH_RE is not among the shapes the boundary reads, so the split below "
        "is between two identical sets and reports nothing"
    )
    newly = sorted(
        doc
        for doc, text in markdown_texts.items()
        if BARE_PATH_RE.search(text) and not any(shape.search(text) for shape in older)
    )

    assert newly, (
        "no in-domain doc is made a carrier by the bare-path shape alone, so this "
        "contract measures an empty population and would pass whatever went unguarded"
    )
    unguarded = [doc for doc in newly if doc not in GUARDED_DOCS]
    assert not unguarded, (
        "docs the bare-path shape makes carriers that nothing guards:\n"
        + "\n".join(f"  {doc}" for doc in unguarded)
        + "\nGuard them, so the arm that reads the shape needs no second widening."
    )

    # THE SPLIT IS PROVED TO BE REAL, not assumed. Withholding precisely the new
    # members must report precisely them back: none was a carrier under the
    # older shapes, so any other answer means the boundary is not reading the
    # fifth one and the clean result below would be about nothing.
    withheld, _stale = guarded_set_problems(
        markdown_texts, [doc for doc in GUARDED_DOCS if doc not in newly], UNGUARDED_DOCS
    )
    assert withheld == newly, (
        "withholding the new members did not report them back, so the boundary never "
        "reached the fifth shape and the check below measures nothing"
    )

    unrecorded, stale = guarded_set_problems(markdown_texts, GUARDED_DOCS, UNGUARDED_DOCS)

    assert (unrecorded, stale) == ([], []), (
        "the boundary is not clean now that the bare-path shape is read:\n"
        + "\n".join(f"  unrecorded {doc}" for doc in unrecorded)
        + "\n".join(f"  stale {problem}" for problem in stale)
    )


# --- contract 2: the disposition table cannot accumulate false declarations --


def disposition_texts(carriers: Mapping[str, str]) -> dict[str, str]:
    """Every text a recorded disposition may be keyed against.

    THE GUARDED DOCS ALONE WERE NOT ENOUGH, and the gap was found by attacking
    this module rather than by reading it. The two graders below built their
    corpus from :data:`GUARDED_DOCS`, which is the CITATION population - so a
    disposition keyed on any other carrier counted ZERO sites and was reported
    stale on arrival. Harmless while the line-pointer arm read only docs and
    Python; a live obstruction once it read every tracked file, because the
    repair path for a finding in a ``.toml`` or a ``.js`` file runs through
    exactly such a record.

    Args:
        carriers: The line-pointer carrier population.

    Returns:
        Carrier path to the text its citations are counted in. Guarded docs
        keep their scoped text, which is what the citation arms adjudicate.
    """
    texts = dict(carriers)
    for doc in GUARDED_DOCS:
        texts[doc] = scoped_text(doc, doc_text(doc))
    return texts


def test_every_recorded_disposition_is_still_in_use(
    sources: Mapping[str, str], line_pointer_carriers: Mapping[str, str]
) -> None:
    """An entry that stopped being needed is a false declaration waiting to happen.

    Checked in the direction an exemption table normally is NOT. A citation that
    was repaired, or a doc that stopped carrying it, leaves an entry here that
    forgives something no longer present - and the next citation that happens to
    match it is forgiven silently. This repository has an open item about
    exactly that shape, so the table is built with the check from the start.
    """
    texts = disposition_texts(line_pointer_carriers)
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


def test_every_recorded_disposition_covers_exactly_the_sites_it_records(
    line_pointer_carriers: Mapping[str, str],
) -> None:
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
    texts = disposition_texts(line_pointer_carriers)

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
# shapes judged AT THE TIME did not make a doc a carrier at all - including the
# elided one, added to this module in the same change that left the boundary
# blind to it. Each corpus below carries exactly ONE shape and nothing else, so
# a predicate that reads only some of them fails on the ones it cannot see.
#
# THE COUNT IS DELIBERATELY NOT RESTATED HERE. There is one entry per member of
# :data:`JUDGED_SHAPES` and the contract below derives the membership, so a
# sentence naming a number would be the fact restated in the one place nothing
# checks it - which is the fault the arm two functions down had to be repaired
# for when the fifth shape arrived.

_ONE_SHAPE_EACH: Final = {
    "docs/elided_only.md": "Verification: `::test_a_name_that_is_not_bound_anywhere`.\n",
    "docs/bare_only.md": 'Verification: `grep -c "test_a_name_that_is_not_bound_anywhere" x`\n',
    "docs/line_only.md": "see `tools/thing.py:900`\n",
    "docs/path_only.md": "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n",
    # THE ONLY MEMBER NAMING A PATH THAT RESOLVES, and the reason is a
    # measurement rather than a preference. Carrier-hood does not depend on
    # resolution, so a synthetic path would serve this corpus equally - but
    # this module is itself a bare-path carrier, and a synthetic one here is a
    # site the R4 rung then declines and the R4 disclosure must then record.
    # It did, on the first run. A disclosure of the tree's real residual should
    # not be carrying a line about one of this module's own fixtures.
    "docs/bare_path_only.md": "see `tools/drift_guard.py` for the rule\n",
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

    Fixing the shapes by hand would leave the NEXT arm to fall out of the
    boundary exactly the way the elided arm did - a new pattern is added, an arm
    is taught to read it, and nothing says the boundary must learn it too. So
    the check is not "are these N there", it is "does anything this module
    compiles sit outside :data:`JUDGED_SHAPES`". A new ``*_RE`` is red until it
    is answered one way or the other.

    IT HAS SINCE BEEN COLLECTED ON, which is worth recording because a contract
    written against a hypothetical usually is not. CS-891 added the fifth
    pattern, and this arm was red on it until the boundary was told - the
    prediction above naming the FIFTH arm specifically, and the widening
    arriving exactly there. The same derivation is what
    ``test_every_container_this_module_holds_is_bounded_or_recorded_as_forgiving_nothing``
    does one level up for the tables rather than the patterns.
    """
    compiled = module_patterns(globals())

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

    THE MEASURED RESIDUAL WENT FROM ZERO TO REAL, AND THIS SENTENCE IS THE
    REPAIR RATHER THAN THE RECORD. It used to read "no tracked ``.claude/*.md``
    carries any judged shape today, so the exclusion currently suppresses
    NOTHING", and it was true of a module that judged four shapes, all of which
    needed a separator after the path. CS-891's bare-path shape falsified it in
    one step: harness prose names module and tool paths constantly. So the
    residual is now MEASURED here every run instead of being asserted in prose,
    because a disclosure nobody re-derives is exactly what this module keeps
    being repaired for - and the number this exclusion suppresses is one that
    only grows.

    WHAT THAT COSTS, STATED: a dead path spelled in tracked harness
    configuration is invisible to every arm here. That is the accepted price of
    the rule, not a gap in it. ``.claude/`` is Claude Code configuration, it
    appears nowhere in the CLAUDE.md doc-topology table, and its prose
    instructs an agent rather than recording a verification.
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
    harness_markdown = [p for p in tracked if p.startswith(OUT_OF_DOMAIN) and p.endswith(".md")]

    assert harness_markdown, (
        "nothing under .claude/ is tracked markdown, so OUT_OF_DOMAIN excludes nothing and "
        "should be deleted rather than left standing as a rule about an empty set"
    )
    suppressed = [
        path
        for path in harness_markdown
        if carries_a_citation((REPO_ROOT / path).read_text(encoding="utf-8", errors="replace"))
    ]

    assert suppressed, (
        "no tracked harness markdown carries any judged shape, so the exclusion "
        "suppresses nothing and this arm is a rule about an empty set of pointers. "
        "That WAS true while every shape needed a separator after the path; if it is "
        "true again, a shape has stopped matching."
    )


def test_the_domain_excludes_the_dated_archive(tracked: list[str]) -> None:
    """Dated material is out of every search for current truth, this one included.

    THE TWO POPULATIONS DISAGREED. :func:`line_pointer_carriers` has skipped
    :data:`DATED_ARCHIVE` since it was built and :func:`in_domain` did not, so
    the same archived file sat outside one arm's population and inside the
    other's. It cost nothing while every judged shape needed a separator after
    the path - the one archived file spells no such pointer - and it would cost
    the moment a shape reads the bare path, by pulling a dated artifact into
    the guarded set that CLAUDE.md section 4 excludes from search.

    BOTH DIRECTIONS, AND THE ARCHIVE IS ASSERTED NON-EMPTY. A rule about an
    empty set reads as coverage and is not: an exclusion with nothing to
    exclude passes however it is broken. The tracked archive is measured here
    so the exclusion cannot be satisfied vacuously.
    """
    assert not in_domain(f"{DATED_ARCHIVE}planted.md"), (
        "a dated artifact reached the documentation domain, so guarding every "
        "carrier would guard the archive CLAUDE.md section 4 excludes"
    )
    assert in_domain("docs/planted.md"), (
        "the same name one directory up was excluded too, so the predicate "
        "rejects live documentation rather than dated material"
    )

    archived = [p for p in tracked if p.startswith(DATED_ARCHIVE) and p.endswith(".md")]

    assert archived, (
        "no dated markdown is tracked, so DATED_ARCHIVE excludes nothing and should be "
        "deleted rather than left standing as a rule about an empty set"
    )
    admitted = [p for p in archived if in_domain(p)]
    assert not admitted, "tracked dated markdown reached the documentation domain:\n" + "\n".join(
        f"  {p}" for p in admitted
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

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

    assert len(empty) == 1, f"a pointer at a blank line was not reported: {empty}"
    assert forbidden == [], "a blank landing was reported as a forbid-leg finding instead"


def test_a_pointer_landing_on_a_lone_bracket_is_reported() -> None:
    """Punctuation is not a declaration, and a closing bracket is the common case."""
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 4), _LANDING_CORPUS)

    empty, _forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

    assert len(empty) == 1, f"a pointer at a bracket-only line was not reported: {empty}"


def test_the_emptiness_leg_is_green_on_a_pointer_that_lands_on_prose() -> None:
    """WHY LEG 1 ALONE IS REFUTED, pinned so it cannot be quietly dropped.

    CS-889's primary target landed on a docstring line roughly eighty lines
    above the declaration its sentence claimed. The line was neither blank nor
    punctuation, so an emptiness check is GREEN on it - which is exactly the
    measurement that made the forbid leg necessary rather than optional.
    """
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

    assert empty == [], "the emptiness leg claimed a finding it cannot honestly make"
    assert len(forbidden) == 1, f"the forbid leg missed what the emptiness leg passes: {forbidden}"


def test_a_grandfathered_pointer_is_forgiven_by_the_forbid_leg_and_not_by_the_other() -> None:
    """The baseline claims nothing about content, so it cannot answer blankness."""
    prose = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)[0]
    blank = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 3), _LANDING_CORPUS)[0]
    body = _LANDING_CORPUS[_SYNTHETIC_MODULE]
    pinned = {
        ("ROADMAP.md", _SYNTHETIC_MODULE, 5): landing_digest(body[4]),
        ("ROADMAP.md", _SYNTHETIC_MODULE, 3): landing_digest(body[2]),
    }

    assert line_pointer_content_problems(prose, [], {}, {}, pinned) == ([], [])
    empty, forbidden = line_pointer_content_problems(blank, [], {}, {}, pinned)
    assert len(empty) == 1, "a pinned pointer that went blank was forgiven, and it must not be"
    assert forbidden == []


def test_a_recorded_redirect_whose_target_resolves_forgives_the_pointer() -> None:
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5))
    table = {key: Disposition(MOVED, f"{_SYNTHETIC_MODULE}::_live_target", "the target is live", 1)}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    assert line_pointer_content_problems(py_sites, other, _LANDING_SOURCE, table, {}) == ([], [])


def test_a_recorded_redirect_whose_target_stopped_resolving_is_reported() -> None:
    """A record that points at nothing forgives nothing, on the new arm too."""
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5))
    table = {key: Disposition(MOVED, f"{_SYNTHETIC_MODULE}::_gone_now", "the target rotted", 1)}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    _empty, forbidden = line_pointer_content_problems(py_sites, other, _LANDING_SOURCE, table, {})

    assert len(forbidden) == 1, "a redirect at a dead target was accepted"
    assert "does not resolve" in forbidden[0]


def test_a_record_forgives_a_blank_landing_that_the_baseline_may_not() -> None:
    """An ADJUDICATED answer silences both legs; that is what adjudication buys."""
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 3))
    table = {key: Disposition(NO_TARGET, "", "the carrier is append-only", 1)}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 3), _LANDING_CORPUS)

    assert line_pointer_content_problems(py_sites, other, {}, table, {}) == ([], [])


def test_a_pointer_at_a_tracked_non_python_file_is_not_forbidden() -> None:
    """No symbol form exists there, so forbidding would leave no way to cite it."""
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_DOC, 2), _LANDING_CORPUS)
    _empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

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

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

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
    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

    assert len(py_sites) == len(_FILED_CERT_LINES) + len(_FILED_ENV_LINES), (
        f"the plant did not reconstruct all five filed pointers: {py_sites}"
    )
    assert len(empty) == len(_FILED_ENV_LINES), (
        f"the two pointers at blank lines were not both reported: {empty}"
    )
    assert len(forbidden) == len(_FILED_CERT_LINES), (
        f"the three pointers at live lines were not all reported: {forbidden}"
    )


# --- contract 6: CS-889 repair - the escape hatch must ratchet ---------------


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


def test_appending_a_pin_is_itself_a_finding() -> None:
    """The adversary's exact move, reproduced against a synthetic budget."""
    pins = {("ROADMAP.md", _SYNTHETIC_MODULE, 5): "deadbeefcafe"}

    assert forgiveness_budget_problems(pins, {}, 1) == []

    appended = dict(pins)
    appended[("ROADMAP.md", _SYNTHETIC_MODULE, 4)] = "0123456789ab"
    problems = forgiveness_budget_problems(appended, {}, 1)

    assert len(problems) == 1, "appending a pin was not reported"
    assert "2 forgivenesses recorded against a ceiling of 1" in problems[0]


def test_appending_a_fabricated_disposition_is_itself_a_finding() -> None:
    """The other half of that attack, which counting the pin alone would miss.

    A ``NO_TARGET`` record names nothing to verify, so no check can call its
    reason false. What the budget removes is adding one SILENTLY.
    """
    table = {("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5)): Disposition(NO_TARGET, "", "x", 1)}

    assert forgiveness_budget_problems((), table, 1) == []

    fabricated = dict(table)
    fabricated[("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 4))] = Disposition(
        NO_TARGET, "", "looks plausible and answers nothing", 1
    )
    problems = forgiveness_budget_problems((), fabricated, 1)

    assert len(problems) == 1, "a fabricated disposition was absorbed by the budget"
    assert "ceiling of 1" in problems[0]


def test_a_ceiling_left_slack_after_a_repair_is_reported() -> None:
    """Slack is banked room for an append nobody has to defend."""
    problems = forgiveness_budget_problems((), {}, 3)

    assert len(problems) == 1, "a slack ceiling was accepted"
    assert "Lower it to 0" in problems[0]


# --- contract 7: the pin must not FOLLOW THE ROT ----------------------------


def test_a_pinned_pointer_whose_line_has_moved_under_it_is_reported() -> None:
    """THE REFUTATION THAT EARNED THE ANCHOR.

    A pin keyed on ``(carrier, path, line)`` alone is immunised against
    detection rather than merely unexamined: edit anything above it and the
    pointer keeps the identical key while naming a different declaration. The
    digest is a CHANGE claim, not a correctness claim, which is why it is
    affordable where a content-anchored resolver was not.
    """
    carriers = _planted(_SYNTHETIC_MODULE, 5)
    py_sites, other = line_pointer_sites(carriers, _LANDING_CORPUS)
    landing = _LANDING_CORPUS[_SYNTHETIC_MODULE][4]
    site = ("ROADMAP.md", _SYNTHETIC_MODULE, 5)

    honest = {site: landing_digest(landing)}
    assert line_pointer_content_problems(py_sites, other, {}, {}, honest) == ([], [])

    rotted = {site: landing_digest("what this line used to say")}
    _empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, rotted)

    assert len(forbidden) == 1, "a pin whose line moved under it was still forgiven"
    assert "THE LINE HAS MOVED UNDER IT" in forbidden[0]


def test_the_anchor_ignores_a_reindent_but_not_a_rewrite() -> None:
    """Stripped before hashing, so a whitespace sweep does not spend an adjudication."""
    assert landing_digest("    x = 1") == landing_digest("\t\tx = 1  ")
    assert landing_digest("x = 1") != landing_digest("x = 2")


def test_every_live_pin_anchors_a_line_that_is_still_there(
    live_line_pointers: tuple[list[tuple[str, str, int, str]], list[tuple[str, str, int, str]]],
) -> None:
    """The anchor, asserted on the real corpus rather than only on a plant."""
    py_sites, _other = live_line_pointers
    landings = {(c, p, ln): text for c, p, ln, text in py_sites}

    drifted = [
        f"{carrier} -> {path} line {line}"
        for (carrier, path, line), pinned in sorted(UNVERIFIED_LINE_POINTERS.items())
        if (carrier, path, line) in landings
        and landing_digest(landings[(carrier, path, line)]) != pinned
    ]

    assert not drifted, "pins whose target line has moved under them:\n" + "\n".join(
        f"  {row}" for row in drifted
    )


# --- contract 8: line zero, and the widened carrier boundary -----------------


def test_a_line_zero_pointer_is_not_judged_against_the_last_line() -> None:
    """LATENT, NOT LIVE, and silent - which is why it is guarded anyway.

    Files number from 1, so a ``:0`` pointer names no line. The range test
    refuses only numbers ABOVE the end, and indexing at ``line - 1`` on zero
    hands back the LAST line of the target - so both legs would judge the
    pointer while quoting the wrong line as evidence.
    """
    last = _LANDING_CORPUS[_SYNTHETIC_MODULE][-1]
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 0), _LANDING_CORPUS)

    assert [landing for _c, _p, _ln, landing in py_sites] != [last], (
        "a :0 pointer was judged against the last line of the target"
    )

    empty, forbidden = line_pointer_content_problems(py_sites, other, {}, {}, {})

    assert len(empty) == 1, f"a :0 pointer was not reported as naming nothing: {empty}"
    assert forbidden == [], "a :0 pointer reached the forbid leg"


def test_the_carrier_population_is_every_tracked_file_less_the_recorded_ones(
    line_pointer_carriers: Mapping[str, str], tracked: list[str]
) -> None:
    """THE BOUNDARY, ASSERTED RATHER THAN DESCRIBED.

    The first build read markdown plus Python and justified the Python half
    with an argument that applied verbatim to every other extension. It cost a
    live defect in a JavaScript test and a pointer in ``pyproject.toml`` at a
    ``(path, line)`` pair already pinned under a doc carrier. Completeness by
    construction is what stops a third repeat: no suffix list to keep in sync,
    so no extension can start carrying a pointer in silence.
    """
    expected = {
        path
        for path in tracked
        if path not in UNGUARDED_DOCS and not path.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
    }
    missing = sorted(expected - set(line_pointer_carriers))
    extra = sorted(set(line_pointer_carriers) - expected)

    assert not missing, f"tracked files no line-pointer arm reads: {missing[:10]}"
    assert not extra, f"carriers outside the tracked set: {extra[:10]}"


def test_the_recorded_exemptions_are_the_only_files_the_line_arm_declines(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """The negative controls, on the LIVE population rather than assumed."""
    intruders = sorted(
        carrier
        for carrier in line_pointer_carriers
        if carrier in UNGUARDED_DOCS or carrier.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
    )

    assert not intruders, f"carriers read from outside the stated boundary: {intruders}"


# --- contract 9: CS-891 - the bare path is judged, and each decline is a rule -

#: How many `docs/ARCHITECTURE.md` paths the ladder must ANSWER - at any rung
#: that resolves - before that arm's empty finding list is an answer rather than
#: silence. 33 do today: 28 at R0 and 5 at R1.
#:
#: THIS FLOOR USED TO COUNT R1 ALONE, AND THAT WAS THE WRONG SUBJECT. It read
#: ``_ARCHITECTURE_SUFFIX_FLOOR: Final = 8`` against ten R1 hits, two rows of
#: slack under a census. CS-928 deleted five of those ten and the floor called
#: an improvement a regression. WHAT THE FIVE WERE, measured rather than
#: assumed: `data/registry.py` and `save/world.py` under Pillar 3 and again
#: under Pillar 4, and `solve/power.py` under Pillar 1. All five were inside
#: "**Implemented by:**" sentences attributing pillars 3 and 4 to `audit/` and
#: `progress/`, which hold a package docstring each and no code. Deleting a
#: false attribution is the repair working. A vacuity floor that reddens when
#: one lands is measuring the wrong thing.
#:
#: A HYPOTHESIS THIS REFUTES, recorded because it is the plausible wrong answer.
#: The five were NOT re-spelled fully qualified and promoted to R0. R0 did rise
#: by five over the same edit, but by six arrivals less one departure, and not
#: one of the six is a re-spelling of a lost R1 path: they are
#: `clockspeed/surface/api/pending.py`, four phase-gate test modules under
#: section 3.1, and `tests/test_architecture_attributions.py`. Nothing moved
#: rungs. Five citations were deleted because the claims around them were
#: false, and five more arrived elsewhere for unrelated reasons.
#:
#: WHY THE SUBJECT IS "RESOLVES AT ALL". The arm's finding list is
#: AMBIGUOUS_SUFFIX plus UNRESOLVED, and an empty one is only an answer if the
#: ladder read a real population out of this doc. That population is every path
#: it ANSWERED, whichever rung answered it. Counting one rung made the floor
#: hostage to which SPELLING the prose happens to use, so every future repair
#: that deletes a suffix-spelled citation would demand another lowering, and a
#: floor lowered on each repair reaches zero while staying green - which is the
#: defect :func:`floor_problems` exists to prevent, arrived by instalments.
#:
#: TWELVE, AND THE TWO NUMBERS IT SITS BETWEEN. Section 1.1's module map alone
#: answers 17 - one row per module, a table rather than prose, so it cannot
#: shrink far without the doc ceasing to be a module map. Every way the reader
#: can fail produces 0 or near it: a carrier dropped from the population, a
#: regex that stops matching, an empty tracked set. 12 is five rows under the
#: structural core and an order of magnitude over the failure mode, so ordinary
#: prose churn cannot reach it and a collapse cannot miss it.
#:
#: R1 IS STILL ASSERTED ON THIS DOC, as a bare non-empty check in the arm
#: itself. A number there is what went wrong; a floor of one is not a budget
#: anybody can shave.
_ARCHITECTURE_RESOLVED_FLOOR: Final = 12

#: How many bare paths this module must spell of its own before the
#: self-infliction arm's clean answer is worth anything. Measured well above
#: this when the arm shipped.
_SELF_SPELLED_FLOOR: Final = 20

#: A leaf name this tree does not carry, for the plants below. ASSEMBLED into a
#: path at call time by :func:`bare_path`, never spelled whole, so the plant
#: cannot become a finding this module makes against itself.
_BARE_PLANT_LEAF: Final = "a-path-this-tree-does-not-carry.md"

#: R1's candidate roots for the controls that need the rung to FIRE. Directory
#: names rather than paths, so nothing here is a citation. The controls that do
#: not exercise R1 pass an empty set instead, which states that they do not.
_CONTROL_SOURCE_ROOTS: Final = ("clockspeed", "shell")


def _planted_bare(carrier: str, cited: str) -> dict[str, str]:
    """A one-carrier corpus spelling ``cited`` once, in the shape the arm reads."""
    return {carrier: f"## Heading\n\nsee `{cited}` for the rule\n"}


def test_every_bare_path_in_the_carrier_population_resolves_or_is_recorded(
    live_bare_path_sites: Sequence[BarePathSite],
    live_bare_path_ladder: Mapping[str, Sequence[BarePathSite]],
) -> None:
    """CS-891's acceptance, on the live tree.

    THE POPULATION IS ASSERTED BEFORE THE ZERO. An `assert not problems` reads
    identically whether the property holds or whether nothing was measured, and
    this section has two places the population could silently empty: a pattern
    that stops matching, and a carrier mapping that arrives empty. So the floor
    comes first and the emptiness second.
    """
    short = floor_problems("bare-path sites", len(live_bare_path_sites), BARE_PATH_POPULATION_FLOOR)

    assert not short, "\n".join(short)

    problems = bare_path_problems(live_bare_path_ladder)

    assert not problems, "bare paths that neither resolve nor carry a reason:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def test_the_bare_path_population_is_the_line_pointer_population(
    live_bare_path_sites: Sequence[BarePathSite],
    line_pointer_carriers: Mapping[str, str],
    file_lines: Mapping[str, Sequence[str]],
    tracked: list[str],
) -> None:
    """The boundary, asserted rather than described - and in both directions.

    THE NAME WAS AN EQUALITY THIS ARM DID NOT CHECK. It computed
    ``carriers - line_pointer_carriers`` and never the reverse, so a DROPPED
    carrier reddened nothing: VERIFIED by removing `docs/LEDGER.md` - 482 of
    2009 sites, and the append-only file where a dead citation is likeliest to
    arrive - with the suite green. With a floor left slack by a quarter, up to
    509 sites could vanish in silence.

    SO THE REVERSE DIRECTION IS DERIVED FROM THE INDEX, NOT THE FIXTURE. Asking
    the fixture which carriers it holds re-asserts the fixture: a ledger dropped
    there is missing from BOTH sides and the comparison is green on nothing. The
    expectation is rebuilt from `git ls-files`, the RECORDED exclusions and the
    shape, so a carrier that stops being offered disagrees with the tree rather
    than with a copy of the same mistake. The exclusions are measured non-empty
    because a rule about an empty set reads as coverage and is not.
    """
    carriers = {site.carrier for site in live_bare_path_sites}

    assert carriers, "no carrier spells a bare path, so the boundary below is vacuous"
    outside = sorted(carriers - set(line_pointer_carriers))
    assert not outside, f"bare paths read from outside the line-pointer population: {outside}"

    offered = {
        path
        for path in tracked
        if path in file_lines
        and path not in UNGUARDED_DOCS
        and not path.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
        and BARE_PATH_RE.search(scoped_text(path, NEWLINE.join(file_lines[path])))
    }

    assert offered, "the index offers no bare-path carrier at all, so the reverse leg is vacuous"
    dropped = sorted(offered - carriers)
    assert not dropped, (
        "tracked files spell a bare path and never reached the population:"
        + NEWLINE
        + NEWLINE.join(f"  {path}" for path in dropped)
        + NEWLINE
        + "The carrier mapping has stopped offering a file the boundary says it covers."
    )

    excluded = [
        path
        for path in tracked
        if path in UNGUARDED_DOCS or path.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
    ]
    assert excluded, "the recorded exclusions match no tracked file, so excluding them is vacuous"
    spelled = [
        path
        for path in excluded
        if BARE_PATH_RE.search((REPO_ROOT / path).read_text(encoding="utf-8", errors="replace"))
    ]
    assert spelled, (
        "no excluded file spells a bare path at all, so this arm's exclusion suppresses"
        " nothing and proves nothing about the boundary"
    )
    assert not (carriers & set(excluded)), (
        f"an excluded file reached the bare-path population: {sorted(carriers & set(excluded))}"
    )


def test_the_bare_path_ladder_answers_every_site_exactly_once(
    live_bare_path_sites: Sequence[BarePathSite],
    live_bare_path_ladder: Mapping[str, Sequence[BarePathSite]],
) -> None:
    """The distribution is auditable, which is the reason the rungs are named.

    A site that fell out of every bucket, or into two, would leave the totals
    disagreeing - and a ladder whose buckets do not sum to its input is one
    where a rung's `continue` has been lost and some population is being judged
    twice or not at all.
    """
    assert sorted(live_bare_path_ladder) == sorted(LADDER_RUNGS), (
        "the ladder's buckets are not exactly LADDER_RUNGS, so a distribution read "
        "from it would be silent about a rung that has stopped firing"
    )
    answered = sum(len(sites) for sites in live_bare_path_ladder.values())

    assert answered == len(live_bare_path_sites), (
        f"the ladder answered {answered} sites out of {len(live_bare_path_sites)}"
    )
    assert live_bare_path_ladder[RESOLVED_EXACT], (
        "not one bare path resolved exactly, which no live corpus can be true of"
    )


def test_the_ignore_probe_answers_a_declared_path_and_a_tracked_one() -> None:
    """R2's subprocess, probed in BOTH directions on the real repository.

    THIS ARM EXISTS BECAUSE THE RUNG FAILS SILENTLY. Under `text=True` on
    Windows the NUL separator's neighbours are newline-translated on write, git
    receives a path with a trailing carriage return and answers NOT IGNORED for
    every one, so R2 reports zero and every declinable site is promoted to a
    finding needing a reason. Measured: the first run of this ladder under text
    mode produced a reason table twice the size, which looks entirely
    plausible. A rung that can stop firing needs a probe that fails when it
    does, not a reader who notices.

    Both directions, because "everything is ignored" is as broken as "nothing
    is" and an arm asserting only the first would pass on it.

    A DECLARED PATH AT BOTH ENDS OF THE BATCH, AND THAT WAS MEASURED RATHER
    THAN REASONED ABOUT. The first build of this arm probed one declared path
    and one tracked one, and a mutant that appended a carriage return to the
    LAST element of the batch SURVIVED it - the mangled element was the tracked
    path, whose answer the arm did not depend on. A separator fault can land on
    the first element, the last, or all of them, so the batch carries a
    declared path at both ends and asserts BOTH come back.
    """
    first = bare_path("data", "planted.json")
    last = bare_path("data", "planted-too.json")

    answered = declares_untracked([first, "CLAUDE.md", last])

    missed = sorted({first, last} - answered)

    assert not missed, (
        f"git did not report {missed} as ignored, though they sit under the"
        " generated-artifacts directory. Either the separator reached git mangled - the"
        " CRLF fault this arm exists for - or the repository has stopped declaring that"
        " directory untracked."
    )
    assert "CLAUDE.md" not in answered, (
        "git reported a tracked, unignored file as ignored, so this rung would decline"
        " every citation put to it"
    )


def test_the_architecture_module_map_resolves_by_unique_suffix_not_by_reporting(
    live_bare_path_ladder: Mapping[str, Sequence[BarePathSite]],
) -> None:
    """TRAP 2, IN THIS ARM, AND R1 IS THE ANSWER TO IT.

    `docs/ARCHITECTURE.md` writes a module map whose paths are relative to a
    package root stated in the surrounding table. Resolving them repo-relative
    and calling them missing would report a heap of absences that are artifacts
    of the reader - the same fault that made a census report six dead targets
    of which all six were artifacts. A unique suffix hit at a segment boundary
    answers them without guessing, and the ambiguous case is refused rather
    than resolved.

    ASSERTED ON THE LIVE DOC rather than on a plant, because the claim is about
    this corpus: that this doc's paths are ANSWERED by the ladder and none is
    left ambiguous or dead.

    THE NON-VACUITY SUBJECT IS THE ANSWERED POPULATION, NOT R1's SHARE OF IT.
    See :data:`_ARCHITECTURE_RESOLVED_FLOOR`, which records what counting R1
    alone cost. R1 keeps a non-empty check of its own here so the rung this arm
    is named for is still exercised against the live doc, and it is a bare
    assertion rather than a number precisely because a number is what rotted.
    """
    doc = "docs/ARCHITECTURE.md"
    by_suffix = [site for site in live_bare_path_ladder[RESOLVED_SUFFIX] if site.carrier == doc]
    answered = [
        site
        for rung in (RESOLVED_EXACT, RESOLVED_SUFFIX)
        for site in live_bare_path_ladder[rung]
        if site.carrier == doc
    ]
    unanswered = [
        site
        for rung in (AMBIGUOUS_SUFFIX, UNRESOLVED)
        for site in live_bare_path_ladder[rung]
        if site.carrier == doc
    ]

    short = floor_problems(
        "module-map paths the ladder answers", len(answered), _ARCHITECTURE_RESOLVED_FLOOR
    )

    assert not short, "\n".join(short) + (" This arm is not measuring the population it describes.")
    assert by_suffix, (
        "no path in this doc resolves by unique suffix, so R1 - the rung this arm exists"
        " to assert - is unexercised here and an empty finding list says nothing about it"
    )
    assert not unanswered, "module-map paths the ladder could not answer:\n" + "\n".join(
        f"  {site.cited} under {site.anchor}" for site in unanswered
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_the_bare_path_arm_has_teeth_on_every_guarded_doc(
    doc: str,
    tracked: list[str],
    live_declared_untracked: frozenset[str],
    live_source_roots: frozenset[str],
) -> None:
    """Every guarded doc is REACHED, measured per doc rather than assumed.

    Modelled on the bare-identifier arm's teeth for its reason: a passing arm
    reads the same on a doc that is clean and on a doc nobody looked at, and
    this module has already shipped one arm hardcoded to a single file while
    its siblings were parametrized.

    The plant is in memory. Nothing is written to a tracked doc.
    """
    dead = bare_path("docs", _BARE_PLANT_LEAF)
    planted = scoped_text(doc, doc_text(doc)) + f"\n\nVerification: `{dead}`.\n"

    answered = bare_path_ladder(
        bare_path_sites({doc: planted}),
        tracked,
        live_declared_untracked,
        BARE_PATH_REASONS,
        live_source_roots,
    )

    assert [site.cited for site in answered[UNRESOLVED]] == [dead], (
        f"a dead bare path planted in {doc} was not the single finding, so the arm "
        "does not reach this doc or the doc already carries another"
    )
    assert answered[AMBIGUOUS_SUFFIX] == [], f"{doc} carries an ambiguous suffix as well"


def test_a_planted_dead_bare_path_is_reported_and_the_same_path_resolves_once_tracked() -> None:
    """The control, on a corpus with no filesystem behind it.

    Both directions in one arm, because an arm that only reddens proves the
    subject can speak and not that it is answering the question asked.
    """
    dead = bare_path("docs", _BARE_PLANT_LEAF)
    corpus = _planted_bare(_SYNTHETIC_DOC, dead)

    missing = bare_path_ladder(bare_path_sites(corpus), [LEDGER], (), {}, ())
    problems = bare_path_problems(missing)

    assert len(problems) == 1, f"a planted dead bare path was not the single finding: {problems}"
    assert dead in problems[0]

    present = bare_path_ladder(bare_path_sites(corpus), [LEDGER, dead], (), {}, ())

    assert bare_path_problems(present) == [], "the same path was still reported once tracked"
    assert len(present[RESOLVED_EXACT]) == 1


def test_an_ambiguous_suffix_is_reported_rather_than_resolved() -> None:
    """R1's teeth: EXACTLY ONE hit resolves, more than one is a finding.

    Without this leg R1 is a laundering route - "the reader guessed" would be
    recorded as "the citation resolved", and a citation matching two tracked
    files names neither.
    """
    tail = bare_path("data", "registry.py")
    corpus = _planted_bare(_SYNTHETIC_DOC, tail)
    sites = bare_path_sites(corpus)
    one = bare_path("clockspeed", "data", "registry.py")
    other = bare_path("shell", "data", "registry.py")

    unique = bare_path_ladder(sites, [one], (), {}, _CONTROL_SOURCE_ROOTS)

    assert len(unique[RESOLVED_SUFFIX]) == 1, "a unique suffix hit did not resolve"
    assert bare_path_problems(unique) == []

    ambiguous = bare_path_ladder(sites, [one, other], (), {}, _CONTROL_SOURCE_ROOTS)
    problems = bare_path_problems(ambiguous)

    assert len(ambiguous[AMBIGUOUS_SUFFIX]) == 1, "a second suffix hit was still resolved"
    assert len(problems) == 1, f"an ambiguous suffix was not the single finding: {problems}"
    assert "more than one tracked path" in problems[0]


def test_a_dead_path_is_declined_only_when_the_repo_declares_it_untracked() -> None:
    """R2's teeth, in both directions, with the declaration injected.

    The rung must not swallow a genuinely dead path. Injecting the answer
    rather than shelling out is what lets the negative half exist at all: there
    is no path that git can be relied on to call ignored and unignored at once.
    """
    dead = bare_path("config", "planted.json")
    sites = bare_path_sites(_planted_bare(_SYNTHETIC_DOC, dead))
    owned = [bare_path("config", "ports.json")]

    declared = bare_path_ladder(sites, owned, [dead], {}, ())

    assert len(declared[DECLARED_UNTRACKED]) == 1, "a declared-untracked path was not declined"
    assert bare_path_problems(declared) == []

    undeclared = bare_path_ladder(sites, owned, (), {}, ())

    assert undeclared[DECLARED_UNTRACKED] == []
    assert len(bare_path_problems(undeclared)) == 1, (
        "a dead path the repo does NOT declare untracked was swallowed by the ignore rung"
    )


def test_a_dead_path_is_declined_only_when_its_root_is_one_this_repo_does_not_own() -> None:
    """R3's teeth, in both directions.

    The rung answers a path whose ROOT this repository does not own - a
    metasyntactic example, or a fragment relative to something else. A dead
    path under a root the repo DOES own must fall through to the report.
    """
    owned_root = [bare_path("docs", "LEDGER.md")]
    invented = bare_path("nowhere", "planted.py")
    owned = bare_path("docs", "planted.py")

    outside = bare_path_ladder(
        bare_path_sites(_planted_bare(_SYNTHETIC_DOC, invented)), owned_root, (), {}, ()
    )

    assert len(outside[UNTRACKED_ROOT]) == 1, "a path under an invented root was not declined"
    assert bare_path_problems(outside) == []

    inside = bare_path_ladder(
        bare_path_sites(_planted_bare(_SYNTHETIC_DOC, owned)), owned_root, (), {}, ()
    )

    assert inside[UNTRACKED_ROOT] == []
    assert len(bare_path_problems(inside)) == 1, (
        "a dead path under a root this repo owns was swallowed by the root rung"
    )


def test_a_dead_path_is_declined_in_a_fixture_literal_and_reported_in_a_docstring() -> None:
    """R4's teeth, in both directions, and it is what makes the rung a RULE.

    The same dead path, the same carrier, the same line - one inside a
    non-docstring string literal, one inside a docstring. AST-decidable, so the
    rung is not reading the sentence and guessing at intent; it is asking
    whether the site is data the module operates on or the author talking.
    """
    dead = bare_path("docs", _BARE_PLANT_LEAF)
    owned_root = [bare_path("docs", "LEDGER.md")]
    fixture = f'CORPUS = {{"note": "see `{dead}` here"}}\n'
    prose = f'"""See `{dead}` here."""\n'

    data = bare_path_ladder(bare_path_sites({_SYNTHETIC_MODULE: fixture}), owned_root, (), {}, ())

    assert len(data[FIXTURE_LITERAL]) == 1, "a fixture path in a non-docstring literal was judged"
    assert bare_path_problems(data) == []

    authored = bare_path_ladder(bare_path_sites({_SYNTHETIC_MODULE: prose}), owned_root, (), {}, ())

    assert authored[FIXTURE_LITERAL] == []
    assert len(bare_path_problems(authored)) == 1, (
        "the identical path in a DOCSTRING was declined, so the rung answers author "
        "prose and not only the data a module feeds itself"
    )


#: The leaf name the five originally filed citations spelled. It has never
#: existed in this repository - the lesson it named lives under another leaf -
#: so the five were wrong when written rather than rotted since.
_FILED_BARE_PATH_LEAF: Final = "pooled-guard-hides-its-worst-member.md"

#: The five sites, as carriers and how many each spelled. Reconstructed rather
#: than cited, for the reason the CS-889 acceptance control gives about its own
#: five: an earlier slice REPAIRED them, so "the arm is green on the five filed
#: instances" is unrunnable as written and "the arm reports them" has to build
#: them again.
_FILED_BARE_PATH_CARRIERS: Final = (
    ("tests/test_chained_cause_census.py", 4),
    ("tests/test_handler_exception_rendering.py", 1),
)


def test_each_of_the_five_originally_filed_bare_paths_is_reported(
    tracked: list[str], live_source_roots: frozenset[str]
) -> None:
    """THE ACCEPTANCE CONTROL, and the arm that grades a repair nothing graded.

    Five citations named a memory leaf this repository has never carried, and a
    slice repointed all five at the leaf that owns the lesson. NOTHING IN THE
    SUITE GRADED THAT REPAIR: the tree was green before it and green after it,
    because no shape read a bare path. This is that arm, on a reconstruction.

    BOTH SPELLINGS, WHICH IS WHAT MAKES IT A GRADE RATHER THAN A PLANT. The
    same five sites carry the old name and then the new one: five findings, then
    none. An arm that only reddened on the old name would prove the shape works
    and say nothing about whether the repair was the right one.
    """
    dead = bare_path("memory", _FILED_BARE_PATH_LEAF)
    repaired = bare_path("memory", "a-guard-can-be-green-by-accident.md")

    def corpus(cited: str) -> dict[str, str]:
        return {
            carrier: '"""The filed sites, reconstructed.\n\n'
            + "".join(f"Site {number}: `{cited}`.\n" for number in range(count))
            + '"""\n'
            for carrier, count in _FILED_BARE_PATH_CARRIERS
        }

    assert repaired in tracked, (
        "the leaf the five were repointed at is not tracked, so the green half below "
        "would be measuring the wrong thing"
    )
    how_many = sum(count for _carrier, count in _FILED_BARE_PATH_CARRIERS)
    filed = bare_path_ladder(bare_path_sites(corpus(dead)), tracked, (), {}, live_source_roots)

    assert len(filed[UNRESOLVED]) == how_many, (
        f"the {how_many} filed bare paths were not all reported: {filed[UNRESOLVED]}"
    )
    assert len(bare_path_problems(filed)) == how_many

    fixed = bare_path_ladder(bare_path_sites(corpus(repaired)), tracked, (), {}, live_source_roots)

    assert len(fixed[RESOLVED_EXACT]) == how_many, (
        "the repaired spelling did not resolve at every filed site"
    )
    assert bare_path_problems(fixed) == []


def test_a_recorded_quoting_site_is_forgiven_and_the_same_text_without_the_record_is_reported() -> (
    None
):
    """CONJUNCT B2: green on prose that DISCUSSES a dead path rather than citing one.

    Trap 4 in this arm. A record whose evidence is that a path was deliberately
    NOT created cites the absent name on purpose, and reporting it would punish
    the record for being right. Both directions in ONE arm, because the green
    half on its own is indistinguishable from an arm that has stopped speaking:
    the identical text without the record must report.
    """
    absent = bare_path("docs", "item_notes", "README.md")
    corpus = {_SYNTHETIC_DOC: f"## Decision\n\nThe family gets no `{absent}` at all.\n"}
    sites = bare_path_sites(corpus)
    identity = (_SYNTHETIC_DOC, absent, "## Decision")

    assert [site.identity for site in sites] == [identity], (
        f"the plant did not produce the identity the record is keyed on: {sites}"
    )
    recorded = bare_path_ladder(
        sites, [LEDGER], (), {identity: BarePathReason("quoted, not cited", 1)}, ()
    )

    assert len(recorded[RECORDED_REASON]) == 1
    assert bare_path_problems(recorded) == [], "a recorded quoting site was still reported"

    unrecorded = bare_path_ladder(sites, [LEDGER], (), {}, ())

    assert len(bare_path_problems(unrecorded)) == 1, (
        "the same prose without the record was ALSO green, so the forgiveness above "
        "is silence rather than a record doing work"
    )


# --- contract 10: CS-891 - the bare-path escape hatch must ratchet too -------


def test_the_bare_path_reason_budget_is_spent_exactly_and_cannot_grow() -> None:
    """THE RATCHET, on the live table, and it is SEPARATE from the line-pointer one.

    CS-889's round-one defect was an arm whose every finding could be silenced
    by appending to a table. That was repaired for line pointers and the repair
    did NOT generalise: a bare-path key spends nothing in
    :func:`forgiveness_budget_problems`, because that function counts only keys
    matching :data:`LINE_POINTER_RE`. A bare-path forgiveness would have been
    silenceable the day it shipped.
    """
    problems = bare_path_budget_problems(BARE_PATH_REASONS, BARE_PATH_REASON_CEILING)

    assert not problems, "\n".join(problems)


def test_appending_a_bare_path_reason_is_itself_a_finding() -> None:
    """The adversary's move, against a synthetic budget."""
    identity = (_SYNTHETIC_DOC, bare_path("docs", _BARE_PLANT_LEAF), "## Heading")
    table = {identity: BarePathReason("adjudicated", 1)}

    assert bare_path_budget_problems(table, 1) == []

    appended = dict(table)
    appended[(_SYNTHETIC_DOC, bare_path("docs", "another-absent.md"), "## Heading")] = (
        BarePathReason("looks plausible and answers nothing", 1)
    )
    problems = bare_path_budget_problems(appended, 1)

    assert len(problems) == 1, "appending a bare-path reason was absorbed by the budget"
    assert "2 bare-path reasons recorded against a ceiling of 1" in problems[0]


def test_a_bare_path_ceiling_left_slack_after_a_repair_is_reported() -> None:
    """Slack is banked room for an append nobody has to defend."""
    problems = bare_path_budget_problems({}, 2)

    assert len(problems) == 1, "a slack bare-path ceiling was accepted"
    assert "Lower it to 0" in problems[0]


def test_every_recorded_bare_path_reason_still_answers_the_sites_it_records(
    live_bare_path_ladder: Mapping[str, Sequence[BarePathSite]],
) -> None:
    """The table against the corpus, in the three directions it can drift.

    AND AGAINST ITS OWN CLAUSE. The acceptance this table answers is worded
    "declines against a STATED reason", and nothing read the string. VERIFIED:
    blanking all seven left the ladder, the reason-vs-corpus check and the
    budget green. The sibling table grades its own at the same one line; this
    one copied the shape and left behind the leg that enforces the clause.
    """
    for identity, recorded in sorted(BARE_PATH_REASONS.items()):
        assert recorded.why.strip(), f"{identity} forgives a dead citation and states no evidence."
    problems = bare_path_reason_problems(live_bare_path_ladder, BARE_PATH_REASONS)

    assert not problems, "BARE_PATH_REASONS no longer matches the corpus:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def test_a_compensating_swap_in_the_bare_path_reasons_is_reported_in_both_directions() -> None:
    """CS-893, ANSWERED RATHER THAN COPIED.

    That item is filed against this module because :attr:`Disposition.sites` is
    a bare count: delete one recorded site and add an unrelated one in the same
    edit, and the cardinality is unchanged and the swap is silent. The table
    below is keyed on an IDENTITY, so the same edit fails twice - the added
    entry answers nothing and the removed one is reported.

    THE CARDINALITY IS ASSERTED EQUAL, so the arm is a statement about the KEY
    rather than about the size of the edit.
    """
    carrier = _SYNTHETIC_DOC
    cited = bare_path("docs", _BARE_PLANT_LEAF)
    elsewhere = bare_path("docs", "another-absent.md")
    sites = bare_path_sites({carrier: f"## Heading\n\nsee `{cited}` here\n"})
    honest = {(carrier, cited, "## Heading"): BarePathReason("adjudicated", 1)}
    swapped = {(carrier, elsewhere, "## Heading"): BarePathReason("adjudicated", 1)}

    assert len(swapped) == len(honest), "the swap changed the table's size, so it is not one"

    good = bare_path_ladder(sites, [LEDGER], (), honest, ())

    assert bare_path_reason_problems(good, honest) == []
    assert bare_path_problems(good) == []

    bad = bare_path_ladder(sites, [LEDGER], (), swapped, ())

    assert len(bare_path_reason_problems(bad, swapped)) == 1, (
        "the swapped-IN entry answers no site and was not reported stale"
    )
    assert len(bare_path_problems(bad)) == 1, (
        "the swapped-OUT site is no longer forgiven and was not reported"
    )


@pytest.mark.parametrize(
    ("rung", "pinned"),
    [
        (DECLARED_UNTRACKED, DECLINED_AS_DECLARED_UNTRACKED),
        (UNTRACKED_ROOT, DECLINED_UNDER_AN_UNTRACKED_ROOT),
        (FIXTURE_LITERAL, DECLINED_AS_A_FIXTURE_LITERAL),
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
    used to buy silence. That is :data:`UNFORBIDDEN_LINE_POINTERS`' shape, and
    it is what separates a disclosure from a permission list.
    """
    assert pinned, f"{rung} discloses nothing, so this arm measures an empty set"

    problems = pinned_rung_problems(live_bare_path_ladder, rung, pinned)

    assert not problems, f"the {rung} disclosure disagrees with the corpus:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def test_appending_to_a_decline_disclosure_is_itself_a_finding() -> None:
    """All three ways a disclosure can drift, on a corpus of one site."""
    site = BarePathSite(_SYNTHETIC_DOC, bare_path("nowhere", "x.py"), 3, 5, "## Heading", False)
    answered: dict[str, list[BarePathSite]] = {rung: [] for rung in LADDER_RUNGS}
    answered[UNTRACKED_ROOT] = [site]
    other = (_SYNTHETIC_DOC, bare_path("nowhere", "y.py"), "## Heading")

    assert pinned_rung_problems(answered, UNTRACKED_ROOT, {site.identity: 1}) == []

    appended = pinned_rung_problems(answered, UNTRACKED_ROOT, {site.identity: 1, other: 1})
    assert len(appended) == 1, f"an appended disclosure entry was absorbed: {appended}"
    assert "no longer declines it" in appended[0]

    undisclosed = pinned_rung_problems(answered, UNTRACKED_ROOT, {})
    assert len(undisclosed) == 1, f"an undisclosed decline was absorbed: {undisclosed}"
    assert "is not disclosed" in undisclosed[0]

    drifted = pinned_rung_problems(answered, UNTRACKED_ROOT, {site.identity: 2})
    assert len(drifted) == 1, f"a drifted spelling count was absorbed: {drifted}"
    assert "spelling(s)" in drifted[0]


def test_the_container_walk_sees_a_lowercase_table_and_not_the_interpreters_own() -> None:
    """The walk's OWN boundary, asserted on a namespace built for the purpose.

    THE CONTRACT BELOW CANNOT PROVE THIS: it asks whether anything unregistered
    is held, and "no" reads the same whether the walk is complete or simply
    cannot see the table that would have been reported.

    AND THE FIRST VERSION OF THIS ARM ASSERTED THE NEXT HOLE AS A FEATURE. It
    required ``__builtins__`` NOT to be returned and said nothing about any
    other dunder, so it was green while a table named with two leading
    underscores escaped the walk entirely - the fixture encoding the
    implementation's own assumption. A DUNDER-NAMED TABLE IS NOW REQUIRED TO BE
    SEEN, which is the assertion that fails if the exclusion widens back into a
    prefix.

    FOUR DIRECTIONS: a lowercase container is returned, a dunder-named one is
    returned, the three the interpreter installs are not, and a non-container of
    any spelling is not.
    """
    space: dict[str, object] = {
        "lowercase_forgiveness": {("a", "b", "c"): 1},
        "UPPER_TABLE": ("x",),
        "__ADJUDICATED": {("a", "b", "c"): "forgiven"},
        "__builtins__": {},
        "__annotations__": {},
        "__conditional_annotations__": {},
        "NOT_A_CONTAINER": 3,
        "not_a_container": "a string is iterable and is not a table",
    }

    found = sorted(module_containers(space))

    assert found == ["UPPER_TABLE", "__ADJUDICATED", "lowercase_forgiveness"], (
        f"the container walk returned {found}. A table spelled in lower case must be "
        "seen, and so must one spelled with two leading underscores - a walk that "
        "exists to catch an unregistered table cannot require the table to be named "
        "in a particular way - while the three names the interpreter itself installs "
        "must not be, or the registries fill up with names nobody wrote."
    )


def test_the_interpreter_exclusion_is_a_closed_set_and_not_a_prefix() -> None:
    """The exclusion's MEMBERSHIP, asserted, because a prefix rule is what shipped.

    The walk's docstring has claimed "a known, closed set" since it was written
    while the code tested a PREFIX. This arm is the difference between those two
    sentences, and widening back to a prefix cannot be done without deleting it.
    """
    assert sorted(_INTERPRETER_NAMES) == [
        "__annotations__",
        "__builtins__",
        "__conditional_annotations__",
    ], (
        f"the interpreter exclusion holds {sorted(_INTERPRETER_NAMES)}. It is a CLOSED "
        "set, enumerated so growing it is a diff rather than a prefix quietly "
        "widening under cover of a rule about the runtime."
    )
    assert all(name.startswith("__") and name.endswith("__") for name in _INTERPRETER_NAMES), (
        f"a name in the interpreter exclusion is not a dunder: {sorted(_INTERPRETER_NAMES)}"
    )

    installed = set(_INTERPRETER_NAMES) & set(globals())

    assert installed == set(_INTERPRETER_NAMES), (
        "the interpreter exclusion names something this module's globals do not carry:"
        f" {sorted(set(_INTERPRETER_NAMES) - installed)}. An exclusion for a name that"
        " is never present is room the walk gives away for nothing."
    )


def test_every_container_this_module_holds_is_bounded_or_recorded_as_forgiving_nothing() -> None:
    """CLOSING THE CLASS, NOT THE INSTANCE.

    Three consecutive repairs to this module reproduced their own filed fault
    one level up: a hole is found, the instance is fixed, and the next table of
    the same shape arrives with nothing counting it. So the question is not
    "are these tables bounded", it is "does any module-scope CONTAINER this
    module holds sit outside both registries". A sixth escape hatch of that
    shape is RED until somebody answers for it, one way or the other.

    THE CLAIM IS THE WALK'S SIZE AND NOT A LARGER ONE, which is a correction
    rather than a hedge. This arm has been read as closing FORGIVENESS, and it
    does not: a module-scope ``str`` used as a prefix silencer, or an ``int``
    used as a bound, is not a container and never reaches here.
    :func:`module_containers` states why admitting strings is the wrong trade,
    and :func:`derived_bound_problems` is what answers the ``int``.
    """
    containers = module_containers(globals())

    assert containers, (
        "this module holds no module-scope container, so the derivation below reads "
        "an empty set and would pass whatever went uncounted"
    )
    unanswered = sorted(
        name
        for name in containers
        if name not in FORGIVENESS_TABLES and name not in NOT_A_FORGIVENESS
    )
    assert not unanswered, (
        "module-scope containers that neither ratchet nor record why they forgive nothing:\n"
        + "\n".join(f"  {name}" for name in unanswered)
        + "\nBound it in FORGIVENESS_TABLES, or say in NOT_A_FORGIVENESS why it forgives nothing."
    )
    both = sorted(set(FORGIVENESS_TABLES) & set(NOT_A_FORGIVENESS))
    assert not both, f"registered as both a forgiveness and not one: {both}"

    registered = set(FORGIVENESS_TABLES) | set(NOT_A_FORGIVENESS)
    stale = sorted(name for name in registered if name not in containers)
    assert not stale, f"registered names this module no longer holds: {stale}"


def test_every_bounded_table_names_a_contract_that_exists_and_every_exemption_a_reason() -> None:
    """The registries' own shape, so an entry cannot be a name with no case behind it.

    THE CEILING OF THIS MECHANISM, STATED: a false sentence in
    :data:`NOT_A_FORGIVENESS` still silences the walk. What it removes is doing
    it SILENTLY - the entry sits in the diff as a claim somebody has to defend,
    which is exactly what the line-pointer budget claims for itself and no more.
    """
    for table, contract in sorted(FORGIVENESS_TABLES.items()):
        bound = globals().get(contract)
        assert callable(bound), f"{table} names {contract}, which this module does not define"
        assert contract.startswith("test_"), f"{table} is bounded by {contract}, not a contract"
    for table, why in sorted(NOT_A_FORGIVENESS.items()):
        assert why.strip(), f"{table} is recorded as forgiving nothing and states no reason"


def test_the_module_spells_no_unresolving_bare_path_of_its_own(
    live_bare_path_sites: Sequence[BarePathSite],
    live_bare_path_ladder: Mapping[str, Sequence[BarePathSite]],
    tracked: list[str],
    live_declared_untracked: frozenset[str],
    live_source_roots: frozenset[str],
) -> None:
    """THE LIKELIEST OWN GOAL, measured rather than reasoned about.

    Any path spelled in this module is read by this module's own arm.
    :func:`line_key` exists for the same hazard one shape over, and this file
    ALREADY spelled a metasyntactic corpus member in its own prose before the
    arm could see it - which is why that site is in the reason table rather
    than in this arm's silence.

    THE THIRD LEG IS WHAT MAKES THE SECOND MEAN ANYTHING. Re-running this
    module's own sites with an EMPTY reason table must report, so the clean
    answer above is bought by a record somebody wrote and not by an arm that
    has stopped reading this file.
    """
    mine = [site for site in live_bare_path_sites if site.carrier == THIS_MODULE]

    short = floor_problems("bare paths spelled by this module", len(mine), _SELF_SPELLED_FLOOR)

    assert not short, "\n".join(short) + (" The arm has stopped reading this module's own source.")
    unanswered = [
        site
        for rung in (AMBIGUOUS_SUFFIX, UNRESOLVED)
        for site in live_bare_path_ladder[rung]
        if site.carrier == THIS_MODULE
    ]

    assert not unanswered, "this module spells bare paths of its own that do not resolve:\n" + (
        "\n".join(f"  {site.cited} at line {site.line}" for site in unanswered)
    )

    unrecorded = bare_path_ladder(mine, tracked, live_declared_untracked, {}, live_source_roots)

    assert unrecorded[UNRESOLVED], (
        "with no reason table at all this module still reports nothing about itself, "
        "so the clean answer above is not bought by the record"
    )


def test_the_source_roots_are_derived_from_the_manifests_this_repo_tracks(
    tracked: list[str], live_source_roots: frozenset[str]
) -> None:
    """R1's candidate set, DERIVED - and both halves of the derivation posed.

    Three questions the live tree cannot answer for itself: does the Python half
    read the manifest, does the Node half read the index, and does the result
    exclude the MIRROR TREE that made R1 a laundering route. The mirror is named
    because it is the measured attack - `tests/` carries an ``__init__.py`` and
    would pass any "is this a package" test, which is why the question asked is
    whether this repository SHIPS it.
    """
    assert live_source_roots, (
        "the source-root derivation came back empty, so a manifest stopped declaring"
        " what this repository ships and every module-map citation is now a finding."
    )
    roots = {path.split("/", 1)[0] for path in tracked if "/" in path}
    assert live_source_roots <= roots, (
        f"the derivation named directories the index does not carry:"
        f" {sorted(live_source_roots - roots)}"
    )
    assert "tests" not in live_source_roots, (
        "the test tree was derived as a source root. It MIRRORS the package tree, so"
        " R1 would resolve a citation into a helper with no package counterpart."
    )

    manifest = "[tool.setuptools.packages.find]" + NEWLINE + 'include = ["clockspeed*"]' + NEWLINE
    only_python = source_roots(["clockspeed/x.py"], manifest)
    assert only_python == {"clockspeed"}, (
        f"the Python half did not read the manifest: {sorted(only_python)}"
    )
    only_node = source_roots(["shell/package.json", "shell/main.js"], "")
    assert only_node == {"shell"}, f"the Node half did not read the index: {sorted(only_node)}"
    neither = source_roots(["tests/__init__.py", "tests/save/helper.py"], "")
    assert neither == frozenset(), (
        f"a package that is not shipped was derived as a source root: {sorted(neither)}"
    )


def test_a_suffix_hit_outside_a_source_root_is_reported_rather_than_resolved() -> None:
    """R1'S REFUTATION, REPRODUCED AND THEN KILLED, on a corpus with no tree behind it.

    The first build read "names A tracked file" as "the citation resolved" and
    wrote that R1 "needs no ratchet" because it is a resolution - restating the
    property instead of closing it. The first leg poses that defect deliberately;
    the last is why the rule is a ROOTED SUFFIX rather than a prefix, since a
    prefix refuses the module-map spellings that omit two directories.

    WHERE THE REFUSED SITE LANDS, STATED, because refusing to resolve is not the
    same as reporting. A citation whose first segment is a root this repository
    owns falls to REPORTED. One whose first segment is not - which the
    mirror-tree spellings are - lands on R3, a DECLINE that is pinned in both
    directions and now spends a ceiling. Both landings are checked; neither is a
    silent resolution, which is the property that was missing.
    """
    cited = bare_path("save", "planted.py")
    sites = bare_path_sites(_planted_bare(_SYNTHETIC_DOC, cited))
    mirror = bare_path("tests", "save", "planted.py")
    package = bare_path("clockspeed", "save", "planted.py")

    launders = bare_path_ladder(sites, [mirror], (), {}, ("tests", "clockspeed"))

    assert len(launders[RESOLVED_SUFFIX]) == 1, (
        "the mirror hit did not resolve even with the mirror declared a source root,"
        " so this control is not posing the defect it exists to reproduce"
    )
    assert bare_path_problems(launders) == [], (
        "the defect posed above was not SILENT, so it is not the defect that shipped"
    )

    rooted = bare_path_ladder(sites, [mirror], (), {}, _CONTROL_SOURCE_ROOTS)

    assert rooted[RESOLVED_SUFFIX] == [], (
        "a suffix hit in the mirror tree still resolved, so R1 is still laundering"
    )
    assert len(rooted[UNTRACKED_ROOT]) == 1, (
        "the refused citation reached neither a report nor a disclosed decline, so R1"
        " stopped resolving it into silence rather than into a price"
    )

    owned = bare_path("docs", "planted.py")
    reported = bare_path_ladder(
        bare_path_sites(_planted_bare(_SYNTHETIC_DOC, owned)),
        [bare_path("tests", "docs", "planted.py"), LEDGER],
        (),
        {},
        _CONTROL_SOURCE_ROOTS,
    )

    assert len(bare_path_problems(reported)) == 1, (
        "a mirror hit under a root this repository DOES own was not reported, and that"
        " spelling has nowhere left to fall"
    )

    real = bare_path_ladder(sites, [package], (), {}, _CONTROL_SOURCE_ROOTS)

    assert len(real[RESOLVED_SUFFIX]) == 1, (
        "a genuine package-relative citation stopped resolving, so the restriction"
        " went from refusing the wrong file to refusing every file"
    )

    deep = bare_path("backends", "greedy.py")
    nested = [bare_path("clockspeed", "solve", "backends", "greedy.py")]
    two_down = bare_path_ladder(
        bare_path_sites(_planted_bare(_SYNTHETIC_DOC, deep)), nested, (), {}, _CONTROL_SOURCE_ROOTS
    )

    assert len(two_down[RESOLVED_SUFFIX]) == 1, (
        "a spelling omitting TWO directories stopped resolving, which is what a prefix"
        " rule would do and why this one is a rooted suffix"
    )


def test_no_recorded_bound_is_computed_from_the_table_it_bounds() -> None:
    """THE PERMANENT DISARM, AND IT IS ONE LINE - so the check reads the source.

    ``BARE_PATH_REASON_CEILING: Final = len(BARE_PATH_REASONS)`` makes every
    budget here true by construction, in a diff carrying NO NUMBER to query, and
    both existing budget arms survive it.

    BOTH DIRECTIONS AGAINST THE REAL SOURCE, which is what makes the green half
    mean something: the same source with one tautology appended must report
    exactly one - proving the walk parsed this file, reached module scope and
    fires - and the file as it stands must report none.
    """
    source = Path(__file__).read_text(encoding="ascii")

    tautology = source + f"{NEWLINE}BARE_PATH_REASON_CEILING = len(BARE_PATH_REASONS){NEWLINE}"
    planted = derived_bound_problems(tautology, FORGIVENESS_TABLES)

    assert len(planted) == 1, (
        f"a ceiling computed from the table it bounds was not the single finding: {planted}"
    )
    assert "BARE_PATH_REASON_CEILING" in planted[0]

    problems = derived_bound_problems(source, FORGIVENESS_TABLES)

    assert not problems, (
        "bounds computed from their own subject:"
        + NEWLINE
        + NEWLINE.join(f"  {problem}" for problem in problems)
    )


@pytest.mark.parametrize(
    ("rung", "pinned", "ceiling"),
    [
        (DECLARED_UNTRACKED, DECLINED_AS_DECLARED_UNTRACKED, DECLARED_UNTRACKED_CEILING),
        (UNTRACKED_ROOT, DECLINED_UNDER_AN_UNTRACKED_ROOT, UNTRACKED_ROOT_CEILING),
        (FIXTURE_LITERAL, DECLINED_AS_A_FIXTURE_LITERAL, FIXTURE_LITERAL_CEILING),
    ],
)
def test_every_decline_disclosure_is_budgeted_and_spent_exactly(
    rung: str, pinned: Mapping[tuple[str, str, str], int], ceiling: int
) -> None:
    """THE THIRD, FOURTH AND FIFTH BUDGETS, because the pin alone was not one.

    The pin catches a row added ALONE, never one added together with the dead
    citation it describes - and that pair was the whole purchase: one dead
    citation, one row, suite green. Every rung now spends a number.
    """
    problems = decline_budget_problems(rung, pinned, ceiling)

    assert not problems, NEWLINE.join(problems)


def test_appending_to_a_decline_disclosure_spends_its_budget() -> None:
    """The adversary's move against a synthetic budget, and the slack direction too."""
    one = {(_SYNTHETIC_DOC, bare_path("nowhere", "x.py"), "## Heading"): 1}

    assert decline_budget_problems(UNTRACKED_ROOT, one, 1) == []

    appended = dict(one)
    appended[(_SYNTHETIC_DOC, bare_path("nowhere", "y.py"), "## Heading")] = 1
    grown = decline_budget_problems(UNTRACKED_ROOT, appended, 1)

    assert len(grown) == 1, "an appended disclosure row was absorbed by the budget"
    assert "2 sites disclosed against a ceiling of 1" in grown[0]

    slack = decline_budget_problems(UNTRACKED_ROOT, {}, 2)

    assert len(slack) == 1, "a slack disclosure ceiling was accepted"
    assert "Lower it to 0" in slack[0]


@pytest.mark.parametrize(
    ("what", "floor"),
    [
        ("bare-path sites", BARE_PATH_POPULATION_FLOOR),
        ("module-map paths the ladder answers", _ARCHITECTURE_RESOLVED_FLOOR),
        ("bare paths spelled by this module", _SELF_SPELLED_FLOOR),
    ],
)
def test_every_non_vacuity_floor_rejects_a_population_that_measured_nothing(
    what: str, floor: int
) -> None:
    """EACH FLOOR, GRADED - because each could be set to zero with the suite green.

    VERIFIED: all three set to 0 reddened nothing, restoring exactly the defect
    each exists to prevent in a one-character diff. THREE DIRECTIONS: nothing
    measured is rejected, one short is rejected, the floor itself is accepted -
    so this is about the boundary rather than about the floor being large.
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
    """CLOSING THE CLASS, so a FOURTH floor cannot arrive ungraded.

    A hand-list of three is exactly what let the third, fourth and fifth
    forgiveness tables arrive unbounded elsewhere in this file. The
    parametrization is checked against what the SOURCE passes as a floor.
    """
    source = Path(__file__).read_text(encoding="ascii")

    used = graded_floor_names(source)

    assert used, "this module passes no named floor to floor_problems at all"
    graded = {
        "BARE_PATH_POPULATION_FLOOR",
        "_ARCHITECTURE_RESOLVED_FLOOR",
        "_SELF_SPELLED_FLOOR",
    }
    ungraded = sorted(used - graded)
    assert not ungraded, (
        f"floors used but not graded: {ungraded}. Add each to the parametrization"
        " above, so a floor that could be zeroed is one something asks about."
    )
    stale = sorted(graded - used)
    assert not stale, f"graded floors this module no longer uses as floors: {stale}"


def test_each_named_leg_of_the_bare_path_shape_is_load_bearing(
    live_bare_path_sites: Sequence[BarePathSite],
) -> None:
    """THE TWO LEGS THE SHAPE'S OWN COMMENT NAMES, and neither was graded.

    VERIFIED: deleting the leading-dot leg from :data:`_FIRST_SEGMENT` killed
    ZERO arms and silently removed 27 live sites - every workflow and
    harness-configuration citation. Dropping ``yml`` killed zero arms and
    removed eight more. A comment explaining why a leg exists is not a check
    that it does. BOTH LEGS, TWICE: the pattern must READ the shape and the live
    corpus must CARRY it, the second being what makes a deletion a finding.
    """
    dotted = bare_path(".github", "workflows", "tier1.yml")
    plain = bare_path("github", "workflows", "tier1.yml")

    assert BARE_PATH_RE.search(f"`{dotted}`"), (
        "the shape no longer reads a FIRST segment starting with a dot, so the workflow"
        " and harness-configuration citations are invisible again"
    )
    assert BARE_PATH_RE.search(f"`{plain}`"), (
        "the leading-dot leg became REQUIRED, so ordinary paths stopped matching"
    )

    dot_leading = [site for site in live_bare_path_sites if site.cited.startswith(".")]

    assert dot_leading, (
        "no live site starts with a dot, so that leg guards nothing and is free to cut"
    )

    yml = [site for site in live_bare_path_sites if site.cited.endswith(".yml")]

    assert yml, "no live site ends in that extension, so its alternative is free to cut"
    assert not BARE_PATH_RE.search("`" + bare_path("docs", "notes.rst") + "`"), (
        "the alternation admits an extension it does not list, so the boundary it draws"
        " is not the one the comment above discloses"
    )


def test_the_ignore_probe_raises_rather_than_reading_a_bad_exit_as_nothing_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R2's LOUD-FAILURE LEG, which was argued in prose and checked by nothing.

    :func:`declares_untracked` argues that a bad exit must RAISE, because it
    otherwise reads as "nothing is ignored" - byte-identical to a clean corpus.
    VERIFIED: ``RuntimeError`` appeared exactly once in this module, in the
    implementation, and replacing the exit check with a constant false passed
    302 of 302.

    The subprocess is replaced rather than persuaded, since the shape refuses
    the traversal path that provokes a real fatal. Both directions: a fatal
    raises, and the exit meaning "no path matched" still answers.
    """
    fatal = subprocess.CompletedProcess(
        args=[], returncode=128, stdout=b"", stderr=b"fatal: is outside repository"
    )
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: fatal)

    with pytest.raises(RuntimeError) as raised:
        declares_untracked([bare_path("config", "planted.json")])

    assert "128" in str(raised.value), (
        f"the failure was raised without the exit that caused it: {raised.value}"
    )

    nothing = subprocess.CompletedProcess(args=[], returncode=1, stdout=b"", stderr=b"")
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: nothing)

    assert declares_untracked([bare_path("config", "planted.json")]) == frozenset(), (
        "exit 1 means NO path matched, an answer rather than a failure; raising on it"
        " makes the rung unusable on a clean corpus"
    )


def test_this_test_module_is_seven_bit_ascii() -> None:
    """Non-negotiable 4, checked on this file rather than assumed of it."""
    raw = Path(__file__).read_bytes()

    assert not [byte for byte in raw if byte > HIGHEST_ASCII], (
        "this module carries a byte above the 7-bit range"
    )


# THE CLOSURE'S BACK-EDGE, AND IT IS THE ONE STATEMENT THIS SPLIT TURNS ON.
# namespace_closure derives the walked family by REACHABILITY from
# `tests/test_bare_path_citations.py`, so a module nothing in the family
# imports is walked by nothing - and this split moved a LIVE forgiveness, the
# deep archive's rot pin, into a module the file above otherwise has no reason
# to name. Without this statement that pin and the derivation behind it sit
# outside both class-closing walks, which is the relocation evasion CS-891
# closed, reopened by the very change that split the module.
#
# AT THE FOOT OF THE FILE, DELIBERATELY, and E402 is answered rather than
# waved through. `tests/test_archive_rot.py` binds this module's fixtures BY
# NAME, so the edge can only be taken once every name above it exists; at the
# top it is a partially-initialised import in every collection order that
# reaches this file first, which is an ImportError rather than a style
# question. F401 is answered the same way: the statement is imported for its
# EDGE and not for a name, which is exactly what reachability means here.
from tests import test_archive_rot  # noqa: E402, F401
