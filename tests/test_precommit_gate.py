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
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from tests.git_env import scrub, scrubbed_env

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
    # CS-968: SCRUBBED FIRST. The gate shells out to git, and under a worktree
    # push the pre-push hook hands this suite a GIT_DIR pointing at the real
    # repository. Without this the gate reads THAT index while the arm stages
    # its violation in a throwaway repo, so the gate is asked about a tree the
    # test never wrote to and passes on an empty diff - measured: "PASS - 0
    # checked, 4 skipped" against an arm that requires a block.
    env = scrub(dict(os.environ))
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
        # CS-968: a push from a worktree exports GIT_DIR to the pre-push hook,
        # and this suite runs under that hook. Without the scrub a throwaway
        # `git init` re-initialises the REAL repository as bare.
        env=scrubbed_env(),
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

    THE BLANK LINE AFTER THE IMPORT IS LOAD-BEARING AND IS NOT COSMETIC. CS-838
    made the gate run `ruff format --check`, and without that line this fixture
    is format-DIRTY, so the gate blocks it and the exit-code assertion below
    fails. The line is the MINIMAL repair on purpose: killing the unused import
    instead would have removed the F401 that produces the `ruff (style` finding
    this test is about, and the guard below would then have SKIPPED the test
    rather than failed it - a coverage reduction wearing the shape of a pass.
    """
    target = outside_target(tmp_path, ".py", b"import os\n\nVALUE = 1\n")
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
        subprocess.run(
            argv,
            cwd=str(repo),
            check=True,
            capture_output=True,
            timeout=TIMEOUT,
            # CS-968: without this the init and both config writes land in
            # whatever GIT_DIR names, which under a worktree push is the real
            # repository. Measured on a decoy: it acquired core.bare and this
            # identity.
            env=scrubbed_env(),
        )

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
# The seam is not violated: docs/ARCHITECTURE.md:148 prohibits clockspeed/
# importing tools/ and NOT the reverse, and tools/drift_guard.py already
# lazily imports clockspeed.data.* and records that direction as correct.

# Assembled rather than spelled out, and existing on no real machine. It is 21
# characters and NOT the measured 22, which the comment here used to claim -
# measured against len() rather than re-read. Nothing in the parsed route cares:
# the header carries an identifier of any length and flags an unmeasured one
# rather than refusing it. The CS-1087 arms at the end of this file need the
# exact length and spell their own token for that reason.
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
    a temporary directory resolves a root that has no package in it.

    THAT IS NECESSARY AND IT IS NOT SUFFICIENT, which this docstring asserted
    for one session and CI falsified. It used to say the copy makes the package
    "genuinely out of reach"; it does not, because an EDITABLE INSTALL puts
    clockspeed in site-packages and site-packages is reachable from every
    directory. The suite passed on a developer machine with no install and
    failed on CI, which installs the package with `pip install -e`. Reaching
    past the derived root is why :func:`run_gate_copy` runs the copy under
    ``-S``; see the reason recorded there.
    """
    isolated = tmp_path / "isolated"
    isolated.mkdir(exist_ok=True)
    copy = isolated / "gate_copy.py"
    copy.write_bytes(GATE.read_bytes())
    return copy


def run_gate_copy(copy: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run an isolated gate copy with SITE-PACKAGES OUT OF REACH.

    ``-S`` is what makes the isolation real rather than nominal. Without it the
    package-unreachable tests assert nothing on any machine that has clockspeed
    installed: the import they expect to fail SUCCEEDS from site-packages, no
    skip is printed, and the assertion that a skip appears is the thing that
    fails. That is not hypothetical - it is how CI went red while the same
    suite was green locally, the difference being `pip install -e`.

    It is safe here because the gate's module-scope imports are standard
    library only, which `test_the_gate_imports_only_the_standard_library`
    asserts by AST. ruff is located on PATH and run as a subprocess rather than
    imported, so it is unaffected. A shadow planted on PYTHONPATH or in the
    working directory still imports under ``-S``, which is what the
    raises-on-import sibling needs.
    """
    proc = subprocess.run(
        [sys.executable, "-S", str(copy), *args],
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


def test_an_over_bound_header_population_blocks_a_real_gate_process(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The bound proven by crossing it, and CS-1083 at the EXIT CODE.

    A directory holding hundreds of rotated autosaves must not turn the commit
    gate into a bulk parser, and the bound that stops it must not be invisible
    at the exit status. THIS EXACT RUN used to print the truncation line and
    then `precommit_gate: PASS` and exit 0, which is the whole of CS-1083: a
    reviewer read that PASS as evidence the world-token check had run.

    It reads the shared over-cap fixture rather than building its own corpus,
    so crossing the bound costs nothing here, and no number is restated in
    this file (CLAUDE.md section 4).

    The stderr channel is checked for a leak in the same run. The diagnostic
    is new text on a channel that is printed to a terminal and pasted into
    issues, so it is an echo path exactly like the skip line beside it
    (non-negotiables 3 and 12) and it carries counts and subject words only.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "PASS" not in result.stdout, result.stdout
    assert "<pii:world>" in result.stdout
    assert "did not cover this machine's whole save population" in result.stderr, result.stderr
    for line in result.stderr.splitlines():
        assert FAKE_ACCOUNT_ID not in line, line
        assert str(over_cap_save_root) not in line, line


# --------------------------------------------------------------------------
# CS-436 - the wall-clock budget is graded as a BOUND, not as a constant
# --------------------------------------------------------------------------
#
# The test that stood here set SAVE_HEADER_BUDGET_SECONDS to 0.0 and asserted
# the word "budget" appeared in a skip reason. It would have passed against an
# unconditional break on the first file, so it graded the constant's existence
# and never the bound. Its first replacement asserted the OPPOSITE property -
# that every save below the file cap is read - which is only true while the
# budget is unspent, and it went in beside a removal of the budget that was a
# coverage reduction (see the fence beside SAVE_HEADER_BUDGET_SECONDS).
#
# Both arms below are needed and neither is redundant. The SPENT arm proves
# reads stop; without the UNSPENT arm an unconditional break passes it. The
# UNSPENT arm proves reads continue; without the SPENT arm a bound that never
# fires passes it. A read COUNT is what discriminates them, so the reader is
# injected at the _load_header_reader seam and counts itself.


class CountingReader:
    """A stand-in for the save-header reader that COUNTS and can SLEEP.

    Injected at the _load_header_reader seam rather than by making real I/O
    slow, so the measurement is deterministic and the suite does not become a
    stopwatch. It parses nothing, which is why the fixture below can be empty
    files: what is under test is the LOOP, not the parser.
    """

    def __init__(self, token: str, per_read: float) -> None:
        """Record the token to hand back and the cost to charge per read."""
        self.token = token
        self.per_read = per_read
        self.reads = 0

    # ARG002: the path is deliberately unread. This stands in for a reader
    # whose signature takes one, and accepting it is what makes the seam
    # substitutable; opening it would make the fixture bytes matter again.
    def __call__(self, path: Path) -> SimpleNamespace:  # noqa: ARG002
        """Count this read, charge it, and return an object carrying a token."""
        self.reads += 1
        if self.per_read:
            time.sleep(self.per_read)
        return SimpleNamespace(world_token=self.token)


BUDGET_TOKEN = "Bgt5Kq" + "2Xn9Tb" + "4Lm6Wz" + "8Rc"


def make_empty_save_root(tmp_path: Path, count: int) -> Path:
    """A save root holding `count` EMPTY .sav files under one account dir.

    Empty on purpose. CountingReader never opens them, so bytes would only
    slow the fixture down - and a save the loop declines to read is exactly
    what these two tests measure.
    """
    save_root = make_save_root(tmp_path, FAKE_ACCOUNT_ID)
    for index in range(count):
        (save_root / FAKE_ACCOUNT_ID / ("Budgetsave%02d.sav" % index)).write_bytes(b"")
    return save_root


def run_header_scan(
    gate: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    files: int,
    per_read: float,
    budget: float,
) -> tuple[CountingReader, list[str]]:
    """Run the header scan with a counted reader and a pinned budget.

    Returns the reader, so the caller can assert on the READ COUNT, and the
    skip reasons that named the budget.
    """
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(make_empty_save_root(tmp_path, files)))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    monkeypatch.delenv("CLOCKSPEED_WORLD_TOKENS", raising=False)
    monkeypatch.delenv("CLOCKSPEED_ACCOUNT_DIR", raising=False)

    reader = CountingReader(BUDGET_TOKEN, per_read)
    monkeypatch.setattr(gate, "_load_header_reader", lambda: reader)
    monkeypatch.setattr(gate, "SAVE_HEADER_BUDGET_SECONDS", budget)

    report = gate.Report()
    gate._world_tokens_from_headers(report)  # noqa: SLF001
    reasons = [why for _label, why in report.skipped if "budget" in why.lower()]
    return reader, reasons


def test_the_header_scan_stops_reading_when_the_time_budget_is_spent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bound BINDS: reads stop short of the files on disk, and it says so.

    A read count strictly below the file count is the assertion the deleted
    test never made. Setting the budget to zero cannot make it - every read
    count from 0 to N satisfies "the budget was reported" - so the budget here
    is deliberately larger than one read and smaller than eight of them.
    """
    gate = load_gate()
    files = 8
    reader, reasons = run_header_scan(
        gate, tmp_path, monkeypatch, files=files, per_read=0.10, budget=0.15
    )

    assert reader.reads < files, "the scan read every file; the budget did not bind"
    assert reasons, "reads stopped without saying why"


def test_the_header_scan_reads_every_save_while_the_time_budget_is_unspent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control, and it is what refutes an unconditional break.

    Same seam, same fixture size, a reader that costs nothing and a budget no
    real run can spend. Every file must be read and no budget line printed -
    so a break that fires regardless of the clock reddens here even though it
    would sail through the test above.
    """
    gate = load_gate()
    files = 8
    reader, reasons = run_header_scan(
        gate, tmp_path, monkeypatch, files=files, per_read=0.0, budget=3600.0
    )

    assert files <= gate.MAX_SAVE_HEADER_FILES, "the fixture must sit below the file cap"
    assert reader.reads == files, "the scan stopped early with the budget unspent"
    assert not reasons, reasons


def test_a_sub_decisecond_budget_is_reported_as_the_value_it_actually_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The skip line must not round the budget it is reporting.

    "%.1f" renders 0.05 as 0.1 and 0.04 as 0.0, so under the old format a
    diagnostic about a bound stated a bound twice the size of the real one, or
    a bound of zero. A gate whose own report of a limit is wrong is the
    false-guarantee class this project rates worse than the bug.
    """
    gate = load_gate()
    budget = 0.05
    _reader, reasons = run_header_scan(
        gate, tmp_path, monkeypatch, files=4, per_read=0.10, budget=budget
    )

    assert reasons, "the budget did not trip, so its rendering was never exercised"
    assert any(str(budget) in why for why in reasons), reasons
    assert not any("0.1 second" in why for why in reasons), reasons


# ==========================================================================
# CS-1083 - an UNCOVERED world-token population is visible at the exit status
# ==========================================================================
#
# THE DEFECT. The world-token scan reported a skip and then TRUNCATED its own
# population whenever a bound tripped, and Report.skip appends only to
# `skipped` while emit() returns 0 whenever `diagnostics` is empty. Nothing on
# the skip channel could reach the exit status, so a commit made while the
# save library sat over the file cap got `precommit_gate: PASS` out of a check
# that had not run. That is <pii:world>, the check that exists to keep a world
# token out of a tracked file (CLAUDE.md non-negotiables 11 and 12), and a
# reviewer reading the PASS line has been told the opposite of the truth.
#
# EVERY ARM HERE IS GRADED OVER THE BOUND, never under it. An arm whose
# fixture sits inside the cap passes for exactly the reason this item exists.
# Each one therefore asserts a READ COUNT strictly below the file count first,
# so a fixture that quietly stopped crossing its bound reddens instead of
# passing. The "must sit below the file cap" assertion in the budget arm above
# is correct THERE, because that arm is about the budget and needs the cap out
# of the way; it is the shape that must not be copied down here.


def world_token_scan(
    gate: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    save_root: Path,
    *,
    per_read: float = 0.0,
) -> tuple[CountingReader, Any]:
    """Run the world-token header scan against one synthetic save root.

    Returns the counted reader, so a caller can prove the population really
    was truncated, and the report, so it can be put through emit() for the
    exit status. The bounds are left for the caller to pin: each arm below
    provokes a DIFFERENT one, and pinning them here would hide which.
    """
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(save_root))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    monkeypatch.delenv("CLOCKSPEED_WORLD_TOKENS", raising=False)
    monkeypatch.delenv("CLOCKSPEED_ACCOUNT_DIR", raising=False)
    reader = CountingReader(BUDGET_TOKEN, per_read)
    monkeypatch.setattr(gate, "_load_header_reader", lambda: reader)
    report = gate.Report()
    gate._world_tokens_from_headers(report)  # noqa: SLF001
    return reader, report


