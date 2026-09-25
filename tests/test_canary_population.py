"""CS-1177 - a canary held by a helper frame that RAISES, and a population nobody types.

THE DEFECT, TWO HALVES. CS-1175 measured its echo repair on ASSERTION failures
in the canary suites. An exception raised INSIDE a helper frame is rendered all
the same: under ``--showlocals`` pytest prints the locals of every frame in
the traceback, and the arguments of its first and last, so a helper that holds
a canary as a named local or an argument prints it. And the suites that
arm forced red were a hand-kept tuple, so a new canary-bearing module was
ungraded until somebody remembered to add it.

THE MEMBERSHIP RULE, STATED ONCE. A canary suite is a ``test_*.py`` module
under ``tests/`` whose CODE reads either canary table of
``tools/outbound_gate.py`` - an attribute access, a bare name or an import of
``CREDENTIAL_CANARIES`` or ``CREDENTIAL_BRANCH_CANARIES`` - itself or through
any chain of modules under ``tests/`` that it imports. A mention in a string
or a comment is not a read. The population is derived from source by
:func:`canary_suites` and is never typed; ``CANARY_SUITES`` in
``tests/test_cs1175_rule_narrowing.py`` is that derivation, not a list.

HOW A HELPER IS FORCED TO RAISE. :data:`HELPER_FORCER` is a plugin for a child
run. During each test's CALL phase it traces every frame whose code lives in a
member module and is not a test function, and selects the frames that hold a
canary: those whose code, or a code nested in it, reads a canary table by name,
and those whose locals hold a canary on entry - a plain function's arguments,
or a generator's locals each time it resumes. A selected frame raises
``ForcedHelperRaise`` at its first return or yield; for a plain function that
is after every local it binds is bound, the moment of greatest exposure. The
tracer's own frame is hidden, so the traceback ends in the helper and pytest
renders that helper's arguments and locals. HYGIENE is the helper holding no canary as a named local
or an argument when it raises; a value that only ever lives on the evaluation
stack cannot be rendered.

WHAT THIS DOES NOT GRADE, SAID RATHER THAN IMPLIED. A frame in a module outside
the population - the gates themselves - is not forced, and a helper that is
never called by a selected test in the forced run is never exercised. The
arms that spawn a forced run of their own are deselected in the child by the
``forced_red_output`` substring, as CS-1172 and CS-1175 already do, so a child
never recurses - and a member whose holding helpers are reached ONLY by such
arms is run but never forced. The arm grades that every member RAN, and that
the population as a whole was forced; it does not claim each member was.

EVERY VERDICT IS A COUNT. The child's output is held only by the helpers that
run and count it, and nothing but scalars reaches a test frame.
"""

from __future__ import annotations

import ast
import functools
import importlib.util
import operator
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from itertools import chain
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
OUTBOUND_PATH = REPO_ROOT / "tools" / "outbound_gate.py"

#: Private to this file, so no other suite's patches can reach this copy.
OUTBOUND_MODULE_NAME = "clockspeed_outbound_gate_for_cs1177"

#: The names whose READ makes a module a member.
CANARY_TABLES = frozenset({"CREDENTIAL_CANARIES", "CREDENTIAL_BRANCH_CANARIES"})

TIMEOUT = 300

#: The child plugin's module name, and the exception it raises.
FORCER_NAME = "cs1177_helper_forcer"
FORCED = "ForcedHelperRaise"

#: The one keyword that deselects, in a child, every arm that spawns a forced
#: run of its own. Every such arm in this file carries it in its name.
NO_RECURSION = "not forced_red_output"


