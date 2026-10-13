"""CS-1124 - every tier2 job is graded against a stated fraction of its OWN timeout.

THE DEFECT THIS MODULE CLOSES. `timeout-minutes` on a tier2 job is a runaway
cutoff, and a job that crosses it is CANCELLED - which reports no failing test,
names no number, and reads to the headless lane as `ci_red`, stopping it. The
Windows clean-checkout probe was cancelled three times in one evening after its
green runs had been creeping toward the cutoff for days with nothing red.

THE SHAPE, AND WHY IT IS A RECORD RATHER THAN A LIVE READ. No test on this
project reaches the network, so no arm here may ask GitHub how long a job took.
`tools/tier2_headroom.py` refreshes a tracked record BY HAND from the API
(like `tools/facts_probe.py`, never a hook) and the guard below grades that
record. The DURATIONS are derived from the recorded timestamps, the TIMEOUTS
are read from the parsed workflow, and the FRACTION and its basis live beside
each other in the tool. A refresh that shows a job past the fraction is red in
this suite before any run is cancelled, which is the whole point.

WHAT IS NOT CLAIMED. The record is only as recent as its last refresh; nothing
here can know a job slowed down since. That staleness is the price of an
offline suite and is stated rather than hidden; the tool's docstring records why
no offline tie to the last workflow commit is sound.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_SOURCE = REPO_ROOT / "tools" / "tier2_headroom.py"
PAYLOAD_FIXTURE = Path(__file__).resolve().parent / "tier2_jobs_payload.json"

#: THE FRACTION, PINNED TWO WAYS. A change to the tool is red here until this
#: literal moves in the same diff, and the tool must bind it as a literal.
EXPECTED_HEADROOM = Fraction(4, 5)
EXPECTED_MINIMUM_RUNS = 3
EXPECTED_RECORD_FIELDS = (
    "run_id",
    "head_sha",
    "job",
    "conclusion",
    "started_at",
    "completed_at",
)

#: CS-1317 - the four tier2 LEGS the sixth tier1 shard adds, each against the
#: item that added it. Keyed by the EXPANDED LEG NAME, never by a job id: a job id
#: would lift the floor on every leg of `suite` and `clean-checkout-probe`, and the
#: twenty legs already measured would lose theirs. PINNED, so a widening is red
#: here until this literal moves in the same diff.
EXPECTED_PENDING = {
    "full suite (ubuntu-latest, scan shard)": "CS-1317",
    "full suite (windows-latest, scan shard)": "CS-1317",
    "clean-checkout probe (ubuntu-latest, scan shard)": "CS-1317",
    "clean-checkout probe (windows-latest, scan shard)": "CS-1317",
}

#: What the tool's parser must derive from the recorded API payload. Literal, so
#: a parser change and a fixture change both turn this red.
EXPECTED_PARSED_FIXTURE = [
    {
        "run_id": 35201160041,
        "head_sha": "7fde21f3ee616701a8a83cc9cba8c9268a15f56f",
        "job": "full suite (windows-latest)",
        "conclusion": "success",
        "started_at": "2026-09-17T08:42:55Z",
        "completed_at": "2026-09-17T09:06:27Z",
    },
    {
        "run_id": 35201160041,
        "head_sha": "7fde21f3ee616701a8a83cc9cba8c9268a15f56f",
        "job": "clean-checkout probe (windows-latest)",
        "conclusion": "cancelled",
        "started_at": "2026-09-17T08:42:54Z",
        "completed_at": "2026-09-17T09:13:06Z",
    },
]


def _load_tool() -> ModuleType:
    """Load the tool by PATH, because tools/ is not an importable package.

    Returns:
        The loaded module.

    Raises:
        ImportError: The source could not be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_tier2_headroom", TOOL_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {TOOL_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


# ---------------------------------------------------------------------------
# Synthetic trees
# ---------------------------------------------------------------------------

BASE = datetime(2026, 9, 1, 3, 17, 0, tzinfo=UTC)


