#!/usr/bin/env python3
"""CS-846 - is a shipped control still grading, and is a shipped guard still guarding?

THE DEFECT. A control that stops grading still reports as passed, and a guard
that stops guarding still answers PASS. Nothing distinguishes graded-and-held
from stopped-before-grading. It is the same shape as this project's standing
finding about mutation testing, where a mutant that never applied and one that
survived produce identical output: the ABSENCE of a signal is being read as the
PRESENCE of a negative result.

THIS MODULE HAS BEEN REFUTED TWICE AND BOTH REFUTATIONS ARE WRITTEN INTO IT.

The first keyed the analysis on ``ast.Return``, and almost every member of this
tree carries no return statement at all - so for almost the whole population
the analysis could not report anything. The unit is now the EXIT, and the
implicit end-of-function exit counts as one.

The second found something worse: the rules had been chosen BY THEIR
FALSE-POSITIVE COUNT ON THIS TREE. The ``match`` arm returned the incoming
verdict, which is wrong for every ``match`` statement ever written - and scored
zero only because this tree contains no ``match`` statement at all. A rule
selected because it scores zero today encodes today's tree as its passing
condition. Every rule below is now stated as a SEMANTIC claim, and the cost of
each is measured and reported rather than used to pick it.

THE SEMANTIC CLAIMS, in the order they matter.

  A GUARDED FAILURE IS AN ASSERTION. ``if bad: pytest.fail(...)`` and ``assert
  not bad`` are the same test written twice, and so are ``except E:
  pytest.fail(...)`` and "this must not raise E". Reaching the code after a
  construct whose other path FAILS is itself the graded fact. An analysis that
  accepts one spelling and rejects the other is grading style, not liveness.

  AN ASSERTION THAT HOLDS FOR EVERY INPUT GRADES NOTHING. ``assert True``
  executes, passes, and asserts nothing about the program. Neither does
  ``assert x is x``, nor ``assert len(x) >= 0``: they are not constants, so a
  constant fold misses them, and they are exactly as vacuous. None of them may
  count as a grading statement, or eleven characters restore any gutting the
  rest of this module closes. :func:`cannot_discriminate` owns the sub-classes
  that are DECIDABLE and names the ones that are not - the identity this
  repository actually shipped was algebraic over values built in another
  function, and no rule over an assertion's own syntax reaches that.

  AND THE SAME SENTENCE READ STRICTLY IS WHAT NARROWED THAT RULE. ``x == x``,
  ``x >= x`` and ``x.a is x.a`` do NOT hold for every input: ``__eq__``,
  ``__ge__`` and ``__getattr__`` are program code, so each genuinely fails
  against a broken one, and each is the standard idiom for testing exactly
  that. They are counted by :func:`self_comparison` rather than decided, on
  the same ground the undecidable exits are counted rather than decided.

  A STATICALLY CONSTANT BRANCH IS NOT A BRANCH, AND A LOOP THAT CANNOT RUN IS
  NOT A LOOP. ``if not globals():`` never runs its body and ``if globals():``
  always does. Folding both is what makes the difference between a CONDITIONAL
  skip - the legitimate idiom, which this tree uses in every skip it ships -
  and a skip written to look conditional. The asymmetry is positional and
  decidable, not a matter of judgement, and ``for _ in []:``, ``for _ in
  range(0):`` and ``while False:`` are the same claim about a loop -
  :func:`never_iterates` decides them, because a module that folded one and not
  the other was contradicting itself in silence.

  A CONSTANT BRANCH THAT ALWAYS LEAVES MAKES EVERYTHING BELOW IT DEAD. That is
  one sentence and it replaced a whole second rule. ``if globals(): return 1``
  always returns, so the grading after it can never run - and reading that as a
  question about the RETURNED VALUE instead reported every ordinary
  ``if kind == "info": return 0``. :func:`always_leaves` decides reachability
  and :func:`dead_grading` reports it; there is no separate rule about what a
  grader hands back, because everything such a rule caught it caught twice and
  everything else it caught was correct code.

  AN EXIT IS AN EXIT WHATEVER IT IS SPELLED. ``return``, falling off the end,
  ``pytest.skip(...)``, ``raise pytest.skip.Exception(...)`` and an
  unconditional ``@pytest.mark.skip`` decorator all leave the function without
  grading. The decorator is the one anybody actually uses to disable a test and
  it is not a statement at all, so ``decorator_list`` is read too.

  A GRADER IS NOT A NAMING CONVENTION, AND A ROUTE IS RESOLVED RATHER THAN
  SPELLED. This module reads a call as grading when the name begins with
  ``assert`` or is one of pytest's own spellings. Widening that to ``require``,
  ``check``, ``verify``, ``ensure`` and ``confirm`` was TRIED AND MEASURED:
  everything it adds is a save-library parser named ``int32`` or ``string``, or
  a dispatcher like ``check_content`` that routes to other checks - NOT ONE IS
  A TEST - and the findings it produced were all false positives, some inside a
  frozen file. In this tree those verbs name parsers; ``assert`` names graders.

  So the vocabulary stays narrow on a semantic ground, and the hole it leaves
  is closed from the other side rather than described. :func:`grading_routes`
  resolves a call against the functions the surveyed modules actually DEFINE,
  so a grader renamed out of every vocabulary keeps its callers in the
  population - the route did not move, only the spelling did. What that cannot
  resolve is named where it lives: a method call, an alias, a call through a
  variable, a call into a module nobody surveyed. :func:`vocabulary_boundary`
  still re-derives the naming difference every run beside it, and the
  vocabulary itself is pinned by literal from the test module, because every
  control here selects it by SYMBOL and none of them could see it change.

WHERE THE ANALYSIS IS DELIBERATELY GENEROUS, and the cost is a number this
module recomputes rather than a sentence. A loop may run zero times and a
``try`` body may raise partway, so strictly neither guarantees anything to the
exit after it. Read strictly, this tree reports a large set of correct
idiomatic bodies of the form ``for node in walk(tree): if isinstance(...):
assert ...``. The generosity is taken - a loop grades if its body carries
grading, a ``try`` grades if its body ends graded or a handler fails - and
every member that leans on either is COUNTED and re-derived by :func:`survey`.

WHAT IS IN THE POPULATION. A member is a function that REACHES A GRADING
STATEMENT and RETURNS NO VALUE. The first half is the derivation the acceptance
asks for. The second keeps out utilities that carry a sanity assert on the way
to a value - and they are NOT dropped: they are counted, and they are graded by
the rule that is decidable for them, that grading which can never run is
grading that grades nothing.

AND TWO POPULATIONS FALL OUTSIDE BOTH HALVES, so both are derived beside them.
A DETECTOR LIBRARY ships no assertion at all, is not named ``test_`` and holds
no ``guard_`` function in a tool directory, so every filter above misses it -
this module is one. :func:`detector_coverage` derives them and asks the only
liveness question available: does anything GRADED call into it? A CONTROL
RENAMED OUT OF PYTEST'S COLLECTION keeps every assertion it had and stops being
run, which no rule over its own source can see;
:func:`uncollected_graders` decides the narrower question that is decidable,
whether anything in the tree names it at all.

EVERY RULE ABOVE IS STATIC, AND STATIC IS NOT ENOUGH. A gutting whose condition
cannot be read at parse time is indistinguishable from a precondition, and no
amount of care about the source changes that - so it is BOUNDED by
:func:`conditional_exits` rather than claimed. The only thing that decides it
is running the code: :func:`observed_grading` counts the grading statements
that ACTUALLY EXECUTED in one call, which is the exact question every rule here
is a proxy for. It is a mechanism plus whatever a caller hands it, NOT a sweep
of the population, and the reason is written where it is defined. The gap
between "this function's assertions ran" and "the population's assertions ran"
is this module's largest remaining residual and it is stated rather than
narrowed by wording.

THE GUARD HALF IS A DIFFERENT MECHANISM BECAUSE GUARDS GRADE DIFFERENTLY. A
``guard_`` function does not assert; it RETURNS a status, and PASS is its
correct answer nearly always. Three criteria are applied, and each exists
because the one before it was defeated.

  - NOT SILENTLY GREEN about a tree it could not read (CONVENTIONS.md section
    15.1). Defeated by fabricating a skip record.
  - THE ANSWER DEPENDS ON THE TREE, compared across three materially different
    ones. Defeated by echoing the root into the detail while reading nothing.
  - IT CAN BE FORCED TO A NON-PASS VERDICT BY A KNOWN-BAD TREE. This is the
    only one of the three that is a property of GUARDING rather than a proxy
    for it: a guard that cannot be made to fail is not guarding, whatever it
    renders.
"""

from __future__ import annotations

import ast
import inspect
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import Any, Final, NamedTuple

#: The verb prefix a delegated grader is spelled with here. The leading
#: underscore is stripped first, so a private grader is not read as a different
#: kind of thing.
#:
#: WIDENING THIS WAS TRIED AND MEASURED, and the measurement is the reason it
#: is narrow. Adding ``require``, ``check``, ``verify``, ``ensure`` and
#: ``confirm`` pulls in save-library parsers named ``int32``, ``string`` and
#: ``skip``, and dispatchers like ``check_content`` which routes to other
#: checks and returns early when there is nothing to route. NOT ONE OF THE
#: ADDITIONS IS A TEST, and the findings it produced were all false positives,
#: some of them inside a frozen file. In this tree those verbs name parsers
#: and dispatchers; ``assert`` names graders. That is a statement about what
#: the words MEAN here, not about what scores best - the live count is
#: reported by :func:`vocabulary_boundary` rather than written down.
#:
#: The residual it leaves is real and is graded rather than described:
#: :func:`vocabulary_boundary` re-derives the difference every run, and a
#: grader renamed out of this vocabulary drops its callers out of the
#: population, which is exactly what that census reports.
GRADING_PREFIXES: Final = ("assert",)

#: The wider set, kept only to MEASURE the boundary the narrow one leaves.
WIDER_GRADING_PREFIXES: Final = (
    "assert",
    "require",
    "check",
    "verify",
    "ensure",
    "confirm",
)

#: pytest's own grading spellings. ``fail`` is the unconditional one; ``raises``
#: and ``warns`` are the context-manager ones.
#:
#: PUBLIC BECAUSE IT IS PINNED BY LITERAL from the test module, on the
#: precedent of ``tests/save/test_byte_order_status.py``. Every control here
#: selects this set by SYMBOL, so removing a word from it silently stops a
#: whole spelling of grading from being read as grading, with every one of
#: those controls still green.
PYTEST_GRADING_CALLS: Final = frozenset({"fail", "raises", "warns"})

#: Calls that LEAVE the function by raising, rather than by failing.
EXITING_CALLS: Final = frozenset({"skip", "xfail", "exit"})

#: Zero-argument builtins whose result is always truthy. Folding these is what
#: separates a real conditional from one written to look like one.
_ALWAYS_TRUTHY_CALLS: Final = frozenset({"globals", "locals", "object", "dict", "vars"})

#: Comparison operators under which an expression is normally expected to
#: compare equal to ITSELF. Membership here is a claim about what the operator
#: is FOR, not about what it is guaranteed to answer - every one of these but
#: ``is`` dispatches to a method the program under test may define.
_REFLEXIVE_OPS: Final = (ast.Eq, ast.GtE, ast.LtE, ast.Is)

#: The one comparison Python NEVER dispatches to program code. ``is`` compares
#: identity, cannot be overloaded on any type, and is the only member of
#: :data:`_REFLEXIVE_OPS` whose answer no ``__eq__``, ``__ge__`` or ``__le__``
#: can change.
_DECIDED_OPS: Final = (ast.Is,)

