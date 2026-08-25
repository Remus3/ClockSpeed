#!/usr/bin/env python3
"""CS-846 - the gutting shapes this check covers, named one by one.

WHAT THIS MODULE CLAIMS, AND THE CLAIM IS DELIBERATELY NARROWER THAN THE ITEM'S
WORDING. It does NOT claim that every shipped control is covered. It claims
that the shapes ENUMERATED BELOW are covered, that each was measured silent
before it was closed, and that the shapes it does NOT cover are named beside
them. Two adversaries refuted earlier versions of this module for claiming more
than they checked, and both times the gap was a shape nobody had listed.

COVERED, each with a test below and each measured silent first:

  - a bare ``return`` before the assertions;
  - a conditional ``return`` before them, which no unreachable-code check sees;
  - the body WRAPPED so it never runs, with no return anywhere;
  - the assertions SWALLOWED by a ``try`` whose handler discards the failure;
  - an unconditional ``pytest.skip`` at the head;
  - a skip written to look conditional - ``if globals(): pytest.skip(...)``;
  - the same thing spelled ``raise pytest.skip.Exception(...)``;
  - ``@pytest.mark.skip`` as a DECORATOR, which is not a statement at all;
  - ``assert True`` appended to any of the above to satisfy a naive check;
  - a value-returning grader made to hand back a FABRICATED literal;
  - grading placed where it can never run.

NOT COVERED, and this half is the one that matters:

  - AN ASSERTION REWRITTEN TO A NON-CONSTANT TAUTOLOGY. ``assert True`` is
    caught because it is decidable; ``assert x == x`` and the shape this
    repository actually shipped, ``empty + (records - empty) == records``, are
    not. That one was removed from the tree during the session this item was
    worked. It is a hole in the middle, not a boundary.
  - A GUTTING BRANCH WHOSE CONDITION IS GENUINELY UNKNOWN AT PARSE TIME.
    ``if globals():`` is folded; ``if _looks_fine():`` is not, and it is
    structurally identical to a real precondition.
  - A GRADER NAMED OUTSIDE THE VOCABULARY. The population is derived from
    calls beginning with ``assert`` plus pytest's own spellings. Renaming a
    grader takes its callers out of the population - which is why
    :func:`liveness.vocabulary_boundary` re-derives that difference every run
    and a ``test_`` function inside it is a hard finding here.
  - A VALUE-RETURNING GRADER GUTTED TO RETURN ``None`` EARLY. Returning a
    literal is fabricating an answer and is caught; returning ``None`` is
    declining to give one, which this tree does legitimately.
  - ANYTHING AT ALL ABOUT WHETHER AN ASSERTION RAN. Every rule here is static.

WHY THE RULES ARE STATED AS SEMANTICS. The second refutation found that the
rules had been picked by their false-positive count on this tree - the
``match`` arm returned the incoming verdict, which is wrong for every ``match``
ever written and scored zero only because this tree contains none. Every rule
is now a claim about MEANING, with its cost measured and reported afterwards
rather than used to choose it. Where a cost was paid, it is named: widening the
grading vocabulary was tried, measured, and reverted on the ground that in this
tree ``check`` and ``require`` name parsers rather than graders.

THE GUARD HALF applies three criteria, and the first two are PROXIES that were
each defeated. Not-silently-green was defeated by fabricating a skip record.
Answering-differently-about-different-trees was defeated by echoing the root
into the detail while reading nothing. Only the third is a property of guarding
itself: handed a tree built to break the rules, a guard must report. All three
ship, because a cheap criterion that catches a lazy gutting is worth having
beside an expensive one that catches a careful one.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
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

#: This module and its helper.
OWN_MODULES: Final = ("tests/liveness.py", "tests/test_liveness.py")


# ---------------------------------------------------------------------------
# Synthetic corpora - authored here, naming no real module.
#
# They are STRINGS rather than real functions on purpose. mypy runs with
# warn_unreachable over tests/, and this module's own check would report every
# one of them if they were real code.
# ---------------------------------------------------------------------------

_BARE_RETURN = '''\
def test_alpha() -> None:
    """Gutted."""
    return
    assert compute() == 1
'''

_CONDITIONAL_RETURN = '''\
def test_beta(corpus: list[int]) -> None:
    """Gutted, and everything after it still reachable."""
    if corpus:
        return
    assert sum(corpus) == 1
'''

#: The shape that refuted the first version: no return anywhere.
_WRAPPED_BODY = '''\
def test_gamma(corpus: list[int]) -> None:
    """Gutted by wrapping."""
    if not globals():
        total = sum(corpus)
        assert total == 1
'''

#: The shape that refuted the second version: the wrap plus eleven characters.
_WRAPPED_BODY_WITH_A_TAUTOLOGY = '''\
def test_gamma(corpus: list[int]) -> None:
    """Gutted by wrapping, with a constant assertion to look busy."""
    if not globals():
        total = sum(corpus)
        assert total == 1
    assert True
'''

_SWALLOWED = '''\
def test_delta(corpus: list[int]) -> None:
    """Gutted by swallowing."""
    try:
        assert sum(corpus) == 1
    except AssertionError:
        pass
'''

_SKIPPED_AT_HEAD = '''\
def test_epsilon(corpus: list[int]) -> None:
    """Gutted by skipping."""
    pytest.skip("not today")
    assert sum(corpus) == 1
'''

#: A skip wearing a conditional's clothes. The condition is decidable.
_SKIP_BEHIND_A_CONSTANT = '''\
def test_zeta(corpus: list[int]) -> None:
    """Gutted by a skip that looks conditional and is not."""
    if globals():
        pytest.skip("temporarily disabled")
    assert sum(corpus) == 1
'''

#: The same defeat spelled as a raise instead of a call.
_SKIP_RAISED_BEHIND_A_CONSTANT = '''\
def test_eta(corpus: list[int]) -> None:
    """Gutted by raising the skip exception instead of calling skip."""
    if globals():
        raise pytest.skip.Exception("temporarily disabled")
    assert sum(corpus) == 1
'''

#: One line, no statement, and the way anybody actually disables a test.
_DISABLED_BY_DECORATOR = '''\
@pytest.mark.skip(reason="temporarily disabled")
def test_theta(corpus: list[int]) -> None:
    """Switched off from outside the body."""
    assert sum(corpus) == 1
'''

_GUTTED_GRADER = '''\
def _assert_every_row_balances(rows: list[int]) -> None:
    """Gutted grader, no return anywhere."""
    if not globals():
        assert not [row for row in rows if row < 0]
'''

_FABRICATED_RETURN = '''\
def _reported_file_count(text: str) -> int:
    """Gutted to hand its caller a number nothing measured."""
    if globals():
        return 1
    match = FOUND.search(text)
    assert match is not None
    return int(match.group(1))
'''

_DECLINING_RETURN = '''\
def _census(paths: list[str]) -> int | None:
    """Declines to answer when there is nothing to measure."""
    if not paths:
        return None
    assert paths
    return len(paths)
'''

_DEAD_GRADING = '''\
def _assert_rows(rows: list[int]) -> None:
    """The grading can never run."""
    raise RuntimeError("always")
    assert rows
'''

# --- correct code, every one of which an earlier version reddened ----------

#: Semantically identical to ``assert not bad``. This module uses that spelling
#: more than twenty times; rejecting the other one grades style.
_GUARDED_FAILURE = '''\
def test_iota(rows: list[int]) -> None:
    """A guarded failure is an assertion."""
    bad = [row for row in rows if row < 0]
    if bad:
        pytest.fail(f"negative rows: {bad}")
'''

#: A handler that CONVERTS the failure rather than discarding it.
_CONVERTED_FAILURE = '''\
def test_kappa(path: str) -> None:
    """The assertion is that the call does not raise."""
    try:
        parse(path)
    except ValueError as exc:
        pytest.fail(f"parse refused a good input: {exc}")
'''

#: Graded in every arm, with an irrefutable one. THE ARM THAT WAS WRONG FOR
#: EVERY MATCH EVER WRITTEN and scored zero because this tree has none.
_MATCH_GRADED_IN_EVERY_ARM = '''\
def test_lambda(kind: str) -> None:
    """Graded on every arm of a match."""
    match kind:
        case "a":
            assert kind == "a"
        case "b":
            assert kind == "b"
        case _:
            pytest.fail(f"unknown kind {kind}")
'''

#: A failure guarded inside a context manager.
_FAILURE_INSIDE_A_WITH = '''\
def test_mu(path: str) -> None:
    """A guarded failure one level down."""
    with open(path) as handle:
        if not handle.read():
            pytest.fail("the file was empty")
'''

_GRADED_THEN_RETURN = '''\
def test_nu(corpus: list[int]) -> None:
    """Graded, then short-circuited."""
    assert corpus
    if len(corpus) == 1:
        return
    assert sum(corpus) > 1
'''

_BOTH_ARMS_GRADE = '''\
def test_xi(flag: bool) -> None:
    """Graded on both arms."""
    if flag:
        assert flag is True
    else:
        assert flag is False
'''

#: The idiom every skip this tree ships uses: the condition is not decidable.
_CONDITIONAL_SKIP = '''\
def test_omicron(corpus: list[int]) -> None:
    """Skipped only when there is nothing to grade."""
    if not corpus:
        pytest.skip("no corpus on this machine")
    assert sum(corpus) > 0
'''

#: The conditional decorator form, whose condition is a runtime fact.
_CONDITIONAL_SKIP_DECORATOR = '''\
@pytest.mark.skipif(sys.platform != "win32", reason="drive letters are Windows")
def test_pi(corpus: list[int]) -> None:
    """Skipped on machines the property cannot hold on."""
    assert sum(corpus) > 0
'''

_VALUE_RETURNING_HELPER = '''\
def _power(base: int, exponent: int) -> int:
    """A utility that happens to assert."""
    if exponent == 0:
        return 1
    assert exponent > 0
    return base ** exponent
'''

#: The loop residual. NO TRAILING RETURN - the first version of this fixture
#: carried one, and that gratuitous return was the only thing the return-only
#: analysis could see, so this test was green straight through the defect.
_LOOP_ONLY_ASSERT = '''\
def test_rho(corpus: list[int]) -> None:
    """The only assertion is inside a loop that may not run."""
    for item in corpus:
        assert item > 0
'''

_LOOP_THEN_BRANCH = '''\
def test_sigma(tree: list[object]) -> None:
    """Graded inside a branch inside a loop."""
    for node in tree:
        if isinstance(node, str):
            assert node
'''

#: A stand-in guard tool. ``{VERDICT}`` and ``{SKIPS}`` are substituted with
#: literals, so the guard under the criteria is real code in a real file.
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

#: The defeat of the distinctness criterion: it reads nothing, can never fail,
#: and renders its input so its answer varies.
_STUB_ECHOING = "\n".join(
    [
        '"""A stand-in that echoes its input and reads nothing."""',
        "",
        "",
        "def guard_planted(root):",
        '    """Vary the answer without ever looking at the tree."""',
        "    verdict = {VERDICT}",
        '    verdict["detail"] = [*verdict["detail"], str(root)]',
        "    return verdict, {SKIPS}",
        "",
    ]
)

#: An honest stand-in: it reads the tree and reports a real violation in it.
_STUB_READING = "\n".join(
    [
        '"""A stand-in that actually reads the tree it is given."""',
        "",
        "",
        "def guard_planted(root):",
        '    """Report every file carrying a byte the character-set rule forbids."""',
        "    bad = []",
        '    for entry in sorted(root.rglob("*")):',
        "        if entry.is_file() and any(byte > 126 for byte in entry.read_bytes()):",
        "            bad.append(entry.name)",
        '    status = "FAIL" if bad else "PASS"',
        '    verdict = {"id": "z", "name": "planted", "status": status,',
        '               "detail": bad or ["clean"]}',
        "    return verdict, []",
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
    tmp_path: Path,
    status: str,
    skips: list[dict[str, str]],
    *,
    template: str = _STUB_CONSTANT,
    tag: str = "constant",
) -> ModuleType:
    """Write and load a one-guard stand-in answering as instructed.

    Args:
        tmp_path: Where the stand-in is written.
        status: The status its guard answers.
        skips: The skip records its guard answers with.
        template: Which stand-in body to write.
        tag: A name fragment keeping the loaded modules distinct.

    Returns:
        The loaded stand-in.
    """
    verdict = {"id": "z", "name": "planted", "status": status, "detail": ["said something"]}
    source = template.replace("{VERDICT}", repr(verdict)).replace("{SKIPS}", repr(skips))
    name = f"stub_{tag}_{status}_{len(skips)}"
    path = tmp_path / f"{name}.py"
    path.write_text(source, encoding="utf-8", newline="\n")
    return _load(path, f"cs846_{name}")


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
    """No module can escape by not opting in, which is the whole point."""
    holding = {member.module for member in surveyed.members}
    test_modules = {relative for relative in tracked if Path(relative).name.startswith("test_")}
    absent = sorted(test_modules - holding)
    assert test_modules, "no tracked module is named as a test module"
    assert not absent, (
        f"{len(absent)} tracked test module(s) contributed no member, so nothing here "
        f"grades them: {absent}"
    )


def test_the_derivation_covers_its_own_two_modules(surveyed: liveness.Survey) -> None:
    """The checker must be inside the population it derives."""
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

    A derived population covering exactly the modules already opting in would
    be a rename rather than a widening. The opt-in set is DERIVED TOO, from
    which modules CALL the pre-existing helper.
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
    """THE RULE. Every member grades before every way out of it."""
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
    """A SECOND consumer over a DIFFERENT population.

    This grades the members AND the value-returning graders the population
    filter excludes, so its census is not the one above.
    """
    rendered = [finding.rendered() for finding in surveyed.dead_grading]
    count = len(rendered)
    graded = len(surveyed.members) + len(surveyed.value_returning)
    assert graded > 1, f"{graded} function(s) ship a grading statement, so this is vacuous"
    assert not count, (
        f"{count} grading statement(s) can never run, so they grade nothing while still "
        f"reading as assertions: {rendered[:20]}"
    )


def test_no_test_ships_its_only_grading_under_a_name_this_module_cannot_read(
    surveyed: liveness.Survey,
) -> None:
    """THE VOCABULARY BOUNDARY, GRADED RATHER THAN DESCRIBED.

    The population comes from calls named ``assert...`` plus pytest's own
    spellings, which is a NAMING CONVENTION - so renaming a grader takes its
    callers out of the population without changing a line of their behaviour.
    The wider vocabulary is re-derived every run and everything it adds is
    counted; a ``test_`` function among them is not a boundary, it is a control
    with no grading route this module can see.
    """
    boundary = surveyed.vocabulary_boundary
    counted = len(boundary)
    tests = sorted(member.rendered() for member in boundary if member.name.startswith("test_"))
    assert counted, (
        "the wider vocabulary now adds nothing, so either the tree changed or this "
        "boundary census stopped being computed"
    )
    assert not tests, (
        f"{len(tests)} test(s) grade only through a name outside this module's "
        f"vocabulary, so they are not in the population at all: {tests}"
    )


def test_this_check_grades_its_own_two_modules(repo_root: Path) -> None:
    """A THIRD consumer, re-deriving rather than reusing the fixture."""
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

    Agreement between two derivations of the same thing is not evidence, but a
    finding from either is. The coupling is stated: if
    ``tests/save/reach_guard`` moves, this import fails loudly rather than
    silently covering nothing.
    """
    _assert_no_test_is_gutted(Path(__file__))


