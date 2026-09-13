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
contiguous and are not one phase: seven sit under `## Phase 6 - surfaces` and one
sits in the phase 4 block. No phase filter expresses that subject, so the subject
has to be written down. The price of writing it down is drift, and the whole
point of ``validate_scope`` is that the price is paid LOUDLY, on every read,
naming the offender - never by quietly answering an empty queue.

NO FLOOR GRADES ANY POPULATION IN THIS MODULE. A floor grades the bottom of a
range and nothing else, which is the CS-988 defect class. Every population claim
below is a set EQUALITY, and each equality's two sides are enumerated from
sources that share no constant.

WHEN THIS MODULE GOES RED ON A LIVE DECLARATION, THAT IS THE MECHANISM WORKING.
``test_the_declared_scopes_all_validate_against_the_live_roadmap`` reddens the
day a declared member closes, is gated, or is renamed out of `ROADMAP.md`. The
repair is to edit `config/lane_scopes.json`, never to weaken the arm.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

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

#: `docs/GATED.md` carries CS-470 and nothing else this corpus names.
SYNTHETIC_GATED = """# Gated items

## Open gated items

### CS-G01 - something outside the repo

CS-470 is blocked behind it and cannot close inside this repository.
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

#: Every id the synthetic roadmap carries that is NOT in the subject and is not
#: fenced out. Written from the corpus above by hand and cross-checked against
#: the parser in ``test_the_synthetic_corpus_parses_to_the_rows_it_was_written_with``.
SYNTHETIC_TAKEABLE_UNSCOPED = ("CS-410", "CS-462", "CS-603", "CS-618", "CS-620")


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


def test_the_dashboard_scope_is_exactly_the_rows_the_live_surface_work_sits_on(
    repo_root: Path,
) -> None:
    """The dashboard scope's members are rows, and they span more than one phase.

    The second leg is the load-bearing one. A scope that collapsed to a single
    phase would be expressible as a phase filter, and the whole reason this
    subject needs a written-down list is that it is not.

    Args:
        repo_root: Repository root.
    """
    members = frozenset(scope.scope_members("dashboard", repo_root))
    rows = {row.item_id: row for row in scope.roadmap_rows(repo_root)}

    assert members, "the dashboard scope declares no members"
    assert members <= frozenset(rows), f"declared but not a live row: {sorted(members - set(rows))}"

    phases = frozenset(rows[item].phase for item in members)
    assert len(phases) > 1, f"the dashboard subject sits in one phase only: {sorted(phases)}"


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
    )

    assert finished.returncode != 0
    assert "CS-799" in finished.stdout + finished.stderr
    assert scope.CLOSED in finished.stdout + finished.stderr
