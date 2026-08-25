#!/usr/bin/env python3
"""CS-846 - is a shipped control still grading, and is a shipped guard still guarding?

THE DEFECT. A control whose body is cut short by an early return before its
only assertion still reports as passed. Nothing distinguishes "asserted and the
assertion held" from "returned before asserting" - both produce a dot. It is
the same shape as this project's standing finding about mutation testing, where
a mutant that never applied and one that survived produce identical output: the
ABSENCE of a signal is being read as the PRESENCE of a negative result.

THE MUTATION THAT MOTIVATES THE ANALYSIS IS CONDITIONAL, NOT BARE. Gutting a
test with a bare ``return`` leaves every statement after it unreachable, and
that IS caught today - mypy runs with ``warn_unreachable`` and
``tests/test_mypy_gate.py`` puts it in the suite, and
``tests/save/reach_guard._gutted_tests`` names the same property locally. Write
it as ``if corpus: return`` instead and neither notices: the assertions below
stay reachable, so no unreachable statement exists to report. The analysis here
therefore keys on whether an exit can be REACHED without grading, not on
whether anything after it is dead.

WHY THE POPULATION IS DERIVED AND NOT LISTED. The property this module checks
already existed, applied by hand: ``tests/save/reach_guard`` ships a gutting
guard, and modules opt into it by calling it on their own ``__file__``. A
refutation pass recorded in that module's own header measured the result - of
the five modules that self-apply its sibling reach guard, two call the gutting
one, and it concluded that the check "is not a rule the package follows, it is
a habit two modules have". Every module that never opted in is invisible to it,
and so is every module outside that package. So the population here comes from
``git ls-files`` plus an AST walk, exactly the way
``tests/test_exception_rendering`` derives its own: a module cannot escape by
not being on a list, because there is no list.

WHAT IS IN THE POPULATION, and both halves of the filter are load-bearing.

A member is a function that SHIPS A GRADING STATEMENT and RETURNS NO VALUE.

  - Ships a grading statement. That is the derivation the acceptance asks for -
    the population comes from the shipped assertions rather than from the word
    "control" or the word "guard". It therefore covers both structures this
    item was filed on: a ``test_`` function that asserts, and a non-test helper
    that asserts on a caller's behalf. The two were reported independently, by
    agents that did not know of each other, which is the evidence the shape is
    not specific to either word.

  - Returns no value. Without it the population swallows ordinary utilities
    that happen to carry a sanity assert and legitimately return early on a
    boundary case - a power helper returning 1 for a zero exponent, a census
    builder returning its rows. Measured on this tree before the filter was
    added: nine such functions, every one a false positive, and none of them a
    grader. A grader computes nothing for a caller; it either says nothing or
    it fails. That is the discriminator, taken from the code rather than from
    an annotation, because an annotation is a claim and the return statement is
    the fact.

WHAT IS NOT COVERED, stated rather than implied, because a guard read as
covering all gutting is the false-guarantee class this project has already paid
for. An exit reached only from inside a loop body that may not run, an
assertion rewritten to a tautology, and a test that grades by calling something
that raises rather than by asserting - none of these leave an ungraded exit and
none of them is reported here. The third is enumerated by
:func:`tests_outside_the_population` so that it is a measured residual with a
shape assertion on it rather than an unexamined remainder.

THE GUARD HALF IS A DIFFERENT MECHANISM BECAUSE GUARDS GRADE DIFFERENTLY. A
``guard_`` function in ``tools/drift_guard.py`` does not assert; it RETURNS a
status, and returning ``PASS`` is its correct behaviour most of the time. So
the ungraded-exit analysis cannot see it, and an early return that yields PASS
is invisible to the whole suite unless something forces the guard to a verdict
it cannot fake. :func:`blind_verdicts` runs each derived guard against a root
whose every read raises, and :func:`silently_green` applies the criterion this
project already states in ``tools/drift_guard.py``'s own skip banner, from
CONVENTIONS.md section 15.1: a guard may be green while self-excusing, but a
green verdict means nothing without the list of what was never looked at. A
guard that can read nothing and reports neither a verdict nor a skip is not
grading - it is returning.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path
from typing import Any, Final, NamedTuple

#: Call names that grade. ``assert`` covers the delegated graders this project
#: writes - ``assert_reported_without_the_filename``,
#: ``_assert_no_test_is_gutted`` - and the leading underscore is stripped
#: first so a private grader is not read as a different kind of thing.
#: ``raises`` and ``warns`` are the context-manager spellings and ``fail`` is
#: the unconditional one.
_GRADING_CALLS: Final = frozenset({"fail", "raises", "warns"})

#: The name a blind read reports having failed on. It is a literal that appears
#: nowhere else in the tree, so a test asserting its absence from guard output
#: is asserting about the injected value and not about a coincidence.
INJECTED_FILENAME: Final = "cs846-blind-read-target"

#: Fields a guard record carries. Read from ``tools/drift_guard.py``'s ``Guard``
#: at the call site rather than imported, because this module is handed the
#: guard module by its caller and must not import a tool to describe one.
_GUARD_FIELDS: Final = ("id", "name", "status", "detail")


class Member(NamedTuple):
    """One derived population member."""

    module: str
    name: str
    line: int


class Finding(NamedTuple):
    """One exit a member can reach without grading."""

    module: str
    name: str
    line: int

    def rendered(self) -> str:
        """Render as a file:line pointer.

        Returns:
            ``module:line name``.
        """
        return f"{self.module}:{self.line} {self.name}"


class Survey(NamedTuple):
    """What one pass over a set of modules found."""

    members: list[Member]
    findings: list[Finding]
    modules: list[str]


class BlindVerdict(NamedTuple):
    """What one guard said about a root it could not read."""

    function: str
    guard_id: str
    status: str
    skips: int
    rendered: str


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


def _scan_compound(node: ast.stmt, graded: bool, holes: list[int]) -> bool:
    """Walk one compound statement and report what the path leaving it knows.

    THE TWO CONSERVATIVE CASES ARE THE POINT, and both refuse to upgrade
    ``graded``.

    A LOOP over an empty collection runs nothing, so an assertion inside one
    guarantees nothing to the code after it. That is the vacuous green this
    project already fights one level down, and treating a loop body as
    guaranteed would import it here.

    A ``try`` body can raise partway, so an assertion inside it is not
    guaranteed either. Only a ``finally`` upgrades, because a ``finally`` runs
    on every way out.

    Args:
        node: A compound statement.
        graded: Whether grading has already happened on the path reaching it.
        holes: Accumulator; the line of every ungraded exit is appended.

    Returns:
        Whether the path leaving the statement is graded.
    """
    if isinstance(node, ast.If):
        taken = _scan(node.body, graded, holes)
        other = _scan(node.orelse, graded, holes) if node.orelse else graded
        return graded or (taken and other)
    if isinstance(node, ast.With | ast.AsyncWith):
        return _scan(node.body, graded, holes) or graded
    if isinstance(node, ast.For | ast.AsyncFor | ast.While):
        _scan(node.body, graded, holes)
        _scan(node.orelse, graded, holes)
    elif isinstance(node, ast.Try):
        _scan(node.body, graded, holes)
        for handler in node.handlers:
            _scan(handler.body, graded, holes)
        _scan(node.orelse, graded, holes)
        if node.finalbody:
            return _scan(node.finalbody, graded, holes) or graded
    elif isinstance(node, ast.Match):
        for case in node.cases:
            _scan(case.body, graded, holes)
    return graded


def _scan(body: list[ast.stmt], graded: bool, holes: list[int]) -> bool:
    """Walk a statement list recording every exit reached without grading.

    ``graded`` means an assertion has DEFINITELY executed on every path that
    reaches this point.

    Args:
        body: The statements to walk.
        graded: Whether grading has already happened on this path.
        holes: Accumulator; the line of every ungraded exit is appended.

    Returns:
        Whether the path leaving this block is graded or has terminated.
    """
    for node in body:
        if isinstance(node, ast.Return):
            if not graded:
                holes.append(node.lineno)
            return True
        if isinstance(node, ast.Raise):
            return True
        if is_grading_statement(node):
            if isinstance(node, ast.With | ast.AsyncWith):
                _scan(node.body, True, holes)
            graded = True
            continue
        graded = _scan_compound(node, graded, holes)
    return graded


def ungraded_exits(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[int]:
    """Every line at which this function can return without having graded.

    Args:
        node: A function node.

    Returns:
        Line numbers, in source order.
    """
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    holes: list[int] = []
    _scan(body, False, holes)
    return sorted(holes)


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


def survey_source(module: str, text: str) -> tuple[list[Member], list[Finding]]:
    """Derive the population of one module and grade every member of it.

    Args:
        module: How the module should be named in a report.
        text: Its source.

    Returns:
        The members found and the ungraded exits among them.
    """
    tree = ast.parse(text)
    members: list[Member] = []
    findings: list[Finding] = []
    for node in functions(tree):
        if not is_population_member(node):
            continue
        members.append(Member(module, node.name, node.lineno))
        findings.extend(Finding(module, node.name, line) for line in ungraded_exits(node))
    return members, findings


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
    """Derive and grade the population across a set of modules.

    Args:
        root: The repository root.
        relatives: Repo-relative Python paths.

    Returns:
        The whole survey.
    """
    members: list[Member] = []
    findings: list[Finding] = []
    seen: list[str] = []
    for relative in relatives:
        text = (root / relative).read_text(encoding="utf-8")
        found, holes = survey_source(relative, text)
        members.extend(found)
        findings.extend(holes)
        seen.append(relative)
    return Survey(members=members, findings=findings, modules=seen)


# ---------------------------------------------------------------------------
# The guard half
# ---------------------------------------------------------------------------


#: Where CLAUDE.md section 2.1 says guards live - "Gates, guards, sync,
#: probes". The DIRECTORY is named because the topology table names it; the
#: TOOLS inside it and the GUARDS inside those are both derived, which is the
#: half that must never become a list. A bare ``guard_`` prefix match over the
#: whole tree would also catch test helpers called ``guard_of``, so the
#: directory is what separates a shipped guard from a fixture that reads one.
GUARD_TOOL_DIRECTORY: Final = "tools"


def guard_tools(root: Path, relatives: list[str]) -> list[str]:
    """Every tracked tool that ships at least one guard.

    Args:
        root: The repository root.
        relatives: Repo-relative Python paths.

    Returns:
        Repo-relative paths, sorted, of the tools defining a guard.
    """
    found: list[str] = []
    for relative in relatives:
        if Path(relative).parent.as_posix() != GUARD_TOOL_DIRECTORY:
            continue
        if guard_function_names((root / relative).read_text(encoding="utf-8")):
            found.append(relative)
    return sorted(found)


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


def guard_function_names(text: str) -> list[str]:
    """Every module-level ``guard_`` function a guard tool defines.

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


