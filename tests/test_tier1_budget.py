"""CS-896 - the tier 1 lane states one budget, reports its duration against it, and stops.

THE DEFECT THIS MODULE CLOSES. `timeout-minutes` is a RUNAWAY CUTOFF and the
workflow's own comment said so, but the lane had drifted to sit inside the noise
band of it: measured runs ranged from just inside the cutoff to CANCELLED past
it, on trees that differ by prose alone. So a breach arrived as a CANCELLATION,
and a cancelled run is evidence of nothing - nothing failed, nothing was
measured, and the next session reads it as flakiness.

THREE LEVELS, EACH WITH A DISTINCT JOB, and the whole point is that they are
three rather than one:

    budget   REPORTED every run. Over it warns loudly. Does NOT fail.
    ceiling  FAILS the lane, naming the number, BELOW the cutoff.
    cutoff   Cancels. POLICY, not a tunable. Evidence of nothing.

WHY THE BUDGET WARNS RATHER THAN FAILS. CONVENTIONS.md section 8 says tier 1
"must never be red", and the runner's own spread on a byte-identical tree is
wide, so a budget that hard-failed on noise would be red for no defect.
`tools/doc_budget.py` is the precedent and its header states the reasoning this
module inherits: "a warn that blocks a commit gets disabled and then enforces
nothing".

WHAT THIS MODULE GRADES, AND WHAT THE FIRST BUILD ONLY DESCRIBED. An adversarial
pass put twenty-six mutants through the first build of this module and eighteen
of them SURVIVED. Every section below exists because one of them did, and each
names the mutant it now kills:

- THE WORKFLOW IS PARSED, NEVER GREPPED. The first build asserted `"-n auto" in
  workflow_text`, and that string also occurs twice in the file's own COMMENTS.
  Deleting the real flag from the real step left the arm named
  `..._runs_in_parallel_...` green while the lane silently reverted to serial -
  straight back into the cancellation CS-896 was filed about. The same held for
  `if: always()` and for the whole start step. A substring search over a file
  that documents itself is a search of the documentation. So every structural
  property here reads the PARSED step: its `run`, its `if`, its name.
- THE REPORT STEP'S SHELL IS EXECUTED. The ceiling is the one mechanism CS-896
  adds - it FAILS the lane and names the number - and deleting its `exit 1` left
  every arm green. All four verdict branches are now run for real, and their
  EXIT CODES are the assertion.
- THE LEVELS ARE RATCHETED, NOT MERELY ORDERED. `budget < ceiling < cutoff` is
  satisfied by any three ascending numbers. Raising the cutoff alone passed;
  raising all three together passed; collapsing the budget to one second passed.
  The order relation grades the SHAPE and says nothing about the SIZE.
- EVERY TABLE IN THE GUARD IS PINNED IN BOTH DIRECTIONS AND EXERCISED MEMBER BY
  MEMBER. Nineteen number words, five bound nouns, the lane spellings, and ten
  narrative exclusions - each was deletable in silence, because the arms only
  ever exercised one member each. Two of the ten exclusions were graded; the
  module docstring claimed the exclusion "is itself graded".

THE PINS ARE A MECHANISM, NOT A RESTATEMENT. This module spells the recorded
levels, the table memberships and the xdist bound as literals and asserts they
EQUAL what the guard derives. That is CS-891's two-way shape: a change on either
side is red until the other side moves in the same diff, which turns a silent
edit into a number somebody has to defend. The one thing it must never be is a
bound computed from the thing it bounds - that tautology makes both directions
true by construction and is filed twice in this repository, so
:func:`test_the_recorded_levels_are_integer_literals_and_not_derived` reads the
guard's own source and refuses anything but a literal.

WHAT IS STILL NOT ASSERTED HERE. A wall-clock reading. The run itself reports
that, which is exactly what the acceptance clause asks for and exactly what a
test on a developer machine cannot stand in for.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIFT_GUARD_SOURCE = REPO_ROOT / "tools" / "drift_guard.py"

#: The guard letter this module grades. Pinned so a letter collision with a
#: guard added later is a loud failure here rather than a silent overwrite.
GUARD_ID = "k"

#: The one file allowed to state the numbers.
WORKFLOW_RELATIVE = ".github/workflows/tier1.yml"
PYPROJECT_RELATIVE = "pyproject.toml"
LEDGER_RELATIVE = "docs/LEDGER.md"

#: The job and the steps this module addresses BY NAME. A name is what a reader
#: and a citation can both survive a restructure on; a line number is not.
JOB_ID = "fast"
START_STEP = "Record the start"
SUITE_STEP = "Unit tests"
REPORT_STEP = "Duration against the budget"
FORMAT_STEP = "Format check (ruff format --check)"
TYPE_STEP = "Type check"

#: The job key GitHub reads as the runaway cutoff.
TIMEOUT_KEY = "timeout-minutes"

#: THE RECORDED LEVELS, PINNED. These are the two-way ratchet's other half: the
#: guard reads the workflow, this reads the guard, and the three only agree when
#: a change moved all of them together.
EXPECTED_RECORDED_BUDGET = 420
EXPECTED_RECORDED_CEILING = 480
EXPECTED_POLICY_CUTOFF_MINUTES = 10
EXPECTED_LANE_WINDOW = 6

#: Every constant that must be a plain integer literal in the guard's source.
LITERAL_PINS = (
    "TIER1_RECORDED_BUDGET",
    "TIER1_RECORDED_CEILING",
    "TIER1_POLICY_CUTOFF_MINUTES",
    "TIER1_LANE_WINDOW",
)

EXPECTED_NUMBER_WORDS = (
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "fifteen",
    "twenty",
    "thirty",
    "forty",
    "forty-five",
    "sixty",
    "ninety",
)

EXPECTED_UNIT_WORDS = (
    "milliseconds?",
    "msecs?",
    "minutes?",
    "mins?",
    "seconds?",
    "secs?",
    "hours?",
    "hrs?",
    "ms",
)

EXPECTED_BOUND_NOUNS = ("target", "budget", "ceiling", "cutoff", "limit")

EXPECTED_LANE_SPELLINGS = (r"tier[\s-]?1", r"fast lane")

EXPECTED_NARRATIVE_EXACT = (
    "docs/LEDGER.md",
    "ROADMAP.md",
    "BACKLOG.md",
    "WAKEUP_NOTES.md",
    "CS-NEXT-SESSION.txt",
    "docs/GATED.md",
    "docs/history_notes.md",
    "docs/item_notes.md",
)

EXPECTED_NARRATIVE_PREFIXES = (
    "docs/item_notes/",
    "docs/_archive/",
    "memory/",
)

#: The pytest-xdist requirement, pinned WHOLE rather than probed for an upper
#: bound alone. Removing the bound entirely was killed by nothing; the comment
#: above it in pyproject.toml argues at length that the bound is load-bearing,
#: and an argument nothing enforces is a comment.
EXPECTED_XDIST_REQUIREMENT = "pytest-xdist>=3.8,<4"

#: The two by-line pointers docs/LEDGER.md holds into the workflow. Spelled as
#: bare integers, never as `<path>:<number>`, because that form would enrol this
#: module in tests/test_docs_citations.py's own pinned pointer set.
STALE_LEDGER_POINTERS = (130, 250)

#: How wide a run of ledger lines counts as one correction record.
LEDGER_CORRECTION_WINDOW = 15

#: Parsed out of the report step's own output line.
REPORTED_LINE = re.compile(r"tier 1 took (-?\d+)s - ([a-zA-Z ]+) \(")

#: The sentence every refusal branch of the report step prints.
REFUSAL = "Refusing to report a duration this job did not measure."

#: The harness-to-shell gap the windows-latest leg of run 35330059133 spent
#: between staging a start and the step's own clock read, in seconds. It is
#: the reproduction's STALL and never a tolerance - CS-1145's whole finding is
#: that no constant is the right bound for this gap.
CI_MEASURED_STALL = 3

#: The fixed tolerance CS-1145 removed. Kept as the reproduction's own
#: anti-vacuity control: the stall above must push the reading STRICTLY past
#: this, or the arm reproduces nothing and passes for that reason.
SUPERSEDED_TOLERANCE = 2


BASH = shutil.which("bash")

#: Seconds allowed for the extracted report step, which is arithmetic and two
#: echoes. Generous on purpose - this bounds a hang, it does not police speed.
REPORT_STEP_TIMEOUT = 120

#: EXECUTING THE STEP NEEDS A SHELL, AND THE SKIP IS NARROW ON PURPOSE. The
#: workflow declares `shell: bash`, so the environment these arms are about has
#: one by definition; only a developer machine without one can miss them, and it
#: says so rather than reporting a pass over nothing.
needs_bash = pytest.mark.skipif(
    BASH is None, reason="no bash on PATH; the report step's shell was NOT executed"
)


def _load_drift_guard() -> Any:
    """Load the guard tool from source, the way its sibling modules do.

    Returns:
        The loaded module.

    Raises:
        ImportError: The source could not be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_drift_guard", DRIFT_GUARD_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {DRIFT_GUARD_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift_guard = _load_drift_guard()


# ---------------------------------------------------------------------------
# Fixtures and helpers - synthetic trees
# ---------------------------------------------------------------------------


def workflow_source(budget: str = "420", ceiling: str = "480", cutoff: str = "10") -> str:
    """A minimal tier 1 workflow carrying the three numbers.

    The DEFAULTS are deliberately the shipped ones so an arm that mutates one
    of them is mutating against a green floor. Every value is a string so a
    non-integer can be planted without changing the shape.

    Args:
        budget: The value for the budget key.
        ceiling: The value for the ceiling key.
        cutoff: The value for ``timeout-minutes``.

    Returns:
        The workflow text.
    """
    return (
        "name: tier1\n"
        "env:\n"
        f"  TIER1_BUDGET_SECONDS: '{budget}'\n"
        f"  TIER1_CEILING_SECONDS: '{ceiling}'\n"
        "jobs:\n"
        "  fast:\n"
        f"    timeout-minutes: {cutoff}\n"
    )


def restatement(
    bound: str = "target",
    lane: str = "Tier 1 - fast lane",
    amount: str = "3",
    unit: str = "minutes",
) -> str:
    """Assemble a sentence that STATES a tier 1 duration target.

    ASSEMBLED RATHER THAN WRITTEN OUT, AND THAT IS NOT A TRICK. The guard reads
    file TEXT, so a plant written as one literal would make THIS MODULE a second
    owner of the number and redden
    :func:`test_no_tracked_file_outside_the_owner_states_a_tier_one_duration_target`
    against the real tree. Composing it at call time keeps the plant exact and
    keeps the carrier clean. Every text-scanning guard in this tree faces the
    same problem and solves it the same way.

    Args:
        bound: The bound noun the sentence hangs the number on.
        lane: The spelling of the lane's name.
        amount: The quantity.
        unit: The unit the quantity is spelled in.

    Returns:
        A one-line restatement.
    """
    return " ".join([lane + ",", bound, "under", amount, unit + "."])


def split_restatement() -> str:
    """A restatement whose bound noun sits on a DIFFERENT line from its number.

    THE SHAPE PROSE ACTUALLY TAKES. The first build required the bound noun on
    the duration's own line, so an ordinary wrapped sentence stated the target
    invisibly.

    Returns:
        A two-line restatement.
    """
    return "\n".join(
        [
            " ".join(["Tier 1 - the fast lane", "budget"]),
            " ".join(["is", "510", "seconds", "on the runner."]),
        ]
    )


#: Every duration spelling the scan must see, ASSEMBLED FROM FRAGMENTS for
#: :func:`restatement`'s reason. Each was MEASURED silent against the first
#: build, and the first two matter most: the bare unit suffix is what the
#: workflow's own report prints AND what the guard's own detail lines print, so
#: it was the one string the guard could not see itself say.
DURATION_SPELLINGS: tuple[tuple[str, str], ...] = (
    ("a unit word", " ".join(["510", "seconds"])),
    ("a bare second suffix", "".join(["510", "s"])),
    ("a bare minute suffix", "".join(["9", "m"])),
    ("a compound", "".join(["8", "m30", "s"])),
    ("a clock reading", ":".join(["0", "08", "30"])),
    ("hours", " ".join(["0.15", "hours"])),
    ("milliseconds", " ".join(["510000", "ms"])),
    ("a number word", " ".join(["three", "minutes"])),
)


def build_tree(root: Path, source: str) -> list[Path]:
    """Write a synthetic tree carrying one workflow.

    Args:
        root: The tree root, which need not exist.
        source: The workflow text.

    Returns:
        The enumerated file list to hand the guard.
    """
    workflow = root / ".github" / "workflows" / "tier1.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(source, encoding="utf-8", newline="\n")
    return [workflow]


def plant_file(root: Path, relative: str, text: str) -> Path:
    """Write one extra file into a synthetic tree and PROVE it landed.

    A plant that never applied is indistinguishable from one that survived
    (CONVENTIONS.md section 7.2), so this refuses to return a plant it did not
    make.

    Args:
        root: The tree root.
        relative: The repo-relative path to write.
        text: The file's content.

    Returns:
        The path written.
    """
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    assert path.read_text(encoding="utf-8") == text, "the plant did not apply"
    return path


def run_guard(root: Path, files: list[Path]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Run the budget guard against one tree, with the SHIPPED pins.

    Args:
        root: The tree root.
        files: The enumerated file list.

    Returns:
        (the guard record, its skip records).
    """
    guard, skips = drift_guard.guard_tier1_budget(root, files)
    return guard, skips


def run_guard_pinned_to(
    root: Path, files: list[Path], budget: str, ceiling: str, cutoff: str
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Run the budget guard with the ratchet SATISFIED by construction.

    WHY THIS EXISTS. Every order arm below plants numbers that are deliberately
    out of order, and every one of those also breaches the shipped ratchet. Left
    at the shipped pins each arm would go red for two reasons at once, and
    deleting the order relation entirely would leave all of them green - the
    order check would be graded by nothing. Handing the guard pins that match
    the plant isolates the relation.

    Args:
        root: The tree root.
        files: The enumerated file list.
        budget: The budget the plant states.
        ceiling: The ceiling the plant states.
        cutoff: The cutoff the plant states, in minutes.

    Returns:
        (the guard record, its skip records).
    """
    guard, skips = drift_guard.guard_tier1_budget(
        root,
        files,
        recorded_budget=int(budget),
        recorded_ceiling=int(ceiling),
        policy_cutoff_minutes=int(cutoff),
    )
    return guard, skips


def rendered(guard: dict[str, Any]) -> str:
    """Join a guard's detail into one searchable string.

    Args:
        guard: The guard record.

    Returns:
        Every detail line, newline separated.
    """
    return "\n".join(guard["detail"])


@pytest.fixture
def green_tree(tmp_path: Path) -> tuple[Path, list[Path]]:
    """A synthetic tree the budget guard reports PASS about.

    A red on a tree that was never green attributes to nothing, so every
    mutation arm below starts from this floor.

    Args:
        tmp_path: pytest temporary directory.

    Returns:
        (the tree root, the enumerated file list).
    """
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source())
    return root, files


# ---------------------------------------------------------------------------
# Helpers - the workflow as a PARSED document, never as text
# ---------------------------------------------------------------------------


def workflow_document() -> dict[str, Any]:
    """The shipped workflow, parsed.

    THE WHOLE POINT OF THIS FUNCTION IS THAT IT IS NOT A SUBSTRING SEARCH. This
    workflow documents itself heavily, so its comments spell every flag and key
    the live steps use; a text scan cannot tell the two apart and a mutation
    that deletes the live one is invisible to it.

    Returns:
        The parsed document.
    """
    text = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8")
    document = yaml.safe_load(text)
    assert isinstance(document, dict), f"{WORKFLOW_RELATIVE} did not parse to a mapping"
    return document


