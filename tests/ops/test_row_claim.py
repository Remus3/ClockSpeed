#!/usr/bin/env python3
"""CS-991 - a row in flight is claimed, so a second lane cannot take it.

WHAT THIS GRADES. `tools/headless-queue.md` section 5 defines the queue as
`ROADMAP.md` read top to bottom with the first surviving row taken, and its
FENCE 6 rules that a row is done only when its id carries a closure record in
`docs/LEDGER.md`. That record is written at the END of a cycle. So for the whole
length of a cycle the row in flight is indistinguishable from an untaken one,
and before this item nothing on disk said otherwise. CS-992 widened the roster,
which turned that from a latent shape into a reachable one: two lanes now poll
one `ROADMAP.md`.

THE THREE ARMS THE ITEM REQUIRES, and each is written so that one stated edit
reddens it:

  * ``test_a_second_lane_offered_the_same_queue_takes_a_different_row``
  * ``test_a_dead_claimants_row_returns_to_the_queue``
  * ``test_a_crashed_cycle_does_not_release_its_claim``

WHY A REAL DEAD PID AND A REAL CRASHED CHILD rather than a patched probe. A
monkeypatched ``pid_alive`` grades the branch that reads its answer and says
nothing about whether the probe can observe a process at all, and a claim store
that stat-ed the file would pass every patched arm. So the liveness arms take a
pid from a child this test started and then reaped, and the crash arm takes one
from a child that called ``os._exit`` past its own cleanup. Both are FRONTED BY
A CONTROL asserting the probe answers True for this very process and False for
the reaped one - without it, a probe that answered False for everything would
make the arm pass for the wrong reason, and a pid the operating system had
already reissued would make it pass for no reason at all.

POPULATIONS ARE GRADED BY SET EQUALITY, NEVER BY A COUNT OVER A THRESHOLD. A
threshold grades the bottom of a range and is satisfied by the strongest member
of a population while the weakest goes unmeasured (CS-988). Where a population
is asserted here, one side is what the API RETURNED and the other is a walk of
the claim directory on disk, so the two enumerations share no constant.

PATHS ARE BOUND TO SCALARS BEFORE THEY ARE ASSERTED ON. pytest renders an
asserted expression's sub-expressions with their own reprs whatever message the
assertion carries (CS-850), so a ``Path`` left inside an assertion would print a
temporary directory - and on this platform a temporary directory carries the
account name - into the failure report.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing claim store must be a COLLECTION
# ERROR naming the module, not a silent skip that leaves the lane unguarded and
# the run green.
from ops.loop import claims, lanes  # noqa: E402

#: Row ids used by the arms. SYNTHETIC AND OUT OF THE `CS-` SPACE THE PROJECT
#: USES, so an arm can never collide with a real row somebody is working, and so
#: a reader cannot mistake one of these for a citation.
ROW_A: Final = "ROW-0001"
ROW_B: Final = "ROW-0002"
ROW_C: Final = "ROW-0003"

#: The lanes the arms drive. Taken from the roster rather than spelled, because
#: a lane off the roster is refused by ``lanes.slot_index`` and the arm would
#: then be measuring the roster check instead of the claim store.
LANE_A: Final = lanes.LANES[0]
LANE_B: Final = lanes.LANES[1]

#: What a claimant that dies without releasing exits with. Distinctive so the
#: parent can tell a deliberate crash from an import failure or a traceback.
CRASH_CODE: Final = 97


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _worktree(tmp_path: Path, name: str) -> Path:
    """A directory that is not the main tree, so the worktree guard admits it."""
    tree = tmp_path / name
    tree.mkdir(parents=True, exist_ok=True)
    return tree


def _offered() -> tuple[str, ...]:
    """The queue a lane is offered. One source, used by both lanes."""
    return (ROW_A, ROW_B, ROW_C)


def _snapshot(root: Path) -> dict[str, bytes]:
    """Every file under the claim root, by name, with its bytes.

    Compared before and against after, this catches a read that wrote - whether
    it unlinked, rewrote or added a file.
    """
    if not root.exists():
        return {}
    return {path.name: path.read_bytes() for path in sorted(root.iterdir()) if path.is_file()}


def _rows_on_disk(root: Path) -> set[str]:
    """The rows the claim directory RECORDS, read by walking it.

    Deliberately independent of ``claims.claim_states``: an arm that graded the
    store's own enumeration against the store's own enumeration would pass on a
    store that had forgotten every claim it wrote.
    """
    if not root.exists():
        return set()
    found: set[str] = set()
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix != claims.CLAIM_SUFFIX:
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and record.get("row") is not None:
            found.add(str(record["row"]))
    return found


def _plant(root: Path, row: str, **overrides: Any) -> Path:
    """Write a claim record by hand, bypassing the acquire path.

    Used where an arm needs a holder this process could not legitimately become
    - a dead pid, for instance.
    """
    root.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "row": row,
        "lane": LANE_A,
        "run_id": "planted",
        "worktree": str(root),
        "pid": os.getpid(),
        "ts": 1.0,
    }
    record.update(overrides)
    target = root / f"{row}{claims.CLAIM_SUFFIX}"
    target.write_text(json.dumps(record), encoding="utf-8")
    return target


def _reaped_pid() -> int:
    """A pid whose process this test started and then waited for.

    A pid picked out of the air names whatever the operating system has since
    issued it to; one that was reaped a moment ago is known dead by
    construction, and the control in each arm re-establishes that at the moment
    the arm runs rather than trusting the construction.
    """
    child = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(0)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    child.wait()
    return int(child.pid)


_CRASHING_CLAIMANT: Final = """
import os
import sys

