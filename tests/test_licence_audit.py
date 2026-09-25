"""CS-1185 - every dependency carries a licence verdict, and the set is DERIVED.

WHAT THIS GRADES. ``tools/licence_audit.py`` derives the dependency set from the
two manifests - the Python closure of ``pyproject.toml``'s runtime list and
every extra, walked through installed metadata, and every package
``shell/package-lock.json`` pins - and compares it with the rows of
``THIRD_PARTY.md``'s dependency verdicts section. Neither side is a hand list
held in the tool.

DETERMINISM IS THE SHAPE OF THIS MODULE, and the split is deliberate. The
Python set depends on whatever is installed, and CI installs the dev extra
unpinned, so an arm that graded the LIVE environment exactly went red on an
older allowed pytest or mypy with nothing wrong in the tree. So:

- Every logic arm runs over a SYNTHETIC tree and a SYNTHETIC environment: the
  CLI is handed a ``--metadata`` map, or the library an injected lookup. Those
  arms mean the same thing on every machine.
- The REAL register is graded only where it is deterministic: its rows are
  complete, its node table equals the tracked lockfile, and Electron's row cites
  ADR 0013.
- ONE live arm runs the CLI against the running environment and asserts only
  that every package it derives is either recorded or REPORTED as a finding. It
  never goes red on version drift; the live verdict is the CLI's exit code, run
  by the merger or CI.

THE CONTROL IS IN EVERY CLI RED ARM'S OWN RUN: the unmutated synthetic copy is
proven clean first, so a red is the plant's doing and not the copier's.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SOURCE = REPO_ROOT / "tools" / "licence_audit.py"
REGISTER_NAME = "THIRD_PARTY.md"
PYPROJECT = "pyproject.toml"
PACKAGE_JSON = "shell/package.json"
LOCKFILE = "shell/package-lock.json"
METADATA = "metadata.json"
ELECTRON_ADR = "docs/adr/0013-electron-licence-gate.md"

#: Seconds a single audit subprocess may take. It reads a handful of small
#: files and installed METADATA records, so this bounds a hang, not a workload.
AUDIT_TIMEOUT = 120

EXIT_CLEAN = 0
EXIT_MISMATCH = 1
EXIT_COULD_NOT_RUN = 2

PYTHON_HEADING = "### Python dependencies"
NODE_HEADING = "### Node dependencies"

TRUE_HERE = 'python_version >= "3"'
FALSE_HERE = 'sys_platform == "zz-no-such-platform"'
UNDECLARED = "zz-undeclared"

COUNTS_RE = re.compile(
    r"python derived (\d+), recorded (\d+); node derived (\d+), recorded (\d+); "
    r"findings (\d+); notes (\d+)"
)

# --- the synthetic tree -------------------------------------------------------

SYNTHETIC_PYPROJECT = """[project]
name = "zz-synthetic"
dependencies = []

[project.optional-dependencies]
dev = [
  "zz-tool>=1",
  "zz-runner",
]
"""

SYNTHETIC_METADATA = {
    "zz-tool": {
        "version": "1.0",
        "requires": [
            "zz-lib",
            f"zz-cond; {TRUE_HERE}",
            f"zz-never; {FALSE_HERE}",
            'zz-extra-only; extra == "zz"',
        ],
    },
    "zz-runner": {"version": "2.0", "requires": ["zz-tool"]},
    "zz-lib": {"version": "3.0", "requires": []},
    "zz-cond": {"version": "4.0", "requires": []},
}

SYNTHETIC_PACKAGE_JSON = {"name": "zz", "private": True, "devDependencies": {"zz-shell": "1.0.0"}}

SYNTHETIC_LOCK = {
    "lockfileVersion": 3,
    "packages": {
        "": {"name": "zz", "devDependencies": {"zz-shell": "1.0.0"}},
        "node_modules/zz-shell": {"version": "1.0.0", "dev": True},
        "node_modules/@zz/scoped": {"version": "2.0.0", "dev": True},
    },
}

ROW_TAIL = "| MIT / MIT | Copyright (c) synthetic | **CLEARED** synthetic | 2026-09-25 |"

SYNTHETIC_REGISTER = f"""# Synthetic register

