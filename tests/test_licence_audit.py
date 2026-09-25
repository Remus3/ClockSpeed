"""CS-1185 - every dependency carries a licence verdict, and the set is DERIVED.

WHAT THIS GRADES. ``tools/licence_audit.py`` derives the dependency set from the
two manifests - the Python closure of ``pyproject.toml``'s runtime list and
every extra, walked through the installed metadata of the running environment,
and every package ``shell/package-lock.json`` pins - and compares it with the
rows of ``THIRD_PARTY.md``'s dependency verdicts section. Neither side is a hand
list held in this module: the register is read from the file and the set is
read from the manifests, so a dependency added to either manifest reaches the
graded population the moment it lands.

THE CONTROL IS THE REAL TREE, IN EVERY CLI RED ARM'S OWN RUN. Each arm that
drives the CLI builds a temp copy of the four inputs, proves the UNMUTATED copy
exits 0, and only then plants its defect and asserts the red exit. An arm that
went red on a copy the audit could not read at all would be measuring the
copier, not the audit. The in-process arms inject a fake installed-metadata
lookup instead; of those, the transitive arm first asserts the same copy clean
under the same lookup, and the others carry no such control.

THE PLANTS LIVE IN TEMP COPIES, NEVER IN THE TRACKED FILES. Nothing here writes
to ``pyproject.toml``, the lockfile or the register in the tree.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SOURCE = REPO_ROOT / "tools" / "licence_audit.py"
REGISTER_NAME = "THIRD_PARTY.md"
ELECTRON_ADR = "docs/adr/0013-electron-licence-gate.md"

#: The four inputs the audit reads, as repo-relative paths.
INPUTS = ("pyproject.toml", "shell/package.json", "shell/package-lock.json", REGISTER_NAME)

#: Seconds a single audit subprocess may take. It reads four small files and a
#: few dozen installed METADATA records, so this bounds a hang, not a workload.
AUDIT_TIMEOUT = 120

SYNTHETIC_DIRECT = "zz-synthetic-undeclared"
SYNTHETIC_PARENT = "zz-synthetic-parent"
SYNTHETIC_CHILD = "zz-synthetic-child"

EXIT_CLEAN = 0
EXIT_MISMATCH = 1
EXIT_COULD_NOT_RUN = 2

COUNTS_RE = re.compile(
    r"python derived (\d+), recorded (\d+); node derived (\d+), recorded (\d+); findings (\d+)"
)


def _load_audit() -> ModuleType:
    """Import ``tools/licence_audit.py`` by path.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_licence_audit", AUDIT_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {AUDIT_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Run:
    """One audit subprocess: its exit code and its combined output."""

    code: int
    output: str


