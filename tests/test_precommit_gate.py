#!/usr/bin/env python3
"""Tests for tools/precommit_gate.py.

The gate is invoked as a SUBPROCESS throughout, because the exit code is half
the contract: 0 pass, 1 block. Importing the module and inspecting a return
value would test something adjacent to what the git hook actually relies on.

Every assertion pins the exit code AND the diagnostic text. CONVENTIONS.md
section 7.2: "A negative assertion rules out without pinning down. Assert what
IS there." So a blocking test names the code and the reason it expects, not
merely that stderr was non-empty.

Every violating literal in this file is assembled from fragments at runtime.
That is deliberate and it is not decoration: this file is itself checked by
the gate, and a spelled-out em dash, PEM header or home path here would block
the commit that adds these tests. test_gate_checks_its_own_slice_files proves
the assembly worked.

WORLD VALUES ARE SYNTHETIC AND CONSTRUCTED HERE, so ground truth is known
independently of anything the gate does. Two rules follow from CLAUDE.md
non-negotiables 3 and 11 and neither is negotiable:

  1. The operator's real world name and real world token are NEVER staged into
     any repository, written into any fixture, or asserted on.
  2. The gate's own redactor is never used as the oracle for "does this string
     hold personal data". A redactor is blind in exactly the places it is
     blind, so testing it against itself proves nothing. Every value below is
     built here, so what it is is known before the gate ever sees it.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "precommit_gate.py"

# The seven files this slice owns. Used by the self-coverage test.
SLICE_FILES = (
    REPO_ROOT / ".githooks" / "pre-commit",
    REPO_ROOT / ".githooks" / "commit-msg",
    REPO_ROOT / ".githooks" / "pre-push",
    REPO_ROOT / "scripts" / "install_hooks.py",
    REPO_ROOT / "tools" / "precommit_gate.py",
    REPO_ROOT / "tools" / "edit_lint_check.py",
    REPO_ROOT / "tests" / "test_precommit_gate.py",
)

# Assembled, never spelled out. See the module docstring. chr() calls on
# purpose: the literal characters would make this file fail the very check
# it is testing, and a backslash-u escape is easy to normalise back into
# the character it denotes.
EM_DASH = chr(0x2014)
RIGHT_SMART_QUOTE = chr(0x2019)
NON_BREAKING_SPACE = chr(0x00A0)
PEM_HEADER = "-----BEGIN " + "RSA PRIVATE KEY" + "-----"
PEM_FOOTER = "-----END " + "RSA PRIVATE KEY" + "-----"
WINDOWS_HOME_PATH = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.txt"

# Account directory names, one per platform shape. The 17-digit Steam form is
# NOT the only shape: Epic writes a hex token and the Microsoft Store a
# braceless GUID, so a filter that recognises only digits recognises one
# platform out of three. All three are synthetic.
FAKE_ACCOUNT_ID = "12345678901234567"
FAKE_EPIC_ACCOUNT_ID = "a7f3" + "c081" + "b29d" + "4e56" + "90ab" + "cdef" + "1234" + "5678"
FAKE_MSSTORE_ACCOUNT_ID = "3f2504e0" + "-4f89" + "-11d3" + "-9a0c" + "-0305e82c3301"

# Synthetic world values. Neither string exists on any real machine, and
# neither is spelled out as one literal - this file is checked by the gate.
SYNTHETIC_WORLD_NAME = "Zynthetiqua" + "Prime"
SYNTHETIC_WORLD_ID = "Zq7vNbXt41" + "KpRs93" + "MwYd2C"

# The measured false-positive population behind condition C1. Every one of
# these is exactly 22 characters, which is the world-token length, and every
# one of them is ordinary tracked content. A shape-only token detector blocks
# all four, so detection has to be driven by a discovered VALUE instead.
TOKEN_SHAPED_BUT_HARMLESS = (
    "Build_ConstructorMk1_C",
    "Recipe_SteelWall_8x4_C",
    "DedicatedServerAPIDocs",
    "most-recently-modified",
)

# A component that appears nowhere else, so counting it in stderr separates
# the diagnostic LABEL channel from an exception rendering. The label
# legitimately carries it once; a leaking exception adds a second.
#
# CS-204 re-pointed this from the DIRECTORY to the BASENAME, and the reason is
# the point rather than a detail. The label channel is now redacted to the
# basename at the render boundary, so a directory-component marker vanishes
# from every line and the anti-vacuity assertion in
# assert_path_is_rendered_once_per_line stops being able to fire. Re-pointing
# it at a component that SURVIVES redaction keeps these tests non-vacuous;
# loosening the redaction to keep the old marker visible would have been the
# wrong repair, because the marker sits in the directory precisely where the
# operator's account name sits. leak_target places it in BOTH, so a rendering
# that echoes the raw path still counts two and still fails.
LEAK_MARKER = "zzleakmarkerdirzz"

TIMEOUT = 180


def base_env(tmp_path: Path) -> dict[str, str]:
    """A deterministic environment for the runtime-detected PII checks.

    The account name and the save root are pinned to values that cannot exist
    on the machine running the suite, so these tests assert the gate's logic
    rather than the operator's login name. The one test that needs real
    detection sets CLOCKSPEED_SAVE_ROOT itself.

    The world-value overrides are CLEARED and the local config is pointed at a
    path that does not exist. Without that, a machine whose config/local.json
    declares a real world would feed a real value into these tests, which
    would make the suite machine-dependent and would risk asserting on the
    operator's own data. test_gate_checks_its_own_slice_files is the one test
    that deliberately runs against the real environment instead.
    """
    env = dict(os.environ)
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        env.pop(key, None)
    env["USERNAME"] = "gatetestaccount"
    env["USER"] = "gatetestaccount"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def load_gate() -> ModuleType:
    """Import the gate by file path, for the checks that are pure text.

    The suite runs the gate as a subprocess everywhere else, because the exit
    code is half the contract. The exception RENDERINGS are the exception:
    subprocess.TimeoutExpired and a failed git invocation cannot be provoked
    end to end without making the suite slow and flaky, and what is under test
    there is a string, not a verdict. Loading from the path rather than
    importing ``tools.precommit_gate`` keeps tools/ out of the import graph.
    """
    name = "clockspeed_gate_under_test"
    spec = importlib.util.spec_from_file_location(name, GATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module, not after. The gate declares dataclasses
    # under `from __future__ import annotations`, and @dataclass resolves those
    # string annotations through sys.modules[cls.__module__]. A module that is
    # not registered yet makes that lookup return None and the decorator raises
    # while the class body is still executing.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_gate(
    *args: str,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(GATE), *args],
        input=stdin,
        capture_output=True,
        env=env,
        cwd=None if cwd is None else str(cwd),
        timeout=TIMEOUT,
        check=False,
    )
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


def write(path: Path, text: str) -> Path:
    """Write bytes explicitly - never write_text, which rewrites LF on Windows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def test_gate_script_exists() -> None:
    assert GATE.is_file(), f"the gate is missing at {GATE}"


# --------------------------------------------------------------------------
# a. character set
# --------------------------------------------------------------------------


