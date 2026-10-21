"""The CS-200 phase 2 gate: properties the data layer must be FORCED to have.

Every other module under ``tests/data`` tests what a data-layer module DOES.
This one tests what the data layer and its own test suite must never start
doing, and it exists because the middle clause of the CS-200 acceptance
criterion - "the synthetic-fixture suite runs green on a machine with no game
installed" - was, until this module, true only by luck.

Luck is not a gate. Slices A through E each happened to write tests that need
no install, but nothing failed if a future test quietly reached for one. That
is precisely the CONVENTIONS.md section 7.2 class "the unrun gate is where the
bug hides": the property that is never exercised is the property that silently
stops holding. The load-bearing test here is
``test_the_data_layer_suite_passes_with_the_install_unresolvable``, which runs
the whole data-layer suite in a child interpreter with the install forced
unresolvable and asserts a zero exit. On a machine with no game installed that
child run is what CI does; on the operator's machine, where the game IS
installed, it is the only thing that reproduces CI's environment.

Five properties, each a separate section below:

a. Every module in ``clockspeed/data/`` imports with no install present, and
   none of them resolves an install at IMPORT time rather than at call time.
b. No test in ``tests/data`` depends on a real install.
c. No source file in ``clockspeed/data/`` hardcodes a drive-letter path or an
   account-id-shaped digit run.
d. The synthetic corpus is genuinely synthetic, and no fixture under
   ``tests/`` is a save, a usmap or a shipped locale file.
e. The data-layer seams are importable in isolation, so the allowed-import
   matrix that ``docs/ARCHITECTURE.md`` section 3.1 calls mechanically
   checkable actually is - for this layer, checked against ``sys.modules``
   rather than against source text.

Nothing here requires a game install, and nothing here writes to one. The
child interpreters are launched through ``sys.executable`` so they inherit the
running interpreter rather than whatever a bare name would resolve to on PATH.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from functools import cache
from pathlib import Path

import pytest

from clockspeed.data import locate
from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
    MIN_ACCOUNT_ID_DIGITS,
)
from clockspeed.data.version import DOCS_RELATIVE, PIN_BEGIN_MARKER, PIN_END_MARKER

# ---------------------------------------------------------------------------
# Paths, derived rather than written down
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PACKAGE = REPO_ROOT / "clockspeed" / "data"
TESTS_ROOT = REPO_ROOT / "tests"
DATA_TESTS = TESTS_ROOT / "data"
SYNTHETIC_CORPUS = DATA_TESTS / "synthetic.py"

# This module's own path. The child pytest run below MUST exclude it or the
# gate re-runs itself forever, so the exclusion is derived from __file__ and
# never from a literal filename that a rename would leave pointing at nothing.
THIS_MODULE = Path(__file__).resolve()

# The modules the phase 2 gate covers. Short names, joined to the package
# below, so the parametrize ids read as the module rather than as a path.
# "assets" joined the list when it landed - it reads the shipped install, which
# is exactly the property this gate exists to hold, so leaving it out would have
# left the newest install reader the only one ungraded.
DATA_MODULES: tuple[str, ...] = (
    "assets",
    "blobs",
    "docs_extract",
    "locate",
    "registry",
    "schematics",
    "version",
)

# ---------------------------------------------------------------------------
# Forcing "no install"
# ---------------------------------------------------------------------------

# clockspeed/data/locate.py resolves in the order environment, then
# config/local.json, then auto-detection - and an override naming something
# that is not a directory resolves to None WITHOUT falling through to
# detection. That behaviour is what lets a test force "no install" on a
# machine where the game is installed, and it is asserted directly by
# tests/data/test_locate.py::
# test_game_dir_environment_override_that_is_not_a_directory_is_reported_not_raised.
#
# The path is under the repo root rather than under a temporary directory so
# it needs no fixture and is identical in every child. It is asserted absent
# below, so it can never quietly become a real directory and turn this whole
# module into a no-op.
ABSENT = REPO_ROOT / "no-such-path-phase-2-gate"

_CHILD_TIMEOUT_SECONDS = 300


def no_install_env() -> dict[str, str]:
    """Build a child environment in which no install, save root or account can resolve.

    All four override variables are set, not just the two that name an
    install: leaving ``CLOCKSPEED_SAVE_ROOT`` unset would let a child fall
    through to ``%LOCALAPPDATA%`` and find the operator's real save
    directory, which is exactly the machine dependence this module exists to
    forbid.

    Returns:
        A copy of the current environment with the overrides applied.
    """
    env = dict(os.environ)
    env[ENV_GAME_DIR] = str(ABSENT / "install")
    env[ENV_SAVE_ROOT] = str(ABSENT / "saves")
    env[ENV_ACCOUNT_DIR] = str(ABSENT / "account")
    env[ENV_LOCAL_CONFIG] = str(ABSENT / "local.json")
    # CONVENTIONS.md section 10: pin the child's text encoding so its output
    # decodes the same way on every machine.
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_child(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run a child interpreter from the repo root and capture its output.

    ``sys.executable`` is the only correct way to name the interpreter here.
    A bare ``python`` would resolve off PATH to whatever happens to be first,
    and an absolute interpreter path in a tracked file is forbidden outright
    (CONVENTIONS.md section 10).

    Every caller binds ``returncode`` to a local before asserting on it, and
    that is not style. ``assert child.returncode == 0`` makes pytest's
    assertion introspection repr the whole CompletedProcess in its "where"
    clause, and ``args[0]`` is the absolute interpreter path - which on a
    default Windows install sits under the operator's home directory and
    carries their account name into the CI log. Asserting on a plain int
    prints a plain int. tests/data/test_drift_guard_data.py records the same
    discipline for the same reason.

    Args:
        args: Arguments after the interpreter.
        env: The child environment.

    Returns:
        The completed process, decoded as text. A non-zero exit is returned
        rather than raised so the caller can assert on it.
    """
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHILD_TIMEOUT_SECONDS,
        env=env,
        check=False,
    )


def test_the_forced_absent_path_really_is_absent() -> None:
    """The path every child points at must not exist, or the whole module is vacuous.

    If ``ABSENT`` ever became a real directory the overrides would resolve to
    something and every "no install" assertion below would be testing the
    opposite of what it says.
    """
    assert not ABSENT.exists(), (
        f"{ABSENT.name} exists, so the no-install overrides resolve to something real"
    )


# ===========================================================================
# a. The data layer imports with no install present
# ===========================================================================

# Importing a module must never resolve an install. Resolution is filesystem
# and registry work whose answer differs per machine and per session, so a
# module that does it at import time is unusable in a test, unusable in CI,
# and produces a different object depending on when it was first imported.
#
# The names are listed rather than discovered so the gate is a stated
# contract, and test_the_resolver_set_matches_locates_public_surface below
# asserts the list against the module so a resolver added later cannot slip
# past by simply not being named here.
RESOLVER_NAMES: tuple[str, ...] = (
    "local_config",
    "local_config_path",
    "numeric_account_dirs",
    "resolve_account_dir",
    "resolve_game_dir",
    "resolve_save_root",
)