def fast_job() -> dict[str, Any]:
    """The one job this lane runs.

    Returns:
        The parsed job.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"
    job = jobs.get(JOB_ID)
    assert isinstance(job, dict), f"{WORKFLOW_RELATIVE} declares no job named {JOB_ID!r}"
    return job


def workflow_steps() -> list[dict[str, Any]]:
    """Every step of the one job, in order.

    Returns:
        The parsed steps.
    """
    listed = fast_job().get("steps")
    assert isinstance(listed, list), f"the {JOB_ID!r} job declares no step list"
    return [step for step in listed if isinstance(step, dict)]


def step_named(name: str) -> dict[str, Any]:
    """One step, addressed BY NAME.

    Args:
        name: The step's ``name`` key.

    Returns:
        The parsed step.
    """
    matched = [step for step in workflow_steps() if step.get("name") == name]
    present = [str(step.get("name")) for step in workflow_steps()]
    assert len(matched) == 1, f"expected exactly one step named {name!r}; the steps are {present}"
    return matched[0]


def workflow_env() -> dict[str, str]:
    """The workflow-level env block, as strings.

    Returns:
        The declared environment.
    """
    declared = workflow_document().get("env")
    assert isinstance(declared, dict), f"{WORKFLOW_RELATIVE} declares no env block"
    return {str(key): str(value) for key, value in declared.items()}


# ---------------------------------------------------------------------------
# Helpers - running the report step's own shell
# ---------------------------------------------------------------------------


def run_report_step(tmp_path: Path, started: str | None) -> subprocess.CompletedProcess[str]:
    """Execute the report step's `run:` script exactly as the runner would.

    GitHub invokes a `shell: bash` step as `bash --noprofile --norc -eo
    pipefail <file>`, and that is reproduced here rather than approximated,
    because two of the three refusal branches below only exist BECAUSE of how
    that shell behaves: an arithmetic syntax error under `-e` does not stop the
    script, it leaves the variable empty and carries on.

    Args:
        tmp_path: pytest temporary directory.
        started: What to put in TIER1_STARTED, or None to leave it unset.

    Returns:
        The completed process.
    """
    assert BASH is not None, "guarded by needs_bash"
    script = step_named(REPORT_STEP)["run"]
    assert isinstance(script, str), "the report step declares no run script"
    path = tmp_path / "report.sh"
    path.write_bytes(script.encode("utf-8"))

    env = dict(os.environ)
    env.update(workflow_env())
    env["GITHUB_STEP_SUMMARY"] = (tmp_path / "summary.md").as_posix()
    env.pop("TIER1_STARTED", None)
    if started is not None:
        env["TIER1_STARTED"] = started

    return subprocess.run(
        [BASH, "--noprofile", "--norc", "-eo", "pipefail", str(path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        # BOUNDED because CS-908's guard grades every subprocess in the tree, and
        # because an unbounded child here would burn the very CI budget this
        # module exists to measure. The step is arithmetic and two echoes.
        timeout=REPORT_STEP_TIMEOUT,
    )


def report_for_elapsed(tmp_path: Path, elapsed: int) -> subprocess.CompletedProcess[str]:
    """Run the report step as though the job had taken ``elapsed`` seconds.

    Args:
        tmp_path: pytest temporary directory.
        elapsed: The duration to stage.

    Returns:
        The completed process.
    """
    return run_report_step(tmp_path, str(int(time.time()) - elapsed))


def report_with_bounded_reading(
    tmp_path: Path, staged: int, stall: int = 0
) -> tuple[subprocess.CompletedProcess[str], int]:
    """Run the report step for ``staged`` seconds and bound what it may report.

    THE BOUND IS ARITHMETIC, NOT A TOLERANCE. The step computes its figure as
    ``$(date +%s) - TIER1_STARTED``, so the reading is the staged duration PLUS
    whatever wall clock passed between staging the start and the shell reading
    its own clock. A fixed allowance for that gap is a guess about the runner,
    and CS-1145 is the measurement that falsified the guess: the windows-latest
    leg of run 35330059133 spent three seconds there against a two second
    window, and nothing about the workflow was wrong.

    SO THE GAP IS BRACKETED RATHER THAN ESTIMATED. The start is computed from a
    clock read taken before the spawn and the clock is read again after it
    returns; ``floor`` is monotonic, so the shell's own read lies between those
    two, and the step can report no less than ``staged`` and no more than the
    bound returned here. A slower runner WIDENS the bracket instead of breaking
    it, and on a fast one the bracket closes to nothing - so the arm stays
    exactly as tight as the run it is measuring, which a constant cannot.

    Args:
        tmp_path: pytest temporary directory.
        staged: The duration to stage.
        stall: Seconds to wait between staging the start and running the step,
            for the arm that reproduces a loaded runner on an idle machine.

    Returns:
        (the completed process, the largest reading the staged start explains).
    """
    started = int(time.time()) - staged
    if stall:
        time.sleep(stall)
    proc = run_report_step(tmp_path, str(started))
    return proc, int(time.time()) - started


def reported(proc: subprocess.CompletedProcess[str]) -> tuple[int, str]:
    """The duration and the verdict the step printed.

    Args:
        proc: The completed process.

    Returns:
        (the reported seconds, the verdict).
    """
    match = REPORTED_LINE.search(proc.stdout)
    assert match is not None, f"the step printed no duration line:\n{proc.stdout}\n{proc.stderr}"
    return int(match.group(1)), match.group(2).strip()


def refused(proc: subprocess.CompletedProcess[str]) -> tuple[bool, str]:
    """Whether the step REFUSED, in the only sense that acts.

    THREE CONJUNCTS, AND THE THIRD IS THE ONE THAT WAS MISSING. A refusal that
    prints its sentence and does not stop is not a refusal: MEASURED, deleting
    the `exit 1` from the missing-start branch left the step printing the
    refusal and then falling through to compute a duration from an unset start
    - which bash reads as zero, making the elapsed the whole Unix epoch, over
    the ceiling, and non-zero for entirely the wrong reason. Both weaker arms
    passed on it. So a refusal must also have reported NO verdict.

    Args:
        proc: The completed process.

    Returns:
        (whether it refused, why not).
    """
    if proc.returncode == 0:
        return False, "it exited 0"
    if REFUSAL not in proc.stdout:
        return False, "it never printed the refusal"
    reported_anyway = REPORTED_LINE.search(proc.stdout)
    if reported_anyway is not None:
        return False, f"it refused and then reported anyway: {reported_anyway.group(0)!r}"
    return True, ""


def staged_budget() -> int:
    """The budget the shipped workflow states.

    Returns:
        The budget in seconds.
    """
    return int(workflow_env()["TIER1_BUDGET_SECONDS"])


def staged_ceiling() -> int:
    """The ceiling the shipped workflow states.

    Returns:
        The ceiling in seconds.
    """
    return int(workflow_env()["TIER1_CEILING_SECONDS"])


# ---------------------------------------------------------------------------
# Registration - a guard the runner never names never runs
# ---------------------------------------------------------------------------


def test_the_budget_guard_is_registered_and_reported() -> None:
    guards, _skips, _source = drift_guard.run_all(REPO_ROOT)
    ids = [guard["id"] for guard in guards]

    assert GUARD_ID in ids, f"guard {GUARD_ID!r} is not registered: {ids}"
    assert ids == sorted(ids), "guards are reported in id order"
    assert len(ids) == len(set(ids)), f"a guard letter is used twice: {ids}"


def test_the_floor_is_green_or_every_mutation_below_proves_nothing(
    green_tree: tuple[Path, list[Path]],
) -> None:
    root, files = green_tree

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "PASS", rendered(guard)
    assert guard["id"] == GUARD_ID, f"guard letter moved: {guard['id']}"


# ---------------------------------------------------------------------------
# The shipped tree
# ---------------------------------------------------------------------------


def test_the_shipped_workflow_states_the_budget_the_ceiling_and_the_cutoff() -> None:
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)

    guard, _skips2 = run_guard(REPO_ROOT, files)

    assert guard["status"] == "PASS", rendered(guard)


def test_the_detail_reports_all_three_levels_so_a_reader_can_see_the_order() -> None:
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)

    guard, _skips2 = run_guard(REPO_ROOT, files)
    text = rendered(guard)

    for level in ("budget", "ceiling", "cutoff"):
        assert level in text.lower(), f"the detail never mentions the {level}:\n{text}"
    assert WORKFLOW_RELATIVE in text, f"the detail never names the owner:\n{text}"


def test_no_tracked_file_outside_the_owner_states_a_tier_one_duration_target() -> None:
    """THE ACCEPTANCE-FACING ARM. One owner, checked over the real tree."""
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)

    guard, _skips2 = run_guard(REPO_ROOT, files)

    assert guard["status"] == "PASS", (
        "a tracked file other than the owner states a tier 1 duration target:\n" + rendered(guard)
    )


# ---------------------------------------------------------------------------
# The keys - exactly one owner, and it parses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["TIER1_BUDGET_SECONDS", "TIER1_CEILING_SECONDS"])
def test_a_deleted_env_key_turns_the_guard_red(key: str, tmp_path: Path) -> None:
    """The guard must die if the env key is deleted - a budget nobody states is no budget."""
    source = workflow_source()
    stripped = "\n".join(line for line in source.splitlines() if key not in line) + "\n"
    assert stripped != source, "the deletion did not apply"
    root = tmp_path / "tree"
    files = build_tree(root, stripped)

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "FAIL", rendered(guard)
    assert key in rendered(guard), f"the red does not name the missing key:\n{rendered(guard)}"


@pytest.mark.parametrize("key", ["TIER1_BUDGET_SECONDS", "TIER1_CEILING_SECONDS"])
def test_a_second_copy_of_an_env_key_turns_the_guard_red(key: str, tmp_path: Path) -> None:
    """Two statements of one number is the exact drift this guard exists to catch."""
    source = workflow_source()
    duplicated = source + f"  {key}: '999'\n"
    root = tmp_path / "tree"
    files = build_tree(root, duplicated)

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "FAIL", rendered(guard)
    assert key in rendered(guard), f"the red does not name the duplicated key:\n{rendered(guard)}"


def test_a_non_integer_budget_turns_the_guard_red(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source(budget="soon"))

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "FAIL", rendered(guard)


def test_a_missing_timeout_minutes_turns_the_guard_red(tmp_path: Path) -> None:
    """The cutoff is one of the three levels; a guard that cannot read it grades two."""
    source = workflow_source()
    stripped = "\n".join(line for line in source.splitlines() if "timeout-minutes" not in line)
    root = tmp_path / "tree"
    files = build_tree(root, stripped + "\n")

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "FAIL", rendered(guard)
    assert "timeout-minutes" in rendered(guard)


# ---------------------------------------------------------------------------
# The ordering - budget < ceiling < cutoff, graded with the ratchet satisfied
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("budget", "ceiling", "why"),
    [
        ("555", "555", "a ceiling equal to the budget leaves no warn band"),
        ("600", "555", "a ceiling below the budget can never be reached second"),
    ],
)
def test_a_ceiling_not_above_the_budget_turns_the_guard_red(
    budget: str, ceiling: str, why: str, tmp_path: Path
) -> None:
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source(budget=budget, ceiling=ceiling))

    guard, _skips = run_guard_pinned_to(root, files, budget, ceiling, "10")

    assert guard["status"] == "FAIL", f"{why}, and the guard passed:\n{rendered(guard)}"
    assert "out of order" in rendered(guard), (
        f"{why}, and the red came from something other than the order:\n{rendered(guard)}"
    )


@pytest.mark.parametrize(
    ("ceiling", "why"),
    [
        ("600", "a ceiling AT the cutoff is cancelled before it can fail"),
        ("900", "a ceiling above the cutoff is unreachable - the run is cancelled first"),
    ],
)
def test_a_ceiling_not_below_the_cutoff_turns_the_guard_red(
    ceiling: str, why: str, tmp_path: Path
) -> None:
    """THE ARM THE ITEM EXISTS FOR.

    A ceiling at or above the cutoff hands the breach back to the canceller,
    which is the state CS-896 was filed about: a breach that arrives as a
    cancellation reports nothing and names no number.
    """
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source(ceiling=ceiling, cutoff="10"))

    guard, _skips = run_guard_pinned_to(root, files, "420", ceiling, "10")

    assert guard["status"] == "FAIL", f"{why}, and the guard passed:\n{rendered(guard)}"
    assert "out of order" in rendered(guard), (
        f"{why}, and the red came from something other than the order:\n{rendered(guard)}"
    )


def test_raising_the_cutoff_does_not_silence_the_ordering_check(tmp_path: Path) -> None:
    """The ordering is a relation, not three independent numbers.

    Without this, a session could close a ceiling breach by raising
    `timeout-minutes` - the exact move the item note forbids in capitals - and
    the guard would go green on it.
    """
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source(budget="900", ceiling="800", cutoff="60"))

    guard, _skips = run_guard_pinned_to(root, files, "900", "800", "60")

    assert guard["status"] == "FAIL", rendered(guard)
    assert "out of order" in rendered(guard), rendered(guard)


# ---------------------------------------------------------------------------
# The ratchet - the SIZE, which the order relation says nothing about
# ---------------------------------------------------------------------------


def test_the_recorded_levels_are_what_this_module_pins() -> None:
    """The two-way pin itself. A change on either side is red until both move."""
    assert drift_guard.TIER1_RECORDED_BUDGET == EXPECTED_RECORDED_BUDGET
    assert drift_guard.TIER1_RECORDED_CEILING == EXPECTED_RECORDED_CEILING
    assert drift_guard.TIER1_POLICY_CUTOFF_MINUTES == EXPECTED_POLICY_CUTOFF_MINUTES
    assert EXPECTED_RECORDED_BUDGET < EXPECTED_RECORDED_CEILING, (
        "the pinned levels are themselves out of order"
    )
    assert (
        EXPECTED_RECORDED_CEILING < EXPECTED_POLICY_CUTOFF_MINUTES * drift_guard.SECONDS_PER_MINUTE
    ), "the pinned ceiling does not sit below the pinned cutoff"


def test_the_recorded_levels_are_integer_literals_and_not_derived() -> None:
    """THE TAUTOLOGY THAT DISARMS EVERY PIN, AND IT IS ONE LINE.

    ``TIER1_RECORDED_BUDGET = _read_the_workflow()`` makes the ratchet agree by
    construction: both directions permanently satisfied, every future inflation
    free, and no number in the diff to query. By import time a constant is just
    an int, so provenance has to be read out of the SOURCE.
    """
    tree = ast.parse(DRIFT_GUARD_SOURCE.read_text(encoding="utf-8"))
    literals: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            targets: list[ast.expr] = [node.target]
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in LITERAL_PINS:
                literals[target.id] = node.value

    missing = [name for name in LITERAL_PINS if name not in literals]
    assert not missing, f"the guard binds no module-scope constant named: {missing}"
    derived = [
        name
        for name, value in literals.items()
        if not (isinstance(value, ast.Constant) and isinstance(value.value, int))
    ]
    assert not derived, (
        "these are not integer literals, so they may be derived from what they bound: "
        f"{sorted(derived)}"
    )


@pytest.mark.parametrize(
    ("budget", "ceiling", "why"),
    [
        ("421", "480", "one second of inflation is still inflation"),
        ("419", "480", "a slack maximum is banked room for an append nobody defends"),
        ("420", "481", "the ceiling inflated"),
        ("420", "479", "the ceiling was lowered and the record was not"),
        ("3000", "3500", "both levels inflated together, which the order relation permits"),
        ("1", "2", "both levels collapsed together, which the order relation also permits"),
    ],
)
def test_a_level_that_disagrees_with_its_recorded_maximum_turns_the_guard_red(
    budget: str, ceiling: str, why: str, tmp_path: Path
) -> None:
    """MEASURED SILENT ON THE FIRST BUILD, in every one of these directions."""
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source(budget=budget, ceiling=ceiling))

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "FAIL", f"{why}, and the guard passed:\n{rendered(guard)}"
    assert "recorded maximum" in rendered(guard), (
        f"{why}, and the red came from something other than the ratchet:\n{rendered(guard)}"
    )


@pytest.mark.parametrize(
    ("cutoff", "why"),
    [
        ("60", "raising the runaway cutoff ALONE was the cheapest inflation of all"),
        ("5", "lowering it hands a slow run back to the canceller, which reports nothing"),
    ],
)
def test_moving_the_runaway_cutoff_at_all_turns_the_guard_red(
    cutoff: str, why: str, tmp_path: Path
) -> None:
    """The workflow forbids this in capitals; before this arm nothing enforced it.

    Raising `timeout-minutes` alone kept the order relation intact - a bigger
    cutoff is still above the ceiling - so every arm stayed green while the only
    signal that the lane is growing was removed.
    """
    root = tmp_path / "tree"
    files = build_tree(root, workflow_source(cutoff=cutoff))

    guard, _skips = run_guard(root, files)

    assert guard["status"] == "FAIL", f"{why}, and the guard passed:\n{rendered(guard)}"
    assert "NOT A TUNABLE" in rendered(guard), (
        f"{why}, and the red does not say the cutoff is policy:\n{rendered(guard)}"
    )


def test_the_shipped_workflow_states_exactly_the_recorded_levels() -> None:
    """The other half of the ratchet, read off the PARSED workflow.

    THE CUTOFF IS READ OFF EVERY JOB AND NOT OFF ONE OF THEM. It used to read
    `fast_job()`, which was the whole lane when it was written and is now one
    shard of several - a shard that carried a different cutoff would have been
    invisible here (CS-1060).
    """
    assert staged_budget() == EXPECTED_RECORDED_BUDGET
    assert staged_ceiling() == EXPECTED_RECORDED_CEILING
    stated = sorted({job.get(TIMEOUT_KEY) for job in every_parsed_job().values()}, key=repr)
    assert stated == [EXPECTED_POLICY_CUTOFF_MINUTES], (
        f"the jobs state cutoffs {stated}, not exactly {EXPECTED_POLICY_CUTOFF_MINUTES}"
    )


# ---------------------------------------------------------------------------
# One owner - the restatement scan, its tables, and its window
# ---------------------------------------------------------------------------


def test_a_second_file_restating_the_target_turns_the_guard_red(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """The guard must die if a second file restates the number."""
    root, files = green_tree
    planted = plant_file(root, "CONVENTIONS.md", f"## CI\n\n{restatement()}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", rendered(guard)
    assert "CONVENTIONS.md" in rendered(guard), (
        f"the red does not name the second owner:\n{rendered(guard)}"
    )


@pytest.mark.parametrize(("label", "spelling"), DURATION_SPELLINGS)
def test_every_spelling_of_a_duration_is_a_second_owner(
    label: str, spelling: str, green_tree: tuple[Path, list[Path]]
) -> None:
    """EIGHT SPELLINGS, SIX OF WHICH WERE MEASURED SILENT.

    The bare unit suffix is the one that mattered most: it is what the
    workflow's own duration report prints and what this guard's own detail lines
    print, so the guard could not see the exact string its subject says.
    """
    root, files = green_tree
    sentence = " ".join(["Tier 1 - fast lane,", "budget", "under", spelling + "."])
    planted = plant_file(root, "docs/OPERATIONS.md", f"## CI\n\n{sentence}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"{label} was not read as a stated duration:\n{rendered(guard)}"
    )


def test_a_bare_number_hung_off_a_bound_noun_is_a_second_owner(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """NO UNIT ANYWHERE, AND EVERY OTHER SCAN NEEDS ONE.

    MEASURED silent: one README line spelling all three levels as
    "budget: <n> (ceiling <n>, cutoff <n>)" restated the whole set and nothing
    saw it, because the unit is carried by the nouns rather than written down.
    """
    root, files = green_tree
    sentence = " ".join(
        [
            "Tier 1 fast lane",
            "budget:",
            "420",
            "(ceiling",
            "480,",
            "cutoff",
            "600).",
        ]
    )
    planted = plant_file(root, "README.md", f"## CI\n\n{sentence}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"three unitless levels restated in one line were invisible:\n{rendered(guard)}"
    )


def test_a_bound_noun_merely_near_a_number_is_not_a_second_owner(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """THE BOUND ON THE ARM ABOVE, and it is what keeps the scan usable.

    The adjacency is the whole rule: only a colon, an equals or horizontal
    whitespace may sit between the noun and the number. Widening it to "both on
    one line" would flag every markdown table and every measurement sentence in
    the repository.
    """
    root, files = green_tree
    sentence = " ".join(
        ["Tier 1 - the fast lane", "budget", "is generous, and", "420", "proves it."]
    )
    planted = plant_file(root, "docs/OPERATIONS.md", f"## CI\n\n{sentence}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "PASS", (
        f"a noun and a number merely sharing a line were read as a target:\n{rendered(guard)}"
    )


@pytest.mark.parametrize("word", EXPECTED_NUMBER_WORDS)
def test_every_number_word_is_a_second_owner(
    word: str, green_tree: tuple[Path, list[Path]]
) -> None:
    """NINETEEN ALTERNATIVES AND ONE OF THEM EXERCISED.

    Reducing the whole table to a nonsense string left the first build green,
    because the only plant that ever reached it spelled a digit.
    """
    root, files = green_tree
    planted = plant_file(
        root, "docs/OPERATIONS.md", f"## CI\n\n{restatement(bound='budget', amount=word)}\n"
    )

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"the number word {word!r} was not read as a quantity:\n{rendered(guard)}"
    )


def test_the_number_words_are_what_this_module_pins() -> None:
    """Adding an alternative is as unreviewed as deleting one, so pin both ways."""
    assert tuple(drift_guard.TIER1_NUMBER_WORDS.split("|")) == EXPECTED_NUMBER_WORDS


def test_the_unit_words_are_what_this_module_pins() -> None:
    assert tuple(drift_guard.TIER1_UNIT_WORDS.split("|")) == EXPECTED_UNIT_WORDS


@pytest.mark.parametrize("bound", EXPECTED_BOUND_NOUNS)
def test_every_bound_noun_is_what_makes_a_duration_a_target(
    bound: str, green_tree: tuple[Path, list[Path]]
) -> None:
    """FIVE NOUNS, ONE EXERCISED. Reducing the table to `target` alone survived."""
    root, files = green_tree
    planted = plant_file(root, "docs/OPERATIONS.md", f"## CI\n\n{restatement(bound=bound)}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"the bound noun {bound!r} did not turn a duration into a target:\n{rendered(guard)}"
    )


def test_the_bound_nouns_are_what_this_module_pins() -> None:
    assert drift_guard.TIER1_BOUND_NOUNS == EXPECTED_BOUND_NOUNS


@pytest.mark.parametrize("lane", ["tier1", "the fast lane"])
def test_every_lane_spelling_reaches_the_scan(
    lane: str, green_tree: tuple[Path, list[Path]]
) -> None:
    """Reducing the lane pattern to EITHER single alternative survived.

    The two spellings are genuinely distinct. A third the first build carried -
    a bare `tier1` alternative beside the separator-optional one - was an
    equivalent mutant no arm could kill, and it is dropped rather than graded.
    """
    root, files = green_tree
    sentence = " ".join([lane, "budget", "under", "3", "minutes."])
    planted = plant_file(root, "docs/OPERATIONS.md", f"## CI\n\n{sentence}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"the lane spelled {lane!r} did not reach the scan:\n{rendered(guard)}"
    )


def test_the_lane_spellings_are_what_this_module_pins() -> None:
    assert drift_guard.TIER1_LANE_SPELLINGS == EXPECTED_LANE_SPELLINGS


def test_a_second_workflow_declaring_the_env_keys_with_values_turns_the_guard_red(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """THE MOST LITERAL SECOND OWNER THERE IS, and the prose scan could not see it.

    A copied env block states the numbers in machine-readable form and spells no
    sentence at all: no bound noun, no lane token, nothing for a prose scan to
    find. MEASURED silent against the first build.
    """
    root, files = green_tree
    planted = plant_file(root, ".github/workflows/tier2.yml", workflow_source())

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", rendered(guard)
    assert "tier2.yml" in rendered(guard), (
        f"the red does not name the second workflow:\n{rendered(guard)}"
    )


def test_naming_the_env_keys_without_a_value_is_not_a_second_owner(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """THE BOUND ON THE ARM ABOVE, and it is load-bearing for this very module.

    Both this module and the guard NAME these keys - they have to, in order to
    grade them - and a scan that flagged every mention would flag its own
    graders and could never be green.
    """
    root, files = green_tree
    prose = "The lane declares TIER1_BUDGET_SECONDS and TIER1_CEILING_SECONDS."
    planted = plant_file(root, "docs/ARCHITECTURE.md", f"## CI\n\n{prose}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "PASS", (
        f"naming a key was read as owning its number:\n{rendered(guard)}"
    )


def test_a_bound_noun_on_a_neighbouring_line_still_states_a_target(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """PROSE WRAPS, AND THE FIRST BUILD REQUIRED BOTH ON ONE LINE."""
    root, files = green_tree
    planted = plant_file(root, "docs/OPERATIONS.md", f"## CI\n\n{split_restatement()}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"a target split over two lines was invisible:\n{rendered(guard)}"
    )


@pytest.mark.parametrize(
    ("distance", "caught", "why"),
    [
        (6, True, "a lane token at the window's edge is inside it"),
        (7, False, "a lane token one line past the window is outside it"),
    ],
)
def test_the_lane_window_is_graded_at_its_edge_in_both_directions(
    distance: int, caught: bool, why: str, green_tree: tuple[Path, list[Path]]
) -> None:
    """THE DISTANCES ARE LITERALS, NOT DERIVED FROM THE WINDOW.

    Deriving them would make both arms true for any window at all - including
    zero, which is what survived the first build. The window is separately
    pinned by :func:`test_the_lane_window_is_what_this_module_pins`, so a change
    to it reddens there and the behaviour is graded here.

    The plant puts the lane token and the duration on SEPARATE lines, which the
    first build's plants never did - they spelled both on one line, so the
    window was never exercised at all.
    """
    root, files = green_tree
    filler = ["padding that names nothing." for _ in range(distance - 1)]
    body = [
        " ".join(["This lane's", "budget", "is", "510", "seconds."]),
        *filler,
        "Tier 1 is what that paragraph is about.",
    ]
    planted = plant_file(root, "docs/OPERATIONS.md", "## CI\n\n" + "\n".join(body) + "\n")

    guard, _skips = run_guard(root, [*files, planted])

    expected = "FAIL" if caught else "PASS"
    assert guard["status"] == expected, f"{why}, and the guard said {guard['status']}"


def test_the_lane_window_is_what_this_module_pins() -> None:
    assert drift_guard.TIER1_LANE_WINDOW == EXPECTED_LANE_WINDOW


def test_a_file_naming_a_duration_without_a_bound_is_not_a_second_owner(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """THE BOUND ON THE ARMS ABOVE.

    A scan that flagged every duration would be indistinguishable from one that
    flagged restated targets, and it would redden on ordinary prose about how
    long something took.
    """
    root, files = green_tree
    planted = plant_file(
        root,
        "docs/OPERATIONS.md",
        "## CI\n\nTier 1 ran for 9 minutes on the last push, which is a measurement.\n",
    )

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "PASS", (
        f"a measurement was read as a restated target:\n{rendered(guard)}"
    )


def test_a_bound_far_from_any_mention_of_the_lane_is_not_a_second_owner(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """The other bound: a budget sentence about something else entirely."""
    root, files = green_tree
    unrelated = " ".join(["The docs size", "budget", "is 40 KB and the parse cost is", "2", "min."])
    planted = plant_file(root, "docs/ARCHITECTURE.md", f"## Budgets\n\n{unrelated}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "PASS", (
        f"an unrelated budget was read as a tier 1 restatement:\n{rendered(guard)}"
    )


# ---------------------------------------------------------------------------
# The exclusion table - every member, because two of ten was not "graded"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("excluded", EXPECTED_NARRATIVE_EXACT)
def test_each_named_narrative_record_is_excluded_and_the_exclusion_is_reported(
    excluded: str, green_tree: tuple[Path, list[Path]]
) -> None:
    """AN EXCLUSION NOBODY MEASURES IS A HOLE NOBODY COUNTS.

    These files RECORD a target that was true when written - `docs/LEDGER.md` is
    append-only by its own rule, and an item LINE keeps the premise it was filed
    with. None of them is a second owner. That is a stated price rather than a
    convenient boundary, so the guard reports what it declined to read and this
    arm requires the report.

    The first build parametrized nothing: eight of the ten members could be
    deleted one at a time in complete silence, and each one is a place a real
    second owner would then be forgiven.
    """
    root, files = green_tree
    planted = plant_file(root, excluded, f"## CS-896\n\n{restatement()}\n")

    guard, skips = run_guard(root, [*files, planted])

    assert guard["status"] == "PASS", f"{excluded} was graded as a second owner:\n{rendered(guard)}"
    excused = [skip["path"] for skip in skips]
    assert excluded in excused, (
        f"the guard declined to read {excluded} and recorded nothing about it: {skips}"
    )


@pytest.mark.parametrize("prefix", EXPECTED_NARRATIVE_PREFIXES)
def test_each_narrative_directory_is_excluded_and_the_exclusion_is_reported(
    prefix: str, green_tree: tuple[Path, list[Path]]
) -> None:
    root, files = green_tree
    relative = prefix + "a-record.md"
    planted = plant_file(root, relative, f"## CS-896\n\n{restatement()}\n")

    guard, skips = run_guard(root, [*files, planted])

    assert guard["status"] == "PASS", f"{relative} was graded as a second owner:\n{rendered(guard)}"
    excused = [skip["path"] for skip in skips]
    assert relative in excused, (
        f"the guard declined to read {relative} and recorded nothing about it: {skips}"
    )


def test_the_exclusion_table_is_what_this_module_pins() -> None:
    """Adding a member forgives a whole file, so the table is pinned both ways."""
    exact = tuple(path for path, _reason in drift_guard.TIER1_NARRATIVE_RECORD)
    prefixes = tuple(path for path, _reason in drift_guard.TIER1_NARRATIVE_PREFIXES)

    assert exact == EXPECTED_NARRATIVE_EXACT
    assert prefixes == EXPECTED_NARRATIVE_PREFIXES


def test_every_exclusion_states_a_reason_rather_than_only_a_path() -> None:
    """A path with no reason is an exemption nobody can argue with later."""
    entries = (*drift_guard.TIER1_NARRATIVE_RECORD, *drift_guard.TIER1_NARRATIVE_PREFIXES)
    silent = [path for path, reason in entries if not reason.strip()]

    assert not silent, f"these are forgiven with no reason recorded: {silent}"


def test_the_exclusion_does_not_spare_a_live_owner_that_merely_sits_under_docs(
    green_tree: tuple[Path, list[Path]],
) -> None:
    """The exclusion is a named set, not a directory-wide amnesty."""
    root, files = green_tree
    planted = plant_file(root, "docs/OPERATIONS.md", f"## CI\n\n{restatement()}\n")

    guard, _skips = run_guard(root, [*files, planted])

    assert guard["status"] == "FAIL", (
        f"a live doc was spared by the narrative exclusion:\n{rendered(guard)}"
    )


# ---------------------------------------------------------------------------
# Absent, unreadable, and the privacy rule on the echo path
# ---------------------------------------------------------------------------


def test_an_absent_workflow_warns_and_records_a_skip(tmp_path: Path) -> None:
    """Green with nothing recorded is not a verdict (CONVENTIONS.md section 15.1).

    WARN rather than FAIL is deliberate and it is a compatibility fact, not a
    softness: guard (e) is the ONE guard that fails outright on an absent file,
    and sibling modules build synthetic trees that carry only the port record
    and require the driver to report no drift.
    """
    root = tmp_path / "empty"
    root.mkdir()

    guard, skips = run_guard(root, [])

    assert guard["status"] == "WARN", rendered(guard)
    assert skips, "the guard graded nothing and recorded nothing it had skipped"


def test_an_unreadable_workflow_never_renders_the_name_the_read_failed_on(
    green_tree: tuple[Path, list[Path]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLAUDE.md non-negotiable 12 - an error message is an echo path.

    ``str()`` on an OSError appends the filename it failed on, which on a
    checkout under a home directory carries the operator's account name.
    """
    root, files = green_tree
    injected_name = "a-name-the-machine-owns"

    def refuse(*_args: object, **_kwargs: object) -> str:
        raise PermissionError(13, "Permission denied", injected_name)

    monkeypatch.setattr(Path, "read_text", refuse)

    guard, skips = run_guard(root, files)

    blob = rendered(guard) + "\n" + "\n".join(f"{s['path']} {s['reason']}" for s in skips)
    assert guard["status"] != "PASS", "an unreadable owner was passed"
    assert injected_name not in blob, f"the guard rendered the failed filename:\n{blob}"


