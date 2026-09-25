#!/usr/bin/env python3
"""CS-817 - a hook whose resolved interpreter cannot import the tools it needs REFUSES.

THE DEFECT. CS-703's probe proves a candidate is a python that runs a program and
reports a failure. It proves nothing about what that python can IMPORT. Measured:
``py -3`` passes the probe and cannot import pytest or ruff - the BOOTSTRAP.md
section 2.5 trap, two installations reporting the same version, one carrying the
toolchain and one not. pre-push already refuses a missing pytest. pre-commit never
checked ruff at all, and ``tools/precommit_gate.py::run_ruff`` answered a missing
ruff with a note - "lint was NOT run and is NOT blocking" - that a passing run
does not even print. So a toolchain-less interpreter silently committed staged
python that no linter ever saw.

THE REPAIR, AND ITS SCOPE (grant G-817, narrowed). Under ``--staged`` only, a
missing ruff is a BLOCKING finding in the gate report that names ruff and the fix.
``--files`` and ``tools/edit_lint_check.py`` keep today's note, so an editor
without ruff is not locked out of every edit. A commit that stages no python
needs no linter and is unaffected.

THE INTERPRETER IS GENUINELY PYTHON AND GENUINELY MISSING THE TOOLS, which is what
the acceptance demands and what a stub could not prove: a virtual environment
created WITHOUT pip, so it carries no third-party package at all, with every PATH
directory that holds a ``ruff`` removed for the refusing arm. The control uses
the SAME environment with ruff's directory put back on PATH, and commits.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE, as in tests/test_hook_probe_bound.py.
"""

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final, NamedTuple

import pytest

from tests.git_env import scrub
from tests.test_hook_probe_bound import (
    ENV_NAME,
    HARNESS_SLACK,
    INSPECT_NAME,
    PRE_COMMIT,
    Environment,
    Sandbox,
    child_env,
    harness_bound,
    head_of,
    make_sandbox,
    run_bounded,
    run_git,
)

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
GATE: Final = REPO_ROOT / "tools" / "precommit_gate.py"
EDIT_LINT_CHECK: Final = REPO_ROOT / "tools" / "edit_lint_check.py"

VENV_TIMEOUT: Final = 300
PROBE_TIMEOUT: Final = 60

# What the gate's refusal must carry: the tool it could not run, its own code,
# and the fix. Pinned here so an arm attributes a refusal to THIS rule.
RUFF_CODE: Final = " RUFF "
RUFF_FIX: Final = "install ruff"
REQUIRE_KEYWORD: Final = "require_ruff"

PYTHON_PAYLOAD: Final = b"VALUE = 1\n"
TEXT_PAYLOAD: Final = b"an ordinary line of 7-bit ascii\n"

DRIVE_PATH: Final = re.compile(r"[A-Za-z]:[\\/]")

RUFF_ON_PATH: Final = shutil.which("ruff")
NO_RUFF_SKIP: Final = (
    "NOT RUN, NOT PASSED: no `ruff` resolves on this process's PATH, so the control "
    "cannot put one back. It makes no claim about whether anything else covers it."
)


class Commit(NamedTuple):
    """One outer-bounded commit, reduced to what an arm may assert on."""

    returncode: int
    killed: bool
    moved: bool
    lines: tuple[str, ...]
    leaked: bool

    @property
    def blocked(self) -> bool:
        """Git refused, nothing was killed, nothing landed."""
        return self.returncode != 0 and not self.killed and not self.moved

    @property
    def accepted(self) -> bool:
        """Git succeeded and the change landed."""
        return self.returncode == 0 and not self.killed and self.moved

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.lines) if self.lines else "(no output)"
        return f"exit={self.returncode} killed={self.killed} moved={self.moved}\n{shown}"


def path_without_ruff(path_value: str) -> str:
    """``path_value`` with every directory that holds a ``ruff`` removed."""
    kept = [d for d in path_value.split(os.pathsep) if d and shutil.which("ruff", path=d) is None]
    return os.pathsep.join(kept)


