"""CS-900 - grade how CONCENTRATED the tier1 lane's cost is in one test.

WHY THIS EXISTS. CS-896 flipped tier1 to `pytest -n auto` and got 1.222x, not the
2x two cores suggest. The reason is not scheduler quality: xdist distributes by
test and a single test cannot be split across workers, so on `W` workers the
makespan floor is `max(t_max, T/W)`. When one test is a large share of the step,
buying runners moves nothing. Nothing in this tree graded that share, and a share
nothing grades is a number in prose, which `CLAUDE.md` section 4 forbids.

TWO MODES, AND ONLY ONE OF THEM TOUCHES THE NETWORK.

    python tools/tier1_concentration.py
        grade the tracked record
    python tools/tier1_concentration.py --refresh --before <id> --after <id>
        re-take the profile from `gh`, then grade it

The refresh is run BY HAND, like `tools/tier1_growth.py` and
`tools/tier2_headroom.py`, and never from a hook or a test: no test on this
project reaches the network. The two run ids are REQUIRED rather than guessed -
which pair of runs is a before and an after is a judgement about what changed
between them, and a tool that picked the two most recent would quietly restate
whatever the lane did last.

TWO LEVELS, BOTH DERIVED, NEITHER FITTED TO TODAY'S READING.

- HARD = 1/W, W being the job's worker count, TAKEN AGAINST THE WALL CLOCK.

  A CORRECTION THIS DOCSTRING OWES ITS OWN FIRST DRAFT, measured by an adversary
  on 2026-09-19. The first draft derived this level from the makespan floor and
  claimed the top test "stops being the binding term exactly at `t_max <= T/W`".
  That criterion is against the SERIAL TOTAL `T`; this tool divides by the STEP
  WALL CLOCK `S`, and the two agree only at W = 1. Both directions were measured
  false at W = 2 through this module's own `verdict`:

      T=440 t_max=165 S=220 - floor is T/W=220, so the top test is NOT binding,
                              and this level calls it a BREACH at 75 per cent
      T=440 t_max=231 S=462 - floor is t_max=231, so the top test IS binding,
                              and this level calls it a WARN at 50 per cent

  The ratio `S / max(t_max, T/W)` that separates them is 1.64 on this very lane
  (`docs/item_notes/phase4-followups-900.md` under CS-900), so the gap is not
  exotic. `T` is not obtainable here - the step prints only the top 15 phases
  over 5s - so the binding-term criterion CANNOT be graded by this tool, and
  saying so is why CS-900 stays open rather than closing on this level.

  WHAT THIS LEVEL IS, then, stated for what it does rather than for what the
  first draft wished it did: a share-of-wall-clock ceiling at 1/W. One test
  holding more than a 1/W share of the step it runs in is a lane whose length no
  scheduling of the remainder can bring under that share. W is read from the
  job's `runs-on` through :data:`RUNNER_WORKERS` below, and an entry the table
  lacks is REFUSED rather than defaulted. That refusal is the whole reason W is
  pinned instead of assumed.
- WARN = (CEILING - BUDGET) / BUDGET, both read from the parsed workflow at run
  time. RATIONALE: that numerator is the entire warn band. A single test costing
  more than the whole band can carry the lane from silent to red on one
  regression OF ITSELF - there is no reading in between for anything to warn on,
  which is precisely the ordering CS-1133 owns for the lane as a whole.

NEITHER LEVEL IS SPELLED IN THIS FILE OR IN THE RECORD, the discipline
`tools/tier1_growth.py` already uses for the band, and
`tests/test_tier1_concentration.py` greps both artifacts for either value.

THE DENOMINATOR IS THE STEP WALL CLOCK AND THAT IS NOT A FREE CHOICE. The `Unit
tests` step runs `--durations=15 --durations-min=5.0`, which prints only the top
fifteen phases over five seconds, so the SUM of test durations is not obtainable
without changing the invocation. The step's own start-to-finish is, it is what
every recorded share in `docs/LEDGER.md` already used, and it is the quantity the
makespan floor is about.

THE NUMERATOR SUMS A NODE ID'S PHASES. pytest prints setup, call and teardown as
separate lines, but all three run on ONE worker for one test, so the unsplittable
cost is their sum. It is a LOWER BOUND: a phase under five seconds never printed,
so a test's real total can only be larger than the figure recorded here, and a
verdict of BREACH can therefore never be an artefact of the parse.

A JOB WHOSE LOG CARRIED NO DURATIONS BLOCK SCORES UNMEASURED AND REDDENS. It must
never score zero per cent. This repository has repeatedly measured oracles that
passed for the sole reason that they could not observe their subject, so the
absent-block case is an offence with its own name rather than a share.

STALENESS IS THE STATED PRICE, as it is for `tools/tier1_growth.py`. The record is
as recent as its last refresh. What IS checked offline covers the structural half:
a job added, renamed or removed in the workflow is red against the record, and
both levels are read live.
"""

