"""Grading for `ops/loop/queue_loop.py`, the driver that owns every wait.

NOT ONE TEST HERE SPAWNS A PROCESS, SLEEPS, SHELLS OUT OR TAKES A REAL OS
MUTEX, and that is a property this module asserts about ITSELF at the bottom
rather than a habit it hopes to keep. The sibling repo this driver was ported
from shipped two tests that took its real driver mutex, and they went red
exactly when the lane was running - a suite that fails because the product is
working is worse than no suite, because the first person to see it disables it.

Every external dependency of the driver is a keyword seam with a real default.
The defaults genuinely spawn processes and talk to `gh`; the tests pass fakes,
and `test_no_seam_defaults_are_reached` is what proves no test forgot one.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip. A missing driver must be a COLLECTION
# ERROR, not a skip: CONVENTIONS.md section 7.2 - "the unrun gate is where the
# bug hides. A skipped suite is not a passing suite."
from ops.loop import lane_launcher, lanes, queue_loop  # noqa: E402

# ---------------------------------------------------------------------------
# Fakes. Every one of them records what it was asked, because half the
# properties below are about ORDER rather than about a return value.
# ---------------------------------------------------------------------------


class FakeClock:
    """A monotonic and a wall clock that advance only when told to.

    Two of them, deliberately separate. The driver measures deadlines on the
    monotonic clock and stamps the ledger on the wall clock, and a test that
    shared one between them could not tell a correct driver from one that had
    them the wrong way round.
    """

    def __init__(self, wall: float = 1_000_000.0, mono: float = 0.0) -> None:
        """Start both clocks. Neither moves until `sleep` is called."""
        self.wall = wall
        self.mono = mono
        self.slept: list[float] = []

    def time(self) -> float:
        """Wall time, for the ledger stamp."""
        return self.wall

    def monotonic(self) -> float:
        """Deadline time. Advances only through `sleep`."""
        return self.mono

    def sleep(self, seconds: float) -> None:
        """Advance both clocks instead of blocking. Nothing here really waits."""
        self.slept.append(float(seconds))
        self.mono += float(seconds)
        self.wall += float(seconds)


class NullHold:
    """A stand-in for the ledger mutex that takes no OS handle at all."""

    def __init__(self) -> None:
        """Nothing is acquired here - there is no handle to acquire."""
        self.entered = 0
        self.wrote_inside = None

    def __call__(self):
        """Enter-able on every call, so one instance serves a whole loop."""
        return self

    def __enter__(self):
        """Count the entry. The count IS the assertion in one test."""
        self.entered += 1

    def __exit__(self, *exc):
        """Never swallow - a fake that hid an exception would hide a defect."""
        return False


class FakeGh:
    """A `gh` seam driven by a list of (rc, payload) answers, in order.

    A CLASS rather than a closure carrying attributes: half these tests assert
    on WHICH `gh` calls were made (that tier1 is never dispatched, that tier2 is
    dispatched exactly once), so the call log is part of the seam's interface
    rather than a debugging afterthought bolted onto a function object.

    `payload` may be a str (returned as-is) or any JSON-serialisable object,
    which is dumped - so a test states the SHAPE `gh` returns rather than
    hand-rolling its JSON.
    """

    def __init__(self, script) -> None:
        """`script` is the ordered list of (rc, payload) answers to hand back."""
        self.calls: list[list[str]] = []
        self.remaining: list = list(script)

    def __call__(self, args) -> tuple[int, str]:
        """Log the call, then answer with the next scripted result."""
        self.calls.append([str(a) for a in args])
        if not self.remaining:
            raise AssertionError(f"fake gh ran out of answers at {args!r}")
        rc, payload = self.remaining.pop(0)
        return rc, payload if isinstance(payload, str) else json.dumps(payload)


def run_row(
    *, database_id=1, head_sha="abc", status="completed", conclusion="success", event="push"
):
    return {
        "databaseId": database_id,
        "headSha": head_sha,
        "status": status,
        "conclusion": conclusion,
        "event": event,
    }


def jobs_payload(pairs):
    return {"jobs": [{"name": name, "conclusion": conclusion} for name, conclusion in pairs]}


#: Ids and pids the fakes hand back. Named so an assertion reads as a claim
#: about identity rather than as a bare literal repeated in two places.
EXISTING_RUN_ID = 7
WORKER_PID = 4242

#: Cycle counts a loop test asks for and then asserts on. Named so the two
#: halves cannot drift apart in an edit - the bug an inline literal invites.
THREE_CYCLES = 3
FIVE_CYCLES = 5
SIX_CYCLES = 6
TWO_CYCLES = 2
#: READ FROM THE MODULE, never hand-copied. A test-side copy of a limit is a
#: second source of truth: change the default in the driver and the arm goes on
#: asserting the old number, green, about a loop that no longer behaves that way.
ERROR_LIMIT = queue_loop.DEFAULT_MAX_CONSECUTIVE_ERRORS
#: Consecutive `launch_failed` cycles before the night stops. Named beside
#: ERROR_LIMIT because the two are separate counters and an inline literal
#: would let a reader assume otherwise.
LAUNCH_FAILURE_LIMIT = queue_loop.DEFAULT_MAX_CONSECUTIVE_LAUNCH_FAILURES
MAX_ASCII = 0x7E

TIER1_GREEN = (("gates, lint, types, tests", "success"), ("tests (save shard)", "success"))
TIER2_GREEN = (
    ("full suite (ubuntu-latest)", "success"),
    ("full suite (windows-latest)", "success"),
    ("clean-checkout probe (ubuntu-latest)", "success"),
    ("clean-checkout probe (windows-latest)", "success"),
    ("shell suite (ubuntu-latest)", "success"),
    ("shell suite (windows-latest)", "success"),
    ("dependency and license audit (advisory)", "success"),
)


# ---------------------------------------------------------------------------
# FIX 2, first half - a verdict is a SUMMARY LINE **and** an EXIT CODE.
#
# The failure this closes: a crashed xdist run leaves no summary line at all,
# and `grep -c FAILED` over that log returns 0 - which reads EXACTLY like a
# green run. Any grader that reads only one of the two halves accepts it.
# ---------------------------------------------------------------------------


def test_a_green_run_is_ok_and_keeps_its_summary_line_verbatim():
    line = "1801 passed, 12 skipped, 3 warnings in 1421.07s (0:23:41)"
    got = queue_loop.summarize_pytest(f"....\n{line}\n", 0)
    assert got["ok"] is True
    assert got["summary"] == line
    assert got["exit_code"] == 0
    assert got["truncated"] is False


def test_a_red_run_is_not_ok_even_though_it_has_a_summary_line():
    line = "2 failed, 1799 passed in 1402.11s (0:23:22)"
    got = queue_loop.summarize_pytest(f"{line}\n", 1)
    assert got["ok"] is False
    assert got["summary"] == line
    assert got["exit_code"] == 1


def test_a_truncated_log_that_exited_zero_is_not_green():
    """THE ONE THAT MATTERS. No summary line, exit 0, and it must not pass.

    This is the shape a crashed parallel run leaves behind: the workers die,
    the log stops mid-progress, and nothing in it says FAILED.
    """
    crashed = "tests/test_solve.py ..........\ntests/test_save.py .....\n"
    got = queue_loop.summarize_pytest(crashed, 0)
    assert got["truncated"] is True
    assert got["ok"] is False
    assert got["summary"] is None


def test_a_truncated_log_that_exited_nonzero_is_not_green_either():
    got = queue_loop.summarize_pytest("INTERNALERROR> ...\n", 3)
    assert got["ok"] is False
    assert got["truncated"] is True


def test_no_tests_collected_is_not_green():
    """Exit 5 with a real summary line. An empty suite proves nothing."""
    got = queue_loop.summarize_pytest("no tests ran in 0.01s\n", 5)
    assert got["summary"] == "no tests ran in 0.01s"
    assert got["ok"] is False


def test_the_last_summary_line_wins_over_an_earlier_one():
    """A rerun or a subprocess test can print more than one.

    The run's own verdict is the last one, never the first.
    """
    text = "1 failed, 2 passed in 0.10s\nrerunning\n5 passed in 0.20s\n"
    assert queue_loop.summarize_pytest(text, 0)["summary"] == "5 passed in 0.20s"


@pytest.mark.parametrize(
    "line",
    [
        "===== 5 failed, 10 passed in 3.21s =====",
        "5 passed in 3.21s",
        "no tests ran in 0.01s",
        "1 error in 0.50s",
        "2 passed, 1 xfailed, 3 warnings in 12.00s (0:00:12)",
    ],
)
def test_the_shapes_pytest_actually_emits_are_all_recognised(line):
    assert queue_loop.summarize_pytest(line + "\n", 0)["summary"] == line


def test_a_fault_is_named_without_rendering_the_exception_object(tmp_path):
    """CLAUDE.md non-negotiable 12, asserted on the OUTPUT and not the shape.

    The repo-wide guard in `tests/test_exception_rendering.py` bans the SHAPE -
    an `{exc}` or `str(exc)` in a message - across every tracked module, which
    is the stronger net. But a shape check passes just as happily if `_fault`
    were written to return `str(exc)`, so nothing would then be checking the
    only thing that matters: that the account name and the path are gone.

    A real OSError is raised against a real missing path under this machine's
    home directory, because that is the exact string the rule exists to keep out
    of the JSONL ledger.
    """
    # `pytest.raises` RATHER THAN try/except/else, and the reshape is the
    # liveness guard's doing rather than taste. A member credited to the try
    # generosity has to carry a try that GRADES - one whose body asserts, or
    # whose HANDLER terminates in failure. This test's first shape had a bare
    # read in the body and its failure in an `else`, which the guard does not
    # count and should not: a try that grades nothing is a try that cannot fail.
    # `raises` makes the expectation the assertion, which is what was meant.
    missing = tmp_path / "no-such-file.txt"
    # FileNotFoundError, not the OSError base: it is what a missing file
    # actually raises, and naming the broad base would let an unrelated
    # OSError satisfy this arm. It is still an OSError, so it takes the
    # same branch of the per-type allowlist under test.
    with pytest.raises(FileNotFoundError) as caught:
        missing.read_text(encoding="utf-8")

    # THE CONTROL IS `filename`, NOT `str(exc)`, and that is not a dodge -
    # `filename` IS the mechanism. It is the attribute OSError's own __str__
    # appends, so asserting the path is in it proves the exception really does
    # carry the thing being redacted. Rendering the object here to prove the
    # point would have written the leak into a tracked file, which the repo-wide
    # guard rightly refuses; it caught that line on the first run.
    carried = caught.value.filename or ""
    named = queue_loop._fault(caught.value)  # noqa: SLF001 - the site under test

    assert str(tmp_path) in carried, "the control failed: the exception carried no path"
    assert str(tmp_path) not in named, "the path survived redaction"
    assert Path(named).drive == "", f"a rooted path survived redaction: {named!r}"
    assert named, "a fault must still be NAMED - an empty string reports nothing"


def test_a_fault_with_no_strerror_degrades_to_its_type_name():
    """A real answer, not a silence: it says what went wrong in kind."""
    fault = queue_loop._fault  # noqa: SLF001 - the site under test
    assert fault(ValueError("something with a path: C:/x")) == "ValueError"


def test_the_local_suite_grades_the_lane_worktree_and_not_the_drivers_own_tree(tmp_path):
    """A green about the wrong commit is worse than no green.

    The worker commits and pushes from the lane worktree; the driver's own
    checkout has not pulled and is whatever it was when the night started. A
    suite run there would grade a tree NOBODY pushed and file it as this cycle's
    acceptance, and nothing in the ledger would distinguish it from a real one.
    """
    seen: list = []
    clock = FakeClock()
    lane_tree = r"C:\cs-worktrees\cs-lane-queue"

    def spy(**kw):
        seen.append(kw.get("cwd"))
        return {
            "ok": True,
            "summary": "1 passed in 0.10s",
            "exit_code": 0,
            "truncated": False,
            "argv": ["pytest"],
            "duration_s": 0.1,
            "detail": "",
        }

    queue_loop.run_loop(
        **loop_seams(
            clock,
            ci_gate=False,
            local_suite=True,
            worktree=lane_tree,
            suite=spy,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert seen == [lane_tree], f"the suite was pointed at {seen} rather than at the lane worktree"


def test_the_local_suite_runner_reports_the_command_it_ran():
    """A verdict nobody can reproduce is not evidence."""

    def runner(_argv, _cwd=None):
        return 0, "9 passed in 1.00s\n"

    clock = FakeClock()
    got = queue_loop.run_local_suite(runner=runner, monotonic=clock.monotonic)
    assert got["ok"] is True
    assert got["summary"] == "9 passed in 1.00s"
    assert isinstance(got["argv"], list), "the argv must be recorded as a list"
    assert got["argv"], "an empty argv would make the verdict unreproducible"


def test_the_local_suite_runner_never_raises_on_a_broken_runner():
    """A missing interpreter ends one cycle's verdict, never the night."""

    def runner(_argv, _cwd=None):
        raise OSError("python is not on PATH")

    got = queue_loop.run_local_suite(runner=runner, monotonic=FakeClock().monotonic)
    assert got["ok"] is False
    # THE TYPE, NOT THE MESSAGE. A single-argument OSError has no `strerror`,
    # and its message is author-written text that may carry anything - which is
    # precisely the case the per-type allowlist refuses to render. The verdict
    # still says the run produced no summary and is not ok, which is what the
    # loop acts on.
    assert got["detail"] == "OSError"
    assert got["truncated"] is True


