#!/usr/bin/env python3
"""CS-846 - is a shipped control still grading, and is a shipped guard still guarding?

THE DEFECT. A control that stops grading still reports as passed, and a guard
that stops guarding still answers PASS. Nothing distinguishes graded-and-held
from stopped-before-grading. It is the same shape as this project's standing
finding about mutation testing, where a mutant that never applied and one that
survived produce identical output: the ABSENCE of a signal is being read as the
PRESENCE of a negative result.

THE FIRST VERSION OF THIS MODULE WAS REFUTED, AND THE REFUTATION SHAPES
EVERYTHING BELOW. It reported a hole only at an explicit ``ast.Return``.
Measured on this tree by the adversary that graded it: 1855 of 1857 members
carry no ``return`` statement anywhere, so for all but two of them the analysis
was structurally incapable of reporting anything and its green was a claim
about a shape they do not contain. Four gutting shapes were demonstrated
silent, none of which uses a return - wrapping a body in ``if not globals():``,
swallowing the assertions in a ``try``, and an unconditional ``pytest.skip`` at
the head. So the unit of analysis here is the EXIT, not the return statement,
and the implicit end-of-function exit counts as one.

WHY THE ANALYSIS IS GENEROUS ABOUT LOOPS AND ``try``, WITH THE COST MEASURED
RATHER THAN ASSUMED. Grading the end-of-function exit strictly - a loop that
may not run grades nothing, a ``try`` body that may raise partway grades
nothing - reports 95 members of this tree, and every one of them is correct
idiomatic code of the form ``for node in walk(tree): if isinstance(...): assert
...``. A check that reports 95 false positives is a check that gets switched
off. Measured across the whole rule matrix, exactly one setting reports ZERO on
this tree while still catching the wrapping shape: a loop grades if its body
CONTAINS a grading statement anywhere, and a ``try`` grades if its body ends
graded. That is the setting used, and the two generosities are not hidden -
every member that leans on either is counted and re-derived by
:func:`survey`, so the exemption is a measured set rather than a sentence.

THE THREE HARD RULES, each measured at ZERO on this tree and each closing one
demonstrated kill.

  1. AN EXIT REACHED WITHOUT GRADING - a ``return``, or falling off the end.
     Closes the bare return, the conditional return, and the ``if not
     globals():`` wrap.
  2. AN EXITING CALL AT A MEMBER'S TOP LEVEL, reached without grading -
     ``pytest.skip``, ``xfail`` or ``exit``. Closes the skip-at-the-head shape.
     It is scoped to the TOP LEVEL because a CONDITIONAL skip is the legitimate
     idiom and this tree carries 38 of them and no unconditional one.
  3. A ``try`` THAT GRADES AND CARRIES A SILENTLY SWALLOWING HANDLER. Closes
     the swallow shape.

WHAT IS IN THE POPULATION, and both halves of the filter are load-bearing.

A member is a function that SHIPS A GRADING STATEMENT and RETURNS NO VALUE.

  - Ships a grading statement. That is the derivation the acceptance asks for -
    the population comes from the shipped assertions rather than from the word
    "control" or the word "guard" - so it covers both structures this item was
    filed on: a ``test_`` function that asserts, and a non-test helper that
    asserts on a caller's behalf.

  - Returns no value. A grader computes nothing for a caller; it either says
    nothing or it fails. Without this the population swallows utilities that
    carry a sanity assert on the way to a value and legitimately return early
    on a boundary case. Those are NOT silently dropped - they are counted and
    named by :func:`survey` as their own residual, because the adversary
    measured that the filter excludes 78 functions and demonstrated a silent
    kill inside one of them.

THE GUARD HALF IS A DIFFERENT MECHANISM BECAUSE GUARDS GRADE DIFFERENTLY. A
``guard_`` function does not assert; it RETURNS a status, and returning PASS is
its correct answer nearly always. Two criteria are applied, and the second
exists because the first was defeated for the length of one dict literal.

  - NOT SILENTLY GREEN. Run against a tree it cannot read, a guard answering
    PASS while recording no skip is not grading (CONVENTIONS.md section 15.1,
    which ``tools/drift_guard.py`` prints a banner about on every run).
  - THE ANSWER DEPENDS ON THE TREE. A guard is run against three materially
    different trees - the real one, an empty one, and one whose every read
    fails - and its rendered answers must not all be identical. A guard
    replaced by a constant return answers the same thing about all three
    WHATEVER that constant is, so fabricating a skip record to satisfy the
    first criterion does not satisfy this one.
"""