def _run(root: Path) -> Run:
    """Run the audit CLI against ``root`` in a fresh interpreter.

    Args:
        root: A directory laid out like the repository's four inputs.

    Returns:
        The exit code and the combined stdout and stderr.
    """
    completed = subprocess.run(
        [sys.executable, "-B", str(AUDIT_SOURCE), "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=AUDIT_TIMEOUT,
        check=False,
    )
    return Run(completed.returncode, completed.stdout + completed.stderr)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Copy the four real inputs into a temp root with the repository layout.

    Returns:
        The temp root.
    """
    for relative in INPUTS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, target)
    return tmp_path


def _control(root: Path) -> None:
    """Assert the unmutated copy passes, so a later red is the plant's doing."""
    run = _run(root)
    assert run.code == EXIT_CLEAN, f"the unmutated copy did not pass: {run.output}"


def _edit(path: Path, old: str, new: str) -> None:
    """Replace exactly one occurrence of ``old`` in ``path``, asserting it landed."""
    text = path.read_bytes().decode("ascii")
    assert text.count(old) == 1, f"plant anchor {old!r} is not unique in {path.name}"
    path.write_bytes(text.replace(old, new).encode("ascii"))


def _table_rows(text: str, heading: str) -> list[str]:
    """Return the body lines of the first table under ``heading``."""
    section = text.split(heading, 1)[1]
    rows: list[str] = []
    for line in section.splitlines():
        if line.startswith("|"):
            rows.append(line)
        elif rows:
            break
    return rows[2:]


def _insert_row(register: Path, heading: str, row: str) -> None:
    """Insert ``row`` as the first body row of the table under ``heading``."""
    text = register.read_bytes().decode("ascii")
    first = _table_rows(text, heading)[0]
    _edit(register, first + "\n", row + "\n" + first + "\n")


PYTHON_HEADING = "### Python dependencies"
NODE_HEADING = "### Node dependencies"


# --- the control ------------------------------------------------------------


def test_the_real_tree_passes_the_audit() -> None:
    run = _run(REPO_ROOT)
    assert run.code == EXIT_CLEAN, run.output
    counts = COUNTS_RE.search(run.output)
    assert counts is not None, f"the audit printed no count line: {run.output}"
    py_derived, py_recorded, node_derived, node_recorded, findings = map(int, counts.groups())
    # Anti-vacuity: an audit that derived nothing would match an empty register.
    assert py_derived > 0, "the Python derivation found nothing, so it graded nothing"
    assert node_derived > 0, "the lockfile derivation found nothing, so it graded nothing"
    assert (py_derived, node_derived, findings) == (py_recorded, node_recorded, 0)


def test_the_audit_prints_counts_and_never_licence_text() -> None:
    run = _run(REPO_ROOT)
    leaked = [
        pattern
        for pattern in (r"permission is hereby granted", r"\bas is\b", r"copyright", r"warrant")
        if re.search(pattern, run.output, re.IGNORECASE)
    ]
    assert leaked == [], f"the audit output carries licence text: {leaked}"


# --- the red arms: an undeclared dependency ---------------------------------


def test_a_synthetic_undeclared_python_dependency_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(
        tree / "pyproject.toml",
        '  "mypy>=1.11",\n',
        f'  "mypy>=1.11",\n  "{SYNTHETIC_DIRECT}>=1",\n',
    )
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert SYNTHETIC_DIRECT in run.output


def test_a_synthetic_undeclared_runtime_dependency_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(
        tree / "pyproject.toml", "dependencies = []\n", f'dependencies = ["{SYNTHETIC_DIRECT}"]\n'
    )
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert SYNTHETIC_DIRECT in run.output


@dataclass(frozen=True)
class FakeDist:
    """The two attributes of an installed distribution the audit reads."""

    version: str
    requires: list[str]


def test_a_synthetic_undeclared_transitive_python_dependency_goes_red(tree: Path) -> None:
    audit = _load_audit()
    real_lookup = audit.installed

    def lookup(name: str) -> object:
        fakes = {
            SYNTHETIC_PARENT: FakeDist("1.0", [SYNTHETIC_CHILD]),
            SYNTHETIC_CHILD: FakeDist("1.0", []),
        }
        return fakes[name] if name in fakes else real_lookup(name)

    assert audit.exit_code(audit.audit(tree, lookup)) == EXIT_CLEAN
    _edit(
        tree / "pyproject.toml", '  "mypy>=1.11",\n', f'  "mypy>=1.11",\n  "{SYNTHETIC_PARENT}",\n'
    )
    _insert_row(
        tree / REGISTER_NAME,
        PYTHON_HEADING,
        f"| `{SYNTHETIC_PARENT}` | 1.0 | `always` | MIT / MIT | Copyright (c) synthetic "
        "| **CLEARED** synthetic | 2026-09-25 |",
    )
    result = audit.audit(tree, lookup)
    assert audit.exit_code(result) == EXIT_MISMATCH
    joined = "\n".join(result.findings)
    assert SYNTHETIC_CHILD in joined
    assert SYNTHETIC_PARENT not in joined, "the recorded parent was reported as a finding"


SYNTHETIC_MANIFEST = '[project]\ndependencies = ["zz-root"]\n'
TRUE_HERE = 'python_version >= "3"'
FALSE_HERE = 'sys_platform == "zz-no-such-platform"'


def test_a_condition_is_conjoined_down_a_path_and_disjoined_across_paths() -> None:
    audit = _load_audit()
    graph = {
        "zz-root": FakeDist(
            "1.0",
            [
                f"zz-parent; {TRUE_HERE}",
                "zz-always",
                f"zz-always; {FALSE_HERE}",
                f"zz-both; {FALSE_HERE}",
                'zz-extra-only; extra == "zz"',
            ],
        ),
        "zz-parent": FakeDist("1.0", ["zz-child; sys_platform != 'zz'", "zz-both"]),
        "zz-child": FakeDist("1.0", []),
        "zz-always": FakeDist("1.0", []),
        "zz-both": FakeDist("1.0", []),
    }
    derivation = audit.derive_python(SYNTHETIC_MANIFEST, graph.get)
    assert derivation.conditions == {
        "zz-root": "always",
        "zz-parent": TRUE_HERE,
        "zz-child": f'({TRUE_HERE}) and (sys_platform != "zz")',
        "zz-always": "always",
        "zz-both": f"({TRUE_HERE}) or ({FALSE_HERE})",
    }
    assert derivation.members == set(derivation.conditions)
    assert derivation.incomplete == []


def test_a_cycle_of_conditional_edges_is_refused_rather_than_walked_forever() -> None:
    audit = _load_audit()
    graph = {
        "zz-root": FakeDist("1.0", [f"zz-a; {TRUE_HERE}"]),
        "zz-a": FakeDist("1.0", [f"zz-b; {TRUE_HERE}"]),
        "zz-b": FakeDist("1.0", [f"zz-a; {TRUE_HERE}"]),
    }
    with pytest.raises(audit.AuditError, match="did not converge"):
        audit.derive_python(SYNTHETIC_MANIFEST, graph.get)


def test_a_synthetic_undeclared_lockfile_package_goes_red(tree: Path) -> None:
    _control(tree)
    lock_path = tree / "shell" / "package-lock.json"
    lock = json.loads(lock_path.read_bytes())
    lock["packages"][f"node_modules/{SYNTHETIC_DIRECT}"] = {"version": "1.0.0", "dev": True}
    lock_path.write_bytes(json.dumps(lock, indent=2).encode("ascii"))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert SYNTHETIC_DIRECT in run.output


def test_a_nested_lockfile_package_is_derived_by_its_own_name(tree: Path) -> None:
    _control(tree)
    lock_path = tree / "shell" / "package-lock.json"
    lock = json.loads(lock_path.read_bytes())
    key = f"node_modules/electron/node_modules/@zz/{SYNTHETIC_CHILD}"
    lock["packages"][key] = {"version": "1.0.0", "dev": True}
    lock_path.write_bytes(json.dumps(lock, indent=2).encode("ascii"))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    # Backticked, so a name that kept its parent's path cannot match.
    assert f"`@zz/{SYNTHETIC_CHILD}`" in run.output


def test_a_package_json_dependency_absent_from_the_lock_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(
        tree / "shell" / "package.json",
        '"electron": "44.0.0"',
        f'"electron": "44.0.0",\n    "{SYNTHETIC_DIRECT}": "1.0.0"',
    )
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert SYNTHETIC_DIRECT in run.output


# --- the red arms: a register row that is wrong -----------------------------


SYNTHETIC_ROWS = {
    PYTHON_HEADING: (
        f"| `{SYNTHETIC_DIRECT}` | 1.0 | `always` | MIT / MIT | Copyright (c) synthetic "
        "| **CLEARED** synthetic | 2026-09-25 |"
    ),
    NODE_HEADING: (
        f"| `{SYNTHETIC_DIRECT}` | 1.0.0 | MIT / MIT | Copyright (c) synthetic "
        "| **CLEARED** synthetic | 2026-09-25 |"
    ),
}


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_register_row_naming_no_dependency_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    _insert_row(tree / REGISTER_NAME, heading, SYNTHETIC_ROWS[heading])
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{SYNTHETIC_DIRECT}` has a register row and is no dependency" in run.output


def test_a_missing_register_row_goes_red(tree: Path) -> None:
    _control(tree)
    register = tree / REGISTER_NAME
    victim = next(
        row
        for row in _table_rows(register.read_bytes().decode("ascii"), PYTHON_HEADING)
        if row.startswith("| `pytest` ")
    )
    _edit(register, victim + "\n", "")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "`pytest`" in run.output


def test_a_duplicated_register_row_goes_red(tree: Path) -> None:
    _control(tree)
    register = tree / REGISTER_NAME
    victim = _table_rows(register.read_bytes().decode("ascii"), NODE_HEADING)[0]
    _edit(register, victim + "\n", victim + "\n" + victim + "\n")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "more than once" in run.output


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_row_without_a_cleared_verdict_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    register = tree / REGISTER_NAME
    victim = _table_rows(register.read_bytes().decode("ascii"), heading)[0]
    _edit(register, victim, victim.replace("**CLEARED", "**PENDING", 1))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "verdict" in run.output


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_row_without_a_copyright_line_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    register = tree / REGISTER_NAME
    victim = _table_rows(register.read_bytes().decode("ascii"), heading)[0]
    cells = victim.split("|")
    # Column 5 of a Python row and column 4 of a node row is the copyright line.
    index = 5 if heading == PYTHON_HEADING else 4
    cells[index] = " read "
    _edit(register, victim, "|".join(cells))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "copyright" in run.output


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_row_without_a_date_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    register = tree / REGISTER_NAME
    victim = _table_rows(register.read_bytes().decode("ascii"), heading)[0]
    cells = victim.split("|")
    cells[-2] = " - "
    _edit(register, victim, "|".join(cells))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "date" in run.output


def test_a_node_row_at_a_stale_version_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(tree / REGISTER_NAME, "| `electron` | 44.0.0 |", "| `electron` | 43.0.0 |")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "`electron`" in run.output


def test_a_wrong_reached_when_condition_goes_red(tree: Path) -> None:
    _control(tree)
    register = tree / REGISTER_NAME
    victim = next(
        row
        for row in _table_rows(register.read_bytes().decode("ascii"), PYTHON_HEADING)
        if row.startswith("| `pytest` ")
    )
    _edit(register, victim, victim.replace("`always`", '`python_version >= "3"`', 1))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "`pytest`" in run.output


def test_a_row_condition_false_here_is_not_expected_here(tree: Path) -> None:
    # The environment-dependence arm, proven in the direction CI needs: a
    # platform-gated row whose marker is false in this interpreter is neither
    # required nor reported as stale, provided its marker is the derived one.
    audit = _load_audit()
    real_lookup = audit.installed

    def lookup(name: str) -> object:
        if name == "pytest":
            real = real_lookup(name)
            gated = [f'{SYNTHETIC_CHILD}; sys_platform == "zz-no-such-platform"']
            return FakeDist(real.version, [*real.requires, *gated])
        return real_lookup(name)

    _insert_row(
        tree / REGISTER_NAME,
        PYTHON_HEADING,
        f'| `{SYNTHETIC_CHILD}` | 1.0 | `sys_platform == "zz-no-such-platform"` | MIT / MIT '
        "| Copyright (c) synthetic | **CLEARED** synthetic | 2026-09-25 |",
    )
    result = audit.audit(tree, lookup)
    assert result.findings == []
    assert audit.exit_code(result) == EXIT_CLEAN


# --- could not run -----------------------------------------------------------


@pytest.mark.parametrize("victim", INPUTS)
def test_a_missing_input_exits_could_not_run(tree: Path, victim: str) -> None:
    _control(tree)
    (tree / victim).unlink()
    run = _run(tree)
    assert run.code == EXIT_COULD_NOT_RUN, run.output


def test_a_register_without_the_verdicts_section_exits_could_not_run(tree: Path) -> None:
    _control(tree)
    _edit(tree / REGISTER_NAME, PYTHON_HEADING + "\n", "### Python deps\n")
    run = _run(tree)
    assert run.code == EXIT_COULD_NOT_RUN, run.output


def test_an_applicable_requirement_not_installed_is_incomplete_not_clean(tree: Path) -> None:
    # A recorded direct dependency whose metadata is absent cannot be walked,
    # so its children are unseen: the audit must not call that clean.
    audit = _load_audit()
    real_lookup = audit.installed

    def lookup(name: str) -> object:
        return None if name == "pytest-xdist" else real_lookup(name)

    result = audit.audit(tree, lookup)
    assert audit.exit_code(result) == EXIT_COULD_NOT_RUN
    assert "pytest-xdist" in result.incomplete


# --- the register's own content ----------------------------------------------


def test_the_electron_row_consumes_adr_0013() -> None:
    text = (REPO_ROOT / REGISTER_NAME).read_bytes().decode("ascii")
    rows = [row for row in _table_rows(text, NODE_HEADING) if row.startswith("| `electron` ")]
    assert len(rows) == 1, "the register carries no single electron row"
    assert ELECTRON_ADR in rows[0], "the electron row does not cite ADR 0013"
    assert (REPO_ROOT / ELECTRON_ADR).is_file()
