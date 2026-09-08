#!/usr/bin/env python3
"""CHARACTERISATION of what `precommit_gate.py --text-stdin` does NOT scan.

WHY THIS FILE EXISTS. CS-957 introduces an outbound leak gate because a
class-A1 auto-responder may take a read-only measurement with no operator in
the loop and REPORT IT BACK. The reporting half is an exfiltration path: a
reply can carry a home path, an account name, a platform account id or a world
name and break CLAUDE.md non-negotiable 3 without writing a byte. The gate an
implementer reaches for first is `tools/precommit_gate.py --text-stdin`,
because it already reads text on stdin and already owns PII matchers. It does
not screen personal data in that mode, and nobody should wire an outbound
reply to it believing that it does. This file is the fence.

WHAT WAS MEASURED, on this tree, 2026-09-08, with the payload built below and
the save root pointed at a directory that does not exist:

  - `--text-stdin` fed PLANTED_TEXT printed
    `precommit_gate: PASS - 1 checked, 5 skipped, 0 blocking` and exited 0.
    Nothing in stdout or stderr named the home path. (The skipped COUNT is a
    function of the machine's save-root coverage, so no arm below pins it.)
  - `--files` fed a file holding those IDENTICAL bytes exited 1 and printed
    `<outside-repo>/planted.txt:1:20: PII absolute Windows home path; ...`.

THIS IS A CHARACTERISATION TEST, NOT AN ACCEPTANCE TEST. It pins behaviour it
does not endorse. `tools/precommit_gate.py` is on the CLAUDE.md section 6
frozen list and no grant was sought for CS-957; this file changes nothing about
the gate. The day someone teaches `--text-stdin` to scan PII, arm 1 goes RED,
and that is CORRECT: it forces the change to be conscious rather than silent.
The fix at that point is to update arm 1 and say so in `docs/LEDGER.md`.

WHY ARM 2 IS LOAD-BEARING. Arm 1 alone is equally satisfied by a home-path
rule that never fires anywhere - a dead rule and a mode that skips a live rule
produce the same silence. Arm 2 routes the SAME MODULE-LEVEL BYTES through
`--files`, the mode that does scan, and requires a block. Only the mode flag
differs between the two arms, so the difference in verdict is attributable to
the mode and to nothing else.

THE PLANTED VALUE IS SYNTHETIC AND ASSEMBLED FROM FRAGMENTS. Two reasons, both
hard rules. First, CLAUDE.md non-negotiable 3: a real home path must never
enter a tracked file. Second, this file is itself checked by the gate on
commit, so a spelled-out home path literal here would block the commit that
adds these tests.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "precommit_gate.py"

TIMEOUT = 180

# Assembled, never spelled out - see the module docstring. The account segment
# is split as well, so a future grep for the whole word finds no literal here.
ACCOUNT_SEGMENT = "some" + "operator"
PLANTED_HOME_PATH = (
    "C:" + "\\" + "Users" + "\\" + ACCOUNT_SEGMENT + "\\" + "Documents" + "\\" + "x.txt"
)

# ONE constant, shared by every arm. If the arms planted their own payloads,
# arm 2 could pass on a string arm 1 never sent and the pairing would prove
# nothing.
PLANTED_TEXT = "the note points at " + PLANTED_HOME_PATH + "\n"

# The gate's own words, quoted so an arm names what it expects rather than
# merely asserting that stderr was non-empty (CONVENTIONS.md section 7.2).
# CLEAN_BANNER is not named for the word it holds: a constant whose name
# carries that word trips ruff S105, the hardcoded-password heuristic.
PII_HOME_REASON = "absolute Windows home path"
CLEAN_BANNER = "PASS - "
BLOCKED_IDIOM = "precommit_gate: BLOCKED"
REDACTED_LABEL = "<outside-repo>"


def base_env(tmp_path: Path) -> dict[str, str]:
    """An environment in which the gate can discover no real personal value.

    The save root and the local config are pointed at paths that cannot exist,
    and the world overrides are cleared, so `PiiMatchers` finds nothing on this
    machine. Without that, a configured machine would feed the operator's own
    world name into these arms, which would make the suite machine-dependent
    and would risk asserting on real personal data (CLAUDE.md non-negotiable
    3). Every value these arms grade is the synthetic one planted above.
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


