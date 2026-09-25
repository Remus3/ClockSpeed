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
import importlib.util
import operator
import os
import re
import subprocess
import sys
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


def reads_a_canary_table(source: str) -> bool:
    """True when `source`'s CODE reads either canary table - never its prose."""
    return _reads(ast.parse(source))


def _reads(tree: ast.AST) -> bool:
    """True when the parsed module's code reads either canary table by name."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in CANARY_TABLES:
            return True
        if isinstance(node, ast.Name) and node.id in CANARY_TABLES:
            return True
        if isinstance(node, ast.alias) and node.name in CANARY_TABLES:
            return True
    return False


def _module_name(path: Path, root: Path) -> tuple[str, bool]:
    """The dotted name `path` imports as under `root`, and whether it is a package."""
    parts = path.relative_to(root).with_suffix("").parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


def _imported(tree: ast.AST, name: str, is_package: bool) -> set[str]:
    """Every dotted name the module's imports could reach, relative ones resolved.

    ``from x import y`` yields both ``x`` and ``x.y``, because ``y`` may be a
    submodule; a name that is not a module simply matches nothing.
    """
    package = name if is_package else name.rpartition(".")[0]
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = package
            for _ in range(max(node.level - 1, 0)):
                base = base.rpartition(".")[0]
            if node.level == 0:
                base = node.module or ""
            elif node.module:
                base = base + "." + node.module if base else node.module
            found.add(base)
            found.update(base + "." + alias.name for alias in node.names)
    return found


def canary_suites(tests_dir: Path) -> list[Path]:
    """Every ``test_*.py`` under `tests_dir` that reads a canary table, sorted.

    READS TRANSITIVELY - CS-1177, from an adversary's measurement: a module
    whose canaries arrive through a helper it imports holds them all the same.
    Every module under `tests_dir` is parsed once; a module is a READER when its
    own code reads a table by name, or when it imports a reader, closed over
    import chains of any length. Members are the readers that are test modules.
    """
    root = tests_dir.parent
    trees: dict[str, tuple[Path, ast.AST, bool]] = {}
    for path in sorted(tests_dir.rglob("*.py")):
        name, is_package = _module_name(path, root)
        trees[name] = (path, ast.parse(path.read_text(encoding="utf-8")), is_package)
    reaches = {
        name: _imported(tree, name, is_package) for name, (_, tree, is_package) in trees.items()
    }
    readers = {name for name, (_, tree, _) in trees.items() if _reads(tree)}
    grown = True
    while grown:
        added = {name for name in trees if name not in readers and reaches[name] & readers}
        readers |= added
        grown = bool(added)
    return sorted(
        path
        for name, (path, _, _) in trees.items()
        if name in readers and path.name.startswith("test_")
    )


def derived_canary_suites() -> tuple[str, ...]:
    """This tree's canary suites as repo-relative POSIX paths - the child's arguments."""
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
    if TABLES & names(code) or any(holds(value) for value in frame.f_locals.values()):
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


def forced_run(workdir: Path, root: Path, suites: tuple[str, ...]) -> Verdict:
    """Run `suites` (relative to `root`) in a child with every holding helper forced to raise.

    Under ``--showlocals`` and ``-vv``, so locals are rendered uncut - the
    greatest exposure pytest offers. `tests.conftest` is loaded in every run,
    as a plugin when `root` is not this tree, so a tree-local run and a
    temporary one render through the same hooks.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    real = [os.path.realpath(root / suite) for suite in suites]
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
            "-p",
            FORCER_NAME,
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
    }
    for relative, source in sources.items():
        (tests_dir / relative).write_text(source, encoding="ascii")
    members = sorted(path.relative_to(tests_dir).as_posix() for path in canary_suites(tests_dir))
    expected = sorted(name for name in sources if "test_" in name and "unrelated" not in name)
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
