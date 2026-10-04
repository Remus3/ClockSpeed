"""A lane can be pointed at a SUBJECT, and the pointing cannot drift silently.

WHAT IS GRADED HERE. ``ops/loop/scope.py`` computes the rows a lane may take.
Without a scope that is the whole of `ROADMAP.md` read top to bottom, which is
what `tools/headless-queue.md` section 5 has always said. With a scope it is the
declared members of that scope, in the file's own line order, after the same
fences. The fences are DERIVED - a phase gate row is recognised by its own
headline in `ROADMAP.md`, a gated row by its presence in `docs/GATED.md`, a
closed row by a closure heading in `docs/LEDGER.md` - so none of the four gate
ids is transcribed into shipped code, and this module holds the one place the
derivation is checked against the prose that governs it.

WHY A HAND-MAINTAINED ID LIST IS ALLOWED AT ALL. The dashboard rows are not
contiguous and are not one phase: most sit under `## Phase 6 - surfaces` and at
least one sits in the phase 4 block - the exact split is derived by the arms
below rather than counted here, because a count in prose is a fact that will
drift. No phase filter expresses that subject, so the subject has to be written
down. The price of writing it down is drift, and ``validate_scope`` is what makes
the price payable: it is paid LOUDLY, on every read, naming the offender, never
by quietly answering a shorter queue.

THE DECLARATION IS GRADED THREE WAYS AND EACH CATCHES WHAT THE OTHERS CANNOT.
Per-member validation catches a member that closed, was gated, or vanished. The
ANCHOR-PHASE PARTITION catches a takeable row of that phase nobody classified -
including a brand new one filed tomorrow, which no written list can anticipate.
``DASHBOARD_MEMBERS`` below catches any change to the member set itself. Dropping
any one of the three leaves a measured hole; the constant's own comment records
which.

NO FLOOR GRADES ANY POPULATION IN THIS MODULE, AND ONE USED TO. The arm that is
now ``test_the_dashboard_scope_partitions_its_anchor_phase`` was called "is
EXACTLY the rows" and asserted a SUBSET plus ``len(phases) > 1``. An adversary
cut the declaration from eight ids to two; both surviving ids happened to sit in
different phases, the floor held, and 18 arms reported green while the lane
served a quarter of its queue. That was instance ELEVEN of the CS-988 class. The
floor is deleted rather than tightened - a tightened floor is still a floor - and
every population claim here is now a set EQUALITY whose two sides are enumerated
from sources that share no constant.

WHEN THIS MODULE GOES RED ON A LIVE DECLARATION, THAT IS THE MECHANISM WORKING.
The arms redden the day a declared member closes, is gated, is renamed out of
`ROADMAP.md`, or is quietly dropped, and the day a new anchor-phase row is filed
that nobody classified. The repair is to edit `config/lane_scopes.json` and this
module's ``DASHBOARD_MEMBERS`` together, never to weaken an arm.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest
from ops.loop import lanes, scope

# ---------------------------------------------------------------------------
# Synthetic corpus. Hand-authored, tiny, and deliberately NOT a slice of the
# live docs - CLAUDE.md section 7 settles that fixtures are synthetic.
# ---------------------------------------------------------------------------

#: A `ROADMAP.md` small enough to reason about and shaped like the real one:
#: two phases, a gate row per phase recognisable only by its own headline, and
#: ordinary rows either side of a phase boundary so "file order" is testable.
SYNTHETIC_ROADMAP = """# Roadmap - OPEN work only

One line per item. Shape:

```
CS-nnn - <one line> - acceptance: <testable condition> - tier: <0|1|2>
```

CS-900, then CS-906 onward. Gaps are expected and are never backfilled.

## Phase 4 - save reader

CS-400 - Phase 4 gate: everything below closes first - acceptance: all of it - tier: 2
CS-410 - an early row that is not about the subject - acceptance: something - tier: 1
CS-462 - a row about the subject filed outside its phase - acceptance: something - tier: 2
CS-470 - a gated row that must never be taken - acceptance: something - tier: 2

## Phase 6 - surfaces

CS-600 - Phase 6 gate: the surface rolls up here - acceptance: all of it - tier: 2
CS-603 - a subject row - acceptance: something - tier: 1
CS-618 - another subject row - acceptance: something - tier: 2
CS-620 - a surface row that is not about the subject - acceptance: something - tier: 1
"""

#: `docs/GATED.md`. It NAMES two rows and CLASSIFIES both, because naming is no
#: longer what fences: the wide id scan is the POPULATION and the block below is
#: the CLASSIFIER. CS-470 is BLOCKED by the gate. CS-410 is merely DISCUSSED and
#: is takeable, which is the case the live file measured fourteen of and had no
#: way to express.
SYNTHETIC_GATED = """# Gated items

## Open gated items

### CS-G01 - something outside the repo

CS-470 is blocked behind it and cannot close inside this repository.
CS-410 is discussed here and this gate does not block it.

```
CLOCKSPEED-GATE-CLASSIFICATION BEGIN
gate: CS-470 BLOCKED CS-G01
gate: CS-410 MENTIONED
CLOCKSPEED-GATE-CLASSIFICATION END
```
"""

#: `docs/LEDGER.md`. CS-799 CLOSED here and appears in no roadmap row, which is
#: what a closed id looks like from the outside. CS-603 appears in a heading
#: that says the opposite of closure IN THE SAME SENTENCE - the exact trap an
#: unanchored substring search for "CLOSED" falls into.
SYNTHETIC_LEDGER = """# Ledger

## Entries

### 2026-09-13 - CS-603 - NOT A COMPLETION RECORD. NOTHING CLOSED. CS-603 STAYS OPEN

Body.

### 2026-09-12 - CS-799 - CLOSED. It shipped and it is done