# ---------------------------------------------------------------------------
# The workflow's own mechanism, read off the PARSED document
# ---------------------------------------------------------------------------


def test_the_lane_records_a_start_before_it_does_anything_else() -> None:
    """A duration measured from after the checkout is a duration of part of the job.

    Deleting this step entirely left the first build green, because the string
    `TIER1_STARTED` also occurs in the report step below it.

    SCOPED TO THE CATCH-ALL SHARD ON PURPOSE, and checked as such for CS-1060.
    It reads `workflow_steps()`, which addresses one job. The lane-wide
    counterpart is
    :func:`test_every_job_records_its_start_before_it_does_anything_else`, which
    asks the same question of every job the parser resolves; this arm is the
    detailed one and additionally grades what the marker is and where it goes.
    """
    steps = workflow_steps()
    names = [str(step.get("name")) for step in steps]

    assert names[0] == START_STEP, f"the start is not recorded first; the order is {names}"
    script = step_named(START_STEP).get("run")
    assert isinstance(script, str), "the start step runs nothing"
    assert "TIER1_STARTED" in script, f"the start step records no marker: {script!r}"
    assert "GITHUB_ENV" in script, (
        f"the marker never reaches a later step's environment: {script!r}"
    )


def test_the_comparison_runs_even_when_an_earlier_step_failed() -> None:
    """`if: always()` is the load-bearing half of the acceptance clause.

    A comparison that only ran when every earlier step succeeded would report
    nothing on exactly the runs worth measuring. Deleting the live key left the
    first build green, because the same string sits in the comment above it.

    SCOPED TO THE CATCH-ALL SHARD ON PURPOSE, and checked as such for CS-1060.
    :func:`test_every_duration_report_runs_on_every_outcome` is the lane-wide
    counterpart and reads every job the parser resolves.
    """
    condition = step_named(REPORT_STEP).get("if")

    assert condition == "always()", (
        f"the comparison is conditional on success; its `if` is {condition!r}"
    )


def test_the_comparison_reaches_the_run_summary() -> None:
    """Read off EVERY job, because a shard is a whole job's worth of silence.

    It read the catch-all shard alone, which was the whole lane when it was
    written. A shard whose report never reached the summary would have been
    invisible here, and the summary is where the operator reads the number
    (CS-1060).
    """
    silent: list[str] = []
    for job_id, job in every_parsed_job().items():
        for step in job.get("steps") or []:
            if isinstance(step, dict) and step.get("name") == REPORT_STEP:
                script = step.get("run")
                if not isinstance(script, str) or "GITHUB_STEP_SUMMARY" not in script:
                    silent.append(job_id)

    assert silent == [], (
        f"the duration report in {silent} never reaches the run summary, so those"
        " shards report a number nobody reading the run will see"
    )


def test_the_unit_test_step_runs_in_parallel() -> None:
    """Silently falling back to serial puts the lane back over the cutoff.

    THE ASSERTION IS ON THE PARSED STEP. `-n auto` is spelled twice more in this
    workflow's own comments, so deleting it from the live command left the first
    build's arm - which grepped the file text - green while the lane reverted to
    serial.

    SCOPED TO THE CATCH-ALL SHARD ON PURPOSE, and checked as such for CS-1060.
    The second assertion here is about the bare `tests` target, which is the
    catch-all's defining property and is true of NO other shard.
    :func:`test_both_shards_run_in_parallel_because_one_of_them_owns_an_open_item`
    carries the parallel half over every shard.
    """
    script = step_named(SUITE_STEP).get("run")

    assert isinstance(script, str), "the suite step runs nothing"
    assert "-n auto" in script, f"the unit test step does not run in parallel: {script!r}"
    assert " tests " in f" {script} ", (
        f"the suite step names no explicit target directory: {script!r}"
    )


def test_the_suite_step_never_invokes_pytest_from_the_bare_repo_root() -> None:
    """CONVENTIONS.md section 7.1 - a bare root run can sweep runtime state.

    ASKED OF EVERY SHARD. It read the catch-all alone, and a shard added later
    that invoked pytest with no target at all would have been outside it
    (CS-1060).
    """
    rootless = sorted(
        job_id for job_id, tokens in suite_shards().items() if not shard_targets(tokens)
    )

    assert rootless == [], (
        f"the {rootless} shards name no target under {SUITE_ROOT!r} as a token of its"
        " own, so pytest runs from the bare repo root and can sweep runtime state"
    )


def test_the_workflow_cites_the_open_item_that_owns_the_parallel_flag() -> None:
    """CS-448 IS OPEN, IT IS TIER 1, AND IT IS ABOUT THIS EXACT FLAG.

    Its acceptance names the single most expensive test on the runner and its
    note explicitly REFUSES a green tier-2 run as evidence. The first build
    justified `-n auto` with "tier2.yml already runs exactly that" and never
    mentioned the item at all, so the next reader had no way to find the
    refutation of the argument they were being handed.
    """
    text = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8")

    assert "CS-448" in text, (
        "the workflow adopts the flag CS-448 is open about and never cites the item"
    )


# ---------------------------------------------------------------------------
# The report step's own shell - four verdicts, three refusals, real exit codes
# ---------------------------------------------------------------------------


@needs_bash
def test_a_run_inside_the_budget_reports_it_and_succeeds(tmp_path: Path) -> None:
    """The reading is bracketed by clocks this arm reads itself (CS-1145).

    It allowed the staged figure plus two seconds, which is a guess about how
    long the harness takes to reach the step's shell. The gap is now bounded by
    arithmetic - see :func:`report_with_bounded_reading` - so a loaded runner
    cannot turn this arm red and a step that ignored the staged start still
    cannot pass it.
    """
    staged = staged_budget() - 30

    proc, most = report_with_bounded_reading(tmp_path, staged)
    seconds, verdict = reported(proc)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert verdict == "within budget", proc.stdout
    assert staged <= seconds <= most, f"reported {seconds} for a staged {staged}, bounded by {most}"


@needs_bash
def test_a_slow_harness_does_not_push_the_reading_outside_what_the_clock_allows(
    tmp_path: Path,
) -> None:
    """THE ARM CS-1145 IS, AND IT IS RED ON THE BOUND IT REPLACED.

    MEASURED: the windows-latest leg of run 35330059133 staged 390 and the step
    reported 393, against a window that allowed two - so the lane was red for
    the distance between two clock reads rather than for anything the workflow
    did, and the ubuntu leg of the same job passed. The stall reproduces that
    gap on an idle machine, where it is otherwise ZERO: ten readings taken
    while filing this item all reported the staged figure exactly, which is why
    a tolerance derived from a developer machine would have been undersized
    again.

    THE TWO ASSERTIONS ARE THE TWO HALVES OF THE REPAIR, and the first is the
    anti-vacuity control. Without it a stall that never landed would leave this
    arm green for the same reason the runner is fast, proving nothing about the
    bound at all.
    """
    staged = staged_budget() - 30

    proc, most = report_with_bounded_reading(tmp_path, staged, stall=CI_MEASURED_STALL)
    seconds, verdict = reported(proc)

    assert verdict == "within budget", proc.stdout
    assert seconds > staged + SUPERSEDED_TOLERANCE, (
        f"the stall never left the window CS-1145 removed, so this arm reproduces"
        f" nothing: reported {seconds} for a staged {staged}"
    )
    assert staged <= seconds <= most, f"reported {seconds} for a staged {staged}, bounded by {most}"


@needs_bash
def test_a_run_over_the_budget_warns_and_still_succeeds(tmp_path: Path) -> None:
    """The budget is a REPORT. CONVENTIONS.md section 8: this lane must never be red."""
    staged = staged_budget() + 5
    assert staged <= staged_ceiling(), "the staged duration must sit inside the warn band"

    proc, most = report_with_bounded_reading(tmp_path, staged)
    seconds, verdict = reported(proc)

    assert proc.returncode == 0, "over budget turned the lane red:\n" + proc.stdout
    assert verdict == "over budget", proc.stdout
    assert "::warning::" in proc.stdout, f"the breach was not annotated:\n{proc.stdout}"
    assert staged <= seconds <= most, f"reported {seconds} for a staged {staged}, bounded by {most}"


@needs_bash
def test_a_run_over_the_ceiling_fails_the_lane_and_names_the_number(tmp_path: Path) -> None:
    """THE ONE MECHANISM CS-896 ADDS, AND NOTHING GRADED IT.

    Deleting this branch's `exit 1` left every arm of the first build green -
    which is the whole item back again, because a breach that does not fail is a
    breach that arrives as a cancellation and reports nothing.
    """
    staged = staged_ceiling() + 5

    proc = report_for_elapsed(tmp_path, staged)
    seconds, verdict = reported(proc)

    assert proc.returncode != 0, "over the ceiling did NOT fail the lane:\n" + proc.stdout
    assert verdict == "OVER THE CEILING", proc.stdout
    assert "::error::" in proc.stdout, f"the failure was not annotated:\n{proc.stdout}"
    assert str(seconds) in proc.stdout, "the failure names no duration"
    assert str(staged_ceiling()) in proc.stdout, "the failure names no ceiling"


@needs_bash
def test_the_ceiling_branch_is_what_fails_and_the_budget_branch_is_not(tmp_path: Path) -> None:
    """The two levels differ in EXIT CODE, which is the only difference that acts."""
    over_budget = report_for_elapsed(tmp_path, staged_budget() + 5)
    over_ceiling = report_for_elapsed(tmp_path, staged_ceiling() + 5)

    codes = (over_budget.returncode, over_ceiling.returncode)

    assert codes[0] == 0, f"over budget exited {codes[0]}"
    assert codes[1] != 0, f"over the ceiling exited {codes[1]}"


@needs_bash
def test_no_recorded_start_is_a_refusal_rather_than_a_report(tmp_path: Path) -> None:
    """Deleting this branch's `exit 1` left an arm asserting only exit-non-zero green.

    Without it the step prints the refusal and carries on. An unset variable is
    zero inside bash arithmetic, so the elapsed becomes the whole Unix epoch,
    the ceiling branch fires, and the step exits non-zero having reported a
    duration it invented.
    """
    verdict, why = refused(run_report_step(tmp_path, None))

    assert verdict, f"a job that measured nothing did not refuse: {why}"


@needs_bash
@pytest.mark.parametrize("started", ["1 2", "soon", "12.5", ""])
def test_a_start_that_is_not_a_whole_number_is_a_refusal(started: str, tmp_path: Path) -> None:
    """MEASURED: `TIER1_STARTED="1 2"` exited 0 reporting an EMPTY duration.

    Under the runner's own `bash -eo pipefail`, an arithmetic syntax error
    inside an assignment does not stop the script. It writes the error to
    stderr, leaves the variable empty, and every later comparison then compares
    against nothing - so the step announced a pass over a measurement it never
    made.
    """
    verdict, why = refused(run_report_step(tmp_path, started))

    assert verdict, f"a start of {started!r} did not refuse: {why}"


@needs_bash
def test_a_start_in_the_future_is_a_refusal_rather_than_a_negative_duration(
    tmp_path: Path,
) -> None:
    """MEASURED: it printed a NEGATIVE duration and called it within budget, exit 0."""
    verdict, why = refused(report_for_elapsed(tmp_path, -9999))

    assert verdict, f"a start in the future did not refuse: {why}"


@needs_bash
def test_every_refusal_prints_the_same_sentence_because_they_are_the_same_fault(
    tmp_path: Path,
) -> None:
    """Three ways to have measured nothing, one thing to say about all of them."""
    outcomes = {
        "no start": run_report_step(tmp_path, None),
        "not an integer": run_report_step(tmp_path, "1 2"),
        "negative": report_for_elapsed(tmp_path, -9999),
    }

    failing = {label: refused(proc)[1] for label, proc in outcomes.items() if not refused(proc)[0]}

    assert not failing, f"not every refusal refused: {failing}"


# ---------------------------------------------------------------------------
# The dependency the budget rests on
# ---------------------------------------------------------------------------


def dev_requirements() -> list[str]:
    """The `dev` extra, PARSED rather than grepped.

    Returns:
        Every requirement string.
    """
    data = tomllib.loads((REPO_ROOT / PYPROJECT_RELATIVE).read_text(encoding="utf-8"))
    listed = data["project"]["optional-dependencies"]["dev"]
    assert isinstance(listed, list), "the dev extra is not a list"
    return [str(item) for item in listed]


def test_pytest_xdist_is_pinned_with_both_bounds_exactly_as_recorded() -> None:
    """THE UPPER BOUND IS LOAD-BEARING AND NOTHING GRADED IT.

    Deleting the line was killed; widening it to a bare `pytest-xdist` SURVIVED,
    even though the comment above it in pyproject.toml argues at length that the
    bound matters - a major bump may change the default distribution mode, and a
    budget measured under one scheduler and enforced under another is a number
    nobody has measured. The same argument is already written into the ruff pin
    beside it, from an incident where an unbounded floor let CI resolve a line
    this machine never ran.
    """
    matched = [item for item in dev_requirements() if item.startswith("pytest-xdist")]

    assert len(matched) == 1, f"expected one pytest-xdist requirement, found {matched}"
    assert "<" in matched[0], (
        f"the pin carries no upper bound, so CI may resolve a major this project has never "
        f"run: {matched[0]!r}"
    )
    assert matched[0] == EXPECTED_XDIST_REQUIREMENT, (
        f"the pin moved to {matched[0]!r}. Bump it deliberately and move the pin in this same "
        f"change, with a fresh timing sample from the runner"
    )


def test_the_workflow_does_not_install_xdist_itself() -> None:
    """One owner for the pin, which is how tier 2 ends up tolerating its absence.

    READ OVER EVERY JOB. It scanned the catch-all shard's steps alone, so a
    second owner of the pin installed by another shard was invisible to it - and
    every shard runs `-n auto`, so every shard has a reason to reach for it
    (CS-1060).
    """
    offending = sorted(
        job_id
        for job_id, job in every_parsed_job().items()
        if any(
            isinstance(step, dict) and "install pytest-xdist" in str(step.get("run", ""))
            for step in (job.get("steps") or [])
        )
    )

    assert offending == [], (
        f"the {offending} jobs install pytest-xdist themselves, so the dev extra is not"
        " the one owner of the pin"
    )