# Imports the module named in argv[1] and reports every clockspeed module the
# import pulled in. Serves section a (it exits non-zero if the import raises)
# and section e (its stdout is the measured import graph).
_PROBE_IMPORT = """
import importlib
import json
import sys

importlib.import_module(sys.argv[1])
print(json.dumps(sorted(name for name in sys.modules if name.startswith("clockspeed"))))
"""

# Replaces every locate resolver with a raiser BEFORE importing the target, so
# a resolver called at import time turns into a non-zero exit with a message
# naming the resolver. Patching locate first is what makes this work through a
# "from clockspeed.data.locate import resolve_game_dir" in the target too: the
# target binds whatever the attribute holds at the moment it imports.
_PROBE_REFUSE = """
import importlib
import sys

locate = importlib.import_module("clockspeed.data.locate")


def _make(resolver):
    def _refuse(*args, **kwargs):
        raise AssertionError("IMPORT-TIME RESOLUTION via " + resolver)

    return _refuse


for _name in sys.argv[2].split(","):
    setattr(locate, _name, _make(_name))

importlib.import_module(sys.argv[1])
print("imported")
"""


@cache
def import_probe(module: str) -> subprocess.CompletedProcess[str]:
    """Import one data-layer module in a fresh interpreter with no install resolvable.

    Cached because sections a and e ask different questions of the same run,
    and a child interpreter per question would double the cost of this module
    for no extra coverage.

    Args:
        module: Short module name under ``clockspeed.data``.

    Returns:
        The completed child process.
    """
    return run_child(["-c", _PROBE_IMPORT, f"clockspeed.data.{module}"], no_install_env())


@pytest.mark.parametrize("module", DATA_MODULES)
def test_data_module_imports_with_the_install_unresolvable(module: str) -> None:
    """Importing the module on a machine with no install must not raise.

    The failure this catches is a module that reads the install, the save
    root or config/local.json at import time: it works on the operator's
    machine, raises on a clean CI runner, and the traceback surfaces inside
    whatever unrelated caller happened to touch the module first.
    """
    probe = import_probe(module)
    exit_code = probe.returncode
    assert exit_code == 0, (
        f"importing clockspeed.data.{module} with no install failed:\n{probe.stderr}"
    )


@pytest.mark.parametrize("module", [name for name in DATA_MODULES if name != "locate"])
def test_data_module_does_not_resolve_the_install_at_import_time(module: str) -> None:
    """No consumer module calls a locate resolver while it is being imported.

    Stronger than the import test above, which a module could pass while
    still resolving successfully on a machine where resolution happens to
    work. Here every resolver raises, so any import-time call fails loudly.

    ``locate`` itself is excluded because it cannot be patched before it is
    imported; ``test_data_module_calls_no_resolver_at_module_level`` covers
    it by reading its module-level statements instead.
    """
    probe = run_child(
        ["-c", _PROBE_REFUSE, f"clockspeed.data.{module}", ",".join(RESOLVER_NAMES)],
        no_install_env(),
    )
    exit_code = probe.returncode
    assert exit_code == 0, (
        f"clockspeed.data.{module} resolved the install at import time:\n{probe.stderr}"
    )
    assert "IMPORT-TIME RESOLUTION" not in probe.stderr


def test_the_resolver_set_matches_locates_public_surface() -> None:
    """RESOLVER_NAMES names every public resolver locate defines, and nothing else.

    An empty or stale set would make both probes above vacuous while leaving
    them green - a claim about the pattern rather than about the code
    (CONVENTIONS.md section 15.1). ``redact`` is excluded deliberately: it is
    the privacy helper, it resolves nothing, and patching it to raise would
    break the very redaction the failure messages depend on. Re-exported
    names such as ``Path`` are filtered by ``__module__``.

    RECORD TYPES ARE EXEMPT, DERIVED RATHER THAN LISTED. A public frozen
    dataclass such as the skip record CS-443 added is callable, defined here,
    and resolves nothing, so naming each one would make this a hand-maintained
    allowlist - and a hand-maintained list is the thing that rots. The
    exemption is taken from the OBJECT instead.

    IT IS CONTROLLED ON TWO PROPERTIES, AND THE FIRST ONE ALONE WAS NOT ENOUGH.
    "Frozen dataclass" was the original test, justified in this docstring by
    the claim that a resolver is not one. An adversary refuted that by planting
    a frozen dataclass carrying ``__call__`` - an entirely ordinary resolver
    shape, and one this codebase is moving toward - which walked straight
    through while the gate stayed green. That sentence was a false universal of
    exactly the kind ADR 0008 forecloses, so it is deleted rather than hedged.
    What is checked now is frozen dataclass AND instances that are not
    callable, both derived from the object, and the planted callable record is
    what grades the second half.
    """
    public = {
        name
        for name in dir(locate)
        if not name.startswith("_")
        and callable(getattr(locate, name))
        and getattr(getattr(locate, name), "__module__", None) == locate.__name__
    }
    record_types = {name for name in public if isinstance(getattr(locate, name), type)}
    for name in sorted(record_types):
        candidate = getattr(locate, name)
        # getattr rather than a direct attribute read: typeshed's dataclass
        # protocol does not declare __dataclass_params__, so reading it
        # directly is a mypy union-attr error on a true statement.
        params = getattr(candidate, "__dataclass_params__", None)
        frozen = dataclasses.is_dataclass(candidate) and bool(getattr(params, "frozen", False))
        # Instances callable => the class can act as a resolver, whatever else
        # it is. Read off the MRO rather than dir(), because every class has a
        # __call__ through its metaclass and dir() would report all of them.
        instances_callable = any(
            "__call__" in vars(base) for base in candidate.__mro__ if base is not object
        )
        exemption_note = (
            "Either it is a resolver the import-time probes must cover and belongs in "
            "RESOLVER_NAMES, or the exemption in this test needs rethinking - do not "
            "widen it silently"
        )
        assert frozen, (
            f"locate.{name} is a public class that is not a frozen dataclass, so it does "
            f"not qualify for the record-type exemption. {exemption_note}"
        )
        assert not instances_callable, (
            f"locate.{name} is a frozen dataclass whose INSTANCES ARE CALLABLE, which is "
            f"an ordinary resolver shape, so it does not qualify either. {exemption_note}"
        )

    assert public - {"redact"} - record_types == set(RESOLVER_NAMES), (
        "locate's public resolver surface moved; RESOLVER_NAMES must be updated or the "
        "import-time probes silently stop covering the new resolver"
    )