# ---------------------------------------------------------------------------
# The CI grader. "Pooled" is the failure mode: a threshold met by a
# population's strongest member leaves the weakest unmeasured.
# ---------------------------------------------------------------------------


def test_all_required_jobs_green_grades_success():
    verdict, _ = queue_loop.grade_ci_jobs(queue_loop.CI_TIER1, jobs_payload(TIER1_GREEN))
    assert verdict == queue_loop.CI_SUCCESS


def test_one_failed_matrix_leg_fails_the_whole_workflow():
    """THE POOLED-GUARD CASE. Five legs green, one red, and the answer is red.

    A grader that stopped at the first match, or that asked "did any leg pass",
    would call this green and the weakest member would go unmeasured.
    """
    jobs = list(TIER2_GREEN)
    jobs[1] = ("full suite (windows-latest)", "failure")
    verdict, detail = queue_loop.grade_ci_jobs(queue_loop.CI_TIER2, jobs_payload(jobs))
    assert verdict == queue_loop.CI_FAILURE
    assert "windows-latest" in detail


def test_a_required_matcher_that_matches_nothing_is_unavailable_not_success():
    """An answer about the TOOL, not about the world.

    A workflow renamed out from under this driver must never read as a pass.
    """
    verdict, detail = queue_loop.grade_ci_jobs(
        queue_loop.CI_TIER1, jobs_payload((("some other job", "success"),))
    )
    assert verdict == queue_loop.CI_UNAVAILABLE
    assert verdict != queue_loop.CI_SUCCESS
    assert "gates, lint, types, tests" in detail


def test_an_advisory_job_going_red_does_not_fail_the_gate():
    """tier2's audit job carries continue-on-error and says advisory in its own name.

    Grading it would stop the night over a dependency advisory.
    """
    jobs = list(TIER2_GREEN)
    jobs[-1] = ("dependency and license audit (advisory)", "failure")
    verdict, _ = queue_loop.grade_ci_jobs(queue_loop.CI_TIER2, jobs_payload(jobs))
    assert verdict == queue_loop.CI_SUCCESS


def test_an_unknown_job_going_red_still_fails_the_gate():
    """A job added to the workflow later is graded, not ignored.

    The default for something this driver has never heard of is to grade
    it, because the opposite default silently drops coverage as CI
    grows.
    """
    jobs = [*TIER1_GREEN, ("a new job nobody told the driver about", "failure")]
    verdict, _ = queue_loop.grade_ci_jobs(queue_loop.CI_TIER1, jobs_payload(jobs))
    assert verdict == queue_loop.CI_FAILURE


def test_a_missing_jobs_list_is_unavailable():
    verdict, _ = queue_loop.grade_ci_jobs(queue_loop.CI_TIER1, {"jobs": "not a list"})
    assert verdict == queue_loop.CI_UNAVAILABLE


def test_every_verdict_word_is_in_the_declared_set():
    """Anything outside the set is a bug in the driver, not a state of the world."""
    assert queue_loop.CI_SUCCESS in queue_loop.CI_VERDICTS
    for name in dir(queue_loop):
        if name.startswith("CI_") and name not in {
            "CI_VERDICTS",
            "CI_REF",
            "CI_SPECS",
            "CI_TIER1",
            "CI_TIER2",
            "CI_RUN_LIST_LIMIT",
            "CI_TRIGGER_TRIES",
            "CI_TRIGGER_WAIT_S",
        }:
            value = getattr(queue_loop, name)
            if isinstance(value, str):
                assert value in queue_loop.CI_VERDICTS, f"{name} is not a declared verdict"


# ---------------------------------------------------------------------------
# Waiting on one workflow. Fail SOFT on tooling, HARD on the verdict.
# ---------------------------------------------------------------------------


def test_a_completed_green_run_is_found_and_graded_without_a_dispatch():
    gh = FakeGh(
        [
            (0, [run_row(database_id=EXISTING_RUN_ID, head_sha="deadbeef")]),
            (0, jobs_payload(TIER1_GREEN)),
        ]
    )
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "deadbeef",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_SUCCESS
    assert got["run_id"] == EXISTING_RUN_ID
    assert not any("workflow" in call and "run" in call for call in gh.calls), (
        "a run already existed - nothing should have been dispatched"
    )


def test_a_pending_run_is_polled_until_it_completes():
    gh = FakeGh(
        [
            (0, [run_row(database_id=9, status="in_progress", conclusion="")]),
            (0, {"status": "in_progress", "conclusion": ""}),
            (0, {"status": "completed", "conclusion": "success"}),
            (0, jobs_payload(TIER1_GREEN)),
        ]
    )
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "abc",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_SUCCESS
    assert clock.slept, "polling must actually wait between reads"


def test_a_run_that_outlives_the_budget_is_timeout_and_never_green():
    gh = FakeGh(
        [(0, [run_row(database_id=9, status="queued", conclusion="")])]
        + [(0, {"status": "queued", "conclusion": ""})] * 40
    )
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "abc",
        budget_s=30,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_TIMEOUT


def test_a_broken_gh_is_unavailable_and_does_not_raise():
    """A CLI hiccup may not end eleven remaining rows."""
    gh = FakeGh([(127, "gh: command not found")])
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "abc",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_UNAVAILABLE
    assert "not found" in got["detail"]


def test_unparseable_json_is_unavailable_not_a_traceback():
    gh = FakeGh([(0, "this is not json")])
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "abc",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_UNAVAILABLE


def test_a_cancelled_run_is_recorded_and_never_read_as_a_pass():
    """A cancelled run is recorded and never read as a pass.

    `gh run watch --exit-status` returns 0 on a cancelled run, so the run's own
    conclusion is the only thing that can say this.
    """
    gh = FakeGh(
        [
            (0, [run_row(database_id=3, conclusion="cancelled")]),
            (0, "gh workflow run failed"),
        ]
    )
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "abc",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_CANCELLED
    assert got["verdict"] != queue_loop.CI_SUCCESS