from __future__ import annotations

import ast
import inspect
import re
import subprocess
from pathlib import Path
from typing import Any, Final, NamedTuple

#: Call names that grade. ``assert`` covers the delegated graders this project
#: writes - ``assert_reported_without_the_filename``,
#: ``_assert_no_test_is_gutted`` - and the leading underscore is stripped first
#: so a private grader is not read as a different kind of thing. ``raises`` and
#: ``warns`` are the context-manager spellings and ``fail`` is the
#: unconditional one.
_GRADING_CALLS: Final = frozenset({"fail", "raises", "warns"})

#: Calls that LEAVE the function by raising. An unconditional one at a member's
#: top level ends the test before anything below it runs, which is the gutting
#: shape wearing pytest's own vocabulary.
EXITING_CALLS: Final = frozenset({"skip", "xfail", "exit"})

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
#: derive which tools actually stand in a blocking position; never written.
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
        loop_leaned: Members whose end exit is graded only because a loop body
            carries the grading. Counted, not failed.
        try_leaned: Members whose end exit is graded only because a ``try``
            body carries it. Counted, not failed.
        value_returning: Graders the population filter excludes because they
            return a value. Counted, not failed.
        dead_grading: Grading statements that can never run. Hard.
        outside: Tests shipping no grading statement at all, split into those
            that at least call something and those that do not.
        modules: What was read.
    """

    members: list[Member]
    findings: list[Finding]
    loop_leaned: list[Member]
    try_leaned: list[Member]
    value_returning: list[Member]
    dead_grading: list[Finding]
    outside: tuple[list[Member], list[Member]]
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


def is_grading_call(name: str | None) -> bool:
    """Whether a called name grades.

    Args:
        name: The bare called name, or None.

    Returns:
        True for an ``assert``-prefixed grader and for the pytest spellings.
    """
    if name is None:
        return False
    bare = name.lstrip("_")
    return bare.startswith("assert") or bare in _GRADING_CALLS


def is_grading_statement(node: ast.stmt) -> bool:
    """Whether one statement grades.

    Args:
        node: A statement.

    Returns:
        True for ``assert``, for a bare call to a grader, and for a ``with``
        whose context manager is ``pytest.raises`` or ``pytest.warns``.
    """
    if isinstance(node, ast.Assert):
        return True
    if isinstance(node, ast.Expr):
        return is_grading_call(_called_name(node.value))
    if isinstance(node, ast.With | ast.AsyncWith):
        return any(is_grading_call(_called_name(item.context_expr)) for item in node.items)
    return False


def is_exiting_statement(node: ast.stmt) -> bool:
    """Whether a statement leaves the function by raising through pytest.

    Args:
        node: A statement.

    Returns:
        True for a bare ``pytest.skip``, ``pytest.xfail`` or ``pytest.exit``.
    """
    return isinstance(node, ast.Expr) and _called_name(node.value) in EXITING_CALLS


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

    This is the EXISTENTIAL question, used for a loop body only. A loop over an
    empty collection grades nothing, so the honest answer for the exit after it
    is "not graded" - and asking that honestly reports 95 correct members of
    this tree. The generosity is taken deliberately and its cost is counted.

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

    def __init__(self) -> None:
        """Start with nothing found and neither generosity used."""
        self.holes: list[tuple[int, str]] = []
        self.leaned_on_loop = False
        self.leaned_on_try = False

    def scan(self, body: list[ast.stmt], graded: bool, *, top: bool = False) -> bool:
        """Walk a statement list, recording every exit reached without grading.

        ``graded`` means grading has DEFINITELY happened on every path reaching
        this point.

        Args:
            body: The statements to walk.
            graded: Whether grading has already happened on this path.
            top: Whether this is the function's own top-level statement list.
                Only there does an exiting call count as a hole, because a
                CONDITIONAL skip is the legitimate idiom.

        Returns:
            Whether the path leaving this block is graded or has terminated.
        """
        for node in body:
            if isinstance(node, ast.Return):
                if not graded:
                    self.holes.append((node.lineno, "return"))
                return True
            if isinstance(node, ast.Raise):
                return True
            if is_exiting_statement(node):
                if top and not graded:
                    self.holes.append((node.lineno, "exiting call"))
                return True
            if is_grading_statement(node):
                if isinstance(node, ast.With | ast.AsyncWith):
                    self.scan(node.body, True)
                graded = True
                continue
            graded = self._compound(node, graded)
        return graded

    def _compound(self, node: ast.stmt, graded: bool) -> bool:
        """Walk one compound statement and report what the path leaving it knows.

        Args:
            node: A compound statement.
            graded: Whether grading has already happened on the path to it.

        Returns:
            Whether the path leaving the statement is graded.
        """
        if isinstance(node, ast.If):
            taken = self.scan(node.body, graded)
            other = self.scan(node.orelse, graded) if node.orelse else graded
            return graded or (taken and other)
        if isinstance(node, ast.With | ast.AsyncWith):
            return self.scan(node.body, graded) or graded
        if isinstance(node, ast.For | ast.AsyncFor | ast.While):
            self.scan(node.body, graded)
            self.scan(node.orelse, graded)
            if not graded and carries_grading(node.body):
                self.leaned_on_loop = True
                return True
            return graded
        if isinstance(node, ast.Try):
            self._swallowed(node)
            body_graded = self.scan(node.body, graded)
            for handler in node.handlers:
                self.scan(handler.body, graded)
            else_graded = self.scan(node.orelse, graded) if node.orelse else False
            after = graded
            if not graded and (body_graded or else_graded):
                self.leaned_on_try = True
                after = True
            if node.finalbody:
                after = self.scan(node.finalbody, after) or after
            return after
        if isinstance(node, ast.Match):
            for case in node.cases:
                self.scan(case.body, graded)
        return graded

    def _swallowed(self, node: ast.Try) -> None:
        """Record a ``try`` that grades and whose handler discards the failure.

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
                self.holes.append((handler.lineno, "swallowed"))


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