def load_outbound() -> ModuleType:
    """Load the outbound gate by path under a module name private to this file."""
    cached = sys.modules.get(OUTBOUND_MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(OUTBOUND_MODULE_NAME, OUTBOUND_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[OUTBOUND_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


OUTBOUND = load_outbound()


# --------------------------------------------------------------------------
# The population - derived from source, never typed
# --------------------------------------------------------------------------


def gate_readers(gate_source: str) -> frozenset[str]:
    """The gate's functions that reach a canary table, derived from its source.

    A function whose own code names a table, and every PRIVATE function that
    calls one, closed over call chains. The gate's public entry points that
    reach a table only through those - ``scan`` and ``main`` - are left out on
    purpose: every outbound suite calls them, and a suite that loads the gate
    at all is admitted by the fail-closed rule in :func:`canary_suites` instead.
    """
    functions = {
        node.name: node for node in ast.parse(gate_source).body if isinstance(node, ast.FunctionDef)
    }

    def names(node: ast.AST) -> set[str]:
        return {found.id for found in ast.walk(node) if isinstance(found, ast.Name)}

    readers = {name for name, node in functions.items() if names(node) & CANARY_TABLES}
    grown = True
    while grown:
        added = {
            name
            for name, node in functions.items()
            if name not in readers and name.startswith("_") and names(node) & readers
        }
        readers |= added
        grown = bool(added)
    return frozenset(readers)


#: Derived once, from the gate this tree ships.
GATE_READERS = gate_readers(OUTBOUND_PATH.read_text(encoding="utf-8"))


#: The kinds of node whose first statement, when a string, is a docstring.
_SCOPES = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


class Facts(NamedTuple):
    """What one module's code shows, gathered in ONE walk of its tree - CS-1193.

    The derivation used to walk every tree once per question - reads, strings,
    docstrings, loader calls, imports, parameters - over the whole of
    ``tests/``, and that was most of its cost. Every question is answered by
    the single walk in :func:`facts`; the rule each field serves is stated on
    the function that consumes it.
    """

    #: A table read by attribute, bare name or import, or a gate reader by attribute.
    reads_by_name: bool
    #: Every string constant in the module's CODE - docstrings excluded.
    strings: tuple[str, ...]
    #: Every dotted name an import or a ``pytest_plugins`` entry names.
    imports: frozenset[str]
    #: Whether the module calls a file loader in :data:`LOADERS`.
    loads: bool
    #: Every parameter name any function in the module takes.
    parameters: frozenset[str]


def _loaded_names(node: ast.Import | ast.ImportFrom | ast.Assign, package: str) -> set[str]:
    """The dotted names one import statement or ``pytest_plugins`` binding names."""
    if isinstance(node, ast.Import):
        return {alias.name for alias in node.names}
    if isinstance(node, ast.ImportFrom):
        base = package
        for _ in range(max(node.level - 1, 0)):
            base = base.rpartition(".")[0]
        if node.level == 0:
            base = node.module or ""
        elif node.module:
            base = base + "." + node.module if base else node.module
        return {base} | {base + "." + alias.name for alias in node.names}
    if any(
        isinstance(target, ast.Name) and target.id == "pytest_plugins" for target in node.targets
    ):
        return {
            item.value
            for item in ast.walk(node.value)
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }
    return set()


def facts(tree: ast.AST, name: str = "", is_package: bool = False) -> Facts:
    """Walk `tree` once and gather every fact the membership rule reads.

    `name` and `is_package` place the module for a RELATIVE import:
    ``from x import y`` yields both ``x`` and ``x.y``, because ``y`` may be a
    submodule; a name that is not a module simply matches nothing. A
    ``pytest_plugins`` entry is an import by another spelling. Prose is never
    code: a docstring's constant is left out of :attr:`Facts.strings`.
    """
    package = name if is_package else name.rpartition(".")[0]
    attributes = CANARY_TABLES | GATE_READERS
    prose: set[int] = set()
    constants: list[tuple[int, str]] = []
    reads = False
    loads = False
    found: set[str] = set()
    parameters: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                constants.append((id(node), node.value))
        elif isinstance(node, ast.Name):
            reads = reads or node.id in CANARY_TABLES
        elif isinstance(node, ast.Attribute):
            reads = reads or node.attr in attributes
        elif isinstance(node, ast.alias):
            reads = reads or node.name in CANARY_TABLES
        elif isinstance(node, ast.Call):
            func = node.func
            called = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            loads = loads or called in LOADERS
        elif isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign)):
            found |= _loaded_names(node, package)
        if isinstance(node, _SCOPES):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                prose.add(id(body[0].value))
            if isinstance(node, _FUNCTIONS):
                parameters.update(arg.arg for arg in node.args.args + node.args.kwonlyargs)
    strings = tuple(value for key, value in constants if key not in prose)
    return Facts(reads, strings, frozenset(found), loads, frozenset(parameters))


def reads_a_canary_table(source: str) -> bool:
    """True when `source`'s CODE reads either canary table - never its prose."""
    return _reads(facts(ast.parse(source)))


def _reads(found: Facts) -> bool:
    """True when the module's code reads a table or a gate reader, or loads the gate.

    A table by attribute, bare name or import; a gate reader by attribute, as
    the suites reach it - ``OUTBOUND._canary(...)``. And FAIL CLOSED: a module
    that loads the gate by path may read a table in a way no syntax shows, so
    naming the gate's file in code is itself a read.
    """
    if found.reads_by_name:
        return True
    gate = OUTBOUND_PATH.name
    return any(
        value == gate or value.replace("\\", "/").endswith("/" + gate) for value in found.strings
    )


def _module_name(path: Path, root: Path) -> tuple[str, bool]:
    """The dotted name `path` imports as under `root`, and whether it is a package."""
    parts = path.relative_to(root).with_suffix("").parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


#: Calls that load a module from a file path. A module calling one of these
#: under another name loads nothing this derivation can see - declared in
#: :func:`canary_suites`.
LOADERS = frozenset({"spec_from_file_location", "run_path", "SourceFileLoader"})


def _imported(found: Facts, by_path: dict[str, str]) -> set[str]:
    """Every dotted name the module could load: imports, plugins and path loads.

    A module that calls a loader in :data:`LOADERS` loads every ``.py`` file
    under the tree its code names - the path may be built anywhere in the
    module and handed over by a name. A module that names a file but calls no
    loader - a table of citations - loads nothing, which is what keeps prose
    about a file from joining it to every module that mentions it.
    """
    loaded = set(found.imports)
    if not found.loads:
        return loaded
    for value in found.strings:
        spelled = value.replace("\\", "/").removeprefix("./")
        if not spelled.endswith(".py"):
            continue
        # Whole path components only: ``conftest.py`` names every conftest, and
        # a bare suffix match would join every module to every other.
        loaded.update(
            module
            for suffix, module in by_path.items()
            if suffix == spelled or suffix.endswith("/" + spelled)
        )
    return loaded


def _fixtures(tree: ast.AST) -> set[str]:
    """The names of the fixtures a module defines."""
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any("fixture" in ast.unparse(decorator) for decorator in node.decorator_list)
    }