#: THE BUILTIN NAMES THIS MODULE TRUSTS BY SPELLING. Every predicate rule below
#: reads one of these names and assumes it is the builtin of that name; a module
#: that rebinds one defeats the rule that reads it, and no analysis of a call
#: site can tell. Declaring them is the honest half of claiming a semantic
#: class: the CLASS is what the language guarantees, the SPELLINGS are how this
#: module recognises members of it, and the two are not the same thing.
_MEASURES: Final = "len"
_TESTS_TYPE: Final = "isinstance"
_ROOT_TYPE: Final = "object"
_COUNTS: Final = "range"

#: BUILT FROM the four above rather than restating them, so the census and the
#: rules cannot disagree about what is trusted. A set written out separately
#: would be exactly the blocklist-behind-a-semantic-claim this module was
#: widened away from, one level up.
TRUSTED_BUILTINS: Final = frozenset({_MEASURES, _TESTS_TYPE, _ROOT_TYPE, _COUNTS})

#: Mirror image of each comparison operator, used to normalise an operand order
#: away before a predicate is decided. ``0 <= len(x)`` and ``len(x) >= 0`` are
#: one predicate written twice, and a rule that reads only one spelling is a
#: blocklist wearing a semantic class's clothes.
_MIRRORED_OPS: Final = {
    ast.Lt: ast.Gt,
    ast.LtE: ast.GtE,
    ast.Gt: ast.Lt,
    ast.GtE: ast.LtE,
    ast.Eq: ast.Eq,
    ast.NotEq: ast.NotEq,
}

#: Floors ``len()`` cannot go below, as ``(operator, bound)``. ``__len__`` must
#: return a non-negative integer or the interpreter raises, so a length is
#: ``>= 0`` and is ``> -1``, and neither reads its input.
_LENGTH_FLOORS: Final = ((ast.GtE, 0), (ast.Gt, -1))

#: Exception names that CATCH what a failed ``assert`` raises. A handler naming
#: any of these stands between an assertion's failure and the caller; one naming
#: something else does not, and reading every handler as a swallow was a false
#: positive class of its own.
_ASSERTION_CATCHERS: Final = frozenset({"AssertionError", "Exception", "BaseException"})

#: How a context manager that discards an exception is spelled.
_SUPPRESSING_CALL: Final = "suppress"

#: The mark that runs a test once per argument set, and runs it zero times when
#: handed none.
_PARAMETRIZING_MARK: Final = "parametrize"

#: How many arguments ``parametrize`` takes before its argument set can be read.
_PARAMETRIZE_ARGS: Final = 2

#: Where the suite lives (CLAUDE.md section 2.1). Read to derive which modules
#: are detector libraries rather than controls; never written.
TEST_DIRECTORY: Final = "tests"

#: What pytest collects a function under when a project says nothing. Used only
#: as the fallback for :func:`collection_prefixes`, which reads the project's
#: own configuration first.
_DEFAULT_COLLECTED: Final = ("test",)

#: Modules in the suite that are NOT detector libraries, with the reason each
#: is exempt written where :func:`detector_modules` explains it. ``__init__``
#: declares a package; ``conftest`` is reached by pytest's own convention -
#: fixtures by parameter name and hooks by hook name - so "does a graded member
#: call into it" is the wrong question about it rather than a question it
#: happens to answer well.
_NOT_A_DETECTOR: Final = frozenset({"__init__.py", "conftest.py"})

#: Marks that disable a test outright when applied with no runtime condition.
_DISABLING_MARKS: Final = frozenset({"skip", "xfail"})

#: The mark that disables a test only when its condition holds.
_CONDITIONAL_MARK: Final = "skipif"

#: Exception names that mean "leave without failing" when raised directly.
_EXITING_EXCEPTIONS: Final = frozenset({"Skipped", "XFailed"})

#: How many dotted parts a qualified name needs before its tail means anything.
_QUALIFIED_PARTS: Final = 2

#: How many arguments ``isinstance`` takes before its second one can be read.
_ISINSTANCE_ARGS: Final = 2

#: What ``sys.settrace`` accepts and what a tracer hands back: either the local
#: tracer to keep using for that frame, or None to stop tracing it. Spelled
#: here because it is recursive and typeshed keeps its own name private.
type _Tracer = Callable[[FrameType, str, Any], _Tracer | None]

#: The name a blind read reports having failed on. It is a literal that appears
#: nowhere else in the tree, so a test asserting its absence from guard output
#: is asserting about the injected value and not about a coincidence.
INJECTED_FILENAME: Final = "cs846-blind-read-target"

#: Where CLAUDE.md section 2.1 says gates and guards live. The DIRECTORIES are
#: named because the topology table names them; the modules inside them and the
#: guards inside those are derived. A bare ``guard_`` prefix match over the
#: whole tree would also catch test helpers called ``guard_of``, so the
#: directory is what separates a shipped guard from a fixture that reads one.
TOOL_DIRECTORIES: Final = ("tools", "scripts")

#: Where the authoritative blocking hooks live (CLAUDE.md section 2.2). Read to
#: derive which tools stand in a blocking position; never written.
HOOK_DIRECTORY: Final = ".githooks"

#: How a tool is spelled inside a hook script.
_TOOL_REFERENCE: Final = re.compile(r"(?:tools|scripts)/[A-Za-z0-9_]+\.py")


class Member(NamedTuple):
    """One derived population member."""

    module: str
    name: str
    line: int

    def rendered(self) -> str:
        """Render as a file:line pointer.

        Returns:
            ``module:line name``.
        """
        return f"{self.module}:{self.line} {self.name}"


class Finding(NamedTuple):
    """One way a member can stop grading without anything noticing."""

    module: str
    name: str
    line: int
    kind: str

    def rendered(self) -> str:
        """Render as a file:line pointer naming the kind of exit.

        Returns:
            ``module:line name (kind)``.
        """
        return f"{self.module}:{self.line} {self.name} ({self.kind})"


class Survey(NamedTuple):
    """Everything one pass over a set of modules derived.

    Attributes:
        members: The population.
        findings: Hard findings - a member that can stop grading.
        loop_leaned: Members whose exit is graded only because a loop body
            carries the grading. Counted, not failed.
        try_leaned: Members whose exit is graded only because a ``try`` does.
            Counted, not failed.
        value_returning: Graders the population filter excludes because they
            return a value. Counted, and graded for UNREACHABLE grading like
            every other function - the walk's exit rules are not applied to
            them, because a boundary return of a computed value is legitimate
            and is not distinguishable from a gutting.
        dead_grading: Grading statements that can never run. Hard.
        outside: Tests shipping no grading statement at all, split into those
            that at least call something and those that do not.
        vocabulary_boundary: Functions a WIDER grading vocabulary would call
            graders and the shipped one does not. Counted, not failed - except
            that a ``test_`` function in here has no grading route this module
            can see, which is.
        modules: What was read.
        vacuous_grading: Assertions that hold for every possible input. Hard,
            and derived over EVERY function rather than over the population, so
            one sitting beside a real assertion is still reported.
        conditional_exits: Members that leave behind a condition this module
            cannot decide. THE BOUND ON THE UNDECIDABLE SHAPE, not a finding -
            a gutting written this way is structurally identical to the
            legitimate idiom, so what is delivered is how much of the
            population it could hide in.
        asserted: How many ``assert`` statements were read at all. The
            denominator under ``vacuous_grading``, so a clean census cannot be
            clean because nothing was looked at.
        self_comparisons: Assertions comparing one expression with ITSELF under
            an operator the program can define. THE SECOND BOUND, not a
            finding - see :func:`self_comparison`. Counted, and credited as
            grading, because such an assertion really can fail.
    """

    members: list[Member]
    findings: list[Finding]
    loop_leaned: list[Member]
    try_leaned: list[Member]
    value_returning: list[Member]
    dead_grading: list[Finding]
    outside: tuple[list[Member], list[Member]]
    vocabulary_boundary: list[Member]
    modules: list[str]
    vacuous_grading: list[Finding]
    conditional_exits: list[Member]
    asserted: int
    self_comparisons: list[Finding]


class GuardAnswer(NamedTuple):
    """What one guard said about one tree."""

    function: str
    guard_id: str
    status: str
    skips: int
    rendered: str

    def signature(self) -> str:
        """Everything the guard said, as one comparable string.

        Returns:
            Status, skip count and every rendered line.
        """
        return f"{self.status}|{self.skips}|{self.rendered}"


# ---------------------------------------------------------------------------
# Static truth - the fold that separates a branch from a costume
# ---------------------------------------------------------------------------


def static_truth(node: ast.expr) -> bool | None:
    """The truth value of an expression, when it has one at parse time.

    A constant branch is not a branch, and deciding that is what tells a
    CONDITIONAL skip - the idiom every skip this tree ships uses - from one
    written to look conditional. Anything not decidable returns None, which is
    the honest answer and the common one.

    Args:
        node: Any expression.

    Returns:
        True, False, or None when it cannot be decided.
    """
    literal = _literal_truth(node)
    if literal is not None:
        return literal
    operator = _operator_truth(node)
    if operator is not None:
        return operator
    always = (
        isinstance(node, ast.Call)
        and not node.args
        and not node.keywords
        and _called_name(node) in _ALWAYS_TRUTHY_CALLS
    )
    return True if always else None


def _literal_truth(node: ast.expr) -> bool | None:
    """The truth value of a literal, if the node is one.

    Args:
        node: Any expression.

    Returns:
        True, False, or None when the node is not a literal.
    """
    if isinstance(node, ast.Constant):
        return bool(node.value)
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return bool(node.elts)
    return bool(node.keys) if isinstance(node, ast.Dict) else None


def _operator_truth(node: ast.expr) -> bool | None:
    """The truth value of a boolean operator over decidable operands.

    Args:
        node: Any expression.

    Returns:
        True, False, or None when it cannot be decided.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = static_truth(node.operand)
        return None if inner is None else not inner
    if not isinstance(node, ast.BoolOp):
        return None
    values = [static_truth(value) for value in node.values]
    if any(value is None for value in values):
        return None
    return all(values) if isinstance(node.op, ast.And) else any(values)


# ---------------------------------------------------------------------------
# The grading vocabulary
# ---------------------------------------------------------------------------


def _called_name(node: ast.expr) -> str | None:
    """The bare name a call expression names, if it is a call at all.

    Args:
        node: Any expression.

    Returns:
        The attribute or name being called, or None.
    """
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _dotted(node: ast.expr) -> str:
    """Render an attribute chain as a dotted name.

    Args:
        node: An expression.

    Returns:
        ``a.b.c`` where it can be read, else "".
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    return ""