def test_tier2_is_dispatched_because_a_branch_push_does_not_trigger_it():
    """tier2.yml fires on schedule, on a v* TAG, and on workflow_dispatch.

    A push to main runs tier1 and nothing else, so the full suite only
    exists if this driver asks for it.
    """
    gh = FakeGh(
        [
            (0, []),  # nothing for this sha yet
            (0, ""),  # gh workflow run
            (0, [run_row(database_id=42, event="workflow_dispatch")]),
            (0, jobs_payload(TIER2_GREEN)),
        ]
    )
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER2,
        "abc",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_SUCCESS
    dispatched = [c for c in gh.calls if c[:2] == ["workflow", "run"]]
    assert len(dispatched) == 1, f"expected exactly one dispatch, saw {gh.calls}"
    assert "tier2.yml" in dispatched[0]


def test_tier1_is_never_dispatched_because_the_push_already_triggered_it():
    gh = FakeGh([(0, []), (0, "")] + [(0, [])] * 12)
    clock = FakeClock()
    got = queue_loop.wait_for_workflow(
        queue_loop.CI_TIER1,
        "abc",
        budget_s=600,
        poll_s=10,
        gh=gh,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert got["verdict"] == queue_loop.CI_UNAVAILABLE
    assert not [c for c in gh.calls if c[:2] == ["workflow", "run"]], (
        "tier1 has no workflow_dispatch trigger - dispatching it can only fail"
    )


# ---------------------------------------------------------------------------
# The roll-up across both workflows.
# ---------------------------------------------------------------------------


def test_the_rollup_is_red_when_either_workflow_is_red():
    def wait(spec, sha, **_kw):
        verdict = queue_loop.CI_SUCCESS if spec.workflow == "tier1.yml" else queue_loop.CI_FAILURE
        return {
            "workflow": spec.workflow,
            "verdict": verdict,
            "run_id": 1,
            "sha": sha,
            "status": "completed",
            "waited_s": 0.0,
            "jobs": {},
            "detail": "",
        }

    got = queue_loop.wait_for_ci("abc", wait_one=wait)
    assert got["verdict"] == queue_loop.CI_FAILURE
    assert len(got["workflows"]) == len(queue_loop.CI_SPECS)


def test_the_rollup_is_green_only_when_every_workflow_is_green():
    def wait(spec, sha, **_kw):
        return {
            "workflow": spec.workflow,
            "verdict": queue_loop.CI_SUCCESS,
            "run_id": 1,
            "sha": sha,
            "status": "completed",
            "waited_s": 0.0,
            "jobs": {},
            "detail": "",
        }

    assert queue_loop.wait_for_ci("abc", wait_one=wait)["verdict"] == queue_loop.CI_SUCCESS


def test_one_unavailable_workflow_downgrades_the_rollup_but_is_not_red():
    def wait(spec, sha, **_kw):
        verdict = (
            queue_loop.CI_SUCCESS if spec.workflow == "tier1.yml" else queue_loop.CI_UNAVAILABLE
        )
        return {
            "workflow": spec.workflow,
            "verdict": verdict,
            "run_id": None,
            "sha": sha,
            "status": "unknown",
            "waited_s": 0.0,
            "jobs": {},
            "detail": "",
        }

    got = queue_loop.wait_for_ci("abc", wait_one=wait)
    assert got["verdict"] == queue_loop.CI_UNAVAILABLE
    assert got["verdict"] != queue_loop.CI_FAILURE, "missing evidence is not a break"


# ---------------------------------------------------------------------------
# The ledger. FIX 2's other half - every cycle leaves an artifact.
# ---------------------------------------------------------------------------


def test_a_record_is_appended_as_one_line_of_json(tmp_path):
    log = tmp_path / "nested" / "queue_loop.jsonl"
    hold = NullHold()
    queue_loop.append_record({"cycle": 1, "ok": True}, log, hold=hold)
    queue_loop.append_record({"cycle": 2, "ok": False}, log, hold=hold)
    lines = log.read_text(encoding="utf-8").splitlines()
    parsed = [json.loads(line)["cycle"] for line in lines]
    assert parsed == [1, 2]


def test_the_ledger_stays_lf_on_windows(tmp_path):
    """The ledger stays LF, including on Windows.

    Text mode would translate to CRLF, which silently changes byte counts and
    makes this file disagree with every other .jsonl in the tree.
    """
    log = tmp_path / "queue_loop.jsonl"
    queue_loop.append_record({"cycle": 1}, log, hold=NullHold())
    assert b"\r\n" not in log.read_bytes()


def test_the_append_happens_inside_the_lock(tmp_path):
    log = tmp_path / "queue_loop.jsonl"
    hold = NullHold()
    queue_loop.append_record({"cycle": 1}, log, hold=hold)
    assert hold.entered == 1


def test_a_wedged_ledger_lock_still_writes_the_row_loudly(tmp_path):
    """FAIL OPEN. A dropped row loses the only evidence of a cycle."""
    log = tmp_path / "queue_loop.jsonl"

    class Wedged:
        def __call__(self):
            raise queue_loop.winmutex.MutexTimeout("held")

    said: list[str] = []
    queue_loop.append_record({"cycle": 1}, log, hold=Wedged(), emit=said.append)
    assert json.loads(log.read_text(encoding="utf-8").strip())["cycle"] == 1
    assert any("UNSERIALIZED" in line for line in said)


# ---------------------------------------------------------------------------
# Stop sentinels.
# ---------------------------------------------------------------------------


def test_no_sentinel_means_no_reason(tmp_path):
    assert queue_loop.stop_reason(tmp_path) is None


@pytest.mark.parametrize("rel", queue_loop.STOP_RELPATHS)
def test_each_sentinel_stops_the_loop(tmp_path, rel):
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("halt", encoding="utf-8")
    assert queue_loop.stop_reason(tmp_path) == Path(rel).name


def test_the_global_halt_is_reported_ahead_of_the_lane_local_one(tmp_path):
    for rel in queue_loop.STOP_RELPATHS:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("halt", encoding="utf-8")
    assert queue_loop.stop_reason(tmp_path) == "STOP"


def test_a_sentinel_name_resolves_back_to_its_full_path(tmp_path):
    assert (
        queue_loop.stop_path_for("QUEUE_DRAINED", tmp_path) == tmp_path / "lanes" / "QUEUE_DRAINED"
    )
    assert queue_loop.stop_path_for("not-a-sentinel", tmp_path) is None


# ---------------------------------------------------------------------------
# One cycle. Every lane seam injected - nothing here touches a real lock.
# ---------------------------------------------------------------------------


def cycle_seams(fake, **over):
    """The full seam set for run_cycle, all fake, with per-test overrides."""
    seams = {
        "acquire": lambda lane, **kw: {
            "ok": True,
            "token": "T",
            "lane": lane,
            "run_id": kw.get("run_id"),
            "worktree": kw.get("worktree"),
        },
        "release": lambda _token, **_kw: True,
        "launch": lambda _lane, **kw: {
            "pid": WORKER_PID,
            "log": "lane.log",
            "worktree": "W",
            "run_id": kw.get("run_id"),
        },
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 123.0,
        "stranger": lambda _pid, _started: False,
        "kill": lambda _pid: None,
        "sleep": fake.sleep,
        "clock": fake.time,
        "monotonic": fake.monotonic,
        "worktree": r"C:\cs-worktrees\cs-lane-queue",
    }
    seams.update(over)
    return seams


def test_the_repo_root_is_forwarded_to_the_launcher():
    """The lane reads its PROMPT from a tree, and which tree is a real choice.

    By default it is the main checkout, which is right in steady state. But
    before the lane's own code has reached main, that checkout does not carry
    `tools/headless-queue.md` at all - so a proving cycle would read a prompt
    that is not there and record `launch_failed` for a reason that has nothing
    to do with the lane. This forwards the choice instead of hardcoding it.
    """
    clock = FakeClock()
    seen: list = []

    class Launcher:
        LaneLaunchError = RuntimeError

        @staticmethod
        def launch_lane(_lane, **kw):
            seen.append(kw.get("root"))
            return {"pid": WORKER_PID, "log": "l"}

        @staticmethod
        def worktree_path(_lane):
            return r"C:\cs-worktrees\cs-lane-queue"

    seams = cycle_seams(clock)
    seams.pop("launch")
    seams.pop("worktree")
    branch_tree = r"C:\Clockspeed\.claude\worktrees\some-branch"
    queue_loop.lane_launcher = Launcher  # the lazily-bound module object
    try:
        queue_loop.run_cycle(1, repo_root=branch_tree, **seams)
    finally:
        del queue_loop.lane_launcher
    assert seen == [branch_tree]


def test_a_clean_cycle_completes_and_records_the_worker_pid():
    clock = FakeClock()
    got = queue_loop.run_cycle(1, **cycle_seams(clock))
    assert got["outcome"] == queue_loop.OUTCOME_COMPLETED
    # `run_cycle` knows only whether the WORKER finished. Whether the cycle
    # was good news needs the verdicts, and only `run_loop` has those.
    assert got["worker_ok"] is True
    assert "ok" not in got, "run_cycle must not claim a roll-up it cannot compute"
    assert got["pid"] == WORKER_PID


def test_the_lane_is_released_on_the_happy_path():
    clock = FakeClock()
    released: list[str] = []
    queue_loop.run_cycle(1, **cycle_seams(clock, release=lambda t, **_kw: released.append(t)))
    assert released == ["T"]


def test_the_lane_is_released_when_the_launch_explodes():
    """A lock with no process behind it is strictly worse than no lock."""
    clock = FakeClock()
    released: list[str] = []

    def boom(_lane, **_kw):
        raise RuntimeError("the launcher fell over")

    with pytest.raises(RuntimeError):
        queue_loop.run_cycle(
            1, **cycle_seams(clock, launch=boom, release=lambda t, **_kw: released.append(t))
        )
    assert released == ["T"], "the release must run before the exception escapes"


def test_a_held_lane_is_recorded_and_is_not_an_error():
    """A refusal is a normal answer, recorded and survived.

    A driver that died the first night the operator's own lane overlapped by a
    minute would be useless.
    """
    clock = FakeClock()
    got = queue_loop.run_cycle(
        1,
        **cycle_seams(
            clock,
            acquire=lambda _lane, **_kw: {
                "ok": False,
                "refused": "lane_held",
                "holder": "queue",
                "pid": 99,
            },
            acquire_retries=3,
            acquire_wait_s=30,
        ),
    )
    assert got["outcome"] == queue_loop.OUTCOME_LANE_HELD
    assert got["worker_ok"] is False
    assert clock.slept == [30, 30], "no wait after the FINAL attempt"


def test_a_launch_failure_is_recorded_not_raised():
    clock = FakeClock()

    def fails(_lane, **_kw):
        raise queue_loop.lane_launcher.LaneLaunchError("no worktree")

    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=fails))
    assert got["outcome"] == queue_loop.OUTCOME_LAUNCH_FAILED
    # THE TYPE PLUS A CODE THE DRIVER ITSELF HOLDS, never the message, and the
    # reason is the guard's structural rule: a module may render whole only an
    # exception type IT defines, because it builds that message. LaneLaunchError
    # is defined in the launcher, so this module may not take its word for it -
    # see queue_loop._launch_fault. A site that named no reason lands on
    # `unspecified`, which is a member of the vocabulary and so is recorded.
    assert got["detail"] == "LaneLaunchError: unspecified"
    assert "no worktree" not in got["detail"], "the launcher's message reached the row"