def grade(node: ast.FunctionDef | ast.AsyncFunctionDef) -> _Walk:
    """Run the analysis over one function.

    Args:
        node: A function node.

    Returns:
        The completed walk, holding every hole and both generosity flags. The
        implicit end-of-function exit is recorded as a hole when the path
        leaving the body is ungraded.
    """
    walk = _Walk()
    if not walk.scan(_significant_body(node), False, top=True):
        walk.holes.append((node.lineno, "end of function"))
    return walk


def dead_grading(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[int]:
    """Grading statements that can never run because an exit precedes them.

    This is the one property that holds for a value-returning grader too, so it
    is applied to the whole grading population rather than only the members.

    Args:
        node: A function node.

    Returns:
        The lines of unreachable grading statements.
    """
    found: list[int] = []
    lists: list[list[ast.stmt]] = [_significant_body(node)]
    while lists:
        body = lists.pop()
        dead = False
        for statement in body:
            if dead and is_grading_statement(statement):
                found.append(statement.lineno)
            if isinstance(statement, ast.Return | ast.Raise) or is_exiting_statement(statement):
                dead = True
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            for field in ("body", "orelse", "finalbody"):
                nested = getattr(statement, field, None)
                if nested:
                    lists.append(list(nested))
            lists.extend(
                list(handler.body) for handler in getattr(statement, "handlers", None) or []
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
    merged = Survey([], [], [], [], [], [], ([], []), [])
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
    return any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name
        for node in ast.parse(text).body
    )


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
            exception = statement.exc
            name = None
            if isinstance(exception, ast.Call):
                name = _called_name(exception)
            elif isinstance(exception, ast.Name):
                name = exception.id
            if name == "SystemExit":
                found.append(f"line {statement.lineno}: raises SystemExit")
    return sorted(found)


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
    nothing without the list of what was never looked at. Green with no list,
    about a tree it could not read, is what a guard replaced by an early return
    returns.

    THIS CRITERION ALONE IS DEFEATED BY A FABRICATED SKIP RECORD, measured by
    the adversary that graded the first version of this module.
    :func:`answers_the_same_about_every_tree` is what closes that, because a
    fabricated record is still a CONSTANT.

    Args:
        answer: One answer about a blind tree.

    Returns:
        True if the guard is not grading.
    """
    return answer.status == "PASS" and answer.skips == 0


def answers_the_same_about_every_tree(answers: list[GuardAnswer]) -> bool:
    """Whether a guard said the identical thing about materially different trees.

    A guard reads a tree and reports on it. One replaced by a constant return
    reports that constant whatever it is handed - so this catches the plain
    gutting and the gutting dressed up with a fabricated skip alike, without
    knowing anything about what any particular guard does.

    Args:
        answers: The same guard's answers about two or more trees.

    Returns:
        True if every answer is identical.
    """
    return len({answer.signature() for answer in answers}) <= 1