# ---------------------------------------------------------------------------
# The by-line citations this restructure invalidated
# ---------------------------------------------------------------------------


def test_the_cited_workflow_lines_still_satisfy_the_citation_guard() -> None:
    """The emptiness leg of the citation guard, checked from this side of the seam.

    `tests/test_docs_citations.py` leg 1 reddens on a pointer that lands on a
    blank or punctuation-only line, and a restructure moves every line below its
    edit. This arm makes that failure attributable to the restructure rather
    than to the citation guard, and it is the ONE property about those pointers
    that is still true.
    """
    lines = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8").splitlines()

    assert len(lines) >= max(STALE_LEDGER_POINTERS), (
        f"the workflow is {len(lines)} lines, so a cited pointer is past its end"
    )
    for number in STALE_LEDGER_POINTERS:
        landing = lines[number - 1].strip()
        assert landing, f"{WORKFLOW_RELATIVE} line {number} is blank, so the pointer names nothing"
        assert any(character.isalnum() for character in landing), (
            f"{WORKFLOW_RELATIVE} line {number} is punctuation only: {landing!r}"
        )


def test_the_steps_the_stale_pointers_meant_are_addressable_by_name() -> None:
    """The repair for a rotted line pointer is to cite the step BY NAME.

    That is this repository's own practice, already written into `docs/LEDGER.md`
    for two earlier stale citations and lifted into
    `tests/test_docs_citations.py` as its forbid rule. A by-name citation is only
    a repair while the names exist, so this arm holds them.

    CORRECTLY SCOPED TO THE CATCH-ALL SHARD, and checked as such for CS-1060.
    Both steps it names are GATES, and the gates read the whole tree and belong
    to exactly one job - the other shards carry none by design, so widening this
    arm over every job would assert a shape the lane deliberately does not have.
    """
    names = [str(step.get("name")) for step in workflow_steps()]

    assert FORMAT_STEP in names, f"the step the first pointer meant is gone: {names}"
    assert TYPE_STEP in names, f"the step the second pointer meant is gone: {names}"


def ledger_names_the_correction() -> bool:
    """Whether `docs/LEDGER.md` carries a correction record for both pointers.

    Returns:
        True when one run of lines names the item, the workflow and both
        pointers together.
    """
    lines = (REPO_ROOT / LEDGER_RELATIVE).read_text(encoding="utf-8", errors="replace").splitlines()
    wanted = ("CS-896", WORKFLOW_RELATIVE, *[str(number) for number in STALE_LEDGER_POINTERS])
    for start in range(len(lines)):
        window = "\n".join(lines[start : start + LEDGER_CORRECTION_WINDOW])
        if all(token in window for token in wanted):
            return True
    return False


def test_the_stale_ledger_pointers_are_corrected_by_an_appended_record() -> None:
    """THE ARM THAT USED TO CLAIM THE POINTERS STILL LANDED ON THEIR CONTENT.

    They do not. At the base commit the two lines were the ruff format step and
    the bare mypy invocation, matching what `docs/LEDGER.md` says about them;
    after this restructure they are a different step and a line inside an
    embedded script. The old arm was named for a property it never checked and
    that had already stopped being true.

    `docs/LEDGER.md` is append-only, so the pointers cannot be edited. The
    repair is an APPENDED correction that cites those steps BY NAME - the same
    repair this file already carries for two earlier stale citations - and this
    arm requires it to exist rather than pretending the rot did not happen.
    """
    assert ledger_names_the_correction(), (
        "docs/LEDGER.md carries no correction for the two by-line pointers this "
        "restructure invalidated. Append a record that names, within "
        f"{LEDGER_CORRECTION_WINDOW} lines of each other: CS-896, {WORKFLOW_RELATIVE}, and both "
        f"pointer line numbers {list(STALE_LEDGER_POINTERS)} - stating that the pointers rotted, "
        f"that the file is append-only so they are deliberately not edited, and that the steps "
        f"they meant are cited by name instead as {FORMAT_STEP!r} and {TYPE_STEP!r}. Spell the "
        f"two numbers as bare numbers in prose and NOT as a path-colon-line pointer: that form "
        f"would enrol the new entry in tests/test_docs_citations.py's own pinned pointer set and "
        f"redden it, which is the rot this correction is about."
    )


# ---------------------------------------------------------------------------
# The lane runs in SHARDS, and a shard is where coverage goes missing
# ---------------------------------------------------------------------------

#: The save shard. The lane was first split on 2026-09-06 after run 34013336391
#: was CANCELLED at 611s at 99 per cent of the suite with nothing failing.
SAVE_JOB_ID = "save"

#: What the CATCH-ALL shard names before any ignore is applied. Exactly one
#: shard may name it, and that shard is the catch-all BY DEFINITION rather than
#: by id - so the arms below never have to know which id it is.
SUITE_ROOT = "tests"

#: The one narrowing spelling this lane permits, and only on the catch-all. The
#: SPACE form is refused outright rather than accommodated: `--ignore x` splits
#: into two tokens, so a scan that accepted it could not say whether the path
#: that follows is an exclusion or a target.
IGNORE_PREFIX = "--ignore="


#: Every flag that can make pytest collect LESS than its target names. The arm
#: below refuses all of them outside the one ignore the partition is built from,
#: because a partition argued from targets alone is defeated by any of these in
#: total silence - MEASURED: adding `--ignore=tests/save/test_phase4_gate.py`
#: and `-m "not slow"` to the narrow shard dropped 244 of its 1413 tests while
#: every guard, gate and arm in this repository stayed green.
NARROWING_FLAGS = (
    "-m",
    "-k",
    "--ignore",
    "--ignore-glob",
    "--deselect",
    "--collect-only",
    "--co",
    "-p",
    "--lf",
    "--ff",
    "--last-failed",
    "--failed-first",
    "-x",
    "--exitfirst",
    "--maxfail",
)


def narrowing_selectors(tokens: list[str]) -> list[str]:
    """Every token in ``tokens`` that can reduce what pytest collects.

    Args:
        tokens: A pytest command, already split.

    Returns:
        The offending tokens, in order, with any ``=`` value retained so a
        failure names what was actually written.
    """
    if "pytest" not in tokens:
        return ["<no pytest in the command, so nothing was scanned>"]
    # SCANNING STARTS AFTER `pytest` AND THAT IS NOT A DETAIL. The command is
    # `python -m pytest ...`, so a scan over the whole token list reads
    # PYTHON's -m - the module flag - as pytest's marker expression and fails a
    # correct lane. Measured the first time this arm ran.
    after = tokens[tokens.index("pytest") + 1 :]
    found: list[str] = []
    for token in after:
        head = token.split("=", 1)[0]
        if head in NARROWING_FLAGS:
            found.append(token)
    return found


def suite_shards() -> dict[str, list[str]]:
    """Every shard of this lane, DERIVED from the parsed workflow.

    THE SHARD SET USED TO BE TWO IDS WRITTEN OUT AS LITERALS, and CS-1060 is
    what that cost. Adding a third job turned three arms red for the wrong
    reason and left two more SILENTLY NARROWED - the parallel arm and the
    partition arm both went on grading the pair they named while the new shard
    was covered by neither. MEASURED on this very edit, before this function
    existed: with the third job appended and nothing else changed, the parallel
    arm passed over a shard it had never looked at.

    SO NO SHARD COUNT IS WRITTEN ANYWHERE IN THIS MODULE. Not a number, not a
    ``len(...) == n``, not a tuple of ids. A count is the same defect as the
    pair of literals it would replace: it is a second copy of a fact the
    workflow already states, and the copy is the one that drifts.

    Returns:
        Every job carrying a step named :data:`SUITE_STEP`, by id, mapped to
        that step's command split into tokens.
    """
    shards: dict[str, list[str]] = {}
    duplicated: list[str] = []
    for job_id, job in every_parsed_job().items():
        matched = [
            step
            for step in (job.get("steps") or [])
            if isinstance(step, dict) and step.get("name") == SUITE_STEP
        ]
        if not matched:
            continue
        if len(matched) > 1:
            duplicated.append(f"{job_id} declares {len(matched)}")
            continue
        script = matched[0].get("run")
        assert isinstance(script, str), f"job {job_id!r} suite step runs nothing"
        shards[job_id] = script.split()
    assert duplicated == [], (
        f"a job declares more than one step named {SUITE_STEP!r}: {duplicated}. The"
        " arms below read one command per shard, so a second one is uncovered"
    )
    assert shards, f"{WORKFLOW_RELATIVE} declares no shard running {SUITE_STEP!r}"
    return shards


def after_pytest(tokens: list[str]) -> list[str]:
    """The arguments pytest itself receives, with python's own flags dropped.

    SCANNING STARTS AFTER `pytest` AND THAT IS NOT A DETAIL - the command is
    `python -m pytest ...`, so a scan over the whole token list reads PYTHON's
    -m as pytest's marker expression.

    Args:
        tokens: A pytest command, already split.

    Returns:
        Every token after the literal ``pytest``.
    """
    assert "pytest" in tokens, f"this command does not invoke pytest: {tokens}"
    return tokens[tokens.index("pytest") + 1 :]


def is_target(token: str) -> bool:
    """Whether ``token`` names a path inside the suite root.

    The boundary is a `/` rather than a prefix, so a sibling directory whose
    name merely starts with the same letters is not read as a target.

    Args:
        token: One token of a pytest command.

    Returns:
        True for the suite root itself and for anything properly under it.
    """
    return token == SUITE_ROOT or token.startswith(SUITE_ROOT + "/")


def test_no_shard_names_a_node_id_where_a_path_is_required() -> None:
    """A node id as a target is a SILENT OVERLAP, and the token arms cannot see it.

    MEASURED by an adversarial pass over ea3591a, not imagined. Give ``guards``
    the target ``tests/test_toolpath.py::test_x`` and the catch-all the BYTE
    IDENTICAL string as its ``--ignore=``, and every partition arm passes: the
    claimed set equals the ignored set, nothing nests, no narrowing flag
    appears. The module reported 143 passed. Collection reported 7720 against a
    true 7719, with that one test collected by TWO shards.

    THE ASYMMETRY IS THE WHOLE MECHANISM. ``--ignore`` matches a PATH and is a
    silent no-op when handed a node id, while the same string as a positional
    argument selects exactly one test. The partition arms compare the two
    strings as opaque tokens, so a string that means one thing on the left and
    nothing on the right reads as a matched pair.

    So the pairing is not enough on its own: both sides have to be the KIND of
    thing ``--ignore`` can act on. That is what this arm pins.
    """
    offenders = sorted(
        f"{job_id} -> {token}"
        for job_id, tokens in suite_shards().items()
        for token in tokens
        if (is_target(token) or token.startswith("--ignore=")) and "::" in token
    )
    assert offenders == [], (
        f"{offenders} name a pytest NODE ID where a path is required. `--ignore=` silently"
        " ignores a node id, so such a token excludes nothing while its twin on another"
        " shard still selects: the two strings match, the collected sets do not, and every"
        " other arm in this module stays green over the overlap"
    )


def test_no_selection_narrowing_hides_in_the_pytest_configuration() -> None:
    """The workflow tokens are only the whole selection if NOTHING ELSE narrows.

    EVERY ARM ABOVE READS THE WORKFLOW AND NOTHING BUT THE WORKFLOW. That is
    exactly as wide as the partition argument reaches, and an adversarial pass
    over ea3591a walked straight through the gap: adding ``-m 'not slow'`` to
    ``addopts`` in pyproject.toml, with the workflow untouched, left this module
    at 143 passed while 12 tests in the guard shard were deselected and
    therefore ran in NO SHARD AT ALL.

    A gap opened outside the file the arms read is still a gap. pytest applies
    ``addopts`` to every invocation, so a narrowing flag there subtracts from
    all three shards at once and the partition proof above says nothing about
    it.

    THE INVERSE IS NOT CHECKED HERE AND THAT IS DELIBERATE. ``testpaths`` cannot
    narrow a run that names its own targets, and a ``collect_ignore`` in a
    conftest is a separate mechanism with its own reach; neither belongs in an
    assertion about ``addopts``. They are named here so the next reader knows
    they were considered rather than missed.
    """
    config = tomllib.loads(Path(PYPROJECT_RELATIVE).read_text(encoding="utf-8"))
    addopts = config["tool"]["pytest"]["ini_options"].get("addopts", "")
    assert isinstance(addopts, str), f"addopts is {type(addopts).__name__}, not a string"

    # SCANNED DIRECTLY RATHER THAN THROUGH :func:`narrowing_selectors`, which
    # refuses a token list carrying no ``pytest`` and returns a sentinel saying
    # so. That refusal is right for a COMMAND - it exists because scanning a
    # whole `python -m pytest ...` list reads python's own -m as pytest's
    # marker expression - and wrong for ``addopts``, which is a bare flag
    # string with no interpreter in front of it. The shared thing is the
    # vocabulary, and that is what is reused here.
    narrowing = [token for token in addopts.split() if token.split("=", 1)[0] in NARROWING_FLAGS]
    assert narrowing == [], (
        f"pyproject.toml addopts carries {narrowing}, which narrows EVERY pytest invocation"
        " including all three shards. Whatever those exclude is run by no shard, while the"
        " partition arms above - which read only the workflow - stay green over the gap"
    )


def shard_targets(tokens: list[str]) -> list[str]:
    """The paths one shard hands pytest, in command order.

    Args:
        tokens: A pytest command, already split.

    Returns:
        Every target token, in order.
    """
    return [token for token in after_pytest(tokens) if is_target(token)]


def shard_ignores(tokens: list[str]) -> list[str]:
    """The `--ignore=` exclusions one shard states, in command order.

    Args:
        tokens: A pytest command, already split.

    Returns:
        Every ``--ignore=<path>`` token, in order.
    """
    return [token for token in after_pytest(tokens) if token.startswith(IGNORE_PREFIX)]


#: The lane below this one. A tier-1 shard may DELETE a path from its own run
#: only while a REQUIRED job of this workflow provably runs it, so this file is
#: read rather than trusted (CS-1073).
TIER2_RELATIVE = ".github/workflows/tier2.yml"

#: A matrix job's declared `name:` is a TEMPLATE, and what CI reports is one job
#: per leg with the expansion substituted in. The driver therefore matches on
#: the literal PREFIX, and this is what cuts a declared name back to it - the
#: same reduction `tests/test_queue_loop_ci_specs.py` performs, for the same
#: reason.
TEMPLATE_EXPANSION = re.compile(r"\$\{\{[^}]*\}\}")


def queue_loop_module() -> Any:
    """The lane driver, imported for its CI specs and nothing else.

    THE MATCHER SET IS READ FROM THE DRIVER RATHER THAN COPIED HERE. A copy
    would agree with whatever it was written from forever, and the fact that
    matters is not "tier 2 declares a job called X" but "the driver WAITS ON X
    and refuses to ship the row without it". A job the driver does not grade is
    a job that can be red while the lane goes on shipping, so an ignore
    justified by such a job is justified by nothing.

    Returns:
        The imported ``ops.loop.queue_loop`` module.
    """
    if str(REPO_ROOT) not in sys.path:  # pragma: no cover - ordering, not logic
        sys.path.insert(0, str(REPO_ROOT))
    return importlib.import_module("ops.loop.queue_loop")


def required_tier_two_matchers() -> tuple[str, ...]:
    """Every job-name prefix the driver REQUIRES of tier 2.

    Returns:
        ``CI_TIER2.required``, verbatim.
    """
    driver = queue_loop_module()
    for spec in driver.CI_SPECS:
        if spec.workflow == Path(TIER2_RELATIVE).name:
            required = tuple(spec.required)
            assert required, (
                f"the driver requires NO job of {TIER2_RELATIVE}, so nothing there is"
                " graded and no tier-1 deletion can be justified by it"
            )
            return required
    raise AssertionError(f"the driver declares no CI spec for {TIER2_RELATIVE}")


def tier_two_document() -> dict[str, Any]:
    """The lane below this one, parsed.

    Parsed rather than scanned for the reason :func:`workflow_document` gives:
    that file documents itself heavily and its comments spell `pytest tests`
    more than once.

    Returns:
        The parsed document.
    """
    text = (REPO_ROOT / TIER2_RELATIVE).read_text(encoding="utf-8")
    document = yaml.safe_load(text)
    assert isinstance(document, dict), f"{TIER2_RELATIVE} did not parse to a mapping"
    return document


def matchable(name: str) -> str:
    """A declared job name cut back to the literal prefix CI reports.

    Args:
        name: A job's declared ``name``, templating included.

    Returns:
        The prefix up to the first ``${{``, or the whole name when there is none.
    """
    match = TEMPLATE_EXPANSION.search(name)
    return name[: match.start()] if match else name


def tier_two_pytest_invocations(matchers: tuple[str, ...]) -> list[tuple[str, list[str]]]:
    """Every pytest command a REQUIRED tier-2 job runs, located.

    THE PARAMETER IS WHY THIS IS A FUNCTION AND NOT A CONSTANT. Handed the real
    matchers it answers the shipped question; handed a narrower set it answers
    the question the arms below need in order to grade themselves - a detector
    that has only ever read a healthy tree is a detector nobody has measured.

    Args:
        matchers: Job-name prefixes to accept, in the driver's own spelling.

    Returns:
        (a label naming the job and step, the command split into tokens) for
        every line of every step of every matching job that invokes pytest.
    """
    jobs = tier_two_document().get("jobs")
    assert isinstance(jobs, dict), f"{TIER2_RELATIVE} declares no jobs mapping"

    found: list[tuple[str, list[str]]] = []
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        declared = matchable(str(job.get("name", job_id)))
        if not any(declared.startswith(m) or m.startswith(declared) for m in matchers):
            continue
        for index, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                continue
            script = step.get("run")
            if not isinstance(script, str):
                continue
            where = f"{TIER2_RELATIVE} job {job_id!r} step {step.get('name', index)!r}"
            # LINE BY LINE, because a `run:` block is a SHELL SCRIPT and several
            # of tier 2's are. A scan over the whole block would read a target
            # from one line against a pytest on another and invent an invocation
            # that no shell ever executes.
            for line in script.splitlines():
                tokens = line.split()
                if "pytest" in tokens:
                    found.append((where, tokens))
    return found


def covered_by(claim: str, path: str) -> bool:
    """Whether a pytest target ``claim`` collects ``path``.

    The boundary is a `/` rather than a prefix, so a sibling whose name merely
    starts with the same letters is not read as covered.

    Args:
        claim: A path handed to pytest as a target or as an ``--ignore=``.
        path: The path being asked about.

    Returns:
        True when ``claim`` is ``path`` or a directory containing it.
    """
    return path == claim or path.startswith(claim + "/")


def run_by_any(invocations: list[tuple[str, list[str]]], path: str) -> bool:
    """Whether some invocation in ``invocations`` genuinely collects ``path``.

    THIS IS A NECESSARY CONDITION AND NEVER A SUFFICIENT ONE. Read on its own it
    is a containment test, and a containment test against a job that runs the
    bare suite root says YES to every path under it - which is a permission that
    cannot refuse anything a tier-1 shard would ever plausibly write.
    :data:`PERMITTED_DELETIONS` is what actually grants; this only takes away.

    THE WHOLE NARROWING VOCABULARY IS APPLIED HERE, not just `--ignore=`. An
    earlier version read the tier-2 targets and its ignores and nothing else,
    and `-m 'not slow'`, `-k`, `--deselect`, `--ignore-glob=`, `-p no:...` and
    `--collect-only` each left a deleted module reading as covered by a job that
    would not have run it. That is the family
    :func:`test_no_selection_narrowing_hides_in_the_pytest_configuration` exists
    for, arriving one lane out, so the same vocabulary answers it: an invocation
    carrying ANY narrowing selector is no cover at all, whatever it targets.

    THE TEMPLATE EXPANSION IS NOT A NARROWING AND IS DELIBERATELY NOT REFUSED.
    tier 2's full-suite command ends in a `${{ steps.xdist.outputs.args }}` that
    resolves to `-n auto` or to nothing; neither subtracts a test. A scan that
    refused every token it could not resolve would refuse the shipped lane.

    Args:
        invocations: The commands to consider.
        path: The path being asked about.

    Returns:
        True when at least one unnarrowed command collects it.
    """
    for _where, tokens in invocations:
        if narrowing_selectors(tokens):
            continue
        after = after_pytest(tokens)
        if any(covered_by(claim, path) for claim in after if is_target(claim)):
            return True
    return False


