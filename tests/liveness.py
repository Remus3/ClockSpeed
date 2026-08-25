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

  A STATICALLY CONSTANT ASSERTION GRADES NOTHING. ``assert True`` executes,
  passes, and asserts nothing about the program. It must not count as a grading
  statement, or eleven characters restore any gutting the rest of this module
  closes.

  A STATICALLY CONSTANT BRANCH IS NOT A BRANCH. ``if not globals():`` never
  runs its body and ``if globals():`` always does. Folding both is what makes
  the difference between a CONDITIONAL skip - the legitimate idiom, which this
  tree uses in every skip it ships - and a skip written to look conditional.
  The asymmetry is positional and decidable, not a matter of judgement.

  AN EXIT IS AN EXIT WHATEVER IT IS SPELLED. ``return``, falling off the end,
  ``pytest.skip(...)``, ``raise pytest.skip.Exception(...)`` and an
  unconditional ``@pytest.mark.skip`` decorator all leave the function without
  grading. The decorator is the one anybody actually uses to disable a test and
  it is not a statement at all, so ``decorator_list`` is read too.

  A GRADER IS NOT A NAMING CONVENTION, AND THIS MODULE CAN ONLY SEE ONE. It
  reads a call as grading when the name begins with ``assert`` or is one of
  pytest's own spellings. Widening that to ``require``, ``check``, ``verify``,
  ``ensure`` and ``confirm`` was TRIED AND MEASURED: everything it adds is a
  save-library parser named ``int32`` or ``string``, or a dispatcher like
  ``check_content`` that routes to other checks - NOT ONE IS A TEST - and the
  findings it produced were all false positives, some inside a frozen file. In
  this tree those verbs name parsers; ``assert`` names graders. So the
  vocabulary stays narrow on a semantic ground, and the residual is GRADED
  rather than described: :func:`vocabulary_boundary`
  re-derives the difference on every run, and a test whose only grading route
  is a name outside the vocabulary is reported by it. That is the failure this
  boundary actually has - rename a grader and its callers leave the population
  in silence - and it is the one thing about it that is now checked.

WHERE THE ANALYSIS IS DELIBERATELY GENEROUS, and the cost is a number this
module recomputes rather than a sentence. A loop may run zero times and a
``try`` body may raise partway, so strictly neither guarantees anything to the
exit after it. Read strictly, this tree reports a large set of correct
idiomatic bodies of the form ``for node in walk(tree): if isinstance(...):
assert ...``. The generosity is taken - a loop grades if its body carries
grading, a ``try`` grades if its body ends graded or a handler fails - and
every member that leans on either is COUNTED and re-derived by :func:`survey`.

WHAT IS IN THE POPULATION. A member is a function that SHIPS A GRADING
STATEMENT and RETURNS NO VALUE. The first half is the derivation the acceptance
asks for. The second keeps out utilities that carry a sanity assert on the way
to a value - and they are NOT dropped: they are graded by the one rule that is
decidable for them, that a CONSTANT return reached without grading is a hole,
and counted besides.

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
from pathlib import Path
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
_GRADING_CALLS: Final = frozenset({"fail", "raises", "warns"})

#: Calls that LEAVE the function by raising, rather than by failing.
EXITING_CALLS: Final = frozenset({"skip", "xfail", "exit"})

#: Zero-argument builtins whose result is always truthy. Folding these is what
#: separates a real conditional from one written to look like one.
_ALWAYS_TRUTHY_CALLS: Final = frozenset({"globals", "locals", "object", "dict", "vars"})

#: Marks that disable a test outright when applied with no runtime condition.
_DISABLING_MARKS: Final = frozenset({"skip", "xfail"})

#: The mark that disables a test only when its condition holds.
_CONDITIONAL_MARK: Final = "skipif"

#: Exception names that mean "leave without failing" when raised directly.
_EXITING_EXCEPTIONS: Final = frozenset({"Skipped", "XFailed"})

#: How many dotted parts a qualified name needs before its tail means anything.
_QUALIFIED_PARTS: Final = 2

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
            return a value. Counted, AND graded by the fabricated-return rule.
        dead_grading: Grading statements that can never run. Hard.
        outside: Tests shipping no grading statement at all, split into those
            that at least call something and those that do not.
        vocabulary_boundary: Functions a WIDER grading vocabulary would call
            graders and the shipped one does not. Counted, not failed - except
            that a ``test_`` function in here has no grading route this module
            can see, which is.
        modules: What was read.
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
    return bare.startswith(prefixes) or bare in _GRADING_CALLS