def emit_verdict(
    gate: ModuleType, report: Any, capsys: pytest.CaptureFixture[str]
) -> tuple[int, str, str]:
    """The exit status emit() would hand the hook, plus both of its channels."""
    code = gate.emit(report, False, False)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_a_world_token_population_over_the_file_cap_reaches_the_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CS-1083's acceptance, graded with the population OVER the cap.

    Three files past the cap, so the scan truncates and the tokens past it are
    not matchable. Before the repair that state printed its skip line and then
    `precommit_gate: PASS` and returned 0.
    """
    gate = load_gate()
    cap = 4
    files = cap + 3
    monkeypatch.setattr(gate, "MAX_SAVE_HEADER_FILES", cap)
    reader, report = world_token_scan(
        gate, tmp_path, monkeypatch, make_empty_save_root(tmp_path, files)
    )

    assert reader.reads < files, "the fixture did not cross the cap, so this arm is vacuous"
    code, out, err = emit_verdict(gate, report, capsys)
    assert code == 1, out
    assert "PASS" not in out, out
    assert "BLOCKED" in err, err


def test_a_world_token_population_inside_the_file_cap_still_reaches_a_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The known-good control that makes the arm above a measurement.

    Same seam and same fixture shape, with a population no bound truncates. An
    implementation that blocks unconditionally satisfies the arm above and
    reddens here, and without this one there is nothing to tell the two apart.
    """
    gate = load_gate()
    files = 4
    monkeypatch.setattr(gate, "MAX_SAVE_HEADER_FILES", files * 2)
    reader, report = world_token_scan(
        gate, tmp_path, monkeypatch, make_empty_save_root(tmp_path, files)
    )

    assert reader.reads == files, "the scan stopped early with every bound unspent"
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 0, out
    assert "PASS" in out, out


def test_the_header_file_cap_admits_every_save_the_listing_retains() -> None:
    """Clause 2 of the CS-1083 grant: COVER the population, do not fail closed.

    Fail-closed is the fallback, and a fallback that fires on an ordinary save
    library is a gate that blocks every commit on the box. The header cap must
    therefore admit at least as many saves as the retention bound keeps, or
    the gate retains a file it then refuses to read and blocks on its own
    bookkeeping. The relationship is asserted rather than left to a reader of
    two adjacent constants, exactly as the scan bound is asserted against the
    retention bound above, and no number is restated (CLAUDE.md section 4).
    """
    gate = load_gate()
    assert gate.MAX_SAVE_HEADER_FILES >= gate.MAX_SAVE_ROOT_ENTRIES


def test_a_spent_header_budget_reaches_the_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The first sibling bound, found by grep rather than named by the item.

    The aggregate budget truncates the same population by a different
    mechanism and reported it through the same silent channel. Clause 3 of the
    grant requires this bound to keep a live refusal path, so it is not
    removed - it is made audible at the exit code.
    """
    gate = load_gate()
    files = 8
    monkeypatch.setattr(gate, "SAVE_HEADER_BUDGET_SECONDS", 0.15)
    reader, report = world_token_scan(
        gate, tmp_path, monkeypatch, make_empty_save_root(tmp_path, files), per_read=0.10
    )

    assert reader.reads < files, "the budget did not bind, so this arm is vacuous"
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 1, out
    assert "PASS" not in out, out


def test_a_truncated_account_directory_listing_reaches_the_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The second sibling: the save-root entry cap degrades this check too.

    _save_root_dirs truncating means the gate did not look under a later
    account directory, so a token there is unmatched. Past that cap an empty
    result means "not looked for" and never "not there" - which is exactly the
    state that must not read as PASS.
    """
    gate = load_gate()
    save_root = make_save_root(tmp_path, "account0000", "account1111", "account2222")
    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_ENTRIES", 1)
    _reader, report = world_token_scan(gate, tmp_path, monkeypatch, save_root)

    reasons = [why for _label, why in report.skipped]
    assert any("the listing stopped there" in why for why in reasons), reasons
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 1, out
    assert "PASS" not in out, out


def test_a_truncated_save_directory_listing_reaches_the_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The third sibling: the per-directory retention bound drops older saves.

    One account directory, so the root listing is untruncated and the only
    bound in play is the retention one inside _bounded_newest_saves.
    """
    gate = load_gate()
    files = 6
    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_ENTRIES", 2)
    reader, report = world_token_scan(
        gate, tmp_path, monkeypatch, make_empty_save_root(tmp_path, files)
    )

    assert reader.reads < files, "the retention bound did not truncate, so this arm is vacuous"
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 1, out
    assert "PASS" not in out, out


def test_an_overscanned_save_directory_reaches_the_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The fourth sibling: the examination bound drops saves it never saw.

    This one is not a retention decision at all - the entries past it were
    never examined, so the gate cannot even say how many it missed.
    """
    gate = load_gate()
    files = 12
    monkeypatch.setattr(gate, "MAX_SAVE_ROOT_SCAN", 4)
    reader, report = world_token_scan(
        gate, tmp_path, monkeypatch, make_empty_save_root(tmp_path, files)
    )

    assert reader.reads < files, "the scan bound did not truncate, so this arm is vacuous"
    reasons = [why for _label, why in report.skipped]
    assert any("the listing stopped there" in why for why in reasons), reasons
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 1, out
    assert "PASS" not in out, out


def test_an_unreadable_save_header_stays_a_skip_and_never_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The one degradation CS-1083 deliberately did NOT make blocking.

    A half-written autosave is the NORMAL case and never fatal (CLAUDE.md
    non-negotiable 7). The six bounds above are the gate's OWN choices not to
    look and every one of them is self-healing - the cap is raised, the budget
    resets on the next run. An unparseable save is the FILE declining to be
    read: blocking there wedges the commit gate permanently on a file the
    gate may never write to or remove
    (non-negotiable 1), and intermittently on every autosave in flight while
    the operator plays. A permanently red gate is a gate that gets bypassed
    with --no-verify, which buys less than the skip line does. This arm pins
    the declination so a later change to it has to be deliberate.

    WHAT IT NO LONGER ARGUES, after CS-1087: that no amount of effort makes
    the file parse. That is still true of PARSING and is beside the point -
    the TOKEN is recoverable from the raw prefix without parsing anything, and
    a recovered one blocks. This fixture is empty files, so there is nothing
    of the identifier's shape at any offset in them and nothing is recovered;
    the declination is what stays pinned here, not the argument under it. The
    recovery itself is graded against a real byte-corrupt save at the end of
    this file.
    """
    gate = load_gate()

    def refuse(path: Path) -> object:  # noqa: ARG001
        raise ValueError("unparseable")

    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(make_empty_save_root(tmp_path, 3)))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    monkeypatch.delenv("CLOCKSPEED_WORLD_TOKENS", raising=False)
    monkeypatch.delenv("CLOCKSPEED_ACCOUNT_DIR", raising=False)
    monkeypatch.setattr(gate, "_load_header_reader", lambda: refuse)

    report = gate.Report()
    gate._world_tokens_from_headers(report)  # noqa: SLF001

    reasons = [why for _label, why in report.skipped]
    assert any("could not be parsed" in why for why in reasons), reasons
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 0, out
    assert "PASS" in out, out


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


# --------------------------------------------------------------------------
# CS-1083 - a LEAK diagnostic is told from a COVERAGE diagnostic by IDENTITY
# --------------------------------------------------------------------------
#
# THE HOLLOWING THIS CLOSES WAS MEASURED, not anticipated. CS-1083 made a
# TRUNCATED world-token population a blocking diagnostic, so under the
# over-bound fixtures below the gate now exits 1 on EVERY run, clean file or
# not - and that diagnostic's own reason ends "...so a world token from an
# older save is not matchable". `returncode == 1` plus `"world token" in
# stderr`, which is what the two CS-436 fail-open arms asserted, is therefore
# satisfied with ZERO detection. Against a mutant replacing
# `found.append(read_header(path).world_token)` with a bare `read_header(path)`
# - world-token detection from headers destroyed outright - both arms reported
# `2 passed`, exit 0.
#
# WHAT MADE THEM POTENT BEFORE was a control that no longer holds: a clean file
# under the SAME fixture used to exit 0, so exit 1 could only come from a
# match. CS-1083 inverted that control, and the arms keyed on it did not notice
# because nothing they asserted changed.
#
# THE SEPARATION IS BY IDENTITY AND NOT BY SUBSTRING, because a substring is
# what failed. A leak is reported against the CHECKED UNIT's label at a real
# line and column; the coverage report is reported against PII_WORLD_LABEL at
# 0:0. Both tests are applied and the reason is excluded as well, so neither a
# relabelled coverage report nor a reworded one can be counted as detection.

#: The gate's own label for a world-value coverage reduction. Spelled here
#: rather than imported, so the oracle is not the module under test.
PII_WORLD_LABEL = "<pii:world>"

#: The opening words of the CS-1083 coverage diagnostic's reason. It is NOT a
#: report that anything was found in a file.
COVERAGE_DIAGNOSTIC = "the world-token check did not cover"


def leak_diagnostics(stderr: str, subject: str) -> list[str]:
    """The diagnostic lines reporting `subject` found IN A CHECKED FILE.

    Args:
        stderr: The gate's stderr, or a `git commit` attempt's stderr.
        subject: "world token" or "world name" - the phrase the gate's own
            blocking reason uses for that class.

    Returns:
        Every line that is a LEAK report. Empty means the gate detected
        nothing, whatever its exit code says.
    """
    found = []
    for line in stderr.splitlines():
        if ": PII " not in line or subject not in line:
            continue
        if COVERAGE_DIAGNOSTIC in line:
            continue
        if line.startswith(PII_WORLD_LABEL + ":") or ":0:0: PII " in line:
            continue
        found.append(line)
    return found


def test_a_token_in_the_newest_save_past_the_entry_cap_is_still_blocked(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The fail-open, at the unit rung. Past the cap the token must still match.

    GRADED ON THE LEAK DIAGNOSTIC'S IDENTITY, never on the exit code. Under
    this fixture CS-1083's coverage diagnostic blocks unconditionally, so exit
    1 says nothing here at all - see leak_diagnostics above for the mutant that
    measured this arm passing with detection destroyed.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "ledger.md", "keyed by " + OVER_CAP_WORLD_TOKEN + "\n")
    result = run_gate("--files", str(target), env=env)

    leaks = leak_diagnostics(result.stderr, "world token")
    assert leaks, "FAIL-OPEN: no world-token LEAK was reported\n" + (result.stdout + result.stderr)
    # THE ANTI-VACUITY FRONT. This fixture is over the bound by construction,
    # so the coverage report must be here too. An arm that stopped seeing it
    # has stopped exercising the condition it is named for and would be
    # discriminating nothing - it would pass on an under-cap fixture, which
    # is exactly the shape CS-1083 exists to forbid.
    assert COVERAGE_DIAGNOSTIC in result.stderr, result.stderr
    assert result.returncode == 1, result.stdout + result.stderr


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

    # Same identity test as the token sibling. This arm was hollowed only
    # HALF way - the coverage reason names the token subject and never the
    # name one, so the substring still bound - but its exit-code assertion
    # went vacuous with the rest, and a reworded coverage reason would
    # finish the job. Graded on the leak line either way.
    leaks = leak_diagnostics(result.stderr, "world name")
    assert leaks, "FAIL-OPEN: no world-name LEAK was reported\n" + (result.stdout + result.stderr)
    assert COVERAGE_DIAGNOSTIC in result.stderr, result.stderr
    assert result.returncode == 1, result.stdout + result.stderr


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

    leaks = leak_diagnostics(attempt.stderr, "world token")
    assert attempt.returncode != 0, "FAIL-OPEN: the commit LANDED\n" + combined
    assert leaks, (
        "FAIL-OPEN: the commit was refused for COVERAGE and not for the token\n" + combined
    )
    assert COVERAGE_DIAGNOSTIC in attempt.stderr, combined
    assert after == before, "HEAD MOVED - the commit was not blocked"
    assert str(tmp_path) not in combined, combined


def test_an_over_cap_directory_does_not_stop_the_gate_starting(
    over_cap_save_root: Path, tmp_path: Path
) -> None:
    """The binding condition on the grant: a gate that cannot START does not block.

    The control for every test above. A clean file under the same over-cap
    save root has to produce a rendered verdict with no traceback - otherwise
    the blocking tests could be green because the gate is crashing rather than
    because it is detecting.

    CS-1083 CHANGED THE EXIT CODE HERE AND CHANGED NOTHING ABOUT THE PROPERTY
    THIS ARM DEFENDS, and the two are worth keeping apart. The gate still
    starts, still renders a verdict and still leaves no traceback; what changed
    is that a world-token population this run TRUNCATED no longer reads as
    clean at the exit status. The verdict is therefore pinned to the coverage
    diagnostic and to a count of one, so a crash, a stack trace or an
    unrelated finding cannot masquerade as the block this expects.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_save_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), env=env)

    assert "Traceback" not in result.stderr, result.stderr
    assert "crashed" not in result.stderr, result.stderr
    assert result.returncode == 1, result.stdout + result.stderr
    assert "1 diagnostic(s)" in result.stderr, result.stderr
    assert "did not cover this machine's whole save population" in result.stderr, result.stderr


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