def test_a_launch_failure_records_the_launchers_own_reason_code():
    """The refusal is NAMED, not merely typed.

    The repoint refusal is the one driven here because it is the raise site the
    evidence on disk points at: a row reading `launch_failed LaneLaunchError`
    says a lane did not start and nothing about why, which is the defect.
    """
    clock = FakeClock()

    def fails(_lane, **_kw):
        raise queue_loop.lane_launcher.LaneLaunchError(
            "could not re-point the lane lock at the worker",
            reason=lane_launcher.REASON_REPOINT_REFUSED,
        )

    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=fails))
    assert got["outcome"] == queue_loop.OUTCOME_LAUNCH_FAILED
    assert "repoint_refused" in got["detail"], f"the reason was dropped: {got['detail']!r}"
    assert "LaneLaunchError" in got["detail"], "a fault must still be named by TYPE"


def test_a_reason_the_driver_does_not_know_is_never_written_into_the_row(tmp_path):
    """THE PRIVACY ARM - the whole justification for the driver's own copy.

    Without it, "the driver validates the code" is an unmeasured claim. The
    planted value is path-shaped, which is exactly the class of string
    CLAUDE.md non-negotiable 12 exists to keep out of a durable JSONL row.
    """
    clock = FakeClock()
    planted = str(tmp_path / "cs-lane-queue")

    def fails(_lane, **_kw):
        raise queue_loop.lane_launcher.LaneLaunchError("refused", reason=planted)

    # THE CONTROL FIRST. An arm that asserts only an absence passes just as
    # happily when the value was never there to redact.
    assert str(tmp_path) in planted, "the control failed: the planted reason carried no path"

    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=fails))
    assert str(tmp_path) not in got["detail"], "an unvalidated reason reached the row"
    assert Path(got["detail"]).drive == "", f"a rooted path survived: {got['detail']!r}"
    assert got["detail"] == "LaneLaunchError", "a fault must still be NAMED by its type"


def test_the_driver_and_the_launcher_hold_the_same_reason_vocabulary():
    """Two copies on purpose, so drift between them has to be LOUD.

    The driver writes only a word it itself contains, which is what makes a
    launcher running ahead of its driver degrade to a bare type name rather
    than leak a word chosen after the driver was written. The cost of that
    design is drift, and this arm is what pays it: without this assertion a
    launcher-side addition degrades silently, which is the defect CS-970
    closes, reintroduced by an edit nobody graded.
    """
    driver = tuple(queue_loop._LAUNCH_REASONS)  # noqa: SLF001 - the copy under test
    assert driver, "the driver's vocabulary is empty - every reason would be discarded"
    assert driver == tuple(lane_launcher.LAUNCH_REASONS), (
        "the driver and the launcher disagree about the reason vocabulary; "
        "a code the driver does not hold is silently discarded"
    )


def test_an_exception_with_no_reason_attribute_still_records_its_type():
    """A launch seam that raises a REASONLESS exception must not fault the driver."""
    clock = FakeClock()

    class Launcher:
        LaneLaunchError = RuntimeError

        @staticmethod
        def worktree_path(_lane):
            return r"C:\cs-worktrees\cs-lane-queue"

    def fails(_lane, **_kw):
        raise RuntimeError("no reason attribute anywhere on me")

    seams = cycle_seams(clock, launch=fails)
    seams.pop("worktree")
    queue_loop.lane_launcher = Launcher  # the lazily-bound module object
    try:
        got = queue_loop.run_cycle(1, **seams)
    finally:
        del queue_loop.lane_launcher
    assert got["outcome"] == queue_loop.OUTCOME_LAUNCH_FAILED
    assert got["detail"] == "RuntimeError"


def test_a_launch_that_returns_no_pid_is_a_launch_failure():
    clock = FakeClock()
    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=lambda _lane, **_kw: {"pid": None}))
    assert got["outcome"] == queue_loop.OUTCOME_LAUNCH_FAILED


def test_a_worker_that_outstays_its_budget_is_killed_once():
    clock = FakeClock()
    killed: list[int] = []
    alive_calls = {"n": 0}

    def alive(_pid):
        alive_calls["n"] += 1
        # Alive until the kill lands, then gone.
        return not killed

    got = queue_loop.run_cycle(
        1, **cycle_seams(clock, alive=alive, kill=killed.append, cycle_timeout_s=30, poll_s=10)
    )
    assert got["outcome"] == queue_loop.OUTCOME_TIMEOUT
    assert killed == [WORKER_PID], "exactly one kill - a second could land on a reissued pid"


def test_a_worker_that_survives_its_kill_is_a_different_outcome():
    """A kill that did not take must not read as a kill that did.

    An unverified kill is the same hazard as no kill: the next cycle would fire
    a second worker into a worktree that still has a live writer.
    """
    clock = FakeClock()
    got = queue_loop.run_cycle(
        1,
        **cycle_seams(
            clock,
            alive=lambda _pid: True,
            kill=lambda _pid: None,
            cycle_timeout_s=30,
            poll_s=10,
            kill_grace_s=15,
        ),
    )
    assert got["outcome"] == queue_loop.OUTCOME_KILL_FAILED
    assert got["outcome"] != queue_loop.OUTCOME_TIMEOUT


def test_the_deadline_runs_on_the_monotonic_clock_not_the_wall_clock():
    """An NTP step backwards must not silently extend the budget.

    The wall clock is frozen here and the cycle must still time out.
    """
    clock = FakeClock()
    killed: list[int] = []
    # The wall clock is handed in FROZEN - it answers the same instant forever,
    # which is what an NTP step backwards looks like at its worst. Substituted
    # rather than assigned onto the fake, because rebinding a method on an
    # instance is a different act from injecting a seam and only one of them is
    # what the driver actually exposes.
    got = queue_loop.run_cycle(
        1,
        **cycle_seams(
            clock,
            alive=lambda _pid: not killed,
            kill=killed.append,
            clock=lambda: 1_000_000.0,
            cycle_timeout_s=30,
            poll_s=10,
        ),
    )
    assert got["outcome"] == queue_loop.OUTCOME_TIMEOUT


def test_a_worker_identity_is_a_pid_and_a_start_time():
    """A pid alone does not name a process - the OS reissues it.

    A pid that is alive but belongs to a stranger means our worker is gone.
    """
    clock = FakeClock()
    got = queue_loop.run_cycle(
        1, **cycle_seams(clock, alive=lambda _pid: True, stranger=lambda _pid, _started: True)
    )
    assert got["outcome"] == queue_loop.OUTCOME_COMPLETED


# ---------------------------------------------------------------------------
# FIX 1 - THE DRIVER OWNS EVERY WAIT. This is the whole point of the port.
# ---------------------------------------------------------------------------


def loop_seams(fake, **over):
    seams = {
        "settle_s": 0,
        "poll_s": 1,
        "max_cycles": 1,
        "acquire": lambda _lane, **_kw: {"ok": True, "token": "T"},
        "release": lambda _token, **_kw: True,
        "launch": lambda _lane, **_kw: {"pid": 1, "log": "l"},
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _s: False,
        "kill": lambda _pid: None,
        "head_sha": lambda: "sha-unchanged",
        "sleep": fake.sleep,
        "clock": fake.time,
        "monotonic": fake.monotonic,
        "emit": lambda _line: None,
        "worktree": r"C:\cs-worktrees\cs-lane-queue",
    }
    seams.update(over)
    return seams


def test_the_driver_waits_between_cycles_and_the_next_cycle_cannot_start_first(tmp_path):
    """THE MECHANISM, asserted as an ORDER.

    The sibling repo wrote this rule as PROSE in the worker's prompt and
    measured it half-hold over six cycles: two workers blocked, four bailed
    early, and each bail let the next cycle cancel the run. The fix is not a
    better sentence - it is that the only thing which can start cycle N+1 is
    the driver, and the driver is inside the wait. So the property to grade is
    the INTERLEAVING, not the presence of a call.
    """
    order: list[str] = []
    shas = iter(["sha0", "sha1", "sha1", "sha2", "sha2", "sha3"])
    clock = FakeClock()

    def launch(_lane, **_kw):
        order.append("cycle")
        return {"pid": 1, "log": "l"}

    def wait(sha, **_kw):
        order.append("wait")
        return {"verdict": queue_loop.CI_SUCCESS, "workflows": [], "sha": sha, "waited_s": 1.0}

    queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=3,
            launch=launch,
            wait=wait,
            head_sha=lambda: next(shas),
            ci_gate=True,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert order == ["cycle", "wait", "cycle", "wait", "cycle", "wait"], (
        f"a wait that does not sit BETWEEN two cycles is not serialising anything: {order}"
    )


