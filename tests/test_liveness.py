#!/usr/bin/env python3
"""CS-846 - every shipped control and every shipped guard is graded on whether it grades.

WHAT WAS MEASURED BEFORE ANY OF THIS EXISTED, on the tree this item was taken
from. A conditional early return planted at the head of
``tests/data/test_drift_guard_data.py::test_a_planted_duplicate_is_reported_as_drift``
- the control whose own docstring says it "has to prove the guard FIRES, not
that it RUNS" - left the drift-guard modules, the mypy gate and the pre-commit
gate all green. The same plant in ``assert_reported_without_the_filename``, the
grader that decides seven privacy controls, left its module green. The same
plant in ``tools/drift_guard.py`` left the whole consuming set green for two of
the nine guards it ships, while the runner went on reporting nine of nine.

THE FIRST VERSION OF THIS MODULE WAS REFUTED AND THE REFUTATION IS WHY THE
CHECK IS SHAPED THIS WAY. It keyed on ``ast.Return``, and 1855 of 1857 members
of this tree carry no return statement anywhere - so for almost the entire
population the analysis could not report anything and its green was a claim
about a shape they do not contain. Four more gutting shapes were demonstrated
silent against it, none of which uses a return. Every one of them now has a
named test below, and each was re-measured silent against the refuted version
first.

WHY THE POPULATION IS THE DELIVERABLE. This defect was filed twice on the same
day by two agents that did not know of each other, once against a CONTROL and
once against a GUARD. The check they each declined to write was the per-arm
one, and both were right: ``tests/save/reach_guard`` already ships a gutting
guard that modules opt into by calling it on their own ``__file__``, and its
own header records that of the five modules self-applying its sibling, two call
it - so it "is not a rule the package follows, it is a habit two modules have".
Everything here is derived from ``git ls-files`` plus an AST walk.

THE HARD RULES ARE THREE, and each was measured at ZERO on this tree before it
was kept. An exit reached without grading, whether through a ``return`` or by
falling off the end. An exiting call - ``pytest.skip`` and its siblings - at a
member's TOP LEVEL, reached without grading. A ``try`` that grades and carries
a handler which discards the failure. The guard half adds two more: a guard
must not answer PASS about a tree it could not read while recording nothing,
and a guard must not answer the IDENTICAL thing about three materially
different trees.

THE RESIDUALS ARE COUNTED AND RE-DERIVED, NEVER PROSE. Prose is the thing that
rots, so every exemption below is a set this module recomputes on every run,
reports by name, and holds to a shape assertion:

  - members whose end exit is graded only because a loop body carries the
    grading, and only because a ``try`` body does;
  - graders excluded from the population because they return a value;
  - tests that ship no grading statement at all;
  - tools the guard criterion cannot run.

WHAT IS STILL NOT COVERED, stated because a check read as covering everything
is the false-guarantee class this project has already paid for. An assertion
rewritten to a tautology leaves every exit graded and is invisible here - this
repository SHIPPED that exact shape and removed it during the session this item
was worked, so it is a hole in the middle rather than a boundary. A gutting
whose branch condition merely LOOKS like a real test is structurally identical
to a legitimate one and no static rule separates them. And nothing here proves
an assertion ran; it proves one COULD not be skipped by the shapes named above.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from tests import liveness
from tests.save.reach_guard import _assert_no_test_is_gutted

#: The entry point that decides which guards actually run. A guard the runner
#: never mentions is a guard that stopped grading one level up.
GUARD_RUNNER: Final = "run_all"

#: The pre-existing per-module gutting guard modules opt into by calling it on
#: their own source. Used to prove the derivation here is WIDER than that
#: habit, never to scope it.
OPT_IN_HELPER: Final = "_assert_no_test_is_gutted"

#: This module and its helper. Named so the check can prove it covers its own
#: two files rather than being the one thing outside the population it derives.
OWN_MODULES: Final = ("tests/liveness.py", "tests/test_liveness.py")


# ---------------------------------------------------------------------------
# Synthetic corpora - authored here, naming no real module.
#
# They are STRINGS rather than real functions on purpose. mypy runs with
# warn_unreachable over tests/, so a real function carrying a bare early return
# would be a mypy finding about this file instead of a fixture for the analysis
# under test - and none of the other shapes could sit beside it as real code
# either, because this module's own check would report them.
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

#: THE SHAPE THAT REFUTED THE FIRST VERSION. No return anywhere; the body is
#: wrapped so it never runs. An analysis keyed on the return statement is
#: structurally blind to it.
_WRAPPED_BODY = '''\
def test_gamma(corpus: list[int]) -> None:
    """Gutted by wrapping, with no return in sight."""
    if not globals():
        total = sum(corpus)
        assert total == 1
'''

#: The assertions still run and their failure is thrown away.
_SWALLOWED = '''\
def test_delta(corpus: list[int]) -> None:
    """Gutted by swallowing."""
    try:
        assert sum(corpus) == 1
    except AssertionError:
        pass
'''

#: The test leaves through pytest's own vocabulary before grading anything.
_SKIPPED_AT_HEAD = '''\
def test_epsilon(corpus: list[int]) -> None:
    """Gutted by skipping."""
    pytest.skip("not today")
    assert sum(corpus) == 1
'''

#: The same wrapping shape in the other structure - a delegated grader.
_GUTTED_GRADER = '''\
def _assert_every_row_balances(rows: list[int]) -> None:
    """Gutted grader, no return anywhere."""
    if not globals():
        assert not [row for row in rows if row < 0]
'''

#: Correct: the early return is a fast path AFTER the grading has happened.
_GRADED_THEN_RETURN = '''\
def test_zeta(corpus: list[int]) -> None:
    """Graded, then short-circuited."""
    assert corpus
    if len(corpus) == 1:
        return
    assert sum(corpus) > 1
'''

#: Correct: both arms grade before the exit, so no path escapes.
_BOTH_ARMS_GRADE = '''\
def test_eta(flag: bool) -> None:
    """Graded on both arms."""
    if flag:
        assert flag is True
    else:
        assert flag is False
'''

#: Correct, and the shape 38 real tests use: the skip is CONDITIONAL.
_CONDITIONAL_SKIP = '''\
def test_theta(corpus: list[int]) -> None:
    """Skipped only when there is nothing to grade."""
    if not corpus:
        pytest.skip("no corpus on this machine")
    assert sum(corpus) > 0
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

#: The loop residual, WITHOUT a trailing return.
#:
#: THE FIRST VERSION OF THIS FIXTURE CARRIED ONE, and that is the whole reason
#: the return-only analysis looked green through its own defect: the trailing
#: return was the only thing the analysis could see, and real test functions do
#: not have it. It is a loop whose iterable may be empty, so nothing is
#: guaranteed to grade - and it is NOT reported, because reporting it reports 95
#: correct members of this tree. It is counted instead.
_LOOP_ONLY_ASSERT = '''\
def test_iota(corpus: list[int]) -> None:
    """The only assertion is inside a loop that may not run."""
    for item in corpus:
        assert item > 0
'''

#: The idiom the strict rule would punish hardest: grading inside a branch
#: inside a loop. Five real members of this tree have exactly this shape.
_LOOP_THEN_BRANCH = '''\
def test_kappa(tree: list[object]) -> None:
    """Graded inside a branch inside a loop."""
    for node in tree:
        if isinstance(node, str):
            assert node
'''

#: Grading is unreachable: an exit precedes it at the same level.
_DEAD_GRADING = '''\
def _assert_rows(rows: list[int]) -> None:
    """The grading can never run."""
    if not rows:
        raise ValueError("empty")
    raise RuntimeError("always")
    assert rows
'''

#: A stand-in guard tool. ``{VERDICT}`` and ``{SKIPS}`` are substituted with
#: literals, so the guard under the sweep is real code in a real file that
#: :func:`inspect.getsource` can read - not an object impersonating one. The
#: varying form appends the root it was given, which is what an honest guard
#: does and a constant return cannot.
_STUB_CONSTANT = "\n".join(
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

_STUB_VARYING = "\n".join(
    [
        '"""A stand-in guard tool whose answer depends on the tree it is given."""',
        "",
        "",
        "def guard_planted(root):",
        '    """Answer something about this particular root."""',
        "    verdict = {VERDICT}",
        '    verdict["detail"] = [*verdict["detail"], str(root)]',
        "    return verdict, {SKIPS}",
        "",
    ]
)


def _survey(text: str) -> liveness.Survey:
    """Survey one synthetic corpus.

    Args:
        text: Synthetic source.

    Returns:
        The survey.
    """
    return liveness.survey_source("synthetic.py", text)


def _findings(text: str) -> list[str]:
    """Render the hard findings a synthetic corpus carries.

    Args:
        text: Synthetic source.

    Returns:
        ``module:line name (kind)`` for each finding.
    """
    return [finding.rendered() for finding in _survey(text).findings]


def _kinds(text: str) -> list[str]:
    """The kinds of exit a synthetic corpus is reported for.

    Args:
        text: Synthetic source.

    Returns:
        One kind per finding.
    """
    return [finding.kind for finding in _survey(text).findings]


def _stub_tool(
    tmp_path: Path, status: str, skips: list[dict[str, str]], *, varying: bool = False
) -> ModuleType:
    """Write and load a one-guard stand-in answering as instructed.

    Args:
        tmp_path: Where the stand-in is written.
        status: The status its guard answers.
        skips: The skip records its guard answers with.
        varying: Whether its answer should depend on the root it is given.

    Returns:
        The loaded stand-in.
    """
    verdict = {"id": "z", "name": "planted", "status": status, "detail": ["said something"]}
    template = _STUB_VARYING if varying else _STUB_CONSTANT
    source = template.replace("{VERDICT}", repr(verdict)).replace("{SKIPS}", repr(skips))
    name = f"stub_guard_tool_{'varying' if varying else 'constant'}_{status}_{len(skips)}"
    path = tmp_path / f"{name}.py"
    path.write_text(source, encoding="utf-8", newline="\n")
    spec = importlib.util.spec_from_file_location(f"cs846_{name}", path)
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


# ---------------------------------------------------------------------------
# The derivation
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


def test_the_derivation_covers_its_own_two_modules(surveyed: liveness.Survey) -> None:
    """The checker must be inside the population it derives.

    The first version of this module derived a population its own helper was
    not in, which meant the one file able to stop the check from reporting was
    the one file the check never read.
    """
    read = set(surveyed.modules)
    missing = sorted(set(OWN_MODULES) - read)
    assert not missing, (
        f"{missing} were not read by the derivation, so this check does not grade the "
        "files it is implemented in"
    )


def test_the_derivation_reaches_further_than_the_opt_in_guard_beside_it(
    repo_root: Path, tracked: list[str], surveyed: liveness.Survey
) -> None:
    """Measured against the habit, not asserted about it.

    A derived population that happened to cover exactly the modules already
    opting in would be a rename rather than a widening. So the opt-in set is
    DERIVED TOO - by reading which modules CALL the pre-existing helper, which
    is why a module merely naming it in a constant does not count.
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