Body.
"""

#: The subject this corpus is pointed at. Non-contiguous and spanning two
#: phases, exactly like the live dashboard subject.
SYNTHETIC_SUBJECT = ("CS-462", "CS-603", "CS-618")

#: THE DASHBOARD SUBJECT, PINNED IN A SECOND FILE. A deliberate second copy of
#: what `config/lane_scopes.json` declares, and the reason it exists was
#: MEASURED rather than argued.
#:
#: The partition alone does not close the hole. A first repair graded the
#: declaration only as a partition of its anchor phase, and moving one id from
#: ``items`` into ``excluded`` IN THE SAME EDIT kept the partition complete: the
#: suite stayed green at 35 passed while the lane served one row fewer. Probed
#: directly - variant G of the knob sweep, exit 0. With this literal in place
#: that same edit reddens, because the left side loses a member the right side
#: still names, and the two sides now live in different files.
#:
#: So the two mechanisms are complementary, not redundant. This equality catches
#: any CHANGE to the member set. The partition catches a NEW anchor-phase row
#: that nobody classified, which no literal can see. Same doctrine as
#: ``SEAM_SENTENCES`` in `tests/test_scaffold.py`, which restates prose verbatim
#: so a paraphrase goes red.
#:
#: WHAT IT STILL DOES NOT CLOSE, stated rather than claimed: editing this file
#: and the declaration together. That is the standing limit of a two-copy
#: agreement and it is a cross-file edit, not a silent drift.
DASHBOARD_MEMBERS = frozenset(
    {
        "CS-962",
        "CS-603",
        "CS-606",
        "CS-608",
        "CS-613",
        "CS-618",
        "CS-887",
        "CS-909",
        "CS-1046",
        "CS-1047",
        "CS-1051",
        "CS-1065",
        "CS-1269",
    }
)

#: Every id the synthetic roadmap carries that is NOT in the subject and is not
#: fenced out. Written from the corpus above by hand and cross-checked against
#: the parser in ``test_the_synthetic_corpus_parses_to_the_rows_it_was_written_with``.
SYNTHETIC_TAKEABLE_UNSCOPED = ("CS-410", "CS-462", "CS-603", "CS-618", "CS-620")


#: Ceiling for the CLI children below. An unbounded child cannot fail the
#: test that owns it - it burns the whole CI budget until the lane is
#: cancelled, which is evidence of nothing (CS-896). Matches the sibling
#: idiom in tests/ops/test_queue_lane_relaunch.py.
_CLI_TIMEOUT_S: Final = 300


def _write_corpus(root: Path, scopes: dict[str, object]) -> Path:
    """Lay the synthetic docs and a scope declaration out under ``root``.

    Args:
        root: A temporary directory standing in for the repository root.
        scopes: The ``scopes`` mapping to serialise into
            ``config/lane_scopes.json``.

    Returns:
        The root, for chaining.
    """
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "ROADMAP.md").write_bytes(SYNTHETIC_ROADMAP.encode("ascii"))
    (root / "docs" / "GATED.md").write_bytes(SYNTHETIC_GATED.encode("ascii"))
    (root / "docs" / "LEDGER.md").write_bytes(SYNTHETIC_LEDGER.encode("ascii"))
    payload = json.dumps({"scopes": scopes}, indent=2) + "\n"
    (root / "config" / "lane_scopes.json").write_bytes(payload.encode("ascii"))
    return root


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """A synthetic root whose one scope names the subject and nothing else."""
    return _write_corpus(
        tmp_path,
        {"subject": {"description": "the synthetic subject", "items": list(SYNTHETIC_SUBJECT)}},
    )


# ===========================================================================
# a. The corpus means what it says
# ===========================================================================


def test_the_synthetic_corpus_parses_to_the_rows_it_was_written_with(corpus: Path) -> None:
    """The parser and the hand-written corpus agree on the row set.

    This is the control every later equality rests on. Both sides are
    enumerated independently: the left from the parser walking the file, the
    right from a regex over the same text that shares no code with the parser.

    Args:
        corpus: The synthetic root.
    """
    parsed = tuple(row.item_id for row in scope.roadmap_rows(corpus))
    independent = tuple(re.findall(r"(?m)^(CS-[0-9]+) - ", SYNTHETIC_ROADMAP))

    assert parsed, "the parser found no rows at all, so every later equality is vacuous"
    assert parsed == independent


def test_a_phase_gate_row_is_recognised_by_its_own_headline(corpus: Path) -> None:
    """Gate rows are DERIVED from the roadmap, never transcribed.

    The right-hand side is built from the corpus text by a different expression
    than the one the module uses, so the two share no constant.

    Args:
        corpus: The synthetic root.
    """
    derived = scope.phase_gate_ids(scope.roadmap_rows(corpus))
    independent = frozenset(re.findall(r"(?m)^(CS-[0-9]+) - Phase [0-9]+ gate:", SYNTHETIC_ROADMAP))

    assert derived, "no gate row was derived, so the fence is graded against nothing"
    assert derived == independent


def test_a_heading_that_says_nothing_closed_does_not_close_an_item(corpus: Path) -> None:
    """The ledger reader is anchored on the verdict field, not a substring.

    `docs/LEDGER.md`'s own entry shape puts the verdict immediately after the
    ids, and the live file carries headings reading "NOT A COMPLETION RECORD.
    NOTHING CLOSED." An unanchored search for the word would close the very item
    such a heading exists to keep open.

    Args:
        corpus: The synthetic root.
    """
    closed = scope.closed_ids(corpus)

    assert closed == frozenset({"CS-799"})
    assert "CS-603" not in closed


@pytest.mark.parametrize(
    ("ids_field", "expected"),
    [
        ("CS-799", ("CS-799",)),
        ("CS-929 CS-933", ("CS-929", "CS-933")),
        ("CS-949, CS-950", ("CS-949", "CS-950")),
        ("CS-829, CS-846, CS-850, CS-851", ("CS-829", "CS-846", "CS-850", "CS-851")),
        ("CS-896 and CS-917", ("CS-896", "CS-917")),
        ("CS-829, CS-981 and CS-G05", ("CS-829", "CS-981", "CS-G05")),
        ("CS-407 PARTIAL", ()),
        ("CORRECTION to the CS-922 record", ()),
        ("LICENCE GATE RESULT for the save-parser field", ()),
    ],
    ids=[
        "single",
        "space-joined",
        "comma-joined",
        "four-comma-joined",
        "and-joined",
        "comma-and-gated-series",
        "prose-suffix-rejected",
        "prose-prefix-rejected",
        "no-id-at-all",
    ],
)
def test_the_ids_field_reader_covers_every_live_heading_shape(
    ids_field: str, expected: tuple[str, ...]
) -> None:
    """Two ids joined by a COMMA are two ids, and a first cut said otherwise.

    The shipped reader spelled the field ``CS-nnn(?: CS-nnn)*`` - space-joined
    only - so every comma-joined or "and"-joined heading matched nothing, and
    both ids in it stayed unclosed and therefore still TAKEABLE. That degrades
    to SILENTLY OPEN, which is the one direction this module must never fail in.
    Every shape here is a real one taken off `docs/LEDGER.md`, and the three
    rejections are real too - an ids field that is prose must not be mined for
    whatever id it happens to mention.

    Args:
        ids_field: The text between the date and the verdict.
        expected: The subject ids, or empty when the field is prose.
    """
    assert scope.heading_subject_ids(ids_field) == expected


def test_no_live_ledger_heading_is_read_by_one_route_and_not_the_other(
    repo_root: Path,
) -> None:
    """The reader and an independent split agree on every live multi-id heading.

    The second enumeration shares no code with the module: it splits on the
    spaced hyphen, takes the middle field, and accepts it when removing the ids
    and the punctuation leaves no letters at all. That last clause is written
    differently from the module's conjunction test on purpose, so the two would
    disagree if either drifted.

    Args:
        repo_root: Repository root.
    """
    text = (repo_root / "docs" / "LEDGER.md").read_text(encoding="utf-8")
    token = re.compile(r"CS-[A-Z]*[0-9]+")

    by_module: dict[str, tuple[str, ...]] = {}
    by_hand: dict[str, tuple[str, ...]] = {}
    heading_fields = 3
    multi_id = 2
    for line in text.splitlines():
        if not line.startswith("### "):
            continue
        parts = line[4:].split(" - ")
        if len(parts) < heading_fields:
            continue
        field = parts[1]
        found = tuple(token.findall(field))
        if len(found) < multi_id:
            continue
        residue = token.sub("", field)
        if not re.fullmatch(r"[^A-Za-z]*(?:and[^A-Za-z]*)*", residue):
            continue
        by_hand[line] = found
        by_module[line] = scope.heading_subject_ids(field)

    assert by_hand, "no live multi-id heading found, so this arm compares nothing"
    assert by_module == by_hand


# ===========================================================================
# b. ARM ONE - a scoped lane is never offered a row outside its scope
# ===========================================================================


def test_a_scoped_lane_is_offered_its_subject_and_nothing_else(corpus: Path) -> None:
    """REQUIRED ARM. A scoped lane's takeable set EQUALS its declared members.

    Three legs, and the second and third are what stop the first being vacuous.
    The equality alone would pass if the scope filter were correct AND if it
    were a no-op over a roadmap that happened to hold only subject rows, so the
    second leg proves the unscoped answer is genuinely wider and the third names
    the rows a no-op would have leaked.

    Args:
        corpus: The synthetic root.
    """
    unscoped = frozenset(row.item_id for row in scope.takeable_rows("queue", corpus, {}))
    scoped = frozenset(
        row.item_id
        for row in scope.takeable_rows(
            "queue", corpus, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "subject"}
        )
    )

    assert scoped == frozenset(SYNTHETIC_SUBJECT)
    assert unscoped == frozenset(SYNTHETIC_TAKEABLE_UNSCOPED)
    assert unscoped - scoped == frozenset({"CS-410", "CS-620"})


def test_a_scoped_lane_keeps_the_roadmaps_own_line_order(corpus: Path) -> None:
    """Order survives the filter, because "the first surviving row" needs it.

    Args:
        corpus: The synthetic root.
    """
    ordered = tuple(
        row.item_id
        for row in scope.takeable_rows(
            "queue", corpus, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "subject"}
        )
    )
    positions = {row.item_id: row.line_no for row in scope.roadmap_rows(corpus)}

    assert ordered == SYNTHETIC_SUBJECT
    assert list(ordered) == sorted(ordered, key=lambda item: positions[item])


def test_the_fences_still_apply_inside_a_scope(corpus: Path) -> None:
    """A fenced row does not become takeable by being named in a scope.

    The scope here names the phase 4 gate and a gated row alongside one good
    row, and declares them as a scope the caller asks to be FILTERED by rather
    than validated - so the only thing standing between the lane and a gate row
    is the fence pipeline itself.

    Args:
        corpus: The synthetic root.
    """
    rows = scope.roadmap_rows(corpus)
    fenced = scope.fenced_ids(corpus, rows)

    assert fenced == frozenset({"CS-400", "CS-600", "CS-470"})
    assert frozenset(r.item_id for r in rows) - fenced == frozenset(SYNTHETIC_TAKEABLE_UNSCOPED)


# ===========================================================================
# c. ARM TWO - a scope naming a closed or non-existent id refuses, loudly
# ===========================================================================


@pytest.mark.parametrize(
    ("item_id", "reason"),
    [
        ("CS-799", scope.CLOSED),
        ("CS-404", scope.ABSENT),
        ("CS-470", scope.GATED),
        ("CS-600", scope.PHASE_GATE),
    ],
)
def test_a_scope_naming_an_untakeable_id_refuses_and_names_it(
    tmp_path: Path, item_id: str, reason: str
) -> None:
    """REQUIRED ARM. Each untakeable class refuses, with the offender named.

    The oracle can observe its subject: it reads the fault's own ``item_id``
    and ``reason`` fields AND asserts the id is rendered in the message a caller
    sees, so an exception that refuses for the right reason while printing
    nothing useful still fails here.

    Args:
        tmp_path: pytest temporary directory.
        item_id: The offending id planted in the declaration.
        reason: The refusal reason it must be reported under.
    """
    root = _write_corpus(
        tmp_path,
        {"bad": {"description": "one good row and one offender", "items": ["CS-603", item_id]}},
    )

    with pytest.raises(scope.ScopeRefusedError) as caught:
        scope.takeable_rows("queue", root, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "bad"})

    faults = frozenset((fault.item_id, fault.reason) for fault in caught.value.faults)
    assert faults == frozenset({(item_id, reason)})
    assert item_id in str(caught.value)
    assert reason in str(caught.value)


def test_a_scope_whose_members_are_all_takeable_refuses_nothing(corpus: Path) -> None:
    """The non-vacuity leg for the refusal arm above.

    Without it, a ``validate_scope`` that refused EVERY scope would pass every
    parametrisation of the arm above and be caught by nothing.

    Args:
        corpus: The synthetic root.
    """
    assert scope.validate_scope("subject", corpus) == ()

    rows = scope.takeable_rows("queue", corpus, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "subject"})
    assert tuple(row.item_id for row in rows) == SYNTHETIC_SUBJECT


def test_an_unknown_scope_name_refuses_rather_than_answering_the_whole_file(
    corpus: Path,
) -> None:
    """Pointing a lane at a scope that does not exist is a refusal.

    Falling back to the whole file would be the silent-empty-queue defect
    wearing its opposite face: the lane would run, take a row, and nobody would
    learn that the subject it was pointed at was never applied.

    Args:
        corpus: The synthetic root.
    """
    with pytest.raises(scope.ScopeRefusedError) as caught:
        scope.takeable_rows("queue", corpus, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "nosuch"})

    assert "nosuch" in str(caught.value)


def test_a_lane_with_no_scope_pointed_at_it_reads_the_whole_file(corpus: Path) -> None:
    """The existing single lane keeps its existing behaviour by default.

    Args:
        corpus: The synthetic root.
    """
    assert lanes.scope_for_lane("queue", {}) is None

    rows = scope.takeable_rows("queue", corpus, {})
    assert tuple(row.item_id for row in rows) == SYNTHETIC_TAKEABLE_UNSCOPED


def test_the_unscoped_read_reports_what_it_dropped_and_why(corpus: Path) -> None:
    """The unscoped path NARROWS, and the narrowing must be visible.

    The scoped path refuses loudly when its declaration is wrong. The unscoped
    path has no declaration to refuse over, so the only thing separating "the
    queue is short" from "the queue was cut" is what it SAYS. Before this, it
    said nothing: rows fenced out were simply absent, with no count and no
    cause.

    Both halves are asserted - the fault set by EQUALITY against a second
    enumeration built from the corpus by hand, and the rendered text, because a
    correct fault set nobody prints helps no worker.

    Args:
        corpus: The synthetic root.
    """
    dropped = scope.fenced_faults(corpus)
    seen = frozenset((fault.item_id, fault.reason) for fault in dropped)

    assert seen == frozenset(
        {
            ("CS-400", scope.PHASE_GATE),
            ("CS-600", scope.PHASE_GATE),
            ("CS-470", scope.GATED),
        }
    )

    rendered = scope.render_report(scope.takeable_rows("queue", corpus, {}), None, dropped)
    for item, reason in sorted(seen):
        assert item in rendered, f"{item} was dropped and never named in the report"
        assert reason in rendered, f"{item} was dropped and its reason never printed"


def test_a_read_that_dropped_nothing_says_so_rather_than_staying_silent(
    tmp_path: Path,
) -> None:
    """NON-VACUITY for the report above, and the two cases must differ.

    A renderer that printed the fenced block unconditionally, or never, would
    satisfy a one-sided arm. This pins the empty case to its own wording and
    asserts the two renderings are not the same string.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = tmp_path / "unfenced"
    (root / "docs").mkdir(parents=True)
    (root / "config").mkdir(parents=True)
    (root / "ROADMAP.md").write_bytes(
        b"## Phase 6 - surfaces\n\nCS-603 - an ordinary row - tier: 1\n"
    )

    dropped = scope.fenced_faults(root)
    assert dropped == ()

    rendered = scope.render_report(scope.rows_for_scope(None, root), None, dropped)
    assert "FENCED OUT: nothing" in rendered
    assert rendered != scope.render_report(
        scope.rows_for_scope(None, root), None, scope.fenced_faults()
    )