def cannot_discriminate(node: ast.expr) -> str | None:
    """Why an asserted expression can never report a defect, when it cannot.

    A NON-CONSTANT TAUTOLOGY IS THE SHAPE THIS REPOSITORY ACTUALLY SHIPPED. The
    one it removed asserted that the two parts of a census added back up to the
    census, which is true of every possible input; ``assert True`` was already
    excluded and this is the same ground one step further out. An assertion
    that holds for every input executes, passes, and reports nothing - it is
    ``assert True`` with more characters.

    THE SUB-CLASSES BELOW ARE DECIDABLE AND ARE NOT THE WHOLE SHAPE. Each is a
    claim about what the language guarantees, so each stays true on a tree that
    has none of them:

      - A LOCAL COMPARED WITH ITSELF BY ``is``. Identity is the one comparison
        Python never dispatches to program code, and a bare ``Name`` load runs
        none either, so both sides are the same object and nothing the program
        does can change the answer.
      - ``len(x) >= 0`` holds because the language requires ``__len__`` to
        return a non-negative integer. The input is not read. So does every
        respelling of the same floor - :func:`_language_decided` normalises the
        operand order away first.
      - ``isinstance(x, object)`` holds because ``object`` is the root of the
        type hierarchy, and a tuple of target types passes when ANY of them
        matches. The first argument is not read either.
      - ``x in (x,)`` holds because container membership tests identity before
        equality, so it is true even for a value that is not equal to itself.

    WHAT WAS IN THIS RULE AND IS NOT ANY MORE, BECAUSE THE STATED GROUND WAS
    FALSE FOR IT. ``==``, ``>=`` and ``<=`` between an expression and itself
    were read here as decided by the operator's reflexivity. They are not: each
    dispatches to a method the program under test may define, so
    ``assert version >= version`` genuinely fails against a broken ``__ge__``
    and is the standard idiom for testing that it is sound. So is
    ``assert parser.parsed is parser.parsed`` against a removed
    ``functools.cached_property`` - the attribute access runs ``__get__``, and
    an attribute access is not an ``ast.Call``. All of those move to
    :func:`self_comparison`, which COUNTS them rather than deciding them.

    THE COST OF THAT NARROWING IS REAL AND IS NOT ARGUED AWAY. ``assert x == x``
    is a vacuity this rule no longer reports and no longer refuses to credit as
    grading. What replaces the refusal is the bound, which is re-derived every
    run.

    WHAT IS NOT REACHED, and it is the more important half. The identity this
    repository actually shipped was ALGEBRAIC and its operands were built in
    another function, so no analysis of this assertion's own syntax reaches it.
    Nor is a bound that its own construction makes unexceedable. Those stay
    open, and :func:`observed_grading` is the only channel in this module that
    could ever answer them.

    Args:
        node: The expression an ``assert`` statement tests.

    Returns:
        A description of why it cannot discriminate, or None when it can.
    """
    if static_truth(node) is True:
        return "a statically true test"
    if _identity_with_itself(node):
        return "a local compared with itself by identity"
    return _language_decided(node)


def _identity_with_itself(node: ast.expr) -> bool:
    """Whether an expression is one local compared with itself by ``is``.

    BOTH HALVES ARE LOAD-BEARING AND EACH CLOSES A DEMONSTRATED FALSE POSITIVE.
    The operator must be ``is``, because ``==``, ``>=`` and ``<=`` all dispatch
    to program code and each is the standard idiom for testing that that code is
    sound. Both operands must be a bare ``Name``, because an attribute access
    runs ``__get__`` or ``__getattr__`` and a subscription runs ``__getitem__``
    - neither is an ``ast.Call`` node and both are arbitrary program code, so
    ``parser.parsed is parser.parsed`` really does fail when the memoization it
    tests is removed.

    NO INLINING OF LOCALS IS DONE, and that is a decision rather than an
    omission. Rewriting a name into its single assignment before comparing
    turns this project's own mutation discipline - bind the original, patch,
    restore, then assert the restore landed - into a self-comparison, because
    the ATTRIBUTE on the other side was reassigned in between. That control is
    shipped, and :data:`tests.test_liveness._REVERT_LANDED` is reduced from it.

    Args:
        node: Any expression.

    Returns:
        True if the comparison is decided by the language alone.
    """
    if not isinstance(node, ast.Compare) or len(node.ops) != 1:
        return False
    if not isinstance(node.ops[0], _DECIDED_OPS):
        return False
    left, right = node.left, node.comparators[0]
    if not isinstance(left, ast.Name) or not isinstance(right, ast.Name):
        return False
    return left.id == right.id


def self_comparison(node: ast.expr) -> str | None:
    """Why an assertion compares one expression with itself, when it does.

    THE SECOND BOUND IN THIS MODULE, AND IT EXISTS FOR THE SAME REASON AS THE
    FIRST. ``assert version >= version`` is either a vacuity or the standard
    test that an ordering is reflexive, and ``assert parser.parsed is
    parser.parsed`` is either a vacuity or the standard test that a
    ``functools.cached_property`` still memoizes. The two readings are
    STRUCTURALLY IDENTICAL and no rule over the assertion's own syntax
    separates them, exactly as no rule separates ``if _looks_fine():
    pytest.skip(...)`` from a real precondition.

    So the set is counted rather than decided, and what that buys is a number:
    how many shipped assertions are about their own operator or their own
    operand access rather than about a value, recomputed every run.

    A CALL-BEARING SELF-COMPARISON IS NOT IN THIS SET. ``f(x) == f(x)`` asserts
    that ``f`` is DETERMINISTIC, which is a property of the code under test
    rather than of the operator, and this tree ships that control and names it
    at :data:`tests.test_liveness._DETERMINISM_CHECK`.

    Args:
        node: The expression an ``assert`` statement tests.

    Returns:
        A description, or None when the two sides are not the same expression.
    """
    if not isinstance(node, ast.Compare) or len(node.ops) != 1:
        return None
    if not isinstance(node.ops[0], _REFLEXIVE_OPS) or _identity_with_itself(node):
        return None
    left, right = node.left, node.comparators[0]
    if ast.dump(left) != ast.dump(right):
        return None
    if any(isinstance(inner, ast.Call) for inner in ast.walk(left)):
        return None
    return "compared with itself"


def _language_decided(node: ast.expr) -> str | None:
    """Whether a predicate's answer is fixed by the language rather than the input.

    THIS RULE CLAIMS A SEMANTIC CLASS AND RECOGNISES IT THROUGH DECLARED
    SPELLINGS, and both halves of that sentence are the honest statement of it.
    The CLASS is what the language guarantees. The SPELLINGS are the builtin
    names in :data:`TRUSTED_BUILTINS`, which a module is free to rebind and no
    analysis of a call site can tell. An earlier version matched exactly two
    spellings while claiming the class, so ``assert 0 <= len(x)`` and
    ``assert isinstance(x, (int, object))`` restored the gutting the rule
    exists to close. Operand order is normalised away first, so a comparison is
    read by what it MEANS rather than by which side it was written on.

    WHAT IS DELIBERATELY LEFT OUTSIDE, named rather than discovered.
    ``not (x != x)`` is not here: ``__ne__`` is program code, so that predicate
    is not decided by the language even though it reads like it is.
    ``id(x) == id(x)`` is not here either: it would be decided only by trusting
    one more name, and adding names one at a time is the blocklist this rule was
    widened away from.

    Args:
        node: Any expression.

    Returns:
        A description, or None.
    """
    if _isinstance_against_object(node):
        return "isinstance against object, which every value satisfies"
    if not isinstance(node, ast.Compare) or len(node.ops) != 1:
        return None
    if _member_of_a_literal_holding_it(node):
        return "membership of a literal holding the same name, which tests identity first"
    normalised = _normalised(node)
    if normalised is None:
        return None
    _, operator, bound = normalised
    limit = _constant_int(bound)
    if limit is None:
        return None
    floor = any(operator is comparison and limit == value for comparison, value in _LENGTH_FLOORS)
    return "a length compared against the floor the language guarantees" if floor else None


def _constant_int(node: ast.expr) -> int | None:
    """The integer an expression names, when it names one at parse time.

    A NEGATIVE LITERAL IS NOT A CONSTANT NODE. ``-1`` parses as a unary minus
    over ``1``, so reading ``ast.Constant`` alone misses every floor written
    below zero - which is exactly the respelling ``len(x) > -1`` is.

    Args:
        node: Any expression.

    Returns:
        The value, or None when it is not a literal integer.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _constant_int(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return None if isinstance(node.value, bool) else node.value
    return None


def _isinstance_against_object(node: ast.expr) -> bool:
    """Whether a call is an ``isinstance`` every value passes.

    A tuple of target types passes when ANY of them matches, so ``object``
    anywhere inside one decides the whole call.

    Args:
        node: Any expression.

    Returns:
        True if ``object`` is among the target types.
    """
    if not isinstance(node, ast.Call) or len(node.args) != _ISINSTANCE_ARGS:
        return False
    if _dotted(node.func).split(".")[-1] != _TESTS_TYPE:
        return False
    target = node.args[1]
    candidates = target.elts if isinstance(target, ast.Tuple) else [target]
    return any(isinstance(one, ast.Name) and one.id == _ROOT_TYPE for one in candidates)


def _member_of_a_literal_holding_it(node: ast.Compare) -> bool:
    """Whether a name is tested for membership of a literal that holds it.

    Container membership compares identity before equality, so this holds for
    every input - including a value that is not equal to itself.

    Args:
        node: A single comparison.

    Returns:
        True if the predicate is decided.
    """
    if not isinstance(node.ops[0], ast.In):
        return False
    left, right = node.left, node.comparators[0]
    if not isinstance(left, ast.Name) or not isinstance(right, ast.Tuple | ast.List | ast.Set):
        return False
    return any(isinstance(one, ast.Name) and one.id == left.id for one in right.elts)


def _normalised(node: ast.Compare) -> tuple[ast.expr, type[ast.cmpop], ast.expr] | None:
    """One comparison rewritten with the measured length on the left.

    ``0 <= len(x)`` and ``len(x) >= 0`` are one predicate written twice. A rule
    that reads only one of the two spellings is a blocklist rather than the
    semantic class it claims to be.

    Args:
        node: A single comparison.

    Returns:
        ``(length, operator, bound)``, or None when neither side is a length.
    """
    left, right = node.left, node.comparators[0]
    operator = type(node.ops[0])
    if _measures_length(left):
        return left, operator, right
    mirrored = _MIRRORED_OPS.get(operator)
    if mirrored is not None and _measures_length(right):
        return right, mirrored, left
    return None


def _measures_length(node: ast.expr) -> bool:
    """Whether an expression is a call to the trusted ``len``.

    Args:
        node: Any expression.

    Returns:
        True if it measures a length.
    """
    return isinstance(node, ast.Call) and _dotted(node.func).split(".")[-1] == _MEASURES


def is_grading_call(name: str | None, prefixes: tuple[str, ...] = GRADING_PREFIXES) -> bool:
    """Whether a called name grades.

    Args:
        name: The bare called name, or None.
        prefixes: The vocabulary to read it against.

    Returns:
        True for a grading-verb prefix and for pytest's own spellings.
    """
    if name is None:
        return False
    bare = name.lstrip("_")
    return bare.startswith(prefixes) or bare in PYTEST_GRADING_CALLS


def _plain_name(node: ast.expr) -> str | None:
    """The bare name a call names DIRECTLY, never through an attribute.

    A route is resolved against functions this tree defines, so ``helper()``
    may be one and ``obj.helper()`` may not - the second names a method on
    something this module did not resolve, and reading it as the module-level
    function of the same name would credit grading that never happens.

    Args:
        node: Any expression.

    Returns:
        The called name, or None.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def is_grading_statement(node: ast.stmt, routes: frozenset[str] = frozenset()) -> bool:
    """Whether one statement grades.

    An ``assert`` whose test cannot discriminate is excluded. It executes and
    passes and says nothing about the program, so counting it lets eleven
    characters restore any gutting this module closes. A statically FALSE one
    is kept: that is a deliberate failure and it does grade.

    A CALL IS GRADING WHEN IT REACHES GRADING, whatever it is spelled. The
    vocabulary is a naming convention and ``routes`` is what stops that
    convention from deciding membership - see :func:`grading_routes`.

    Args:
        node: A statement.
        routes: Names whose call reaches a grading statement in this module.

    Returns:
        True for a real assertion, a call to a grader, and a ``with`` whose
        context manager is ``pytest.raises`` or ``pytest.warns``.
    """
    if isinstance(node, ast.Assert):
        return cannot_discriminate(node.test) is None
    if isinstance(node, ast.Expr):
        return is_grading_call(_called_name(node.value)) or _plain_name(node.value) in routes
    if isinstance(node, ast.With | ast.AsyncWith):
        return any(is_grading_call(_called_name(item.context_expr)) for item in node.items)
    return False