# ---------------------------------------------------------------------------
# The rules, over the real tree
# ---------------------------------------------------------------------------


def test_no_shipped_control_or_grader_can_exit_without_grading(
    surveyed: liveness.Survey,
) -> None:
    """THE RULE. Every member grades before every way out of it.

    A finding here is a function that can leave having asserted nothing. It
    reports as passed, and the diff still shows the assertions in the file.
    """
    population = len(surveyed.members)
    rendered = [finding.rendered() for finding in surveyed.findings]
    count = len(rendered)
    assert population > 1, (
        f"the derived population holds {population} member(s), so a clean result below "
        "is a claim about nothing"
    )
    assert not count, (
        f"{count} shipped control(s) or grader(s) can stop grading without anything "
        f"noticing: {rendered[:20]}"
    )


def test_no_grading_statement_in_the_repository_is_unreachable(
    surveyed: liveness.Survey,
) -> None:
    """A SECOND consumer of a tree-wide census, so one gutting is not enough.

    This grades the whole grading population - the members AND the graders that
    return a value, which the population filter excludes. Its census is
    different from the one above, so gutting either test leaves the other
    reporting the finding the gutting creates in this file.
    """
    rendered = [finding.rendered() for finding in surveyed.dead_grading]
    count = len(rendered)
    graded = len(surveyed.members) + len(surveyed.value_returning)
    assert graded > 1, f"{graded} function(s) ship a grading statement, so this is vacuous"
    assert not count, (
        f"{count} grading statement(s) can never run, so they grade nothing while still "
        f"reading as assertions: {rendered[:20]}"
    )


