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
   later correcting record. :data:`tests.test_citation_tables.DISPOSITIONS` is where that
   distinction is
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
:data:`tests.test_citation_tables.UNGUARDED_DOCS` is the whole of it, and it is a RECORD rather than
a
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
HERE IS THE EXEMPTION ITSELF: :data:`tests.test_citation_tables.UNGUARDED_DOCS`, the path it names
and the
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
   it resolves today". One did not, and :data:`tests.test_citation_tables.DISPOSITIONS` already
   recorded
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
  :data:`tests.test_citation_tables.UNVERIFIED_LINE_POINTERS` resolves in RANGE and has NOT been
  checked
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
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Final

import pytest

# CS-1066 - THE TABLES AND THE CORPUS, TAKEN TWO DIFFERENT WAYS ON PURPOSE.
#
# THE CONTAINERS COME THROUGH THE MODULE OBJECT, never by name, and that is a
# mechanism rather than a style. An imported name lands in THIS module's
# `globals()`, where the container contract below - the one that closes the
# class rather than the instance - finds it and demands a registry row, so
# every table bounded over there would
# need a second contract here, and two contracts for one table is two places for
# one ratchet to drift. The alias keeps each table answered exactly once, in the
# module that holds it. What that costs - a table invisible to the walk that
# reads one namespace - is already paid by the cross-module container walk in
# `tests/test_bare_path_citations.py`, which reads every module the import
# graph reaches and holds each answerable for what it holds.
#
# THE FUNCTIONS, THE FIXTURES AND THE SCALARS COME BY NAME, because none of them
# is a container and none of them costs a registry row. Binding the fixtures
# here is not optional either: pytest resolves a fixture out of the COLLECTING
# module's namespace, so one defined a file over is invisible until its name is
# bound here - the idiom `tests/test_archive_rot.py` already records at length.
from tests import test_citation_tables as tables
from tests.bare_path_guard import (
    _INTERPRETER_NAMES,
    ABSENT_DECLARATION_RE,
    AMBIGUOUS_SUFFIX,
    BARE_PATH_RE,
    DECLARED_ABSENT,
    DECLARED_ABSENT_BOUND,
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
    non_citation_budget_problems,
    pinned_rung_problems,
    source_roots,
    stale_declaration_problems,
)
from tests.save import test_oracle_citations as oracle_citations
from tests.test_citation_tables import (
    DATED_ARCHIVE,
    DECLARED_ABSENT_CEILING,
    DECLARED_UNTRACKED_CEILING,
    DELIBERATE,
    FIXTURE_LITERAL_CEILING,
    LEDGER,
    MOVED,
    NEWLINE,
    NO_TARGET,
    OUT_OF_DOMAIN,
    RENAMED,
    UNTRACKED_ROOT_CEILING,
    Disposition,
    bare_path,
    doc_text,
    forgiveness_budget_problems,
    in_domain,
    line_key,
    scoped_text,
)
from tests.test_citation_tables import (
    file_lines as _file_lines,
)
from tests.test_citation_tables import (
    line_counts as _line_counts,
)
from tests.test_citation_tables import (
    line_pointer_carriers as _line_pointer_carriers,
)
from tests.test_citation_tables import (
    live_bare_path_ladder as _live_bare_path_ladder,
)
from tests.test_citation_tables import (
    live_bare_path_sites as _live_bare_path_sites,
)
from tests.test_citation_tables import (
    live_declared_untracked as _live_declared_untracked,
)
from tests.test_citation_tables import (
    live_source_roots as _live_source_roots,
)
from tests.test_citation_tables import (
    markdown_texts as _markdown_texts,
)
from tests.test_citation_tables import (
    module_basenames as _module_basenames,
)
from tests.test_citation_tables import (
    sources as _sources,
)
from tests.test_citation_tables import (
    tracked as _tracked,
)
from tests.test_citation_tables import (
    tracked_files as _tracked_files,
)

# THE CORPUS FIXTURES, REBOUND UNDER THE NAMES PYTEST RESOLVES THEM BY, and
# ALIASED rather than imported plainly for the reason the sibling arm records:
# a plain import of a name a test then takes as a PARAMETER is reported twice,
# unused at module scope and then redefined by the parameter, and the usual
# answer is a noqa on each. The rebinding makes each import genuinely used.
file_lines = _file_lines
line_counts = _line_counts
line_pointer_carriers = _line_pointer_carriers
live_bare_path_ladder = _live_bare_path_ladder
live_bare_path_sites = _live_bare_path_sites
live_declared_untracked = _live_declared_untracked
live_source_roots = _live_source_roots
markdown_texts = _markdown_texts
module_basenames = _module_basenames
sources = _sources
tracked = _tracked

# RE-EXPORTED RATHER THAN DROPPED, and the alias is the same one the fixtures
# above take for the same reason - a plain import of a name this module does not
# itself use is reported unused, and the answer to that is a rebinding rather
# than a suppression. `tests/test_sphinx_roles.py` takes the index walk from
# here and sits outside this relocation, so the name stays bound at its old
# address while its OWNER moves. It is one statement rather than an edit to a
# file this change has no other business in.
tracked_files = _tracked_files

# Non-negotiable 4 is 7-bit ASCII, so the highest byte an authored file may
# carry is 0x7E - the tilde, the last printable character in the range.
HIGHEST_ASCII: Final = 0x7E

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


def _adr_docs() -> tuple[str, ...]:
    """Return every ADR and its index, repo-relative and sorted.

    DERIVED, NOT LISTED, for the reason :func:`_item_notes_leaves` gives about
    its own family - and adopted here only after that reason was paid for. The
    family was listed a file at a time until the list had eaten this module's
    byte budget and a new ADR could not be registered at all. The per-ADR
    reasoning is kept by the ``ADR_00NN`` constants above as an arrival record;
    what it argued is now structural, so a new ADR is covered on arrival.

    Returns:
        Each ADR's repo-relative path, sorted, empty if the family is absent.
    """
    family = REPO_ROOT / "docs" / "adr"
    if not family.is_dir():
        return ()
    return tuple(f"docs/adr/{path.name}" for path in sorted(family.glob("*.md")))


#: Every ADR, derived from disk. Widens GUARDED_DOCS the way ITEM_NOTES_LEAVES
#: does, and is recorded beside it in NOT_A_FORGIVENESS for the same reason.
ADR_DOCS: Final = _adr_docs()

#: The leaves of the item-notes family. `docs/item_notes.md` was ONE file until
#: 2026-08-25, when it became an index over `docs/item_notes/` with one leaf per
#: phase; the bodies - and so every citation in them - moved into the leaves.
ITEM_NOTES_LEAVES: Final = _item_notes_leaves()

