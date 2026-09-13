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

import contextlib
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
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


def _plant(root: Path, row: str, file_name: str | None = None, **overrides: Any) -> Path:
    """Write a claim record by hand, bypassing the acquire path.

    Used where an arm needs a holder this process could not legitimately become
    - a dead pid, for instance. ``file_name`` names the FILE rather than the row,
    so an arm can put two records for one row under names that sort either way
    round.
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
    target = root / f"{row if file_name is None else file_name}{claims.CLAIM_SUFFIX}"
    target.write_text(json.dumps(record), encoding="utf-8")
    return target


def _state_of_row_a(root: Path) -> str:
    """The per-row read for ``ROW_A``, which is the half a scan can disagree with."""
    return str(claims.claim_state(ROW_A, root=root)["state"])


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
    child.wait(timeout=_CHILD_TIMEOUT_S)
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
        timeout=_CHILD_TIMEOUT_S,
    )
    exited_as_told = done.returncode == CRASH_CODE
    assert exited_as_told, f"the child did not reach its crash - stderr was {done.stderr!r}"
    reported, _, spelled = done.stdout.partition("|")
    return reported == "True", int(spelled)


# ---------------------------------------------------------------------------
# Synthetic checkouts - the only way to grade the DEFAULT root
# ---------------------------------------------------------------------------

#: The package files a synthetic checkout needs to import the claim store.
_COPIED_MODULES: Final = (
    "ops/__init__.py",
    "ops/loop/__init__.py",
    "ops/loop/lanes.py",
    "ops/loop/claims.py",
)


def _checkout(tmp_path: Path, name: str, main: Path | None) -> Path:
    """Build a checkout that carries its own copy of the claim store.

    ``main`` None makes a MAIN tree - ``.git`` is a directory, the way git lays
    one out. Otherwise it makes a LINKED WORKTREE of that main tree: ``.git`` is
    a FILE holding a ``gitdir:`` pointer, which is the indirection
    ``lanes.REPO_ROOT`` exists to resolve.

    THE COPY IS THE POINT. A lane's worker runs inside its own checkout and
    imports that checkout's copy of the module, so a store rooted at ``__file__``
    lands somewhere different in every lane. Only separate copies on disk can
    show that.
    """
    tree = tmp_path / name
    for relative in _COPIED_MODULES:
        destination = tree / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    if main is None:
        (tree / ".git").mkdir(parents=True, exist_ok=True)
    else:
        pointer = main / ".git" / "worktrees" / name
        pointer.mkdir(parents=True, exist_ok=True)
        (tree / ".git").write_text(f"gitdir: {pointer}", encoding="utf-8")
    return tree


#: Printed by a child in a synthetic checkout: the store root it would use, and
#: - as the CONTROL - the root the defective ``__file__`` derivation gives. The
#: control is what proves the probe can see a difference between two checkouts
#: at all; without it, equal store roots would also be what a probe that printed
#: a constant produced.
_ROOT_PROBE: Final = """
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

from ops.loop import claims

here_derived = Path(claims.__file__).resolve().parent / "control" / "claims"
sys.stdout.write("{0}\\n{1}".format(claims.DEFAULT_ROOT, here_derived))
"""


def _probe_roots(checkout: Path) -> tuple[str, str]:
    """The store root and the ``__file__``-derived control, as that checkout sees them.

    Returns:
        The default claim root, and the root a ``__file__`` derivation gives.
    """
    script = checkout / "root_probe.py"
    script.write_text(_ROOT_PROBE, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(script), str(checkout)],
        cwd=str(checkout),
        capture_output=True,
        check=False,
        text=True,
        timeout=_CHILD_TIMEOUT_S,
    )
    ran = done.returncode == 0
    assert ran, f"the root probe did not run - stderr was {done.stderr!r}"
    store, _, here = done.stdout.partition("\n")
    return store.strip(), here.strip()


#: Claims a row from inside one checkout and then BLOCKS on stdin, so the
#: claimant is still ALIVE while a second process tries the same row. A claimant
#: that exited would be reclaimed on its own merits and the arm would grade the
#: reclaim path instead of exclusion.
#:
#: NO root= ARGUMENT ANYWHERE BELOW. That omission is the whole point: passing a
#: shared root would hand the store the answer it is being graded on.
_HOLDING_CLAIMANT: Final = """
import sys

sys.path.insert(0, sys.argv[1])