from __future__ import annotations

import argparse
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
# BARE name, the way tools/tier1_growth.py and tools/tier2_headroom.py do it.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

WORKFLOW_RELATIVE = ".github/workflows/tier1.yml"
RECORD_RELATIVE = "tools/tier1_concentration.json"

BUDGET_KEY = "TIER1_BUDGET_SECONDS"
CEILING_KEY = "TIER1_CEILING_SECONDS"

# HOW MANY TEST WORKERS EACH RUNNER LABEL GIVES `pytest -n auto`, WHICH IS ITS
# CPU COUNT. This is a LITERAL TABLE on purpose and its gaps are refusals.
#
# WHY NOT READ IT FROM THE LANE. The workflow's `Runner CPU count` step echoes
# `nproc`, and CS-1073 fenced this tree off deriving a pinned quantity from that
# echo: a value a run printed is a reading of one run, and a grader that takes its
# own denominator from the subject it grades moves with the subject.
#
# BASIS FOR THE ONE ENTRY. `docs/item_notes/phase4-followups-900.md` records the
# tier1 runner profile taken on the runner itself: GitHub `ubuntu-latest`,
# `nproc` 2, 7938 MB. GitHub's hosted standard Linux runner is a 2-core machine.
#
# A LABEL THAT IS NOT HERE IS AN ERROR, NOT A DEFAULT. Defaulting an unknown
# runner to any number would make the hard level a guess wearing a measurement's
# clothes, and the guess would be invisible. `worker_counts` raises instead.
RUNNER_WORKERS = {
    "ubuntu-latest": 2,
}

#: The step whose wall clock is the denominator. See the module docstring.
STEP_NAME = "Unit tests"

#: pytest's own heading for the block the numerator is read from.
DURATIONS_HEADING = "slowest 15 durations"

#: `gh run view --log` prefixes each line with job and step, both tab separated,
#: so a usable line splits into at least this many fields.
LOG_FIELDS = 3

RUN_FIELDS = ("run_id", "head_sha", "label", "profiles")
PROFILE_FIELDS = ("job", "step_seconds", "top_test", "top_test_centiseconds")

#: The two ends the acceptance asks for, exactly one row each.
RUN_LABELS = ("before", "after")

# EVERY DECLARED JOB NO RECORDED RUN HAS PROFILED YET, BECAUSE IT IS NEW (CS-1193).
#
# A job added to the workflow appears in no run the record already holds, so the
# absence offence reddens the shipped record on the very commit that adds it.
# No profile is made up for it, and no level moves; the ABSENCE is waived for the
# jobs named here and nothing else. A pending job that IS profiled is graded on
# its share exactly as any other.
#
# THE SET IS A TWO-WAY RATCHET, the rule tools/tier1_growth.py applies to its
# reading floor. A name profiled in EVERY recorded run is red in `grade`, which
# forces this literal down at the refresh that profiles it at both ends; a name
# the workflow does not declare is red in `grade_tree`, through
# `pending_undeclared`, so a synthetic workflow is graded on its own jobs alone.
# Basis: the wave-3 CI route ruling, condition A3, and for the fill shard the
# CS-1198 ruling's Route N.
PENDING_PROFILE: tuple[str, ...] = ("tests (hook shard)", "tests (fill shard)")

# Bounds every `gh` call. A hung credential prompt must not hang the refresh.
SUBPROCESS_TIMEOUT_SECONDS = 300