# ==========================================================================
# CS-436 - the account-directory cap reports on EVERY channel it degrades
# ==========================================================================
#
# MAX_SAVE_ROOT_ENTRIES caps the ACCOUNT DIRECTORIES that _save_root_dirs
# lists, and three callers consume that listing: the account-id discovery, the
# world-NAME discovery, and the world-TOKEN header scan. The cap reported to
# the first of the three and was silent on the other two, because those two
# handed `None` to the parameter the report belongs in.
#
# The silence is the defect and the channel it fell in is what makes it
# matter. Past the cap a world name and a world token under a later account
# directory are undiscovered, and the two lines the operator is then shown are
# "no world name is discoverable on this machine" and "no world token is
# discoverable on this machine". Those are not silence - they are FALSE
# STATEMENTS, and CS-209-B is on record for that exact shape one rung down.
#
# Severity sits below CS-209-B and the reason is worth keeping rather than
# flattening: autosave rotation grows the FILES INSIDE an account directory,
# not the COUNT of account directories, so time alone does not produce a save
# root one entry past this cap the way it produces one past the save cap.
#
# Every directory name below is generated in this file and exists on no
# machine. Nothing here reads, asserts on, or renders a real account id.

OVER_CAP_ACCOUNT_PREFIX = "acct"


def make_over_cap_account_root(root: Path) -> Path:
    """A save root holding one MORE account directory than the cap.

    Each name is long enough, carries a digit, and is not a generic word, so
    every one of them clears the account-id filters - a fixture whose entries
    were all rejected for shape would leave the cap untested.

    The cap is read from the gate rather than restated here, so raising it in
    the module does not leave a stale number in this file (CLAUDE.md section 4).
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    save_root = root / "save-root"
    save_root.mkdir(parents=True, exist_ok=True)
    for index in range(cap + 1):
        (save_root / (OVER_CAP_ACCOUNT_PREFIX + "%05d" % index)).mkdir()
    assert len(list(save_root.iterdir())) == cap + 1
    return save_root


@pytest.fixture(scope="module")
def over_cap_account_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Built once and only ever READ - the gate never writes to a save root."""
    return make_over_cap_account_root(tmp_path_factory.mktemp("overcapaccounts"))


def pin_save_root(monkeypatch: pytest.MonkeyPatch, save_root: Path, tmp_path: Path) -> None:
    """Point the gate at one synthetic save root and clear every declaration.

    The in-process rung has no base_env to inherit, so the same isolation
    base_env provides to the subprocess rung is applied here by hand. Without
    it a machine whose config/local.json declares a real world would feed a
    real value into these tests.
    """
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(save_root))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        monkeypatch.delenv(key, raising=False)


def truncation_reasons(skipped: list[tuple[str, str]], label: str) -> list[str]:
    """The skip reasons on one label that name the account-directory cap.

    Takes the skip list rather than the report, so the annotation is the real
    shape - Report is only reachable through a dynamically loaded module.
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    needle = "save root holds more than %d entries" % cap
    return [why for lbl, why in skipped if lbl == label and needle in why]


def test_the_account_cap_reports_on_the_world_name_channel(
    over_cap_account_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Half one of the acceptance, on the channel the truncation degrades.

    discover_world_names consumes the capped listing, so past the cap a world
    name under a later account directory is not matchable. The report has to
    say so on the WORLD label, because that is the check that lost coverage -
    a line on the account-id label does not tell a reader that the world-name
    check degraded.
    """
    gate = load_gate()
    pin_save_root(monkeypatch, over_cap_account_root, tmp_path)

    report = gate.Report()
    gate.discover_world_names(report)

    reasons = truncation_reasons(report.skipped, gate.PII_WORLD_LABEL)
    assert any("world name" in why for why in reasons), report.skipped


def test_the_account_cap_reports_on_the_world_token_channel(
    over_cap_account_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The token twin, and it is a separate consumer of the same listing.

    A repair that passed the report at the world-NAME site alone would make
    the test above green and leave the header scan exactly as silent as it
    was. The two are asserted apart for that reason.
    """
    gate = load_gate()
    pin_save_root(monkeypatch, over_cap_account_root, tmp_path)

    report = gate.Report()
    gate.discover_world_tokens(report)

    reasons = truncation_reasons(report.skipped, gate.PII_WORLD_LABEL)
    assert any("world token" in why for why in reasons), report.skipped


def test_the_account_cap_still_reports_on_the_account_id_channel(
    over_cap_account_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control, and it was already true before this item.

    This channel is the one site that reported. Asserting it here is what
    distinguishes "the other two were taught to report" from "the reporting
    moved", which would close two holes by opening a third.
    """
    gate = load_gate()
    pin_save_root(monkeypatch, over_cap_account_root, tmp_path)

    report = gate.Report()
    gate.discover_account_ids(report)

    assert truncation_reasons(report.skipped, gate.PII_ACCOUNT_ID_LABEL), report.skipped


def test_the_account_cap_truncation_is_reported_with_no_flags_at_all(
    over_cap_account_root: Path, tmp_path: Path
) -> None:
    """CS-209's property applied to this cap, through a real gate process.

    .githooks/pre-commit passes neither --verbose nor --list-skipped, so a
    coverage reduction that only renders under a flag is a reduction nobody is
    ever shown. Run flagless on purpose.

    The subject word is required to appear ON THE TRUNCATION LINE rather than
    anywhere in stdout, and that is not pedantry: the unrepaired gate printed
    "no world name is discoverable on this machine" in this same run, so a
    bare substring test for "world name" passed against it and proved nothing.
    That sentence is now suppressed past the cap - see the sibling test that
    asserts its absence - and pinning the subject to the truncation line keeps
    this test measuring the line it names rather than the whole stream.
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_account_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), env=env)

    needle = "save root holds more than %d entries" % cap
    lines = [line for line in result.stdout.splitlines() if needle in line]

    # CS-1083: this run TRUNCATED the world-token population, so it no longer
    # reads as clean at the exit status. What this arm is about - the
    # truncation line, flagless, on the channel the hook actually shows -
    # is unchanged, and it is asserted below.
    assert result.returncode == 1, result.stdout + result.stderr
    assert lines, result.stdout
    assert any("world name" in line for line in lines), lines
    assert any("world token" in line for line in lines), lines


def test_the_account_cap_report_echoes_no_path_and_no_directory_name(
    over_cap_account_root: Path, tmp_path: Path
) -> None:
    """The skip reason carries COUNTS and a subject word only.

    A message naming the directory it truncated would print an account id -
    the gate would leak, through its own diagnostic, one of the values it
    exists to keep out of a commit (CLAUDE.md non-negotiables 3 and 12).
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_account_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), "--list-skipped", env=env)

    needle = "save root holds more than %d entries" % cap
    lines = [line for line in result.stdout.splitlines() if needle in line]
    assert lines, result.stdout
    for line in lines:
        assert OVER_CAP_ACCOUNT_PREFIX not in line, line
        assert str(over_cap_account_root) not in line, line


def test_an_over_cap_account_root_does_not_stop_the_gate_starting(
    over_cap_account_root: Path, tmp_path: Path
) -> None:
    """The binding condition on the grant: a gate that cannot START does not block.

    The control for every test above. A clean file under the same over-cap
    save root has to produce a rendered verdict with no traceback - otherwise
    the reporting tests could be green because the gate is crashing rather
    than because it is reporting.

    Same CS-1083 split as the directory-cap sibling above: the gate still
    starts and still renders, and the truncated world-token population now
    reaches the exit status instead of printing under a PASS banner.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_account_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), env=env)

    assert "Traceback" not in result.stderr, result.stderr
    assert "crashed" not in result.stderr, result.stderr
    assert result.returncode == 1, result.stdout + result.stderr
    assert "1 diagnostic(s)" in result.stderr, result.stderr
    assert "did not cover this machine's whole save population" in result.stderr, result.stderr


# --------------------------------------------------------------------------
# CS-436 - past the cap, the "nothing is discoverable" sentence is DELETED
# --------------------------------------------------------------------------
#
# Reporting the truncation was necessary and it was not sufficient. The first
# repair added a true line and left the false one standing beside it, so on a
# 513-entry save root the operator saw, adjacently:
#
#   skipped <pii:world> save root holds more than 512 entries; ... world names
#   skipped <pii:world> no world name is discoverable on this machine; set ...
#
# The second sentence is false and MEASURABLY so. With the identical bytes on
# disk and only the account directory renamed so it sorts inside the cap, the
# gate BLOCKS a file carrying that world name and that world token - exit 1,
# both diagnostics. Over the cap it exits 0 while telling the operator neither
# value exists. "Not looked for" is not "not there", and only the gate knows
# the difference.
#
# THE REMEDY IS DELETION, NOT A HEDGE (docs/adr/0008), and the file already
# held the pattern: `dropped_by_exclusion` suppresses this same sentence when
# every discovered name was excluded, for exactly this reason - two skip lines
# that disagree teach a reader to stop reading the channel. The truncation
# line survives and carries the fact; the unsupported universal claim goes.
#
# The three channels are asserted apart because they are three call sites, and
# the defect this repairs is a repair that fixed one of them.

NO_ACCOUNT_SENTENCE = "no account directory is discoverable"
NO_WORLD_NAME_SENTENCE = "no world name is discoverable"
# S105: a fragment of the gate's own diagnostic text, not a credential. The
# rule fires on the substring "token" in the name.
NO_WORLD_TOKEN_SENTENCE = "no world token is discoverable"  # noqa: S105


def make_loose_file_save_root(root: Path) -> Path:
    """A save root one entry past the cap holding NO directory at all.

    Every entry is a regular file, so there is no account directory anywhere
    under this root and there is no later one either. It is the fixture that
    catches a truncation message asserting the existence of something it never
    looked at.
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    save_root = root / "save-root"
    save_root.mkdir(parents=True, exist_ok=True)
    for index in range(cap + 1):
        (save_root / ("loose%05d.txt" % index)).write_bytes(b"")
    assert len(list(save_root.iterdir())) == cap + 1
    assert not [entry for entry in save_root.iterdir() if entry.is_dir()]
    return save_root


@pytest.fixture(scope="module")
def loose_file_save_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Built once and only ever READ - the gate never writes to a save root."""
    return make_loose_file_save_root(tmp_path_factory.mktemp("loosefiles"))


@pytest.fixture
def empty_save_root(tmp_path: Path) -> Path:
    """A save root that EXISTS and holds nothing. The honest-emptiness case."""
    save_root = tmp_path / "empty-save-root"
    save_root.mkdir(parents=True, exist_ok=True)
    return save_root


def sentences_matching(skipped: list[tuple[str, str]], needle: str) -> list[str]:
    """Every skip reason carrying `needle`, on any label."""
    return [why for _label, why in skipped if needle in why]


def test_the_truncated_listing_does_not_claim_no_world_name_exists(
    over_cap_account_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The false sentence is gone on the world-NAME channel past the cap."""
    gate = load_gate()
    pin_save_root(monkeypatch, over_cap_account_root, tmp_path)

    report = gate.Report()
    gate.discover_world_names(report)

    assert truncation_reasons(report.skipped, gate.PII_WORLD_LABEL), report.skipped
    assert not sentences_matching(report.skipped, NO_WORLD_NAME_SENTENCE), report.skipped