GUARDED_DOCS: Final = (
    LEDGER,
    "ROADMAP.md",
    # docs/CHANNEL.md is a VENDORED file, byte-identical across five repositories
    # and pinned by tests/test_channel_doc.py. It carries one bare repo-relative
    # path, which makes it a carrier under BARE_PATH_RE - so it is GUARDED here
    # rather than recorded UNGUARDED. That direction is forced, not chosen: an
    # exemption would be a disposition about a file this tree may not edit, and
    # the one path it names resolves, so there is nothing to forgive. If a future
    # re-pin lands a path that does NOT resolve, this guard is the thing that must
    # fail - never the doc that must change.
    "docs/CHANNEL.md",
    "docs/GATED.md",
    "WAKEUP_NOTES.md",
    # CS-959 - THE THREE COMMUNITY-HEALTH FILES THAT CITE A PATH. They are the
    # first documents in this tree written FOR AN OUTSIDER, and every path they
    # name is one a stranger will follow on their first day. A broken pointer in
    # CONTRIBUTING.md is the defect that costs a contributor before they ever
    # reach the code, so these are guarded on arrival rather than recorded
    # UNGUARDED. .github/CODE_OF_CONDUCT.md is absent from this list because it
    # cites no path at all; it will become a carrier the moment it does, and
    # this guard is what will say so.
    ".github/CONTRIBUTING.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/SECURITY.md",
    # THE WHOLE ADR FAMILY, derived rather than listed - see _adr_docs.
    *ADR_DOCS,
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
    # The one memory leaf left outside the three above. It names the test
    # module its lesson was learned in, and that module is tracked today - the
    # same reason those three are guarded rather than recorded.
    "memory/a-guard-can-be-accepted-and-unscoped.md",
    "memory/full-authority-adjudicate-do-not-ask.md",
    # The headless queue lane's worker prompt (CS-918). Guarded on arrival
    # rather than recorded, because every path in it resolves today AND because
    # of who reads it: an unattended worker, once per cycle, with nobody
    # watching. That is precisely where a rotted pointer goes unobserved - the
    # worker would follow it, find nothing, and improvise.
    "tools/headless-queue.md",
)

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
JUDGED_SHAPES: Final = (CITATION_RE, LINE_POINTER_RE, BARE_RE, ELIDED_RE, BARE_PATH_RE)

#: THE PATTERNS THIS FAMILY COMPILES THAT ARE NOT CITATION SHAPES, and the
#: boundary contract reads this beside :data:`JUDGED_SHAPES` rather than
#: instead of it.
#:
#: WHY IT EXISTS. The contract walked every compiled pattern in the family and
#: required each to be a shape the carrier boundary reads. That was true while
#: every pattern here ANSWERED the question "does this text cite something". It
#: stopped being true when CS-899 added a pattern that answers a different
#: question - whether the author has DECLARED the path on this line absent -
#: and the two cannot be merged: a doc carrying a declaration and no citation
#: is not a carrier, and admitting one to :data:`JUDGED_SHAPES` would move the
#: guarded-set boundary as a side effect of a repair that is not about it.
#:
#: WHY IT IS A TABLE RATHER THAN A WIDER RULE. "Not every pattern is a citation
#: shape" as a sentence forgives every future pattern in silence, which is the
#: permission-list shape this module exists to refuse. Naming them costs one
#: row per pattern and the contract checks the table in BOTH directions, so a
#: row for a pattern the family no longer compiles reddens exactly as an
#: undeclared pattern does.
#:
#: AND THE PIN IS NOT THE WHOLE BOUND, WHICH IS WHAT CS-1127 MEASURED. Both
#: directions stay satisfied when a row arrives TOGETHER WITH the pattern it
#: describes, and that pair is the purchase: a pattern that IS a citation shape
#: declared not one, in a single row carrying no number. The row costs
#: :data:`NON_CITATION_PATTERN_CEILING` as well now.
#:
#: THE RENAMING EVASION IS WORTH STATING because it is the cheap way past the
#: contract and it is forbidden here: :func:`tests.bare_path_guard.module_patterns`
#: reads the ``_RE`` suffix, so a pattern named anything else is invisible to
#: the walk entirely. A pattern this family judges by is named ``_RE`` and is
#: then declared in one of these two tables. Nowhere else.
#: A backticked span is the repository's own idiom for a path, an identifier
#: or a shell line, so it is admitted as one token even when it holds spaces.
BACKTICK_RE: Final = re.compile(r"`([^`\n]+)`")

#: A sentence ends at a full stop followed by whitespace, or at a blank line.
#: A dot INSIDE a path has no whitespace after it, so `locate.py` never splits.
SENTENCE_BREAK_RE: Final = re.compile(r"\.\s|\n[ \t]*\n")

#: Line-leading noise stripped before a sentence is read, so a claim spanning
#: several comment lines or a quoted block reads as the one sentence it is.
LINE_MARKER_RE: Final = re.compile(r"(?m)^[ \t]*(?:#+|//|>|[-*+])[ \t]*")

NON_CITATION_PATTERNS: Final = (
    ABSENT_DECLARATION_RE,
    BACKTICK_RE,
    SENTENCE_BREAK_RE,
    LINE_MARKER_RE,
)

#: THE RECORDED BUDGET FOR THE TABLE ABOVE. An integer somebody typed, so
#: declaring a SECOND pattern not to be a citation shape is a number in the diff
#: rather than a row - which is the half the two-way pin above cannot reach, for
#: the reason :func:`tests.bare_path_guard.non_citation_budget_problems` states:
#: a row added TOGETHER WITH the pattern it describes satisfies both directions.
#:
#: ONE IS NOT A PLACEHOLDER SIZE. The identical instrument at the identical size
#: is already live over a one-row table -
#: :data:`tests.test_bare_path_citations._SEPARATE_GUARD_CEILING` - and the
#: value is spent EXACTLY, so the slack direction refuses banked room too.
#: 1 TO 4 WHEN CS-937 ADDED THE CLAIM LEG. Three patterns arrived that judge a
#: pointer without deciding what carries a citation: they find a backticked
#: span, a sentence boundary and a line-leading comment marker. None of them
#: can make a citation exist, so admitting them to `JUDGED_SHAPES` would widen
#: the carrier boundary on the strength of a sentence parser - which is the
#: permissive direction this module refuses everywhere else. Each is declared
#: here in the same change as the pattern it describes, which is the two-way
#: pin the comment above names.
NON_CITATION_PATTERN_CEILING: Final = 4


