#!/usr/bin/env python
r"""Lane scope - which `ROADMAP.md` rows one lane may take, computed not asserted.

THE PROBLEM THIS EXISTS FOR. `tools/headless-queue.md` section 5 defines the
queue as `ROADMAP.md` read top to bottom, with the phase headings as the default
order. There has been no way to point a lane at a SUBJECT. The dashboard rows
are the worked example and they defeat every filter the file already supports:
they are not contiguous, they are not one phase, and one of them sits in the
phase 4 block entirely. A subject like that has to be written down.

A WRITTEN-DOWN LIST IS THE DEFECT UNLESS IT IS VALIDATED ON EVERY READ. An id
list that can quietly name a row that has closed, been gated, or vanished is
worse than no scope at all: the lane answers a shorter queue and nothing says
why. So ``validate_scope`` runs before any filtering, on every call, and a
member that is closed, gated, a phase gate row, or absent from `ROADMAP.md`
raises ``ScopeRefusedError`` naming the offender and the class it offends under.
**A scoped lane that finds nothing and a scoped lane whose scope is wrong are
different events and must never render the same.**

AND VALIDATING EACH MEMBER IS STILL NOT ENOUGH, WHICH WAS MEASURED ON THIS
MODULE'S FIRST ROUND. Every member can be a live takeable row while the list
holds only a QUARTER of the subject, because nothing graded what was MISSING. An
adversary narrowed the declaration from eight ids to two and the suite reported
35 green while the lane served two rows. That is the CS-988 defect class - a
population guarded by a floor and a subset rather than an equality - and the
answer is that a scope may declare an ``anchor_phase`` it PARTITIONS: every
takeable row of that phase must be a member or must be listed in ``excluded``
with a written reason, or it is ``UNCLASSIFIED`` and the lane refuses naming it.
The same narrowing now refuses with all six orphaned ids on the line.

THE PARTITION DOES NOT CLOSE IT ALONE EITHER, ALSO MEASURED. Moving one id from
``items`` into ``excluded`` in a single edit keeps the partition complete and
went green. `tests/ops/test_lane_scope.py` therefore pins the member set a
SECOND time, in that file, so the two live apart and a compensating edit in one
of them reddens. What neither mechanism closes is an edit to BOTH, which is the
standing limit of a two-copy agreement and is recorded rather than claimed shut.

THE FENCES ARE DERIVED, NOT TRANSCRIBED. `tools/headless-queue.md` section 5
carries six fences. Three of them are keyed on an item id and all three are
computed here from the files that OWN the fact rather than copied into this
module as a literal:

- FENCE 1, never a phase gate row. Derived from the row's own headline in
  `ROADMAP.md` - a gate row is the row whose headline opens ``Phase <n> gate:``.
  The four ids the prompt names are nowhere in this file, and
  `tests/ops/test_lane_scope.py` asserts the derived set EQUALS the set read out
  of the prompt's own fence sentence, so the two cannot drift apart in silence.
- FENCE 2, never anything `docs/GATED.md` says is BLOCKED. Derived by reading
  that file as a CLASSIFIED PARTITION rather than as a bare id scan: the wide
  scan is the population, a machine-readable block in that file classifies every
  id it finds as BLOCKED or MENTIONED, and an id nothing classifies is gated AND
  named. See ``gate_classification`` for the fourteen-row measurement that forced
  it and for why narrowing the scan instead would have been the denylist shape.
- FENCE 4, never anything on the do-not-redo set. Its id-bearing half is
  section 5b's closing clause, "AND EVERY ITEM ALREADY CLOSED", and that is
  derived from `docs/LEDGER.md`.

THREE FENCES ARE NOT ID-KEYED AND THIS MODULE DOES NOT PRETEND OTHERWISE.
FENCE 3 is about frozen FILES, not rows. FENCE 5 says `BACKLOG.md` is not the
queue, which holds here for free because nothing reads that file - a backlog id
named in a scope is simply ABSENT from `ROADMAP.md` and refuses. And the prose
half of the do-not-redo set - the settled DECISIONS in `CLAUDE.md` section 7 -
names no ids at all and is unmechanizable from here. It stays prose in the
prompt, and a worker can still rationalise past it. That is the residual cost
and it is stated rather than hidden.

WHY THE LEDGER READ IS ANCHORED, AND WHY ITS IDS FIELD IS NOT. `docs/LEDGER.md`'s
entry shape puts the verdict immediately after the ids, and the live file carries
headings reading "NOT A COMPLETION RECORD. NOTHING CLOSED. CS-nnn STAYS OPEN". An
unanchored search for the word CLOSED would close the very item such a heading
exists to keep open, so the VERDICT is matched at its START and nowhere else.

The IDS field goes the other way, and a first cut got it wrong in the dangerous
direction. It pattern-matched the field as ids joined by a SPACE, which reads
nothing from the 24 live headings that join with a comma or with the word "and" -
so a heading closing two items closed neither, and both rows stayed TAKEABLE. A
missed closure is not the same class of failure as a missed member: the member
refuses loudly, the closure just silently leaves a done row in the queue. So the
ids are recognised and SUBTRACTED, and the residue decides - see ``_PUNCTUATION``.
The failure direction that remains is a closure whose verdict is spelled some
third way, which reads as ABSENT rather than CLOSED: still a loud refusal, one
class less precise.

NOTHING HERE TAKES A ROW. This module answers WHICH rows are takeable. Choosing
among them, and doing the work, stays with the worker.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# THE REPOSITORY ROOT, PUT ON THE PATH AHEAD OF THE PACKAGE IMPORT BELOW, and
# it is a measured fix rather than defensive scaffolding. The detached driver
# runs as `pythonw <repo>/ops/loop/queue_loop.py`, which puts `ops/loop` on
# `sys.path` and the repository root NOWHERE, and it binds this file BY PATH
# through `queue_loop._bind`. So the import under this comment is guaranteed to
# fail on exactly the run that matters and guaranteed never to fail in a suite,
# every arm of which puts the root on the path itself. MEASURED: one real
# detached cycle, run to prove the launch path end to end, died here inside
# `run_loop` before its first acquire - no lane lock, no worker, no JSONL row,
# and a traceback no operator was awake to read.
#
# THE PACKAGE ROUTE, NOT A SECOND FILE-PATH LOADER - that is CS-1000 one file
# over. `importlib` consults `sys.modules` before it looks for a loader, so a
# copy a sibling has already published under `ops.loop.lanes` is what this
# import receives; repairing the path repairs it for every later importer
# rather than minting one more private copy with its own `_OWNED` table.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ops.loop import lanes  # noqa: E402

#: An item LINE in `ROADMAP.md`: the id at column zero, then the spaced-hyphen
#: clause break the whole project uses. The file's own prose carries ``CS-nnn -``
#: as a shape example and ``CS-900, then`` in a sentence; neither matches.
#:
#: THE ``CS-G`` SERIES IS ADMITTED, and its absence was a measured hole rather
#: than a style choice. `docs/GATED.md`'s own header prescribes that a gated item
#: which unblocks moves to `ROADMAP.md` UNDER ITS OWN ``CS-G`` ID. A pattern
#: reading only ``CS-[0-9]+`` sees no such line at all, so that row would be
#: INVISIBLE to the lane rather than takeable - and invisible is the worse of the
#: two failures, because a takeable row refuses loudly when something is wrong
#: with it while a row nobody parses is a row nobody can miss.
_ITEM_LINE = re.compile(r"^(CS-[A-Z]*[0-9]+) - (.*)$")

#: A phase heading in `ROADMAP.md`. The headings are the single owner of which
#: phase a row belongs to.
_PHASE_HEADING = re.compile(r"^## (Phase [0-9]+)\b")

#: FENCE 1, derived. A gate row says so in its own headline.
_GATE_HEADLINE = re.compile(r"^Phase [0-9]+ gate:")

#: Any item id, wherever it appears. Used for `docs/GATED.md`, which names its
#: blocked rows in prose rather than on item lines. THE WIDE SCAN SURVIVES THE
#: PARTITION BELOW AND IS NOT THE THING TO NARROW - see ``gate_classification``.
_ANY_ID = re.compile(r"CS-[0-9]+")

#: THE CLASSIFICATION BLOCK IN `docs/GATED.md`, which turns the wide scan from a
#: FENCE into a PARTITION. The scan says which ids that file names; the block
#: says, for each one, whether a gate BLOCKS the row or the file merely MENTIONS
#: it. An id the scan finds and the block does not classify is GATED and
#: REPORTED - omission fails CLOSED, which is what makes the block an allowlist
#: rather than the denylist shape this project has measured leaking four times.
_CLASSIFY_BEGIN = "CLOCKSPEED-GATE-CLASSIFICATION BEGIN"
_CLASSIFY_END = "CLOCKSPEED-GATE-CLASSIFICATION END"

#: One classification line, matched ONLY between the sentinels. The block is the
#: classifier, not the line shape: a sentence in gate prose that happens to read
#: like a classification must not unfence a row, or quoting the mechanism inside
#: the file it governs would switch it off - the fenced-block trap
#: `.githooks/commit-msg` already records one instance of.
_CLASSIFY_LINE = re.compile(r"^gate: (CS-[0-9]+) (?:BLOCKED (CS-G[0-9]+)|MENTIONED)$")

#: Any item id INCLUDING the ``CS-G`` gated series, which a ledger heading can
#: name alongside ordinary ids. Tokenising the G series too is what keeps the
#: residue test below clean when a heading closes a mixed set.
_ID_TOKEN = re.compile(r"CS-[A-Z]*[0-9]+")

#: A `docs/LEDGER.md` entry heading, split LOOSELY into its date, an ids field
#: and the verdict that follows. The ids field is NOT pattern-matched as a list
#: of ids joined by a fixed separator, and that is the repair: a first cut
#: spelled it ``CS-nnn(?: CS-nnn)*``, which accepts only a SPACE and so read
#: nothing at all from the 24 live headings that join their ids with a comma or
#: with the word "and". A heading it fails to read leaves every id in it
#: unclosed and therefore still TAKEABLE - a silent widening, not a loud
#: refusal, which is the opposite of what this module promises.
_LEDGER_HEADING = re.compile(r"^### (?P<date>\S+) - (?P<ids>.*?) - (?P<verdict>.*)$")

#: WHAT SEPARATES TWO IDS IS DERIVED, NOT LISTED. The ids are recognised and
#: REMOVED; whatever is left must carry no substance. After whitespace and
#: commas are dropped the residue may only be repetitions of the one English
#: conjunction the file actually uses, so ``CS-a, CS-b and CS-c`` reads while
#: ``CS-407 PARTIAL`` and ``CORRECTION to the CS-922 record`` are rejected -
#: their residue is a word, which means the field is prose that merely mentions
#: an id rather than a field that names the entry's subjects.
_PUNCTUATION = re.compile(r"[\s,]+")
_CONJUNCTION_ONLY = re.compile(r"(?:and)*$")

#: A closure. Anchored at the START of the verdict field - see the module
#: docstring on why an unanchored search is a live trap on this file.
_CLOSURE_VERDICT = re.compile(r"^CLOSED\b")

#: The declaration file, relative to the repository root.
SCOPES_FILE = "config/lane_scopes.json"

#: Why a declared member cannot be taken. These strings reach a worker's
#: terminal, so they are the vocabulary of the refusal and not internal tags.
ABSENT = "absent"
CLOSED = "closed"
GATED = "gated"
PHASE_GATE = "phase_gate"

#: The three faults an ANCHORED scope can carry. An anchored scope promises to
#: PARTITION a phase rather than merely list some of it, and these are the three
#: ways that promise breaks. UNCLASSIFIED is the one that matters most: without
#: it, deleting a member shortens the subject and nothing anywhere notices,
#: which is the defect this module was refuted for on its first round.
#: FENCE 2's own fault, and the one that makes the partition an allowlist. An
#: id `docs/GATED.md` NAMES that its classification block does not classify is
#: fenced AND named - both, never either. Fencing it silently would be the
#: narrowing ``fenced_faults`` already refuses over; naming it without fencing it
#: would make a forgotten block a fail-open lever.
UNCLASSIFIED_GATE_MENTION = "named_in_gated_md_and_classified_by_no_block"

CONTRADICTED = "in_items_and_excluded"
STALE_EXCLUSION = "excluded_but_not_a_takeable_anchor_row"
UNCLASSIFIED = "anchor_phase_row_neither_member_nor_excluded"

#: The three ways the row a cycle WORKED fails to bind to the rows its lane was
#: PERMITTED to work - see :func:`binding_fact`. These strings are written into
#: the cycle record and read by an operator at 3am, so they are the vocabulary
#: of the refusal rather than internal tags, and each one sends a reader
#: somewhere different: to the declaration, to the worker log, to the prompt.
UNCOMPUTED = "the_lanes_takeable_rows_could_not_be_computed"
OUT_OF_SCOPE = "a_row_this_lane_may_not_take"
UNNAMED = "the_cycle_committed_while_claiming_no_row"

#: A scope declaration whose file is missing, unreadable or malformed answers
#: nothing rather than guessing - and a lane pointed at a scope then refuses,
#: because an unknown name is a refusal.
_EMPTY: dict[str, dict[str, Any]] = {}


@dataclass(frozen=True)
class Row:
    """One `ROADMAP.md` item line.

    Attributes:
        item_id: The permanent ``CS-`` id.
        line_no: One-based line number, which is what gives the lane its order.
        phase: The phase heading this row sits under, or ``""`` above the first
            one. A string rather than None so a sorted() in a failure message
            cannot itself raise.
        headline: Everything after the id and its clause break.
    """

    item_id: str
    line_no: int
    phase: str
    headline: str


@dataclass(frozen=True)
class ScopeFault:
    """One declared member that cannot be taken, and why.

    Attributes:
        item_id: The offender, named so a refusal is actionable.
        reason: One of ABSENT, CLOSED, GATED or PHASE_GATE.
    """

    item_id: str
    reason: str


class ScopeRefusedError(RuntimeError):
    """A lane was pointed at a scope that cannot be honoured.

    Raised rather than returned, and never downgraded to an empty result. An
    empty result is a claim about the queue; this is a claim about the
    declaration, and collapsing the two is the defect the scope mechanism
    exists to prevent.

    Attributes:
        scope_name: The scope that was asked for.
        faults: The offending members. EMPTY when the scope name itself is not
            declared, which is a refusal about the name rather than its rows.
        detail: The human-readable body. Render THIS, never the exception
            object - see the field's own comment below.
    """

    def __init__(self, scope_name: str, faults: tuple[ScopeFault, ...], detail: str) -> None:
        """Build the refusal.

        Args:
            scope_name: The scope that was asked for.
            faults: The offending members, possibly empty.
            detail: The human-readable body.
        """
        super().__init__(detail)
        self.scope_name = scope_name
        self.faults = faults
        #: The human-readable body, kept as a NAMED FIELD because rendering the
        #: exception OBJECT is an echo path - str() on an OSError appends the
        #: path it failed on, which carries the account name (CLAUDE.md
        #: non-negotiable 12). Callers render this, never the exception.
        self.detail = detail


#: THIS CHECKOUT, and deliberately NOT ``lanes.REPO_ROOT``. That constant
#: resolves the MAIN working tree through the ``.git``-file indirection, which is
#: the right answer for a lane LOCK - the lock is a machine-wide control plane
#: and every worktree must contend for the same one. It is the wrong answer here.
#: A worker runs in its own worktree, and reading the main tree's `ROADMAP.md`
#: from inside a worktree would compute a row list for a tree the worker is not
#: standing in - the stale-derivation trap `tools/headless-queue.md` section 4b
#: exists to close, arriving through the back door.
_THIS_TREE = Path(__file__).resolve().parents[2]


def _root(root: Any = None) -> Path:
    """The tree to read the docs out of.

    Args:
        root: An explicit root, or None for the checkout this module lives in.

    Returns:
        The resolved root.
    """
    return _THIS_TREE if root is None else Path(str(root))


def _text(path: Path) -> str:
    """A tracked markdown or json file's text, or empty when it is not there.

    Total on purpose. A missing `docs/GATED.md` must not crash a lane; it
    means no row is gated, which is the correct reading of an absent fence
    source, and the row-existence fence still refuses anything invented.

    Args:
        path: The file to read.

    Returns:
        Its text, or ``""``.
    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def roadmap_rows(root: Any = None) -> tuple[Row, ...]:
    """Every item LINE in `ROADMAP.md`, in the file's own order.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        The rows, in file order.
    """
    rows: list[Row] = []
    phase = ""
    for index, line in enumerate(_text(_root(root) / "ROADMAP.md").splitlines(), start=1):
        heading = _PHASE_HEADING.match(line)
        if heading is not None:
            phase = heading.group(1)
            continue
        item = _ITEM_LINE.match(line)
        if item is not None:
            rows.append(Row(item.group(1), index, phase, item.group(2)))
    return tuple(rows)