def is_exiting_statement(node: ast.stmt) -> bool:
    """Whether a statement leaves the function without failing.

    Both spellings count. ``pytest.skip(...)`` is a call and ``raise
    pytest.skip.Exception(...)`` is a raise, and they do the identical thing -
    an analysis that reads one and not the other is closed by spelling.

    Args:
        node: A statement.

    Returns:
        True for either spelling of a skip, xfail or exit.
    """
    if isinstance(node, ast.Expr):
        return _called_name(node.value) in EXITING_CALLS
    if isinstance(node, ast.Raise) and node.exc is not None:
        tail = _dotted(node.exc).split(".")
        nested = (
            len(tail) >= _QUALIFIED_PARTS and tail[-1] == "Exception" and tail[-2] in EXITING_CALLS
        )
        return nested or tail[-1] in _EXITING_EXCEPTIONS
    return False


def disabling_decorators(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[int, str]]:
    """Decorators that switch a function off with no runtime condition.

    ``@pytest.mark.skip`` is one line, is how anyone actually disables a test,
    and is not a statement - so an analysis reading only the body never sees
    it. ``skipif`` is included only when its condition is statically decidable
    and true; every one this tree ships tests the running machine and none of
    them is.

    ``parametrize`` OVER AN EMPTY LITERAL RUNS THE BODY ZERO TIMES, and pytest
    reports the module as passed with one skip while the assertions inside
    never execute once. That is decidable from the decorator on exactly the
    same ground a constant ``skipif`` condition is, so it is read here. WHAT IS
    NOT DECIDABLE is an argument set built elsewhere and named at the
    decorator; that residual stays open and is not claimed.

    Args:
        node: A function node.

    Returns:
        ``(line, description)`` for each disabling decorator.
    """
    found: list[tuple[int, str]] = []
    for decorator in node.decorator_list:
        dotted = _dotted(decorator)
        parts = dotted.split(".")
        if len(parts) < _QUALIFIED_PARTS or "mark" not in parts:
            continue
        mark = parts[-1]
        conditional = (
            mark == _CONDITIONAL_MARK
            and isinstance(decorator, ast.Call)
            and bool(decorator.args)
            and static_truth(decorator.args[0]) is True
        )
        empty = (
            mark == _PARAMETRIZING_MARK
            and isinstance(decorator, ast.Call)
            and len(decorator.args) >= _PARAMETRIZE_ARGS
            and static_truth(decorator.args[1]) is False
        )
        if mark in _DISABLING_MARKS:
            found.append((decorator.lineno, dotted))
        elif conditional:
            found.append((decorator.lineno, f"{dotted} on a constant condition"))
        elif empty:
            found.append((decorator.lineno, f"{dotted} over an empty argument set"))
    return found


def own_statements(node: ast.AST) -> list[ast.stmt]:
    """Every statement belonging to a function, excluding nested definitions.

    A nested ``def`` is a different function with its own exits, so its body
    must not decide anything about the one that encloses it.

    Args:
        node: A function node.

    Returns:
        The function's own statements, in no particular order.
    """
    found: list[ast.stmt] = []
    pending: list[ast.AST] = list(getattr(node, "body", []))
    while pending:
        current = pending.pop()
        if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        if isinstance(current, ast.stmt):
            found.append(current)
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            pending.extend(getattr(current, field, None) or [])
    return found


def carries_grading(body: list[ast.stmt], routes: frozenset[str] = frozenset()) -> bool:
    """Whether a statement list holds a grading statement anywhere inside it.

    The EXISTENTIAL question, used for a loop body. A loop over an empty
    collection grades nothing, so the strict answer for the exit after it is
    "not graded" - and that answer reports a large set of correct bodies on
    this tree. The generosity is taken and counted rather than hidden.

    Args:
        body: The statements to look through.
        routes: Names whose call reaches a grading statement.

    Returns:
        True if grading appears anywhere within.
    """
    return any(
        isinstance(inner, ast.stmt) and is_grading_statement(inner, routes)
        for node in body
        for inner in ast.walk(node)
    )


def grading_routes(sources: dict[str, str]) -> dict[str, frozenset[str]]:
    """Per module, the names whose call reaches a grading statement.

    THE VOCABULARY IS A NAMING CONVENTION AND THIS IS ITS FAILURE MODE. Rename
    ``_assert_every_row_balances`` to ``_every_row_balances`` and nothing about
    any caller changes, but every one of them stops shipping a grading
    statement and leaves the population in silence. The route is the same route
    it always was; only the spelling moved.

    So membership stops depending on the spelling. A call is resolved against
    the functions the surveyed modules actually define - the calling module's
    own module-level functions, and names it imports by ``from <module> import
    <name>`` where that module is one of the surveyed ones - and a name whose
    target reaches grading is itself a grading route. The relation is closed
    under itself, so a chain of renamed helpers resolves too.

    WHAT IS RETURNED IS WHAT IS CALLABLE FROM A MODULE, NOT WHAT IS DEFINED IN
    IT, and the difference is the whole of what makes this work across a file
    boundary. The renamed grader lives in one module and its caller in another;
    returning only local definitions resolved the synthetic corpus where both
    sit together and NOTHING in the real tree, which is exactly what a fixture
    authored beside the analysis hides. So an imported name whose definition
    reaches grading is in the calling module's set, under the LOCAL spelling,
    because the local spelling is what the call site uses.

    WHAT IS NOT RESOLVED, stated rather than implied. A method call, a call
    through a variable, a call into a module outside the surveyed set, and a
    call to a function shadowed by a local binding all stay unresolved. Every
    one of those is a route this returns nothing for, which means the
    population stays as narrow as it is today rather than wrongly wide - the
    failure direction is under-reporting, and it is the same direction the loop
    and ``try`` generosities already take.

    Args:
        sources: Repo-relative path to module source, for every module in the
            survey. Resolution is scoped to this set, so a two-module survey
            resolves less than a whole-tree one.

    Returns:
        Repo-relative path to the names a call in it can reach grading through.
    """
    trees = {relative: ast.parse(text) for relative, text in sources.items()}
    defined: dict[str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for relative, tree in trees.items():
        defined[_module_path(relative)] = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        }
    imported = {relative: _imported_from(tree) for relative, tree in trees.items()}

    reaching: dict[str, set[str]] = {relative: set() for relative in sources}
    for _ in range(len(sources) + 1):
        settled = True
        for relative in sources:
            own = defined[_module_path(relative)]
            for name, node in own.items():
                if name in reaching[relative] or not _reaches_grading(
                    node, relative, reaching, defined, imported
                ):
                    continue
                reaching[relative].add(name)
                settled = False
        if settled:
            break

    by_module = {_module_path(relative): relative for relative in sources}
    callable_here: dict[str, frozenset[str]] = {}
    for relative in sources:
        names = set(reaching[relative])
        for local, (origin, original) in imported[relative].items():
            source = by_module.get(origin)
            if source is not None and original in reaching[source]:
                names.add(local)
        callable_here[relative] = frozenset(names)
    return callable_here


def _module_path(relative: str) -> str:
    """The dotted module a repo-relative path names.

    Args:
        relative: A repo-relative Python path.

    Returns:
        The dotted module name.
    """
    return relative.removesuffix(".py").replace("/", ".")


def _imported_from(tree: ast.Module) -> dict[str, tuple[str, str]]:
    """Every name an absolute ``from ... import ...`` brought in, to where it came from.

    The LOCAL name and the ORIGINAL name are both kept, because an alias makes
    them different and the call site uses the local one while the definition
    carries the original.

    Args:
        tree: A parsed module.

    Returns:
        Local name to ``(dotted module, original name)``.
    """
    found: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                found[alias.asname or alias.name] = (node.module, alias.name)
    return found


def _reaches_grading(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    relative: str,
    reaching: dict[str, set[str]],
    defined: dict[str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]],
    imported: dict[str, dict[str, tuple[str, str]]],
) -> bool:
    """Whether one function grades directly or through a resolvable call.

    Args:
        node: The function.
        relative: The module it lives in.
        reaching: What is known to reach grading so far, per module.
        defined: Module-level functions, per dotted module.
        imported: Local name to ``(module, original name)``, per module.

    Returns:
        True if it grades or calls something that does.
    """
    if ships_a_grading_statement(node):
        return True
    own = _module_path(relative)
    for statement in own_statements(node):
        if not isinstance(statement, ast.Expr):
            continue
        name = _plain_name(statement.value)
        if name is None:
            continue
        if name in defined[own]:
            if name in reaching[relative]:
                return True
            continue
        elsewhere = imported[relative].get(name)
        if elsewhere is None:
            continue
        origin, original = elsewhere
        source = next((key for key in reaching if _module_path(key) == origin), None)
        if source is not None and original in reaching[source]:
            return True
    return False


def terminates_in_failure(body: list[ast.stmt]) -> bool:
    """Whether a statement list is guaranteed to end in a FAILURE.

    This is what makes a guarded failure an assertion. ``if bad:
    pytest.fail(...)`` grades the path that does NOT take the branch, exactly
    as ``assert not bad`` does, because reaching the code after it means the
    condition was false. A ``return`` does not qualify - leaving early is not
    grading - and neither does an exiting call, which is a skip and not a
    failure.

    Args:
        body: The statements to inspect.

    Returns:
        True if every path through the list ends by failing.
    """
    if not body:
        return False
    last = body[-1]
    if is_exiting_statement(last):
        return False
    if isinstance(last, ast.Assert):
        return static_truth(last.test) is False
    if isinstance(last, ast.If) and last.orelse:
        return terminates_in_failure(last.body) and terminates_in_failure(last.orelse)
    fails = isinstance(last, ast.Expr) and _called_name(last.value) == "fail"
    return isinstance(last, ast.Raise) or fails


def never_iterates(node: ast.For | ast.AsyncFor | ast.While) -> bool:
    """Whether a loop's body provably runs zero times.

    THE MODULE'S OWN CLAIM, APPLIED WHERE IT WAS NOT. "A statically constant
    branch is not a branch" is why every ``if`` is folded through
    :func:`static_truth`; a loop over a constant empty iterable is the same
    claim and was not folded, so ``for _ in []:``, ``for _ in range(0):`` and
    ``while False:`` each wrapped a whole shipped control in silence - no
    finding, no vacuous assertion, no dead grading, and the control still
    counted as a live member.

    Only the EMPTY direction is decided. A loop that provably runs at least
    once would let the walk credit grading less generously, which is a widening
    of what counts as graded and is not what this closes.

    Args:
        node: A loop.

    Returns:
        True when the body cannot run.
    """
    if isinstance(node, ast.While):
        return static_truth(node.test) is False
    return static_truth(node.iter) is False or _empty_range(node.iter)


def _empty_range(node: ast.expr) -> bool:
    """Whether an expression is a ``range`` over constant integers that yields nothing.

    ``range`` is read by name, which is what :data:`TRUSTED_BUILTINS` declares.
    A step of zero raises rather than yielding nothing, so it is not decided
    here.

    Args:
        node: Any expression.

    Returns:
        True when the range is provably empty.
    """
    if not isinstance(node, ast.Call) or _dotted(node.func).split(".")[-1] != _COUNTS:
        return False
    if node.keywords or not node.args:
        return False
    bounds: list[int] = []
    for argument in node.args:
        if not isinstance(argument, ast.Constant) or not isinstance(argument.value, int):
            return False
        if isinstance(argument.value, bool):
            return False
        bounds.append(argument.value)
    try:
        return len(range(*bounds)) == 0
    except (TypeError, ValueError):
        return False


def always_leaves(body: list[ast.stmt]) -> bool:
    """Whether every path through a statement list leaves the function.

    A ``return``, a ``raise`` and a skip all leave. So does an ``if`` whose
    taken arm leaves, when which arm is taken is decidable - and so does one
    whose BOTH arms leave, whatever the condition. Reaching the statement after
    such a list is impossible, which is what makes any grading below it dead.

    Args:
        body: The statements to inspect.

    Returns:
        True when the list cannot fall through to what follows it.
    """
    for statement in body:
        if isinstance(statement, ast.Return | ast.Raise) or is_exiting_statement(statement):
            return True
        if isinstance(statement, ast.If) and _branch_always_leaves(statement):
            return True
        if isinstance(statement, ast.With | ast.AsyncWith) and always_leaves(statement.body):
            return True
    return False


