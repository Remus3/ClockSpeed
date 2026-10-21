"""CS-818 - verify_env runs the hooks' own interpreter ladder and grades its winner.

THE DEFECT. ``scripts/verify_env.py`` graded ``sys.executable`` - the interpreter
RUNNING IT - and never performed the resolution the hooks perform. So the table
could read PASS while every hook resolved a DIFFERENT interpreter, and a green
environment report said nothing about the thing that gates a commit.

THE ACCEPTANCE, from docs/history_notes.md, CS-818: "it runs the hooks' own ladder
and reports the winner, failing when that winner differs from the interpreter it
just graded".

THE LADDER IS EXECUTED FROM THE HOOK'S OWN BYTES, NEVER RE-IMPLEMENTED. A Python
copy of four rungs is a second answer waiting to disagree with the first, so the
first arm below proves the executed program CONTAINS the hook's marked region and
that verify_env's own source spells no rung.

THE INTEGRATION ARMS NEED A POSIX SHELL. They skip, with a stated reason, where no
bash resolves - the hooks could not run there either.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
VERIFY_ENV_SOURCE: Final = REPO_ROOT / "scripts" / "verify_env.py"
PRE_COMMIT_HOOK: Final = REPO_ROOT / ".githooks" / "pre-commit"

LADDER_BEGIN: Final = "# >>> CS-818 LADDER BEGIN"
LADDER_END: Final = "# <<< CS-818 LADDER END"
ENV_NAME: Final = "CLOCKSPEED_PYTHON"

# Invented segments. Each survives redact() untouched, so its absence from a row
# can only mean the row never carried it.
SYNTHETIC_VENV_SEGMENT: Final = "zz-cs818-other-interpreter-zz"
SYNTHETIC_MISSING_SEGMENT: Final = "zz-cs818-no-such-interpreter-zz"

VENV_TIMEOUT: Final = 180


def _load_verify_env() -> ModuleType:
    """Load scripts/verify_env.py by path under a name no other loader binds."""
    spec = importlib.util.spec_from_file_location("clockspeed_verify_env_cs818", VERIFY_ENV_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {VERIFY_ENV_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


verify_env = _load_verify_env()

BASH_PRESENT: Final = verify_env.resolve_tool("bash") is not None
BASH_SKIP: Final = "no bash resolves on PATH, so the hooks cannot run here either"


def _env_without(name: str) -> dict[str, str]:
    """A copy of the environment with ``name`` removed under ANY letter case.

    ``dict(os.environ)`` upper-cases its keys on Windows, so popping a mixed-case
    key removes nothing; this matches case-insensitively instead.
    """
    return {key: value for key, value in os.environ.items() if key.upper() != name.upper()}


def _path_key(env: dict[str, str]) -> str:
    """The key PATH is stored under, whatever its case on this platform."""
    for key in env:
        if key.upper() == "PATH":
            return key
    return "PATH"


def _with_path_first(env: dict[str, str], directory: Path) -> dict[str, str]:
    """``env`` with ``directory`` prepended to PATH, in the platform's own form."""
    key = _path_key(env)
    out = dict(env)
    out[key] = str(directory) + os.pathsep + env.get(key, "")
    return out


def _rendered(row: dict) -> str:
    """Everything a row can print, as one string."""
    return " ".join(str(row[field]) for field in ("scope", "name", "status", "value", "note"))


