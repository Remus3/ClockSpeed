"""CS-1124 - grade every tier2 job's recorded duration against a fraction of its timeout.

WHY THIS EXISTS. A tier2 job that crosses its `timeout-minutes` is CANCELLED. A
cancellation names no failing test and no number, and the headless lane reads it
as `ci_red` and stops. The Windows clean-checkout probe crept toward its cutoff
for days on green runs and was then cancelled three times in one evening, with
nothing red anywhere beforehand. This tool makes that creep red while a run can
still finish.

TWO MODES, AND ONLY ONE OF THEM TOUCHES THE NETWORK.

    python tools/tier2_headroom.py             grade the tracked record, exit 1 on any offence
    python tools/tier2_headroom.py --refresh   re-take the record from `gh`, then grade it

The refresh is run BY HAND, like `tools/facts_probe.py`, and never from a hook or
a test: no test on this project reaches the network. `tests/test_tier2_headroom.py`
grades the tracked record offline, so a refresh that captures a job past the
fraction is red in the suite at once.

WHAT IS DERIVED, WHAT IS READ, WHAT IS STATED.

- Each job's DURATION is derived here from the recorded start and completion
  timestamps. The record carries no duration of its own to drift from them.
- Each job's TIMEOUT is read from the parsed workflow, with the matrix expanded
  into the display names the API reports. No timeout is transcribed anywhere.
- The FRACTION is stated below, beside its basis, as integer literals.

THE RECORD IS AN ALLOWLIST OF FIELDS. The jobs API returns URLs carrying the
repository owner, host labels and step detail; none of it is needed and none of it
is kept. A row carrying any field not in :data:`RECORD_FIELDS` is an offence, so
an extra field cannot ride into a tracked file by a later edit either.

STALENESS IS THE STATED PRICE, AND NO OFFLINE CHECK OF IT IS SOUND. The record is
as recent as its last refresh; the suite cannot know a job slowed down since.
Tying the record to the last commit touching the workflow was examined and NOT
built, for three reasons: CI checks out shallow, so that commit and the ancestry
of a recorded head_sha are often absent; a run can only exist AFTER the workflow
commit it ran is pushed, so every workflow edit would ship this guard red until a
second commit refreshed the record; and wall-clock age is not deterministic. What
IS checked offline covers the structural half of staleness: a job added, renamed
or removed in the workflow is red against the record, and every timeout is read
live from the workflow rather than from the record.

A RENAME IS THE ONE STRUCTURAL CHANGE THAT CANNOT BE RECORDED IN ITS OWN COMMIT,
for the second reason above, so a commit renaming a job ships this guard red
until a refresh records the run floor's worth of runs under the new names.
CS-1229 bridged its shard rename with a self-expiring table that lifted the run
floor, and only that, for the named jobs; it was removed once every renamed leg
was measured over the floor's worth of runs. A refresh drops rows for jobs the workflow no longer
declares, so a renamed job's old rows do not stand as an offence no run can clear.

AN ADDED LEG HAS THE SAME DILEMMA, and :data:`PENDING_FIRST_RECORD` is its bounded
answer: CS-1317 restored the CS-1229 table, keyed now by the expanded LEG name rather
than the job id, so the legs already measured keep their floor.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/facts_probe.py does it.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

WORKFLOW_RELATIVE = ".github/workflows/tier2.yml"
RECORD_RELATIVE = "tools/tier2_durations.json"

# THE FRACTION, AND ITS BASIS. A job whose longest recorded run reaches this
# fraction of its own `timeout-minutes` is an offence.
#
# BASIS, measured 2026-09-17 over the tier2 run history the refresh reads:
# - RETROSPECTIVE LEAD. At 4/5, the Windows clean-checkout probe would first
#   have reddened on run 34908659460 (25.4 of 30 minutes), SEVEN completed tier2
#   runs before its first cancellation on run 35163459856. At 17/20 the first red
#   is run 35146663356, two runs before it. At 9/10 there is no red at all before
#   the cancellations - the job never recorded a green run that slow.
# - NOT BELOW IT. At 3/4 the record taken after the probe was parallelised is
#   already red (the Windows full suite recorded 23.5 of 30 minutes on run
#   35201160041), so a tighter fraction ships red on the day it is written and
#   measures only that it was set too low.
# - WHAT IT BUYS. One fifth of the timeout is the margin a single slow run must
#   eat before it is cancelled. Consecutive Windows runs of one job have been
#   measured more than one fifth apart, so this is an early warning, not a
#   guarantee - the guarantee would be a fraction the current record fails.
HEADROOM_NUMERATOR = 4
HEADROOM_DENOMINATOR = 5
HEADROOM = Fraction(HEADROOM_NUMERATOR, HEADROOM_DENOMINATOR)

# A job graded on one or two runs is graded on a sample that says nothing about
# its spread, so fewer than this many SAMPLES is itself an offence. A sample is a
# DISTINCT run id carrying a job that actually ran: not skipped, and taking more
# than zero seconds. Counting rows let one run copied three times, or one real
# run beside two skipped ones, satisfy the floor with a single measurement.
MINIMUM_RUNS_PER_JOB = 3

# CS-1317 - THE TRANSITION, AND WHY IT IS A TABLE AND NOT A SKIP. The sixth tier1
# shard ADDS a leg to each tier2 matrix job, and a leg can only be measured after
# the commit adding it is pushed and a tier2 run on it completes. So for the first
# nights the new legs have no recorded run, and the run floor above would ship that
# commit red - the dilemma this module's docstring names.
#
# An entry here, keyed by the EXPANDED LEG NAME the API reports and naming the item
# that added the leg, lifts THE RUN FLOOR ONLY, for that one leg, and nothing else:
# - keyed by LEG, never by job id: CS-1229 keyed its table by job id, which lifted
#   the floor on every leg of the job, and here the legs already measured keep it;
# - every recorded run of a pending leg is still graded against the fraction;
# - an entry naming a leg the workflow does not declare is an offence, which also
#   refuses a bare job id, since no leg is named that;
# - an entry not naming an item in the `CS-<number>` spelling is an offence;
# - SELF-EXPIRING: once the leg holds the floor's worth of runs, the entry itself
#   is an offence until it is removed, so it cannot stand on as an exemption;
# - every tolerated leg is PRINTED on each grade, never silently passed;
# - tests/test_tier2_headroom.py pins this literal, so widening it is red there
#   until that pin moves in the same diff.
PENDING_FIRST_RECORD: dict[str, str] = {
    "full suite (ubuntu-latest, scan shard)": "CS-1317",
    "full suite (windows-latest, scan shard)": "CS-1317",
    "clean-checkout probe (ubuntu-latest, scan shard)": "CS-1317",
    "clean-checkout probe (windows-latest, scan shard)": "CS-1317",
}

_ITEM_ID = re.compile(r"^CS-\d+$")

# How many completed tier2 runs a refresh records by default.
DEFAULT_RUNS = 5

RECORD_FIELDS = (
    "run_id",
    "head_sha",
    "job",
    "conclusion",
    "started_at",
    "completed_at",
)

SECONDS_PER_MINUTE = 60

# Bounds every `gh` call. A hung credential prompt must not hang the refresh.
GH_TIMEOUT_SECONDS = 120

_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_MATRIX_REFERENCE = re.compile(r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}")
_ANY_EXPRESSION = re.compile(r"\$\{\{")


# ---------------------------------------------------------------------------
# The workflow - every job's display name and its own timeout
# ---------------------------------------------------------------------------


def _matrix_combinations(job_id: str, job: dict[str, Any]) -> list[dict[str, str]]:
    """Expand a job's matrix into one mapping per combination.

    Args:
        job_id: The job's key, for messages.
        job: The parsed job.

    Returns:
        One mapping per combination; a single empty mapping for no matrix.

    Raises:
        ValueError: The matrix uses a shape this tool does not expand.
    """
    strategy = job.get("strategy")
    if not isinstance(strategy, dict) or "matrix" not in strategy:
        return [{}]
    matrix = strategy["matrix"]
    if not isinstance(matrix, dict) or not matrix:
        message = f"job {job_id!r} declares a matrix this tool cannot read"
        raise ValueError(message)
    if "include" in matrix or "exclude" in matrix:
        message = f"job {job_id!r} uses matrix include/exclude, which this tool does not expand"
        raise ValueError(message)
    keys = sorted(matrix)
    values = []
    for key in keys:
        listed = matrix[key]
        if not isinstance(listed, list) or not listed:
            message = f"job {job_id!r} matrix key {key!r} is not a non-empty list"
            raise ValueError(message)
        values.append([str(item) for item in listed])
    return [dict(zip(keys, combo, strict=True)) for combo in itertools.product(*values)]


def _expand_name(job_id: str, template: str, combination: dict[str, str]) -> str:
    """One display name, with every matrix reference substituted.

    Args:
        job_id: The job's key, for messages.
        template: The job's ``name`` as written.
        combination: One matrix combination.

    Returns:
        The display name the API reports for that combination.

    Raises:
        ValueError: A reference is not in the matrix, or another expression remains.
    """
    name = template
    for match in _MATRIX_REFERENCE.finditer(template):
        key = match.group(1)
        if key not in combination:
            message = f"job {job_id!r} names matrix.{key}, which its matrix lacks"
            raise ValueError(message)
        name = name.replace(match.group(0), combination[key])
    if _ANY_EXPRESSION.search(name):
        message = f"job {job_id!r} name {template!r} carries an expression not expanded"
        raise ValueError(message)
    return name


def declared_timeouts(workflow_text: str) -> dict[str, int]:
    """Every job display name the workflow expands to, mapped to its timeout in minutes.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        Display name to ``timeout-minutes``.
    """
    return {name: timeout for name, (_job_id, timeout) in declared_jobs(workflow_text).items()}


def declared_jobs(workflow_text: str) -> dict[str, tuple[str, int]]:
    """Every job display name the workflow expands to, with its job id and timeout.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        Display name to (the job's key, its ``timeout-minutes``).

    Raises:
        ValueError: The workflow cannot be read into that mapping.
    """
    document = yaml.safe_load(workflow_text)
    jobs = document.get("jobs") if isinstance(document, dict) else None
    if not isinstance(jobs, dict) or not jobs:
        message = f"{WORKFLOW_RELATIVE} declares no jobs mapping"
        raise ValueError(message)
    declared: dict[str, tuple[str, int]] = {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            message = f"job {job_id!r} is not a mapping"
            raise ValueError(message)
        timeout = job.get("timeout-minutes")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            message = f"job {job_id!r} states no positive integer timeout-minutes"
            raise ValueError(message)
        template = str(job.get("name", job_id))
        for combination in _matrix_combinations(str(job_id), job):
            name = _expand_name(str(job_id), template, combination)
            if name in declared:
                message = f"two jobs expand to the display name {name!r}"
                raise ValueError(message)
            declared[name] = (str(job_id), timeout)
    return declared


# ---------------------------------------------------------------------------
# The record - rows, their shape, and the durations derived from them
# ---------------------------------------------------------------------------


def _parse_stamp(value: object) -> datetime | None:
    """A UTC second-resolution API timestamp, or None when it is not one.

    Args:
        value: The recorded value.

    Returns:
        The parsed instant, or None.
    """
    if not isinstance(value, str) or not _STAMP.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _row_offence(index: int, entry: object) -> str | tuple[str, int, int, str]:
    """Validate one record row and derive its duration.

    Args:
        index: The row's position, for messages.
        entry: The row.

    Returns:
        The offence, or (the job name, the run id, the derived seconds, the conclusion).
    """
    if not isinstance(entry, dict):
        return f"record row {index} is not a mapping"
    keys = set(entry)
    unlisted = sorted(keys - set(RECORD_FIELDS))
    if unlisted:
        return f"record row {index} carries fields off the allowlist: {unlisted}"
    missing = [field for field in RECORD_FIELDS if field not in keys]
    if missing:
        return f"record row {index} lacks fields: {missing}"
    job = entry["job"]
    run_id = entry["run_id"]
    started = _parse_stamp(entry["started_at"])
    completed = _parse_stamp(entry["completed_at"])
    faults = [
        ("names no job", not isinstance(job, str) or not job),
        (
            "carries no positive integer run_id",
            isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0,
        ),
        (
            "carries no full head_sha",
            not isinstance(entry["head_sha"], str) or not _SHA.match(entry["head_sha"]),
        ),
        (
            "carries no conclusion",
            not isinstance(entry["conclusion"], str) or not entry["conclusion"],
        ),
        ("carries an unreadable timestamp", started is None or completed is None),
    ]
    named = [why for why, failed in faults if failed]
    if named or started is None or completed is None:
        return f"record row {index} ({job!r}) {'; '.join(named)}"
    seconds = int((completed - started).total_seconds())
    if seconds < 0:
        return f"record row {index} ({job!r}) completes before it starts"
    return str(job), int(run_id), seconds, str(entry["conclusion"])


def _pending_offences(
    pending: dict[str, str],
    timeouts: dict[str, int],
    samples: dict[str, set[int]],
) -> list[str]:
    """Every fault of the pending table itself - see :data:`PENDING_FIRST_RECORD`.

    Args:
        pending: Leg display name to item id.
        timeouts: Display name to timeout, from the workflow.
        samples: Display name to the distinct run ids that ran.

    Returns:
        The offences.
    """
    offences: list[str] = []
    for leg, item in sorted(pending.items()):
        if leg not in timeouts:
            offences.append(f"pending entry {leg!r}: {WORKFLOW_RELATIVE} declares no such leg")
        if not isinstance(item, str) or not _ITEM_ID.match(item):
            offences.append(f"pending entry {leg!r} names no item id: {item!r}")
        if leg in timeouts and len(samples.get(leg, set())) >= MINIMUM_RUNS_PER_JOB:
            offences.append(
                f"pending entry {leg!r}: the leg now holds {MINIMUM_RUNS_PER_JOB} runs, "
                "so the transition is over - remove the entry"
            )
    return offences


def _graded(
    record: object, workflow_text: str, pending: dict[str, str]
) -> tuple[list[str], list[str]]:
    """Every offence of one record against one workflow, and every tolerated leg.

    Args:
        record: The parsed record document.
        workflow_text: The workflow file's text.
        pending: Leg display name to the item id that added it.

    Returns:
        (the offences, the pending legs tolerated below the run floor).
    """
    try:
        timeouts = declared_timeouts(workflow_text)
    except (ValueError, yaml.YAMLError) as exc:
        # The type and an authored first argument, never the object.
        detail = exc.args[0] if exc.args and isinstance(exc.args[0], str) else ""
        return [f"{WORKFLOW_RELATIVE}: {type(exc).__name__}: {detail}"], []
    rows = record.get("jobs") if isinstance(record, dict) else None
    if not isinstance(record, dict) or set(record) != {"jobs"} or not isinstance(rows, list):
        return [f"{RECORD_RELATIVE} is not a mapping holding exactly one 'jobs' list"], []

    offences: list[str] = []
    tolerated: list[str] = []
    durations: dict[str, list[tuple[int, int]]] = {}
    samples: dict[str, set[int]] = {}
    for index, entry in enumerate(rows):
        verdict = _row_offence(index, entry)
        if isinstance(verdict, str):
            offences.append(verdict)
            continue
        job, run_id, seconds, conclusion = verdict
        durations.setdefault(job, []).append((run_id, seconds))
        if conclusion != "skipped" and seconds > 0:
            samples.setdefault(job, set()).add(run_id)

    offences.extend(
        f"{job}: recorded, but {WORKFLOW_RELATIVE} declares no such job"
        for job in sorted(set(durations) - set(timeouts))
    )
    offences.extend(_pending_offences(pending, timeouts, samples))
    for job, timeout_minutes in sorted(timeouts.items()):
        runs = durations.get(job, [])
        distinct = len(samples.get(job, set()))
        if distinct < MINIMUM_RUNS_PER_JOB and job in pending:
            tolerated.append(
                f"{job}: {distinct} distinct run(s), below {MINIMUM_RUNS_PER_JOB} and tolerated "
                f"while {pending[job]} awaits its first record"
            )
        elif distinct < MINIMUM_RUNS_PER_JOB:
            offences.append(
                f"{job}: {distinct} distinct run(s) that ran, fewer than {MINIMUM_RUNS_PER_JOB}; "
                f"refresh with `python {Path(__file__).name} --refresh`"
            )
            continue
        limit = HEADROOM * timeout_minutes * SECONDS_PER_MINUTE
        for run_id, seconds in sorted(runs):
            if seconds >= limit:
                offences.append(
                    f"{job}: run {run_id} took {seconds}s, at or past {HEADROOM} of its "
                    f"{timeout_minutes}-minute timeout-minutes ({limit}s)"
                )
    return offences, tolerated


def grade(record: object, workflow_text: str, pending: dict[str, str] | None = None) -> list[str]:
    """Every offence of one record against one workflow.

    Args:
        record: The parsed record document.
        workflow_text: The workflow file's text.
        pending: Leg display name to item id, lifting the run floor per
            :data:`PENDING_FIRST_RECORD`; none when omitted.

    Returns:
        The offences, empty when the record is clean.
    """
    return _graded(record, workflow_text, pending or {})[0]


def pending_notes(
    record: object, workflow_text: str, pending: dict[str, str] | None = None
) -> list[str]:
    """Every leg the pending table tolerates below the run floor, one line each.

    Args:
        record: The parsed record document.
        workflow_text: The workflow file's text.
        pending: Leg display name to item id; none when omitted.

    Returns:
        The tolerated legs, empty when none is.
    """
    return _graded(record, workflow_text, pending or {})[1]


def _tree_inputs(root: Path) -> tuple[object, str] | str:
    """The record and the workflow text under ``root``, or why they cannot be read.

    Args:
        root: The repository root.

    Returns:
        (the parsed record, the workflow text), or the offence.
    """
    record_path = root / RECORD_RELATIVE
    workflow_path = root / WORKFLOW_RELATIVE
    if not workflow_path.is_file():
        return f"{WORKFLOW_RELATIVE} is absent"
    if not record_path.is_file():
        return f"{RECORD_RELATIVE} is absent; run this tool with --refresh"
    try:
        document = json.loads(record_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"{RECORD_RELATIVE} is not JSON: {exc.msg} at line {exc.lineno}"
    return document, workflow_path.read_text(encoding="utf-8")


def grade_tree(root: Path) -> list[str]:
    """Grade the record and the workflow as they stand under ``root``.

    Args:
        root: The repository root.

    Returns:
        The offences.
    """
    inputs = _tree_inputs(root)
    if isinstance(inputs, str):
        return [inputs]
    return grade(inputs[0], inputs[1], PENDING_FIRST_RECORD)


def pending_tree(root: Path) -> list[str]:
    """The legs :data:`PENDING_FIRST_RECORD` tolerates under ``root``.

    Args:
        root: The repository root.

    Returns:
        One line per tolerated leg.
    """
    inputs = _tree_inputs(root)
    if isinstance(inputs, str):
        return []
    return pending_notes(inputs[0], inputs[1], PENDING_FIRST_RECORD)


# ---------------------------------------------------------------------------
# The refresh - the only network path, run by hand
# ---------------------------------------------------------------------------


def parse_jobs_payload(payload: object) -> list[dict[str, Any]]:
    """The record rows one jobs-API page yields, keeping allowlisted fields only.

    A job that has not completed is dropped: it has no duration yet.

    Args:
        payload: The parsed ``actions/runs/<id>/jobs`` response.

    Returns:
        The rows, in payload order.

    Raises:
        ValueError: The payload is not a complete jobs listing.
    """
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(payload, dict) or not isinstance(jobs, list):
        message = "the payload is not a jobs listing"
        raise ValueError(message)
    total = payload.get("total_count")
    if not isinstance(total, int) or total > len(jobs):
        message = f"the payload is one page of {total} jobs holding {len(jobs)}"
        raise ValueError(message)
    rows = []
    for job in jobs:
        if not isinstance(job, dict) or job.get("status") != "completed":
            continue
        rows.append(
            {
                "run_id": job.get("run_id"),
                "head_sha": job.get("head_sha"),
                "job": job.get("name"),
                "conclusion": job.get("conclusion"),
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at"),
            }
        )
    return rows


def gh_fetch(args: list[str]) -> str:
    """Run one bounded `gh` call and return its stdout.

    Args:
        args: The arguments after ``gh``.

    Returns:
        The standard output.

    Raises:
        RuntimeError: `gh` is absent or the call failed.
    """
    gh = resolve_tool("gh")
    if gh is None:
        message = "gh is not on PATH; the refresh needs it"
        raise RuntimeError(message)
    completed = subprocess.run(
        [gh, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=GH_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        message = f"gh {args[0]} exited {completed.returncode}"
        raise RuntimeError(message)
    return completed.stdout


def _atomic_write(target: Path, data: bytes) -> None:
    """Write bytes via a sibling temp file and a rename, retried on Windows.

    Args:
        target: The destination.
        data: The bytes.

    Raises:
        PermissionError: The rename kept failing.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name(target.name + ".tmp")
    staging.write_bytes(data)
    for attempt in range(4):
        try:
            staging.replace(target)
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
        else:
            return
    # The fifth attempt is unguarded, so a persistent refusal propagates as itself.
    staging.replace(target)


def refresh(root: Path, runs: int, fetch: Callable[[list[str]], str] = gh_fetch) -> Path:
    """Re-take the record from the most recent completed tier2 runs.

    Args:
        root: The repository root.
        runs: How many completed runs to record.
        fetch: Runs one `gh` call; injected so the path is testable offline.

    Returns:
        The record path written.

    Raises:
        ValueError: The workflow under ``root`` cannot be read, so there is
            nothing to keep rows for.
    """
    # CS-1229 - ROWS FOR A JOB THE WORKFLOW NO LONGER DECLARES ARE DROPPED. A
    # rename leaves the old name's rows measuring nothing the lane still runs,
    # and kept they are an offence no future run can clear. The new names are
    # graded by the run floor, so a rename is still red until it is measured.
    workflow_path = root / WORKFLOW_RELATIVE
    if not workflow_path.is_file():
        message = f"{WORKFLOW_RELATIVE} is absent, so no job can be kept"
        raise ValueError(message)
    declared = declared_jobs(workflow_path.read_text(encoding="utf-8"))
    listing = json.loads(
        fetch(
            [
                "run",
                "list",
                "--workflow",
                Path(WORKFLOW_RELATIVE).name,
                "--limit",
                str(runs * 4),
                "--json",
                "databaseId,status",
            ]
        )
    )
    completed = [
        entry["databaseId"]
        for entry in listing
        if isinstance(entry, dict) and entry.get("status") == "completed"
    ][:runs]
    rows: list[dict[str, Any]] = []
    for run_id in completed:
        payload = json.loads(
            fetch(["api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs?per_page=100"])
        )
        rows.extend(row for row in parse_jobs_payload(payload) if row["job"] in declared)
    target = root / RECORD_RELATIVE
    text = json.dumps({"jobs": rows}, indent=2, sort_keys=False) + "\n"
    _atomic_write(target, text.encode("ascii"))
    return target


def main(argv: list[str] | None = None) -> int:
    """Grade, optionally after a refresh.

    Args:
        argv: Command-line arguments.

    Returns:
        0 when clean, 1 on any offence or a failed refresh.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--refresh", action="store_true", help="re-take the record from gh")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    args = parser.parse_args(argv)

    if args.refresh:
        try:
            written = refresh(args.root, args.runs)
        except subprocess.TimeoutExpired:
            # Never rendered: the expired command's argv carries the resolved
            # program path, which can sit under a home directory.
            sys.stderr.write(f"refresh failed: gh ran past {GH_TIMEOUT_SECONDS}s\n")
            return 1
        except (RuntimeError, ValueError) as exc:
            # The type and an authored first argument are rendered, never the object.
            detail = exc.args[0] if exc.args and isinstance(exc.args[0], str) else ""
            sys.stderr.write(f"refresh failed: {type(exc).__name__}: {detail}\n")
            return 1
        sys.stdout.write(f"wrote {written.relative_to(args.root).as_posix()}\n")

    offences = grade_tree(args.root)
    for note in pending_tree(args.root):
        sys.stdout.write(f"PENDING {note}\n")
    for offence in offences:
        sys.stdout.write(f"OFFENCE {offence}\n")
    if not offences:
        sys.stdout.write(f"tier2 headroom clean at {HEADROOM} of every job's timeout\n")
    return 1 if offences else 0


if __name__ == "__main__":
    raise SystemExit(main())