_SHA = re.compile(r"^[0-9a-f]{40}$")
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# One printed duration line: `158.74s call     tests/x.py::test_y`. The node id
# runs to end of line because a parametrised id can carry spaces.
_DURATION_LINE = re.compile(r"^(\d+)\.(\d\d)s (?:call|setup|teardown)\s+(\S.*)$")


class Profile(NamedTuple):
    """One job's concentration reading on one run.

    ``top_test`` and ``top_test_centiseconds`` are both None when that job's log
    carried no durations block. That pair is UNMEASURED, never a share.
    """

    job: str
    step_seconds: int
    top_test: str | None
    top_test_centiseconds: int | None

    @property
    def share(self) -> Fraction | None:
        """The top test's exact share of the step, or None when unmeasured."""
        if self.top_test_centiseconds is None or self.step_seconds <= 0:
            return None
        return Fraction(self.top_test_centiseconds, self.step_seconds * 100)


# ---------------------------------------------------------------------------
# The workflow - the jobs, the two levels, the worker counts
# ---------------------------------------------------------------------------


def _jobs_mapping(workflow_text: str) -> dict[str, Any]:
    """The workflow's jobs mapping.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        The mapping from job key to parsed job.

    Raises:
        ValueError: The workflow declares no usable jobs mapping.
    """
    parsed = yaml.safe_load(workflow_text)
    jobs = parsed.get("jobs") if isinstance(parsed, dict) else None
    if not isinstance(jobs, dict) or not jobs:
        message = "the workflow declares no jobs mapping"
        raise ValueError(message)
    return jobs


def _display_name(job_id: str, job: object) -> str:
    """One job's display name, as the API reports it.

    Args:
        job_id: The job's key, for messages.
        job: The parsed job.

    Returns:
        The display name.

    Raises:
        ValueError: The job declares no plain display name.
    """
    if not isinstance(job, dict):
        message = f"job {job_id!r} is not a mapping"
        raise ValueError(message)
    name = job.get("name")
    if not isinstance(name, str) or not name.strip():
        message = f"job {job_id!r} declares no display name"
        raise ValueError(message)
    if "${{" in name:
        message = f"job {job_id!r} names an expression this tool does not expand"
        raise ValueError(message)
    return name


def declared_jobs(workflow_text: str) -> list[str]:
    """Every job display name the workflow declares, in file order.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        The display names.

    Raises:
        ValueError: The workflow cannot be read into that list.
    """
    jobs = _jobs_mapping(workflow_text)
    return [_display_name(str(job_id), job) for job_id, job in jobs.items()]


def worker_counts(workflow_text: str) -> dict[str, int]:
    """Each job's test-worker count, from its `runs-on` through the literal table.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        Display name to worker count.

    Raises:
        ValueError: A job's `runs-on` is absent, is not a plain label, or is a
            label :data:`RUNNER_WORKERS` has no entry for.
    """
    jobs = _jobs_mapping(workflow_text)
    counts: dict[str, int] = {}
    for job_id, job in jobs.items():
        name = _display_name(str(job_id), job)
        runs_on = job.get("runs-on") if isinstance(job, dict) else None
        if not isinstance(runs_on, str):
            message = (
                f"job {job_id!r} declares runs-on {runs_on!r}, which is not a plain "
                "label this tool can price"
            )
            raise ValueError(message)
        label = runs_on.strip()
        if label not in RUNNER_WORKERS:
            message = (
                f"job {job_id!r} runs on {label!r}, which RUNNER_WORKERS has no entry "
                "for; add its measured CPU count rather than defaulting it"
            )
            raise ValueError(message)
        counts[name] = RUNNER_WORKERS[label]
    return counts