def test_the_census_this_module_computes_is_graded_from_another_file(repo_root: Path) -> None:
    """A FIFTH consumer, and the only one that is not in this file.

    FOUR CONSUMERS IN ONE FILE IS ONE CONSUMER - measured by an adversary, who
    silenced all four with a single edit. This asserts the cross-file grader
    EXISTS and calls the same derivation, so removing it is a change to a file
    an attacker would also have to find.
    """
    elsewhere = repo_root / "tests" / "test_doc_budget.py"
    text = elsewhere.read_text(encoding="utf-8")
    assert "liveness.survey" in text, (
        f"{elsewhere.name} no longer grades the liveness census, so every consumer of it "
        "is back inside the one file it grades"
    )
    assert "test_the_liveness_census_is_clean_when_read_from_another_module" in text, (
        f"{elsewhere.name} lost the cross-file consumer this check depends on"
    )


# ---------------------------------------------------------------------------
# COVERED SHAPES. Every one was measured silent against an earlier version.
# ---------------------------------------------------------------------------


def test_a_bare_early_return_is_reported() -> None:
    """The cheapest gutting."""
    assert _kinds(_BARE_RETURN) == ["return"], f"got {_findings(_BARE_RETURN)}"


def test_the_conditional_early_return_the_item_was_filed_on_is_reported() -> None:
    """The shape no unreachable-code check can see."""
    assert _kinds(_CONDITIONAL_RETURN) == ["return"], f"got {_findings(_CONDITIONAL_RETURN)}"


