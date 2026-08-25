#!/usr/bin/env python3
"""CS-846 - every shipped control and every shipped guard is graded on whether it grades.

WHAT WAS MEASURED BEFORE THIS MODULE EXISTED, on the tree at the commit this
item was taken from. A conditional early return planted at the head of
``tests/data/test_drift_guard_data.py::test_a_planted_duplicate_is_reported_as_drift``
- the control whose own docstring says "It has to prove the guard FIRES, not
that it RUNS" - left the drift-guard modules, the mypy gate and the pre-commit
gate all green. The same plant put into ``tools/drift_guard.py`` left the whole
consuming set green for two of the nine guards it ships, while the runner went
on reporting nine of nine. Two structures, one silence.

WHY THE POPULATION IS THE DELIVERABLE. This defect was filed twice on the same
day by two agents that did not know of each other, once against a CONTROL and
once against a GUARD. The check they each declined to write was the per-arm
one, and both were right to decline: ``tests/save/reach_guard`` already ships a
gutting guard that modules opt into by calling it on their own ``__file__``,
and its own header records the measurement that finished that idea - of the
five modules that self-apply its sibling, two call the gutting one, so it "is
not a rule the package follows, it is a habit two modules have". Everything
here is derived from ``git ls-files`` plus an AST walk. There is no list to add
a module to and none to forget.

THE TWO HALVES ARE DIFFERENT MECHANISMS BECAUSE THE TWO STRUCTURES GRADE
DIFFERENTLY, and collapsing them would have covered whichever one the author
had in mind. A control and a delegated grader both grade by ASSERTING, so both
are caught by asking whether an exit can be reached without an assertion having
run. A ``guard_`` function grades by RETURNING a status, and returning PASS is
its correct answer nearly always - so no analysis of its exits can see anything
wrong. That half is forced instead: every derived guard is run against a root
whose every read raises, and a guard that answers PASS while recording nothing
about what it could not read is not grading.

WHY THE BLIND ROOT AND NOT AN EMPTY ONE. Measured on this tree, both were
tried. Against an EMPTY directory ``guard_dated`` answers PASS with no skips,
because there is no markdown to scan - so an empty-root criterion reports a
guard that is in fact well covered, and a criterion that manufactures a finding
is one that gets switched off. Against a root whose reads fail, the same guard
answers PASS with a skip for each file it could not read, which is the honest
self-excusing green CONVENTIONS.md section 15.1 describes and
``tools/drift_guard.py`` prints a banner about on every run. Every shipped
guard clears that bar today and an early return clears neither half of it.

THE RESIDUALS ARE ENUMERATED RATHER THAN ASSUMED AWAY, and there are three.

A handful of tests grade by calling something that raises rather than by
asserting, so the assertion-derived population cannot see them and a planted
early return in one of them is NOT caught here. They are re-derived every run
and held to the weaker property that they at least exercise something, so that
exemption is a measured set with an assertion on it rather than a silence.

An exit reachable only from inside a loop body that may never run is not
reported, and neither is an assertion rewritten to a tautology. Both leave the
function's exits graded on paper.

On the guard half, the criterion answers "did it say anything", so a guard
rewritten to answer PASS while FABRICATING a skip record clears it. That is a
deliberate falsification rather than an edit that launders itself, which is the
distinction that matters here: CS-840's lesson is that a guard explaining how
to satisfy it explains how to defeat it wherever the two differ, and the two do
not differ for an honest edit. Both alternatives were measured and rejected
before this one was kept - requiring the blind verdict to DIFFER from the real
one lets ``guard_budgets`` through, which stats rather than reads and answers
identically either way, and requiring the skip to carry the read's own reason
reddens ``guard_topology``, which catches the error and reports a parse failure
instead. A criterion that manufactures a finding on correct code is one that
gets switched off.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from tests import liveness

#: The entry point that decides which guards actually run. A guard the runner
#: never mentions is a guard that stopped grading one level up.
GUARD_RUNNER: Final = "run_all"

#: The pre-existing per-module gutting guard modules opt into by calling it on
#: their own source. Used to prove the derivation here is WIDER than that
#: habit, never to scope it.
OPT_IN_HELPER: Final = "_assert_no_test_is_gutted"


# ---------------------------------------------------------------------------
# Synthetic corpora - authored here, naming no real module.
#
# They are STRINGS rather than real functions on purpose. mypy runs with
# warn_unreachable over tests/, so a real function carrying a bare early return
# would be a mypy finding about this file instead of a fixture for the analysis
# under test - and the conditional shape, which is the one that matters, would
# still have to be a string to sit beside it.
# ---------------------------------------------------------------------------

#: The bare gutting. Caught today by mypy's warn_unreachable as well.
_BARE_RETURN = '''\
def test_alpha() -> None:
    """Gutted."""
    return
    assert compute() == 1
'''

#: The shape CS-846 was filed on. Nothing after it is unreachable, so no
#: unreachable-code check can see it.
_CONDITIONAL_RETURN = '''\
def test_beta(corpus: list[int]) -> None:
    """Gutted, and everything after it still reachable."""
    if corpus:
        return
    assert sum(corpus) == 1
'''

#: The same shape in the other structure - a delegated grader, not a test.
_GUTTED_GRADER = '''\
def _assert_every_row_balances(rows: list[int]) -> None:
    """Gutted grader."""
    if rows:
        return
    assert not [row for row in rows if row < 0]
'''

#: Correct: the early return is a fast path AFTER the grading has happened.
_GRADED_THEN_RETURN = '''\
def test_gamma(corpus: list[int]) -> None:
    """Graded, then short-circuited."""
    assert corpus
    if len(corpus) == 1:
        return
    assert sum(corpus) > 1
'''

#: Correct: both arms grade before the exit, so no path escapes.
_BOTH_ARMS_GRADE = '''\
def test_delta(flag: bool) -> None:
    """Graded on both arms."""
    if flag:
        assert flag is True
    else:
        assert flag is False
    return
'''

#: NOT a member: it computes something for a caller. The assert is a sanity
#: check on the way to a value, and the early return is a boundary case.
_VALUE_RETURNING_HELPER = '''\
def _power(base: int, exponent: int) -> int:
    """A utility that happens to assert."""
    if exponent == 0:
        return 1
    assert exponent > 0
    return base ** exponent
'''

#: A loop may run zero times, so an assertion inside one guarantees nothing to
#: the exit after it. This is the vacuous-green shape one level down.
_LOOP_ONLY_ASSERT = '''\
def test_epsilon(corpus: list[int]) -> None:
    """The only assertion is inside a loop that may not run."""
    for item in corpus:
        assert item > 0
    return
'''

#: A stand-in guard tool. ``{VERDICT}`` and ``{SKIPS}`` are substituted with
#: literals, so the guard under the sweep is real code in a real file that
#: :func:`inspect.getsource` can read - not an object impersonating one.
_STUB_TOOL = "\n".join(
    [
        '"""A stand-in guard tool. No guard this project ships is named here."""',
        "",
        "",
        "def guard_planted(root):",
        '    """Answer having read nothing, exactly as an early return does."""',
        "    assert root is not None",
        "    return {VERDICT}, {SKIPS}",
        "",
    ]
)


def _findings(text: str) -> list[str]:
    """Render the ungraded exits a synthetic corpus carries.

    Args:
        text: Synthetic source.

    Returns:
        ``module:line name`` for each finding.
    """
    _members, findings = liveness.survey_source("synthetic.py", text)
    return [finding.rendered() for finding in findings]


def _population(text: str) -> list[str]:
    """Render the population a synthetic corpus contributes.

    Args:
        text: Synthetic source.

    Returns:
        The member names.
    """
    members, _findings = liveness.survey_source("synthetic.py", text)
    return [member.name for member in members]


def _stub_tool(tmp_path: Path, status: str, skips: list[dict[str, str]]) -> ModuleType:
    """Write and load a one-guard stand-in answering as instructed.

    Args:
        tmp_path: Where the stand-in is written.
        status: The status its guard answers.
        skips: The skip records its guard answers with.

    Returns:
        The loaded stand-in.
    """
    verdict = {"id": "z", "name": "planted", "status": status, "detail": ["said something"]}
    source = _STUB_TOOL.replace("{VERDICT}", repr(verdict)).replace("{SKIPS}", repr(skips))
    path = tmp_path / "stub_guard_tool.py"
    path.write_text(source, encoding="utf-8", newline="\n")
    spec = importlib.util.spec_from_file_location("cs846_stub_guard_tool", path)
    assert spec is not None, "the stand-in produced no import spec"
    assert spec.loader is not None, "the stand-in spec carries no loader"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _blind(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every read fail for the rest of the calling test.

    Args:
        monkeypatch: Pytest's patcher, which undoes this even when an assertion
            fires inside the window.
    """
    for name in ("read_text", "read_bytes", "iterdir", "open"):
        monkeypatch.setattr(Path, name, liveness.unreadable)