def test_the_truncated_listing_does_not_claim_no_world_token_exists(
    over_cap_account_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The token twin, and a separate call site from the name above."""
    gate = load_gate()
    pin_save_root(monkeypatch, over_cap_account_root, tmp_path)

    report = gate.Report()
    gate.discover_world_tokens(report)

    assert truncation_reasons(report.skipped, gate.PII_WORLD_LABEL), report.skipped
    assert not sentences_matching(report.skipped, NO_WORLD_TOKEN_SENTENCE), report.skipped


def test_the_truncated_listing_does_not_claim_no_account_directory_exists(
    loose_file_save_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The third channel, and it needs its own fixture to reach the sentence.

    Under over_cap_account_root the account-id channel finds 512 ids, so its
    false sentence never prints and the hole is invisible. Here every entry is
    a file, the id list comes back empty, and the claim is reachable.
    """
    gate = load_gate()
    pin_save_root(monkeypatch, loose_file_save_root, tmp_path)

    report = gate.Report()
    gate.discover_account_ids(report)

    assert truncation_reasons(report.skipped, gate.PII_ACCOUNT_ID_LABEL), report.skipped
    assert not sentences_matching(report.skipped, NO_ACCOUNT_SENTENCE), report.skipped


def test_a_genuinely_empty_save_root_still_says_nothing_is_discoverable(
    empty_save_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control that separates a suppression from a deletion.

    Without it the repair above is indistinguishable from dropping the advice
    outright, which would strip the coverage warning CS-209 put on this path.

    An empty save root is the unconfigured machine CS-209 exists to warn, and
    on it all three sentences are TRUE: the listing was complete and it found
    nothing. The suppression must be conditional on the truncation, never on
    the emptiness.
    """
    gate = load_gate()
    pin_save_root(monkeypatch, empty_save_root, tmp_path)

    report = gate.Report()
    gate.discover_account_ids(report)
    gate.discover_world_names(report)
    gate.discover_world_tokens(report)

    assert not truncation_reasons(report.skipped, gate.PII_ACCOUNT_ID_LABEL), report.skipped
    for sentence in (NO_ACCOUNT_SENTENCE, NO_WORLD_NAME_SENTENCE, NO_WORLD_TOKEN_SENTENCE):
        assert sentences_matching(report.skipped, sentence), (sentence, report.skipped)


def test_no_truncation_line_asserts_a_later_account_directory_exists(
    loose_file_save_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A warning that fires is not a warning that says something true.

    513 regular files and no directory anywhere. The truncation is real - the
    listing did stop - but there is no later account directory to hold
    anything, so a line saying values "under a later account directory" are
    unmatchable states something the gate never looked at and that is not so.
    The honest form says what this run did not DO, not what the disk contains.
    """
    gate = load_gate()
    pin_save_root(monkeypatch, loose_file_save_root, tmp_path)

    report = gate.Report()
    gate.discover_account_ids(report)
    gate.discover_world_names(report)
    gate.discover_world_tokens(report)

    truncation = sentences_matching(report.skipped, "save root holds more than")
    assert truncation, report.skipped
    for why in truncation:
        assert "later account directory" not in why, why


def test_the_cap_report_replaces_the_false_sentence_in_a_real_gate_process(
    over_cap_account_root: Path, tmp_path: Path
) -> None:
    """The operator-facing proof, flagless, through a real gate process.

    .githooks/pre-commit passes no flags, so this is the exact text an
    over-cap machine is shown on every commit. Both halves are asserted in one
    run because the defect was their ADJACENCY: the truncation line present,
    the contradicting sentence absent.
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_account_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate("--files", str(target), env=env)

    needle = "save root holds more than %d entries" % cap
    lines = [line for line in result.stdout.splitlines() if needle in line]

    # CS-1083: this run TRUNCATED the world-token population, so it no longer
    # reads as clean at the exit status. What this arm is about - the
    # truncation line, flagless, on the channel the hook actually shows -
    # is unchanged, and it is asserted below.
    assert result.returncode == 1, result.stdout + result.stderr
    assert any("world name" in line for line in lines), result.stdout
    assert any("world token" in line for line in lines), result.stdout
    assert NO_WORLD_NAME_SENTENCE not in result.stdout, result.stdout
    assert NO_WORLD_TOKEN_SENTENCE not in result.stdout, result.stdout


def test_the_world_token_cap_report_survives_an_unreachable_package(
    over_cap_account_root: Path, tmp_path: Path
) -> None:
    """The truncation report must not sit below an early return.

    The world-token report was written after the _load_header_reader guard, so
    on a checkout where the package cannot be imported the guard returns first
    and the line never prints - while its test asserts it does. That shape is
    what reddened CI on ddc5fe0: a test green locally for a reason it did not
    state. Run under -S so the package is genuinely out of reach here even on
    a runner that pip-installed it editable; see run_gate_copy.
    """
    cap = load_gate().MAX_SAVE_ROOT_ENTRIES
    copy = isolated_gate_copy(tmp_path)
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(over_cap_account_root)

    target = write(tmp_path / "clean.md", "nothing to see\n")
    result = run_gate_copy(copy, "--files", str(target), env=env)

    needle = "save root holds more than %d entries" % cap
    lines = [line for line in result.stdout.splitlines() if needle in line]

    # CS-1083: this run TRUNCATED the world-token population, so it no longer
    # reads as clean at the exit status. What this arm is about - the
    # truncation line, flagless, on the channel the hook actually shows -
    # is unchanged, and it is asserted below.
    assert result.returncode == 1, result.stdout + result.stderr
    assert "not importable from this checkout" in result.stdout, result.stdout
    assert any("world token" in line for line in lines), result.stdout


# ==========================================================================
# CS-436 - the header scan's time bound states what it does and does not bound
# ==========================================================================
#
# SAVE_HEADER_BUDGET_SECONDS is a wall-clock deadline tested at the TOP of the
# read loop, BEFORE the read. Two facts about that position, and the order of
# them is the whole item:
#
#   IT BINDS. Given reads slow enough to exhaust it, the loop stops with files
#   still unread and reports the skip; delete it and the same input reads them
#   all. There is an input where the bound REFUSED and its absence PROCEEDS,
#   which is the definition of a coverage reduction, so removing it was never
#   available. The counts behind that are in the commit that reverted the
#   removal and are deliberately not restated here - they are a function of
#   both gate constants, so a comment holding them rots the moment either is
#   edited. The two arms below re-derive the property on every run instead.
#
#   IT BOUNDS THE AGGREGATE SCAN, NOT ONE READ. It can notice time already
#   spent and cannot abort a read in flight, so a single slow open on a
#   hydrating cloud placeholder, a redirected LOCALAPPDATA or a dead network
#   path runs to completion however small the budget is set, and the scan
#   overruns by the cost of that one open. That is a true fact about a
#   PER-READ bound and it does not make the AGGREGATE bound decorative.
#
# So the defect was never the construct - it was the claim beside it, which
# named a bound the code did not have. The fence below therefore grades the
# CONSTRUCT AND ITS CLAIM TOGETHER. The fence it replaces asserted that the
# string "SAVE_HEADER_BUDGET" was absent from the source, which graded a
# SPELLING: the identical construct under a different name walked through it
# with the whole suite green. Grading a name is the defect that fence accused
# its predecessor of, inverted.
#
# Bounding a read in flight is still not on offer here and the reason is
# recorded beside the constant in the gate: it needs a worker thread, and both
# thread shapes buy a new way for the gate to fail to start.


CLOCK_CALL_NAMES = frozenset(
    {"monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns", "process_time", "time"}
)


def _is_clock_read(node: ast.AST) -> bool:
    """Whether one AST node is a call that reads a wall clock.

    Two call shapes are looked for - an attribute call on a module named
    `time` or `datetime`, and a bare call to one of CLOCK_CALL_NAMES, which is
    what `from time import monotonic` leaves behind. That is a list of shapes
    this looks for, not a claim about every way a clock could be read.
    """
    if not isinstance(node, ast.Call):
        return False
    call = node.func
    if isinstance(call, ast.Attribute) and isinstance(call.value, ast.Name):
        return call.value.id in {"time", "datetime"}
    return isinstance(call, ast.Name) and call.id in CLOCK_CALL_NAMES


def time_bound_constants_in(function_name: str) -> list[str]:
    """The module constants one gate function compares a wall clock against.

    STRUCTURAL rather than textual, which is the whole correction this helper
    exists to make. Matching on a constant's NAME grades how a thing is
    spelled - an identical construct spelled differently walked straight
    through the fence this replaces. Walking the function's own syntax tree
    finds the comparison first and learns the name from it, so the name is an
    OUTPUT here and never an input.

    Returns:
        The names on the far side of every clock comparison, in source order.
        Empty means the function reads a clock without bounding anything by
        it, or does not read one at all.
    """
    tree = ast.parse(GATE.read_bytes().decode("utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Compare):
                continue
            if not any(_is_clock_read(part) for part in ast.walk(inner.left)):
                continue
            found.extend(side.id for side in inner.comparators if isinstance(side, ast.Name))
    return found


def test_the_header_scan_time_bound_declares_the_scope_it_actually_has() -> None:
    """A wall-clock bound in this loop OBLIGES the docstring to state its limit.

    The obligation runs from the CONSTRUCT to the CLAIM, and both ends are
    found rather than spelled. Reintroducing the bound under any other
    constant name still lands a clock comparison inside this function, which
    still demands the disclosures below - and renaming it consistently, which
    changes nothing about what the code does, still passes.

    The non-vacuity assertion is a fence in its own direction: with no clock
    comparison at all this test would have nothing to grade, and reaching that
    state by deleting the bound is the coverage reduction CS-425 forbids.
    """
    gate = load_gate()
    bounds = time_bound_constants_in("_world_tokens_from_headers")
    assert bounds, "the header scan bounds nothing by the clock; its aggregate bound is gone"

    doc = (gate._world_tokens_from_headers.__doc__ or "").lower()  # noqa: SLF001

    # What it DOES bound. A bound whose docstring does not name its own scope
    # is the sentence this item was filed against.
    assert "aggregate" in doc, "the time bound does not say what it bounds"

    # What it does NOT bound, named as a known limit rather than left implied.
    for phrase in ("cannot abort", "in flight"):
        assert phrase in doc, "the time bound does not state its limit: " + phrase

    # The docstring must name the constant the code actually compares against,
    # whatever that is called, and the constant must be a real positive bound.
    for name in bounds:
        assert name.lower() in doc, "the docstring does not name the bound in the loop: " + name
        assert getattr(gate, name) > 0, name

    # The count bound is named too, so satisfying one and dropping the other
    # does not read as success.
    assert gate.MAX_SAVE_HEADER_FILES > 0
    assert "max_save_header_files" in doc


# ==========================================================================
# CS-436 - the --text-stdin path keeps its coverage warning
# ==========================================================================
#
# main() builds PiiMatchers before it dispatches, and --text-stdin never
# matches on them - mode_text_stdin runs the character-set and secret checks
# only. Skipping the construction there looks free and is not: PiiMatchers is
# what RUNS the discovery, and the discovery is what records the coverage
# skips, which print flagless since CS-209. Dropping it would strip this
# warning from the PreToolUse path on every unconfigured machine.
#
# MEASURED on this path rather than reasoned about, because the saving is what
# the trade was supposed to buy: the whole call is about 92 ms, of which the
# interpreter floor is about 20 ms and the gate's own module import about 57
# ms. Stubbing the construction out entirely moved the median to about 79 ms.
# So the purchase is roughly 13 ms of 92, and the price is the four lines
# below. This test is the fence that keeps that trade from being made quietly.


def test_text_stdin_still_reports_the_coverage_skips_with_no_flags(tmp_path: Path) -> None:
    """The coverage warning survives on the busiest path the gate has.

    base_env points the save root at a directory that does not exist and
    clears every declaration, which is exactly the unconfigured machine this
    channel exists to warn. Flagless on purpose: that is how the hook runs it.
    """
    result = run_gate("--text-stdin", stdin=b"git status --short\n", env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert "<pii:account-id>" in result.stdout, result.stdout
    assert "<pii:world>" in result.stdout, result.stdout
    assert "no world name is discoverable" in result.stdout, result.stdout
    assert "no world token is discoverable" in result.stdout, result.stdout


# ==========================================================================
# CS-838 - a staged file `ruff format --check` rejects must block a commit
# ==========================================================================
#
# THE DEFECT. The gate ran `ruff check` and never `ruff format --check`, so a
# staged file CI rejects committed cleanly at tier 0. What was broken is the
# tier-0 gate's AGREEMENT with CI rather than the project's protection:
# .github/workflows/tier1.yml already runs `ruff format --check .`, and would
# have caught the commit that prompted this item. A gate that passes what CI
# rejects trains the operator to ignore it.
#
# WHY THESE ARMS WIRE THE REAL TRACKED HOOK RATHER THAN REUSE hooked_repo.
# That fixture writes its OWN minimal one-line hook, so it grades the GATE'S
# VERDICT and says nothing about the path a real commit takes. The tracked
# hook captures the gate's stdout in a COMMAND SUBSTITUTION and requires the
# PASS banner as the LAST LINE of it, so a new child that inherited that pipe
# would HANG the commit rather than fail it, and any stray child output would
# break the anchored `case` pattern. Only the tracked hook grades those two,
# and both are properties of THIS change.
#
# THE SANDBOX CARRIES pyproject.toml ON PURPOSE. The format check arms only
# when ruff_config_args resolves a project config - the R1 mitigation pinned
# by test_the_format_check_skips_when_no_ruff_config_resolves below. A sandbox
# without one would make every arm here silently vacuous.

# Format-dirty and format-clean by ONE property each, measured with ruff
# 0.15.12: the first answers `Would reformat`, the second `already formatted`.
# Both carry a module docstring so D100 stays quiet, and neither trips the
# blocking band (E9, F63, F7, F82) - so a block here can only be the new check.
FORMAT_DIRTY = b'"""Doc."""\n\nVALUE = [1,2,3]\n'
FORMAT_CLEAN = b'"""Doc."""\n\nVALUE = [1, 2, 3]\n'

# The one source fragment that separates the two. Asserted ABSENT from the
# gate's output: `ruff format --diff` prints source lines verbatim, and a
# staged file can carry a world name or an account id.
FORMAT_SOURCE_FRAGMENT = "[1,2,3]"

TRACKED_PRE_COMMIT = REPO_ROOT / ".githooks" / "pre-commit"


@pytest.fixture
def tracked_hook_repo(tmp_path: Path) -> Path:
    """A throwaway repo wired to the REAL .githooks/pre-commit, plus a base commit.

    THE BASE COMMIT IS MADE BEFORE THE HOOK IS WIRED, so "HEAD is unchanged"
    after a blocked commit is a real assertion rather than "HEAD never
    existed".

    The gate and pyproject.toml are left UNTRACKED on purpose. The hook
    resolves the gate from the WORKING TREE and ruff resolves its config from
    disk, so neither needs to be in the index - and keeping them out of it
    keeps them off the list of units every arm here checks, which is what
    makes the checked count below small enough to read.
    """
    root = tmp_path / "trackedhookrepo"
    root.mkdir()
    assert git("init", "-q", "-b", "main", cwd=root).returncode == 0
    git("config", "user.email", "gate@example.invalid", cwd=root)
    git("config", "user.name", "Gate Test", cwd=root)
    git("config", "commit.gpgsign", "false", cwd=root)

    (root / "seed.txt").write_bytes(b"seed\n")
    assert git("add", "seed.txt", cwd=root).returncode == 0
    assert git("commit", "-q", "-m", "seed", cwd=root).returncode == 0

    (root / "tools").mkdir()
    shutil.copy2(GATE, root / "tools" / "precommit_gate.py")
    shutil.copy2(REPO_ROOT / "pyproject.toml", root / "pyproject.toml")

    hooks = root / "gate-hooks"
    hooks.mkdir()
    installed = hooks / "pre-commit"
    installed.write_bytes(TRACKED_PRE_COMMIT.read_bytes())
    installed.chmod(0o755)
    assert git("config", "core.hooksPath", "gate-hooks", cwd=root).returncode == 0

    # Setting a value is not evidence the value took - scripts/install_hooks.py
    # reads its own write back for exactly this reason.
    readback = git("config", "--get", "core.hooksPath", cwd=root)
    assert readback.stdout.strip() == "gate-hooks", "core.hooksPath did not take"
    return root


def attempt_commit(
    root: Path, tmp_path: Path, name: str, body: bytes
) -> tuple[subprocess.CompletedProcess[str], str, str]:
    """Stage one file and drive a REAL git commit. Returns the attempt and both HEADs."""
    (root / name).write_bytes(body)
    assert git("add", name, cwd=root).returncode == 0

    before = git("rev-parse", "HEAD", cwd=root).stdout.strip()
    assert before, "there is no base commit, so HEAD-unchanged would prove nothing"

    attempt = git_with_env(
        "commit",
        "-m",
        "CS-838: stage " + name,
        cwd=root,
        env=base_env(tmp_path),
    )
    after = git("rev-parse", "HEAD", cwd=root).stdout.strip()
    return attempt, before, after


def test_the_wired_hook_is_the_tracked_pre_commit_byte_for_byte(
    tracked_hook_repo: Path,
) -> None:
    """Without this, every arm below could be grading a copy that drifted."""
    wired = (tracked_hook_repo / "gate-hooks" / "pre-commit").read_bytes()
    assert wired == TRACKED_PRE_COMMIT.read_bytes(), (
        "the sandbox hook is not the tracked hook, so nothing below grades the real file"
    )


def test_a_format_violation_is_blocked_by_a_real_commit(
    tracked_hook_repo: Path, tmp_path: Path
) -> None:
    """CS-838 acceptance, the blocking direction. Real hook, real commit, HEAD unchanged.

    MEASURED before the repair, in this exact harness: the same staged file
    COMMITTED with exit 0, HEAD moved, and the gate printed its PASS banner.
    """
    attempt, before, after = attempt_commit(tracked_hook_repo, tmp_path, "dirty.py", FORMAT_DIRTY)
    combined = attempt.stdout + attempt.stderr

    assert attempt.returncode != 0, combined
    assert after == before, "HEAD MOVED, so the commit was not blocked"
    assert "precommit_gate: BLOCKED" in combined, combined
    assert " FORMAT " in combined, combined


def test_the_format_finding_names_the_repo_relative_label_and_leaks_no_path(
    tracked_hook_repo: Path, tmp_path: Path
) -> None:
    """The identity goes in Diagnostic.path, which display_label redacts. Two rules.

    ONE, the blocked file is named by its REPO-RELATIVE label, because that is
    what identifies it to the operator. TWO, nothing above that label survives:
    not the sandbox directory, not the gate's own temp staging directory, and
    not the account name that both of those sit under (CLAUDE.md
    non-negotiables 3 and 12).

    The SOURCE LINE is asserted absent as well. `ruff format --diff` prints
    source verbatim, and a staged file can carry a world name or an account id,
    so the check must never reach for it.
    """
    attempt, _before, _after = attempt_commit(tracked_hook_repo, tmp_path, "dirty.py", FORMAT_DIRTY)
    combined = attempt.stdout + attempt.stderr

    assert "dirty.py:" in combined, combined
    assert str(tmp_path) not in combined, "an absolute sandbox path reached the output"
    assert str(tmp_path).replace("\\", "/") not in combined, "same, with forward slashes"
    assert "clockspeed_gate_" not in combined, "the gate's temp staging dir reached the output"
    assert FORMAT_SOURCE_FRAGMENT not in combined, "a source line reached the output"


def test_a_format_clean_file_still_commits_through_the_tracked_hook(
    tracked_hook_repo: Path, tmp_path: Path
) -> None:
    """THE CONTROL. An always-refuse gate passes every arm above and fails here.

    A ZERO EXIT HERE IS ALSO THE LAST-LINE PROOF, and it is worth saying why
    rather than adding a weaker assertion that looks like one. The hook matches
    the gate's PASS banner against an ANCHORED `case` pattern applied to the
    LAST LINE of the captured stdout, and refuses with "the gate DID NOT RUN"
    on any mismatch. So a new child whose output was NOT captured - appending
    its own lines after the banner - could not reach exit 0 through this path
    at all. The banner is matched here too, for a legible failure when it is
    the banner rather than the exit code that moved.

    Git delivers hook output on ITS stderr, so both streams are searched. That
    is a property of git, not of the hook, and asserting on stdout alone would
    make this arm fail for a reason that is not the gate's.
    """
    attempt, before, after = attempt_commit(tracked_hook_repo, tmp_path, "clean.py", FORMAT_CLEAN)
    combined = attempt.stdout + attempt.stderr

    assert attempt.returncode == 0, combined
    assert after != before, "HEAD did not move, so the clean file did not commit"

    banner = [line for line in combined.splitlines() if "precommit_gate: PASS - " in line]
    assert len(banner) == 1, combined
    assert banner[0].rstrip().endswith(" blocking"), banner[0]


def test_the_format_check_does_not_rewrite_the_file_it_checks(
    tracked_hook_repo: Path, tmp_path: Path
) -> None:
    """`--check` only, proven by the bytes on disk rather than by reading argv.

    THIS ARM DRIVES --files, AND THAT IS THE WHOLE POINT. An earlier version
    drove --staged alone and COULD NOT FAIL: mode_staged builds every Unit
    WITHOUT a disk_path, so stage_for_lint copies to a temp directory and ruff
    never sees a working-tree path at all. Deleting `--check` from the argv left
    that version passing. The sentence that justified it - that stage_for_lint
    returns real working-tree paths for every unit whose bytes match disk - is
    never true in --staged mode.

    The exposure is EXCLUSIVE to --files, where mode_files sets disk_path to the
    operator's own path, and CI runs exactly that mode over every tracked file.
    """
    attempt_commit(tracked_hook_repo, tmp_path, "dirty.py", FORMAT_DIRTY)

    assert (tracked_hook_repo / "dirty.py").read_bytes() == FORMAT_DIRTY, (
        "the gate REWROTE a file it was only asked to check"
    )

    target = write(tmp_path / "loose.py", FORMAT_DIRTY.decode("ascii"))
    before = target.read_bytes()
    result = run_gate("--files", str(target), env=base_env(tmp_path))

    # THE INVARIANT FIRST, so a rewrite is reported AS a rewrite. Dropping
    # `--check` from the argv makes ruff rewrite this file and exit 0, which is
    # the exact defect this arm exists to catch.
    assert target.read_bytes() == before, (
        "the gate REWROTE a working-tree file in --files mode, which is the one "
        "mode where stage_for_lint hands ruff the operator's real disk path"
    )
    # Then non-vacuity: a check that never ran rewrites nothing either, so
    # without this the assertion above would pass for the wrong reason.
    assert "FORMAT" in result.stderr, (
        f"the format check did not run in --files mode, so this arm is vacuous: {result.stderr}"
    )


def test_the_format_check_skips_when_no_ruff_config_resolves() -> None:
    """R1, pinned rather than left to a reader. Ruff's defaults are not this project's.

    MEASURED with ruff 0.15.12 over the 90 tracked .py files: 90 of 90 are
    clean WITH the project config and 75 of 90 would be reformatted WITHOUT it.
    tools/edit_lint_check.py builds its Unit with no disk_path and calls
    run_ruff with no root, so every unit it checks is staged into a temp
    directory where ruff discovers no config at all. Without this skip that
    hook would refuse most of the tree.

    THE RESIDUAL THIS LEAVES IS SILENT, and that is recorded rather than
    hidden: emit prints notes only under --verbose, and the PostToolUse entry
    invokes tools/edit_lint_check.py without it. Repairing that would arm a
    blocking check on a path this item holds no grant for, so it is filed
    separately instead of absorbed here.
    """
    gate = load_gate()
    if gate.ruff_command() is None:
        pytest.skip("ruff is not installed, so run_ruff returns before the format check")

    unit = gate.Unit(label="dirty.py", origin="test", data=FORMAT_DIRTY, ext=".py")
    report = gate.Report()

    gate.run_ruff([unit], report, None)

    assert not report.diagnostics, [diag.render() for diag in report.diagnostics]
    assert any("no project config" in note for note in report.notes), report.notes


def test_a_format_dirty_unit_blocks_when_the_project_config_does_resolve(tmp_path: Path) -> None:
    """The other half of the arm above: the skip is the CONFIG's doing, not the check's.

    Without this, a format check that never fired at all would satisfy the skip
    test and look like a working mitigation.
    """
    gate = load_gate()
    if gate.ruff_command() is None:
        pytest.skip("ruff is not installed, so run_ruff returns before the format check")

    unit = gate.Unit(label="dirty.py", origin="test", data=FORMAT_DIRTY, ext=".py")
    report = gate.Report()

    gate.run_ruff([unit], report, REPO_ROOT)

    formats = [diag for diag in report.diagnostics if diag.code == "FORMAT"]
    assert len(formats) == 1, [diag.render() for diag in report.diagnostics]
    assert formats[0].path == "dirty.py", formats[0].render()
    assert FORMAT_SOURCE_FRAGMENT not in formats[0].reason, formats[0].reason
    assert str(tmp_path) not in formats[0].reason, formats[0].reason


def test_an_unparseable_python_file_is_a_note_and_never_a_format_block() -> None:
    """`ruff format --check` exits 2 on a file it cannot parse. That is neither verdict.

    Read as clean it would wave the file through; read as "would reformat" it
    would block on a file whose real defect is a syntax error the gate already
    reports on its own. It is a NOTE, and the note names the exit code and
    nothing ruff wrote - ruff sends the parse failure to stderr WITH THE PATH
    IN IT, so neither channel may be re-emitted.
    """
    gate = load_gate()
    if gate.ruff_command() is None:
        pytest.skip("ruff is not installed, so run_ruff returns before the format check")

    unit = gate.Unit(label="broken.py", origin="test", data=b"def broken(\n", ext=".py")
    report = gate.Report()

    gate.run_ruff([unit], report, REPO_ROOT)

    assert "FORMAT" not in {diag.code for diag in report.diagnostics}, [
        diag.render() for diag in report.diagnostics
    ]
    assert any("ruff format: exited 2" in note for note in report.notes), report.notes


def test_the_format_check_reads_its_timeout_at_call_time() -> None:
    """tools/edit_lint_check.py monkeypatches gate.RUFF_TIMEOUT around its call.

    A DEFAULT ARGUMENT BINDS AT IMPORT, so it would ignore that assignment and
    silently restore the 90-second budget on the PostToolUse path, where the
    whole point of that module's own 20-second value is that an editor hook
    must not stall. The name has to be read in the BODY.
    """
    tree = ast.parse(GATE.read_bytes())
    found = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "run_ruff_format"
    ]
    assert len(found) == 1, f"expected one run_ruff_format in the gate, found {len(found)}"
    function = found[0]

    defaults = [node for node in function.args.defaults if node is not None]
    defaults.extend(node for node in function.args.kw_defaults if node is not None)
    for default in defaults:
        names = {node.id for node in ast.walk(default) if isinstance(node, ast.Name)}
        assert "RUFF_TIMEOUT" not in names, "the timeout is bound at import, not read at call time"

    body_names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name)}
    assert "RUFF_TIMEOUT" in body_names, "the format check does not bound its child at all"


def test_the_format_prefix_names_files_and_never_decides_the_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Condition FIVE. The blocking signal is the EXIT CODE, not the prefix string.

    pyproject.toml pins ruff with NO upper bound, so a release that reworded
    `Would reformat: ` must not turn this into a check that exits 0 having done
    nothing. That is the CS-819 and CS-823 shape this project has twice paid to
    close. Proven behaviourally rather than by reading the source: the constant
    is replaced with a string ruff will never print, and the gate must STILL
    refuse - it just cannot say which file any more.
    """
    gate = load_gate()
    if gate.ruff_command() is None:
        pytest.skip("ruff is not installed, so run_ruff returns before the format check")

    monkeypatch.setattr(gate, "RUFF_FORMAT_PREFIX", "This is not what ruff prints: ")
    unit = gate.Unit(label="dirty.py", origin="test", data=FORMAT_DIRTY, ext=".py")
    report = gate.Report()

    gate.run_ruff([unit], report, REPO_ROOT)

    formats = [diag for diag in report.diagnostics if diag.code == "FORMAT"]
    assert formats, "a reworded prefix silently disarmed the format check"


# --------------------------------------------------------------------------
# CS-1087 - a world token carried ONLY by a header that will not parse
# --------------------------------------------------------------------------
#
# THE FIXTURE IS A REAL BYTE-CORRUPT SAVE ON DISK and never a suppressed or a
# monkeypatched reader. CS-1083's first cut HOLLOWED the CS-436 arms and they
# passed with world-token detection destroyed outright, because a patched
# reader proves a code path was entered and proves nothing about whether a
# token was recovered. Every arm below points a real gate process at a real
# temporary save root and grades what came back out of it.
#
# THE GRADE IS THE LEAK DIAGNOSTIC'S IDENTITY, never the exit code, for the
# reason leak_diagnostics above records: under a fixture that also trips a
# coverage report, exit 1 is satisfied with zero detection.

#: 22 characters, the measured token length, carried ONLY by the unparseable
#: save. Assembled rather than spelled out, and existing on no real machine.
CORRUPT_HEADER_WORLD_TOKEN = "Crp5Jd" + "3Vx8Ns" + "6Bt2Qw" + "9Ly7"

#: The `.sav` basename the unparseable save is written under. It sorts BEFORE
#: the readable sibling's basename, so the file that will not parse is reached
#: first and a scan that abandoned the rest cannot hide behind the ordering.
CORRUPT_SAVE_STEM = "Aard" + "vark"

#: The header version no measured layout exists for. Spelled here rather than
#: imported from the parser, so the oracle is not the module under test.
UNSUPPORTED_HEADER_VERSION = 99

#: The bytes the existing corrupt fixture uses: a file carrying no framed
#: string at all, and therefore no recoverable token at any offset. This is
#: the honest residue of CS-1087 rather than a case it covers.
NOTHING_FRAMED = b"\x00\xff" * 64


def unparseable_save_bytes(world_token: str) -> bytes:
    """A save carrying `world_token` whose header genuinely does not parse.

    EXACTLY ONE FIELD IS MUTATED. The leading int32 is the header version and
    99 has no measured layout, so the parser refuses BEFORE a single string is
    read - which is precisely the population CS-1083 declined to cover. Every
    other byte is the builder's own output, so the identifier is still framed
    the way a real one is.
    """
    import struct  # noqa: PLC0415

    body = synthetic_save_bytes(world_token)
    return struct.pack("<i", UNSUPPORTED_HEADER_VERSION) + body[4:]


def count_prefix_corrupt_save_bytes(world_token: str) -> bytes:
    """A save whose identifier CHARACTERS survive but whose count prefix does not.

    THE FIFTH RESIDUE SHAPE, built rather than described. The 22 characters sit
    at a known offset, intact, and the int32 that frames them is overwritten -
    so a scan that matches on the FRAMING cannot see a value that is genuinely
    on disk. That is a true residue rather than a floor: the bytes are there.
    """
    import struct  # noqa: PLC0415

    from tests.save import synthetic  # noqa: PLC0415

    blob = unparseable_save_bytes(world_token)
    framed = synthetic.fstring(world_token)
    at = blob.index(framed)
    damaged = blob[:at] + struct.pack("<i", 7) + blob[at + 4 :]
    assert len(damaged) == len(blob)
    return damaged


def make_mixed_header_save_root(tmp_path: Path, corrupt: bytes) -> Path:
    """A save root holding one PARSEABLE save and one that will not parse.

    The sibling is the known-good control. A plant that killed the reader
    outright, or a scan that died on the first refusal, takes the sibling's
    token down with it and every arm below reddens.
    """
    save_root = make_header_save_root(tmp_path, HEADER_WORLD_TOKEN)
    (save_root / FAKE_ACCOUNT_ID / (CORRUPT_SAVE_STEM + ".sav")).write_bytes(corrupt)
    return save_root


def parse_refusals(save_root: Path) -> list[str]:
    """The `.sav` basenames under `save_root` the REAL reader refuses.

    The reader is driven directly, in this process, so the arms below can
    state which files parse rather than assuming it. That is the half that
    proves the reader is ALIVE: a fixture whose every file refuses would make
    "the corrupt one was skipped" unfalsifiable.
    """
    from clockspeed.save.header import read_header  # noqa: PLC0415

    refused = []
    for path in sorted((save_root / FAKE_ACCOUNT_ID).glob("*.sav")):
        try:
            read_header(path)
        except BaseException:  # every refusal counts here, whatever it is
            refused.append(path.name)
    return refused


def unparseable_skip_reasons(stdout: str) -> list[str]:
    """Every skip line reporting a header that could not be parsed."""
    return [line for line in stdout.splitlines() if "could not be parsed" in line]


def test_a_token_carried_only_by_an_unparseable_header_is_still_matchable(
    tmp_path: Path,
) -> None:
    """CS-1087, graded with an unreadable header ACTUALLY PRESENT on disk.

    The token is in a `.sav` whose header the real reader refuses, and in no
    other place: base_env clears CLOCKSPEED_WORLD_TOKENS and points the local
    config at a path that does not exist, so the only route from that file to
    a diagnostic is a scan that does not need the header to parse.

    THE READER IS PROVEN ALIVE RATHER THAN ASSUMED, which is what separates
    "this one file was refused" from "the scan died" and from "the plant
    killed the reader outright". Three independent halves say so: the reader
    refuses the corrupt path and RETURNS the sibling's token in this process;
    the gate reports exactly ONE unparseable header and not two; and the
    sibling's own leak is still reported beside the recovered one.
    """
    save_root = make_mixed_header_save_root(
        tmp_path, unparseable_save_bytes(CORRUPT_HEADER_WORLD_TOKEN)
    )
    readable = save_root / FAKE_ACCOUNT_ID / (HEADER_SAVE_STEM + ".sav")

    from clockspeed.save.header import read_header  # noqa: PLC0415

    assert parse_refusals(save_root) == [CORRUPT_SAVE_STEM + ".sav"], (
        "the plant did not DEGRADE one file - either it parsed after all, or it "
        "killed the reader for the sibling too, which makes this arm vacuous"
    )
    # Bound to a scalar BEFORE the assert, and not merely described in a
    # message: pytest reprs the sub-expressions of the TEST independently of
    # the message, so asserting on the attribute itself renders a field whose
    # class ships a __repr__ to WITHHOLD it (non-negotiables 11 and 12).
    sibling_token_matches = read_header(readable).world_token == HEADER_WORLD_TOKEN
    assert sibling_token_matches, (
        "the parseable sibling did not read back its own token, so this arm cannot "
        "tell a live reader from a dead one"
    )

    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)
    corrupt_target = write(tmp_path / "from-the-corrupt-save.md", CORRUPT_HEADER_WORLD_TOKEN + "\n")
    readable_target = write(tmp_path / "from-the-readable-save.md", HEADER_WORLD_TOKEN + "\n")

    result = run_gate(
        "--list-skipped", "--files", str(corrupt_target), str(readable_target), env=env
    )

    leaks = leak_diagnostics(result.stderr, "world token")
    assert any(corrupt_target.name in line for line in leaks), (
        "FAIL-OPEN: the token carried only by the unparseable header was not "
        "reported as a leak\n" + result.stdout + result.stderr
    )
    assert any(readable_target.name in line for line in leaks), (
        "the READABLE sibling's token stopped being reported, so the scan did "
        "not degrade one file - it took the whole header source down\n" + result.stderr
    )
    reasons = unparseable_skip_reasons(result.stdout)
    assert len(reasons) == 1, reasons
    assert PII_WORLD_LABEL in reasons[0], reasons
    assert "1 save header(s)" in reasons[0], reasons
    assert "not matchable" not in reasons[0], (
        "the skip line still says the token is not matchable, which is now a "
        "false statement about a token this run recovered: " + reasons[0]
    )
    assert "crashed" not in result.stderr, result.stderr


def test_no_channel_renders_a_token_recovered_from_a_raw_header_prefix(
    tmp_path: Path,
) -> None:
    """The grant's clause 7 as a regression arm rather than as a reader's duty.

    The recovery binds raw save bytes, and the one thing that must never
    follow from that is the VALUE reaching a channel a human reads or pastes
    into an issue (non-negotiable 12). No byte of the recovered token may
    appear in stdout, in stderr, in a skip line or in any diagnostic.

    NON-VACUOUS BY CONSTRUCTION: the same run's leak diagnostic proves the
    gate knew the value, so "it never printed it" cannot be satisfied by
    never having had it.
    """
    save_root = make_mixed_header_save_root(
        tmp_path, unparseable_save_bytes(CORRUPT_HEADER_WORLD_TOKEN)
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)
    target = write(tmp_path / "from-the-corrupt-save.md", CORRUPT_HEADER_WORLD_TOKEN + "\n")

    result = run_gate("--list-skipped", "--verbose", "--files", str(target), env=env)

    assert leak_diagnostics(result.stderr, "world token"), (
        "nothing was recovered, so this arm measures silence rather than "
        "restraint\n" + result.stdout + result.stderr
    )
    assert CORRUPT_HEADER_WORLD_TOKEN not in result.stdout, result.stdout
    assert CORRUPT_HEADER_WORLD_TOKEN not in result.stderr, result.stderr
    for line in result.stderr.splitlines():
        assert FAKE_ACCOUNT_ID not in line, line
        assert str(save_root) not in line, line


@pytest.mark.parametrize(
    "plant",
    [
        pytest.param(NOTHING_FRAMED, id="overwritten wholesale"),
        pytest.param(
            count_prefix_corrupt_save_bytes(CORRUPT_HEADER_WORLD_TOKEN),
            id="identifier intact behind a damaged count prefix",
        ),
    ],
)
def test_an_unparseable_header_with_no_framed_token_recovers_nothing_and_never_blocks(
    plant: bytes,
    tmp_path: Path,
) -> None:
    """THE RESIDUE, pinned as a positive fact rather than left unstated.

    TWO SHAPES, AND THEY ARE NOT THE SAME KIND OF GAP. Overwritten bytes hold
    nothing of the identifier at any offset, so no means available to this
    gate could read a value that is not there - a floor. A damaged COUNT
    PREFIX is different and the earlier wording here was simply false about
    it: the 22 characters are intact on disk at a known offset, and this
    route misses them because it matches on the FRAMING. That is the honest
    residue of CS-1087 and it is named rather than rounded down to "nothing
    to recover".

    What must hold for both is the CS-1083 declination: the run says what it
    could not do and does NOT block, because a gate that refuses on a corrupt
    save it may never remove (non-negotiable 1) is one that gets bypassed
    with --no-verify.
    """
    save_root = make_mixed_header_save_root(tmp_path, plant)
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root)
    target = write(tmp_path / "clean.md", "nothing to see\n")

    result = run_gate("--list-skipped", "--files", str(target), env=env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout, result.stdout
    reasons = unparseable_skip_reasons(result.stdout)
    assert len(reasons) == 1, reasons
    assert "no framed world token" in reasons[0], reasons
    assert "not matchable" in reasons[0], reasons
    assert "crashed" not in result.stderr, result.stderr


# --------------------------------------------------------------------------
# CS-1087 - the scan's own cap, and the three skip lines it can print
# --------------------------------------------------------------------------
#
# The candidate cap is one more bound that truncates this population, and it
# is blocking for the reason the other truncating bounds are: a cap is the
# gate's own choice not to look and it is self-healing. A FILE declining to be
# read stays a non-blocking skip, and that is unchanged.


def framed_tokens(count: int) -> bytes:
    """`count` DISTINCT identifier-shaped framed strings, builder-encoded.

    tests/save/synthetic.py is the repository's one encoder of this framing,
    so the fixture drives it rather than hand-packing a second opinion.
    """
    from tests.save import synthetic  # noqa: PLC0415

    return b"".join(synthetic.fstring("ClockspeedCapTokens%03d" % index) for index in range(count))


def scan_cap() -> int:
    """The scan's per-framing candidate cap, read from the module that owns it.

    Restating the number here would be a second copy to drift (CLAUDE.md
    section 4), and a fixture that guessed it would stop crossing the bound
    the day it changed.
    """
    from clockspeed.save.header import MAX_SCANNED_TOKENS  # noqa: PLC0415

    return int(MAX_SCANNED_TOKENS)


def save_root_with_candidates(tmp_path: Path, count: int) -> Path:
    """A save root whose one save will not parse and holds `count` candidates."""
    save_root = make_save_root(tmp_path, FAKE_ACCOUNT_ID)
    blob = unparseable_save_bytes(CORRUPT_HEADER_WORLD_TOKEN) + framed_tokens(count)
    (save_root / FAKE_ACCOUNT_ID / (CORRUPT_SAVE_STEM + ".sav")).write_bytes(blob)
    return save_root


def test_a_candidate_cap_truncation_reaches_the_exit_status(tmp_path: Path) -> None:
    """The fifth bound, graded by CROSSING it and at the EXIT CODE.

    A prefix holding more identifier-shaped candidates than the scan admits
    leaves some of them unread, so a world token in a staged file might not
    have been matched - which is precisely the state CS-1083 refuses to let
    end in `PASS`. The reason carries no value and no number.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(save_root_with_candidates(tmp_path, scan_cap() + 3))
    target = write(tmp_path / "clean.md", "nothing to see\n")

    result = run_gate("--list-skipped", "--files", str(target), env=env)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "PASS" not in result.stdout, result.stdout
    assert "did not cover this machine's whole save population" in result.stderr, result.stderr
    assert "than the scan cap admits" in result.stderr, result.stderr
    for line in result.stderr.splitlines():
        assert FAKE_ACCOUNT_ID not in line, line
        assert "ClockspeedCapToken" not in line, line


def test_a_candidate_population_inside_the_cap_passes_and_still_matches(
    tmp_path: Path,
) -> None:
    """THE CONTROL, and it is what stops the arm above hollowing.

    Without it, a scan that reported truncation unconditionally - or one that
    recovered nothing at all and blocked on principle - would satisfy every
    assertion up there. Under the cap the run must reach `PASS` and exit 0 on
    a clean file, AND the token must still be matchable in the same fixture.
    CS-1083's first cut passed with detection destroyed for want of exactly
    this pairing.
    """
    save_root = str(save_root_with_candidates(tmp_path, 3))
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = save_root

    clean = write(tmp_path / "clean.md", "nothing to see\n")
    quiet = run_gate("--list-skipped", "--files", str(clean), env=env)

    assert quiet.returncode == 0, quiet.stdout + quiet.stderr
    assert "PASS" in quiet.stdout, quiet.stdout
    assert "than the scan cap admits" not in quiet.stderr, quiet.stderr

    leaky = write(tmp_path / "ledger.md", CORRUPT_HEADER_WORLD_TOKEN + "\n")
    blocked = run_gate("--files", str(leaky), env=env)

    assert leak_diagnostics(blocked.stderr, "world token"), (
        "nothing was matched under the cap, so the arm above blocks on a scan "
        "that recovers nothing\n" + blocked.stdout + blocked.stderr
    )


def test_the_lazy_token_scanner_recovers_a_real_unparseable_header(tmp_path: Path) -> None:
    """_load_token_scanner, driven rather than asserted about.

    An arm that only checked the import resolved would pass against a loader
    that returned the PARSER by the wrong name - which recovers nothing from
    an unparseable file and would silently turn the fallback off. So the
    callable this function hands back is put to work on a real byte-corrupt
    save and its answer is graded.
    """
    gate = load_gate()
    corrupt = tmp_path / "Unparseable.sav"
    corrupt.write_bytes(unparseable_save_bytes(CORRUPT_HEADER_WORLD_TOKEN))

    scanner = gate._load_token_scanner()  # noqa: SLF001
    candidates, truncated = scanner(corrupt)

    assert candidates == (CORRUPT_HEADER_WORLD_TOKEN,), candidates
    assert truncated is False


def test_a_header_that_cannot_be_scanned_either_is_a_skip_and_never_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The floor: no parse AND no raw read. Reported, and still not blocking.

    A file the gate cannot open for even a raw read is the same class as one
    that will not parse - the FILE declining to be read - so it stays out of
    the exit status (non-negotiables 1 and 7). What it must not do is share a
    sentence with the recovered case, which is the CS-209-B shape: the line
    has to say a raw scan was attempted and could not read the bytes.
    """
    gate = load_gate()

    def refuse(path: Path) -> object:  # noqa: ARG001
        raise ValueError("unparseable")

    def refuse_scan(path: Path) -> object:  # noqa: ARG001
        raise OSError("unreadable")

    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(make_empty_save_root(tmp_path, 3)))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    monkeypatch.delenv("CLOCKSPEED_WORLD_TOKENS", raising=False)
    monkeypatch.delenv("CLOCKSPEED_ACCOUNT_DIR", raising=False)
    monkeypatch.setattr(gate, "_load_header_reader", lambda: refuse)
    monkeypatch.setattr(gate, "_load_token_scanner", lambda: refuse_scan)

    report = gate.Report()
    gate._world_tokens_from_headers(report)  # noqa: SLF001

    reasons = [why for _label, why in report.skipped]
    assert any("could not be read for a raw scan either" in why for why in reasons), reasons
    assert any("3 save header(s)" in why for why in reasons), reasons
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 0, out
    assert "PASS" in out, out