def is_grading_statement(node: ast.stmt) -> bool:
    """Whether one statement grades.

    An ``assert`` whose test is statically TRUE is excluded. It executes and
    passes and says nothing about the program, so counting it lets eleven
    characters restore any gutting this module closes. A statically FALSE one
    is kept: that is a deliberate failure and it does grade.

    Args:
        node: A statement.

    Returns:
        True for a real assertion, a call to a grader, and a ``with`` whose
        context manager is ``pytest.raises`` or ``pytest.warns``.
    """
    if isinstance(node, ast.Assert):
        return static_truth(node.test) is not True
    if isinstance(node, ast.Expr):
        return is_grading_call(_called_name(node.value))
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
    and true; the seven this tree ships all test the running machine and none
    of them is.

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
        if mark in _DISABLING_MARKS:
            found.append((decorator.lineno, dotted))
        elif conditional:
            found.append((decorator.lineno, f"{dotted} on a constant condition"))
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


def carries_grading(body: list[ast.stmt]) -> bool:
    """Whether a statement list holds a grading statement anywhere inside it.

    The EXISTENTIAL question, used for a loop body. A loop over an empty
    collection grades nothing, so the strict answer for the exit after it is
    "not graded" - and that answer reports a large set of correct bodies on
    this tree. The generosity is taken and counted rather than hidden.

    Args:
        body: The statements to look through.

    Returns:
        True if grading appears anywhere within.
    """
    return any(
        isinstance(inner, ast.stmt) and is_grading_statement(inner)
        for node in body
        for inner in ast.walk(node)
    )


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


def ships_a_grading_statement(node: ast.AST) -> bool:
    """Whether a function grades anywhere in its own body.

    Args:
        node: A function node.

    Returns:
        True if it carries at least one grading statement.
    """
    return any(is_grading_statement(statement) for statement in own_statements(node))


def is_population_member(node: ast.AST) -> bool:
    """Whether a function is a control or a grader.

    Args:
        node: A function node.

    Returns:
        True if it grades and returns nothing.
    """
    return ships_a_grading_statement(node) and not returns_a_value(node)


# ---------------------------------------------------------------------------
# The analysis
# ---------------------------------------------------------------------------