#: The pointers the forbid rule DOES NOT reach, pinned so the hole stays
#: countable. A ``.yml``, ``.md`` or ``.toml`` target has no symbol form, so
#: forbidding the line form there would leave no way to cite it at all - the
#: rule would be asking for something that does not exist. That is a STATED
#: PRICE rather than a convenient boundary: these pointers rot on an edit above
#: them exactly as the Python ones do, and nothing in this module checks their
#: content either.
#:
#: Pinned as sites for :data:`tests.test_citation_tables.UNVERIFIED_LINE_POINTERS`' reason - a count
#: alone
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
        judges by, so the count cannot disagree with what the arm sees. A VIEW
        over :func:`citation_site_offsets` since CS-1121 - the length of what
        that returns, never a second traversal that could answer differently.
    """
    return len(citation_site_offsets(text, cited))


def citation_site_offsets(text: str, cited: str) -> list[int]:
    """WHERE each judged spelling of one citation begins in ``text``.

    THE OWNER OF THE THREE SHAPES, from which both the count and the identity
    are derived. Keeping one traversal is not tidiness: the count is what the
    forgiveness table was keyed on until CS-1121 and the identity is what it is
    keyed on now, and two traversals would let the table's key and the table's
    audit disagree about the same doc.

    Args:
        text: The scoped doc text - the same text the arm reads.
        cited: A full ``path.py::name`` key, a :func:`line_key` pointer key, or
            a bare identifier key.

    Returns:
        Ascending character offsets into ``text``, one per judged spelling.
    """
    if "::" in cited:
        path, _, name = cited.partition("::")
        return [
            match.start()
            for match in CITATION_RE.finditer(text)
            if match.group(1, 2) == (path, name)
        ]
    pointer = LINE_POINTER_RE.fullmatch(cited)
    if pointer:
        want = (pointer.group(1), pointer.group(2))
        return [
            match.start() for match in LINE_POINTER_RE.finditer(text) if match.group(1, 2) == want
        ]
    return [offset for offset, name in judged_bare_hits(text) if name == cited]


class UnanchoredCitationSiteError(RuntimeError):
    """A citation site sits above its doc's first heading, so it has no identity.

    Raised rather than digested, because two failed lookups must never compare
    equal - :func:`citation_site_identities` carries the mechanism. CAUGHT PER
    ENTRY by :func:`disposition_site_problems` and reported as a finding that
    names the carrier: an unanchorable site must not abort the grading of every
    other entry, which is what a bare propagation did.

    CARRIES A NAMED FIELD BECAUSE THE CATCHER MUST NOT RENDER THE OBJECT.
    ``tests/test_exception_rendering.py`` sweeps the whole tree for a caught
    exception formatted whole, on CLAUDE.md non-negotiable 12 - ``str()`` on an
    OSError appends the path it failed on, which carries the account name - and
    the rule is enforced by shape rather than by type, so a tree-local exception
    is swept too. The catcher renders :attr:`line` and writes its own sentence.
    """

    def __init__(self, message: str, line: int) -> None:
        """Record the message and the 1-based line the unanchored site sits on.

        Args:
            message: What went wrong, for anyone who raises without catching.
            line: The 1-based line number of the site that has no chain.
        """
        super().__init__(message)
        self.line = line


def heading_chain(text: str, line: int) -> tuple[str, ...]:
    """The headings enclosing ``line``, outermost first.

    AN INSTANCE, NOT A TEXT, and that distinction is CS-1121's second
    refutation. The identity keyed on the NEAREST heading alone, and live docs
    repeat heading text hard - one item-notes leaf spells one ``### detail``
    sub-heading under many distinct ``## CS-nnn`` sections, and in the worst
    carrier one heading text recurs repeatedly. Two sites in different
    sections therefore produced the SAME identity, so deleting a forgiven site
    and re-adding the identical line under another section was silent.
    Measured on the live table before this repair. It is the mirror of the fault
    :class:`UnanchoredCitationSiteError` fences: there, two FAILED lookups would
    have compared equal; here, two SUCCESSFUL lookups of different sites did.

    The chain separates them because the enclosing ``## CS-440`` and
    ``## CS-400`` differ even where the ``### detail`` beneath them does not.

    WHAT IT STILL CANNOT SEE, disclosed rather than left to be found: two sites
    under the IDENTICAL chain - the same sub-heading twice inside one section,
    or the same line twice in one section - remain one chain, which is what the
    ordinal beneath it is for. And a heading is a line starting with ``#``,
    which is ``tests.bare_path_guard.markdown_anchor``'s own rule: a setext
    underline is not seen, and a ``#`` inside a fenced code block is. Those are
    inherited from the convention, not introduced here.

    THE IDENTITY NO LONGER CALLS THAT FUNCTION AT ALL, which answers the
    common-mode risk rather than arguing around it. It was the shared input to
    the identity, to :attr:`tests.bare_path_guard.BarePathSite.identity` and to
    the arm that measured the collapse, so nothing routed through it could
    observe its own granularity being wrong. This walk is independent of it;
    what they share is only the one-line rule for recognising a heading.

    Args:
        text: The doc text.
        line: 1-based line number of the site.

    Returns:
        One heading per open level, outermost first, stripped. Empty above the
        first heading.
    """
    stack: list[tuple[int, str]] = []
    for number, raw in enumerate(text.split(NEWLINE), start=1):
        if number > line:
            break
        if not raw.startswith("#"):
            continue
        level = len(raw) - len(raw.lstrip("#"))
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, raw.strip()))
    return tuple(heading for _level, heading in stack)


def citation_site_anchors(text: str, cited: str) -> tuple[str, ...]:
    """The heading each judged spelling of ``cited`` sits under, in site order.

    THE READABLE HALF of the identity :data:`tables.DISPOSITIONS` records. The
    table stores digests; a failure report renders this, so a mismatch names
    the entry a human has to go and read rather than twelve hex characters.
    REPORTING ONLY - :func:`citation_site_identities` does not call this, and
    must not, because it needs the line beside the heading from the same
    traversal.

    Args:
        text: The scoped doc text.
        cited: The disposition key.

    Returns:
        One rendered chain per site, ascending by offset, duplicates kept. An
        unanchored site renders as the empty string here rather than raising,
        because a report about a failure must not fail.
    """
    return tuple(
        " / ".join(heading_chain(text, text.count(NEWLINE, 0, offset) + 1))
        for offset in citation_site_offsets(text, cited)
    )


def citation_site_identities(text: str, cited: str) -> tuple[str, ...]:
    """WHICH sites of ``cited`` this doc spells, as the identity CS-1121 keys on.

    AN IDENTITY, NOT A CARDINALITY, and that is the whole item. A count is
    satisfied by ANY set of the same size, so a COMPENSATING SWAP is silent:
    delete the one adjudicated site and add a brand-new dead citation of the
    same name in the same edit, and the cardinality never moves while an
    unadjudicated citation rides under a forgiveness written about a different
    one. Measured before the repair, on a live ledger entry, by
    ``test_a_compensating_swap_that_keeps_the_site_count_is_reported``. CS-893
    repaired the identical fault in ``tests/chained_exemption_guard.py``,
    whose cited precedent was this very table.

    THE IDENTITY IS THE ENCLOSING HEADING AND NEVER A LINE NUMBER. The ledger
    is append-only newest-first, so prepending one entry moves every site below
    it and rewrites nothing under any heading - a line-keyed table would churn
    on an edit that changed none of what it records. It is the same derivation
    :attr:`tests.bare_path_guard.BarePathSite.identity` already keys on, reused
    rather than reinvented.

    TWO DERIVED HALVES AND AN ORDINAL, all through :func:`landing_digest` and
    all from the ONE :func:`citation_site_offsets` traversal: the digest of the
    enclosing heading CHAIN, the digest of the LINE the site sits on, then
    0, 1, 2 ... among sites sharing BOTH. Nothing is transcribed and nothing is
    a line number. WHY IT IS SHAPED THIS WAY is argued once at
    :attr:`tables.Disposition.at`; what the CHAIN buys over the nearest heading
    alone is argued at :func:`heading_chain`.

    A SITE UNDER NO HEADING RAISES RATHER THAN DIGESTING THE EMPTY STRING. The
    chain is empty above the first heading and ``landing_digest("")`` is one
    fixed value, so digesting it would make every unanchored site anywhere
    compare EQUAL to every other - two failed lookups reading as a match, a
    shape this project has already been bitten by. Such a site cannot be
    identified, so it must not be silently forgiven.

    THE COUNT REMAINS RECOVERABLE, which is what keeps the older direction
    honest: duplicates are kept, so a site arriving with no deletion lengthens
    the tuple exactly as it used to raise the count.

    Args:
        text: The scoped doc text.
        cited: The disposition key.

    Returns:
        ``<heading digest>:<line digest>:<ordinal>`` per site, in ascending
        offset order, duplicates distinguished by the ordinal.

    Raises:
        UnanchoredCitationSiteError: A site sits above the doc's first heading,
            so it has no identity to record.
    """
    lines = text.split(NEWLINE)
    seen: Counter[str] = Counter()
    identities: list[str] = []
    for offset in citation_site_offsets(text, cited):
        index = text.count(NEWLINE, 0, offset)
        chain = heading_chain(text, index + 1)
        if not chain:
            raise UnanchoredCitationSiteError(
                f"{cited} is spelled above the first heading of its doc, so it has no"
                " enclosing chain. Digesting the empty chain would make it compare"
                " equal to every other unanchored site anywhere; give the doc a"
                " heading above the site, or do not record a forgiveness for it.",
                index + 1,
            )
        both = f"{landing_digest(NEWLINE.join(chain))}:{landing_digest(lines[index])}"
        identities.append(f"{both}:{seen[both]}")
        seen[both] += 1
    return tuple(identities)


def disposition_site_problems(
    texts: Mapping[str, str],
    dispositions: Mapping[tuple[str, str], Disposition],
) -> list[str]:
    """Every recorded disposition whose IDENTIFIED sites no longer match its doc.

    KEYED ON WHICH, NOT ON HOW MANY, since CS-1121. A cardinality is satisfied
    by any set of the same size, so a compensating swap in one edit passed in
    silence with an unadjudicated citation riding under the old forgiveness.
    Comparing the identity MULTISET reports both halves of that swap.

    A MULTISET AND NOT A TUPLE, which is a decision rather than an oversight.
    The comparison was ordered while this sentence said multiset, and the two
    disagreed on exactly one input: a reorder of two sections, which an ordered
    comparison called a problem and then described as "0 unforgiven, 0
    unspelled" - a finding naming nothing. A reorder changes neither which
    citations are forgiven nor where any site sits relative to its own heading
    chain, so it is NOT a finding, and the code now agrees with the sentence.

    Args:
        texts: Guarded doc path to its scoped text.
        dispositions: The recorded answers.

    Returns:
        One line per entry whose recorded sites have drifted, in either
        direction. A site the doc spells that the record does not name is a NEW
        dead citation arriving under an old forgiveness; a site the record
        names that the doc no longer spells is a record that has outgrown what
        it answers. Both are the table drifting from the corpus, and the table
        is only worth what it is checked against.
    """
    problems: list[str] = []
    for (doc, cited), recorded in sorted(dispositions.items()):
        text = texts.get(doc, "")
        try:
            found = citation_site_identities(text, cited)
        except UnanchoredCitationSiteError as unanchored:
            # PER ENTRY, NOT A WHOLE-RUN ABORT. Propagating this took down every
            # consuming arm as an ERROR, so one unanchorable site anywhere in the
            # corpus stopped the other entries being graded at all. The refusal
            # stands; it is reported as a finding against the entry that earned it.
            problems.append(
                f"{doc} :: {cited} - spelled at line {unanchored.line}, above the"
                " doc's first heading, so it has no enclosing chain and no identity"
            )
            continue
        arrived = Counter(found) - Counter(recorded.at)
        departed = Counter(recorded.at) - Counter(found)
        if not arrived and not departed:
            # A REORDER IS NOT A FINDING, and this is the line that decides it.
            # The comparison is a MULTISET, so two sections swapping places -
            # which changes neither what is forgiven nor where any site sits
            # relative to its own heading chain - passes. An ordered comparison
            # called that a problem and then rendered it as "0 unforgiven, 0
            # unspelled", a report naming nothing, which is worse than silence.
            continue
        # Rendered from the LIVE doc rather than from the record, so the report
        # names chains a reader can go and open. The record's own side is
        # digests by construction - see citation_site_identities.
        problems.append(
            f"{doc} :: {cited} - forgives {len(recorded.at)} identified site(s),"
            f" the doc spells {len(found)}:"
            f" {sum(arrived.values())} unforgiven, {sum(departed.values())} unspelled."
            f" Live sites: {list(citation_site_anchors(text, cited))}"
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
        doc: The repo-relative doc path, used to key
        :data:`tests.test_citation_tables.DISPOSITIONS`.
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
    table = tables.DISPOSITIONS if dispositions is None else dispositions
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
# is grandfathered into :data:`tests.test_citation_tables.UNVERIFIED_LINE_POINTERS`.
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
    table = tables.DISPOSITIONS if dispositions is None else dispositions
    grandfathered = dict(tables.UNVERIFIED_LINE_POINTERS if baseline is None else baseline)
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
#: CS-1066 MOVED SEVEN OF THE EIGHT ROWS AND NOT THE MECHANISM. A table and the
#: contract that bounds it must live in ONE module -
#: :func:`tests.bare_path_guard.registry_problems` requires a bounded table's
#: contract to be a callable that module defines - so the seven relocated tables
#: took their budgets and their contracts with them to
#: `tests/test_citation_tables.py`, and are registered there. TWO STAY, and for
#: the same reason rather than two: each one's contract cannot travel.
#: `UNFORBIDDEN_LINE_POINTERS` reads the `live_line_pointers` fixture, derived
#: by :func:`line_pointer_sites` in this file, and the dependency between the
#: two modules runs ONE WAY on purpose. :data:`NON_CITATION_PATTERNS` is read
#: by the carrier boundary in this module and named in the walk that grades it,
#: so a budget held one module over would be a bound on a table its own
#: registry does not hold - which :func:`tests.bare_path_guard.registry_problems`
#: refuses by name.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {
    "NON_CITATION_PATTERNS": (
        "test_the_non_citation_pattern_budget_is_spent_exactly_and_cannot_grow"
    ),
    "UNFORBIDDEN_LINE_POINTERS": (
        "test_the_unforbidden_line_pointer_residual_is_pinned_in_both_directions"
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
    "ADR_DOCS": "derived from the filesystem, and widens GUARDED_DOCS",
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
    return [name for _offset, name in judged_bare_hits(text)]


def judged_bare_hits(text: str) -> list[tuple[int, str]]:
    """:func:`judged_bare_names`, keeping the offset each match was found at.

    THE OWNER OF THE RULE, and :func:`judged_bare_names` is a VIEW over it
    rather than a second traversal. CS-1121 needed WHERE each judged spelling
    sits, not merely how many there are, and the first prototype of that
    re-implemented the blanking and the two patterns in the module that holds
    the table. Measured, that copy was wrong on one of nine live keys - it
    reported three sites where this rule reports one. A second code path
    computing the same thing is the drift this module spends its whole length
    refusing; so the offsets are exposed here, beside the patterns, and nothing
    else reads them.

    BLANKED LENGTH-FOR-LENGTH RATHER THAN TO ONE SPACE, and that is the whole
    reason this is not a pure extraction. A full citation collapsed to a single
    space shortens the text, so every offset after it points at the wrong
    character and any line derived from it names the wrong line. Spaces do not
    contain a newline and neither does :data:`CITATION_RE`, so the substitution
    preserves both the length and the line structure of the text it reads.
    THE JUDGED POPULATION IS ARGUED UNCHANGED BY IT - both patterns refuse a
    name preceded by ``:``, ``.`` or a word character, and one space and
    several are the same character to that lookbehind - AND THAT ARGUMENT IS
    NOT WHAT THE ARM BELOW GRADES. ``test_every_offset_indexes_the_name_it_found``
    asserts that every offset returned indexes, in the ORIGINAL text, the name
    it is paired with. That is the property the callers depend on and a
    collapse to one space breaks it; it is NOT a population comparison under
    the lookbehind change, and this sentence said it was. The population claim
    stands on the lookbehinds alone and nothing re-measures it.

    THE FIGURE THAT USED TO CARRY IT IS GONE: this docstring once gave the
    population as a spelled number that matched no live count anybody could
    reproduce - the carriers, the guarded docs and the tracked files are three
    different sizes and it was none of them.

    Args:
        text: The scoped doc text.

    Returns:
        ``(offset, identifier)`` per match, ascending by offset, duplicates
        included. The offset indexes ``text`` itself, which is what makes it
        usable for a line - see the blanking note above.
    """
    stripped = CITATION_RE.sub(lambda match: " " * len(match.group(0)), text)
    # start(1), not start(). ELIDED_RE's match BEGINS at the "::" it requires,
    # so a plain match start indexes two characters before the identifier it
    # names. Both spellings report where the NAME is, which is the only reading
    # under which the offset means what its caller assumes. Caught by
    # test_every_offset_indexes_the_name_it_found on its first run.
    found = [(match.start(1), match.group(1)) for match in BARE_RE.finditer(stripped)]
    found += [(match.start(1), match.group(1)) for match in ELIDED_RE.finditer(stripped)]
    return sorted(found)


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
        doc: The repo-relative doc path, used to key
        :data:`tests.test_citation_tables.DISPOSITIONS`.
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
    table = tables.DISPOSITIONS if dispositions is None else dispositions
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
    or any call at all, would make :data:`tests.test_archive_rot.ARCHIVE_ROT` agree with the
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
    unrecorded, _stale = guarded_set_problems(markdown_texts, GUARDED_DOCS, tables.UNGUARDED_DOCS)

    assert not unrecorded, (
        "markdown carrying citations that nothing guards and nothing records:\n"
        + "\n".join(f"  {doc}" for doc in unrecorded)
        + "\nGuard it, or record it in UNGUARDED_DOCS with the reason."
    )


def test_every_recorded_unguarded_doc_still_needs_its_record(
    markdown_texts: Mapping[str, str],
) -> None:
    """The other direction, for the reason the disposition table has one.

    See :data:`tests.test_citation_tables.DISPOSITIONS`: a record that outlives
    what it answered is a false declaration waiting to be believed.
    """
    _unrecorded, stale = guarded_set_problems(markdown_texts, GUARDED_DOCS, tables.UNGUARDED_DOCS)

    assert not stale, "stale entries in UNGUARDED_DOCS:\n" + "\n".join(
        f"  {problem}" for problem in stale
    )


def test_every_unguarded_record_states_a_reason_and_none_is_also_guarded() -> None:
    """The record's own shape, so an entry cannot be a bare path with no case."""
    for doc, why in tables.UNGUARDED_DOCS.items():
        assert why.strip(), f"{doc} is recorded as unguarded and states no reason"
        assert doc not in GUARDED_DOCS, f"{doc} is recorded as unguarded AND listed as guarded"


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
        markdown_texts, [doc for doc in GUARDED_DOCS if doc not in newly], tables.UNGUARDED_DOCS
    )
    assert withheld == newly, (
        "withholding the new members did not report them back, so the boundary never "
        "reached the fifth shape and the check below measures nothing"
    )

    unrecorded, stale = guarded_set_problems(markdown_texts, GUARDED_DOCS, tables.UNGUARDED_DOCS)

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
    for doc, cited in tables.DISPOSITIONS:
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
    """A forgiveness is granted per SITE, not per name, and it names WHICH sites.

    The table's keys are ``(doc, name)``, so without this a single adjudicated
    dead citation buys silence for every later citation of the same name in the
    same doc. That is not hypothetical: three new ledger entries, each citing a
    name this table already forgives, were planted and the module stayed green
    on all three. A dead pointer written today is a defect whatever was
    adjudicated about the same name a year ago.

    A COUNT ANSWERED THAT AND ONLY THAT, which is CS-1121: it says how many
    sites a record forgives and never which, so any set of the same size
    satisfies it and a COMPENSATING SWAP in one edit is silent. The key is an
    identity multiset now, and the sibling arms below perform the swap on this
    very table - across headings and within one - and assert it reddens. Why
    neither half of that identity is a line number: :attr:`tables.Disposition.at`.
    """
    texts = disposition_texts(line_pointer_carriers)

    problems = disposition_site_problems(texts, tables.DISPOSITIONS)

    assert not problems, (
        "DISPOSITIONS no longer matches the docs it forgives:\n"
        + "\n".join(f"  {problem}" for problem in problems)
        + "\nA site that appeared since the record was written is a NEW citation."
        " Adjudicate it, then record the site it sits at."
    )


