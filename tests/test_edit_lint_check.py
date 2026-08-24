#!/usr/bin/env python3
"""Tests for tools/edit_lint_check.py.

The tool is invoked as a SUBPROCESS throughout, for the same reason the gate
suite does it: the exit code is half the contract, 0 pass and 1 problem, and
this runs as a PostToolUse hook where that code is the whole signal.

CS-204 is why this file exists. edit_lint_check builds its own labels - it
calls gate.label_for itself at tools/edit_lint_check.py:102 and constructs its
own gate.Unit at :104 - but it renders them through the SAME gate.emit at :132.
So a redaction applied in emit covers both tools, and a redaction applied
anywhere else covers only one. The grant made this a test obligation rather
than an inspection obligation precisely because "it shares the renderer" is
the kind of claim that is true right up until someone adds a second printer.

Every violating literal is assembled at runtime rather than spelled out: this
file is itself checked by the gate, so a literal em dash or home path here
would block the commit that adds it.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "edit_lint_check.py"

EM_DASH = chr(0x2014)

TIMEOUT = 180

# The same two markers the gate suite uses, for the same reason: one component
# must survive the redaction and one must not.
OUTSIDE_DIR = "zzoutsidedirzz"
OUTSIDE_BASE = "zzbasenamezz"

CHANNEL_CHECKED = "  checked  "
CHANNEL_SKIPPED = "  skipped  "
CHANNEL_NOTE = "  note     "
CHANNEL_DIAGNOSTIC = " CHARSET "


def base_env(tmp_path: Path) -> dict[str, str]:
    """A deterministic environment for the runtime-detected PII checks.

    Pinned to values that cannot exist on the machine running the suite, so
    these tests assert the tool's logic rather than the operator's login name.
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


def run_tool(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), *args],
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