## Dependency licence verdicts

{PYTHON_HEADING}

| Package | Version read | Reached when | Licence read | Copyright line | Verdict | Date |
|---|---|---|---|---|---|---|
| `zz-cond` | 4.0 | `{TRUE_HERE}` {ROW_TAIL}
| `zz-lib` | 3.0 | `always` {ROW_TAIL}
| `zz-never` | 5.0 | `{FALSE_HERE}` {ROW_TAIL}
| `zz-runner` | 2.0 | `always` {ROW_TAIL}
| `zz-tool` | 1.0 | `always` {ROW_TAIL}

{NODE_HEADING}

| Package | Version read | Licence read | Copyright line | Verdict | Date |
|---|---|---|---|---|---|
| `@zz/scoped` | 2.0.0 {ROW_TAIL}
| `zz-shell` | 1.0.0 {ROW_TAIL}

## After the section
"""


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


def _run(root: Path, *, synthetic: bool = True) -> Run:
    """Run the audit CLI against ``root`` in a fresh interpreter.

    Args:
        root: A directory laid out like the repository's inputs.
        synthetic: Hand the CLI ``root``'s metadata map instead of the real
            installed environment.

    Returns:
        The exit code and the combined stdout and stderr.
    """
    argv = [sys.executable, "-B", str(AUDIT_SOURCE), "--root", str(root)]
    if synthetic:
        argv += ["--metadata", str(root / METADATA)]
    completed = subprocess.run(
        argv, capture_output=True, text=True, timeout=AUDIT_TIMEOUT, check=False
    )
    return Run(completed.returncode, completed.stdout + completed.stderr)


def _write_json(path: Path, data: object) -> None:
    path.write_bytes(json.dumps(data, indent=2).encode("ascii"))


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Lay out the synthetic tree and its synthetic environment.

    Returns:
        The temp root.
    """
    (tmp_path / "shell").mkdir()
    (tmp_path / PYPROJECT).write_bytes(SYNTHETIC_PYPROJECT.encode("ascii"))
    (tmp_path / REGISTER_NAME).write_bytes(SYNTHETIC_REGISTER.encode("ascii"))
    _write_json(tmp_path / PACKAGE_JSON, SYNTHETIC_PACKAGE_JSON)
    _write_json(tmp_path / LOCKFILE, SYNTHETIC_LOCK)
    _write_json(tmp_path / METADATA, SYNTHETIC_METADATA)
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


def _edit_json(path: Path, change: Callable[[Any], object]) -> None:
    """Load ``path``, apply ``change`` to the decoded object, and write it back."""
    data = json.loads(path.read_bytes())
    change(data)
    _write_json(path, data)


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


def _row_of(register: Path, heading: str, name: str) -> str:
    """Return the one row under ``heading`` naming ``name``."""
    rows = _table_rows(register.read_bytes().decode("ascii"), heading)
    matches = [row for row in rows if row.startswith(f"| `{name}` ")]
    assert len(matches) == 1, f"no single {name!r} row under {heading!r}"
    return matches[0]


# --- the synthetic control -----------------------------------------------------


def test_the_synthetic_tree_is_clean_and_counted(tree: Path) -> None:
    run = _run(tree)
    assert run.code == EXIT_CLEAN, run.output
    counts = COUNTS_RE.search(run.output)
    assert counts is not None, f"the audit printed no count line: {run.output}"
    # zz-never is recorded under a condition false everywhere, so it is neither
    # derived here nor counted as recorded here, and it is not a note either.
    assert tuple(map(int, counts.groups())) == (4, 4, 2, 2, 0, 0)
    assert "`zz-never`" not in run.output