# ===========================================================================
# d. The live tree - the declaration is validated against what is actually open
# ===========================================================================


def test_the_derived_gate_fence_equals_the_prompts_stated_gate_fence(repo_root: Path) -> None:
    """The derivation and `tools/headless-queue.md` FENCE 1 name the same rows.

    Two enumerations, two files, no shared constant: the left is derived from
    `ROADMAP.md` headlines by the shipped module, the right is read out of the
    prompt's own fence sentence. If somebody adds a phase 8 gate row and does
    not say so in the prompt, this is what says so.

    Args:
        repo_root: Repository root.
    """
    derived = scope.phase_gate_ids(scope.roadmap_rows(repo_root))

    prompt = (repo_root / "tools" / "headless-queue.md").read_text(encoding="ascii")
    sentence = next(
        line for line in prompt.splitlines() if line.startswith("**FENCE 1 - NEVER TAKE")
    )
    stated = frozenset(re.findall(r"CS-[0-9]+", sentence))

    assert derived, "no gate row derived from the live roadmap"
    assert stated, "no gate id read out of the live FENCE 1 sentence"
    assert derived == stated


def test_the_declared_scopes_all_validate_against_the_live_roadmap(repo_root: Path) -> None:
    """Every declared scope member is a live, takeable `ROADMAP.md` row.

    THIS ARM REDDENS WHEN A DECLARED MEMBER CLOSES, and that is the mechanism
    doing its job rather than a flake. The repair is to remove the id from
    `config/lane_scopes.json`; never to relax the assertion.

    The second leg is the non-vacuity guard - a declaration file that lost its
    scopes, or a scope that lost its members, would satisfy the first leg by
    having nothing to validate.

    Args:
        repo_root: Repository root.
    """
    names = scope.scope_names(repo_root)
    assert names, "no scope is declared, so this arm validates nothing"

    for name in names:
        members = scope.scope_members(name, repo_root)
        assert members, f"scope {name} declares no members"
        assert scope.validate_scope(name, repo_root) == ()