def test_this_check_grades_its_own_two_modules(repo_root: Path) -> None:
    """THE THIRD CONSUMER, and it re-derives rather than reusing the fixture.

    The refutation that killed the first version noted that one test was the
    sole consumer of the tree-wide finding set, so gutting that one test
    silenced everything. This surveys only the two files this check is written
    in, from its own call to :func:`liveness.survey`, so gutting either of the
    two tests above creates a finding in this file that THIS test reports.
    """
    own = liveness.survey(repo_root, list(OWN_MODULES))
    rendered = [finding.rendered() for finding in [*own.findings, *own.dead_grading]]
    count = len(rendered)
    population = len(own.members)
    assert population > 1, (
        f"this check's own two modules contribute {population} member(s), so it does not "
        "grade itself"
    )
    assert not count, f"{count} finding(s) in this check's own source: {rendered[:20]}"


def test_no_test_in_this_module_is_gutted_to_an_early_return() -> None:
    """A FOURTH consumer, owned by another package and implemented differently.

    CS-433's guard is a second, independent implementation of a narrower
    property, and this module opts into it deliberately: agreement between two
    derivations of the same thing is not evidence, but a finding from either is.
    The coupling is stated - if ``tests/save/reach_guard`` moves, this import
    fails loudly rather than silently covering nothing.
    """
    _assert_no_test_is_gutted(Path(__file__))