def test_an_unimportable_token_scanner_is_reported_once_and_never_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The scanner import failing mid-run, which is _load_header_reader's own case.

    A gate that cannot start does not block, so an import failure is an
    ordinary skip here exactly as it is for the reader. THE LOADER IS TRIED
    ONCE and not once per file: three unparseable saves must not mean three
    import attempts, and the call count is asserted rather than assumed,
    because a retry loop over a broken import is how a gate turns a bad save
    directory into a slow one.
    """
    gate = load_gate()
    attempts = []

    def refuse(path: Path) -> object:  # noqa: ARG001
        raise ValueError("unparseable")

    def refuse_import() -> object:
        attempts.append(1)
        raise ImportError("the package went away mid-run")

    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(make_empty_save_root(tmp_path, 3)))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    monkeypatch.delenv("CLOCKSPEED_WORLD_TOKENS", raising=False)
    monkeypatch.delenv("CLOCKSPEED_ACCOUNT_DIR", raising=False)
    monkeypatch.setattr(gate, "_load_header_reader", lambda: refuse)
    monkeypatch.setattr(gate, "_load_token_scanner", refuse_import)

    report = gate.Report()
    gate._world_tokens_from_headers(report)  # noqa: SLF001

    assert len(attempts) == 1, attempts
    reasons = [why for _label, why in report.skipped]
    assert any("could not be read for a raw scan either" in why for why in reasons), reasons
    code, out, _err = emit_verdict(gate, report, capsys)
    assert code == 0, out
    assert "PASS" in out, out


# --------------------------------------------------------------------------
# CS-1095 - the console flash, and the platform guard that keeps the gate
# able to START on a non-Windows runner
# --------------------------------------------------------------------------
#
# WHAT THIS IS AND WHAT IT IS NOT. Every console-subsystem CHILD of a windowless
# parent - a pythonw process, or a hook running under the desktop harness -
# flashes a console window unless the spawn carries CREATE_NO_WINDOW. That is
# the documented mechanism, and carrying the flag at every spawn in the gate
# makes the file uniform in it. No measurement of this gate's own flash is
# cited, because none is on record: attributing the flash the operator reported
# to THIS gate is PROBABLE at n=1 and is unverified here. So the flag is
# UNIFORMITY, not a proven repair, and nothing below asserts a flash was fixed.
#
# THE FAILURE THESE ARMS EXIST TO PREVENT is not a missing flag. It is an
# AttributeError: subprocess.CREATE_NO_WINDOW exists only on Windows and tier1
# runs on ubuntu-latest, so an unguarded reference would make a tier-0 gate FAIL
# TO START, which _load_header_reader's own docstring names as the one failure a
# gate must not have. Recorded as the load-bearing clause of the section 6
# frozen-file grant at b283fee.

# The child that proves the non-Windows path. It runs in a SEPARATE interpreter
# because the absence has to exist before the gate module is executed, and this
# box will never supply that absence on its own - win32 always has the
# attribute, so an arm that merely ran here would pass for that reason alone and
# measure nothing. The child DELETES the attribute, ASSERTS the deletion took,
# and only then loads the gate and makes a real spawn through it.
NO_WINDOW_ABSENT_CHILD = """
import importlib.util
import json
import subprocess
import sys