def _branch_always_leaves(node: ast.If) -> bool:
    """Whether an ``if`` leaves the function however it is taken.

    Args:
        node: The ``if``.

    Returns:
        True when no path through it falls through.
    """
    decided = static_truth(node.test)
    if decided is True:
        return always_leaves(node.body)
    if decided is False:
        return always_leaves(node.orelse)
    return bool(node.orelse) and always_leaves(node.body) and always_leaves(node.orelse)


def returns_a_value(node: ast.AST) -> bool:
    """Whether a function ever returns something to its caller.

    Args:
        node: A function node.

    Returns:
        True if any of its own ``return`` statements carries a value.
    """
    return any(
        isinstance(statement, ast.Return) and statement.value is not None
        for statement in own_statements(node)
    )


def ships_a_grading_statement(node: ast.AST, routes: frozenset[str] = frozenset()) -> bool:
    """Whether a function grades anywhere in its own body.

    Args:
        node: A function node.
        routes: Names whose call reaches a grading statement.

    Returns:
        True if it carries at least one grading statement.
    """
    return any(is_grading_statement(statement, routes) for statement in own_statements(node))


def is_population_member(node: ast.AST, routes: frozenset[str] = frozenset()) -> bool:
    """Whether a function is a control or a grader.

    Args:
        node: A function node.
        routes: Names whose call reaches a grading statement.

    Returns:
        True if it grades and returns nothing.
    """
    return ships_a_grading_statement(node, routes) and not returns_a_value(node)


# ---------------------------------------------------------------------------
# The analysis
# ---------------------------------------------------------------------------


class _Walk:
    """One pass over one function, accumulating holes and generosity flags."""

    def __init__(self, *, routes: frozenset[str] = frozenset()) -> None:
        """Start with nothing found and neither generosity used.

        Args:
            routes: Names whose call reaches a grading statement.
        """
        self.holes: list[tuple[int, str]] = []
        self.leaned_on_loop = False
        self.leaned_on_try = False
        self._routes = routes

    def scan(self, body: list[ast.stmt], graded: bool, *, unconditional: bool = False) -> bool:
        """Walk a statement list, recording every exit reached without grading.

        Args:
            body: The statements to walk.
            graded: Whether grading has already happened on every path here.
            unconditional: Whether this list runs on every call - the function's
                own top level, or a branch a constant condition always takes.
                An exiting call is a hole only here, because a genuinely
                CONDITIONAL skip is the legitimate idiom.

        Returns:
            Whether the path leaving this block is graded or has terminated.
        """
        for node in body:
            if isinstance(node, ast.Return):
                if not graded:
                    self.holes.append((node.lineno, "return"))
                return True
            if is_exiting_statement(node):
                if unconditional and not graded:
                    self.holes.append((node.lineno, "exit without grading"))
                return True
            if isinstance(node, ast.Raise):
                return True
            if is_grading_statement(node, self._routes):
                if isinstance(node, ast.With | ast.AsyncWith):
                    self.scan(node.body, True)
                graded = True
                continue
            graded = self._compound(node, graded, unconditional=unconditional)
        return graded

    def _compound(self, node: ast.stmt, graded: bool, *, unconditional: bool) -> bool:
        """Walk one compound statement and report what the path leaving it knows.

        Args:
            node: A compound statement.
            graded: Whether grading has already happened on the path to it.
            unconditional: Whether this statement runs on every call.

        Returns:
            Whether the path leaving the statement is graded.
        """
        if isinstance(node, ast.If):
            return self._branch(node, graded, unconditional=unconditional)
        if isinstance(node, ast.With | ast.AsyncWith):
            self._suppressed(node)
            return self.scan(node.body, graded, unconditional=unconditional) or graded
        if isinstance(node, ast.For | ast.AsyncFor | ast.While):
            return self._loop(node, graded, unconditional=unconditional)
        if isinstance(node, ast.Try):
            return self._try(node, graded, unconditional=unconditional)
        return self._match(node, graded) if isinstance(node, ast.Match) else graded

    def _loop(
        self, node: ast.For | ast.AsyncFor | ast.While, graded: bool, *, unconditional: bool
    ) -> bool:
        """A loop, folded when it provably never runs and credited generously when it may.

        A LOOP THAT CANNOT RUN IS NOT A LOOP, on exactly the ground that a
        constant branch is not a branch. Its body grades nothing and its
        ``orelse`` is what actually executes, so folding it is what stops
        ``for _ in []:`` from wrapping a whole control in silence.

        Args:
            node: The loop.
            graded: Whether grading has already happened.
            unconditional: Whether the loop itself runs on every call.

        Returns:
            Whether the path leaving it is graded.
        """
        if never_iterates(node):
            return self.scan(node.orelse, graded, unconditional=unconditional) or graded
        self.scan(node.body, graded)
        self.scan(node.orelse, graded)
        if not graded and carries_grading(node.body, self._routes):
            self.leaned_on_loop = True
            return True
        return graded

    def _branch(self, node: ast.If, graded: bool, *, unconditional: bool) -> bool:
        """An ``if``, with a constant condition folded away first.

        Folding is what tells a real conditional from one written to look like
        one, and it is also what makes a guarded failure readable: when the
        condition is genuinely unknown, reaching the code after a branch that
        FAILS is the graded fact.

        Args:
            node: The ``if``.
            graded: Whether grading has already happened.
            unconditional: Whether the ``if`` itself always runs.

        Returns:
            Whether the path leaving it is graded.
        """
        decided = static_truth(node.test)
        if decided is True:
            return self.scan(node.body, graded, unconditional=unconditional)
        if decided is False:
            return self.scan(node.orelse, graded, unconditional=unconditional)
        taken = self.scan(node.body, graded)
        other = self.scan(node.orelse, graded) if node.orelse else graded
        if graded or (taken and other):
            return True
        if terminates_in_failure(node.body):
            return True
        return bool(node.orelse) and terminates_in_failure(node.orelse)

    def _try(self, node: ast.Try, graded: bool, *, unconditional: bool) -> bool:
        """A ``try``, including the handler that converts a failure rather than eating it.

        Args:
            node: The ``try``.
            graded: Whether grading has already happened.
            unconditional: Whether the ``try`` itself always runs.

        Returns:
            Whether the path leaving it is graded.
        """
        self._swallowed(node)
        body_graded = self.scan(node.body, graded, unconditional=unconditional)
        for handler in node.handlers:
            self.scan(handler.body, graded)
        else_graded = self.scan(node.orelse, graded) if node.orelse else False
        converts = any(terminates_in_failure(handler.body) for handler in node.handlers)
        after = graded
        if not graded and (body_graded or else_graded or converts):
            self.leaned_on_try = True
            after = True
        if node.finalbody:
            after = self.scan(node.finalbody, after) or after
        return after

    def _match(self, node: ast.Match, graded: bool) -> bool:
        """A ``match``, which grades when every arm does AND one is irrefutable.

        THE ARM THAT REFUTED THE PREVIOUS VERSION. It returned the incoming
        verdict, so no ``match`` could ever grade anything - wrong for every
        ``match`` ever written, and scoring zero only because this tree
        contains none.

        Args:
            node: The ``match``.
            graded: Whether grading has already happened.

        Returns:
            Whether the path leaving it is graded.
        """
        arms = [self.scan(case.body, graded) for case in node.cases]
        exhaustive = any(
            case.guard is None
            and isinstance(case.pattern, ast.MatchAs)
            and case.pattern.pattern is None
            for case in node.cases
        )
        if graded or (arms and all(arms) and exhaustive):
            return True
        return bool(node.cases) and all(terminates_in_failure(case.body) for case in node.cases)

    def _swallowed(self, node: ast.Try) -> None:
        """Record a ``try`` that grades and whose handler DISCARDS the failure.

        THREE THINGS HAVE TO HOLD, and each closes a measured hole or a measured
        false positive.

        The handler must CATCH what a failed ``assert`` raises. Reading every
        handler as a swallow reported ``except ValueError: pass`` around a
        graded call, which does not stand between the assertion and its caller
        at all.

        The handler must not CONVERT the failure, by raising, by re-raising, by
        calling ``pytest.fail`` or by leaving the function.

        The handler must be INERT - see :func:`_inert_handler`. The previous
        version required every statement to be ``pass`` or a bare constant, so
        one ``print(exc)`` defeated it, and a swallow into a log call is how
        anybody actually writes one. Widening it as far as "does not convert"
        would report ``except AssertionError: rejected.append(path)``, which
        CONVERTS the failure into a value its caller grades and is shipped in
        ``tests/save/reach_guard.py``.

        Args:
            node: A ``try`` statement.
        """
        if not carries_grading(node.body, self._routes):
            return
        for handler in node.handlers:
            bound = handler.name
            if not _catches_an_assertion(handler.type) or _converts_a_failure(handler.body):
                continue
            if _inert_handler(handler.body, bound):
                self.holes.append((handler.lineno, "failure discarded"))

    def _suppressed(self, node: ast.With | ast.AsyncWith) -> None:
        """Record a ``with`` that discards the failure of the grading inside it.

        ``with contextlib.suppress(AssertionError):`` does what a ``try`` with
        an empty handler does and has no ``try`` in it, so an analysis
        inspecting ``ast.Try`` alone had nothing to inspect.

        Args:
            node: A ``with`` statement.
        """
        if not carries_grading(node.body, self._routes):
            return
        for item in node.items:
            context = item.context_expr
            if not isinstance(context, ast.Call):
                continue
            if _dotted(context.func).split(".")[-1] != _SUPPRESSING_CALL:
                continue
            if any(_catches_an_assertion(argument) for argument in context.args):
                self.holes.append((node.lineno, "failure discarded"))
                return


def _catches_an_assertion(node: ast.expr | None) -> bool:
    """Whether an exception expression catches what a failed ``assert`` raises.

    A bare ``except`` names nothing and catches everything, so None is True.

    Args:
        node: The caught type expression, a tuple of them, or None.

    Returns:
        True when a failing assertion would be caught.
    """
    if node is None:
        return True
    candidates = node.elts if isinstance(node, ast.Tuple) else [node]
    return any(_dotted(one).split(".")[-1] in _ASSERTION_CATCHERS for one in candidates)


def _converts_a_failure(body: list[ast.stmt]) -> bool:
    """Whether a handler turns the failure it caught into something else.

    Raising, re-raising, failing and leaving all carry the failure somewhere.
    None of them is a swallow.

    Args:
        body: The handler's statements.

    Returns:
        True when the failure does not simply stop here.
    """
    if terminates_in_failure(body):
        return True
    return any(
        isinstance(statement, ast.Raise) or is_exiting_statement(statement) for statement in body
    )


def _inert_handler(body: list[ast.stmt], bound: str | None) -> bool:
    """Whether nothing in a handler body can carry the failure out of it.

    WHERE THE LINE IS AND WHY IT IS THERE. ``print(exc)`` and ``pass`` are the
    same handler: the failure is rendered or dropped and nothing the enclosing
    function can read afterwards has changed. ``rejected.append(path)`` is a
    different handler: it writes the failure into a collection bound outside,
    which is the CONVERSION idiom ``tests/save/reach_guard.py`` ships, and its
    caller grades the result.

    So a bare call statement is inert only when its callee is a plain name and
    its arguments name nothing but the handler's own exception binding. THE
    RESIDUAL IS STATED: a method call on a module, ``logging.warning(exc)``,
    is not read as inert, because from the source alone it is the same shape as
    a call that mutates a receiver.

    Args:
        body: The handler's statements.
        bound: The name the handler binds its exception to, or None.

    Returns:
        True when the handler cannot carry the failure anywhere.
    """
    allowed = {bound} if bound is not None else set()
    for statement in body:
        if isinstance(statement, ast.Pass):
            continue
        if not isinstance(statement, ast.Expr):
            return False
        value = statement.value
        if isinstance(value, ast.Constant):
            continue
        if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name):
            return False
        named = {inner.id for inner in ast.walk(value) if isinstance(inner, ast.Name)} - {
            value.func.id
        }
        if named - allowed:
            return False
    return True