def test_no_wait_runs_when_the_worker_pushed_nothing(tmp_path):
    """The remote ref not moving means there is no run to wait for.

    Waiting anyway would grade somebody else's push as this cycle's
    acceptance.
    """
    waits: list[str] = []
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            head_sha=lambda: "same",
            ci_gate=True,
            wait=lambda sha, **_kw: waits.append(sha),
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert waits == []
    assert summary["records"][0]["ci"]["verdict"] == queue_loop.CI_NO_PUSH


def test_a_cycle_that_pushed_nothing_is_recorded_as_no_push_and_is_not_ok(tmp_path):
    """THE PAIR IS THE POINT: the worker was fine and the cycle was not good news.

    Measured on disk: `ops/loop/reports/queue_loop.jsonl` carries a 972-second
    cycle whose console line says `ci=no-push` and whose row says `"ok": true`,
    because the no-push branch set a local console note and never set
    `record["ci"]` at all. An absent key made the roll-up's verdict clause
    vacuously true.
    """
    waits: list[str] = []
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            head_sha=lambda: "same",
            ci_gate=True,
            wait=lambda sha, **_kw: waits.append(sha),
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    row = summary["records"][0]
    assert waits == [], "no run exists to wait for when nothing was pushed"
    assert row["ci"]["verdict"] == queue_loop.CI_NO_PUSH
    assert row["worker_ok"] is True, "the WORKER finished - that half is unchanged"
    assert row["ok"] is False, "a cycle that shipped nothing is not good news"
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES, (
        "a no-push is not a broken branch and must not stop the night"
    )


def test_a_gate_that_did_not_run_leaves_an_absent_ci_key(tmp_path):
    """A PRESERVED GUARD, not a new one.

    `test_no_wait_runs_when_the_worker_pushed_nothing` used to carry this
    assertion - "an absent gate must be an ABSENT key, never a verdict word".
    That case now has a verdict of its own, so the property MOVES here, to the
    case that still holds it: the gate was off, so no gate ran.
    """
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            ci_gate=False,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    row = summary["records"][0]
    assert "ci" not in row, "an absent gate must be an ABSENT key, never a verdict word"
    assert row["ok"] is True


def test_an_unresolvable_remote_is_recorded_as_unavailable_not_as_a_green(tmp_path):
    """A night whose CI evidence is missing must not read like a night of greens."""
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            head_sha=lambda: None,
            ci_gate=True,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["records"][0]["ci"]["verdict"] == queue_loop.CI_UNAVAILABLE