def workflow_text(suite_timeout: int = 30, audit_timeout: int = 20) -> str:
    """A two-job workflow, one of them a matrix, carrying its own timeouts.

    Args:
        suite_timeout: ``timeout-minutes`` for the matrix job.
        audit_timeout: ``timeout-minutes`` for the plain job.

    Returns:
        The workflow text.
    """
    return (
        "name: tier2\n"
        "jobs:\n"
        "  suite:\n"
        "    name: full suite (${{ matrix.os }})\n"
        "    runs-on: ${{ matrix.os }}\n"
        f"    timeout-minutes: {suite_timeout}\n"
        "    strategy:\n"
        "      matrix:\n"
        "        os: [ubuntu-latest, windows-latest]\n"
        "    steps: []\n"
        "  audits:\n"
        "    name: audit\n"
        "    runs-on: ubuntu-latest\n"
        f"    timeout-minutes: {audit_timeout}\n"
        "    steps: []\n"
    )


def row(job: str, run_id: int, seconds: int) -> dict[str, Any]:
    """One record row for a job that took ``seconds``.

    Args:
        job: The job's display name.
        run_id: The run the job belonged to.
        seconds: The duration to stage.

    Returns:
        The row.
    """
    started = BASE + timedelta(days=run_id)
    completed = started + timedelta(seconds=seconds)
    stamp = "%Y-%m-%dT%H:%M:%SZ"
    return {
        "run_id": run_id,
        "head_sha": f"{run_id:040x}",
        "job": job,
        "conclusion": "success",
        "started_at": started.strftime(stamp),
        "completed_at": completed.strftime(stamp),
    }


JOBS = ("full suite (ubuntu-latest)", "full suite (windows-latest)", "audit")


def record(overrides: dict[str, int] | None = None, runs: int = 3) -> dict[str, Any]:
    """A record every job of :func:`workflow_text` passes, unless overridden.

    Args:
        overrides: Job name to the duration its LAST run should carry.
        runs: How many runs each job has.

    Returns:
        The record.
    """
    staged = overrides or {}
    rows: list[dict[str, Any]] = []
    for run_id in range(1, runs + 1):
        rows.extend(
            row(job, run_id, staged[job] if run_id == runs and job in staged else 600)
            for job in JOBS
        )
    return {"jobs": rows}


def graded(document: dict[str, Any], text: str | None = None) -> list[str]:
    """Grade one record against one workflow.

    Args:
        document: The record.
        text: The workflow text, defaulting to :func:`workflow_text`.

    Returns:
        The offences.
    """
    found: list[str] = tool.grade(document, workflow_text() if text is None else text)
    return found


# ---------------------------------------------------------------------------
# The floor and the shipped tree
# ---------------------------------------------------------------------------


def test_the_floor_is_green_or_every_plant_below_proves_nothing() -> None:
    assert graded(record()) == []


def test_the_shipped_record_grades_clean_against_the_shipped_workflow() -> None:
    """THE ACCEPTANCE-FACING ARM. A red here means a refresh found a job past the fraction."""
    offences = tool.grade_tree(REPO_ROOT)
    assert offences == [], "\n".join(offences)


def test_the_shipped_record_covers_every_job_the_workflow_expands_to() -> None:
    """Every declared job is recorded, bar a PENDING leg (CS-1317), and nothing else is."""
    workflow = (REPO_ROOT / tool.WORKFLOW_RELATIVE).read_text(encoding="utf-8")
    declared = set(tool.declared_jobs(workflow))
    document = json.loads((REPO_ROOT / tool.RECORD_RELATIVE).read_text(encoding="utf-8"))
    recorded = {entry["job"] for entry in document["jobs"]}
    assert declared, "the shipped workflow expanded to no jobs"
    assert sorted(recorded - declared) == []
    assert sorted(declared - recorded - set(EXPECTED_PENDING)) == []


# ---------------------------------------------------------------------------
# The fraction - planted past it, at it, and under it
# ---------------------------------------------------------------------------


def test_a_duration_past_the_fraction_turns_the_guard_red() -> None:
    limit = int(EXPECTED_HEADROOM * 30 * 60)
    offences = graded(record({"full suite (windows-latest)": limit + 1}))
    assert len(offences) == 1, offences
    assert "full suite (windows-latest)" in offences[0]
    assert str(limit + 1) in offences[0], offences[0]


def test_a_duration_exactly_at_the_fraction_is_already_red() -> None:
    limit = int(EXPECTED_HEADROOM * 30 * 60)
    assert len(graded(record({"full suite (windows-latest)": limit}))) == 1