# ---------------------------------------------------------------------------
# The analysis' POWER. Every one of these was measured SILENT against the
# version of this module that keyed on the return statement.
# ---------------------------------------------------------------------------


def test_a_bare_early_return_is_reported() -> None:
    """The cheapest gutting."""
    assert _kinds(_BARE_RETURN) == ["return"], f"got {_findings(_BARE_RETURN)}"


def test_the_conditional_early_return_the_item_was_filed_on_is_reported() -> None:
    """The shape no unreachable-code check can see.

    Everything after the cut is still reachable, so mypy's warn_unreachable and
    the per-module gutting guard both stay silent.
    """
    assert _kinds(_CONDITIONAL_RETURN) == ["return"], f"got {_findings(_CONDITIONAL_RETURN)}"


def test_a_body_wrapped_so_it_never_runs_is_reported_with_no_return_in_it() -> None:
    """THE SHAPE THAT REFUTED THE FIRST VERSION OF THIS MODULE.

    There is no return anywhere, and 1855 of 1857 members of this tree carry no
    return either - so an analysis keyed on the return statement was
    structurally incapable of reporting this or of reporting anything about
    almost the whole population. The exit graded here is the IMPLICIT one at the
    end of the function.
    """
    assert _kinds(_WRAPPED_BODY) == ["end of function"], f"got {_findings(_WRAPPED_BODY)}"


def test_a_try_that_discards_the_failure_it_grades_is_reported() -> None:
    """The assertions run and their verdict is thrown away."""
    assert _kinds(_SWALLOWED) == ["swallowed"], f"got {_findings(_SWALLOWED)}"


def test_an_unconditional_skip_at_the_head_is_reported() -> None:
    """Gutting written in pytest's own vocabulary.

    Scoped to the member's TOP LEVEL because a CONDITIONAL skip is the
    legitimate idiom, and this tree carries 38 of those and no unconditional
    one. :func:`test_a_conditional_skip_is_not_reported` holds that boundary.
    """
    assert _kinds(_SKIPPED_AT_HEAD) == ["exiting call"], f"got {_findings(_SKIPPED_AT_HEAD)}"


def test_a_grader_that_is_not_a_test_is_reported_the_same_way() -> None:
    """The second structure, on the same terms as the first.

    This item was widened because the identical shape was measured in a GUARD
    rather than a control. A derivation keyed on the word "test" would cover one
    report and not the other.
    """
    assert _kinds(_GUTTED_GRADER) == ["end of function"], f"got {_findings(_GUTTED_GRADER)}"
    assert [member.name for member in _survey(_GUTTED_GRADER).members] == [
        "_assert_every_row_balances"
    ], "the grader did not enter the population, so the finding above is incidental"


def test_grading_that_can_never_run_is_reported() -> None:
    """An assertion below an unconditional exit reads as coverage and is not."""
    dead = [finding.kind for finding in _survey(_DEAD_GRADING).dead_grading]
    assert dead == ["unreachable grading"], f"got {_survey(_DEAD_GRADING).dead_grading}"