# ---------------------------------------------------------------------------
# The derivation itself
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tracked(repo_root: Path) -> list[str]:
    """Every tracked Python file, repo-relative.

    Args:
        repo_root: Repository root.

    Returns:
        Repo-relative paths.
    """
    return liveness.tracked_python_files(repo_root)


@pytest.fixture(scope="module")
def surveyed(repo_root: Path, tracked: list[str]) -> liveness.Survey:
    """One pass of the analysis over the whole tracked tree.

    Args:
        repo_root: Repository root.
        tracked: Repo-relative Python paths.

    Returns:
        The survey.
    """
    return liveness.survey(repo_root, tracked)


def test_the_population_is_derived_from_a_non_empty_file_enumeration(tracked: list[str]) -> None:
    """The floor under everything else. A silent zero would pass as green."""
    count = len(tracked)
    assert count > 1, (
        f"git enumerated {count} tracked Python file(s), so every assertion below is "
        "about a population of nothing"
    )


def test_every_tracked_test_module_contributes_a_member(
    tracked: list[str], surveyed: liveness.Survey
) -> None:
    """No module can escape by not opting in, which is the whole point.

    The per-module gutting guard this project already ships is called by a
    module on its own source, so a module that never calls it is invisible to
    it. This asserts the opposite property directly: every tracked module whose
    name marks it a test module is REPRESENTED in the derived population, and a
    new module joins by existing rather than by remembering.
    """
    holding = {member.module for member in surveyed.members}
    test_modules = {relative for relative in tracked if Path(relative).name.startswith("test_")}
    absent = sorted(test_modules - holding)
    assert test_modules, "no tracked module is named as a test module"
    assert not absent, (
        f"{len(absent)} tracked test module(s) contributed no member, so nothing here "
        f"grades them: {absent}"
    )