_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _calls_under(node: ast.AST) -> list[ast.Call]:
    """Collect every call expression anywhere beneath a node.

    Args:
        node: Any AST node.

    Returns:
        The call nodes, in traversal order.
    """
    return [child for child in ast.walk(node) if isinstance(child, ast.Call)]


def _import_time_calls(node: ast.AST) -> list[ast.Call]:
    """Collect the calls a module makes while it is being imported.

    Descends through every statement that runs at import time - including
    ones nested in a module-level ``if``, ``try`` or ``with`` - and prunes at
    a function or class body, whose contents run when they are called rather
    than when the module loads. Decorator expressions are NOT pruned, because
    a decorator does run at import time.

    Args:
        node: The module node, or any node inside import-time scope.

    Returns:
        The call nodes that execute during import.
    """
    found: list[ast.Call] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _SCOPE_NODES):
            for decorator in child.decorator_list:
                found.extend(_calls_under(decorator))
            continue
        if isinstance(child, ast.Call):
            found.append(child)
        found.extend(_import_time_calls(child))
    return found


def _called_name(call: ast.Call) -> str | None:
    """Return the bare name a call targets, ignoring how it was reached.

    ``resolve_game_dir()`` and ``locate.resolve_game_dir()`` are the same
    defect, so both reduce to ``resolve_game_dir``.

    Args:
        call: The call node.

    Returns:
        The name, or None for a call on an expression with no simple name.
    """
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


@pytest.mark.parametrize("module", DATA_MODULES)
def test_data_module_calls_no_resolver_at_module_level(module: str) -> None:
    """No data-layer module invokes a resolver from a statement that runs on import.

    The AST is the right instrument here and a grep is not: a grep cannot
    tell a call inside a function body, which is correct, from the identical
    text at module level, which is the defect. This is also the only check
    that covers ``locate`` itself, which cannot be patched before it loads.
    """
    source = (DATA_PACKAGE / f"{module}.py").read_text(encoding="utf-8")
    offenders = sorted(
        {
            name
            for name in (_called_name(call) for call in _import_time_calls(ast.parse(source)))
            if name in RESOLVER_NAMES
        }
    )
    assert not offenders, (
        f"clockspeed/data/{module}.py calls {offenders} at module level, so importing it "
        "resolves the install instead of leaving that to the caller"
    )


def test_the_import_time_call_finder_actually_finds() -> None:
    """The AST walker separates import-time calls from deferred ones.

    Without this the test above would pass for a module that never runs, and
    a walker bug would make it permanently green. Both directions are pinned:
    what it must catch, and what it must not flag.
    """
    caught = ast.parse(
        "if True:\n    resolve_game_dir()\n\n@resolve_save_root()\ndef decorated():\n    pass\n"
    )
    deferred = ast.parse(
        "def later():\n"
        "    return resolve_game_dir()\n"
        "\n"
        "class Holder:\n"
        "    def method(self):\n"
        "        return locate.resolve_account_dir(None)\n"
    )

    found = {name for name in (_called_name(call) for call in _import_time_calls(caught)) if name}
    assert found == {"resolve_game_dir", "resolve_save_root"}, (
        f"the walker missed an import-time call; it found {sorted(found)}"
    )
    assert not _import_time_calls(deferred), (
        "the walker flagged a call inside a function or method body, which runs at "
        "call time and is exactly what the modules are supposed to do"
    )


# ---------------------------------------------------------------------------
# a, continued: redact() reaches no resolver, at any depth
# ---------------------------------------------------------------------------
#
# A resolver call inside redact() is not a style problem. It is an infinite
# recursion, and the cycle is short:
#
#     redact -> resolve_save_root -> _override -> local_config
#            -> _read_local_config -> _note -> redact
#
# It does not blow up today for one reason only: ``_override`` passes no
# collector, so ``_note`` returns at its first statement without redacting
# anything. Wire a collector down that path - which is precisely what the
# open reporting work does - and the cycle closes. Measured on a planted
# version of exactly that shape, it terminates in a RecursionError.
#
# The safety of redact() therefore rests on a call that is ABSENT, and nothing
# mechanical was keeping it absent. Reaching for resolve_save_root() to learn
# where the save root is would read as entirely reasonable in review, and the
# comment saying not to is not a mechanism - it is a hope with better
# formatting.
#
# THIS IS A FENCE, NOT A REPRODUCTION. It is green at HEAD and must stay
# green; it fails only if someone later reintroduces the call. Stating that
# plainly matters, because a fence written up as a reproduction is a false
# sentence about what the suite has measured.
#
# It reads the TRANSITIVE closure rather than redact()'s own body, because the
# recursion does not care how many helpers sit between its two ends. A single
# private wrapper would defeat a body-only check while leaving the cycle
# exactly as closed as before.

_FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def _function_defs_by_name(tree: ast.AST) -> dict[str, list[_FunctionNode]]:
    """Index every function definition in a parsed module by its bare name.

    Indexed at ANY depth rather than at module level only, and the resulting
    over-approximation is deliberate. ``_redaction_pairs`` defines its two
    accumulators as closures today; a later refactor that hoists one to module
    level, or tucks a helper into a class body, must not quietly drop it out of
    the call graph. Over-approximating can only WIDEN what the fence covers,
    which is the direction that fails safe.

    A name defined more than once maps to every definition and all of them are
    walked, for the same reason: guessing which one a call reaches would be the
    place a real defect hid.

    Args:
        tree: A parsed module, or any node to search beneath.

    Returns:
        Bare function name to the definitions carrying it.
    """
    found: dict[str, list[_FunctionNode]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found.setdefault(node.name, []).append(node)
    return found


def _transitively_called_names(source: str, root: str) -> set[str]:
    """Collect every name called by ``root`` or by any local function it reaches.

    Walks the call graph from ``root``, following only names the module itself
    defines - an external call such as ``re.sub`` is recorded but not descended
    into, because the module cannot reintroduce a resolver through the standard
    library.

    Args:
        source: Module source text.
        root: The function to start from. Must be defined in ``source``.

    Returns:
        Every bare called name reachable from ``root``, the root's own direct
        calls included.
    """
    defs = _function_defs_by_name(ast.parse(source))
    assert root in defs, f"{root} is not defined in the source under test"

    reached = {root}
    pending = [root]
    called: set[str] = set()
    while pending:
        for node in defs[pending.pop()]:
            for name in (_called_name(call) for call in _calls_under(node)):
                if name is None:
                    continue
                called.add(name)
                if name in defs and name not in reached:
                    reached.add(name)
                    pending.append(name)
    return called


def test_redact_calls_no_resolver_at_any_depth() -> None:
    """redact() must not reach a resolver, directly or through any helper.

    The recursion argument is spelled out in the comment above this test. The
    check is graded against RESOLVER_NAMES, which
    ``test_the_resolver_set_matches_locates_public_surface`` holds against
    locate's live public surface - so a resolver ADDED later is inside this
    fence automatically, with nothing to remember to update. Transcribing the
    resolver names into a second literal list here would have produced a fence
    that grades itself.

    This also turns the parenthetical in that test's docstring - that redact
    "resolves nothing" - from a stated belief into a checked property. The
    prose stays where it is; it explains why redact is exempt from the
    import-time probes, which is a different point from this one.
    """
    source = (DATA_PACKAGE / "locate.py").read_text(encoding="utf-8")
    offenders = sorted(_transitively_called_names(source, "redact") & set(RESOLVER_NAMES))
    assert not offenders, (
        f"redact() reaches {offenders}. Every resolver funnels through _override, which "
        "reads config/local.json, which reports a discard through _note, which redacts the "
        "subject - so this call is a cycle back into redact. It survives review only while "
        "_note is passed no collector. Read os.environ directly instead."
    )


def test_the_redact_closure_finder_flags_a_planted_resolver_and_only_that() -> None:
    """The closure walker catches a planted resolver call and leaves innocents alone.

    Three directions, because two would not be enough. A walker that flagged
    every module containing the string would pass the first check and be
    useless; one that read only redact's own body would pass the first two and
    miss the wrapper case, which is the one an ordinary refactor produces.
    """
    planted_directly = (
        "def redact(text):\n"
        "    root = resolve_save_root()\n"
        "    return str(text).replace(str(root), '<root>')\n"
    )
    planted_elsewhere = (
        "def redact(text):\n"
        "    return str(text)\n"
        "\n"
        "def resolve_account_dir(save_root):\n"
        "    return locate.resolve_save_root()\n"
    )
    planted_behind_a_helper = (
        "def redact(text):\n"
        "    return _pairs(str(text))\n"
        "\n"
        "def _pairs(out):\n"
        "    return _needles(out)\n"
        "\n"
        "def _needles(out):\n"
        "    return out.replace(str(locate.resolve_save_root()), '<root>')\n"
    )

    direct = _transitively_called_names(planted_directly, "redact") & set(RESOLVER_NAMES)
    assert direct == {"resolve_save_root"}, (
        f"the walker missed a resolver called straight from redact; it found {sorted(direct)}"
    )

    elsewhere = _transitively_called_names(planted_elsewhere, "redact") & set(RESOLVER_NAMES)
    assert not elsewhere, (
        "the walker flagged a resolver call that redact cannot reach, so it is really "
        f"just a search for the word: it found {sorted(elsewhere)}"
    )

    behind = _transitively_called_names(planted_behind_a_helper, "redact") & set(RESOLVER_NAMES)
    assert behind == {"resolve_save_root"}, (
        "the walker did not follow redact through two private helpers, so a one-line "
        f"wrapper would defeat it: it found {sorted(behind)}"
    )


# ===========================================================================
# b. No data-layer test depends on a real install
# ===========================================================================
#
# The load-bearing section. Everything above proves the SOURCE is
# install-independent; this proves the SUITE is, which is the clause CS-200
# actually states and the one nothing enforced before.


def _child_pytest_args() -> list[str]:
    """Build the argv for the child pytest run over the data-layer suite.

    The recursion guard is explicit and not incidental: without
    ``--ignore``, the child collects this module, which launches its own
    child, forever. It is expressed as an absolute path derived from
    ``__file__`` so renaming this file cannot leave the guard pointing at a
    path that no longer exists - which would look green right up to the
    moment the machine ran out of processes.

    ``-p no:cacheprovider`` keeps the child from writing a .pytest_cache
    that the parent run would then read.

    Returns:
        Arguments after the interpreter.
    """
    return [
        "-m",
        "pytest",
        str(DATA_TESTS),
        f"--ignore={THIS_MODULE}",
        "-p",
        "no:cacheprovider",
        "-q",
    ]


def test_the_data_layer_suite_passes_with_the_install_unresolvable() -> None:
    """The whole data-layer suite exits zero with the install forced unresolvable.

    This is the CS-200 middle clause, enforced. A test that reaches for the
    real shipped docs file, the real save root or the operator's
    config/local.json turns this red on the machine where the game IS
    installed - which is the only machine where the mistake is otherwise
    invisible, because there it passes.

    A test that genuinely needs an install is not forbidden; it must skip
    with a reason, and a skip keeps the exit code at zero.
    """
    child = run_child(_child_pytest_args(), no_install_env())
    exit_code = child.returncode
    assert exit_code == 0, (
        "the data-layer suite does not pass without a game install.\n"
        f"exit code: {exit_code}\n"
        f"stdout:\n{child.stdout}\n"
        f"stderr:\n{child.stderr}"
    )
    # Exit 0 with nothing collected is impossible (pytest exits 5), but the
    # count is asserted anyway rather than inferred: "the unrun gate is where
    # the bug hides" applies to this gate as much as to the ones it guards.
    passed = re.search(r"(\d+) passed", child.stdout)
    assert passed is not None, f"the child run reported no passing tests:\n{child.stdout}"
    assert int(passed.group(1)) > 0


def test_the_child_run_excludes_this_module_so_the_gate_cannot_recurse() -> None:
    """The recursion guard is verified against pytest's own collection, not assumed.

    ``--ignore`` silently accepts a path it does not match, so the guard
    working is a claim until pytest is asked what it collected. Both halves
    matter: this module absent, and the rest of the data suite present. A
    guard that excluded everything would also make the test above pass.
    """
    child = run_child([*_child_pytest_args(), "--collect-only"], no_install_env())
    exit_code = child.returncode
    assert exit_code == 0, f"collection failed:\n{child.stdout}\n{child.stderr}"

    collected = child.stdout
    assert THIS_MODULE.name not in collected, (
        f"{THIS_MODULE.name} is collected by its own child run, so the gate recurses"
    )
    for sibling in ("test_locate.py", "test_registry.py", "test_version.py"):
        assert sibling in collected, (
            f"the child run collects no {sibling}; the ignore is too wide and the gate "
            "would pass by testing nothing"
        )


# ===========================================================================
# c. Path literals specific to the data layer
# ===========================================================================
#
# WHAT tests/test_scaffold.py ALREADY COVERS, tree-wide, so none of it is
# repeated here: every authored file is 7-bit ASCII
# (test_authored_text_files_are_seven_bit_ascii), and no authored file holds
# an absolute path under a user home directory - a Windows user profile, a
# Linux /home or a macOS /Users path (test_no_absolute_home_paths_in_authored
# _files, with its own detector self-test).
#
# What it does NOT cover, and what this section adds for the data layer:
#   - a drive-letter absolute path that is NOT under a home directory. This
#     layer is the one that resolves the install, so a hardcoded install root
#     is the specific mistake available to it and to nothing else.
#   - an account-id-shaped digit run. The account directory name is a
#     platform account id and is personal data (BOOTSTRAP.md section 2.2).
#     Scaffold catches it only when it appears inside a home path.

# Assembled from fragments, exactly as scaffold does, so this file does not
# contain the literal it hunts and can never match its own pattern.
_DRIVE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")

# The floor is imported from the resolver rather than restated, so the scan
# and the thing it models cannot drift apart.
_ACCOUNT_ID_SHAPE = re.compile(
    r"(?<![0-9A-Za-z])[0-9]{" + str(MIN_ACCOUNT_ID_DIGITS) + r",}(?![0-9A-Za-z])"
)


def _strip_generated_pin(source: str) -> str:
    """Remove the machine-generated pin block from a module's source text.

    The pin is a census of the shipped docs file and legitimately carries
    measured counts long enough to look like an account id - a byte count in
    the tens of millions, for one. Those are numbers about a game file, not
    about a person.

    The exclusion is narrow on purpose. CONVENTIONS.md section 15.1 records
    that a guard can be green while self-excusing, so this drops only the
    lines strictly between the module's own two markers, and only in the file
    that has them. If a marker is ever renamed this strips nothing, the scan
    covers the whole file, and the test fails loudly - the safe direction.

    Args:
        source: Module source text.

    Returns:
        The source with the generated block removed.
    """
    kept: list[str] = []
    inside = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped == PIN_BEGIN_MARKER:
            inside = True
            continue
        if stripped == PIN_END_MARKER:
            inside = False
            continue
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def test_the_data_layer_path_detectors_actually_detect() -> None:
    """Both detectors match what they are for and leave the legitimate cases alone.

    An empty scan result is a claim about the PATTERN, not about the
    codebase (CONVENTIONS.md section 15.1). The negatives are the ones that
    matter here: this layer legitimately writes registry key paths, an
    environment-variable-relative save root, and version numbers, and a
    detector that flagged those would be turned off within a week.
    """
    sep = "\\"
    drive_positives = ("C:" + sep + "Game", "d:/Games/Steam", "E:" + sep)
    drive_negatives = (
        "HKLM:" + sep + "SOFTWARE",  # a registry drive prefix, not a filesystem path
        "%LOCALAPPDATA%" + sep + "Saved",
        "CommunityResources/Docs",
        "/Script/FactoryGame.FGRecipe",
        "https://example.invalid/x",
    )
    for sample in drive_positives:
        assert _DRIVE_PATH.search(sample) is not None, f"missed a drive path: {sample!r}"
    for sample in drive_negatives:
        assert _DRIVE_PATH.search(sample) is None, f"false positive on: {sample!r}"

    long_run = "1" * MIN_ACCOUNT_ID_DIGITS
    assert _ACCOUNT_ID_SHAPE.search("saves/" + long_run + "/world") is not None
    assert _ACCOUNT_ID_SHAPE.search("1" * (MIN_ACCOUNT_ID_DIGITS - 1)) is None
    assert _ACCOUNT_ID_SHAPE.search("v1.2.3") is None


@pytest.mark.parametrize("module", DATA_MODULES)
def test_no_data_layer_source_hardcodes_a_drive_letter_path(module: str) -> None:
    """No module in the data layer names an absolute drive-letter path.

    A hardcoded install root is wrong on every other machine including a
    clean CI checkout, and this is the one layer with a reason to reach for
    one. BOOTSTRAP.md section 12 item 3: detect it at runtime instead, which
    is what locate.py exists to do.
    """
    path = DATA_PACKAGE / f"{module}.py"
    violations = [
        f"{module}.py:{number}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _DRIVE_PATH.search(line) is not None
    ]
    assert not violations, (
        "absolute drive-letter paths in the data layer (auto-detect these at runtime "
        f"instead): {violations}"
    )


@pytest.mark.parametrize("module", DATA_MODULES)
def test_no_data_layer_source_carries_an_account_id_shaped_digit_run(module: str) -> None:
    """No module in the data layer holds a digit run long enough to be an account id.

    Only the line NUMBER is reported. A message quoting the run would print
    the personal data into CI logs and session transcripts, which is the harm
    the assertion exists to prevent (BOOTSTRAP.md section 2.2).
    """
    source = (DATA_PACKAGE / f"{module}.py").read_text(encoding="utf-8")
    scanned = _strip_generated_pin(source)
    if PIN_BEGIN_MARKER in source:
        assert len(scanned) < len(source), (
            f"{module}.py carries the pin markers but stripping removed nothing, so the "
            "exclusion has silently stopped matching"
        )

    violations = [
        f"{module}.py:{number}"
        for number, line in enumerate(scanned.splitlines(), start=1)
        if _ACCOUNT_ID_SHAPE.search(line) is not None
    ]
    assert not violations, (
        f"account-id-shaped digit runs in the data layer (content withheld): {violations}"
    )


# ===========================================================================
# d. The synthetic corpus is genuinely synthetic
# ===========================================================================

# A save, a usmap and a shipped locale file are the three publisher-owned or
# personal-data-bearing artifacts a fixture directory could plausibly acquire.
# tests/test_scaffold.py asserts .gitignore EXCLUDES *.sav; this asserts none
# has been placed under tests/ regardless, which is a different question - a
# path can be force-added, and .gitignore says nothing about .usmap or a
# locale file at all.
_FORBIDDEN_FIXTURE_SUFFIXES = frozenset({".sav", ".usmap"})
_LOCALE_FILE = re.compile(r"^[a-z]{2}-[A-Za-z]{2,4}\.json$")

# THE STATED BASIS OF THIS CEILING WAS FALSIFIED AND CS-898 CORRECTED IT TO WHAT
# THE NUMBER ACTUALLY PROMISES. The sentence that stood here said a ceiling well
# above the largest authored file and well below a real data slice separated the
# two "without ever tripping on ordinary test code". Ordinary test code tripped
# it: a repair took one module past this number and the module had to be split to
# land. The reading lives with the item note and is not restated here.
#
# WHAT IT PROMISES NOW, WHICH IS LESS AND IS TRUE: no file under tests/ exceeds
# this many bytes, whatever wrote it. That is enough for the move BOOTSTRAP.md
# section 8.1 fences off - a trimmed real docs file dropped in "just for tests",
# which no content assertion would catch because a real slice parses perfectly.
# It is NOT a claim that authored code stays clear of the ceiling on its own.
#
# SO AUTHORED CODE REACHING IT IS AN EXPECTED EVENT WITH A DESIGNED ANSWER rather
# than a sign the number is wrong: the approach band below reddens at 90 per cent
# while there is still room to act, and the repair is RELOCATION into a sibling
# module. Raising the ceiling to fit code launders a data-hygiene control for a
# code-size reason and is refused.
_MAX_TEST_FILE_BYTES = 256 * 1024


def _test_tree_files() -> list[Path]:
    """List real files under tests/, skipping bytecode caches.

    Returns:
        Sorted absolute paths.
    """
    return sorted(
        path for path in TESTS_ROOT.rglob("*") if path.is_file() and "__pycache__" not in path.parts
    )


def test_no_fixture_is_a_save_a_usmap_or_a_shipped_locale_file() -> None:
    """No artifact under tests/ is a save, a usmap or a shipped locale file.

    BOOTSTRAP.md section 12 items 11 and 12: a save file is personal-data
    bearing and is never placed in a fixture directory. The locale file and
    the usmap are publisher-owned content that must be read from the install
    at runtime and never committed (CONVENTIONS.md section 14).
    """
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in _test_tree_files()
        if path.suffix.lower() in _FORBIDDEN_FIXTURE_SUFFIXES or _LOCALE_FILE.match(path.name)
    ]
    assert not offenders, f"publisher-owned or personal-data artifacts under tests/: {offenders}"