def deletion_ignores(
    shards: dict[str, list[str]], claimed: list[str], catch: str
) -> dict[str, list[str]]:
    """Every `--ignore=` that is NOT the partition's own one-per-target bookkeeping.

    The catch-all carries one ignore per other shard's target, and those name
    paths another tier-1 shard runs: they are how the partition is spelled, not
    a deletion. ANYTHING ELSE names a path no tier-1 shard runs at all, and that
    is a deletion from this lane whatever job it is written on.

    RECOGNISED ONLY ON THE CATCH-ALL, deliberately. A non-catch-all shard
    writing another shard's target as its own ignore is at best a no-op and at
    worst a second exclusion of a path already excluded once; classifying it as
    bookkeeping would let it past the governed check for free.

    Args:
        shards: Every shard's command, by id.
        claimed: Every target claimed by a non-catch-all shard.
        catch: The catch-all shard's id.

    Returns:
        The deleted paths, by shard id, for the shards that delete anything.
    """
    wanted = set(claimed)
    found: dict[str, list[str]] = {}
    for job_id, tokens in shards.items():
        paths = [token[len(IGNORE_PREFIX) :] for token in shard_ignores(tokens)]
        deleted = [path for path in paths if not (job_id == catch and path in wanted)]
        if deleted:
            found[job_id] = deleted
    return found


#: THE ONLY PATHS TIER 1 MAY DELETE, each paired with the item that authorised
#: it. AN ALLOWLIST, AND THE DISTINCTION IS THE WHOLE REPAIR. The first version
#: of this rule permitted any path a required tier-2 job could be argued to
#: contain, and a required tier-2 job runs the bare suite root - so it said YES
#: to `tests`, to `tests/save`, to `tests/solve`, to everything a shard would
#: ever actually write. It could refuse only paths outside the suite root, which
#: no tier-1 shard would ever name. An adversarial pass measured what that cost:
#: a save shard carrying `--ignore=tests/save` - the whole directory, run by NO
#: tier-1 shard, since the catch-all already ignores it - was GREEN on every arm
#: in this module while the base commit was RED.
#:
#: THIS REPO HAS MEASURED THE GENERAL FORM OF THAT MISTAKE ALREADY: one defect
#: wore four different fields across four green commits, and only an allowlist
#: of known-good values held. A containment test is a denylist in disguise.
#:
#: THE ITEM ID IS NOT DECORATION. A permission with no item behind it is a
#: permission nobody has to justify or ever close, so the id is required, its
#: spelling is checked, and every entry must name a path the lane deletes TODAY
#: - a standing permission for a path nothing excludes is a hole waiting for
#: someone to walk into it.
PERMITTED_DELETIONS: dict[str, str] = {
    # It re-runs the WHOLE of tests/save as a nested child pytest, targeting the
    # DIRECTORY rather than the shard, so no arrangement of shards could ever
    # have contained it. `.githooks/pre-push` and tier 2's `full suite` both
    # still collect it; the workflow states the measurement.
    "tests/save/test_phase4_gate.py": "CS-1073",
}

#: How an item id is spelled. `CLAUDE.md` section 5: ids carry the `CS-` prefix,
#: are permanent and are never reused.
ITEM_ID = re.compile(r"^CS-\d+$")

#: What separates a refusal from its reason. Chosen over `:` because a refusal
#: renders a PATH, and a Windows path carries a drive colon that would split in
#: the middle of the very thing being named.
REASON_MARK = " -- "


def named_paths(refusals: list[str]) -> list[str]:
    """The ``"<shard> -> <path>"`` head of each refusal, reason discarded.

    Args:
        refusals: Lines as :func:`ungoverned_deletions` renders them.

    Returns:
        The heads, sorted.
    """
    return sorted(line.split(REASON_MARK, 1)[0] for line in refusals)


def ungoverned_deletions(
    deletions: dict[str, list[str]],
    invocations: list[tuple[str, list[str]]],
    permitted: dict[str, str],
) -> list[str]:
    """Every tier-1 deletion the two conditions do not BOTH permit.

    THE CONDITIONS ARE CONJUNCTIVE AND NEITHER IS SUFFICIENT. A path must be on
    the recorded allowlist AND be provably run by a required tier-2 job. The
    allowlist alone would let a recorded permission outlive the tier-2 job that
    made it safe; the tier-2 read alone is the containment hole described on
    :data:`PERMITTED_DELETIONS`.

    SEPARATED FROM THE ARMS THAT USE IT SO IT CAN BE GRADED, for the reason
    :func:`jobs_without_a_cutoff` gives: an arm that reads the shipped tree and
    finds nothing wrong passes identically whether it asks the right question or
    no question at all. ``permitted`` is a parameter for the same reason - an
    allowlist the arms cannot vary is an allowlist they cannot measure.

    Args:
        deletions: The deleted paths, by shard id.
        invocations: The commands the required tier-2 jobs run.
        permitted: The recorded permissions, path to item id.

    Returns:
        ``"<shard> -> <path> -- <reason>"`` for each, sorted.
    """
    found: list[str] = []
    for job_id, paths in deletions.items():
        for path in paths:
            head = f"{job_id} -> {path}"
            if path not in permitted:
                found.append(f"{head}{REASON_MARK}on no recorded permission")
            elif not run_by_any(invocations, path):
                found.append(
                    f"{head}{REASON_MARK}permitted by {permitted[path]}, but no REQUIRED"
                    " tier-2 job runs it unnarrowed"
                )
    return sorted(found)


def test_the_two_shards_partition_the_suite_with_no_gap_and_no_overlap() -> None:
    """CS-896 and CS-1060 - a shard is exactly where a directory stops being tested.

    THE NAME SAYS TWO AND THE ARM COUNTS NONE. It is kept because `docs/LEDGER.md`
    cites it by name and that file is append-only by its own header, so the
    pointer cannot be repaired by an edit there. What the arm grades is stated
    below and holds for ANY number of shards.

    THE FIRST VERSION READ ONE SIDE AND AN ADVERSARY WALKED THROUGH THE OTHER.
    It took the wide shard's ignore list and the narrow shard's target and
    argued a partition from the pair, which says nothing about what the narrow
    shard additionally excludes. Adding one ignore and one marker expression to
    the save job dropped 244 of its 1413 tests - the whole of
    tests/save/test_phase4_gate.py - while this file, the drift guard and the
    pre-commit gate all stayed green.

    THE SECOND VERSION NAMED ITS TWO SHARDS AS LITERALS, which is the fault
    CS-1060 repairs. A third shard was outside every sentence the arm could
    make, so the lane could grow a job that ran tests nothing here reasoned
    about.

    THE ARGUMENT, FOR ANY N, AND IT NEEDS NO COUNT:

      1. Exactly one shard names the bare suite root. That shard is the
         CATCH-ALL, identified by what it runs rather than by its id.
      2. Every other shard names its own explicit paths properly under the
         suite root, and narrows itself NOT AT ALL.
      3. The catch-all's ignores are exactly the union of the other shards'
         targets - one ignore per target, no duplicates, nothing else.
      4. No two claimed targets nest at a path boundary.

    (1) and (3) make the catch-all `tests` MINUS that union, so nothing is run
    twice. (2) and (4) make the union disjoint and every claimed path really
    collected by the shard that claims it, so nothing is run by no one. A target
    added without its ignore is an OVERLAP; an ignore added without its target
    is a GAP. Both are red here, and neither is argued from a shard count.
    """
    shards = suite_shards()
    targets = {job_id: shard_targets(tokens) for job_id, tokens in shards.items()}
    ignores = {job_id: shard_ignores(tokens) for job_id, tokens in shards.items()}

    # (1) EXACTLY ONE CATCH-ALL, found by what it runs.
    catch_all = sorted(job_id for job_id, named in targets.items() if named == [SUITE_ROOT])
    assert len(catch_all) == 1, (
        f"the shards naming the bare {SUITE_ROOT!r} target are {catch_all}; exactly one"
        f" shard may be the catch-all, because the partition is {SUITE_ROOT!r} minus the"
        f" other shards' targets. The shards are { {key: targets[key] for key in targets} }"
    )
    catch = catch_all[0]
    others = sorted(job_id for job_id in shards if job_id != catch)
    assert others, (
        f"only the catch-all shard {catch!r} runs the suite, so this lane is not"
        " sharded at all and the arm below would be grading nothing"
    )

    # (2) EVERY OTHER SHARD NAMES ITS OWN PATHS AND NARROWS ITSELF NOT AT ALL.
    for job_id in others:
        named = targets[job_id]
        assert named, f"the {job_id!r} shard names no target under {SUITE_ROOT!r}: {shards[job_id]}"
        outside = [name for name in named if not name.startswith(SUITE_ROOT + "/")]
        assert outside == [], (
            f"the {job_id!r} shard names {outside}, which are not proper paths under"
            f" {SUITE_ROOT + '/'!r}, so the catch-all cannot exclude them by name"
        )
        # NARROWING ITSELF "NOT AT ALL" WAS RELAXED BY EXACTLY ONE CLAUSE, AND
        # THE CLAUSE IS A NAMED PERMISSION RATHER THAN AN ARGUMENT (CS-1073).
        # The original reading was right about the general case and wrong about
        # one: an ignore here names a path NEITHER tier-1 shard runs, which is a
        # gap - UNLESS the path is on :data:`PERMITTED_DELETIONS` by item id AND
        # a job the lane driver will not ship without provably runs it
        # unnarrowed. Both, never either.
        #
        # THE FIRST ATTEMPT AT THIS CLAUSE ASKED ONLY THE SECOND HALF AND WAS
        # REFUTED. A required tier-2 job runs the bare suite root, so every path
        # under `tests/` satisfied it: a save shard carrying `--ignore=tests/save`
        # - the whole directory, run by no tier-1 shard at all - went GREEN here
        # while the commit before this one was RED. What the allowlist adds is
        # the ability to refuse a path tier 2 demonstrably runs.
        governed = ungoverned_deletions(
            {job_id: [name[len(IGNORE_PREFIX) :] for name in ignores[job_id]]},
            tier_two_pytest_invocations(required_tier_two_matchers()),
            PERMITTED_DELETIONS,
        )
        assert governed == [], (
            f"the {job_id!r} shard excludes {governed}; whatever those name is run by"
            " NEITHER tier-1 shard, and nothing has recorded a permission for it that a"
            " REQUIRED tier-2 job still honours, so every lane stays green over it"
        )

    # (3) THE CATCH-ALL IGNORES EXACTLY THE UNION OF THE OTHERS' TARGETS.
    claimed = [name for job_id in others for name in targets[job_id]]
    repeated = sorted({name for name in claimed if claimed.count(name) > 1})
    assert repeated == [], (
        f"{repeated} are claimed by more than one shard, so those tests run twice on"
        " every push and the catch-all's single ignore hides it"
    )
    # THE CATCH-ALL'S IGNORES ARE READ IN TWO PARTS SINCE CS-1073, AND THE
    # EQUALITY BELOW IS UNCHANGED OVER THE FIRST. Bookkeeping ignores - the ones
    # naming another shard's target - must still be exactly the union of the
    # claims, one for one. A DELETION ignore is anything else, it is governed by
    # the tier-2 clause rather than by this equality, and it is subtracted here
    # so that clause is the only thing that can permit it.
    bookkeeping = sorted(name for name in ignores[catch] if name[len(IGNORE_PREFIX) :] in claimed)
    assert bookkeeping == sorted(IGNORE_PREFIX + name for name in claimed), (
        f"the catch-all shard {catch!r} excludes {sorted(ignores[catch])} while the other"
        f" shards claim {sorted(claimed)}. Each claimed target needs exactly one"
        f" {IGNORE_PREFIX!r} on the catch-all: a target without one is run twice, and an"
        " ignore without one is run by nobody"
    )
    deleted = ungoverned_deletions(
        deletion_ignores(shards, claimed, catch),
        tier_two_pytest_invocations(required_tier_two_matchers()),
        PERMITTED_DELETIONS,
    )
    assert deleted == [], (
        f"{deleted} are deleted from tier 1 on no recorded permission, or on one no"
        " REQUIRED tier-2 job still honours, so they are collected by nothing the lane"
        " waits on"
    )

    # (4) NO CLAIMED TARGET SITS INSIDE ANOTHER.
    nested = sorted(
        f"{inner} sits inside {outer}"
        for outer in claimed
        for inner in claimed
        if inner != outer and inner.startswith(outer + "/")
    )
    assert nested == [], (
        f"{nested}; a nested pair makes the union ambiguous and the single ignore that"
        " covers the outer path silently covers the inner one too"
    )


#: The guard shard's job id - the third shard CS-1060 added.
GUARD_JOB_ID = "guards"

#: The file CS-1170 moved from the guard shard to the save shard.
REBALANCED_FILE = "tests/test_toolpath.py"


def test_the_toolpath_guard_runs_first_in_the_save_shard_and_not_in_the_guard_shard() -> None:
    """CS-1170 - the guard shard was full while the save shard idled.

    The guard shard read over its budget on every green run from CS-1060 on,
    over a population that did not change, while the save shard finished far
    under it. So the single heaviest guard file moved to the save shard. No
    level moved and no test was dropped: the partition arm above still proves
    that every file runs in exactly one leg, and this arm pins WHICH leg.

    It is named FIRST among the save shard's targets on purpose. Under
    `--dist loadfile` a worker takes it at the start instead of at the end, so
    the shard's longest run is not that file plus everything queued before it.
    """
    shards = suite_shards()
    for job_id in (SAVE_JOB_ID, GUARD_JOB_ID):
        assert job_id in shards, f"no {job_id!r} shard runs {SUITE_STEP!r}: {sorted(shards)}"
    save_targets = shard_targets(shards[SAVE_JOB_ID])
    guard_targets = shard_targets(shards[GUARD_JOB_ID])
    assert REBALANCED_FILE not in guard_targets, (
        f"the {GUARD_JOB_ID!r} shard still names {REBALANCED_FILE!r}, so the shard CS-1170"
        f" emptied is full again: {guard_targets}"
    )
    assert save_targets[:1] == [REBALANCED_FILE], (
        f"the {SAVE_JOB_ID!r} shard must name {REBALANCED_FILE!r} as its FIRST target so"
        f" loadfile starts it at once; it names {save_targets}"
    )


#: The files CS-1173 moved from the catch-all shard to the guard shard and kept there.
REBALANCED_TO_GUARDS = (
    "tests/test_archive_rot.py",
    "tests/test_sphinx_roles.py",
    "tests/test_handler_exception_rendering.py",
    "tests/test_locals_rendering.py",
    "tests/test_assertion_rendering.py",
)

#: The files CS-1173's correction handed back to the catch-all shard.
RETURNED_TO_CATCH_ALL = (
    "tests/test_chained_exemption_guard.py",
    "tests/test_disposition_sites.py",
)

#: The guard file CS-1173's correction moved to the save shard.
REBALANCED_TO_SAVE = "tests/test_commit_msg_gate.py"


def test_the_moved_guard_files_run_in_the_guard_shard_and_not_in_the_catch_all() -> None:
    """CS-1173 - the catch-all read over its budget once CS-1170 emptied the guard shard.

    CS-1170 moved the guard shard's heaviest file out, and the next CI run left
    the guard shard far under its budget while the catch-all job, whose pytest
    step is most of its duration, read over it. So a block of guard-family files
    from the catch-all's measured head moved to the guard shard.

    THE FIRST MOVE OVERSHOT, AND THIS ARM PINS THE CORRECTION. The guard reading
    it was projected from came off a fast runner: on the run after the move the
    moved files cost what they had cost in the catch-all, while the guard
    shard's OWN files ran at the speed every earlier reading shows, and the
    shard read over its budget. So two moved files went back to the catch-all
    and one guard file went to the save shard, balancing all three legs rather
    than two. No level moved and no test was dropped: the partition arm above
    still proves every file runs in exactly one leg, and this arm pins WHICH leg.

    The three rendering files stay TOGETHER on purpose. They share `@cache`d
    helpers in `tests/assertion_rendering_guard.py` and
    `tests/locals_rendering_guard.py`, so splitting them across shards would pay
    for those censuses twice.
    """
    shards = suite_shards()
    for job_id in (JOB_ID, GUARD_JOB_ID, SAVE_JOB_ID):
        assert job_id in shards, f"no {job_id!r} shard runs {SUITE_STEP!r}: {sorted(shards)}"
    guard_targets = shard_targets(shards[GUARD_JOB_ID])
    save_targets = shard_targets(shards[SAVE_JOB_ID])
    catch_all_ignores = shard_ignores(shards[JOB_ID])
    not_in_guards = [path for path in REBALANCED_TO_GUARDS if path not in guard_targets]
    assert not_in_guards == [], (
        f"the {GUARD_JOB_ID!r} shard does not name {not_in_guards}, so the catch-all"
        f" CS-1173 relieved is full again: {guard_targets}"
    )
    not_ignored = [
        path for path in REBALANCED_TO_GUARDS if IGNORE_PREFIX + path not in catch_all_ignores
    ]
    assert not_ignored == [], (
        f"the {JOB_ID!r} shard still runs {not_ignored}; a moved file it does not"
        f" ignore runs twice: {catch_all_ignores}"
    )
    still_in_guards = [path for path in RETURNED_TO_CATCH_ALL if path in guard_targets]
    still_ignored = [
        path for path in RETURNED_TO_CATCH_ALL if IGNORE_PREFIX + path in catch_all_ignores
    ]
    assert (still_in_guards, still_ignored) == ([], []), (
        f"the files CS-1173 handed back to the {JOB_ID!r} shard are still in the"
        f" {GUARD_JOB_ID!r} shard {still_in_guards} or still ignored by the catch-all"
        f" {still_ignored}, so the guard shard CS-1173 overfilled is full again"
    )
    assert REBALANCED_TO_SAVE not in guard_targets, (
        f"the {GUARD_JOB_ID!r} shard still names {REBALANCED_TO_SAVE!r}: {guard_targets}"
    )
    # CS-1193 MOVED IT ON AGAIN, to the hook shard, because it drives a real
    # hook. The arm below pins where it lives now; this one keeps only the half
    # CS-1173 decided - it is not in the guard shard - and adds that it is not
    # back in the save shard either, so the file cannot run in two legs.
    assert REBALANCED_TO_SAVE not in save_targets, (
        f"the {SAVE_JOB_ID!r} shard still names {REBALANCED_TO_SAVE!r}, which CS-1193 moved"
        f" to the {HOOK_JOB_ID!r} shard: {save_targets}"
    )


#: The fourth shard CS-1193 added, by the adjudicated route (A) of the wave-3
#: CI route ruling. Its job id; the display name is read by the lane driver.
HOOK_JOB_ID = "hooks"

#: Named FIRST in the hook shard, as the ruling's condition A2 requires. It is
#: the file that waits out the hooks' literal probe bound, so under
#: `--dist loadfile` it must start at t=0 rather than form the tail.
HOOK_SHARD_FIRST = "tests/test_hook_probe_bound.py"

#: Every file that DRIVES A SHIPPED HOOK - installs `.githooks/<hook>` into a
#: throwaway repo and runs it through a real git command, or runs the hook file
#: itself. Sleep- and subprocess-bound work, the part of the lane least sensitive
#: to the bimodal runner, which is why the ruling isolated it. Enumerated by what
#: each file EXERCISES, not by its name: tests/test_hook_file_mode.py (a static
#: mode check), tests/test_install_hooks.py and tests/test_git_env_scrub.py (both
#: run synthetic hooks, never the shipped ones) stay where they were.
HOOK_DRIVING_FILES = (
    HOOK_SHARD_FIRST,
    "tests/test_hook_interpreter_ladder.py",
    "tests/test_commit_msg_gate.py",
    "tests/test_precommit_gate.py",
    "tests/test_pre_push_ref_race.py",
    "tests/test_hook_toolchain.py",
    "tests/test_precommit_gate_lint_cwd.py",
)

#: The ruling's condition A5 filled the hook shard's headroom from the fast
#: shard's heaviest CPU-bound files, rather than from the guard shard that
#: tools/tier1_growth.py pins in BUDGET_UNMET. CS-1198 took three of the four
#: back out - the hook shard itself read over its budget on a slow runner - and
#: moved them to the fill shard below. Only the canary child stays: at about
#: 154s on a slow runner it would be over half of any fill step, so it runs
#: second here, and the hook shard dispatches in command order (see
#: :data:`HOOK_NO_REORDER`) so it starts at t=0 instead of forming the tail.
HOOK_SHARD_FILL = ("tests/test_canary_population_forced.py",)