@pytest.fixture(scope="module")
def bare_python(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A virtual environment created WITHOUT pip: genuinely python, no toolchain."""
    target = tmp_path_factory.mktemp("bare-venv") / "venv"
    made = subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(target)],
        capture_output=True,
        timeout=VENV_TIMEOUT,
        env=scrub(dict(os.environ)),
        check=False,
    )
    assert made.returncode == 0, "the bare virtual environment could not be created"
    python = (
        target
        / ("Scripts" if os.name == "nt" else "bin")
        / ("python.exe" if os.name == "nt" else "python")
    )
    assert python.is_file(), "the bare virtual environment has no interpreter"
    return python


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment with the operator's git configuration excluded."""
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for name in (ENV_NAME, INSPECT_NAME):
        env.pop(name, None)
    return Environment(env)


def runs(python: Path, program: str, path_value: str) -> int:
    """Run ``program`` under ``python`` with ``path_value`` and return its exit code."""
    env = scrub(dict(os.environ))
    env["PATH"] = path_value
    return subprocess.run(
        [str(python), "-c", program],
        capture_output=True,
        timeout=PROBE_TIMEOUT,
        env=env,
        check=False,
    ).returncode


_STAGED: list[int] = [0]


def commit_file(box: Sandbox, env: dict[str, str], suffix: str, content: bytes) -> Commit:
    """Stage a NEW file with ``suffix`` and drive a real, outer-bounded commit."""
    _STAGED[0] += 1
    name = f"staged_{_STAGED[0]}{suffix}"
    (box.work / name).write_bytes(content)
    staged = run_git(box, "add", name, env=env)
    assert staged == 0, "the sandbox change did not stage"
    before = head_of(box, env)
    run = run_bounded(
        ["git", "commit", "-q", "-m", "CS-817: stage one file"],
        box.work,
        env,
        harness_bound() + HARNESS_SLACK,
    )
    moved = head_of(box, env) != before
    python = env.get(ENV_NAME, "")
    leaked = bool(python) and (python in run.stderr or str(Path(python)) in run.stderr)
    lines = tuple(
        line for line in run.stderr.split("\n") if line.strip() and not DRIVE_PATH.search(line)
    )
    return Commit(run.returncode, run.killed, moved, lines, leaked)


def bare_env(box: Sandbox, python: Path, path_value: str) -> dict[str, str]:
    """The sandbox environment naming the bare interpreter under ``path_value``."""
    env = child_env(box, interpreter=python.as_posix())
    env["PATH"] = path_value
    return env


def load_gate() -> ModuleType:
    """Import the gate by file path, as tests/test_precommit_gate.py does."""
    name = "clockspeed_gate_cs817"
    spec = importlib.util.spec_from_file_location(name, GATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --- the preconditions are MEASURED, not assumed ------------------------------


def test_the_bare_interpreter_is_genuinely_python_and_genuinely_missing_the_tools(
    bare_python: Path,
) -> None:
    """The acceptance's own words: genuinely python, genuinely missing them."""
    scrubbed = path_without_ruff(os.environ.get("PATH", ""))
    assert (
        runs(bare_python, "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)", scrubbed)
        == 0
    ), "the bare interpreter is not a working python 3"
    assert runs(bare_python, "import ruff", scrubbed) != 0, "the bare interpreter imports ruff"
    assert runs(bare_python, "import pytest", scrubbed) != 0, "the bare interpreter imports pytest"
    assert shutil.which("ruff", path=scrubbed) is None, "the scrubbed PATH still reaches a ruff"


# --- the refusal, by a real commit --------------------------------------------


def test_staged_python_under_an_interpreter_without_ruff_is_refused(
    tmp_path: Path, isolated: Environment, bare_python: Path
) -> None:
    """CS-817 acceptance. RED before the repair: exit 0, HEAD MOVED, lint never ran."""
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    scrubbed = path_without_ruff(box.env["PATH"])
    outcome = commit_file(box, bare_env(box, bare_python, scrubbed), ".py", PYTHON_PAYLOAD)
    assert outcome.blocked, f"staged python committed with no linter:\n{outcome.report}"
    refusal = [line for line in outcome.lines if RUFF_CODE in line]
    assert len(refusal) == 1, f"blocked, but NOT by the missing-ruff rule:\n{outcome.report}"
    assert RUFF_FIX in refusal[0], f"the refusal does not name the fix:\n{outcome.report}"
    assert not outcome.leaked, "the refusal echoed the interpreter's path"


@pytest.mark.skipif(RUFF_ON_PATH is None, reason=NO_RUFF_SKIP)
def test_control_the_same_interpreter_with_ruff_reachable_commits(
    tmp_path: Path, isolated: Environment, bare_python: Path
) -> None:
    """The control: the SAME bare interpreter, ruff's directory put back on PATH."""
    assert RUFF_ON_PATH is not None
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    scrubbed = path_without_ruff(box.env["PATH"])
    restored = str(Path(RUFF_ON_PATH).parent) + os.pathsep + scrubbed
    outcome = commit_file(box, bare_env(box, bare_python, restored), ".py", PYTHON_PAYLOAD)
    assert outcome.accepted, f"the control was refused with ruff reachable:\n{outcome.report}"


def test_a_commit_staging_no_python_needs_no_linter(
    tmp_path: Path, isolated: Environment, bare_python: Path
) -> None:
    """The scope control: nothing to lint, so a missing linter refuses nothing."""
    box = make_sandbox(tmp_path, isolated, PRE_COMMIT)
    scrubbed = path_without_ruff(box.env["PATH"])
    outcome = commit_file(box, bare_env(box, bare_python, scrubbed), ".txt", TEXT_PAYLOAD)
    assert outcome.accepted, f"a text-only commit was refused:\n{outcome.report}"


# --- the refusal is scoped to --staged ----------------------------------------


def test_files_mode_keeps_the_note_and_does_not_block(tmp_path: Path, bare_python: Path) -> None:
    """Grant condition 7: ``--files`` is unchanged - a note, never a block."""
    target = tmp_path / "edited.py"
    target.write_bytes(PYTHON_PAYLOAD)
    env = scrub(dict(os.environ))
    env["PATH"] = path_without_ruff(env.get("PATH", ""))
    proc = subprocess.run(
        [str(bare_python), str(GATE), "--verbose", "--files", str(target)],
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT,
        env=env,
        check=False,
    )
    noted = "lint was NOT run and is NOT blocking" in proc.stdout
    assert proc.returncode == 0, "--files blocked on a missing ruff; only --staged may"
    assert noted, "--files no longer carries today's missing-ruff note"


def test_run_ruff_refuses_only_when_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    """The keyword's default keeps today's behaviour; passing it makes the block."""
    gate = load_gate()
    monkeypatch.setattr(gate, "ruff_command", lambda: None)
    unit = gate.Unit(label="staged.py", origin="index", data=PYTHON_PAYLOAD, ext=".py")

    default = gate.Report()
    gate.run_ruff([unit], default, None)
    assert default.diagnostics == [], "the default now blocks, so --files and editors lock out"
    assert any("NOT blocking" in note for note in default.notes), "the default lost its note"

    asked = gate.Report()
    gate.run_ruff([unit], asked, None, require_ruff=True)
    codes = [diag.code for diag in asked.diagnostics]
    assert codes == ["RUFF"], f"asked to require ruff, the gate recorded {codes}"


def test_only_the_staged_call_site_requires_ruff() -> None:
    """Grant condition 7, by the call sites: main passes it, edit_lint_check never does."""
    gate_tree = ast.parse(GATE.read_bytes().decode("ascii"))
    lint_tree = ast.parse(EDIT_LINT_CHECK.read_bytes().decode("ascii"))

    def keyword_sites(tree: ast.AST) -> list[ast.Call]:
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and any(kw.arg == REQUIRE_KEYWORD for kw in node.keywords)
        ]

    main = next(
        node
        for node in ast.walk(gate_tree)
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    in_main = keyword_sites(main)
    assert len(in_main) == 1, f"main passes {REQUIRE_KEYWORD} at {len(in_main)} sites, not 1"
    assert len(keyword_sites(gate_tree)) == 1, "the gate passes the keyword outside main"
    assert keyword_sites(lint_tree) == [], "edit_lint_check now requires ruff"