sys.path.insert(0, sys.argv[1])

from ops.loop import claims

answer = claims.try_claim_row(
    sys.argv[2],
    lane=sys.argv[3],
    run_id="crashing",
    worktree=sys.argv[4],
    root=sys.argv[5],
)
sys.stdout.write("{0}|{1}".format(answer.get("ok"), os.getpid()))
sys.stdout.flush()
# NOT sys.exit, and that is the whole point of this child. SystemExit unwinds
# the stack and would run any finally, atexit hook or context manager the claim
# store had leaned on; os._exit does not, so what survives on disk is what a
# genuinely killed cycle leaves behind.
os._exit({code})
""".replace("{code}", str(CRASH_CODE))


def _crash_after_claiming(tmp_path: Path, row: str, root: Path) -> tuple[bool, int]:
    """Claim ``row`` in a child process that then dies past its own cleanup.

    Returns:
        Whether the child reported the claim taken, and the child's pid.
    """
    script = tmp_path / "crashing_claimant.py"
    script.write_text(_CRASHING_CLAIMANT, encoding="utf-8")
    done = subprocess.run(
        [
            sys.executable,
            str(script),
            str(ROOT),
            row,
            LANE_A,
            str(_worktree(tmp_path, "crashtree")),
            str(root),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    exited_as_told = done.returncode == CRASH_CODE
    assert exited_as_told, f"the child did not reach its crash - stderr was {done.stderr!r}"
    reported, _, spelled = done.stdout.partition("|")
    return reported == "True", int(spelled)


# ===========================================================================
# a. Two lanes, one queue - the claimed row is not offered twice
# ===========================================================================


def test_a_second_lane_offered_the_same_queue_takes_a_different_row(tmp_path: Path) -> None:
    """ACCEPTANCE 1. A row taken by one lane is not takeable by another.

    Both lanes are handed the SAME offered queue from one source, so nothing
    but the claim store can make their answers differ. The population is graded
    three ways - what the calls returned, what the disk records, and the head of
    the offered queue - and those enumerations share no constant.
    """
    root = tmp_path / "claims"
    offered = _offered()

    first = claims.first_takeable(offered, root=root)
    taken_a = claims.try_claim_row(
        first, lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt-a"), root=root
    )
    a_ok = bool(taken_a["ok"])
    assert a_ok, "the first lane could not claim an unclaimed row"

    second = claims.first_takeable(offered, root=root)
    taken_b = claims.try_claim_row(
        second, lane=LANE_B, run_id="b", worktree=_worktree(tmp_path, "wt-b"), root=root
    )
    b_ok = bool(taken_b["ok"])
    assert b_ok, "the second lane could not claim any row at all"

    distinct = taken_a["row"] != taken_b["row"]
    assert distinct, "both lanes took the same row"

    reported = {str(taken_a["row"]), str(taken_b["row"])}
    expected = {offered[0], offered[1]}
    took_the_head_in_order = reported == expected
    assert took_the_head_in_order, f"the two lanes took {sorted(reported)}"

    recorded = _rows_on_disk(root)
    disk_agrees = recorded == reported
    assert disk_agrees, f"the claim directory records {sorted(recorded)}"


def test_a_claimed_row_is_refused_to_a_second_lane_that_asks_for_it_directly(
    tmp_path: Path,
) -> None:
    """The other half of acceptance 1, and the half a queue filter cannot give.

    ``first_takeable`` merely declines to OFFER a claimed row. A lane that names
    the row itself - because an operator pointed it there, or because it read
    the file by hand - has to be refused at the claim, and the refusal has to
    touch nothing on disk. REFUSE, DO NOT QUEUE, as the lane lock already rules.
    """
    root = tmp_path / "claims"
    held = claims.try_claim_row(
        ROW_A, lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt-a"), root=root
    )
    held_ok = bool(held["ok"])
    assert held_ok, "the first claim did not land, so the refusal proves nothing"

    before = _snapshot(root)
    refused = claims.try_claim_row(
        ROW_A, lane=LANE_B, run_id="b", worktree=_worktree(tmp_path, "wt-b"), root=root
    )
    refused_ok = bool(refused["ok"])
    assert refused_ok is False, "a claimed row was handed to a second lane"

    reason = refused.get("refused")
    assert reason == "row_claimed", f"the refusal was reported as {reason!r}"

    holder = refused.get("lane")
    assert holder == LANE_A, f"the refusal names {holder!r} as the holder"

    untouched = _snapshot(root) == before
    assert untouched, "a refusal mutated the claim store"


def test_the_offered_queue_loses_only_the_claimed_row(tmp_path: Path) -> None:
    """The filter is narrow. A claim removes its own row and no other.

    The failure this rules out is a filter that answers the empty queue the
    moment ANY claim exists, which would look like a working fence and would
    stop the second lane dead. Graded by set equality against the offered queue
    minus one named member - both sides non-empty, so neither leg is vacuous.
    """
    root = tmp_path / "claims"
    offered = _offered()
    taken = claims.try_claim_row(
        offered[1], lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt-a"), root=root
    )
    taken_ok = bool(taken["ok"])
    assert taken_ok, "the claim did not land"

    still_offered = set(claims.takeable_rows(offered, root=root))
    expected = set(offered) - {offered[1]}
    exactly_one_gone = still_offered == expected
    assert exactly_one_gone, f"the queue now offers {sorted(still_offered)}"

    both_legs_populated = bool(still_offered) and bool(expected)
    assert both_legs_populated, "the equality above compared two empty sets"


# ===========================================================================
# b. A dead claimant is reclaimable, not held
# ===========================================================================


def test_the_liveness_probe_can_tell_this_process_from_a_reaped_one() -> None:
    """THE CONTROL the two liveness arms are fronted by, standing on its own.

    A probe that answered False for everything would make a reclaim arm pass
    for the wrong reason; a pid the operating system had already reissued would
    make it pass for no reason. This asserts both directions on the same probe
    in the same run.
    """
    live = lanes.pid_alive(os.getpid())
    assert live is True, "the probe cannot see the process running it"

    dead = lanes.pid_alive(_reaped_pid())
    assert dead is False, "a reaped pid still reads alive - it was reissued, or the probe is blind"


def test_a_dead_claimants_row_returns_to_the_queue(tmp_path: Path) -> None:
    """ACCEPTANCE 3. A wedged claim is as bad as no claim and worse.

    It looks like progress. So the state is decided by PROBING the holder's pid,
    never by stat-ing the claim file, and a claim whose holder is provably gone
    reads RECLAIMABLE and is offered again.
    """
    root = tmp_path / "claims"
    offered = _offered()
    reaped = _reaped_pid()

    # CONTROL FIRST - the probe can observe its subject in both directions.
    can_see_itself = lanes.pid_alive(os.getpid())
    assert can_see_itself is True, "the probe cannot see the process running it"
    holder_is_gone = lanes.pid_alive(reaped)
    assert holder_is_gone is False, "the planted holder is still alive - nothing is being graded"

    _plant(root, ROW_A, pid=reaped)

    state = claims.claim_state(ROW_A, root=root)["state"]
    assert state == claims.RECLAIMABLE, f"a dead claimant reads {state!r}"

    offered_again = claims.first_takeable(offered, root=root)
    assert offered_again == ROW_A, f"the queue offered {offered_again!r} instead"

    retaken = claims.try_claim_row(
        ROW_A, lane=LANE_B, run_id="b", worktree=_worktree(tmp_path, "wt-b"), root=root
    )
    retaken_ok = bool(retaken["ok"])
    assert retaken_ok, "a reclaimable row could not be retaken"

    now_held_by = claims.claim_state(ROW_A, root=root)
    holder_pid = now_held_by["pid"]
    assert holder_pid == os.getpid(), f"the claim still names pid {holder_pid!r}"

    holder_lane = now_held_by["lane"]
    assert holder_lane == LANE_B, f"the claim names lane {holder_lane!r}"


def test_a_live_claimant_is_not_reclaimed_by_the_same_path(tmp_path: Path) -> None:
    """The specificity half. Reclaim must not be the answer to every claim.

    Without this, a store that reclaimed unconditionally would satisfy the dead
    claimant arm and destroy acceptance 1 at the same time.
    """
    root = tmp_path / "claims"
    _plant(root, ROW_A, pid=os.getpid())
    state = claims.claim_state(ROW_A, root=root)["state"]
    assert state == claims.HELD, f"a live claimant reads {state!r}"


def test_a_read_never_clears_a_reclaimable_claim(tmp_path: Path) -> None:
    """READS DO NOT WRITE - the ruling `ops/loop/lanes.py` already paid for.

    Auto-clearing a stale claim inside a read makes a rendering pass mutate the
    control plane, and two pollers then race each other into a reclaim.
    """
    root = tmp_path / "claims"
    reaped = _reaped_pid()
    gone = lanes.pid_alive(reaped)
    assert gone is False, "the planted holder is alive - the arm would grade nothing"

    _plant(root, ROW_A, pid=reaped)
    before = _snapshot(root)

    seen = claims.claim_state(ROW_A, root=root)["state"]
    assert seen == claims.RECLAIMABLE, f"the planted claim reads {seen!r}"
    claims.claim_state(ROW_A, root=root)
    claims.takeable_rows(_offered(), root=root)

    unchanged = _snapshot(root) == before
    assert unchanged, "a read mutated the claim store"


def test_a_read_of_a_missing_root_does_not_create_it(tmp_path: Path) -> None:
    """The poll path is safe against a store nobody has written to yet."""
    root = tmp_path / "claims"
    claims.claim_state(ROW_A, root=root)
    claims.takeable_rows(_offered(), root=root)
    created = root.exists()
    assert created is False, "a read created the claim root"


# ===========================================================================
# c. Release is deliberate, never a side effect of a process ending
# ===========================================================================


def test_a_deliberate_release_removes_the_claim(tmp_path: Path) -> None:
    """ACCEPTANCE 2, and the CONTROL the crash arm needs.

    Without this, "the claim survived the crash" would pass just as happily on
    a store whose release did nothing at all.
    """
    root = tmp_path / "claims"
    taken = claims.try_claim_row(
        ROW_A, lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt-a"), root=root
    )
    taken_ok = bool(taken["ok"])
    assert taken_ok, "the claim did not land"

    released = claims.release_claim(taken["token"], root=root)
    assert released is True, "the release reported nothing removed"

    after = claims.claim_state(ROW_A, root=root)["state"]
    assert after == claims.FREE, f"the row reads {after!r} after a deliberate release"

    offered_again = claims.first_takeable(_offered(), root=root)
    assert offered_again == ROW_A, f"the queue offered {offered_again!r} after the release"


def test_a_crashed_cycle_does_not_release_its_claim(tmp_path: Path) -> None:
    """ACCEPTANCE 4c. Release is DELIBERATE, not a side effect of dying.

    The child claims its row and then calls ``os._exit``, which runs no finally,
    no atexit hook and no context manager exit. What is on disk afterwards is
    therefore what a genuinely killed cycle leaves, and the claim must still be
    there - naming the dead holder, reading RECLAIMABLE rather than FREE, and
    unchanged by having been read.

    The row is RECLAIMABLE and so a later fire can take it. That is a different
    event from a release, and the difference is the point: a release says the
    holder finished, a reclaim says nobody can prove it did.
    """
    root = tmp_path / "claims"
    claimed, child_pid = _crash_after_claiming(tmp_path, ROW_A, root)
    assert claimed, "the child never took the claim, so its survival proves nothing"

    child_is_gone = lanes.pid_alive(child_pid)
    assert child_is_gone is False, "the crashed child is still running"

    survived = (root / f"{ROW_A}{claims.CLAIM_SUFFIX}").exists()
    assert survived, "the claim was released by a process merely ending"

    recorded = _rows_on_disk(root)
    still_recorded = recorded == {ROW_A}
    assert still_recorded, f"the claim directory records {sorted(recorded)}"

    state = claims.claim_state(ROW_A, root=root)
    reads_as = state["state"]
    assert reads_as == claims.RECLAIMABLE, f"the crashed claim reads {reads_as!r}"

    names = state["pid"]
    assert names == child_pid, f"the claim names pid {names!r}, not the child"

    intact = (root / f"{ROW_A}{claims.CLAIM_SUFFIX}").exists()
    assert intact, "reading the crashed claim removed it"


# ===========================================================================
# d. The key is what the row IS, never where it sits
# ===========================================================================


def test_a_claim_is_resolved_by_the_row_it_records_not_by_its_file_name(
    tmp_path: Path,
) -> None:
    """The non-positional half, graded structurally rather than by inspection.

    A claim keyed by the row's POSITION in the queue would re-point every claim
    the moment a row above it closed, and a live holder would then read FREE -
    the defect `ops/loop/lanes.py` measured on its own slot index. So the
    RECORDED row is authoritative and the derived file name is merely where a
    NEW claim is written. This arm moves a claim to a file name that derives
    from nothing and asserts the row is still held.
    """
    root = tmp_path / "claims"
    planted = _plant(root, ROW_A, pid=os.getpid())
    moved = root / f"stranger{claims.CLAIM_SUFFIX}"
    planted.replace(moved)

    derived_is_absent = not (root / f"{ROW_A}{claims.CLAIM_SUFFIX}").exists()
    assert derived_is_absent, "the arm did not actually move the claim"

    state = claims.claim_state(ROW_A, root=root)["state"]
    assert state == claims.HELD, f"a relocated live claim reads {state!r}"

    offered = set(claims.takeable_rows(_offered(), root=root))
    expected = set(_offered()) - {ROW_A}
    hidden_holder_would_widen_this = offered == expected
    assert hidden_holder_would_widen_this, f"the queue offers {sorted(offered)}"


def test_the_claim_store_reports_every_row_it_holds(tmp_path: Path) -> None:
    """Set equality between the store's enumeration and a walk of the directory.

    Two enumerations, no shared constant: one is what ``claim_states`` derives,
    the other reads the files. A store that forgot a claim, or invented one,
    separates them.
    """
    root = tmp_path / "claims"
    for row in (ROW_A, ROW_B, ROW_C):
        _plant(root, row, pid=os.getpid())

    reported = set(claims.claim_states(root=root))
    walked = _rows_on_disk(root)
    agree = reported == walked
    assert agree, f"the store reports {sorted(reported)} over {sorted(walked)}"

    neither_is_empty = bool(reported) and bool(walked)
    assert neither_is_empty, "the equality above compared two empty sets"


def test_a_row_the_store_cannot_spell_is_refused_rather_than_defaulted(
    tmp_path: Path,
) -> None:
    """A row id is a file name here, so an unspellable one is a hard error.

    Answering some default row would hand a caller a claim on a row it did not
    name, which is how a typo takes a running lane's work. The path separator is
    the case that matters - a row id carrying one would write outside the claim
    root.
    """
    root = tmp_path / "claims"
    for bad in ("", "   ", "../escape", "with/sep", "with\\sep"):
        with pytest.raises(ValueError, match="row"):
            claims.try_claim_row(
                bad, lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt"), root=root
            )
    nothing_written = _snapshot(root) == {}
    assert nothing_written, "a refused row id still wrote to the claim store"


def test_a_lane_off_the_roster_cannot_claim(tmp_path: Path) -> None:
    """The roster check is the lane lock's, not a second copy of it.

    A lane that cannot be placed on the roster has no slot and no business
    holding a row either. Reusing ``lanes.slot_index`` here is what keeps the
    two answers from drifting apart.
    """
    root = tmp_path / "claims"
    with pytest.raises(ValueError, match="unknown lane"):
        claims.try_claim_row(
            ROW_A,
            lane="not-a-lane",
            run_id="a",
            worktree=_worktree(tmp_path, "wt"),
            root=root,
        )
    nothing_written = _snapshot(root) == {}
    assert nothing_written, "an unknown lane still wrote to the claim store"


def test_a_claim_may_not_be_taken_against_the_main_tree(tmp_path: Path) -> None:
    """The worktree rule reaches the claim path too, through the same guard.

    A lane rewrites files while it works. Pointed at the checkout the operator
    is reading, two writers land in one working directory, which is the
    concurrent-index corruption class.
    """
    root = tmp_path / "claims"
    with pytest.raises(ValueError, match="worktree"):
        claims.try_claim_row(ROW_A, lane=LANE_A, run_id="a", worktree=lanes.REPO_ROOT, root=root)
    nothing_written = _snapshot(root) == {}
    assert nothing_written, "a refused worktree still wrote to the claim store"


def test_a_late_release_cannot_unlink_the_next_holders_claim(tmp_path: Path) -> None:
    """The ABA guard, carried over from the lane lock rather than reinvented.

    A release arriving after the row was reclaimed and retaken must remove
    nothing: the claim on disk has moved on, and unlinking it would hand the row
    to a third lane while the second is working it.
    """
    root = tmp_path / "claims"
    first = claims.try_claim_row(
        ROW_A, lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt-a"), root=root
    )
    first_ok = bool(first["ok"])
    assert first_ok, "the first claim did not land"

    # The row is reclaimed and retaken by somebody else, out from under the
    # token the first lane is still holding.
    _plant(root, ROW_A, pid=os.getpid(), run_id="somebody-else", lane=LANE_B, ts=2.0)

    released = claims.release_claim(first["token"], root=root)
    assert released is False, "a late release removed a claim that was not ours"

    survivor = claims.claim_state(ROW_A, root=root)
    holder = survivor["run_id"]
    assert holder == "somebody-else", f"the surviving claim names {holder!r}"


def test_releasing_a_row_that_is_not_claimed_reports_nothing_removed(tmp_path: Path) -> None:
    """Release is idempotent and never raises - it runs in a finally."""
    root = tmp_path / "claims"
    answer = claims.release_claim(str(root / f"{ROW_A}{claims.CLAIM_SUFFIX}"), root=root)
    assert answer is False, "a release reported removing a claim that was never taken"