def _identity(executable: str) -> tuple[str, str]:
    """The (realpath of the executable, realpath of the prefix) an interpreter reports."""
    program = (
        "import os, sys; "
        "sys.stdout.write(os.path.realpath(sys.executable) + chr(10) + "
        "os.path.realpath(sys.prefix))"
    )
    proc = subprocess.run(
        [executable, "-c", program],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    lines = proc.stdout.split("\n")
    return os.path.normcase(lines[0]), os.path.normcase(lines[1])


@pytest.fixture(scope="module")
def other_interpreter(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A GENUINELY different interpreter: a fresh venv with no pip in it.

    On Windows its python.exe is a launcher copy, so its executable differs; on a
    POSIX runner it is a symlink back to this interpreter's binary, so only its
    prefix differs. Both are a different interpreter to a gate - the venv carries
    none of the toolchain this one was graded on.
    """
    base = tmp_path_factory.mktemp("cs818") / SYNTHETIC_VENV_SEGMENT
    made = subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(base)],
        capture_output=True,
        text=True,
        timeout=VENV_TIMEOUT,
        check=False,
    )
    assert made.returncode == 0, "the throwaway venv could not be created"
    scripts = base / ("Scripts" if os.name == "nt" else "bin")
    exe = scripts / ("python.exe" if os.name == "nt" else "python")
    assert exe.is_file(), "the throwaway venv carries no python executable"
    return exe


# --- the ladder is the hook's, not a copy -----------------------------------


def test_the_executed_program_carries_the_hooks_own_marked_ladder() -> None:
    """The program verify_env runs CONTAINS the hook's marked region verbatim.

    Non-vacuity: the region is checked to hold the four rungs before the
    containment is asserted, so an extractor that returned an empty string could
    not make this pass.
    """
    text = PRE_COMMIT_HOOK.read_text(encoding="ascii")
    begin = text.index(LADDER_BEGIN)
    end = text.index(LADDER_END) + len(LADDER_END)
    region = text[begin:end]
    for rung in ("CLOCKSPEED_PYTHON:-", "cs_probe python;", "cs_probe python3;", "cs_probe py -3;"):
        assert rung in region, "the marked region is missing a rung"

    program, reason = verify_env.ladder_program(text)
    assert program is not None, reason
    assert region in program, "the executed program does not carry the hook's ladder verbatim"
    assert "cs_probe() {" in program, "the executed program carries no probe definition"


def test_verify_env_spells_no_rung_of_its_own() -> None:
    """A Python re-implementation of the ladder is a copy that drifts - forbidden."""
    source = VERIFY_ENV_SOURCE.read_text(encoding="utf-8")
    for rung in ("cs_probe python;", "cs_probe python3;", "cs_probe py -3;"):
        assert rung not in source, "verify_env spells a ladder rung itself"


def test_the_identity_program_carries_nothing_msys_would_rewrite() -> None:
    """No single quote, slash or colon - the claim its comment makes, pinned."""
    program = verify_env._LADDER_IDENTITY_PROGRAM  # noqa: SLF001 - the pinned constant
    for char in ("'", "/", ":"):
        present = char in program
        assert not present, "the identity program carries a character MSYS may rewrite"


def test_a_hook_without_the_markers_is_refused() -> None:
    program, reason = verify_env.ladder_program("#!/bin/sh\ncs_probe() {\n}\n")
    assert program is None, "a hook with no marked ladder produced a program"
    assert "marker" in reason, "the refusal does not say the markers are missing"


def test_a_hook_without_the_probe_is_refused() -> None:
    text = f"#!/bin/sh\n{LADDER_BEGIN}\nCS_PY=python\n{LADDER_END}\n"
    program, reason = verify_env.ladder_program(text)
    assert program is None, "a hook with no cs_probe definition produced a program"
    assert "cs_probe" in reason, "the refusal does not name the missing probe"


def test_a_missing_hook_is_a_hard_missing_row(tmp_path: Path) -> None:
    row = verify_env.ladder_row(tmp_path, env=_env_without(ENV_NAME))
    assert row["scope"] == "HARD", "the ladder row is not HARD"
    assert not row["ok"], "a checkout with no hook reported a winner"


def test_absent_git_is_a_soft_undetermined_row(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no git to ask, what the hooks would do is UNKNOWN - never a false HARD."""
    real = verify_env.resolve_tool

    def no_git(name: str, **kwargs: object) -> str | None:
        return None if name == "git" else real(name, **kwargs)

    monkeypatch.setattr(verify_env, "resolve_tool", no_git)
    row = verify_env.ladder_row(REPO_ROOT, env=_env_without(ENV_NAME))
    assert row["scope"] == "SOFT", "an undetermined environment was reported HARD"
    assert not row["ok"], "no git, yet the ladder reported a winner"
    assert "git" in row["value"], "the row does not say git is what is missing"


def _hook_run_dir(cmd: list[str]) -> Path | None:
    """The throwaway repository a ``git -C <repo> ... hook run`` targets, if this is one."""
    if "hook" not in cmd or "-C" not in cmd:
        return None
    return Path(cmd[cmd.index("-C") + 1])


def test_an_expired_hook_run_is_bounded_and_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    """The hook run carries the outer bound, and its expiry is SOFT, not a refusal."""
    bounds: list[object] = []

    def expired(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if _hook_run_dir(cmd) is not None:
            bounds.append(kwargs.get("timeout"))
            raise subprocess.TimeoutExpired(cmd="git", timeout=1)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(verify_env.subprocess, "run", expired)
    monkeypatch.setattr(verify_env, "resolve_tool", lambda _name, **_kwargs: "git")
    row = verify_env.ladder_row(REPO_ROOT, env=_env_without(ENV_NAME))
    bounded = bounds == [verify_env.LADDER_OUTER_TIMEOUT]
    assert bounded, "the hook run did not carry the outer bound"
    assert row["scope"] == "SOFT", "an expired hook run was reported HARD"
    assert not row["ok"], "an expired hook run reported a winner"
    assert "within" in row["value"], "the row does not name the expiry"


def test_an_inherited_git_dir_is_not_passed_to_the_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pre-push exports GIT_DIR; the probe must never be aimed at a real repository."""
    seen: list[bool] = []

    def spy(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = kwargs.get("env")
        keys = list(env) if isinstance(env, dict) else []
        seen.append(any(str(key).upper() == "GIT_DIR" for key in keys))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(verify_env.subprocess, "run", spy)
    monkeypatch.setattr(verify_env, "resolve_tool", lambda _name, **_kwargs: "git")
    env = _env_without(ENV_NAME)
    env["GIT_DIR"] = "zz-cs818-inherited-git-dir-zz"
    verify_env.ladder_row(REPO_ROOT, env=env)
    spawned = len(seen)
    leaked = any(seen)
    assert spawned >= 1, "no spawn was observed, so this arm graded nothing"
    assert not leaked, "an inherited GIT_DIR reached the probe's git"


def test_the_ladder_row_is_a_hard_row_of_the_table(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = {
        "scope": "HARD",
        "name": "cs818-sentinel",
        "status": "FOUND",
        "ok": True,
        "value": "sentinel",
        "note": "",
    }
    monkeypatch.setattr(verify_env, "ladder_row", lambda _root: sentinel)
    rows, _ports, _facts = verify_env.collect_rows(REPO_ROOT)
    names = [row["name"] for row in rows]
    assert "cs818-sentinel" in names, "the table does not carry the ladder row"


def _canned_ladder(
    monkeypatch: pytest.MonkeyPatch, executable: str, prefix: str, version: str = "9.9.9"
) -> None:
    """Make the probe hook answer as if ``python`` won with this identity.

    ``git init`` is answered without creating anything, so the stub creates the
    repository directory itself before writing the hook's answer into it.
    """

    def answered(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        repo = _hook_run_dir(cmd)
        if repo is not None:
            identity = " ".join(
                (executable.encode("utf-8").hex(), prefix.encode("utf-8").hex(), version)
            )
            answer = f"cs818-rung=python\ncs818-status=0\ncs818-identity={identity}\n"
            repo.mkdir(parents=True, exist_ok=True)
            (repo / verify_env.LADDER_OUTPUT).write_text(answer, encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(verify_env.subprocess, "run", answered)
    monkeypatch.setattr(verify_env, "resolve_tool", lambda _name, **_kwargs: "git")


def test_a_winner_with_this_identity_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    """The control for the two arms below: the same identity is graded the same."""
    _canned_ladder(monkeypatch, os.path.realpath(sys.executable), os.path.realpath(sys.prefix))
    row = verify_env.ladder_row(REPO_ROOT, env=_env_without(ENV_NAME))
    assert row["ok"], "a winner reporting this interpreter's identity failed the row"


def test_a_winner_sharing_the_executable_but_not_the_prefix_differs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A POSIX venv's executable resolves to the base binary; only its prefix differs."""
    _canned_ladder(monkeypatch, os.path.realpath(sys.executable), str(tmp_path))
    row = verify_env.ladder_row(REPO_ROOT, env=_env_without(ENV_NAME))
    assert not row["ok"], "a winner in another prefix passed as this interpreter"
    assert "prefix" in row["value"], "the row does not say the prefix is what differs"


def test_a_winner_sharing_the_prefix_but_not_the_executable_differs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _canned_ladder(monkeypatch, str(tmp_path / "python"), os.path.realpath(sys.prefix))
    row = verify_env.ladder_row(REPO_ROOT, env=_env_without(ENV_NAME))
    assert not row["ok"], "a winner with another executable passed as this interpreter"
    assert "executable" in row["value"], "the row does not say the executable differs"


# --- the ladder, run for real ------------------------------------------------


@pytest.mark.skipif(not BASH_PRESENT, reason=BASH_SKIP)
def test_this_interpreter_as_the_winner_passes() -> None:
    """The CONTROL that the injected value reached the ladder: the rung is named."""
    env = _env_without(ENV_NAME)
    env[ENV_NAME] = sys.executable
    row = verify_env.ladder_row(REPO_ROOT, env=env)
    assert row["ok"], "this interpreter won the ladder and still failed the row"
    assert row["value"].startswith(ENV_NAME), "the row does not name the winning rung"


@pytest.mark.skipif(not BASH_PRESENT, reason=BASH_SKIP)
def test_a_different_winner_through_the_variable_fails_without_echoing_it(
    other_interpreter: Path,
) -> None:
    assert _identity(str(other_interpreter)) != _identity(sys.executable), (
        "the throwaway venv is not a different interpreter; the arm would prove nothing"
    )
    env = _env_without(ENV_NAME)
    env[ENV_NAME] = str(other_interpreter)
    row = verify_env.ladder_row(REPO_ROOT, env=env)
    rendered = _rendered(row)
    assert row["scope"] == "HARD", "the ladder row is not HARD"
    assert not row["ok"], "a different interpreter won the ladder and the row passed"
    assert row["value"].startswith(ENV_NAME), "the row does not name the winning rung"
    assert "differs" in row["value"], "the row does not say why the winner differs"
    leaked = SYNTHETIC_VENV_SEGMENT in rendered
    assert not leaked, "the row echoed the CLOCKSPEED_PYTHON value"


@pytest.mark.skipif(not BASH_PRESENT, reason=BASH_SKIP)
def test_a_different_winner_through_path_fails(other_interpreter: Path) -> None:
    """The realistic CS-818 shape: no variable set, and PATH's python is another."""
    env = _with_path_first(_env_without(ENV_NAME), other_interpreter.parent)
    row = verify_env.ladder_row(REPO_ROOT, env=env)
    assert not row["ok"], "PATH's python differs from this one and the row passed"
    assert row["value"].startswith("python "), "the row does not name the python rung"
    assert "differs" in row["value"], "the row does not say why the winner differs"


@pytest.mark.skipif(not BASH_PRESENT, reason=BASH_SKIP)
def test_this_interpreter_first_on_path_passes() -> None:
    """The control for the arm above: the same PATH rung, this interpreter first."""
    directory = Path(sys.executable).parent
    plain = directory / ("python.exe" if os.name == "nt" else "python")
    if not plain.is_file() or _identity(str(plain)) != _identity(sys.executable):
        pytest.skip("this interpreter's directory carries no plain 'python' that is this one")
    env = _with_path_first(_env_without(ENV_NAME), directory)
    row = verify_env.ladder_row(REPO_ROOT, env=env)
    assert row["ok"], "this interpreter won the python rung and still failed the row"
    assert row["value"].startswith("python "), "the row does not name the python rung"


@pytest.mark.skipif(not BASH_PRESENT, reason=BASH_SKIP)
def test_a_refused_variable_fails_with_the_hooks_reason_and_no_value(tmp_path: Path) -> None:
    env = _env_without(ENV_NAME)
    env[ENV_NAME] = str(tmp_path / SYNTHETIC_MISSING_SEGMENT)
    row = verify_env.ladder_row(REPO_ROOT, env=env)
    rendered = _rendered(row)
    assert not row["ok"], "an unrunnable CLOCKSPEED_PYTHON reported a winner"
    assert "did not answer the probe" in row["value"], "the hook's own reason is not reported"
    leaked = SYNTHETIC_MISSING_SEGMENT in rendered
    assert not leaked, "the row echoed the CLOCKSPEED_PYTHON value"


# --- the environment git gives its hooks, not the caller's -------------------
#
# REFUTED BY THE M8 ADVERSARY: the ladder used to be run by a bash looked up on
# the CALLER's PATH. Git for Windows runs hooks under its own shell and puts its
# own tool directories on the hook's PATH, so a caller PATH naming only git's
# cmd directory, or one putting System32 ahead of git's usr/bin, made the row
# report a failure while a real commit ran the hook fine. Both PATH shapes are
# built at run time from where git resolves, never spelled.


def _git_for_windows_root() -> Path | None:
    """The Git for Windows install git resolves into, found by its layout."""
    if os.name != "nt":
        return None
    git = verify_env.resolve_tool("git")
    if git is None:
        return None
    for candidate in Path(git).resolve().parents:
        if (candidate / "cmd").is_dir() and (candidate / "usr" / "bin").is_dir():
            return candidate
    return None


GIT_ROOT: Final = _git_for_windows_root()
GIT_SHAPE_SKIP: Final = "these PATH shapes are Git for Windows layouts"


def _system_dir() -> Path:
    system_root = os.environ.get("SYSTEMROOT", "")
    return Path(system_root) / "System32"


def _require_plain_python_here() -> Path:
    directory = Path(sys.executable).parent
    plain = directory / "python.exe"
    if not plain.is_file() or _identity(str(plain)) != _identity(sys.executable):
        pytest.skip("this interpreter's directory carries no plain 'python' that is this one")
    return directory


def _with_path(path: str) -> dict[str, str]:
    env = _env_without(ENV_NAME)
    env[_path_key(env)] = path
    return env


@pytest.mark.skipif(GIT_ROOT is None, reason=GIT_SHAPE_SKIP)
def test_a_path_naming_only_gits_cmd_directory_still_runs_the_ladder() -> None:
    assert GIT_ROOT is not None
    directory = _require_plain_python_here()
    path = os.pathsep.join((str(GIT_ROOT / "cmd"), str(_system_dir()), str(directory)))
    row = verify_env.ladder_row(REPO_ROOT, env=_with_path(path))
    assert row["ok"], "the row failed on a PATH under which git runs the hook fine"
    assert row["value"].startswith("python "), "the row does not name the python rung"


@pytest.mark.skipif(GIT_ROOT is None, reason=GIT_SHAPE_SKIP)
def test_a_path_with_system32_before_gits_usr_bin_still_runs_the_ladder() -> None:
    assert GIT_ROOT is not None
    directory = _require_plain_python_here()
    path = os.pathsep.join(
        (
            str(_system_dir()),
            str(GIT_ROOT / "usr" / "bin"),
            str(GIT_ROOT / "cmd"),
            str(directory),
        )
    )
    row = verify_env.ladder_row(REPO_ROOT, env=_with_path(path))
    assert row["ok"], "the row failed on a PATH under which git runs the hook fine"
    assert row["value"].startswith("python "), "the row does not name the python rung"