def _significant_body(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    """A function's body with a leading docstring dropped.

    Args:
        node: A function node.

    Returns:
        The statements that actually run.
    """
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        return body[1:]
    return body


def grade(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    routes: frozenset[str] = frozenset(),
) -> _Walk:
    """Run the analysis over one function.

    Args:
        node: A function node.
        routes: Names whose call reaches a grading statement.

    Returns:
        The completed walk, holding every hole and both generosity flags. The
        implicit end-of-function exit and every disabling decorator are
        recorded as holes.
    """
    walk = _Walk(routes=routes)
    walk.holes.extend(
        (line, f"disabled by {description}") for line, description in disabling_decorators(node)
    )
    if not walk.scan(_significant_body(node), False, unconditional=True):
        walk.holes.append((node.lineno, "end of function"))
    return walk


def dead_grading(
    node: ast.FunctionDef | ast.AsyncFunctionDef, routes: frozenset[str] = frozenset()
) -> list[int]:
    """Grading statements that can never run.

    Three ways in: an exit precedes it at the same level, it sits inside a
    branch a constant condition never takes, or it sits inside a loop whose
    body provably runs zero times.

    THE HOLE THAT WAS HERE AND IS NOT ANY MORE. Deadness was propagated INSIDE
    a folded branch and never PAST one, so ``if globals(): return 1`` - which
    always returns and makes every statement below it unreachable - left the
    grading after it reading as live. That hole was the whole reason a separate
    fabricated-return rule looked necessary, and that rule's own false
    positives were the cost of keeping it. :func:`always_leaves` decides the
    same question for both, and it decides it for an undecidable ``if`` whose
    two arms BOTH leave as well.

    Args:
        node: A function node.
        routes: Names whose call reaches a grading statement.

    Returns:
        The lines of unreachable grading statements.
    """
    found: list[int] = []
    lists: list[tuple[list[ast.stmt], bool]] = [(_significant_body(node), False)]
    while lists:
        body, already_dead = lists.pop()
        dead = already_dead
        for statement in body:
            if dead and is_grading_statement(statement, routes):
                found.append(statement.lineno)
            if isinstance(statement, ast.Return | ast.Raise) or is_exiting_statement(statement):
                dead = True
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            if isinstance(statement, ast.If):
                decided = static_truth(statement.test)
                lists.append((statement.body, dead or decided is False))
                lists.append((statement.orelse, dead or decided is True))
                dead = dead or _branch_always_leaves(statement)
                continue
            if isinstance(statement, ast.For | ast.AsyncFor | ast.While):
                idle = never_iterates(statement)
                lists.append((list(statement.body), dead or idle))
                lists.append((list(statement.orelse), dead))
                continue
            for field in ("body", "orelse", "finalbody"):
                nested = getattr(statement, field, None)
                if nested:
                    lists.append((list(nested), dead))
            lists.extend(
                (list(handler.body), dead) for handler in getattr(statement, "handlers", None) or []
            )
            if isinstance(statement, ast.With | ast.AsyncWith) and always_leaves(statement.body):
                dead = True
    return sorted(found)


def functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Every function defined anywhere in a module.

    Args:
        tree: A parsed module.

    Returns:
        Function nodes, including methods and nested definitions.
    """
    return [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def vacuous_grading(module: str, text: str) -> tuple[list[Finding], int, list[Finding]]:
    """Every assertion that holds for every possible input, and how many were read.

    DERIVED OVER EVERY FUNCTION rather than over the population, and that is
    deliberate. A vacuous assertion beside a real one leaves the function
    grading, so the population filter cannot see it - and the shipped instance
    this rule was written from was one of several in one control, most of them
    bounds no input could exceed. Reporting only the ones that empty a function
    would have reported none of them.

    THE SELF-COMPARISON BOUND IS DERIVED IN THE SAME PASS, over the same
    denominator, because it is what the narrowing of :func:`cannot_discriminate`
    hands back. It is COUNTED, not reported - see :func:`self_comparison`.

    Args:
        module: How the module should be named in a report.
        text: Its source.

    Returns:
        ``(findings, asserted, self_comparisons)`` - what cannot discriminate,
        how many ``assert`` statements were examined to find it, and what
        compares an expression with itself under an operator the program can
        define.
    """
    found: list[Finding] = []
    reflexive: list[Finding] = []
    asserted = 0
    for node in functions(ast.parse(text)):
        for statement in own_statements(node):
            if not isinstance(statement, ast.Assert):
                continue
            asserted += 1
            if cannot_discriminate(statement.test) is not None:
                found.append(Finding(module, node.name, statement.lineno, "cannot discriminate"))
            elif self_comparison(statement.test) is not None:
                reflexive.append(
                    Finding(module, node.name, statement.lineno, "compared with itself")
                )
    return found, asserted, reflexive


def conditional_exits(module: str, text: str, routes: frozenset[str] = frozenset()) -> list[Member]:
    """Members that can leave behind a condition this module cannot decide.

    THIS IS A BOUND AND NOT A FINDING, and the difference is the whole of what
    is honest about it. ``if globals(): pytest.skip(...)`` is folded and
    reported as a hole. ``if not corpus: pytest.skip(...)`` is the legitimate
    idiom every skip in this tree uses. ``if _looks_fine(): pytest.skip(...)``
    is a gutting and is STRUCTURALLY IDENTICAL to the second one - the
    condition is opaque at parse time, and no rule over the source separates
    them. Claiming one does would be the false coverage this module was refuted
    for twice.

    So the set is counted instead. What that buys is a number: exactly how much
    of the population a gutting of this shape could hide in, recomputed every
    run rather than written down. :func:`observed_grading` is the only channel
    here that could ever decide one of these, and it decides them one call at a
    time.

    Args:
        module: How the module should be named in a report.
        text: Its source.
        routes: Names whose call reaches a grading statement.

    Returns:
        One member per function carrying such an exit.
    """
    found: list[Member] = []
    for node in functions(ast.parse(text)):
        if not is_population_member(node, routes):
            continue
        opaque = any(
            isinstance(statement, ast.If)
            and static_truth(statement.test) is None
            and any(is_exiting_statement(inner) for inner in statement.body)
            for statement in own_statements(node)
        )
        if opaque:
            found.append(Member(module, node.name, node.lineno))
    return found


def tests_outside_the_population(
    module: str, text: str, routes: frozenset[str]
) -> tuple[list[Member], list[Member]]:
    """Tests the assertion-derived population cannot reach, split by whether they act.

    A test that ships no grading statement grades by the code under test NOT
    raising. The population here is derived from the shipped assertions, so it
    cannot see one - which makes the set a RESIDUAL, and a residual is only
    honest if it is measured every run and has a shape assertion on it. The
    split is that assertion: a test outside the population must at least CALL
    something, because a test that neither grades nor calls grades nothing at
    all and is the endpoint of the very defect this module is about.

    Args:
        module: How the module should be named in a report.
        text: Its source.
        routes: Names whose call reaches a grading statement.

    Returns:
        ``(exercising, inert)`` - those that call something and those that do
        not.
    """
    exercising: list[Member] = []
    inert: list[Member] = []
    for node in functions(ast.parse(text)):
        if not node.name.startswith("test_") or ships_a_grading_statement(node, routes):
            continue
        acts = any(
            isinstance(inner, ast.Call)
            for statement in own_statements(node)
            for inner in ast.walk(statement)
        )
        (exercising if acts else inert).append(Member(module, node.name, node.lineno))
    return exercising, inert


def vocabulary_boundary(module: str, text: str) -> list[Member]:
    """Functions a WIDER grading vocabulary would see and the shipped one does not.

    The shipped vocabulary is a naming convention, so its failure mode is a
    rename: a grader called ``_verify_rows`` instead of ``_assert_rows`` takes
    every caller out of the population without changing a line of their
    behaviour. This re-derives that difference on every run so the boundary is
    a measured set. A ``test_`` function inside it is not a boundary at all -
    it is a control with no grading route this module can see.

    Args:
        module: How the module should be named in a report.
        text: Its source.

    Returns:
        The members of the difference.
    """
    found: list[Member] = []
    for node in functions(ast.parse(text)):
        if ships_a_grading_statement(node):
            continue
        wider = any(
            is_grading_call(_called_name(statement.value), WIDER_GRADING_PREFIXES)
            for statement in own_statements(node)
            if isinstance(statement, ast.Expr)
        )
        if wider:
            found.append(Member(module, node.name, node.lineno))
    return found


def survey_source(module: str, text: str, routes: frozenset[str] = frozenset()) -> Survey:
    """Derive every population and every residual for one module.

    Args:
        module: How the module should be named in a report.
        text: Its source.
        routes: Names whose call reaches a grading statement, from
            :func:`grading_routes`. Empty means the vocabulary alone decides,
            which is what a synthetic corpus wants.

    Returns:
        The survey for that module alone.
    """
    tree = ast.parse(text)
    members: list[Member] = []
    findings: list[Finding] = []
    loop_leaned: list[Member] = []
    try_leaned: list[Member] = []
    value_returning: list[Member] = []
    dead: list[Finding] = []
    for node in functions(tree):
        if not ships_a_grading_statement(node, routes):
            continue
        entry = Member(module, node.name, node.lineno)
        dead.extend(
            Finding(module, node.name, line, "unreachable grading")
            for line in dead_grading(node, routes)
        )
        if returns_a_value(node):
            value_returning.append(entry)
            continue
        members.append(entry)
        walk = grade(node, routes=routes)
        findings.extend(Finding(module, node.name, line, kind) for line, kind in walk.holes)
        if walk.leaned_on_loop:
            loop_leaned.append(entry)
        if walk.leaned_on_try:
            try_leaned.append(entry)
    vacuous, asserted, reflexive = vacuous_grading(module, text)
    return Survey(
        members=members,
        findings=findings,
        loop_leaned=loop_leaned,
        try_leaned=try_leaned,
        value_returning=value_returning,
        dead_grading=dead,
        outside=tests_outside_the_population(module, text, routes),
        vocabulary_boundary=vocabulary_boundary(module, text),
        modules=[module],
        vacuous_grading=vacuous,
        conditional_exits=conditional_exits(module, text, routes),
        asserted=asserted,
        self_comparisons=reflexive,
    )


#: Wall-clock bound for the git plumbing below (CS-896). An unbounded child
#: cannot fail the test that owns it - it burns the CI job's whole budget until
#: the lane is cancelled, which is evidence of nothing. 120s matches the git
#: timeout in tests/test_doc_budget.py and tests/test_commit_msg_gate.py. It is
#: deliberately generous: the job is to bound a hang, not to police speed, and a
#: tight value under two-worker contention on a 2-vCPU runner is a new flake.
GIT_TIMEOUT: Final = 120


def tracked_python_files(root: Path) -> list[str]:
    """Every Python file git tracks, repo-relative and sorted.

    Args:
        root: The repository root.

    Returns:
        Repo-relative paths with forward slashes.

    Raises:
        RuntimeError: If git cannot answer, because a population silently
            falling back to a partial walk is the vacuous green this module
            exists to catch.
    """
    proc = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError("git could not enumerate the tracked Python files")
    return sorted(line for line in proc.stdout.splitlines() if line)


def survey(root: Path, relatives: list[str]) -> Survey:
    """Derive and grade every population across a set of modules.

    Args:
        root: The repository root.
        relatives: Repo-relative Python paths.

    Returns:
        The whole survey.
    """
    sources = {relative: (root / relative).read_text(encoding="utf-8") for relative in relatives}
    routes = grading_routes(sources)
    merged = Survey(
        members=[],
        findings=[],
        loop_leaned=[],
        try_leaned=[],
        value_returning=[],
        dead_grading=[],
        outside=([], []),
        vocabulary_boundary=[],
        modules=[],
        vacuous_grading=[],
        conditional_exits=[],
        asserted=0,
        self_comparisons=[],
    )
    asserted = 0
    for relative in relatives:
        one = survey_source(relative, sources[relative], routes[relative])
        merged.members.extend(one.members)
        merged.findings.extend(one.findings)
        merged.loop_leaned.extend(one.loop_leaned)
        merged.try_leaned.extend(one.try_leaned)
        merged.value_returning.extend(one.value_returning)
        merged.dead_grading.extend(one.dead_grading)
        merged.outside[0].extend(one.outside[0])
        merged.outside[1].extend(one.outside[1])
        merged.vocabulary_boundary.extend(one.vocabulary_boundary)
        merged.modules.append(relative)
        merged.vacuous_grading.extend(one.vacuous_grading)
        merged.conditional_exits.extend(one.conditional_exits)
        merged.self_comparisons.extend(one.self_comparisons)
        asserted += one.asserted
    return merged._replace(asserted=asserted)


def collection_prefixes(root: Path) -> tuple[str, ...]:
    """The name prefixes pytest collects a function under, read from the project.

    THE PREFIX IS A CONFIGURED FACT AND IS NOT WRITTEN DOWN HERE. A project
    setting ``python_functions`` changes what pytest runs, and a rule that
    hardcoded the default would go on reporting against a collection nobody
    uses - silently, which is the failure class this whole module is about. The
    default is pytest's own and is used only when the project states nothing.

    Args:
        root: The repository root.

    Returns:
        The prefixes, with any trailing glob star stripped.

    Raises:
        RuntimeError: If the configuration exists and cannot be read, because a
            rule falling back to a default it was told not to use is the
            silence this module exists to catch.
    """
    configured: object = None
    settings = root / "pyproject.toml"
    if settings.is_file():
        try:
            parsed = tomllib.loads(settings.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            # The exception's TYPE, never the object. str() on a caught exception can
            # append the path it failed on, which carries the account name (CLAUDE.md
            # non-negotiable 12), and `raise ... from exc` already chains the full
            # detail for a human reader without this message rendering it.
            raise RuntimeError(
                f"the project configuration could not be read: {type(exc).__name__}"
            ) from exc
        tools = parsed.get("tool", {})
        pytest_settings = tools.get("pytest", {}).get("ini_options", {})
        configured = pytest_settings.get("python_functions")
    if configured is None:
        return _DEFAULT_COLLECTED
    if isinstance(configured, str):
        patterns: list[object] = list(configured.split())
    elif isinstance(configured, list):
        patterns = list(configured)
    else:
        shape = type(configured).__name__
        raise RuntimeError(f"python_functions is a {shape}, which is neither a string nor a list")
    return tuple(str(pattern).removesuffix("*") for pattern in patterns)


def uncollectable_graders(sources: dict[str, str], prefixes: tuple[str, ...]) -> list[Member]:
    """Every module-level grader in a test module pytest will not collect.

    THE DENOMINATOR UNDER :func:`uncollected_graders`, and the great majority
    of it is correct code: a delegated grader is precisely a function pytest
    does not run and a control does. Deriving it is what stops a clean result
    from that check being a claim about nothing.

    Args:
        sources: Repo-relative path to module source.
        prefixes: What pytest collects a function under.

    Returns:
        One member per candidate, sorted by where it lives.
    """
    found: list[Member] = []
    for relative, text in sorted(sources.items()):
        path = Path(relative)
        if path.parts[0] != TEST_DIRECTORY or not path.name.startswith("test_"):
            continue
        for node in ast.parse(text).body:
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if node.name.startswith(prefixes) or not ships_a_grading_statement(node):
                continue
            found.append(Member(relative, node.name, node.lineno))
    return found


def uncollected_graders(sources: dict[str, str], prefixes: tuple[str, ...]) -> list[Member]:
    """Graders pytest will not collect and nothing in the tree names.

    THE GUTTING NO RULE OVER A FUNCTION'S OWN SOURCE CAN SEE. Rename
    ``test_x`` to ``not_a_test_x`` and the body is untouched, every assertion
    is intact, and the control stays a full member with nothing against it -
    pytest simply stops running it. What changed is not in the source.

    It is decidable from the TREE all the same, on a ground narrower than
    collection and therefore sound: a module-level grader a test module ships,
    that pytest will not collect, and whose name nothing anywhere loads can
    never run, whoever was supposed to call it.

    THE READING OF "NAMES IT" IS DELIBERATELY GENEROUS - a ``Name`` load, an
    attribute of that spelling, an import alias, and a plain string, which is
    how a name reached through ``getattr`` is spelled. Every one of those makes
    a function NOT reported, so the failure direction is under-reporting, which
    is the direction every other generosity in this module takes.

    A DECORATED FUNCTION IS EXEMPT AND THE REASON IS ITS OWN: a decorator can
    hand a function to a framework that reaches it with no name load at all,
    which is exactly what ``pytest.fixture`` does.

    Args:
        sources: Repo-relative path to module source, for every module in the
            survey. Resolution is scoped to this set.
        prefixes: What pytest collects a function under.

    Returns:
        One member per grader nothing can reach.
    """
    named = _every_name(sources)
    return [
        member
        for member in uncollectable_graders(sources, prefixes)
        if member.name not in named and not _is_decorated(sources[member.module], member.name)
    ]


def _every_name(sources: dict[str, str]) -> frozenset[str]:
    """Every spelling any module could reach a definition through.

    Args:
        sources: Repo-relative path to module source.

    Returns:
        Loaded names, attribute spellings, import aliases and string literals.
    """
    found: set[str] = set()
    for text in sources.values():
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                found.add(node.id)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
            elif isinstance(node, ast.alias):
                found.add(node.name.rsplit(".", 1)[-1])
                if node.asname:
                    found.add(node.asname)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
    return frozenset(found)


def _is_decorated(text: str, name: str) -> bool:
    """Whether a module-level function carries any decorator.

    Args:
        text: The module's source.
        name: The function name.

    Returns:
        True if it is decorated.
    """
    node = module_function(text, name)
    return node is not None and bool(node.decorator_list)


def detector_modules(sources: dict[str, str]) -> list[str]:
    """Every module in the suite that ships no grading statement of its own.

    THE POPULATION NEITHER HALF OF THIS MODULE REACHED. A detector library
    ships no ``assert``, so it contributes no member. It is not named ``test_``,
    so no test population holds it. It ships no ``guard_`` function in a tool
    directory, so :func:`guard_tools` does not derive it. Every function in it
    returns a value, so it is not even in the excluded census. This module is
    one of those; so are the rendering guards beside it. Together they fall
    through every filter while being exactly what the acceptance means by a
    shipped guard.

    DERIVED RATHER THAN LISTED, because a hand-maintained list is the thing
    this repository keeps recording as the thing that rots, and because another
    one of these will arrive.

    ONE EXEMPTION, AND ITS REASON IS ABOUT REACHABILITY RATHER THAN ABOUT ITS
    NAME. A ``conftest.py`` is reached by pytest's own convention: its fixtures
    are selected by PARAMETER NAME and its hooks by hook name, and neither is a
    call anything in the tree makes. Asking "does a graded member call into it"
    is therefore the wrong question about it - a green answer would be luck and
    a red one would be wrong. It is exempt here and covered by the population
    that consumes its fixtures.

    Args:
        sources: Repo-relative path to module source, for every module in the
            survey.

    Returns:
        Repo-relative paths, sorted.
    """
    found: list[str] = []
    for relative, text in sources.items():
        path = Path(relative)
        if path.parts[0] != TEST_DIRECTORY:
            continue
        if path.name.startswith("test_") or path.name in _NOT_A_DETECTOR:
            continue
        if any(ships_a_grading_statement(node) for node in functions(ast.parse(text))):
            continue
        found.append(relative)
    return sorted(found)


def detector_coverage(sources: dict[str, str]) -> dict[str, list[str]]:
    """Every detector module, to the graded members that call into it.

    A DETECTOR GRADES NOTHING BY ITSELF. It answers, and something else decides
    whether the answer is right - so it is covered exactly when a member of the
    population calls into it, and a detector nothing graded calls is a detector
    nothing grades. That is the same relation :func:`grading_routes` resolves,
    read in the other direction and one module at a time.

    Both spellings of the call are read, because both are shipped: a name
    imported from the detector and called directly, and the detector imported
    as a module with a method called on it.

    Args:
        sources: Repo-relative path to module source, for every module in the
            survey.

    Returns:
        Repo-relative detector path to ``module::name`` for each graded caller.
    """
    trees = {relative: ast.parse(text) for relative, text in sources.items()}
    coverage: dict[str, list[str]] = {relative: [] for relative in detector_modules(sources)}
    for detector, callers in coverage.items():
        origin = _module_path(detector)
        for relative, tree in trees.items():
            if relative == detector:
                continue
            direct, indirect = _names_reaching(tree, origin)
            if not direct and not indirect:
                continue
            callers.extend(
                f"{relative}::{node.name}"
                for node in functions(tree)
                if is_population_member(node) and _calls_into(node, direct, indirect)
            )
    return coverage


def _names_reaching(tree: ast.Module, origin: str) -> tuple[frozenset[str], frozenset[str]]:
    """The local spellings through which one module can reach another.

    Args:
        tree: The calling module, parsed.
        origin: The dotted module being reached.

    Returns:
        ``(imported names, module aliases)`` under their local spellings.
    """
    direct: set[str] = set()
    aliases: set[str] = set()
    tail = origin.rsplit(".", 1)[-1]
    package = origin.rsplit(".", 1)[0] if "." in origin else ""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            if node.module == origin:
                direct |= {alias.asname or alias.name for alias in node.names}
            elif node.module == package:
                aliases |= {
                    alias.asname or alias.name for alias in node.names if alias.name == tail
                }
        if isinstance(node, ast.Import):
            aliases |= {alias.asname or alias.name for alias in node.names if alias.name == origin}
    return frozenset(direct), frozenset(aliases)


def _calls_into(
    node: ast.FunctionDef | ast.AsyncFunctionDef, direct: frozenset[str], aliases: frozenset[str]
) -> bool:
    """Whether one function calls a name that reaches another module.

    Args:
        node: The calling function.
        direct: Names imported from the reached module.
        aliases: Local spellings of the reached module itself.

    Returns:
        True if it calls into it either way.
    """
    for statement in own_statements(node):
        for inner in ast.walk(statement):
            if not isinstance(inner, ast.Call):
                continue
            called = inner.func
            if isinstance(called, ast.Name) and called.id in direct:
                return True
            if (
                isinstance(called, ast.Attribute)
                and isinstance(called.value, ast.Name)
                and called.value.id in aliases
            ):
                return True
    return False


# ---------------------------------------------------------------------------
# Whether an assertion actually RAN - the only channel here that is not static
# ---------------------------------------------------------------------------


def grading_statement_lines(function: Callable[..., object]) -> frozenset[int]:
    """The lines a function's grading statements sit on, read from its own source.

    Args:
        function: A live function object.

    Returns:
        The line numbers of its grading statements.

    Raises:
        RuntimeError: If the source cannot be located, or if the name is
            defined more than once in it. Guessing which definition was meant
            would make the count below a claim about a function nobody chose.
    """
    path = inspect.getsourcefile(function)
    if path is None:
        raise RuntimeError(f"{function.__name__} has no source file to read its grading from")
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    matches = [node for node in functions(tree) if node.name == function.__name__]
    if len(matches) != 1:
        raise RuntimeError(
            f"{function.__name__} is defined {len(matches)} time(s) in its own source, so "
            "which definition ran cannot be decided"
        )
    return frozenset(
        statement.lineno
        for statement in own_statements(matches[0])
        if is_grading_statement(statement)
    )


def observed_grading(function: Callable[..., object], *args: object, **kwargs: object) -> int:
    """How many of a function's grading statements ACTUALLY RAN during one call.

    EVERY OTHER RULE IN THIS MODULE IS STATIC, and none of them can answer this
    question. A gutting whose condition is opaque at parse time - the residual
    :func:`conditional_exits` bounds rather than decides - is decided here in
    one call, because execution is not a matter of opinion. So is an assertion
    that was never reached for a reason nobody wrote down.

    WHAT THIS DOES NOT DO, and the gap is the point rather than an oversight.
    It grades ONE CALL of ONE function that something has chosen to call. It is
    not applied to the population: doing that means counting while the suite
    itself runs, which is a collection hook in ``tests/conftest.py``, and this
    module cannot install one. The population is covered statically; this
    covers whatever a caller hands it, exactly.

    The hook is installed globally because that is the only way to see a frame
    being entered, and it is narrowed to this function's own code object
    immediately. It is restored in a ``finally`` - including when the call
    raises, which is the normal outcome when a grading statement does its job.

    Args:
        function: The function to call.
        args: Positional arguments to call it with.
        kwargs: Keyword arguments to call it with.

    Returns:
        How many grading statements were executed.
    """
    lines = grading_statement_lines(function)
    code = function.__code__
    counted = 0

    def within(frame: FrameType, event: str, _arg: object) -> _Tracer | None:
        nonlocal counted
        if event == "line" and frame.f_lineno in lines:
            counted += 1
        return within

    def entering(frame: FrameType, event: str, arg: object) -> _Tracer | None:
        return within(frame, event, arg) if frame.f_code is code else None

    previous = sys.gettrace()
    sys.settrace(entering)
    try:
        function(*args, **kwargs)
    finally:
        sys.settrace(previous)
    return counted


# ---------------------------------------------------------------------------
# The tools, the gates and the guards
# ---------------------------------------------------------------------------


def defines(text: str, name: str) -> bool:
    """Whether a module defines a module-level function by that name.

    Args:
        text: The module's source.
        name: The function name.

    Returns:
        True if it is defined at module scope.
    """
    return module_function(text, name) is not None


def module_function(text: str, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """The named module-level function, if the module defines one.

    Args:
        text: The module's source.
        name: The function name.

    Returns:
        The node, or None.
    """
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return node
    return None


def tool_modules(relatives: list[str]) -> list[str]:
    """Every tracked module in a tool directory.

    Args:
        relatives: Repo-relative Python paths.

    Returns:
        Repo-relative paths, sorted.
    """
    return sorted(
        relative for relative in relatives if Path(relative).parent.as_posix() in TOOL_DIRECTORIES
    )


def guard_function_names(text: str) -> list[str]:
    """Every module-level ``guard_`` function a tool defines.

    Args:
        text: The tool's source.

    Returns:
        Names in source order.
    """
    return [
        node.name
        for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("guard_")
    ]


def guard_tools(root: Path, relatives: list[str]) -> list[str]:
    """Every tracked tool that ships at least one guard.

    Args:
        root: The repository root.
        relatives: Repo-relative Python paths.

    Returns:
        Repo-relative paths, sorted.
    """
    return sorted(
        relative
        for relative in tool_modules(relatives)
        if guard_function_names((root / relative).read_text(encoding="utf-8"))
    )


def hook_invoked_tools(root: Path) -> list[str]:
    """Every tool a tracked git hook invokes, read from the hooks themselves.

    These are the modules standing in a BLOCKING position, so "can it report a
    failure at all" is a real question about them. The hooks are frozen
    (CLAUDE.md section 6); they are READ here and never written.

    Args:
        root: The repository root.

    Returns:
        Repo-relative paths, sorted.
    """
    found: set[str] = set()
    directory = root / HOOK_DIRECTORY
    if not directory.is_dir():
        return []
    for hook in sorted(directory.iterdir()):
        if hook.is_file():
            found.update(_TOOL_REFERENCE.findall(hook.read_text(encoding="utf-8")))
    return sorted(found)


def failure_exits(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Every way a function can report failure to a caller or to the shell.

    A gate that cannot reach a non-zero outcome cannot block anything, whatever
    else it does. That is checkable from the source without running it, and it
    is the only liveness question this module can ask of a tool that ships no
    guard and no assertion.

    Args:
        node: A function node.

    Returns:
        A description of each failure route, in source order.
    """
    found: list[str] = []
    for statement in own_statements(node):
        if isinstance(statement, ast.Return) and statement.value is not None:
            value = statement.value
            if isinstance(value, ast.Constant):
                if value.value not in (0, None, False):
                    found.append(f"line {statement.lineno}: returns {value.value!r}")
            else:
                found.append(f"line {statement.lineno}: returns a computed code")
        if isinstance(statement, ast.Raise):
            name = _dotted(statement.exc).split(".")[-1] if statement.exc else ""
            if name == "SystemExit":
                found.append(f"line {statement.lineno}: raises SystemExit")
    return sorted(found)


# ---------------------------------------------------------------------------
# Forcing a guard
# ---------------------------------------------------------------------------

#: A document that breaks several stated rules of this project at once - a
#: non-ASCII byte (CLAUDE.md non-negotiable 4), a dated heading inside a file
#: declaring itself LIVE (the dated-section rule), an unparseable ownership
#: table, and enough bytes to blow every documentation budget. It is ONE
#: authored artifact rather than nine per-guard fixtures: the tree is known-bad,
#: not the input to any particular guard.
KNOWN_BAD_DOCUMENT: Final = (
    "# Known-bad fixture\n"
    "\n"
    "Section status: LIVE\n"
    "\n"
    "## 2026-01-01 - this heading dates a section the header calls live\n"
    "\n"
    "not a table, not json, not python, not a pin\n"
    "\x80\n"
) + ("filler to blow every documented byte budget. " * 4000)


def write_known_bad_tree(root: Path, relatives: list[str]) -> None:
    """Fill a directory with a tree every guard should have something to say about.

    The FILE NAMES are the real tree's, so a guard looking for a specific path
    finds one; the CONTENT is the known-bad document, so what it finds is
    wrong. Neither half names a guard.

    Args:
        root: An empty directory to build in.
        relatives: Repo-relative paths to recreate.
    """
    payload = KNOWN_BAD_DOCUMENT.encode("utf-8", errors="surrogateescape")
    for relative in relatives:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def unreadable(*_args: object, **_kwargs: object) -> bytes:
    """Fail every read the way a permission error does.

    The filename is the injected literal rather than a real path, so a guard
    that renders the exception leaks a value the test owns instead of one the
    machine owns (CLAUDE.md non-negotiable 12).

    Args:
        _args: Ignored.
        _kwargs: Ignored.

    Returns:
        Never; the annotation exists so the stand-in matches what it replaces.

    Raises:
        PermissionError: Always.
    """
    raise PermissionError(13, "Permission denied", INJECTED_FILENAME)


def guard_answers(module: Any, root: Path, files: list[Path], source: str) -> list[GuardAnswer]:
    """Ask every derived guard about one tree.

    Arguments are dispatched by PARAMETER NAME rather than by position, so a
    guard taking a different set of them needs no entry anywhere: a name this
    does not know is a loud KeyError rather than a guard quietly skipped.

    Args:
        module: The loaded guard tool.
        root: The root to point every guard at.
        files: The enumerated file list.
        source: How that list was enumerated.

    Returns:
        One answer per derived guard, in the order the tool defines them.
    """
    available: dict[str, object] = {"root": root, "files": files, "source": source}
    answers: list[GuardAnswer] = []
    for name in guard_function_names(inspect.getsource(module)):
        function = getattr(module, name)
        # A KEYWORD-ONLY PARAMETER CARRYING A DEFAULT IS A TEST SEAM, NOT PART OF
        # THE CALLING CONTRACT. The driver calls every guard with root, files and
        # source and nothing else, so a defaulted keyword-only knob is never
        # supplied in production and this harness must grade the same call the
        # driver makes. Binding it here would make a legitimate guard design
        # unrepresentable - guard (k) carries three recorded levels this way so
        # its ORDER arms can isolate the order relation from the ratchet.
        #
        # ANYTHING ELSE IS STILL A HARD REFUSAL. A parameter that is neither
        # available nor a defaulted keyword-only one would let a guard dodge
        # grading by widening its signature, so it raises rather than being
        # skipped. An ungraded guard is the unrun-gate class (CONVENTIONS 7.2).
        arguments = []
        for parameter in inspect.signature(function).parameters.values():
            if parameter.name in available:
                arguments.append(available[parameter.name])
                continue
            keyword_only = parameter.kind is inspect.Parameter.KEYWORD_ONLY
            if keyword_only and parameter.default is not inspect.Parameter.empty:
                continue
            message = (
                f"{name} takes a parameter this harness cannot supply: "
                f"{parameter.name!r} ({parameter.kind}). A guard is called with "
                "root, files and source. Widen those, or make the parameter "
                "keyword-only with a default so it is plainly a test seam."
            )
            raise AssertionError(message)
        guard, skips = function(*arguments)
        answers.append(
            GuardAnswer(
                function=name,
                guard_id=guard["id"],
                status=guard["status"],
                skips=len(skips),
                rendered=" ".join(
                    [*guard["detail"], *(f"{skip['path']} {skip['reason']}" for skip in skips)]
                ),
            )
        )
    return answers


def silently_green(answer: GuardAnswer) -> bool:
    """Whether a guard passed a tree it could not read while recording nothing.

    CONVENTIONS.md section 15.1, which ``tools/drift_guard.py`` prints on every
    run: a guard may be green while self-excusing, and a green verdict means
    nothing without the list of what was never looked at.

    DEFEATED ON ITS OWN by fabricating a skip record, measured. It is kept
    because it is cheap and because a criterion that catches the LAZIEST
    gutting is worth having beside the ones that catch the careful kind.

    Args:
        answer: One answer about a blind tree.

    Returns:
        True if the guard is not grading.
    """
    return answer.status == "PASS" and answer.skips == 0


def answers_the_same_about_every_tree(answers: list[GuardAnswer]) -> bool:
    """Whether a guard said the identical thing about materially different trees.

    DEFEATED ON ITS OWN by rendering an input into the detail while reading
    nothing, measured: distinctness is a PROXY for reading the tree, and any
    guard that echoes its root satisfies it. Kept for the same reason as the
    criterion above, and :func:`cannot_be_forced_to_fail` is the one that is a
    property of guarding rather than a proxy for it.

    Args:
        answers: The same guard's answers about two or more trees.

    Returns:
        True if every answer is identical.
    """
    return len({answer.signature() for answer in answers}) <= 1


def cannot_be_forced_to_fail(answer: GuardAnswer) -> bool:
    """Whether a guard answered PASS about a tree built to be wrong.

    THE CRITERION THAT IS NOT A PROXY. The two above ask whether a guard SAID
    something or whether what it said VARIED. This asks the only question that
    is actually about guarding: handed a tree that breaks the rules, does it
    report? A guard that cannot be made to fail is not guarding, whatever it
    renders and however much its rendering varies.

    Args:
        answer: One answer about the known-bad tree.

    Returns:
        True if the guard passed a tree it should have failed.
    """
    return answer.status == "PASS"