def outside_target(tmp_path: Path, suffix: str, data: bytes) -> Path:
    """A path outside any repository, marked in BOTH directory and basename."""
    target = tmp_path / OUTSIDE_DIR / (OUTSIDE_BASE + suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
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


def test_tool_script_exists() -> None:
    assert TOOL.is_file(), f"the tool is missing at {TOOL}"


def test_a_clean_file_passes(tmp_path: Path) -> None:
    """The baseline verdict, so the redaction tests are not the only coverage."""
    target = outside_target(tmp_path, ".py", b'"""Doc."""\n\nVALUE = 1\n')
    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0


def test_an_em_dash_still_blocks(tmp_path: Path) -> None:
    """The verdict this tool exists to produce is unchanged by the redaction."""
    target = outside_target(tmp_path, ".md", ("# T\n\nAlpha " + EM_DASH + " b\n").encode("utf-8"))
    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert ":3:7: CHARSET" in result.stderr
    assert "U+2014 em dash" in result.stderr


def test_checked_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 1 of 4, through the second tool's own labels."""
    target = outside_target(tmp_path, ".py", b'"""Doc."""\n\nVALUE = 1\n')
    result = run_tool("--files", str(target), "--verbose", env=base_env(tmp_path))

    assert result.returncode == 0
    assert_channel_is_clean(result.stdout, CHANNEL_CHECKED, tmp_path, OUTSIDE_BASE + ".py")


def test_skipped_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 2 of 4, through the second tool's own labels."""
    target = outside_target(tmp_path, ".png", b"not really a png\n")
    result = run_tool("--files", str(target), "--list-skipped", env=base_env(tmp_path))

    assert result.returncode == 0
    assert_channel_is_clean(result.stdout, CHANNEL_SKIPPED, tmp_path, OUTSIDE_BASE + ".png")


def test_notes_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 3 of 4, provoked without ruff so it cannot go vacuous."""
    target = outside_target(tmp_path, ".md", b"alpha \xff beta\n")
    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert "decoded as latin-1" in result.stderr
    assert_channel_is_clean(result.stderr, CHANNEL_NOTE, tmp_path, OUTSIDE_BASE + ".md")


def test_ruff_style_note_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 3, second shape.

    This tool builds its Unit WITHOUT disk_path, so ruff lints a temp staging
    copy and the label comes back through the ruff output mapping. That is the
    one path where a mapping miss would render a temp directory instead of the
    label, and on Windows the temp directory sits under the home directory.
    """
    target = outside_target(tmp_path, ".py", b"import os\nVALUE = 1\n")
    result = run_tool("--files", str(target), "--verbose", env=base_env(tmp_path))

    if "ruff (style" not in result.stdout:
        pytest.skip("ruff produced no style finding; nothing to assert here")
    assert result.returncode == 0
    assert_channel_is_clean(result.stdout, "ruff (style", tmp_path, OUTSIDE_BASE + ".py")


def test_diagnostics_channel_drops_the_out_of_repo_directory(tmp_path: Path) -> None:
    """Channel 4 of 4, through the second tool's own labels."""
    target = outside_target(tmp_path, ".md", ("# T\n\nAlpha " + EM_DASH + " b\n").encode("utf-8"))
    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 1
    assert_channel_is_clean(result.stderr, CHANNEL_DIAGNOSTIC, tmp_path, OUTSIDE_BASE + ".md")


def test_no_temp_staging_directory_is_rendered(tmp_path: Path) -> None:
    """The staging copy lives under the system temp directory.

    On Windows that is under the home directory, so a rendered staging path is
    the same class of leak as a rendered target path. Asserted against the
    interpreter's own temp root, computed here rather than spelled out.
    """
    target = outside_target(tmp_path, ".py", b"import os\nVALUE = 1\n")
    result = run_tool("--files", str(target), "--verbose", env=base_env(tmp_path))

    temp_root = str(Path(tempfile.gettempdir()))
    combined = result.stdout + result.stderr

    assert temp_root not in combined, combined
    assert temp_root.replace("\\", "/") not in combined, combined


# --------------------------------------------------------------------------
# CS-841 - the format check is OFF on this path. That must be DISCLOSED, and
# the transition that switches it ON must redden a test.
# --------------------------------------------------------------------------

# Bytes `ruff format` rewrites and `ruff check` has nothing BLOCKING to say
# about. MEASURED against this project's own config rather than assumed: the
# format check exits 1 naming the file, and the E9/F63/F7/F82 band comes back
# empty, so a refusal of these bytes can only have come from the format check.
FORMAT_DIRTY = b'"""Doc."""\n\nVALUE = [1,2,3]\n'

# The one source fragment separating those bytes from their formatted twin.
# Asserted ABSENT from every channel: ruff prints source lines, and a checked
# file can carry a world name or an account id (CLAUDE.md non-negotiables 3
# and 12).
FORMAT_SOURCE_FRAGMENT = "[1,2,3]"

# The disclosure this tool owes the operator, as a substring contract.
FORMAT_SKIP_MARKER = "ruff format --check is NOT enforced here"

# gate.Diagnostic renders as `path:line:col: CODE reason`, so the code arrives
# surrounded by spaces. Matching the bare word would hit prose instead.
FORMAT_CODE = " FORMAT "

GATE = REPO_ROOT / "tools" / "precommit_gate.py"


def run_gate(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the SIBLING gate - the tool that DOES hand the linter a root.

    cwd is pinned to the repository root because that gate resolves its ruff
    config from the git toplevel of the working directory. A suite invoked
    from anywhere else would resolve no config, the gate would then skip the
    format check exactly as this tool does, and the differential these tests
    are built on would vanish with nothing failing to say so.
    """
    proc = subprocess.run(
        [sys.executable, str(GATE), *args],
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=TIMEOUT,
        check=False,
    )
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


def test_the_format_skip_is_disclosed_without_verbose(tmp_path: Path) -> None:
    """CS-841's SILENT half, and the channel it was silent on.

    gate.emit renders report.notes under --verbose, or on a run that already
    BLOCKED. The PostToolUse entry in .claude/settings.json passes neither of
    those, so on the one path the skip actually covers - a clean edit - the
    mitigation was never rendered at all. That is NOT a coverage reduction,
    because there is no format coverage here to reduce; it is a permanent
    disablement that no output disclosed.

    gate.emit lives in a frozen file (CLAUDE.md section 6), so the disclosure
    is this tool's to make rather than the renderer's.
    """
    target = outside_target(tmp_path, ".py", FORMAT_DIRTY)

    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert FORMAT_SKIP_MARKER in result.stdout, (
        "the format check is disabled on this path and no output said so: " + repr(result.stdout)
    )
    assert FORMAT_SOURCE_FRAGMENT not in result.stdout + result.stderr


def test_a_non_python_edit_gets_no_format_notice(tmp_path: Path) -> None:
    """The disclosure is PROPORTIONAL, or it becomes the noise nobody reads.

    gate.run_ruff returns before the format check whenever no unit is python
    at all, so a notice on a markdown edit would report a skip that was never
    reached. This pins the filter in the second direction - the test above
    proves the disclosure fires, this one proves it does not fire everywhere.
    """
    target = outside_target(tmp_path, ".md", b"# T\n\nAlpha b\n")

    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0, result.stderr
    assert FORMAT_SKIP_MARKER not in result.stdout, result.stdout


def test_a_root_reaching_this_tool_would_arm_a_blocking_format_check(tmp_path: Path) -> None:
    """CS-841's SELF-ARMING half. WRITTEN TO FAIL ON A TRANSITION, NOT ON TODAY.

    tools/edit_lint_check.py is not frozen, so a one-line change handing
    gate.run_ruff a root needs no grant and no review. It would turn the
    format check ON, blocking, on the operator's LIVE edit path - and the
    first sign of it would be an edit being refused. This test is what says
    so first, and it fails on the change rather than on the current state.

    THE ARMING STEP COMES FIRST AND IS THE POINT. A tripwire whose bait has
    stopped being a violation passes forever while guarding nothing, and a
    survived mutant and a mutant that never applied produce identical output.
    So the same bytes go through the SIBLING gate, which does pass a root, and
    it must REFUSE them with a FORMAT diagnostic. That arm failing is a better
    outcome than a green tripwire standing over a dead fixture.

    It ASSERTS rather than skips when ruff is absent. A tripwire that disarms
    itself whenever a tool is missing cannot promise the RED this item is
    required to produce, and this project pins ruff.
    """
    target = outside_target(tmp_path, ".py", FORMAT_DIRTY)

    reference = run_gate("--files", str(target), env=base_env(tmp_path))

    assert reference.returncode == 1, (
        "the bait is no longer refused by the tool that DOES pass a root, so this "
        "tripwire guards nothing: " + reference.stdout + reference.stderr
    )
    assert FORMAT_CODE in reference.stderr, (
        "the sibling gate refused these bytes for some reason OTHER than formatting, "
        "so the differential under test is not the root: " + reference.stderr
    )

    result = run_tool("--files", str(target), env=base_env(tmp_path))

    assert result.returncode == 0, (
        "a root now reaches tools/edit_lint_check.py: the format check is armed and "
        "BLOCKING on the operator's live edit path. CS-841 says that needs a grant "
        "and a recorded review, not a one-line edit. " + result.stderr
    )
    assert FORMAT_CODE not in result.stderr, result.stderr
    assert FORMAT_SKIP_MARKER in result.stdout, (
        "the format skip stopped being disclosed, which means either the check is "
        "now armed or the disclosure was dropped: " + repr(result.stdout)
    )
