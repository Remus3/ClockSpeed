"""CS-917 - the tier1 lane's growth and its run-to-run jitter are measured, not asserted.

THE DEFECT THIS MODULE ADDRESSES. CS-896 watches the tier1 lane's DURATION
against a budget and a ceiling. Nothing watched its GROWTH RATE, and nothing
graded the WARN BAND against the lane's own jitter - so a red was reachable
having never warned, and three re-derivations of that band each sized it from a
noise figure their own next reading falsified.

WHY THE NOISE FIGURE IS A MAX CONSECUTIVE STEP AND NOT A SERIES RANGE. The
ordering guarantee CS-896's leaf asks for is that growth be VISIBLE before it is
FATAL: a reading must land in the warn band rather than jumping the band
outright. What defeats that is one RUN-TO-RUN jump wider than the band. A
series range over days conflates real growth with jitter and is the figure that
was falsified three times; a max consecutive step is an observed maximum of
differences and assumes no distribution at all, which is what this item's clause
demands over a heterogeneous runner pool.

WHY A RECORD RATHER THAN A LIVE READ. No test on this project reaches the
network. `tools/tier1_growth.py` refreshes a tracked record BY HAND from the
API - like `tools/facts_probe.py` and `tools/tier2_headroom.py`, never from a
hook - and the arms below grade that record offline.

WHAT IS PINNED TWO WAYS AND WHY. The set of jobs whose band is NARROWER than
their own jitter is pinned as a literal here and computed in the tool. That set
is not empty today, and pinning it is the ratchet: a job that degrades into it
is red at once, and a job that improves out of it is ALSO red, which forces the
literal down rather than letting a met condition sit unrecorded.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_SOURCE = REPO_ROOT / "tools" / "tier1_growth.py"

#: PINNED TWO WAYS. The tool must bind each of these as a literal.
EXPECTED_JITTER_RATCHET_SECONDS = 129
EXPECTED_MINIMUM_READINGS_PER_JOB = 5
EXPECTED_RECORD_FIELDS = (
    "run_id",
    "head_sha",
    "job",
    "conclusion",
    "started_at",
    "completed_at",
)

#: The synthetic workflow's levels. Their DIFFERENCE is what every arm turns on,
#: and it is deliberately the same band the shipped workflow declares, so a
#: synthetic verdict reads across to the real one.
BUDGET = 420
CEILING = 480

#: Figures the arms below assert on. Named, so a comparison in an arm is never a
#: bare literal and a change to one has exactly one place to move.
STEP_IN_A_SAWTOOTH = 40
CREEP_RANGE = 200
CREEP_STEP = 20
HETEROGENEOUS_STEP = 98
HETEROGENEOUS_STEP_REORDERED = 95
TIED_STEP = 129
TIED_PAIR_STEP = 82
OVER_BAND_STEP = 70
EXACTLY_THE_BAND = CEILING - BUDGET

#: Bounds the two `git` calls in the anti-transcription arm below. An unbounded
#: child cannot fail the test that owns it - it burns the CI job's whole budget
#: until the lane is cancelled, which is evidence of nothing (CS-896).
GIT_TIMEOUT_SECONDS = 60

#: THE ORDERING RATCHET. Every job whose warn band is narrower than its own
#: measured jitter, as the shipped record stands. Two-way: see the docstring.
EXPECTED_ORDERING_UNMET = ("gates, lint, types, tests",)


def _load_tool() -> ModuleType:
    """Load the tool by PATH, because tools/ is not an importable package.

    Returns:
        The loaded module.

    Raises:
        ImportError: The source could not be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_tier1_growth", TOOL_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {TOOL_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOL = _load_tool()

WORKFLOW_TEXT = (REPO_ROOT / TOOL.WORKFLOW_RELATIVE).read_text(encoding="utf-8")
SHIPPED_RECORD = json.loads((REPO_ROOT / TOOL.RECORD_RELATIVE).read_text(encoding="ascii"))


# ---------------------------------------------------------------------------
# Synthetic records - every plant below is built from this, never from the
# shipped record, so an arm cannot pass by accident of real data.
# ---------------------------------------------------------------------------

_BASE = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)