def test_the_control_one_second_under_the_fraction_stays_silent() -> None:
    limit = int(EXPECTED_HEADROOM * 30 * 60)
    assert graded(record({"full suite (windows-latest)": limit - 1})) == []


def test_each_job_is_graded_against_its_own_timeout_not_the_largest() -> None:
    """A 20-minute job at 17 minutes is past 4/5 even though a 30-minute job would not be."""
    offences = graded(record({"audit": 17 * 60}))
    assert len(offences) == 1, offences
    assert "audit" in offences[0]


def test_an_older_run_past_the_fraction_is_red_not_only_the_newest() -> None:
    document = record()
    document["jobs"][1] = row("full suite (windows-latest)", 1, 29 * 60)
    assert len(graded(document)) == 1


def test_the_timeout_is_read_from_the_workflow_rather_than_transcribed() -> None:
    """The same record flips verdict when only the WORKFLOW's timeout moves."""
    document = record({"full suite (windows-latest)": 25 * 60})
    assert len(graded(document, workflow_text(suite_timeout=30))) == 1
    assert graded(document, workflow_text(suite_timeout=40)) == []


# ---------------------------------------------------------------------------
# Coverage of the population - no job escapes by being absent
# ---------------------------------------------------------------------------


def test_a_record_missing_a_job_turns_the_guard_red() -> None:
    document = record()
    document["jobs"] = [entry for entry in document["jobs"] if entry["job"] != "audit"]
    offences = graded(document)
    assert any("audit" in offence for offence in offences), offences


def test_a_record_naming_a_job_the_workflow_does_not_declare_turns_the_guard_red() -> None:
    document = record()
    document["jobs"].append(row("retired job", 9, 60))
    offences = graded(document)
    assert any("retired job" in offence for offence in offences), offences


def test_a_job_with_too_few_runs_turns_the_guard_red() -> None:
    document = record(runs=EXPECTED_MINIMUM_RUNS - 1)
    assert len(graded(document)) == len(JOBS)


def test_one_run_copied_three_times_is_one_run_not_three() -> None:
    """The floor counts DISTINCT run ids; duplicated rows add no sample."""
    document = record()
    audit_first = next(entry for entry in document["jobs"] if entry["job"] == "audit")
    document["jobs"] = [entry for entry in document["jobs"] if entry["job"] != "audit"]
    document["jobs"].extend(dict(audit_first) for _ in range(EXPECTED_MINIMUM_RUNS))
    offences = graded(document)
    assert len(offences) == 1, offences
    assert "audit" in offences[0]


@pytest.mark.parametrize(
    ("conclusion", "seconds", "why"),
    [
        ("skipped", 5, "a skipped job that still took seconds"),
        ("success", 0, "a zero-second job that reports success"),
    ],
)
def test_a_row_that_did_not_run_does_not_count_toward_the_floor(
    conclusion: str, seconds: int, why: str
) -> None:
    """Two real runs plus one row that did not run is two samples, below the floor.

    ONE EXCLUSION PER PARAMETER, and that is the point: a single plant carrying
    both a skipped row and a zero-second row stays red when EITHER exclusion is
    deleted, so neither was graded on its own. Measured before this split.
    """
    document = record()
    audit_rows = [entry for entry in document["jobs"] if entry["job"] == "audit"]
    hollow = row("audit", audit_rows[2]["run_id"], seconds)
    hollow["conclusion"] = conclusion
    document["jobs"] = [entry for entry in document["jobs"] if entry["job"] != "audit"]
    document["jobs"].extend([audit_rows[0], audit_rows[1], hollow])
    offences = graded(document)
    assert len(offences) == 1, f"{why} counted as a sample: {offences}"
    assert len(offences) == 1, offences
    assert "audit" in offences[0]


def test_a_workflow_job_without_timeout_minutes_turns_the_guard_red() -> None:
    text = workflow_text().replace("    timeout-minutes: 20\n", "")
    offences = graded(record(), text)
    assert any("timeout-minutes" in offence for offence in offences), offences