def _oversized_over_the_ceiling(paths: Iterable[Path], root: Path) -> list[str]:
    """Every path past the size ceiling, one report line each.

    Factored out of the arm below by CS-898 so the predicate can be run over
    material an arm PLANTS rather than only over the real tree. An oversize
    file written into ``tests/`` to prove the ceiling works would redden the
    arm below in the same run, so planting needs a root that is not this
    repository.

    Args:
        paths: Files to measure.
        root: Directory the report lines are rendered relative to.

    Returns:
        One ``<path> (<size> bytes)`` line per file over the ceiling, in the
        order the paths were given. Empty when none is over it.
    """
    return [
        f"{path.relative_to(root).as_posix()} ({path.stat().st_size} bytes)"
        for path in paths
        if path.stat().st_size > _MAX_TEST_FILE_BYTES
    ]


def test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data() -> None:
    """No file under tests/ is large enough to hide a slice of real game data.

    A size ceiling is crude and that is the point: it is the one check that
    catches a trimmed real docs file dropped in "just for tests", which is
    the specific move BOOTSTRAP.md section 8.1 fences off and which no
    content assertion would catch because a real slice parses perfectly.

    IT DOES NOT CLASSIFY WHAT WROTE A FILE, and CS-898 corrected the comment
    over ``_MAX_TEST_FILE_BYTES`` that said it did. A large hand-authored
    module reddens this arm exactly as an extracted slice would; the approach
    band is what gives authored code somewhere to land before that happens.
    """
    oversized = _oversized_over_the_ceiling(_test_tree_files(), REPO_ROOT)
    assert not oversized, (
        f"files under tests/ exceed {_MAX_TEST_FILE_BYTES} bytes, which is too large to be "
        f"hand-authored synthetic material: {oversized}"
    )