# ---------------------------------------------------------------------------
# The BOUNDARIES. A rule that reports everything is indistinguishable from one
# that reports the right thing.
# ---------------------------------------------------------------------------


def test_an_early_return_after_the_grading_is_not_reported() -> None:
    """A fast path below the assertion is correct code."""
    assert not _findings(_GRADED_THEN_RETURN)


def test_an_exit_both_arms_of_an_if_have_graded_before_is_not_reported() -> None:
    """The boundary that needs the branch merge to be right."""
    assert not _findings(_BOTH_ARMS_GRADE)


def test_a_conditional_skip_is_not_reported() -> None:
    """38 real members of this tree skip conditionally and every one is correct."""
    assert not _findings(_CONDITIONAL_SKIP)


def test_a_value_returning_helper_that_asserts_is_not_in_the_population() -> None:
    """The filter that keeps utilities out - and counts them rather than dropping them.

    Measured before it existed: every finding the analysis raised was a helper
    computing a value with a sanity assert in it, and not one was a grader.
    """
    survey = _survey(_VALUE_RETURNING_HELPER)
    assert not survey.members, "a value-returning utility entered the grader population"
    assert not survey.findings, "a value-returning utility's boundary return was reported"
    assert [member.name for member in survey.value_returning] == ["_power"], (
        "the excluded utility was dropped instead of counted"
    )


def test_a_loop_that_may_not_run_is_counted_rather_than_reported() -> None:
    """THE FIXTURE THAT HID THE DEFECT, RE-AUTHORED WITHOUT ITS TRAILING RETURN.

    The first version of this fixture ended with a gratuitous ``return`` that no
    real test function has. That return was the only thing the return-only
    analysis could see, so the test was green through the very defect that
    refuted the module. Without it the shape is what real code looks like, and
    the answer changes: it is NOT a finding, because reporting it reports 95
    correct members of this tree - it is COUNTED instead, and both halves are
    asserted here.
    """
    survey = _survey(_LOOP_ONLY_ASSERT)
    assert not survey.findings, f"a legitimate loop-only grading was reported: {survey.findings}"
    assert [member.name for member in survey.loop_leaned] == ["test_iota"], (
        "the loop generosity was applied without being counted, which makes it a silence "
        "rather than an exemption"
    )


def test_grading_inside_a_branch_inside_a_loop_is_counted_rather_than_reported() -> None:
    """The idiom the strict rule punishes hardest. Five real members have it."""
    survey = _survey(_LOOP_THEN_BRANCH)
    assert not survey.findings, f"the commonest correct idiom was reported: {survey.findings}"
    assert [member.name for member in survey.loop_leaned] == ["test_kappa"]


# ---------------------------------------------------------------------------
# The residuals - counted and re-derived on every run, never prose
# ---------------------------------------------------------------------------


def test_every_test_outside_the_population_at_least_exercises_something(
    surveyed: liveness.Survey,
) -> None:
    """A test that ships no assertion grades by the code under test not raising.

    The assertion-derived population cannot see one, and that is stated rather
    than hidden. What it IS held to is that it calls something: a test that
    neither grades nor acts is the endpoint of this defect, not an exemption.
    """
    exercising, inert = surveyed.outside
    rendered = [member.rendered() for member in inert]
    count = len(rendered)
    residual = len(exercising)
    assert residual or count, "the residual census found no test outside the population at all"
    assert not count, (
        f"{count} test(s) ship neither a grading statement nor a call, so they grade "
        f"nothing at all: {rendered[:20]}"
    )


def test_every_member_credited_to_the_loop_generosity_really_carries_a_loop(
    repo_root: Path, surveyed: liveness.Survey
) -> None:
    """The loop residual, re-derived and held to its own shape.

    A census nobody checks is prose with a number on it. Every member credited
    to this generosity is re-read here and must actually carry a loop whose body
    grades - so a member cannot land in the exemption by accident, and the count
    is a measurement rather than an assertion about itself.
    """
    credited = surveyed.loop_leaned
    count = len(credited)
    wrong: list[str] = []
    for member in credited:
        tree = ast.parse((repo_root / member.module).read_text(encoding="utf-8"))
        node = next(item for item in liveness.functions(tree) if item.name == member.name)
        loops = [
            statement
            for statement in liveness.own_statements(node)
            if isinstance(statement, ast.For | ast.AsyncFor | ast.While)
            and liveness.carries_grading(statement.body)
        ]
        if not loops:
            wrong.append(member.rendered())
    assert count, (
        "no member was credited to the loop generosity, so either the tree changed "
        "shape or the generosity is no longer being applied and should be removed"
    )
    assert not wrong, f"{len(wrong)} member(s) credited to a loop that does not grade: {wrong}"