def test_a_body_wrapped_so_it_never_runs_is_reported_with_no_return_in_it() -> None:
    """The shape that refuted the FIRST version. There is no return anywhere."""
    kinds = _kinds(_WRAPPED_BODY)
    assert "end of function" in kinds, f"got {_findings(_WRAPPED_BODY)}"


def test_the_wrap_is_still_reported_when_a_constant_assertion_is_appended() -> None:
    """THE SHAPE THAT REFUTED THE SECOND VERSION - the wrap plus eleven characters.

    ``assert True`` executes and passes and asserts nothing, so counting it as
    grading restores every gutting this module closes. It is excluded on that
    ground and not because it is rare.
    """
    kinds = _kinds(_WRAPPED_BODY_WITH_A_TAUTOLOGY)
    assert "end of function" in kinds, f"got {_findings(_WRAPPED_BODY_WITH_A_TAUTOLOGY)}"


def test_a_try_that_discards_the_failure_it_grades_is_reported() -> None:
    """The assertions run and their verdict is thrown away."""
    assert _kinds(_SWALLOWED) == ["failure discarded"], f"got {_findings(_SWALLOWED)}"


def test_an_unconditional_skip_at_the_head_is_reported() -> None:
    """Gutting written in pytest's own vocabulary."""
    assert _kinds(_SKIPPED_AT_HEAD) == ["exit without grading"], (
        f"got {_findings(_SKIPPED_AT_HEAD)}"
    )