def test_a_job_name_carrying_an_unexpandable_expression_turns_the_guard_red() -> None:
    text = workflow_text().replace("name: audit", "name: audit (${{ github.ref }})")
    assert graded(record(), text) != []


# ---------------------------------------------------------------------------
# The row shape - an allowlist, so nothing personal rides along
# ---------------------------------------------------------------------------


def test_a_row_carrying_an_unlisted_field_turns_the_guard_red() -> None:
    document = record()
    document["jobs"][0]["html_url"] = "https://github.com/example-owner/example-repo"
    offences = graded(document)
    assert any("html_url" in offence for offence in offences), offences


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("started_at", "yesterday"),
        ("completed_at", "2026-09-01T03:17:00"),
        ("run_id", "35201160041"),
    ],
)
def test_a_malformed_row_turns_the_guard_red(field: str, value: str) -> None:
    document = record()
    document["jobs"][0][field] = value
    assert graded(document) != []


def test_a_row_that_completes_before_it_starts_turns_the_guard_red() -> None:
    document = record()
    document["jobs"][0] = row("full suite (ubuntu-latest)", 1, -5)
    assert graded(document) != []


def test_the_record_fields_are_what_this_module_pins() -> None:
    assert tool.RECORD_FIELDS == EXPECTED_RECORD_FIELDS


# ---------------------------------------------------------------------------
# The parser, on a recorded payload
# ---------------------------------------------------------------------------


def test_the_parser_derives_exactly_the_pinned_rows_from_the_recorded_payload() -> None:
    """The in-progress job is dropped; every API field off the allowlist is dropped."""
    payload = json.loads(PAYLOAD_FIXTURE.read_text(encoding="utf-8"))
    assert tool.parse_jobs_payload(payload) == EXPECTED_PARSED_FIXTURE


def test_the_parser_refuses_a_payload_that_is_not_a_jobs_listing() -> None:
    with pytest.raises(ValueError, match="jobs"):
        tool.parse_jobs_payload({"total_count": 1})


def test_the_parser_refuses_a_truncated_page() -> None:
    """A listing whose total exceeds its page would silently grade part of a run."""
    payload = json.loads(PAYLOAD_FIXTURE.read_text(encoding="utf-8"))
    payload["total_count"] = 99
    with pytest.raises(ValueError, match="page"):
        tool.parse_jobs_payload(payload)


def write_workflow(root: Path, text: str) -> None:
    """Stage ``text`` as the workflow under ``root``.

    Args:
        root: The synthetic repository root.
        text: The workflow text.
    """
    workflow = root / tool.WORKFLOW_RELATIVE
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_bytes(text.encode("ascii"))


#: A workflow declaring both jobs the recorded payload names.
FIXTURE_WORKFLOW = workflow_text() + (
    "  clean-checkout-probe:\n"
    "    name: clean-checkout probe (${{ matrix.os }})\n"
    "    runs-on: ${{ matrix.os }}\n"
    "    timeout-minutes: 30\n"
    "    strategy:\n"
    "      matrix:\n"
    "        os: [ubuntu-latest, windows-latest]\n"
    "    steps: []\n"
)


def test_a_refresh_writes_the_parsed_rows_through_an_injected_fetch(tmp_path: Path) -> None:
    """The refresh path, exercised with no network: the fetch is handed in."""
    write_workflow(tmp_path, FIXTURE_WORKFLOW)
    payload_text = PAYLOAD_FIXTURE.read_text(encoding="utf-8")
    listing = json.dumps(
        [
            {"databaseId": 35201300783, "status": "in_progress"},
            {"databaseId": 35201160041, "status": "completed"},
        ]
    )
    calls: list[list[str]] = []

    def fetch(args: list[str]) -> str:
        calls.append(args)
        return listing if args[:2] == ["run", "list"] else payload_text

    written = tool.refresh(tmp_path, runs=1, fetch=fetch)

    assert written == tmp_path / tool.RECORD_RELATIVE
    document = json.loads(written.read_text(encoding="utf-8"))
    assert document == {"jobs": EXPECTED_PARSED_FIXTURE}
    fetched_runs = [args for args in calls if args[0] == "api"]
    assert len(fetched_runs) == 1, calls
    assert "35201160041" in fetched_runs[0][1], calls


