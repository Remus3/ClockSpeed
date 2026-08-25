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
  - THE BODY WRAPPED IN A LOOP THAT NEVER RUNS - ``for _ in []``,
    ``for _ in range(0)`` and ``while False``, all three of which folded
    nowhere while the module's own words said a constant branch is folded;
  - the assertions SWALLOWED by a ``try`` whose handler discards the failure,
    INCLUDING one that logs it rather than passing, and one spelled
    ``with contextlib.suppress(AssertionError):`` with no ``try`` in it at all;
  - an unconditional ``pytest.skip`` at the head;
  - a skip written to look conditional - ``if globals(): pytest.skip(...)``;
  - the same thing spelled ``raise pytest.skip.Exception(...)``;
  - ``@pytest.mark.skip`` as a DECORATOR, which is not a statement at all;
  - ``@pytest.mark.parametrize("unused", [])``, which runs the body zero times
    while pytest reports the module passed;
  - ``assert True`` appended to any of the above to satisfy a naive check;
  - grading placed where it can never run, INCLUDING below a constant branch
    that always returns - which is what a value-returning grader gutted to
    fabricate a literal or to decline on every call actually is;
  - AN ASSERTION REWRITTEN TO COMPARE ONE LOCAL WITH ITSELF BY ``is``, and one
    whose predicate the language decides rather than the input, in any of its
    respellings;
  - A CONTROL RENAMED OUT OF PYTEST'S COLLECTION and named nowhere else, which
    no rule over its own source can see at all;
  - A DETECTOR LIBRARY NOTHING GRADED CALLS, which contributes no member, is
    not named ``test_`` and ships no ``guard_`` function, so every population
    above missed it;
  - A GRADER RENAMED OUT OF THE VOCABULARY, wherever the call resolves inside
    the surveyed set;
  - THE VOCABULARY ITSELF narrowed or respelled, which every control here
    selects by symbol and none of them could see;
  - WHETHER AN ASSERTION RAN, for one call of one function handed to
    :func:`liveness.observed_grading`.

NOT COVERED, AND THIS HALF IS STILL THE ONE THAT MATTERS. Shapes named here
keep MOVING rather than vanishing, because each is closed for a DECIDABLE
SUB-CLASS and left open for the rest. What remains:

  - THE ALGEBRAIC TAUTOLOGY THIS REPOSITORY ACTUALLY SHIPPED.
    ``empty + (records - empty) == records`` is not caught: its operands were
    built in ANOTHER function, so nothing about this assertion's own syntax
    decides it. Nor is a bound its own construction makes unexceedable, which
    the same control carried more than once. This is a hole in the middle, not
    a boundary, and the sub-class that is closed is the smaller half of it.
  - A SELF-COMPARISON UNDER AN OPERATOR THE PROGRAM DEFINES. ``assert x == x``
    was reported and is not any more, and the reason is that the claim made
    about it was FALSE: ``__eq__``, ``__ge__``, ``__getattr__`` and
    ``__getitem__`` are all program code, so ``assert version >= version`` and
    ``assert parser.parsed is parser.parsed`` each fail against a real defect
    and are each the standard test for it. BOUNDED RATHER THAN DECIDED, by
    :func:`liveness.self_comparison`, and the cost of that is stated where the
    rule is: a gutter typing ``assert x == x`` is no longer refused.
  - A CONTROL WHOSE ASSERTIONS ARE SIMPLY DELETED, leaving the calls. It grades
    by the code under test not raising, which is a real if weaker test, and it
    is COUNTED by the outside-the-population census rather than reported.
  - A GUTTING BRANCH WHOSE CONDITION IS GENUINELY UNKNOWN AT PARSE TIME.
    ``if globals():`` is folded; ``if _looks_fine():`` is not, and it is
    structurally identical to a real precondition. BOUNDED RATHER THAN DECIDED
    - :func:`liveness.conditional_exits` counts how much of the population a
    gutting of this shape could hide in, and counting is the whole of what is
    honest to do with it.
  - A GRADER RENAMED AND THEN REACHED BY A ROUTE NOTHING RESOLVES: a method
    call, an alias, a call through a variable, or a call into a module outside
    the surveyed set. The resolution under-reports by construction, which is
    the same direction the loop and ``try`` generosities already take.
  - WHETHER AN ASSERTION RAN, FOR THE POPULATION. The channel exists and is
    exact, and it is demonstrated below on a real shipped grader. It is not
    applied to the population: that means counting while the suite runs, which
    is a collection hook in ``tests/conftest.py``, and this module does not own
    that file. The population is covered STATICALLY and that sentence is the
    residual, not a formality.

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
import sys
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

#: THE GRADING VOCABULARY, TRANSCRIBED AS LITERALS. This is the one deliberate
#: transcription in the file and it exists for the reason
#: ``tests/save/test_byte_order_status.py`` records for the byte-order status
#: words: every control in the checker selects these sets by SYMBOL, so
#: narrowing one to nothing, or respelling a word inside it, changes what
#: counts as grading while every symbol still resolves and every control stays
#: green. A word added or removed there is added or removed HERE, together with
#: whatever grades it.
PINNED_GRADING_PREFIXES: Final = ("assert",)
PINNED_PYTEST_GRADING_CALLS: Final = frozenset({"fail", "raises", "warns"})
PINNED_EXITING_CALLS: Final = frozenset({"skip", "xfail", "exit"})


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

# --- the non-constant tautology, and the correct code beside it ------------
#
# EVERY FIXTURE IN THIS BLOCK IS DERIVED FROM A REAL MEMBER OF THE POPULATION,
# because a fixture authored beside the analysis is green through the real
# defect. The two boundaries below are reductions of code this tree ships
# TODAY, at tests/solve/test_optimize.py and tests/save/test_container_
# elements.py, and each is the reason a wider rule was measured and refused.

#: THE SHAPE THIS REPOSITORY ACTUALLY SHIPPED AND REMOVED, reduced to the half
#: that is decidable. The real one asserted that the two parts of a census
#: added back up to the census - true of every possible input - and its
#: operands were built in ANOTHER function, so no static rule reaches it. What
#: is decidable is the same defect written without the indirection.
_SELF_COMPARISON = '''\
def test_upsilon(found: object) -> None:
    """Grades nothing: the comparison holds for every possible input."""
    records = found.records
    assert records == records
'''

#: The language guarantees the answer, so the input cannot change it.
_VACUOUS_LENGTH = '''\
def test_phi(rows: list[int]) -> None:
    """Grades nothing: len() is non-negative whatever it is handed."""
    assert len(rows) >= 0
'''

#: Every value is an instance of object, so the first argument is not read.
_VACUOUS_ISINSTANCE = '''\
def test_chi(row: object) -> None:
    """Grades nothing: object is the root of the type hierarchy."""
    assert isinstance(row, object)
'''

#: REDUCED FROM tests/solve/test_optimize.py, WHICH SHIPS THIS TODAY. Two calls
#: written the same way are not the same value: this asserts the solver is
#: DETERMINISTIC, and it fails the moment it stops being. A reflexive rule that
#: ignored the calls would report it, which is why the shipped rule requires the
#: compared expression to be call-free.
_DETERMINISM_CHECK = '''\
def test_omega_two(registry: object, request: object) -> None:
    """Two runs on one input must agree, and the calls may disagree."""
    assert repr(_run(registry, request)) == repr(_run(registry, request))
'''

#: REDUCED FROM tests/save/test_container_elements.py, WHICH SHIPS THIS TODAY,
#: and it is this project's own mutation discipline - assert the revert landed.
#: Inlining single-assignment locals before comparing would rewrite the left
#: side into the right and report it, because the ATTRIBUTE was reassigned
#: between the binding and the assertion. That is why no inlining is done.
_REVERT_LANDED = '''\
def test_psi(objects: object, real: object) -> None:
    """The shipped decoder must be back, and the attribute moved in between."""
    objects._bound_container_elements = _mutated
    try:
        sweep = _sweep_the_library()
    finally:
        objects._bound_container_elements = real
    assert objects._bound_container_elements is real
'''