def test_a_skip_behind_a_constant_condition_is_reported() -> None:
    """A skip wearing a conditional's clothes.

    The previous version certified this as legitimate, because it read every
    nested skip as conditional. ``globals()`` is decidable and looks nothing
    like a precondition; the asymmetry is positional, not undecidable.
    """
    assert _kinds(_SKIP_BEHIND_A_CONSTANT) == ["exit without grading"], (
        f"got {_findings(_SKIP_BEHIND_A_CONSTANT)}"
    )


def test_the_same_skip_spelled_as_a_raise_is_reported() -> None:
    """``raise pytest.skip.Exception(...)`` does what ``pytest.skip(...)`` does.

    An analysis that reads one spelling and not the other is closed by
    spelling, which is not closed at all.
    """
    assert _kinds(_SKIP_RAISED_BEHIND_A_CONSTANT) == ["exit without grading"], (
        f"got {_findings(_SKIP_RAISED_BEHIND_A_CONSTANT)}"
    )


def test_a_test_disabled_by_a_decorator_is_reported() -> None:
    """One line, no statement, and the way anybody actually disables a test.

    A decorator is not in the body, so an analysis reading only statements
    never sees it. ``decorator_list`` is read for exactly this.
    """
    kinds = _kinds(_DISABLED_BY_DECORATOR)
    assert any(kind.startswith("disabled by") for kind in kinds), (
        f"got {_findings(_DISABLED_BY_DECORATOR)}"
    )


