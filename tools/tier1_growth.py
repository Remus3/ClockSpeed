"""CS-917 - measure the tier1 lane's growth per commit and grade its warn band.

WHY THIS EXISTS. `CS-896` watches the tier1 lane's DURATION against a budget and
a ceiling. Nothing watched its GROWTH RATE, and nothing graded the WARN BAND -
the gap between those two levels - against the lane's own run-to-run movement.
Two consequences, both measured on this project: a reading could jump the whole
band in one run, reaching a red having never warned; and three separate
re-derivations of that band each sized it from a noise figure their own next
reading falsified.

TWO MODES, AND ONLY ONE OF THEM TOUCHES THE NETWORK.

    python tools/tier1_growth.py             grade the tracked record, exit 1 on any offence
    python tools/tier1_growth.py --refresh   re-take the record from `gh`, then grade it

The refresh is run BY HAND, like `tools/facts_probe.py` and
`tools/tier2_headroom.py`, and never from a hook or a test: no test on this
project reaches the network. `tests/test_tier1_growth.py` grades the tracked
record offline, so a refresh that captures a wider jump is red in the suite at
once.

TWO CONDITIONS ARE GRADED, PER JOB, AND THEY ARE NOT INTERCHANGEABLE. Writing
`M` for a job's worst reading, `N` for its jitter and `B`, `C` for the budget
and the ceiling, CS-896's leaf asks for `B >= M` (a clean run does not warn) and
`C - B >= N` (a rise lands in the band before it reaches the ceiling). This tool
graded only the second until CS-1146, and the shipped guard shard is exactly the
job that shape misses: its jitter is inside the band while every successful
reading it has is over the budget. Each job is graded against each condition and
NAMED - never pooled into one line, which is met by its strongest member.

THE NOISE FIGURE IS A MAX CONSECUTIVE STEP, NOT A SERIES RANGE, AND THAT CHOICE
IS THE WHOLE ITEM. The condition being graded is that growth is VISIBLE before
it is FATAL: a rising lane must land in the warn band rather than clearing it in
one jump. What defeats that is a single RUN-TO-RUN jump wider than the band, so
the figure is the largest step between consecutive readings of one job in time
order.

    - A series range over days conflates real growth with jitter. It is the
      figure that was falsified three times, and on a lane that creeps steadily
      it demands a band no cutoff can hold while every transition it is meant to
      catch is in fact visible.
    - A tolerance bound assumes a distribution. This project measured a
      BYTE-IDENTICAL population at 314s and then 226s, and a normal bound over
      the readings gave 452s at n=3 and 564s at n=4 - it moved the wrong way,
      because the sample is not from one distribution. A max consecutive step is
      an observed difference: no variance, quantile or fitted spread enters it.

CONCURRENT READINGS ARE NOT ORDERED AND THE FIGURE MUST NOT TURN ON A TIEBREAK.
Two runs of one job can start in the SAME SECOND - a batched push sends several
commits and the API reports one `started_at` for both. Their order is not a
fact, and on the shipped record breaking that tie one way gives 101s and the
other 129s. So readings sharing a `started_at` form one CONCURRENT GROUP and the
figure is the largest step available under ANY consistent ordering of each
group: the widest pair across adjacent groups, and the widest pair inside a
group, since two concurrent readings can be adjacent to each other. That is
deterministic, it never understates, and it does not depend on which member of a
tie a sort happened to put first.

WHAT IS DERIVED, WHAT IS READ, WHAT IS STATED.

- Each reading's DURATION is derived here from the recorded start and completion
  timestamps. The record carries no duration of its own to drift from them.
- The BUDGET and the CEILING are read from the parsed workflow, so the band is
  never transcribed into this file or into the record.
- Each reading's position on the COMMIT AXIS is recorded, because it is a fact
  about this repository rather than one the jobs API reports, and `git` is not
  reachable from CI's shallow checkout. `tests/test_tier1_growth.py` re-derives
  every recorded distance from git when the checkout carries the ancestry, which
  is what stops a hand-edited distance from being invisible.
- The RATCHET and the UNMET SET are stated below, each beside its basis.

A READING IS A SUCCESSFUL JOB AND NOTHING ELSE. Tier1 runs pytest with `-x`, so
a failing job stops at the first failure: its duration is a lower bound on the
lane's length and admitting it would UNDERSTATE both the worst reading and the
jitter. Three runs in the shipped record failed almost at once.

THE RECORD IS AN ALLOWLIST OF FIELDS, for the reason `tools/tier2_headroom.py`
states: the jobs API returns URLs carrying the repository owner, host labels and
step detail, none of it needed and none of it kept.

STALENESS IS THE STATED PRICE. The record is as recent as its last refresh and
the suite cannot know the lane moved since. What IS checked offline covers the
structural half: a job added, renamed or removed in the workflow is red against
the record, and both levels are read live from the workflow.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any, NamedTuple

import yaml

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/tier2_headroom.py does it.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

WORKFLOW_RELATIVE = ".github/workflows/tier1.yml"
RECORD_RELATIVE = "tools/tier1_readings.json"

BUDGET_KEY = "TIER1_BUDGET_SECONDS"
CEILING_KEY = "TIER1_CEILING_SECONDS"

# THE RATCHET ON THE FIGURE, AND ITS BASIS. A job whose largest step between
# consecutive readings exceeds this is an offence.
#
# BASIS, measured 2026-09-17 over the readings the shipped record holds: the
# widest step any job took is the fast shard's, and this figure IS that step. It
# is set AT the observed worst rather than above it for the reason
# `tools/tier2_headroom.py` gives for its own fraction - a figure set above the
# record measures only that it was set too high, and the next reading that moves
# the lane further is then silent. Set here, the next refresh that captures a
# wider jump is red in the suite while a run can still finish.
#
# IT IS THE ORDER-INDEPENDENT FIGURE AND NOT THE SMALLER ONE A TIEBREAK OFFERS.
# The shipped record carries two fast-shard readings starting in the same second;
# breaking that tie one way gives 101s. The rule in the module docstring takes
# the widest step available under any ordering of a concurrent group, which is
# what makes this figure a measurement rather than an artefact of a sort.
#
# IT IS NOT A BUDGET AND IT IS NOT THE BAND. Whether a job's band COVERS its
# jitter is the separate, stated verdict in ORDERING_UNMET below; this figure
# only refuses further degradation of the jitter itself.
JITTER_RATCHET_SECONDS = 129

# A job graded on one or two readings is graded on a sample that says nothing
# about its movement, so fewer than this many READINGS is itself an offence. A
# reading is a DISTINCT run id whose job concluded `success`.
MINIMUM_READINGS_PER_JOB = 5

# EVERY JOB WHOSE BAND IS NARROWER THAN ITS OWN JITTER, as the shipped record
# stands - so a rising reading on one of these can reach the ceiling without
# ever having landed in the band.
#
# THIS SET IS NOT EMPTY AND THAT IS THE MEASUREMENT, NOT AN OVERSIGHT. The
# condition CS-896's leaf asks for is UNMET for the job named here, and it is
# not reachable by choosing better levels: guard (k) of `tools/drift_guard.py`
# ratchets the budget, the ceiling and the cutoff in BOTH directions, and even
# with all three free the feasible window is empty at this job's measured jitter
# and worst reading. CS-1133 owns that remainder.
#
# THE SET IS A TWO-WAY RATCHET, which is the only reason recording it is worth
# anything. `tests/test_tier1_growth.py` pins it as a literal and compares it to
# the computed set, so a job that DEGRADES into it is red at once, and a job
# that IMPROVES out of it is red too - which forces this literal down rather
# than letting a met condition sit here unrecorded.
ORDERING_UNMET = ("gates, lint, types, tests",)

# EVERY JOB WHOSE WORST READING IS ALREADY OVER THE BUDGET, as the shipped
# record stands - CS-896's FIRST condition, `B >= M`, which nothing in this tool
# graded until CS-1146.
#
# WHY THIS IS A SEPARATE SET AND NOT A FOLD INTO ORDERING_UNMET ABOVE. That set
# answers "can a rising reading clear the whole band in one jump" - a question
# about MOVEMENT. This one answers "does a clean run already warn" - a question
# about LEVEL. The shipped guard shard is the proof they are independent: its
# jitter is well inside the band, so the ordering verdict calls it covered,
# while every successful reading it has is over the budget. A tool reporting
# only the first says that job is fine.
#
# ONE ENTRY PER JOB, NEVER A POOLED VERDICT. A single line summed over three
# jobs is met by its strongest member, and this project has measured that
# failure; `report` below names each breaching job on its own line for the same
# reason.
#
# THE SET IS A TWO-WAY RATCHET, like the one above. `tests/test_tier1_growth.py`
# pins it as a literal and compares it to the computed set, so a job that
# DEGRADES into it is red at once, and a job that IMPROVES out of it is red too.
# Closing a breach by RAISING the budget is not available: guard (k) of
# `tools/drift_guard.py` ratchets the budget, the ceiling and the cutoff in both
# directions, and CS-1133 records the ruling that raising a level to meet a slow
# lane is the move CS-896 exists to refuse.
BUDGET_UNMET = ("tests (guard shard)",)

# EVERY DECLARED JOB THAT IS NEW AND STILL UNDER THE READING FLOOR (CS-1193).
#
# A job added to the workflow has no readings, so the floor above reddens the
# shipped-record arm and the pre-push hook on the very commit that adds it -
# before CI has had a chance to produce a single reading. The floor is NOT
# lowered for it; it is waived for the jobs named here, and for NOTHING else:
#
#   - only the reading-floor offence, in both of its forms - a job the record
#     does not hold at all has zero readings, and one it holds may have fewer
#     than the floor. A breach, a jitter past the ratchet or a malformed row on
#     a pending job is graded exactly as on any other.
#   - only the jobs named. Every other declared job keeps its floor.
#
# THE SET IS A TWO-WAY RATCHET, like the two above, and it is graded in the tool
# rather than only in a test. A name whose job has REACHED the floor is red in
# `grade`, which forces this literal down at the refresh that records its fifth
# green reading; a name the workflow does not declare is red in `grade_tree`,
# through `pending_undeclared`. That direction sits on the TREE and not in
# `grade` for the reason the two sets above are intersected with the declared
# jobs there: a synthetic workflow must be graded on its own jobs, and an
# offence it cannot avoid would make every negative arm over one pass vacuously.
# Basis: the wave-3 CI route ruling, condition A3, and for the fill shard the
# CS-1198 ruling's Route N.
PENDING_READINGS = ("tests (hook shard)", "tests (fill shard)")

# THE CRASH THRESHOLD, AND WHAT IT IS NOT. A tier1 job that dies on a syntax
# error or a missing dependency concludes in a couple of seconds, and the
# shipped record carries several such rows.
#
# THIS FIGURE IS NOT THE EXCLUSION RULE. The rule is the recorded CONCLUSION -
# see `readings` and `READING_CONCLUSION` - because a duration threshold is
# corrupt in BOTH directions. A crash that happens LATE carries a long duration
# and would OVERSTATE the worst reading, inventing a breach no successful run
# supports; and a threshold has to guess where a crash ends and a genuinely fast
# run begins, while the conclusion field states it outright.
#
# It exists only so an arm can CORROBORATE the two rules still agree on the
# shipped record - every sub-threshold row there is a failed job - and say so
# the moment a successful row lands beneath it.
CRASH_SECONDS = 10

RECORD_FIELDS = (
    "run_id",
    "head_sha",
    "job",
    "conclusion",
    "started_at",
    "completed_at",
)

#: The one conclusion that makes a row a reading. See the module docstring.
READING_CONCLUSION = "success"

#: A step needs two readings to be taken between. Named so the floor is not a
#: bare literal at three separate comparisons.
READINGS_PER_STEP = 2

# How many completed tier1 runs a refresh records by default. Each run costs one
# `gh api` call, and the readings floor above needs several successful ones.
DEFAULT_RUNS = 14

# Bounds every `gh` and `git` call. A hung credential prompt must not hang the
# refresh.
SUBPROCESS_TIMEOUT_SECONDS = 180

_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_MATRIX_REFERENCE = re.compile(r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}")
_ANY_EXPRESSION = re.compile(r"\$\{\{")


class Reading(NamedTuple):
    """One successful job run, as everything downstream needs it."""

    started_at: str
    duration: int
    run_id: int
    head_sha: str


# ---------------------------------------------------------------------------
# The workflow - the job names it expands to, and the two levels
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


def declared_jobs(workflow_text: str) -> list[str]:
    """Every job display name the workflow expands to.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        The display names, in file order.

    Raises:
        ValueError: The workflow cannot be read into that list.
    """
    parsed = yaml.safe_load(workflow_text)
    jobs = parsed.get("jobs") if isinstance(parsed, dict) else None
    if not isinstance(jobs, dict) or not jobs:
        message = "the workflow declares no jobs mapping"
        raise ValueError(message)
    names: list[str] = []
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            message = f"job {job_id!r} is not a mapping"
            raise ValueError(message)
        template = job.get("name")
        if not isinstance(template, str) or not template.strip():
            message = f"job {job_id!r} declares no display name"
            raise ValueError(message)
        names.extend(
            _expand_name(str(job_id), template, combination)
            for combination in _matrix_combinations(str(job_id), job)
        )
    return names


def declared_levels(workflow_text: str) -> tuple[int, int]:
    """The budget and the ceiling, read from the workflow's env block.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        ``(budget, ceiling)`` in seconds.

    Raises:
        ValueError: Either level is absent or is not a whole number of seconds.
    """
    parsed = yaml.safe_load(workflow_text)
    env = parsed.get("env") if isinstance(parsed, dict) else None
    if not isinstance(env, dict):
        message = "the workflow declares no env block"
        raise ValueError(message)
    levels = []
    for key in (BUDGET_KEY, CEILING_KEY):
        raw = env.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (int, str)):
            message = f"the workflow does not declare {key}"
            raise ValueError(message)
        text = str(raw).strip()
        if not text.isdigit():
            message = f"{key} is {raw!r}, not a whole number of seconds"
            raise ValueError(message)
        levels.append(int(text))
    budget, ceiling = levels
    if ceiling <= budget:
        message = f"{CEILING_KEY} {ceiling} is not above {BUDGET_KEY} {budget}"
        raise ValueError(message)
    return budget, ceiling


def band(workflow_text: str) -> int:
    """The warn band - the seconds between the budget and the ceiling.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        The band in seconds.

    Raises:
        ValueError: Either level is unreadable.
    """
    budget, ceiling = declared_levels(workflow_text)
    return ceiling - budget


# ---------------------------------------------------------------------------
# The record - readings, jitter, growth
# ---------------------------------------------------------------------------


def _detail(failure: BaseException) -> str:
    """One caught failure's TYPE and its authored first argument, never the object.

    Rendering an exception object whole can leak a path, an argv or a byte
    preview into a log; `tests/test_exception_rendering.py` refuses it outright
    and `tools/tier2_headroom.py` carries the same helper shape.

    Args:
        failure: The caught exception.

    Returns:
        A one-line rendering safe to print.
    """
    first = failure.args[0] if failure.args and isinstance(failure.args[0], str) else ""
    return f"{type(failure).__name__}: {first}" if first else type(failure).__name__


def _parse_stamp(value: object) -> datetime | None:
    """One recorded timestamp, or None if it is not one.

    Args:
        value: The recorded value.

    Returns:
        The instant, or None.
    """
    if not isinstance(value, str) or not _STAMP.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _row_offence(index: int, entry: object) -> str | tuple[str, int, int, str]:
    """Grade one recorded row.

    Args:
        index: The row's position, for messages.
        entry: The row.

    Returns:
        An offence string, or ``(job, run_id, duration, head_sha)``.
    """
    where = f"row {index}"
    if not isinstance(entry, dict):
        return f"{where} is not a mapping"
    keys = set(entry)
    unlisted = sorted(keys - set(RECORD_FIELDS))
    if unlisted:
        return f"{where} carries field(s) off the allowlist: {unlisted}"
    missing = [field for field in RECORD_FIELDS if field not in keys]
    if missing:
        return f"{where} lacks field(s): {missing}"
    job = entry["job"]
    run_id = entry["run_id"]
    head_sha = entry["head_sha"]
    conclusion = entry["conclusion"]
    started = _parse_stamp(entry["started_at"])
    completed = _parse_stamp(entry["completed_at"])
    faults = [
        ("names no job", not isinstance(job, str) or not job.strip()),
        (
            "carries no positive integer run_id",
            isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0,
        ),
        (
            "carries no full head_sha",
            not isinstance(head_sha, str) or not _SHA.match(head_sha),
        ),
        (
            "carries no conclusion",
            not isinstance(conclusion, str) or not conclusion.strip(),
        ),
        ("carries an unreadable timestamp", started is None or completed is None),
    ]
    named = [why for why, failed in faults if failed]
    if named or started is None or completed is None:
        return f"{where} ({job!r}) {'; '.join(named)}"
    duration = int((completed - started).total_seconds())
    if duration < 0:
        return f"{where} ({job!r}) completes {abs(duration)}s before it starts"
    return str(job), int(run_id), duration, str(head_sha)


def readings(record: object) -> dict[str, list[Reading]]:
    """Every job's readings, oldest first, one per distinct run.

    A row whose conclusion is not :data:`READING_CONCLUSION` is not a reading;
    see the module docstring for why a failed job's duration is not one either.

    Args:
        record: The parsed record.

    Returns:
        Job display name to its readings in started_at order.
    """
    rows = record.get("jobs") if isinstance(record, dict) else None
    if not isinstance(rows, list):
        return {}
    collected: dict[str, dict[int, Reading]] = {}
    for index, entry in enumerate(rows):
        graded = _row_offence(index, entry)
        if isinstance(graded, str):
            continue
        job, run_id, duration, head_sha = graded
        seen = collected.setdefault(job, {})
        if entry["conclusion"] != READING_CONCLUSION:
            continue
        seen.setdefault(run_id, Reading(entry["started_at"], duration, run_id, head_sha))
    return {
        job: sorted(seen.values(), key=lambda reading: (reading.started_at, reading.run_id))
        for job, seen in collected.items()
    }


def jitter(durations: Sequence[int]) -> int | None:
    """The largest step between consecutive readings.

    Args:
        durations: Durations in time order.

    Returns:
        The largest absolute step, or None when there is no step to take.
    """
    if len(durations) < READINGS_PER_STEP:
        return None
    return max(abs(durations[index + 1] - durations[index]) for index in range(len(durations) - 1))


def jitter_over(found: Sequence[Reading]) -> int | None:
    """The largest step available under any ordering of the concurrent groups.

    Readings sharing a ``started_at`` are concurrent and their order is not a
    fact; see the module docstring for why the figure maximises over that
    ambiguity rather than letting a sort decide it.

    Args:
        found: One job's readings, in started_at order.

    Returns:
        The figure in seconds, or None when there is no step to take.
    """
    if len(found) < READINGS_PER_STEP:
        return None
    ordered = sorted(found, key=lambda item: item.started_at)
    groups = [
        [reading.duration for reading in concurrent]
        for _, concurrent in itertools.groupby(ordered, key=lambda item: item.started_at)
    ]
    steps = []
    for index, group in enumerate(groups):
        if len(group) > 1:
            steps.append(max(group) - min(group))
        if index + 1 < len(groups):
            following = groups[index + 1]
            steps.append(max(abs(later - earlier) for earlier in group for later in following))
    return max(steps) if steps else None


def _job_jitter(record: object) -> dict[str, int]:
    """Every job's jitter, skipping any job with fewer than two readings.

    Args:
        record: The parsed record.

    Returns:
        Job display name to its jitter in seconds.
    """
    figures = {}
    for job, found in readings(record).items():
        figure = jitter_over(found)
        if figure is not None:
            figures[job] = figure
    return figures


def worst_reading(record: object) -> dict[str, int]:
    """Every job's worst reading - `M` in CS-896's conditions.

    The population is :func:`readings`, so a job that FAILED contributes
    nothing however long or short it ran. See :data:`CRASH_SECONDS` for why the
    conclusion decides this rather than a duration threshold.

    Args:
        record: The parsed record.

    Returns:
        Job display name to its longest successful run in seconds, skipping
        any job with no readings at all.
    """
    return {
        job: max(reading.duration for reading in found)
        for job, found in readings(record).items()
        if found
    }


def budget_unmet(record: object, workflow_text: str) -> list[str]:
    """Every job whose worst reading is already over the budget.

    This is CS-896's `B >= M` - "no false warn" - and it is a DIFFERENT verdict
    from :func:`ordering_unmet`. Equality meets it: a reading landing exactly on
    the budget does not warn.

    Args:
        record: The parsed record.
        workflow_text: The workflow file's text. The budget is READ from it,
            never transcribed here.

    Returns:
        The display names, sorted.

    Raises:
        ValueError: The workflow's levels are unreadable.
    """
    budget, _ = declared_levels(workflow_text)
    return sorted(job for job, worst in worst_reading(record).items() if worst > budget)


def ordering_unmet(record: object, workflow_text: str) -> list[str]:
    """Every job whose warn band is narrower than its own jitter.

    Args:
        record: The parsed record.
        workflow_text: The workflow file's text.

    Returns:
        The display names, sorted.

    Raises:
        ValueError: The workflow's levels are unreadable.
    """
    width = band(workflow_text)
    return sorted(job for job, figure in _job_jitter(record).items() if figure > width)


def growth_per_commit(record: object) -> dict[str, Fraction]:
    """Every job's growth in seconds per commit, over the recorded window.

    The slope is a least-squares fit of duration against the reading's distance
    along the commit axis, computed in exact rational arithmetic. A job whose
    readings all sit on one commit has no slope and is absent from the result.

    Args:
        record: The parsed record.

    Returns:
        Job display name to seconds gained per commit.
    """
    distances = record.get("commits") if isinstance(record, dict) else None
    if not isinstance(distances, dict):
        return {}
    slopes: dict[str, Fraction] = {}
    for job, found in readings(record).items():
        points = [
            (Fraction(distances[reading.head_sha]), Fraction(reading.duration))
            for reading in found
            if isinstance(distances.get(reading.head_sha), int)
            and not isinstance(distances.get(reading.head_sha), bool)
        ]
        if len(points) < READINGS_PER_STEP:
            continue
        count = len(points)
        mean_x = sum((x for x, _ in points), Fraction(0)) / count
        mean_y = sum((y for _, y in points), Fraction(0)) / count
        denominator = sum(((x - mean_x) ** 2 for x, _ in points), Fraction(0))
        if denominator == 0:
            continue
        numerator = sum(((x - mean_x) * (y - mean_y) for x, y in points), Fraction(0))
        slopes[job] = numerator / denominator
    return slopes


# ---------------------------------------------------------------------------
# The grade
# ---------------------------------------------------------------------------


def _window_offences(record: dict[str, Any], found: dict[str, list[Reading]]) -> list[str]:
    """Grade the recorded window and commit axis against the readings.

    Args:
        record: The parsed record.
        found: Every job's readings.

    Returns:
        The offences.
    """
    offences = []
    window = record.get("window")
    distances = record.get("commits")
    if not isinstance(window, dict):
        return ["the record declares no window"]
    if not isinstance(distances, dict):
        return ["the record declares no commit distances"]
    every = [reading for job_readings in found.values() for reading in job_readings]
    if not every:
        return ["the record holds no readings, so its window describes nothing"]
    for reading in every:
        recorded = distances.get(reading.head_sha)
        if isinstance(recorded, bool) or not isinstance(recorded, int) or recorded < 0:
            offences.append(
                f"the reading on {reading.head_sha[:8]} has no recorded commit distance"
            )
    oldest = min(every, key=lambda reading: (reading.started_at, reading.run_id))
    newest = max(every, key=lambda reading: (reading.started_at, reading.run_id))
    if window.get("oldest_sha") != oldest.head_sha:
        offences.append(
            f"the window names {str(window.get('oldest_sha'))[:8]} as its oldest, "
            f"but the oldest reading is on {oldest.head_sha[:8]}"
        )
    if window.get("newest_sha") != newest.head_sha:
        offences.append(
            f"the window names {str(window.get('newest_sha'))[:8]} as its newest, "
            f"but the newest reading is on {newest.head_sha[:8]}"
        )
    spans = [
        distances[reading.head_sha]
        for reading in every
        if isinstance(distances.get(reading.head_sha), int)
        and not isinstance(distances.get(reading.head_sha), bool)
    ]
    if spans and window.get("commits") != max(spans):
        offences.append(
            f"the window states {window.get('commits')!r} commits, "
            f"but its widest recorded distance is {max(spans)}"
        )
    return offences


def _floor_offences(
    declared: Sequence[str],
    recorded_names: set[str],
    found: dict[str, list[Reading]],
    pending: Sequence[str],
) -> list[str]:
    """The reading floor, per declared job, with the pending set's one waiver.

    THE PENDING SET IS READ AGAINST THE DECLARED JOBS, as the two pinned sets
    are in :func:`grade`, so a synthetic workflow is graded on its own jobs
    alone. The set's OTHER direction - a name the workflow does not declare -
    is a fact about the shipped pin, and :func:`pending_undeclared` grades it
    for the tree.

    Args:
        declared: Every job the workflow declares.
        recorded_names: Every job name the record carries a row for.
        found: The readings, by job.
        pending: The pinned pending set.

    Returns:
        Every floor offence, in declaration order.
    """
    offences = []
    for name in declared:
        count = len(found.get(name, []))
        if name in pending:
            # THE ONLY OFFENCE THE PENDING SET WAIVES IS THE FLOOR, so the one
            # thing graded here is the closing direction of its ratchet.
            if count >= MINIMUM_READINGS_PER_JOB:
                offences.append(
                    f"{name!r} is pending but has {count} readings, at or over the floor of "
                    f"{MINIMUM_READINGS_PER_JOB}; drop it from the pending set"
                )
            continue
        if name not in recorded_names:
            offences.append(f"the workflow declares {name!r}, which the record does not hold")
            continue
        if count < MINIMUM_READINGS_PER_JOB:
            offences.append(
                f"{name!r} has {count} readings, under the floor of {MINIMUM_READINGS_PER_JOB}"
            )
    return offences


def grade(
    record: object,
    workflow_text: str,
    unmet: Sequence[str] = ORDERING_UNMET,
    over_budget: Sequence[str] = BUDGET_UNMET,
    pending: Sequence[str] = PENDING_READINGS,
) -> list[str]:
    """Grade one record against one workflow.

    Args:
        record: The parsed record.
        workflow_text: The workflow file's text.
        unmet: The pinned set of jobs whose band is narrower than their jitter.
        over_budget: The pinned set of jobs whose worst reading is over the
            budget. Compared BOTH ways, so an unreported breach and a reported
            compliance are each an offence.
        pending: The pinned set of NEW jobs whose reading floor is waived. A
            named job that has reached the floor is an offence here; a name
            the workflow does not declare is graded by
            :func:`pending_undeclared`, which :func:`grade_tree` adds.

    Returns:
        Every offence, in reading order. Empty means clean.
    """
    if not isinstance(record, dict) or not isinstance(record.get("jobs"), list):
        return ["the record is not a mapping carrying a jobs list"]
    try:
        declared = declared_jobs(workflow_text)
        width = band(workflow_text)
    except ValueError as failure:
        return [f"the workflow is unreadable: {_detail(failure)}"]

    offences = []
    for index, entry in enumerate(record["jobs"]):
        graded = _row_offence(index, entry)
        if isinstance(graded, str):
            offences.append(graded)

    found = readings(record)
    recorded_names = {
        entry["job"]
        for entry in record["jobs"]
        if isinstance(entry, dict) and isinstance(entry.get("job"), str)
    }
    offences.extend(
        f"the record names {name!r}, which the workflow does not declare"
        for name in sorted(recorded_names - set(declared))
    )
    offences.extend(_floor_offences(declared, recorded_names, found, pending))

    offences.extend(_window_offences(record, found))

    for name, figure in sorted(_job_jitter(record).items()):
        if figure > JITTER_RATCHET_SECONDS:
            offences.append(
                f"ratchet: {name!r} moved {figure}s between consecutive readings, "
                f"over the stated {JITTER_RATCHET_SECONDS}s"
            )

    computed = ordering_unmet(record, workflow_text)
    expected = sorted(set(unmet) & set(declared))
    if computed != expected:
        offences.append(
            f"the pinned unmet set is {expected} but the band of {width}s is narrower "
            f"than the jitter of {computed}"
        )

    breaching = budget_unmet(record, workflow_text)
    pinned = sorted(set(over_budget) & set(declared))
    if breaching != pinned:
        budget, _ = declared_levels(workflow_text)
        offences.append(
            f"the pinned over-budget set is {pinned} but the worst reading is over "
            f"the budget of {budget}s on {breaching}"
        )
    return offences


def grade_tree(
    root: Path,
    unmet: Sequence[str] = ORDERING_UNMET,
    over_budget: Sequence[str] = BUDGET_UNMET,
    pending: Sequence[str] = PENDING_READINGS,
) -> list[str]:
    """Grade the tracked record of one checkout.

    Args:
        root: The repository root.
        unmet: The pinned set, passed through to :func:`grade`.
        over_budget: The pinned over-budget set, passed through to :func:`grade`.
        pending: The pinned pending set, passed through to :func:`grade`.

    Returns:
        Every offence. Empty means clean.
    """
    record_path = root / RECORD_RELATIVE
    workflow_path = root / WORKFLOW_RELATIVE
    if not record_path.is_file():
        return [f"{RECORD_RELATIVE} is absent; run --refresh"]
    if not workflow_path.is_file():
        return [f"{WORKFLOW_RELATIVE} is absent"]
    try:
        record = json.loads(record_path.read_text(encoding="ascii"))
    except (ValueError, UnicodeDecodeError) as failure:
        return [f"{RECORD_RELATIVE} is not readable as ascii JSON: {_detail(failure)}"]
    workflow_text = workflow_path.read_text(encoding="utf-8")
    offences = grade(
        record,
        workflow_text,
        unmet=unmet,
        over_budget=over_budget,
        pending=pending,
    )
    return offences + pending_undeclared(workflow_text, pending)


def pending_undeclared(workflow_text: str, pending: Sequence[str] = PENDING_READINGS) -> list[str]:
    """The pending set's opening direction: every name the workflow does not declare.

    A pending name that matches no declared job exempts nothing today, and it
    would silently exempt a job added under that name later. So it is an
    offence, and the name must be removed or corrected.

    Args:
        workflow_text: The workflow file's text.
        pending: The pinned pending set.

    Returns:
        One offence per undeclared name, sorted. An unreadable workflow yields
        nothing here, because :func:`grade` has already reported it.
    """
    try:
        declared = set(declared_jobs(workflow_text))
    except ValueError:
        return []
    return [
        f"the pending set names {name!r}, which the workflow does not declare"
        for name in sorted(set(pending) - declared)
    ]


# ---------------------------------------------------------------------------
# The report - what a session reads
# ---------------------------------------------------------------------------


def _seconds(value: Fraction) -> str:
    """One slope, rendered to two places without claiming more.

    Args:
        value: Seconds per commit.

    Returns:
        A signed decimal string.
    """
    # Rendered from integers, so no float enters a figure this project reports.
    sign = "-" if value < 0 else "+"
    hundredths = int(abs(value) * 100)
    return f"{sign}{hundredths // 100}.{hundredths % 100:02d}"


def _unmeasured_lines(workflow_text: str, found: dict[str, list[Reading]]) -> list[str]:
    """One report line per declared job the record holds no reading for.

    A DECLARED JOB WITH NO READING IS NAMED TOO, so a new shard is visibly
    unmeasured rather than absent from the one report watching the lane.

    Args:
        workflow_text: The workflow file's text.
        found: The readings, by job.

    Returns:
        The lines, sorted by job; empty when the workflow is unreadable, which
        the caller has already reported.
    """
    try:
        declared = declared_jobs(workflow_text)
    except ValueError:
        return []
    return [f"  {job}: n=0, no reading measured" for job in sorted(set(declared) - set(found))]


def report(record: object, workflow_text: str) -> str:
    """The growth report, as a session reads it.

    Args:
        record: The parsed record.
        workflow_text: The workflow file's text.

    Returns:
        The report text, 7-bit ASCII.
    """
    lines = []
    try:
        budget, ceiling = declared_levels(workflow_text)
    except ValueError as failure:
        return f"tier1 growth: the workflow is unreadable: {_detail(failure)}\n"
    width = ceiling - budget
    window = record.get("window") if isinstance(record, dict) else None
    if isinstance(window, dict):
        lines.append(
            f"tier1 growth over {window.get('commits')} commits, "
            f"{str(window.get('oldest_sha'))[:8]}..{str(window.get('newest_sha'))[:8]}"
        )
    else:
        lines.append("tier1 growth over an undeclared window")
    lines.append(f"  levels: budget {budget}s, ceiling {ceiling}s, warn band {width}s")
    slopes = growth_per_commit(record)
    figures = _job_jitter(record)
    found = readings(record)
    for job in sorted(found):
        durations = [reading.duration for reading in found[job]]
        slope = slopes.get(job)
        figure = figures.get(job)
        verdict = "no jitter measured"
        if figure is not None:
            covered = "band covers it" if figure <= width else "BAND NARROWER THAN JITTER"
            verdict = f"jitter {figure}s - {covered}"
        growth = "no slope" if slope is None else f"{_seconds(slope)}s per commit"
        worst = max(durations) if durations else 0
        # THE SECOND VERDICT, AND IT IS NOT THE ONE BESIDE IT. `verdict` above
        # grades MOVEMENT against the band; this grades LEVEL against the
        # budget. Both are printed for every job, named, one line each.
        if not durations:
            level = "no reading measured"
        elif worst > budget:
            level = f"BUDGET BREACHED by {worst - budget}s"
        else:
            level = "budget covers it"
        lines.append(f"  {job}: n={len(durations)}, worst {worst}s, {growth}, {verdict}, {level}")
    lines.extend(_unmeasured_lines(workflow_text, found))
    unmet = ordering_unmet(record, workflow_text)
    if unmet:
        lines.append(
            "  ORDERING UNMET - a reading on these jobs can reach the ceiling "
            "without ever landing in the band:"
        )
        lines.extend(f"    {job}" for job in unmet)
        lines.append("  CS-1133 owns that remainder; the levels are ratcheted by guard (k).")
    else:
        lines.append("  ordering: every job's band covers its own jitter.")
    breaching = budget_unmet(record, workflow_text)
    if breaching:
        worst_by = worst_reading(record)
        lines.append(
            "  BUDGET UNMET - the worst reading on these jobs is already over the "
            "budget, so a clean run warns and the warning carries no signal:"
        )
        lines.extend(
            f"    {job} - worst {worst_by[job]}s against a budget of {budget}s, "
            f"over by {worst_by[job] - budget}s"
            for job in breaching
        )
        lines.append("  CS-1146 owns that remainder; the levels are ratcheted by guard (k).")
    else:
        lines.append("  budget: every job's worst reading is inside the budget.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# The refresh - the only network path and the only git path, run by hand
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
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        message = f"gh {args[0]} exited {completed.returncode}"
        raise RuntimeError(message)
    return completed.stdout


def git_distance(root: Path, oldest: str, sha: str) -> int:
    """How many commits ``sha`` is ahead of ``oldest`` in this checkout.

    Args:
        root: The repository root.
        oldest: The window's oldest recorded head.
        sha: The head to place.

    Returns:
        The commit count.

    Raises:
        RuntimeError: `git` is absent or cannot place the head.
    """
    git = resolve_tool("git")
    if git is None:
        message = "git is not on PATH; the refresh needs it"
        raise RuntimeError(message)
    completed = subprocess.run(
        [git, "rev-list", "--count", f"{oldest}..{sha}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0 or not completed.stdout.strip().isdigit():
        message = f"git cannot place {sha[:8]} against {oldest[:8]}; is the ancestry present?"
        raise RuntimeError(message)
    return int(completed.stdout.strip())


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


def refresh(
    root: Path,
    runs: int,
    fetch: Callable[[list[str]], str] = gh_fetch,
    distance: Callable[[Path, str, str], int] = git_distance,
) -> Path:
    """Re-take the record from the most recent completed tier1 runs.

    Args:
        root: The repository root.
        runs: How many completed runs to record.
        fetch: Runs one `gh` call; injected so the path is testable offline.
        distance: Places one head on the commit axis; injected for the same reason.

    Returns:
        The record path written.

    Raises:
        RuntimeError: No run carried a reading, so no window can be stated.
    """
    listing = json.loads(
        fetch(
            [
                "run",
                "list",
                "--workflow",
                Path(WORKFLOW_RELATIVE).name,
                "--limit",
                str(runs * 3),
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
        rows.extend(parse_jobs_payload(payload))

    found = readings({"jobs": rows})
    every = [reading for job_readings in found.values() for reading in job_readings]
    if not every:
        message = "no recorded run carried a successful job, so there is no window to state"
        raise RuntimeError(message)
    oldest = min(every, key=lambda reading: (reading.started_at, reading.run_id))
    newest = max(every, key=lambda reading: (reading.started_at, reading.run_id))
    distances = {
        head: distance(root, oldest.head_sha, head)
        for head in sorted({reading.head_sha for reading in every})
    }
    record = {
        "window": {
            "oldest_sha": oldest.head_sha,
            "newest_sha": newest.head_sha,
            "commits": max(distances.values()),
        },
        "commits": distances,
        "jobs": rows,
    }
    target = root / RECORD_RELATIVE
    text = json.dumps(record, indent=2, sort_keys=False) + "\n"
    _atomic_write(target, text.encode("ascii"))
    return target


def open_conditions(root: Path) -> list[str]:
    """Every CS-896 condition currently unmet over one checkout's record.

    Named per job and per condition, never pooled: a summary summed over three
    jobs is met by its strongest member.

    Args:
        root: The repository root.

    Returns:
        One line per unmet (job, condition) pair, empty when all are met. A
        checkout whose record or workflow is unreadable yields nothing, because
        :func:`grade_tree` has already reported that as an offence.
    """
    try:
        record = json.loads((root / RECORD_RELATIVE).read_text(encoding="ascii"))
        workflow_text = (root / WORKFLOW_RELATIVE).read_text(encoding="utf-8")
        breaching = budget_unmet(record, workflow_text)
        narrow = ordering_unmet(record, workflow_text)
    except (OSError, ValueError, UnicodeDecodeError):
        return []
    lines = [
        f"{job!r}: B >= M is unmet - its worst reading is over the budget" for job in breaching
    ]
    lines.extend(
        f"{job!r}: C - B >= N is unmet - its band is narrower than its own jitter" for job in narrow
    )
    return lines


def main(argv: list[str] | None = None) -> int:
    """Grade the tracked record, optionally refreshing it first.

    Args:
        argv: The arguments after the program name.

    Returns:
        0 when clean, 1 over any offence, 2 when a refresh could not run.
    """
    parser = argparse.ArgumentParser(
        description="CS-917 - report the tier1 lane's growth per commit and grade its "
        "warn band against the lane's own run-to-run jitter."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="re-take the record from `gh` before grading. Run BY HAND; never in a hook.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_RUNS,
        help=f"how many completed runs a refresh records (default {DEFAULT_RUNS})",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    if args.refresh:
        try:
            written = refresh(root, args.runs)
        except (RuntimeError, ValueError) as failure:
            print(f"FAIL: the refresh did not complete: {_detail(failure)}")
            return 2
        print(f"recorded {written.relative_to(root).as_posix()}")

    record_path = root / RECORD_RELATIVE
    workflow_path = root / WORKFLOW_RELATIVE
    if record_path.is_file() and workflow_path.is_file():
        try:
            print(
                report(
                    json.loads(record_path.read_text(encoding="ascii")),
                    workflow_path.read_text(encoding="utf-8"),
                ),
                end="",
            )
        except (ValueError, UnicodeDecodeError) as failure:
            print(f"the record could not be reported: {_detail(failure)}")

    offences = grade_tree(root)
    if offences:
        print(f"FAIL: {len(offences)} offence(s) against {RECORD_RELATIVE}")
        for offence in offences:
            print(f"  - {offence}")
        return 1

    # THE EXIT CODE GRADES DRIFT; THE SUMMARY LINE MUST NOT OVERCLAIM IT.
    #
    # Two of CS-896's conditions are UNMET over the shipped record and neither
    # is closable here - the item's own DO-NOT clause refuses raising a level to
    # meet a slow lane, and guard (k) of `tools/drift_guard.py` ratchets all
    # three levels in both directions anyway. So a permanently non-zero exit
    # would only teach a session to ignore this tool, and the exit code keeps
    # meaning "no NEW drift against the pinned sets".
    #
    # What it must not do is print the word PASS over a record carrying a known
    # breach. CS-1146 was filed because the one report watching this lane said
    # PASS while a job sat 16s under the ceiling; a summary that still reads
    # PASS there reproduces the very defect.
    still_open = open_conditions(root)
    if still_open:
        print(
            "UNMET: no new drift - both pinned sets hold - but this record leaves "
            f"{len(still_open)} CS-896 condition(s) unmet:"
        )
        for condition in still_open:
            print(f"  - {condition}")
        return 0
    print(
        "PASS: every job's jitter is inside the stated ratchet, and both pinned "
        "sets - band versus jitter, and worst reading versus budget - hold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