# --- the value-returning grader gutted to decline --------------------------

#: The residual :data:`_DECLINING_RETURN` names. Declining is legitimate; a
#: decline that happens on every call is a stop wearing a decline's clothes.
_UNCONDITIONAL_DECLINE = '''\
def _census(paths: list[str]) -> int | None:
    """Gutted to decline every time, which is not declining."""
    if globals():
        return None
    assert paths
    return len(paths)
'''

# --- the grader renamed out of the vocabulary ------------------------------

#: A grader whose name no vocabulary reaches, and the control that grades only
#: through it. Renaming ``_assert_every_row_balances`` to this is the whole
#: defect: nothing about the caller changed, and the vocabulary stopped seeing
#: that it grades at all.
_RENAMED_GRADER = '''\
def _every_row_balances(rows: list[int]) -> None:
    """A grader named outside every vocabulary this module carries."""
    assert not [row for row in rows if row < 0]


def test_tau(rows: list[int]) -> None:
    """Grades only by calling the renamed grader."""
    _every_row_balances(rows)
'''

#: The same pair with the caller gutted. The route is what makes this visible.
_RENAMED_GRADER_GUTTED = '''\
def _every_row_balances(rows: list[int]) -> None:
    """A grader named outside every vocabulary this module carries."""
    assert not [row for row in rows if row < 0]


def test_tau(rows: list[int]) -> None:
    """Gutted, and no vocabulary can see that it ever graded."""
    if globals():
        return
    _every_row_balances(rows)
'''

#: THE SAME RENAME ACROSS A FILE BOUNDARY, AND IT IS A SEPARATE FIXTURE BECAUSE
#: THE ONE-MODULE VERSION ABOVE WAS GREEN THROUGH A REAL DEFECT. The resolution
#: first returned the names each module DEFINES, which resolves the pair above -
#: they sit together - and resolves NOTHING in this tree, where every grader
#: worth renaming is imported by the module that calls it. A plant against a
#: real shipped grader is what reported it. This is the shape that occurs in the
#: wild; the one above is the reduction of it.
#:
#: THE REAL MEMBER IT IS DERIVED FROM IS IN THIS FILE.
#: :func:`test_no_test_in_this_module_is_gutted_to_an_early_return` grades ONLY
#: by calling ``_assert_no_test_is_gutted``, which it imports from
#: ``tests/save/reach_guard.py`` - one module defines the grader, another calls
#: it, and the caller ships no assertion of its own. The pair below is that
#: member with the grader RENAMED, which is the one edit the shipped vocabulary
#: cannot see. Nothing in this tree recovers a member through the route rule
#: today, and that number is derived rather than written down - see
#: :func:`test_resolving_routes_only_ever_widens_the_population`.
_CROSS_MODULE_GRADER = '''\
def _every_row_balances(rows: list[int]) -> None:
    """A grader named outside every vocabulary, in its own module."""
    assert not [row for row in rows if row < 0]
'''

_CROSS_MODULE_CALLER = '''\
from grader import _every_row_balances


def test_tau(rows: list[int]) -> None:
    """Gutted, and its grading route crosses a file boundary."""
    if globals():
        return
    _every_row_balances(rows)
'''

# --- the self-comparison family, split by whether the program participates --
#
# THE RULE THAT WAS STATED AND THE RULE THAT WAS IMPLEMENTED WERE NOT THE SAME
# RULE. The stated ground was "both sides evaluate the same object in the same
# frame, so nothing about the program can change the answer". The code excluded
# only ``ast.Call`` - but an attribute access runs ``__get__`` or
# ``__getattr__``, a subscription runs ``__getitem__``, and the comparison
# operator itself runs ``__eq__``, ``__ge__`` or ``__le__``. None of those is a
# ``Call`` node and every one of them is arbitrary program code.
#
# NEITHER OF THE TWO REFUSED FIXTURES BELOW IS DERIVED FROM A MEMBER OF THIS
# TREE, and that is said here rather than left implicit: this tree ships
# neither idiom, which is the whole reason the rule could score zero while
# being wrong. They are warranted by EXECUTION instead, which is stronger than a
# structural analogue - see
# :func:`test_the_self_comparisons_this_rule_refuses_to_decide_really_can_fail`,
# which builds both objects and watches each assertion fail once the code under
# test breaks.

#: THE ONE THE LANGUAGE DECIDES. ``is`` is the only comparison Python never
#: dispatches to program code, and a bare ``Name`` load runs none either.
_SELF_IDENTITY = '''\
def test_upsilon_one(found: object) -> None:
    """Grades nothing: identity of one local with itself, decided by the language."""
    records = found.records
    assert records is records
'''

#: The standard ``functools.cached_property`` memoization test. One access must
#: return the object the previous access returned, and it FAILS the moment the
#: cache is removed.
_MEMOIZED_ATTRIBUTE = '''\
def test_upsilon_two(parser: object) -> None:
    """Two accesses of a memoized attribute must be the same object."""
    assert parser.parsed is parser.parsed
'''

#: The standard ordering-reflexivity test. It FAILS the moment ``__ge__`` stops
#: being reflexive, which is exactly the defect it exists to find.
_REFLEXIVE_ORDER = '''\
def test_upsilon_three(version: object) -> None:
    """A total order must place every value at least as high as itself."""
    assert version >= version
'''

# --- respellings of the class the language decides -------------------------
#
# EACH IS THE SAME GUARANTEE THE SHIPPED RULE ALREADY CLAIMS, WRITTEN ANOTHER
# WAY. None has an analogue in this tree, because this tree ships no vacuous
# length or type predicate at all - so their warrant is the language's own
# contract rather than a member, and the contract is what the rule cites. A
# gutter typing any of them restored the gutting the rule exists to close.

_VACUOUS_LENGTH_MIRRORED = '''\
def test_phi_two(rows: list[int]) -> None:
    """The same floor with the operands the other way round."""
    assert 0 <= len(rows)
'''

_VACUOUS_LENGTH_FLOOR = '''\
def test_phi_three(rows: list[int]) -> None:
    """A floor one below the one the language guarantees."""
    assert len(rows) > -1
'''

_VACUOUS_ISINSTANCE_TUPLE = '''\
def test_chi_two(row: object) -> None:
    """A tuple of types passes when ANY of them matches, and object always does."""
    assert isinstance(row, (int, object))
'''

_VACUOUS_MEMBERSHIP = '''\
def test_chi_three(row: object) -> None:
    """Container membership shortcuts on identity, so this holds for every input."""
    assert row in (row,)
'''

# --- the body wrapped in a loop that never runs ----------------------------
#
# THE SAME SHAPE AS :data:`_WRAPPED_BODY`, which is validated, respelled three
# ways. The module folds a constant ``if`` and says out loud that a statically
# constant branch is not a branch; a loop over an empty literal is the same
# claim and was not folded, so all three gutted a real shipped control in
# silence.

_WRAPPED_IN_AN_EMPTY_LOOP = '''\
def test_gamma_two(corpus: list[int]) -> None:
    """Gutted by a loop over a literal that has nothing in it."""
    for _ in []:
        total = sum(corpus)
        assert total == 1
'''

_WRAPPED_IN_A_ZERO_RANGE = '''\
def test_gamma_three(corpus: list[int]) -> None:
    """Gutted by a range that yields nothing."""
    for _ in range(0):
        total = sum(corpus)
        assert total == 1
'''

_WRAPPED_IN_WHILE_FALSE = '''\
def test_gamma_four(corpus: list[int]) -> None:
    """Gutted by a while whose condition this module already folds to False."""
    while False:
        total = sum(corpus)
        assert total == 1
'''