def canary_suites(tests_dir: Path) -> list[Path]:
    """Every ``test_*.py`` under `tests_dir` that reads a canary table, sorted.

    READS TRANSITIVELY - CS-1177, from two adversary passes. Every module under
    `tests_dir` is parsed once and walked once (:func:`facts`). A module is a
    READER when its own code reads a table, calls a gate reader by attribute,
    or names the gate's file (fail closed, see :func:`_reads`); or when it
    loads a reader - by import, by ``pytest_plugins`` or by a path string; or,
    for a test module, when it takes a fixture a reader ``conftest.py`` above
    it defines. Closed over chains of any length. Members are the readers that
    are test modules.

    WHAT NO SYNTAX HERE CAN SEE, declared rather than implied: a table reached
    through ``getattr`` with a computed name on a gate imported under a name
    other than its file's, which neither reads a table by name nor names the
    gate's file; a fixture supplied by a plugin rather than a conftest; and a
    module loaded from a path by a loader outside :data:`LOADERS`.
    """
    root = tests_dir.parent
    trees: dict[str, tuple[Path, ast.Module, Facts]] = {}
    for path in sorted(tests_dir.rglob("*.py")):
        name, is_package = _module_name(path, root)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        trees[name] = (path, tree, facts(tree, name, is_package))
    by_path = {path.relative_to(root).as_posix(): name for name, (path, _, _) in trees.items()}
    reaches = {name: _imported(found, by_path) for name, (_, _, found) in trees.items()}
    readers = {name for name, (_, _, found) in trees.items() if _reads(found)}
    defined: dict[str, set[str]] = {}
    grown = True
    while grown:
        added = {name for name in trees if name not in readers and reaches[name] & readers}
        for conftest in readers:
            path, tree, _ = trees[conftest]
            if path.name != "conftest.py":
                continue
            if conftest not in defined:
                defined[conftest] = _fixtures(tree)
            fixtures = defined[conftest]
            added |= {
                name
                for name, (other, _, found) in trees.items()
                if name not in readers
                and other.is_relative_to(path.parent)
                and found.parameters & fixtures
            }
        readers |= added
        grown = bool(added)
    return sorted(
        path
        for name, (path, _, _) in trees.items()
        if name in readers and path.name.startswith("test_")
    )


@functools.cache
def derived_canary_suites() -> tuple[str, ...]:
    """This tree's canary suites as repo-relative POSIX paths - the child's arguments.

    DERIVED ONCE PER PROCESS - CS-1193. The tree cannot change under one run,
    and every caller in a process - the import of the CS-1175 suite, the
    ``pristine`` fixture, the floor arm - read the same answer at several
    seconds a call. A temporary tree is never cached: :func:`canary_suites` is
    called on it directly.
    """
    return tuple(path.relative_to(REPO_ROOT).as_posix() for path in canary_suites(TESTS_DIR))


# --------------------------------------------------------------------------
# The forced run
# --------------------------------------------------------------------------