def declared_levels(workflow_text: str) -> tuple[int, int]:
    """The budget and the ceiling, read from the workflow's env block.

    Read here rather than imported from `tools/tier1_growth.py` on purpose: the
    two tools grade different things and neither should be able to break the
    other by changing a helper.

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


def warn_level(workflow_text: str) -> Fraction:
    """The warn level - the warn band as a fraction of the budget.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        The exact fraction.

    Raises:
        ValueError: Either level is unreadable.
    """
    budget, ceiling = declared_levels(workflow_text)
    return Fraction(ceiling - budget, budget)


def hard_levels(workflow_text: str) -> dict[str, Fraction]:
    """Each job's hard level - the reciprocal of its worker count.

    Args:
        workflow_text: The workflow file's text.

    Returns:
        Display name to the exact fraction.

    Raises:
        ValueError: A job's runner cannot be priced.
    """
    return {job: Fraction(1, workers) for job, workers in worker_counts(workflow_text).items()}


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def verdict(profile: Profile, warn: Fraction, hard: Fraction) -> str:
    """One profile's verdict against the two levels.

    Args:
        profile: The reading.
        warn: The warn level.
        hard: The job's hard level.

    Returns:
        ``UNMEASURED``, ``BREACH``, ``WARN`` or ``CLEAR``.
    """
    share = profile.share
    if share is None:
        return "UNMEASURED"
    if share > hard:
        return "BREACH"
    if share > warn:
        return "WARN"
    return "CLEAR"


def render_share(share: Fraction | None) -> str:
    """One share as a percentage to two places, or the unmeasured word.

    Rendered from integers, so no float enters a figure this project reports.

    Args:
        share: The exact share, or None.

    Returns:
        The rendering.
    """
    if share is None:
        return "UNMEASURED"
    # Rounded half up ON THE EXACT FRACTION, never through a float. Truncating
    # instead would render the warn level, an exact one seventh, a hundredth
    # BELOW the figure this item's ruling derived it as.
    hundredths = (share * 20000 + 1) // 2
    return f"{hundredths // 100}.{hundredths % 100:02d} per cent"


# ---------------------------------------------------------------------------
# The record - structure, then verdicts
# ---------------------------------------------------------------------------


def _detail(failure: BaseException) -> str:
    """One caught failure's TYPE and its authored first argument, never the object.

    Rendering an exception object whole can leak a path, an argv or a byte
    preview into a log; `tests/test_exception_rendering.py` refuses it outright.

    Args:
        failure: The caught exception.

    Returns:
        A one-line rendering safe to print.
    """
    first = failure.args[0] if failure.args and isinstance(failure.args[0], str) else ""
    return f"{type(failure).__name__}: {first}" if first else type(failure).__name__


def _whole(value: object) -> bool:
    """Whether a recorded value is a positive whole number rather than a bool.

    ``isinstance(True, int)`` is True in Python, so the bool is struck first.

    Args:
        value: The recorded value.

    Returns:
        True when it is a usable count.
    """
    return not isinstance(value, bool) and isinstance(value, int) and value > 0


def _field_offences(where: str, entry: dict[str, Any]) -> list[str]:
    """Every structural offence one profile row carries.

    Args:
        where: The row's position, for messages.
        entry: The profile row, already known to be a mapping with every field.

    Returns:
        Every offence. Empty means the row can be read as a profile.
    """
    offences = []
    if not isinstance(entry["job"], str) or not entry["job"].strip():
        offences.append(f"{where} names no job")
    if not _whole(entry["step_seconds"]):
        step = entry["step_seconds"]
        offences.append(f"{where} records step_seconds {step!r}, not a positive whole number")
    top = entry["top_test"]
    cost = entry["top_test_centiseconds"]
    if (top is None) != (cost is None):
        offences.append(f"{where} records half an unmeasured reading; both fields must be null")
    elif top is not None:
        if not isinstance(top, str) or "::" not in top:
            offences.append(f"{where} records top_test {top!r}, which is not a node id")
        if not _whole(cost):
            offences.append(
                f"{where} records top_test_centiseconds {cost!r}, not a positive whole number"
            )
    return offences


def _profile_offence(where: str, entry: object) -> str | Profile:
    """Grade one recorded profile's structure.

    Args:
        where: The row's position, for messages.
        entry: The profile row.

    Returns:
        The FIRST offence string, or the parsed profile.
    """
    if not isinstance(entry, dict):
        return f"{where} is not a mapping"
    unlisted = sorted(set(entry) - set(PROFILE_FIELDS))
    if unlisted:
        return f"{where} carries field(s) off the allowlist: {unlisted}"
    missing = [field for field in PROFILE_FIELDS if field not in entry]
    if missing:
        return f"{where} lacks field(s): {missing}"
    offences = _field_offences(where, entry)
    if offences:
        return offences[0]
    return Profile(
        job=entry["job"],
        step_seconds=entry["step_seconds"],
        top_test=entry["top_test"],
        top_test_centiseconds=entry["top_test_centiseconds"],
    )


def grade_profile(label: str, profile: Profile, warn: Fraction, hard: Fraction) -> list[str]:
    """Grade one profile's verdict. WARN is reported, not refused.

    Args:
        label: The run's label, for messages.
        profile: The reading.
        warn: The warn level.
        hard: The job's hard level.

    Returns:
        Every offence. Empty means this profile is acceptable.
    """
    call = verdict(profile, warn, hard)
    if call == "UNMEASURED":
        return [
            f"{label}: {profile.job!r} is UNMEASURED - its log carried no "
            f"{DURATIONS_HEADING!r} block, so no share was observed"
        ]
    if call == "BREACH":
        return [
            f"{label}: {profile.job!r} BREACHES the hard level - {profile.top_test} is "
            f"{render_share(profile.share)} of the {profile.step_seconds}s step, over "
            f"{render_share(hard)}, so the step cannot be shortened by adding workers"
        ]
    return []


def _grade_run_profiles(
    where: str,
    label: str,
    profiles: object,
    declared: Sequence[str],
    warn: Fraction,
    hard: dict[str, Fraction],
    pending: Sequence[str] = (),
) -> list[str]:
    """Grade one run's profile list, structurally and then on its verdicts.

    Args:
        where: The run's position, for messages.
        label: The run's label.
        profiles: The recorded profiles.
        declared: Every job the workflow declares.
        warn: The warn level.
        hard: Each job's hard level.
        pending: The jobs whose ABSENCE from this run is waived.

    Returns:
        Every offence.
    """
    if not isinstance(profiles, list) or not profiles:
        return [f"{where} carries no profiles"]
    offences: list[str] = []
    seen: list[str] = []
    for position, entry in enumerate(profiles):
        graded = _profile_offence(f"{where} profile {position}", entry)
        if isinstance(graded, str):
            offences.append(graded)
            continue
        seen.append(graded.job)
        if graded.job not in hard:
            offences.append(
                f"{where} profiles {graded.job!r}, which the workflow no longer declares"
            )
            continue
        offences.extend(grade_profile(label, graded, warn, hard[graded.job]))
    absent = [job for job in declared if job not in seen and job not in pending]
    if absent:
        offences.append(f"{where} ({label}) profiles no reading for: {absent}")
    repeated = sorted({job for job in seen if seen.count(job) > 1})
    if repeated:
        offences.append(f"{where} profiles job(s) twice: {repeated}")
    return offences


def _grade_run(
    where: str,
    run: object,
    declared: Sequence[str],
    warn: Fraction,
    hard: dict[str, Fraction],
    pending: Sequence[str] = (),
) -> tuple[list[str], str | None]:
    """Grade one recorded run.

    Args:
        where: The run's position, for messages.
        run: The recorded run.
        declared: Every job the workflow declares.
        warn: The warn level.
        hard: Each job's hard level.
        pending: The jobs whose absence is waived.

    Returns:
        ``(offences, label)``. The label is None when the row carried no usable one.
    """
    if not isinstance(run, dict):
        return ([f"{where} is not a mapping"], None)
    unlisted = sorted(set(run) - set(RUN_FIELDS))
    if unlisted:
        return ([f"{where} carries field(s) off the allowlist: {unlisted}"], None)
    missing = [field for field in RUN_FIELDS if field not in run]
    if missing:
        return ([f"{where} lacks field(s): {missing}"], None)
    label = run["label"]
    if label not in RUN_LABELS:
        return ([f"{where} is labelled {label!r}, not one of {list(RUN_LABELS)}"], None)
    offences: list[str] = []
    if not _whole(run["run_id"]):
        run_id = run["run_id"]
        offences.append(f"{where} records run_id {run_id!r}, not a positive whole number")
    head = run["head_sha"]
    if not isinstance(head, str) or not _SHA.match(head):
        offences.append(f"{where} records a head_sha that is not 40 hex characters")
    offences.extend(
        _grade_run_profiles(where, label, run["profiles"], declared, warn, hard, pending)
    )
    return (offences, label)


def grade(
    record: object, workflow_text: str, pending: Sequence[str] = PENDING_PROFILE
) -> list[str]:
    """Grade a parsed record against the live workflow.

    Args:
        record: The parsed record.
        workflow_text: The workflow file's text.
        pending: The pinned set of NEW jobs whose absence from a run is
            waived. A named job profiled in every run is an offence here; a
            name the workflow does not declare is graded by
            :func:`pending_undeclared`, which :func:`grade_tree` adds.

    Returns:
        Every offence. Empty means clean.
    """
    try:
        declared = declared_jobs(workflow_text)
        warn = warn_level(workflow_text)
        hard = hard_levels(workflow_text)
    except ValueError as failure:
        return [f"the workflow is unreadable: {_detail(failure)}"]

    if not isinstance(record, dict):
        return ["the record is not a mapping"]
    runs = record.get("runs")
    if not isinstance(runs, list) or not runs:
        return ["the record declares no runs list"]

    offences: list[str] = []
    labels: list[str] = []
    for index, run in enumerate(runs):
        run_offences, label = _grade_run(f"run {index}", run, declared, warn, hard, pending)
        offences.extend(run_offences)
        if label is not None:
            labels.append(label)
    offences.extend(_pending_reached(runs, declared, pending))

    offences.extend(
        f"the record carries {labels.count(wanted)} run(s) labelled {wanted!r}; "
        "the acceptance asks for exactly one at each end"
        for wanted in RUN_LABELS
        if labels.count(wanted) != 1
    )
    return offences


def grade_tree(root: Path) -> list[str]:
    """Grade the tracked record of one checkout.

    Args:
        root: The repository root.

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
    return grade(record, workflow_text) + pending_undeclared(workflow_text)