def phase_gate_ids(rows: tuple[Row, ...]) -> frozenset[str]:
    """FENCE 1, derived from the rows themselves.

    Args:
        rows: What ``roadmap_rows`` returned.

    Returns:
        The ids of the phase gate rows.
    """
    return frozenset(row.item_id for row in rows if _GATE_HEADLINE.match(row.headline))


@dataclass(frozen=True)
class GateClassification:
    """How `docs/GATED.md` classifies every id it names.

    Attributes:
        named: Every id the WIDE SCAN found, wherever it appears. This is the
            POPULATION, and it is deliberately not narrowed.
        blocked: ``(item_id, gate_id)`` pairs, in block order - the rows a gate
            genuinely blocks. A tuple rather than a dict so the record stays
            frozen and hashable.
        mentioned: The ids the file merely DISCUSSES.
        unclassified: Every named id the block classifies neither way, or
            classifies twice over, sorted. Each one is fenced AND reported.
    """

    named: frozenset[str]
    blocked: tuple[tuple[str, str], ...]
    mentioned: frozenset[str]
    unclassified: tuple[str, ...]


def gate_classification(root: Any = None) -> GateClassification:
    """FENCE 2, derived by reading `docs/GATED.md` as a CLASSIFIED PARTITION.

    THE WIDE SCAN STAYS AND IS THE POPULATION. That file names a genuinely
    blocked row inside a gate's PROSE rather than in any structural field -
    CS-G06 is the live instance - so a fence that read only headings, item lines
    or a declared field would fail open on exactly the rows the fence exists for.
    That is the denylist shape, and this project has measured a denylist leaking
    four times across four green commits with only an allowlist holding.

    WHAT THE BLOCK ADDS IS THE CLASSIFIER, and the cost it repays was measured:
    FOURTEEN live roadmap rows were fenced by mention alone and an adjudicator
    graded THIRTEEN of them accidental. The sharpest was a deadlock - the row
    whose entire job is to empty a section OUT of that file was fenced BY that
    file, so the headless lane could never execute the repair. Four more were
    named by a sentence whose own opening clause says they are filed separately,
    and one by a heading reading "WHY IT IS NO LONGER GATED".

    OMISSION FAILS CLOSED. An id the scan finds that the block does not classify
    is treated as gated and is reported by name, which is what makes an omitted
    or stale block DETECTABLE rather than silently permissive. It is the same
    idiom ``validate_scope`` already ships one function over under
    ``UNCLASSIFIED``, deliberately reused rather than reinvented.

    A CONTRADICTED ID FAILS CLOSED TOO. Two lines disagreeing about one id is a
    declaration nobody can read, and resolving it either way would let a BLOCKED
    row be unfenced by appending a MENTIONED line below it.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        The classification of every id that file names.
    """
    text = _text(_root(root) / "docs" / "GATED.md")
    named = frozenset(_ANY_ID.findall(text))

    verdicts: dict[str, list[str | None]] = {}
    order: list[str] = []
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == _CLASSIFY_BEGIN:
            inside = True
            continue
        if stripped == _CLASSIFY_END:
            inside = False
            continue
        if not inside:
            continue
        entry = _CLASSIFY_LINE.match(stripped)
        if entry is None:
            continue
        if entry.group(1) not in verdicts:
            verdicts[entry.group(1)] = []
            order.append(entry.group(1))
        verdicts[entry.group(1)].append(entry.group(2))

    blocked: list[tuple[str, str]] = []
    mentioned: set[str] = set()
    contradicted: set[str] = set()
    for item in order:
        seen = verdicts[item]
        if len(seen) != 1:
            contradicted.add(item)
        elif seen[0] is None:
            mentioned.add(item)
        else:
            blocked.append((item, str(seen[0])))

    classified = frozenset(item for item, _ in blocked) | mentioned
    return GateClassification(
        named=named,
        blocked=tuple(blocked),
        mentioned=frozenset(mentioned),
        unclassified=tuple(sorted((named - classified) | (named & contradicted))),
    )