def test_a_refresh_drops_rows_for_jobs_the_workflow_no_longer_declares(tmp_path: Path) -> None:
    """CS-1229 - a renamed job's old rows measure nothing the workflow still runs.

    Kept, they are graded recorded-but-undeclared forever. Dropped, the new names
    are graded by the run floor instead, so a rename is still red until it is
    measured.
    """
    write_workflow(tmp_path, workflow_text())
    payload_text = PAYLOAD_FIXTURE.read_text(encoding="utf-8")
    listing = json.dumps([{"databaseId": 35201160041, "status": "completed"}])

    def fetch(args: list[str]) -> str:
        return listing if args[:2] == ["run", "list"] else payload_text

    written = tool.refresh(tmp_path, runs=1, fetch=fetch)
    document = json.loads(written.read_text(encoding="utf-8"))
    assert document == {"jobs": EXPECTED_PARSED_FIXTURE[:1]}


def test_a_refresh_with_no_workflow_to_filter_by_refuses(tmp_path: Path) -> None:
    def fetch(args: list[str]) -> str:  # pragma: no cover - never reached
        raise AssertionError(args)

    with pytest.raises(ValueError, match="workflow"):
        tool.refresh(tmp_path, runs=1, fetch=fetch)
    assert not (tmp_path / tool.RECORD_RELATIVE).exists()


# ---------------------------------------------------------------------------
# CS-1317 - the PENDING transition: a NEW leg awaiting its first runs
# ---------------------------------------------------------------------------

#: The synthetic leg every pending arm below stages as new, and its sibling leg
#: of the same matrix job, which must keep its run floor throughout.
NEW_LEG = "full suite (windows-latest)"
SIBLING_LEG = "full suite (ubuntu-latest)"


def without_legs(document: dict[str, Any], *legs: str) -> dict[str, Any]:
    """The record with every row of ``legs`` removed.

    Args:
        document: A record.
        legs: The display names whose rows are dropped.

    Returns:
        A new record.
    """
    return {"jobs": [entry for entry in document["jobs"] if entry["job"] not in legs]}


def offending_names(offences: list[str]) -> list[str]:
    """The job or entry each offence opens with, sorted.

    Args:
        offences: The grade's offences.

    Returns:
        The text before each offence's first colon.
    """
    return sorted(offence.split(":")[0] for offence in offences)


def test_a_leg_with_no_runs_is_red_without_a_pending_entry() -> None:
    """The control for every pending arm below."""
    offences = tool.grade(without_legs(record(), NEW_LEG), workflow_text())
    assert offending_names(offences) == [NEW_LEG]


def test_a_pending_leg_below_the_run_floor_is_tolerated() -> None:
    offences = tool.grade(without_legs(record(), NEW_LEG), workflow_text(), {NEW_LEG: "CS-0"})
    assert offences == []


def test_a_pending_leg_lifts_the_floor_on_that_leg_alone() -> None:
    """THE ONE CHANGE FROM CS-1229: keyed by LEG, so a sibling leg keeps its floor.

    CS-1229 keyed its table by job id, which lifted the floor on every leg of the
    job. Here the sibling leg of the same matrix job is unrecorded too, and it is
    still red.
    """
    document = without_legs(record(), NEW_LEG, SIBLING_LEG)
    offences = tool.grade(document, workflow_text(), {NEW_LEG: "CS-0"})
    assert offending_names(offences) == [SIBLING_LEG]


def test_a_pending_entry_keyed_by_a_job_id_is_red_and_lifts_nothing() -> None:
    """The CS-1229 key shape is refused: a job id names no leg."""
    offences = tool.grade(without_legs(record(), NEW_LEG), workflow_text(), {"suite": "CS-0"})
    floor = [offence for offence in offences if offence.startswith(NEW_LEG)]
    entry = [offence for offence in offences if "'suite'" in offence]
    assert (len(floor), len(entry)) == (1, 1), offences
    assert sorted(offences) == sorted(floor + entry), offences


def test_a_pending_leg_is_still_graded_against_the_fraction() -> None:
    """Pending lifts the run floor only; a recorded run past the fraction is red."""
    document = without_legs(record(), NEW_LEG)
    document["jobs"].append(row(NEW_LEG, 7, int(EXPECTED_HEADROOM * 30 * 60)))
    offences = tool.grade(document, workflow_text(), {NEW_LEG: "CS-0"})
    assert len(offences) == 1, offences
    assert NEW_LEG in offences[0]