def test_one_cycle_writes_exactly_one_jsonl_row_carrying_its_verdict(tmp_path):
    """ACCEPTANCE 1, in unit form."""
    log = tmp_path / "queue_loop.jsonl"
    clock = FakeClock()
    shas = iter(["before", "after"])
    queue_loop.run_loop(
        **loop_seams(
            clock,
            head_sha=lambda: next(shas),
            ci_gate=True,
            wait=lambda sha, **_kw: {
                "verdict": queue_loop.CI_SUCCESS,
                "workflows": [{"workflow": "tier1.yml", "verdict": "success"}],
                "sha": sha,
                "waited_s": 12.0,
            },
            cycle_log=log,
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    for key in ("cycle", "run_id", "outcome", "pid", "duration_s", "ci"):
        assert key in row, f"a row without {key!r} cannot be read at 3am"
    assert row["ci"]["verdict"] == "success"


def test_a_red_verdict_is_not_carried_by_a_green_row(tmp_path):
    """THE 3AM PROPERTY. A row whose tests failed must not say `ok`.

    Measured on the first real cycle: the row read `"ok": true` beside
    `"suite": {"ok": false, "exit_code": 1}`. Each field was correctly scoped -
    the outer one about the worker, the inner one about the tests - and the pair
    was still a trap, because anyone grepping the ledger for a failure would
    have walked straight past it. The outer field now says which question it
    answers, and `ok` answers the one a reader assumes.
    """
    log = tmp_path / "queue_loop.jsonl"
    clock = FakeClock()
    queue_loop.run_loop(
        **loop_seams(
            clock,
            ci_gate=False,
            local_suite=True,
            suite=lambda **_kw: {
                "ok": False,
                "summary": "1 failed, 5672 passed in 820.97s",
                "exit_code": 1,
                "truncated": False,
                "argv": ["pytest"],
                "duration_s": 820.97,
                "detail": "exit 1",
            },
            cycle_log=log,
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    row = json.loads(log.read_text(encoding="utf-8").strip())
    assert row["worker_ok"] is True, "the worker did finish - that half is unchanged"
    assert row["ok"] is False, "a row whose suite went red must not read as ok"


def test_the_local_suite_verdict_rides_on_the_same_row(tmp_path):
    log = tmp_path / "queue_loop.jsonl"
    clock = FakeClock()
    queue_loop.run_loop(
        **loop_seams(
            clock,
            ci_gate=False,
            local_suite=True,
            suite=lambda **_kw: {
                "ok": True,
                "summary": "5 passed in 1.00s",
                "exit_code": 0,
                "truncated": False,
                "argv": ["pytest"],
                "duration_s": 1.0,
                "detail": "",
            },
            cycle_log=log,
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    row = json.loads(log.read_text(encoding="utf-8").strip())
    assert row["suite"]["summary"] == "5 passed in 1.00s"
    assert row["suite"]["exit_code"] == 0


def test_a_red_local_suite_stops_the_loop(tmp_path):
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=5,
            ci_gate=False,
            local_suite=True,
            suite=lambda **_kw: {
                "ok": False,
                "summary": "2 failed, 9 passed in 1.0s",
                "exit_code": 1,
                "truncated": False,
                "argv": ["pytest"],
                "duration_s": 1.0,
                "detail": "",
            },
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_SUITE_RED
    assert summary["cycles_run"] == 1


# ---------------------------------------------------------------------------
# The loop's stops.
# ---------------------------------------------------------------------------


def test_a_sentinel_present_before_cycle_one_runs_zero_cycles(tmp_path):
    """The sentinel is checked before cycle one, not only between cycles.

    A driver that only checks BETWEEN cycles fires one unwanted worker on every
    start, and against this lane that is one work item executed and committed.
    """
    control = tmp_path / "control"
    (control / "lanes").mkdir(parents=True)
    (control / "lanes" / "QUEUE_STOP").write_text("halt", encoding="utf-8")
    clock = FakeClock()
    fired: list[int] = []
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=5,
            launch=lambda _lane, **_kw: fired.append(1),
            control_dir=control,
            cycle_log=tmp_path / "l.jsonl",
            hold=NullHold(),
        )
    )
    assert summary["cycles_run"] == 0
    assert fired == []
    assert summary["stopped_by"] == "QUEUE_STOP"


def test_ci_going_red_stops_the_night(tmp_path):
    clock = FakeClock()
    shas = iter(["a", "b", "c", "d"])
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=4,
            ci_gate=True,
            head_sha=lambda: next(shas),
            wait=lambda sha, **_kw: {
                "verdict": queue_loop.CI_FAILURE,
                "workflows": [],
                "sha": sha,
                "waited_s": 1.0,
            },
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_CI_RED
    assert summary["cycles_run"] == 1, "no further row may be stacked on a break"


def test_a_cancelled_ci_run_is_recorded_but_does_not_stop_the_night(tmp_path):
    clock = FakeClock()
    shas = iter(["a", "b", "c", "d", "e", "f"])
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=TWO_CYCLES,
            ci_gate=True,
            head_sha=lambda: next(shas),
            wait=lambda sha, **_kw: {
                "verdict": queue_loop.CI_CANCELLED,
                "workflows": [],
                "sha": sha,
                "waited_s": 1.0,
            },
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["cycles_run"] == TWO_CYCLES
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES


def test_a_worker_surviving_its_kill_stops_the_night(tmp_path):
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=4,
            ci_gate=False,
            alive=lambda _pid: True,
            cycle_timeout_s=10,
            poll_s=5,
            kill_grace_s=5,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["stopped_by"] == queue_loop.OUTCOME_KILL_FAILED
    assert summary["cycles_run"] == 1


def test_one_fault_is_recorded_and_the_night_goes_on(tmp_path):
    """One fault is recorded and the night goes on.

    The SILENT half was the worse half: a fault used to leave no ledger row at
    all, and the morning's only evidence was a log that stopped.
    """
    log = tmp_path / "l.jsonl"
    clock = FakeClock()
    n = {"i": 0}

    def flaky(_lane, **_kw):
        n["i"] += 1
        if n["i"] == 1:
            raise ValueError("one bad cycle")
        return {"ok": True, "token": "T"}

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=THREE_CYCLES,
            ci_gate=False,
            acquire=flaky,
            cycle_log=log,
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == THREE_CYCLES
    assert rows[0]["outcome"] == queue_loop.OUTCOME_ERROR
    # THE TYPE, NOT THE MESSAGE, and that is deliberate rather than a
    # weakening. This detail is written into the JSONL ledger, and non-negotiable
    # 12 forbids rendering a caught exception object there: `str()` on an
    # OSError appends the path it failed on, which carries the account name. So
    # the row names the fault in KIND. The full text still reaches a traceback
    # through the chained cause; it is only kept out of the durable file.
    assert rows[0]["detail"] == "ValueError"
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES


def test_a_fault_that_repeats_stops_the_night(tmp_path):
    clock = FakeClock()

    def always(_lane, **_kw):
        raise ValueError("the same traceback every time")

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=12,
            ci_gate=False,
            acquire=always,
            max_consecutive_errors=ERROR_LIMIT,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_CONSECUTIVE_ERRORS
    assert summary["cycles_run"] == ERROR_LIMIT


def test_errors_are_consecutive_not_cumulative(tmp_path):
    """One bad cycle between good ones is a transient the loop must survive."""
    clock = FakeClock()
    n = {"i": 0}

    def alternating(_lane, **_kw):
        n["i"] += 1
        if n["i"] % 2:
            raise ValueError("flaky")
        return {"ok": True, "token": "T"}

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=SIX_CYCLES,
            ci_gate=False,
            acquire=alternating,
            max_consecutive_errors=2,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["cycles_run"] == SIX_CYCLES


def _always_refuses(_lane, **_kw):
    """A launch seam that refuses every time, the way a mis-wired lane does."""
    raise queue_loop.lane_launcher.LaneLaunchError(
        "the lane is not wired", reason=lane_launcher.REASON_LANE_NOT_WIRED
    )


def test_launch_failures_that_repeat_stop_the_night(tmp_path):
    """A refusal that will repeat must not burn the whole budget.

    Measured on disk before this arm existed: `launch_failed` fell into the
    `else` that RESETS the error counter, so twelve cycles could refuse in a
    row and the night still read as a full night's work.
    """
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=12,
            ci_gate=False,
            launch=_always_refuses,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    # THE EXACT COUNT, not merely fewer than twelve: the exact count is what
    # proves the NEW limit is the one that fired.
    assert summary["cycles_run"] == LAUNCH_FAILURE_LIMIT
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_LAUNCH_FAILED
    rows = (tmp_path / "l.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == LAUNCH_FAILURE_LIMIT


def test_launch_failures_are_consecutive_not_cumulative(tmp_path):
    """One refusal between good cycles is a transient the loop must survive."""
    clock = FakeClock()
    script = iter([True, True, False, True, True])

    def scripted(lane, **kw):
        if next(script):
            return _always_refuses(lane, **kw)
        return {"pid": 1, "log": "l"}

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=FIVE_CYCLES,
            ci_gate=False,
            launch=scripted,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert summary["cycles_run"] == FIVE_CYCLES
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES


def test_an_error_and_a_launch_failure_do_not_share_one_counter(tmp_path):
    """TWO named counters, and this is what makes that design a measured claim.

    THE ACCEPTANCE CLAUSE OF THIS ARM WAS WITHDRAWN. It used to assert that an
    alternating night ran its WHOLE budget, which encoded a residual a later
    adversary reproduced as a defect: a night that completes nothing must not
    burn twelve cycles, whatever mixture of words it uses to complete nothing.
    The separateness property survives that correction and is graded here in
    the form that actually tests it - the night stops, and it stops under
    NEITHER specific word. Folding the two counters into one would stop it under
    one of them and redden here.
    """
    clock = FakeClock()
    seen = {"n": 0}

    def alternating_acquire(_lane, **_kw):
        seen["n"] += 1
        if seen["n"] % 2:
            raise ValueError("a fault run_cycle does not convert into an outcome")
        return {"ok": True, "token": "T"}

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=SIX_CYCLES,
            ci_gate=False,
            acquire=alternating_acquire,
            launch=_always_refuses,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    outcomes = [r["outcome"] for r in summary["records"]]
    assert outcomes == ["error", "launch_failed", "error"], (
        f"the plant did not alternate: {outcomes}"
    )
    assert summary["cycles_run"] == THREE_CYCLES
    # NEITHER specific word: each counter was reset by the other's cycle, which
    # is precisely what "they do not share a counter" means. The night still
    # ends, under the general invariant rather than under either name.
    assert summary["stopped_by"] == "no_progress"


def test_the_settle_does_not_run_after_the_final_cycle(tmp_path):
    clock = FakeClock()
    queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=THREE_CYCLES,
            settle_s=45,
            ci_gate=False,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
        )
    )
    assert clock.slept.count(45) == THREE_CYCLES - 1, "three cycles, two gaps"


# ---------------------------------------------------------------------------
# The CLI. Distinct exit codes, because a launcher cannot otherwise tell a
# night that ran from a launch that did nothing.
# ---------------------------------------------------------------------------


class FakeSingleton:
    """Stands in for the driver mutex. Takes no OS handle."""

    def __init__(self, raises=None):
        """`raises` makes this refuse, standing in for a second live driver."""
        self.raises = raises
        self.held = 0

    def __call__(self):
        """Refuse, or hand back a context manager holding nothing."""
        if self.raises is not None:
            raise self.raises
        return self

    def __enter__(self):
        """Count the hold."""
        self.held += 1

    def __exit__(self, *exc):
        """Never swallow."""
        return False


def test_zero_cycles_over_a_pre_existing_sentinel_exits_distinctly(tmp_path, monkeypatch):
    control = tmp_path / "control"
    control.mkdir()
    (control / "STOP").write_text("operator halt", encoding="utf-8")
    monkeypatch.setattr(
        queue_loop, "run_loop", lambda **_kw: {"cycles_run": 0, "stopped_by": "STOP", "records": []}
    )
    code = queue_loop.main(["--once", "--control-dir", str(control)], singleton=FakeSingleton())
    assert code == queue_loop.EXIT_STOP_SENTINEL
    assert code != queue_loop.EXIT_OK, "a launcher must be able to tell a no-op from a night's work"


def test_a_second_driver_refuses_with_its_own_code():
    code = queue_loop.main(
        ["--once"], singleton=FakeSingleton(raises=queue_loop.winmutex.MutexTimeout("held"))
    )
    assert code == queue_loop.EXIT_ALREADY_RUNNING


@pytest.mark.parametrize(
    ("stopped_by", "expected"),
    [
        ("max_cycles", 0),
        ("QUEUE_DRAINED", 0),
        ("timeout_kill_failed", 4),
        ("consecutive_errors", 5),
        ("ci_red", 6),
        ("suite_red", 7),
        ("consecutive_launch_failures", 8),
        ("no_progress", 9),
    ],
)
def test_every_stop_reason_has_its_own_exit_code(monkeypatch, stopped_by, expected):
    """THE NUMBERS ARE PINNED AS LITERALS, never resolved from the module.

    This arm used to read its expectation back out of the very constant it was
    grading - `assert code == getattr(queue_loop, expected)` - so it could never
    observe that constant changing. Proof: setting
    EXIT_CONSECUTIVE_LAUNCH_FAILURES to 5 collided it with
    EXIT_CONSECUTIVE_ERRORS and this arm stayed GREEN while two stop reasons
    collapsed onto one number. A literal is the only oracle an exit code has,
    because the number IS the contract with the launcher and the scheduled task.
    """
    monkeypatch.setattr(
        queue_loop,
        "run_loop",
        lambda **_kw: {"cycles_run": 1, "stopped_by": stopped_by, "records": []},
    )
    code = queue_loop.main(["--once"], singleton=FakeSingleton())
    assert code == expected


def test_a_drained_queue_mid_run_is_still_a_success(monkeypatch):
    """The normal end of a good night.

    A sentinel the WORKER wrote after doing real work is not the same as
    one that was already there.
    """
    monkeypatch.setattr(
        queue_loop,
        "run_loop",
        lambda **_kw: {"cycles_run": 4, "stopped_by": "QUEUE_DRAINED", "records": []},
    )
    assert queue_loop.main([], singleton=FakeSingleton()) == queue_loop.EXIT_OK


def test_once_overrides_the_cycle_count(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        queue_loop,
        "run_loop",
        lambda **kw: (
            seen.update(kw) or {"cycles_run": 1, "stopped_by": "max_cycles", "records": []}
        ),
    )
    queue_loop.main(["--cycles", "12", "--once"], singleton=FakeSingleton())
    assert seen["max_cycles"] == 1


def test_the_exit_codes_are_all_distinct():
    codes = {
        name: getattr(queue_loop, name) for name in dir(queue_loop) if name.startswith("EXIT_")
    }
    assert len(set(codes.values())) == len(codes), f"colliding exit codes: {codes}"


# ---------------------------------------------------------------------------
# THE DRIVER/LAUNCHER SEAM. One lanes module, or the lane never frees itself.
# ---------------------------------------------------------------------------


def test_the_driver_and_the_launcher_hold_one_lanes_module():
    """MEASURED on the first real cycle, and it left the lock behind.

    `lanes.py` carries process-global state: `_OWNED`, the table that decides
    whether a release is ours. Loaded under two names it becomes two objects
    with two tables, and then `repoint_lane_pid` records ownership in one while
    `release_lane` checks the other, finds a mismatch, and refuses. The lock
    survives every cycle and the lane reads RECLAIMABLE for ever.

    The launcher's own docstring predicts exactly this. It still happened,
    because the launcher and its test agreed with each other - both loaded
    lanes by file path - while the DRIVER imports the package. Two agreeing
    parties are not evidence when both derive from the same assumption.
    """
    assert lane_launcher.lanes is lanes, (
        f"the launcher holds {lane_launcher.lanes.__name__!r} and the driver holds "
        f"{lanes.__name__!r}; a re-point recorded in one is invisible to a release "
        f"called on the other"
    )


def test_a_release_after_a_launcher_repoint_actually_removes_the_lock(tmp_path):
    """The behaviour the shared module exists for, end to end on a real lock.

    This is the arm that would have caught it. The identity check above states
    the cause; this one states the CONSEQUENCE, and it would still fail if some
    future change split the modules again by another route.

    A real lock file under `tmp_path` - no OS mutex, no process, no git.
    """
    root = tmp_path / "lanes"
    claim = lanes.try_acquire_lane("queue", run_id="r1", worktree=tmp_path / "wt", root=root)
    token = claim["token"]
    assert claim["ok"], "the lane was not claimed"
    assert Path(token).exists(), "no lock file was written"

    # Re-pointed the way `launch_lane` does it - through the LAUNCHER's binding.
    assert lane_launcher.lanes.repoint_lane_pid(token, WORKER_PID, root=root)
    # Released the way `run_cycle` does it - through the DRIVER's binding.
    released = lanes.release_lane(token, root=root)

    assert released, "the release refused a lock this process owns"
    assert not Path(token).exists(), "the lock survived its own release"


# ---------------------------------------------------------------------------
# House rules, asserted about this file and about the driver.
# ---------------------------------------------------------------------------


DRIVER_SOURCE = (ROOT / "ops" / "loop" / "queue_loop.py").read_text(encoding="utf-8")
THIS_SOURCE = Path(__file__).read_text(encoding="utf-8")


def test_this_test_module_never_takes_a_real_os_mutex():
    """ACCEPTANCE 2, asserted rather than promised.

    The ported repo shipped two tests that took its real driver mutex; they
    went red exactly when the lane was running, which is the one time a suite
    must not.
    """
    # THE NEEDLE IS AN ATTRIBUTE ACCESS, NOT A SUBSTRING, and that is the whole
    # correction this line records. A bare substring scan matched the word
    # `_ledger_lock` inside the NAME of the test two screens up
    # (`test_a_wedged_ledger_lock_...`), so the guard failed on a test that
    # takes no mutex at all. Reaching the real helper requires naming it on the
    # module, which is what this matches - and a guard that cannot tell a call
    # site from a test name is a guard that gets deleted.
    #
    # The pattern is ASSEMBLED so the scan cannot match its own source.
    reached = re.findall(r"queue_loop\.(_driver_" + r"singleton|_ledger_" + r"lock)", THIS_SOURCE)
    assert not reached, f"a test reached for the real mutex helper: {reached}"
    # BALANCED PARENS, not `[^)]*`. The cheap character class stopped at the
    # first `)` it met, which inside `main([..., str(control)], ...)` is the one
    # closing `str(` - so it reported a call that DOES inject a singleton. A
    # guard that manufactures a finding on a compliant call site is worse than
    # no guard, because the finding is what teaches people to ignore it.
    for start in (m.end() for m in re.finditer(r"queue_loop\.main\(", THIS_SOURCE)):
        depth, index = 1, start
        while depth and index < len(THIS_SOURCE):
            depth += {"(": 1, ")": -1}.get(THIS_SOURCE[index], 0)
            index += 1
        call = THIS_SOURCE[start : index - 1]
        assert "singleton=" in call, (
            f"main() was called without an injected singleton: main({call})"
        )


def test_this_test_module_never_spawns_sleeps_or_shells_out():
    banned = (
        "subprocess" + ".",
        "os." + "system",
        "time." + "sleep",
        "importlib." + "import_module",
    )
    body = THIS_SOURCE.split('"""', 2)[-1]
    for token in banned:
        assert token not in body, f"a test reached for {token!r}"


def test_the_driver_never_names_the_banned_powershell_cmdlet_in_code():
    """CLAUDE.md bans it because it hangs the MCP pipe.

    This scans CODE lines only: the docstrings must stay free to explain
    why it is forbidden.
    """
    offenders = [
        (n, line)
        for n, line in enumerate(DRIVER_SOURCE.splitlines(), 1)
        if "Stop-" + "Process" in line
        and not line.lstrip().startswith("#")
        and '"' not in line.split("Stop-" + "Process")[0][-2:]
    ]
    assert not offenders, f"the banned cmdlet appears in code: {offenders}"


def test_the_driver_is_seven_bit_ascii():
    """CLAUDE.md non-negotiable 4, and it has a mechanism behind it.

    PowerShell 5.1 ANSI-decodes a BOM-less script, and a UTF-8 dash inside a
    double-quoted string becomes a character the tokenizer reads as a string
    terminator.
    """
    raw = (ROOT / "ops" / "loop" / "queue_loop.py").read_bytes()
    bad = sorted({byte for byte in raw if byte > MAX_ASCII})
    assert not bad, f"non-ASCII bytes in the driver: {bad}"


def test_the_driver_kills_with_taskkill_and_uses_the_tree_flag():
    """`/T` is not decoration.

    The pid is the powershell WRAPPER and `claude` is its child; killing
    only the wrapper orphans a live worker inside the lane worktree while
    the next cycle fires a second one into it.
    """
    assert '"/T"' in DRIVER_SOURCE
    assert '"taskkill"' in DRIVER_SOURCE


def test_importing_the_driver_creates_nothing_on_disk():
    """Importing the driver must not touch the control plane.

    Anything that renders lane state imports this module, and an import with a
    side effect would make a rendering pass fire a lane.
    """
    # ASSERTED ON THE SOURCE, not on the disk. "the control directory does not
    # exist" is not a property of the module - a previous real run legitimately
    # leaves one behind, so an on-disk check passes vacuously the first time and
    # fails for the wrong reason afterwards. What IS a property of the module is
    # that nothing at import time can create anything, and that is visible in
    # the top-level statements.
    tree = ast.parse(DRIVER_SOURCE)
    executable = [
        node
        for node in tree.body
        if not isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Assign,
                ast.AnnAssign,
                ast.Expr,
                ast.If,
            ),
        )
    ]
    assert not executable, (
        f"top-level statements that are not declarations: {[type(n).__name__ for n in executable]}"
    )
    banned = ("mkdir", "open", "write_text", "write_bytes", "touch", "Popen", "run", "unlink")
    for node in ast.walk(
        ast.Module(
            body=[n for n in tree.body if isinstance(n, (ast.Assign, ast.Expr))], type_ignores=[]
        )
    ):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert name not in banned, (
                f"import-time call to {name!r} - an import that mutated the "
                f"control plane would make a rendering pass fire a lane"
            )


# ===========================================================================
# CS-970 REPAIR - R1. NO NIGHT THAT NEVER COMPLETES A CYCLE MAY RUN THE BUDGET.
#
# Measured by an adversary driving the real `run_loop`: a night whose lane lock
# is held on every cycle gave `cycles_run 12, stopped_by max_cycles,
# outcomes {'lane_held'}, exit 0`. That falsified the module's own stated
# invariant - "a refusal is not a fault inside a cycle, it is the cycle never
# happening". Alternating `lane_held` / `launch_failed` ran the full budget too,
# and so did the alternating `error` / `launch_failed` pattern a previous merge
# accepted as a residual.
#
# The residual ruling is WITHDRAWN, because the same hole was found again
# wearing a different outcome. Enumerating bad outcomes is what let it reopen,
# so the property graded here is the general one and the driver enforces it with
# an allowlist of PRODUCTIVE outcomes rather than a denylist of bad ones.
# ===========================================================================


def _scripted_outcomes(words):
    """Seams that make `run_loop` produce exactly `words`, one word per cycle.

    `acquire_retries` is pinned to 1 so `acquire` is called EXACTLY once per
    cycle - the driver's default of twenty retries would advance the script
    twenty times inside one held-lane cycle and the sequence under test would
    be a different sequence.

    Args:
        words: One `OUTCOME_*` value per cycle, in order.

    Returns:
        Seam overrides for `loop_seams`.
    """
    cursor = {"n": 0}
    current = {"word": queue_loop.OUTCOME_COMPLETED}

    def acquire(_lane, **_kw):
        current["word"] = words[cursor["n"]]
        cursor["n"] += 1
        if current["word"] == queue_loop.OUTCOME_ERROR:
            raise ValueError("a scripted fault")
        if current["word"] == queue_loop.OUTCOME_LANE_HELD:
            return {"ok": False, "refused": "lane_held", "holder": "queue", "pid": 99}
        return {"ok": True, "token": "T"}

    def launch(lane, **kw):
        if current["word"] == queue_loop.OUTCOME_LAUNCH_FAILED:
            return _always_refuses(lane, **kw)
        return {"pid": 1, "log": "l"}

    return {"acquire": acquire, "launch": launch, "acquire_retries": 1}


#: The outcome words the sequence table below scripts. Spelled as the module's
#: own constants so a renamed outcome cannot leave the table scripting a word
#: the driver no longer produces.
_HELD = "lane_held"
_REFUSED = "launch_failed"
_FAULT = "error"
_DONE = "completed"

#: A budget far above every limit, so a sequence that reaches the end of the
#: budget is unambiguous evidence that NO counter fired.
BUDGET = 12


@pytest.mark.parametrize(
    ("script", "budget", "stopped_by", "cycles_run"),
    [
        pytest.param([_HELD] * BUDGET, BUDGET, "no_progress", 3, id="all-lane-held"),
        pytest.param(
            [_REFUSED] * BUDGET, BUDGET, "consecutive_launch_failures", 3, id="all-launch-failed"
        ),
        pytest.param([_FAULT] * BUDGET, BUDGET, "consecutive_errors", 3, id="all-error"),
        pytest.param([_HELD, _REFUSED] * BUDGET, BUDGET, "no_progress", 3, id="held-then-refused"),
        pytest.param(
            [_FAULT, _REFUSED] * BUDGET, BUDGET, "no_progress", 3, id="error-then-refused"
        ),
        pytest.param(
            [_REFUSED, _HELD, _FAULT] * BUDGET, BUDGET, "no_progress", 3, id="three-way-cycle"
        ),
        pytest.param(
            [_HELD, _HELD, _DONE, _HELD, _HELD], 5, "max_cycles", 5, id="one-good-cycle-continues"
        ),
    ],
)
def test_a_night_that_never_completes_a_cycle_cannot_run_the_full_budget(
    tmp_path, script, budget, stopped_by, cycles_run
):
    """THE INVARIANT, graded over SEQUENCES rather than over outcome words.

    The expected stop reasons are spelled as LITERALS, never resolved from the
    module under test: an oracle that reads its expectation from the thing it
    is grading cannot observe that thing changing.

    The last case is the control. A counter that stops a night which DID
    complete a cycle is a worse defect than the one being closed, so a sequence
    with one good cycle in the middle must be allowed to run its whole budget.
    """
    clock = FakeClock()
    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=budget,
            ci_gate=False,
            cycle_log=tmp_path / "l.jsonl",
            control_dir=tmp_path / "control",
            hold=NullHold(),
            **_scripted_outcomes(script),
        )
    )
    # THE DRIVER'S OWN ANSWER, never a value this arm re-derives.
    assert summary["stopped_by"] == stopped_by
    assert summary["cycles_run"] == cycles_run
    rows = (tmp_path / "l.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == cycles_run, "the ledger and the driver disagree about the night"


def test_only_a_completed_cycle_counts_as_progress():
    """THE ALLOWLIST, fenced - widening it must be a VISIBLE edit.

    The hole this repair closes was opened twice by the same mechanism: a
    denylist of outcomes that stop the night, and a new outcome that nobody
    remembered to add to it. An allowlist inverts the default, so a future
    `OUTCOME_*` constant is unproductive until somebody deliberately says
    otherwise - and this arm is what makes saying so deliberate.
    """
    productive = set(queue_loop.PRODUCTIVE_OUTCOMES)
    assert productive == {"completed"}, (
        "the productive set changed; a night made entirely of the added outcome "
        "can now run the whole budget without completing a cycle"
    )
    outcomes = {
        value
        for name, value in vars(queue_loop).items()
        if name.startswith("OUTCOME_") and isinstance(value, str)
    }
    assert productive <= outcomes, "a productive outcome the driver never produces"
    assert outcomes - productive, "every outcome is productive - the counter can never fire"


# ===========================================================================
# CS-970 REPAIR - R2. THE ROW CARRIES THE DRIVER'S OWN LITERAL, NOT THE CALLER'S
# OBJECT.
#
# The existing privacy arm plants a plain `str` and stayed green through both
# attacks below, which is exactly why it did not catch them. Validating by VALUE
# and then rendering the INCOMING OBJECT is the defect; the two are only the
# same thing for a plain `str`.
#
# NOT A LIVE LEAK at the commit this repairs - all twelve raise sites bind plain
# module constants - but the docstring at `_launch_fault` promised a guarantee
# the code did not have, and a promise that is only nearly true is the kind that
# gets relied on.
# ===========================================================================


class ReasonThatLiesAboutEquality(str):
    """A reason whose `__eq__` says yes to everything, so `in` cannot refuse it."""

    def __eq__(self, other: object) -> bool:
        """Say yes to every comparison, so a membership test cannot refuse."""
        return True

    def __ne__(self, other: object) -> bool:
        """The mirror of `__eq__`, so the lie is consistent in both directions."""
        return False

    def __hash__(self) -> int:
        """Hash the REAL data - overriding `__eq__` drops the inherited hash."""
        return hash(str.__str__(self))


class ReasonThatLiesAboutItsText(str):
    """A reason whose DATA is a real member and whose `__str__` is a path.

    The stronger of the two: membership is TRUTHFULLY true, no comparison is
    overridden, and an f-string on a `str` subclass calls `__str__`. Probed, not
    assumed - `f"{obj}"` renders `__str__` for a subclass while rendering the
    raw data for an exact `str`.
    """

    def __str__(self) -> str:
        """Render a path while the object's own data stays a genuine member."""
        return self.planted

    planted = ""


def test_a_reason_that_lies_about_equality_never_reaches_the_row(tmp_path):
    """Attack (a) - membership passed by overriding the comparison itself."""
    clock = FakeClock()
    planted = ReasonThatLiesAboutEquality(str(tmp_path / "cs-lane-queue"))

    # THE CONTROLS FIRST. An arm asserting an absence passes just as happily
    # when the attack never worked in the first place.
    assert planted in queue_loop._LAUNCH_REASONS, (  # noqa: SLF001 - the fence under test
        "the control failed: the planted reason did not pass the membership test"
    )
    assert str(tmp_path) in f"{planted}", "the control failed: the plant rendered no path"

    def fails(_lane, **_kw):
        raise queue_loop.lane_launcher.LaneLaunchError("refused", reason=planted)

    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=fails))
    assert str(tmp_path) not in got["detail"], "a caller-supplied object was rendered into the row"
    assert got["detail"] == "LaneLaunchError", "a fault must still be NAMED by its type"