def test_the_hook_driving_files_run_in_the_hook_shard_and_nowhere_else() -> None:
    """CS-1193 - the catch-all read over its ceiling, and the hook files were why.

    Run 36130961603 read the catch-all at 509s against a 480s ceiling. The new
    offender was tests/test_hook_probe_bound.py, which waits out the hooks'
    literal probe bound on every refusal arm - sleep, not CPU, so it costs the
    same on every runner and all of it on ONE worker under loadfile. The ruling
    took route (A): a fourth job carrying every file that drives a shipped
    hook, plus the fast shard's heaviest CPU-bound files as fill. No level
    moved and no test was dropped: the partition arm still proves every file
    runs in exactly one leg, and this arm pins WHICH leg.
    """
    shards = suite_shards()
    for job_id in (JOB_ID, HOOK_JOB_ID):
        assert job_id in shards, f"no {job_id!r} shard runs {SUITE_STEP!r}: {sorted(shards)}"
    hook_targets = shard_targets(shards[HOOK_JOB_ID])
    assert hook_targets[:1] == [HOOK_SHARD_FIRST], (
        f"the {HOOK_JOB_ID!r} shard must name {HOOK_SHARD_FIRST!r} FIRST so loadfile"
        f" starts its bound-waiting arms at once; it names {hook_targets}"
    )
    expected = [*HOOK_DRIVING_FILES, *HOOK_SHARD_FILL]
    missing = [path for path in expected if path not in hook_targets]
    assert missing == [], (
        f"the {HOOK_JOB_ID!r} shard does not name {missing}, so the shard CS-1193"
        f" relieved is carrying them again: {hook_targets}"
    )
    elsewhere = sorted(
        f"{path} in {job_id}"
        for job_id, tokens in shards.items()
        if job_id != HOOK_JOB_ID
        for path in shard_targets(tokens)
        if path in expected
    )
    assert elsewhere == [], f"{elsewhere}; a moved file named by two shards runs twice"
    catch_all_ignores = shard_ignores(shards[JOB_ID])
    not_ignored = [path for path in expected if IGNORE_PREFIX + path not in catch_all_ignores]
    assert not_ignored == [], (
        f"the {JOB_ID!r} shard still runs {not_ignored}; a moved file it does not"
        f" ignore runs twice: {catch_all_ignores}"
    )


#: The fifth shard CS-1198 added, by the adjudicated Route N. Its job id, and
#: the display name the lane driver and the two tier-1 readers key on.
FILL_JOB_ID = "fill"
FILL_JOB_NAME = "tests (fill shard)"

#: The CPU-bound fill CS-1198 took back OUT of the hook shard. The hook shard
#: read over its budget on every slow runner, and these carry no hook - they
#: were there for room, and the room was gone.
FILL_FROM_HOOK = (
    "tests/test_cs1175_rule_narrowing.py",
    "tests/test_citation_tables.py",
    "tests/data/test_phase2_gate.py",
)

#: The catch-all's measured head, moved with them by CS-1198 so the fill shard's
#: heaviest single test stays under the concentration limit
#: (tools/tier1_concentration.py) and the catch-all leaves the warn band. The last
#: was added by the S0 measurement's share fallback, heaviest first, skipping the
#: two files pinned to the catch-all in :data:`RETURNED_TO_CATCH_ALL` and
#: tests/test_flip_checks.py, which pins that no workflow names its tool - naming
#: the file here would. CS-1214's later arrivals are a separate group below,
#: because they came from the GUARD shard and not from here.
FILL_FROM_CATCH_ALL = (
    "tests/solve/test_phase3_gate.py",
    "tests/test_cs1174_placeholder_delimiters.py",
    "tests/test_exception_messages.py",
    "tests/data/test_drift_guard_data.py",
    "tests/surface/test_server.py",
    "tests/test_pathless_clone_agreement.py",
    "tests/test_credential_redaction.py",
    "tests/test_provenance_stamp.py",
)

#: The guard shard's head, moved here by CS-1214. The guard shard read over its
#: budget and then over its ceiling on a docs-only tip, and this shard was the
#: receiver its acceptance clause named. No level moved and no test was dropped:
#: both files were already named as an `--ignore=` on the catch-all shard, so a
#: move between two non-catch-all shards changes no ignore line at all.
#:
#: THE REASONS CAME WITH THE FILES, because a reason left behind rots.
#: tests/test_probe_refusal_output.py drives every shipped hook through real git
#: and the wrapper with planted canaries (CS-814, CS-1200) - it was on the guard
#: shard for ROOM, not for kinship, and the room was gone.
#: tests/test_liveness.py is the guard shard's heaviest single file and this tree
#: has measured it at about twice its local wall on the runner
#: (docs/item_notes/phase4-followups-900.md). tests/test_mypy_gate.py is the
#: second subprocess-heavy head, and this shard is the CPU-bound one by
#: construction.
FILL_FROM_GUARDS = (
    "tests/test_liveness.py",
    "tests/test_mypy_gate.py",
    "tests/test_probe_refusal_output.py",
)

#: The fill shard's whole membership, exactly.
FILL_SHARD_FILES = (*FILL_FROM_HOOK, *FILL_FROM_CATCH_ALL, *FILL_FROM_GUARDS)

#: The flag that makes the hook shard dispatch its files in COMMAND ORDER.
#: pytest-xdist 3.8 reorders the loadfile queue by test count, descending, by
#: default, so the 3-test canary file was always dispatched LAST and ran alone
#: for about 160s on a slow runner. `LoadFileScheduling` inherits the gate from
#: `LoadScopeScheduling`, so this flag governs `--dist loadfile` too.
HOOK_NO_REORDER = "--no-loadscope-reorder"

#: Named second in the hook shard, so under command order it starts at t=0 on
#: the other worker.
HOOK_SHARD_SECOND = HOOK_SHARD_FILL[0]


def test_the_fill_shard_runs_exactly_the_moved_files_and_no_other_shard_does() -> None:
    """CS-1198 then CS-1214 - two shards read over budget, and this one took the fill.

    CS-1198 added the shard and gave it the hook shard's CPU-bound fill plus the
    catch-all's measured head. CS-1214 added the guard shard's head to it, after
    the guard shard read over its budget and then over its ceiling on a
    docs-only tip; this shard is the receiver CS-1214's acceptance named.

    No level moved in either item and no test was dropped. CS-1214 moved files
    between two NON-CATCH-ALL shards, so the catch-all's ignore list is
    byte-identical across it - the miscount block below is what proves that
    rather than assuming it. The generic partition arm already proves every file
    runs in exactly one leg; this arm pins WHICH leg for each moved file, that
    the fill shard names nothing else, that the display name the lane driver
    keys on is the one written here, and that every moved file is claimed by
    exactly one shard and ignored by the catch-all exactly once.
    """
    shards = suite_shards()
    for job_id in (JOB_ID, HOOK_JOB_ID, FILL_JOB_ID):
        assert job_id in shards, f"no {job_id!r} shard runs {SUITE_STEP!r}: {sorted(shards)}"
    job_name = every_parsed_job()[FILL_JOB_ID].get("name")
    assert job_name == FILL_JOB_NAME, (
        f"the {FILL_JOB_ID!r} job is named {job_name!r}; the lane driver and both tier-1"
        f" readers key on {FILL_JOB_NAME!r}"
    )
    fill_targets = shard_targets(shards[FILL_JOB_ID])
    assert sorted(fill_targets) == sorted(FILL_SHARD_FILES), (
        f"the {FILL_JOB_ID!r} shard names {fill_targets}; CS-1198 and CS-1214 gave it exactly"
        f" {list(FILL_SHARD_FILES)}"
    )
    claims = {
        path: sorted(
            job_id
            for job_id, tokens in shards.items()
            for target in shard_targets(tokens)
            if target == path
        )
        for path in FILL_SHARD_FILES
    }
    wrong = {path: owners for path, owners in claims.items() if owners != [FILL_JOB_ID]}
    assert wrong == {}, (
        f"{wrong}; each moved file must be claimed by the {FILL_JOB_ID!r} shard alone,"
        " or it runs twice or in the wrong leg"
    )
    catch_all_ignores = shard_ignores(shards[JOB_ID])
    miscounted = {
        path: catch_all_ignores.count(IGNORE_PREFIX + path)
        for path in FILL_SHARD_FILES
        if catch_all_ignores.count(IGNORE_PREFIX + path) != 1
    }
    assert miscounted == {}, (
        f"the {JOB_ID!r} shard ignores these moved files the wrong number of times"
        f" {miscounted}; each needs exactly one {IGNORE_PREFIX!r}"
    )


def test_the_hook_shard_dispatches_in_command_order_with_the_canary_second() -> None:
    """CS-1198 - under xdist 3.8's default reorder the canary always ran last.

    The S0 measurement found the hook shard's wall was about half its worker
    time PLUS a 160s single-worker tail: the 3-test canary file, dispatched last
    because loadfile sorts files by test count, descending. The adjudicated
    repair turns that sort off on the HOOK job only, so the command order is the
    dispatch order - the probe-bound file first and the canary second, each
    starting at t=0 on its own worker. The flag is pinned here, on this job and
    on no other: the ruling scoped it to this job, and widening it moves every
    other shard's measured schedule.
    """
    shards = suite_shards()
    assert HOOK_JOB_ID in shards, f"no {HOOK_JOB_ID!r} shard runs {SUITE_STEP!r}"
    hook_args = after_pytest(shards[HOOK_JOB_ID])
    assert HOOK_NO_REORDER in hook_args, (
        f"the {HOOK_JOB_ID!r} shard does not pass {HOOK_NO_REORDER!r}, so xdist reorders"
        f" its files by test count and the canary runs last and alone: {hook_args}"
    )
    hook_targets = shard_targets(shards[HOOK_JOB_ID])
    assert hook_targets[:2] == [HOOK_SHARD_FIRST, HOOK_SHARD_SECOND], (
        f"under command order the {HOOK_JOB_ID!r} shard must name {HOOK_SHARD_FIRST!r}"
        f" then {HOOK_SHARD_SECOND!r}; it names {hook_targets}"
    )
    elsewhere = sorted(
        job_id
        for job_id, tokens in shards.items()
        if job_id != HOOK_JOB_ID and HOOK_NO_REORDER in after_pytest(tokens)
    )
    assert elsewhere == [], (
        f"the {elsewhere} shards also pass {HOOK_NO_REORDER!r}; CS-1198's ruling scoped it"
        f" to the {HOOK_JOB_ID!r} job alone"
    )