#: The child plugin. Formatted with the outbound gate's path and the member
#: modules' real paths. Its canary values live in a module global of the
#: plugin, which no traceback in the child ever reaches.
HELPER_FORCER = '''
import functools
import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest

OUTBOUND = Path(%r)
SUITES = frozenset(os.path.normcase(os.path.realpath(path)) for path in %r)
GATE = os.path.normcase(os.path.realpath(OUTBOUND))
TABLES = frozenset({"CREDENTIAL_CANARIES", "CREDENTIAL_BRANCH_CANARIES"})
VALUES = []


class ForcedHelperRaise(RuntimeError):
    """Raised inside a canary suite's helper frame, at its return."""


def pytest_configure(config):
    spec = importlib.util.spec_from_file_location("cs1177_forcer_outbound", OUTBOUND)
    module = importlib.util.module_from_spec(spec)
    sys.modules["cs1177_forcer_outbound"] = module
    spec.loader.exec_module(module)
    VALUES.extend(module.CREDENTIAL_CANARIES.values())
    for table in module.CREDENTIAL_BRANCH_CANARIES.values():
        VALUES.extend(table.values())


@functools.lru_cache(maxsize=None)
def in_the_gate(filename):
    return os.path.normcase(os.path.realpath(filename)) == GATE


@functools.lru_cache(maxsize=None)
def in_a_suite(filename):
    return os.path.normcase(os.path.realpath(filename)) in SUITES


def names(code):
    found = set(code.co_names)
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            found |= names(const)
    return found


def holds(value):
    if isinstance(value, str):
        return any(canary in value for canary in VALUES)
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(holds(item) for item in value)
    if isinstance(value, dict):
        return any(holds(item) for item in value.values())
    return False


def raise_at_return(frame, event, arg):
    __tracebackhide__ = True
    if event == "return":
        raise ForcedHelperRaise("forced inside a canary suite helper")
    return raise_at_return


def select(frame, event, arg):
    code = frame.f_code
    if event != "call" or code.co_name.startswith("test_") or code.co_name == "<module>":
        return None
    if not in_a_suite(code.co_filename):
        return None
    if in_the_gate(code.co_filename):
        caller = frame.f_back
        called_by_a_member = caller is not None and not in_the_gate(caller.f_code.co_filename)
        if TABLES & names(code) and called_by_a_member and in_a_suite(caller.f_code.co_filename):
            return raise_at_return
        return None
    if TABLES & names(code):
        return raise_at_return
    if any(holds(value) for value in frame.f_locals.values()):
        return raise_at_return
    return None


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    sys.settrace(select)
    try:
        return (yield)
    finally:
        sys.settrace(None)
'''


class Verdict(NamedTuple):
    """What one forced run showed - counts only, never a value."""

    code: int
    leaked: int
    graded: dict[str, int]
    forced: dict[str, int]


def canaries_in(output: str) -> int:
    """How many canary values, from either table, appear in `output`.

    No canary value and no table is ever bound to a name of this frame; the
    values are mapped over on the stack. `output` itself carries a canary only
    when a leak is what is being counted.
    """
    return sum(
        map(
            output.count,
            chain(
                OUTBOUND.CREDENTIAL_CANARIES.values(),
                chain.from_iterable(
                    map(
                        operator.methodcaller("values"),
                        OUTBOUND.CREDENTIAL_BRANCH_CANARIES.values(),
                    )
                ),
            ),
        )
    )


def _verdict(code: int, output: str, suites: tuple[str, ...]) -> Verdict:
    """Count, per member, the tests that ran and the failures a forced raise caused."""
    lines = output.splitlines()
    graded = {
        suite: sum(
            1
            for line in lines
            if line.startswith(suite + "::") and re.search(r" (PASSED|FAILED|ERROR)\b", line)
        )
        for suite in suites
    }
    forced = {
        suite: sum(
            1 for line in lines if line.startswith("FAILED " + suite + "::") and FORCED in line
        )
        for suite in suites
    }
    return Verdict(code, canaries_in(output), graded, forced)