def test_every_member_credited_to_the_try_generosity_really_carries_a_try(
    repo_root: Path, surveyed: liveness.Survey
) -> None:
    """The try residual, re-derived and held to its own shape."""
    credited = surveyed.try_leaned
    count = len(credited)
    wrong: list[str] = []
    for member in credited:
        tree = ast.parse((repo_root / member.module).read_text(encoding="utf-8"))
        node = next(item for item in liveness.functions(tree) if item.name == member.name)
        tries = [
            statement
            for statement in liveness.own_statements(node)
            if isinstance(statement, ast.Try) and liveness.carries_grading(statement.body)
        ]
        if not tries:
            wrong.append(member.rendered())
    assert count, (
        "no member was credited to the try generosity, so either the tree changed shape "
        "or the generosity is no longer being applied and should be removed"
    )
    assert not wrong, f"{len(wrong)} member(s) credited to a try that does not grade: {wrong}"


def test_every_grader_the_population_filter_excludes_is_counted_and_returns_a_value(
    repo_root: Path, surveyed: liveness.Survey
) -> None:
    """THE 78, RE-DERIVED. The filter excludes them; this proves it excluded the right ones.

    The refutation measured that the filter drops 78 functions with no census
    and demonstrated a silent kill inside one of them. They are counted here and
    each is re-read to confirm it really does return a value - so the exclusion
    is a measured set, not a filter nobody looks at. The residual that REMAINS
    is stated plainly: an ungraded early return in a value-returning grader is
    structurally identical to a legitimate boundary return, so it is not
    decidable from the return alone and is not claimed to be. What IS graded
    about them is that none of their grading is unreachable, which
    :func:`test_no_grading_statement_in_the_repository_is_unreachable` asserts
    over this same set.
    """
    excluded = surveyed.value_returning
    count = len(excluded)
    wrong: list[str] = []
    for member in excluded:
        tree = ast.parse((repo_root / member.module).read_text(encoding="utf-8"))
        node = next(item for item in liveness.functions(tree) if item.name == member.name)
        if not liveness.returns_a_value(node) or not liveness.ships_a_grading_statement(node):
            wrong.append(member.rendered())
    assert count, (
        "the population filter excluded nothing, so it is either inert or the census "
        "stopped being computed"
    )
    assert not wrong, f"{len(wrong)} excluded function(s) do not have the excluded shape: {wrong}"


# ---------------------------------------------------------------------------
# The tools and the gates
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


def test_every_tracked_tool_is_either_run_by_the_guard_criterion_or_counted(
    tracked: list[str], guard_tools: list[str]
) -> None:
    """THE GUARD HALF REACHES ONE FILE, AND THAT IS SAID OUT LOUD HERE.

    The guard criterion needs a callable with a known contract - a ``guard_``
    function it can hand a root to - and only one tracked tool has one. The
    other tools are gates in every ordinary sense, including a frozen tier-0
    blocking one, and the criterion cannot reach any of them. They are counted
    and NAMED rather than left out of the arithmetic, and
    :func:`test_every_tool_a_blocking_hook_invokes_can_report_a_failure` is the
    one liveness question that can be asked of them.
    """
    tools = liveness.tool_modules(tracked)
    uncovered = sorted(set(tools) - set(guard_tools))
    assert tools, "no tracked module lives in a tool directory, so this is green about nothing"
    assert guard_tools, "no tracked tool ships a guard, so the guard half grades nothing"
    assert set(guard_tools) <= set(tools), (
        f"{sorted(set(guard_tools) - set(tools))} were derived as guard tools from outside "
        "the tool directories, so the two derivations disagree"
    )
    assert uncovered, (
        "every tracked tool is now reachable by the guard criterion, which would be an "
        "improvement - delete this exemption rather than leaving it asserting nothing"
    )