from ops.loop import claims

answer = claims.try_claim_row(
    sys.argv[2],
    lane=sys.argv[3],
    run_id=sys.argv[4],
    worktree=sys.argv[1],
)
sys.stdout.write(str(answer.get("ok")) + "\\n")
sys.stdout.flush()
sys.stdin.readline()
"""

_PASSING_CLAIMANT: Final = """
import sys

sys.path.insert(0, sys.argv[1])

from ops.loop import claims

answer = claims.try_claim_row(
    sys.argv[2],
    lane=sys.argv[3],
    run_id=sys.argv[4],
    worktree=sys.argv[1],
)
sys.stdout.write(str(answer.get("ok")))
"""

#: Seconds a child gets. Generous - it starts an interpreter and imports two
#: modules - and present only so a wedged arm fails rather than hanging the run.
_CHILD_TIMEOUT_S: Final = 60.0


@contextmanager
def _holding_claim(checkout: Path, row: str, lane: str, run_id: str) -> Iterator[bool]:
    """Claim a row from one checkout and KEEP the claimant alive inside the block.

    Yields:
        Whether the claim was taken.
    """
    script = checkout / "holding_claimant.py"
    script.write_text(_HOLDING_CLAIMANT, encoding="utf-8")
    child = subprocess.Popen(
        [sys.executable, str(script), str(checkout), row, lane, run_id],
        cwd=str(checkout),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        yield child.stdout.readline().strip() == "True"
    finally:
        with contextlib.suppress(OSError, ValueError):
            assert child.stdin is not None
            child.stdin.close()
        with contextlib.suppress(subprocess.TimeoutExpired):
            child.wait(timeout=_CHILD_TIMEOUT_S)
        if child.poll() is None:
            child.kill()
            child.wait()


def _claim_from_checkout(checkout: Path, row: str, lane: str, run_id: str) -> bool:
    """Claim a row from inside one checkout and let the claimant exit."""
    script = checkout / "passing_claimant.py"
    script.write_text(_PASSING_CLAIMANT, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(script), str(checkout), row, lane, run_id],
        cwd=str(checkout),
        capture_output=True,
        check=False,
        text=True,
        timeout=_CHILD_TIMEOUT_S,
    )
    ran = done.returncode == 0
    assert ran, f"the claimant did not run - stderr was {done.stderr!r}"
    return done.stdout.strip() == "True"


# ===========================================================================
# e. The DEFAULT root, which every arm above assumes away
# ===========================================================================


def test_two_checkouts_resolve_the_default_store_to_one_directory(tmp_path: Path) -> None:
    """THE ACCEPTANCE FOR THE ROOTING, and the arm this file was missing.

    Every other arm here passes an explicit shared ``root=``, so none of them
    can see a defect that IS the root. A lane's worker runs inside its own
    checkout and imports that checkout's copy of the store, so a root derived
    from ``__file__`` puts each lane in a private directory and nothing is ever
    excluded - measured across two real processes both holding one row.

    THE CONTROL IS THE OTHER HALF. The same probe also reports what the
    ``__file__`` derivation gives, and those MUST DIFFER between the two
    checkouts. Without that leg, two equal store roots would be exactly what a
    probe reading one checkout twice would print.
    """
    main = _checkout(tmp_path, "main", None)
    lane_a = _checkout(tmp_path, "lane-a", main)
    lane_b = _checkout(tmp_path, "lane-b", main)

    store_a, here_a = _probe_roots(lane_a)
    store_b, here_b = _probe_roots(lane_b)
    store_main, _here_main = _probe_roots(main)

    # CONTROL FIRST - the two checkouts really are distinct on disk, and the
    # defective derivation can be seen to separate them.
    control_separates = here_a != here_b
    assert control_separates, "the probe cannot tell the two checkouts apart"

    lanes_agree = store_a == store_b
    assert lanes_agree, "the two lanes root their claim stores in different directories"

    main_agrees = store_a == store_main
    assert main_agrees, "the lanes and the main checkout do not share one store"

    not_per_checkout = store_a != here_a
    assert not_per_checkout, "the store root is still derived from the module's own file"


def test_two_concurrent_checkouts_cannot_both_claim_one_row(tmp_path: Path) -> None:
    """The adversary's counter-example, kept as a regression arm.

    Two processes, two checkouts, one row, and NEITHER is told where the store
    is - each resolves the default. The first claimant is STILL RUNNING while the
    second tries, which is what makes this exclusion rather than a reclaim: a
    claimant that had exited would be reclaimed on its own merits and the second
    lane would rightly get the row.

    TWO CONTROLS, because "the second was refused" is also what a store that
    refused everything would produce, and "the first won" is also what a store
    that granted everything would produce:

      * the first claimant must have SUCCEEDED, so something is being excluded;
      * a DISTINCT row must be granted to the second lane while the first claim
        is still held, so the refusal is about the row and not about the lane.
    """
    main = _checkout(tmp_path, "main", None)
    lane_a = _checkout(tmp_path, "lane-a", main)
    lane_b = _checkout(tmp_path, "lane-b", main)

    with _holding_claim(lane_a, ROW_A, LANE_A, "a") as first:
        assert first, "the first checkout could not claim at all - nothing is being graded"

        second = _claim_from_checkout(lane_b, ROW_A, LANE_B, "b")
        assert second is False, "two checkouts both hold one row"

        # CONTROL - the store is not simply refusing the second lane everything.
        other_row = _claim_from_checkout(lane_b, ROW_B, LANE_B, "b2")
        assert other_row, "a distinct row was refused too, so the refusal above proves nothing"


# ===========================================================================
# f. One fact, one resolution rule
# ===========================================================================


def test_a_live_holder_decides_the_row_whatever_the_file_names_sort_to(
    tmp_path: Path,
) -> None:
    """TWO RULES FOR ONE FACT IS A DISAGREEMENT WAITING FOR AN OCCASION.

    The shape this grades once resolved a single row by the derived path and the
    whole store by a scan where the last file name won. With two records naming
    one row they DISAGREED: the per-row read answered held while the scan
    answered reclaimable, and the queue offered a row that a live process was
    working.

    BOTH ORDERINGS ARE DRIVEN. The live record sits before the dead one in one
    leg and after it in the other, so neither "derived path first" nor "last
    name wins" can pass this by luck.
    """
    reaped = _reaped_pid()
    gone = lanes.pid_alive(reaped)
    assert gone is False, "the planted dead holder is alive - the arm grades nothing"

    for tag, live_name, dead_name in (
        ("live-sorts-first", f"aaa-{ROW_A}", f"zzz-{ROW_A}"),
        ("live-sorts-last", f"zzz-{ROW_A}", f"aaa-{ROW_A}"),
    ):
        root = tmp_path / f"claims-{tag}"
        _plant(root, ROW_A, pid=os.getpid(), file_name=live_name)
        _plant(root, ROW_A, pid=reaped, file_name=dead_name)

        single = _state_of_row_a(root)
        agrees_with_the_scan = single == claims.claim_states(root=root)[ROW_A]["state"]
        assert agrees_with_the_scan, f"{tag}: the per-row and whole-store reads disagree"

        assert single == claims.HELD, f"{tag}: a live holder reads {single!r}"

        offered = claims.first_takeable(_offered(), root=root)
        assert offered == ROW_B, f"{tag}: the queue offered {offered!r} over a live holder"


def test_a_row_whose_records_are_all_stale_is_offered(tmp_path: Path) -> None:
    """The control for the arm above, and the non-vacuity leg it needs.

    "The row was not offered" would also be what a store that offered nothing
    produced. With every record for the row stale, the row must come back.
    """
    reaped = _reaped_pid()
    gone = lanes.pid_alive(reaped)
    assert gone is False, "the planted dead holder is alive - the arm grades nothing"

    root = tmp_path / "claims"
    _plant(root, ROW_A, pid=reaped, file_name=f"aaa-{ROW_A}")
    _plant(root, ROW_A, pid=reaped, file_name=f"zzz-{ROW_A}")

    single = _state_of_row_a(root)
    assert single == claims.RECLAIMABLE, f"an all-stale row reads {single!r}"

    offered = claims.first_takeable(_offered(), root=root)
    assert offered == ROW_A, f"the queue offered {offered!r} instead of the stale row"


def test_claiming_a_row_clears_every_stale_record_naming_it(tmp_path: Path) -> None:
    """A duplicate left behind can win a later grading and report a dead holder.

    So a claim clears ALL of them, and the store is left holding exactly one
    record for the row - graded by set equality against a walk of the directory.
    """
    reaped = _reaped_pid()
    gone = lanes.pid_alive(reaped)
    assert gone is False, "the planted dead holder is alive - the arm grades nothing"

    root = tmp_path / "claims"
    _plant(root, ROW_A, pid=reaped, file_name=f"aaa-{ROW_A}")
    _plant(root, ROW_A, pid=reaped, file_name=f"zzz-{ROW_A}")
    before = set(_snapshot(root))
    planted_names = {f"aaa-{ROW_A}{claims.CLAIM_SUFFIX}", f"zzz-{ROW_A}{claims.CLAIM_SUFFIX}"}
    two_planted = before == planted_names
    assert two_planted, f"the arm planted {sorted(before)}"

    taken = claims.try_claim_row(
        ROW_A, lane=LANE_A, run_id="a", worktree=_worktree(tmp_path, "wt"), root=root
    )
    taken_ok = bool(taken["ok"])
    assert taken_ok, "the claim over stale duplicates was refused"

    after = set(_snapshot(root))
    only_the_new_one = after == {f"{ROW_A}{claims.CLAIM_SUFFIX}"}
    assert only_the_new_one, f"the store now holds {sorted(after)}"


# ===========================================================================
# g. The reclaim removes the record it GRADED, and nothing else
# ===========================================================================


def test_a_reclaim_refuses_when_the_record_changed_under_it(tmp_path: Path) -> None:
    """The time-of-check race, driven by hand at the seam where it happens.

    The old shape re-read the state and then unlinked the path. Between those
    two steps another process could reclaim the record and write its own LIVE
    claim there, whereupon the unlink deleted a live record and the create that
    followed double-booked the row. This drives exactly that interleaving: a
    record is graded reclaimable, then REPLACED by a live one before the reclaim
    acts.
    """
    reaped = _reaped_pid()
    gone = lanes.pid_alive(reaped)
    assert gone is False, "the planted dead holder is alive - the arm grades nothing"

    root = tmp_path / "claims"
    _plant(root, ROW_A, pid=reaped)
    graded = claims._candidates(root, None)[ROW_A][0]  # noqa: SLF001 - the seam under test
    was_reclaimable = graded[3] == claims.RECLAIMABLE
    assert was_reclaimable, f"the planted record graded {graded[3]!r}"

    # CONTROL - acting on the record AS GRADED does remove it.
    control_root = tmp_path / "claims-control"
    _plant(control_root, ROW_A, pid=reaped)
    control = claims._candidates(control_root, None)[ROW_A][0]  # noqa: SLF001 - the seam
    control_removed = claims._reclaim(control)  # noqa: SLF001 - the seam under test
    assert control_removed is True, "a reclaim of the graded record removed nothing"

    # Now the race: a live claimant replaces the record between grade and act.
    _plant(root, ROW_A, pid=os.getpid(), run_id="the-live-one")
    acted = claims._reclaim(graded)  # noqa: SLF001 - the seam under test
    assert acted is False, "the reclaim carried off a record it had not graded"

    survivor = claims.claim_state(ROW_A, root=root)
    holder = survivor["run_id"]
    assert holder == "the-live-one", f"the surviving record names {holder!r}"

    still_held = survivor["state"]
    assert still_held == claims.HELD, f"the live record now reads {still_held!r}"


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


# ===========================================================================
# f. CS-1009 - the claim outlives the process that made it, not the cycle
# ===========================================================================
#
# WHY THIS SECTION EXISTS. Every arm above claims a row from a process that
# stays alive for the length of the arm, so every one of them is satisfied by
# the pid anchor. An LLM worker does not run that way: it reaches python through
# a FRESH SUBPROCESS PER CALL, so the process that writes the claim has exited
# microseconds later while its CYCLE runs for thousands of seconds. Under the
# pid anchor the record read RECLAIMABLE for that whole span and a second lane
# reclaimed a row somebody was working, which is the double-booking CS-991 was
# filed to stop, restored by the calling convention rather than by the code.
#
# THE ANCHOR THESE ARMS GRADE IS THE LANE LOCK. A cycle's lane lock is held by
# the spawned WORKER - ``ops/loop/lane_launcher.py`` re-points it through
# ``lanes.repoint_lane_pid`` the moment it has a worker pid - and that process
# lives the whole cycle. So the arms below drive a REAL lane lock behind a REAL
# live foreign process rather than patching a probe, for the reason the module
# docstring already gives about ``pid_alive``.


def _lock_root_beside(root: Path) -> Path:
    """Where the lane locks sit for a claim store rooted at ``root``.

    SPELLED FROM ``lanes.DEFAULT_ROOT`` RATHER THAN AS A LITERAL, so a rename of
    the lane lock directory moves the arms with it instead of leaving them
    writing locks nothing reads. What these arms grade is the DELEGATION, not
    the location: the location has its own arm, which compares the production
    answer against the main tree.
    """
    return root.parent / lanes.DEFAULT_ROOT.name


#: Claims a row and then EXITS NORMALLY, which is how a per-call worker
#: subprocess ends. Not ``os._exit``: the crash arm above already grades a death
#: past cleanup, and a normal exit is the case CS-1009 is about.
_EXITING_CLAIMANT: Final = """
import os
import sys