before = hasattr(subprocess, "CREATE_NO_WINDOW")
if before:
    del subprocess.CREATE_NO_WINDOW
assert not hasattr(subprocess, "CREATE_NO_WINDOW"), "the deletion did not take"

spec = importlib.util.spec_from_file_location("gate_no_window_absent", sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules["gate_no_window_absent"] = module
spec.loader.exec_module(module)

out = module.git(["rev-parse", "--is-inside-work-tree"], cwd=sys.argv[2])
print(json.dumps({
    "attribute_was_present_before_deletion": before,
    "no_window": module.NO_WINDOW,
    "git_stdout": out.decode("utf-8", "replace").strip(),
}))
"""


# Every spawning entry point on the subprocess module. An ALLOWLIST OF GOOD,
# not a denylist of the one shape this file happens to use today. A denylist in
# this tree has leaked four times across four green commits, and the shape a
# later edit reaches for is always the one nobody enumerated. Popen, call,
# check_call and check_output each spawn a console-subsystem child and each
# accept creationflags, so each is graded exactly as run is.
SPAWN_ENTRY_POINTS = frozenset({"run", "Popen", "call", "check_call", "check_output"})

# The label carried by a spawn that sits outside every function. Deliberately
# not a valid identifier, so it can never collide with a real function name and
# can never be misread as one in the roster assertion's failure text.
MODULE_SCOPE = "<module>"

# The pinned roster of spawn sites, and its size stated BESIDE it rather than
# derived from it. On this project ids go absent exactly where a count
# miscounts, so a bare set-equality that quietly lost a member to a walk bug
# would read as a pass. Both are updated deliberately or not at all.
GATE_SPAWN_SITES = frozenset({"run_ruff_format", "run_ruff", "git"})
GATE_SPAWN_SITE_COUNT = 3


def _gate_subprocess_import_shape(source: bytes | None = None) -> None:
    """Refuse every subprocess import shape the spawn walk cannot attribute.

    `from subprocess import run as _run` puts a spawn behind a bare Name that
    resolves only by reading the import back, and `import subprocess as sp`
    moves the module itself behind another name. An import shape that cannot
    be graded is one that must be FORBIDDEN: the alternative is an enumerator
    that silently stops covering the file the day someone edits the import
    line, with nothing red to say so.
    """
    tree = ast.parse(GATE.read_bytes() if source is None else source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            names = ", ".join(alias.name for alias in node.names)
            raise AssertionError(
                "subprocess must be imported as a plain module, never as "
                f"`from subprocess import {names}` - a spawn behind a bare "
                "name is not attributable to the module by this walk"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess" and alias.asname is not None:
                    raise AssertionError(
                        f"subprocess is aliased to {alias.asname}; this walk "
                        "grades `subprocess.<entry point>` and nothing else"
                    )


def _gate_spawn_calls(source: bytes | None = None) -> dict[str, ast.Call]:
    """Map every subprocess spawn in the gate to its enclosing scope label.

    Three properties, each load-bearing, each proven against a planted
    counter-example below rather than assumed:

      1. The walk covers the WHOLE module. A spawn at module scope, or inside
         a class, is labelled and returned - not skipped for the accident of
         living outside a FunctionDef body.
      2. The entry point is matched against SPAWN_ENTRY_POINTS, so Popen and
         check_output are seen exactly as readily as run.
      3. The import shape is refused up front, so the one spawn shape this
         walk provably cannot attribute cannot enter the file at all.

    Graded as a SET by the caller. A threshold met by the strongest member
    leaves the weakest unmeasured, so "at least one site carries the flag" is
    exactly the shape that lets a fourth spawn be added later with no flag and
    no red.
    """
    _gate_subprocess_import_shape(source)
    tree = ast.parse(GATE.read_bytes() if source is None else source)
    sites: dict[str, ast.Call] = {}

    def is_spawn(func: ast.expr) -> bool:
        return (
            isinstance(func, ast.Attribute)
            and func.attr in SPAWN_ENTRY_POINTS
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
        )

    def walk(node: ast.AST, label: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = child.name if label == MODULE_SCOPE else f"{label}.{child.name}"
                walk(child, inner)
                continue
            if isinstance(child, ast.Call) and is_spawn(child.func):
                assert label not in sites, f"{label} spawns twice, so the map would hide one site"
                sites[label] = child
            walk(child, label)

    walk(tree, MODULE_SCOPE)
    return sites


def _unflagged_spawn_sites(sites: dict[str, ast.Call]) -> set[str]:
    """Labels whose creationflags is not the BARE name NO_WINDOW.

    The VALUE is graded, never the presence of the name. An expression that
    merely CONTAINS NO_WINDOW - `NO_WINDOW & 0`, `NO_WINDOW if x else 0` -
    evaluates to 0 on Windows and flashes, so a name-presence check calls a
    flashing spawn flagged. A spawn carrying no creationflags at all, or more
    than one, is unflagged for the same reason: nothing conforming is pinned.
    """
    unflagged: set[str] = set()
    for name, call in sites.items():
        flags = [kw.value for kw in call.keywords if kw.arg == "creationflags"]
        if len(flags) != 1:
            unflagged.add(name)
            continue
        value = flags[0]
        if not (isinstance(value, ast.Name) and value.id == "NO_WINDOW"):
            unflagged.add(name)
    return unflagged


def test_every_spawn_site_in_the_gate_carries_the_no_window_flag() -> None:
    """Graded as a SET over all three sites, and by VALUE, never by name.

    Two anti-narrowing controls sit here on purpose:

      - The roster is pinned as a set AND its size asserted beside it against
        a literal. On this project ids go absent exactly where a count
        miscounts, so a bare set-equality that quietly lost a member to a walk
        bug would read as a pass.
      - creationflags is graded through _unflagged_spawn_sites, which demands
        the bare name and rejects any expression merely containing it.

    A FOURTH spawn added later without the flag reddens this by appearing in
    the unflagged set; a spawn at module scope or inside a class reddens it by
    joining the roster under a label the roster does not hold; a Popen or a
    check_output reddens it the same way; a site renamed or removed reddens it
    by leaving the expected set. Each of those is measured, not asserted:
    test_the_spawn_walk_sees_every_shape_a_later_edit_could_reach_for and
    test_creationflags_is_graded_by_value_and_never_by_the_name_appearing are
    this arm's positive controls, and without them a blind enumerator would
    pass here for the reason that it found nothing.
    """
    sites = _gate_spawn_calls()
    assert set(sites) == set(GATE_SPAWN_SITES), sorted(sites)
    assert len(sites) == GATE_SPAWN_SITE_COUNT, sorted(sites)
    unflagged = _unflagged_spawn_sites(sites)
    assert unflagged == set(), sorted(unflagged)


def test_the_spawn_walk_sees_every_shape_a_later_edit_could_reach_for() -> None:
    """The enumerator's positive control, kept in the file, not measured once.

    An arm whose enumerator is blind to a shape passes for that reason alone,
    and the blindness is invisible from the pass. Every fixture below is a
    counter-example the ORIGINAL enumerator returned EMPTY for - measured
    2026-09-16 against scratch copies of the gate, five shapes green where
    they should have been red - which is why the control lives here now
    instead of in a transcript.
    """
    for entry_point in sorted(SPAWN_ENTRY_POINTS):
        source = b"import subprocess\ndef f():\n    subprocess.%s([])\n" % (
            entry_point.encode("ascii"),
        )
        assert set(_gate_spawn_calls(source)) == {"f"}, entry_point

    nested = b"import subprocess\nclass C:\n    def f(self):\n        subprocess.run([])\n"
    assert set(_gate_spawn_calls(nested)) == {"C.f"}, "a spawn inside a class is unseen"

    at_module = b"import subprocess\nsubprocess.run([])\n"
    assert set(_gate_spawn_calls(at_module)) == {MODULE_SCOPE}, "a module spawn is unseen"

    aliased = b"from subprocess import run as _run\ndef f():\n    _run([])\n"
    with pytest.raises(AssertionError, match="plain module"):
        _gate_spawn_calls(aliased)

    renamed = b"import subprocess as sp\ndef f():\n    sp.run([])\n"
    with pytest.raises(AssertionError, match="aliased to sp"):
        _gate_spawn_calls(renamed)

    # The floor. Without it every assertion above could be satisfied by an
    # enumerator that returns its argument's scope labels and never looks at
    # a call at all.
    inert = b"import subprocess\ndef f():\n    return subprocess\n"
    assert _gate_spawn_calls(inert) == {}, "a non-spawn is counted as a spawn"


def test_creationflags_is_graded_by_value_and_never_by_the_name_appearing() -> None:
    """The value control. NO_WINDOW & 0 is 0 on Windows and flashes.

    The original arm collected every ast.Name inside the creationflags
    expression and asked whether NO_WINDOW was among them, so each rejected
    fixture below passed it. The bare-name demand is what closes that, and
    the conforming fixture at the end is the known-good control that keeps
    the demand from being satisfied by rejecting everything.
    """
    head = b"import subprocess\nNO_WINDOW = 0\ndef f():\n    subprocess.run([], "
    rejected = (
        b"creationflags=NO_WINDOW & 0)\n",
        b"creationflags=NO_WINDOW if True else 0)\n",
        b"creationflags=(NO_WINDOW, 0)[1])\n",
        b"creationflags=0)\n",
        b"creationflags=subprocess.CREATE" + b"_NO_WINDOW)\n",
        b"check=True)\n",
    )
    for tail in rejected:
        sites = _gate_spawn_calls(head + tail)
        assert set(sites) == {"f"}, tail
        assert _unflagged_spawn_sites(sites) == {"f"}, tail

    conforming = b"creationflags=NO_WINDOW)\n"
    sites = _gate_spawn_calls(head + conforming)
    assert set(sites) == {"f"}, conforming
    assert _unflagged_spawn_sites(sites) == set(), conforming


def test_the_gate_imports_subprocess_in_the_one_attributable_shape() -> None:
    """The import shape is its own arm, because the whole walk rests on it.

    Stated separately from the spawn roster so that a future edit changing
    only the import line fails with the reason, rather than with an empty
    roster that reads like the file lost its spawns.
    """
    _gate_subprocess_import_shape()
    source = GATE.read_text(encoding="utf-8")
    assert "\nimport subprocess\n" in source, "the plain module import is gone"


def test_the_flag_is_read_through_getattr_and_never_as_a_bare_attribute() -> None:
    """The guard itself, asserted structurally against the module source.

    subprocess.CREATE_NO_WINDOW spelled directly at module scope raises
    AttributeError on ubuntu-latest at IMPORT time, so the gate would not
    start at all and every other arm in this file would be reporting on a
    module that never loaded. Asserted here rather than left to the runner,
    because this box cannot produce that failure.
    """
    source = GATE.read_text(encoding="utf-8")
    bare = "subprocess." + "CREATE_NO_WINDOW"
    guarded = 'getattr(subprocess, "' + "CREATE_NO_WINDOW" + '", 0)'
    assert guarded in source, "the flag is not read through a defaulted getattr"
    for line in source.splitlines():
        if bare in line and guarded not in line:
            raise AssertionError(f"unguarded flag reference: {line.strip()}")


def test_the_gate_starts_and_spawns_when_the_flag_attribute_is_absent() -> None:
    """The non-Windows path, with the absence SIMULATED rather than waited for.

    On this box hasattr(subprocess, "CREATE_NO_WINDOW") is always True, so an
    arm that relied on the platform to supply the absence would pass without
    ever entering the frame it names. The child deletes the attribute, asserts
    the deletion took, THEN loads the gate and makes a real git spawn through
    it - so what is graded is that the module executes, that the flag degrades
    to the documented no-op 0, and that a child still runs.
    """
    proc = subprocess.run(
        [sys.executable, "-c", NO_WINDOW_ABSENT_CHILD, str(GATE), str(REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout.strip().splitlines()[-1])

    # The known-good control. Without it a child on a platform that never had
    # the attribute would report success having deleted nothing, and the arm
    # would be a statement about no state at all.
    if sys.platform == "win32":
        assert result["attribute_was_present_before_deletion"] is True, result

    assert result["no_window"] == 0, result
    assert result["git_stdout"] == "true", result


def test_the_gate_still_starts_with_the_flag_in_place() -> None:
    """A gate that cannot start does not block, so start-up is its own arm.

    --help is the cheapest invocation that executes the whole module body,
    including the flag derivation, without doing any work.
    """
    proc = subprocess.run(
        [sys.executable, str(GATE), "--help"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