def _pending_reached(runs: list[Any], declared: Sequence[str], pending: Sequence[str]) -> list[str]:
    """The closing direction: every pending job every recorded run now profiles.

    Args:
        runs: The recorded runs.
        declared: Every job the workflow declares.
        pending: The pinned pending set.

    Returns:
        One offence per such job, sorted.
    """
    profiled_by_run = [
        {entry.get("job") for entry in run.get("profiles") or [] if isinstance(entry, dict)}
        for run in runs
        if isinstance(run, dict) and isinstance(run.get("profiles"), list)
    ]
    if not profiled_by_run:
        return []
    return [
        f"{job!r} is pending but every recorded run profiles it; drop it from the pending set"
        for job in sorted(set(pending) & set(declared))
        if all(job in profiled for profiled in profiled_by_run)
    ]


def pending_undeclared(workflow_text: str, pending: Sequence[str] | None = None) -> list[str]:
    """The pending set's opening direction: every name the workflow does not declare.

    A pending name matching no declared job waives nothing today and would
    silently waive a job added under that name later, so it is an offence.

    Args:
        workflow_text: The workflow file's text.
        pending: The set to check; the module's pinned set when omitted, read
            at call time.

    Returns:
        One offence per undeclared name, sorted. An unreadable workflow yields
        nothing here, because :func:`grade` has already reported it.
    """
    names = PENDING_PROFILE if pending is None else pending
    try:
        declared = set(declared_jobs(workflow_text))
    except ValueError:
        return []
    return [
        f"the pending set names {name!r}, which the workflow does not declare"
        for name in sorted(set(names) - declared)
    ]