def test_a_grader_that_is_not_a_test_is_reported_the_same_way() -> None:
    """The second structure, on the same terms as the first."""
    assert "end of function" in _kinds(_GUTTED_GRADER), f"got {_findings(_GUTTED_GRADER)}"
    assert [member.name for member in _survey(_GUTTED_GRADER).members] == [
        "_assert_every_row_balances"
    ], "the grader did not enter the population, so the finding above is incidental"


def test_a_value_returning_grader_made_to_fabricate_a_value_is_reported() -> None:
    """The kill an adversary demonstrated live inside the excluded set.

    Handing a caller a literal nothing measured turns that caller's assertion
    into a tautology. The function is still outside the population - it returns
    a value - and it is graded by the one rule that is decidable for it.
    """
    survey = _survey(_FABRICATED_RETURN)
    assert [finding.kind for finding in survey.findings] == ["returns a fabricated value"], (
        f"got {[finding.rendered() for finding in survey.findings]}"
    )
    assert [member.name for member in survey.value_returning] == ["_reported_file_count"]


def test_grading_that_can_never_run_is_reported() -> None:
    """An assertion below an unconditional exit reads as coverage and is not."""
    dead = [finding.kind for finding in _survey(_DEAD_GRADING).dead_grading]
    assert dead == ["unreachable grading"], f"got {_survey(_DEAD_GRADING).dead_grading}"


# ---------------------------------------------------------------------------
# BOUNDARIES. Every one of these reddened under an earlier version, and every
# one is correct code.
# ---------------------------------------------------------------------------