def _stamp(offset_seconds: int) -> str:
    """One recorded timestamp.

    Args:
        offset_seconds: Seconds after the base instant.

    Returns:
        The API's timestamp spelling.
    """
    return (_BASE + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(index: int) -> str:
    """A well-formed head sha standing for commit ``index``.

    Args:
        index: The commit's distance from the window's oldest.

    Returns:
        Forty hex characters.
    """
    return f"{index:040x}"


def _record(job_durations: dict[str, list[int]], *, conclusion: str = "success") -> dict[str, Any]:
    """A synthetic record placing one run per commit, in commit order.

    Args:
        job_durations: Job display name to its durations, oldest run first.
        conclusion: The conclusion every row carries.

    Returns:
        A record in the tool's shape.
    """
    runs = max(len(values) for values in job_durations.values())
    rows = []
    for job, values in job_durations.items():
        for index, duration in enumerate(values):
            start = index * 3600
            rows.append(
                {
                    "run_id": 1000 + index,
                    "head_sha": _sha(index),
                    "job": job,
                    "conclusion": conclusion,
                    "started_at": _stamp(start),
                    "completed_at": _stamp(start + duration),
                }
            )
    return {
        "window": {
            "oldest_sha": _sha(0),
            "newest_sha": _sha(runs - 1),
            "commits": runs - 1,
        },
        "commits": {_sha(index): index for index in range(runs)},
        "jobs": rows,
    }


def _workflow(budget: int, ceiling: int, jobs: tuple[str, ...]) -> str:
    """A minimal workflow text declaring the levels and the job names.

    Args:
        budget: Seconds.
        ceiling: Seconds.
        jobs: The display names.

    Returns:
        Parseable workflow YAML.
    """
    lines = [
        "name: tier1",
        "env:",
        f"  TIER1_BUDGET_SECONDS: '{budget}'",
        f"  TIER1_CEILING_SECONDS: '{ceiling}'",
        "jobs:",
    ]
    for index, job in enumerate(jobs):
        lines.extend(
            [
                f"  job{index}:",
                f"    name: {job}",
                "    runs-on: ubuntu-latest",
                "    timeout-minutes: 10",
                "    steps:",
                "      - run: echo hi",
            ]
        )
    return "\n".join(lines) + "\n"


_FLAT = [300, 305, 302, 308, 301, 306]
_FLAT_JOBS = ("only job",)


def _flat_case(durations: list[int] | None = None) -> tuple[dict[str, Any], str]:
    """A green synthetic pair: one job, jitter well inside the band.

    Args:
        durations: Override the durations.

    Returns:
        The record and the workflow text.
    """
    values = list(_FLAT if durations is None else durations)
    return _record({_FLAT_JOBS[0]: values}), _workflow(BUDGET, CEILING, _FLAT_JOBS)


# ---------------------------------------------------------------------------
# The floor. Every plant below is worthless if this is not green.
# ---------------------------------------------------------------------------


def test_the_synthetic_floor_is_green_or_every_plant_below_proves_nothing() -> None:
    record, workflow = _flat_case()
    assert TOOL.grade(record, workflow) == []


def test_the_shipped_record_grades_clean_against_the_shipped_workflow() -> None:
    offences = TOOL.grade(SHIPPED_RECORD, WORKFLOW_TEXT)
    assert offences == []


def test_the_shipped_record_covers_every_job_the_workflow_expands_to() -> None:
    declared = set(TOOL.declared_jobs(WORKFLOW_TEXT))
    recorded = {row["job"] for row in SHIPPED_RECORD["jobs"]}
    assert declared == recorded


# ---------------------------------------------------------------------------
# The noise figure - what it is, and what it is NOT
# ---------------------------------------------------------------------------


def test_the_noise_figure_is_the_largest_step_between_consecutive_runs() -> None:
    assert TOOL.jitter([300, 320, 300, 340]) == STEP_IN_A_SAWTOOTH


def test_a_wide_series_range_with_small_steps_is_not_noise() -> None:
    """A lane that CREEPS 200s in ten small steps has jitter, not range, at issue.

    The range is what three falsified re-derivations used. A criterion that
    reads this series as 200s of noise would demand a band no cutoff can hold,
    and would do it over a lane whose every run-to-red transition is visible.
    """
    creeping = [300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500]
    assert max(creeping) - min(creeping) == CREEP_RANGE
    assert TOOL.jitter(creeping) == CREEP_STEP


def test_the_figure_is_an_observed_step_and_not_a_bound_from_a_fitted_spread() -> None:
    """Two readings 98s below a tight cluster - the heterogeneous-pool shape.

    A normal tolerance bound over this sample moves with the sample's standard
    deviation and gave 452s at n=3 and then 564s at n=4 on this project's own
    readings, because the sample is not from one distribution. The figure here
    is an observed difference: it is whatever step was actually taken, and no
    spread, variance or quantile of a fitted distribution enters it.
    """
    heterogeneous = [358, 359, 360, 262, 357]
    assert TOOL.jitter(heterogeneous) == HETEROGENEOUS_STEP
    # The same multiset in a different ORDER has a different figure, which a
    # distribution-based criterion cannot express: order is the whole point.
    assert TOOL.jitter([262, 357, 358, 359, 360]) == HETEROGENEOUS_STEP_REORDERED


def test_a_single_reading_has_no_step_and_therefore_no_figure() -> None:
    assert TOOL.jitter([300]) is None
    assert TOOL.jitter([]) is None
    assert TOOL.jitter_over([]) is None


def _reading(stamp_offset: int, duration: int, run_id: int) -> Any:
    """One reading at a stated instant.

    Args:
        stamp_offset: Seconds after the base instant.
        duration: The job's duration.
        run_id: The run id.

    Returns:
        The tool's reading tuple.
    """
    return TOOL.Reading(_stamp(stamp_offset), duration, run_id, _sha(run_id))


def test_two_readings_starting_in_the_same_second_do_not_let_a_sort_pick_the_figure() -> None:
    """The measured defect: one tiebreak gave 101s and the other 129s.

    A batched push starts several runs of a job in the same second and the API
    reports one started_at for both, so their order is not a fact. The figure
    takes the widest step available under ANY ordering of the tie, which is the
    only spelling that does not move when a sort is stable in a different way.
    """
    tied = [
        _reading(0, 395, 1),
        _reading(3600, 287, 2),
        _reading(3600, 369, 3),
        _reading(7200, 240, 4),
    ]
    swapped = [tied[0], tied[2], tied[1], tied[3]]
    assert TOOL.jitter_over(tied) == TIED_STEP
    assert TOOL.jitter_over(swapped) == TIED_STEP
    # And the tie's own two members count as a step, since an ordering can put
    # them next to each other.
    assert TOOL.jitter_over([_reading(0, 287, 1), _reading(0, 369, 2)]) == TIED_PAIR_STEP


# ---------------------------------------------------------------------------
# The ordering guarantee, pinned two ways
# ---------------------------------------------------------------------------


def test_the_ordering_verdict_over_the_shipped_record_equals_the_pinned_set() -> None:
    computed = TOOL.ordering_unmet(SHIPPED_RECORD, WORKFLOW_TEXT)
    assert tuple(computed) == EXPECTED_ORDERING_UNMET


def test_a_job_whose_band_covers_its_jitter_is_not_in_the_unmet_set() -> None:
    record, workflow = _flat_case()
    assert TOOL.ordering_unmet(record, workflow) == []


def test_a_job_whose_jitter_exceeds_its_band_is_in_the_unmet_set() -> None:
    record, workflow = _flat_case([300, 305, 302, 308, 301, 371])
    assert TOOL.jitter([300, 305, 302, 308, 301, 371]) == OVER_BAND_STEP
    assert TOOL.ordering_unmet(record, workflow) == [_FLAT_JOBS[0]]


def test_jitter_exactly_equal_to_the_band_still_meets_the_guarantee() -> None:
    """A step of exactly the band lands ON the ceiling, which warns before it reds."""
    values = [300, 305, 302, 308, 301, 361]
    record, workflow = _flat_case(values)
    assert TOOL.jitter(values) == EXACTLY_THE_BAND
    assert TOOL.ordering_unmet(record, workflow) == []


def test_the_band_is_read_from_the_workflow_rather_than_transcribed() -> None:
    values = [300, 305, 302, 308, 301, 371]
    record = _record({_FLAT_JOBS[0]: values})
    narrow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    wide = _workflow(BUDGET, CEILING + 20, _FLAT_JOBS)
    assert TOOL.ordering_unmet(record, narrow) == [_FLAT_JOBS[0]]
    assert TOOL.ordering_unmet(record, wide) == []


def test_a_pinned_unmet_set_that_no_longer_matches_is_an_offence_in_both_directions() -> None:
    record, workflow = _flat_case()
    degraded = _record({_FLAT_JOBS[0]: [300, 305, 302, 308, 301, 371]})
    assert TOOL.grade(record, workflow, unmet=(_FLAT_JOBS[0],)) != []
    assert TOOL.grade(degraded, workflow, unmet=()) != []
    assert TOOL.grade(degraded, workflow, unmet=(_FLAT_JOBS[0],)) == []


# ---------------------------------------------------------------------------
# The ratchet on the figure itself
# ---------------------------------------------------------------------------


def test_a_jitter_past_the_stated_ratchet_turns_the_guard_red() -> None:
    values = [300, 305, 302, 308, 301, 301 + EXPECTED_JITTER_RATCHET_SECONDS + 1]
    record = _record({_FLAT_JOBS[0]: values})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    offences = TOOL.grade(record, workflow, unmet=(_FLAT_JOBS[0],))
    assert any("ratchet" in offence for offence in offences)


def test_a_jitter_exactly_at_the_ratchet_is_not_yet_red() -> None:
    values = [300, 305, 302, 308, 301, 301 + EXPECTED_JITTER_RATCHET_SECONDS]
    record = _record({_FLAT_JOBS[0]: values})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    assert TOOL.jitter(values) == EXPECTED_JITTER_RATCHET_SECONDS
    assert TOOL.grade(record, workflow, unmet=(_FLAT_JOBS[0],)) == []


# ---------------------------------------------------------------------------
# What counts as a reading
# ---------------------------------------------------------------------------


def test_a_failed_job_is_not_a_reading() -> None:
    """A tier1 job runs pytest with -x, so a failure stops early.

    Its duration is a lower bound on the lane's length and including it would
    UNDERSTATE both the worst reading and the jitter. Three runs in the shipped
    record failed almost at once.
    """
    record = _record({_FLAT_JOBS[0]: _FLAT}, conclusion="failure")
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    offences = TOOL.grade(record, workflow)
    assert any("readings" in offence for offence in offences)
    assert TOOL.readings(record)[_FLAT_JOBS[0]] == []


def test_too_few_readings_for_a_job_is_an_offence() -> None:
    short = _FLAT[: EXPECTED_MINIMUM_READINGS_PER_JOB - 1]
    record = _record({_FLAT_JOBS[0]: short})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    assert any("readings" in offence for offence in TOOL.grade(record, workflow))


def test_one_run_copied_five_times_is_one_reading_not_five() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    for row in record["jobs"]:
        row["run_id"] = 1000
        row["head_sha"] = _sha(0)
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    assert any("readings" in offence for offence in TOOL.grade(record, workflow))


# ---------------------------------------------------------------------------
# Growth per commit
# ---------------------------------------------------------------------------


def test_growth_per_commit_is_exact_and_reads_the_commit_axis() -> None:
    """One second per commit, planted, with one run per commit."""
    record = _record({_FLAT_JOBS[0]: [300, 301, 302, 303, 304, 305]})
    growth = TOOL.growth_per_commit(record)
    assert growth[_FLAT_JOBS[0]] == Fraction(1)


def test_growth_is_measured_against_commits_and_not_against_run_ordinals() -> None:
    """Halve the commit axis and the per-commit figure doubles."""
    record = _record({_FLAT_JOBS[0]: [300, 302, 304, 306, 308, 310]})
    assert TOOL.growth_per_commit(record)[_FLAT_JOBS[0]] == Fraction(2)
    for row in record["jobs"]:
        record["commits"][row["head_sha"]] = record["commits"][row["head_sha"]] * 2
    record["window"]["commits"] = max(record["commits"].values())
    assert TOOL.growth_per_commit(record)[_FLAT_JOBS[0]] == Fraction(1)


def test_a_reading_whose_commit_distance_is_unrecorded_is_an_offence() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    del record["commits"][_sha(3)]
    assert any("commit distance" in offence for offence in TOOL.grade(record, workflow))


def test_a_window_whose_commit_count_disagrees_with_its_distances_is_an_offence() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    record["window"]["commits"] = record["window"]["commits"] + 7
    assert any("window" in offence for offence in TOOL.grade(record, workflow))


def test_the_recorded_commit_distances_agree_with_this_repository() -> None:
    """Skip-if-absent, because a shallow clone does not carry the ancestry.

    This is the anti-transcription arm: the stored distances are captured from
    git at refresh time and nothing else re-derives them, so without this a
    hand-edited distance would be invisible.
    """
    oldest = SHIPPED_RECORD["window"]["oldest_sha"]
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{oldest}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if probe.returncode != 0:
        pytest.skip("this checkout does not carry the recorded window's oldest commit")
    for sha, recorded in SHIPPED_RECORD["commits"].items():
        seen = subprocess.run(
            ["git", "rev-list", "--count", f"{oldest}..{sha}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if seen.returncode != 0:
            pytest.skip(f"this checkout does not carry {sha[:8]}")
        assert int(seen.stdout.strip()) == recorded, sha


# ---------------------------------------------------------------------------
# Record integrity
# ---------------------------------------------------------------------------


def test_a_row_carrying_an_unlisted_field_turns_the_guard_red() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    record["jobs"][0]["runner_label"] = "ubuntu-latest"
    assert any("field" in offence for offence in TOOL.grade(record, workflow))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("run_id", "1000"),
        ("head_sha", "nope"),
        ("job", 7),
        ("conclusion", None),
        ("started_at", "2026-09-17 12:00:00"),
        ("completed_at", ""),
    ],
)
def test_a_malformed_row_turns_the_guard_red(field: str, value: object) -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    record["jobs"][0][field] = value
    assert TOOL.grade(record, workflow) != []


def test_a_row_that_completes_before_it_starts_turns_the_guard_red() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    record["jobs"][0]["completed_at"] = _stamp(-30)
    assert TOOL.grade(record, workflow) != []


def test_a_record_missing_a_declared_job_turns_the_guard_red() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    workflow = _workflow(BUDGET, CEILING, (*_FLAT_JOBS, "a second job"))
    assert any("a second job" in offence for offence in TOOL.grade(record, workflow))


def test_a_record_naming_a_job_the_workflow_does_not_declare_turns_the_guard_red() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT, "ghost job": _FLAT})
    workflow = _workflow(BUDGET, CEILING, _FLAT_JOBS)
    assert any("ghost job" in offence for offence in TOOL.grade(record, workflow))