def test_the_audit_prints_counts_and_never_licence_text() -> None:
    run = _run(REPO_ROOT, synthetic=False)
    leaked = [
        pattern
        for pattern in (r"permission is hereby granted", r"\bas is\b", r"copyright", r"warrant")
        if re.search(pattern, run.output, re.IGNORECASE)
    ]
    assert leaked == [], f"the audit output carries licence text: {leaked}"


# --- red: a dependency with no verdict row ---------------------------------------


def test_a_synthetic_undeclared_dev_dependency_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(tree / PYPROJECT, '  "zz-runner",\n', f'  "zz-runner",\n  "{UNDECLARED}>=1",\n')
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{UNDECLARED}` is a dependency here and has no register row" in run.output


def test_a_synthetic_undeclared_runtime_dependency_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(tree / PYPROJECT, "dependencies = []\n", f'dependencies = ["{UNDECLARED}"]\n')
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{UNDECLARED}` is a dependency here and has no register row" in run.output


def test_a_newly_installed_transitive_package_without_a_verdict_goes_red(tree: Path) -> None:
    _control(tree)

    def plant(data: Any) -> None:
        data["zz-lib"]["requires"] = [UNDECLARED]
        data[UNDECLARED] = {"version": "9.0", "requires": []}

    _edit_json(tree / METADATA, plant)
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{UNDECLARED}` is a dependency here and has no register row" in run.output
    assert "`zz-lib`" not in run.output, "the recorded parent was reported"


def test_a_synthetic_undeclared_lockfile_package_goes_red(tree: Path) -> None:
    _control(tree)

    def plant(data: Any) -> None:
        data["packages"][f"node_modules/{UNDECLARED}"] = {"version": "1.0.0"}

    _edit_json(tree / LOCKFILE, plant)
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{UNDECLARED}` is pinned by the lockfile and has no register row" in run.output


def test_a_nested_lockfile_package_is_derived_by_its_own_name(tree: Path) -> None:
    _control(tree)

    def plant(data: Any) -> None:
        data["packages"][f"node_modules/zz-shell/node_modules/@zz/{UNDECLARED}"] = {
            "version": "1.0.0"
        }

    _edit_json(tree / LOCKFILE, plant)
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    # Backticked, so a name that kept its parent's path cannot match.
    assert f"`@zz/{UNDECLARED}`" in run.output