def test_the_size_ceiling_still_catches_a_planted_oversize_non_authored_artifact(
    tmp_path: Path,
) -> None:
    """A planted oversize artifact is caught, and an under-ceiling sibling is not.

    CS-898. The comment above ``_MAX_TEST_FILE_BYTES`` used to claim the number
    separated hand-authored modules from a slice of real game data "without ever
    tripping on ordinary test code", and ordinary test code tripped it. Correcting
    that claim is a prose edit, and a prose edit is exactly the change that can
    quietly take the guard with it - so this arm grades the PREDICATE rather than
    the sentence, over material it plants itself.

    IT IS PLANTED OUTSIDE ``tests/`` ON PURPOSE. An oversize file written into the
    real tree would redden
    ``test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data``
    in the same run, so the arm would be proving its point by breaking its
    neighbour. The predicate takes its root, which is what makes planting
    possible at all.

    THE UNDER-CEILING CONTROL IS THE ANTI-VACUITY LEG. A predicate that returned
    every path it was handed would satisfy a bare non-empty assertion and fail
    this one, so the pair says the ceiling DISCRIMINATES rather than merely
    complains.
    """
    planted = tmp_path / "FactoryGame.json"
    planted.write_bytes(b'{"NativeClass":"' + b"A" * (_MAX_TEST_FILE_BYTES + 1) + b'"}')
    control = tmp_path / "synthetic_registry.json"
    control.write_bytes(b'{"NativeClass":"' + b"A" * 16 + b'"}')

    caught = _oversized_over_the_ceiling([planted, control], tmp_path)

    assert caught == [f"FactoryGame.json ({planted.stat().st_size} bytes)"], caught


def _write_a_file_of_exactly(path: Path, size: int) -> Path:
    """Write a plausible-looking JSON artifact measuring exactly ``size`` bytes.

    The caller passes a size DERIVED from ``_MAX_TEST_FILE_BYTES`` rather than
    spelled, which is the whole point of the boundary arm below: a spelled
    262144 would keep agreeing with itself if the constant were respelled, and
    the ceiling would have moved out from under the proof.

    NO GUARD CLAUSE, ON PURPOSE. A ``size`` smaller than the wrapper makes the
    filler count negative, ``b"A" * -1`` is empty, and the file then measures
    the wrapper rather than what was asked for - which the caller's own
    measurement leg reddens on. A raise here would be a second failure channel
    for a condition the arm already grades.

    Args:
        path: File to write. Any parent must already exist.
        size: Exact byte count the written file is meant to measure.

    Returns:
        ``path``, so a caller can bind and measure in one line.
    """
    prefix = b'{"NativeClass":"'
    suffix = b'"}'
    path.write_bytes(prefix + b"A" * (size - len(prefix) - len(suffix)) + suffix)
    return path


def test_the_size_ceiling_admits_its_own_byte_and_refuses_the_one_above_it(
    tmp_path: Path,
) -> None:
    """The ceiling sits exactly where ``_MAX_TEST_FILE_BYTES`` says it sits.

    CS-1123, and the arm above is WHY it was needed rather than a duplicate of
    it. That arm plants a file 19 bytes past the ceiling against a 34-byte
    control, so it proves the predicate DISCRIMINATES over a gap of a quarter
    of a megabyte and says nothing about where inside that gap the line falls.
    The CS-898 verifier measured the consequence: planting ``>=`` for ``>`` left
    it GREEN while three other mutants of the same comparison reddened, so the
    boundary itself was unguarded.

    THREE SIZES, EACH DERIVED FROM THE CONSTANT, CATCH THE OFF-BY-ONE IN EITHER
    DIRECTION. A file OF exactly the ceiling is admitted, the byte above it is
    refused, and the byte below it is admitted. Shifting the comparison down by
    one - ``>=`` - catches the exact-ceiling file and reddens the expectation;
    shifting it up by one - ``> _MAX_TEST_FILE_BYTES + 1`` - stops catching the
    over-by-one file and reddens it too.

    THE TWO ADMITTED FILES ARE THE ANTI-VACUITY LEG AT THE SAME SIZES. A
    predicate that reported every path it was handed would satisfy a bare
    non-empty assertion and fail this one, and it would fail it at the boundary
    rather than a quarter of a megabyte away from it.

    IT PLANTS OUTSIDE ``tests/`` for the reason the arm above states: a file at
    or over the ceiling inside the real tree would redden
    ``test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data``
    in the same run.
    """
    under = _write_a_file_of_exactly(tmp_path / "under_by_one.json", _MAX_TEST_FILE_BYTES - 1)
    at = _write_a_file_of_exactly(tmp_path / "at_the_ceiling.json", _MAX_TEST_FILE_BYTES)
    over = _write_a_file_of_exactly(tmp_path / "over_by_one.json", _MAX_TEST_FILE_BYTES + 1)

    measured = [path.stat().st_size for path in (under, at, over)]
    expected_sizes = [
        _MAX_TEST_FILE_BYTES - 1,
        _MAX_TEST_FILE_BYTES,
        _MAX_TEST_FILE_BYTES + 1,
    ]
    assert measured == expected_sizes, measured

    caught = _oversized_over_the_ceiling([under, at, over], tmp_path)
    expected_caught = [f"over_by_one.json ({_MAX_TEST_FILE_BYTES + 1} bytes)"]

    assert caught == expected_caught, caught