def test_the_installed_pytest_accepts_the_hook_shards_dispatch_flag() -> None:
    """A flag pytest does not know is exit 4 on the runner, not a slower shard.

    The partition arms read tokens and would pass a misspelt flag, so the
    installed scheduler is asked directly. The pinned floor
    (:data:`EXPECTED_XDIST_REQUIREMENT`) is the version this was verified on.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--help", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        timeout=120,
    )
    known = HOOK_NO_REORDER in proc.stdout
    assert proc.returncode == 0, f"pytest --help exited {proc.returncode}"
    assert known, f"the installed pytest does not list {HOOK_NO_REORDER!r} in its help"


def test_every_path_a_shard_names_exists_in_the_tree() -> None:
    """A target that does not exist is not a claim, it is a red CI run.

    pytest refuses a missing target with `file or directory not found` and
    exits 4, so a shard naming a file that has not landed yet turns the lane
    red on a runner rather than here. The partition arm cannot see it: a
    missing target and its matching ignore still pair up one for one. So a
    file on its way in from another slice is named at MERGE, once it exists,
    and never ahead of it.
    """
    absent = sorted(
        f"{path} in {job_id}"
        for job_id, tokens in suite_shards().items()
        for path in shard_targets(tokens)
        if not (REPO_ROOT / path).exists()
    )
    assert absent == [], f"{absent}; pytest exits 4 on a target that is not there"


def test_no_shard_narrows_itself_by_any_route_the_ignore_list_cannot_name() -> None:
    """CS-896 - a partition argued from targets alone is defeated in one flag.

    MEASURED: adding `--ignore=tests/save/test_phase4_gate.py` and `-m "not slow"`
    to a shard dropped 244 of its 1413 tests while every guard, gate and arm in
    this repository stayed green. So the COMPLETE selector set of every shard is
    read, and the only narrowing permitted anywhere is the catch-all's own
    `--ignore=` list - which the arm above has already matched against the other
    shards' targets.

    THE SPACE FORM IS REFUSED SEPARATELY AND ON PURPOSE. `--ignore tests/save`
    splits into a bare `--ignore` and a path that then reads as a TARGET, so a
    scan that tolerated it would classify an exclusion as a claim. It is named
    here rather than absorbed, so the failure says which spelling was written.
    """
    shards = suite_shards()

    spaced = sorted(job_id for job_id, tokens in shards.items() if "--ignore" in tokens)
    assert spaced == [], (
        f"{spaced} write the SPACE form of an ignore. Only {IGNORE_PREFIX!r} is"
        " readable here: the path after a bare --ignore is indistinguishable from a"
        " target, so the partition above would count an exclusion as a claim"
    )

    # THE CATCH-ALL IS NO LONGER LOCATED HERE, AND THAT IS THE HANDOVER BELOW
    # ARRIVING IN THE CODE. This arm used to permit an ignore only on the
    # catch-all, so it had to know which shard that was; it now permits an
    # ignore on any shard and leaves WHICH paths to the partition arm, which
    # locates the catch-all itself. Two arms deciding the same thing is how one
    # of them drifts.

    # THE PERMITTED SET IS EVERY SHARD'S OWN `--ignore=` LIST SINCE CS-1073, AND
    # THAT IS NOT A WIDENING OF WHAT IS ALLOWED. It is a HANDOVER: this arm asks
    # only whether a shard narrows itself by a route the ignore list cannot
    # NAME, and the partition arm above now grades the ignore list itself on
    # every shard - bookkeeping ignores against the claims, deletion ignores
    # against what a required tier-2 job provably runs. Keeping `[]` here for
    # the other shards would make the two arms disagree about the same token,
    # and the one that fails first would be the one nobody could read.
    offending: list[str] = []
    for job_id, tokens in shards.items():
        permitted = shard_ignores(tokens)
        found = narrowing_selectors(tokens)
        if sorted(found) != sorted(permitted):
            offending.append(f"{job_id} -> {found}")
    assert offending == [], (
        f"{offending} narrow themselves by a route the partition cannot see. A shard may"
        f" narrow itself only by its {IGNORE_PREFIX!r} list, which the partition arm"
        " grades path by path; every other selector is invisible to it"
    )


def test_the_tier_two_cross_check_reads_the_jobs_and_the_targets_it_claims_to() -> None:
    """THE KNOWN-GOOD CONTROL. Every clause above is vacuous without it.

    :func:`run_by_any` answers False for everything when the parse finds
    nothing, and False is the SAFE direction - a deletion would be refused
    rather than waved through. That makes a broken parse a red lane rather than
    a silent hole, which is the right way round, and it also makes a broken
    parse indistinguishable from a healthy one for as long as nothing is
    deleted. So the parse is required to have found something, here, by name.
    """
    matchers = required_tier_two_matchers()
    invocations = tier_two_pytest_invocations(matchers)

    assert invocations, (
        f"no REQUIRED job of {TIER2_RELATIVE} was found to invoke pytest at all, so the"
        f" clause permitting a tier-1 deletion is reading nothing. The matchers are"
        f" {list(matchers)}"
    )
    running_the_root = [
        where for where, tokens in invocations if SUITE_ROOT in after_pytest(tokens)
    ]
    assert running_the_root, (
        f"no REQUIRED tier-2 job runs the bare {SUITE_ROOT!r} target; the invocations"
        f" found were {[where for where, _ in invocations]}"
    )


def lane_deletions() -> dict[str, list[str]]:
    """Every path this lane excludes and no tier-1 shard picks up.

    Returns:
        The deleted paths, by shard id.
    """
    shards = suite_shards()
    targets = {job_id: shard_targets(tokens) for job_id, tokens in shards.items()}
    catch_all = [job_id for job_id, named in targets.items() if named == [SUITE_ROOT]]
    assert len(catch_all) == 1, f"the catch-all shards are {sorted(catch_all)}"
    catch = catch_all[0]
    claimed = [name for job_id, named in targets.items() if job_id != catch for name in named]
    return deletion_ignores(shards, claimed, catch)


def test_the_recorded_permissions_are_live_and_each_names_the_item_that_granted_it() -> None:
    """CS-1073 - an allowlist nobody prunes becomes the hole it replaced.

    THREE PROPERTIES, AND EACH HAS ITS OWN FAILURE MODE. An entry with no item
    id is a permission nobody has to justify or ever close. An entry naming a
    path the lane does NOT currently delete is a STANDING permission: the next
    person to write that ignore gets it for free, with no review and no item,
    which is precisely the containment hole arriving by a slower route. And an
    empty allowlist would make every arm below grade nothing.

    THE DIRECTION THAT IS NOT CHECKED, DELIBERATELY. A deletion with no entry is
    refused by :func:`ungoverned_deletions` rather than here, because that is a
    statement about the workflow and this arm is a statement about the list.
    """
    assert PERMITTED_DELETIONS, (
        "no deletion is recorded at all, so every arm grading the allowlist below is"
        " grading an empty question. Delete them rather than leave them passing"
    )

    malformed = sorted(
        f"{path} -> {item!r}"
        for path, item in PERMITTED_DELETIONS.items()
        if not ITEM_ID.match(item)
    )
    assert malformed == [], (
        f"{malformed} record no item id in the `CS-<number>` spelling CLAUDE.md section 5"
        " pins. A permission with no item behind it is one nobody has to justify or close"
    )

    outside = sorted(path for path in PERMITTED_DELETIONS if not is_target(path))
    assert outside == [], (
        f"{outside} are recorded as tier-1 deletions but are not under {SUITE_ROOT!r}, so"
        " no shard could ever have been running them and the entry permits nothing"
    )

    deleted = {path for paths in lane_deletions().values() for path in paths}
    stale = sorted(path for path in PERMITTED_DELETIONS if path not in deleted)
    assert stale == [], (
        f"{stale} carry a recorded permission and are NOT excluded by any shard today."
        " A permission for a path nothing deletes is a standing one: whoever writes that"
        f" ignore next gets it with no item and no review. Remove the entry from"
        " PERMITTED_DELETIONS when the deletion goes"
    )


def test_every_path_tier_one_deletes_is_recorded_and_still_run_by_a_required_tier_two_job() -> None:
    """CS-1073 - the rule that lets a tier-1 shard drop a module, stated once.

    A tier-1 shard may carry an `--ignore=` that no other tier-1 shard picks up
    only while BOTH hold: the path is on :data:`PERMITTED_DELETIONS` against the
    item that authorised it, AND a job `ops/loop/queue_loop.py` REQUIRES of
    tier 2 provably runs it unnarrowed.

    REQUIRED IS LOAD-BEARING ON THE SECOND HALF. The driver refuses to ship a
    lane row without those jobs, so a path they run is a path something waits
    on; an advisory job, or one the driver does not grade at all, can be red for
    the rest of the project's life without anything noticing.

    THE ALLOWLIST IS LOAD-BEARING ON THE FIRST, AND IT IS THE HALF AN
    ADVERSARIAL PASS HAD TO ADD. Read alone, the tier-2 half is a containment
    test against a job that runs the bare suite root, so it says YES to every
    path a shard would ever write.

    THIS IS THE SAME CLAUSE THE PARTITION ARM APPLIES, ASKED WHOLE. That arm
    reaches it through the partition's own bookkeeping and would go red for
    several other reasons first; this one names the paths and nothing else, so a
    failure here says exactly which deletion lost its cover.
    """
    escaped = ungoverned_deletions(
        lane_deletions(),
        tier_two_pytest_invocations(required_tier_two_matchers()),
        PERMITTED_DELETIONS,
    )

    assert escaped == [], (
        f"{escaped}. Either restore them to tier 1, or record the path against the item"
        f" that authorises it in PERMITTED_DELETIONS and make a REQUIRED job of"
        f" {TIER2_RELATIVE} collect it unnarrowed"
    )


#: The shapes a tier-1 deletion actually takes, every one of them a path a
#: REQUIRED tier-2 job demonstrably runs. MEASURED BY AN ADVERSARY AGAINST THE
#: FIRST VERSION OF THIS RULE, which permitted all four: `tests/save` is the
#: whole save directory, already excluded by the catch-all, so a save shard
#: excluding it too leaves the directory running in NO shard; `tests` is the
#: entire suite. The first rule could refuse only paths OUTSIDE the suite root,
#: which is to say only paths no tier-1 shard would ever write.
DELETIONS_THE_LANE_COULD_PLAUSIBLY_WRITE = (
    SUITE_ROOT,
    SUITE_ROOT + "/save",
    SUITE_ROOT + "/solve",
    SUITE_ROOT + "/advisor",
)

#: A path NO pytest invocation in either workflow names. Deliberately OUTSIDE
#: the suite root, so it is refused by the tier-2 half rather than by the
#: allowlist - which is what makes it usable for grading that half on its own.
#: It names no file on disk: :func:`run_by_any` compares strings and never
#: touches the filesystem, so a real path would only invite a reader to check
#: whether it still exists.
UNCOVERED_PLANT = "tools/planted_path_no_tier_two_job_collects.py"

#: A borrowed item id for the synthetic allowlists below. NOT a real item, and
#: spelled so no search for a live id finds it here.
SYNTHETIC_ITEM = "CS-0"


def test_a_deletion_on_no_recorded_permission_is_refused_even_where_tier_two_runs_it() -> None:
    """CS-1073 - THE REFUTATION THIS ARM EXISTS TO KEEP CLOSED.

    THE FIRST VERSION OF THIS RULE COULD NOT REFUSE ANYTHING IT WOULD EVER FACE.
    It granted cover whenever a required tier-2 job named a CONTAINING target,
    and a required tier-2 job runs the bare suite root - so every path under
    `tests/` was unconditionally governed. An adversary measured the
    consequence: a save shard carrying `--ignore=tests/save` put the WHOLE save
    directory in no tier-1 shard, since the catch-all already ignores it, and
    every zero-argument arm in this module stayed GREEN. The base commit was
    RED. The extension had made the tree weaker than the thing it extended.

    SO THE PLANTS HERE ARE THE ADVERSARY'S OWN, NOT FRIENDLIER ONES. Each names
    a path tier 2 demonstrably runs, and each must be refused on the allowlist
    alone. A rule that can only refuse paths outside the suite root is not a
    rule about this lane.
    """
    invocations = tier_two_pytest_invocations(required_tier_two_matchers())
    assert invocations, "nothing was parsed, so every plant below would be caught vacuously"

    escaped: list[str] = []
    for path in DELETIONS_THE_LANE_COULD_PLAUSIBLY_WRITE:
        assert path not in PERMITTED_DELETIONS, (
            f"{path} is on the recorded allowlist, so this plant cannot grade the refusal"
        )
        assert run_by_any(invocations, path), (
            f"a REQUIRED tier-2 job does not run {path}, so a refusal below would prove"
            " nothing about the allowlist - the tier-2 half would have refused it anyway"
        )
        if not ungoverned_deletions({"planted": [path]}, invocations, PERMITTED_DELETIONS):
            escaped.append(path)

    assert escaped == [], (
        f"{escaped} were planted as tier-1 deletions and permitted. Every one is run by a"
        " required tier-2 job, so a containment test cannot refuse them; only a recorded"
        " permission can, and that is the whole point of one"
    )


def test_a_recorded_permission_no_required_tier_two_job_honours_is_still_refused() -> None:
    """CS-1073 - the two conditions are CONJUNCTIVE, and this grades the second.

    The allowlist alone would let a recorded permission outlive the tier-2 job
    that made it safe: someone narrows or retargets tier 2, the entry says
    nothing, and a module runs in no lane at all. So an allowlisted path that no
    required tier-2 job runs must still be red.

    GRADED WITH A SYNTHETIC ALLOWLIST rather than by editing the real one. The
    shipped entry is honoured by tier 2 - that is why the tree is green - so
    proving this half needs a permission the tier-2 read will refuse, and
    :data:`UNCOVERED_PLANT` is a path outside every tier-2 target.
    """
    invocations = tier_two_pytest_invocations(required_tier_two_matchers())
    assert invocations, "nothing was parsed, so the plant below would be caught vacuously"

    permitted = {UNCOVERED_PLANT: SYNTHETIC_ITEM}
    refused = ungoverned_deletions({"planted": [UNCOVERED_PLANT]}, invocations, permitted)

    assert named_paths(refused) == [f"planted -> {UNCOVERED_PLANT}"], (
        f"a recorded permission for {UNCOVERED_PLANT} was honoured while NO required"
        " tier-2 job runs that path. The allowlist would then be the only condition, and"
        " an entry nobody revisits would outlive the job that made it safe"
    )


#: Every way a tier-2 job can go on naming the suite root while collecting less
#: of it. ASSEMBLED FROM :data:`NARROWING_FLAGS` RATHER THAN LISTED, so a flag
#: added to that vocabulary is graded here without anyone remembering to.
#:
#: MEASURED: with the tier-2 side read for its targets and its `--ignore=` only,
#: EVERY one of these left the shipped deletion reading as covered by a job that
#: would not have run it. `-p` is in the vocabulary and belongs there - measured
#: on this box, `-p no:unittest` silently drops `unittest.TestCase` collection
#: and exits 0 - and tier 2 is now load-bearing for a test tier 1 deleted, which
#: is exactly where a silent plugin drop costs the most.
#: What each option-taking narrowing flag is planted WITH. A flag absent from
#: this mapping takes no value and is planted bare, which is why
#: `--collect-only` is not here: writing it as `--collect-only=tests` would
#: grade the token scan against a spelling pytest does not accept.
NARROWING_PLANT_VALUES = {
    "-m": "not slow",
    "-k": "not phase4",
    "--ignore": SUITE_ROOT,
    "--ignore-glob": SUITE_ROOT + "/*",
    "--deselect": SUITE_ROOT,
    "-p": "no:python",
    "--maxfail": "1",
}


def narrowing_plants() -> list[tuple[str, list[str]]]:
    """One planted narrowing per flag in :data:`NARROWING_FLAGS`.

    Returns:
        (the flag, the tokens to append) for each.
    """
    plants: list[tuple[str, list[str]]] = []
    for flag in NARROWING_FLAGS:
        value = NARROWING_PLANT_VALUES.get(flag)
        if value is None:
            plants.append((flag, [flag]))
        elif flag.startswith("--"):
            plants.append((flag, [f"{flag}={value}"]))
        else:
            plants.append((flag, [flag, value]))
    return plants


def test_a_narrowed_required_tier_two_job_is_no_cover_at_all() -> None:
    """CS-1073 - the second hole the adversarial pass found, closed by vocabulary.

    THE TIER-2 SIDE WAS READ FOR ITS TARGETS AND ITS `--ignore=` AND NOTHING
    ELSE. Nothing anywhere in this repository reads tier2.yml's commands, so a
    `-m 'not slow'`, a `-k`, a `--deselect`, an `--ignore-glob=` or a
    `--collect-only` added there subtracted the deleted module from the only
    lane still running it, in total silence, with every arm green. That is the
    family `test_no_selection_narrowing_hides_in_the_pytest_configuration`
    exists for, reintroduced one lane out.

    THE PLANTS ARE DERIVED FROM :data:`NARROWING_FLAGS`, not listed, so the two
    lanes are read with ONE vocabulary and a flag added to it is graded on both
    sides without anyone remembering to.

    EACH PLANT IS CHECKED TO HAVE LANDED. A mutation that never applied and a
    detector that missed it print the same thing.
    """
    invocations = tier_two_pytest_invocations(required_tier_two_matchers())
    assert invocations, "nothing was parsed, so every plant below would be caught vacuously"

    deletions = lane_deletions()
    assert deletions, "the lane deletes nothing, so there is nothing to lose cover"
    assert ungoverned_deletions(deletions, invocations, PERMITTED_DELETIONS) == [], (
        "the shipped tree is already refused, so a red below attributes to nothing"
    )

    expected = sorted(
        f"{job_id} -> {path}" for job_id, paths in deletions.items() for path in paths
    )
    escaped: list[str] = []
    for label, appended in narrowing_plants():
        narrowed = [(where, [*tokens, *appended]) for where, tokens in invocations]
        assert narrowed != invocations, f"{label}: the plant never landed, so it graded nothing"
        refused = ungoverned_deletions(deletions, narrowed, PERMITTED_DELETIONS)
        if named_paths(refused) != expected:
            escaped.append(f"{label} -> {named_paths(refused)}")

    assert escaped == [], (
        f"{escaped}. A required tier-2 job carrying any of those selectors collects less"
        " than its target names, so it cannot be the thing that makes a tier-1 deletion"
        " safe - and nothing else in this repository reads that file's commands"
    )


def test_a_retargeted_required_tier_two_job_is_no_cover_either() -> None:
    """CS-1073 - the narrowing scan is not the only way tier 2 can stop covering.

    A job that simply stops NAMING the path collects none of it, with no
    narrowing selector written anywhere. Graded beside the scan above so neither
    mechanism can be deleted on the grounds that the other one covers it.
    """
    invocations = tier_two_pytest_invocations(required_tier_two_matchers())
    assert invocations, "nothing was parsed, so the plant below would be caught vacuously"
    deletions = lane_deletions()
    assert deletions, "the lane deletes nothing, so there is nothing to lose cover"

    expected = sorted(
        f"{job_id} -> {path}" for job_id, paths in deletions.items() for path in paths
    )
    retargeted = [
        (where, [token for token in tokens if not is_target(token)])
        for where, tokens in invocations
    ]
    assert retargeted != invocations, "the plant never landed, so it graded nothing"

    refused = ungoverned_deletions(deletions, retargeted, PERMITTED_DELETIONS)
    assert named_paths(refused) == expected, (
        "a required tier-2 job that names no target at all was still read as covering the"
        f" lane's deletions; the refusals were {refused}"
    )


def test_the_permission_is_spent_by_what_the_driver_requires_not_by_what_tier_two_declares() -> (
    None
):
    """CS-1073 - REQUIRED is the load-bearing word, and it is graded as such.

    A job tier 2 merely DECLARES proves nothing. The driver waits on the jobs in
    ``CI_TIER2.required`` and refuses to ship a row without them; anything else
    can be skipped, cancelled or red indefinitely while the lane keeps shipping,
    so a deletion covered only by such a job is covered by nothing.

    MEASURED BY SUBTRACTION rather than argued, and the subtraction is the set
    the driver does NOT require. Ask the same question with only the unrequired
    jobs visible, and every deletion must lose its cover; ask it with nothing
    visible, and the same.

    NOT BY DROPPING ONE MATCHER AT A TIME, and that is deliberate. More than one
    required job runs the suite root, so removing any single one leaves the
    deletions still covered - correctly. An arm built on that subtraction would
    be red over healthy redundancy.
    """
    required = required_tier_two_matchers()
    deletions = lane_deletions()
    assert deletions, (
        "the lane deletes nothing, so this arm is grading a shape the workflow does not"
        " have. Delete the arm rather than leave it passing over an empty question"
    )

    jobs = tier_two_document().get("jobs")
    assert isinstance(jobs, dict), f"{TIER2_RELATIVE} declares no jobs mapping"
    declared = [
        matchable(str(job.get("name", job_id)))
        for job_id, job in jobs.items()
        if isinstance(job, dict)
    ]
    unrequired = tuple(
        name
        for name in declared
        if not any(name.startswith(m) or m.startswith(name) for m in required)
    )
    assert unrequired, (
        f"{TIER2_RELATIVE} declares nothing outside the driver's required set {list(required)},"
        " so this arm cannot tell a required job from a declared one"
    )

    expected = sorted(
        f"{job_id} -> {path}" for job_id, paths in deletions.items() for path in paths
    )
    thinner = ungoverned_deletions(
        deletions, tier_two_pytest_invocations(unrequired), PERMITTED_DELETIONS
    )
    assert named_paths(thinner) == expected, (
        f"a deletion stayed covered with only the UNREQUIRED tier-2 jobs {list(unrequired)}"
        " visible. Those jobs can be red or skipped for the life of the project without the"
        " driver noticing, so a path only they collect is collected by nothing the lane"
        " waits on"
    )
    blind = ungoverned_deletions(deletions, tier_two_pytest_invocations(()), PERMITTED_DELETIONS)
    assert named_paths(blind) == expected, (
        "a deletion stayed covered with NO tier-2 job visible at all, so the cross-check is"
        " not reading the workflow it claims to"
    )


def test_both_shards_run_in_parallel_because_one_of_them_owns_an_open_item() -> None:
    """CS-448 - the flag its acceptance names must be pinned on EVERY shard that runs it.

    THE NAME SAYS BOTH AND THE ARM READS EVERY SHARD. It is kept because
    `docs/LEDGER.md` cites it by name and that file is append-only.

    Only the catch-all job's invocation was ever asserted to carry ``-n auto``,
    and the test CS-448 is filed against lives elsewhere. MEASURED twice:
    deleting the flag from the save job alone left every arm in this module and
    the drift guard green, and a THIRD shard appended with no flag at all was
    invisible to the id pair this arm used to name.
    """
    serial = sorted(
        job_id for job_id, tokens in suite_shards().items() if "-n auto" not in " ".join(tokens)
    )

    assert serial == [], (
        f"the {serial} shards do not run in parallel, so each of them reverts to serial"
        " and puts this lane back over the cutoff while saying nothing about why"
    )


def test_no_third_job_runs_the_suite_without_being_part_of_the_partition() -> None:
    """CS-896 and CS-1060 - the partition is over EVERY job that runs pytest.

    A job that ran its own pytest outside the shard table would be outside the
    argument above, and the partition arm would keep passing while the lane
    silently ran something nobody reasoned about.

    BOTH SIDES ARE DERIVED FROM THE PARSED DOCUMENT AND NEITHER IS A LIST. The
    shard table is every job carrying a step named :data:`SUITE_STEP`; the other
    side is every job whose steps mention pytest at all, whatever the step is
    called. A job that invoked pytest from a step under another name would show
    up on the second side and not the first, which is exactly the hole this arm
    exists to close - and the previous version, which compared against two
    hardcoded ids, could not see it once a third id was legitimate.
    """
    invoking = sorted(
        job_id
        for job_id, job in every_parsed_job().items()
        if any(
            isinstance(step, dict) and "pytest" in str(step.get("run", ""))
            for step in (job.get("steps") or [])
        )
    )

    assert sorted(suite_shards()) == invoking, (
        f"the jobs invoking pytest are {invoking} but the shard table is"
        f" {sorted(suite_shards())}. Every job that runs the suite must do it from a"
        f" step named {SUITE_STEP!r}, or the partition above says nothing about it"
    )


def test_every_job_reports_its_own_duration_with_the_identical_step() -> None:
    """CS-896 - the duplicated step is duplicated, and that is the risk.

    THE ACCEPTANCE IS PER JOB. "Reports its own duration against a budget" is a
    claim about whichever job is slowest, so a shard without the step could run
    to the cutoff reporting nothing - the cancellation-shaped silence the item
    was filed about.

    THE STEP IS COPIED RATHER THAN SHARED, because a job key cannot be written
    once for several jobs, and its shell carries five refusals that took a
    measurement each to find. A copy that drifts keeps one of them and loses
    another, so every copy is asserted BYTE-IDENTICAL rather than merely
    present.

    THE JOB SET IS THE PARSER'S, NOT A PAIR OF LITERALS. MEASURED on this edit:
    with the ids written out, appending a third job turned this arm red for the
    wrong reason - it reported an unexpected id rather than a missing report -
    and the natural repair was to add the id, which is how a list stops grading.
    """
    scripts: dict[str, str] = {}
    wrong: list[str] = []
    for job_id, job in every_parsed_job().items():
        matched = [
            step
            for step in (job.get("steps") or [])
            if isinstance(step, dict) and step.get("name") == REPORT_STEP
        ]
        if len(matched) != 1:
            wrong.append(f"{job_id} declares {len(matched)}")
            continue
        scripts[job_id] = str(matched[0].get("run"))

    assert wrong == [], (
        f"{wrong} steps named {REPORT_STEP!r}; every job in this lane must report its"
        " own duration exactly once, or it can reach the cutoff reporting nothing"
    )
    distinct = sorted(set(scripts.values()))
    assert len(distinct) == 1, (
        f"the duration steps of {sorted(scripts)} are NOT identical, so one shard grades"
        " its duration by rules the others do not"
    )


def test_the_guard_rejects_two_jobs_whose_cutoffs_disagree() -> None:
    """CS-896 - a per-job level is only a level while every job states the same one.

    The multiplicity rejection was relaxed when the lane gained a second job:
    ``timeout-minutes`` is a JOB key, so two jobs state it twice and neither is
    a restatement. What replaced it is this - the statements must AGREE - and a
    relaxation nobody re-armed is how a cutoff gets raised one job at a time.
    """
    shipped = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8")
    stated = shipped.count("\n    timeout-minutes:")
    assert stated > 1, (
        "the lane no longer states a per-job cutoff more than once, so this arm is"
        " grading a shape the workflow does not have"
    )

    divergent = shipped.replace(
        f"timeout-minutes: {EXPECTED_POLICY_CUTOFF_MINUTES}",
        f"timeout-minutes: {EXPECTED_POLICY_CUTOFF_MINUTES + 5}",
        1,
    )
    assert divergent != shipped, "the cutoff was not found, so nothing was made to disagree"

    value, problem = drift_guard._tier1_declaration(  # noqa: SLF001 - the site under test
        divergent, drift_guard.TIER1_TIMEOUT_KEY, per_job=True
    )

    assert value is None, "a lane whose two jobs carry different cutoffs was accepted"
    assert problem is not None, "the disagreement was rejected without saying why"
    assert "DISAGREE" in problem, f"the reason does not name the disagreement: {problem}"


def test_every_job_records_its_start_before_it_does_anything_else() -> None:
    """CS-896 - a start recorded late under-reports by whatever ran before it.

    THE STEP IS FIRST ON PURPOSE AND ONLY A COMMENT SAID SO. Moving it below the
    install leaves the shard reporting a duration that excludes checkout, the
    interpreter setup and the dependency install - 13 seconds on a warm cache
    and far more on a cold one - while still printing "within budget". MEASURED:
    the move left every arm in this file green, which is why this one exists.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"

    misplaced: list[str] = []
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = [step for step in (job.get("steps") or []) if isinstance(step, dict)]
        if not steps or steps[0].get("name") != START_STEP:
            first = steps[0].get("name") if steps else "(no steps)"
            misplaced.append(f"{job_id} starts with {first!r}")

    assert misplaced == [], (
        f"a job does not record its start first, so it measures less than it ran:"
        f" {misplaced}. Every job must open with {START_STEP!r}"
    )


def test_every_duration_report_runs_on_every_outcome() -> None:
    """CS-896 - `if: always()` is the load-bearing half of the report.

    A comparison that ran only when every earlier step succeeded would report
    nothing on exactly the runs worth measuring - a red or cancelled lane. The
    workflow's own comment calls this "the load-bearing half"; nothing asserted
    it, and MEASURED, deleting the key from one shard left every arm green.

    THE JOB SET IS THE PARSER'S. It was a pair of ids, and a third job appended
    with no report step at all turned this arm red for the wrong reason.
    """
    conditions: dict[str, object] = {}
    for job_id, job in every_parsed_job().items():
        for step in job.get("steps") or []:
            if isinstance(step, dict) and step.get("name") == REPORT_STEP:
                conditions[job_id] = step.get("if")

    missing = sorted(job_id for job_id in every_parsed_job() if job_id not in conditions)
    assert missing == [], (
        f"{missing} carry no {REPORT_STEP!r} step at all, so they report nothing on any"
        " outcome whatever their condition says"
    )
    silent = sorted(job_id for job_id, value in conditions.items() if value != "always()")
    assert silent == [], (
        f"the duration report in {silent} does not run on every outcome, so those shards"
        " report nothing on precisely the runs worth measuring"
    )


def jobs_without_a_cutoff(jobs: dict[str, Any]) -> list[str]:
    """Every job of ``jobs`` that states no runaway cutoff.

    SEPARATED FROM THE ARM THAT USES IT SO IT CAN BE GRADED. An arm that reads
    the shipped tree and finds nothing wrong is a statement about the shipped
    tree and NOT about the arm: it passes identically whether it looks at
    :data:`TIMEOUT_KEY` or at nothing at all. Lifting the question out lets the
    arm below hand it a document with a known hole and check it says so.

    Args:
        jobs: A jobs mapping, parsed from the workflow or synthesised from one.

    Returns:
        The ids stating no :data:`TIMEOUT_KEY`, sorted.
    """
    return sorted(
        str(job_id)
        for job_id, job in jobs.items()
        if not isinstance(job, dict) or job.get(TIMEOUT_KEY) is None
    )


def test_every_job_the_parser_sees_states_the_runaway_cutoff() -> None:
    """CS-896 - the guard counted job ids with a pattern, and a comment walked past it.

    guard (k) compares its count of `timeout-minutes` statements against a count
    of job ids matched by a regex anchored at `:$`. MEASURED: a third job
    declared `  third:  # a scratch job`, or with a quoted id, was invisible to
    that pattern while PyYAML resolved it to a real job - so the two counts
    agreed, the guard stayed green, and that job would have run under GitHub's
    360-minute default instead of this lane's cutoff.

    THIS ARM IS THE AUTHORITY AND THE REGEX IS THE CHEAP HALF. A parser was
    already in this module - :func:`workflow_document` - so the complete check
    costs nothing and cannot be defeated by a spelling. It asks the question the
    guard means to ask: does EVERY job GitHub will actually run declare the
    cutoff?
    """
    uncapped = jobs_without_a_cutoff(dict(every_parsed_job()))

    assert uncapped == [], (
        f"{uncapped} declare no {TIMEOUT_KEY!r}, so they run under the platform default"
        " rather than this lane's runaway cutoff"
    )