def test_the_derivation_reaches_further_than_the_opt_in_guard_beside_it(
    repo_root: Path, tracked: list[str], surveyed: liveness.Survey
) -> None:
    """Measured against the habit, not asserted about it.

    A derived population that happened to cover exactly the modules already
    opting in would be a rename rather than a widening, and its green would say
    nothing. So the opt-in set is DERIVED TOO - by reading which modules CALL
    the pre-existing helper, which is why a module merely naming it in a
    constant does not count - and the assertion is that the population is a
    strict superset.
    """
    opted_in = set()
    for relative in tracked:
        tree = ast.parse((repo_root / relative).read_text(encoding="utf-8"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        if OPT_IN_HELPER in called:
            opted_in.add(relative)

    holding = {member.module for member in surveyed.members}
    opted_count = len(opted_in)
    holding_count = len(holding)
    assert opted_count, (
        f"no tracked module calls {OPT_IN_HELPER}, so this comparison has nothing to "
        "discriminate and its green means nothing"
    )
    assert opted_in <= holding, (
        f"{sorted(opted_in - holding)} opt into the per-module guard and are NOT in the "
        "derived population, so this would replace a check with a narrower one"
    )
    assert holding_count > opted_count, (
        f"the derived population covers {holding_count} module(s) and the opt-in habit "
        f"covers {opted_count}; a derivation that is not wider is a rename"
    )


def test_no_shipped_control_or_grader_can_exit_without_grading(
    surveyed: liveness.Survey,
) -> None:
    """THE RULE. Every member grades before every way out of it.

    A finding here is a function that can return having asserted nothing. It
    reports as passed, and the diff still shows the assertions sitting below
    the cut.
    """
    population = len(surveyed.members)
    rendered = [finding.rendered() for finding in surveyed.findings]
    count = len(rendered)
    assert population > 1, (
        f"the derived population holds {population} member(s), so a clean result below "
        "is a claim about nothing"
    )
    assert not count, (
        f"{count} shipped control(s) or grader(s) can return before grading anything: "
        f"{rendered[:20]}"
    )


def test_every_test_outside_the_population_at_least_exercises_something(
    repo_root: Path, tracked: list[str]
) -> None:
    """The residual, re-derived every run rather than listed once.

    A test that ships no assertion grades by the code under test not raising.
    The assertion-derived population cannot see it, and that is stated rather
    than hidden. What it IS held to is that it calls something: a test that
    neither grades nor acts is the endpoint of this defect, not an exemption
    from it.
    """
    inert: list[liveness.Member] = []
    scanned = 0
    for relative in tracked:
        text = (repo_root / relative).read_text(encoding="utf-8")
        _acts, still = liveness.tests_outside_the_population(relative, text)
        inert.extend(still)
        scanned += 1
    rendered = [f"{member.module}:{member.line} {member.name}" for member in inert]
    count = len(rendered)
    assert scanned > 1, f"the residual census read {scanned} module(s)"
    assert not count, (
        f"{count} test(s) ship neither a grading statement nor a call, so they grade "
        f"nothing at all: {rendered[:20]}"
    )


# ---------------------------------------------------------------------------
# The analysis' POWER, forced rather than asserted about
# ---------------------------------------------------------------------------


def test_a_bare_early_return_is_reported() -> None:
    """The cheapest gutting."""
    found = _findings(_BARE_RETURN)
    assert len(found) == 1, f"expected the bare return to be the only finding, got {found}"


def test_the_conditional_early_return_the_item_was_filed_on_is_reported() -> None:
    """The shape no unreachable-code check can see.

    Everything after the cut is still reachable, so mypy's warn_unreachable and
    the per-module gutting guard both stay silent. This is the mutation the
    acceptance names.
    """
    found = _findings(_CONDITIONAL_RETURN)
    assert len(found) == 1, f"the conditional gutting went unreported, got {found}"


def test_a_grader_that_is_not_a_test_is_reported_the_same_way() -> None:
    """The second structure, on the same terms as the first.

    This item was widened because the identical shape was measured in a GUARD
    rather than a control. A derivation keyed on the word "test" would cover
    one report and not the other.
    """
    found = _findings(_GUTTED_GRADER)
    assert len(found) == 1, f"a gutted delegated grader went unreported, got {found}"
    assert _population(_GUTTED_GRADER) == ["_assert_every_row_balances"], (
        "the grader did not enter the population, so the finding above is incidental"
    )


def test_an_early_return_after_the_grading_is_not_reported() -> None:
    """The boundary. A fast path below the assertion is correct code."""
    found = _findings(_GRADED_THEN_RETURN)
    assert not found, f"a graded fast path was reported as a hole: {found}"


def test_a_return_both_arms_of_an_if_have_graded_before_is_not_reported() -> None:
    """The boundary that needs the branch merge to be right."""
    found = _findings(_BOTH_ARMS_GRADE)
    assert not found, f"an exit graded on both arms was reported as a hole: {found}"


def test_a_value_returning_helper_that_asserts_is_not_in_the_population() -> None:
    """The filter that keeps utilities out.

    Measured on this tree before it existed: every finding the analysis raised
    was a helper computing a value with a sanity assert in it, nine of them,
    and not one was a grader. A check that reports nine false positives on
    correct code is a check that gets switched off.
    """
    assert not _population(_VALUE_RETURNING_HELPER), (
        "a value-returning utility entered the grader population"
    )
    assert not _findings(_VALUE_RETURNING_HELPER), (
        "a value-returning utility's boundary return was reported as a hole"
    )


def test_an_assertion_inside_a_loop_does_not_license_the_exit_after_it() -> None:
    """A loop over an empty collection runs nothing.

    Treating an assertion inside one as guaranteed would import the vacuous
    green into the analysis that is meant to catch it.
    """
    found = _findings(_LOOP_ONLY_ASSERT)
    assert len(found) == 1, (
        f"an exit reachable with the loop never entered was treated as graded: {found}"
    )


# ---------------------------------------------------------------------------
# The guard half
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def guard_tools(repo_root: Path, tracked: list[str]) -> list[str]:
    """Every tracked tool that ships a guard, derived rather than named.

    Args:
        repo_root: Repository root.
        tracked: Repo-relative Python paths.

    Returns:
        Repo-relative paths.
    """
    return liveness.guard_tools(repo_root, tracked)


def _load(path: Path, name: str) -> ModuleType:
    """Load a module by path under a private name.

    Args:
        path: The module's path.
        name: The private name to load it under.

    Returns:
        The loaded module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None, f"{path.name} produced no import spec"
    assert spec.loader is not None, f"{path.name} spec carries no loader"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def loaded_guard_tools(repo_root: Path, guard_tools: list[str]) -> dict[str, ModuleType]:
    """Every derived guard tool, loaded once.

    Args:
        repo_root: Repository root.
        guard_tools: Repo-relative paths of the derived tools.

    Returns:
        Repo-relative path to loaded module.
    """
    return {
        relative: _load(repo_root / relative, f"cs846_guard_tool_{index}")
        for index, relative in enumerate(guard_tools)
    }


def test_the_repository_ships_at_least_one_guard_tool(guard_tools: list[str]) -> None:
    """The floor under the guard half.

    The tools DIRECTORY is named because CLAUDE.md section 2.1 names it; the
    tools inside it and the guards inside those are derived. A derivation that
    quietly resolved to nothing would leave every guard assertion below green
    about an empty set, which is the exact silence this module is about.
    """
    count = len(guard_tools)
    assert count, (
        f"no tracked module under {liveness.GUARD_TOOL_DIRECTORY}/ defines a guard, so "
        "every guard assertion below is green about nothing"
    )


def test_every_derived_guard_is_reached_by_its_runner(
    repo_root: Path, guard_tools: list[str]
) -> None:
    """A guard the runner never names is a guard that never runs.

    The runner lists the guards it drives, so a new one only ever runs when
    someone remembers to add it there. That is the same silence one level up,
    and it is cheap to close: the population comes from the definitions and the
    runner's body is read for the names it mentions.
    """
    unreached: list[str] = []
    derived: list[str] = []
    for relative in guard_tools:
        text = (repo_root / relative).read_text(encoding="utf-8")
        names = liveness.guard_function_names(text)
        derived.extend(f"{relative}::{name}" for name in names)
        assert liveness.defines(text, GUARD_RUNNER), (
            f"{relative} defines guards and no {GUARD_RUNNER} to drive them, so nothing "
            "here can tell which of them ever run"
        )
        reached = liveness.names_reached_by(text, GUARD_RUNNER)
        unreached.extend(f"{relative}::{name}" for name in sorted(set(names) - reached))
    count = len(derived)
    assert count > 1, f"{count} guard(s) were derived, so this is green about nothing"
    assert not unreached, (
        f"{unreached} are defined and {GUARD_RUNNER} never mentions them, so they ship "
        "without ever running"
    )


def test_no_shipped_guard_answers_pass_about_a_tree_it_could_not_read(
    loaded_guard_tools: dict[str, ModuleType], repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE RULE FOR GUARDS. Green with nothing recorded is not a verdict.

    CONVENTIONS.md section 15.1, which the tool prints on every run: a guard
    may be green while self-excusing, and a green verdict means nothing without
    the list of what was never looked at. A guard replaced by an early return
    answers PASS and records nothing, which fails both halves.

    The enumeration happens BEFORE the reads start failing, so every guard is
    handed the same file list a real run would give it and the blindness is
    about reading rather than about finding.
    """
    enumerated = {
        relative: module.enumerate_files(repo_root)
        for relative, module in loaded_guard_tools.items()
    }
    _blind(monkeypatch)

    silent: list[str] = []
    graded = 0
    for relative, module in loaded_guard_tools.items():
        files, source, _skips = enumerated[relative]
        for verdict in liveness.blind_verdicts(module, repo_root, files, source):
            graded += 1
            if liveness.silently_green(verdict):
                silent.append(f"{relative}::{verdict.function} [{verdict.guard_id}]")

    count = len(silent)
    assert graded > 1, f"the blind sweep reached {graded} guard(s), so it grades nothing"
    assert not count, (
        f"{count} guard(s) answered PASS about a tree they could not read while recording "
        f"nothing they had skipped: {sorted(silent)}"
    )


def test_the_blind_sweep_reaches_every_guard_each_tool_defines(
    loaded_guard_tools: dict[str, ModuleType], repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sweep that quietly skipped a guard would report the same clean result.

    The population is read from each module's OWN source through
    :func:`inspect.getsource`, so the set that is swept and the set that is
    derived cannot come from two different files.
    """
    enumerated = {
        relative: module.enumerate_files(repo_root)
        for relative, module in loaded_guard_tools.items()
    }
    derived = {
        relative: liveness.guard_function_names((repo_root / relative).read_text(encoding="utf-8"))
        for relative in loaded_guard_tools
    }
    _blind(monkeypatch)

    swept = {
        relative: [
            verdict.function
            for verdict in liveness.blind_verdicts(module, repo_root, *enumerated[relative][:2])
        ]
        for relative, module in loaded_guard_tools.items()
    }

    assert swept == derived, (
        f"the sweep visited {swept} and the tools define {derived}; a guard missing from "
        "the sweep is a guard the criterion never applied to"
    )


def test_no_guard_renders_the_name_a_blind_read_failed_on(
    loaded_guard_tools: dict[str, ModuleType], repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The privacy half, derived over the same population.

    A read failure carries the path it failed on, and on this project every
    path is discovered at runtime and routinely sits under a home directory
    (CLAUDE.md non-negotiable 12). Seven near-identical tests already pin this
    one guard at a time; this asks it of every DERIVED guard, so a guard added
    tomorrow is covered without anyone writing an eighth.
    """
    enumerated = {
        relative: module.enumerate_files(repo_root)
        for relative, module in loaded_guard_tools.items()
    }
    _blind(monkeypatch)

    leaking: list[str] = []
    for relative, module in loaded_guard_tools.items():
        files, source, _skips = enumerated[relative]
        leaking.extend(
            f"{relative}::{verdict.function}"
            for verdict in liveness.blind_verdicts(module, repo_root, files, source)
            if liveness.INJECTED_FILENAME in verdict.rendered
        )
    count = len(leaking)
    assert not count, f"{count} guard(s) rendered the name the read failed on: {sorted(leaking)}"


# ---------------------------------------------------------------------------
# The guard criterion's POWER, forced on a stand-in
# ---------------------------------------------------------------------------


def test_a_guard_replaced_by_an_early_return_is_reported(tmp_path: Path) -> None:
    """THE CRITERION'S POWER. The mutation, wearing the verdict it produces.

    An early return in a guard yields PASS with no skip recorded - which is
    what the stand-in written here answers - and the criterion has to call that
    silent. Without this, the clean result above is a claim about a criterion
    that might report nothing about anything.
    """
    tool = _stub_tool(tmp_path, "PASS", [])
    verdicts = liveness.blind_verdicts(tool, tmp_path, [], "stub enumeration")
    silent = [verdict.function for verdict in verdicts if liveness.silently_green(verdict)]
    assert silent == ["guard_planted"], f"the gutted guard was not reported: {verdicts}"


@pytest.mark.parametrize(
    ("status", "skips", "why"),
    [
        ("WARN", [], "a non-PASS verdict is a verdict"),
        ("FAIL", [], "a red is a verdict"),
        ("PASS", [{"path": "a", "reason": "unreadable"}], "green while self-excusing is allowed"),
    ],
)
def test_a_guard_that_says_something_about_a_blind_tree_is_not_reported(
    status: str, skips: list[dict[str, str]], why: str, tmp_path: Path
) -> None:
    """The boundary, on each half of the criterion separately.

    Asserting only the silent case would leave a criterion that reports
    everything indistinguishable from one that reports the right thing.
    """
    tool = _stub_tool(tmp_path, status, skips)
    verdicts = liveness.blind_verdicts(tool, tmp_path, [], "stub enumeration")
    silent = [verdict.function for verdict in verdicts if liveness.silently_green(verdict)]
    assert not silent, f"{why}, and it was reported anyway: {verdicts}"