def test_a_package_json_dependency_absent_from_the_lock_goes_red(tree: Path) -> None:
    _control(tree)

    def plant(data: Any) -> None:
        data["devDependencies"][UNDECLARED] = "1.0.0"

    _edit_json(tree / PACKAGE_JSON, plant)
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{UNDECLARED}` is declared in" in run.output


# --- the register rows: deterministic findings, and python drift as notes ---------


def test_a_node_row_naming_no_pinned_package_goes_red(tree: Path) -> None:
    _control(tree)
    anchor = _row_of(tree / REGISTER_NAME, NODE_HEADING, "zz-shell")
    _edit(tree / REGISTER_NAME, anchor, f"| `{UNDECLARED}` | 1.0.0 {ROW_TAIL}\n{anchor}")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"node: `{UNDECLARED}` has a register row and is no dependency" in run.output


def test_a_python_row_not_reached_here_is_a_note_and_not_a_failure(tree: Path) -> None:
    _control(tree)
    anchor = _row_of(tree / REGISTER_NAME, PYTHON_HEADING, "zz-lib")
    _edit(tree / REGISTER_NAME, anchor, f"| `{UNDECLARED}` | 1.0 | `always` {ROW_TAIL}\n{anchor}")
    run = _run(tree)
    assert run.code == EXIT_CLEAN, run.output
    assert f"note: python: `{UNDECLARED}` has a register row and is not reached here" in run.output


def test_a_python_row_whose_package_dropped_out_is_a_note_not_a_failure(tree: Path) -> None:
    # The measured drift: an older allowed release that no longer requires a
    # recorded transitive package.
    _control(tree)

    def drop(data: Any) -> None:
        data["zz-tool"]["requires"] = [f"zz-cond; {TRUE_HERE}", f"zz-never; {FALSE_HERE}"]
        del data["zz-lib"]

    _edit_json(tree / METADATA, drop)
    run = _run(tree)
    assert run.code == EXIT_CLEAN, run.output
    assert "note: python: `zz-lib` has a register row and is not reached here" in run.output


def test_a_python_row_under_another_condition_is_a_note_not_a_failure(tree: Path) -> None:
    _control(tree)
    row = _row_of(tree / REGISTER_NAME, PYTHON_HEADING, "zz-lib")
    _edit(tree / REGISTER_NAME, row, row.replace("`always`", f"`{TRUE_HERE}`", 1))
    run = _run(tree)
    assert run.code == EXIT_CLEAN, run.output
    assert "note: python: `zz-lib` is reached here when `always`, not as recorded" in run.output


def test_a_missing_python_row_goes_red(tree: Path) -> None:
    _control(tree)
    row = _row_of(tree / REGISTER_NAME, PYTHON_HEADING, "zz-tool")
    _edit(tree / REGISTER_NAME, row + "\n", "")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "`zz-tool` is a dependency here and has no register row" in run.output


def test_a_duplicated_register_row_goes_red(tree: Path) -> None:
    _control(tree)
    row = _row_of(tree / REGISTER_NAME, NODE_HEADING, "zz-shell")
    _edit(tree / REGISTER_NAME, row + "\n", row + "\n" + row + "\n")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "`zz-shell` is recorded more than once" in run.output


VICTIMS = {PYTHON_HEADING: "zz-lib", NODE_HEADING: "zz-shell"}


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_row_without_a_cleared_verdict_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    row = _row_of(tree / REGISTER_NAME, heading, VICTIMS[heading])
    _edit(tree / REGISTER_NAME, row, row.replace("**CLEARED", "**PENDING", 1))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{VICTIMS[heading]}` carries no CLEARED verdict" in run.output


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_row_without_a_copyright_line_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    row = _row_of(tree / REGISTER_NAME, heading, VICTIMS[heading])
    _edit(tree / REGISTER_NAME, row, row.replace("Copyright (c) synthetic", "read", 1))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{VICTIMS[heading]}` records no copyright line" in run.output


@pytest.mark.parametrize("heading", [PYTHON_HEADING, NODE_HEADING])
def test_a_row_without_a_date_goes_red(tree: Path, heading: str) -> None:
    _control(tree)
    row = _row_of(tree / REGISTER_NAME, heading, VICTIMS[heading])
    _edit(tree / REGISTER_NAME, row, row.replace("2026-09-25", "-", 1))
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert f"`{VICTIMS[heading]}` carries no YYYY-MM-DD date" in run.output


def test_a_node_row_at_a_stale_version_goes_red(tree: Path) -> None:
    _control(tree)
    _edit(tree / REGISTER_NAME, "| `zz-shell` | 1.0.0 ", "| `zz-shell` | 0.9.0 ")
    run = _run(tree)
    assert run.code == EXIT_MISMATCH, run.output
    assert "`zz-shell` is pinned at 1.0.0" in run.output


# --- could not run ---------------------------------------------------------------


@pytest.mark.parametrize("victim", [PYPROJECT, PACKAGE_JSON, LOCKFILE, REGISTER_NAME, METADATA])
def test_a_missing_input_exits_could_not_run(tree: Path, victim: str) -> None:
    _control(tree)
    (tree / victim).unlink()
    run = _run(tree)
    assert run.code == EXIT_COULD_NOT_RUN, run.output
    assert "could not run" in run.output


def test_a_register_without_the_python_table_exits_could_not_run(tree: Path) -> None:
    _control(tree)
    _edit(tree / REGISTER_NAME, PYTHON_HEADING + "\n", "### Python deps\n")
    run = _run(tree)
    assert run.code == EXIT_COULD_NOT_RUN, run.output


def test_an_applicable_package_not_installed_is_incomplete_not_clean(tree: Path) -> None:
    _control(tree)
    _edit_json(tree / METADATA, lambda data: data.pop("zz-runner"))
    run = _run(tree)
    assert run.code == EXIT_COULD_NOT_RUN, run.output
    assert "`zz-runner` applies here and is not installed" in run.output


# --- the walk, over injected metadata ----------------------------------------------


@dataclass(frozen=True)
class FakeDist:
    """The two attributes of an installed distribution the audit reads."""

    version: str
    requires: list[str]


SYNTHETIC_MANIFEST = '[project]\ndependencies = ["zz-root"]\n'


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


def test_a_requested_extra_is_refused_rather_than_walked_without_its_extras() -> None:
    audit = _load_audit()
    graph = {"zz-root": FakeDist("1.0", ["zz-lib[fast]"]), "zz-lib": FakeDist("1.0", [])}
    with pytest.raises(audit.AuditError, match="requested extras are not modelled"):
        audit.derive_python(SYNTHETIC_MANIFEST, graph.get)


def test_an_extra_marker_that_holds_with_no_extra_is_refused() -> None:
    audit = _load_audit()
    graph = {
        "zz-root": FakeDist("1.0", [f'zz-lib; extra == "zz" or {TRUE_HERE}']),
        "zz-lib": FakeDist("1.0", []),
    }
    with pytest.raises(audit.AuditError, match="holds with no extra"):
        audit.derive_python(SYNTHETIC_MANIFEST, graph.get)


# --- the real register, where it is deterministic -----------------------------------


def test_the_real_register_rows_are_complete_and_the_node_table_matches_the_lock() -> None:
    audit = _load_audit()
    text = (REPO_ROOT / REGISTER_NAME).read_bytes().decode("ascii").replace("\r\n", "\n")
    python_rows, node_rows, malformed = audit.parse_register(text)
    node = audit.derive_node(
        (REPO_ROOT / PACKAGE_JSON).read_bytes().decode("utf-8"),
        (REPO_ROOT / LOCKFILE).read_bytes().decode("utf-8"),
    )
    assert python_rows, "the real register's Python table is empty"
    assert node.versions, "the real lockfile pins nothing, so this arm graded nothing"
    findings = [
        *malformed,
        *audit.row_findings("python", python_rows),
        *audit.row_findings("node", node_rows),
        *audit.node_findings(node, node_rows),
    ]
    assert findings == []


def test_the_electron_row_consumes_adr_0013() -> None:
    text = (REPO_ROOT / REGISTER_NAME).read_bytes().decode("ascii")
    rows = [row for row in _table_rows(text, NODE_HEADING) if row.startswith("| `electron` ")]
    assert len(rows) == 1, "the register carries no single electron row"
    assert ELECTRON_ADR in rows[0], "the electron row does not cite ADR 0013"
    assert (REPO_ROOT / ELECTRON_ADR).is_file()


# --- the ONE live arm ------------------------------------------------------------------


def test_every_package_the_running_environment_derives_is_recorded_or_reported() -> None:
    # Never red on drift: a package the environment adds is REPORTED by the CLI,
    # and one it drops is a note. Red only if the audit could not run at all, or
    # derived a package and then neither recorded nor reported it.
    audit = _load_audit()
    run = _run(REPO_ROOT, synthetic=False)
    assert COUNTS_RE.search(run.output), f"the live audit did not run: {run.output}"
    derivation = audit.derive_python((REPO_ROOT / PYPROJECT).read_text("utf-8"), audit.installed)
    assert derivation.members, "the live environment derived nothing, so this arm graded nothing"
    text = (REPO_ROOT / REGISTER_NAME).read_bytes().decode("ascii").replace("\r\n", "\n")
    recorded = {row.name for row in audit.parse_register(text)[0]}
    silent = sorted(
        name
        for name in derivation.members - recorded
        if f"`{name}` is a dependency here and has no register row" not in run.output
    )
    assert silent == [], f"derived, unrecorded and unreported: {silent}"
