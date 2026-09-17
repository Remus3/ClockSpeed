"""CS-1105 - every truncation CONDITION on the world-token scan reaches the exit status.

WHAT CS-1096 LEFT OPEN (its documented limit F3). The bound-count arm in
tests/test_world_token_bound_count.py counts REPORTING SITES: the places a
blocking diagnostic is produced. A cap that only ORs into `scan_capped` beside
the existing report, or a cap inside clockspeed/save/header.py's scanner that
only sets `truncated = True`, adds a truncation CONDITION without adding a
reporting site, so that arm stayed green over it.

THE DESIGN IS BEHAVIOURAL, WITH A STRUCTURAL ENUMERATION AS ITS CONTROL, and
the two halves answer different questions:

- BEHAVIOURAL. `CONDITION_TABLE` holds one case per truncation condition. Each
  case builds a synthetic save root that trips exactly that condition - small
  cap values are monkeypatched onto a gate module loaded from its path, and
  the header case crafts a refused header holding one candidate past the
  scanner's own cap - then drives the real `discover_world_tokens` and the
  real `emit`, which is the value `main` returns as the exit status. The case
  passes only on exit 1 with exactly one diagnostic, and that diagnostic names
  the case's own bound, so a case cannot pass on a neighbour's report. A
  control on the same fixture shape with no cap tripped must exit 0. Driving
  `main` itself would add git and the lint subprocess and no coverage of this
  path. Why behavioural at all: only running the code proves a condition
  REACHES the exit status - a data-flow proof would be a second model of the
  gate that can be wrong the same way the prose was.
- STRUCTURAL. A table of hand-built cases cannot see a condition nobody wrote
  a case for, so `enumerate_conditions` reads the conditions out of the two
  sources through the syntax tree and the arm demands the enumeration equal
  the table's keys as a MULTISET. A new condition with no case is red; a case
  whose condition is gone is red too.

WHAT THE ENUMERATION COUNTS, derived from the code rather than a name list:

1. REPORTING CALLS are calls of `_report_world_token_uncovered`, or of a
   reached gate function whose every such call sits under `if` tests made of
   its own parameters alone (a pure wrapper, today `_report_root_cap`).
2. In every other reached gate function, the enclosing `if` tests of a
   reporting call are split. A ROUTING test - names, constants, `and`, `or`,
   `not`, `is` - does not decide truncation; any other test IS a condition,
   keyed by its source text. The local names in a routing test are FLAGS.
3. A flag is traced backward through its bindings. `False` initialises;
   `True` is a condition keyed by the non-routing tests around it; a boolean
   combination is read operand by operand, so its names become flags; a tuple unpacked from a call
   follows the callee's LAST return element, and a call through a local name
   in the gate resolves to every function the reached gate code imports from
   clockspeed/save/header.py whose annotation returns `tuple[..., bool]`.
   Anything else bound to a flag - a comparison, `|=` with an expression, a
   `True` constant inside `or` - is a condition keyed by its text. Fail closed.

KNOWN LIMITS, stated rather than implied:

- A cap that sets NO flag and makes NO report - a bare `break` - is a silent
  drop, not a truncation condition in this sense, and is not seen.
- A flag bound through a `for` target, a `with ... as`, an attribute or a
  container is not traced. A flag that enters a function as a PARAMETER is
  refused as a problem rather than followed.
- The CS-1096 limit F2 applies unchanged: an alias or an indirect reach to a
  helper is not followed.

The mutation arms feed MODIFIED SOURCE TEXT to the enumeration, and a gate
module built from modified text to the behavioural cases. The files on disk
are never mutated, and every mutant asserts it applied.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import struct
import sys
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

from clockspeed.save import header as header_module
from tests.save import synthetic
from tests.test_world_token_bound_count import SINK, reached_functions

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "precommit_gate.py"
HEADER = REPO_ROOT / "clockspeed" / "save" / "header.py"
HEADER_IMPORT = "clockspeed.save.header"

# (module tag, function name, condition text)
Key = tuple[str, str, str]


def _text(path: Path) -> str:
    """A source file as text, decoded from bytes so no newline is rewritten."""
    return path.read_bytes().decode("utf-8")


# --------------------------------------------------------------------------
# The STRUCTURAL enumeration. Syntax tree only.
# --------------------------------------------------------------------------

_ROUTING_NODES = (
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.Compare,
    ast.Is,
    ast.IsNot,
)
_TUPLE_OF_BOOL = re.compile(r"^tuple\[.*,\s*bool\]$")


def _is_routing(test: ast.expr) -> bool:
    return all(isinstance(node, _ROUTING_NODES) for node in ast.walk(test))


def _names(expr: ast.AST) -> Iterator[str]:
    return (node.id for node in ast.walk(expr) if isinstance(node, ast.Name))


def _params(func: ast.FunctionDef) -> set[str]:
    args = func.args
    names = {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
    names.update(a.arg for a in (args.vararg, args.kwarg) if a is not None)
    return names


class Enumeration:
    """The truncation conditions of the world-token scan, read from two sources."""

    def __init__(self, gate_source: str, header_source: str) -> None:
        """Parse both sources and walk the scan from the gate's reporting calls."""
        self.trees = {"gate": ast.parse(gate_source), "header": ast.parse(header_source)}
        self.functions = {
            tag: {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
            for tag, tree in self.trees.items()
        }
        self.parents: dict[int, ast.AST] = {}
        for tree in self.trees.values():
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    self.parents[id(child)] = node
        self.found: set[tuple[str, str, int, int, str]] = set()
        self.problems: list[str] = []
        self.traced: set[tuple[str, str, str]] = set()
        self.returned: set[tuple[str, str]] = set()
        self.reached = [name for name in reached_functions(gate_source) if name != SINK]
        self._walk_gate()

    # -- helpers -----------------------------------------------------------

    def _chain(self, node: ast.AST) -> list[tuple[ast.If, ast.expr]]:
        """The enclosing `if` statements of a node, outermost first, with the test that holds."""
        chain: list[tuple[ast.If, ast.expr]] = []
        prev = node
        parent = self.parents.get(id(prev))
        while parent is not None and not isinstance(parent, ast.FunctionDef):
            if isinstance(parent, ast.If) and prev is not parent.test:
                in_body = any(prev is statement for statement in parent.body)
                test = parent.test if in_body else ast.UnaryOp(op=ast.Not(), operand=parent.test)
                chain.append((parent, test))
            prev, parent = parent, self.parents.get(id(parent))
        return list(reversed(chain))

    def _record(
        self,
        tag: str,
        func: str,
        at: ast.AST,
        extra: str | None = None,
        keyed_by: ast.AST | None = None,
    ) -> None:
        """Record one condition: the non-routing tests around `at`, keyed by a node."""
        texts = [ast.unparse(test) for _if, test in self._chain(at) if not _is_routing(test)]
        if extra is not None:
            texts.append(extra)
        node = at if keyed_by is None else keyed_by
        text = " / ".join(texts) or "<unconditional>"
        self.found.add(
            (tag, func, getattr(node, "lineno", 0), getattr(node, "col_offset", 0), text)
        )

    # -- the gate seed -----------------------------------------------------

    def _walk_gate(self) -> None:
        functions = self.functions["gate"]
        reporters = {SINK}
        changed = True
        while changed:
            changed = False
            for name in self.reached:
                if name in reporters:
                    continue
                calls = self._reporting_calls(functions[name], reporters)
                params = _params(functions[name])
                if calls and all(
                    _is_routing(test) and set(_names(test)) <= params
                    for call in calls
                    for _if, test in self._chain(call)
                ):
                    reporters.add(name)
                    changed = True
        for name in self.reached:
            if name in reporters:
                continue
            func = functions[name]
            for call in self._reporting_calls(func, reporters):
                chain = self._chain(call)
                deciding = [if_node for if_node, test in chain if not _is_routing(test)]
                if deciding:
                    self._record("gate", name, call, keyed_by=deciding[-1])
                for _if, test in chain:
                    if _is_routing(test):
                        for flag in set(_names(test)) - _params(func):
                            self._trace("gate", name, flag)

    @staticmethod
    def _reporting_calls(func: ast.FunctionDef, reporters: set[str]) -> list[ast.Call]:
        return [
            node
            for node in ast.walk(func)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in reporters
        ]

    # -- flag flow ---------------------------------------------------------

    def _flow(self, tag: str, func: str, expr: ast.expr, at: ast.AST, label: str) -> None:
        """An expression whose value flows into a flag, read operand by operand.

        `and`, `or` and `not` are looked through, so `flag or capped or n > 8`
        still traces `capped` AND records `n > 8`. A name is traced, `False`
        initialises, `True` is a condition under its tests, and anything else
        is a condition keyed by its own text - fail closed.
        """
        if isinstance(expr, ast.BoolOp):
            for operand in expr.values:
                self._flow(tag, func, operand, at, label)
        elif isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
            self._flow(tag, func, expr.operand, at, label)
        elif isinstance(expr, ast.Name):
            self._trace(tag, func, expr.id)
        elif isinstance(expr, ast.Constant) and expr.value is False:
            return
        elif isinstance(expr, ast.Constant) and expr.value is True:
            self._record(tag, func, at)
        else:
            self._record(tag, func, at, "%s = %s" % (label, ast.unparse(expr)))

    def _trace(self, tag: str, func: str, flag: str) -> None:
        if (tag, func, flag) in self.traced:
            return
        self.traced.add((tag, func, flag))
        node_fn = self.functions[tag][func]
        if flag in _params(node_fn):
            self.problems.append(
                "%s.%s: the flag %r enters as a parameter and is not followed" % (tag, func, flag)
            )
            return
        for node in ast.walk(node_fn):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    self._bind(tag, func, flag, target, node.value, node)
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
                self._bind(tag, func, flag, node.target, node.value, node)
            elif (
                isinstance(node, ast.AugAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == flag
            ):
                self._flow(tag, func, node.value, node, flag + " |=")

    def _bind(
        self, tag: str, func: str, flag: str, target: ast.expr, value: ast.expr, at: ast.AST
    ) -> None:
        if isinstance(target, ast.Name) and target.id == flag:
            self._flow(tag, func, value, at, flag)
            return
        if not isinstance(target, (ast.Tuple, ast.List)):
            return
        for index, element in enumerate(target.elts):
            if not (isinstance(element, ast.Name) and element.id == flag):
                continue
            if isinstance(value, ast.Tuple) and len(value.elts) == len(target.elts):
                self._flow(tag, func, value.elts[index], at, flag)
            elif isinstance(value, ast.Call) and index == len(target.elts) - 1:
                self._through_call(tag, func, value)
            else:
                self.problems.append(
                    "%s.%s: the flag %r is unpacked from a shape not followed at line %d"
                    % (tag, func, flag, at.lineno)  # type: ignore[attr-defined]
                )

    def _through_call(self, tag: str, func: str, call: ast.Call) -> None:
        """The LAST return element of whatever a call reaches."""
        if isinstance(call.func, ast.Name) and call.func.id in self.functions[tag]:
            self._returns(tag, call.func.id)
            return
        if tag == "gate":
            entries = self._header_entries()
            for entry in entries:
                self._returns("header", entry)
            if entries:
                return
        self.problems.append(
            "%s.%s: a flag comes from %r, which is not resolved"
            % (tag, func, ast.unparse(call.func))
        )

    def _header_entries(self) -> list[str]:
        imported = {
            alias.name
            for name in self.reached
            for node in ast.walk(self.functions["gate"][name])
            if isinstance(node, ast.ImportFrom) and node.module == HEADER_IMPORT
            for alias in node.names
        }
        entries: list[str] = []
        for name in sorted(imported):
            func = self.functions["header"].get(name)
            returns = None if func is None else func.returns
            if returns is not None and _TUPLE_OF_BOOL.match(ast.unparse(returns)):
                entries.append(name)
        return entries

    def _returns(self, tag: str, func: str) -> None:
        if (tag, func) in self.returned:
            return
        self.returned.add((tag, func))
        node_fn = self.functions[tag][func]
        for node in ast.walk(node_fn):
            if not isinstance(node, ast.Return) or node.value is None:
                continue
            value = node.value
            if isinstance(value, ast.Tuple) and value.elts:
                self._flow(tag, func, value.elts[-1], node, "return")
            elif isinstance(value, ast.Call):
                self._through_call(tag, func, value)
            elif isinstance(value, ast.Name):
                self._returned_name(tag, func, value.id)
            else:
                self.problems.append(
                    "%s.%s: a return at line %d is not followed" % (tag, func, node.lineno)
                )

    def _returned_name(self, tag: str, func: str, name: str) -> None:
        bindings = [
            node
            for node in ast.walk(self.functions[tag][func])
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
        ]
        if not bindings:
            self.problems.append("%s.%s: the returned name %r is not bound" % (tag, func, name))
        for node in bindings:
            if isinstance(node.value, ast.Call):
                self._through_call(tag, func, node.value)
            elif isinstance(node.value, ast.Tuple) and node.value.elts:
                self._flow(tag, func, node.value.elts[-1], node, "return")
            else:
                self.problems.append(
                    "%s.%s: the returned name %r is bound to a shape not followed"
                    % (tag, func, name)
                )

    def keys(self) -> Counter[Key]:
        """The conditions found, as a multiset of (module, function, condition text)."""
        return Counter((tag, func, text) for tag, func, _line, _col, text in self.found)


def enumerate_conditions(gate_source: str, header_source: str) -> tuple[Counter[Key], list[str]]:
    """Every truncation condition the scan reaches, and what could not be read."""
    enumeration = Enumeration(gate_source, header_source)
    return enumeration.keys(), enumeration.problems


# --------------------------------------------------------------------------
# The BEHAVIOURAL table. One synthetic save root per condition.
# --------------------------------------------------------------------------

ACCOUNT = "cs1105-account"


def _account(root: Path, name: str = ACCOUNT) -> Path:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _saves(directory: Path, count: int) -> None:
    for index in range(count):
        (directory / ("Cs1105save%02d.sav" % index)).write_bytes(b"")


def _arrange_quiet(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    del gate, monkeypatch
    _saves(_account(root), 1)


def _arrange_file_cap(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "MAX_SAVE_HEADER_FILES", 1)
    _saves(_account(root), 2)


def _arrange_budget(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "SAVE_HEADER_BUDGET_SECONDS", -1.0)
    _saves(_account(root), 1)


def _arrange_root_cap(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_ENTRIES", 1)
    _account(root, ACCOUNT + "-a")
    _account(root, ACCOUNT + "-b")


def _arrange_examination(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_SCAN", 1)
    _saves(_account(root), 2)


def _arrange_retention(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_ENTRIES", 1)
    _saves(_account(root), 2)


def _synthetic_candidate(index: int) -> str:
    """A distinct identifier-shaped value. Synthetic, generated, never a real token."""
    return ("Cs1105cap%03d" % index).ljust(header_module.WORLD_TOKEN_LENGTH, "x")


def _arrange_scan_cap(gate: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A refused header holding one distinct candidate past the scanner's own cap.

    The cap is read from the module that owns it, never restated. The header
    version is one no measured layout carries, so the parser refuses before a
    string is read and no save-name slot is skipped.
    """
    del gate, monkeypatch
    unmeasured = max(header_module.SUPPORTED_HEADER_VERSIONS) + 1000
    count = header_module.MAX_SCANNED_TOKENS + 1
    blob = struct.pack("<iii", unmeasured, 0, 0) + b"".join(
        synthetic.fstring(_synthetic_candidate(index)) for index in range(count)
    )
    (_account(root) / "Cs1105capped.sav").write_bytes(blob)


@dataclass(frozen=True)
class Case:
    """One truncation condition, the fixture that trips it and its own reason text."""

    key: Key
    marker: str
    arrange: Callable[[ModuleType, Path, pytest.MonkeyPatch], None]


CONDITION_TABLE: tuple[Case, ...] = (
    Case(
        ("gate", "_save_root_dirs", "index >= MAX_SAVE_ROOT_ENTRIES"),
        "save root holds more than",
        _arrange_root_cap,
    ),
    Case(
        ("gate", "_bounded_newest_saves", "examined >= MAX_SAVE_ROOT_SCAN"),
        "a save directory holds more than",
        _arrange_examination,
    ),
    Case(
        ("gate", "_bounded_newest_saves", "matched > len(kept)"),
        "save files in one save directory; only the",
        _arrange_retention,
    ),
    Case(
        ("gate", "_world_tokens_from_headers", "len(paths) > MAX_SAVE_HEADER_FILES"),
        "more save files than the",
        _arrange_file_cap,
    ),
    Case(
        (
            "gate",
            "_world_tokens_from_headers",
            "time.monotonic() - started > SAVE_HEADER_BUDGET_SECONDS",
        ),
        "aggregate save-header budget was spent",
        _arrange_budget,
    ),
    Case(
        (
            "header",
            "scan_framed_tokens",
            "candidate is not None and candidate not in admitted"
            " / len(admitted) >= MAX_SCANNED_TOKENS",
        ),
        "than the scan cap admits",
        _arrange_scan_cap,
    ),
)


def load_gate(source: str | None = None, name: str = "cs1105_gate_under_test") -> ModuleType:
    """The gate as a module, from its path or from modified source text.

    Registered in sys.modules BEFORE execution, because the gate's dataclasses
    resolve string annotations through it. `__file__` is the real path either
    way, so the gate's own repo-root lookup finds this checkout's header module.
    """
    if source is None:
        spec = importlib.util.spec_from_file_location(name, GATE)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    module = ModuleType(name)
    module.__file__ = str(GATE)
    sys.modules[name] = module
    exec(compile(source, str(GATE), "exec"), module.__dict__)  # noqa: S102
    return module


def drive(
    gate: ModuleType,
    arrange: Callable[[ModuleType, Path, pytest.MonkeyPatch], None],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[int, list[str]]:
    """Run the real world-token discovery on a synthetic save root; the exit status and reasons."""
    root = tmp_path / "cs1105-save-root"
    root.mkdir(parents=True)
    monkeypatch.setenv(gate.ENV_SAVE_ROOT, str(root))
    monkeypatch.setenv(gate.ENV_LOCAL_CONFIG, str(tmp_path / "cs1105-absent-config.json"))
    monkeypatch.delenv(gate.ENV_WORLD_TOKENS, raising=False)
    monkeypatch.delenv(gate.ENV_ACCOUNT_DIR, raising=False)
    arrange(gate, root, monkeypatch)
    report = gate.Report()
    gate.discover_world_tokens(report)
    status = gate.emit(report, False, False)
    return status, [diagnostic.reason for diagnostic in report.diagnostics]


@pytest.fixture(scope="module")
def pristine_gate() -> ModuleType:
    return load_gate()


# --------------------------------------------------------------------------
# The arms.
# --------------------------------------------------------------------------


def condition_problems(gate_source: str, header_source: str) -> list[str]:
    """Every disagreement between the enumerated conditions and the table."""
    found, problems = enumerate_conditions(gate_source, header_source)
    table = Counter(case.key for case in CONDITION_TABLE)
    problems = list(problems)
    problems.extend(
        "CS-1105: truncation condition %r reaches the world-token scan and no "
        "CONDITION_TABLE case proves it blocks" % (key,)
        for key in sorted((found - table).elements())
    )
    problems.extend(
        "CS-1105: CONDITION_TABLE case %r names a condition the code no longer has" % (key,)
        for key in sorted((table - found).elements())
    )
    return problems


def test_every_truncation_condition_has_a_blocking_case() -> None:
    """The enumeration and the table agree, as a multiset."""
    problems = condition_problems(_text(GATE), _text(HEADER))
    assert problems == [], "\n".join(problems)


def test_the_enumeration_reaches_both_modules() -> None:
    """Anti-vacuity: conditions in the gate AND behind the scanner in the header."""
    found, _problems = enumerate_conditions(_text(GATE), _text(HEADER))
    tags = {tag for tag, _func, _text_ in found}
    assert tags == {"gate", "header"}


@pytest.mark.parametrize("case", CONDITION_TABLE, ids=lambda case: case.marker)
def test_each_truncation_condition_blocks(
    case: Case, pristine_gate: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The condition, tripped alone, ends the run at exit 1 on its own reason."""
    status, reasons = drive(pristine_gate, case.arrange, tmp_path, monkeypatch)
    assert status == 1, reasons
    assert len(reasons) == 1, reasons
    assert case.marker in reasons[0], reasons


def test_the_quiet_control_passes(
    pristine_gate: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE KNOWN-GOOD CONTROL: the same fixture shape with no cap tripped exits 0."""
    status, reasons = drive(pristine_gate, _arrange_quiet, tmp_path, monkeypatch)
    assert (status, reasons) == (0, [])


def test_the_table_markers_are_distinct() -> None:
    """A marker shared by two cases would let one case pass on the other's report."""
    markers = [case.marker for case in CONDITION_TABLE]
    assert all(a == b or a not in b for a in markers for b in markers), (
        "a marker is a substring of another"
    )


# --------------------------------------------------------------------------
# Mutation arms - modified source text only, each asserting it applied.
# --------------------------------------------------------------------------


def _plant(source: str, anchor: str, addition: str) -> str:
    assert source.count(anchor) == 1, "the plant anchor is not unique"
    mutant = source.replace(anchor, anchor + addition)
    assert mutant != source, "the plant did not apply"
    return mutant


def _swap(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, "the swap anchor is not unique"
    mutant = source.replace(old, new)
    assert mutant != source, "the swap did not apply"
    return mutant


_SCAN_CAPPED = "        scan_capped = scan_capped or capped\n"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda src: _plant(
            src, _SCAN_CAPPED, "        if len(candidates) > 8:\n            scan_capped = True\n"
        ),
        lambda src: _swap(
            src,
            _SCAN_CAPPED,
            "        scan_capped = scan_capped or capped or len(candidates) > 8\n",
        ),
        lambda src: _swap(
            src, _SCAN_CAPPED, "        scan_capped = scan_capped or capped or True\n"
        ),
    ],
    ids=["if-sets-flag", "or-comparison", "or-true"],
)
def test_a_gate_cap_that_only_sets_scan_capped_reddens_the_arm(
    mutate: Callable[[str], str],
) -> None:
    """F3's first shape: no new reporting site, one new condition."""
    gate = _text(GATE)
    mutant = mutate(gate)
    assert condition_problems(gate, _text(HEADER)) == []
    assert condition_problems(mutant, _text(HEADER)) != []


_TRUNCATED_INIT = "    truncated = False\n"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda src: _plant(
            src, _TRUNCATED_INIT, "    if len(data) > MAX_HEADER_BYTES:\n        truncated = True\n"
        ),
        lambda src: _plant(
            src, _TRUNCATED_INIT, "    if len(data) > MAX_HEADER_BYTES:\n        return (), True\n"
        ),
    ],
    ids=["sets-truncated", "returns-true"],
)
def test_a_header_cap_reddens_the_arm(mutate: Callable[[str], str]) -> None:
    """F3's second shape: a cap inside the scanner, invisible to the gate's sites."""
    header = _text(HEADER)
    mutant = mutate(header)
    assert condition_problems(_text(GATE), header) == []
    assert condition_problems(_text(GATE), mutant) != []


def test_a_truncation_the_scan_never_reaches_stays_green() -> None:
    """A `truncated = True` in a header function the gate never calls is not counted."""
    header = _text(HEADER)
    mutant = header + (
        "\n\ndef _cs1105_unreached(data: bytes) -> tuple[tuple[str, ...], bool]:\n"
        "    truncated = False\n"
        "    if len(data) > 1:\n"
        "        truncated = True\n"
        "    return (), truncated\n"
    )
    assert condition_problems(_text(GATE), mutant) == []


def test_a_cap_whose_flag_nothing_reports_stays_green() -> None:
    """A flag that reaches no report is not one of the scan's truncation conditions."""
    gate = _text(GATE)
    mutant = _plant(
        gate, _SCAN_CAPPED, "        if len(candidates) > 8:\n            unrelated = True\n"
    )
    assert condition_problems(mutant, _text(HEADER)) == []


_SCAN_CAP_REPORT = '            "tokens are not matchable",\n            blocking=True,\n'
_HEADER_CALLER_FLAGS = "files_only=True, uncovered_blocks=True"
_SINK_BLOCKS = "    if blocking and report is not None:\n"


@pytest.mark.parametrize(
    ("old", "new", "markers"),
    [
        (
            _SCAN_CAP_REPORT,
            _SCAN_CAP_REPORT.replace("blocking=True", "blocking=False"),
            {"than the scan cap admits"},
        ),
        (
            _HEADER_CALLER_FLAGS,
            "files_only=True, uncovered_blocks=False",
            {"a save directory holds more than", "save files in one save directory; only the"},
        ),
        (_SINK_BLOCKS, "    if False:\n", {case.marker for case in CONDITION_TABLE}),
    ],
    ids=["scan-cap-non-blocking", "token-caller-non-blocking", "sink-never-blocks"],
)
def test_a_truncation_made_non_blocking_reddens_its_case(
    old: str,
    new: str,
    markers: set[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A condition that still truncates but no longer blocks fails its behavioural case.

    Every OTHER case keeps blocking on the same mutant, so the red is the
    mutation's and not the fixture's.
    """
    mutant = load_gate(_swap(_text(GATE), old, new), name="cs1105_gate_mutant")
    try:
        for index, case in enumerate(CONDITION_TABLE):
            status, _reasons = drive(mutant, case.arrange, tmp_path / str(index), monkeypatch)
            expected = 0 if case.marker in markers else 1
            assert status == expected, case.marker
            monkeypatch.undo()
    finally:
        sys.modules.pop("cs1105_gate_mutant", None)
