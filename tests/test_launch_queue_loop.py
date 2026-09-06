"""Grading for `ops/loop/launch_queue_loop.ps1`, the detached launcher.

STATIC BY DESIGN. Every property below is read out of the script's source
rather than by running it, because running it would spawn a real driver against
the real lane - and the one assertion that genuinely needs a process (that the
refusal path exits 2 without spawning anything) is exercised by hand and
recorded in `docs/OPERATIONS.md`, not from inside the suite.

The properties here are the three ways this file has been got wrong before, in
the tree it was ported from. Each of them produced the same symptom: a real pid,
exit 0, and no work done. That symptom is invisible to an operator reading a
success banner, which is why the banner's reachability is itself graded.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.loop import queue_loop  # noqa: E402

#: The top of the 7-bit range. CLAUDE.md non-negotiable 4.
MAX_ASCII = 0x7E

#: What BOTH halves of the pair return when a stop sentinel is already
#: present. The driver owns the value; this module asserts they agree.
REFUSAL_EXIT = 2

LAUNCHER = ROOT / "ops" / "loop" / "launch_queue_loop.ps1"
RAW = LAUNCHER.read_bytes()
SOURCE = RAW.decode("ascii")


def _code_lines():
    """Source lines with comment-only lines dropped.

    The measured reasons live in comments and name the very things this module
    forbids, so a scan that could not tell a comment from a call site would
    report the explanation as the defect.
    """
    return [line for line in SOURCE.splitlines() if not line.lstrip().startswith("#")]


def test_the_launcher_is_tracked_and_on_disk():
    assert LAUNCHER.is_file()


def test_the_launcher_is_seven_bit_ascii_with_no_bom():
    """CLAUDE.md non-negotiable 4, and here it has teeth rather than taste.

    Windows PowerShell 5.1 ANSI-decodes a BOM-less .ps1, so a UTF-8 em-dash
    inside a double-quoted string becomes a character the tokenizer treats as a
    string terminator. One incident made the rule permanent.
    """
    assert not RAW.startswith(b"\xef\xbb\xbf"), "a BOM would change how 5.1 decodes this"
    bad = sorted({byte for byte in RAW if byte > MAX_ASCII})
    assert not bad, f"non-ASCII bytes in a .ps1: {bad}"


def test_the_launcher_is_lf_and_stays_that_way():
    assert b"\r\n" not in RAW


# ---------------------------------------------------------------------------
# ACCEPTANCE 3, first half - it refuses over a stop sentinel unless forced.
# ---------------------------------------------------------------------------


def test_the_sentinel_list_matches_the_drivers_own_list_exactly_and_in_order():
    """TWO COPIES OF ONE LIST IS THE DRIFT CLAUDE.md SECTION 4 IS ABOUT.

    The launcher cannot import the driver - it is PowerShell - so the list is
    duplicated by necessity. What is NOT necessary is letting the copies
    disagree: a sentinel the driver honours and the launcher does not is a
    launcher that prints a success banner over a no-op, which is the exact
    defect this file exists to prevent.
    """
    found = re.findall(r'Join-Path \$PSScriptRoot "control\\(.+?)"', SOURCE)
    expected = [rel.replace("/", "\\") for rel in queue_loop.STOP_RELPATHS]
    assert found == expected, f"the launcher checks {found} but the driver honours {expected}"


def test_the_refusal_exit_code_is_the_drivers_own_sentinel_code():
    """One number for one condition, whichever half of the pair refused."""
    pattern = rf"^\s*exit {REFUSAL_EXIT}\s*$"
    assert re.search(pattern, SOURCE, re.MULTILINE), f"no `exit {REFUSAL_EXIT}` on the refusal path"
    assert queue_loop.EXIT_STOP_SENTINEL == REFUSAL_EXIT, (
        "the driver's sentinel exit code moved; this launcher still exits 2"
    )


def test_force_exists_and_is_documented_as_only_bypassing_this_script():
    assert "[switch]$Force" in SOURCE
    assert "-not $Force" in SOURCE, "the refusal must be gated on -Force"
    lowered = SOURCE.lower()
    assert "re-checks these files itself" in lowered or "re-checks the same files" in lowered, (
        "-Force must say plainly that it does NOT override the driver's own check"
    )


def test_the_success_banner_is_unreachable_from_the_refusal():
    """ACCEPTANCE 3, second half - no success banner over a no-op.

    Asserted as an ORDER, which is the only thing a static read can honestly
    claim: the refusal's `exit` must come before the banner in the file, and the
    banner must not sit inside the sentinel block.
    """
    exit_at = SOURCE.index("exit 2")
    banner_at = SOURCE.index("queue-loop driver started")
    assert exit_at < banner_at, "the banner is reachable before the refusal returns"
    between = SOURCE[exit_at:banner_at]
    assert between.count("}") >= 1, "the refusal block never closes before the banner"


# ---------------------------------------------------------------------------
# ACCEPTANCE 3, third half - every path carrying a space is quoted.
# ---------------------------------------------------------------------------


def test_the_driver_path_is_quoted_in_the_argument_list():
    """MEASURED, not defensive style.

    Start-Process joins -ArgumentList with spaces and quotes NOTHING, so an
    unquoted repo root containing a space splits the path in two and the
    interpreter receives only the first half. It still issues a real pid and
    still exits 0, so the launcher prints "driver started" over a process that
    did nothing.
    """
    arglist = re.search(r"\$argList\s*=\s*@\((.*?)\)", SOURCE, re.DOTALL)
    assert arglist, "no -ArgumentList array found"
    first = arglist.group(1).split(",")[0].strip()
    assert first.startswith('"`"') or '`"$driver`"' in first, (
        f"the driver path is not quoted for Start-Process: {first}"
    )


def test_no_detached_process_equivalent_appears_anywhere():
    """No DETACHED_PROCESS equivalent appears anywhere in the launcher.

    MEASURED over three spawns differing only in flags: DETACHED_PROCESS issues
    a real pid and returns rc=0 while the child does nothing at all, because it
    cannot initialise a host without a console.
    """
    for line in _code_lines():
        assert "DETACHED_PROCESS" not in line
        assert "-Detached" not in line


def test_the_api_key_is_cleared_at_the_root_of_the_process_tree():
    """The API key is cleared at the root of the process tree.

    A Windows child inherits the parent's environment block, so one clear here
    covers every worker the driver spawns. Scoped to this process - the
    machine-wide variable is left alone.
    """
    assert "$env:ANTHROPIC_API_KEY = $null" in SOURCE


def test_no_home_path_is_hardcoded():
    """CLAUDE.md non-negotiable 3.

    The ported original pinned an absolute path under a user profile
    directory for its interpreter; this one resolves it.
    """
    offenders = [line for line in _code_lines() if re.search(r"[A-Za-z]:\\Users\\", line)]
    assert not offenders, f"a home path is hardcoded: {offenders}"
    assert "Get-Command pythonw" in SOURCE, "the interpreter must be resolved, not pinned"


def test_a_missing_interpreter_is_a_loud_failure_not_a_fallback():
    """An unresolvable interpreter throws rather than falling through.

    A launcher that silently picked a different interpreter would be the same
    class of lie as the two measured failures above: a real pid, exit 0, and no
    work done.
    """
    assert re.search(r"if \(-not \$py\) \{\s*\n?\s*throw", SOURCE), (
        "an unresolvable pythonw must throw, not fall through"
    )


def test_the_kill_advice_names_taskkill_and_not_the_banned_cmdlet():
    """CLAUDE.md bans the PowerShell process-stopping cmdlet because it hangs the MCP pipe.

    The advice this script prints has to be the allowed one.
    """
    assert "taskkill /F /T /PID" in SOURCE
    for line in _code_lines():
        assert "Stop-" + "Process" not in line


def test_the_flags_it_forwards_are_flags_the_driver_actually_has():
    """Every flag the launcher forwards is one the driver actually accepts.

    A launcher passing an argument the driver rejects would die in argparse
    AFTER Start-Process had already reported a pid - a success banner over a
    process that lived for a fraction of a second.
    """
    forwarded = set(re.findall(r'"(--[a-z-]+)"', SOURCE))
    # THE DRIVER'S SIDE IS READ FROM ITS SYNTAX TREE, NOT FROM ITS LINES, and
    # that is a correction rather than a preference. The first cut matched
    # `add_argument("--flag"` on one line; the formatter then put every flag on
    # a line of its own, the regex matched exactly one of them, and the guard
    # reported four correct flags as rejected. A guard that reddens when the
    # formatter runs is a guard that gets deleted. An AST walk finds the same
    # calls however they are wrapped.
    tree = ast.parse((ROOT / "ops" / "loop" / "queue_loop.py").read_text(encoding="utf-8"))
    parser_flags = {
        arg.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument"
        for arg in node.args
        if isinstance(arg, ast.Constant)
        and isinstance(arg.value, str)
        and arg.value.startswith("--")
    }
    assert parser_flags, "no argparse flags were found - the walk matched nothing"
    unknown = sorted(forwarded - parser_flags)
    assert not unknown, f"the launcher forwards flags the driver rejects: {unknown}"
