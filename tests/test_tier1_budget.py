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
EXPECTED_XDIST_REQUIREMENT = "pytest-xdist>=3.5,<4"

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
    """The other half of the ratchet, read off the PARSED workflow."""
    assert staged_budget() == EXPECTED_RECORDED_BUDGET
    assert staged_ceiling() == EXPECTED_RECORDED_CEILING
    assert fast_job()["timeout-minutes"] == EXPECTED_POLICY_CUTOFF_MINUTES


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
    """
    condition = step_named(REPORT_STEP).get("if")

    assert condition == "always()", (
        f"the comparison is conditional on success; its `if` is {condition!r}"
    )


def test_the_comparison_reaches_the_run_summary() -> None:
    script = step_named(REPORT_STEP).get("run")

    assert isinstance(script, str), "the report step runs nothing"
    assert "GITHUB_STEP_SUMMARY" in script, "the comparison never reaches the run summary"


def test_the_unit_test_step_runs_in_parallel() -> None:
    """Silently falling back to serial puts the lane back over the cutoff.

    THE ASSERTION IS ON THE PARSED STEP. `-n auto` is spelled twice more in this
    workflow's own comments, so deleting it from the live command left the first
    build's arm - which grepped the file text - green while the lane reverted to
    serial.
    """
    script = step_named(SUITE_STEP).get("run")

    assert isinstance(script, str), "the suite step runs nothing"
    assert "-n auto" in script, f"the unit test step does not run in parallel: {script!r}"
    assert " tests " in f" {script} ", (
        f"the suite step names no explicit target directory: {script!r}"
    )


def test_the_suite_step_never_invokes_pytest_from_the_bare_repo_root() -> None:
    """CONVENTIONS.md section 7.1 - a bare root run can sweep runtime state."""
    script = step_named(SUITE_STEP)["run"]
    tokens = str(script).split()

    assert "tests" in tokens, f"the target directory is not a token of its own: {script!r}"


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
    staged = staged_budget() - 30

    proc = report_for_elapsed(tmp_path, staged)
    seconds, verdict = reported(proc)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert verdict == "within budget", proc.stdout
    assert staged <= seconds <= staged + 2, f"reported {seconds} for a staged {staged}"


@needs_bash
def test_a_run_over_the_budget_warns_and_still_succeeds(tmp_path: Path) -> None:
    """The budget is a REPORT. CONVENTIONS.md section 8: this lane must never be red."""
    staged = staged_budget() + 5
    assert staged <= staged_ceiling(), "the staged duration must sit inside the warn band"

    proc = report_for_elapsed(tmp_path, staged)
    seconds, verdict = reported(proc)

    assert proc.returncode == 0, "over budget turned the lane red:\n" + proc.stdout
    assert verdict == "over budget", proc.stdout
    assert "::warning::" in proc.stdout, f"the breach was not annotated:\n{proc.stdout}"
    assert staged <= seconds <= staged + 2, f"reported {seconds} for a staged {staged}"


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
    """One owner for the pin, which is how tier 2 ends up tolerating its absence."""
    scripts = " ".join(str(step.get("run", "")) for step in workflow_steps())

    assert "install pytest-xdist" not in scripts, (
        "the workflow installs pytest-xdist itself, so the dev extra is not the one owner "
        "of the pin"
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
# The lane runs in two shards, and a shard is where coverage goes missing
# ---------------------------------------------------------------------------

#: The second job. The lane was split on 2026-09-06 after run 34013336391 was
#: CANCELLED at 611s at 99 per cent of the suite with nothing failing.
SAVE_JOB_ID = "save"

#: What the save shard runs, and therefore what the other shard must ignore.
SHARD_BOUNDARY = "tests/save"

#: What the wide shard runs before its ignore is applied.
SUITE_ROOT = "tests"


def job_named(job_id: str) -> dict[str, Any]:
    """One job of the lane, addressed by its id.

    Args:
        job_id: The key under ``jobs``.

    Returns:
        The parsed job.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"
    job = jobs.get(job_id)
    assert isinstance(job, dict), f"{WORKFLOW_RELATIVE} declares no job named {job_id!r}"
    return job


def suite_invocation(job_id: str) -> list[str]:
    """The pytest command one job runs, as tokens.

    Args:
        job_id: The key under ``jobs``.

    Returns:
        The tokens of the single step named :data:`SUITE_STEP`.
    """
    listed = job_named(job_id).get("steps")
    assert isinstance(listed, list), f"the {job_id!r} job declares no step list"
    matched = [step for step in listed if isinstance(step, dict) and step.get("name") == SUITE_STEP]
    assert len(matched) == 1, f"the {job_id!r} job has {len(matched)} steps named {SUITE_STEP!r}"
    script = matched[0].get("run")
    assert isinstance(script, str), f"the {job_id!r} job's suite step runs nothing"
    return script.split()


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