def test_a_workflow_without_the_two_levels_turns_the_guard_red() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    # The ceiling is dropped BY KEY rather than by writing its declaration out
    # here: guard (k) of tools/drift_guard.py refuses a tier 1 level stated
    # anywhere but the workflow, and a test fixture is not an exemption.
    declared = _workflow(BUDGET, CEILING, _FLAT_JOBS).splitlines()
    stripped = "\n".join(line for line in declared if TOOL.CEILING_KEY not in line) + "\n"
    assert TOOL.grade(record, stripped) != []


def test_a_ceiling_below_the_budget_turns_the_guard_red() -> None:
    record = _record({_FLAT_JOBS[0]: _FLAT})
    inverted = _workflow(CEILING, BUDGET, _FLAT_JOBS)
    assert TOOL.grade(record, inverted) != []


# ---------------------------------------------------------------------------
# The report, the parser, the refresh and the entry point
# ---------------------------------------------------------------------------


def test_the_report_names_every_job_its_growth_and_its_verdict() -> None:
    text = TOOL.report(SHIPPED_RECORD, WORKFLOW_TEXT)
    for job in TOOL.declared_jobs(WORKFLOW_TEXT):
        assert job in text
    assert "per commit" in text
    for job in EXPECTED_ORDERING_UNMET:
        assert job in text
    assert SHIPPED_RECORD["window"]["oldest_sha"][:8] in text


