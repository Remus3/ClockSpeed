"""CS-910 - the census of every program this repository can be made to spawn.

WHAT THIS GRADES, AND WHY A CENSUS RATHER THAN A FIX. CS-910 began as one line
in ``scripts/make_cert.py``. The finding is not that line: it is that a tool
NAMED and not RESOLVED is chosen by wherever the process happens to be standing,
which on Windows means the CURRENT DIRECTORY is searched before PATH whenever the
gate variable is absent - its state at both machine and user scope on the
development machine. MEASURED 2026-09-05: ``shutil.which("openssl")`` returned a
RELATIVE path to a planted file, and a bare ``"git"`` in an argv reaches the same
search through ``CreateProcess``. Repairing the one site that was found would
leave every sibling that was not, so the acceptance asks the question of the
whole tree and this module is what asks it.

THE TWO SHAPES IT JUDGES, and it judges them PER SITE rather than in aggregate. A
threshold summed over a population is satisfied by its strongest member while its
weakest goes unmeasured, so there is no ratio here and no pooled score: every
graded site is named, classified and reported on its own.

  1. A call to ``shutil.which``. That function consults the current directory,
     measured, so its presence anywhere in the graded roots is the defect itself
     rather than a proxy for it.
  2. A spawn whose PROGRAM folds to a string constant. A bare name is resolved
     by the operating system, current directory first; a spelled path is
     non-negotiable 3.

WHAT IT DOES NOT PROVE, STATED LOUDLY BECAUSE A GUARD WHOSE REACH IS ASSUMED IS
WORSE THAN NO GUARD. A program expression that does not fold to a constant is
recorded :data:`INDIRECT` and is NOT a finding. ``subprocess.run(argv, ...)``
inside a function that received ``argv`` from its caller cannot be graded by
reading one function, and an interprocedural walk that guessed would manufacture
confidence rather than evidence. Three live sites are in that class -
``scripts/make_cert.py``, ``scripts/make_shortcut.py`` and
``scripts/verify_env.py`` each spawn an argv built elsewhere - and each is
covered instead by a RUNTIME arm in its own test module, which observes what was
actually handed to the spawn. Static reach and runtime reach are different
instruments and neither one is a substitute for the other.

CONSTANT FOLDING IS ONE HOP AND DELIBERATELY SO. ``prog = "git"`` followed by
``subprocess.run([prog, ...])`` is the obvious way to walk past a scanner that
only reads call sites, so a Name is resolved against its enclosing function's
assignments and then against module scope. It is not a dataflow analysis and does
not claim to be: a name assembled from fragments, read off a mapping, or passed
in from another module folds to nothing and lands in INDIRECT with everything
else.

THE GRADED POPULATION IS THE SPAWN ROOTS AND THAT BOUNDARY IS A DECISION.
:data:`SPAWN_ROOTS` is what a shipped run executes - a script the operator
launches from wherever they are standing, a hook that fires from whatever
directory a session opened in. ``tests/`` is enumerated by the same walk and
reported by :func:`ungraded`, but it is not asserted over: repairing it is not
this item's write-list, and a boundary drawn quietly would be worse than one
drawn out loud. The remainder is CS-910's, and it is stated in the item's record
rather than buried in a skip.

THE WALK IS AST AND NEVER TEXT. A text scan matches its own needle - this module
names every callee it looks for, so grepping for them would find this file first
and grade nothing.

FLOORS, NOT MEASUREMENTS. The two counts below are literals well beneath what
this tree holds, sized to catch a walk that broke and returned a handful rather
than to pin ordinary churn. A census that silently enumerates nothing passes
every per-site assertion in this file, which is the one failure mode a per-site
rule cannot catch by itself.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: This checkout's root, derived from this file's own location.
REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# tools/toolpath.py is the module under census AND the module this file uses to
# find git, which is deliberate rather than circular: a census that spawned a
# bare "git" to enumerate the sites that spawn a bare "git" would be the first
# finding in its own report. The bare module name matches every other importer -
# see scripts/make_cert.py for the measurement that rules out `tools.toolpath`.
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

# ---------------------------------------------------------------------------
# The vocabulary
# ---------------------------------------------------------------------------

#: The program was resolved through tools/toolpath.py before it was spawned.
RESOLVED: Final = "RESOLVED"

#: The program is this process's own interpreter, which is already absolute and
#: has nothing left to resolve.
INTERPRETER: Final = "INTERPRETER"

#: The program folds to a bare name, so the operating system picks it - current
#: directory first. THE DEFECT CS-910 MEASURED.
BARE_NAME: Final = "BARE_NAME"

#: The program folds to a string carrying a directory part. A relative one
#: depends on where the process is standing; an absolute one is non-negotiable 3.
SPELLED_PATH: Final = "SPELLED_PATH"

#: A call to a resolver that consults the current directory.
CURDIR_RESOLVER: Final = "CURDIR_RESOLVER"

#: The program expression does not fold. Recorded, reported, and NOT graded -
#: see this module's docstring on why, and on what covers these instead.
INDIRECT: Final = "INDIRECT"

#: The verdicts that mean the site is answered.
ROUTED_VERDICTS: Final = frozenset({RESOLVED, INTERPRETER})

#: The verdicts that are findings. INDIRECT is deliberately not among them.
FINDING_VERDICTS: Final = frozenset({BARE_NAME, SPELLED_PATH, CURDIR_RESOLVER})

#: Every verdict this census can produce.
VERDICTS: Final = ROUTED_VERDICTS | FINDING_VERDICTS | {INDIRECT}

# ---------------------------------------------------------------------------
# What counts as a spawn, and what counts as a resolver
# ---------------------------------------------------------------------------

#: subprocess entry points that take an argv or a command.
SUBPROCESS_SPAWNERS: Final = frozenset(
    {"run", "Popen", "check_output", "check_call", "call", "getoutput", "getstatusoutput"}
)

#: The subprocess entry points whose first argument is a SHELL STRING rather
#: than an argv. The first word of one of those is a program name the shell
#: resolves, so the same question applies with different syntax.
SHELL_STRING_SPAWNERS: Final = frozenset({"getoutput", "getstatusoutput"})

#: os entry points that spawn. None are used in this tree, and the census says
#: so out loud rather than by omission - an arm below asserts the population.
OS_SPAWNERS: Final = frozenset(
    {
        "system",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "execl",
        "execle",
        "execlp",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "spawnl",
        "spawnle",
        "spawnlp",
        "startfile",
        "popen",
    }
)

#: The resolver whose answer can come from the current directory.
CURDIR_RESOLVERS: Final = frozenset({"which"})

#: The module that publishes :data:`CURDIR_RESOLVERS`.
CURDIR_RESOLVER_MODULE: Final = "shutil"

#: The functions tools/toolpath.py publishes. A program assigned from one of
#: these is resolved.
TOOLPATH_FUNCTIONS: Final = frozenset({"resolve_tool", "resolve"})

#: How tools/toolpath.py is spelled when it is imported as a module rather than
#: by name. Both spellings are accepted because both appear in this tree.
TOOLPATH_MODULES: Final = frozenset({"toolpath", "tools.toolpath"})

#: The attribute that is already an absolute interpreter path.
INTERPRETER_EXPRESSION: Final = "sys.executable"

#: The directories a shipped run executes from. See the module docstring.
SPAWN_ROOTS: Final = ("clockspeed", "scripts", "tools")

#: What a folded program must NOT contain to count as a bare name.
DIRECTORY_MARKERS: Final = ("/", "\\", ":")

MODULE_SCOPE: Final = "<module>"

#: How far a name is followed through other names before the fold gives up. A
#: bound rather than a cycle check alone, so a pathological chain cannot make the
#: census quadratic; the cycle check below is what makes it terminate.
MAX_FOLD_DEPTH: Final = 8

#: How long the enumeration waits on git.
GIT_TIMEOUT: Final = 120

#: The tool the enumeration asks which files are graded.
GIT_NAME: Final = "git"

# FLOORS. Deliberately NOT the measured values and NOT derived from the
# population they check - see the module docstring.
FILE_FLOOR: Final = 90
SITE_FLOOR: Final = 40

#: The shortest reason that reads as an argument rather than as a placeholder.
#: It cannot make a reason TRUE; it only makes "frozen" cost more to type than
#: it is worth.
EXEMPTION_REASON_MINIMUM: Final = 60

# EXEMPTIONS - graded sites that are not going to be repaired here, and why.
#
# Keyed by (repo-relative path, enclosing function, callee, LINE). The line is
# in the key on purpose: without it one row blankets every same-callee site in
# that function. A line that moves reddens the staleness arm below, which is a
# loud false refusal and the direction this project prefers.
#
# EVERY ROW HERE IS A FROZEN FILE AND THAT IS THE WHOLE TABLE. CLAUDE.md
# section 6 lists scripts/install_hooks.py and tools/precommit_gate.py as
# requiring explicit operator approval to modify, routed through an adjudicator
# and recorded in docs/LEDGER.md before the edit. No agent grants itself that
# exception and none widens the list, so these four sites carry the SAME defect
# as the seven that were repaired and are recorded here as OUTSTANDING rather
# than closed. CS-910 therefore does not fully close while this table is
# non-empty: its acceptance says "every other external tool this repository
# spawns", and four of them are behind a door this slice may not open.
EXEMPTIONS: Final[dict[tuple[str, str, str, int], str]] = {
    ("scripts/install_hooks.py", "run_git", "subprocess.run", 119): (
        "FROZEN under CLAUDE.md section 6 - scripts/install_hooks.py needs an adjudicator"
        " grant recorded in docs/LEDGER.md before any edit, and no agent grants itself"
        " one. The defect is present and unrepaired: this is the installer a fresh clone"
        " runs before any protection exists, so the current directory it inherits is"
        " whatever the operator was standing in."
    ),
    ("scripts/install_hooks.py", "run_git_optional", "subprocess.run", 308): (
        "FROZEN under CLAUDE.md section 6 - same route and same grant as the sibling site"
        " above. This one writes core.hooksPath, so a planted git here would report a"
        " wired clone while wiring nothing, which is the exact failure mode the module's"
        " own docstring calls out as the one that must never be silent."
    ),
    ("tools/precommit_gate.py", "ruff_command", "which", 1744): (
        "FROZEN under CLAUDE.md section 6 - tools/precommit_gate.py is the tier-0"
        " blocking gate and needs an adjudicator grant before any edit. shutil.which was"
        " MEASURED returning a relative current-directory path, so the linter this gate"
        " runs over staged content can be supplied by the tree being committed."
    ),
    ("tools/precommit_gate.py", "git", "subprocess.run", 2118): (
        "FROZEN under CLAUDE.md section 6 - same file, same route, same grant. The gate"
        " asks git what is staged, so a planted git decides what the gate believes it is"
        " inspecting, which makes this the highest-value of the four to repair once the"
        " grant exists."
    ),
}

# THE BUDGET, TYPED BY HAND. Never len(EXEMPTIONS) - that tautology is satisfied
# in both directions by construction, spends nothing, and leaves no number in a
# diff to argue with.
EXEMPTION_BUDGET: Final = 4


@dataclass(frozen=True)
class ProgramSite:
    """One place a program name enters a spawn, and what the census made of it."""

    path: str
    lineno: int
    callee: str
    function: str
    program: str
    verdict: str

    @property
    def routed(self) -> bool:
        """True when the program cannot be supplied by the working directory."""
        return self.verdict in ROUTED_VERDICTS

    @property
    def finding(self) -> bool:
        """True when this site is a defect of the class CS-910 measured."""
        return self.verdict in FINDING_VERDICTS

    @property
    def graded(self) -> bool:
        """True when this site sits under a root the assertions cover."""
        return self.path.split("/")[0] in SPAWN_ROOTS

    @property
    def key(self) -> tuple[str, str, str, int]:
        """The exemption key for this site, line number included."""
        return (self.path, self.function, self.callee, self.lineno)

    def __str__(self) -> str:
        """Render as `path:line  callee` inside `function`, with the verdict."""
        return (
            f"{self.path}:{self.lineno}  {self.callee}  in {self.function}()"
            f"  program={self.program}  {self.verdict}"
        )


def _dotted(node: ast.AST) -> str:
    """Render an attribute chain as a dotted name, or the empty string.

    Args:
        node: The expression to render.

    Returns:
        Something like ``subprocess.run``, or ``""`` when the chain is not made
        entirely of names and attributes.
    """
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return ""
    parts.append(current.id)
    return ".".join(reversed(parts))


def _imported_from(tree: ast.Module, module: str, names: frozenset[str]) -> dict[str, str]:
    """Local name to original name, for `from <module> import ...` bindings.

    An alias is followed, because ``from shutil import which as w`` binds the
    same function under a name no text scan would recognise.

    Args:
        tree: The parsed module.
        module: The module imported from.
        names: The original names worth recording.

    Returns:
        Local name to original name.
    """
    bound: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            for alias in node.names:
                if alias.name in names:
                    bound[alias.asname or alias.name] = alias.name
    return bound


def _module_aliases(tree: ast.Module, module: str) -> set[str]:
    """Every local name that refers to ``module``.

    Args:
        tree: The parsed module.
        module: The dotted module name.

    Returns:
        The local names, including ``module`` itself.
    """
    aliases = {module}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module:
                    aliases.add(alias.asname or alias.name)
    return aliases


def _direct_children(node: ast.AST) -> list[ast.AST]:
    """Every statement inside ``node``, stopping at a nested function or class.

    A binding inside a nested scope is not the binding a call in the outer scope
    sees, so folding across that boundary would answer a question nobody asked.

    Args:
        node: The scope to walk.

    Returns:
        The nodes reachable without entering another scope.
    """
    found: list[ast.AST] = []
    stack: list[ast.AST] = list(ast.iter_child_nodes(node))
    while stack:
        current = stack.pop()
        if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda):
            continue
        found.append(current)
        stack.extend(ast.iter_child_nodes(current))
    return found


def _assignments(scope: ast.AST, name: str) -> list[ast.expr]:
    """Every value assigned to ``name`` within ``scope``, nested scopes excluded.

    Args:
        scope: The function or module the call sits in.
        name: The identifier being resolved.

    Returns:
        The assigned value expressions, in source order.
    """
    values: list[ast.expr] = []
    for node in _direct_children(scope):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                values.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign | ast.NamedExpr)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            values.append(node.value)
    return values


class _Census(ast.NodeVisitor):
    """Walk one module, recording every program that enters a spawn."""

    def __init__(self, path: str, tree: ast.Module) -> None:
        """Bind the module's import shape before anything is judged.

        Args:
            path: The repo-relative path, posix-style.
            tree: The parsed module.
        """
        self.path = path
        self.tree = tree
        self.sites: list[ProgramSite] = []
        self._subprocess = _module_aliases(tree, "subprocess")
        self._os = _module_aliases(tree, "os")
        self._direct_spawners = _imported_from(tree, "subprocess", SUBPROCESS_SPAWNERS)
        self._direct_resolvers = _imported_from(
            tree, CURDIR_RESOLVER_MODULE, frozenset(CURDIR_RESOLVERS)
        )
        self._resolver_modules = _module_aliases(tree, CURDIR_RESOLVER_MODULE)
        self._scopes: list[tuple[str, ast.AST]] = [(MODULE_SCOPE, tree)]

    # -- callee classification ------------------------------------------------

    def _spawn_callee(self, node: ast.Call) -> str | None:
        """The spawn this call makes, rendered, or None when it makes none."""
        function = node.func
        if isinstance(function, ast.Attribute):
            base = _dotted(function.value)
            if base in self._subprocess and function.attr in SUBPROCESS_SPAWNERS:
                return f"subprocess.{function.attr}"
            if base in self._os and function.attr in OS_SPAWNERS:
                return f"os.{function.attr}"
            return None
        if isinstance(function, ast.Name) and function.id in self._direct_spawners:
            return f"subprocess.{self._direct_spawners[function.id]}"
        return None

    def _resolver_callee(self, node: ast.Call) -> str | None:
        """The current-directory resolver this call makes, or None."""
        function = node.func
        if isinstance(function, ast.Attribute):
            if _dotted(function.value) in self._resolver_modules and function.attr in (
                CURDIR_RESOLVERS
            ):
                return f"{CURDIR_RESOLVER_MODULE}.{function.attr}"
            return None
        if isinstance(function, ast.Name) and function.id in self._direct_resolvers:
            return self._direct_resolvers[function.id]
        return None

    @staticmethod
    def _is_toolpath_call(value: ast.expr) -> bool:
        """Whether ``value`` is a tools/toolpath.py resolution."""
        expression = value
        # `resolve(...).path` - the Resolution shape. Unwrap one attribute.
        if isinstance(expression, ast.Attribute):
            expression = expression.value
        if not isinstance(expression, ast.Call):
            return False
        function = expression.func
        if isinstance(function, ast.Name):
            return function.id in TOOLPATH_FUNCTIONS
        if isinstance(function, ast.Attribute):
            return _dotted(function.value) in TOOLPATH_MODULES and (
                function.attr in TOOLPATH_FUNCTIONS
            )
        return False

    # -- program resolution ---------------------------------------------------

    def _program_expression(self, node: ast.Call, callee: str) -> ast.expr | None:
        """The expression naming the program, or None when there is no argument."""
        if not node.args:
            return None
        first = node.args[0]
        if callee.rpartition(".")[2] in SHELL_STRING_SPAWNERS:
            return first
        if isinstance(first, ast.List | ast.Tuple):
            return first.elts[0] if first.elts else None
        return first

    @staticmethod
    def _fold_attribute(expression: ast.Attribute) -> tuple[str, str]:
        """An attribute chain: the interpreter, or something this cannot read."""
        rendered = _dotted(expression)
        if rendered == INTERPRETER_EXPRESSION:
            return rendered, INTERPRETER
        return rendered or "<attribute>", INDIRECT

    def _fold_call(self, expression: ast.Call) -> tuple[str, str]:
        """A call: a tools/toolpath.py resolution, or something this cannot read."""
        if self._is_toolpath_call(expression):
            return "<toolpath>", RESOLVED
        return "<call>", INDIRECT

    def _fold(
        self, expression: ast.expr, scope: ast.AST, seen: frozenset[str] = frozenset()
    ) -> tuple[str, str]:
        """Resolve one program expression to (rendered program, verdict).

        THE FALL-THROUGH IS INDIRECT AND THAT IS THE SAFE DIRECTION HERE: an
        expression shape this does not recognise is reported as ungraded rather
        than waved through as routed.
        """
        if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
            return expression.value, self._verdict_of(expression.value)
        if isinstance(expression, ast.Attribute):
            return self._fold_attribute(expression)
        if isinstance(expression, ast.Call):
            return self._fold_call(expression)
        if isinstance(expression, ast.Name):
            return self._fold_name(expression.id, scope, seen)
        return f"<{type(expression).__name__}>", INDIRECT

    def _fold_name(self, name: str, scope: ast.AST, seen: frozenset[str]) -> tuple[str, str]:
        """Resolve a bare identifier against its function, then module, scope.

        IT FOLLOWS A NAME THROUGH A NAME, and that is a repair rather than a
        flourish. The first version of this stopped at the first value that was
        not a constant, and MEASURED against a planted regression - ``git =
        GIT_NAME`` one line above a spawn, with ``GIT_NAME = "git"`` at module
        scope - it answered INDIRECT and the census stayed green. One indirection
        is all it took, and one indirection is what an ordinary edit produces.

        THE COMBINATION RULE IS SAFEST-FIRST. A name assigned a bare constant on
        ANY path is reported as that finding even when another path resolves it
        properly, because a program that is sometimes chosen by the working
        directory is chosen by the working directory. Routed is claimed only when
        EVERY assignment is routed.

        Args:
            name: The identifier being resolved.
            scope: The function the spawn sits in.
            seen: Identifiers already being resolved, so a cycle terminates.

        Returns:
            The rendered program and its verdict.
        """
        if name in seen or len(seen) >= MAX_FOLD_DEPTH:
            return name, INDIRECT
        deeper = seen | {name}
        for candidate_scope in (scope, self.tree):
            values = _assignments(candidate_scope, name)
            if not values:
                continue
            folded = [self._fold(value, scope, deeper) for value in values]
            for program, verdict in folded:
                if verdict in FINDING_VERDICTS:
                    return f"{name}={program}", verdict
            verdicts = {verdict for _program, verdict in folded}
            if verdicts == {RESOLVED}:
                return f"{name}=<toolpath>", RESOLVED
            if verdicts == {INTERPRETER}:
                return f"{name}={INTERPRETER_EXPRESSION}", INTERPRETER
            break
        return name, INDIRECT

    @staticmethod
    def _verdict_of(program: str) -> str:
        """Whether a folded program string is a bare name or a spelled path."""
        word = program.split(maxsplit=1)[0] if program.split() else program
        if any(marker in word for marker in DIRECTORY_MARKERS):
            return SPELLED_PATH
        return BARE_NAME

    # -- the walk -------------------------------------------------------------

    def _enter(self, node: ast.AST, name: str) -> None:
        self._scopes.append((name, node))
        self.generic_visit(node)
        self._scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record the enclosing function so a site can name where it sits."""
        self._enter(node, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Async functions scope exactly as ordinary ones do."""
        self._enter(node, node.name)

    def visit_Call(self, node: ast.Call) -> None:
        """Record a spawn's program, or a call to a current-directory resolver."""
        function_name, scope = self._scopes[-1]

        resolver = self._resolver_callee(node)
        if resolver is not None:
            named = node.args[0] if node.args else None
            rendered = (
                named.value
                if isinstance(named, ast.Constant) and isinstance(named.value, str)
                else "<name>"
            )
            self.sites.append(
                ProgramSite(
                    self.path, node.lineno, resolver, function_name, rendered, CURDIR_RESOLVER
                )
            )

        callee = self._spawn_callee(node)
        if callee is not None:
            expression = self._program_expression(node, callee)
            if expression is None:
                program, verdict = "<none>", INDIRECT
            else:
                program, verdict = self._fold(expression, scope, frozenset())
            self.sites.append(
                ProgramSite(self.path, node.lineno, callee, function_name, program, verdict)
            )

        self.generic_visit(node)


def scan_source(path: str, source: str) -> list[ProgramSite]:
    """Every program site in one module's source.

    Args:
        path: The repo-relative path, posix-style, used only for reporting.
        source: The module text.

    Returns:
        The sites, in the order the walk found them.
    """
    tree = ast.parse(source)
    census = _Census(path, tree)
    census.visit(tree)
    return census.sites


def graded_python_files() -> list[str]:
    """Every ``*.py`` path in this repository that git can see.

    ``--cached`` is the committed set; ``--others --exclude-standard`` adds what
    is written but not yet committed, minus anything gitignored. Both halves are
    needed - an untracked new file is invisible to a cached-only enumeration, and
    a census that cannot see a file cannot grade it.

    Returns:
        Repo-relative posix paths, sorted.

    Raises:
        RuntimeError: When git cannot be resolved. A census that quietly
            enumerated nothing would pass every per-site assertion in the suite.
    """
    git = resolve_tool(GIT_NAME)
    if git is None:
        raise RuntimeError("git could not be resolved from PATH, so no file set could be read")
    completed = subprocess.run(
        [git, "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    seen = {
        line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()
    }
    return sorted(seen)


def scan_repository() -> list[ProgramSite]:
    """Every program site across every file git can see."""
    sites: list[ProgramSite] = []
    for relative in graded_python_files():
        target = REPO_ROOT / relative
        if not target.is_file():
            continue
        sites.extend(scan_source(relative, target.read_text(encoding="utf-8")))
    return sites


def findings(sites: list[ProgramSite]) -> list[ProgramSite]:
    """The graded findings that no exemption excuses."""
    return [site for site in sites if site.graded and site.finding and site.key not in EXEMPTIONS]


def ungraded(sites: list[ProgramSite]) -> list[ProgramSite]:
    """Findings OUTSIDE the spawn roots - reported, never asserted over.

    See the module docstring: this is CS-910's stated remainder, not a silence.
    """
    return [site for site in sites if not site.graded and site.finding]


def describe(sites: list[ProgramSite]) -> str:
    """Render sites one per line so a failure names every one of them."""
    return "\n".join(f"  {site}" for site in sites)


def stale_exemptions(sites: list[ProgramSite]) -> list[str]:
    """Exemption rows naming a site the census did not find.

    A row that no longer matches anything is a forgiveness with nothing left to
    forgive, and it will silently absorb the next site that lands on that key.

    Args:
        sites: The whole census.

    Returns:
        One line per stale row.
    """
    live = {site.key for site in sites if site.finding}
    return [
        f"{path}:{line} {callee} in {function}() is exempted and is not a live finding"
        for (path, function, callee, line) in sorted(EXEMPTIONS)
        if (path, function, callee, line) not in live
    ]


def exemption_budget_problems(
    pinned: dict[tuple[str, str, str, int], str], ceiling: int
) -> list[str]:
    """The exemption ratchet, checked in BOTH directions.

    A ceiling checked only from below is met forever by a table that shrinks and
    banks room for an append nobody has to defend.

    Args:
        pinned: The recorded exemptions.
        ceiling: The recorded budget.

    Returns:
        One line per direction that has drifted.
    """
    spent = len(pinned)
    if spent > ceiling:
        return [
            f"{spent} exemption(s) recorded against a budget of {ceiling}. A row was added."
            " That is a finding to argue, not a line to type: route the program through"
            " tools/toolpath.py, or raise the budget in this same change and say why."
        ]
    if spent < ceiling:
        return [
            f"{spent} exemption(s) recorded against a budget of {ceiling}. A site was"
            " repaired and the budget was not lowered with it, which banks room for a"
            " future row that nobody has to defend. Lower the budget to match."
        ]
    return []