def test_the_two_shards_partition_the_suite_with_no_gap_and_no_overlap() -> None:
    """CS-896 - a shard is exactly where a directory stops being tested silently.

    THE FIRST VERSION OF THIS ARM READ ONE SIDE AND AN ADVERSARY WALKED THROUGH
    THE OTHER. It took the wide shard's ignore list and the narrow shard's
    target and argued a partition from the pair, which says nothing at all about
    what the NARROW shard additionally excludes. Adding one ignore and one
    marker expression to the save job dropped 244 of its 1413 tests - the whole
    of tests/save/test_phase4_gate.py, including the test CS-448's acceptance
    names - and this file, the drift guard and the pre-commit gate all stayed
    green. The docstring claimed the gap case was covered while the gap was
    reachable in one line.

    SO THE PARTITION IS NOW ARGUED FROM THE COMPLETE SELECTOR SET OF BOTH
    SHARDS. The wide shard may narrow itself exactly once, by the ignore that
    names the narrow shard; the narrow shard may not narrow itself at all. Any
    other selector on either side fails, by NAME, because the failure has to say
    which flag reintroduced the hole.
    """
    wide = suite_invocation(JOB_ID)
    narrow = suite_invocation(SAVE_JOB_ID)

    wide_selectors = narrowing_selectors(wide)
    narrow_selectors = narrowing_selectors(narrow)
    narrow_targets = [token for token in narrow if token.startswith(SUITE_ROOT)]

    assert SUITE_ROOT in wide, f"the wide shard names no explicit target directory: {wide}"
    assert narrow_targets == [SHARD_BOUNDARY], (
        f"the narrow shard runs {narrow_targets}, not [{SHARD_BOUNDARY!r}]"
    )
    assert wide_selectors == [f"--ignore={SHARD_BOUNDARY}"], (
        f"the wide shard's narrowing selectors are {wide_selectors}; it may narrow itself"
        f" exactly once, by the ignore naming {SHARD_BOUNDARY!r}, or the two shards are"
        " not a partition"
    )
    assert narrow_selectors == [], (
        f"the narrow shard narrows itself with {narrow_selectors}; whatever those exclude"
        " is run by NEITHER shard and both jobs stay green over it"
    )


def test_both_shards_run_in_parallel_because_one_of_them_owns_an_open_item() -> None:
    """CS-448 - the flag its acceptance names must be pinned on the shard that runs it.

    Only the wide job's invocation was ever asserted to carry ``-n auto``, and
    the test CS-448 is filed against lives in the NARROW one. MEASURED: deleting
    the flag from the save job alone left every arm in this module and the drift guard green,
    so the acceptance could have been silently ungenerated by a one-word edit.
    """
    for job_id in (JOB_ID, SAVE_JOB_ID):
        tokens = suite_invocation(job_id)
        joined = " ".join(tokens)
        assert "-n auto" in joined, f"the {job_id!r} shard does not run in parallel: {joined!r}"


def test_no_third_job_runs_the_suite_without_being_part_of_the_partition() -> None:
    """CS-896 - the partition is over EVERY job, not over the two it names.

    A third job added later that ran its own pytest would be outside the
    argument above, and the arm would keep passing while the lane silently ran
    something a fourth reader knows nothing about. The set of suite-running jobs
    is pinned instead of assumed.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"

    running = sorted(
        job_id
        for job_id, job in jobs.items()
        if isinstance(job, dict)
        and any(
            isinstance(step, dict) and "pytest" in str(step.get("run", ""))
            for step in (job.get("steps") or [])
        )
    )

    assert running == sorted([JOB_ID, SAVE_JOB_ID]), (
        f"the jobs that run pytest are {running}; the partition above reasons about"
        f" exactly {sorted([JOB_ID, SAVE_JOB_ID])} and says nothing about any other"
    )


def test_every_job_reports_its_own_duration_with_the_identical_step() -> None:
    """CS-896 - the duplicated step is duplicated, and that is the risk.

    THE ACCEPTANCE IS PER JOB. "Reports its own duration against a budget" is a
    claim about whichever job is slowest, so a shard without the step could run
    to the cutoff reporting nothing - the cancellation-shaped silence the item
    was filed about.

    THE STEP IS COPIED RATHER THAN SHARED, because a job key cannot be written
    once for two jobs, and its shell carries three refusals that took a
    measurement each to find. A copy that drifts keeps one of them and loses the
    other, so the two are asserted BYTE-IDENTICAL rather than merely both
    present.
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"

    scripts: dict[str, str] = {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if isinstance(step, dict) and step.get("name") == REPORT_STEP:
                scripts[job_id] = str(step.get("run"))

    reporting = sorted(scripts)
    assert reporting == sorted([JOB_ID, SAVE_JOB_ID]), (
        f"the jobs carrying a {REPORT_STEP!r} step are {reporting}, so some job can"
        " reach the cutoff without reporting the duration it took"
    )
    distinct = sorted(set(scripts.values()))
    assert len(distinct) == 1, (
        f"the {len(scripts)} duration steps are NOT identical, so one shard grades its"
        " duration by rules the other does not"
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
    """
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"

    conditions: dict[str, object] = {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if isinstance(step, dict) and step.get("name") == REPORT_STEP:
                conditions[job_id] = step.get("if")

    assert sorted(conditions) == sorted([JOB_ID, SAVE_JOB_ID]), (
        f"the jobs carrying a {REPORT_STEP!r} step are {sorted(conditions)}"
    )
    silent = sorted(job_id for job_id, value in conditions.items() if value != "always()")
    assert silent == [], (
        f"the duration report in {silent} does not run on every outcome, so those shards"
        " report nothing on precisely the runs worth measuring"
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
    jobs = workflow_document().get("jobs")
    assert isinstance(jobs, dict), f"{WORKFLOW_RELATIVE} declares no jobs mapping"

    uncapped = sorted(
        str(job_id)
        for job_id, job in jobs.items()
        if not isinstance(job, dict) or job.get("timeout-minutes") is None
    )

    assert uncapped == [], (
        f"{uncapped} declare no {TIMEOUT_KEY!r}, so they run under the platform default"
        " rather than this lane's runaway cutoff"
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

    The arms above call :func:`_tier1_effective_levels` directly, so deleting
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