def gated_ids(root: Any = None) -> frozenset[str]:
    """FENCE 2 - the ids a cycle may not take because `docs/GATED.md` says so.

    The BLOCKED half of :func:`gate_classification`, PLUS every id it could not
    classify. An unclassified id is gated because omission fails closed, and it
    is reported by name through ``fenced_faults`` and ``render_report`` because
    a fence nobody can see is the silent narrowing this module exists against.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        The fenced ids.
    """
    classification = gate_classification(root)
    return frozenset(item for item, _ in classification.blocked) | frozenset(
        classification.unclassified
    )


def heading_subject_ids(ids_field: str) -> tuple[str, ...]:
    """The ids a `docs/LEDGER.md` heading's second field NAMES AS ITS SUBJECTS.

    PUBLIC ON PURPOSE. `tests/ops/test_lane_scope.py` grades this against the
    live file's real heading shapes, and a test re-deriving the split for itself
    would be a second derivation of the same rule - the shape this project has
    measured wrong repeatedly.

    Returns EMPTY when the field is prose that merely mentions an id, which is
    the case this exists to separate. See ``_PUNCTUATION`` above for why the
    separator vocabulary is derived by subtraction rather than listed.

    Args:
        ids_field: The text between the date and the verdict.

    Returns:
        The subject ids in order, or an empty tuple when the field is not an
        ids field at all.
    """
    found = tuple(_ID_TOKEN.findall(ids_field))
    if not found:
        return ()
    residue = _PUNCTUATION.sub("", _ID_TOKEN.sub("", ids_field))
    if _CONJUNCTION_ONLY.fullmatch(residue) is None:
        return ()
    return found


