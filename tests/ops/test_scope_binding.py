"""The row a cycle WORKED is bound to the row the lane was PERMITTED to work.

WHAT WAS BROKEN. `ops/loop/scope.py` computed the takeable rows correctly and
`ops/loop/claims.py` recorded which row was in flight, and NOTHING IN THE DRIVER
PATH IMPORTED EITHER. A repo-wide grep for both names across `ops/loop/queue_loop.py`,
`ops/loop/lane_launcher.py` and the runner returned unrelated docstring prose. The
only bridge from those two mechanisms to the row a worker actually took was a
hand-transcription of printed text by the worker itself - which is the shape
`tools/headless-queue.md` section 1 calls "an instruction a worker can rationalize
past", about a rule that had already failed four times out of six.

WHAT IS GRADED HERE, in one sentence: the driver computes the permitted set
BEFORE the cycle, samples the claim store WHILE the worker runs, and writes the
comparison into the cycle RECORD, where a roll-up that refuses `ok` reads it.

THE THREE HALVES ARE GRADED APART, because each one fails differently:

- ``scope.lane_permit`` answers what the lane may take. Graded by SET EQUALITY
  against a second enumeration hand-written in this module from the synthetic
  corpus - no shared constant, and no length, floor or count anywhere.
- ``queue_loop.ClaimWatch`` answers what the lane actually held. It samples
  DURING the cycle rather than after it, and the arm that proves why carries its
  own control: the worker releases the claim before the cycle ends, so a
  post-cycle read of the same store finds nothing and the row is known anyway.
- ``scope.binding_fact`` compares the two. Graded on each of its four answers,
  each against a control differing in one thing.

THE RECORD IS THE ACCEPTANCE, NOT THE LOG LINE. CS-993 measured why: a marker
that goes only to the driver's stdout is truncated at every launch, so a row an
operator reads at 3am is byte-identical to a row that earned its verdict. The
arms therefore read the JSONL the driver wrote and never the console.

NO ARM HERE PASSES THE PRODUCTION PATH ITS OWN ANSWER. The run_loop legs differ
in the claimed row and in nothing else; the claim-store legs differ in one field
of one record. An arm whose fixture supplies the thing the code derives grades
the fixture, which is how a claim-exclusion arm shipped last week blind to the
rooting bug it was written for.
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip. A missing driver or a missing store must
# be a COLLECTION ERROR naming the module, not a skip that leaves the binding
# unmeasured and the run green - CONVENTIONS.md section 7.2.
from ops.loop import claims, lanes, queue_loop, scope  # noqa: E402

# CS-1104 - the live-channel audit, AUTOUSE by import: any test here that lists or
# opens `moon_sync_inbox/` or its seen store fails at teardown. One owner of the
# hook, in tests/test_queue_loop.py; tests/ops has no conftest to share it through.
from tests.test_queue_loop import channel_audit  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Synthetic corpus. Hand-authored and deliberately NOT a slice of the live docs
# - CLAUDE.md section 7 settles that fixtures are synthetic.
# ---------------------------------------------------------------------------

#: A `ROADMAP.md` shaped like the real one: two phases, a gate row in each
#: recognisable only by its own headline, a gated row, and ordinary rows either
#: side of a phase boundary.
SYNTHETIC_ROADMAP: Final = """# Roadmap - OPEN work only

One line per item.

## Phase 4 - save reader

CS-400 - Phase 4 gate: everything below closes first - acceptance: all of it - tier: 2
CS-421 - an ordinary row outside the subject - acceptance: something - tier: 1
CS-433 - a subject row filed outside its phase - acceptance: something - tier: 2
CS-444 - a gated row that must never be taken - acceptance: something - tier: 2

## Phase 6 - surfaces

CS-600 - Phase 6 gate: the surface rolls up here - acceptance: all of it - tier: 2
CS-655 - a subject row - acceptance: something - tier: 1
CS-661 - another subject row - acceptance: something - tier: 2
CS-677 - an ordinary row outside the subject - acceptance: something - tier: 1
"""

#: `docs/GATED.md` carries CS-444 and nothing else this corpus names.
SYNTHETIC_GATED: Final = """# Gated items