def test_a_second_site_for_a_forgiven_citation_is_reported() -> None:
    """The control, in both spellings, so the key is not a decorative field.

    THE SECOND SITE SITS UNDER A DIFFERENT HEADING, which is what makes this a
    statement about the identity rather than about the size. The record answers
    the first heading; the arrival under the second is reported as UNFORGIVEN
    while the first stays spelled, so the report distinguishes an addition from
    a move. A cardinality could not tell those apart.
    """
    bare_cited = "test_a_name_that_is_not_bound"
    full_cited = bare_path("tests", "synthetic", "test_planted.py") + "::" + "test_a_name_thats_out"
    first = f'## The adjudicated entry\n\ngrep -c "{bare_cited}" x\nsee `{full_cited}`\n'
    second = f"\n## A later entry nobody adjudicated\n\n{first.partition(NEWLINE * 2)[2]}"
    once = {"ROADMAP.md": first}
    twice = {"ROADMAP.md": first + second}
    one_of_each = {
        ("ROADMAP.md", bare_cited): Disposition(
            DELIBERATE, "", "cited to prove it is dead", citation_site_identities(first, bare_cited)
        ),
        ("ROADMAP.md", full_cited): Disposition(
            NO_TARGET, "", "no test bears this meaning", citation_site_identities(first, full_cited)
        ),
    }

    assert disposition_site_problems(once, one_of_each) == [], (
        "the record did not match a doc spelling each citation once, so the report"
        " below proves nothing about a SECOND site"
    )
    reported = disposition_site_problems(twice, one_of_each)
    # Bound to a scalar before asserting: pytest renders the asserted expression
    # past the message, and the reports carry the heading text.
    arrivals = [line for line in reported if "1 unforgiven, 0 unspelled" in line]
    both_named_an_arrival = len(arrivals) == len(reported) == len(one_of_each)
    assert both_named_an_arrival, (
        f"a second site went unreported, or was reported as a move: {reported}"
    )