def forced_run(
    workdir: Path, root: Path, suites: tuple[str, ...], *, force: bool = True
) -> Verdict:
    """Run `suites` (relative to `root`) in a child with every holding helper forced to raise.

    Under ``--showlocals`` and ``-vv``, so locals are rendered uncut - the
    greatest exposure pytest offers. `tests.conftest` is loaded in every run,
    as a plugin when `root` is not this tree, so a tree-local run and a
    temporary one render through the same hooks.

    THE GATE'S OWN FRAMES ARE GRADED TOO - CS-1177, from an adversary's probe:
    ``tools/outbound_gate.py`` is where the canary tables live and where they
    are read, and a raise inside its helper printed a canary under
    ``--showlocals`` with every suite's own helpers clean. So the traced
    population is the member modules PLUS the gate, whichever member called it.
    A gate frame is selected when its code READS a table AND a member module
    called it directly - the gate's own hygiene, as the suites reach it. NOT
    GRADED, and said rather than implied: a table reader the gate calls from
    inside ``scan``, because ``scan`` holds the payload it was handed as its
    ``text`` argument - a message carrying a canary, in the CS-1167 suite - and
    a raise anywhere beneath it renders that argument. Holding its input is what
    a scanner is; a raise inside ``scan`` rendering a real payload is a residual
    of the gate's API, recorded here, not a helper's hygiene. The same holds one
    frame further down: ``tools/precommit_gate.py::check_secrets`` takes the
    text it scans as its ``text`` argument - staged content at commit, a canary
    when a gap helper probes one - and a raise inside it renders that argument.
    That file is FROZEN, so this is declared rather than repaired here.

    `force` False runs the same child without the forcer, for an arm whose
    raise is planted by the child itself.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    real = [os.path.realpath(root / suite) for suite in suites]
    real.append(os.path.realpath(OUTBOUND_PATH))
    forcer = ["-p", FORCER_NAME] if force else []
    (workdir / (FORCER_NAME + ".py")).write_text(
        HELPER_FORCER % (str(OUTBOUND_PATH), real), encoding="ascii"
    )
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}
    env["PYTHONPATH"] = os.pathsep.join((str(workdir), str(REPO_ROOT)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CLOCKSPEED_SAVE_ROOT"] = str(workdir / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(workdir / "absent-local-config.json")
    plugin = [] if root == REPO_ROOT else ["-p", "tests.conftest", "--rootdir", str(root)]
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-vv",
            "--showlocals",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:randomly",
            *forcer,
            *plugin,
            "-k",
            NO_RECURSION,
            *suites,
        ],
        capture_output=True,
        cwd=root,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return _verdict(
        proc.returncode,
        proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace"),
        suites,
    )


@pytest.fixture(scope="module")
def pristine(tmp_path_factory: pytest.TempPathFactory) -> Verdict:
    """The derived population of THIS tree, forced once and shared - counts only."""
    return forced_run(
        tmp_path_factory.mktemp("cs1177_pristine"), REPO_ROOT, derived_canary_suites()
    )


# --------------------------------------------------------------------------
# Arm 1 - the membership rule
# --------------------------------------------------------------------------


def test_the_rule_reads_code_and_not_prose(tmp_path: Path) -> None:
    """A table named in a string or a comment is not a read; an attribute access is."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_cs1177_prose.py").write_text(
        '"""Mentions CREDENTIAL_CANARIES in prose."""\n# CREDENTIAL_BRANCH_CANARIES\n',
        encoding="ascii",
    )
    reader = tests_dir / "test_cs1177_reader.py"
    reader.write_text("import gate\n\nTABLE = gate.CREDENTIAL_BRANCH_CANARIES\n", encoding="ascii")
    (tests_dir / "helper_not_a_test.py").write_text(
        "import gate\n\nTABLE = gate.CREDENTIAL_CANARIES\n", encoding="ascii"
    )
    members = canary_suites(tests_dir)
    exact = members == [reader]
    assert exact, "members: %d" % len(members)