def closed_ids(root: Any = None) -> frozenset[str]:
    """The id-bearing half of FENCE 4, derived by reading `docs/LEDGER.md`.

    A closure is an entry heading whose VERDICT FIELD - the text after the date
    and the ids, per that file's own stated entry shape - begins with CLOSED.
    See the module docstring for why the anchor is load-bearing.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        Every id carrying a closure record.
    """
    closed: set[str] = set()
    for line in _text(_root(root) / "docs" / "LEDGER.md").splitlines():
        heading = _LEDGER_HEADING.match(line)
        if heading is None:
            continue
        subjects = heading_subject_ids(heading.group("ids"))
        if subjects and _CLOSURE_VERDICT.match(heading.group("verdict")):
            closed.update(subjects)
    return frozenset(closed)


def fenced_faults(root: Any = None, rows: tuple[Row, ...] | None = None) -> tuple[ScopeFault, ...]:
    """Every row a cycle may not take, EACH WITH THE REASON IT WAS DROPPED.

    THE REASON IS CARRIED, NOT DISCARDED, AND THAT IS THE WHOLE POINT OF THIS
    FUNCTION EXISTING. A first cut answered a bare id set and the unscoped path
    then silently narrowed 187 live rows to 169 with nothing said - eighteen
    rows vanishing with no printed cause. A scoped lane already refuses loudly
    when its declaration is wrong, so the unscoped path was the one place where
    "the queue is short" and "the queue was quietly cut" rendered identically.
    The caller renders this; the drop is now observable.

    The fences are evaluated in the order `tools/headless-queue.md` section 5
    states them, and a row is reported under the FIRST that catches it, so one
    row yields one reason rather than a set.

    Args:
        root: Repository root, or None for the checkout this module lives in.
        rows: What ``roadmap_rows`` returned, re-read when not supplied.

    Returns:
        One fault per fenced row, in `ROADMAP.md`'s own line order. Rows only -
        an id that is not a row is refused by EXISTENCE rather than by a fence,
        and reporting it here would blur two different classes.
    """
    known = roadmap_rows(root) if rows is None else rows
    gates = phase_gate_ids(known)
    unclassified = frozenset(gate_classification(root).unclassified)
    gated = gated_ids(root)
    closed = closed_ids(root)

    faults: list[ScopeFault] = []
    for row in known:
        if row.item_id in gates:
            faults.append(ScopeFault(row.item_id, PHASE_GATE))
        elif row.item_id in unclassified:
            faults.append(ScopeFault(row.item_id, UNCLASSIFIED_GATE_MENTION))
        elif row.item_id in gated:
            faults.append(ScopeFault(row.item_id, GATED))
        elif row.item_id in closed:
            faults.append(ScopeFault(row.item_id, CLOSED))
    return tuple(faults)