def test_em_dash_in_markdown_is_blocked(tmp_path: Path) -> None:
    target = write(tmp_path / "notes.md", "# Title\n\nAlpha " + EM_DASH + " beta\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert ":3:7: CHARSET" in result.stderr
    assert "U+2014 em dash" in result.stderr
    assert "use a spaced hyphen" in result.stderr
    assert "BLOCKED" in result.stderr


def test_smart_quote_in_python_is_blocked(tmp_path: Path) -> None:
    target = write(tmp_path / "mod.py", 'x = "it' + RIGHT_SMART_QUOTE + 's"\n')
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert ":1:8: CHARSET" in result.stderr
    assert "U+2019 right smart single quote" in result.stderr


def test_non_breaking_space_is_blocked(tmp_path: Path) -> None:
    body = "alpha" + NON_BREAKING_SPACE + "beta\n"
    target = write(tmp_path / "doc.md", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "U+00A0 non-breaking space" in result.stderr


def test_clean_ascii_passes(tmp_path: Path) -> None:
    target = write(tmp_path / "clean.py", "def add(a, b):\n    return a + b\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0
    assert "PASS" in result.stdout
    assert "1 checked" in result.stdout
    assert "0 blocking" in result.stdout


# --------------------------------------------------------------------------
# b. secrets
# --------------------------------------------------------------------------


def test_pem_private_key_block_is_blocked(tmp_path: Path) -> None:
    body = PEM_HEADER + "\nQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo=\n" + PEM_FOOTER + "\n"
    target = write(tmp_path / "id_rsa.txt", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "SECRET" in result.stderr
    assert "PEM private key block" in result.stderr
    assert ":1:1:" in result.stderr


def test_aws_access_key_id_is_blocked(tmp_path: Path) -> None:
    body = "aws = " + '"' + "AKIA" + ("Q7" * 8) + '"' + "\n"
    target = write(tmp_path / "conf.txt", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "AWS access key id" in result.stderr


def test_changeme_placeholder_is_not_blocked(tmp_path: Path) -> None:
    """False-positive guard: an obvious placeholder must not block a commit."""
    target = write(tmp_path / "settings.py", 'api_key = "CHANGEME_CHANGEME"\n')
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0
    assert "PASS" in result.stdout
    assert "SECRET" not in result.stderr


def test_real_looking_credential_is_blocked(tmp_path: Path) -> None:
    """The counterpart to the placeholder test: the rule still has teeth."""
    body = "api" + "_key = " + '"' + "hunter2hunter2hunter2" + '"' + "\n"
    target = write(tmp_path / "settings.py", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "SECRET" in result.stderr
    assert "quoted literal of 16 or more characters" in result.stderr


# --------------------------------------------------------------------------
# c. PII
# --------------------------------------------------------------------------


def test_windows_home_path_is_blocked(tmp_path: Path) -> None:
    target = write(tmp_path / "readme.md", "See " + WINDOWS_HOME_PATH + " for logs.\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "PII" in result.stderr
    assert "absolute Windows home path" in result.stderr
    assert "auto-detect it at runtime" in result.stderr


def test_posix_home_path_is_blocked(tmp_path: Path) -> None:
    body = "log at " + "/" + "home" + "/someoperator" + "/app.log" + "\n"
    target = write(tmp_path / "ops.md", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "absolute POSIX home path" in result.stderr


def test_current_account_name_is_blocked(tmp_path: Path) -> None:
    """The name comes from the environment at runtime, never from a literal."""
    env = base_env(tmp_path)
    target = write(tmp_path / "note.md", "owner is gatetestaccount here\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1
    assert "PII" in result.stderr
    assert "account name appears as a whole word" in result.stderr


def test_runtime_discovered_account_id_is_blocked(tmp_path: Path) -> None:
    """The id is discovered by globbing the save root, never hardcoded."""
    save_root = tmp_path / "save-root"
    (save_root / FAKE_ACCOUNT_ID).mkdir(parents=True)
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

    target = write(tmp_path / "world.md", "account " + FAKE_ACCOUNT_ID + " parsed\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1
    assert "PII" in result.stderr
    assert "platform account id" in result.stderr


def test_absent_save_root_is_a_reported_skip_not_a_crash(tmp_path: Path) -> None:
    """A machine with no game installed must still be able to commit."""
    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 0
    assert "save root does not exist on this machine" in result.stdout


# --------------------------------------------------------------------------
# d. publisher data
# --------------------------------------------------------------------------


def test_sav_path_is_blocked(tmp_path: Path) -> None:
    target = write(tmp_path / "Some Save Name.sav", "harmless ascii\n")
    result = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 1
    assert "PUBLISHER" in result.stderr
    assert "publisher-owned game artifact" in result.stderr
    assert "add -f" in result.stderr
    # The path is rejected without the bytes ever being read.
    assert "path itself is a violation" in result.stdout


def test_usmap_and_headers_zip_are_blocked(tmp_path: Path) -> None:
    for name in ("FactoryGame.usmap", "Headers.zip"):
        target = write(tmp_path / name, "x\n")
        result = run_gate("--files", str(target), env=base_env(tmp_path))
        assert result.returncode == 1, name
        assert "PUBLISHER" in result.stderr, name


# --------------------------------------------------------------------------
# e. python syntax
# --------------------------------------------------------------------------


def test_python_syntax_error_is_blocked(tmp_path: Path) -> None:
    target = write(tmp_path / "broken.py", "def broken(:\n    return 1\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "SYNTAX" in result.stderr
    assert "python syntax error" in result.stderr
    assert "broken.py:1:" in result.stderr


# --------------------------------------------------------------------------
# --text-stdin
# --------------------------------------------------------------------------


def test_text_stdin_blocks_em_dash(tmp_path: Path) -> None:
    payload = ("git commit -m " + EM_DASH + " nope").encode("utf-8")
    result = run_gate("--text-stdin", stdin=payload, env=base_env(tmp_path))

    assert result.returncode == 1
    assert "<stdin>:1:15: CHARSET" in result.stderr
    assert "U+2014 em dash" in result.stderr


def test_text_stdin_blocks_a_secret(tmp_path: Path) -> None:
    payload = (PEM_HEADER + "\n").encode("utf-8")
    result = run_gate("--text-stdin", stdin=payload, env=base_env(tmp_path))

    assert result.returncode == 1
    assert "PEM private key block" in result.stderr


def test_text_stdin_passes_clean_ascii(tmp_path: Path) -> None:
    result = run_gate("--text-stdin", stdin=b"git status --short", env=base_env(tmp_path))

    assert result.returncode == 0
    assert "PASS" in result.stdout


# --------------------------------------------------------------------------
# self-coverage and skip transparency
# --------------------------------------------------------------------------


def test_gate_checks_its_own_slice_files() -> None:
    """CONVENTIONS.md 15.1: a guard can be green while self-excusing.

    Deliberately run against the REAL environment, not base_env. This is the
    check that proves none of the seven files carries this machine's account
    name, its numeric account id, a home path or a non-ASCII byte.
    """
    for path in SLICE_FILES:
        assert path.is_file(), f"missing slice file {path}"

    result = run_gate("--files", *[str(p) for p in SLICE_FILES])

    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout
    assert "7 checked" in result.stdout


def test_list_skipped_names_the_skip_and_the_reason(tmp_path: Path) -> None:
    target = write(tmp_path / "art.png", "not really a png\n")
    result = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 0
    assert "skipped" in result.stdout
    assert "known-binary extension '.png'" in result.stdout


def test_verbose_lists_every_checked_unit(tmp_path: Path) -> None:
    target = write(tmp_path / "clean.py", "VALUE = 1\n")
    result = run_gate("--files", str(target), "--verbose", env=base_env(tmp_path))

    assert result.returncode == 0
    assert "checked" in result.stdout
    assert "worktree" in result.stdout
    assert "clean.py" in result.stdout


def test_unreadable_path_blocks_rather_than_passing(tmp_path: Path) -> None:
    """Fail closed: a path the gate cannot read is never waved through."""
    missing = tmp_path / "does-not-exist.py"
    result = run_gate("--files", str(missing), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "IO" in result.stderr
    assert "could not read the file" in result.stderr


def test_a_mode_flag_is_required(tmp_path: Path) -> None:
    result = run_gate(env=base_env(tmp_path))

    assert result.returncode != 0
    assert "one of the arguments" in result.stderr


# --------------------------------------------------------------------------
# --staged reads the INDEX, not the working tree
# --------------------------------------------------------------------------


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


@pytest.fixture
def throwaway_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    assert git("init", "-q", "-b", "main", cwd=root).returncode == 0
    git("config", "user.email", "gate@example.invalid", cwd=root)
    git("config", "user.name", "Gate Test", cwd=root)
    git("config", "commit.gpgsign", "false", cwd=root)
    return root


def test_staged_mode_blocks_a_violation_staged_in_the_index(
    throwaway_repo: Path, tmp_path: Path
) -> None:
    write(throwaway_repo / "doc.md", "clean " + EM_DASH + " dirty\n")
    assert git("add", "doc.md", cwd=throwaway_repo).returncode == 0

    env = base_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(GATE), "--staged"],
        cwd=str(throwaway_repo),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")

    assert proc.returncode == 1
    assert "doc.md:1:7: CHARSET" in stderr
    assert "U+2014 em dash" in stderr


def test_staged_mode_reads_the_index_not_the_dirty_worktree(
    throwaway_repo: Path, tmp_path: Path
) -> None:
    """The hole this closes: stage a violation, then clean the worktree.

    A gate that read the working tree would see clean bytes and pass, and the
    em dash would be committed anyway. Reading `git show :<path>` is what makes
    the difference, so it gets its own test.
    """
    target = throwaway_repo / "doc.md"
    write(target, "staged " + EM_DASH + " violation\n")
    assert git("add", "doc.md", cwd=throwaway_repo).returncode == 0
    # Now make the WORKING TREE spotless. The index still holds the em dash.
    write(target, "worktree is clean ascii now\n")

    env = base_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(GATE), "--staged"],
        cwd=str(throwaway_repo),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")

    assert proc.returncode == 1
    assert "U+2014 em dash" in stderr


def test_staged_mode_passes_on_a_clean_index(throwaway_repo: Path, tmp_path: Path) -> None:
    write(throwaway_repo / "doc.md", "plain ascii only\n")
    assert git("add", "doc.md", cwd=throwaway_repo).returncode == 0

    env = base_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(GATE), "--staged"],
        cwd=str(throwaway_repo),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )

    assert proc.returncode == 0
    assert "PASS" in proc.stdout.decode("utf-8", "replace")


def test_staged_mode_blocks_a_force_added_sav(throwaway_repo: Path, tmp_path: Path) -> None:
    write(throwaway_repo / ".gitignore", "*.sav\n")
    write(throwaway_repo / "pinned_world.sav", "pretend save bytes\n")
    assert git("add", "-f", "pinned_world.sav", cwd=throwaway_repo).returncode == 0

    env = base_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(GATE), "--staged"],
        cwd=str(throwaway_repo),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")

    assert proc.returncode == 1
    assert "pinned_world.sav" in stderr
    assert "PUBLISHER" in stderr


def test_long_camelcase_identifier_after_a_key_label_is_not_a_secret(
    tmp_path: Path,
) -> None:
    """A 40-plus character identifier following a "KEY:" label is not a credential.

    Regression. The bare-high-entropy rule originally matched any long
    [A-Za-z0-9+/] run after a word containing "key", so an ordinary documentation
    line blocked a real commit:

        KEY: mProductionBoostPowerConsumptionExponent

    That is a false positive, and a gate that fires on prose is a gate that gets
    overridden. The rule now requires at least two digits in the literal.
    """
    clean = tmp_path / "report.md"
    write(
        clean,
        "KEY: mProductionBoostPowerConsumptionExponent\nKEY: mEstimatedMininumPowerConsumption\n",
    )
    result = run_gate("--files", str(clean), env=base_env(tmp_path))
    out = result.stdout
    assert result.returncode == 0, f"false positive on a documentation line:\n{out}"
    assert "PASS" in out


def test_a_real_bare_credential_is_still_blocked(tmp_path: Path) -> None:
    """The digit requirement must not blunt the rule against actual secrets."""
    for name, literal in (
        ("b64", "a" * 20 + "1234567890" + "b" * 12),
        ("hex", "deadbeef" * 4),
    ):
        bad = tmp_path / f"conf_{name}.txt"
        write(bad, f"api_token = {literal}\n")
        result = run_gate("--files", str(bad), env=base_env(tmp_path))
        # Diagnostics go to stderr; stdout carries only the PASS summary.
        err = result.stderr
        assert result.returncode == 1, f"{name} credential NOT blocked:\n{err}"
        assert "SECRET" in err
        assert "bare high-entropy literal" in err


# ==========================================================================
# CS-201 - world names, world tokens, and account directories that are not
# all digits.
# ==========================================================================
#
# The finding that shapes every test below, measured over the whole tracked
# tree rather than assumed: a world token is 22 characters of [A-Za-z0-9_-],
# and so are thousands of ordinary strings already in this repository. Shape
# alone cannot separate them. Detection is therefore driven by a VALUE the
# gate discovered on this machine, and the tests come in pairs - one proving
# the value blocks, one proving the lookalikes do not.


def make_save_root(tmp_path: Path, *account_dirs: str) -> Path:
    """Build a synthetic save root holding the named account directories."""
    save_root = tmp_path / "save-root"
    save_root.mkdir(parents=True, exist_ok=True)
    for name in account_dirs:
        (save_root / name).mkdir(parents=True, exist_ok=True)
    return save_root


# --------------------------------------------------------------------------
# C1 - no shape-only blocking
# --------------------------------------------------------------------------


def test_token_shaped_ordinary_content_is_not_blocked(tmp_path: Path) -> None:
    """C1. Four measured 22-character lookalikes must all pass.

    This is the test that would catch a shape-only token detector. Every
    string here is exactly a world token's length and character class, and
    every one of them is ordinary content: two game class names of the kind
    clockspeed/data/registry.py generates by the thousand, the name of a
    first-party documentation file, and a phrase out of a docstring. A gate
    that blocked these would refuse nearly every commit in this project.
    """
    body = "\n".join(TOKEN_SHAPED_BUT_HARMLESS) + "\n"
    target = write(tmp_path / "lookalikes.md", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


# --------------------------------------------------------------------------
# C2 - discovery, never a literal
# --------------------------------------------------------------------------


def test_world_name_declared_in_the_environment_is_blocked(tmp_path: Path) -> None:
    """C2, source 1: an operator-declared override, mirroring locate.py."""
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = SYNTHETIC_WORLD_NAME

    target = write(tmp_path / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "PII" in result.stderr
    assert "world name discovered on this machine" in result.stderr


def test_world_name_declared_in_local_config_is_blocked(tmp_path: Path) -> None:
    """C2, source 2: config/local.json, which is gitignored.

    tests/test_scaffold.py owns the assertion that the pattern really is
    ignored; this test only proves the gate reads it.
    """
    config = tmp_path / "local.json"
    write(config, '{"world_names": "' + SYNTHETIC_WORLD_NAME + '"}\n')
    env = base_env(tmp_path)
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(config)

    target = write(tmp_path / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world name discovered on this machine" in result.stderr


def test_world_name_discovered_from_a_sav_basename_is_blocked(tmp_path: Path) -> None:
    """C2, source 3: a .sav basename read under the discovered account dir.

    The save directory is opened READ-ONLY and only its entry names are used.
    This is the only source that needs no operator declaration, which makes it
    the one that protects a machine nobody configured.
    """
    save_root = make_save_root(tmp_path, FAKE_ACCOUNT_ID)
    (save_root / FAKE_ACCOUNT_ID / (SYNTHETIC_WORLD_NAME + ".sav")).write_bytes(b"")
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

    target = write(tmp_path / "note.md", "loaded " + SYNTHETIC_WORLD_NAME + " today\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world name discovered on this machine" in result.stderr


def test_autosave_basename_yields_the_bare_world_name(tmp_path: Path) -> None:
    """The game rotates autosaves, so the stem carries a suffix the name does not."""
    save_root = make_save_root(tmp_path, FAKE_ACCOUNT_ID)
    rotated = SYNTHETIC_WORLD_NAME + "_autosave_2.sav"
    (save_root / FAKE_ACCOUNT_ID / rotated).write_bytes(b"")
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

    target = write(tmp_path / "note.md", "loaded " + SYNTHETIC_WORLD_NAME + " today\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world name discovered on this machine" in result.stderr


def test_world_token_declared_in_the_environment_is_blocked(tmp_path: Path) -> None:
    """C2: the token half, declaration source.

    A world token lives inside the save HEADER, not in any filename, so a
    declaration was the ONLY source until CS-403 - which added a second, by
    reading the header through the parser CS-400 shipped rather than by
    growing a second one here. The declaration source is unchanged and this
    test pins that it stayed unchanged; the header source has its own tests at
    the foot of this file.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_TOKENS"] = SYNTHETIC_WORLD_ID

    target = write(tmp_path / "ledger.md", "world " + SYNTHETIC_WORLD_ID + " seen\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "PII" in result.stderr
    assert "world token for this machine" in result.stderr


def test_the_gate_source_carries_no_world_value_of_its_own(tmp_path: Path) -> None:
    """C2: detection is discovery, so an undiscoverable world matches nothing.

    The structural proof that no world value is baked into the tracked gate.
    With no override, no local config and no save root, the gate must hold
    ZERO world matchers, so content that looks exactly like a world value
    passes. If a literal had been embedded, this would block.

    The complementary proof runs against the REAL environment in
    test_gate_checks_its_own_slice_files: the gate is checked by itself with
    the operator's own world values live, so a literal in the source would
    make the gate block its own file.
    """
    body = SYNTHETIC_WORLD_NAME + "\n" + SYNTHETIC_WORLD_ID + "\n"
    target = write(tmp_path / "worldish.md", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


# --------------------------------------------------------------------------
# C4 - the matchability filter applies to world names too
# --------------------------------------------------------------------------


def test_generic_world_name_is_skipped_not_matched(tmp_path: Path) -> None:
    """C4. A world named "test" must not blocklist the word across the repo.

    Widening a whole-word blocklist is only safe when it is filtered, and the
    exemption has to be visible: --list-skipped is where it shows up, so it
    can never be silently in force.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = "test"

    target = write(tmp_path / "doc.md", "run the test suite before the test push\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout
    assert "generic" in result.stdout


def test_short_world_name_is_skipped_not_matched(tmp_path: Path) -> None:
    """C4, the length half of the same filter."""
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = "ab"

    target = write(tmp_path / "doc.md", "ab ab ab\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout
    assert "too short to match safely" in result.stdout


def test_a_skipped_value_is_never_echoed_in_the_skip_reason(tmp_path: Path) -> None:
    """A skip reason that prints the value it skipped is itself the leak.

    Non-negotiable 12 counts log lines as an echo path, and --list-skipped
    prints to stdout on a PASSING run - the output nobody reads closely.

    Both needles are distinctive on purpose. An earlier draft used a two
    character world name and matched the "ab" inside "discoverable", which
    would have made this test fail for a reason that had nothing to do with
    the property under test.
    """
    dropped_dir = "Zynthetiquaville"
    save_root = make_save_root(tmp_path, dropped_dir)
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)
    env["CLOCKSPEED_WORLD_NAMES"] = "Zq"

    target = write(tmp_path / "clean.md", "nothing here\n")
    result = run_gate("--files", str(target), "--list-skipped", "--verbose", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout
    assert "<pii:account-id>" in result.stdout
    assert dropped_dir not in result.stdout
    assert "Zq" not in result.stdout


# --------------------------------------------------------------------------
# C5 - dropping .isdigit() widens, and widening is only safe when filtered
# --------------------------------------------------------------------------


def test_non_digit_account_directories_are_blocked(tmp_path: Path) -> None:
    """C5. The Epic hex and Microsoft Store GUID shapes, which .isdigit() missed.

    This is the whole point of the item: an account directory is identified by
    WHERE it sits, not by being all digits, and two of the three shipping
    platforms do not write digits.
    """
    for account_id in (FAKE_EPIC_ACCOUNT_ID, FAKE_MSSTORE_ACCOUNT_ID):
        save_root = make_save_root(tmp_path / account_id[:4], account_id)
        env = base_env(tmp_path)
        env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

        target = write(tmp_path / account_id[:4] / "note.md", "acct " + account_id + "\n")
        result = run_gate("--files", str(target), env=env)

        assert result.returncode == 1, f"{account_id} not blocked:\n{result.stdout}"
        assert "platform account id" in result.stderr


def test_generic_save_root_subdirectory_is_a_reported_skip(tmp_path: Path) -> None:
    """C5. Widening turns EVERY subdirectory into a blocklist entry.

    A directory the operator made beside the account directory is not an
    account id, and blocklisting its name would flag ordinary prose across the
    repository. The drop is reported rather than silent, so the filter is
    auditable instead of assumed.
    """
    save_root = make_save_root(tmp_path, "backup", "screenshots")
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

    body = "keep a backup and check the screenshots directory\n"
    target = write(tmp_path / "ops.md", body)
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:account-id>" in result.stdout
    assert "not an account id" in result.stdout


def test_the_gate_no_longer_filters_account_dirs_on_isdigit() -> None:
    """The acceptance criterion, asserted against the shipped source.

    The removed filter was `entry.name.isdigit()` guarded by
    MIN_ACCOUNT_ID_DIGITS, a constant that was doing two jobs - the id-shape
    test and the matchability floor - which is why dropping one without
    replacing the other would have widened the blocklist unfiltered.

    A bare "isdigit" search would NOT state the criterion, and asserting it
    would be wrong rather than merely weak: the replacement filter asks
    `any(char.isdigit() ...)`, which is the deliberate opposite of the removed
    one - ANY digit rather than EVERY digit - and is what admits the Epic hex
    and Microsoft Store GUID shapes. That behaviour is pinned by execution in
    test_non_digit_account_directories_are_blocked; this pins the source.
    """
    source = GATE.read_bytes().decode("utf-8")

    assert "name.isdigit" not in source
    assert "MIN_ACCOUNT_ID_DIGITS" not in source


def test_locate_keeps_its_isdigit_selection_filter() -> None:
    """C6. The asymmetry is deliberate and must survive a later tidy-up.

    clockspeed/data/locate.py SELECTS which world to read. Widening a selector
    makes the resolver silently pick the wrong world, which is a correctness
    bug, not a privacy fix. The gate only widens what it REFUSES to commit, so
    it is deliberately wider than the resolver. This test exists so that
    "make the two consistent" fails loudly instead of landing quietly.
    """
    resolver = (REPO_ROOT / "clockspeed" / "data" / "locate.py").read_bytes().decode("utf-8")

    assert "isdigit" in resolver


# --------------------------------------------------------------------------
# C8 - discovery failure is a reported skip
# --------------------------------------------------------------------------


def test_undiscoverable_world_is_a_reported_skip_not_a_crash(tmp_path: Path) -> None:
    """C8. No override, no config, no save root: report it and pass.

    CI runs on a runner with no game, no LOCALAPPDATA and no local config.
    A gate that crashed or blocked there would block every branch at once.
    """
    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout


def test_world_discovery_survives_an_absent_localappdata(tmp_path: Path) -> None:
    """C7, the CI half: the suite runs where neither the game nor the vars exist."""
    env = base_env(tmp_path)
    for key in ("CLOCKSPEED_SAVE_ROOT", "LOCALAPPDATA", "XDG_DATA_HOME"):
        env.pop(key, None)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout


def test_unreadable_save_root_is_a_skip_not_a_crash(tmp_path: Path) -> None:
    """C8. A save root that is a FILE, not a directory, must not take the gate down."""
    not_a_dir = write(tmp_path / "save-root-file", "this is not a directory\n")
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(not_a_dir)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout


# --------------------------------------------------------------------------
# C9 - the gate needs no import outside the standard library
# --------------------------------------------------------------------------


def test_gate_imports_nothing_from_the_package_at_module_scope() -> None:
    """C9. The gate is the one tool that has to run in a checkout with nothing set up.

    CS-403 NARROWED THIS, and the narrowing is the point rather than a
    concession. The original assertion was textual - the string "import
    clockspeed" appears nowhere - which was the right shape while the gate
    reached the package not at all. It now reaches the header parser through
    ONE function-local import, so the property that actually protects startup
    is MODULE SCOPE, not absence: a module-scope import runs before main() and
    takes the gate down with the package, while a function-local one cannot.
    test_the_package_import_is_function_local_and_never_at_module_scope pins
    the same boundary from the other side and refuses a vacuous pass.
    """
    tree = ast.parse(GATE.read_bytes().decode("utf-8"))

    module_scope: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            module_scope.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            module_scope.append(node.module)

    offenders = [name for name in module_scope if name.split(".")[0] == "clockspeed"]
    assert not offenders, offenders


def test_gate_still_runs_and_blocks_with_the_package_out_of_reach(tmp_path: Path) -> None:
    """C9, proved by execution rather than by reading the imports.

    A copy of the gate is run from a directory with no clockspeed package
    anywhere above it. If the gate had grown a dependency on the data layer it
    would fail to start here, and a gate that fails to start is a gate that
    does not block.
    """
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    copy = isolated / "gate_copy.py"
    copy.write_bytes(GATE.read_bytes())

    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = SYNTHETIC_WORLD_NAME
    target = write(isolated / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")

    proc = subprocess.run(
        [sys.executable, str(copy), "--files", str(target)],
        cwd=str(isolated),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "replace")

    assert proc.returncode == 1, proc.stdout.decode("utf-8", "replace")
    assert "world name discovered on this machine" in stderr


# --------------------------------------------------------------------------
# C7 - end to end, through a real commit, with no real personal data
# --------------------------------------------------------------------------


def git_with_env(*args: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run git with an explicit environment, so the hook inherits it."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


@pytest.fixture
def hooked_repo(tmp_path: Path) -> Path:
    """A throwaway repo whose pre-commit hook runs THIS gate, plus a base commit.

    The repository's own .githooks/pre-commit is deliberately NOT reused
    verbatim. It resolves the gate as $ROOT/tools/precommit_gate.py, which
    does not exist inside a throwaway repo, so it would die "gate not found"
    and the commit would fail for a reason that has nothing to do with the
    gate's verdict. HEAD would be unchanged and the test would be green while
    proving nothing. The hook written here names the real gate, and every test
    that uses it also asserts the gate's own diagnostic text so that an
    unrelated failure cannot masquerade as a block.

    The base commit is made BEFORE the hook is wired, so the assertion after a
    blocked commit is "HEAD did not move" rather than "HEAD never existed".
    """
    root = tmp_path / "hookedrepo"
    root.mkdir()
    assert git("init", "-q", "-b", "main", cwd=root).returncode == 0
    git("config", "user.email", "gate@example.invalid", cwd=root)
    git("config", "user.name", "Gate Test", cwd=root)
    git("config", "commit.gpgsign", "false", cwd=root)

    write(root / "seed.txt", "seed\n")
    assert git("add", "seed.txt", cwd=root).returncode == 0
    assert git("commit", "-q", "-m", "seed", cwd=root).returncode == 0

    hooks = root / "gate-hooks"
    hooks.mkdir()
    hook = hooks / "pre-commit"
    # Forward slashes and single quotes: git runs the hook under its bundled
    # sh even on Windows, where a backslash inside double quotes is an escape.
    interpreter = Path(sys.executable).as_posix()
    body = f"#!/bin/sh\nexec '{interpreter}' '{GATE.as_posix()}' --staged\n"
    hook.write_bytes(body.encode("ascii"))
    hook.chmod(0o755)
    assert git("config", "core.hooksPath", "gate-hooks", cwd=root).returncode == 0
    return root


def test_a_staged_world_name_is_blocked_by_a_real_commit(hooked_repo: Path, tmp_path: Path) -> None:
    """C7. The acceptance criterion, end to end, on a SYNTHETIC world value.

    CONVENTIONS.md is explicit that a hook's presence is never proof it fires;
    the only valid test is to stage a violation, attempt a real commit and
    assert HEAD is unchanged. The value staged here is built in this file and
    exists on no machine - the operator's real world name is never written
    into any repository, throwaway or not.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = SYNTHETIC_WORLD_NAME

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    assert before

    write(hooked_repo / "world.md", "played " + SYNTHETIC_WORLD_NAME + " tonight\n")
    assert git("add", "world.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a world note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()

    assert attempt.returncode != 0, attempt.stdout
    assert "world name discovered on this machine" in attempt.stderr
    assert after == before, "HEAD MOVED - the commit was not blocked"


def test_a_staged_world_token_is_blocked_by_a_real_commit(
    hooked_repo: Path, tmp_path: Path
) -> None:
    """C7, the token half. Same route, same synthetic-only rule."""
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_TOKENS"] = SYNTHETIC_WORLD_ID

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    write(hooked_repo / "ledger.md", "keyed by " + SYNTHETIC_WORLD_ID + "\n")
    assert git("add", "ledger.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a ledger note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()

    assert attempt.returncode != 0, attempt.stdout
    assert "world token for this machine" in attempt.stderr
    assert after == before, "HEAD MOVED - the commit was not blocked"


def test_the_same_commit_succeeds_when_no_world_value_is_discoverable(
    hooked_repo: Path, tmp_path: Path
) -> None:
    """The control for the two tests above, and it is not optional.

    Without it, a hook that failed for ANY reason - a bad interpreter, a
    missing gate, a broken shebang - would make both blocking tests green
    while proving nothing at all. This asserts the same repo, the same hook
    and the same content DO commit once the world value is undiscoverable.
    """
    env = base_env(tmp_path)

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    write(hooked_repo / "world.md", "played " + SYNTHETIC_WORLD_NAME + " tonight\n")
    assert git("add", "world.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a world note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()

    assert attempt.returncode == 0, attempt.stdout + attempt.stderr
    assert after != before, "HEAD did not move; the hook blocked a clean commit"


# ==========================================================================
# CS-202-B - no exception is rendered into a message, by any syntax
# ==========================================================================
#
# On Windows, str() on an OSError appends the FILENAME it failed on, and that
# filename routinely carries the account name and the home directory. An error
# message is an echo path exactly like a debug dump (CLAUDE.md non-negotiable
# 12). The renderings in this file use three different formatting syntaxes -
# f-string, percent and .format - so an assertion written against one shape
# would miss the other two. These are written against the OUTPUT instead.
#
# The diagnostic LABEL still carries the path, deliberately: that channel is
# CS-204 and is not in scope here. So the tests count occurrences rather than
# asserting absence - the label may carry it once, the reason may not repeat it.


def leak_target(tmp_path: Path, name: str, text: str | None = None) -> Path:
    """Place a file under a uniquely named directory, for occurrence counting.

    The marker goes in BOTH the directory and the basename. The basename copy
    is what survives the CS-204 label redaction and keeps the count assertion
    non-vacuous; the directory copy is what makes a raw-path echo count two.
    """
    target = tmp_path / LEAK_MARKER / (LEAK_MARKER + "_" + name)
    target.parent.mkdir(parents=True, exist_ok=True)
    if text is not None:
        target.write_bytes(text.encode("utf-8"))
    return target


def assert_path_is_rendered_once_per_line(stderr: str) -> None:
    """Every diagnostic line may name the path ONCE, in its label, and no more.

    Counted per line rather than over the whole stream, because one file can
    produce several diagnostics and each is entitled to its own label. A
    stream-wide count would read two legitimate labels as a leak, which is how
    a test ends up asserting the wrong thing and being "fixed" by loosening it.
    """
    lines = stderr.splitlines()
    assert any(LEAK_MARKER in line for line in lines), "nothing named the path; test is vacuous"
    for line in lines:
        assert line.count(LEAK_MARKER) <= 1, line


def test_oserror_rendering_does_not_repeat_the_path(tmp_path: Path) -> None:
    """D2, OSError. The measured leak: str(exc) appends the filename.

    Before the fix this reads
        <label>:0:0: IO could not read the file: [Errno 2] ...: '<full path>'
    with the absolute path rendered a second time, backslashes and all.
    """
    missing = leak_target(tmp_path, "does-not-exist.py")
    result = run_gate("--files", str(missing), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "could not read the file" in result.stderr
    assert_path_is_rendered_once_per_line(result.stderr)


def test_syntax_error_rendering_does_not_repeat_the_path(tmp_path: Path) -> None:
    """D2, SyntaxError. compile() is handed the label, and str(exc) echoes it."""
    target = leak_target(tmp_path, "broken.py", "def broken(:\n    return 1\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "python syntax error" in result.stderr
    assert_path_is_rendered_once_per_line(result.stderr)


def test_nul_byte_source_blocks_without_repeating_the_path(tmp_path: Path) -> None:
    """A NUL byte in a .py file is the one input that reaches compile() unhappy.

    MEASURED on the interpreter this suite runs under: compile() answers a NUL
    byte with SyntaxError("source code string cannot contain null bytes"), NOT
    with ValueError. Older interpreters raised ValueError here, which is why
    the gate still catches it, but the branch is unreachable on this floor. So
    this asserts the property that holds either way - it blocks, and the path
    is not rendered twice - and the ValueError rendering itself is pinned
    directly in test_exception_renderer_handles_a_value_error.

    The file is NOT called nul.py. "nul" is a reserved device name on Windows,
    so that path resolves to the null device and the read fails with "Incorrect
    function" long before compile() is reached, sending the test down the
    OSError branch and proving nothing at all.
    """
    target = leak_target(tmp_path, "has_nul_byte.py")
    target.write_bytes(b"VALUE = 1\x00\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "BINARY" in result.stderr
    assert_path_is_rendered_once_per_line(result.stderr)


def test_exception_renderer_handles_a_value_error() -> None:
    """D2, ValueError.

    It carries no strerror either, so the same strerror-shaped helper would
    fall through to the full str() here too.
    """
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "mod.py"
    rendered = gate.safe_exc_text(ValueError(leaked))

    assert "someoperator" not in rendered
    assert rendered


def test_exception_renderer_strips_the_filename_from_an_oserror() -> None:
    """D2, per TYPE. strerror carries the reason; str() carries the path too."""
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "world.sav"
    rendered = gate.safe_exc_text(OSError(2, "No such file or directory", leaked))

    assert "someoperator" not in rendered
    assert "No such file or directory" in rendered


def test_exception_renderer_strips_the_filename_from_a_syntax_error() -> None:
    """D2, SyntaxError.

    The end-to-end sibling of this test is green even before the fix, because
    compile() always sets .msg and the leaking `or exc` fallback beside it is
    therefore unreachable in practice. Unreachable is not absent: a SyntaxError
    with no .msg renders as "<msg> (<filename>, line N)" and the filename is
    the path handed to compile(). This provokes that branch directly.
    """
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "mod.py"
    exc = SyntaxError("", (leaked, 1, 1, "def broken(:\n"))
    rendered = gate.safe_exc_text(exc)

    assert "someoperator" not in rendered
    assert rendered


def test_exception_renderer_handles_a_subprocess_error_with_no_strerror() -> None:
    """D2, SubprocessError.

    It has no strerror, so a strerror-shaped helper falls through to the full
    str() - the exact leak being fixed.
    """
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "python.exe"
    rendered = gate.safe_exc_text(subprocess.SubprocessError(leaked))

    assert "someoperator" not in rendered
    assert rendered


def test_exception_renderer_handles_a_timeout_carrying_the_argv() -> None:
    """D2. TimeoutExpired renders its whole command line, argv included."""
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.md"
    rendered = gate.safe_exc_text(subprocess.TimeoutExpired(["ruff", leaked], 90))

    assert "someoperator" not in rendered
    assert rendered


def test_exception_renderer_handles_a_called_process_error() -> None:
    """D2. CalledProcessError renders its argv the same way."""
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.md"
    rendered = gate.safe_exc_text(subprocess.CalledProcessError(2, ["git", "show", leaked]))

    assert "someoperator" not in rendered
    assert rendered


def test_exception_renderer_handles_a_bare_exception() -> None:
    """D2. The fallback must never be the unfiltered str() of an unknown type."""
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.md"
    rendered = gate.safe_exc_text(RuntimeError(leaked))

    assert "someoperator" not in rendered
    assert rendered


def test_git_error_message_carries_no_caller_supplied_argument() -> None:
    """D2, GitError. Its message is BUILT by the gate at the failure site.

    The message that reaches the diagnostic is assembled from the argv, and in
    --files mode the caller supplies the paths that argv is derived from. Only
    the subcommand - a fixed literal - belongs in a message.
    """
    gate = load_gate()
    leaked = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.md"
    error = gate.git_run_error(["show", ":" + leaked], OSError(2, "No such file or directory"))
    rendered = gate.safe_exc_text(error)

    assert "someoperator" not in str(error)
    assert "someoperator" not in rendered
    assert "show" in rendered


def test_the_unreadable_path_verdict_is_unchanged(tmp_path: Path) -> None:
    """D4. This half changes message TEXT and must change no verdict."""
    missing = tmp_path / "does-not-exist.py"
    result = run_gate("--files", str(missing), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "IO" in result.stderr
    assert "could not read the file" in result.stderr


# ==========================================================================
# CS-204 - the LABEL channel is redacted at the render boundary
# ==========================================================================
#
# label_for() deliberately returns an out-of-repo path AS GIVEN, because the
# label is VERDICT-BEARING: it selects which checks run (the extension is
# derived from it), it becomes SyntaxError.filename via compile(), it keys the
# ruff output mapping, it names the staging copy, it is scanned for non-ASCII
# with the column reported as label.index(...) + 1, and it is handed to
# `git show :<label>`. Redacting it there would change verdicts. So the
# redaction lives in emit(), as a pure function of the label, and these tests
# pin BOTH halves: the label keeps its value, the rendered line loses the
# directory.
#
# The oracle is the directory THIS FILE created, never the gate's own redactor
# (module docstring, rule 2) and never a spelled-out home path (CLAUDE.md
# non-negotiable 3). On Windows tmp_path sits under the home directory and on
# Linux under /tmp; both are outside the repository, so the assertions below
# hold identically on either - which is the point of condition 4.

OUTSIDE_DIR = "zzoutsidedirzz"
OUTSIDE_BASE = "zzbasenamezz"

# The literal emit() formats, one per channel.
CHANNEL_CHECKED = "  checked  "
CHANNEL_SKIPPED = "  skipped  "
CHANNEL_NOTE = "  note     "
CHANNEL_DIAGNOSTIC = " CHARSET "


def outside_target(tmp_path: Path, suffix: str, data: bytes | None = None) -> Path:
    """A path outside any repository, marked in BOTH directory and basename.

    Two distinct markers, because the whole point is that one survives the
    redaction and the other does not.
    """
    target = tmp_path / OUTSIDE_DIR / (OUTSIDE_BASE + suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
    if data is not None:
        target.write_bytes(data)
    return target


def assert_channel_is_clean(
    stream: str,
    needle: str,
    tmp_path: Path,
    basename: str,
) -> None:
    """One emit channel names the basename and no directory above it."""
    lines = [line for line in stream.splitlines() if needle in line]
    assert lines, f"no {needle!r} line was emitted; this channel test is vacuous"
    joined = "\n".join(lines)
    assert basename in joined, joined
    assert OUTSIDE_DIR not in joined, joined
    assert str(tmp_path) not in joined, joined
    assert str(tmp_path).replace("\\", "/") not in joined, joined


def test_checked_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 1 of 4: report.checked, printed by emit under --verbose."""
    target = outside_target(tmp_path, ".py", b'"""Doc."""\n\nVALUE = 1\n')
    result = run_gate("--files", str(target), "--verbose", env=base_env(tmp_path))

    assert result.returncode == 0
    assert_channel_is_clean(result.stdout, CHANNEL_CHECKED, tmp_path, OUTSIDE_BASE + ".py")


def test_skipped_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 2 of 4: report.skipped, printed by emit under --list-skipped."""
    target = outside_target(tmp_path, ".png", b"not really a png\n")
    result = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 0
    assert_channel_is_clean(result.stdout, CHANNEL_SKIPPED, tmp_path, OUTSIDE_BASE + ".png")


def test_notes_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 3 of 4: report.notes - the channel the acceptance criterion missed.

    Provoked WITHOUT ruff, so this cannot go vacuous on a machine where ruff is
    absent: invalid UTF-8 in a text file makes decode_for_report return a note,
    which emit prints on the blocked path.
    """
    target = outside_target(tmp_path, ".md", b"alpha \xff beta\n")
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "decoded as latin-1" in result.stderr
    assert_channel_is_clean(result.stderr, CHANNEL_NOTE, tmp_path, OUTSIDE_BASE + ".md")


def test_ruff_style_note_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 3 again, second shape: the label is EMBEDDED mid-string here.

    `ruff (style, not blocking) <label>:<row>:<col>: ...` puts the label after
    a fixed prefix rather than at the start, so a fix that only handles the
    leading-label shape passes the test above and fails this one.
    """
    target = outside_target(tmp_path, ".py", b"import os\nVALUE = 1\n")
    result = run_gate("--files", str(target), "--verbose", env=base_env(tmp_path))

    if "ruff (style" not in result.stdout:
        pytest.skip("ruff produced no style finding; nothing to assert here")
    assert result.returncode == 0
    assert_channel_is_clean(result.stdout, "ruff (style", tmp_path, OUTSIDE_BASE + ".py")


def test_diagnostics_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 4 of 4: Diagnostic.render(), printed to stderr."""
    body = ("# T\n\nAlpha " + EM_DASH + " beta\n").encode("utf-8")
    target = outside_target(tmp_path, ".md", body)
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert ":3:7: CHARSET" in result.stderr
    assert_channel_is_clean(result.stderr, CHANNEL_DIAGNOSTIC, tmp_path, OUTSIDE_BASE + ".md")


def test_label_for_still_returns_the_out_of_repo_path_unchanged(tmp_path: Path) -> None:
    """Condition 1, the boundary: the VALUE is untouched, the RENDERING is not.

    This is the test that would catch a fix applied in the wrong place. If
    someone moves the redaction into label_for or Unit.label, the eight
    verdict-bearing call sites start seeing a different string and this goes
    red - which is the entire reason the grant put the redaction in emit.
    """
    gate = load_gate()
    target = outside_target(tmp_path, ".py", b"VALUE = 1\n")

    label = gate.label_for(str(target))

    assert label == str(target).replace("\\", "/")
    assert OUTSIDE_DIR in label
    assert OUTSIDE_BASE + ".py" in label
    assert gate.display_label(label) != label


def test_display_label_does_not_depend_on_the_home_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Condition 4, determinism.

    A home-keyed redactor renders differently depending on where the machine's
    home directory sits, which makes a tmp_path-based test green in CI and red
    locally, or the reverse. The rendered shape is pinned against a constant
    here, under three different home directories and both path spellings.
    """
    gate = load_gate()
    posix_absolute = "/var/somewhere/" + OUTSIDE_DIR + "/" + OUTSIDE_BASE + ".py"
    windows_absolute = "D:/Somewhere/" + OUTSIDE_DIR + "/" + OUTSIDE_BASE + ".py"
    expected = gate.OUTSIDE_REPO_PREFIX + OUTSIDE_BASE + ".py"

    # Assembled, never spelled out. A home path literal in this file is the
    # very thing the gate blocks, and this file is checked by the gate - which
    # is itself a small proof that the redaction matters (non-negotiable 3).
    homes = (
        "/" + "home" + "/one",
        "/" + "home" + "/two",
        "D:" + "/" + "Users" + "/three",
    )

    for home in homes:
        monkeypatch.setenv("HOME", home)
        monkeypatch.setenv("USERPROFILE", home)
        assert gate.display_label(posix_absolute) == expected
        assert gate.display_label(windows_absolute) == expected


def test_display_label_leaves_a_repo_relative_label_alone() -> None:
    """Condition 5: the in-repo label - the common case - is byte-identical."""
    gate = load_gate()

    for label in ("tools/precommit_gate.py", "README.md", "docs/adr/0001-x.md"):
        assert gate.display_label(label) == label


def test_display_label_leaves_the_stdin_label_alone() -> None:
    """Condition 6: the literal <stdin> is not a path and is not redacted."""
    gate = load_gate()

    assert gate.display_label("<stdin>") == "<stdin>"


def test_text_stdin_still_reports_the_stdin_label(tmp_path: Path) -> None:
    """Condition 6, end to end rather than by unit."""
    result = run_gate(
        "--text-stdin",
        "--list-skipped",
        stdin=b"clean ascii text\n",
        env=base_env(tmp_path),
    )

    assert result.returncode == 0
    assert "<stdin>" in result.stdout


def test_a_repo_under_a_home_directory_keeps_its_labels_repo_relative(tmp_path: Path) -> None:
    """The common-mode gap every other test in this file leaves open.

    They all put the FILE outside the repository while the REPOSITORY itself
    stays at a path that is not under any home directory. So the one
    combination that matters most - a repo-relative label whose ABSOLUTE form
    contains the account name - is exercised by nothing. Here HOME and
    USERPROFILE are pointed at the temporary directory and a throwaway repo is
    created inside it, so the repository genuinely sits under a home directory
    on Windows and on Linux alike.

    What must hold: labels stay repo-relative and UNREDACTED, because being
    inside a repository is the whole test, and no absolute path is rendered.

    MEASURED, not assumed: a home-keyed redactor does NOT turn this test red.
    label_for has already made these labels relative, so they do not start
    with the home directory and a home-keyed rule leaves them alone. The one
    test that catches that mistake is
    test_display_label_does_not_depend_on_the_home_directory, verified by
    swapping the real implementation for a home-keyed one and watching exactly
    that test - and only that test - go red. This test covers the other half:
    that a repository sitting under a home directory is still rendered
    relative rather than absolute.
    """
    if shutil.which("git") is None:
        pytest.skip("git is not on PATH")

    repo = tmp_path / "throwaway"
    repo.mkdir()
    for argv in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "t@example.invalid"],
        ["git", "config", "user.name", "t"],
    ):
        subprocess.run(argv, cwd=str(repo), check=True, capture_output=True, timeout=TIMEOUT)

    write(repo / "pkg" / "charset.md", "# T\n\nAlpha " + EM_DASH + " beta\n")
    write(repo / "pkg" / "broken.py", "def broken(:\n    return 1\n")

    env = base_env(tmp_path)
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)

    result = run_gate(
        "--files",
        "pkg/charset.md",
        "pkg/broken.py",
        "--verbose",
        env=env,
        cwd=repo,
    )
    combined = result.stdout + result.stderr

    # Non-vacuous: the run really did produce findings to render.
    assert result.returncode == 1
    assert "SYNTAX" in result.stderr

    # The label is repo-relative and untouched.
    assert "pkg/charset.md:3:7: CHARSET" in result.stderr
    assert load_gate().OUTSIDE_REPO_PREFIX not in combined

    # And no absolute path is rendered anywhere, in any channel.
    assert str(tmp_path) not in combined, combined
    assert str(tmp_path).replace("\\", "/") not in combined, combined


def test_the_gate_imports_only_the_standard_library() -> None:
    """Condition 7: no new dependency, proven from the import graph.

    Running the gate puts tools/ on sys.path, not the repo root, so an
    `import clockspeed` does not even resolve until the lazy loader puts the
    root there itself. Asserted against the parsed AST rather than the text,
    because the docstrings name the package.

    CS-403 REMOVED the walk-level "clockspeed appears nowhere" assertion that
    used to sit here, because the gate now reaches the header parser through
    one function-local import. What replaced it is not weaker, it is more
    specific: the module-scope rung below still admits stdlib only, and
    test_the_package_import_is_function_local_and_never_at_module_scope
    asserts every package import sits inside a function body AND that at least
    one exists, so the surface cannot silently vanish either.
    """
    tree = ast.parse(GATE.read_bytes().decode("utf-8"))

    def roots(nodes: list[ast.stmt] | list[ast.AST]) -> set[str]:
        found: set[str] = set()
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0])
        return found

    # MODULE SCOPE is the rung that matters for a dependency: those imports run
    # at startup, so a missing one stops the gate from starting at all. `ruff`
    # is imported inside ruff_command() as a guarded probe and is deliberately
    # not counted here - the gate treats a machine without ruff as fail-open.
    assert roots(tree.body) <= set(sys.stdlib_module_names), sorted(roots(tree.body))


# ==========================================================================
# CS-209 - a per-value world-name exclusion surface, and a skip channel that
#          prints on the path .githooks/pre-commit actually runs
# ==========================================================================
#
# CS-208 asked for a raised length floor and was DENIED BY MEASUREMENT on
# 2026-08-14: 16 matchable world names exist on the operator's machine and the
# shortest is 4 characters, so any floor at or above 5 drops a REAL world name
# and it then commits. Narrowing a PII blocklist by default is the refuted
# approach. The replacement is an EXPLICIT per-value exclusion the operator
# opts into, one value at a time, in a file that cannot be committed.
#
# Every value below is synthetic and built in this file, per the module
# docstring: the operator's real world name is never written into any
# repository, throwaway or not, and never asserted on.

SECOND_WORLD_NAME = "Qvarnholt" + "Basin"

# The exclusion key and the environment override that shadows it. Named here
# so a rename in the gate turns these tests red instead of silently leaving
# the remedy sentence pointing at a key that no longer exists.
EXCLUSIONS_CONFIG_KEY = "world_name_exclusions"
EXCLUSIONS_ENV = "CLOCKSPEED_WORLD_NAME_EXCLUSIONS"


def local_config_env(tmp_path: Path, payload: str) -> dict[str, str]:
    """base_env plus a real config/local.json holding `payload`."""
    config = tmp_path / "local.json"
    write(config, payload)
    env = base_env(tmp_path)
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(config)
    return env


def test_an_excluded_world_name_is_dropped_after_discovery(tmp_path: Path) -> None:
    """CS-209 acceptance, first clause.

    The value is DISCOVERED - it reaches the gate through the same
    `world_names` source as any other - and is then dropped by name. The drop
    happens after discovery rather than by narrowing the discovery filter,
    which is exactly the distinction CS-208's denial turned on.
    """
    env = local_config_env(
        tmp_path,
        '{"world_names": "%s", "%s": "%s"}\n'
        % (SYNTHETIC_WORLD_NAME, EXCLUSIONS_CONFIG_KEY, SYNTHETIC_WORLD_NAME),
    )
    target = write(tmp_path / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")

    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert EXCLUSIONS_CONFIG_KEY in result.stdout, result.stdout


def test_the_exclusion_is_per_value_and_leaves_its_siblings_matching(tmp_path: Path) -> None:
    """The non-vacuity control, and it is what makes the test above mean anything.

    Without it, an exclusion surface that dropped EVERY world name would pass
    the first test while silently disabling the check - which is the failure
    mode CS-208 was denied for. Two names are declared, one is excluded, and
    the other must still block.
    """
    env = local_config_env(
        tmp_path,
        '{"world_names": "%s,%s", "%s": "%s"}\n'
        % (
            SYNTHETIC_WORLD_NAME,
            SECOND_WORLD_NAME,
            EXCLUSIONS_CONFIG_KEY,
            SYNTHETIC_WORLD_NAME,
        ),
    )
    target = write(tmp_path / "note.md", "the " + SECOND_WORLD_NAME + " save\n")

    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world name discovered on this machine" in result.stderr


def test_the_exclusion_skip_never_echoes_the_excluded_value(tmp_path: Path) -> None:
    """CS-209 acceptance: reported WITHOUT echoing the value.

    A world name is personal data (CLAUDE.md non-negotiable 3) and a skip line
    that prints what it skipped is an echo path exactly like a debug dump
    (non-negotiable 12). The oracle is independent of the gate: the value is
    built in this file, so what it is is known before the gate ever sees it.
    """
    env = local_config_env(
        tmp_path,
        '{"world_names": "%s", "%s": "%s"}\n'
        % (SYNTHETIC_WORLD_NAME, EXCLUSIONS_CONFIG_KEY, SYNTHETIC_WORLD_NAME),
    )
    target = write(tmp_path / "clean.md", "nothing to see\n")

    result = run_gate("--files", str(target), "--verbose", "--list-skipped", env=env)
    combined = result.stdout + result.stderr

    assert result.returncode == 0, result.stderr
    assert EXCLUSIONS_CONFIG_KEY in combined
    assert SYNTHETIC_WORLD_NAME not in combined, combined
    assert SYNTHETIC_WORLD_NAME.lower() not in combined.lower(), combined


def test_the_exclusion_matches_case_insensitively_like_the_matcher(tmp_path: Path) -> None:
    """An exclusion that is case SENSITIVE does not actually exclude.

    World names are matched with re.IGNORECASE, so a blocklist entry differing
    only in case still blocks. An exclusion surface that folded differently
    from the matcher it is exempting would read as working and do nothing.
    """
    env = local_config_env(
        tmp_path,
        '{"world_names": "%s", "%s": "%s"}\n'
        % (SYNTHETIC_WORLD_NAME, EXCLUSIONS_CONFIG_KEY, SYNTHETIC_WORLD_NAME.upper()),
    )
    target = write(tmp_path / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")

    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 0, result.stderr


def test_the_exclusion_reads_the_environment_like_every_other_surface(tmp_path: Path) -> None:
    """The override precedence every other declared value already has.

    declared_values reads the environment first and the config second. An
    exclusion that read only one of the two would be the single surface in
    this file behaving differently from its five siblings.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = SYNTHETIC_WORLD_NAME
    env[EXCLUSIONS_ENV] = SYNTHETIC_WORLD_NAME
    target = write(tmp_path / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")

    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 0, result.stderr


def test_excluding_every_name_does_not_advise_declaring_one(tmp_path: Path) -> None:
    """Found by reading a real end-to-end transcript, not by reasoning.

    When the only discovered name is excluded, `found` is empty and the
    "nothing is discoverable, set CLOCKSPEED_WORLD_NAMES" skip used to fire
    directly beneath the exclusion skip. Its ADVICE is false in that state -
    the operator HAS declared a name, and following the advice would change
    nothing. Two skip lines that contradict each other teach a reader to stop
    reading the channel, which is the one thing CS-209 cannot afford, since
    printing that channel on the authoritative path is the whole item.
    """
    env = local_config_env(
        tmp_path,
        '{"world_names": "%s", "%s": "%s"}\n'
        % (SYNTHETIC_WORLD_NAME, EXCLUSIONS_CONFIG_KEY, SYNTHETIC_WORLD_NAME),
    )
    target = write(tmp_path / "clean.md", "nothing to see\n")

    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert EXCLUSIONS_CONFIG_KEY in result.stdout, result.stdout
    assert "no world name is discoverable" not in result.stdout, result.stdout


def test_the_undiscoverable_advice_still_fires_when_nothing_was_excluded(
    tmp_path: Path,
) -> None:
    """The control. Suppressing that line unconditionally would hide a real gap.

    On a machine with no game, no override and no config the advice is correct
    and is the only thing telling the operator the world check is inert.
    """
    target = write(tmp_path / "clean.md", "nothing to see\n")

    result = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert "no world name is discoverable" in result.stdout, result.stdout


def test_the_world_name_diagnostic_names_the_exclusion_key_as_the_remedy(
    tmp_path: Path,
) -> None:
    """CS-209 acceptance, second clause.

    A diagnostic that says "this is personal data" and stops leaves the
    operator with a red gate and no move. The remedy names the key, and it
    must not name the VALUE.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = SYNTHETIC_WORLD_NAME
    target = write(tmp_path / "note.md", "the " + SYNTHETIC_WORLD_NAME + " save\n")

    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world name discovered on this machine" in result.stderr
    assert EXCLUSIONS_CONFIG_KEY in result.stderr, result.stderr


def test_a_coverage_skip_prints_with_neither_verbose_nor_list_skipped(tmp_path: Path) -> None:
    """CS-209 acceptance, third clause, at the unit rung.

    .githooks/pre-commit runs the gate with NEITHER flag. Until now `emit`
    printed the skipped channel only under one of them, so the gate's own
    claim that a dropped value stays visible per CONVENTIONS section 15.1 was
    FALSE on the authoritative path. The end-to-end proof is below; this pins
    the same property without a repository in the way.
    """
    env = local_config_env(
        tmp_path,
        '{"world_names": "%s", "%s": "%s"}\n'
        % (SYNTHETIC_WORLD_NAME, EXCLUSIONS_CONFIG_KEY, SYNTHETIC_WORLD_NAME),
    )
    target = write(tmp_path / "clean.md", "nothing to see\n")

    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 0, result.stderr
    assert EXCLUSIONS_CONFIG_KEY in result.stdout, result.stdout


def test_a_file_level_skip_still_needs_a_flag(tmp_path: Path) -> None:
    """The other half of the rule, and it is what keeps the change honest.

    Only COVERAGE skips - the ones saying the gate's own detection was
    reduced - print unconditionally. A per-file skip says a unit was not read,
    its count is already on the PASS line, and printing every one of them on
    every commit is how a gate becomes noise and then gets turned off.
    """
    target = write(tmp_path / "picture.png", "not really a png\n")

    quiet = run_gate("--files", str(target), env=base_env(tmp_path))
    loud = run_gate("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert quiet.returncode == 0, quiet.stderr
    assert loud.returncode == 0, loud.stderr
    assert "picture.png" in loud.stdout, loud.stdout
    assert "picture.png" not in quiet.stdout, quiet.stdout


def test_the_coverage_skip_channel_prints_through_a_real_commit(
    hooked_repo: Path, tmp_path: Path
) -> None:
    """CS-209 acceptance, third clause, END TO END and with NO flags passed.

    This is the hole CS-209 exists to close. Every other test in this suite
    hands the gate --verbose or --list-skipped explicitly, so nothing in the
    tree asserted what the hook actually prints. The hook here runs `--staged`
    and nothing else, exactly as .githooks/pre-commit does.

    Both halves are asserted through one commit because they are one claim:
    the excluded name does NOT block (HEAD moves), and the exemption is still
    VISIBLE (the skip reason is printed) rather than silently applied.

    HOME and USERPROFILE point at the temporary directory, so the throwaway
    repository genuinely sits under a home directory on Windows and on Linux
    alike and no absolute path may be rendered.
    """
    config = tmp_path / "local.json"
    write(
        config,
        '{"world_names": "%s", "%s": "%s"}\n'
        % (SYNTHETIC_WORLD_NAME, EXCLUSIONS_CONFIG_KEY, SYNTHETIC_WORLD_NAME),
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(config)
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    assert before

    write(hooked_repo / "world.md", "played " + SYNTHETIC_WORLD_NAME + " tonight\n")
    assert git("add", "world.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a world note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    combined = attempt.stdout + attempt.stderr

    assert attempt.returncode == 0, combined
    assert after != before, "HEAD did not move; the exclusion did not take"
    assert EXCLUSIONS_CONFIG_KEY in combined, combined
    assert SYNTHETIC_WORLD_NAME not in combined, combined
    assert str(tmp_path) not in combined, combined


def test_the_same_commit_is_blocked_without_the_exclusion(
    hooked_repo: Path, tmp_path: Path
) -> None:
    """The control for the commit above. Same repo, same hook, same content.

    Without this, an exclusion surface that did nothing at all - or a hook
    that never ran - would make that test green while proving nothing.
    """
    config = tmp_path / "local.json"
    write(config, '{"world_names": "%s"}\n' % SYNTHETIC_WORLD_NAME)
    env = base_env(tmp_path)
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(config)

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    write(hooked_repo / "world.md", "played " + SYNTHETIC_WORLD_NAME + " tonight\n")
    assert git("add", "world.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a world note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()

    assert attempt.returncode != 0, attempt.stdout
    assert "world name discovered on this machine" in attempt.stderr
    assert after == before, "HEAD MOVED - the commit was not blocked"


# ==========================================================================
# CS-403 - the world-TOKEN half of CS-201, now that a header parser exists
# ==========================================================================
#
# A world token lives inside the save HEADER and cannot be recovered from a
# filename, so until CS-400 landed the gate could only match a token the
# operator had DECLARED, and an undeclared one committed unblocked. The gate
# now reads the header - through a LAZY, function-local import that falls back
# to a printed skip on ANY exception.
#
# THE CONSTRAINT THAT SHAPES ALL OF IT, from the grant: a gate that cannot
# START does not block, so nothing here may add a new way for the gate to fail
# to start. That is why the import is function-local, why it is wrapped, and
# why four of the tests below are about the gate SURVIVING rather than about
# it blocking.
#
# The seam is not violated: docs/ARCHITECTURE.md:144 prohibits clockspeed/
# importing tools/ and NOT the reverse, and tools/drift_guard.py already
# lazily imports clockspeed.data.* and records that direction as correct.

# 22 characters, the measured token length, assembled rather than spelled out
# and existing on no real machine.
HEADER_WORLD_TOKEN = "Hdr7Kq" + "2Xn9Tb" + "4Lm6Wz" + "8Rc"

# The .sav basename the synthetic save is written under. Deliberately NOT a
# substring of any staged content below, so a block can only be attributed to
# the TOKEN read out of the header and never to the world NAME the basename
# also yields.
HEADER_SAVE_STEM = "Bramblewick" + "Hollow"


def synthetic_save_bytes(world_token: str) -> bytes:
    """A parseable save carrying `world_token`, built by the shared builder.

    tests/save/synthetic.py is the repository's one save builder and it imports
    only the standard library, so reusing it adds no dependency here. Building
    a second header layout inline would be a second answer waiting to disagree
    with clockspeed/save/header.py - the exact duplication the honest-limit
    note in the gate used to warn about.

    The four magic bytes matter: parse_header refuses a header with fewer than
    four bytes left at body_offset, because the seam it promises would then be
    unverifiable.
    """
    # Both imports are kept function-local, and the top-level-import rule is
    # suppressed on each: importing this module must still cost nothing on a
    # machine where tests/save is unavailable, which is the standalone
    # property the module docstring claims for this suite.
    import struct  # noqa: PLC0415

    from tests.save import synthetic  # noqa: PLC0415

    return synthetic.build_header(world_token=world_token) + struct.pack(
        "<I", synthetic.CHUNK_MAGIC
    )


def make_header_save_root(tmp_path: Path, *tokens: str) -> Path:
    """A save root holding one parseable synthetic save per token."""
    save_root = make_save_root(tmp_path, FAKE_ACCOUNT_ID)
    for index, token in enumerate(tokens):
        stem = HEADER_SAVE_STEM if index == 0 else "%s%d" % (HEADER_SAVE_STEM, index)
        (save_root / FAKE_ACCOUNT_ID / (stem + ".sav")).write_bytes(synthetic_save_bytes(token))
    return save_root


def test_an_undeclared_token_from_a_save_header_is_blocked(tmp_path: Path) -> None:
    """CS-403's core claim at the unit rung: UNDECLARED, and still matched.

    CLOCKSPEED_WORLD_TOKENS is cleared by base_env, so the only route from the
    save on disk to a blocking diagnostic runs through the header parser.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(make_header_save_root(tmp_path, HEADER_WORLD_TOKEN))

    target = write(tmp_path / "ledger.md", "keyed by " + HEADER_WORLD_TOKEN + "\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "PII" in result.stderr
    assert "world token" in result.stderr


def test_a_token_read_from_a_save_header_is_blocked_by_a_real_commit(
    hooked_repo: Path, tmp_path: Path
) -> None:
    """CS-403 acceptance, END TO END through a real `git commit`.

    Stage a file carrying a token that exists only inside a synthetic save
    header, attempt the real commit, and assert exit non-zero with HEAD
    unchanged. A hook's presence is never proof it fires; this is the only
    test shape that proves the block.

    HOME and USERPROFILE point at the temporary directory so the throwaway
    repository sits under a home directory, and no absolute path may be
    rendered into any channel.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(make_header_save_root(tmp_path, HEADER_WORLD_TOKEN))
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    assert before

    write(hooked_repo / "ledger.md", "keyed by " + HEADER_WORLD_TOKEN + "\n")
    assert git("add", "ledger.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a ledger note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    combined = attempt.stdout + attempt.stderr

    assert attempt.returncode != 0, attempt.stdout
    assert "world token" in attempt.stderr, combined
    assert after == before, "HEAD MOVED - the commit was not blocked"
    assert str(tmp_path) not in combined, combined


def test_the_same_commit_succeeds_with_no_save_root(hooked_repo: Path, tmp_path: Path) -> None:
    """The control. Without it a hook failing for ANY reason reads as a block."""
    env = base_env(tmp_path)

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    write(hooked_repo / "ledger.md", "keyed by " + HEADER_WORLD_TOKEN + "\n")
    assert git("add", "ledger.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a ledger note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()

    assert attempt.returncode == 0, attempt.stdout + attempt.stderr
    assert after != before, "HEAD did not move; the hook blocked a clean commit"


def isolated_gate_copy(tmp_path: Path) -> Path:
    """A copy of the gate whose derived repo root holds no clockspeed package.

    The gate derives its root from its OWN location, so a copy two levels down
    a temporary directory resolves a root that has no package in it. That is
    what makes the package genuinely out of reach rather than merely absent
    from the current working directory.
    """
    isolated = tmp_path / "isolated"
    isolated.mkdir(exist_ok=True)
    copy = isolated / "gate_copy.py"
    copy.write_bytes(GATE.read_bytes())
    return copy


def run_gate_copy(copy: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(copy), *args],
        cwd=str(copy.parent),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


def test_the_gate_starts_and_skips_when_the_package_cannot_be_imported(
    tmp_path: Path,
) -> None:
    """CS-403 acceptance, second clause, and the one the grant cares about most.

    A gate that cannot START does not block. With the package out of reach the
    gate must still run, still exit 0 on a clean file, and PRINT the honest
    skip saying the header was not read - rather than crash, hang, or silently
    pretend the token surface is covered.
    """
    copy = isolated_gate_copy(tmp_path)
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(make_header_save_root(tmp_path, HEADER_WORLD_TOKEN))

    target = write(tmp_path / "isolated" / "clean.md", "nothing to see\n")
    result = run_gate_copy(copy, "--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout, result.stdout
    assert "crashed" not in result.stderr, result.stderr


def test_a_package_that_raises_on_import_is_caught_like_an_absent_one(
    tmp_path: Path,
) -> None:
    """ANY exception, not merely ImportError - stated in the grant that way.

    A half-installed or mid-edit package can raise anything at all while being
    imported. Here the package the gate would reach is a module that raises a
    RuntimeError at import time, which no `except ImportError` would catch.
    """
    copy = isolated_gate_copy(tmp_path)
    write(
        tmp_path / "clockspeed.py",
        "raise RuntimeError('mid-edit package, deliberately unimportable')\n",
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(make_header_save_root(tmp_path, HEADER_WORLD_TOKEN))

    target = write(tmp_path / "isolated" / "clean.md", "nothing to see\n")
    result = run_gate_copy(copy, "--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout, result.stdout
    assert "crashed" not in result.stderr, result.stderr


def test_a_declared_token_still_blocks_with_the_package_out_of_reach(
    tmp_path: Path,
) -> None:
    """The fallback degrades the header source ONLY, never the whole check.

    Without this, a fallback that returned an empty token list AND discarded
    the declared ones would pass both tests above while disabling the surface
    CS-201 already shipped.
    """
    copy = isolated_gate_copy(tmp_path)
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_TOKENS"] = SYNTHETIC_WORLD_ID

    target = write(tmp_path / "isolated" / "ledger.md", "world " + SYNTHETIC_WORLD_ID + "\n")
    result = run_gate_copy(copy, "--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world token" in result.stderr


def test_a_corrupt_save_leaves_the_gate_passing_on_a_clean_file(tmp_path: Path) -> None:
    """CS-403 acceptance, third clause.

    A truncated, half-written or foreign .sav under the save root is the
    NORMAL case, not an error: the game writes during autosave and the gate
    reads whatever is there. Non-negotiable 7 - flagged and skipped, never
    fatal and never silently wrong.
    """
    save_root = make_header_save_root(tmp_path, HEADER_WORLD_TOKEN)
    (save_root / FAKE_ACCOUNT_ID / "Corrupted.sav").write_bytes(b"\x00\xff" * 64)
    (save_root / FAKE_ACCOUNT_ID / "Truncated.sav").write_bytes(
        synthetic_save_bytes(HEADER_WORLD_TOKEN)[:31]
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "crashed" not in result.stderr, result.stderr


def test_a_corrupt_save_does_not_stop_a_readable_sibling_from_blocking(
    tmp_path: Path,
) -> None:
    """The control for the test above.

    A fallback that abandoned the whole scan on the first unreadable save
    would make that test green while quietly turning the header source off for
    any operator with one stale .sav in the directory. The corrupt file sorts
    BEFORE the readable one by name, so it is hit first.
    """
    save_root = make_header_save_root(tmp_path, HEADER_WORLD_TOKEN)
    (save_root / FAKE_ACCOUNT_ID / "Aardvark.sav").write_bytes(b"\x00\xff" * 64)
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)

    target = write(tmp_path / "ledger.md", "keyed by " + HEADER_WORLD_TOKEN + "\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, result.stdout
    assert "world token" in result.stderr


def test_the_header_scan_is_bounded_by_a_file_cap(tmp_path: Path) -> None:
    """The bound the grant asked for, proven by crossing it.

    A directory holding hundreds of rotated autosaves must not turn the commit
    gate into a bulk parser. The cap is read from the gate rather than
    restated here, so raising it in the module does not leave a stale number
    in this file (CLAUDE.md section 4).
    """
    cap = load_gate().MAX_SAVE_HEADER_FILES
    tokens = ["Cap%02dKq2Xn9Tb4Lm6Wz8R" % index for index in range(cap + 2)]
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(make_header_save_root(tmp_path, *tokens))

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 0, result.stderr
    assert "<pii:world>" in result.stdout
    assert "cap" in result.stdout.lower(), result.stdout


def test_the_header_scan_is_bounded_by_a_wall_clock_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other bound. A gate that hangs is a gate that gets turned off.

    Exercised in process with the budget set to zero, because a real timeout
    cannot be provoked deterministically without making the suite slow and
    flaky - and what is under test here is a bound, not a verdict. The verdict
    is covered end to end above.
    """
    gate = load_gate()
    monkeypatch.setattr(gate, "SAVE_HEADER_BUDGET_SECONDS", 0.0)
    monkeypatch.setenv(
        "CLOCKSPEED_SAVE_ROOT", str(make_header_save_root(tmp_path, HEADER_WORLD_TOKEN))
    )
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent.json"))
    monkeypatch.delenv("CLOCKSPEED_WORLD_TOKENS", raising=False)

    report = gate.Report()
    tokens = gate.discover_world_tokens(report)
    reasons = " ".join(why for _label, why in report.skipped)

    assert HEADER_WORLD_TOKEN not in tokens
    assert "budget" in reasons.lower(), reasons


def test_the_package_import_is_function_local_and_never_at_module_scope() -> None:
    """The failure-to-start guarantee, structurally.

    An `import clockspeed` at MODULE scope runs before main() and takes the
    gate down with the package - which is the one failure a gate must not
    have, and the reason the CS-201 grant was ruled not to extend to this.
    Asserted against the parsed AST rather than the text, because the
    docstrings name the package and always have.
    """
    tree = ast.parse(GATE.read_bytes().decode("utf-8"))

    inside_a_function: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for inner in ast.walk(node):
                inside_a_function.add(id(inner))

    package_imports = 0
    for node in ast.walk(tree):
        # The `else: continue` is what narrows `node` for the .lineno below;
        # ast.walk yields bare ast.AST, which carries no line number.
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module and node.level == 0 else []
        else:
            continue
        if not any(name.split(".")[0] == "clockspeed" for name in names):
            continue
        package_imports += 1
        assert id(node) in inside_a_function, (
            "an import of the package sits outside a function body, at line %d" % node.lineno
        )

    # Non-vacuous: the assertion above passes trivially if the gate stopped
    # importing the package at all, which would silently drop the CS-403
    # surface. There must be at least one, and it must be function-local.
    assert package_imports >= 1, "the gate no longer reaches the header parser at all"


# ==========================================================================
# CS-209-B - the entry cap keeps the NEWEST saves, and says when it truncates
# ==========================================================================
#
# MAX_SAVE_ROOT_ENTRIES bounds three listings. Before this section it was
# reported at one of the three and silent at the other two, and the silence
# was only half the defect. _save_files ordered the listing BY NAME, applied
# the cap to that order, and only then sorted newest-first - so the truncation
# was alphabetical and the saves it discarded were exactly the recent ones its
# own docstring said had to survive. _world_names_from_saves enumerated an
# UNSORTED iterdir(), so which basename it discarded was whatever order the
# filesystem happened to return.
#
# The consequence was a FAIL-OPEN, which is the one direction a PII gate may
# not fail in: past the cap the gate exits 0 and the commit lands carrying an
# undiscovered world value. It needs no attacker, only time - the game rotates
# autosaves into one directory and the count only grows.
#
# Every value below is synthetic and built in this file. The fixture writes
# more entries than the cap into ONE directory, and the two facts that make
# the tests discriminating are that the real save is the NEWEST and sorts
# alphabetically LAST. A cap that truncates by name drops it; a cap that keeps
# the newest retains it. A test built on a save that sorts early would pass
# against both behaviours and prove nothing.

OVER_CAP_WORLD_TOKEN = "Ovc4Jm" + "8Pz3Rk" + "6Tq1Yb" + "5Nd"

# Sorts after every decoy, and is not a substring of any staged token text, so
# a block can be attributed to the value under test and not to its neighbour.
OVER_CAP_SAVE_STEM = "zzzz" + "Umbral" + "Reach"
OVER_CAP_DECOY_PREFIX = "aaaa_decoy_"


def make_over_cap_save_root(root: Path, token: str) -> Path:
    """A save root whose account directory holds one MORE entry than the cap.

    The real save is written last and then has its mtime pushed forward
    EXPLICITLY. Relying on write order would not be sound: mtime resolution is
    coarse enough that several hundred files written in a fraction of a second
    can share a timestamp, and the test would then turn on a race.
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    save_root = make_save_root(root, FAKE_ACCOUNT_ID)
    account = save_root / FAKE_ACCOUNT_ID
    for index in range(cap):
        (account / (OVER_CAP_DECOY_PREFIX + "%05d.sav" % index)).write_bytes(b"not a save")
    real = account / (OVER_CAP_SAVE_STEM + ".sav")
    real.write_bytes(synthetic_save_bytes(token))
    stamp = time.time() + 3600
    os.utime(real, (stamp, stamp))
    assert len(list(account.iterdir())) == cap + 1
    return save_root


@pytest.fixture(scope="module")
def over_cap_save_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Built once and only ever READ - the gate never writes to a save root."""
    return make_over_cap_save_root(tmp_path_factory.mktemp("overcap"), OVER_CAP_WORLD_TOKEN)


def test_a_token_in_the_newest_save_past_the_entry_cap_is_still_blocked(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The fail-open, at the unit rung. Past the cap the token must still match."""
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "ledger.md", "keyed by " + OVER_CAP_WORLD_TOKEN + "\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, "FAIL-OPEN: the gate passed a staged world token\n" + (
        result.stdout + result.stderr
    )
    assert "world token" in result.stderr, result.stderr


def test_a_world_name_in_the_newest_save_past_the_entry_cap_is_still_blocked(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The same fail-open on the NAME path, which reads basenames rather than headers.

    This one is the worse of the two to leave standing. The cap discards a
    basename with no skip line at all, and the discovery still returns the
    several hundred decoy names, so nothing in any channel is even empty -
    the gate reports a healthy world-name check that has dropped the one name
    that mattered.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "world.md", "played " + OVER_CAP_SAVE_STEM + " tonight\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 1, "FAIL-OPEN: the gate passed a staged world name\n" + (
        result.stdout + result.stderr
    )
    assert "world name" in result.stderr, result.stderr


def test_an_over_cap_listing_reports_the_truncation(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The silence half. A cap that trips has to say so, per CONVENTIONS 15.1."""
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert "most recent were listed" in result.stdout, result.stdout


def test_the_over_cap_truncation_is_reported_with_no_flags_at_all(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """CS-209's own property, applied to this cap.

    .githooks/pre-commit passes neither --verbose nor --list-skipped, so a
    reduction in coverage that only renders under a flag is a reduction nobody
    is ever shown. PII_WORLD_LABEL is a COVERAGE_SKIP_LABEL precisely so this
    class of line survives the flagless invocation.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), env=env)

    assert "most recent were listed" in result.stdout, result.stdout


def test_the_truncation_report_echoes_no_path_and_no_filename(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The skip reason carries COUNTS only.

    A message naming the directory it truncated would print the account id,
    and one naming a dropped save would print the world name - the gate would
    leak, through its own diagnostic, the two values it exists to keep out of
    a commit (CLAUDE.md non-negotiables 3 and 12).
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    truncation = [line for line in result.stdout.splitlines() if "most recent were listed" in line]
    assert truncation, result.stdout
    for line in truncation:
        assert FAKE_ACCOUNT_ID not in line, line
        assert OVER_CAP_SAVE_STEM not in line, line
        assert str(over_cap_save_root) not in line, line
        assert OVER_CAP_DECOY_PREFIX not in line, line


def test_a_token_past_the_entry_cap_is_blocked_by_a_real_commit(
    over_cap_save_root: Path, hooked_repo: Path, tmp_path: Path
) -> None:
    """The acceptance criterion, END TO END, through a real `git commit`.

    This is the shape the adversary used to pin the fail-open: at the cap the
    commit was refused, one entry past it the same commit LANDED. A hook's
    presence is never proof it fires, and passing flags to the gate by hand
    proves something weaker than the hook path does.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)

    before = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    assert before

    write(hooked_repo / "ledger.md", "keyed by " + OVER_CAP_WORLD_TOKEN + "\n")
    assert git("add", "ledger.md", cwd=hooked_repo).returncode == 0

    attempt = git_with_env("commit", "-m", "add a ledger note", cwd=hooked_repo, env=env)
    after = git("rev-parse", "HEAD", cwd=hooked_repo).stdout.strip()
    combined = attempt.stdout + attempt.stderr

    assert attempt.returncode != 0, "FAIL-OPEN: the commit LANDED\n" + combined
    assert "world token" in attempt.stderr, combined
    assert after == before, "HEAD MOVED - the commit was not blocked"
    assert str(tmp_path) not in combined, combined


def test_an_over_cap_directory_does_not_stop_the_gate_starting(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The binding condition on the grant: a gate that cannot START does not block.

    The control for every test above. A clean file under the same over-cap
    save root has to PASS, exit 0, and produce no traceback - otherwise the
    blocking tests could be green because the gate is crashing rather than
    because it is detecting.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), env=env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    assert "crashed" not in result.stderr, result.stderr


# --------------------------------------------------------------------------
# The retention rule at the unit rung, called directly rather than by subprocess
# --------------------------------------------------------------------------


def test_the_listing_retains_the_newest_and_discards_the_oldest(tmp_path: Path) -> None:
    """The ORDERING half, isolated from the reporting half.

    Asserted on WHICH entries survive rather than on how many, because a cap
    that kept the right number of the wrong files would satisfy a count.
    """
    gate = load_gate()
    account = tmp_path / "account"
    account.mkdir()

    cap = gate.MAX_SAVE_ROOT_ENTRIES
    surplus = 8
    # Names and mtimes ascend TOGETHER, which is what makes this corpus able
    # to tell the two candidate behaviours apart. A name-ordered cap keeps
    # save_00000 upward - the OLDEST - and a recency-ordered one keeps the
    # last `cap` names, the NEWEST. The two retained sets are disjoint in
    # exactly the `surplus` entries at each end.
    stamp = time.time()
    for index in range(cap + surplus):
        path = account / ("save_%05d.sav" % index)
        path.write_bytes(b"x")
        os.utime(path, (stamp + index, stamp + index))

    # SLF001 flags a layer reaching past its neighbour. Here the module under
    # test IS the neighbour, and the retention rule has no public surface: the
    # subprocess tests above reach it only through a verdict, which cannot say
    # WHICH entries survived. That distinction is the whole defect.
    kept = gate._save_files(account, None)  # noqa: SLF001
    names = [path.name for path in kept]

    assert len(kept) == cap
    # Newest first: the highest-numbered save is the most recent.
    assert names[0] == ("save_%05d.sav" % (cap + surplus - 1)), names[:3]
    assert names == sorted(names, reverse=True), "the retained set is not newest-first"
    for index in range(surplus):
        assert ("save_%05d.sav" % index) not in names, (
            "an OLDER save displaced a newer one - the cap is still truncating by name"
        )


def test_the_scan_bound_is_reported_when_it_trips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second bound, and it is separate from the retention bound.

    Examining every entry is what makes the retention bound able to keep the
    newest, so a bound on examination is the only remaining way this listing
    can drop a save it never saw. It is set far above any directory the game
    produces, which is why it is provoked here by lowering it rather than by
    writing a directory that large.
    """
    gate = load_gate()
    account = tmp_path / "account"
    account.mkdir()
    for index in range(12):
        (account / ("save_%05d.sav" % index)).write_bytes(b"x")

    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_SCAN", 4)
    report = gate.Report()
    gate._save_files(account, report)  # noqa: SLF001

    reasons = [why for _, why in report.skipped]
    assert any("listing stopped there" in why for why in reasons), reasons


def test_the_scan_bound_sits_above_the_retention_bound() -> None:
    """A scan bound at or below the retention bound would re-fuse the two.

    The whole repair is that one number stopped doing two jobs. If these ever
    met again the listing would truncate before it could rank by recency and
    the fail-open would return, so the relationship is asserted rather than
    left to a reader of two adjacent constants.
    """
    gate = load_gate()
    assert gate.MAX_SAVE_ROOT_SCAN > gate.MAX_SAVE_ROOT_ENTRIES