def test_a_module_reading_through_a_helper_import_is_a_member(tmp_path: Path) -> None:
    """A test module that reaches a table only THROUGH a helper it imports is a member.

    MEASURED by an adversary on the first build: membership read each test
    module's own source, so a module whose canaries came from an imported
    helper was named in no list AND derived by no rule. Every import form is
    planted - absolute, from a package, relative, and through a chain of two
    helpers - beside a module importing an unrelated helper, which must stay out.

    THE SECOND ADVERSARY'S FORMS are planted too: the gate's ``_canary``
    accessor and a gap helper called by attribute, a fixture from a reader
    ``conftest.py``, ``pytest_plugins``, a helper loaded by a path string, and a
    module that loads the gate by its file name (fail closed). The one form no
    syntax can show - ``getattr`` with a computed name on a gate imported under
    another name - is DECLARED uncovered, and pinned out so the declaration
    cannot silently go stale; a gate file named only in a docstring is prose.
    """
    tests_dir = tmp_path / "tests"
    (tests_dir / "deep").mkdir(parents=True)
    (tests_dir / "__init__.py").write_text("", encoding="ascii")
    (tests_dir / "deep" / "__init__.py").write_text("", encoding="ascii")
    sources = {
        "canary_helper.py": "import gate\n\nTABLE = gate.CREDENTIAL_CANARIES\n",
        "chained_helper.py": "from tests.canary_helper import TABLE\n",
        "plain_helper.py": "VALUE = 1\n",
        "test_absolute.py": "from tests.canary_helper import TABLE\n",
        "test_package.py": "from tests import canary_helper\n",
        "test_relative.py": "from .canary_helper import TABLE\n",
        "test_chained.py": "import tests.chained_helper\n",
        "deep/test_up_two.py": "from ..chained_helper import TABLE\n",
        "test_unrelated.py": "from tests.plain_helper import VALUE\n",
        "test_accessor.py": "import gate\n\nVALUE = gate._canary('AWS access key id')\n",
        "test_gap_helper.py": "import gate\n\nGAPS = gate.credential_canary_gaps\n",
        "conftest.py": (
            "import pytest\nimport gate\n\n\n@pytest.fixture\n"
            "def canary():\n    return gate.CREDENTIAL_CANARIES\n"
        ),
        "test_fixture.py": "def test_x(canary):\n    raise RuntimeError(canary)\n",
        "test_plugins.py": "pytest_plugins = ['tests.canary_helper']\n",
        "test_path_load.py": (
            "import importlib.util\n\n"
            "SPEC = importlib.util.spec_from_file_location('h', 'tests/canary_helper.py')\n"
        ),
        "test_loads_the_gate.py": "GATE = 'tools/' + 'outbound_gate.py'\n",
        "test_unrelated_getattr.py": (
            "import gate\n\nTABLE = getattr(gate, 'CREDENTIAL_' + 'CANARIES')\n"
        ),
        "test_gate_in_prose.py": '"""Mentions tools/outbound_gate.py in prose."""\n',
    }
    for relative, source in sources.items():
        (tests_dir / relative).write_text(source, encoding="ascii")
    members = sorted(path.relative_to(tests_dir).as_posix() for path in canary_suites(tests_dir))
    expected = sorted(
        name
        for name in sources
        if "test_" in name and "unrelated" not in name and "prose" not in name
    )
    missing = sorted(set(expected) - set(members))
    extra = sorted(set(members) - set(expected))
    assert missing == [], "helper-import members the rule missed: " + ", ".join(missing)
    assert extra == [], "modules admitted that reach no table: " + ", ".join(extra)


def test_canary_suites_in_the_cs1175_suite_is_the_derivation() -> None:
    """``CANARY_SUITES`` is BOUND to the derivation, not merely equal to it today.

    MEASURED by an adversary on the first build: restoring the hand-kept
    three-module tuple SURVIVED, because every arm here graded
    :func:`canary_suites` and none graded the name the forced arm actually
    reads. Equality alone would pass a hand list typed to match; the binding is
    read from source, so a list typed in its place is red on the day it lands.
    """
    source = (TESTS_DIR / "test_cs1175_rule_narrowing.py").read_text(encoding="utf-8")
    bindings = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "CANARY_SUITES" for t in node.targets)
    ]
    count = len(bindings)
    derived = [
        value
        for value in bindings
        if isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "derived_canary_suites"
    ]
    bound = len(derived)
    assert count == 1, "CANARY_SUITES is bound %d times" % count
    assert bound == 1, "CANARY_SUITES is not bound to derived_canary_suites()"


def test_the_derivation_runs_once_per_process() -> None:
    """CS-1193: the tree's population is derived once and every caller reads that answer.

    MEASURED on CI: the derivation cost about ten seconds a call and ran at the
    import of the CS-1175 suite, in the ``pristine`` fixture and in the floor
    arm, in every worker and every child. The same object back is the proof
    the second call derived nothing.
    """
    first = derived_canary_suites()
    again = derived_canary_suites()
    same = first is again
    assert same, "derived_canary_suites() derived the population a second time"


def test_every_module_is_walked_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CS-1193: the derivation walks each module's tree ONCE, not once per question.

    A tree of plain modules - no reader, so no conftest fixture read either -
    is walked exactly as many times as it has modules.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    modules = 3
    for index in range(modules):
        (tests_dir / ("test_plain_%d.py" % index)).write_text(
            '"""Plain."""\n\nimport os\n\n\ndef test_x(a, b):\n    return os.sep\n',
            encoding="ascii",
        )
    walked: list[int] = []
    real = ast.walk

    def counting(node: ast.AST) -> Iterator[ast.AST]:
        if isinstance(node, ast.Module):
            walked.append(1)
        return real(node)

    monkeypatch.setattr(ast, "walk", counting)
    members = canary_suites(tests_dir)
    count = len(walked)
    found = len(members)
    assert found == 0, "plain modules admitted: %d" % found
    assert count == modules, "%d module walks for %d modules" % (count, modules)