# ---------------------------------------------------------------------------
# The report - what a session reads
# ---------------------------------------------------------------------------


def report(record: object, workflow_text: str) -> str:
    """The concentration report, as a session reads it.

    Args:
        record: The parsed record.
        workflow_text: The workflow file's text.

    Returns:
        The report text, 7-bit ASCII.
    """
    try:
        warn = warn_level(workflow_text)
        hard = hard_levels(workflow_text)
    except ValueError as failure:
        return f"tier1 concentration: the workflow is unreadable: {_detail(failure)}\n"

    lines = ["tier1 concentration - the most expensive single test as a share of its step"]
    hard_rendered = sorted({render_share(level) for level in hard.values()})
    lines.append(
        f"  levels: warn over {render_share(warn)} (the warn band over the budget), "
        f"hard over {'/'.join(hard_rendered)} (1 over the runner's worker count)"
    )
    runs = record.get("runs") if isinstance(record, dict) else None
    if not isinstance(runs, list):
        lines.append("  the record declares no runs list")
        return "\n".join(lines) + "\n"
    order = {label: position for position, label in enumerate(RUN_LABELS)}
    for run in sorted(
        (entry for entry in runs if isinstance(entry, dict)),
        key=lambda entry: order.get(str(entry.get("label")), len(order)),
    ):
        lines.append(
            f"  {run.get('label')}: run {run.get('run_id')} at {str(run.get('head_sha'))[:8]}"
        )
        profiles = run.get("profiles")
        if not isinstance(profiles, list):
            lines.append("    the run declares no profiles list")
            continue
        for entry in profiles:
            graded = _profile_offence("profile", entry)
            if isinstance(graded, str):
                lines.append(f"    {graded}")
                continue
            level = hard.get(graded.job)
            call = "no level" if level is None else verdict(graded, warn, level)
            # Bound to a local so the None case narrows for the type checker as
            # well as for the reader; `graded.share is None` cannot narrow a
            # sibling field of the tuple.
            cost = graded.top_test_centiseconds
            if cost is None:
                lines.append(
                    f"    {graded.job}: step {graded.step_seconds}s, "
                    f"no {DURATIONS_HEADING!r} block - {call}"
                )
                continue
            lines.append(
                f"    {graded.job}: step {graded.step_seconds}s, top test "
                f"{cost // 100}.{cost % 100:02d}s = "
                f"{render_share(graded.share)} - {call}"
            )
            lines.append(f"      {graded.top_test}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# The parsers - pure, so the by-hand refresh is testable offline
# ---------------------------------------------------------------------------


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


def step_seconds_by_job(payload: object) -> dict[str, int]:
    """Each completed job's :data:`STEP_NAME` wall clock, from one jobs payload.

    Args:
        payload: The parsed ``actions/runs/<id>/jobs`` response.

    Returns:
        Display name to whole seconds. A job with no such completed step is absent.

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
    found: dict[str, int] = {}
    for job in jobs:
        if not isinstance(job, dict) or job.get("status") != "completed":
            continue
        name = job.get("name")
        steps = job.get("steps")
        if not isinstance(name, str) or not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict) or step.get("name") != STEP_NAME:
                continue
            started = _parse_stamp(step.get("started_at"))
            completed = _parse_stamp(step.get("completed_at"))
            if started is None or completed is None:
                continue
            seconds = int((completed - started).total_seconds())
            if seconds > 0:
                found[name] = seconds
    return found


def top_test_by_job(log_text: str) -> dict[str, tuple[str, int]]:
    """Each job's most expensive single test, summed over its printed phases.

    `gh run view --log` prefixes every line with the job's display name and the
    step's name, both tab separated, which is what lets one log yield every job.

    Args:
        log_text: The downloaded log.

    Returns:
        Display name to ``(node id, centiseconds)``. A job whose
        :data:`STEP_NAME` printed no durations block is ABSENT rather than zero.
    """
    totals: dict[str, dict[str, int]] = {}
    inside: dict[str, bool] = {}
    for raw in log_text.splitlines():
        parts = raw.split("\t")
        if len(parts) < LOG_FIELDS:
            continue
        job, step, tail = parts[0], parts[1], parts[2]
        if step != STEP_NAME:
            continue
        body = tail.split(" ", 1)[1] if " " in tail else ""
        if DURATIONS_HEADING in body:
            inside[job] = True
            totals.setdefault(job, {})
            continue
        if not inside.get(job):
            continue
        match = _DURATION_LINE.match(body)
        if match is None:
            # The block ends at the first line that is not a duration.
            inside[job] = False
            continue
        node = match.group(3).strip()
        centiseconds = int(match.group(1)) * 100 + int(match.group(2))
        totals[job][node] = totals[job].get(node, 0) + centiseconds
    found: dict[str, tuple[str, int]] = {}
    for job, per_test in totals.items():
        if not per_test:
            continue
        # Ties broken by node id, so the reading does not turn on dict order.
        node, cost = max(per_test.items(), key=lambda item: (item[1], item[0]))
        found[job] = (node, cost)
    return found


# ---------------------------------------------------------------------------
# The refresh - the only network path, run by hand
# ---------------------------------------------------------------------------


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


def profile_run(run_id: int, fetch: Callable[[list[str]], str]) -> dict[str, Any]:
    """One run's profile row - every job's step wall clock and its top test.

    A job whose log carried no durations block is recorded with BOTH test fields
    null. It is not dropped and it is not zeroed: the grader reddens on it.

    Args:
        run_id: The workflow run.
        fetch: Runs one `gh` call.

    Returns:
        The row, without its label.

    Raises:
        RuntimeError: The run carried no completed :data:`STEP_NAME` step.
        ValueError: The jobs payload is unreadable.
    """
    payload = json.loads(
        fetch(["api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs?per_page=100"])
    )
    steps = step_seconds_by_job(payload)
    if not steps:
        message = f"run {run_id} carried no completed {STEP_NAME!r} step"
        raise RuntimeError(message)
    tops = top_test_by_job(fetch(["run", "view", str(run_id), "--log"]))
    head = ""
    for job in payload.get("jobs", []):
        if isinstance(job, dict) and isinstance(job.get("head_sha"), str):
            head = job["head_sha"]
            break
    profiles = []
    for name in sorted(steps):
        top = tops.get(name)
        profiles.append(
            {
                "job": name,
                "step_seconds": steps[name],
                "top_test": None if top is None else top[0],
                "top_test_centiseconds": None if top is None else top[1],
            }
        )
    return {"run_id": run_id, "head_sha": head, "profiles": profiles}


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
    before: int,
    after: int,
    fetch: Callable[[list[str]], str] = gh_fetch,
) -> Path:
    """Re-take the record from two named runs.

    Args:
        root: The repository root.
        before: The run id of the earlier profile.
        after: The run id of the later one.
        fetch: Runs one `gh` call; injected so the path is testable offline.

    Returns:
        The record path written.

    Raises:
        RuntimeError: Either run carried nothing to profile.
        ValueError: Either payload is unreadable.
    """
    runs = []
    for label, run_id in zip(RUN_LABELS, (before, after), strict=True):
        row = profile_run(run_id, fetch)
        runs.append(
            {
                "run_id": row["run_id"],
                "head_sha": row["head_sha"],
                "label": label,
                "profiles": row["profiles"],
            }
        )
    target = root / RECORD_RELATIVE
    text = json.dumps({"runs": runs}, indent=2, sort_keys=False) + "\n"
    _atomic_write(target, text.encode("ascii"))
    return target


def main(argv: list[str] | None = None) -> int:
    """Grade the tracked record, optionally refreshing it first.

    Args:
        argv: The arguments after the program name.

    Returns:
        0 when clean, 1 over any offence, 2 when a refresh could not run.
    """
    parser = argparse.ArgumentParser(
        description="CS-900 - report the tier1 lane's concentration in one test and "
        "grade it against the warn band and the runner's worker count."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="re-take the record from `gh`. Run BY HAND; never in a hook.",
    )
    parser.add_argument("--before", type=int, help="the run id of the earlier profile")
    parser.add_argument("--after", type=int, help="the run id of the later profile")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    if args.refresh:
        if args.before is None or args.after is None:
            print("FAIL: --refresh needs both --before and --after run ids.")
            return 2
        try:
            written = refresh(root, args.before, args.after)
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
    if PENDING_PROFILE:
        print(
            "PASS: no profiled job's most expensive test breaches its hard level; "
            f"not yet profiled, pending: {list(PENDING_PROFILE)}"
        )
        return 0
    print("PASS: no job's most expensive test breaches its hard level, and every job measured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