def test_the_dashboard_scope_partitions_its_anchor_phase(repo_root: Path) -> None:
    """REQUIRED ARM, REPLACING A FLOOR. The members are an EQUALITY, not a subset.

    THE ARM THIS REPLACES WAS INSTANCE ELEVEN OF THE CS-988 DEFECT CLASS. It was
    named "is exactly the rows" and asserted a SUBSET plus ``len(phases) > 1`` -
    a floor on a population-derived quantity. Narrowing the declaration from
    eight ids to two left it green, and the lane served a quarter of its queue
    while the whole suite reported health. The floor is DELETED rather than
    tightened, because a tightened floor is still a floor.

    TWO RIGHT-HAND SIDES, NEITHER OF WHICH READS ``items``. The first is
    ``DASHBOARD_MEMBERS``, pinned in this file, so any change to the member set
    reddens. The second is the anchor phase's own takeable rows minus the
    declared EXCLUSIONS, so a new anchor-phase row nobody classified reddens too
    - something the literal alone cannot see. Both are needed and the module
    docstring records the measurement that proved it.

    Args:
        repo_root: Repository root.
    """
    members = frozenset(scope.scope_members("dashboard", repo_root))
    rows = scope.roadmap_rows(repo_root)
    fenced = scope.fenced_ids(repo_root, rows)
    anchor = scope.scope_anchor_phase("dashboard", repo_root)
    excluded = frozenset(scope.scope_exclusions("dashboard", repo_root))

    anchor_takeable = frozenset(
        row.item_id for row in rows if row.phase == anchor and row.item_id not in fenced
    )
    out_of_phase = DASHBOARD_MEMBERS - anchor_takeable

    assert anchor, "the dashboard scope anchors no phase, so it partitions nothing"
    assert anchor_takeable, "the anchor phase has no takeable row, so the equality is vacuous"
    assert excluded, "no exclusion is declared, so the partition grades nothing"

    assert members == DASHBOARD_MEMBERS
    assert members == (anchor_takeable - excluded) | out_of_phase
    assert members & excluded == frozenset()
    assert excluded <= anchor_takeable