def test_a_guarded_failure_is_read_as_an_assertion() -> None:
    """``if bad: pytest.fail(...)`` is ``assert not bad`` written differently.

    An earlier version reported this. It accepts one spelling of a test and
    rejects the other, which is grading style rather than liveness.
    """
    assert not _findings(_GUARDED_FAILURE), f"got {_findings(_GUARDED_FAILURE)}"


def test_a_handler_that_converts_a_failure_is_not_read_as_swallowing_it() -> None:
    """``except E: pytest.fail(...)`` asserts the call does not raise."""
    assert not _findings(_CONVERTED_FAILURE), f"got {_findings(_CONVERTED_FAILURE)}"


def test_a_match_graded_in_every_arm_is_not_reported() -> None:
    """THE ARM THAT WAS WRONG FOR EVERY MATCH EVER WRITTEN.

    The previous version returned the incoming verdict here, so no ``match``
    could ever grade anything. It scored zero only because this tree contains
    no ``match`` statement - the rule had been chosen by its count on today's
    tree rather than by what it means.
    """
    assert not _findings(_MATCH_GRADED_IN_EVERY_ARM), f"got {_findings(_MATCH_GRADED_IN_EVERY_ARM)}"


def test_a_failure_guarded_inside_a_with_is_not_reported() -> None:
    """The guarded failure one level down."""
    assert not _findings(_FAILURE_INSIDE_A_WITH), f"got {_findings(_FAILURE_INSIDE_A_WITH)}"


def test_an_early_return_after_the_grading_is_not_reported() -> None:
    """A fast path below the assertion is correct code."""
    assert not _findings(_GRADED_THEN_RETURN)


def test_an_exit_both_arms_of_an_if_have_graded_before_is_not_reported() -> None:
    """The boundary that needs the branch merge to be right."""
    assert not _findings(_BOTH_ARMS_GRADE)


def test_a_genuinely_conditional_skip_is_not_reported() -> None:
    """Every skip this tree ships is conditional on a runtime fact."""
    assert not _findings(_CONDITIONAL_SKIP)


def test_a_skipif_on_a_runtime_condition_is_not_reported() -> None:
    """The decorator form whose condition is a property of the machine."""
    assert not _findings(_CONDITIONAL_SKIP_DECORATOR)


def test_a_value_returning_helper_that_declines_to_answer_is_not_reported() -> None:
    """Declining is not fabricating.

    Returning ``None`` says "I have no answer"; returning a literal answers
    without looking. This tree ships the first shape in a census that finds no
    save library, and it is correct there.
    """
    assert not _findings(_DECLINING_RETURN), f"got {_findings(_DECLINING_RETURN)}"


def test_a_value_returning_helper_is_counted_and_its_literal_return_is_reported() -> None:
    """THE COST OF THE FABRICATED-RETURN RULE, STATED RATHER THAN HIDDEN.

    ``if exponent == 0: return 1`` is a correct boundary and ``if globals():
    return 1`` is a gutting, and they are the same three tokens. The rule
    reports both. Measured on this tree it reports NEITHER, because no
    value-returning grader here has an ungraded literal return - but the false
    positive class is real and this test is where it is written down, so nobody
    reads the zero on the tree as a claim that the rule is exact.

    The population filter itself is unaffected: the helper is still excluded
    from the member population and still counted.
    """
    survey = _survey(_VALUE_RETURNING_HELPER)
    assert not survey.members, "a value-returning utility entered the grader population"
    assert [finding.kind for finding in survey.findings] == ["returns a fabricated value"], (
        f"the cost of this rule changed shape: {[f.rendered() for f in survey.findings]}"
    )
    assert [member.name for member in survey.value_returning] == ["_power"], (
        "the excluded utility was dropped instead of counted"
    )


def test_a_loop_that_may_not_run_is_counted_rather_than_reported() -> None:
    """THE FIXTURE THAT HID THE FIRST DEFECT, RE-AUTHORED WITHOUT ITS TRAILING RETURN."""
    survey = _survey(_LOOP_ONLY_ASSERT)
    assert not survey.findings, f"a legitimate loop-only grading was reported: {survey.findings}"
    assert [member.name for member in survey.loop_leaned] == ["test_rho"], (
        "the loop generosity was applied without being counted, which makes it a silence "
        "rather than an exemption"
    )


def test_grading_inside_a_branch_inside_a_loop_is_counted_rather_than_reported() -> None:
    """The commonest correct idiom in this tree."""
    survey = _survey(_LOOP_THEN_BRANCH)
    assert not survey.findings, f"the commonest correct idiom was reported: {survey.findings}"
    assert [member.name for member in survey.loop_leaned] == ["test_sigma"]


