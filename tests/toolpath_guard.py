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
confidence rather than evidence. Several live sites are in that class - among
them ``scripts/make_cert.py``, ``scripts/make_shortcut.py`` and
``scripts/verify_env.py``, which each spawn an argv built elsewhere - and each is
meant to be covered instead by a RUNTIME arm in its own test module, which
observes what was actually handed to the spawn. Static reach and runtime reach
are different instruments and neither one is a substitute for the other.

THE POPULATION IS NOT RESTATED HERE. A prose count of that class was carried in
this docstring and was WRONG - it named three while the census reported five,
having missed both sites in ``tools/precommit_gate.py``. Ask :func:`ungraded`
and the INDIRECT verdict for the current set rather than reading a number off
this paragraph.

THAT DELEGATION IS A CLAIM ABOUT ANOTHER FILE, AND IT WAS ONCE FALSE. The arm
for ``scripts/verify_env.py`` called two hand-picked functions and then asserted
the spawn count equalled two - which EXCLUDED BY CONSTRUCTION the six argv a
real collection builds, three of them a bare ``git``. The defect was live and
reproducible while this docstring asserted it was covered. That arm now drives
the script's own entry point rather than a chosen list of functions, asserts
every recorded argv is rooted with no ceiling on the population, and carries a
companion arm proving a single primitive is the only spawn in the file - which
is what makes "every argv recorded" mean "every argv built". THE OTHER TWO
DELEGATIONS ABOVE HAVE NOT BEEN RE-DERIVED HERE and are named, not vouched for.

CONSTANT FOLDING IS ONE HOP AND DELIBERATELY SO. ``prog = "git"`` followed by
``subprocess.run([prog, ...])`` is the obvious way to walk past a scanner that
only reads call sites, so a Name is resolved against its enclosing function's
assignments and then against module scope. A SEQUENCE FOLDS TO ITS FIRST ELEMENT
WHEREVER IT IS REACHED, which is a repair: unwrapping used to happen only where
a list was written inline, so ``argv = ["git", "x"]`` on the line above the spawn
answered INDIRECT - the plainest indirection there is, walking past the scanner
by one ordinary edit. It is not a dataflow analysis and does not claim to be: a
name assembled from fragments, read off a mapping, or passed in from another
module folds to nothing and lands in INDIRECT with everything else.

EVERY IMPORT FORM IS ENUMERATED, AND ONE OF THEM WAS NOT. Aliases are followed
for ``subprocess`` spawners, for the current-directory resolver, and - since a
census that reported ZERO sites for ``from os import system`` was measured
against a plant in a real spawn root - for the ``os`` spawners too. A site the
walk never records is invisible to :func:`findings`, to :func:`ungraded` and to
the site floor at once, which is strictly worse than a site graded wrongly.

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
import re
import subprocess
import sys
from dataclasses import dataclass, replace
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
#:
#: ``ops`` joined with CS-918, and it is the MOST exposed member rather than a
#: routine addition. The headless lane spawns `git`, `powershell` and `taskkill`
#: with its working directory set to the LANE WORKTREE - a directory whose
#: entire purpose is to be written into by an unattended agent for hours. So the
#: precondition CS-910 measured is not incidental here, it is the design: a file
#: named like a tool, dropped in that tree by the very worker the lane launched,
#: is searched before PATH and executed by the driver that launched it. Of every
#: root on this list, this is the one where a bare tool name is least defensible.
SPAWN_ROOTS: Final = ("clockspeed", "ops", "scripts", "tools")

#: What a folded program must NOT contain to count as a bare name.
DIRECTORY_MARKERS: Final = ("/", "\\", ":")

MODULE_SCOPE: Final = "<module>"

#: How far a name is followed through other names before the fold gives up. A
#: bound rather than a cycle check alone, so a pathological chain cannot make the
#: census quadratic; the cycle check below is what makes it terminate.
MAX_FOLD_DEPTH: Final = 8