sys.path.insert(0, sys.argv[1])

from ops.loop import claims

answer = claims.try_claim_row(
    sys.argv[2],
    lane=sys.argv[3],
    run_id=sys.argv[4],
    worktree=sys.argv[5],
    root=sys.argv[6],
)
sys.stdout.write("{0}|{1}|{2}".format(answer.get("ok"), os.getpid(), answer.get("token")))
"""

#: Releases a claim by token from a DIFFERENT process than the one that took it,
#: which is the second facet CS-1009 names: ``_OWNED`` is process-local, so a
#: later per-call subprocess of one cycle cannot release what an earlier one
#: took. The run id is the identity it offers in place of the lost table entry.
_RELEASING_SUBPROCESS: Final = """
import sys

sys.path.insert(0, sys.argv[1])

from ops.loop import claims

offered = sys.argv[4]
answer = claims.release_claim(
    sys.argv[2],
    root=sys.argv[3],
    run_id=None if offered == "-" else offered,
)
sys.stdout.write(str(answer))
"""


def _claim_and_exit(
    tmp_path: Path, row: str, lane: str, run_id: str, root: Path
) -> tuple[int, str]:
    """Claim ``row`` in a child that then exits normally. Returns its pid and token."""
    script = tmp_path / "cs1009_exiting_claimant.py"
    script.write_text(_EXITING_CLAIMANT, encoding="utf-8")
    done = subprocess.run(
        [
            sys.executable,
            str(script),
            str(ROOT),
            row,
            lane,
            run_id,
            str(_worktree(tmp_path, "cs1009-claimtree")),
            str(root),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=_CHILD_TIMEOUT_S,
    )
    ran = done.returncode == 0
    assert ran, f"the claimant did not run - stderr was {done.stderr!r}"
    reported, _, rest = done.stdout.partition("|")
    took_it = reported == "True"
    assert took_it, f"the claimant did not take the row - stdout was {done.stdout!r}"
    spelled, _, token = rest.partition("|")
    return int(spelled), token


def _release_from_a_second_process(tmp_path: Path, token: str, root: Path, run_id: str) -> str:
    """Call ``release_claim`` from a process that never held the claim."""
    script = tmp_path / "cs1009_releasing_subprocess.py"
    script.write_text(_RELEASING_SUBPROCESS, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(script), str(ROOT), token, str(root), run_id],
        capture_output=True,
        check=False,
        text=True,
        timeout=_CHILD_TIMEOUT_S,
    )
    ran = done.returncode == 0
    assert ran, f"the releasing process did not run - stderr was {done.stderr!r}"
    return done.stdout.strip()


@contextmanager
def _cycle_on_lane(
    lock_root: Path, lane: str, run_id: str, worktree: Path, pid: Any = None
) -> Iterator[int]:
    """A lane lock RUNNING behind a real process, exactly as a launch leaves it.

    Acquired through ``lanes.try_acquire_lane`` and re-pointed through
    ``lanes.repoint_lane_pid`` - the same two calls ``ops/loop/lane_launcher.py``
    makes - so what the arm drives is the production shape rather than a
    hand-written lock file. ``pid`` names the process the lock ends up pointing
    at; None means a long-lived child this helper starts and reaps.

    Yields:
        The pid the lock names.
    """
    child = None
    if pid is None:
        child = subprocess.Popen(
            [sys.executable, "-c", "import sys; sys.stdin.readline()"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pid = child.pid
    token = None
    try:
        got = lanes.try_acquire_lane(
            lane, run_id=run_id, worktree=str(worktree), root=str(lock_root)
        )
        acquired = bool(got["ok"])
        assert acquired, f"the arm could not acquire lane {lane!r}"
        token = got["token"]
        pointed = lanes.repoint_lane_pid(token, pid, root=str(lock_root))
        assert pointed, "the arm could not re-point the lane lock at its worker"
        yield int(pid)
    finally:
        if token is not None:
            lanes.release_lane(token, root=str(lock_root))
        if child is not None:
            with contextlib.suppress(OSError, ValueError):
                assert child.stdin is not None
                child.stdin.close()
            with contextlib.suppress(subprocess.TimeoutExpired):
                child.wait(timeout=_CHILD_TIMEOUT_S)
            if child.poll() is None:
                child.kill()
                child.wait()


def test_the_arms_can_tell_a_live_cycle_from_the_exited_process_that_claimed_it(
    tmp_path: Path,
) -> None:
    """THE CONTROL. Without it, the arms below could pass by grading nothing.

    A probe that answered False for everything would make the reclaim arms pass
    for the wrong reason, and a probe that answered True for everything would
    make the exclusion arms pass for no reason at all. So this fronts the
    section by asserting the two readings the arms depend on, at the moment they
    depend on them: the process that claimed the row is GONE, and the process
    the cycle's lane lock names is ALIVE.
    """
    root = tmp_path / "control" / "claims"
    lock_root = _lock_root_beside(root)
    with _cycle_on_lane(lock_root, LANE_A, "cycle-control", _worktree(tmp_path, "wt-cycle")) as pid:
        claimant, _token = _claim_and_exit(tmp_path, ROW_A, LANE_A, "worker-call", root)
        claimant_is_gone = not lanes.pid_alive(claimant)
        assert claimant_is_gone, "the claiming process outlived its own exit"
        cycle_is_running = lanes.pid_alive(pid)
        assert cycle_is_running, "the cycle's process died before the arm could read it"
        lock_says = str(lanes.lane_state(str(lock_root), None, LANE_A)["state"])
        assert lock_says == lanes.RUNNING, f"the lane lock reads {lock_says}"


def test_a_claim_outlives_the_process_that_made_it_while_its_cycle_runs(
    tmp_path: Path,
) -> None:
    """THE SUBJECT OF CS-1009, driven through a real process exit.

    The claiming process is a child that takes the row and then returns - a per
    call worker subprocess, which is how an LLM worker reaches python. Its pid is
    dead before the assertions run, and the control above establishes that at
    the moment it matters. What is still alive is the CYCLE, named by the lane
    lock its claim recorded.

    The edit that reddens this: deleting the lane-lock branch from
    ``claims._state_of`` puts the store back on the pid anchor and the second
    lane takes the row.
    """
    root = tmp_path / "control" / "claims"
    lock_root = _lock_root_beside(root)
    with _cycle_on_lane(lock_root, LANE_A, "cycle-alpha", _worktree(tmp_path, "wt-cycle")):
        _claimant, _token = _claim_and_exit(tmp_path, ROW_A, LANE_A, "worker-call", root)

        state = str(claims.claim_state(ROW_A, root=root)["state"])
        assert state == claims.HELD, f"a claim whose cycle is running reads {state}"

        offered = claims.first_takeable(_offered(), root=root)
        assert offered == ROW_B, f"the queue still offered {offered!r}"

        second = claims.try_claim_row(
            ROW_A, lane=LANE_B, run_id="lane-b", worktree=_worktree(tmp_path, "wt-b"), root=root
        )
        double_booked = bool(second["ok"])
        assert not double_booked, "a second lane took a row whose cycle is still running"
        refusal = str(second["refused"])
        assert refusal == "row_claimed", f"the second lane was refused with {refusal!r}"


def test_a_genuinely_dead_cycle_returns_its_row(tmp_path: Path) -> None:
    """The other half of the acceptance, and it must beat a LIVE claimant pid.

    The record here names THIS process, which is alive, so the pid anchor alone
    would report the row held forever. What decides it is the cycle: the lane
    lock is present but names a reaped pid, so the cycle is provably over and the
    row goes back on the queue.

    The edit that reddens this: making the lane-lock branch answer HELD whenever
    a lock file EXISTS, rather than when ``lanes.lane_state`` reports RUNNING.
    """
    root = tmp_path / "control" / "claims"
    lock_root = _lock_root_beside(root)
    dead = _reaped_pid()
    claimant_is_alive = lanes.pid_alive(os.getpid())
    assert claimant_is_alive, "the control process cannot see itself"
    cycle_is_dead = not lanes.pid_alive(dead)
    assert cycle_is_dead, "the reaped pid was reissued before the arm could read it"

    with _cycle_on_lane(lock_root, LANE_A, "cycle-dead", _worktree(tmp_path, "wt-cycle"), pid=dead):
        _plant(root, ROW_A, pid=os.getpid(), lane=LANE_A, lane_run_id="cycle-dead")
        state = str(claims.claim_state(ROW_A, root=root)["state"])
        assert state == claims.RECLAIMABLE, f"a dead cycle's row reads {state}"

        offered = claims.first_takeable(_offered(), root=root)
        assert offered == ROW_A, f"the queue withheld the row and offered {offered!r}"

        retaken = claims.try_claim_row(
            ROW_A, lane=LANE_B, run_id="lane-b", worktree=_worktree(tmp_path, "wt-b"), root=root
        )
        took_it = bool(retaken["ok"])
        assert took_it, f"a dead cycle wedged its row - {retaken.get('refused')!r}"


def test_a_later_cycle_on_the_same_lane_does_not_inherit_the_earlier_claim(
    tmp_path: Path,
) -> None:
    """A lane is reused; a cycle is not. The match is on the LOCK'S RUN ID.

    Without the run id the anchor would be the lane, and a lane is occupied
    again within seconds of a cycle ending - so every abandoned record would
    read held for as long as the loop kept firing. The record here names a live
    pid as well, so the pid anchor cannot be what answers.

    The edit that reddens this: dropping the run-id comparison and answering HELD
    on RUNNING alone.
    """
    root = tmp_path / "control" / "claims"
    lock_root = _lock_root_beside(root)
    with _cycle_on_lane(lock_root, LANE_A, "cycle-two", _worktree(tmp_path, "wt-cycle")) as pid:
        running = lanes.pid_alive(pid)
        assert running, "the later cycle's process died before the arm could read it"
        _plant(root, ROW_A, pid=os.getpid(), lane=LANE_A, lane_run_id="cycle-one")

        state = str(claims.claim_state(ROW_A, root=root)["state"])
        assert state == claims.RECLAIMABLE, f"an earlier cycle's record reads {state}"

        retaken = claims.try_claim_row(
            ROW_A, lane=LANE_B, run_id="lane-b", worktree=_worktree(tmp_path, "wt-b"), root=root
        )
        took_it = bool(retaken["ok"])
        assert took_it, f"a finished cycle kept its row - {retaken.get('refused')!r}"


def test_a_live_cycle_holds_its_row_however_old_the_record_is(tmp_path: Path) -> None:
    """NO FLOOR OVER A CLAIM'S AGE ANYWHERE ON THIS PATH - the CS-988 shape.

    The record is stamped at the epoch and read against a clock reading decades
    later, and its own pid is dead, so age and pid both say abandon it. The cycle
    says otherwise and the cycle decides.

    The edit that reddens this: inserting any ``age_s > <number>`` test into
    ``claims._state_of`` ahead of the lane-lock branch. That is the whole point
    of the arm - an age floor is the fix this item forbids by name, and this is
    what makes adding one visible.
    """
    root = tmp_path / "control" / "claims"
    lock_root = _lock_root_beside(root)
    dead = _reaped_pid()
    long_after = 2_000_000_000.0
    with _cycle_on_lane(lock_root, LANE_A, "cycle-old", _worktree(tmp_path, "wt-cycle")):
        _plant(root, ROW_A, pid=dead, lane=LANE_A, lane_run_id="cycle-old", ts=0.0)
        reading = claims.claim_state(ROW_A, root=root, now=long_after)
        age = reading["age_s"]
        ancient = age is not None and float(age) > long_after / 2
        assert ancient, f"the arm did not age the record - it reads {age!r} seconds old"
        state = str(reading["state"])
        assert state == claims.HELD, f"an aged record under a live cycle reads {state}"


def test_a_claim_made_with_no_lane_lock_falls_back_to_the_pid_and_says_so(
    tmp_path: Path,
) -> None:
    """THE STATED LIMIT, made observable rather than left in prose.

    A hand-run worker, a test or an operator at a REPL holds no lane lock, and a
    claim that read dead the instant it was made would be a new defect. So the
    store falls back to the pid anchor there, and the record SAYS which anchor it
    is on, so a reader can tell a cycle-anchored claim from a process-anchored
    one without inferring it.

    This arm is the second control the section needs: it holds under the pid
    anchor and under the lane-lock anchor alike, so a change that broke every
    reading would not be able to hide behind the arms above.
    """
    root = tmp_path / "control" / "claims"
    held = claims.try_claim_row(
        ROW_A, lane=LANE_A, run_id="by-hand", worktree=_worktree(tmp_path, "wt-a"), root=root
    )
    took_it = bool(held["ok"])
    assert took_it, "a claim with no lane lock was refused"

    reading = claims.claim_state(ROW_A, root=root)
    anchor = str(reading["anchor"])
    assert anchor == claims.ANCHOR_PID, f"a claim with no lane lock is anchored on {anchor!r}"
    state = str(reading["state"])
    assert state == claims.HELD, f"a claim held by this live process reads {state}"

    claimant, _token = _claim_and_exit(tmp_path, ROW_B, LANE_A, "by-hand", root)
    gone = not lanes.pid_alive(claimant)
    assert gone, "the claiming process outlived its own exit"
    orphan = str(claims.claim_state(ROW_B, root=root)["state"])
    assert orphan == claims.RECLAIMABLE, f"an unanchored claim by a dead process reads {orphan}"


def test_the_lane_lock_root_the_store_anchors_to_is_the_main_trees(tmp_path: Path) -> None:
    """The production wiring, which every arm above assumes away by passing a root.

    A lane's worker runs inside its own checkout, so ``lanes.DEFAULT_ROOT`` -
    rooted at the importing file - names a directory in the WORKTREE that holds
    no lock at all. Anchored there, every claim would fall back to the pid and
    CS-1009 would be undisclosed rather than fixed. The production answer must be
    the MAIN tree's lane lock root, and a root a caller names must sit beside the
    claim root it named.

    The edit that reddens this: anchoring on ``lanes.DEFAULT_ROOT`` itself, which
    resolves inside whichever checkout imported the module.
    """
    resolved = claims.lock_root()
    under_the_repo = str(resolved).startswith(str(lanes.REPO_ROOT))
    assert under_the_repo, "the default lane lock root is outside the main checkout"
    tail = resolved.name
    assert tail == lanes.DEFAULT_ROOT.name, f"the default lane lock root ends in {tail!r}"
    shape = resolved.relative_to(lanes.REPO_ROOT).as_posix()
    expected = lanes.DEFAULT_ROOT.relative_to(lanes.DEFAULT_ROOT.parents[3]).as_posix()
    assert shape == expected, f"the default lane lock root sits at {shape!r} under the main tree"

    named = claims.lock_root(tmp_path / "control" / "claims")
    beside = named == _lock_root_beside(tmp_path / "control" / "claims")
    assert beside, "a named claim root did not resolve its lane locks beside it"


def test_a_later_subprocess_of_the_same_cycle_can_release_the_claim(tmp_path: Path) -> None:
    """THE SECOND FACET. ``_OWNED`` is process-local and a worker is not one process.

    An earlier per-call subprocess takes the claim and exits, taking its
    ``_OWNED`` entry with it. A later call of the SAME cycle then wraps and
    releases, and before CS-1009 it could not: the fallback compared the
    record's pid against the releasing process's own, which never matched, so
    the wrap left the record behind.

    The run id is what the later call offers in place of the lost table entry,
    and it is a real ABA guard rather than a waiver - the control below offers a
    DIFFERENT run id against the same token and is refused.

    The edit that reddens this: dropping the run-id branch from
    ``claims._is_ours``.
    """
    root = tmp_path / "control" / "claims"
    _claimant, token = _claim_and_exit(tmp_path, ROW_A, LANE_A, "one-cycle", root)

    refused = _release_from_a_second_process(tmp_path, token, root, "a-different-cycle")
    assert refused == "False", f"a stranger's run id released the claim - it answered {refused!r}"
    survived = str(claims.claim_state(ROW_A, root=root)["row"])
    assert survived == ROW_A, "the refused release removed the record anyway"

    released = _release_from_a_second_process(tmp_path, token, root, "one-cycle")
    assert released == "True", f"the cycle's own later call could not release - {released!r}"
    left = _rows_on_disk(root)
    assert left == set(), f"the release left {sorted(left)} behind"