## Open gated items

### CS-G02 - something outside the repo

CS-444 is blocked behind it and cannot close inside this repository.
"""

#: `docs/LEDGER.md`. CS-701 closed and is in no roadmap row, which is what a
#: closed id looks like from the outside.
SYNTHETIC_LEDGER: Final = """# Ledger

## Entries

### 2026-09-13 - CS-701 - CLOSED. It shipped and it is done

Body.
"""

#: The subject the corpus scope names.
SUBJECT_ITEMS: Final = ("CS-433", "CS-655", "CS-661")

#: THE SECOND ENUMERATION, AND IT SHARES NO CONSTANT WITH THE PARSER. Written by
#: reading the corpus above by eye: the two gate rows go by FENCE 1, CS-444 goes
#: by FENCE 2, and these five are what is left. A floor over the count would
#: hold against any four of them, so the arms below compare SETS.
TAKEABLE_UNSCOPED: Final = frozenset({"CS-421", "CS-433", "CS-655", "CS-661", "CS-677"})

#: A takeable row the subject scope deliberately does NOT name. The out-of-scope
#: leg uses this rather than an invented id, so the arm measures the SCOPE
#: rather than the existence fence, which already has its own coverage.
OUTSIDE_THE_SUBJECT: Final = "CS-677"

#: A row the subject scope does name, for the control leg.
INSIDE_THE_SUBJECT: Final = "CS-655"

#: The lane the arms drive, and one that is not it.
LANE: Final = lanes.LANES[0]
OTHER_LANE: Final = lanes.LANES[1]

#: The scope name declared in the corpus, and one that is not declared.
SCOPE_NAME: Final = "subject"
UNDECLARED_SCOPE: Final = "no-such-subject"


def _write_corpus(root: Path, scopes: dict[str, Any]) -> Path:
    """Lay the synthetic docs and a scope declaration out under ``root``."""
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
        tmp_path / "corpus",
        {"subject": {"description": "the synthetic subject", "items": list(SUBJECT_ITEMS)}},
    )


def _env(scope_name: str | None) -> dict[str, str]:
    """An environment pointing the lane at ``scope_name``, or at nothing."""
    if scope_name is None:
        return {}
    return {lanes.LANE_SCOPE_ENV_PREFIX + LANE.upper(): scope_name}


# ===========================================================================
# a. The permit - what the lane is ALLOWED to work
# ===========================================================================


def test_the_permit_is_the_scopes_takeable_rows_and_is_compared_as_a_set(corpus: Path) -> None:
    permit = scope.lane_permit(LANE, corpus, _env(SCOPE_NAME))

    assert permit["ok"] is True, permit["detail"]
    assert permit["lane_scope"] == SCOPE_NAME
    # SET EQUALITY against the hand-written enumeration. Deleting a member from
    # the corpus declaration reddens this; so does a fence that stops firing,
    # because the left side would then gain a gate row.
    assert set(permit["allowed"]) == set(SUBJECT_ITEMS)


def test_an_unscoped_lane_is_permitted_every_takeable_row_and_no_fenced_one(corpus: Path) -> None:
    permit = scope.lane_permit(LANE, corpus, _env(None))

    assert permit["ok"] is True, permit["detail"]
    assert permit["lane_scope"] is None
    # THE CONTROL FOR THE ARM ABOVE. Without it, a permit that answered the
    # whole file whatever it was pointed at would satisfy neither arm's
    # complement - and this one also proves the three fences fire at all,
    # because the two gate rows and the gated row are absent from a set that
    # was NOT narrowed by any scope.
    assert set(permit["allowed"]) == set(TAKEABLE_UNSCOPED)


def test_a_permit_that_could_not_be_computed_permits_nothing_rather_than_everything(
    corpus: Path,
) -> None:
    permit = scope.lane_permit(LANE, corpus, _env(UNDECLARED_SCOPE))

    assert permit["ok"] is False
    # EMPTY, not the whole file. A refusal that fell back to every row would
    # turn the loudest failure this module has into the quietest.
    assert set(permit["allowed"]) == set()
    # THE DETAIL IS THE NAMED FIELD `ScopeRefusedError.detail`, never the
    # exception object - CLAUDE.md non-negotiable 12. The scope name is what
    # makes it actionable at 3am.
    assert UNDECLARED_SCOPE in permit["detail"]


# ===========================================================================
# b. The comparison - binding a worked row to a permit
# ===========================================================================


def _permit(allowed: tuple[str, ...] = SUBJECT_ITEMS) -> dict[str, Any]:
    """A computed permit, as ``lane_permit`` answers one."""
    return {"ok": True, "lane_scope": SCOPE_NAME, "allowed": allowed, "detail": ""}


def test_a_worked_row_inside_the_permit_binds() -> None:
    fact = scope.binding_fact(_permit(), (INSIDE_THE_SUBJECT,), committed=True)

    assert fact["bound"] is True
    assert fact["checked"] is True
    assert fact["observed"] is True
    assert fact["reason"] == ""
    assert set(fact["worked"]) == {INSIDE_THE_SUBJECT}
    assert set(fact["outside"]) == set()


def test_a_worked_row_outside_the_permit_refuses_and_names_the_row() -> None:
    fact = scope.binding_fact(_permit(), (OUTSIDE_THE_SUBJECT,), committed=True)

    assert fact["bound"] is False
    assert fact["reason"] == scope.OUT_OF_SCOPE
    # NAMED, because a refusal nobody can act on is a refusal nobody acts on.
    assert set(fact["outside"]) == {OUTSIDE_THE_SUBJECT}
    assert OUTSIDE_THE_SUBJECT in fact["detail"]


def test_one_row_outside_the_permit_refuses_a_cycle_that_also_worked_an_allowed_one() -> None:
    # THE ANY-RULE, PINNED. A cycle that touched two rows is refused on the one
    # it may not take; grading the FIRST row, or the majority, would let a
    # worker launder an out-of-scope row behind an in-scope one.
    fact = scope.binding_fact(_permit(), (INSIDE_THE_SUBJECT, OUTSIDE_THE_SUBJECT), committed=True)

    assert fact["bound"] is False
    assert set(fact["outside"]) == {OUTSIDE_THE_SUBJECT}
    assert set(fact["worked"]) == {INSIDE_THE_SUBJECT, OUTSIDE_THE_SUBJECT}


def test_a_cycle_that_committed_while_holding_no_claim_is_recorded_as_unobserved() -> None:
    fact = scope.binding_fact(_permit(), (), committed=True)

    assert fact["observed"] is False
    assert fact["reason"] == scope.UNNAMED
    # NOT A REFUSAL, AND THE RESIDUAL IS THE POINT OF THIS ASSERTION RATHER THAN
    # AN ADMISSION HIDDEN IN IT. Nothing was checked here, so nothing failed.
    # The clause that would refuse it is one turn of the ratchet away and was
    # not taken, because no worker claims a row today and a refusal that fires
    # on every cycle of every night is one nobody reads. Flipping this to False
    # is the edit that closes the gap, and `binding_fact`'s docstring records
    # what has to happen first.
    assert fact["bound"] is True


def test_a_cycle_that_worked_nothing_at_all_carries_no_reason_at_all() -> None:
    # THE CONTROL FOR THE ARM ABOVE, and the two differ in `committed` alone.
    # A lane_held cycle, a launch failure and a worker that gave up all reach
    # here, and reporting them as an observation gap would drown the real gaps
    # in cycles that never had a row to observe.
    fact = scope.binding_fact(_permit(), (), committed=False)

    assert fact["bound"] is True
    assert fact["observed"] is False
    assert fact["reason"] == ""


def test_an_uncomputed_permit_leaves_the_cycle_unbound_rather_than_unchecked(
    corpus: Path,
) -> None:
    refused = scope.lane_permit(LANE, corpus, _env(UNDECLARED_SCOPE))
    fact = scope.binding_fact(refused, (INSIDE_THE_SUBJECT,), committed=True)

    assert fact["checked"] is False
    assert fact["bound"] is False
    assert fact["reason"] == scope.UNCOMPUTED
    # THE CONTROL: the SAME worked row against a computed permit binds, so the
    # refusal above is attributable to the permit and not to the row.
    assert scope.binding_fact(_permit(), (INSIDE_THE_SUBJECT,), committed=True)["bound"] is True


# ===========================================================================
# c. The observation - which row the lane actually held
# ===========================================================================


def _worktree(tmp_path: Path, name: str) -> Path:
    """A directory standing in for a lane worktree - never the main tree."""
    path = tmp_path / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_the_driver_learns_a_row_the_worker_claims_and_releases_inside_the_cycle(
    tmp_path: Path,
) -> None:
    root = tmp_path / "claims"
    watch = queue_loop.ClaimWatch(LANE, started_at=time.time(), root=root)

    held = claims.try_claim_row(
        INSIDE_THE_SUBJECT,
        lane=LANE,
        run_id="r1",
        worktree=_worktree(tmp_path, "wt"),
        root=root,
    )
    assert held["ok"] is True, held
    watch.sample()
    released = claims.release_claim(held["token"], root=root)
    assert released is True

    # THE CONTROL, AND IT IS THE WHOLE POINT OF SAMPLING DURING THE CYCLE. A
    # reader arriving after the wrap sees an empty store, so an arm that read
    # the store post-cycle would grade nothing and would pass on a driver that
    # never looked at all.
    assert claims.claim_states(root) == {}
    assert set(watch.rows()) == {INSIDE_THE_SUBJECT}


def test_a_claim_another_lane_holds_is_not_read_as_this_lanes_row(tmp_path: Path) -> None:
    root = tmp_path / "claims"
    started = time.time()
    theirs = claims.try_claim_row(
        OUTSIDE_THE_SUBJECT,
        lane=OTHER_LANE,
        run_id="r2",
        worktree=_worktree(tmp_path, "wt-b"),
        root=root,
    )
    assert theirs["ok"] is True, theirs

    assert set(queue_loop.ClaimWatch(LANE, started_at=started, root=root).sample()) == set()
    # THE CONTROL: the SAME record, read for the lane that wrote it, IS its row.
    # Without this the arm above would hold on a watch that reads nothing at all.
    assert set(queue_loop.ClaimWatch(OTHER_LANE, started_at=started, root=root).sample()) == {
        OUTSIDE_THE_SUBJECT
    }


def test_a_claim_left_behind_by_an_earlier_cycle_is_not_attributed_to_this_one(
    tmp_path: Path,
) -> None:
    root = tmp_path / "claims"
    stale = claims.try_claim_row(
        OUTSIDE_THE_SUBJECT,
        lane=LANE,
        run_id="old",
        worktree=_worktree(tmp_path, "wt"),
        root=root,
    )
    assert stale["ok"] is True, stale
    # AGED THROUGH THE STORE'S OWN RECORD rather than hand-written beside it, so
    # the arm cannot drift from the format `claims.py` actually writes. An hour
    # old is the shape of a lane whose previous cycle died holding its row.
    aged = 3600.0
    record_path = claims.claim_path(OUTSIDE_THE_SUBJECT, root)
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    payload["ts"] = float(payload["ts"]) - aged
    record_path.write_text(json.dumps(payload), encoding="utf-8")

    now = time.time()
    fresh_cycle = queue_loop.ClaimWatch(LANE, started_at=now, root=root)
    assert set(fresh_cycle.sample()) == set()

    # THE CONTROL, AND THE TWO LEGS DIFFER IN `started_at` ALONE: a cycle that
    # has itself been running for two hours COULD have produced an hour-old
    # record, and does see it. Without this leg the exclusion above would hold
    # just as well on a watch that read nothing at all.
    long_cycle = queue_loop.ClaimWatch(LANE, started_at=now - 2 * aged, root=root)
    assert set(long_cycle.sample()) == {OUTSIDE_THE_SUBJECT}


def test_the_watch_reads_the_stores_own_default_root_and_invents_none() -> None:
    seen: list[Any] = []

    def spy(root: Any = None, _now: Any = None) -> dict[str, Any]:
        """Record the root the watch asked for and answer an empty store."""
        seen.append(root)
        return {}

    watch = queue_loop.ClaimWatch(LANE, started_at=time.time(), states=spy)
    watch.sample()

    # NOT VACUOUS: the call happened, and it named no root. Two builders rooted
    # a worker-side store at `Path(__file__).parent` in one day, and each lane's
    # worker runs in its OWN checkout, so a root spelled anywhere but inside the
    # store is a store the other lane cannot see. `claims.DEFAULT_ROOT` resolves
    # the main tree for itself; the driver's job is to not get in the way.
    assert seen == [None]


def test_a_store_that_cannot_be_read_is_recorded_rather_than_raised() -> None:
    def angry(_root: Any = None, _now: Any = None) -> dict[str, Any]:
        """A store read that fails the way a locked or vanished directory does."""
        message = "the claim store could not be read"
        raise OSError(message)

    watch = queue_loop.ClaimWatch(LANE, started_at=time.time(), states=angry)

    # NEVER RAISES. This runs on the poll path inside `run_cycle`, and a fault
    # escaping there would take the driver down with no ledger row and no exit
    # code for the launcher to read.
    assert set(watch.sample()) == set()
    assert watch.faults == 1

    # THE CONTROL. The fault is a COUNTED FIELD, so a night whose store was
    # unreadable is distinguishable from a night that observed a genuinely
    # empty one - and without this leg the count above would hold on a watch
    # that counted every sample as a fault.
    clean = queue_loop.ClaimWatch(LANE, started_at=time.time(), states=lambda *_a, **_k: {})
    assert set(clean.sample()) == set()
    assert clean.faults == 0


def test_the_driver_samples_while_the_worker_is_up_and_again_once_it_is_down(
    tmp_path: Path,
) -> None:
    up = {"alive": True}
    polls = {"n": 0}
    seen: list[bool] = []
    #: How many polls the worker survives. More than one, so a sample taken on
    #: the first pass alone cannot stand in for sampling THROUGHOUT the wait.
    live_polls = 2

    def alive(_pid: Any) -> bool:
        """Alive for two polls, then gone - a worker that finished normally."""
        polls["n"] += 1
        if polls["n"] > live_polls:
            up["alive"] = False
        return up["alive"]

    queue_loop.run_cycle(
        1,
        lane=LANE,
        worktree=_worktree(tmp_path, "wt"),
        run_id="r",
        acquire=lambda _lane, **_kw: {"ok": True, "token": "T"},
        release=lambda _token, **_kw: True,
        launch=lambda _lane, **_kw: {"pid": 7, "log": "l"},
        alive=alive,
        proc_started=lambda _pid: 1.0,
        stranger=lambda _pid, _s: False,
        kill=lambda _pid: None,
        observe=lambda: seen.append(up["alive"]),
        sleep=lambda _s: None,
        clock=lambda: 1000.0,
        monotonic=lambda: 1.0,
    )

    # SET EQUALITY OVER WHAT WAS TRUE AT EACH SAMPLE, not a count of samples. A
    # floor over the number of reads would be met by the post-cycle one alone,
    # which is the read that learns nothing from a worker that released its
    # claim at the wrap. Deleting the in-loop call leaves {False}; deleting the
    # one after the wait leaves {True}; both redden.
    assert set(seen) == {True, False}


# ===========================================================================
# d. The wiring - the comparison reaches the cycle RECORD
# ===========================================================================


def _drive_one_cycle(tmp_path: Path, name: str, corpus_root: Path, store: dict[str, Any]) -> Any:
    """One real `run_loop` cycle over a canned claim store. Returns the row.

    The claim store is the injected seam here rather than a real directory,
    because the property under test is what the RECORD says about what was
    observed; the observation itself is graded against a real store in section
    c above, where a canned one would have hidden the rooting question.
    """
    log = tmp_path / f"{name}.jsonl"
    lines: list[str] = []

    queue_loop.run_loop(
        max_cycles=1,
        settle_s=0,
        poll_s=1,
        ci_gate=False,
        local_suite=False,
        lane=LANE,
        worktree=tmp_path / f"tree-{name}",
        permit=lambda lane: scope.lane_permit(lane, corpus_root, _env(SCOPE_NAME)),
        claim_states=lambda _root=None, _now=None: dict(store),
        acquire=lambda _lane, **_kw: {"ok": True, "token": "T"},
        release=lambda _token, **_kw: True,
        launch=lambda _lane, **_kw: {"pid": 1, "log": "l"},
        alive=lambda _pid: False,
        proc_started=lambda _pid: 1.0,
        stranger=lambda _pid, _s: False,
        kill=lambda _pid: None,
        head_sha=lambda: "sha",
        tree_sha=lambda _tree: "tree-sha",
        cycle_log=log,
        control_dir=tmp_path / f"control-{name}",
        hold=contextlib.nullcontext,
        sleep=lambda _s: None,
        emit=lines.append,
    )
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
    drove = len(rows)
    assert drove == 1, f"the {name} leg drove {drove} cycles rather than one"
    rows[0]["_emitted"] = "\n".join(lines)
    return rows[0]


def _store(row: str) -> dict[str, Any]:
    """A claim store reading holding ``row`` for this lane, claimed just now."""
    return {
        row: {
            "state": claims.HELD,
            "age_s": 1.0,
            "row": row,
            "lane": LANE,
            "pid": 4242,
            "run_id": "r",
            "worktree": "wt",
        }
    }


def test_a_row_outside_the_permit_reaches_the_record_and_refuses_the_roll_up(
    tmp_path: Path, corpus: Path
) -> None:
    outside = _drive_one_cycle(tmp_path, "outside", corpus, _store(OUTSIDE_THE_SUBJECT))
    inside = _drive_one_cycle(tmp_path, "inside", corpus, _store(INSIDE_THE_SUBJECT))

    # THE TWO LEGS DIFFER IN THE CLAIMED ROW AND IN NOTHING ELSE: same permit,
    # same worker outcome, same seams. So a difference in the roll-up is
    # attributable to the row and to nothing else.
    assert outside["outcome"] == inside["outcome"]

    assert outside["scope"]["bound"] is False
    assert set(outside["scope"]["outside"]) == {OUTSIDE_THE_SUBJECT}
    assert outside["scope"]["reason"] == scope.OUT_OF_SCOPE
    # THE ROLL-UP REFUSES. A marker that reached the row but left `ok` true
    # would leave a violating cycle indistinguishable from an earned one by the
    # one field every reader of this file sorts on.
    assert outside["ok"] is False

    assert inside["scope"]["bound"] is True
    assert set(inside["scope"]["worked"]) == {INSIDE_THE_SUBJECT}
    assert inside["ok"] is True


def test_the_console_line_carries_the_refusal_as_well_as_the_row(
    tmp_path: Path, corpus: Path
) -> None:
    outside = _drive_one_cycle(tmp_path, "note-out", corpus, _store(OUTSIDE_THE_SUBJECT))
    inside = _drive_one_cycle(tmp_path, "note-in", corpus, _store(INSIDE_THE_SUBJECT))

    # The row is the acceptance and the line is the 3am convenience. The token
    # appears only on the leg that was refused, so deleting it from the note
    # reddens the first assertion and emitting it unconditionally reddens the
    # second.
    assert queue_loop.SCOPE_NOTE in outside["_emitted"]
    assert queue_loop.SCOPE_NOTE not in inside["_emitted"]


def test_every_cycle_carries_the_binding_even_when_no_row_was_ever_claimed(
    tmp_path: Path, corpus: Path
) -> None:
    quiet = _drive_one_cycle(tmp_path, "quiet", corpus, {})

    # WRITTEN RATHER THAN OMITTED - the CS-993 shape. An absent key makes a
    # cycle nobody checked read exactly like a cycle that passed the check.
    assert "scope" in quiet
    assert quiet["scope"]["checked"] is True
    assert set(quiet["scope"]["worked"]) == set()
    # This cycle committed nothing, so there was no row to bind and the roll-up
    # is left alone.
    assert quiet["scope"]["bound"] is True
    assert quiet["ok"] is True