def test_the_report_is_seven_bit_ascii() -> None:
    TOOL.report(SHIPPED_RECORD, WORKFLOW_TEXT).encode("ascii")


def test_the_parser_keeps_the_allowlisted_fields_only() -> None:
    payload = {
        "total_count": 2,
        "jobs": [
            {
                "run_id": 42,
                "head_sha": _sha(1),
                "name": _FLAT_JOBS[0],
                "conclusion": "success",
                "status": "completed",
                "started_at": _stamp(0),
                "completed_at": _stamp(300),
                "html_url": "https://example.invalid/owner/repo/actions/runs/42",
            },
            {
                "run_id": 42,
                "name": "still running",
                "status": "in_progress",
            },
        ],
    }
    assert TOOL.parse_jobs_payload(payload) == [
        {
            "run_id": 42,
            "head_sha": _sha(1),
            "job": _FLAT_JOBS[0],
            "conclusion": "success",
            "started_at": _stamp(0),
            "completed_at": _stamp(300),
        }
    ]


def test_the_parser_refuses_a_payload_that_is_not_a_jobs_listing() -> None:
    with pytest.raises(ValueError, match="jobs listing"):
        TOOL.parse_jobs_payload({"message": "Not Found"})


def test_the_parser_refuses_a_truncated_page() -> None:
    with pytest.raises(ValueError, match="one page"):
        TOOL.parse_jobs_payload({"total_count": 9, "jobs": []})