# ---------------------------------------------------------------------------
# The residuals - counted and re-derived on every run, never prose
# ---------------------------------------------------------------------------


def test_every_test_outside_the_population_at_least_exercises_something(
    surveyed: liveness.Survey,
) -> None:
    """A test that ships no assertion grades by the code under test not raising."""
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
    """The loop residual, re-derived and held to its own shape."""
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
        "no member was credited to the loop generosity, so either the tree changed shape "
        "or the generosity is no longer being applied and should be removed"
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
            if isinstance(statement, ast.Try)
            and (
                liveness.carries_grading(statement.body)
                or any(
                    liveness.terminates_in_failure(handler.body) for handler in statement.handlers
                )
            )
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
    """The excluded set, re-derived, and each re-read to confirm the excluded shape."""
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
    """THE GUARD HALF REACHES ONE FILE, AND THAT IS SAID OUT LOUD HERE."""
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

    The only liveness question available about a tool that ships no guard and
    no assertion, and it covers ``tools/precommit_gate.py`` - a frozen tier-0
    blocking gate - by READING it. The blocking set is derived from the hook
    scripts themselves, so a tool promoted into a hook joins by being invoked.
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


@pytest.fixture(scope="module")
def tracked_everything(repo_root: Path) -> list[str]:
    """Every tracked file, not only the Python ones.

    Args:
        repo_root: Repository root.

    Returns:
        Repo-relative paths.
    """
    proc = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, "git could not enumerate the tracked files"
    return sorted(line for line in proc.stdout.splitlines() if line)


def test_every_derived_guard_is_reached_by_its_runner(
    repo_root: Path, guard_tools: list[str]
) -> None:
    """A guard the runner never names is a guard that never runs."""
    unreached: list[str] = []
    derived: list[str] = []
    for relative in guard_tools:
        text = (repo_root / relative).read_text(encoding="utf-8")
        names = liveness.guard_function_names(text)
        derived.extend(f"{relative}::{name}" for name in names)
        runner = liveness.module_function(text, GUARD_RUNNER)
        assert runner is not None, (
            f"{relative} defines guards and no {GUARD_RUNNER} to drive them, so nothing "
            "here can tell which of them ever run"
        )
        reached = {node.id for node in ast.walk(runner) if isinstance(node, ast.Name)}
        unreached.extend(f"{relative}::{name}" for name in sorted(set(names) - reached))
    count = len(derived)
    assert count > 1, f"{count} guard(s) were derived, so this is green about nothing"
    assert not unreached, (
        f"{unreached} are defined and {GUARD_RUNNER} never mentions them, so they ship "
        "without ever running"
    )


def test_no_shipped_guard_survives_a_tree_built_to_break_the_rules(
    loaded_guard_tools: dict[str, ModuleType], tracked_everything: list[str], tmp_path: Path
) -> None:
    """THE ONE CRITERION THAT IS NOT A PROXY.

    The other two ask whether a guard SAID something and whether what it said
    VARIED. Both were defeated - one by fabricating a skip record, the other by
    echoing the root into the detail while reading nothing. This asks the only
    question that is about guarding: handed a tree that breaks the rules, does
    it report?

    The tree is built from the REAL tracked file names with a single authored
    document as every file's content, so a guard looking for a particular path
    finds one and what it finds is wrong. Neither half names a guard.
    """
    root = tmp_path / "known-bad"
    root.mkdir()
    liveness.write_known_bad_tree(root, tracked_everything)

    survivors: list[str] = []
    asked = 0
    for relative, module in loaded_guard_tools.items():
        files, source, _skips = module.enumerate_files(root)
        for answer in liveness.guard_answers(module, root, files, source):
            asked += 1
            if liveness.cannot_be_forced_to_fail(answer):
                survivors.append(f"{relative}::{answer.function} [{answer.guard_id}]")
    count = len(survivors)
    assert asked > 1, f"{asked} guard(s) were asked about the known-bad tree, so this is vacuous"
    assert not count, (
        f"{count} guard(s) passed a tree built to break the rules, so nothing they do "
        f"depends on the tree being right: {sorted(survivors)}"
    )


