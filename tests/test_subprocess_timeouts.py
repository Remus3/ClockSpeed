#!/usr/bin/env python3
"""CS-896 - every subprocess call this repository ships is bounded by a timeout.

THE FAILURE MODE IS LIVE, NOT HYPOTHETICAL. Tier 1 CI runs `python -m pytest
tests -q` as the bulk of a job carrying a `timeout-minutes` runaway cutoff, and
one run was already CANCELLED with nothing failing. An unbounded subprocess
cannot fail the test that owns it - it burns the whole job's budget until the
lane is cancelled, and a cancelled lane is evidence of nothing. It gets worse
under `pytest -n auto` on a 2-vCPU runner: two workers contending stretch every
child's wall time, so a call that merely ran slowly starts to look like a hang
and there is no arm to catch it. A `timeout=` converts that into a named,
attributable failure inside the budget.

WHY THIS IS AN AST WALK AND NOT A REGEX, with the measurement that settled it.
The population for this item was first derived by a brace-matching scan over a
700-character window. It reported an unbounded call site in
`tests/test_exception_rendering.py`, at what was then line 1391. That line is a
COMMENT:

    # subprocess.run() inside run_git(); run_git() catches only FileNotFoundError,

The number is quoted as provenance rather than as a live pointer, and it is
already stale: adding a timeout to that file's own git call - in the same slice
that first built this module - pushed the comment down a line. A citation that
its own commit invalidates is the argument for citing the TEXT, which does not
move.

The same file's `INSTALLER_CRASH_WRAPPER` holds `subprocess.run = boom` inside a
string literal - Python source as DATA, deliberately, so the installer can be
crashed from outside a frozen file. Neither a comment nor a string literal is in
the abstract syntax tree, so this module cannot repeat either false positive: it
grades what the interpreter would execute, not what the bytes look like.

WHY THE CALLEE IS BINDING-RESOLVED. The mirror-image failure is worse. A scan
keyed on the bare NAMES `run`, `call`, `check_output` and `Popen` finds dozens of
extra "sites" in this tree, every one of them a local test helper - `def
call(door, value, parameters)` at `tests/surface/test_solve.py::call`, and a
`Callable` parameter named `call` threaded through `tests/save/test_chunks.py`.
Neither file imports subprocess at all. So the bindings are read first and a call
counts only when it actually resolves to the subprocess module.

FIVE ROUTES TO THE MODULE, AND THE FIRST BUILD READ ONLY TWO. Reading `Import`
and `ImportFrom` alone left five silent escape hatches, MEASURED: a probe file
carrying six genuinely unbounded spawns passed the whole suite, while a control
holding a plain `subprocess.run` correctly failed - so the harness was live and
the rule was not. All five are read now:

    import subprocess [as alias]      ->  alias.run(...)
    from subprocess import run as r   ->  r(...)
    from subprocess import *          ->  run(...)
    _sp = subprocess                  ->  _sp.run(...)
    _runner = subprocess.run          ->  _runner(...)

The last two are followed to a FIXPOINT, so `a = subprocess; b = a; b.run(...)`
resolves as well. The re-binding pass reads assignments in ANY scope and pools
them module-wide, which is deliberately over-broad: a local `_runner =
subprocess.run` in one function makes a call to `_runner(...)` in another resolve
too. That direction produces a LOUD FALSE REFUSAL, never a silent accept.

`getattr(subprocess, "run")(...)` resolves through the string. `getattr(
subprocess, name)(...)`, where the attribute is not a literal, CANNOT be graded
statically and is REFUSED rather than waved through - the `.githooks/pre-push`
rule that a loud false refusal beats a silent false accept, applied here.

`timeout=None` IS NOT A BOUND, and this is the hole that made the whole module
revertible by ONE TOKEN. `timeout=None` is bit-for-bit `subprocess.run`'s
unbounded default. MEASURED at the interpreter rather than argued: against a
child sleeping three seconds, `timeout=None` returned after 3.1s and raised
nothing, `timeout=1` raised `TimeoutExpired` at 1.0s, and `timeout=0` raised it
at 0.00s. The first build tested the keyword's NAME and never its VALUE, so
every bound this module protects could be restored to the default with the guard
green. Three decisions follow, and each is stated with its price:

  - `timeout=None` is REFUSED. It is the default spelled out loud.
  - `timeout=0` is ACCEPTED. It cannot hang - it raises immediately, which is a
    named, attributable failure inside the budget and therefore the OPPOSITE of
    what this module exists to catch. The price: a zero typed by mistake reddens
    its own test on every run, so it corrects itself rather than hiding.
  - `timeout=SOME_NAME` is ACCEPTED, because a named constant is the dominant
    real spelling in this tree and refusing it would refuse the thing the rule
    wants. A name is resolved ONE HOP against module-scope bindings, so a name
    bound to `None` there is still refused. THE RESIDUAL, DISCLOSED: a name bound
    to `None` inside a function, imported from another module, or produced by a
    call still passes. Closing that means constant-folding across imports; the
    one-hop version is what costs nothing to write and therefore what arrives.

`getoutput` AND `getstatusoutput` ARE REFUSED OUTRIGHT, and the rule for them is
refusal rather than "needs a timeout" because THEY CANNOT TAKE ONE - neither has
a timeout parameter in any Python version. Swapping a bounded `subprocess.run`
for one of these would otherwise be a permanent exemption that never appears in
any table. They are also the one class that is NOT EXEMPTIBLE: there is always
`subprocess.run(..., shell=True, timeout=N)`, so no site ever needs one. If that
is ever wrong, the fix is to change this rule in a diff somebody reviews, not to
add a row.

UNTRACKED FILES ARE IN THE POPULATION, AND THAT IS THE DELIBERATE CHOICE. The
enumeration is `git ls-files --cached --others --exclude-standard "*.py"`, the
same three flags and the same reason as `tests/test_exception_rendering.py` and
`tests/shell/test_shell_assets.py`. `--cached` alone is the committed set, and a
guard reading only that cannot see a module until it has been committed -
including THIS module on the commit that adds it, which would hand every file
added alongside it one free pass. `--others` adds what is written but not yet
committed and `--exclude-standard` drops anything gitignored, so generated trees
under `data/` never enter. The consequence worth stating plainly: a brand-new
`.py` is graded here BEFORE it is committed, which is the opposite of the
familiar trap where a guard is green locally and red at commit time. VERIFIED
this round: a probe file written and never added was enumerated and graded.

THE SCOPE IS THE WHOLE REPOSITORY, NOT `tests/`, and the widening was free. The
first build restricted the sweep to `tests/` and asserted the restriction without
defending it - but an unbounded call in `tools/` or `scripts/` cancels the SAME
CI lane, invoked by the same tests, and would have been ungraded forever. The
restriction was measured before it was removed: every subprocess site outside
`tests/` was ALREADY bounded, so widening cost no edit to any file and no
exemption. A prefix filter that excludes code which can hang the lane is not a
scope, it is a blind spot, and this one had no price to pay for closing it.

POPEN IS BOUNDED AT THE WAIT, NOT AT THE CONSTRUCTOR, and this is a language
fact rather than a preference. `subprocess.Popen.__init__` has no `timeout`
parameter; passing one is a `TypeError`. The bound for a Popen lives on
`.wait(timeout=...)` or `.communicate(timeout=...)`. So a Popen site is required
to carry a bounding call in its enclosing function instead. That is strictly
stronger than exempting Popen as a class, which would wave through a genuinely
unbounded one wearing identical syntax.

A CLEANUP WAIT IS NOT A BOUND, AND THIS WAS MEASURED RATHER THAN REASONED. The
first version of the rule looked for any `.wait(timeout=)` anywhere in the
enclosing function. Removing the real bound from the one Popen site in this tree
left the guard GREEN, because the site keeps a second wait in its handler:

    try:
        code = proc.wait(timeout=TIMEOUT)   <- the bound
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)              <- cleanup, accepted as the bound

A wait inside an `except TimeoutExpired` handler cannot be the bound: it runs
only BECAUSE some other bound already fired, so if the primary wait is unbounded
the handler is unreachable and the process hangs forever. Those handler bodies
are therefore pruned from the search.

THE WAIT IS NOW TIED TO THE HANDLE BY NAME, which is where the previous build was
WIDER THAN THE LIMITATION IT ADMITTED. It matched `.wait(timeout=)` on ANY
object, so `threading.Event().wait(timeout=5)` in the same function satisfied the
bound while `proc.wait()` stayed unbounded - and that pairing is idiomatic in
exactly the code that spawns a server and waits for readiness. A bound inside a
NESTED FUNCTION THAT IS NEVER CALLED satisfied it too. Both are MEASURED: a probe
holding each shape reported `bounded=True` twice with the suite green. The bound
must now be spelled on the same name the Popen was assigned to, and nested
function and lambda bodies are pruned alongside the timeout handlers.

WHERE THE HANDLE CANNOT BE NAMED, THE SITE IS REFUSED. A Popen whose result is
not bound to a plain name or dotted chain - a bare expression, a tuple unpack -
has no name a wait can be tied to, so it is reported rather than assumed bounded.
`with subprocess.Popen(...) as proc:` binds a name and is accepted.

A `**kwargs` SPLAT COUNTS AS UNBOUNDED. `subprocess.run(*args, **options)` might
carry a timeout inside `options` and cannot be shown to. A guard that accepts
"there might be one in that dict" grades nothing, so an explicit `timeout=` is
required even in the presence of a splat. Zero sites splat today, which is
exactly when a rule like this is free to adopt.

THE FLOORS EXIST BECAUSE A GUARD THAT WALKS NOTHING PASSES SILENTLY - the unrun
gate of CONVENTIONS.md section 7.2, which this repo has been bitten by
repeatedly. They are deliberately NOT the measured values and NOT derived from
the population they check, which would make the assertion a tautology about its
own arithmetic. They are literals well below what this guard measures.

AND THE FLOORS ARE THEMSELVES GRADED, because the first build could set BOTH to
zero with the whole suite green - the defect each exists to prevent, restored in
a two-character diff. They are routed through `floor_problems` so a control can
ask the LIVE number whether it rejects an empty population, and
`graded_floor_names` closes the class so a THIRD floor cannot arrive ungraded.
NO MEASURED COUNT IS RESTATED IN THIS DOCSTRING. The first build wrote two of
them into prose and both were WRONG on the day they were typed - they excluded
this module's own file, which contains a `subprocess.run`. A count in a docstring
is a lie with a timestamp on it (CLAUDE.md section 4); the floors are the one
machine-checked place, and the arms below are what check them.

THE EXEMPTION TABLE IS GRADED, AND IT IS THE OTHER TWO-LINE DISARM. Deleting one
`timeout=` and adding one row naming that live site left the suite green: the
staleness arm only reddens on a key naming code that is GONE, and a key naming
LIVE code is precisely what it accepts. Three things changed. The key carries the
LINE NUMBER, so one row can no longer blanket every same-callee site in a
function, and a row whose line has moved reddens loudly instead of silently
excusing the wrong thing. Every row must state a reason of real length. And the
table is spent against a PINNED BUDGET checked in BOTH directions, so adding a
row costs a number in the diff that somebody has to argue for, and removing one
without lowering the budget banks room for a future append nobody will defend.
The budget is a typed literal, and `derived_bound_problems` proves it was not
written as `len(EXEMPTIONS)` - the one-line tautology that satisfies both
directions by construction and has been filed in this repo twice.

WHAT THE BUDGET CANNOT DO, DISCLOSED: a reason long enough to pass the length
check can still be untrue, and a wrong number typed by hand still silences what
it bounds. What is removed is the row that costs NOTHING, and the bound that
CANNOT be wrong.
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from tests.bare_path_guard import (
    derived_bound_problems,
    floor_problems,
    graded_floor_names,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# Bounding the git enumeration itself, by the rule this module enforces. 120s
# matches tests/test_doc_budget.py and tests/test_commit_msg_gate.py, which run
# the same class of git plumbing.
GIT_TIMEOUT: Final = 120

# The subprocess entry points that accept a `timeout=` keyword. `call` and
# `check_call` are here for completeness; neither is used in this tree today.
TIMEOUT_TAKING: Final = frozenset({"run", "check_output", "check_call", "call"})

# Bounded at the wait instead - see the module docstring.
POPEN: Final = "Popen"

# The two that accept no timeout in any Python version, and so are refused
# outright rather than asked for one - see the module docstring.
UNBOUNDABLE: Final = frozenset({"getoutput", "getstatusoutput"})

# Everything that spawns a child, by any route.
SPAWNING: Final = TIMEOUT_TAKING | {POPEN} | UNBOUNDABLE

# The methods on a Popen handle that accept a `timeout=` and so provide a bound.
BOUNDING_METHODS: Final = frozenset({"wait", "communicate"})

# The exception whose handler bodies are pruned from the bound search - a wait
# in there is cleanup after a bound fired, never the bound itself.
TIMEOUT_EXPIRED: Final = "TimeoutExpired"

# Bodies pruned alongside those handlers: a bound inside a function nobody calls
# is not a bound. A lambda is here for the same reason.
NESTED_SCOPES: Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)

MODULE_SCOPE: Final = "<module>"

# The callee recorded for a `getattr()` dispatch whose attribute is not a
# literal. It resolves to no known name on purpose - it is a refusal.
DYNAMIC: Final = "subprocess.<dynamic>"

STAR: Final = "*"

# `getattr(obj, name)` - the arity below which there is nothing to resolve.
GETATTR_ARITY: Final = 2

# The reasons a site is not bounded. Named rather than inlined so an arm can ask
# for one by identity instead of matching on prose.
NO_KEYWORD: Final = "no timeout= keyword"
NONE_IS_THE_DEFAULT: Final = "timeout=None is bit-for-bit subprocess's unbounded default"
CANNOT_BE_BOUNDED: Final = (
    "cannot take a timeout at ALL - neither getoutput nor getstatusoutput has a timeout"
    " parameter, so this is a permanent exemption wearing ordinary syntax. Use"
    " subprocess.run(..., shell=True, timeout=N) instead. This class is not exemptible."
)
DYNAMIC_DISPATCH: Final = (
    "getattr() dispatch on the subprocess module cannot be graded statically, and a"
    " loud false refusal beats a silent false accept - spell the call out instead"
)
UNNAMED_HANDLE: Final = (
    "the Popen result is not bound to a plain name, so no wait can be tied to it -"
    " assign it to a name and bound that name's .wait(timeout=)"
)

# FLOORS. Deliberately NOT the measured values and NOT derived from the
# population they check. They are literals well below what this guard measures,
# sized to catch a walk that broke and returned a handful rather than to pin
# ordinary churn. Every one of them is graded by the parametrized arm below, and
# `test_every_floor_this_module_uses_is_one_this_arm_grades` closes the class.
FILE_FLOOR: Final = 90
CALL_SITE_FLOOR: Final = 50

# The shortest reason that reads as an argument rather than as a placeholder.
# It cannot make a reason TRUE - see the docstring - it only makes "fast" cost
# more to type than it is worth.
EXEMPTION_REASON_MINIMUM: Final = 40

# EXEMPTIONS - call sites that genuinely must not carry a timeout.
#
# Keyed by (repo-relative path, enclosing function, callee, LINE). The line is in
# the key on purpose: without it one row blankets every same-callee site in that
# function, and the two-line disarm this module was refuted for spent exactly
# that. A line that moves reddens the staleness arm, which is a loud false
# refusal and the direction this project prefers.
#
# THIS TABLE IS EMPTY, AND THAT IS A RESULT RATHER THAN AN OVERSIGHT. Every
# `run` site in this repository can take a `timeout=`, and the one Popen site is
# bounded at its `wait()` by the derived rule above rather than excused. An
# exemption written for a site that does not need one is a hole that outlives
# the reason for it, so none were written. The mechanism is proved to work in
# both directions by the synthetic-source arms below.
EXEMPTIONS: Final[dict[tuple[str, str, str, int], str]] = {}

# THE BUDGET, TYPED BY HAND. Never `len(EXEMPTIONS)` - that tautology satisfies
# both directions by construction, spends nothing, and leaves no number in the
# diff to query. `test_the_budget_is_not_derived_from_the_table_it_bounds` is
# what keeps this a literal.
EXEMPTION_BUDGET: Final = 0


@dataclass(frozen=True)
class CallSite:
    """One resolved subprocess call and why its wall time is or is not bounded."""

    path: str
    lineno: int
    callee: str
    function: str
    reason: str

    @property
    def bounded(self) -> bool:
        """True exactly when nothing is wrong with this site's bound."""
        return not self.reason

    @property
    def exemptible(self) -> bool:
        """False for the class that can never take a timeout - see the docstring."""
        return self.reason != CANNOT_BE_BOUNDED

    @property
    def key(self) -> tuple[str, str, str, int]:
        """The exemption key for this site, line number included."""
        return (self.path, self.function, self.callee, self.lineno)

    def __str__(self) -> str:
        """Render as `path:line  callee` inside `function`, with the reason."""
        return f"{self.path}:{self.lineno}  {self.callee}  in {self.function}() - {self.reason}"