def test_the_record_fields_are_what_this_module_pins() -> None:
    assert TOOL.RECORD_FIELDS == EXPECTED_RECORD_FIELDS


def test_the_ratchet_and_the_reading_floor_are_what_this_module_pins() -> None:
    assert TOOL.JITTER_RATCHET_SECONDS == EXPECTED_JITTER_RATCHET_SECONDS
    assert TOOL.MINIMUM_READINGS_PER_JOB == EXPECTED_MINIMUM_READINGS_PER_JOB
    assert tuple(TOOL.ORDERING_UNMET) == EXPECTED_ORDERING_UNMET


def test_main_exits_non_zero_over_a_red_tree_and_zero_over_a_green_one(tmp_path: Path) -> None:
    record, workflow = _flat_case()
    (tmp_path / "tools").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / TOOL.WORKFLOW_RELATIVE).write_text(workflow, encoding="ascii")
    target = tmp_path / TOOL.RECORD_RELATIVE
    target.write_text(json.dumps(record) + "\n", encoding="ascii")
    assert TOOL.grade_tree(tmp_path, unmet=()) == []
    record["jobs"][0]["conclusion"] = "cancelled"
    target.write_text(json.dumps(record) + "\n", encoding="ascii")
    assert TOOL.grade_tree(tmp_path, unmet=()) != []