def test_a_disposition_for_a_citation_that_has_vanished_is_reported() -> None:
    """The other direction: a record that outlived what it answered."""
    cited = "test_a_name_that_is_not_bound"
    spelled = f'## An entry\n\ngrep -c "{cited}" x\n'
    table = {
        ("ROADMAP.md", cited): Disposition(
            DELIBERATE, "", "cited to prove it is dead", citation_site_identities(spelled, cited)
        )
    }

    problems = disposition_site_problems({"ROADMAP.md": "no pointer here at all\n"}, table)

    assert len(problems) == 1, "a record forgiving a citation nothing spells was accepted"
    assert "0 unforgiven, 1 unspelled" in problems[0], problems[0]


def test_every_correctable_disposition_names_a_target_and_the_others_do_not() -> None:
    """The table's own shape, so a MOVED entry cannot silently carry no target."""
    for (doc, cited), recorded in tables.DISPOSITIONS.items():
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
        assert recorded.at, (
            f"{doc}::{cited} names no site, so it answers nothing that is written"
            " - delete it, or record the sites it covers"
        )
        assert all(identity.strip() for identity in recorded.at), (
            f"{doc}::{cited} records an empty identity, which matches a site sitting"
            " under no heading at all and is never what an adjudication meant"
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
    table = {key: Disposition(DELIBERATE, "", "cited to prove it is dead", ())}

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
    missing = sorted(
        name
        for name, value in compiled.items()
        if value not in JUDGED_SHAPES and value not in NON_CITATION_PATTERNS
    )
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
            MOVED, "tests/synthetic/test_planted.py::test_a_real_one", "the target is live", ()
        )
    }

    assert unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table) == []