#: The APPROACH band for the tests-tree size ceiling, as a fraction of that
#: ceiling. A plain FLOAT LITERAL, and never a fraction of whatever the largest
#: file currently measures - a bound computed from the thing it bounds is the
#: tautology `tests/test_doc_budget.py` records this project filing twice.
_TEST_FILE_APPROACH = 0.90

#: THE BASELINE RESIDUAL: repo-relative path -> the item id that retires the row.
#: NOT an exemption list. Each row is a filed piece of work, and the arm below
#: pins the table in BOTH directions, so relocating a file FORCES the row out
#: and the ceiling down in the same change.
_TEST_FILE_BAND_RESIDUAL: dict[str, str] = {
    "tests/save/test_struct_interior.py": "CS-1089",
    "tests/save/test_properties.py": "CS-1090",
    "tests/save/test_world.py": "CS-1091",
}

#: THE RATCHET. The number of rows the residual may hold, SPELLED as an integer
#: and never `len(_TEST_FILE_BAND_RESIDUAL)` - a budget computed from the table
#: it budgets forgives every append in advance, which is the same tautology the
#: band fraction above refuses. It only ever comes DOWN.
#:
#: 4 TO 3, 2026-09-15 BY CS-1066, AND IT IS THE RATCHET WORKING RATHER THAN A
#: NUMBER BEING TYPED. `tests/test_docs_citations.py` was the row this table was
#: filed with at 100.0 per cent of the ceiling; that item RELOCATED its
#: disposition and pin tables, their budgets and the contracts that spend them
#: into `tests/test_citation_tables.py`, and the file now measures well under the
#: approach band. The row goes with the repair and the ceiling goes with the row:
#: leaving either behind is the banked room the STALE and RATCHET legs above
#: exist to refuse, and they redden on doing exactly one of the two.
_TEST_FILE_BAND_RESIDUAL_CEILING = 3


def _approach_band_problems() -> list[str]:
    """Every way the tests-tree approach band has drifted, one line each.

    Four directions, because a one-way check is an exemption list wearing a
    ratchet's clothes:

    * a file past the band with NO row is an UNBUDGETED regression;
    * a row naming a file back UNDER the band is STALE, so repairing a file
      forces the row out and the ceiling down rather than leaving slack behind;
    * a row naming a file that does not exist is a MISSING pin, which is how a
      rename launders a row into permanent cover;
    * a row count that is not the spelled ceiling is the RATCHET, over it or
      under it.

    Returns:
        One line per drifted direction. Empty when the tree is clean.
    """
    band = int(_MAX_TEST_FILE_BYTES * _TEST_FILE_APPROACH)
    measured = {
        path.relative_to(REPO_ROOT).as_posix(): path.stat().st_size for path in _test_tree_files()
    }
    problems: list[str] = []

    for name, size in sorted(measured.items()):
        if size > band and name not in _TEST_FILE_BAND_RESIDUAL:
            problems.append(
                f"UNBUDGETED: {name} is {size} bytes, "
                f"{100 * size / _MAX_TEST_FILE_BYTES:.1f} per cent of the "
                f"{_MAX_TEST_FILE_BYTES}-byte ceiling and past the {band}-byte approach "
                "band. RELOCATE a block of arms into a sibling module under tests/. Do "
                "NOT delete an arm and do NOT raise the ceiling."
            )

    for name, item in sorted(_TEST_FILE_BAND_RESIDUAL.items()):
        if name not in measured:
            problems.append(
                f"MISSING: the residual row {name} -> {item} names a file that is not in "
                "the tree. A renamed or deleted file leaves its row standing as cover for "
                "whatever takes the name next. Repoint the row or drop it and lower the "
                "ceiling in the same change."
            )
        elif measured[name] <= band:
            problems.append(
                f"STALE: the residual row {name} -> {item} names a file that now measures "
                f"{measured[name]} bytes, back under the {band}-byte band. Drop the row "
                "and lower the ceiling by one in the same change - a repair that leaves "
                "its row behind is banked room for the next regression."
            )

    recorded = len(_TEST_FILE_BAND_RESIDUAL)
    if recorded > _TEST_FILE_BAND_RESIDUAL_CEILING:
        problems.append(
            f"RATCHET: {recorded} residual rows against a ceiling of "
            f"{_TEST_FILE_BAND_RESIDUAL_CEILING}. A row was added. That is a finding to "
            "argue, not a line to type: RELOCATE a block of arms into a sibling module "
            "under tests/, or raise the ceiling in this same change and file the item. Do "
            "NOT delete an arm and do NOT raise the size ceiling."
        )
    elif recorded < _TEST_FILE_BAND_RESIDUAL_CEILING:
        problems.append(
            f"RATCHET: {recorded} residual rows against a ceiling of "
            f"{_TEST_FILE_BAND_RESIDUAL_CEILING}. A file was repaired and the ceiling was "
            f"not lowered to match. Lower it to {recorded} - a slack ceiling is banked "
            "room for an append nobody will have to defend."
        )

    return problems


def test_every_file_under_tests_near_the_size_ceiling_is_budgeted_and_pinned() -> None:
    """The size ceiling is caught on APPROACH, and every forgiveness is a filed item.

    WHY AN ARM AND NOT JUST THE CEILING.
    ``test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data``
    reddens the moment a file passes 256 KB, and at that moment the session that
    tripped it cannot add the arm it came to add without first doing unrelated
    surgery under time pressure - which is how a gate gets bent instead of a
    file getting split. This one reddens while there is still room to act.

    THE REPAIR IS RELOCATION, NEVER DELETION, and never raising the ceiling.
    ``_MAX_TEST_FILE_BYTES`` argues its own number where it is defined, and
    CS-898 corrected what that argument claims: the ceiling BOUNDS every file
    under ``tests/`` rather than separating authored material from extracted
    material, so moving it moves a data-hygiene bound and nothing else. Split a
    block of arms into a sibling module under ``tests/`` and let it import the
    fixtures it needs.

    THE RESIDUAL IS NOT AN EXEMPTION LIST. Each row names the item that retires
    it, the table is pinned in both directions, and the count is ratcheted, so
    the only cheap move left - appending a row - shows up in the diff as a
    number somebody has to defend.
    """
    problems = _approach_band_problems()
    report = "\n  ".join(problems)
    drifted = bool(problems)
    assert not drifted, (
        f"the tests-tree approach band at {100 * _TEST_FILE_APPROACH:.0f} per cent of "
        f"{_MAX_TEST_FILE_BYTES} bytes has drifted:\n  {report}"
    )


