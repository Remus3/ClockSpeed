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
- FENCE 2, never anything in `docs/GATED.md`. Derived by reading that file.
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

from ops.loop import lanes

#: An item LINE in `ROADMAP.md`: the id at column zero, then the spaced-hyphen
#: clause break the whole project uses. The file's own prose carries ``CS-nnn -``
#: as a shape example and ``CS-900, then`` in a sentence; neither matches.
_ITEM_LINE = re.compile(r"^(CS-[0-9]+) - (.*)$")

#: A phase heading in `ROADMAP.md`. The headings are the single owner of which
#: phase a row belongs to.
_PHASE_HEADING = re.compile(r"^## (Phase [0-9]+)\b")

#: FENCE 1, derived. A gate row says so in its own headline.
_GATE_HEADLINE = re.compile(r"^Phase [0-9]+ gate:")

#: Any item id, wherever it appears. Used for `docs/GATED.md`, which names its
#: blocked rows in prose rather than on item lines.
_ANY_ID = re.compile(r"CS-[0-9]+")

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
CONTRADICTED = "in_items_and_excluded"
STALE_EXCLUSION = "excluded_but_not_a_takeable_anchor_row"
UNCLASSIFIED = "anchor_phase_row_neither_member_nor_excluded"

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


def gated_ids(root: Any = None) -> frozenset[str]:
    """FENCE 2, derived by reading `docs/GATED.md`.

    Every id the file NAMES, wherever it names it. Deliberately wide: that file
    names a blocked row inside the gate's prose rather than on an item line, and
    a fence that reads only headings would miss exactly the rows it exists for.
    The cost of the wide reading is that a row merely DISCUSSED there is fenced
    out too, which errs toward refusing rather than toward taking.

    Args:
        root: Repository root, or None for the main working tree.

    Returns:
        The ids named anywhere in that file.
    """
    return frozenset(_ANY_ID.findall(_text(_root(root) / "docs" / "GATED.md")))


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
    gated = gated_ids(root)
    closed = closed_ids(root)

    faults: list[ScopeFault] = []
    for row in known:
        if row.item_id in gates:
            faults.append(ScopeFault(row.item_id, PHASE_GATE))
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
    gated = gated_ids(root)
    closed = closed_ids(root)

    members = scope_members(name, root)
    excluded = scope_exclusions(name, root)

    faults: list[ScopeFault] = []
    for item in members:
        if item in gates:
            faults.append(ScopeFault(item, PHASE_GATE))
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


def render_report(rows: tuple[Row, ...], name: str | None, dropped: tuple[ScopeFault, ...]) -> str:
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
    sys.stdout.write(render_report(rows, name, fenced_faults(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