class _Walk:
    """One pass over one function, accumulating holes and generosity flags."""

    def __init__(self, *, fabricated_returns_only: bool = False) -> None:
        """Start with nothing found and neither generosity used.

        Args:
            fabricated_returns_only: Report a ``return`` only when it hands
                back a FABRICATED value. Used for value-returning graders, where
                a boundary return of a computed value is legitimate and cannot
                be told from a gutting.
        """
        self.holes: list[tuple[int, str]] = []
        self.leaned_on_loop = False
        self.leaned_on_try = False
        self._fabricated_returns_only = fabricated_returns_only

    def _record_return(self, node: ast.Return) -> None:
        """Record an ungraded return, subject to the fabrication filter.

        DECLINING IS NOT FABRICATING, and that is the whole distinction. A
        grader returning ``None`` without grading has said "I have no answer",
        which this tree does in a census that finds no save library on the
        machine, and it is correct there. A grader returning a
        LITERAL VALUE without grading has answered without looking, and its
        caller then compares against a number nothing measured, which is how
        the demonstrated ``if globals(): return 1`` turns a consumer's
        assertion into a tautology.

        THE RESIDUAL THIS LEAVES IS NAMED: a value-returning grader gutted to
        return ``None`` early is not reported here.

        Args:
            node: The return statement.
        """
        if self._fabricated_returns_only:
            fabricated = isinstance(node.value, ast.Constant) and node.value.value is not None
            if not fabricated:
                return
        self.holes.append((node.lineno, "return"))

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
                    self._record_return(node)
                return True
            if is_exiting_statement(node):
                if unconditional and not graded:
                    self.holes.append((node.lineno, "exit without grading"))
                return True
            if isinstance(node, ast.Raise):
                return True
            if is_grading_statement(node):
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
            return self.scan(node.body, graded, unconditional=unconditional) or graded
        if isinstance(node, ast.For | ast.AsyncFor | ast.While):
            return self._loop(node, graded)
        if isinstance(node, ast.Try):
            return self._try(node, graded, unconditional=unconditional)
        return self._match(node, graded) if isinstance(node, ast.Match) else graded

    def _loop(self, node: ast.For | ast.AsyncFor | ast.While, graded: bool) -> bool:
        """A loop, which may run zero times and is credited generously anyway.

        Args:
            node: The loop.
            graded: Whether grading has already happened.

        Returns:
            Whether the path leaving it is graded.
        """
        self.scan(node.body, graded)
        self.scan(node.orelse, graded)
        if not graded and carries_grading(node.body):
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

        A handler that converts the failure - by raising, or by calling
        ``pytest.fail`` - is not swallowing it and is not recorded.

        Args:
            node: A ``try`` statement.
        """
        if not carries_grading(node.body):
            return
        for handler in node.handlers:
            silent = all(
                isinstance(statement, ast.Pass)
                or (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant))
                for statement in handler.body
            )
            if silent:
                self.holes.append((handler.lineno, "failure discarded"))


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
    node: ast.FunctionDef | ast.AsyncFunctionDef, *, fabricated_returns_only: bool = False
) -> _Walk:
    """Run the analysis over one function.

    Args:
        node: A function node.
        fabricated_returns_only: Report only returns of a fabricated literal.

    Returns:
        The completed walk, holding every hole and both generosity flags. The
        implicit end-of-function exit and every disabling decorator are
        recorded as holes.
    """
    walk = _Walk(fabricated_returns_only=fabricated_returns_only)
    walk.holes.extend(
        (line, f"disabled by {description}") for line, description in disabling_decorators(node)
    )
    if not walk.scan(_significant_body(node), False, unconditional=True):
        walk.holes.append((node.lineno, "end of function"))
    return walk


def dead_grading(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[int]:
    """Grading statements that can never run.

    Two ways in: an exit precedes it at the same level, or it sits inside a
    branch a constant condition never takes.

    Args:
        node: A function node.

    Returns:
        The lines of unreachable grading statements.
    """
    found: list[int] = []
    lists: list[tuple[list[ast.stmt], bool]] = [(_significant_body(node), False)]
    while lists:
        body, already_dead = lists.pop()
        dead = already_dead
        for statement in body:
            if dead and is_grading_statement(statement):
                found.append(statement.lineno)
            if isinstance(statement, ast.Return | ast.Raise) or is_exiting_statement(statement):
                dead = True
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            if isinstance(statement, ast.If):
                decided = static_truth(statement.test)
                lists.append((statement.body, dead or decided is False))
                lists.append((statement.orelse, dead or decided is True))
                continue
            for field in ("body", "orelse", "finalbody"):
                nested = getattr(statement, field, None)
                if nested:
                    lists.append((list(nested), dead))
            lists.extend(
                (list(handler.body), dead) for handler in getattr(statement, "handlers", None) or []
            )
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


def tests_outside_the_population(module: str, text: str) -> tuple[list[Member], list[Member]]:
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

    Returns:
        ``(exercising, inert)`` - those that call something and those that do
        not.
    """
    exercising: list[Member] = []
    inert: list[Member] = []
    for node in functions(ast.parse(text)):
        if not node.name.startswith("test_") or ships_a_grading_statement(node):
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


def survey_source(module: str, text: str) -> Survey:
    """Derive every population and every residual for one module.

    Args:
        module: How the module should be named in a report.
        text: Its source.

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
        if not ships_a_grading_statement(node):
            continue
        entry = Member(module, node.name, node.lineno)
        dead.extend(
            Finding(module, node.name, line, "unreachable grading") for line in dead_grading(node)
        )
        if returns_a_value(node):
            value_returning.append(entry)
            walk = grade(node, fabricated_returns_only=True)
            findings.extend(
                Finding(module, node.name, line, "returns a fabricated value")
                for line, kind in walk.holes
                if kind == "return"
            )
            continue
        members.append(entry)
        walk = grade(node)
        findings.extend(Finding(module, node.name, line, kind) for line, kind in walk.holes)
        if walk.leaned_on_loop:
            loop_leaned.append(entry)
        if walk.leaned_on_try:
            try_leaned.append(entry)
    return Survey(
        members=members,
        findings=findings,
        loop_leaned=loop_leaned,
        try_leaned=try_leaned,
        value_returning=value_returning,
        dead_grading=dead,
        outside=tests_outside_the_population(module, text),
        vocabulary_boundary=vocabulary_boundary(module, text),
        modules=[module],
    )


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
    merged = Survey([], [], [], [], [], [], ([], []), [], [])
    for relative in relatives:
        one = survey_source(relative, (root / relative).read_text(encoding="utf-8"))
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
    return merged


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
        arguments = [available[parameter] for parameter in inspect.signature(function).parameters]
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