def test_a_reason_that_lies_about_its_text_never_reaches_the_row(tmp_path):
    """Attack (b) - honest membership, dishonest rendering.

    This one needs no trickery in the comparison at all. The object's DATA is
    `unspecified`, a genuine member; only its `__str__` carries the path. A
    validator that checks the value and then renders the object is defeated by
    an object whose value and rendering differ.
    """
    clock = FakeClock()
    planted = ReasonThatLiesAboutItsText("unspecified")
    planted.planted = str(tmp_path / "cs-lane-queue")

    assert planted in queue_loop._LAUNCH_REASONS, (  # noqa: SLF001 - the fence under test
        "the control failed: the planted reason is not a genuine member"
    )
    assert str(tmp_path) in f"{planted}", "the control failed: the plant rendered no path"

    def fails(_lane, **_kw):
        raise queue_loop.lane_launcher.LaneLaunchError("refused", reason=planted)

    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=fails))
    assert str(tmp_path) not in got["detail"], "a caller-supplied object was rendered into the row"
    assert Path(got["detail"]).drive == "", f"a rooted path survived: {got['detail']!r}"


def test_a_plain_string_reason_still_reaches_the_row_whole():
    """THE CONTROL FOR BOTH ATTACKS ABOVE.

    A fence that rejected every reason would pass both arms above and be
    useless. This is the arm that says the fence still lets the real thing
    through - and it must keep passing for the SAME code that rejects the two
    subclasses.
    """
    clock = FakeClock()

    def fails(_lane, **_kw):
        raise queue_loop.lane_launcher.LaneLaunchError(
            "refused", reason=lane_launcher.REASON_GIT_NOT_FOUND
        )

    got = queue_loop.run_cycle(1, **cycle_seams(clock, launch=fails))
    assert got["detail"] == "LaneLaunchError: git_not_found"