def fenced_ids(root: Any = None, rows: tuple[Row, ...] | None = None) -> frozenset[str]:
    """Every id a cycle may not take, for whatever reason.

    Derived from ``fenced_faults`` rather than recomputed, so the set a caller
    filters by and the report a caller prints can never disagree about which
    rows were dropped.

    Args:
        root: Repository root, or None for the checkout this module lives in.
        rows: What ``roadmap_rows`` returned, re-read when not supplied.

    Returns:
        The fenced row ids.
    """
    return frozenset(fault.item_id for fault in fenced_faults(root, rows))


def _declarations(root: Any = None) -> dict[str, dict[str, Any]]:
    """The scope declarations, or nothing when the file cannot be read.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        Scope name -> its declaration body.
    """
    raw = _text(_root(root) / SCOPES_FILE)
    if not raw.strip():
        return dict(_EMPTY)
    try:
        loaded = json.loads(raw)
    except ValueError:
        return dict(_EMPTY)
    if not isinstance(loaded, dict):
        return dict(_EMPTY)
    scopes = loaded.get("scopes")
    if not isinstance(scopes, dict):
        return dict(_EMPTY)
    return {str(name): body for name, body in scopes.items() if isinstance(body, dict)}


def scope_names(root: Any = None) -> tuple[str, ...]:
    """Every declared scope name, in declaration order.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        The names.
    """
    return tuple(_declarations(root))