def test_a_disposition_whose_target_stopped_resolving_is_reported() -> None:
    """The mutant that survived until this test was written."""
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_planted.py::test_gone_now", "the target rotted", ()
        )
    }

    problems = unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table)

    assert len(problems) == 1, "a disposition pointing at a dead target was accepted"
    assert "does not resolve" in problems[0][2]


def test_a_disposition_whose_target_file_vanished_is_reported() -> None:
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_deleted.py::test_a_real_one", "the file is gone", ()
        )
    }

    assert len(unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table)) == 1


def test_a_bare_disposition_whose_target_stopped_resolving_is_reported() -> None:
    """The same non-default branch, on the arm that has no path to check."""
    text = 'Verification: `grep -c "test_a_name_that_is_not_bound" x.py`\n'
    key = ("ROADMAP.md", "test_a_name_that_is_not_bound")

    live = {key: Disposition(RENAMED, "tests/x.py::test_a_real_one", "live", ())}
    rotted = {key: Disposition(RENAMED, "tests/x.py::test_gone_now", "rotted", ())}

    assert bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], [], live) == []
    assert len(bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], [], rotted)) == 1


def test_a_no_target_disposition_forgives_without_naming_anything() -> None:
    """A disposition with nothing to verify forgives without naming a target.

    NO_TARGET and DELIBERATE must not be treated as a redirect carrying an
    empty target, which would resolve to nothing and report a defect on a
    citation that was deliberately left unassigned.
    """
    table = {_REDIRECT_KEY: Disposition(NO_TARGET, "", "no test bears this meaning", ())}

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

    problems = stale_pin_problems(live, tables.UNVERIFIED_LINE_POINTERS)

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
    adjudicated = {
        (doc, cited) for doc, cited in tables.DISPOSITIONS if LINE_POINTER_RE.fullmatch(cited)
    }
    grandfathered = {
        (carrier, line_key(path, line)) for carrier, path, line in tables.UNVERIFIED_LINE_POINTERS
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
    table = {
        key: Disposition(MOVED, f"{_SYNTHETIC_MODULE}::_live_target", "the target is live", ())
    }
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    assert line_pointer_content_problems(py_sites, other, _LANDING_SOURCE, table, {}) == ([], [])


def test_a_recorded_redirect_whose_target_stopped_resolving_is_reported() -> None:
    """A record that points at nothing forgives nothing, on the new arm too."""
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5))
    table = {key: Disposition(MOVED, f"{_SYNTHETIC_MODULE}::_gone_now", "the target rotted", ())}
    py_sites, other = line_pointer_sites(_planted(_SYNTHETIC_MODULE, 5), _LANDING_CORPUS)

    _empty, forbidden = line_pointer_content_problems(py_sites, other, _LANDING_SOURCE, table, {})

    assert len(forbidden) == 1, "a redirect at a dead target was accepted"
    assert "does not resolve" in forbidden[0]