def test_a_pending_entry_whose_leg_reached_the_floor_is_red() -> None:
    """Self-expiring: once measured, the entry must go, so it cannot stand as a hole."""
    offences = tool.grade(record(), workflow_text(), {NEW_LEG: "CS-0"})
    assert len(offences) == 1, offences
    assert NEW_LEG in offences[0]
    assert "remove" in offences[0]


def test_a_pending_entry_naming_an_undeclared_leg_is_red() -> None:
    offences = tool.grade(record(), workflow_text(), {"retired leg": "CS-0"})
    assert len(offences) == 1, offences
    assert "retired leg" in offences[0]


def test_a_pending_entry_without_an_item_id_is_red() -> None:
    offences = tool.grade(without_legs(record(), NEW_LEG), workflow_text(), {NEW_LEG: "soon"})
    assert len(offences) == 1, offences
    assert "soon" in offences[0]


def test_the_tolerated_legs_are_reported_rather_than_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_workflow(tmp_path, workflow_text())
    target = tmp_path / tool.RECORD_RELATIVE
    target.parent.mkdir(parents=True)
    target.write_bytes(json.dumps(without_legs(record(), NEW_LEG)).encode("ascii"))
    monkeypatch.setattr(tool, "PENDING_FIRST_RECORD", {NEW_LEG: "CS-0"})
    assert tool.main(["--root", str(tmp_path)]) == 0
    pending = [line for line in capsys.readouterr().out.splitlines() if line.startswith("PENDING")]
    assert len(pending) == 1, pending
    assert NEW_LEG in pending[0]
    assert "CS-0" in pending[0]


def test_the_shipped_pending_entries_are_what_this_module_pins() -> None:
    assert tool.PENDING_FIRST_RECORD == EXPECTED_PENDING


def test_main_exits_non_zero_over_a_red_tree_and_zero_over_a_green_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The synthetic workflow is not the shipped one, so the shipped PENDING
    # table - which names shipped legs - does not describe it.
    monkeypatch.setattr(tool, "PENDING_FIRST_RECORD", {})
    for name, document, expected in (
        ("red", record({"audit": 19 * 60}), 1),
        ("green", record(), 0),
    ):
        root = tmp_path / name
        workflow = root / tool.WORKFLOW_RELATIVE
        workflow.parent.mkdir(parents=True)
        workflow.write_bytes(workflow_text().encode("ascii"))
        target = root / tool.RECORD_RELATIVE
        target.parent.mkdir(parents=True)
        target.write_bytes(json.dumps(document).encode("ascii"))
        assert tool.main(["--root", str(root)]) == expected, name


def test_main_is_red_when_the_record_is_absent(tmp_path: Path) -> None:
    workflow = tmp_path / tool.WORKFLOW_RELATIVE
    workflow.parent.mkdir(parents=True)
    workflow.write_bytes(workflow_text().encode("ascii"))
    assert tool.main(["--root", str(tmp_path)]) == 1


# ---------------------------------------------------------------------------
# The pins - literal, and equal to what this module expects
# ---------------------------------------------------------------------------


def test_the_fraction_and_the_run_floor_are_what_this_module_pins() -> None:
    assert tool.HEADROOM == EXPECTED_HEADROOM
    assert tool.MINIMUM_RUNS_PER_JOB == EXPECTED_MINIMUM_RUNS


def test_the_fraction_is_bound_from_integer_literals_and_not_derived() -> None:
    """A fraction computed from the record would agree with it by construction."""
    tree = ast.parse(TOOL_SOURCE.read_text(encoding="utf-8"))
    pinned = ("HEADROOM_NUMERATOR", "HEADROOM_DENOMINATOR", "MINIMUM_RUNS_PER_JOB")
    bound: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                bound[node.target.id] = node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bound[target.id] = node.value
    derived = [
        name
        for name in pinned
        if not (
            isinstance(bound.get(name), ast.Constant)
            and isinstance(getattr(bound.get(name), "value", None), int)
        )
    ]
    assert derived == [], f"not bound from an integer literal: {derived}"