def test_grade_tree_is_red_when_the_record_is_absent(tmp_path: Path) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / TOOL.WORKFLOW_RELATIVE).write_text(
        _workflow(BUDGET, CEILING, _FLAT_JOBS), encoding="ascii"
    )
    assert TOOL.grade_tree(tmp_path, unmet=()) != []


def test_a_refresh_writes_the_parsed_rows_through_injected_seams(tmp_path: Path) -> None:
    """The refresh is the only network path and the only git path; both injected."""
    (tmp_path / "tools").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / TOOL.WORKFLOW_RELATIVE).write_text(
        _workflow(BUDGET, CEILING, _FLAT_JOBS), encoding="ascii"
    )
    calls: list[list[str]] = []

    def fetch(args: list[str]) -> str:
        calls.append(args)
        if args[0] == "run":
            return json.dumps(
                [
                    {"databaseId": 1, "status": "completed"},
                    {"databaseId": 2, "status": "in_progress"},
                    {"databaseId": 3, "status": "completed"},
                ]
            )
        run_id = 1 if "runs/1/" in args[1] else 3
        index = 0 if run_id == 1 else 1
        return json.dumps(
            {
                "total_count": 1,
                "jobs": [
                    {
                        "run_id": run_id,
                        "head_sha": _sha(index),
                        "name": _FLAT_JOBS[0],
                        "conclusion": "success",
                        "status": "completed",
                        "started_at": _stamp(index * 3600),
                        "completed_at": _stamp(index * 3600 + 300),
                    }
                ],
            }
        )

    def distance(root: Path, oldest: str, sha: str) -> int:
        assert root == tmp_path
        return 0 if sha == oldest else 4

    written = TOOL.refresh(tmp_path, runs=2, fetch=fetch, distance=distance)
    assert written == tmp_path / TOOL.RECORD_RELATIVE
    record = json.loads(written.read_text(encoding="ascii"))
    assert [row["run_id"] for row in record["jobs"]] == [1, 3]
    assert record["commits"] == {_sha(0): 0, _sha(1): 4}
    assert record["window"] == {"oldest_sha": _sha(0), "newest_sha": _sha(1), "commits": 4}
    assert [args[0] for args in calls] == ["run", "api", "api"]
