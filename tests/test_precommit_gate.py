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
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

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
FAKE_ACCOUNT_ID = "12345678901234567"

TIMEOUT = 180


def base_env(tmp_path: Path) -> dict[str, str]:
    """A deterministic environment for the runtime-detected PII checks.

    The account name and the save root are pinned to values that cannot exist
    on the machine running the suite, so these tests assert the gate's logic
    rather than the operator's login name. The one test that needs real
    detection sets CLOCKSPEED_SAVE_ROOT itself.
    """
    env = dict(os.environ)
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["USERNAME"] = "gatetestaccount"
    env["USER"] = "gatetestaccount"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_gate(
    *args: str,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(GATE), *args],
        input=stdin,
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
    assert "numeric platform account id" in result.stderr


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