#: The heading that opens CLAUDE.md's frozen-file list. The section NUMBER is
#: optional in the pattern deliberately: renumbering the document must not
#: quietly turn the justification check into a check of nothing.
FROZEN_HEADING: Final = re.compile(r"^#+\s*(?:\d+\.)?\s*Frozen files\s*$", re.IGNORECASE)

#: One entry of that list. Backtick-quoted, one per bullet.
FROZEN_BULLET: Final = re.compile(r"^-\s+`([^`]+)`\s*$")

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
# Keyed by (repo-relative path, enclosing function, callee, ORDINAL). The
# ordinal is the site's 1-based position among the FINDING sites in that same
# function making that same callee, in the order the walk meets them - see
# ProgramSite.ordinal. It is in the key on purpose: without a discriminator one
# row blankets every same-callee site in that function, so a second spawn
# planted beside an exempted one would be excused with it. Each row must answer
# EXACTLY one live site; one answering none is stale and one answering two is
# reported by name, both by stale_exemptions below.
#
# EVERY ROW HERE IS A FROZEN FILE, AND THAT CLAIM IS NOW CHECKED AGAINST THE
# LIST. CLAUDE.md section 6 lists scripts/install_hooks.py and
# tools/precommit_gate.py as requiring explicit operator approval to modify,
# routed through an adjudicator and recorded in docs/LEDGER.md before the edit.
# No agent grants itself that exception and none widens the list, so these four
# sites carry the SAME defect as the ones that were repaired and are recorded
# here as OUTSTANDING rather than closed.
#
# THE JUSTIFICATION USED TO BE UNCHECKED. The arm behind this table asked
# whether the path appeared anywhere in CLAUDE.md, and CLAUDE.md names twelve
# .py spellings of which exactly two are frozen - the module map and the tooling
# map account for the rest. MEASURED: a row keyed on tools/drift_guard.py PASSED
# that check. It is now checked against the parsed frozen LIST.
#
# WHAT THIS TABLE IS NOT. It is the set of graded findings that are excused, and
# NOT a statement that the four are all CS-910 has left. INDIRECT sites are not
# findings and never enter this table, tests/ is enumerated and not asserted
# over, and a bare name reached through a shape the fold does not read is
# recorded ungraded rather than here. A live HIGH defect sat in
# scripts/verify_env.py - a file that is NOT frozen - while this table held four
# rows, so "the remainder is the frozen four" is exactly the inference this
# comment must not invite. Read ungraded() and the runtime arms before claiming
# a remainder, and re-derive it rather than quoting a prior claim.
# THESE ROWS WERE KEYED BY LINE, AND THAT KEY WENT STALE ON AN EDIT ABOVE THE
# SITE RATHER THAN AT IT. Measured twice: the CS-1087 gate change and then the
# CS-1095 console-flash constant each moved two of these rows without touching a
# spawn, and both times the arm reported the exemption stale and the finding
# live - the correct verdicts from a key that cannot tell an edit above a site
# from a change to it. CS-1102 replaced the integer with the ordinal. THE KNOWN
# RESIDUE, stated rather than hidden: a new same-callee spawn planted ABOVE an
# exempted one in the same function takes the lower ordinal, so the row excuses
# the plant and the original is reported instead. Still red - it names the
# other site. tests/test_toolpath.py plants both directions.
EXEMPTIONS: Final[dict[tuple[str, str, str, int], str]] = {
    ("scripts/install_hooks.py", "run_git", "subprocess.run", 1): (
        "FROZEN under CLAUDE.md section 6 - scripts/install_hooks.py needs an adjudicator"
        " grant recorded in docs/LEDGER.md before any edit, and no agent grants itself"
        " one. The defect is present and unrepaired: this is the installer a fresh clone"
        " runs before any protection exists, so the current directory it inherits is"
        " whatever the operator was standing in."
    ),
    ("scripts/install_hooks.py", "run_git_optional", "subprocess.run", 1): (
        "FROZEN under CLAUDE.md section 6 - same route and same grant as the sibling site"
        " above. This one writes core.hooksPath, so a planted git here would report a"
        " wired clone while wiring nothing, which is the exact failure mode the module's"
        " own docstring calls out as the one that must never be silent."
    ),
    ("tools/precommit_gate.py", "ruff_command", "which", 1): (
        "FROZEN under CLAUDE.md section 6 - tools/precommit_gate.py is the tier-0"
        " blocking gate and needs an adjudicator grant before any edit. shutil.which was"
        " MEASURED returning a relative current-directory path, so the linter this gate"
        " runs over staged content can be supplied by the tree being committed."
    ),
    ("tools/precommit_gate.py", "git", "subprocess.run", 1): (
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
    #: The 1-based position of this site among the FINDING sites in the same
    #: path, function and callee, in walk order; 0 for a site that is not a
    #: finding. LINE-FREE ON PURPOSE (CS-1102): an edit above the site moves
    #: ``lineno`` and leaves this alone, while a second same-callee finding in
    #: the same function takes the next ordinal and so a key of its own.
    ordinal: int = 0

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
        """The exemption key for this site - the ordinal, and never the line."""
        return (self.path, self.function, self.callee, self.ordinal)

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
        # THE THIRD APPLICATION, WHICH WAS MISSING. This defence was already run
        # over subprocess and over the resolver module and never over os, so
        # `from os import system` produced sites=0 - not a finding, not an
        # ungraded row, invisible to findings(), to ungraded() and to the site
        # floor alike. MEASURED by planting one in a real spawn root, hashing the
        # file to prove the mutation landed, and watching the whole module stay
        # green. Two arms looked like they covered this and did not: one tests
        # `from shutil import which as w`, the other `import os; os.system(...)`.
        self._direct_os_spawners = _imported_from(tree, "os", OS_SPAWNERS)
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
        if isinstance(function, ast.Name):
            if function.id in self._direct_spawners:
                return f"subprocess.{self._direct_spawners[function.id]}"
            if function.id in self._direct_os_spawners:
                return f"os.{self._direct_os_spawners[function.id]}"
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

    def _fold_sequence(
        self, expression: ast.List | ast.Tuple, scope: ast.AST, seen: frozenset[str]
    ) -> tuple[str, str]:
        """An argv literal: the program is its first element.

        REACHED FROM ANYWHERE, and not only from the direct-argument position.
        ``argv = ["git", "x"]`` one line above the spawn used to fold to INDIRECT
        because unwrapping happened only where the sequence was written inline: a
        Name bound to a List arrived at the fold and gave up. That is the
        plainest indirection there is, and this module's own docstring calls one
        indirection what an ordinary edit produces.

        Args:
            expression: The sequence literal.
            scope: The function the spawn sits in.
            seen: Identifiers already being resolved, so a cycle terminates.

        Returns:
            The rendered program and its verdict. An empty sequence names no
            program at all and is INDIRECT rather than a finding.
        """
        if not expression.elts:
            return "<empty>", INDIRECT
        return self._fold(expression.elts[0], scope, seen)

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
        if isinstance(expression, ast.List | ast.Tuple):
            return self._fold_sequence(expression, scope, seen)
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
    counted: dict[tuple[str, str], int] = {}
    numbered: list[ProgramSite] = []
    for site in census.sites:
        if site.finding:
            slot = (site.function, site.callee)
            counted[slot] = counted.get(slot, 0) + 1
            numbered.append(replace(site, ordinal=counted[slot]))
        else:
            numbered.append(site)
    return numbered


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
    """Exemption rows that do not answer EXACTLY one live finding.

    A row that no longer matches anything is a forgiveness with nothing left to
    forgive, and it will silently absorb the next site that lands on that key. A
    row that matches MORE than one excuses a site nobody argued for, which is
    the same defect from the other side, so it is reported by name too.

    Args:
        sites: The whole census.

    Returns:
        One line per row matching zero or several live findings. A row carries
        no line, so a matched site's live ``path:line`` is rendered instead.
    """
    live: dict[tuple[str, str, str, int], list[ProgramSite]] = {}
    for site in sites:
        if site.finding:
            live.setdefault(site.key, []).append(site)
    problems: list[str] = []
    for key in sorted(EXEMPTIONS):
        path, function, callee, ordinal = key
        matched = live.get(key, [])
        if not matched:
            problems.append(
                f"{path} {callee} #{ordinal} in {function}() is exempted and is not a live finding"
            )
        elif len(matched) > 1:
            where = ", ".join(f"{site.path}:{site.lineno}" for site in matched)
            problems.append(
                f"{path} {callee} #{ordinal} in {function}() is exempted and matches"
                f" {len(matched)} live findings, not one: {where}"
            )
    return problems


def frozen_files() -> list[str]:
    """The entries of CLAUDE.md's frozen-file LIST, in the order they are written.

    WHY THE LIST AND NEVER THE DOCUMENT. The arm that checks the exemption
    table's justification used to ask ``path not in CLAUDE.md``, and CLAUDE.md
    mentions twelve ``.py`` spellings of which exactly two are frozen - the
    module map and the tooling map name the rest. MEASURED: an exemption keyed
    on ``tools/drift_guard.py`` PASSED that check, because the tooling map
    mentions the file. A substring test against a whole document is not a test
    of membership in a list inside it; it is a test of whether the document has
    ever heard of the string.

    Returns:
        The entries exactly as written, backticks stripped.

    Raises:
        RuntimeError: The section could not be found or held no entries. Loud
            rather than empty: an empty answer would silently make every
            exemption unjustified, which is the safe direction but names the
            wrong cause.
    """
    text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="ascii")
    lines = text.splitlines()
    entries: list[str] = []
    inside = False
    for line in lines:
        if FROZEN_HEADING.match(line):
            inside = True
            continue
        if inside:
            if line.startswith("#"):
                break
            matched = FROZEN_BULLET.match(line)
            if matched:
                entries.append(matched.group(1))
            elif entries and line.strip() and not line.startswith("-"):
                # The list has ended and the prose after it has begun.
                break
    if not entries:
        message = (
            "CLAUDE.md section 6 yielded no frozen-file entries - the heading or the"
            " list shape changed, so no exemption can be justified against it"
        )
        raise RuntimeError(message)
    return entries


def is_frozen(path: str, entries: list[str]) -> bool:
    """Whether ``path`` is covered by one of the frozen-list entries.

    THE GLOB ENTRY IS HONOURED RATHER THAN COMPARED. CLAUDE.md freezes
    ``.githooks/*`` as a directory, so an exact-string test would refuse every
    real file under it while accepting the literal entry, which no path is.

    Args:
        path: A repo-relative posix path.
        entries: The frozen list, as :func:`frozen_files` returns it.

    Returns:
        True when the path is frozen.
    """
    for entry in entries:
        if entry.endswith("/*"):
            prefix = entry[:-1]
            if path.startswith(prefix) and "/" not in path[len(prefix) :]:
                return True
        elif path == entry:
            return True
    return False


def unfrozen_exemptions(pinned: dict[tuple[str, str, str, int], str]) -> list[str]:
    """Exemption rows naming a file CLAUDE.md's frozen LIST does not cover.

    The table's entire stated justification is that every row sits behind
    CLAUDE.md section 6. This is that claim, checked against the list rather
    than against the prose surrounding it.

    Args:
        pinned: The recorded exemptions.

    Returns:
        One line per row whose file is not frozen.
    """
    entries = frozen_files()
    return [
        f"{path} is exempted as FROZEN and is not in CLAUDE.md's frozen-file list"
        for path in sorted({path for (path, _f, _c, _o) in pinned})
        if not is_frozen(path, entries)
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