def test_every_tool_a_blocking_hook_invokes_can_report_a_failure(repo_root: Path) -> None:
    """A gate that cannot reach a non-zero outcome cannot block anything.

    This is the only liveness question available about a tool that ships no
    guard and no assertion, and it is a real one: it covers
    ``tools/precommit_gate.py``, the frozen tier-0 blocking gate, by READING it.
    The blocking set is derived from the hook scripts themselves rather than
    listed, so a tool promoted into a hook joins by being invoked.
    """
    invoked = liveness.hook_invoked_tools(repo_root)
    mute: list[str] = []
    for relative in invoked:
        text = (repo_root / relative).read_text(encoding="utf-8")
        node = liveness.module_function(text, "main")
        if node is None or not liveness.failure_exits(node):
            mute.append(relative)
    count = len(invoked)
    assert count > 1, (
        f"{count} tool(s) were derived as invoked by a blocking hook, so this is green "
        "about nothing"
    )
    assert not mute, (
        f"{len(mute)} tool(s) stand in a blocking position and their main can never "
        f"report a failure: {mute}"
    )


# ---------------------------------------------------------------------------
# The guard half
# ---------------------------------------------------------------------------


def test_every_derived_guard_is_reached_by_its_runner(
    repo_root: Path, guard_tools: list[str]
) -> None:
    """A guard the runner never names is a guard that never runs.

    The runner lists the guards it drives, so a new one only ever runs when
    someone remembers to add it there. That is the same silence one level up.
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
        runner = liveness.module_function(text, GUARD_RUNNER)
        assert runner is not None, f"{relative} lost its {GUARD_RUNNER} between two reads"
        reached = {node.id for node in ast.walk(runner) if isinstance(node, ast.Name)}
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
    """Green with nothing recorded is not a verdict.

    CONVENTIONS.md section 15.1, which the tool prints on every run: a guard may
    be green while self-excusing, and a green verdict means nothing without the
    list of what was never looked at.
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
        for answer in liveness.guard_answers(module, repo_root, files, source):
            graded += 1
            if liveness.silently_green(answer):
                silent.append(f"{relative}::{answer.function} [{answer.guard_id}]")

    count = len(silent)
    assert graded > 1, f"the blind sweep reached {graded} guard(s), so it grades nothing"
    assert not count, (
        f"{count} guard(s) answered PASS about a tree they could not read while recording "
        f"nothing they had skipped: {sorted(silent)}"
    )