# --- the failure swallowed by something other than `pass` ------------------

#: THE WAY ANYONE ACTUALLY WRITES A SWALLOW. The shipped rule accepted a handler
#: body only when every statement was ``pass`` or a bare constant, so one print
#: call defeated it.
_SWALLOWED_INTO_A_LOG = '''\
def test_delta_two(corpus: list[int]) -> None:
    """Gutted by logging the failure instead of raising it."""
    try:
        assert sum(corpus) == 1
    except AssertionError as exc:
        print(exc)
'''

#: The same swallow with no ``try`` in it at all, which is why inspecting only
#: ``ast.Try`` missed it.
_SUPPRESSED = '''\
def test_delta_three(corpus: list[int]) -> None:
    """Gutted by suppressing the failure in a context manager."""
    with contextlib.suppress(AssertionError):
        assert sum(corpus) == 1
'''

#: BOUNDARY, AND ITS ANALOGUE IS SHIPPED: ``tests/save/reach_guard.py`` catches
#: ``AssertionError`` from a delegated grader and appends the rejection to a
#: list its caller then grades. The failure is CONVERTED into a value, not
#: discarded, and a rule that could not tell the two apart would redden it.
_CONVERTED_TO_A_RECORD = '''\
def _rejected(paths: list[str]) -> list[str]:
    """Record which inputs the delegated grader refuses."""
    rejected: list[str] = []
    for path in paths:
        try:
            _assert_declared(path)
        except AssertionError:
            rejected.append(path)
    return rejected
'''

#: Verified end to end against a real shipped control: pytest reports
#: ``1 passed, 1 skipped`` and exits 0 while the body never runs once.
_DISABLED_BY_AN_EMPTY_PARAMETRIZE = '''\
@pytest.mark.parametrize("unused", [])
def test_theta_two(corpus: list[int], unused: int) -> None:
    """Switched off by giving the parametrizer nothing to run it with."""
    assert sum(corpus) == 1
'''

# --- the ordinary shapes the fabricated-return rule reported ---------------
#
# NONE OF THE THREE HAS A MEMBER IN THIS TREE TODAY, and that is exactly why
# the rule's cost was never measured: a rule whose false positives are absent
# from the tree it was written against reads as exact. Their warrant is
# EXECUTION - :func:`test_the_shapes_the_withdrawn_return_rule_reported_do_grade`
# calls each one and counts the grading statements that really ran.

_GRADES_THE_NON_EMPTY_CASE = '''\
def _census(paths: list[str]) -> int:
    """Grade the non-empty case, then answer either way."""
    if paths:
        assert all(paths)
    return len(paths)
'''

_ORDINARY_LITERAL_EARLY_RETURN = '''\
def _severity(kind: str, known: set[str], levels: dict[str, int]) -> int:
    """An early return of a literal on a boundary the caller relies on."""
    if kind == "info":
        return 0
    assert kind in known
    return levels[kind]
'''

_GRADES_ONLY_IN_STRICT_MODE = '''\
def _measured(text: str, strict: bool) -> int:
    """Grade only when the caller asked for it, and answer either way."""
    if strict:
        assert text
    return len(text)
'''

# --- the rename that takes a control out of pytest's collection ------------
#
# THE SHAPE THAT IS NOT A SHAPE. Every rule above reads the function's own
# source, and this one is invisible there: the body is untouched, every
# assertion is intact, and the control is a full population member with no
# finding against it. What changed is whether anything ever CALLS it, and that
# is a fact about pytest's collection rather than about the source.
#
# It is decidable from the tree all the same, on a narrower ground than
# collection: a module-level grader in a test module that pytest will not
# collect and that NOTHING IN THE TREE NAMES can never run, whoever was
# supposed to call it.

_RENAMED_OUT_OF_COLLECTION = '''\
def not_a_test_gamma(corpus: list[int]) -> None:
    """Gutted by a rename that takes it out of pytest's collection."""
    assert sum(corpus) == 1
'''