# ===========================================================================
# CS-970 REPAIR - R3. THE EXIT-CODE ARM HAD NO ORACLE.
#
# `assert code == getattr(queue_loop, expected)` resolved the expected value
# FROM THE CONSTANT IT WAS GRADING, so it could never observe that constant
# changing. Proof: setting EXIT_CONSECUTIVE_LAUNCH_FAILURES to 5 collides it
# with EXIT_CONSECUTIVE_ERRORS and the arm stayed GREEN while two stop reasons
# collapsed onto one number - the precise failure this feature was built to
# prevent.
# ===========================================================================


def test_no_two_stop_reasons_share_one_exit_code():
    """DISTINCTNESS, asserted once over the whole table.

    The per-reason arm below pins each number, but a pinned number is a claim
    about one row. A collision is a claim about the table, and nothing in this
    repo asserted it before this arm.
    """
    table = queue_loop._STOP_EXIT  # noqa: SLF001 - the table under test
    codes = list(table.values())
    distinct = len(set(codes))
    total = len(table)
    assert distinct == total, f"two stop reasons share one exit code: {sorted(codes)}"
    assert queue_loop.EXIT_OK not in codes, (
        "a stop reason in this table maps to the success code, so a launcher "
        "cannot tell that night from a good one"
    )


def test_every_stop_reason_constant_has_a_number():
    """A new stop reason without an exit code must REDDEN, not exit 0 quietly.

    `_STOP_EXIT.get(stopped, EXIT_OK)` silently yields success for a stop reason
    the table does not list, which contradicts that table's own comment. The
    sweep is over the module's `STOPPED_BY_*` constants, so adding one without a
    number fails here rather than in the morning.
    """
    #: The only stop reason that legitimately means EXIT_OK: the night ran its
    #: whole budget and ended the way it was asked to.
    means_success = {"max_cycles"}
    declared = {
        value
        for name, value in vars(queue_loop).items()
        if name.startswith("STOPPED_BY_") and isinstance(value, str)
    }
    assert declared, "no stop reason constants were found - the sweep would be vacuous"
    numbered = set(queue_loop._STOP_EXIT) | means_success  # noqa: SLF001 - the table under test
    unnumbered = sorted(declared - numbered)
    assert unnumbered == [], f"a stop reason carries no exit code and would exit 0: {unnumbered}"


def test_the_launch_fault_row_never_renders_the_caller_s_object():
    """A STRUCTURAL ORACLE, because no VALUE can kill this mutant.

    With `type(reason) is str` in place, both subclass attacks are already
    rejected, so replacing the index substitution with a bare `{reason}` changes
    the behaviour of no input the two arms above can construct. That makes it an
    EQUIVALENT mutant to a value oracle - and an equivalent mutant is not a
    surviving one, it is an unmeasured property.

    The property is therefore measured where it lives: in the source. The
    sentence in the docstring is "the row carries a string the driver itself
    contains", and the only way that sentence stays literally true is if the
    incoming object is never interpolated. The two halves are defence in depth
    against different attacks - the type check against an overridden `__eq__`,
    the substitution against an overridden `__str__` - and each must be graded
    by something, or the next edit drops the one no test can see.
    """
    tree = ast.parse(DRIVER_SOURCE)
    body = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_launch_fault"
    ]
    assert len(body) == 1, "_launch_fault was renamed or duplicated - the sweep is not vacuous"
    # A POSITIVE SHAPE, not a blacklist of bad ones. `reason` may legitimately
    # appear INSIDE the rendered expression - as the index being looked up - so
    # "does the word appear" is the wrong question. The question is what the
    # OUTERMOST rendered expression is, and the only answer that keeps the
    # docstring's sentence true is an element of this module's own tuple.
    wrong: list[str] = []
    substituted = 0
    for node in ast.walk(body[0]):
        if not isinstance(node, ast.FormattedValue):
            continue
        mentions = any(
            isinstance(inner, ast.Name) and inner.id == "reason" for inner in ast.walk(node.value)
        )
        if not mentions:
            continue
        value = node.value
        ok = (
            isinstance(value, ast.Subscript)
            and isinstance(value.value, ast.Name)
            and value.value.id == "_LAUNCH_REASONS"
        )
        if ok:
            substituted += 1
        else:
            wrong.append(ast.unparse(value))
    assert wrong == [], (
        "the caller's own object is interpolated into the row; validating by "
        f"VALUE and rendering the OBJECT are not the same thing: {wrong}"
    )
    assert substituted == 1, (
        "the index substitution is gone from _launch_fault - the sweep above "
        "would then be vacuously true of a function that renders nothing"
    )