def test_no_shipped_guard_answers_the_same_about_three_different_trees(
    loaded_guard_tools: dict[str, ModuleType],
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE CRITERION THAT SURVIVES A FABRICATED SKIP RECORD.

    The silence criterion above asks "did it say anything", and the adversary
    that refuted the first version of this module defeated it for the length of
    one dict literal: an early return carrying a made-up skip record satisfies
    it while grading nothing, leaving the net position on the only two guards
    ever uncovered UNCHANGED.

    This asks a different question that a fabrication cannot answer - does the
    guard's answer DEPEND on the tree? It is run against the real repository, an
    empty directory and a tree whose every read fails. A guard replaced by a
    constant return says the identical thing about all three whatever that
    constant is, and every guard shipped today says at least two different
    things.
    """
    real = {
        relative: module.enumerate_files(repo_root)
        for relative, module in loaded_guard_tools.items()
    }
    void = {
        relative: module.enumerate_files(tmp_path)
        for relative, module in loaded_guard_tools.items()
    }

    collected: dict[str, list[list[liveness.GuardAnswer]]] = {}
    for relative, module in loaded_guard_tools.items():
        collected[relative] = [
            liveness.guard_answers(module, repo_root, *real[relative][:2]),
            liveness.guard_answers(module, tmp_path, *void[relative][:2]),
        ]

    _blind(monkeypatch)
    for relative, module in loaded_guard_tools.items():
        collected[relative].append(liveness.guard_answers(module, repo_root, *real[relative][:2]))

    constant: list[str] = []
    compared = 0
    for relative, rounds in collected.items():
        for index, first in enumerate(rounds[0]):
            answers = [round_[index] for round_ in rounds]
            compared += 1
            if liveness.answers_the_same_about_every_tree(answers):
                constant.append(f"{relative}::{first.function} [{first.guard_id}]")
    count = len(constant)
    assert compared > 1, f"{compared} guard(s) were compared across trees, so this is vacuous"
    assert not count, (
        f"{count} guard(s) said the identical thing about the real tree, an empty tree and "
        f"an unreadable tree, so their answer does not depend on what they were given: "
        f"{sorted(constant)}"
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
            answer.function
            for answer in liveness.guard_answers(module, repo_root, *enumerated[relative][:2])
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

    A read failure carries the path it failed on, and on this project every path
    is discovered at runtime and routinely sits under a home directory
    (CLAUDE.md non-negotiable 12). Seven near-identical tests already pin this
    one guard at a time; this asks it of every DERIVED guard.
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
            f"{relative}::{answer.function}"
            for answer in liveness.guard_answers(module, repo_root, files, source)
            if liveness.INJECTED_FILENAME in answer.rendered
        )
    count = len(leaking)
    assert not count, f"{count} guard(s) rendered the name the read failed on: {sorted(leaking)}"


# ---------------------------------------------------------------------------
# The guard criteria's POWER, forced on stand-ins
# ---------------------------------------------------------------------------


def test_a_guard_replaced_by_an_early_return_is_reported_silent(tmp_path: Path) -> None:
    """An early return yields PASS with no skip recorded, and that is not a verdict."""
    tool = _stub_tool(tmp_path, "PASS", [])
    answers = liveness.guard_answers(tool, tmp_path, [], "stub enumeration")
    silent = [answer.function for answer in answers if liveness.silently_green(answer)]
    assert silent == ["guard_planted"], f"the gutted guard was not reported: {answers}"


def test_a_guard_that_fabricates_a_skip_record_is_still_reported(tmp_path: Path) -> None:
    """THE DEFEAT OF THE FIRST CRITERION, CLOSED BY THE SECOND.

    Appending a made-up skip dict to a planted return satisfies the silence
    criterion completely - and this asserts that it does, rather than pretending
    otherwise - while the dependence criterion still reports it, because a
    fabricated record is a CONSTANT and a guard's answer has to depend on the
    tree it was given.
    """
    tool = _stub_tool(tmp_path, "PASS", [{"path": "docs", "reason": "not reached"}])
    answers = [
        liveness.guard_answers(tool, tmp_path, [], "stub enumeration"),
        liveness.guard_answers(tool, tmp_path / "elsewhere", [], "stub enumeration"),
    ]
    silent = [answer.function for answer in answers[0] if liveness.silently_green(answer)]
    constant = [
        first.function
        for index, first in enumerate(answers[0])
        if liveness.answers_the_same_about_every_tree([round_[index] for round_ in answers])
    ]
    assert not silent, "the fabricated skip did NOT defeat the silence criterion after all"
    assert constant == ["guard_planted"], f"the fabricating guard was not reported: {answers}"


def test_a_guard_whose_answer_depends_on_the_tree_is_not_reported(tmp_path: Path) -> None:
    """The boundary. An honest guard varies with what it is handed."""
    tool = _stub_tool(tmp_path, "PASS", [{"path": "a", "reason": "unreadable"}], varying=True)
    answers = [
        liveness.guard_answers(tool, tmp_path, [], "stub enumeration"),
        liveness.guard_answers(tool, tmp_path / "elsewhere", [], "stub enumeration"),
    ]
    constant = [
        first.function
        for index, first in enumerate(answers[0])
        if liveness.answers_the_same_about_every_tree([round_[index] for round_ in answers])
    ]
    assert not constant, f"a guard that varied with the tree was reported constant: {answers}"


@pytest.mark.parametrize(
    ("status", "skips", "why"),
    [
        ("WARN", [], "a non-PASS verdict is a verdict"),
        ("FAIL", [], "a red is a verdict"),
        ("PASS", [{"path": "a", "reason": "unreadable"}], "green while self-excusing is allowed"),
    ],
)
def test_a_guard_that_says_something_about_a_blind_tree_is_not_reported_silent(
    status: str, skips: list[dict[str, str]], why: str, tmp_path: Path
) -> None:
    """The silence criterion's boundary, on each of its halves separately."""
    tool = _stub_tool(tmp_path, status, skips)
    answers = liveness.guard_answers(tool, tmp_path, [], "stub enumeration")
    silent = [answer.function for answer in answers if liveness.silently_green(answer)]
    assert not silent, f"{why}, and it was reported anyway: {answers}"