def test_the_out_of_phase_additions_are_live_rows_outside_the_anchor_phase(
    repo_root: Path,
) -> None:
    """The pinned out-of-phase literal is what makes the subject inexpressible.

    NON-VACUITY FOR THE ARM ABOVE, AND THE REASON THE SUBJECT NEEDS A LIST AT
    ALL. If this set were empty the scope would be exactly a phase minus some
    exclusions, a phase filter would express it, and none of this machinery
    would be justified. Each member is asserted to be a live row that is NOT in
    the anchor phase, so the literal cannot quietly become a duplicate of rows
    the partition already covers.

    Args:
        repo_root: Repository root.
    """
    rows = {row.item_id: row for row in scope.roadmap_rows(repo_root)}
    anchor = scope.scope_anchor_phase("dashboard", repo_root)

    assert frozenset(rows) >= DASHBOARD_MEMBERS, (
        f"pinned but not a live row: {sorted(DASHBOARD_MEMBERS - set(rows))}"
    )

    out_of_phase = frozenset(item for item in DASHBOARD_MEMBERS if rows[item].phase != anchor)
    assert out_of_phase, "no out-of-phase addition, so a phase filter would express this subject"
    assert frozenset(rows[item].phase for item in out_of_phase) == frozenset({"Phase 4"})


def test_an_anchored_scope_refuses_a_member_deleted_without_an_exclusion(
    tmp_path: Path,
) -> None:
    """The MECHANISM refuses a silently narrowed scope, not only the suite.

    The arm above reddens at push time. This one proves the lane itself will not
    run against a subject somebody quietly shortened - the refusal names the
    orphaned row under ``UNCLASSIFIED``, which is the class that did not exist
    when the first cut was refuted.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(
        tmp_path,
        {
            "subject": {
                "description": "a partition with CS-618 quietly dropped",
                "anchor_phase": "Phase 6",
                "items": ["CS-462", "CS-603"],
                "excluded": {"CS-620": "not about the subject"},
            }
        },
    )

    with pytest.raises(scope.ScopeRefusedError) as caught:
        scope.takeable_rows("queue", root, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "subject"})

    faults = frozenset((fault.item_id, fault.reason) for fault in caught.value.faults)
    assert faults == frozenset({("CS-618", scope.UNCLASSIFIED)})
    assert "CS-618" in str(caught.value)


def test_an_anchored_scope_that_accounts_for_every_row_refuses_nothing(
    tmp_path: Path,
) -> None:
    """The non-vacuity leg for the refusal above.

    Without it a ``validate_scope`` that refused every anchored scope outright
    would satisfy the arm above and be caught by nothing.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(
        tmp_path,
        {
            "subject": {
                "description": "a complete partition",
                "anchor_phase": "Phase 6",
                "items": ["CS-462", "CS-603", "CS-618"],
                "excluded": {"CS-620": "not about the subject"},
            }
        },
    )

    assert scope.validate_scope("subject", root) == ()

    rows = scope.takeable_rows("queue", root, {lanes.LANE_SCOPE_ENV_PREFIX + "QUEUE": "subject"})
    assert tuple(row.item_id for row in rows) == SYNTHETIC_SUBJECT


@pytest.mark.parametrize(
    ("declaration", "expected"),
    [
        (
            {"items": ["CS-462", "CS-603", "CS-618"], "excluded": {"CS-618": "contradiction"}},
            frozenset(
                {
                    ("CS-618", "in_items_and_excluded"),
                    ("CS-620", "neither_member_nor_excluded"),
                }
            ),
        ),
        (
            {
                "items": ["CS-462", "CS-603", "CS-618"],
                "excluded": {"CS-620": "fine", "CS-410": "not in the anchor phase"},
            },
            frozenset({("CS-410", "excluded_but_not")}),
        ),
    ],
    ids=["member-also-excluded", "exclusion-outside-the-anchor-phase"],
)
def test_a_contradictory_partition_is_refused(
    tmp_path: Path, declaration: dict[str, object], expected: frozenset[tuple[str, str]]
) -> None:
    """INSTANCE TWELVE CHECK. The knob the repair introduced is itself graded.

    ``excluded`` is a new knob, and a knob that can quiet a red is exactly the
    shape this module was refuted over. Two ways it could be abused are refused
    here: naming a row in BOTH lists, and naming a row the anchor phase does not
    contain. What remains possible - deleting from ``items`` and adding to
    ``excluded`` in the same edit - is stated in the module docstring rather than
    claimed closed, because it takes two deliberate edits and a written reason,
    which is the loud bar rather than the silent one.

    The expected reasons are spelled by their SHORT tokens and matched by
    containment, so this arm cannot pass by transcribing the module's own
    constants back at it.

    Args:
        tmp_path: pytest temporary directory.
        declaration: The scope body to plant, less its fixed fields.
        expected: (id, reason fragment) pairs the refusal must carry.
    """
    body = {"description": "a broken partition", "anchor_phase": "Phase 6", **declaration}
    root = _write_corpus(tmp_path, {"subject": body})

    faults = scope.validate_scope("subject", root)
    seen = frozenset((fault.item_id, fault.reason) for fault in faults)

    assert seen, "no fault at all, so the contradiction went unnoticed"
    assert frozenset(item for item, _ in seen) == frozenset(item for item, _ in expected)
    for item, fragment in expected:
        reason = next(actual for found, actual in seen if found == item)
        assert fragment in reason, f"{item} refused as {reason!r}, expected to mention {fragment!r}"


# ===========================================================================
# e. The worker's callable mechanism actually runs
# ===========================================================================