def test_the_population_is_derived_and_reaches_every_known_reader() -> None:
    """The derivation reaches the modules the retired hand list named, and this one.

    A FLOOR, NOT A LIST: it may grow without an edit here. The names below are
    the control that the rule still reads this tree, not the population.
    """
    members = derived_canary_suites()
    floor = {
        "tests/test_cs1167_credential_canary_coverage.py",
        "tests/test_cs1172_branch_canaries.py",
        "tests/test_cs1175_rule_narrowing.py",
        "tests/test_canary_population.py",
    }
    missing = sorted(floor - set(members))
    assert missing == [], "known canary readers the rule missed: " + ", ".join(missing)


# --------------------------------------------------------------------------
# Arm 2 - a raise inside a holding helper renders no canary
# --------------------------------------------------------------------------

#: The hygienic line in the CS-1167 suite's `refused_lines`, and the same
#: helper with its hygiene removed - the message bound to a named local. The
#: control edits a TEMPORARY copy, never the tree.
HYGIENIC = (
    "    refusals, _, _ = OUTBOUND.scan(\n"
    '        "Status report.\\nsee " + OUTBOUND.CREDENTIAL_CANARIES[reason] + " here\\n"\n'
    "    )\n"
)
UNHYGIENIC = (
    '    message = "Status report.\\nsee " + OUTBOUND.CREDENTIAL_CANARIES[reason] + " here\\n"\n'
    "    refusals, _, _ = OUTBOUND.scan(message)\n"
)
ROOT_LINE = "REPO_ROOT = Path(__file__).resolve().parents[1]\n"
CONTROL_SUITE = "tests/test_cs1167_credential_canary_coverage.py"


def unhygienic_copy(root: Path) -> tuple[str, int, int]:
    """Copy the CS-1167 suite under `root` with one helper's hygiene removed.

    Returns:
        ``(relative path, hygiene edits landed, root edits landed)`` - both
        must be exactly one, or the control grades a copy it did not make.
    """
    source = (REPO_ROOT / CONTROL_SUITE).read_text(encoding="utf-8")
    hygiene = source.count(HYGIENIC)
    rooted = source.count(ROOT_LINE)
    source = source.replace(HYGIENIC, UNHYGIENIC).replace(
        ROOT_LINE, "REPO_ROOT = Path(%r)\n" % str(REPO_ROOT)
    )
    relative = "tests/test_cs1177_unhygienic_copy.py"
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / relative).write_text(source, encoding="utf-8")
    return relative, hygiene, rooted


def test_a_helper_raise_under_showlocals_renders_no_canary_forced_red_output(
    tmp_path: Path, pristine: Verdict
) -> None:
    """CS-1177: every derived member, holding helpers forced to RAISE, renders no canary.

    THE CONTROL RUNS IN THE SAME TEST: the CS-1167 suite with ONE helper's
    hygiene removed, forced the same way, renders the planted canary - so the
    zero from the tree is a measurement of hygiene, not a capture that cannot
    see a local.
    """
    relative, hygiene, rooted = unhygienic_copy(tmp_path / "control")
    assert hygiene == 1, "the hygiene edit landed %d times" % hygiene
    assert rooted == 1, "the root edit landed %d times" % rooted
    control = forced_run(tmp_path / "control_work", tmp_path / "control", (relative,))
    control_forced = control.forced[relative]
    control_leaked = control.leaked
    assert control_forced >= 1, "the control forced no helper raise"
    assert control_leaked >= 1, "the unhygienic control rendered no canary"

    # Every verdict is bound to a scalar first: assertion rewriting renders an
    # asserted attribute's whole owner, and the owner is not what is graded.
    code = pristine.code
    ungraded = sorted(suite for suite, count in pristine.graded.items() if count == 0)
    total = sum(pristine.forced.values())
    leaked = pristine.leaked
    assert code == 1, "the forced run did not fail: exit %d" % code
    assert ungraded == [], "members no test of which ran: " + ", ".join(ungraded)
    assert total >= 1, "no helper raise was forced in the tree"
    assert leaked == 0, "the forced run rendered %d canary value(s)" % leaked