def scope_members(name: str, root: Any = None) -> tuple[str, ...]:
    """A scope's declared member ids, exactly as declared and unvalidated.

    Args:
        name: The scope name.
        root: Repository root, or None for the main working tree.

    Returns:
        The declared ids, or an empty tuple when the scope is not declared.
    """
    body = _declarations(root).get(name)
    if body is None:
        return ()
    items = body.get("items")
    if not isinstance(items, list):
        return ()
    return tuple(str(item).strip() for item in items if str(item).strip())


def scope_anchor_phase(name: str, root: Any = None) -> str:
    """The `ROADMAP.md` phase heading a scope PARTITIONS, or ``""``.

    A scope that names an anchor phase is promising something stronger than a
    list: every takeable row of that phase is either a member or is recorded in
    ``excluded`` with a reason. That is what makes the declaration a partition
    of a population the module DERIVES, rather than a list whose length nothing
    grades - so deleting a member cannot shrink the subject in silence.

    Args:
        name: The scope name.
        root: Repository root, or None for the checkout this module lives in.

    Returns:
        The phase heading text, e.g. ``"Phase 6"``, or ``""`` when the scope
        anchors no phase.
    """
    body = _declarations(root).get(name)
    if body is None:
        return ""
    return str(body.get("anchor_phase", "")).strip()


def scope_exclusions(name: str, root: Any = None) -> dict[str, str]:
    """Anchor-phase rows DELIBERATELY left out of a scope, and why.

    A reason per id, because an exclusion with no reason is indistinguishable
    from an omission and the whole mechanism turns on telling those apart.

    Args:
        name: The scope name.
        root: Repository root, or None for the checkout this module lives in.

    Returns:
        Excluded id -> the recorded reason.
    """
    body = _declarations(root).get(name)
    if body is None:
        return {}
    excluded = body.get("excluded")
    if not isinstance(excluded, dict):
        return {}
    return {
        str(item).strip(): str(reason).strip()
        for item, reason in excluded.items()
        if str(item).strip() and str(reason).strip()
    }


def validate_scope(name: str, root: Any = None) -> tuple[ScopeFault, ...]:
    """Grade every declared member of one scope against the live docs.

    Runs on every read, which is the whole bargain that makes a hand-maintained
    id list acceptable.

    Args:
        name: The scope name.
        root: Repository root, or None for the main working tree.

    Returns:
        One fault per offending member, in declaration order. Empty when every
        member is a live, takeable row.
    """
    rows = roadmap_rows(root)
    present = {row.item_id for row in rows}
    gates = phase_gate_ids(rows)
    unclassified = frozenset(gate_classification(root).unclassified)
    gated = gated_ids(root)
    closed = closed_ids(root)

    members = scope_members(name, root)
    excluded = scope_exclusions(name, root)

    faults: list[ScopeFault] = []
    for item in members:
        if item in gates:
            faults.append(ScopeFault(item, PHASE_GATE))
        elif item in unclassified:
            faults.append(ScopeFault(item, UNCLASSIFIED_GATE_MENTION))
        elif item in gated:
            faults.append(ScopeFault(item, GATED))
        elif item not in present:
            faults.append(ScopeFault(item, CLOSED if item in closed else ABSENT))
        elif item in excluded:
            faults.append(ScopeFault(item, CONTRADICTED))

    anchor = scope_anchor_phase(name, root)
    if not anchor:
        return tuple(faults)

    fenced = fenced_ids(root, rows)
    anchor_rows = tuple(
        row.item_id for row in rows if row.phase == anchor and row.item_id not in fenced
    )
    faults.extend(ScopeFault(item, STALE_EXCLUSION) for item in excluded if item not in anchor_rows)
    declared = frozenset(members) | frozenset(excluded)
    faults.extend(ScopeFault(item, UNCLASSIFIED) for item in anchor_rows if item not in declared)
    return tuple(faults)


def _refuse(name: str, faults: tuple[ScopeFault, ...]) -> ScopeRefusedError:
    """Build the refusal a caller and a worker both read.

    Args:
        name: The scope that was asked for.
        faults: The offending members, possibly empty.

    Returns:
        The exception to raise.
    """
    if not faults:
        detail = (
            f"lane scope {name!r} is not declared in {SCOPES_FILE}. "
            "A lane pointed at an undeclared scope refuses rather than falling "
            "back to the whole file, because a silent fallback would run the "
            "lane against a subject it was never pointed at."
        )
        return ScopeRefusedError(name, faults, detail)

    named = ", ".join(f"{fault.item_id} [{fault.reason}]" for fault in faults)
    detail = (
        f"lane scope {name!r} names {len(faults)} row(s) that cannot be taken: {named}. "
        f"Repair {SCOPES_FILE}; do not widen the fences. This refusal is NOT an "
        "empty queue - the scope itself is wrong."
    )
    return ScopeRefusedError(name, faults, detail)


def rows_for_scope(name: str | None, root: Any = None) -> tuple[Row, ...]:
    """The takeable rows, optionally narrowed to one declared scope.

    Args:
        name: A declared scope name, or None for the whole file.
        root: Repository root, or None for the main working tree.

    Returns:
        The takeable rows in `ROADMAP.md`'s own line order.

    Raises:
        ScopeRefusedError: The scope is not declared, or a member cannot be taken.
    """
    rows = roadmap_rows(root)
    fenced = fenced_ids(root, rows)
    survivors = tuple(row for row in rows if row.item_id not in fenced)
    if name is None:
        return survivors

    if name not in _declarations(root):
        raise _refuse(name, ())
    faults = validate_scope(name, root)
    if faults:
        raise _refuse(name, faults)

    members = frozenset(scope_members(name, root))
    return tuple(row for row in survivors if row.item_id in members)