def test_no_shipped_guard_answers_pass_about_a_tree_it_could_not_read(
    loaded_guard_tools: dict[str, ModuleType], repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Green with nothing recorded is not a verdict (CONVENTIONS.md section 15.1).

    A PROXY, and defeated on its own by fabricating a skip record. Kept because
    it catches the laziest gutting for almost nothing.
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
    """A PROXY, and defeated on its own by echoing an input into the detail.

    Kept beside the known-bad criterion because it catches a constant return
    without needing a tree built for the purpose.
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
        f"an unreadable tree: {sorted(constant)}"
    )


def test_the_blind_sweep_reaches_every_guard_each_tool_defines(
    loaded_guard_tools: dict[str, ModuleType], repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sweep that quietly skipped a guard would report the same clean result."""
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
    """The privacy half, derived over the same population."""
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


def test_a_guard_that_fabricates_a_skip_record_is_reported_by_the_next_criterion(
    tmp_path: Path,
) -> None:
    """The defeat of the FIRST criterion, closed by the second."""
    tool = _stub_tool(tmp_path, "PASS", [{"path": "docs", "reason": "not reached"}])
    rounds = [
        liveness.guard_answers(tool, tmp_path, [], "stub enumeration"),
        liveness.guard_answers(tool, tmp_path / "elsewhere", [], "stub enumeration"),
    ]
    silent = [answer.function for answer in rounds[0] if liveness.silently_green(answer)]
    constant = [
        first.function
        for index, first in enumerate(rounds[0])
        if liveness.answers_the_same_about_every_tree([round_[index] for round_ in rounds])
    ]
    assert not silent, "the fabricated skip did NOT defeat the silence criterion after all"
    assert constant == ["guard_planted"], f"the fabricating guard was not reported: {rounds}"


def test_a_guard_that_echoes_its_input_is_reported_by_the_known_bad_tree(
    tmp_path: Path,
) -> None:
    """THE DEFEAT OF THE SECOND CRITERION, CLOSED BY THE THIRD.

    A guard that reads nothing, can never fail, and renders its root into the
    detail satisfies both proxies completely - and this asserts that it does,
    rather than pretending otherwise. Only the known-bad tree reports it,
    because only that criterion asks whether the guard can be made to FAIL.
    """
    tool = _stub_tool(tmp_path, "PASS", [], template=_STUB_ECHOING, tag="echoing")
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()
    rounds = [
        liveness.guard_answers(tool, first, [], "stub enumeration"),
        liveness.guard_answers(tool, second, [], "stub enumeration"),
    ]
    varied = not liveness.answers_the_same_about_every_tree([rounds[0][0], rounds[1][0]])
    forced = [answer.function for answer in rounds[0] if liveness.cannot_be_forced_to_fail(answer)]
    assert varied, "the echoing guard did NOT defeat the distinctness criterion after all"
    assert forced == ["guard_planted"], f"the echoing guard was not reported: {rounds}"


def test_a_guard_that_reads_the_known_bad_tree_and_reports_is_not_flagged(
    tmp_path: Path,
) -> None:
    """THE BOUNDARY OF THE KNOWN-BAD CRITERION.

    A criterion that flagged every guard would be indistinguishable from one
    that flagged the right guards. This stand-in genuinely reads the tree - it
    looks for the byte the character-set rule forbids, which the known-bad
    document carries - so it FAILS that tree and is not reported. Handed a
    clean tree the same stand-in passes, which is the answer it earned.
    """
    tool = _stub_tool(tmp_path, "PASS", [], template=_STUB_READING, tag="reading")
    bad_tree = tmp_path / "known-bad"
    bad_tree.mkdir()
    liveness.write_known_bad_tree(bad_tree, ["CLAUDE.md", "docs/LEDGER.md"])
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "CLAUDE.md").write_text("plain ascii\n", encoding="utf-8", newline="\n")

    forced = liveness.guard_answers(tool, bad_tree, [], "stub enumeration")
    honest = liveness.guard_answers(tool, clean, [], "stub enumeration")

    assert forced[0].status == "FAIL", (
        f"the reading stand-in did not fail the known-bad tree, so this boundary is "
        f"not exercising the criterion: {forced}"
    )
    assert not [a.function for a in forced if liveness.cannot_be_forced_to_fail(a)], (
        f"a guard that read the known-bad tree and reported it was flagged anyway: {forced}"
    )
    assert honest[0].status == "PASS", (
        f"the reading stand-in failed a clean tree, so it is not discriminating: {honest}"
    )


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