def _spell(node: ast.AST | None) -> str | None:
    """The dotted spelling of a name or attribute chain - `proc`, `self.proc`.

    Args:
        node: The expression to spell.

    Returns:
        The spelling, or None for anything that is not a plain chain.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _spell(node.value)
        return None if base is None else f"{base}.{node.attr}"
    return None


def _none_valued_names(tree: ast.Module) -> frozenset[str]:
    """Every module-scope name bound to a literal `None`.

    ONE HOP, MODULE SCOPE ONLY. See the module docstring for what this cannot
    see and why that residual was accepted rather than closed.

    Args:
        tree: The parsed module.

    Returns:
        The names whose module-scope value is `None`.
    """
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            targets: list[ast.expr] = [node.target]
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
        else:
            continue
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            names.update(target.id for target in targets if isinstance(target, ast.Name))
    return frozenset(names)


def _timeout_problem(node: ast.Call, none_valued: frozenset[str]) -> str:
    """Why this call's `timeout=` is not a bound, or empty when it is one.

    A `**kwargs` splat carries `arg is None` and so never matches - it is not
    accepted as evidence of a timeout. See the module docstring.

    Args:
        node: The call to grade.
        none_valued: Module-scope names bound to `None`.

    Returns:
        The reason, or an empty string when the call is bounded.
    """
    for keyword in node.keywords:
        if keyword.arg != "timeout":
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and value.value is None:
            return NONE_IS_THE_DEFAULT
        if isinstance(value, ast.Name) and value.id in none_valued:
            return f"timeout={value.id}, and {value.id} is bound to None at module scope"
        return ""
    return NO_KEYWORD


def _is_timeout_handler(node: ast.AST) -> bool:
    """True for an `except ...TimeoutExpired...:` clause, tuple form included."""
    if not isinstance(node, ast.ExceptHandler) or node.type is None:
        return False
    caught = node.type.elts if isinstance(node.type, ast.Tuple) else [node.type]
    return any(
        (isinstance(entry, ast.Name) and entry.id == TIMEOUT_EXPIRED)
        or (isinstance(entry, ast.Attribute) and entry.attr == TIMEOUT_EXPIRED)
        for entry in caught
    )


def _rebinding(
    value: ast.expr, modules: set[str], direct: dict[str, str]
) -> tuple[bool, str] | None:
    """What a value expression re-spells, for the fixpoint pass.

    Args:
        value: The right-hand side.
        modules: Names already bound to the subprocess module.
        direct: Names already bound to a subprocess attribute.

    Returns:
        `(True, "")` for the module itself, `(False, attr)` for one attribute,
        or None when the expression re-spells neither.
    """
    if isinstance(value, ast.Name):
        if value.id in modules:
            return (True, "")
        if value.id in direct:
            return (False, direct[value.id])
    if (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id in modules
        and value.attr in SPAWNING
    ):
        return (False, value.attr)
    return None


def _widen_by_assignment(tree: ast.Module, modules: set[str], direct: dict[str, str]) -> None:
    """Follow `_sp = subprocess` and `_runner = subprocess.run` to a fixpoint.

    Both sets only ever GROW and are bounded by the names the file spells, so
    the loop terminates. See the module docstring on why this pools bindings
    across scopes rather than tracking them per function.

    Args:
        tree: The parsed module.
        modules: Mutated in place.
        direct: Mutated in place.
    """
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = [t for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target]
            else:
                continue
            if node.value is None:
                continue
            rebinding = _rebinding(node.value, modules, direct)
            if rebinding is None:
                continue
            is_module, attr = rebinding
            for target in targets:
                if is_module and target.id not in modules:
                    modules.add(target.id)
                    changed = True
                elif not is_module and target.id not in direct:
                    direct[target.id] = attr
                    changed = True


def _subprocess_bindings(tree: ast.Module) -> tuple[set[str], dict[str, str]]:
    """Every name in this module that reaches subprocess, by any of five routes.

    Args:
        tree: The parsed module.

    Returns:
        (names bound to the subprocess MODULE, {local name: subprocess attr}).
    """
    modules: set[str] = set()
    direct: dict[str, str] = {}
    star = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    modules.add(alias.asname or "subprocess")
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name == STAR:
                    star = True
                else:
                    direct[alias.asname or alias.name] = alias.name
    if star:
        for name in SPAWNING:
            direct.setdefault(name, name)
    _widen_by_assignment(tree, modules, direct)
    return modules, direct


def _handle_spelling(call: ast.Call, scope: ast.AST) -> str | None:
    """The name a Popen result is bound to, found BY IDENTITY on the call node.

    Identity rather than position, so no line number or statement order is
    involved and a reformat cannot move the answer.

    Args:
        call: The `subprocess.Popen(...)` call.
        scope: The enclosing function.

    Returns:
        The handle's spelling, or None when it is not bound to a plain name.
    """
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and node.value is call:
            return _spell(node.targets[0]) if len(node.targets) == 1 else None
        if isinstance(node, ast.AnnAssign) and node.value is call:
            return _spell(node.target)
        if isinstance(node, ast.withitem) and node.context_expr is call:
            return _spell(node.optional_vars)
    return None


def _wait_in(node: ast.AST, handle: str, none_valued: frozenset[str]) -> bool:
    """True if this subtree bounds `handle` at a wait, pruning what cannot count.

    Args:
        node: The subtree.
        handle: The Popen handle's spelling.
        none_valued: Module-scope names bound to `None`.

    Returns:
        Whether a bounding wait on this handle is reachable here.
    """
    if _is_timeout_handler(node) or isinstance(node, NESTED_SCOPES):
        return False
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in BOUNDING_METHODS
        and _spell(node.func.value) == handle
        and not _timeout_problem(node, none_valued)
    ):
        return True
    return any(_wait_in(child, handle, none_valued) for child in ast.iter_child_nodes(node))


def _bounding_wait_present(scope: ast.AST, handle: str, none_valued: frozenset[str]) -> bool:
    """True if this scope bounds `handle` at `.wait(timeout=)`/`.communicate(timeout=)`.

    The scope's own node is never pruned - only its children are - so an
    enclosing function is not mistaken for the nested function rule.

    Args:
        scope: The enclosing function.
        handle: The Popen handle's spelling.
        none_valued: Module-scope names bound to `None`.

    Returns:
        Whether the handle is bounded in this scope.
    """
    return any(_wait_in(child, handle, none_valued) for child in ast.iter_child_nodes(scope))


class _SubprocessVisitor(ast.NodeVisitor):
    """Collect every binding-resolved subprocess call site in one module."""

    def __init__(
        self,
        path: str,
        modules: set[str],
        direct: dict[str, str],
        none_valued: frozenset[str],
    ) -> None:
        """Bind the module under scan and the names that resolve to subprocess."""
        self.path = path
        self.modules = modules
        self.direct = direct
        self.none_valued = none_valued
        self.sites: list[CallSite] = []
        self._scopes: list[tuple[str, ast.AST]] = []

    def _enter(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._scopes.append((node.name, node))
        self.generic_visit(node)
        self._scopes.pop()

    # `ast.AsyncFunctionDef` is NOT a subclass of `ast.FunctionDef`, so an
    # `async def` needs its own visitor or its calls are never scoped.
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track the enclosing function for calls inside it."""
        self._enter(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track the enclosing async function for calls inside it."""
        self._enter(node)

    def _resolve_getattr(self, func: ast.Call) -> str | None:
        """`getattr(subprocess, "run")(...)`, resolved - or refused when dynamic."""
        if not (isinstance(func.func, ast.Name) and func.func.id == "getattr"):
            return None
        if len(func.args) < GETATTR_ARITY:
            return None
        target, attribute = func.args[0], func.args[1]
        if not (isinstance(target, ast.Name) and target.id in self.modules):
            return None
        if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str):
            return f"subprocess.{attribute.value}" if attribute.value in SPAWNING else None
        return DYNAMIC

    def _resolve(self, node: ast.Call) -> str | None:
        """Return `subprocess.<attr>` when this call resolves to subprocess."""
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in self.modules and func.attr in SPAWNING:
                return f"subprocess.{func.attr}"
            return None
        if isinstance(func, ast.Name):
            attr = self.direct.get(func.id)
            return f"subprocess.{attr}" if attr in SPAWNING else None
        if isinstance(func, ast.Call):
            return self._resolve_getattr(func)
        return None

    def _popen_reason(self, node: ast.Call, scope: ast.AST | None) -> str:
        """Why this Popen is not bounded at a wait on its OWN handle."""
        if scope is None:
            # A module-scope Popen has no enclosing function to search, so there
            # is nowhere a bound could be found - refused rather than assumed.
            return UNNAMED_HANDLE
        handle = _handle_spelling(node, scope)
        if handle is None:
            return UNNAMED_HANDLE
        if _bounding_wait_present(scope, handle, self.none_valued):
            return ""
        return (
            f"no bounding {handle}.wait(timeout=) or {handle}.communicate(timeout=)"
            " outside an except TimeoutExpired handler and outside a nested function"
        )

    def _reason(self, node: ast.Call, callee: str, scope: ast.AST | None) -> str:
        """Why this resolved site is not bounded, or empty when it is."""
        if callee == DYNAMIC:
            return DYNAMIC_DISPATCH
        if callee.rpartition(".")[2] in UNBOUNDABLE:
            return CANNOT_BE_BOUNDED
        if callee == f"subprocess.{POPEN}":
            return self._popen_reason(node, scope)
        return _timeout_problem(node, self.none_valued)

    def visit_Call(self, node: ast.Call) -> None:
        """Record a resolved subprocess call and decide whether it is bounded."""
        callee = self._resolve(node)
        if callee is not None:
            function, scope = self._scopes[-1] if self._scopes else (MODULE_SCOPE, None)
            reason = self._reason(node, callee, scope)
            self.sites.append(CallSite(self.path, node.lineno, callee, function, reason))
        self.generic_visit(node)


def scan_source(path: str, source: str) -> list[CallSite]:
    """Every resolved subprocess call site in one module's source."""
    tree = ast.parse(source)
    modules, direct = _subprocess_bindings(tree)
    if not modules and not direct:
        return []
    visitor = _SubprocessVisitor(path, modules, direct, _none_valued_names(tree))
    visitor.visit(tree)
    return visitor.sites


def graded_python_files() -> list[str]:
    """Every `*.py` path in this repository that git can see.

    `--cached` is the committed set; `--others --exclude-standard` adds what is
    written but not yet committed, minus anything gitignored. Both halves are
    needed - see the module docstring on why an untracked file belongs here, and
    on why the scope is the whole repository rather than `tests/`.
    """
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
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


def scan_repository() -> list[CallSite]:
    """Every resolved subprocess call site across every graded file."""
    sites: list[CallSite] = []
    for relative in graded_python_files():
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        sites.extend(scan_source(relative, source))
    return sites


def findings(sites: list[CallSite]) -> list[CallSite]:
    """The unbounded sites no exemption excuses - the unboundable class included."""
    return [
        site
        for site in sites
        if not site.bounded and not (site.exemptible and site.key in EXEMPTIONS)
    ]


def describe(sites: list[CallSite]) -> str:
    """Render sites one per line so a failure names every one of them."""
    return "\n".join(f"  {site}" for site in sites)


def exemption_budget_problems(
    pinned: dict[tuple[str, str, str, int], str], ceiling: int
) -> list[str]:
    """The exemption ratchet, checked in BOTH directions.

    A ceiling checked only from below is met forever by a table that shrinks,
    and banks room for an append nobody has to defend. See the module docstring.

    Args:
        pinned: The recorded exemptions.
        ceiling: The recorded budget.

    Returns:
        One line per direction that has drifted.
    """
    spent = len(pinned)
    if spent > ceiling:
        return [
            f"{spent} exemption(s) recorded against a budget of {ceiling}. A row was"
            " added. That is a finding to argue, not a line to type: bound the call,"
            " or raise the budget in this same change and say why. Deleting one"
            " timeout= and adding one row naming that live site is the exact disarm"
            " this budget exists to price."
        ]
    if spent < ceiling:
        return [
            f"{spent} exemption(s) recorded against a budget of {ceiling}. A site was"
            f" bounded and the budget was not lowered to match. Lower it to {spent} -"
            " a slack budget is banked room for an append nobody will have to defend."
        ]
    return []


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


def test_every_subprocess_call_in_this_repository_is_bounded_by_a_timeout() -> None:
    unbounded = findings(scan_repository())
    assert not unbounded, (
        f"{len(unbounded)} subprocess call site(s) are not bounded. An unbounded "
        "child cannot fail the test that owns it - it burns the CI job's whole "
        "budget until the lane is cancelled, which is evidence of nothing "
        "(CS-896). Pass a real timeout= at the call, or for a Popen bound it at "
        "<handle>.wait(timeout=) / <handle>.communicate(timeout=):\n" + describe(unbounded)
    )


# ---------------------------------------------------------------------------
# The guard's own liveness - a sweep that walked nothing passes silently
# ---------------------------------------------------------------------------


def test_the_enumeration_reaches_a_real_population() -> None:
    problems = floor_problems("Python files git can see", len(graded_python_files()), FILE_FLOOR)
    assert not problems, describe_problems(problems)


def test_the_sweep_finds_a_real_population_of_call_sites() -> None:
    problems = floor_problems(
        "resolved subprocess call sites", len(scan_repository()), CALL_SITE_FLOOR
    )
    assert not problems, describe_problems(problems)


@pytest.mark.parametrize(
    ("what", "floor"),
    [
        ("Python files git can see", FILE_FLOOR),
        ("resolved subprocess call sites", CALL_SITE_FLOOR),
    ],
)
def test_every_non_vacuity_floor_rejects_a_population_that_measured_nothing(
    what: str, floor: int
) -> None:
    """THE FLOOR, GRADED - because BOTH could be set to zero with the suite green.

    MEASURED on the refuted build: `FILE_FLOOR = 0` and `CALL_SITE_FLOOR = 0`
    together left the whole module at 20 passed. That is the defect each floor
    exists to prevent, restored in a two-character diff.

    THREE DIRECTIONS: nothing measured is rejected, one short is rejected, and
    the floor itself is accepted - so this is about the boundary rather than
    about the floor being large.
    """
    assert floor_problems(what, 0, floor), (
        f"the floor under {what} is {floor}, which ACCEPTS a population of nothing -"
        " the defect it exists to prevent, restored"
    )
    assert floor_problems(what, floor - 1, floor), f"the floor under {what} is off by one"
    assert floor_problems(what, floor, floor) == [], (
        f"the floor under {what} rejects a population that exactly meets it"
    )


def test_every_floor_this_module_uses_is_one_this_arm_grades() -> None:
    """CLOSING THE CLASS, so a THIRD floor here cannot arrive ungraded.

    The parametrization above is checked against what this module's SOURCE
    passes as a floor, rather than against a list somebody keeps in step by hand.
    """
    used = graded_floor_names(Path(__file__).read_text(encoding="ascii"))

    assert used, "this module passes no named floor to the floor check at all"
    graded = {"FILE_FLOOR", "CALL_SITE_FLOOR"}
    ungraded = sorted(used - graded)

    assert not ungraded, (
        f"floors used but not graded: {ungraded}. Add each to the parametrization"
        " above, so a floor that could be zeroed is one something asks about."
    )
    stale = sorted(graded - used)

    assert not stale, f"graded floors this module no longer uses as floors: {stale}"


def test_the_guard_scans_itself() -> None:
    # The detector must be inside its own population, or the file most likely to
    # grow a new subprocess call is the one file nothing grades.
    assert "tests/test_subprocess_timeouts.py" in graded_python_files()


def test_the_scan_reaches_past_the_tests_tree() -> None:
    # The scope widening, asserted rather than merely claimed. An unbounded call
    # in tools/ or scripts/ cancels the same CI lane; a prefix filter that
    # excluded them was a blind spot, not a scope.
    outside = [path for path in graded_python_files() if not path.startswith("tests/")]

    assert outside, "the sweep sees nothing outside tests/, so the widening is not real"
    sites = [site for site in scan_repository() if not site.path.startswith("tests/")]

    assert sites, "no subprocess call site was resolved outside tests/"


def test_every_enumerated_file_actually_parsed() -> None:
    # A file that failed to parse would contribute zero sites and look clean.
    unparsed = []
    for relative in graded_python_files():
        try:
            ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        except SyntaxError:
            unparsed.append(relative)
    assert not unparsed, f"files that did not parse: {unparsed}"


def describe_problems(problems: list[str]) -> str:
    """Render a problem list one per line."""
    return "\n".join(f"  {problem}" for problem in problems)


# ---------------------------------------------------------------------------
# The detector, graded on synthetic source - the known-good controls
# ---------------------------------------------------------------------------

UNBOUNDED_SOURCE: Final = """
import subprocess

def probe():
    return subprocess.run(["git", "status"], check=False)
"""

BOUNDED_SOURCE: Final = """
import subprocess

def probe():
    return subprocess.run(["git", "status"], check=False, timeout=30)
"""

ALIASED_SOURCE: Final = """
import subprocess as sp

def probe():
    return sp.check_output(["git", "status"])
"""

FROM_IMPORT_SOURCE: Final = """
from subprocess import run as launch

def probe():
    return launch(["git", "status"])
"""

SPLAT_SOURCE: Final = """
import subprocess

def probe(options):
    return subprocess.run(["git", "status"], **options)
"""

LOCAL_HELPER_SOURCE: Final = '''
def call(door, value):
    """A local helper named exactly like a subprocess entry point."""
    return door(value)

def probe():
    return call(1, 2)
'''

COMMENT_AND_STRING_SOURCE: Final = '''
import subprocess

WRAPPER = """
import subprocess
subprocess.run(["git", "status"])
"""

def probe():
    # subprocess.run() is discussed here but never called.
    return WRAPPER
'''

POPEN_BOUNDED_SOURCE: Final = """
import subprocess

def probe():
    proc = subprocess.Popen(["git", "status"])
    return proc.wait(timeout=60)
"""

POPEN_UNBOUNDED_SOURCE: Final = """
import subprocess

def probe():
    proc = subprocess.Popen(["git", "status"])
    return proc.wait()
"""

# The shape that slipped through the first version of the rule: the primary wait
# is unbounded and only the CLEANUP wait carries a timeout.
POPEN_CLEANUP_WAIT_ONLY_SOURCE: Final = """
import subprocess

def probe():
    proc = subprocess.Popen(["git", "status"])
    try:
        return proc.wait()
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)
        raise
"""

# The same shape with the bound restored - this one must still be accepted, or
# the tightening above would have broken the real site it was derived from.
POPEN_BOUNDED_WITH_CLEANUP_SOURCE: Final = """
import subprocess

def probe():
    proc = subprocess.Popen(["git", "status"])
    try:
        return proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)
        raise
"""


def test_the_detector_finds_a_planted_unbounded_call() -> None:
    # The positive control. Without this, a detector that found nothing ever
    # and a detector that works are indistinguishable from a green sweep.
    sites = scan_source("synthetic.py", UNBOUNDED_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded
    assert sites[0].reason == NO_KEYWORD


def test_the_detector_accepts_an_explicit_timeout() -> None:
    sites = scan_source("synthetic.py", BOUNDED_SOURCE)
    assert len(sites) == 1
    assert sites[0].bounded


def test_the_detector_resolves_an_aliased_module_import() -> None:
    sites = scan_source("synthetic.py", ALIASED_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.check_output"]
    assert not sites[0].bounded


def test_the_detector_resolves_a_renamed_from_import() -> None:
    sites = scan_source("synthetic.py", FROM_IMPORT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded


def test_a_kwargs_splat_is_not_accepted_as_a_bound() -> None:
    sites = scan_source("synthetic.py", SPLAT_SOURCE)
    assert len(sites) == 1
    assert not sites[0].bounded, "a **kwargs splat cannot be shown to carry a timeout"


def test_a_local_helper_sharing_a_subprocess_name_is_not_a_finding() -> None:
    # The false positive a name-only scan produces dozens of times in this tree.
    assert scan_source("synthetic.py", LOCAL_HELPER_SOURCE) == []


def test_a_comment_or_a_string_literal_is_not_a_call_site() -> None:
    # The false positive the 700-character regex window produced on the
    # `# subprocess.run() inside run_git()` comment in
    # tests/test_exception_rendering.py, and on `subprocess.run = boom` inside
    # that file's INSTALLER_CRASH_WRAPPER string literal.
    assert scan_source("synthetic.py", COMMENT_AND_STRING_SOURCE) == []


def test_a_popen_bounded_at_its_wait_is_accepted() -> None:
    sites = scan_source("synthetic.py", POPEN_BOUNDED_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert sites[0].bounded


def test_a_popen_with_an_unbounded_wait_is_a_finding() -> None:
    # Popen cannot take a constructor timeout, so exempting the class would wave
    # this through. The bound is graded at the wait instead.
    sites = scan_source("synthetic.py", POPEN_UNBOUNDED_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert not sites[0].bounded


def test_a_cleanup_wait_in_a_timeout_handler_is_not_a_bound() -> None:
    # MEASURED: the first version of this rule passed this shape, which is the
    # exact shape of the one real Popen site in the tree. A wait inside an
    # `except TimeoutExpired` handler runs only because a bound already fired.
    sites = scan_source("synthetic.py", POPEN_CLEANUP_WAIT_ONLY_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert not sites[0].bounded, "a cleanup wait was accepted as the bound"


def test_a_real_bound_alongside_a_cleanup_wait_is_still_accepted() -> None:
    # The other direction. Pruning the handler must not redden the real site.
    sites = scan_source("synthetic.py", POPEN_BOUNDED_WITH_CLEANUP_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert sites[0].bounded


# ---------------------------------------------------------------------------
# THE TIMEOUT VALUE - the one-token disarm the refuted build accepted
# ---------------------------------------------------------------------------

NONE_TIMEOUT_SOURCE: Final = """
import subprocess

def probe():
    return subprocess.run(["git", "status"], timeout=None)
"""

ZERO_TIMEOUT_SOURCE: Final = """
import subprocess

def probe():
    return subprocess.run(["git", "status"], timeout=0)
"""

NAMED_TIMEOUT_SOURCE: Final = """
import subprocess

LIMIT = 120

def probe():
    return subprocess.run(["git", "status"], timeout=LIMIT)
"""

NAMED_NONE_TIMEOUT_SOURCE: Final = """
import subprocess

LIMIT = None

def probe():
    return subprocess.run(["git", "status"], timeout=LIMIT)
"""

POPEN_NONE_WAIT_SOURCE: Final = """
import subprocess

def probe():
    proc = subprocess.Popen(["git", "status"])
    return proc.wait(timeout=None)
"""


def test_timeout_none_is_not_a_bound() -> None:
    # THE HEADLINE. MEASURED at the interpreter: timeout=None returned after
    # 3.1s against a 3s child and raised nothing - it IS the unbounded default.
    # The refuted build read the keyword's name and never its value, so every
    # bound in this repository was revertible by one token with the guard green.
    sites = scan_source("synthetic.py", NONE_TIMEOUT_SOURCE)
    assert len(sites) == 1
    assert not sites[0].bounded, "timeout=None was accepted as a bound"
    assert sites[0].reason == NONE_IS_THE_DEFAULT


def test_timeout_zero_is_accepted_and_the_price_is_stated() -> None:
    # THE DELIBERATE ACCEPT. MEASURED: timeout=0 raised TimeoutExpired at 0.00s.
    # It cannot burn the budget, so it is not the failure this module exists for
    # - it is a loud immediate failure, which is the outcome the module wants.
    sites = scan_source("synthetic.py", ZERO_TIMEOUT_SOURCE)
    assert len(sites) == 1
    assert sites[0].bounded, "timeout=0 cannot hang, so refusing it grades the wrong thing"


def test_a_named_constant_is_accepted_as_a_bound() -> None:
    # The dominant real spelling in this tree - refusing it would refuse exactly
    # what the rule wants written.
    sites = scan_source("synthetic.py", NAMED_TIMEOUT_SOURCE)
    assert len(sites) == 1
    assert sites[0].bounded


def test_a_name_bound_to_none_at_module_scope_is_still_refused() -> None:
    # The two-token version of the headline: spell None once, use it by name.
    # ONE HOP is all this resolves - see the module docstring for the residual.
    sites = scan_source("synthetic.py", NAMED_NONE_TIMEOUT_SOURCE)
    assert len(sites) == 1
    assert not sites[0].bounded, "a name bound to None at module scope was a bound"


def test_a_popen_wait_with_a_none_timeout_is_not_a_bound() -> None:
    # The same rule has to reach the wait, or the Popen path keeps the hole.
    sites = scan_source("synthetic.py", POPEN_NONE_WAIT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert not sites[0].bounded, "wait(timeout=None) was accepted as the bound"


# ---------------------------------------------------------------------------
# THE FIVE ESCAPE HATCHES - six unbounded spawns passed the refuted build
# ---------------------------------------------------------------------------

GETOUTPUT_SOURCE: Final = """
import subprocess

def probe():
    return subprocess.getoutput("git status")
"""

GETSTATUSOUTPUT_SOURCE: Final = """
import subprocess

def probe():
    return subprocess.getstatusoutput("git status")
"""

MODULE_REBOUND_SOURCE: Final = """
import subprocess

_sp = subprocess

def probe():
    return _sp.run(["git", "status"])
"""

MODULE_REBOUND_TWICE_SOURCE: Final = """
import subprocess

_first = subprocess
_second = _first

def probe():
    return _second.run(["git", "status"])
"""

CALLABLE_REBOUND_SOURCE: Final = """
import subprocess

_runner = subprocess.run

def probe():
    return _runner(["git", "status"])
"""

GETATTR_SOURCE: Final = """
import subprocess

def probe():
    return getattr(subprocess, "run")(["git", "status"])
"""

GETATTR_DYNAMIC_SOURCE: Final = """
import subprocess

def probe(name):
    return getattr(subprocess, name)(["git", "status"])
"""

STAR_IMPORT_SOURCE: Final = """
from subprocess import *

def probe():
    return run(["git", "status"])
"""

REBOUND_AND_BOUNDED_SOURCE: Final = """
import subprocess

_sp = subprocess

def probe():
    return _sp.run(["git", "status"], timeout=30)
"""


def test_getoutput_is_refused_outright_rather_than_asked_for_a_timeout() -> None:
    # It has no timeout parameter in any Python version, so "add one" is not
    # advice anybody can follow. The message has to say that.
    sites = scan_source("synthetic.py", GETOUTPUT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.getoutput"]
    assert not sites[0].bounded
    assert sites[0].reason == CANNOT_BE_BOUNDED


def test_getstatusoutput_is_refused_outright() -> None:
    sites = scan_source("synthetic.py", GETSTATUSOUTPUT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.getstatusoutput"]
    assert not sites[0].bounded
    assert sites[0].reason == CANNOT_BE_BOUNDED


def test_an_unboundable_call_cannot_be_excused_by_an_exemption() -> None:
    # The class is not exemptible - a row for one would be a permanent hole for
    # a call that never needed to exist. Even a key that matches exactly must
    # leave the site in the findings.
    sites = scan_source("synthetic.py", GETOUTPUT_SOURCE)
    assert not sites[0].exemptible
    assert findings(sites) == sites, "an unboundable site was excused"


def test_the_module_rebound_by_assignment_is_resolved() -> None:
    sites = scan_source("synthetic.py", MODULE_REBOUND_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded


def test_the_module_rebound_twice_is_resolved_by_the_fixpoint() -> None:
    # One pass would resolve `_first` and stop. The loop runs to a fixpoint.
    sites = scan_source("synthetic.py", MODULE_REBOUND_TWICE_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded


def test_the_callable_rebound_by_assignment_is_resolved() -> None:
    sites = scan_source("synthetic.py", CALLABLE_REBOUND_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded


def test_a_getattr_dispatch_on_a_literal_name_is_resolved() -> None:
    sites = scan_source("synthetic.py", GETATTR_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded


def test_a_getattr_dispatch_on_a_variable_is_refused_not_ignored() -> None:
    # Undecidable statically. The .githooks/pre-push rule: a LOUD FALSE REFUSAL
    # beats a SILENT FALSE ACCEPT, so this is reported rather than skipped.
    sites = scan_source("synthetic.py", GETATTR_DYNAMIC_SOURCE)
    assert [site.callee for site in sites] == [DYNAMIC]
    assert not sites[0].bounded
    assert sites[0].reason == DYNAMIC_DISPATCH


def test_a_star_import_binds_the_entry_points() -> None:
    sites = scan_source("synthetic.py", STAR_IMPORT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.run"]
    assert not sites[0].bounded


def test_a_rebound_module_that_is_bounded_is_still_accepted() -> None:
    # The other direction: widening the bindings must not redden a real bound.
    sites = scan_source("synthetic.py", REBOUND_AND_BOUNDED_SOURCE)
    assert len(sites) == 1
    assert sites[0].bounded


# ---------------------------------------------------------------------------
# THE POPEN HANDLE - the bound has to belong to the process, not to anything
# ---------------------------------------------------------------------------

POPEN_FOREIGN_WAIT_SOURCE: Final = """
import subprocess
import threading

def probe():
    ready = threading.Event()
    proc = subprocess.Popen(["git", "status"])
    ready.wait(timeout=5)
    return proc.wait()
"""

POPEN_NESTED_WAIT_SOURCE: Final = """
import subprocess

def probe():
    proc = subprocess.Popen(["git", "status"])

    def never_called():
        return proc.wait(timeout=5)

    return proc.wait()
"""

POPEN_WITH_STATEMENT_SOURCE: Final = """
import subprocess

def probe():
    with subprocess.Popen(["git", "status"]) as proc:
        return proc.wait(timeout=60)
"""

POPEN_UNNAMED_SOURCE: Final = """
import subprocess

def probe():
    subprocess.Popen(["git", "status"])
    return None
"""

POPEN_ATTRIBUTE_HANDLE_SOURCE: Final = """
import subprocess

class Runner:
    def probe(self):
        self.proc = subprocess.Popen(["git", "status"])
        return self.proc.wait(timeout=60)
"""

POPEN_TWO_PROCESSES_SOURCE: Final = """
import subprocess

def probe():
    first = subprocess.Popen(["git", "status"])
    second = subprocess.Popen(["git", "log"])
    first.wait(timeout=60)
    return second.wait()
"""


def test_a_wait_on_a_foreign_object_does_not_bound_a_popen() -> None:
    # MEASURED on the refuted build: this reported bounded=True. Waiting on an
    # Event for readiness and then on the child is idiomatic in exactly the code
    # that spawns a server, so this shape is common rather than contrived.
    sites = scan_source("synthetic.py", POPEN_FOREIGN_WAIT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert not sites[0].bounded, "an Event().wait(timeout=) satisfied a Popen bound"


def test_a_wait_in_a_function_nobody_calls_does_not_bound_a_popen() -> None:
    # MEASURED on the refuted build: this reported bounded=True as well. A bound
    # that never executes is not a bound.
    sites = scan_source("synthetic.py", POPEN_NESTED_WAIT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert not sites[0].bounded, "a wait in an uncalled nested function was the bound"


def test_a_popen_bound_in_a_with_statement_is_accepted() -> None:
    # The context-manager spelling binds a name too, and must not be refused.
    sites = scan_source("synthetic.py", POPEN_WITH_STATEMENT_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert sites[0].bounded


def test_a_popen_bound_to_no_name_is_refused_rather_than_assumed() -> None:
    # Nothing can be tied to it, so the honest answer is a refusal.
    sites = scan_source("synthetic.py", POPEN_UNNAMED_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert not sites[0].bounded
    assert sites[0].reason == UNNAMED_HANDLE


def test_a_popen_held_on_an_attribute_is_bounded_through_that_spelling() -> None:
    # `self.proc` is a chain, not a bare name, and the wait spells it the same
    # way - so tying the bound by spelling accepts it.
    sites = scan_source("synthetic.py", POPEN_ATTRIBUTE_HANDLE_SOURCE)
    assert [site.callee for site in sites] == ["subprocess.Popen"]
    assert sites[0].bounded


def test_two_processes_in_one_function_are_graded_separately() -> None:
    # The limitation the refuted build ADMITTED but did not close: one bounded
    # wait used to excuse both. Now each Popen is tied to its own handle.
    sites = scan_source("synthetic.py", POPEN_TWO_PROCESSES_SOURCE)
    # Named, and named LOCALLY: ruff PLR2004 reads a bare 2 in a comparison as a
    # magic value, and a module-scope name would owe the floor walk a registration.
    both_processes = 2

    assert len(sites) == both_processes
    assert [site.bounded for site in sites] == [True, False]


# ---------------------------------------------------------------------------
# The exemption table, graded in every direction it can be disarmed from
# ---------------------------------------------------------------------------


def test_an_exemption_actually_excuses_a_site() -> None:
    # Proves the mechanism works, which an empty live table cannot show.
    sites = scan_source("synthetic.py", UNBOUNDED_SOURCE)
    exemptions = {sites[0].key: "synthetic - proves the exemption path is wired"}
    assert [site for site in sites if not site.bounded and site.key not in exemptions] == []


def test_a_site_without_an_exemption_is_still_a_finding() -> None:
    # The other direction: the exemption must be specific, not a blanket. A key
    # naming a DIFFERENT function must not excuse this site.
    sites = scan_source("synthetic.py", UNBOUNDED_SOURCE)
    elsewhere = {("synthetic.py", "someone_else", "subprocess.run", 5): "wrong function"}
    still_found = [site for site in sites if not site.bounded and site.key not in elsewhere]
    assert len(still_found) == 1


def test_an_exemption_naming_another_line_does_not_excuse_this_one() -> None:
    # The LINE is in the key, so one row cannot blanket every same-callee site
    # in one function - which is what the refuted build's three-part key did.
    sites = scan_source("synthetic.py", UNBOUNDED_SOURCE)
    path, function, callee, line = sites[0].key
    other_line = {(path, function, callee, line + 1): "a row for the line next door"}
    still_found = [site for site in sites if not site.bounded and site.key not in other_line]
    assert len(still_found) == 1, "a row naming another line excused this site"


def test_no_exemption_names_a_site_that_no_longer_exists() -> None:
    # A stale entry stops excusing anything and starts hiding the next one. With
    # the line in the key this also reddens when the site merely MOVED, which is
    # a loud false refusal rather than a silent wrong excuse.
    live = {site.key for site in scan_repository()}
    stale = sorted(key for key in EXEMPTIONS if key not in live)
    assert not stale, f"exemption entries naming call sites that no longer exist: {stale}"


def test_every_exemption_states_a_substantive_reason() -> None:
    thin = sorted(
        key for key, reason in EXEMPTIONS.items() if len(reason.strip()) < EXEMPTION_REASON_MINIMUM
    )
    assert not thin, (
        f"exemption entries whose reason is too thin to be an argument: {thin}."
        " A length check cannot make a reason TRUE - it only makes a placeholder"
        " cost more to type than it is worth."
    )


def test_the_exemption_table_is_within_its_recorded_budget() -> None:
    problems = exemption_budget_problems(EXEMPTIONS, EXEMPTION_BUDGET)
    assert not problems, describe_problems(problems)


def test_the_exemption_budget_is_graded_in_both_directions() -> None:
    """THE TWO-LINE DISARM, PRICED - and it is why an empty table needs a budget.

    MEASURED on the refuted build: deleting one `timeout=` from a live site and
    adding one row naming that site left the suite at 20 passed. Nothing asked
    how many rows there were, so the row cost nothing. Now a row must be paid
    for with a number in the diff that somebody has to argue for.

    BOTH DIRECTIONS, because a ceiling checked only from below is met forever by
    a table that shrinks, and the slack it leaves is banked room for a future
    append nobody will have to defend.
    """
    one_row = {("synthetic.py", "probe", "subprocess.run", 5): "a row added for a live site"}

    assert exemption_budget_problems(one_row, EXEMPTION_BUDGET), (
        "a row added against the recorded budget was free - the exact disarm this"
        " module was refuted for"
    )
    assert exemption_budget_problems({}, 1), "a budget with slack in it was accepted"
    assert exemption_budget_problems(one_row, 1) == [], "a table that exactly spends its budget"


def test_the_budget_is_not_derived_from_the_table_it_bounds() -> None:
    """`EXEMPTION_BUDGET = len(EXEMPTIONS)` satisfies both directions forever.

    One line, no number in the diff, every future append free. It has been filed
    in this repo twice, so it is checked from the SOURCE - by import time the
    budget is just an int and its provenance is gone.
    """
    problems = derived_bound_problems(Path(__file__).read_text(encoding="ascii"), ["EXEMPTIONS"])
    assert not problems, describe_problems(problems)