#: The adversary's probe, planted: the gate's own gap helpers driven with a
#: gate whose ``check_secrets`` is a BUILTIN that raises, so no frame of this
#: child holds the canary and the last Python frames in the traceback are the
#: gate's. The rule is named by its reason - a key, never a value.
GATE_PROBE = """
import importlib.util
import math
import re
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("cs1177_gate_probe_outbound", Path(%r))
OUTBOUND = importlib.util.module_from_spec(spec)
sys.modules["cs1177_gate_probe_outbound"] = OUTBOUND
spec.loader.exec_module(OUTBOUND)
REASON = "AWS access key id"


class RaisingGate:
    SECRET_PATTERNS = [(re.compile("(?:A|B)"), REASON)]
    PLACEHOLDER_RE = re.compile("x^")
    Report = list
    check_secrets = staticmethod(math.sqrt)


def test_the_canary_gap_helper_raises():
    OUTBOUND.credential_canary_gaps(RaisingGate)


def test_the_branch_gap_helper_raises():
    OUTBOUND.credential_branch_gaps(RaisingGate)
"""

#: How many tests GATE_PROBE holds - one per gap helper.
GATE_PROBE_TESTS = 2

#: The same raise from a frame that DOES bind the canary - the control.
GATE_PROBE_CONTROL = (
    GATE_PROBE
    + """

def test_a_frame_that_binds_the_canary_raises():
    held = OUTBOUND.CREDENTIAL_CANARIES[REASON]
    math.sqrt(held, held)
"""
)


def test_a_raise_inside_the_gates_own_helper_renders_no_canary_forced_red_output(
    tmp_path: Path,
) -> None:
    """CS-1177: the adversary's probe - a raise INSIDE the gate's gap helpers - renders none.

    Measured on the first build: one canary printed, from the gate helper's own
    ``canary`` local. The control is the same child plus one frame that binds
    the canary before the same builtin raises, so a zero here is a measurement.
    """
    root = tmp_path / "probe"
    (root / "tests").mkdir(parents=True)
    probe = root / "tests" / "test_cs1177_gate_probe.py"
    probe.write_text(GATE_PROBE % str(OUTBOUND_PATH), encoding="ascii")
    control = root / "tests" / "test_cs1177_gate_probe_control.py"
    control.write_text(GATE_PROBE_CONTROL % str(OUTBOUND_PATH), encoding="ascii")

    shown = forced_run(
        tmp_path / "control_work", root, (control.relative_to(root).as_posix(),), force=False
    )
    shown_leaked = shown.leaked
    assert shown_leaked >= 1, "the control rendered no canary"

    relative = probe.relative_to(root).as_posix()
    verdict = forced_run(tmp_path / "probe_work", root, (relative,), force=False)
    code = verdict.code
    graded = verdict.graded[relative]
    leaked = verdict.leaked
    assert code == 1, "the probe did not fail: exit %d" % code
    assert graded == GATE_PROBE_TESTS, "probe tests run: %d" % graded
    assert leaked == 0, "a raise inside the gate helper rendered %d canary value(s)" % leaked


# --------------------------------------------------------------------------
# Arm 3 - a new module named in no list is picked up and graded
# --------------------------------------------------------------------------

#: A new canary-holding module, named in no list anywhere. Its helper binds a
#: canary to a local, so a forced run that GRADED it renders one.
PLANTED = """
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("cs1177_planted_outbound", Path(%r))
module = importlib.util.module_from_spec(spec)
sys.modules["cs1177_planted_outbound"] = module
spec.loader.exec_module(module)


def held_length():
    held = module.CREDENTIAL_CANARIES["AWS access key id"]
    return len(held)


def test_a_planted_module_reads_a_canary():
    size = held_length()
    assert size > 0
"""


def test_a_new_canary_module_in_no_list_is_picked_up_and_graded_forced_red_output(
    tmp_path: Path, pristine: Verdict
) -> None:
    """The mutation the acceptance names: plant a module, derive, force, and see it graded.

    The pristine tree is green IN THE SAME RUN - the shared forced verdict of
    this tree is asserted here too, so a planted red and a pristine green are
    one run's two readings.
    """
    root = tmp_path / "planted"
    (root / "tests").mkdir(parents=True)
    planted = root / "tests" / "test_cs1177_planted.py"
    planted.write_text(PLANTED % str(OUTBOUND_PATH), encoding="ascii")
    members = canary_suites(root / "tests")
    picked = members == [planted]
    assert picked, "the planted module was not derived: %d member(s)" % len(members)

    relative = planted.relative_to(root).as_posix()
    verdict = forced_run(tmp_path / "planted_work", root, (relative,))
    graded = verdict.graded[relative]
    forced = verdict.forced[relative]
    rendered = verdict.leaked
    assert graded >= 1, "the planted module was not run"
    assert forced >= 1, "the planted helper was not forced"
    assert rendered >= 1, "the planted module was run but not graded"

    code = pristine.code
    leaked = pristine.leaked
    assert code == 1, "the pristine forced run did not fail: exit %d" % code
    assert leaked == 0, "the pristine tree rendered %d canary value(s)" % leaked