def test_the_tests_tree_approach_band_sits_below_the_ceiling_it_guards() -> None:
    """The band is only a warning if it is strictly inside the thing it guards.

    A band equal to the ceiling reddens at the same moment the ceiling does and
    buys nothing, which is the whole defect this pair exists to close. Asserted
    rather than assumed, because the fraction is a literal somebody can edit -
    and the second leg keeps holding if ``_MAX_TEST_FILE_BYTES`` is respelled,
    since it reads the constant rather than restating ``256 * 1024``.
    """
    assert 0 < _TEST_FILE_APPROACH < 1, _TEST_FILE_APPROACH
    assert int(_MAX_TEST_FILE_BYTES * _TEST_FILE_APPROACH) < _MAX_TEST_FILE_BYTES


def test_the_synthetic_corpus_names_no_install_path_and_no_account_id() -> None:
    """The corpus holds no install path, no account id and no pointer at the shipped file.

    The 7-bit ASCII half of "genuinely synthetic" is already asserted
    tree-wide by tests/test_scaffold.py and is not repeated. What is specific
    to the corpus is that it must be authored material rather than something
    read off a real install: no drive-letter path, no account-id-shaped digit
    run, and no reference to the shipped docs file's own relative path, which
    is imported from the version pin rather than restated here.
    """
    text = SYNTHETIC_CORPUS.read_text(encoding="utf-8")

    drive_hits = [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if _DRIVE_PATH.search(line) is not None
    ]
    account_hits = [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if _ACCOUNT_ID_SHAPE.search(line) is not None
    ]

    assert not drive_hits, f"the synthetic corpus names an absolute path at lines {drive_hits}"
    assert not account_hits, (
        f"the synthetic corpus holds an account-id-shaped digit run at lines {account_hits} "
        "(content withheld)"
    )
    assert DOCS_RELATIVE not in text, (
        "the synthetic corpus references the shipped docs file's own path, so it is "
        "pointing at real game data rather than standing in for it"
    )


# ===========================================================================
# e. The data-layer seams are importable in isolation
# ===========================================================================
#
# docs/ARCHITECTURE.md section 3.1 states that layering reduces to an
# allowed-import matrix and that walking the import graph makes it
# mechanically checkable. This is that check for the data layer, measured
# against sys.modules in a fresh interpreter rather than read out of source
# text: an import that only fires under a conditional, or one reached
# indirectly through a third module, is invisible to a source scan and
# perfectly visible here.

# module -> the clockspeed.data submodules importing it is allowed to pull in.
# Read as a contract, not as a description: the FORBIDDEN half is asserted
# because that is the layering claim, and the REQUIRED half is asserted too
# because a negative assertion rules out without pinning down
# (CONVENTIONS.md section 7.2) - it would pass just as happily for a module
# that had collapsed to importing nothing at all.
ALLOWED_IMPORTS: dict[str, frozenset[str]] = {
    # assets reaches locate and NOTHING else: reading the shipped archive must not
    # depend on the registry, on the build pin, or on the blob grammar.
    "assets": frozenset({"locate"}),
    "blobs": frozenset(),
    "docs_extract": frozenset(),
    "locate": frozenset(),
    "registry": frozenset({"blobs", "docs_extract"}),
    # schematics is the registry's SIBLING (CS-1043): it reads the same loaded
    # document through the same two neighbours and never reaches the registry.
    "schematics": frozenset({"blobs", "docs_extract"}),
    "version": frozenset({"docs_extract"}),
}


def _imported_submodules(module: str) -> set[str]:
    """Report which clockspeed.data submodules importing ``module`` pulled in.

    Args:
        module: Short module name under ``clockspeed.data``.

    Returns:
        Short names of the sibling submodules present in the child's
        sys.modules, excluding the module itself.
    """
    probe = import_probe(module)
    exit_code = probe.returncode
    assert exit_code == 0, f"the import probe for {module} failed:\n{probe.stderr}"
    loaded: list[str] = json.loads(probe.stdout.strip().splitlines()[-1])
    prefix = "clockspeed.data."
    return {
        name.removeprefix(prefix)
        for name in loaded
        if name.startswith(prefix) and name.removeprefix(prefix) != module
    }


@pytest.mark.parametrize("module", DATA_MODULES)
def test_importing_a_data_module_pulls_in_only_its_permitted_neighbours(module: str) -> None:
    """Each data-layer module imports its permitted set and nothing above it.

    The three claims that matter, all of them measured here: blobs imports
    nothing from clockspeed at all, so the blob grammar can be reasoned about
    on its own; docs_extract reaches for neither locate nor registry, so
    reading the shipped document is independent of finding it and of
    normalizing it; and registry imports neither locate nor version, so
    building the registry cannot depend on where the install is or on which
    build it came from.
    """
    permitted = ALLOWED_IMPORTS[module]
    imported = _imported_submodules(module)

    forbidden = sorted(imported - permitted)
    assert not forbidden, (
        f"importing clockspeed.data.{module} also loaded {forbidden}, which is outside its "
        f"permitted set {sorted(permitted)} - a layer reaching past its neighbour"
    )

    missing = sorted(permitted - imported)
    assert not missing, (
        f"clockspeed.data.{module} no longer imports {missing}; the allowed-import matrix "
        "is the contract and must be changed deliberately, not left describing the past"
    )


def test_blobs_imports_nothing_from_clockspeed_beyond_its_own_package_shell() -> None:
    """Importing the blob grammar drags in no clockspeed module other than the packages.

    Asserted on the full clockspeed namespace rather than on the data package
    alone, because "blobs imports nothing from clockspeed" is the actual
    claim - an import of clockspeed.solve would satisfy the per-package check
    above and still be a seam violation.
    """
    probe = import_probe("blobs")
    exit_code = probe.returncode
    assert exit_code == 0, probe.stderr
    loaded = set(json.loads(probe.stdout.strip().splitlines()[-1]))
    assert loaded == {"clockspeed", "clockspeed.data", "clockspeed.data.blobs"}, (
        f"importing clockspeed.data.blobs loaded {sorted(loaded)}; it is the bottom of the "
        "layer and must depend on nothing inside the project"
    )