def run_gate(
    *args: str,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the gate as a real subprocess, because the exit code is the contract.

    An auto-responder would shell out to it exactly this way. Importing the
    module and reading a return value would grade something adjacent to the
    thing a caller actually relies on.
    """
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


def plant_file(tmp_path: Path) -> Path:
    """Write PLANTED_TEXT to disk verbatim.

    write_bytes and never write_text: on Windows write_text rewrites LF as
    CRLF, which would shift the byte offsets the gate reports and would mean
    arms 1 and 2 no longer share identical bytes.
    """
    planted = tmp_path / "planted.txt"
    planted.write_bytes(PLANTED_TEXT.encode("utf-8"))
    return planted


# ==========================================================================
# Arm 1 - the characterisation proper
# ==========================================================================


def test_text_stdin_passes_a_planted_home_path(tmp_path: Path) -> None:
    """--text-stdin exits 0 on a payload holding an absolute Windows home path.

    THIS IS THE BEHAVIOUR TO KNOW ABOUT, NOT THE BEHAVIOUR TO COPY. Read the
    module docstring before changing this arm.
    """
    result = run_gate(
        "--text-stdin",
        stdin=PLANTED_TEXT.encode("utf-8"),
        env=base_env(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert CLEAN_BANNER in result.stdout, result.stdout
    # The mode reports a clean pass AND never names the class it did not scan.
    combined = result.stdout + result.stderr
    assert PII_HOME_REASON not in combined, "the stdin mode began scanning home paths"
    assert BLOCKED_IDIOM not in combined, combined


# ==========================================================================
# Arm 2 - the positive control that makes arm 1 mean something
# ==========================================================================


def test_the_same_bytes_block_through_the_mode_that_scans_pii(tmp_path: Path) -> None:
    """--files blocks on the IDENTICAL bytes arm 1 saw pass.

    Without this arm, arm 1 is satisfied by a home-path rule that fires
    nowhere at all, and the pair would pin nothing.
    """
    planted = plant_file(tmp_path)

    result = run_gate("--files", str(planted), env=base_env(tmp_path))

    assert result.returncode == 1, result.stdout
    assert BLOCKED_IDIOM in result.stderr, result.stderr
    assert PII_HOME_REASON in result.stderr, result.stderr


# ==========================================================================
# Arm 3 - the diagnostic names the class, never the value
# ==========================================================================


def test_the_blocking_reason_carries_no_planted_value(tmp_path: Path) -> None:
    """The reason says WHAT was found and never quotes it.

    CLAUDE.md non-negotiable 12: a diagnostic is printed to a terminal and
    pasted into issues, so a diagnostic that echoes the personal data it found
    is the same leak in a different costume. The label is redacted to
    REDACTED_LABEL for a path outside the repository, which is why this arm can
    grade the whole of stderr rather than only the reason clause.
    """
    planted = plant_file(tmp_path)

    result = run_gate("--files", str(planted), env=base_env(tmp_path))

    # Not vacuous: the finding has to be there before its rendering is graded.
    assert PII_HOME_REASON in result.stderr, result.stderr

    # Bound to a scalar first. pytest renders the asserted EXPRESSION
    # independently of the message, so comparing the fragments inline would
    # print the planted value into the transcript on failure.
    leaked = sorted(
        name
        for name, value in (
            ("PLANTED_HOME_PATH", PLANTED_HOME_PATH),
            ("ACCOUNT_SEGMENT", ACCOUNT_SEGMENT),
            ("PLANTED_TEXT", PLANTED_TEXT.strip()),
        )
        if value in result.stderr
    )
    assert leaked == [], "the diagnostic echoed a planted value: " + ", ".join(leaked)
    assert REDACTED_LABEL in result.stderr, result.stderr