def takeable_rows(
    lane: str, root: Any = None, env: dict[str, str] | None = None
) -> tuple[Row, ...]:
    """The rows ``lane`` may take right now.

    Args:
        lane: The lane name, from ``ops.loop.lanes.LANES``.
        root: Repository root, or None for the main working tree.
        env: The environment to read the lane's scope pointer from. None means
            the live process environment.

    Returns:
        The takeable rows in `ROADMAP.md`'s own line order.

    Raises:
        ScopeRefusedError: The lane is pointed at a scope that cannot be honoured.
    """
    return rows_for_scope(lanes.scope_for_lane(lane, env), root)


def lane_permit(lane: str, root: Any = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    """What this lane is ALLOWED to work, as a fact that NEVER raises.

    THE SAME ANSWER ``takeable_rows`` GIVES, TURNED INTO A ROW OF A LEDGER. The
    driver computes this BEFORE it launches a worker and carries it across the
    cycle, and that ordering is load-bearing rather than incidental: a cycle that
    CLOSES its row removes that row from `ROADMAP.md`, so a permit recomputed
    after the cycle would report the row the worker just finished as one it was
    never allowed to take. The permit is what the lane could take when it
    started.

    A REFUSAL IS A PERMIT TO TAKE NOTHING, NOT A PERMIT TO TAKE ANYTHING. The
    refusal is carried as ``ok`` plus the refusal's own ``detail`` field, which
    is what a caller renders - never the exception object, whose ``str()`` on an
    OSError appends the path it failed on (CLAUDE.md non-negotiable 12).

    Args:
        lane: The lane name, from ``ops.loop.lanes.LANES``.
        root: Repository root, or None for the checkout this module lives in.
        env: The environment to read the lane's scope pointer from, or None for
            the live process environment.

    Returns:
        ``{"ok", "lane_scope", "allowed", "detail"}``. ``allowed`` is a tuple of
        row ids in `ROADMAP.md`'s own order, EMPTY when ``ok`` is false.
    """
    try:
        rows = takeable_rows(lane, root, env)
    except ScopeRefusedError as refused:
        return {
            "ok": False,
            "lane_scope": refused.scope_name,
            "allowed": (),
            "detail": refused.detail,
        }
    return {
        "ok": True,
        "lane_scope": lanes.scope_for_lane(lane, env),
        "allowed": tuple(row.item_id for row in rows),
        "detail": "",
    }


def binding_fact(permit: Any, worked: Any, *, committed: bool = False) -> dict[str, Any]:
    """Bind the rows a cycle WORKED to the rows its lane was PERMITTED to work.

    THIS IS THE MECHANISM THE PROMPT'S OWN STANDARD ASKS FOR. `tools/headless-queue.md`
    section 1 says an instruction a worker can rationalize past is not a
    mechanism; until this existed, the only thing joining the computed queue to
    the row a worker took was the worker's own reading of printed text. Nothing
    here is authored by the worker: the permit is computed from the docs and the
    worked set is observed from the claim store by the driver.

    MEMBERSHIP, NEVER A COUNT. The answer is a set difference and a set
    difference only. A floor over the size of the permitted set would be
    satisfied by its strongest member while the weakest went unmeasured - the
    CS-988 class, twelve instances of which are measured in this repository -
    and would pass a lane permitted one row that worked a different one.

    ANY row outside refuses the whole cycle. Grading the first row, or the
    majority, would let an out-of-scope row travel behind an in-scope one.

    THE FOUR ANSWERS ARE DISTINCT ON PURPOSE, because they send a reader to four
    different files:

    - UNCOMPUTED - the permit itself was refused, so nothing was checked. Not
      bound, because a check that did not happen is not a check that passed.
    - OUT_OF_SCOPE - a row was worked that this lane may not take.
    - UNNAMED - the cycle produced a commit while holding no claim, so there was
      NOTHING TO CHECK. This is an observation gap and it is recorded as one:
      ``observed`` is false and the reason names it, so a reader can count the
      nights this lane never claimed a row. It does NOT refuse the roll-up, and
      that boundary is deliberate rather than lenient - see the residual below.
    - Bound, with no reason - either every worked row is permitted, or the cycle
      worked nothing and committed nothing. The second is the ``RATION_NO_SUITE``
      shape: a lane_held cycle, a failed launch and a worker that gave up all
      reach here, and refusing them would make every such row read like a
      violation.

    THE RESIDUAL, STATED RATHER THAN CLAIMED SHUT. A cycle that never claims is
    a cycle this cannot check, so the mechanism binds what it can SEE and says
    plainly when it saw nothing. Making an unnamed commit refuse the roll-up is
    the obvious next turn of the ratchet and it was NOT taken here, for a
    measured reason: no worker claims a row today, so the clause would report
    every cycle of every night unbound on the night it shipped, and a refusal
    that fires on everything is the kind nobody reads. The gap closes from the
    other end - a worker that claims, which `tools/headless-queue.md` section 5
    already requires and which this field now MEASURES rather than assumes.

    Args:
        permit: What :func:`lane_permit` answered.
        worked: The row ids the driver observed this cycle holding.
        committed: Did the cycle advance its lane worktree's HEAD.

    Returns:
        ``{"checked", "observed", "bound", "lane_scope", "worked", "outside",
        "reason", "detail"}``, JSON-safe, written into the cycle record on EVERY
        cycle. ``checked`` says the permit was computable, ``observed`` says a
        row was seen at all, and ``bound`` is the roll-up's clause.
    """
    body = permit if isinstance(permit, dict) else {}
    allowed = frozenset(str(item) for item in (body.get("allowed") or ()))
    rows = tuple(sorted({str(row).strip().upper() for row in (worked or ()) if str(row).strip()}))
    fact: dict[str, Any] = {
        "checked": bool(body.get("ok")),
        "observed": bool(rows),
        "bound": False,
        "lane_scope": body.get("lane_scope"),
        "worked": list(rows),
        "outside": [],
        "reason": "",
        "detail": "",
    }
    if not fact["checked"]:
        fact["reason"] = UNCOMPUTED
        fact["detail"] = str(body.get("detail") or "the lane's takeable rows could not be read")
        return fact

    outside = tuple(row for row in rows if row not in allowed)
    if outside:
        fact["reason"] = OUT_OF_SCOPE
        fact["outside"] = list(outside)
        fact["detail"] = (
            f"this cycle worked {', '.join(outside)}, which this lane may not take. "
            f"The lane was permitted {len(allowed)} row(s) under scope "
            f"{fact['lane_scope']!r} and none of them is that. The work is not "
            "discarded and the row is not withdrawn - this cycle is recorded as "
            "one nobody authorised, which is the thing a later reader has to be "
            "able to tell apart from an earned one."
        )
        return fact
    fact["bound"] = True
    if rows:
        return fact
    if committed:
        fact["reason"] = UNNAMED
        fact["detail"] = (
            "this cycle committed while holding no claim, so there was no row to "
            "check it against - the check did not fail, it did not happen. The "
            "claim is what names the row; see tools/headless-queue.md section 5."
        )
        return fact
    fact["detail"] = "this cycle worked no row and committed nothing, so there was nothing to bind"
    return fact


def render_report(
    rows: tuple[Row, ...],
    name: str | None,
    dropped: tuple[ScopeFault, ...],
    unclassified: tuple[str, ...] = (),
) -> str:
    """What the command prints on success.

    THE DROP IS PRINTED, NOT ONLY THE SURVIVORS. Rendering the survivors alone
    made the unscoped path narrow the file silently - every fenced row simply
    absent, with no count and no cause - so a queue that had been cut and a
    queue that was genuinely short looked identical. That is the same fault the
    scoped path already refuses over, and it has no business being tolerable one
    branch away.

    Args:
        rows: The takeable rows.
        name: The scope they were narrowed to, or None.
        dropped: Every row a fence removed, with its reason.
        unclassified: Every id `docs/GATED.md` names that its classification
            block does not classify. REPORTED SEPARATELY FROM ``dropped``
            because not every one of them is a `ROADMAP.md` row, and an
            unclassified id that is not a row would otherwise be fenced with
            nothing printed anywhere - which is precisely the silent case.

    Returns:
        The report body.
    """
    heading = f"scope: {name}" if name else "scope: (none) - the whole of ROADMAP.md"
    parts = [heading]

    if rows:
        parts.extend(
            f"{row.item_id}  [{row.phase or 'no phase'}  line {row.line_no}]" for row in rows
        )
    else:
        parts.append(
            "NO TAKEABLE ROW. Every row in this scope is fenced out or the scope is "
            "empty. This is an empty QUEUE, not a bad scope - a bad scope refuses."
        )

    parts.append("")
    if dropped:
        parts.append(f"FENCED OUT, {len(dropped)} row(s) - these were removed, not missing:")
        parts.extend(f"  {fault.item_id}  {fault.reason}" for fault in dropped)
    else:
        parts.append("FENCED OUT: nothing. No fence removed a row from this read.")

    if unclassified:
        parts.append("")
        parts.append(
            f"{UNCLASSIFIED_GATE_MENTION}, {len(unclassified)} id(s) - docs/GATED.md NAMES "
            "these and its classification block classifies none of them, so they are "
            "fenced. Omission fails CLOSED. The repair is a BLOCKED or MENTIONED line "
            "in that block, never a narrowed scan:"
        )
        parts.extend(f"  {item}" for item in unclassified)
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Compute the takeable rows for a lane and print them.

    This is the mechanism `tools/headless-queue.md` section 5 points a worker
    at. The prompt's own standard is that an instruction a worker can
    rationalise past is not a mechanism, so the scope is not stated to the
    worker as prose to apply - it is computed here and handed over as a list.

    Args:
        argv: Command line, or None for ``sys.argv[1:]``.

    Returns:
        0 when rows were computed, 2 when the scope was refused.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ops.loop.scope",
        description="Print the ROADMAP.md rows a lane may take, fences applied.",
    )
    parser.add_argument("--lane", default=lanes.LANES[0], help="lane name")
    parser.add_argument("--root", default=None, help="repository root to read (default: this one)")
    parser.add_argument(
        "--scope",
        default=None,
        help="scope name, overriding whatever the lane is pointed at",
    )
    args = parser.parse_args(argv)

    name = args.scope if args.scope is not None else lanes.scope_for_lane(args.lane, None)
    try:
        rows = rows_for_scope(name, args.root)
    except ScopeRefusedError as refused:
        sys.stdout.write(f"REFUSED: {refused.detail}\n")
        return 2
    sys.stdout.write(
        render_report(
            rows,
            name,
            fenced_faults(args.root),
            gate_classification(args.root).unclassified,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