def test_the_module_runs_as_a_command_and_prints_the_rows_it_computed(
    repo_root: Path, corpus: Path
) -> None:
    """`python -m ops.loop.scope` is the thing the prompt tells a worker to run.

    An instruction a worker can rationalise past is not a mechanism, which is
    `tools/headless-queue.md`'s own wording. The prompt therefore points at a
    command, and this arm proves the command exists, exits clean, and prints
    the ids the library computed rather than a different answer.

    Args:
        repo_root: Repository root, used as the interpreter's working directory.
        corpus: The synthetic root the command is pointed at.
    """
    finished = subprocess.run(
        [sys.executable, "-m", "ops.loop.scope", "--root", str(corpus), "--scope", "subject"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=_CLI_TIMEOUT_S,
    )

    assert finished.returncode == 0, finished.stderr
    printed = tuple(re.findall(r"(?m)^(CS-[0-9]+)\b", finished.stdout))
    assert printed == SYNTHETIC_SUBJECT


def test_the_command_exits_non_zero_and_names_the_offender_on_a_bad_scope(
    repo_root: Path, tmp_path: Path
) -> None:
    """A refusal reaches the worker as a non-zero exit AND a named id.

    A scoped lane that finds nothing must be distinguishable from a scoped lane
    whose scope is wrong, and for a worker reading a terminal the distinction is
    exactly this: the exit code and the offender's id in the text.

    Args:
        repo_root: Repository root, used as the interpreter's working directory.
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(
        tmp_path, {"bad": {"description": "names a closed row", "items": ["CS-603", "CS-799"]}}
    )

    finished = subprocess.run(
        [sys.executable, "-m", "ops.loop.scope", "--root", str(root), "--scope", "bad"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=_CLI_TIMEOUT_S,
    )

    assert finished.returncode != 0
    assert "CS-799" in finished.stdout + finished.stderr
    assert scope.CLOSED in finished.stdout + finished.stderr


# ===========================================================================
# e. FENCE 2 is a CLASSIFIED PARTITION, not a structural-position match
# ===========================================================================
#
# WHY THE WIDE SCAN SURVIVED THE REPAIR. `docs/GATED.md` names a genuinely
# blocked row inside a gate's PROSE - CS-G06 is the live proof - so a fence that
# read only headings, item lines or a declared field would fail open on exactly
# the rows the fence exists for. That is the denylist shape, and this project has
# measured a denylist leaking four times.
#
# WHAT CHANGED IS WHAT THE SCAN ANSWERS. The scan is the POPULATION; a
# machine-readable block in that file is the CLASSIFIER; and an id the scan finds
# that the block does not classify is GATED AND REPORTED, both rather than
# either. Omission fails CLOSED, which is what makes the block an allowlist.

#: The sentinels, SPELLED OUT HERE rather than imported from the module under
#: test. A grader that reads its subject's own constant grades nothing about the
#: constant; these two copies live in different files, so a silent rename of
#: either reddens.
_BEGIN = "CLOCKSPEED-GATE-CLASSIFICATION BEGIN"
_END = "CLOCKSPEED-GATE-CLASSIFICATION END"

#: The gate prose the synthetic file carries. It names one row the gate blocks
#: and one row it merely discusses, IN THE SAME PARAGRAPH, so nothing about a
#: line's position can separate them - only the classification can.
_GATE_PROSE = (
    "# Gated items\n"
    "\n"
    "## Open gated items\n"
    "\n"
    "### CS-G01 - something outside the repo\n"
    "\n"
    "CS-470 is blocked behind it and cannot close inside this repository.\n"
    "CS-410 is discussed here and this gate does not block it.\n"
)


def _gated_text(*classifications: str) -> str:
    """A synthetic `docs/GATED.md` whose classification block is under test control.

    Args:
        classifications: The block's body lines, in order. NONE of them means
            the file names two rows and classifies neither.

    Returns:
        The file text.
    """
    body = _GATE_PROSE
    if classifications:
        body += "\n```\n" + _BEGIN + "\n" + "\n".join(classifications) + "\n" + _END + "\n```\n"
    return body


def _fence_reasons(root: Path) -> dict[str, str]:
    """Every fenced row of a corpus, mapped to the reason it was fenced.

    Args:
        root: A synthetic root.

    Returns:
        Row id -> fault reason.
    """
    return {fault.item_id: fault.reason for fault in scope.fenced_faults(root)}


def test_a_row_this_file_merely_mentions_is_takeable(tmp_path: Path) -> None:
    """REQUIRED ARM. A MENTIONED id is not fenced.

    THE DEFECT THIS CLOSES, MEASURED ON THE LIVE FILE: fourteen live roadmap
    rows were fenced by mention alone and an adjudicator graded thirteen of them
    accidental. The sharpest was a deadlock - the row whose entire job is to
    empty a section OUT of `docs/GATED.md` was fenced BY that file, so the
    headless lane could never execute the repair.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    (root / "docs" / "GATED.md").write_bytes(
        _gated_text("gate: CS-470 BLOCKED CS-G01", "gate: CS-410 MENTIONED").encode("ascii")
    )

    takeable = frozenset(row.item_id for row in scope.rows_for_scope(None, root))

    assert takeable, "no row is takeable at all, so this arm proves nothing about CS-410"
    assert "CS-410" in takeable
    assert "CS-470" not in takeable


def test_a_row_a_gate_blocks_is_refused_and_reported_as_gated(tmp_path: Path) -> None:
    """REQUIRED ARM. A BLOCKED id is fenced, under the GATED reason.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    (root / "docs" / "GATED.md").write_bytes(
        _gated_text("gate: CS-470 BLOCKED CS-G01", "gate: CS-410 MENTIONED").encode("ascii")
    )

    classification = scope.gate_classification(root)

    assert scope.gated_ids(root) == frozenset({"CS-470"})
    assert _fence_reasons(root)["CS-470"] == scope.GATED
    assert dict(classification.blocked) == {"CS-470": "CS-G01"}
    assert classification.mentioned == frozenset({"CS-410"})
    assert classification.unclassified == ()


def test_an_id_the_block_does_not_classify_is_fenced_and_named(tmp_path: Path) -> None:
    """REQUIRED ARM. Omission fails CLOSED, and it fails LOUDLY.

    BOTH, NOT EITHER. Fencing an unclassified id without naming it would be the
    silent narrowing this module already refuses one function over; naming it
    without fencing it would make an omitted block a fail-open lever. The arm
    reads the fence set, the fault's own reason field, and the text a worker
    sees in the terminal - so a module that refuses for the right reason while
    printing nothing useful still fails here.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    (root / "docs" / "GATED.md").write_bytes(
        _gated_text("gate: CS-470 BLOCKED CS-G01").encode("ascii")
    )

    classification = scope.gate_classification(root)
    report = scope.render_report(
        scope.rows_for_scope(None, root),
        None,
        scope.fenced_faults(root),
        classification.unclassified,
    )

    assert classification.unclassified == ("CS-410",)
    assert "CS-410" in scope.gated_ids(root)
    assert _fence_reasons(root)["CS-410"] == scope.UNCLASSIFIED_GATE_MENTION
    assert "CS-410" in report
    assert scope.UNCLASSIFIED_GATE_MENTION in report


def test_dropping_one_classification_line_flips_that_row_from_takeable_to_fenced(
    tmp_path: Path,
) -> None:
    """POTENCY CONTROL. The two corpora differ by ONE line and the answer flips.

    WHY THIS ARM EXISTS AS A SEPARATE ARM. An arm whose oracle cannot observe
    the value it names passes for that reason alone, and this repository caught
    exactly that twice in one item. So rather than asserting a property of one
    fixture, this compares two fixtures that differ ONLY in the presence of
    ``CS-410 MENTIONED`` and asserts the classification MOVED. If the block were
    inert - read by nothing, or read and discarded - both sides would agree and
    this arm would fail, which is the whole point of measuring a difference
    rather than a value.

    Args:
        tmp_path: pytest temporary directory.
    """
    classified = _write_corpus(tmp_path / "classified", {})
    (classified / "docs" / "GATED.md").write_bytes(
        _gated_text("gate: CS-470 BLOCKED CS-G01", "gate: CS-410 MENTIONED").encode("ascii")
    )
    dropped = _write_corpus(tmp_path / "dropped", {})
    (dropped / "docs" / "GATED.md").write_bytes(
        _gated_text("gate: CS-470 BLOCKED CS-G01").encode("ascii")
    )

    before = scope.gated_ids(classified)
    after = scope.gated_ids(dropped)

    assert "CS-410" not in before
    assert "CS-410" in after
    assert after - before == frozenset({"CS-410"})
    assert _fence_reasons(dropped)["CS-410"] == scope.UNCLASSIFIED_GATE_MENTION


def test_an_id_classified_twice_over_is_unclassified_rather_than_resolved(
    tmp_path: Path,
) -> None:
    """A contradicted id fails CLOSED, because a partition is not a vote.

    Two lines disagreeing about one id is a declaration nobody can read, and
    picking either one would let a BLOCKED row be unfenced by appending a
    MENTIONED line below it - a fail-open lever exactly like the one this
    mechanism replaced.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    (root / "docs" / "GATED.md").write_bytes(
        _gated_text(
            "gate: CS-470 BLOCKED CS-G01", "gate: CS-470 MENTIONED", "gate: CS-410 MENTIONED"
        ).encode("ascii")
    )

    classification = scope.gate_classification(root)

    assert classification.unclassified == ("CS-470",)
    assert dict(classification.blocked) == {}
    assert "CS-470" in scope.gated_ids(root)


def test_a_classification_line_outside_the_sentinels_classifies_nothing(
    tmp_path: Path,
) -> None:
    """The BLOCK is the classifier, not the line shape.

    A sentence in gate prose that happens to read like a classification must not
    unfence a row, or quoting the mechanism inside this file would switch it off
    - the same fenced-block trap `.githooks/commit-msg` already records.

    THE PLANTED LINES ARE SPELLED THE WAY THE PARSER READS THEM, ``gate: `` AND
    ALL, and that prefix is the whole arm. A first cut spelled them ``CS-410
    MENTIONED`` with no prefix, which ``_CLASSIFY_LINE`` never matches ANYWHERE,
    so the containment was graded by nothing: deleting the ``if not inside``
    guard from ``gate_classification`` left this module at 45 passed, exit 0.
    The lines also ABUT the sentinels, one immediately above BEGIN and one
    immediately below END, because near the block and inside it is the whole
    distinction under test.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    abutting = (
        _GATE_PROSE
        + "\ngate: CS-410 MENTIONED\n"
        + "```\n"
        + _BEGIN
        + "\n"
        + _END
        + "\n```\n"
        + "gate: CS-470 MENTIONED\n"
    )
    (root / "docs" / "GATED.md").write_bytes(abutting.encode("ascii"))

    classification = scope.gate_classification(root)

    assert classification.mentioned == frozenset()
    assert classification.unclassified == ("CS-410", "CS-470")
    assert scope.gated_ids(root) == frozenset({"CS-410", "CS-470"})


def test_prose_that_quotes_a_sentinel_does_not_open_the_block(
    tmp_path: Path,
) -> None:
    """THE SENTINEL IS MATCHED WHOLE, NEVER AS A SUBSTRING.

    `docs/GATED.md` is the file most likely to DOCUMENT this mechanism, and a
    sentence naming the BEGIN sentinel is the obvious way to document it. If the
    match were a containment test rather than an equality, that sentence would
    OPEN the block over ordinary prose, and the next line spelled like a
    classification would unfence a genuinely blocked row - fail-open, silently,
    in the one file whose whole job is to fence rows.

    THIS IS THE SIBLING LEVER OF
    ``test_a_classification_line_outside_the_sentinels_classifies_nothing`` AND
    IT IS A SEPARATE ARM BECAUSE IT DIED SEPARATELY. That arm was repaired to
    plant parser-matching lines around the sentinels, and an adversary then
    turned both ``stripped == _CLASSIFY_BEGIN`` and the END comparison into
    ``in`` tests and watched the WHOLE of `tests/ops` stay at 146 passed,
    exit 0. Containment and equality are two levers and one plant cannot reach
    both.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    quoting = (
        _GATE_PROSE
        + "\nThe classifier opens at "
        + _BEGIN
        + " and this sentence is prose.\n"
        + "gate: CS-410 MENTIONED\n"
    )
    (root / "docs" / "GATED.md").write_bytes(quoting.encode("ascii"))

    classification = scope.gate_classification(root)

    assert classification.mentioned == frozenset()
    assert classification.unclassified == ("CS-410", "CS-470")
    assert scope.gated_ids(root) == frozenset({"CS-410", "CS-470"})


def test_prose_that_quotes_the_end_sentinel_does_not_close_the_block(
    tmp_path: Path,
) -> None:
    """THE OTHER SENTINEL, AND THE OTHER DIRECTION OF FAILURE.

    The two arms above detect OVER-classification: something got classified that
    should not have been. This one detects UNDER-classification, where the block
    closes EARLY over a sentence that merely quotes the END sentinel and the
    real classification lines beneath it are never read. That failure is quieter
    than the fail-open one and it is not harmless: an id the block no longer
    classifies falls to UNCLASSIFIED, so a MENTIONED row silently becomes gated
    and the lane stops serving a row nobody said was blocked.

    IT IS A THIRD ARM BECAUSE THE END SENTINEL SURVIVED THE OTHER TWO. A sweep
    of the final tree turned ``stripped == _CLASSIFY_END`` into an ``in`` test
    ON ITS OWN and the module stayed at 46 passed, exit 0 - the BEGIN half of
    the same edit reddens, the END half did not. An adversary had changed both
    comparisons together, which hid it: the BEGIN arm caught the pair and
    nothing was left to catch the half.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    quoting = (
        _GATE_PROSE
        + "\n```\n"
        + _BEGIN
        + "\n"
        + "It closes at "
        + _END
        + " and this sentence is inside the block.\n"
        + "gate: CS-470 BLOCKED CS-G01\n"
        + "gate: CS-410 MENTIONED\n"
        + _END
        + "\n```\n"
    )
    (root / "docs" / "GATED.md").write_bytes(quoting.encode("ascii"))

    classification = scope.gate_classification(root)

    assert classification.blocked == (("CS-470", "CS-G01"),)
    assert classification.mentioned == frozenset({"CS-410"})
    assert classification.unclassified == ()
    assert scope.gated_ids(root) == frozenset({"CS-470"})


def test_the_live_gated_file_classifies_every_id_its_own_scan_finds(
    repo_root: Path,
) -> None:
    """THE LIVE PARTITION IS COMPLETE, and the population is the scan's own.

    Both sides are enumerated independently: the left by the shipped module, the
    right by a regex over the same bytes that shares no code with it. The
    non-vacuity legs matter more than usual here - a `docs/GATED.md` that named
    no id at all would satisfy the equality with nothing in it.

    THIS ARM REDDENS THE DAY SOMEBODY SPELLS A NEW ID IN THAT FILE. That is the
    mechanism working. The repair is a line in the classification block, never a
    narrowed scan.

    Args:
        repo_root: Repository root.
    """
    classification = scope.gate_classification(repo_root)
    independent = frozenset(
        re.findall(r"CS-[0-9]+", (repo_root / "docs" / "GATED.md").read_text(encoding="utf-8"))
    )

    assert independent, "the live gated file names no id, so this arm grades nothing"
    assert classification.named == independent
    assert classification.mentioned, "no id is classified MENTIONED, so the partition is trivial"
    assert classification.unclassified == ()


def test_the_live_blocked_set_is_the_one_row_a_gate_actually_blocks(
    repo_root: Path,
) -> None:
    """The BLOCKED half is pinned in a second file, like ``DASHBOARD_MEMBERS``.

    WHY A LITERAL AND NOT A DERIVATION. The whole hazard the partition replaces
    is a row being unfenced by an edit to prose, and the mirror hazard is a row
    being FENCED by an edit to the block. A literal here makes either direction
    a cross-file edit somebody has to make on purpose. The standing limit is the
    same one ``DASHBOARD_MEMBERS`` records: editing both together.

    Args:
        repo_root: Repository root.
    """
    blocked = dict(scope.gate_classification(repo_root).blocked)
    rows = frozenset(row.item_id for row in scope.roadmap_rows(repo_root))

    assert blocked == {"CS-913": "CS-G06"}
    assert frozenset(blocked) <= rows, "a BLOCKED id that is not a live row fences nothing"
    assert frozenset(blocked) <= scope.gated_ids(repo_root)


def test_the_rows_unfenced_by_describe_never_number_are_pinned_as_mentions(
    repo_root: Path,
) -> None:
    """The four rows commit `7fbe529` unfenced are now pinned, not merely unnamed.

    THE HAZARD THIS CLOSES. Those four were unfenced by DELETING their numbers
    from gate prose, and nothing pinned that they stay unnamed - the next
    sentence spelling one of them would silently re-fence it. Under the
    partition they are named AND classified, so they are unfenced by a recorded
    decision rather than by the absence of evidence.

    THE LEGS SPLIT ON 2026-09-13 BECAUSE CLOSURE IS NOT A FENCE. CS-1040 and
    CS-1044 closed that day, left `ROADMAP.md`, and took the old single
    ``pinned <= takeable`` leg red with them. Deleting the two ids to get green
    was REFUSED by adjudication: shrinking a literal population until it passes
    is the CS-988 move this module's own docstring records eleven instances of.
    All four stay pinned for the classification legs, which are not row-filtered
    and so still grade a closed id; the takeable leg applies to the live subset,
    DERIVED from `ROADMAP.md` rather than written as a second literal; and every
    id that left is required to have left BY CLOSURE, read from `docs/LEDGER.md`
    - a different file from the one the other legs read, which is the only part
    of this arm not exposed to a common-mode fault in the gate block.

    THE NON-VACUITY LEG IS LOAD-BEARING. If all four ever close, ``live`` empties
    and this arm reddens rather than passing on nothing. The repair then is to
    retire the arm by a recorded decision, never to edit it green.

    Args:
        repo_root: Repository root.
    """
    classification = scope.gate_classification(repo_root)
    takeable = frozenset(row.item_id for row in scope.rows_for_scope(None, repo_root))
    rows = frozenset(row.item_id for row in scope.roadmap_rows(repo_root))
    pinned = frozenset({"CS-1040", "CS-1044", "CS-1047", "CS-1048"})
    live = pinned & rows

    assert pinned <= classification.mentioned
    assert pinned & scope.gated_ids(repo_root) == frozenset()
    assert live, "every pinned row has left ROADMAP.md, so the takeable leg grades nothing"
    assert live <= takeable
    assert pinned - live <= scope.closed_ids(repo_root)


def test_a_roadmap_line_under_the_cs_g_series_parses_as_a_row(tmp_path: Path) -> None:
    """A `CS-Gnn` row is a ROW, not an invisible line.

    THE RESIDUAL THIS CLOSES, MEASURED. The item-line pattern was
    ``^(CS-[0-9]+) - ``, which excludes the `CS-G` series entirely - so the day
    a gated item routes out of `docs/GATED.md` into `ROADMAP.md` under its own
    `CS-G` id, as that file's own header prescribes, the row would be INVISIBLE
    to the lane rather than takeable. Invisible is the worse failure: a takeable
    row refuses loudly when something is wrong with it, and a row nobody parses
    is a row nobody can miss.

    Args:
        tmp_path: pytest temporary directory.
    """
    root = _write_corpus(tmp_path, {})
    (root / "ROADMAP.md").write_bytes(
        (
            "# Roadmap\n"
            "\n"
            "## Phase 4 - save reader\n"
            "\n"
            "CS-410 - an ordinary row - acceptance: something - tier: 1\n"
            "CS-G05 - a gated item routed out under its own id - acceptance: it - tier: 2\n"
        ).encode("ascii")
    )
    (root / "docs" / "GATED.md").write_bytes(_gated_text().encode("ascii"))

    parsed = tuple(row.item_id for row in scope.roadmap_rows(root))

    assert parsed == ("CS-410", "CS-G05")
    assert scope.roadmap_rows(root)[1].phase == "Phase 4"