#: The boundary beside it: the same shape, named by a caller, which is every
#: delegated grader this tree ships.
_NAMED_BY_A_CALLER = '''\
def _assert_balanced(corpus: list[int]) -> None:
    """A delegated grader, which pytest never collects and a caller names."""
    assert sum(corpus) == 1


def test_gamma_five(corpus: list[int]) -> None:
    """Grades by delegating."""
    _assert_balanced(corpus)
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


def _written(tmp_path: Path, name: str, source: str) -> Path:
    """Write a synthetic module to a real file, so it has a readable source.

    The runtime counter derives its grading lines from the function's own
    source file, so a module compiled from a string has nothing to read.

    Args:
        tmp_path: Where to write it.
        name: The file name.
        source: The module's source.

    Returns:
        The path written.
    """
    path = tmp_path / name
    path.write_text(source, encoding="utf-8", newline="\n")
    return path


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
def routes(repo_root: Path, tracked: list[str]) -> dict[str, frozenset[str]]:
    """The resolved grading routes, re-derived rather than taken from a survey.

    Args:
        repo_root: Repository root.
        tracked: Repo-relative Python paths.

    Returns:
        Repo-relative path to the names that reach grading from it.
    """
    return liveness.grading_routes(
        {relative: (repo_root / relative).read_text(encoding="utf-8") for relative in tracked}
    )


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
    a value - and it is still reported, by the rule that was ALREADY meant to
    cover it: ``if globals(): return 1`` always returns, so the grading below
    it can never run. The rule that used to report this shape was withdrawn
    because that was the only thing it added.
    """
    survey = _survey(_FABRICATED_RETURN)
    assert [finding.kind for finding in survey.dead_grading] == ["unreachable grading"], (
        f"got {[finding.rendered() for finding in survey.dead_grading]}"
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


def test_a_value_returning_helper_is_counted_and_not_reported() -> None:
    """THE RULE THAT WAS WITHDRAWN, AND THE SHAPE THAT WITHDREW IT.

    ``if exponent == 0: return 1`` is a correct boundary and ``if globals():
    return 1`` is a gutting, and to a rule reading the returned value they are
    the same three tokens - so it reported both. The gutting is now reported
    where it belongs, as grading a folded branch makes unreachable, and what
    was left of the rule was this false positive and two more like it.

    The population filter itself is unaffected: the helper is still excluded
    from the member population and still counted.
    """
    survey = _survey(_VALUE_RETURNING_HELPER)
    assert not survey.members, "a value-returning utility entered the grader population"
    assert not survey.findings, (
        f"a correct boundary return was reported: {[f.rendered() for f in survey.findings]}"
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
# THE NON-CONSTANT TAUTOLOGY AND THE RENAMED GRADER, each stated as a semantic
# claim and each with its cost on this tree measured in the census tests
# further down rather than asserted from memory here.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("corpus", "why"),
    [
        (_VACUOUS_LENGTH, "len() is non-negative by the language's own contract"),
        (_VACUOUS_ISINSTANCE, "object is the root of the type hierarchy"),
    ],
)
def test_a_predicate_the_language_decides_grades_nothing(corpus: str, why: str) -> None:
    """SHAPE 1 again, where the guarantee is the interpreter's rather than the shape's."""
    survey = _survey(corpus)
    kinds = [finding.kind for finding in survey.vacuous_grading]
    assert kinds == ["cannot discriminate"], f"{why}, and it was not reported: {survey}"


@pytest.mark.parametrize(
    ("corpus", "why"),
    [
        (_DETERMINISM_CHECK, "two calls written alike are not the same value"),
        (_REVERT_LANDED, "the attribute was reassigned between the binding and the assert"),
    ],
)
def test_the_wider_tautology_rules_that_were_refused_stay_refused(corpus: str, why: str) -> None:
    """THE COST OF THE WIDER RULES, PAID BY REAL CODE THIS TREE SHIPS TODAY.

    Both fixtures are reductions of live members of the population. A reflexive
    rule that ignored calls reports the first; one that inlined
    single-assignment locals reports the second. Neither ships, and the reason
    is that each of these assertions genuinely CAN fail - not that the count
    looked better.
    """
    survey = _survey(corpus)
    assert not survey.vacuous_grading, f"{why}, and it was reported anyway: {survey}"
    assert not survey.findings, f"{why}, and the walk reported it: {survey.findings}"


# ---------------------------------------------------------------------------
# SESSION 40 - THE SHAPES AN ADVERSARY MEASURED SILENT OR WRONGLY REPORTED.
#
# Every rule below is stated as a SEMANTIC claim and its cost is measured by
# the census tests further down rather than asserted from memory here.
# ---------------------------------------------------------------------------


def test_a_local_compared_with_itself_by_identity_grades_nothing() -> None:
    """THE ONLY SELF-COMPARISON THE LANGUAGE DECIDES, AND NOW THE ONLY ONE REPORTED.

    ``is`` is the one comparison Python never dispatches to program code, and a
    bare ``Name`` load runs none either - so the two sides are the same object
    and the answer is fixed whatever the program does. That is the claim the
    docstring always made; it is now also the code.
    """
    survey = _survey(_SELF_IDENTITY)
    assert [finding.kind for finding in survey.vacuous_grading] == ["cannot discriminate"], (
        f"the self-identity was not reported: {survey.vacuous_grading}"
    )
    assert not survey.members, (
        "a control whose only assertion cannot discriminate is still counted as grading, "
        "so eleven more characters restore every gutting this module closes"
    )


def test_the_self_comparisons_this_rule_refuses_to_decide_really_can_fail() -> None:
    """WHY THE RULE WAS NARROWED, DEMONSTRATED BY RUNNING IT RATHER THAN BY ARGUING.

    THE STATED GROUND WAS FALSE FOR THE EXPRESSIONS THE CODE ACCEPTED. Excluding
    only ``ast.Call`` leaves attribute access, which runs ``__get__`` or
    ``__getattr__``, and leaves the comparison operator, which runs ``__eq__``,
    ``__ge__`` or ``__le__``. Neither is a ``Call`` node and both are arbitrary
    program code.

    So both shapes below are built here and executed. Each PASSES against sound
    code and FAILS against broken code, which is the definition of an assertion
    that discriminates - and each is the standard idiom for the property it
    tests, one for ``functools.cached_property`` and one for an ordering.
    """

    class Memoized:
        """A parser whose parse is cached, and whose cache can be removed."""

        def __init__(self, *, cached: bool) -> None:
            """Build one with the cache present or absent.

            Args:
                cached: Whether the memoization is in place.
            """
            self._cached = cached
            self._value: object = object()

        @property
        def parsed(self) -> object:
            """The parse, memoized or recomputed.

            Returns:
                The same object every time when cached, a new one when not.
            """
            return self._value if self._cached else object()

    class Ordered:
        """A value whose ordering can be made non-reflexive."""

        def __init__(self, *, sound: bool) -> None:
            """Build one with a sound or a broken ordering.

            Args:
                sound: Whether the ordering places a value at least as high as
                    itself.
            """
            self._sound = sound

        def __ge__(self, other: object) -> bool:
            """Compare, soundly or otherwise.

            Args:
                other: The right-hand operand, which is ignored.

            Returns:
                Whether this value is at least as high as the other.
            """
            return self._sound

    def memoization_holds(subject: Memoized) -> None:
        """Two accesses of a memoized attribute must be the same object.

        Args:
            subject: The parser to grade.
        """
        assert subject.parsed is subject.parsed

    def reflexivity_holds(subject: Ordered) -> None:
        """A total order must place every value at least as high as itself.

        Args:
            subject: The value to grade.
        """
        # PLR0124 IS THE SAME RULE THIS MODULE JUST NARROWED, AND IT IS WRONG
        # HERE FOR THE SAME REASON: the ordering is what is under test, so the
        # comparison discriminates. The lint is suppressed for one line, and
        # the two arms below prove the suppression is earned rather than
        # convenient.
        assert subject >= subject  # noqa: PLR0124

    memoization_holds(Memoized(cached=True))
    reflexivity_holds(Ordered(sound=True))
    with pytest.raises(AssertionError):
        memoization_holds(Memoized(cached=False))
    with pytest.raises(AssertionError):
        reflexivity_holds(Ordered(sound=False))


@pytest.mark.parametrize(
    ("corpus", "why"),
    [
        (_MEMOIZED_ATTRIBUTE, "an attribute access runs __get__ and __getattr__"),
        (_REFLEXIVE_ORDER, "the comparison itself runs __ge__"),
        (_SELF_COMPARISON, "the comparison itself runs __eq__, which NaN fails"),
    ],
)
def test_a_self_comparison_the_program_joins_in_is_bounded_rather_than_decided(
    corpus: str, why: str
) -> None:
    """SHAPE 1's OTHER HALF, HANDLED THE WAY THIS MODULE HANDLES EVERY UNDECIDABLE SHAPE.

    A self-comparison whose operator or whose operand access dispatches to
    program code is STRUCTURALLY IDENTICAL to a deliberate test of that code,
    and no rule over the assertion's own syntax separates them. It is therefore
    COUNTED rather than decided, exactly as :func:`liveness.conditional_exits`
    counts the undecidable exits.

    THE DISCLOSED COST OF THIS IS REAL AND IS NOT ARGUED AWAY: such an assertion
    is credited as grading, so ``assert x == x`` is a vacuity this module no
    longer refuses to count. What replaces the refusal is the bound, which is
    re-derived every run and is where the number lives.
    """
    survey = _survey(corpus)
    assert not survey.vacuous_grading, f"{why}, so it is not decidable: {survey.vacuous_grading}"
    assert [finding.kind for finding in survey.self_comparisons] == ["compared with itself"], (
        f"{why}, and the bound did not count it: {survey.self_comparisons}"
    )
    assert not survey.findings, f"{why}, and the walk reported it anyway: {survey.findings}"


@pytest.mark.parametrize(
    ("corpus", "why"),
    [
        (_VACUOUS_LENGTH_MIRRORED, "0 <= len(x) is len(x) >= 0 written the other way round"),
        (_VACUOUS_LENGTH_FLOOR, "len(x) > -1 is the same floor one below itself"),
        (_VACUOUS_ISINSTANCE_TUPLE, "a tuple of types passes when any of them matches"),
        (_VACUOUS_MEMBERSHIP, "container membership shortcuts on identity"),
    ],
)
def test_every_respelling_of_the_language_decided_class_is_reported(corpus: str, why: str) -> None:
    """SHAPE 2 WIDENED FROM A BLOCKLIST TOWARDS THE CLASS IT CLAIMED TO BE.

    The rule matched exactly two spellings while claiming a semantic class, and
    a gutter typing any of the four respellings below restored the gutting the
    rule exists to close. Comparisons are normalised before they are decided, so
    the operand order stops mattering.
    """
    survey = _survey(corpus)
    kinds = [finding.kind for finding in survey.vacuous_grading]
    assert kinds == ["cannot discriminate"], f"{why}, and it was not reported: {survey}"


@pytest.mark.parametrize(
    ("expression", "why"),
    [
        ("not (x != x)", "__ne__ is program code, so this is not decided by the language"),
        ("id(x) == id(x)", "trusting the name id is a spelling, not a semantic class"),
    ],
)
def test_the_predicates_this_rule_deliberately_leaves_alone_are_named(
    expression: str, why: str
) -> None:
    """THE BOUNDARY OF SHAPE 2, NAMED RATHER THAN DISCOVERED.

    Widening towards the class is not widening without limit. Both spellings
    below LOOK like the class and are outside it, and each is left alone for a
    reason about meaning rather than about the count it would produce here.
    """
    verdict = liveness.cannot_discriminate(ast.parse(expression, mode="eval").body)
    assert verdict is None, f"{why}, and it was decided anyway as {verdict!r}"


@pytest.mark.parametrize(
    ("corpus", "why"),
    [
        (_WRAPPED_IN_AN_EMPTY_LOOP, "a literal with nothing in it yields nothing"),
        (_WRAPPED_IN_A_ZERO_RANGE, "range(0) yields nothing"),
        (_WRAPPED_IN_WHILE_FALSE, "False is the constant this module already folds"),
    ],
)
def test_a_body_wrapped_in_a_loop_that_never_runs_is_reported(corpus: str, why: str) -> None:
    """THE MODULE CONTRADICTED ITS OWN STATED CLAIM, AND THE LOOP IS WHERE.

    "A STATICALLY CONSTANT BRANCH IS NOT A BRANCH" is the module's own words and
    it folds every ``if`` through :func:`liveness.static_truth`. The loop was
    never folded, so all three spellings below gutted a real shipped control
    while producing no finding, no vacuous assertion and no dead grading - and
    still counted the control as a live member.
    """
    kinds = _kinds(corpus)
    assert "end of function" in kinds, f"{why}, and it was not reported: {_findings(corpus)}"


def test_grading_a_folded_branch_jumps_over_can_never_run() -> None:
    """THE HOLE THAT MADE THE FABRICATED-RETURN RULE LOOK NECESSARY.

    ``if globals(): return 1`` always returns, so every statement after it is
    dead - and the dead-grading walk propagated deadness INSIDE a folded branch
    without propagating it PAST one. Both shapes the withdrawn return rule was
    built for are unreachable grading and are reported as exactly that.
    """
    one = _survey(_FABRICATED_RETURN).dead_grading
    two = _survey(_UNCONDITIONAL_DECLINE).dead_grading
    fabricated = [finding.kind for finding in one]
    declined = [finding.kind for finding in two]
    assert fabricated == ["unreachable grading"], f"got {[f.rendered() for f in one]}"
    assert declined == ["unreachable grading"], f"got {[f.rendered() for f in two]}"


@pytest.mark.parametrize(
    ("corpus", "why"),
    [
        (_GRADES_THE_NON_EMPTY_CASE, "grade the non-empty case, answer either way"),
        (_ORDINARY_LITERAL_EARLY_RETURN, "an early return of a literal on a boundary"),
        (_GRADES_ONLY_IN_STRICT_MODE, "grade only when the caller asked for it"),
    ],
)
def test_an_ordinary_return_beside_conditional_grading_is_not_reported(
    corpus: str, why: str
) -> None:
    """THE COST THAT WITHDREW THE RULE, PAID BY THREE ORDINARY SHAPES.

    Once the dead-grading walk propagates past a folded branch, every case the
    fabricated-return rule caught is reported as unreachable grading - and the
    only thing left that was unique to it is this class, which is one of the
    most ordinary shapes in Python. Withdrawing a rule that adds nothing but
    false positives is the correct outcome for it.
    """
    survey = _survey(corpus)
    rendered = [finding.rendered() for finding in survey.findings]
    assert not rendered, f"{why}, and it was reported: {rendered}"
    assert survey.value_returning, f"{why}, and it left the excluded census entirely"


def test_the_shapes_the_withdrawn_return_rule_reported_do_grade(tmp_path: Path) -> None:
    """THE WARRANT FOR THE THREE FIXTURES ABOVE, WHICH THIS TREE HAS NO MEMBER OF.

    A rule whose false positives are absent from the tree it was written against
    reads as exact, and that is the whole reason this cost went unmeasured. So
    the fixtures are warranted by EXECUTION instead of by a structural analogue:
    each is called and the grading statements that really ran are counted by
    this module's own runtime channel.
    """
    path = _written(tmp_path, "counting.py", _GRADES_THE_NON_EMPTY_CASE)
    module = _load(path, "cs846_counting")
    # SLF001: the fixture's leading underscore is part of the shape under test.
    # A delegated grader in this tree is private by convention, and renaming
    # this one to satisfy a lint would validate the rule against a shape that
    # does not occur.
    census = module._census  # noqa: SLF001
    graded = liveness.observed_grading(census, ["one"])
    idle = liveness.observed_grading(census, [])
    assert graded == 1, (
        f"the shape reported as declining without ever grading ran {graded} grading "
        "statement(s) on a non-empty input, so the report was about a call that grades"
    )
    assert idle == 0, (
        f"the same shape ran {idle} grading statement(s) on an empty input, so the "
        "fixture is not the conditional shape it is claimed to be"
    )


def test_a_failure_logged_instead_of_raised_is_reported() -> None:
    """THE WAY ANYONE ACTUALLY WRITES A SWALLOW.

    The handler test accepted a body only when every statement was ``pass`` or a
    bare constant, so one ``print`` call defeated it. A handler that catches
    what an ``assert`` raises and neither re-raises it, converts it to a
    failure, nor leaves the function has discarded it.
    """
    assert "failure discarded" in _kinds(_SWALLOWED_INTO_A_LOG), (
        f"got {_findings(_SWALLOWED_INTO_A_LOG)}"
    )


def test_a_failure_suppressed_by_a_context_manager_is_reported() -> None:
    """THE SAME SWALLOW WITH NO ``try`` IN IT AT ALL.

    ``contextlib.suppress`` is the standard spelling and the handler test
    inspected ``ast.Try`` only, so this one had nothing to inspect.
    """
    assert "failure discarded" in _kinds(_SUPPRESSED), f"got {_findings(_SUPPRESSED)}"


def test_a_handler_that_converts_a_failure_into_a_record_is_not_reported() -> None:
    """BOUNDARY, AND ITS ANALOGUE IS SHIPPED IN ``tests/save/reach_guard.py``.

    That module catches ``AssertionError`` from a delegated grader and appends
    the rejection to a list its caller then grades. The failure is CONVERTED
    into a value rather than discarded, and a rule that could not tell those
    apart would redden a correct control.
    """
    survey = _survey(_CONVERTED_TO_A_RECORD)
    discarded = [finding.kind for finding in survey.findings if finding.kind == "failure discarded"]
    assert not discarded, f"a converted failure was read as discarded: {survey.findings}"


def test_a_test_disabled_by_an_empty_parametrize_is_reported() -> None:
    """ONE DECORATOR, NO STATEMENT, AND PYTEST REPORTS ``1 passed, 1 skipped``.

    An empty literal argvalues gives the parametrizer nothing to run the body
    with, which is decidable from the decorator exactly as a constant ``skipif``
    condition is. What is NOT decidable is an argvalues built elsewhere and
    named here, and that residual is stated rather than closed.
    """
    kinds = _kinds(_DISABLED_BY_AN_EMPTY_PARAMETRIZE)
    assert any(kind.startswith("disabled by") for kind in kinds), (
        f"got {_findings(_DISABLED_BY_AN_EMPTY_PARAMETRIZE)}"
    )


def test_a_control_renamed_out_of_pytest_collection_is_reported() -> None:
    """THE GUTTING NO RULE OVER THE FUNCTION'S OWN SOURCE CAN SEE.

    The body is untouched, every assertion is intact, and the control is a full
    population member with nothing against it - what changed is whether pytest
    ever calls it. That is a fact about collection rather than about the
    source, so it is decided on a NARROWER ground that is decidable: a
    module-level grader in a test module which pytest will not collect and
    which nothing in the tree names can never run, whoever was meant to call
    it.

    THE COLLECTION PREFIX IS READ FROM THE PROJECT'S OWN pytest CONFIGURATION
    rather than written down here, so a project that changes it changes this
    rule with it instead of silently invalidating it.
    """
    prefixes = liveness.collection_prefixes(Path(__file__).resolve().parents[1])
    orphaned = liveness.uncollected_graders(
        {"tests/test_synthetic.py": _RENAMED_OUT_OF_COLLECTION}, prefixes
    )
    assert [member.name for member in orphaned] == ["not_a_test_gamma"], (
        f"the rename out of collection was not reported: {orphaned}"
    )


def test_a_delegated_grader_a_caller_names_is_not_reported() -> None:
    """BOUNDARY, AND IT IS EVERY DELEGATED GRADER THIS TREE SHIPS.

    pytest collects none of them either. The difference is that something names
    them, and being named is the whole of what separates a helper from a
    control nothing will ever call.
    """
    prefixes = liveness.collection_prefixes(Path(__file__).resolve().parents[1])
    orphaned = liveness.uncollected_graders(
        {"tests/test_synthetic.py": _NAMED_BY_A_CALLER}, prefixes
    )
    assert not orphaned, f"a named delegated grader was reported as unreachable: {orphaned}"


def test_no_shipped_grader_sits_in_a_test_module_that_nothing_will_ever_call(
    repo_root: Path, tracked: list[str]
) -> None:
    """THE COST OF THAT RULE, PAID ON THE REAL TREE.

    Every delegated grader in the suite is a candidate and the great majority
    of them are correct code, so the number that matters is how many are
    CANDIDATES rather than how many are reported. A decorated one is exempted
    with its reason: a decorator can hand a function to a framework that
    reaches it without any name load, which is exactly what a ``pytest.fixture``
    does.
    """
    sources = {relative: (repo_root / relative).read_text(encoding="utf-8") for relative in tracked}
    prefixes = liveness.collection_prefixes(repo_root)
    candidates = liveness.uncollectable_graders(sources, prefixes)
    orphaned = liveness.uncollected_graders(sources, prefixes)
    rendered = [member.rendered() for member in orphaned]
    count = len(rendered)
    population = len(candidates)
    assert prefixes, "no collection prefix was derived, so nothing here knows what pytest runs"
    assert population > 1, (
        f"{population} grader(s) in test modules are outside pytest's collection, so a "
        "clean result here is a claim about nothing"
    )
    assert not count, (
        f"{count} of {population} grader(s) sit in a test module, are not collected by "
        f"pytest and are named nowhere in the tree, so nothing can ever run them: "
        f"{rendered[:20]}"
    )


def test_a_value_returning_grader_that_declines_every_time_is_reported() -> None:
    """SHAPE 4. A decline reached on every call is a stop wearing a decline's clothes.

    :data:`_DECLINING_RETURN` is the legitimate shape and stays legitimate, and
    it is now legitimate for a reason that holds for every ordinary shape like
    it rather than for one the rule happened to spell out. What separates the
    two is not the returned value at all: it is that the grading below an
    UNCONDITIONAL decline can never run, and that is decidable.
    """
    survey = _survey(_UNCONDITIONAL_DECLINE)
    assert [finding.kind for finding in survey.dead_grading] == ["unreachable grading"], (
        f"the unconditional decline was not reported: {survey.dead_grading}"
    )
    assert [member.name for member in survey.value_returning] == ["_census"], (
        "the gutted grader left the excluded census as well, so nothing counts it"
    )


def test_a_grader_renamed_out_of_the_vocabulary_keeps_its_callers_in_the_population() -> None:
    """SHAPE 3. A grading route is a route whatever it is spelled.

    The vocabulary is a naming convention and this is its failure mode: rename
    ``_assert_every_row_balances`` and every caller leaves the population with
    nothing red. The route is resolved from the call graph instead, so the name
    stops deciding membership.
    """
    routes = liveness.grading_routes({"synthetic.py": _RENAMED_GRADER})
    survey = liveness.survey_source("synthetic.py", _RENAMED_GRADER, routes=routes["synthetic.py"])
    named = sorted(member.name for member in survey.members)
    assert named == ["_every_row_balances", "test_tau"], (
        f"the caller of the renamed grader is not in the population: {named}"
    )


def test_a_caller_of_a_renamed_grader_is_graded_once_the_route_is_resolved() -> None:
    """SHAPE 3, and the half that makes it worth resolving at all.

    Membership is not the point; being GRADED is. Without the route the gutted
    caller is invisible because it is not in the population; with it, the same
    walk that grades every other member reports it.
    """
    routes = liveness.grading_routes({"synthetic.py": _RENAMED_GRADER_GUTTED})
    resolved = liveness.survey_source(
        "synthetic.py", _RENAMED_GRADER_GUTTED, routes=routes["synthetic.py"]
    )
    blind = liveness.survey_source("synthetic.py", _RENAMED_GRADER_GUTTED)
    assert [finding.kind for finding in resolved.findings] == ["return"], (
        f"the gutted caller was not reported once its route was resolved: {resolved.findings}"
    )
    assert not blind.findings, (
        "the vocabulary alone already reported this, so the route resolution is not what "
        "closes the shape and this test is not measuring it"
    )


def test_a_renamed_grader_resolves_across_a_file_boundary() -> None:
    """SHAPE 3 AS IT ACTUALLY OCCURS, WHICH IS NOT HOW THE FIXTURE ABOVE WRITES IT.

    THIS TEST EXISTS BECAUSE THE ONE-MODULE FIXTURE PASSED WHILE THE ANALYSIS
    RESOLVED NOTHING IN THE REAL TREE. Returning the names each module DEFINES
    is enough when the grader and its caller sit in the same file, and every
    grader in this tree worth renaming is IMPORTED by the module that calls it,
    so the whole rule was inert where it mattered. Only a plant against a real
    shipped grader reported it.

    So the route set is what a call in a module can REACH, under the local
    spelling, and the boundary is what this grades.
    """
    sources = {"grader.py": _CROSS_MODULE_GRADER, "caller.py": _CROSS_MODULE_CALLER}
    routes = liveness.grading_routes(sources)
    resolved = liveness.survey_source("caller.py", _CROSS_MODULE_CALLER, routes["caller.py"])
    blind = liveness.survey_source("caller.py", _CROSS_MODULE_CALLER)

    assert "_every_row_balances" in routes["caller.py"], (
        f"the imported grader is not callable-as-grading from the module that calls it: "
        f"{sorted(routes['caller.py'])}"
    )
    assert [finding.kind for finding in resolved.findings] == ["return"], (
        f"the gutted caller was not reported across the boundary: {resolved.findings}"
    )
    assert not blind.findings, (
        "the vocabulary alone already reported this, so the cross-module resolution is "
        "not what closes it and this test is not measuring it"
    )


def test_the_grading_vocabulary_is_pinned_by_literal() -> None:
    """SHAPE 3's other half - the vocabulary itself moving without anything red.

    THE PRECEDENT IS ``tests/save/test_byte_order_status.py``. Every control in
    this module selects the vocabulary by SYMBOL, so emptying it or respelling
    a word changes what is graded while every symbol still resolves. The words
    are transcribed here as literals for that reason, and this is the one
    deliberate transcription in the file.
    """
    assert liveness.GRADING_PREFIXES == PINNED_GRADING_PREFIXES, (
        f"the grading prefix vocabulary is now {liveness.GRADING_PREFIXES}. Every control "
        "here selects it by symbol, so narrowing it to nothing empties the population with "
        "every one of them still green. Change this literal together with whatever grades "
        "the new word."
    )
    assert liveness.PYTEST_GRADING_CALLS == PINNED_PYTEST_GRADING_CALLS, (
        f"pytest's grading spellings are now {sorted(liveness.PYTEST_GRADING_CALLS)}; a word "
        "removed here stops being read as grading and every caller of it leaves the "
        "population silently"
    )
    assert liveness.EXITING_CALLS == PINNED_EXITING_CALLS, (
        f"the exiting vocabulary is now {sorted(liveness.EXITING_CALLS)}; a word removed "
        "here stops being read as an exit, so a gutting spelled with it reads as grading"
    )


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


def test_no_shipped_assertion_is_one_that_cannot_discriminate(
    surveyed: liveness.Survey,
) -> None:
    """THE COST OF THE TAUTOLOGY RULES, PAID ON THE REAL TREE.

    This is the census the shape tests above are proven against, and it is the
    number that is disclosed rather than designed around. It grades every
    assert statement in the tree, not only the ones inside the population, so a
    vacuous assertion sitting beside a real one is still reported - the real
    one would otherwise hide it.
    """
    rendered = [finding.rendered() for finding in surveyed.vacuous_grading]
    count = len(rendered)
    candidates = surveyed.asserted
    assert candidates > 1, (
        f"{candidates} assert statement(s) were read, so a clean result here is a claim "
        "about nothing"
    )
    assert not count, (
        f"{count} shipped assertion(s) hold for every possible input, so they execute and "
        f"pass and report nothing: {rendered[:20]}. Compare against an independently "
        f"derived expectation rather than against the same value twice"
    )


def test_every_self_comparison_the_bound_counts_really_compares_something_with_itself(
    repo_root: Path, surveyed: liveness.Survey
) -> None:
    """THE SECOND BOUND, RE-DERIVED AND HELD TO ITS OWN SHAPE.

    NO FLOOR ON THE NUMERATOR, AND THAT IS DELIBERATE. A tree that ships no
    reflexive assertion at all is a tree with nothing for this bound to say,
    not a tree where the bound stopped working - and asserting the count is
    non-zero would make the check require the shape it exists to measure. The
    denominator IS floored: the census must have read assertions to be clean
    about them.

    What is graded instead is that every entry really has the shape, re-read
    from its own source rather than taken from the census that produced it.
    """
    census = surveyed.self_comparisons
    wrong: list[str] = []
    for finding in census:
        tree = ast.parse((repo_root / finding.module).read_text(encoding="utf-8"))
        statement = next(
            (
                item
                for item in ast.walk(tree)
                if isinstance(item, ast.Assert) and item.lineno == finding.line
            ),
            None,
        )
        if statement is None or liveness.self_comparison(statement.test) is None:
            wrong.append(finding.rendered())
    counted = len(census)
    candidates = surveyed.asserted
    assert candidates > 1, (
        f"{candidates} assert statement(s) were read, so this bound is a claim about nothing"
    )
    assert not wrong, (
        f"{len(wrong)} of {counted} entr(ies) in the self-comparison bound do not compare "
        f"anything with itself, so the bound is measuring something else: {wrong}"
    )


def test_the_conditional_exits_this_module_cannot_decide_are_counted_and_bounded(
    repo_root: Path, surveyed: liveness.Survey
) -> None:
    """SHAPE 2, REPORTED RATHER THAN DECIDED, WHICH IS THE HONEST ANSWER FOR IT.

    ``if globals(): pytest.skip(...)`` is folded and reported. ``if not
    corpus: pytest.skip(...)`` is the legitimate idiom every skip in this tree
    uses. ``if _looks_fine(): pytest.skip(...)`` is a gutting and is
    STRUCTURALLY IDENTICAL to the second - no static rule separates them, and
    claiming one does would be the false coverage this item was refuted for
    twice.

    So the set is bounded instead: every member is re-derived, and each is
    re-read to confirm it really is an undecidable condition guarding a real
    exit. What that buys is a number - this is exactly how much of the
    population a gutting could hide in, and it is recomputed rather than
    written down.
    """
    census = surveyed.conditional_exits
    count = len(census)
    wrong: list[str] = []
    for member in census:
        tree = ast.parse((repo_root / member.module).read_text(encoding="utf-8"))
        node = next(item for item in liveness.functions(tree) if item.name == member.name)
        guarded = [
            statement
            for statement in liveness.own_statements(node)
            if isinstance(statement, ast.If)
            and liveness.static_truth(statement.test) is None
            and any(liveness.is_exiting_statement(inner) for inner in statement.body)
        ]
        if not guarded:
            wrong.append(member.rendered())
    assert count, (
        "no member exits behind a condition this module cannot decide, so either the tree "
        "changed shape or this bound stopped being computed - and an uncomputed bound is "
        "the silence the whole item is about"
    )
    assert not wrong, (
        f"{len(wrong)} member(s) are counted against the undecidable-exit bound and carry "
        f"no such exit, so the bound is measuring something else: {wrong}"
    )


def test_every_grader_the_population_filter_excludes_is_counted_and_returns_a_value(
    repo_root: Path, surveyed: liveness.Survey, routes: dict[str, frozenset[str]]
) -> None:
    """The excluded set, re-derived, and each re-read to confirm the excluded shape.

    THE RE-DERIVATION RESOLVES ROUTES TOO, and it has to. A grader that reaches
    its grading through a call rather than through an ``assert`` of its own is
    in this set for a reason the vocabulary alone cannot see, so re-deriving
    without the routes would report it as the wrong shape - which is the same
    census disagreeing with itself about what it derived.
    """
    excluded = surveyed.value_returning
    count = len(excluded)
    wrong: list[str] = []
    for member in excluded:
        tree = ast.parse((repo_root / member.module).read_text(encoding="utf-8"))
        node = next(item for item in liveness.functions(tree) if item.name == member.name)
        resolved = routes.get(member.module, frozenset())
        if not liveness.returns_a_value(node) or not liveness.ships_a_grading_statement(
            node, resolved
        ):
            wrong.append(member.rendered())
    assert count, (
        "the population filter excluded nothing, so it is either inert or the census "
        "stopped being computed"
    )
    assert not wrong, f"{len(wrong)} excluded function(s) do not have the excluded shape: {wrong}"


def test_the_resolved_routes_recover_only_functions_that_really_reach_grading(
    repo_root: Path, tracked: list[str], routes: dict[str, frozenset[str]]
) -> None:
    """THE COST OF THE ROUTE RULE, AND THERE IS NO FLOOR UNDER IT ON PURPOSE.

    Every name a route recovers is re-read here and has to either grade
    directly or call something in the same resolved set. Nothing asserts that
    the recovered set is NON-empty, and that omission is deliberate: a tree
    where every grader is spelled ``assert_...`` recovers nothing and is a tree
    with none of this defect in it. A floor here would make the check require
    the defect it exists to find.
    """
    sources = {relative: (repo_root / relative).read_text(encoding="utf-8") for relative in tracked}
    defined: dict[str, set[str]] = {}
    for relative, text in sources.items():
        module = relative.removesuffix(".py").replace("/", ".")
        defined[module] = {
            node.name
            for node in ast.parse(text).body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        }

    recovered = 0
    wrong: list[str] = []
    for relative in tracked:
        resolved = routes[relative]
        tree = ast.parse(sources[relative])
        brought_in = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module in defined and not node.level
            for alias in node.names
        }
        for name in sorted(resolved):
            node = liveness.module_function(sources[relative], name)
            if node is None:
                if name not in brought_in:
                    wrong.append(f"{relative}::{name} is neither defined here nor imported")
                continue
            if liveness.ships_a_grading_statement(node):
                continue
            recovered += 1
            if not liveness.ships_a_grading_statement(node, resolved):
                wrong.append(f"{relative}::{name} reaches no grading by any route")
    count = len(wrong)
    assert not count, (
        f"{count} of {recovered} recovered route(s) reach no grading at all, so the "
        f"resolution is crediting grading that never happens: {wrong[:20]}"
    )


def test_resolving_routes_only_ever_widens_the_population(
    repo_root: Path, tracked: list[str], surveyed: liveness.Survey
) -> None:
    """THE ROUTE RULE'S LIVE EFFECT, DERIVED HERE AND ALLOWED TO BE ZERO.

    THE FLOOR THAT WAS MISSING. The check beside this one re-reads every name
    the resolution recovers, and its own denominator is whatever the tree
    happens to offer - which on a tree where every grader is spelled
    ``assert_...`` is nothing at all. That is not a defect in the rule and a
    floor on the numerator would make the check require the very defect it
    exists to find, so what is graded here is the DIRECTION instead.

    Resolving a route may only ever ADD a member: it credits a call that
    reaches grading and it withdraws nothing. A member that LEAVES the
    population once routes are resolved means resolution is shadowing a name
    rather than following it, and that is a real failure mode with a real
    signal. The count it adds is derived beside it and is not asserted.
    """
    blind: set[tuple[str, str]] = set()
    for relative in tracked:
        tree = ast.parse((repo_root / relative).read_text(encoding="utf-8"))
        blind |= {
            (relative, node.name)
            for node in liveness.functions(tree)
            if liveness.is_population_member(node)
        }
    resolved = {(member.module, member.name) for member in surveyed.members}
    lost = sorted(f"{module}::{name}" for module, name in blind - resolved)
    added = len(resolved - blind)
    assert blind, (
        "the shipped vocabulary alone derives no member at all, so comparing the two "
        "derivations has nothing to discriminate"
    )
    assert not lost, (
        f"{len(lost)} member(s) LEFT the population once routes were resolved, so the "
        f"resolution is narrowing it rather than widening it - it added {added} and "
        f"lost these: {lost[:20]}"
    )


def test_every_detector_module_is_reached_from_the_graded_population(
    repo_root: Path, tracked: list[str]
) -> None:
    """THE HALF OF THE ACCEPTANCE NEITHER POPULATION REACHED.

    A DETECTOR LIBRARY SHIPS NO ASSERTION OF ITS OWN, so it contributes no
    member; it is not named ``test_``, so no test population holds it; it ships
    no ``guard_`` function in a tool directory, so the guard half does not
    derive it. This module is one, and so are the two rendering guards beside
    it - together they fall through every filter while being exactly the kind of
    thing the acceptance means by a shipped guard.

    THE POPULATION IS DERIVED RATHER THAN LISTED, because a fourth such module
    will arrive and a hand-maintained list is the thing this repository keeps
    recording as the thing that rots. A detector grades nothing by itself; it is
    covered exactly when something that IS graded calls into it, and a detector
    nothing graded calls is a detector nothing grades.
    """
    sources = {relative: (repo_root / relative).read_text(encoding="utf-8") for relative in tracked}
    coverage = liveness.detector_coverage(sources)
    unreached = sorted(module for module, callers in coverage.items() if not callers)
    derived = len(coverage)
    assert derived, (
        "no detector module was derived at all, so either the tree changed shape or this "
        "derivation stopped running - and an underived population is the silence the "
        "whole item is about"
    )
    assert not unreached, (
        f"{len(unreached)} of {derived} detector module(s) are called by no graded member, "
        f"so nothing in the suite grades whether they still detect anything: {unreached}"
    )


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


# ---------------------------------------------------------------------------
# SHAPE 5 - WHETHER AN ASSERTION ACTUALLY RAN. Everything above this line is
# static, and no amount of static analysis answers this question: the shapes
# above are the ones a reader can name, and execution is what actually happened.
#
# WHAT IS DELIVERED AND WHAT IS NOT. The channel exists, it is exact, and it is
# demonstrated below on a REAL SHIPPED GRADER rather than only on a fixture.
# What is NOT delivered is the channel applied to the whole population: doing
# that means counting during the suite's own run, which is a collection hook in
# tests/conftest.py, and that file is not this slice's to write. So this is a
# mechanism plus one real member, and the population remains covered statically
# only. Saying that plainly is the point - an unstated residual here is the
# exact defect the item is about.
# ---------------------------------------------------------------------------

#: DERIVED FROM ``_assert_no_test_is_gutted`` ITSELF, which is a real shipped
#: grader with exactly this shape: read something, grade it, derive again,
#: grade that. Two grading statements at the top level and no loop.
_RUNTIME_GRADER = "\n".join(
    [
        '"""A stand-in grader with the shape of a real one."""',
        "",
        "",
        "def check(rows):",
        '    """Grade a list of rows twice, as the real grader does."""',
        '    assert rows, "no rows, so this guard is vacuous"',
        "    bad = [row for row in rows if row < 0]",
        '    assert not bad, f"negative rows: {len(bad)}"',
        "",
    ]
)

#: The same grader with the gutting this whole item is about. It is STILL a
#: valid call and it STILL returns without complaint.
_RUNTIME_GRADER_GUTTED = _RUNTIME_GRADER.replace(
    '    assert rows, "no rows, so this guard is vacuous"',
    "    if rows:\n        return\n    assert rows",
)


def test_the_runtime_channel_counts_the_grading_that_actually_ran(tmp_path: Path) -> None:
    """The mechanism, on a module whose gutting is the only difference.

    Both modules are written, loaded and CALLED. The live one runs both of its
    grading statements; the gutted one runs neither and returns normally, which
    is precisely the pair of outcomes every static rule in this file exists to
    tell apart from the outside.
    """
    live = _load(_written(tmp_path, "live.py", _RUNTIME_GRADER), "cs846_runtime_live")
    gutted = _load(_written(tmp_path, "gutted.py", _RUNTIME_GRADER_GUTTED), "cs846_runtime_gutted")

    shipped = len(liveness.grading_statement_lines(live.check))
    ran = liveness.observed_grading(live.check, [1, 2, 3])
    silent = liveness.observed_grading(gutted.check, [1, 2, 3])

    assert shipped > 1, f"the live grader was read as shipping {shipped} grading statement(s)"
    assert ran == shipped, f"the live grader ran {ran} of its {shipped} grading statements"
    assert silent == 0, (
        f"the gutted grader ran {silent} grading statement(s); it returns without "
        "complaint either way, so the count is the only thing that separates them"
    )


def test_a_real_shipped_grader_is_observed_grading_when_it_is_called() -> None:
    """THE ONE REAL MEMBER, and it is deliberately not a fixture.

    ``_assert_no_test_is_gutted`` ships, is called by this file's own fourth
    consumer, and takes an argument this file can supply. Running it under the
    counter answers the question no static rule here can: its assertions did
    not merely exist, they EXECUTED, and the count matches what the source
    says it should be.
    """
    static = liveness.grading_statement_lines(_assert_no_test_is_gutted)
    expected = len(static)
    observed = liveness.observed_grading(_assert_no_test_is_gutted, Path(__file__))
    assert expected > 1, (
        f"{OPT_IN_HELPER} was read as shipping {expected} grading statement(s), so the "
        "count below is a claim about nothing"
    )
    assert observed == expected, (
        f"{OPT_IN_HELPER} ships {expected} grading statement(s) and {observed} of them ran. "
        "The source says it grades and the execution says otherwise"
    )


def test_the_runtime_counter_leaves_no_trace_function_behind(tmp_path: Path) -> None:
    """A counter that leaked its hook would poison every later test in the session.

    The same discipline this project applies to a planted mutation: assert the
    revert landed. The hook is installed globally and restored in a ``finally``,
    and this is what checks the restore rather than trusting it.
    """
    live = _load(_written(tmp_path, "restore.py", _RUNTIME_GRADER), "cs846_runtime_restore")
    before = sys.gettrace()
    liveness.observed_grading(live.check, [1])
    assert sys.gettrace() is before, (
        "the runtime counter left its trace hook installed, so every frame entered after "
        "it would be traced by a hook nothing owns"
    )

    with pytest.raises(AssertionError):
        liveness.observed_grading(live.check, [])
    assert sys.gettrace() is before, (
        "the trace hook survived a call that raised, so a single failing grader would "
        "leave it installed for the rest of the session"
    )