def test_a_record_forgives_a_blank_landing_that_the_baseline_may_not() -> None:
    """An ADJUDICATED answer silences both legs; that is what adjudication buys."""
    key = ("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 3))
    table = {key: Disposition(NO_TARGET, "", "the carrier is append-only", ())}
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
    table = {("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 5)): Disposition(NO_TARGET, "", "x", ())}

    assert forgiveness_budget_problems((), table, 1) == []

    fabricated = dict(table)
    fabricated[("ROADMAP.md", line_key(_SYNTHETIC_MODULE, 4))] = Disposition(
        NO_TARGET, "", "looks plausible and answers nothing", ()
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
        for (carrier, path, line), pinned in sorted(tables.UNVERIFIED_LINE_POINTERS.items())
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
        if path not in tables.UNGUARDED_DOCS and not path.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
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
        if carrier in tables.UNGUARDED_DOCS or carrier.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
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


def test_no_absence_declaration_in_the_live_tree_has_outlived_its_prose(
    line_pointer_carriers: Mapping[str, str],
) -> None:
    """CS-899's third direction, on the live tree.

    A declaration buys silence for the citation on its own line and for nothing
    else, so prose that is rewritten takes its declaration with it. This arm is
    what makes that a property of the TREE rather than of the controls: a
    declaration left behind by an edit is reported here before anybody notices
    the sentence around it stopped saying what it said.

    THE POPULATION IS THE SAME ONE THE LADDER JUDGES, injected rather than
    re-derived, so the two cannot come to disagree about which files are read.
    """
    assert line_pointer_carriers, (
        "the carrier population is empty, so this arm would read no declarations "
        "and pass whatever it ignored"
    )

    problems = stale_declaration_problems(line_pointer_carriers)

    assert not problems, (
        "absence declarations that no longer forgive anything:"
        + NEWLINE
        + (NEWLINE.join(f"  {problem}" for problem in problems))
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
        and path not in tables.UNGUARDED_DOCS
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
        if path in tables.UNGUARDED_DOCS or path.startswith((DATED_ARCHIVE, OUT_OF_DOMAIN))
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
        tables.BARE_PATH_REASONS,
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
    for identity, recorded in sorted(tables.BARE_PATH_REASONS.items()):
        assert recorded.why.strip(), f"{identity} forgives a dead citation and states no evidence."
    problems = bare_path_reason_problems(live_bare_path_ladder, tables.BARE_PATH_REASONS)

    assert not problems, "BARE_PATH_REASONS no longer matches the corpus:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def test_a_compensating_swap_in_the_bare_path_reasons_is_reported_in_both_directions() -> None:
    """CS-893, ANSWERED RATHER THAN COPIED.

    That item was filed against this module because the forgiveness table then
    keyed on a bare count: delete one recorded site and add an unrelated one in
    the same edit, and the cardinality is unchanged and the swap is silent. The
    table below is keyed on an IDENTITY, so the same edit fails twice - the
    added entry answers nothing and the removed one is reported. CS-1121 has
    since carried the same repair into :data:`tables.DISPOSITIONS`, whose own
    swap arm is ``test_a_compensating_swap_that_keeps_the_site_count_is_reported``;
    this one stays because the two tables derive their identities differently
    and an arm shared between them would prove neither.

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

    AND THE ATTRIBUTE SPELLING, WHICH A FILE SPLIT REACHES FOR THE FIRST TIME.
    While every bounded table lived in the file that bounded it, the tautology
    could only ever be written ``len(TABLE)`` - a bare name. A table relocated
    into a sibling module is spelled ``len(tables.TABLE)``, and a walk that
    filters on :class:`ast.Name` alone cannot see it: the permanent disarm comes
    back, one dot wider, in a diff that still carries no number to query. CS-1066
    made that spelling writable here, so the leg arrived with the split.

    BOTH SOURCES, ONE ARM, AND THE REGISTRY IS THE ONE THAT OWNS THE TABLES. The
    names to look for come from `tests/test_citation_tables.py`, because that is
    where the seven relocated tables and their budgets now live; the SOURCES
    checked are that file - where the tautology is a bare name - and this one,
    where it can only be an attribute. Checking one file would leave the other's
    spelling unguarded, which is the hole the split opened.
    """
    here = Path(__file__).read_text(encoding="ascii")
    there = Path(tables.__file__).read_text(encoding="ascii")
    bounded = {**tables.FORGIVENESS_TABLES, **FORGIVENESS_TABLES}

    tautology = there + f"{NEWLINE}BARE_PATH_REASON_CEILING = len(BARE_PATH_REASONS){NEWLINE}"
    planted = derived_bound_problems(tautology, bounded)

    assert len(planted) == 1, (
        f"a ceiling computed from the table it bounds was not the single finding: {planted}"
    )
    assert "BARE_PATH_REASON_CEILING" in planted[0]

    qualified = here + f"{NEWLINE}BARE_PATH_REASON_CEILING = len(tables.BARE_PATH_REASONS){NEWLINE}"
    reached = derived_bound_problems(qualified, bounded)

    assert len(reached) == 1, (
        "a ceiling computed from a table held one module over was not the single"
        f" finding: {reached}. A walk that reads only a bare name is blind to every"
        " tautology a file split makes writable."
    )
    assert "BARE_PATH_REASON_CEILING" in reached[0]

    problems = [
        f"{name}: {problem}"
        for name, source in (("this module", here), (tables.__name__, there))
        for problem in derived_bound_problems(source, bounded)
    ]

    assert not problems, (
        "bounds computed from their own subject:"
        + NEWLINE
        + NEWLINE.join(f"  {problem}" for problem in problems)
    )


@pytest.mark.parametrize(
    ("rung", "pinned", "ceiling"),
    [
        (DECLARED_UNTRACKED, tables.DECLINED_AS_DECLARED_UNTRACKED, DECLARED_UNTRACKED_CEILING),
        (UNTRACKED_ROOT, tables.DECLINED_UNDER_AN_UNTRACKED_ROOT, UNTRACKED_ROOT_CEILING),
        (FIXTURE_LITERAL, tables.DECLINED_AS_A_FIXTURE_LITERAL, FIXTURE_LITERAL_CEILING),
        (DECLARED_ABSENT, tables.DECLARED_ABSENT_IN_DOC, DECLARED_ABSENT_CEILING),
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


def test_the_non_citation_pattern_budget_is_spent_exactly_and_cannot_grow() -> None:
    """THE SIXTH BUDGET, and the escape route this family shipped without one.

    The two-way pin above catches a row added ALONE. This catches the pair -
    a pattern compiled and declared a non-citation shape in the same change,
    which left every direction satisfied and carried no number to query.
    """
    problems = non_citation_budget_problems(NON_CITATION_PATTERNS, NON_CITATION_PATTERN_CEILING)

    assert not problems, NEWLINE.join(problems)


def test_appending_a_non_citation_pattern_spends_its_budget() -> None:
    """The adversary's move against a synthetic budget, and the slack direction too."""
    one = (re.compile("a"),)

    assert non_citation_budget_problems(one, 1) == []

    appended = (*one, re.compile("b"))
    grown = non_citation_budget_problems(appended, 1)

    assert len(grown) == 1, "an appended non-citation declaration was absorbed by the budget"
    assert "2 non-citation pattern declarations recorded against a ceiling of 1" in grown[0]

    slack = non_citation_budget_problems((), 2)

    assert len(slack) == 1, "a slack non-citation ceiling was accepted"
    assert "Lower it to 0" in slack[0]


def test_the_non_citation_pattern_ceiling_is_visible_to_the_derived_bound_check() -> None:
    """A BUDGET THE TAUTOLOGY CHECK CANNOT SEE IS A BUDGET THAT DISARMS IN ONE LINE.

    :func:`derived_bound_problems` reports a ceiling computed from its own
    subject only for a table the REGISTRY names, so registering the table is
    what arms the fence CS-1127's note states in capitals. Asserted here rather
    than assumed, because the registration and the ceiling are separable edits.
    """
    here = Path(__file__).read_text(encoding="ascii")
    bounded = {**tables.FORGIVENESS_TABLES, **FORGIVENESS_TABLES}

    assert "NON_CITATION_PATTERNS" in bounded, (
        "the table is not registered as bounded, so a ceiling derived from it is unguarded"
    )

    tautology = (
        here + f"{NEWLINE}NON_CITATION_PATTERN_CEILING = len(NON_CITATION_PATTERNS){NEWLINE}"
    )
    planted = derived_bound_problems(tautology, bounded)

    assert len(planted) == 1, (
        f"a non-citation ceiling computed from its own table was not the single finding: {planted}"
    )
    assert "NON_CITATION_PATTERN_CEILING" in planted[0]


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

    VERIFIED: deleting the leading-dot leg from :data:`tests.bare_path_guard._FIRST_SEGMENT` killed
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


# --- contract 11: CS-899 - discussing-prose in markdown is DECIDED, not forgiven


def test_discussing_prose_that_declares_the_absence_is_declined_with_no_record() -> None:
    """CS-899's acceptance, and the whole of it.

    Planted discussing-prose that DECLARES the absence it is talking about is
    green with NO entry in any forgiveness table, and the identical prose
    without the declaration still reports. The declaration is a MECHANISM
    rather than a recorded forgiveness because it names something the ladder
    CHECKS on every run - see the arm below for the other direction.

    BOTH HALVES IN ONE ARM, and a verifier is why. The first draft asserted
    only the green half, which is indistinguishable from a rung that answers
    EVERYTHING - a `declared_absent` stuck True passes the green half and every
    other unit arm here, and was caught only at tree level. The negative half
    below is what makes the green one mean something.
    """
    absent = bare_path("docs", "item_notes", "README.md")
    sentence = f"## Decision\n\nThe family gets no `{absent}` at all."
    prose = f"{sentence} <!-- absent: {absent} -->\n"
    sites = bare_path_sites({_SYNTHETIC_DOC: prose})

    declared = bare_path_ladder(sites, [LEDGER], (), {}, ())

    assert len(declared[DECLARED_ABSENT]) == 1, "a declared absence was not answered by its rung"
    assert bare_path_problems(declared) == [], "declared discussing-prose was reported"

    undeclared = bare_path_ladder(
        bare_path_sites({_SYNTHETIC_DOC: sentence + "\n"}), [LEDGER], (), {}, ()
    )

    assert undeclared[DECLARED_ABSENT] == [], "the rung answered prose that declares nothing"
    assert len(bare_path_problems(undeclared)) == 1, (
        "the identical prose WITHOUT the declaration was also green, so the rung above "
        "is answering everything rather than answering the declaration"
    )


def test_a_declared_absence_the_tree_binds_is_reported() -> None:
    """The other direction, which is what makes the declaration a rule.

    A recorded forgiveness names nothing to check and is spent forever. This
    declaration is falsifiable by the tree: the moment the path it calls absent
    becomes tracked, the carrier is REPORTED rather than silently wrong.
    """
    live = bare_path("docs", "LEDGER.md")
    sentence = f"## Decision\n\nThere is no `{live}` here."
    prose = f"{sentence} <!-- absent: {live} -->\n"
    sites = bare_path_sites({_SYNTHETIC_DOC: prose})

    bound = bare_path_ladder(sites, [LEDGER], (), {}, ())

    assert len(bound[DECLARED_ABSENT_BOUND]) == 1, "a declaration the tree falsifies was not caught"
    assert len(bare_path_problems(bound)) == 1, "a false absence declaration was not reported"

    plain = bare_path_ladder(
        bare_path_sites({_SYNTHETIC_DOC: sentence + "\n"}), [LEDGER], (), {}, ()
    )

    assert plain[DECLARED_ABSENT_BOUND] == [], (
        "the rung fired on a line carrying no declaration at all"
    )
    assert bare_path_problems(plain) == [], (
        "the same live path with NO declaration was reported, so the arm above is measuring "
        "resolution rather than the falsified declaration it claims to measure"
    )


def test_a_declaration_naming_a_path_its_line_does_not_spell_is_reported() -> None:
    """The third direction: a declaration cannot be left behind by its prose.

    The landmine CS-891's merger asked about and nobody answered. A record in a
    Python table outlives the sentence it forgives; a declaration on the line
    cannot, because a line carrying one and no matching spelling is REPORTED.
    """
    absent = bare_path("docs", "item_notes", "README.md")
    stranded = f"## Decision\n\nThe prose moved on. <!-- absent: {absent} -->\n"

    assert stale_declaration_problems({_SYNTHETIC_DOC: stranded}), (
        "a declaration whose line spells no such citation was accepted"
    )
    assert stale_declaration_problems({_SYNTHETIC_DOC: "## Decision\n\nNothing here.\n"}) == []


def test_a_declaration_inside_a_fixture_literal_silences_nothing_outside_it() -> None:
    """The SIBLING of the arm below, and it was found by a verifier rather than here.

    The walk that judges a declaration STALE applies R4; the collection that
    decides whether a site is declared absent did not. So a declaration written
    inside a non-docstring string literal silenced a genuinely dead citation
    spelled OUTSIDE that literal on the same line, and was exempt from the
    staleness direction besides - two of the three directions, on a shape whose
    docstring claims all three.

    ONE LINE, TWO CONTEXTS, AST-DECIDABLE, which is the same shape the arm
    below already had for the walk.
    """
    dead = bare_path("docs", _BARE_PLANT_LEAF)
    line = f'X = "<!-- absent: {dead} -->"  # see `{dead}` for detail\n'
    owned_root = [bare_path("docs", "LEDGER.md")]

    answered = bare_path_ladder(bare_path_sites({_SYNTHETIC_MODULE: line}), owned_root, (), {}, ())

    assert answered[DECLARED_ABSENT] == [], (
        "a declaration inside a fixture literal was read as the author declaring an"
        " absence, so it bought silence for a citation it does not sit with"
    )
    assert len(bare_path_problems(answered)) == 1, (
        "the dead citation outside the literal was silenced by a declaration inside it"
    )


def test_a_declaration_in_a_fixture_literal_is_declined_and_the_same_one_in_prose_is_not() -> None:
    """R4's teeth again, on the declaration walk rather than on the ladder.

    A control that plants a declaration to prove this walk fires spells that
    declaration inside a string literal, so a walk that read every line would
    report the module that proves it works. The partition is AST-decidable and
    it is the same one R4 already uses, which is why this is not a second rule
    with a second boundary to rot.
    """
    stranded = "<!-- absent: docs/nowhere.md -->"
    fixture = f'CORPUS = {{"note": "{stranded}"}}\n'
    prose = f'"""A note saying {stranded} and nothing else."""\n'

    assert stale_declaration_problems({_SYNTHETIC_MODULE: fixture}) == [], (
        "a declaration inside a non-docstring literal was read as a live one"
    )
    assert len(stale_declaration_problems({_SYNTHETIC_MODULE: prose})) == 1, (
        "the identical declaration in a DOCSTRING was declined, so the walk answers "
        "fixture data rather than the author talking"
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