def test_a_shard_that_states_no_cutoff_is_named_rather_than_walked_past() -> None:
    """CS-1060 - the arm above passes over the shipped tree, and only over that.

    THE CLAUSE THE ACCEPTANCE ASKS FOR. A cutoff check that has only ever seen a
    healthy document is a check nobody has measured: it reports the same empty
    list whether it reads :data:`TIMEOUT_KEY`, reads a key that does not exist,
    or reads nothing. So each shard's cutoff is REMOVED IN TURN and the detector
    is required to name that shard and only that shard.

    IN TURN, AND NOT ONCE. A detector that stopped at the first job, or that
    reported the LAST hole it found, passes a single-mutation grading and then
    misses the shard nobody thought to try. Every job the parser resolves is
    mutated here, and the failure names each one that escaped rather than the
    first.

    THE MUTATION IS APPLIED TO A COPY. The shipped workflow is never written to
    - a graded mutation that touched the tree would poison every sibling arm in
    this run and, if the process were killed mid-grade, would survive on disk.
    """
    jobs = every_parsed_job()
    escaped: list[str] = []
    for job_id in sorted(jobs):
        mutated: dict[str, Any] = {}
        for other, job in jobs.items():
            copied = dict(job)
            if other == job_id:
                copied.pop(TIMEOUT_KEY, None)
            mutated[other] = copied
        assert TIMEOUT_KEY not in mutated[job_id], (
            f"the mutation never landed on {job_id!r}, so this iteration graded the"
            " unmutated document and a surviving detector is indistinguishable from a"
            " working one"
        )
        named = jobs_without_a_cutoff(mutated)
        if named != [job_id]:
            escaped.append(f"{job_id} -> {named}")

    assert escaped == [], (
        f"{escaped}. A shard whose {TIMEOUT_KEY!r} is deleted must be named by"
        " :func:`jobs_without_a_cutoff`, and by it alone; a shard the detector walks"
        " past runs under the platform's 360-minute default while this lane reports"
        " that every job is capped"
    )


def test_every_job_the_parser_sees_states_the_same_cutoff() -> None:
    """CS-896 - a lane whose shards carry different cutoffs has only the larger one.

    Stated per job is only a cutoff while the statements AGREE. guard (k) checks
    this over the text; this checks it over what the parser resolves, so a
    spelling that changes the value without changing the text pattern cannot
    pass both.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"

    # str() rather than the raw value: a job may state nothing, and None is not
    # orderable against an int. A failure names what was written either way.
    stated = sorted({str(job.get(TIMEOUT_KEY)) for job in jobs.values() if isinstance(job, dict)})

    assert stated == [str(EXPECTED_POLICY_CUTOFF_MINUTES)], (
        f"the jobs state cutoffs {stated}; every job must state exactly"
        f" {EXPECTED_POLICY_CUTOFF_MINUTES}, which is policy and not a tunable"
    )


# ---------------------------------------------------------------------------
# CS-896 - THE LEVELS ARE A RATCHET ONLY WHILE NOTHING CAN OVERRIDE THEM
#
# MEASURED 2026-09-06 (session 65). Three adversaries graded the shipped
# mechanism at 58a30f1 and all three returned REFUTED. Between them they moved
# the effective levels or made the ceiling decorative in ONE LINE, with guard
# (k) printing PASS, this module green at 122 passed, and the 528-test floor
# green. The four routes they measured, none of which any arm could see:
#
#   1. A job-level or step-level `env:` block restating either level. guard (k)
#      anchors its read at the start of a line, so a FLOW mapping - written
#      as a flow mapping restating that key - never begins a line and is
#      invisible to it, while PyYAML resolves it to a real override. This is the
#      regex-versus-parser family AGAIN, one spelling further out than the `:$`
#      trailing-comment hole the session before this one found.
#   2. `continue-on-error` on the job or on the step, which discards the
#      ceiling's `exit 1`. MEASURED ungoverned: the key appeared nowhere under
#      tests/ or tools/, so the one mechanism CS-896 adds was decorative on
#      request.
#   3. The start step writing any SECOND key into `$GITHUB_ENV`, which sets the
#      environment for every later step in that job.
#   4. The report step reading a level it cannot parse. Its three refusals all
#      guard TIER1_STARTED and the two LEVELS get none. `[ 900 -gt "" ]` exits 2
#      with `integer expression expected` on stderr, an `if` condition is exempt
#      from `set -e`, so both comparisons fall to `else` and a 900-second run
#      prints `within budget` and exits 0.
#
# EVERY ARM BELOW GRADES WHAT THE PARSER RESOLVES, NEVER WHAT THE TEXT SPELLS.
# That is the whole lesson of the repairs before them: each matched a spelling
# and the next adversary simply wrote a different one.
# ---------------------------------------------------------------------------

#: The two level keys, by the name GitHub reads.
BUDGET_KEY = "TIER1_BUDGET_SECONDS"
CEILING_KEY = "TIER1_CEILING_SECONDS"
LEVEL_KEYS = (BUDGET_KEY, CEILING_KEY)

#: The key that turns a failing step or job into an advisory one.
ADVISORY_KEY = "continue-on-error"

#: An elapsed value comfortably past every level this lane states, so a report
#: that still calls such a run healthy is reporting on nothing it actually read.
OVER_EVERY_LEVEL_SECONDS = 900


def every_parsed_job() -> dict[str, dict[str, Any]]:
    """Every job THE PARSER resolves, never the ones this module happens to name.

    `fast_job()` addresses one job by id. That is right for arms about that
    job and wrong for arms about the LANE, because a job added later inherits
    none of them - which is exactly how a third job once reached the runner
    under the platform's own 360-minute default.

    Returns:
        Every job, by id.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"
    resolved = {str(key): value for key, value in jobs.items() if isinstance(value, dict)}
    assert resolved, f"{WORKFLOW_RELATIVE} resolved no jobs at all"
    return resolved


def env_blocks_beneath_the_workflow() -> list[tuple[str, dict[str, Any]]]:
    """Every env block GitHub applies AFTER the workflow-level one, located.

    GitHub layers three environments and the later one wins: workflow, then
    job, then step. The workflow block is the owner this lane declares; the
    other two are overrides and there should be none of them.

    Returns:
        (where it sits, the block) for every job-level and step-level env.
    """
    found: list[tuple[str, dict[str, Any]]] = []
    for job_id, job in every_parsed_job().items():
        block = job.get("env")
        if isinstance(block, dict):
            found.append((f"job {job_id!r}", block))
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            block = step.get("env")
            if isinstance(block, dict):
                name = step.get("name", f"index {index}")
                found.append((f"step {name!r} of job {job_id!r}", block))
    return found


def test_no_env_block_the_parser_resolves_overrides_either_level() -> None:
    """CS-896 - a level a later env block can restate is not a level.

    THE MUTATION THIS REFUSES, MEASURED GREEN AGAINST THE SHIPPED TREE: one line
    under the save shard - a flow mapping restating both level keys with higher
    values - left guard (k) printing PASS and its own detail asserting the pair
    was pinned two-way, while PyYAML resolved that shard's effective levels to
    the restated ones. A run long enough to breach the shipped ceiling then
    exited 0 where the shipped levels exit 1.

    THIS ARM READS THE PARSED DOCUMENT, so the flow spelling that defeated the
    regex is the same object here as the block spelling that did not.
    """
    offenders = [
        (where, key, block[key])
        for where, block in env_blocks_beneath_the_workflow()
        for key in LEVEL_KEYS
        if key in block
    ]

    assert offenders == [], (
        f"{WORKFLOW_RELATIVE} lets a later env block restate a level: {offenders}."
        " GitHub applies workflow env, then job env, then step env, and the last"
        " one wins - so a level restated below the workflow block is the level"
        " that actually grades the run, whatever the workflow block says and"
        " whatever guard (k) prints"
    )


def test_no_job_or_step_makes_a_failure_advisory() -> None:
    """CS-896 - the ceiling's `exit 1` is the only thing it adds; one key discards it.

    `continue-on-error` was governed by NOTHING when this was written - it
    appeared nowhere under tests/ or tools/. On the job it also silently
    disables that shard's entire suite, which is a coverage hole well beyond
    the levels.

    The existing ceiling arms assert the SCRIPT's exit code, which stays
    non-zero under this key; GitHub is what discards it. So they are blind to it
    by construction and this arm is not a restatement of them.
    """
    advisory: list[str] = []
    for job_id, job in every_parsed_job().items():
        if ADVISORY_KEY in job:
            advisory.append(f"job {job_id!r} sets {ADVISORY_KEY}={job[ADVISORY_KEY]!r}")
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for index, step in enumerate(steps):
            if isinstance(step, dict) and ADVISORY_KEY in step:
                name = step.get("name", f"index {index}")
                advisory.append(
                    f"step {name!r} of job {job_id!r} sets {ADVISORY_KEY}={step[ADVISORY_KEY]!r}"
                )

    assert advisory == [], (
        f"{WORKFLOW_RELATIVE} makes a failure advisory: {advisory}. The ceiling"
        " fails the lane by exiting non-zero, and this key tells GitHub to"
        " record that failure as a success - so the lane would drift past its"
        " stated ceiling with nothing red, which is CS-896's filed defect"
        " reproduced on CS-896's own repair"
    )


def test_the_start_step_writes_only_the_start_marker_into_the_env_file() -> None:
    """CS-896 - anything the start step exports overrides the env for every later step.

    `$GITHUB_ENV` is not a scratch file: a line written into it sets that
    variable for every subsequent step of the job. A start step that writes a
    second key therefore owns the levels the report step reads, and neither the
    workflow-level block nor guard (k) would show it.
    """
    for job_id, job in every_parsed_job().items():
        steps = job.get("steps")
        assert isinstance(steps, list), f"job {job_id!r} declares no step list"
        for step in steps:
            if not isinstance(step, dict):
                continue
            script = step.get("run")
            if not isinstance(script, str) or "GITHUB_ENV" not in script:
                continue
            # NON-GREEDY, AND THAT IS THE WHOLE ARM. MEASURED 2026-09-06: the
            # greedy first draft of this line scored its OWN mutation GREEN. A
            # plain YAML scalar FOLDS a continuation line into the same string,
            # so a smuggled second write lands on one line beside the first; a
            # greedy run then reached from the first key past the second write
            # to the LAST marker and captured one key where there were two, and
            # the arm reported the property held with the mutation in the tree.
            exported = sorted(
                set(
                    re.findall(
                        r"([A-Za-z_][A-Za-z0-9_]*)=[^\n]*?>>[ \t]*\"?\$GITHUB_ENV",
                        script,
                    )
                )
            )
            assert exported == ["TIER1_STARTED"], (
                f"step {step.get('name')!r} of job {job_id!r} writes {exported} into"
                " $GITHUB_ENV. Only the start marker may be exported: every other key"
                " written there silently replaces the value the report step reads,"
                " including either level"
            )


def report_with_levels(
    tmp_path: Path, elapsed_started: str, levels: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Run the report step's own script with the LEVELS under test.

    `run_report_step` injects `workflow_env()` unconditionally, so every arm
    built on it grades the script against the real levels and none of them can
    reach the branch where a level is the thing that is wrong.

    Args:
        tmp_path: pytest temporary directory.
        elapsed_started: The value for TIER1_STARTED.
        levels: The level variables to set. A None value unsets the key.

    Returns:
        The completed process.
    """
    assert BASH is not None, "guarded by needs_bash"
    script = step_named(REPORT_STEP)["run"]
    assert isinstance(script, str), "the report step declares no run script"
    path = tmp_path / "report_levels.sh"
    path.write_bytes(script.encode("utf-8"))

    env = dict(os.environ)
    env.update(workflow_env())
    env["GITHUB_STEP_SUMMARY"] = (tmp_path / "summary_levels.md").as_posix()
    env["TIER1_STARTED"] = elapsed_started
    env.update(levels)

    return subprocess.run(
        [BASH, "--noprofile", "--norc", "-eo", "pipefail", str(path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=REPORT_STEP_TIMEOUT,
    )


@needs_bash
@pytest.mark.parametrize(
    ("case", "levels"),
    [
        ("ceiling empty", {CEILING_KEY: ""}),
        ("budget empty", {BUDGET_KEY: ""}),
        ("both empty", {BUDGET_KEY: "", CEILING_KEY: ""}),
        ("ceiling carries a unit", {CEILING_KEY: "480s"}),
        ("budget carries a unit", {BUDGET_KEY: "420s"}),
        ("ceiling is a word", {CEILING_KEY: "none"}),
    ],
)
def test_the_report_refuses_a_level_it_cannot_read(
    tmp_path: Path, case: str, levels: dict[str, str]
) -> None:
    """CS-896 - a comparison against an unreadable level is not a comparison.

    THE MEASURED FAILURE, reproduced against the shipped script: with the
    a level left empty, the shell's integer comparison against it exits 2 with
    `integer expression expected` on stderr. An `if` CONDITION is exempt from
    `set -e`, so the script does not stop; both comparisons fall through to
    `else` and it prints the healthiest verdict it has, and exits 0.

    The step's own comment claims "every way that number can be meaningless has
    to end in a refusal rather than in a cheerful verdict". All three refusals
    it ships guard TIER1_STARTED. The two levels get none, which is what this
    arm holds it to.
    """
    # A start far enough back that the run is unambiguously past every level.
    # Read correctly, this MUST NOT produce a healthy verdict.
    started = str(int(time.time()) - OVER_EVERY_LEVEL_SECONDS)
    proc = report_with_levels(tmp_path, started, levels)

    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, (
        f"{case}: the report exited 0 over an unreadable level and said:"
        f" {combined.strip()!r}. A level the shell cannot compare against makes"
        " every branch fall to `else`, so the lane reports the healthiest"
        " verdict it has exactly when its own configuration is broken"
    )
    assert "within budget" not in proc.stdout, (
        f"{case}: the report printed a within-budget verdict over an unreadable"
        f" level: {proc.stdout.strip()!r}"
    )


def test_both_shards_run_the_same_report_script() -> None:
    """CS-896 - a repair applied to one shard's copy leaves the other unrepaired.

    The two jobs carry the report step as duplicated text rather than a shared
    reference, so nothing structural keeps them in step. The session before this
    one found a guard that read ONE SIDE of this very split; this arm is what
    makes that impossible for this step.
    """
    scripts: dict[str, str] = {}
    for job_id, job in every_parsed_job().items():
        steps = job.get("steps")
        assert isinstance(steps, list), f"job {job_id!r} declares no step list"
        matched = [
            step for step in steps if isinstance(step, dict) and step.get("name") == REPORT_STEP
        ]
        assert len(matched) == 1, (
            f"job {job_id!r} declares {len(matched)} steps named {REPORT_STEP!r};"
            " every job in this lane must report its own duration exactly once"
        )
        script = matched[0].get("run")
        assert isinstance(script, str), f"job {job_id!r} report step declares no run script"
        scripts[job_id] = script

    distinct = sorted(set(scripts.values()))
    assert len(distinct) == 1, (
        f"the {sorted(scripts)} jobs run DIFFERENT report scripts. They are"
        " duplicated text, so a repair made to one is not made to the other and"
        " the shard nobody looked at keeps the defect"
    )


#: A single quote, SPELLED rather than written. The plants below assemble a
#: level statement, and a literal one here would make this module a second
#: owner of the number - which guard (k) catches, correctly.
QUOTE = chr(39)


def override_line(key: str, value: str, *, flow: bool) -> str:
    """A job-level env block restating one level, ASSEMBLED rather than written.

    Assembled for the reason :func:`restatement` gives: a plant written as one
    literal would make THIS MODULE a second owner of the number and redden the
    second-owner arm against the real tree. MEASURED 2026-09-06 - the first
    draft of these arms did exactly that and guard (k) caught it.

    Args:
        key: The level key to restate.
        value: The value to restate it as.
        flow: True for the inline brace spelling that defeated the pattern,
            False for the ordinary block spelling that did not.

    Returns:
        The lines to splice under a job, newline-terminated.
    """
    quoted = QUOTE + value + QUOTE
    if flow:
        return "    env: {" + key + ": " + quoted + "}" + chr(10)
    return "    env:" + chr(10) + "      " + key + ": " + quoted + chr(10)


def job_with(extra: str) -> str:
    """The shipped workflow with `extra` spliced under the save shard.

    Args:
        extra: Lines to insert, newline-terminated.

    Returns:
        The mutated workflow text.
    """
    shipped = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8")
    head = "  " + SAVE_JOB_ID + ":" + chr(10)
    start = shipped.index(head)
    cut = shipped.index(chr(10), shipped.index("runs-on:", start)) + 1
    return shipped[:cut] + extra + shipped[cut:]


@pytest.mark.parametrize("flow", [True, False], ids=["flow mapping", "block mapping"])
@pytest.mark.parametrize("key", list(LEVEL_KEYS))
def test_the_guard_reads_the_level_a_later_env_block_actually_imposes(key: str, flow: bool) -> None:
    """CS-896 - a level a job can restate is not pinned, whatever the guard prints.

    MEASURED 2026-09-06 by an adversary that wrote none of this: the FLOW
    spelling moved the save shard's effective levels while guard (k) printed
    PASS and its detail asserted the pair was pinned two ways. The BLOCK
    spelling was caught. One spelling of one key was the whole difference, which
    is why both are graded here rather than the one that broke.
    """
    mutated = job_with(override_line(key, "599", flow=flow))
    problems = drift_guard._tier1_effective_levels(  # noqa: SLF001 - the site under test
        mutated, EXPECTED_RECORDED_BUDGET, EXPECTED_RECORDED_CEILING
    )

    assert problems, (
        f"a job-level env restating {key} in the {'flow' if flow else 'block'}"
        " spelling was accepted, so that job runs against a level nothing owns"
    )
    assert any(key in problem for problem in problems), (
        f"the rejection does not name {key}: {problems}"
    )


@pytest.mark.parametrize("where", ["job", "step"])
def test_the_guard_rejects_a_lane_that_records_its_own_failure_as_a_success(
    where: str,
) -> None:
    """CS-896 - the ceiling's non-zero exit is the only thing the ceiling adds.

    `continue-on-error` was governed by NOTHING when this was written. On a job
    it also silently disables that shard's whole suite, so the blast radius is
    well past the levels.
    """
    advisory = "    " + ADVISORY_KEY + ": true" + chr(10)
    if where == "job":
        mutated = job_with(advisory)
    else:
        shipped = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8")
        anchor = "      - name: " + REPORT_STEP + chr(10)
        assert anchor in shipped, "the report step was not found by name"
        advisory_step = "        " + ADVISORY_KEY + ": true" + chr(10)
        mutated = shipped.replace(anchor, anchor + advisory_step, 1)

    problems = drift_guard._tier1_effective_levels(  # noqa: SLF001 - the site under test
        mutated, EXPECTED_RECORDED_BUDGET, EXPECTED_RECORDED_CEILING
    )

    assert problems, (
        f"a {where} marked {ADVISORY_KEY} was accepted, so a run over the ceiling"
        " would be recorded as a success and the lane would go green over a breach"
    )
    assert any(ADVISORY_KEY in problem for problem in problems), (
        f"the rejection does not name {ADVISORY_KEY}: {problems}"
    )


def test_the_effective_level_read_is_green_on_the_shipped_lane() -> None:
    """The arms above only mean something against a clean floor.

    An arm that reddens on a mutation AND on the shipped tree has proved
    nothing about the mutation.
    """
    shipped = (REPO_ROOT / WORKFLOW_RELATIVE).read_text(encoding="utf-8")
    problems = drift_guard._tier1_effective_levels(  # noqa: SLF001 - the site under test
        shipped, EXPECTED_RECORDED_BUDGET, EXPECTED_RECORDED_CEILING
    )
    assert problems == [], f"the shipped lane does not read clean: {problems}"


@pytest.mark.parametrize("flow", [True, False], ids=["flow mapping", "block mapping"])
def test_the_guard_record_reddens_on_an_overridden_level_not_merely_the_helper(
    tmp_path: Path, green_tree: tuple[Path, list[Path]], flow: bool
) -> None:
    """CS-896 - a reader nothing calls is a reader that grades nothing.

    The arms above call :func:`tools.drift_guard._tier1_effective_levels` directly, so deleting
    its CALL SITE inside the guard would leave every one of them green while the
    guard went blind again - which is the precise shape of the defect they were
    written for. This one goes through the guard's public record instead, so the
    wiring is what it grades.
    """
    root, files = green_tree
    floor, _ = run_guard(root, files)
    assert floor["status"] == "PASS", (
        f"the floor is not green, so a red below attributes to nothing: {floor}"
    )

    # Spliced INSIDE the job rather than appended, because that is where an env
    # block has to sit to override anything.
    override = override_line(CEILING_KEY, "599", flow=flow)
    source = workflow_source()
    anchor = "  fast:" + chr(10)
    assert anchor in source, "the synthetic workflow no longer declares that job"
    mutated = source.replace(anchor, anchor + override, 1)
    assert mutated != source, "nothing was planted"

    root2 = tmp_path / "mutated"
    files2 = build_tree(root2, mutated)
    guard, _ = run_guard(root2, files2)

    assert guard["status"] == "FAIL", (
        "the guard RECORD stayed "
        + str(guard["status"])
        + " while the job it grades ran against an overridden ceiling. The helper"
        " may see it; what matters is whether the guard does"
    )
    rendered_detail = rendered(guard)
    assert CEILING_KEY in rendered_detail, (
        "the guard failed without naming the key that was overridden: " + rendered_detail
    )