def names_reached_by(text: str, runner: str) -> set[str]:
    """Every bare name the named function mentions.

    A guard the runner never mentions is a guard that never runs, which is the
    same silence this module is about one level up.

    Args:
        text: The tool's source.
        runner: The function to read.

    Returns:
        Every ``Name`` in its body.

    Raises:
        LookupError: If the tool defines no such function.
    """
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == runner:
            return {inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name)}
    raise LookupError(runner)


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


def blind_verdicts(module: Any, root: Path, files: list[Path], source: str) -> list[BlindVerdict]:
    """Run every derived guard against a root it cannot read.

    Reads must ALREADY be failing when this is called - the caller owns that
    window, so the patching goes through pytest's monkeypatch and is undone
    even when an assertion fires inside it.

    Arguments are dispatched by PARAMETER NAME rather than by position, so a
    guard taking a different set of them needs no entry anywhere: a name this
    does not know is a loud KeyError rather than a guard quietly skipped.

    Args:
        module: The loaded guard tool.
        root: The root to point every guard at.
        files: The enumerated file list, gathered before reads began failing.
        source: How that list was enumerated.

    Returns:
        One verdict per derived guard, in the order the tool defines them.
    """
    available: dict[str, object] = {"root": root, "files": files, "source": source}
    verdicts: list[BlindVerdict] = []
    for name in guard_function_names(inspect.getsource(module)):
        function = getattr(module, name)
        arguments = [available[parameter] for parameter in inspect.signature(function).parameters]
        guard, skips = function(*arguments)
        rendered = " ".join(
            [*guard["detail"], *(f"{skip['path']} {skip['reason']}" for skip in skips)]
        )
        verdicts.append(
            BlindVerdict(
                function=name,
                guard_id=guard["id"],
                status=guard["status"],
                skips=len(skips),
                rendered=rendered,
            )
        )
    return verdicts


def silently_green(verdict: BlindVerdict) -> bool:
    """Whether a guard passed a root it could not read while recording nothing.

    CONVENTIONS.md section 15.1, which ``tools/drift_guard.py`` prints on every
    run: a guard may be green while self-excusing, and a green verdict means
    nothing without the list of what was never looked at. Green with no list,
    about a tree it could not read, is what a guard replaced by an early return
    returns.

    Args:
        verdict: One blind verdict.

    Returns:
        True if the guard is not grading.
    """
    return verdict.status == "PASS" and verdict.skips == 0
